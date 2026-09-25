from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from fpl_api import fetch_bootstrap, fetch_user_team, fetch_fixtures, fetch_all_fixtures
import math
import requests
import os
import json
import logging
import traceback
import time
from fastapi import Request
import datetime

app = FastAPI(title="FPL Elite Scout API")

# Setup Error Monitoring Logger
os.makedirs("logs", exist_ok=True)
import sys
logging.basicConfig(
    level=logging.ERROR, 
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/error_log.txt'),
        logging.StreamHandler(sys.stdout)
    ]
)

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        if response.status_code >= 500:
            logging.error(f"{request.method} {request.url.path} | Status: {response.status_code} | Time: {time.time() - start_time:.3f}s")
        return response
    except Exception as e:
        logging.error(f"FATAL {request.method} {request.url.path} | Exception: {str(e)}\n{traceback.format_exc()}")
        raise

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Default calibrated weights (to be updated by Backtest findings)
DEFAULT_WEIGHTS = {
    "form_weight": 0.5,
    "defcon_weight": 0.033,  # 1/30
    "xg_weight": 1.0,
    "xa_weight": 1.0,
    "fdr_scale": 1.0,
    "opportunity_cost": 2.0
}

# --- DECISION ENGINE LAYER ---
def decision_engine_score(c):
    score = c["xp"]
    if "Rotation Risk / Bench" in c.get("reason", ""):
        score *= 0.75
    if "Low (Minutes Uncertainty)" in c.get("confidence", ""):
        score *= 0.60
    return score

import datetime
import os
import json

_prediction_cache = set()
_transfer_cache = set()

def log_prediction(player_data, gw, context=""):
    try:
        today = str(datetime.date.today())
        player_id = player_data["id"]
        cache_key = (player_id, gw, today)
        if cache_key in _prediction_cache:
            return
            
        _prediction_cache.add(cache_key)
        
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "predictions_log.jsonl")
        
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "gw": gw,
            "player_id": player_id,
            "player_name": player_data["name"],
            "team": player_data["team"],
            "position": player_data["pos_code"],
            "price": player_data["cost"],
            "xp": player_data["xp"],
            "expected_minutes": player_data.get("expected_minutes", 0),
            "rotation_risk": "Rotation Risk / Bench" in player_data.get("reason", ""),
            "start_probability": player_data.get("prob", 1.0),
            "fixture_diff": player_data.get("fixture_diff", 0),
            "confidence": player_data.get("confidence", ""),
            "decision_score": decision_engine_score(player_data),
            "context": context
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"Failed to log prediction: {e}")

def log_transfer_decision(gw, player_sold, player_bought, net_gain, recommendation):
    try:
        today = str(datetime.date.today())
        cache_key = (player_sold["id"] if player_sold else 0, player_bought["id"] if player_bought else 0, gw, today)
        if cache_key in _transfer_cache:
            return
            
        _transfer_cache.add(cache_key)
        
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "transfers_log.jsonl")
        
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "gw": gw,
            "player_sold": player_sold["name"] if player_sold else None,
            "player_sold_id": player_sold["id"] if player_sold else None,
            "player_bought": player_bought["name"] if player_bought else None,
            "player_bought_id": player_bought["id"] if player_bought else None,
            "predicted_5gw_gain": round(net_gain, 2),
            "decision_score_sold": decision_engine_score(player_sold) if player_sold else 0,
            "decision_score_bought": decision_engine_score(player_bought) if player_bought else 0,
            "recommendation": recommendation
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"Failed to log transfer: {e}")

def calculate_player_projection(p, next_gw, upcoming_fixtures_raw, teams, weights=None):
    if weights is None:
        weights = DEFAULT_WEIGHTS
        
    team_id_fpl = p["team"]
    pos_code = p["element_type"]
    
    # 1. Availability
    chance = p.get("chance_of_playing_next_round")
    availability_prob = 1.0 if chance is None else float(chance) / 100.0
    
    # 2. Expected Minutes (Realistic Model)
    total_mins = p.get("minutes", 0)
    starts = p.get("starts", 0)
    
    # Safe calculation for xMins
    if starts > 0:
        mins_per_app = min(90, total_mins / starts)
    elif total_mins > 0:
        mins_per_app = 20 # sub appearances only
    else:
        mins_per_app = 0
        
    form_val = float(p.get("form", 0) or 0)
    
    # Only upgrade minutes if they actually have some solid playing time or starts
    # A single goal in 10 mins shouldn't make them a starter.
    if form_val > 3.0 and mins_per_app < 45 and starts > 0:
        mins_per_app = min(75, mins_per_app + 15) # Momentum / breaking into team


    base_expected_minutes = mins_per_app
    if base_expected_minutes > 90: base_expected_minutes = 90
    base_cop = availability_prob
    expected_minutes = base_expected_minutes * base_cop # Store for confidence metric
    
    # 3. Base Per-90 Stats with Regression to the Mean (Shrinkage)
    raw_xg_90 = float(p.get("expected_goals_per_90", 0) or 0)
    raw_xa_90 = float(p.get("expected_assists_per_90", 0) or 0)
    raw_xgc_90 = float(p.get("expected_goals_conceded_per_90", 0) or 0)
    raw_defcon_90 = float(p.get("defensive_contribution_per_90", 0) or 0)
    
    # Shrinkage factor based on total_mins to avoid SSS (Small Sample Size) bias
    # If a player played 10 mins, weight is 10/450 = 0.02. We trust baseline 98%.
    # If a player played 450+ mins, weight is 1.0. We trust their stats 100%.
    weight = min(1.0, total_mins / 450.0) 
    
    baseline_xg = 0.05 if pos_code in [1, 2] else (0.15 if pos_code == 3 else 0.3)
    baseline_xa = 0.05 if pos_code == 1 else 0.1
    baseline_xgc = 1.5
    baseline_defcon = 4.0 if pos_code in [1, 2] else 2.0
    
    xg_90 = (weight * raw_xg_90 + (1 - weight) * baseline_xg) * weights["xg_weight"]
    xa_90 = (weight * raw_xa_90 + (1 - weight) * baseline_xa) * weights["xa_weight"]
    xgc_90 = weight * raw_xgc_90 + (1 - weight) * baseline_xgc
    defcon_90 = weight * raw_defcon_90 + (1 - weight) * baseline_defcon

    # 4. Form / Momentum Proxy
    # Cap form multiplier to avoid insane spikes from a single haul
    form_multiplier = 1.0 + (min(6.0, max(0, form_val)) / 30.0) 
    xg_90 *= form_multiplier
    xa_90 *= form_multiplier

    # FPL Rule 2024/2025: Defensive Contributions points
    # Defenders need 10 actions, Mid/Fwd need 12 actions for +2 points.
    import math
    defcon_threshold = 10 if pos_code == 2 else 12
    defcon_std = max(defcon_90 * 0.35, 1.0)
    z = (defcon_90 - defcon_threshold) / defcon_std
    prob_cross_threshold = 1 / (1 + math.exp(-1.7 * z)) if defcon_90 > 0 else 0
    
    goal_pts = {1: 6, 2: 6, 3: 5, 4: 4}.get(pos_code, 4)
    assist_pts = 3
    
    xAtt_90 = (xg_90 * goal_pts) + (xa_90 * assist_pts)
    cs_pts = {1: 4, 2: 4, 3: 1, 4: 0}.get(pos_code, 0)
    cs_prob_90 = math.exp(-xgc_90) if xgc_90 > 0 else 0.5
    xSave_90 = (float(p.get("saves_per_90", 0) or 0) / 3.0) * 1 if pos_code == 1 else 0
    
    # 2 points awarded for crossing Defensive Contribution threshold
    xDefcon_90 = prob_cross_threshold * 2.0
    
    gw_range = min(5, 38 - next_gw + 1)
    
    next_gw_opponent = "Blank"
    next_gw_diff = 5
    fixtures_found = 0
    
    total_5gw_projection = 0.0
    
    for gw_inc in range(gw_range):

        # Dynamic Expected Minutes & Injury Recovery Model
        current_cop = min(1.0, base_cop + (gw_inc * 0.25))
        dyn_expected_minutes = base_expected_minutes * current_cop
        target_gw = next_gw + gw_inc
        gw_fixs = [f for f in upcoming_fixtures_raw if f.get("event") == target_gw]
        player_fixs = [f for f in gw_fixs if f["team_h"] == team_id_fpl or f["team_a"] == team_id_fpl]
        
        gw_proj = 0.0
        
        for f in player_fixs:
            fixtures_found += 1
            is_home = (f["team_h"] == team_id_fpl)
            diff = f["team_h_difficulty"] if is_home else f["team_a_difficulty"]
            
            opp_id = f["team_a"] if is_home else f["team_h"]
            
            if gw_inc == 0 and fixtures_found == 1:
                next_gw_opponent = f"{teams.get(opp_id, {}).get('short_name', 'UNK')} ({'H' if is_home else 'A'})"
                next_gw_diff = diff
            
            # Split FDR based on Opponent Strength (V2 Logic)
            opp_team = teams.get(opp_id, {})
            avg_strength = 1100.0 # Baseline FPL strength index
            
            if is_home:
                opp_defence_strength = opp_team.get("strength_defence_away", avg_strength)
                opp_attack_strength = opp_team.get("strength_attack_away", avg_strength)
                home_adv = 1.05
            else:
                opp_defence_strength = opp_team.get("strength_defence_home", avg_strength)
                opp_attack_strength = opp_team.get("strength_attack_home", avg_strength)
                home_adv = 0.95
                
            att_multiplier = (avg_strength / opp_defence_strength) * home_adv if opp_defence_strength > 0 else 1.0
            def_multiplier = (avg_strength / opp_attack_strength) * home_adv if opp_attack_strength > 0 else 1.0
            
            match_xAtt = xAtt_90 * (dyn_expected_minutes / 90.0) * att_multiplier
            
            # Clean sheet
            match_xgc = (xgc_90 * (dyn_expected_minutes / 90.0)) / def_multiplier
            match_cs_prob = math.exp(-match_xgc) if match_xgc > 0 else 0.5
            match_xDef = match_cs_prob * cs_pts
            
            match_xSave = xSave_90 * (dyn_expected_minutes / 90.0) * def_multiplier
            match_xDefcon = xDefcon_90 * (dyn_expected_minutes / 90.0)
            
            appearance_pts = 0
            if dyn_expected_minutes >= 60: appearance_pts = 2 * current_cop
            elif dyn_expected_minutes > 0: appearance_pts = 1 * current_cop
            
            gw_proj += match_xAtt + match_xDef + match_xSave + match_xDefcon + appearance_pts
            
        total_5gw_projection += gw_proj
        
    total_5gw_projection = max(0.0, total_5gw_projection)
    
    # Confidence metrics based on uncertainty
    confidence = "Medium"
    if availability_prob < 0.9 or expected_minutes < 45:
        confidence = "Low (Minutes Uncertainty)"
    elif total_mins > 500 and availability_prob == 1.0 and fixtures_found >= gw_range:
        confidence = "High (Nailed Starter)"
        
    reasons = []
    if expected_minutes > 60:
        reasons.append("Nailed Starter")
    else:
        reasons.append("Rotation Risk / Bench")
        
    if form_multiplier > 1.1:
        reasons.append(f"Form Momentum: +{int((form_multiplier - 1)*100)}% to expected returns")
    if xg_90 > 0.3 or xa_90 > 0.3:
        reasons.append(f"Strong attacking threat (xG/90: {round(xg_90, 2)}, xA/90: {round(xa_90, 2)})")
    if cs_prob_90 > 0.4 and pos_code in [1, 2]:
        reasons.append(f"High Clean Sheet probability ({int(cs_prob_90*100)}%)")
        
    reason_str = "\n".join(reasons)
    
    proj_result = {
        "id": p["id"],
        "name": p["web_name"],
        "team": teams.get(p["team"], {}).get("short_name", "UNK"),
        "team_code": p["team_code"],
        "pos_code": pos_code,
        "cost": p["now_cost"] / 10,
        "xp": round(total_5gw_projection / max(1, gw_range), 2),
        "form": form_val,
        "total_points": p.get("total_points", 0),
        "selected_by_percent": float(p.get("selected_by_percent", 0) or 0),
        "fixture": next_gw_opponent,
        "fixture_diff": next_gw_diff,
        "confidence": confidence,
        "reason": reason_str,
        "prob": availability_prob,
        "news": p.get("news", ""),
        "xg": float(p.get("expected_goals", 0) or 0),
        "xa": float(p.get("expected_assists", 0) or 0),
        "expected_minutes": round(expected_minutes, 1),
        "expected_goals": float(p.get("expected_goals", 0) or 0),
        "expected_assists": float(p.get("expected_assists", 0) or 0),
        "expected_goals_conceded": float(p.get("expected_goals_conceded", 0) or 0),
        "defensive_contribution": p.get("defensive_contribution_per_90", 0.0),
        "clean_sheets": p.get("clean_sheets", 0),
        "goals_conceded": p.get("goals_conceded", 0),
        "minutes": p.get("minutes", 0)
    }
    
    # Global Logging Hook
    log_prediction(proj_result, next_gw, "Model Evaluation")
    
    return proj_result

def enrich_picks(picks_ids, squad):
    enriched = []
    for pid in picks_ids:
        player = next((p for p in squad if p["id"] == pid), None)
        if player:
            enriched.append(player)
    return enriched

def enrich_shared(shared_ids, squad_a, squad_b):
    enriched = []
    for pid in shared_ids:
        player = next((p for p in squad_a if p["id"] == pid), next((p for p in squad_b if p["id"] == pid), None))
        if player:
            enriched.append(player)
    return enriched
def get_fpl_context(gw_limit: int = 5, override_next_gw: int = None):
    """מחזיר bootstrap, teams, elements, next_gw ו-fixtures לטווח נתון — משותף לכל ה-endpoints."""
    bootstrap = fetch_bootstrap()
    events = bootstrap.get("events", [])
    current_gw = next((e["id"] for e in events if e["is_current"]), None)
    next_gw = next((e["id"] for e in events if e["is_next"]), None)
    if not next_gw and current_gw:
        next_gw = current_gw + 1
    elif not next_gw:
        next_gw = 1
    if override_next_gw:
        next_gw = override_next_gw
    all_fixtures = fetch_all_fixtures()
    max_gw = 38
    gw_range = min(gw_limit, max_gw - next_gw + 1) if gw_limit else max(1, max_gw - next_gw + 1)
    upper_bound = next_gw + gw_range - 1 if gw_limit else max_gw
    upcoming_fixtures_raw = [
        f for f in all_fixtures
        if f.get("event") and next_gw <= f["event"] <= upper_bound
    ]
    teams = {t["id"]: t for t in bootstrap.get("teams", [])}
    elements = {p["id"]: p for p in bootstrap.get("elements", [])}
    return {
        "bootstrap": bootstrap,
        "teams": teams,
        "elements": elements,
        "next_gw": next_gw,
        "gw_range": gw_range,
        "upcoming_fixtures_raw": upcoming_fixtures_raw,
    }


@app.get("/api/dashboard/{team_id}")
def get_dashboard_data(team_id: int):
    try:
        ctx = get_fpl_context(gw_limit=None)
        next_gw = ctx["next_gw"]
        gw_range = ctx["gw_range"]
        upcoming_fixtures_raw = ctx["upcoming_fixtures_raw"]
        elements = ctx["elements"]
        teams = ctx["teams"]

        picks, bank, team_name, rank, chips_used, leagues = fetch_user_team(team_id, next_gw)

        enriched_picks = []
        for pick in picks:
            player = elements.get(pick["element"])
            if player:
                proj = calculate_player_projection(player, next_gw, upcoming_fixtures_raw, teams)
                
                upcoming_fixtures = []
                for gw_inc in range(gw_range):
                    target_gw = next_gw + gw_inc
                    gw_fixs = [f for f in upcoming_fixtures_raw if f.get("event") == target_gw]
                    
                    found = False
                    for f in gw_fixs:
                        if f["team_h"] == player["team"]:
                            opp = teams.get(f["team_a"], {}).get("short_name", "UNK")
                            upcoming_fixtures.append({"gw": target_gw, "opponent": f"{opp} (H)", "difficulty": f["team_h_difficulty"]})
                            found = True
                            break
                        elif f["team_a"] == player["team"]:
                            opp = teams.get(f["team_h"], {}).get("short_name", "UNK")
                            upcoming_fixtures.append({"gw": target_gw, "opponent": f"{opp} (A)", "difficulty": f["team_a_difficulty"]})
                            found = True
                            break
                    if not found:
                        upcoming_fixtures.append({"gw": target_gw, "opponent": "Blank", "difficulty": 5})

                enriched_picks.append({
                    "id": player["id"],
                    "name": player["web_name"],
                    "team": teams.get(player["team"], {}).get("short_name", "UNK"),
                    "team_code": player.get("team_code", 1),
                    "pos_code": player["element_type"],
                    "position": pick.get("position"),
                    "cost": player["now_cost"] / 10,
                    "is_captain": pick.get("is_captain", False),
                    "is_vice_captain": pick.get("is_vice_captain", False),
                    "multiplier": pick.get("multiplier", 1),
                    "xp": proj["xp"],
                    "form": float(player.get("form", 0) or 0),
                    "chance_of_playing": player.get("chance_of_playing_next_round"),
                    "news": player.get("news"),
                    "upcoming_fixtures": upcoming_fixtures,
                    "total_points": player.get("total_points", 0),
                    "selected_by_percent": float(player.get("selected_by_percent", 0) or 0),
                    "expected_goals": float(player.get("expected_goals", 0) or 0),
                    "expected_assists": float(player.get("expected_assists", 0) or 0),
                    "expected_goals_conceded": float(player.get("expected_goals_conceded", 0) or 0),
                    "defensive_contribution": player.get("defensive_contribution_per_90", 0.0),
                    "clean_sheets": player.get("clean_sheets", 0),
                    "goals_conceded": player.get("goals_conceded", 0),
                    "fixture": proj.get("fixture", ""),
                    "fixture_diff": proj.get("fixture_diff", 3),
                    "minutes": player.get("minutes", 0)
                })
                
        schedule = {}
        for gw_inc in range(gw_range):
            target_gw = next_gw + gw_inc
            gw_fixs = [f for f in upcoming_fixtures_raw if f.get("event") == target_gw]
            formatted_fixs = []
            for f in gw_fixs:
                formatted_fixs.append({
                    "home": teams.get(f["team_h"], {}).get("short_name", "UNK"),
                    "away": teams.get(f["team_a"], {}).get("short_name", "UNK"),
                    "h_diff": f["team_h_difficulty"],
                    "a_diff": f["team_a_difficulty"],
                    "time": f.get("kickoff_time")
                })
            schedule[str(target_gw)] = formatted_fixs

        return {
            "team_id": team_id,
            "team_name": team_name,
            "rank": rank,
            "bank": bank,
            "next_gw": next_gw,
            "squad": enriched_picks,
            "schedule": schedule,
            "chips_used": chips_used,
        "leagues": leagues,
        "teams": teams
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/league/{league_id}")
def get_league_data(league_id: int):
    try:
        url = f"https://fantasy.premierleague.com/api/leagues-classic/{league_id}/standings/"
        import requests
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=12)
        if res.status_code != 200:
            raise Exception("League not found")
        return res.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compare/{team_a}/{team_b}")
def compare_teams(team_a: int, team_b: int):
    try:
        bootstrap = fetch_bootstrap()
        events = bootstrap.get("events", [])
        next_gw = next((e["id"] for e in events if e["is_next"]), 1)
        
        a_picks, a_bank, _, _, _, _ = fetch_user_team(team_a, next_gw)
        b_picks, b_bank, _, _, _, _ = fetch_user_team(team_b, next_gw)
        
        import requests
        a_info = requests.get(f"https://fantasy.premierleague.com/api/entry/{team_a}/", headers={'User-Agent': 'Mozilla/5.0'}, timeout=12)
        b_info = requests.get(f"https://fantasy.premierleague.com/api/entry/{team_b}/", headers={'User-Agent': 'Mozilla/5.0'}, timeout=12)
        
        a_data = {}
        b_data = {}
        
        if a_info.status_code == 200:
            a_data = a_info.json()
        if b_info.status_code == 200:
            b_data = b_info.json()
            
        a_ids = set([p["element"] for p in a_picks])
        b_ids = set([p["element"] for p in b_picks])
        
        shared = list(a_ids.intersection(b_ids))
        a_unique = list(a_ids - b_ids)
        b_unique = list(b_ids - a_ids)
        
        elements = {p["id"]: p for p in bootstrap.get("elements", [])}
        teams = {t["id"]: t for t in bootstrap.get("teams", [])}
        
        def hydrate(pick_list):
            res = []
            for pick in pick_list:
                player = elements.get(pick["element"])
                if player:
                    res.append({
                        "id": player["id"],
                        "name": player["web_name"],
                        "team": teams.get(player["team"], {}).get("short_name", "UNK"),
                        "team_code": player.get("team_code", 1),
                        "pos_code": player["element_type"],
                        "position": pick.get("position"),
                        "is_captain": pick.get("is_captain", False),
                        "multiplier": pick.get("multiplier", 1)
                    })
            return res
            
        a_squad = hydrate(a_picks)
        b_squad = hydrate(b_picks)
        
        return {
            "team_a": {
                "name": a_data.get("name", f"Team {team_a}"),
                "manager": f"{a_data.get('player_first_name', '')} {a_data.get('player_last_name', '')}",
                "unique": enrich_picks(a_unique, a_squad),
                "picks": a_squad,
                "active_chip": a_data.get("active_chip")
            },
            "team_b": {
                "name": b_data.get("name", f"Team {team_b}"),
                "manager": f"{b_data.get('player_first_name', '')} {b_data.get('player_last_name', '')}",
                "unique": enrich_picks(b_unique, b_squad),
                "picks": b_squad,
                "active_chip": b_data.get("active_chip")
            },
            "shared": enrich_shared(shared, a_squad, b_squad)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TransferRequest(BaseModel):
    pos_code: int
    max_budget: float
    current_squad_ids: List[int]
    transfer_out_id: Optional[int] = None
    target_gw: Optional[int] = None

@app.post("/api/transfer-lab")
def get_transfer_recommendations(req: TransferRequest):
    try:
        ctx = get_fpl_context(gw_limit=5, override_next_gw=req.target_gw)
        next_gw = ctx["next_gw"]
        upcoming_fixtures_raw = ctx["upcoming_fixtures_raw"]
        elements = ctx["bootstrap"].get("elements", [])
        teams = ctx["teams"]
        
        current_player = None
        if req.transfer_out_id:
            curr_p_raw = next((p for p in elements if p["id"] == req.transfer_out_id), None)
            if curr_p_raw:
                current_player = calculate_player_projection(curr_p_raw, next_gw, upcoming_fixtures_raw, teams)
                
        team_counts = {}
        for p in elements:
            if p["id"] in req.current_squad_ids and p["id"] != req.transfer_out_id:
                t = p["team"]
                team_counts[t] = team_counts.get(t, 0) + 1

        candidates = []
        for p in elements:
            if p["element_type"] == req.pos_code and p["id"] not in req.current_squad_ids:
                if (p["now_cost"] / 10) <= req.max_budget:
                    if team_counts.get(p["team"], 0) < 3:
                        c = calculate_player_projection(p, next_gw, upcoming_fixtures_raw, teams)
                        candidates.append(c)
                    
        candidates = sorted(candidates, key=decision_engine_score, reverse=True)
        best_candidate = candidates[0] if candidates else None
        
        recommendation = "HOLD"
        delta = 0.0
        threshold = DEFAULT_WEIGHTS["opportunity_cost"]
        explanation = ""
        
        if current_player and best_candidate:
            raw_gain = round(best_candidate["xp"] - current_player["xp"], 2)
            delta = raw_gain
            
            if raw_gain <= 0:
                recommendation = "HOLD"
                explanation = "השחקן הנוכחי צפוי להביא יותר או אותו מספר נקודות מאשר האלטרנטיבות, כך שאין צורך בחילוף."
            elif raw_gain <= 1.0:
                recommendation = "HOLD"
                explanation = f"המחליף ({best_candidate['name']}) צפוי להביא רק {raw_gain} נקודות יותר למחזור בממוצע. פער כה קטן לא מצדיק שריפת חילוף, אלא אם כן השחקן שלך פצוע."
            elif raw_gain <= 2.0:
                recommendation = "CONSIDER"
                explanation = f"שדרוג סביר. {best_candidate['name']} צפוי להביא {raw_gain} נקודות יותר. מומלץ לבצע את החילוף רק אם יש לך חילופים חינמיים עודפים ואין בעיות דחופות יותר."
            else:
                recommendation = "TRANSFER"
                explanation = f"חילוף מצוין! {best_candidate['name']} משדרג אותך משמעותית עם פער של {raw_gain} נקודות צפויות למחזור (פיצוי מהיר על עלות החילוף). מומלץ מאוד."
                
        if current_player:
            log_prediction(current_player, next_gw, "Transfer Lab - Current")
        if best_candidate:
            log_prediction(best_candidate, next_gw, "Transfer Lab - Candidate")
            
        if current_player and best_candidate:
            log_transfer_decision(next_gw, current_player, best_candidate, delta, recommendation)

        return {
            "recommendation": recommendation,
            "delta": delta,
            "threshold": threshold,
            "explanation": explanation,
            "current_player": current_player,
            "best_transfer": best_candidate,
            "candidates": candidates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def build_squad(players, forced_players=[]):
    squad = list(forced_players)
    cost = sum(p['cost'] for p in squad)
    team_counts = {}
    pos_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    
    for p in squad:
        team_counts[p['team']] = team_counts.get(p['team'], 0) + 1
        pos_counts[p['pos_code']] += 1
        
    min_costs = {1: 4.0, 2: 4.0, 3: 4.5, 4: 4.5}
    
    for p in players:
        if len(squad) == 15:
            break
        if any(x['id'] == p['id'] for x in squad):
            continue
            
        needed = False
        if p['pos_code'] == 1 and pos_counts[1] < 2: needed = True
        if p['pos_code'] == 2 and pos_counts[2] < 5: needed = True
        if p['pos_code'] == 3 and pos_counts[3] < 5: needed = True
        if p['pos_code'] == 4 and pos_counts[4] < 3: needed = True
        
        if not needed:
            continue
        if team_counts.get(p['team'], 0) >= 3:
            continue
            
        rem_slots_budget = 0
        for t in range(1, 5):
            needed_count = (2 if t == 1 else 5 if t == 2 else 5 if t == 3 else 3) - pos_counts[t]
            if t == p['pos_code']:
                needed_count -= 1
            if needed_count > 0:
                rem_slots_budget += needed_count * min_costs[t]
                
        if cost + p['cost'] + rem_slots_budget <= 100.0:
            squad.append(p)
            cost += p['cost']
            team_counts[p['team']] = team_counts.get(p['team'], 0) + 1
            pos_counts[p['pos_code']] += 1
            
    squad.sort(key=lambda x: (x['pos_code'], -x['cost']))
    
    # map to frontend format
    formatted = []
    for p in squad:
        formatted.append({
            "id": p["id"],
            "name": p["name"],
            "team_code": p.get("team_code", p.get("team")),
            "element_type": p["pos_code"],
            "now_cost": int(p["cost"] * 10),
            "xp": p["xp"]
        })
    return {"squad": formatted, "cost": int(cost * 10)}

@app.get("/api/drafts")
def get_drafts():
    try:
        bootstrap = fetch_bootstrap()
        elements = bootstrap.get("elements", [])
        teams = {t["id"]: t for t in bootstrap.get("teams", [])}
        
        events = bootstrap.get("events", [])
        next_gw = next((e["id"] for e in events if e["is_next"]), 1)
        all_fixtures = fetch_all_fixtures()
        
        gw_range = min(5, 38 - next_gw + 1)
        upcoming_fixtures_raw = [f for f in all_fixtures if f.get("event") and next_gw <= f["event"] <= next_gw + gw_range - 1]
        
        all_players = []
        for p in elements:
            if p["status"] not in ["u", "i", "s"]:
                proj = calculate_player_projection(p, next_gw, upcoming_fixtures_raw, teams)
                # Ensure we have team_code for shirt image
                proj["team_code"] = p.get("team_code")
                all_players.append(proj)
                
        premiums = sorted([p for p in all_players if p["cost"] >= 10.0], key=lambda x: x["xp"], reverse=True)[:2]
        others_for_premium = sorted(all_players, key=lambda x: x["xp"]/max(0.1, x["cost"]), reverse=True)
        premium_draft = build_squad(others_for_premium, premiums)
        
        balanced_players = sorted([p for p in all_players if p["cost"] <= 9.5], key=lambda x: x["xp"], reverse=True)
        balanced_draft = build_squad(balanced_players, [])
        
        def diff_score(p):
            bonus = 2 if p["selected_by_percent"] < 10 else 1 if p["selected_by_percent"] < 15 else 0
            return p["xp"] + bonus
            
        differential_players = sorted(all_players, key=diff_score, reverse=True)
        diff_draft = build_squad(differential_players, [])
        
        return {
            "drafts": [
                {"id": 1, "name": "Premium Heavies (כוכבים יקרים)", "description": "הרכב מבוסס על שחקני פרימיום חזקים יחד עם שחקנים זולים משלימים.", "data": premium_draft},
                {"id": 2, "name": "Balanced Spread (הרכב מאוזן)", "description": "ללא שחקנים יקרים מדי, מאפשר עומק חזק מאוד בכל העמדות במגרש.", "data": balanced_draft},
                {"id": 3, "name": "Differentials (פנינים נסתרות)", "description": "שחקנים בכושר שיא שאחוזי הבחירה שלהם נמוכים, כדי לעקוף מתחרים.", "data": diff_draft}
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/radar")
def get_radar():
    try:
        bootstrap = fetch_bootstrap()
        elements = bootstrap.get("elements", [])
        teams = {t["id"]: t for t in bootstrap.get("teams", [])}
        
        events = bootstrap.get("events", [])
        next_gw = next((e["id"] for e in events if e["is_next"]), 1)
        all_fixtures = fetch_all_fixtures()
        
        gw_range = min(5, 38 - next_gw + 1)
        upcoming_fixtures_raw = [f for f in all_fixtures if f.get("event") and next_gw <= f["event"] <= next_gw + gw_range - 1]
        
        all_players = []
        for p in elements:
            if p["status"] != "u":
                proj = calculate_player_projection(p, next_gw, upcoming_fixtures_raw, teams)
                all_players.append(proj)
        
        scout_picks = sorted(all_players, key=lambda x: x["xp"], reverse=True)[:10]
        hot_form = sorted(all_players, key=lambda x: x["form"], reverse=True)[:10]
        
        differentials = sorted([p for p in all_players if p["selected_by_percent"] < 10.0 and p["xp"] > 3.0], key=lambda x: x["xp"], reverse=True)[:10]
        if not differentials:
            differentials = sorted([p for p in all_players if p["selected_by_percent"] < 10.0], key=lambda x: x["xp"], reverse=True)[:10]
            
        return {
            "scout_picks": scout_picks,
            "hot_form": hot_form,
            "differentials": differentials
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class BudgetScenariosRequest(BaseModel):
    squad: List[dict]
    bank: float
    next_gw: int

@app.post("/api/budget-scenarios")
def get_budget_scenarios(req: BudgetScenariosRequest):
    try:
        squad = req.squad
        bank = req.bank
        next_gw = req.next_gw
        
        bootstrap = fetch_bootstrap()
        all_fixtures = fetch_all_fixtures()
        elements = bootstrap.get("elements", [])
        teams = {t["id"]: t for t in bootstrap.get("teams", [])}
        
        gw_range = min(5, 38 - next_gw + 1)
        upcoming_fixtures_raw = [f for f in all_fixtures if f.get("event") and next_gw <= f["event"] <= next_gw + gw_range - 1]
        
        all_players = []
        for p in elements:
            if p["status"] == "a":
                proj = calculate_player_projection(p, next_gw, upcoming_fixtures_raw, teams)
                all_players.append(proj)
        
        current_squad_ids = [p["id"] for p in squad]
        suggestions = []
        
        for sp in squad:
            reason = None
            if sp.get("chance_of_playing") is not None and sp.get("chance_of_playing") < 75:
                reason = "Injury / Doubtful"
            elif sp.get("form", 0) < 2.0 and sp.get("xp", 0) < 3.0:
                reason = "Poor Output (Low Form & Projection)"
            elif sp.get("xp", 0) < 3.0:
                reason = "Tough Upcoming Run (Low 5GW Projection)"
                
            if reason:
                budget = bank + sp["cost"]
                candidates = [p for p in all_players if p["pos_code"] == sp["pos_code"] and p["id"] not in current_squad_ids and p["cost"] <= budget]
                
                candidates = sorted(candidates, key=decision_engine_score, reverse=True)
                top_candidates = candidates[:3]
                
                if top_candidates:
                    suggestions.append({
                        "sell": sp,
                        "reason": reason,
                        "buys": top_candidates
                    })
                    
        return suggestions
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/player/{player_id}")
def get_player_details(player_id: int):
    try:
        url = f"https://fantasy.premierleague.com/api/element-summary/{player_id}/"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        ctx = get_fpl_context(gw_limit=5)
        elements = ctx["elements"]
        p = elements.get(player_id, {})
        
        return {
            "id": player_id,
            "name": p.get("web_name", "Unknown"),
            "team_code": p.get("team_code", 1),
            "pos_code": p.get("element_type", 1),
            "cost": p.get("now_cost", 0) / 10,
            "form": p.get("form", "0.0"),
            "points": p.get("total_points", 0),
            "xg": p.get("expected_goals", "0.0"),
            "xa": p.get("expected_assists", "0.0"),
            "xgc": p.get("expected_goals_conceded", "0.0"),
            "defcon": p.get("defensive_contribution_per_90", 0.0),
            "history": data.get("history", [])[-5:], # last 5 GWs
            "fixtures": data.get("fixtures", [])[:5] # next 5 GWs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
