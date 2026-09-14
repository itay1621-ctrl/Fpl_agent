import json
import time
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

st.set_page_config(
    page_title="FPL Elite Scout | מנוע החלטות",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================================================================
# מילון צבעי חולצות הקבוצות הרשמי של הפרמייר-ליג
# =====================================================================
TEAM_KITS = {
    "ARS": {"primary": "#EF0107", "secondary": "#FFFFFF"},
    "AVL": {"primary": "#670E36", "secondary": "#95B1D3"},
    "BHA": {"primary": "#0057B8", "secondary": "#FFFFFF"},
    "BOU": {"primary": "#DA291C", "secondary": "#000000"},
    "BRE": {"primary": "#E30613", "secondary": "#FFFFFF"},
    "CHE": {"primary": "#034694", "secondary": "#FFFFFF"},
    "CRY": {"primary": "#1B458F", "secondary": "#C4122E"},
    "EVE": {"primary": "#003399", "secondary": "#FFFFFF"},
    "FUL": {"primary": "#FFFFFF", "secondary": "#000000"},
    "IPS": {"primary": "#00448A", "secondary": "#FFFFFF"},
    "LEI": {"primary": "#003090", "secondary": "#FFFFFF"},
    "LIV": {"primary": "#C8102E", "secondary": "#00B2A9"},
    "MCI": {"primary": "#6CABDD", "secondary": "#1C2C5B"},
    "MUN": {"primary": "#DA291C", "secondary": "#000000"},
    "NEW": {"primary": "#241F20", "secondary": "#FFFFFF"},
    "NFO": {"primary": "#DD0000", "secondary": "#FFFFFF"},
    "SOU": {"primary": "#D71920", "secondary": "#FFFFFF"},
    "TOT": {"primary": "#FFFFFF", "secondary": "#132257"},
    "WHU": {"primary": "#7A263A", "secondary": "#1BB1E7"},
    "WOL": {"primary": "#FDB913", "secondary": "#231F20"},
    "LEE": {"primary": "#FFFFFF", "secondary": "#0000FF"},
    "BRU": {"primary": "#003399", "secondary": "#FFFFFF"},
}

def get_kit(team_code):
    return TEAM_KITS.get(team_code, {"primary": "#38bdf8", "secondary": "#1e2e46"})

def render_jersey_svg(team_code):
    kit = get_kit(team_code)
    p = kit["primary"]
    s = kit["secondary"]
    return (
        f'<svg width="24" height="22" viewBox="0 0 40 38" style="margin: 0 auto 3px auto; display: block; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.6));">'
        f'<path d="M12,4 L20,9 L28,4 L38,11 L33,20 L29,17 L29,36 L11,36 L11,17 L7,20 L2,11 Z" fill="{p}" stroke="{s}" stroke-width="2"/>'
        f'<path d="M16,6 Q20,12 24,6" fill="none" stroke="{s}" stroke-width="2.5"/>'
        f'</svg>'
    )

# =====================================================================
# עיצוב CSS: מבודד ומדויק - שומר על מסך הכניסה ומונע מריחה
# =====================================================================
st.markdown(
    """
<style>
:root {
    --bg-main: #090e17;
    --bg-card: #111a28;
    --bg-card-hover: #162235;
    --border-color: #1e2e46;
    --text-primary: #f8fafc;
    --text-muted: #94a3b8;
    --accent-blue: #38bdf8;
    --accent-green: #10b981;
    --accent-yellow: #f59e0b;
    --accent-red: #ef4444;
}

.main {
    direction: rtl;
    text-align: right;
    background-color: var(--bg-main);
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    color: var(--text-primary);
}

div[data-testid="stMarkdownContainer"] p {
    direction: rtl;
    text-align: right;
    line-height: 1.6;
}

.ltr-tag {
    direction: ltr !important;
    unicode-bidi: isolate;
    display: inline-block;
    font-weight: 600;
}

/* מסך נחיתה / כניסה - רחב ונקי */
.gate-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 28px 20px;
    margin: 20px auto;
    max-width: 580px;
    text-align: center;
    box-shadow: 0 10px 25px rgba(0,0,0,0.4);
}

.kpi-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 10px;
    margin-bottom: 16px;
}
.kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 12px;
    text-align: center;
}
.kpi-title {
    font-size: 12px;
    color: var(--text-muted);
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 19px;
    font-weight: 700;
    color: var(--text-primary);
}

/* =====================================================================
   עיצוב מגרש ירוק ממורכז ואחיד (באמצעות סלקטור מבודד :has)
   ===================================================================== */
div[data-testid="stVerticalBlock"]:has(.pitch-anchor) {
    background: radial-gradient(circle at 50% 50%, #1c4422 0%, #112d16 75%, #0a1c0d 100%) !important;
    border: 2px solid #2d6b34 !important;
    border-radius: 20px !important;
    padding: 20px 16px !important;
    box-shadow: 0 16px 45px rgba(0, 0, 0, 0.65), inset 0 0 50px rgba(0, 0, 0, 0.5) !important;
    max-width: 800px !important;
    margin: 10px auto !important;
    position: relative;
}

/* ספסל ממורכז */
div[data-testid="stVerticalBlock"]:has(.bench-anchor) {
    background: #0d1624 !important;
    border: 1px dashed #2a3c55 !important;
    border-radius: 16px !important;
    padding: 14px 12px !important;
    max-width: 620px !important;
    margin: 12px auto !important;
}

/* מרכוז עמודות אך ורק בתוך המגרש והספסל (לא פוגע במסך הכניסה!) */
div[data-testid="stVerticalBlock"]:has(.pitch-anchor) div[data-testid="column"],
div[data-testid="stVerticalBlock"]:has(.bench-anchor) div[data-testid="column"] {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
}

/* כפתורי חילוף בתוך המגרש/ספסל בלבד */
div[data-testid="stVerticalBlock"]:has(.pitch-anchor) div[data-testid="stButton"],
div[data-testid="stVerticalBlock"]:has(.bench-anchor) div[data-testid="stButton"] {
    width: 100%;
    max-width: 104px !important;
}

div[data-testid="stVerticalBlock"]:has(.pitch-anchor) div[data-testid="stButton"] button,
div[data-testid="stVerticalBlock"]:has(.bench-anchor) div[data-testid="stButton"] button {
    width: 100% !important;
    border-radius: 8px 8px 0 0 !important;
    margin-bottom: -1px !important;
    padding: 1px 4px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    height: 24px !important;
    min-height: 24px !important;
    line-height: 22px !important;
    transition: all 0.2s ease !important;
    box-shadow: none !important;
}

div[data-testid="stVerticalBlock"]:has(.pitch-anchor) div[data-testid="stButton"] button[kind="secondary"],
div[data-testid="stVerticalBlock"]:has(.bench-anchor) div[data-testid="stButton"] button[kind="secondary"] {
    background: #141f2e !important;
    color: #38bdf8 !important;
    border: 1px solid #1e2e46 !important;
    border-bottom: none !important;
}

div[data-testid="stVerticalBlock"]:has(.pitch-anchor) div[data-testid="stButton"] button[kind="secondary"]:hover,
div[data-testid="stVerticalBlock"]:has(.bench-anchor) div[data-testid="stButton"] button[kind="secondary"]:hover {
    background: #38bdf8 !important;
    color: #090e17 !important;
    border-color: #38bdf8 !important;
    box-shadow: 0 0 8px rgba(56, 189, 248, 0.7) !important;
}

div[data-testid="stVerticalBlock"]:has(.pitch-anchor) div[data-testid="stButton"] button[kind="primary"],
div[data-testid="stVerticalBlock"]:has(.bench-anchor) div[data-testid="stButton"] button[kind="primary"] {
    background: #ef4444 !important;
    color: #ffffff !important;
    border: 1px solid #ef4444 !important;
    border-bottom: none !important;
    box-shadow: 0 0 10px rgba(239, 68, 68, 0.7) !important;
}

/* כרטיס שחקן צמוד ומדויק */
.p-card-body {
    background: rgba(17, 26, 40, 0.95);
    border: 1px solid var(--border-color);
    border-radius: 0 0 8px 8px !important;
    padding: 6px 4px 6px 4px;
    text-align: center;
    box-shadow: 0 5px 12px rgba(0,0,0,0.4);
    width: 100%;
    max-width: 104px !important;
    min-height: 118px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-sizing: border-box;
}

.cap-gold { border: 2px solid #facc15 !important; border-top: none !important; }
.card-bench { background: rgba(22, 32, 48, 0.85); border: 1px dashed #475569; border-top: none !important; }
.card-danger { border: 2px solid #f87171 !important; border-top: none !important; background: rgba(248, 113, 113, 0.15) !important; }
.card-warning { border: 2px solid #fbd38d !important; border-top: none !important; background: rgba(251, 211, 141, 0.15) !important; }
.card-selected-sub { border: 2px solid #38bdf8 !important; border-top: none !important; box-shadow: 0 0 14px rgba(56, 189, 248, 0.75) !important; }

.p-name {
    font-weight: 700;
    font-size: 11.5px;
    color: #f8fafc;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.2;
}
.p-sub {
    font-size: 9px;
    color: var(--text-muted);
    margin: 1px 0;
}

.badge-fdr {
    font-size: 8.5px;
    font-weight: 800;
    padding: 1px 4px;
    border-radius: 4px;
    display: inline-block;
}
.fdr-2 { background: #15803d; color: #fff; }
.fdr-3 { background: #475569; color: #fff; }
.fdr-4 { background: #b91c1c; color: #fff; }
.fdr-5 { background: #7f1d1d; color: #fff; }

.prob-badge {
    font-size: 8.5px;
    font-weight: 700;
    padding: 1px 4px;
    border-radius: 4px;
    margin: 2px auto 0 auto;
    width: fit-content;
}

.prob-red { background: rgba(248, 113, 113, 0.25); color: #fca5a5; border: 1px solid #f87171; }
.prob-yellow { background: rgba(251, 211, 141, 0.25); color: #fde68a; border: 1px solid #fbd38d; }
.prob-green { background: #064e3b; color: #6ee7b7; border: 1px solid #059669; }

.accessible-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 12px;
}
.accessible-card:hover {
    background: var(--bg-card-hover);
}
.split-box {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #1e293b;
    padding-bottom: 8px;
    margin-bottom: 10px;
}
.meta-chip {
    font-size: 11px;
    background: #1e293b;
    color: var(--text-muted);
    padding: 3px 8px;
    border-radius: 6px;
}

.flaw-row {
    background: #1c1518;
    border-right: 4px solid var(--accent-red);
    border-radius: 6px;
    padding: 8px 12px;
    margin-bottom: 6px;
    font-size: 12.5px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.flaw-pen {
    background: #7f1d1d;
    color: #fecaca;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 11px;
}

.mini-fxt-container { 
    display: flex; 
    justify-content: center; 
    gap: 3px; 
    margin-top: 4px; 
}
.mini-fxt { 
    font-size: 8px; 
    font-weight: 800; 
    text-transform: uppercase; 
    padding: 1px 3px; 
    border-radius: 3px; 
    color: white; 
    line-height: 1.1; 
    text-shadow: 0 1px 1px rgba(0,0,0,0.6);
}

.planner-swap-box {
    background: #111a28;
    border: 2px solid #38bdf8;
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 16px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.5);
}

.badge-transfer-pill {
    background: #162235;
    border: 1px solid #334155;
    border-radius: 20px;
    padding: 4px 12px;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin: 4px;
    font-size: 12px;
}
</style>
    """,
    unsafe_allow_html=True,
)


# --- 1. משיכת נתוני הליגה וכיול אלגוריתמי (עד GW 38) ---
@st.cache_data(ttl=600)
def fetch_league_data():
    base = "https://fantasy.premierleague.com/api/"
    bootstrap = requests.get(f"{base}bootstrap-static/").json()
    fixtures = requests.get(f"{base}fixtures/").json()
    teams = {t["id"]: t for t in bootstrap["teams"]}
    elements = {el["id"]: el for el in bootstrap["elements"]}

    next_gw = 4
    next_deadline = ""
    for ev in bootstrap["events"]:
        if ev.get("is_next"):
            next_gw = ev["id"]
            next_deadline = ev["deadline_time"]
            break

    pos_map = {1: "שוער", 2: "הגנה", 3: "קישור", 4: "חלוץ"}
    elite_defenses = ["ARS", "MCI", "LIV", "NEW", "CHE"]
    processed = {}

    all_season_gws = list(range(next_gw, 39))

    for el_id, el in elements.items():
        if el["status"] == "u":
            continue

        team_short = teams[el["team"]]["short_name"]
        gw_fixtures_map = {}
        upcoming = []
        fdr_list = []

        for f in fixtures:
            ev = f.get("event")
            if ev in all_season_gws:
                if f["team_h"] == el["team"]:
                    opp = teams[f["team_a"]]["short_name"]
                    diff = f["team_h_difficulty"]
                    gw_fixtures_map[ev] = (f"{opp} (H)", diff)
                elif f["team_a"] == el["team"]:
                    opp = teams[f["team_h"]]["short_name"]
                    diff = f["team_a_difficulty"]
                    gw_fixtures_map[ev] = (f"{opp} (A)", diff)

        for g in range(next_gw, min(39, next_gw + 5)):
            if g in gw_fixtures_map:
                match_str, diff = gw_fixtures_map[g]
                upcoming.append(match_str)
                fdr_list.append(diff)
            else:
                upcoming.append("BLANK")
                fdr_list.append(3)

        weights = [0.50, 0.30, 0.20]
        weighted_fdr = sum(
            (5.3 - fdr) * weights[i] for i, fdr in enumerate(fdr_list[:3])
        )
        avg_fdr = sum(fdr_list[:3]) / 3.0

        mins = el.get("minutes", 0)
        actual_gi = el.get("goals_scored", 0) + el.get("assists", 0)
        expected_gi = float(el.get("expected_goal_involvements", 0.0))
        form = float(el.get("form", 0.0))
        cost = el["now_cost"] / 10
        threat = float(el.get("threat", 0.0))

        status = el.get("status", "a")
        chance_raw = el.get("chance_of_playing_next_round")
        if chance_raw is not None:
            chance = int(chance_raw)
        elif status in ["i", "s", "u"]:
            chance = 0
        elif status == "d":
            chance = 50
        else:
            chance = 100

        mins_per_gw = mins / max(1, (next_gw - 1))
        
        if mins_per_gw >= 75 or cost >= 8.0:
            tactical_rate = 100
        elif mins_per_gw >= 55:
            tactical_rate = 85
        elif mins_per_gw >= 35:
            tactical_rate = 65
        else:
            tactical_rate = 40 if mins_per_gw > 0 else 20
            
        start_prob = (
            int(round(tactical_rate * (chance / 100.0))) if chance > 0 else 0
        )

        xgi_p90 = (expected_gi / mins) * 90 if mins >= 60 else expected_gi

        tag_status = None
        buy_low_bonus = 0.0
        if expected_gi >= 1.2 and actual_gi <= 1:
            tag_status = "BUY_LOW"
            buy_low_bonus = 1.0
        elif actual_gi >= 3 and expected_gi < 0.9:
            tag_status = "OVERPERFORMING_TRAP"
            buy_low_bonus = -0.8

        nailed_mult = 1.15 if mins_per_gw >= 75 else 0.85
        score = (
            (xgi_p90 * 3.2)
            + (form * 1.3)
            + (weighted_fdr * 1.8)
            + (threat * 0.015)
            + buy_low_bonus
        )
        if el["element_type"] in [1, 2]:
            if team_short in elite_defenses:
                score *= 1.3
            elif threat > 35:
                score *= 1.15
        else:
            if form >= 5.0 or actual_gi >= 2:
                score *= 1.2

        score *= nailed_mult

        next_fdr = fdr_list[0] if fdr_list else 3
        cs_prob = {2: 0.45, 3: 0.28, 4: 0.15, 5: 0.08}.get(next_fdr, 0.22)
        base_app = 2.0 if chance >= 75 else (1.0 if chance >= 25 else 0.0)

        if el["element_type"] in [1, 2]:
            pred_xp = base_app + (cs_prob * 4.0) + (xgi_p90 * 0.4 * 5.0)
        elif el["element_type"] == 3:
            pred_xp = base_app + (cs_prob * 1.0) + (xgi_p90 * 5.5)
        else:
            pred_xp = base_app + (xgi_p90 * 5.2)

        if form >= 5.0:
            pred_xp += 0.6
        if chance < 100:
            pred_xp *= chance / 100.0
        pred_xp = round(max(0.0, pred_xp), 1)

        if tag_status == "BUY_LOW":
            reason = "מייצר מצבים ברצף (xGI גבוה) אך טרם תוגמל במספרים. פוטנציאל התפוצצות."
        elif tag_status == "OVERPERFORMING_TRAP":
            reason = "כבש מעבר למצבים הממשיים שייצר. סכנת ירידה לממוצע ולוח מתקשה."
        elif el["element_type"] in [1, 2]:
            reason = (
                "עוגן רשת נקייה מוביל מקבוצה בכירה."
                if team_short in elite_defenses
                else "מגן פעיל התקפית בלוח ירוק."
            )
        else:
            reason = (
                "כושר שיא עם מעורבות ישירה בהתקפה."
                if form >= 5.0
                else "תוחלת שערים יציבה לקראת משחקים נוחים."
            )

        processed[el_id] = {
            "id": el_id,
            "name": el["web_name"],
            "team": team_short,
            "pos": pos_map[el["element_type"]],
            "pos_code": el["element_type"],
            "cost": cost,
            "form": form,
            "total_points": el.get("total_points", 0),
            "xgi_p90": round(xgi_p90, 2),
            "selected_by": float(el["selected_by_percent"]),
            "score": round(score, 2),
            "xp": pred_xp,
            "tag": tag_status,
            "reason": reason,
            "status": status,
            "chance": chance,
            "start_prob": start_prob,
            "next_match": upcoming[0] if upcoming else "—",
            "next_fdr": next_fdr,
            "avg_fdr": round(avg_fdr, 2),
            "fixtures": " | ".join(upcoming[:3]),
            "gw_fixtures_map": gw_fixtures_map,
            "upcoming_list": upcoming,
            "fdr_list_full": fdr_list,
        }

    return processed, next_gw, next_deadline


all_players, next_gw, next_deadline = fetch_league_data()

# --- 2. שער כניסה ומסך נחיתה ---
url_id = st.query_params.get("team", None)

if "user_team_id" not in st.session_state:
    st.session_state.user_team_id = (
        url_id.strip() if url_id and url_id.strip().isdigit() else None
    )

if st.session_state.get("user_team_id"):
    st.query_params["team"] = str(st.session_state.user_team_id)

if not st.session_state.user_team_id:
    st.write("")
    st.markdown(
        """
    <div class="gate-card">
        <h1 style="color:#38bdf8; margin-bottom:6px;">⚽ FPL Elite Scout</h1>
        <div style="font-size:15px; color:#94a3b8; margin-bottom:18px;">
            סוכן בינה ואסטרטגיית הרכב לקראת מחזור המכוון ל-<b class="ltr-tag">Top 50K</b>
        </div>
        <p style="font-size:13px; color:#cbd5e1; line-height:1.6; margin-bottom:20px;">
            הזן את מספר הקבוצה שלך כדי לטעון ניתוח כשירות, ציון סגל מכויל, חסרונות הרכב והצעות חילוף מותאמות לתקציב.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    c_form = st.columns([1, 2, 1])[1]
    with c_form:
        input_val = st.text_input(
            "מספר קבוצה (Team ID):",
            placeholder="למשל: 139103",
            help="המספר שמופיע בכתובת הדפדפן בלשונית Points",
        )
        b1, b2 = st.columns(2)
        with b1:
            if st.button("🚀 כניסה לסגל שלי", use_container_width=True, type="primary"):
                if input_val.strip().isdigit():
                    st.session_state.user_team_id = input_val.strip()
                    st.query_params["team"] = input_val.strip()
                    st.rerun()
                else:
                    st.error("נא להזין ספרות בלבד.")
        with b2:
            if st.button("👀 סגל דמו לדוגמה", use_container_width=True):
                st.session_state.user_team_id = "1"
                st.query_params["team"] = "1"
                st.rerun()

        with st.expander("❓ איפה מוצאים את ה-Team ID?"):
            st.markdown(
                """
            1. היכנס ל-<span class="ltr-tag">fantasy.premierleague.com</span> והתחבר.
            2. לחץ על לשונית **Points** (נקודות).
            3. העתק את רצף הספרות מתוך שורת הכתובת:  
               `.../entry/XXXXXX/event/...`  
            """,
                unsafe_allow_html=True,
            )
    st.stop()

team_id = st.session_state.user_team_id


# --- 3. משיכת נתוני הקבוצה מה-API ---
@st.cache_data(ttl=300)
def fetch_user_team(t_id, gw):
    try:
        last_gw = max(1, gw - 1)
        base = "https://fantasy.premierleague.com/api/"
        picks_url = f"{base}entry/{t_id}/event/{last_gw}/picks/"
        picks_res = requests.get(picks_url).json()
        entry_url = f"{base}entry/{t_id}/"
        entry_res = requests.get(entry_url).json()

        if picks_res.get("active_chip") == "free_hit" and last_gw > 1:
            base_gw = last_gw - 1
            base_url = f"{base}entry/{t_id}/event/{base_gw}/picks/"
            picks_res = requests.get(base_url).json()

        bank = picks_res.get("entry_history", {}).get("bank", 0) / 10
        picks = picks_res.get("picks", [])
        team_name = entry_res.get("name", f"Team {t_id}")
        rank = entry_res.get("summary_overall_rank", "—")
        return picks, bank, team_name, rank
    except Exception:
        return None, 0.0, None, None


raw_picks, initial_bank, my_team_name, my_rank = fetch_user_team(
    team_id, next_gw
)
if not raw_picks:
    st.error(f"❌ לא ניתן למשוך נתונים עבור מזהה {team_id}. ודא שהמספר תקין.")
    if st.button("🔄 חזרה להזנת ID"):
        st.session_state.user_team_id = None
        st.query_params.clear()
        st.rerun()
    st.stop()

# ניהול סגל גלובלי
if (
    "user_squad" not in st.session_state
    or st.session_state.get("synced_team_id") != team_id
):
    st.session_state.user_squad = [dict(p) for p in raw_picks]
    st.session_state.user_bank = initial_bank
    st.session_state.synced_team_id = team_id
    st.session_state.transfers_log = []

# ניהול תוכנית ה-Planner בכל מחזורי העונה (עד GW 38)
if "planner_plan" not in st.session_state:
    st.session_state.planner_plan = {
        g: {"chip": "ללא צ'יפ", "transfers": []} for g in range(next_gw, 39)
    }
if "planner_starting_fts" not in st.session_state:
    st.session_state.planner_starting_fts = 1
if "planner_horizon_count" not in st.session_state:
    st.session_state.planner_horizon_count = 5
if "planner_sell_id" not in st.session_state:
    st.session_state.planner_sell_id = None

starters = []
bench = []
for p in st.session_state.user_squad:
    pid = p["element"]
    p_info = all_players.get(pid)
    if p_info:
        item = {
            **p_info,
            "is_cap": p.get("is_captain", False),
            "is_vc": p.get("is_vice_captain", False),
            "position": p["position"],
        }
        if p["position"] <= 11:
            starters.append(item)
        else:
            bench.append(item)

pos_counts = {1: 0, 2: 0, 3: 0, 4: 0}
for p in starters:
    pos_counts[p["pos_code"]] += 1

formation_valid = (
    pos_counts[1] == 1
    and (3 <= pos_counts[2] <= 5)
    and (2 <= pos_counts[3] <= 5)
    and (1 <= pos_counts[4] <= 3)
    and len(starters) == 11
)

starting_xp_total = sum(
    p["xp"] * (2 if p.get("is_cap") else 1) for p in starters
)

# חישוב ציון מכויל וחסרונות
benchmark_xp = 60.0
base_score = (starting_xp_total / benchmark_xp) * 84.0
squad_flaws = []
total_penalty = 0.0

for p in starters:
    if p["status"] != "a" or p["chance"] < 100:
        pen = 6.5 if p["chance"] <= 25 else 4.0
        total_penalty += pen
        squad_flaws.append({
            "type": "כשירות בהרכב",
            "penalty": f"-{pen:.1f}",
            "text": (
                f"<b>{p['name']}</b> בספק/פצוע ({p['chance']}% כשירות רפואית |"
                f" {p['start_prob']}% סבירות לפתוח)."
            ),
        })

for bp in bench:
    if bp["status"] != "a" or bp["chance"] < 100:
        pen = 3.0
        total_penalty += pen
        squad_flaws.append({
            "type": "ספסל מושבת",
            "penalty": f"-{pen:.1f}",
            "text": (
                f"<b>{bp['name']}</b> פצוע/מושבת ({bp['chance']}%) - אין גיבוי"
                " אוטומטי בהיעדרות."
            ),
        })

for p in starters:
    if p["pos_code"] in [1, 2] and p["next_fdr"] >= 4:
        pen = 4.0
        total_penalty += pen
        squad_flaws.append({
            "type": "הגנה בסיכון ספיגה",
            "penalty": f"-{pen:.1f}",
            "text": (
                f"<b>{p['name']}</b> מול יריבה קשה (<span"
                f' class="ltr-tag">{p["next_match"]}</span>, FDR'
                f" {p['next_fdr']})."
            ),
        })

for p in starters:
    if p["status"] == "a" and p["form"] < 2.5 and p["pos_code"] in [3, 4]:
        pen = 2.0
        total_penalty += pen
        squad_flaws.append({
            "type": "כושר התקפי דל",
            "penalty": f"-{pen:.1f}",
            "text": (
                f"<b>{p['name']}</b> בבצורת (כושר {p['form']}) במחזורים האחרונים."
            ),
        })

for p in starters:
    if p["tag"] == "OVERPERFORMING_TRAP":
        pen = 1.5
        total_penalty += pen
        squad_flaws.append({
            "type": "סכנת דעיכה (מלכודת)",
            "penalty": f"-{pen:.1f}",
            "text": f"<b>{p['name']}</b> הבקיע מעבר למצבי השער שייצר (xGI נמוך).",
        })

if not formation_valid:
    pen = 8.0
    total_penalty += pen
    squad_flaws.append({
        "type": "מערך לא חוקי",
        "penalty": f"-{pen:.1f}",
        "text": (
            "המערך הנוכחי אינו חוקי (חובה שוער 1, 3–5 מגנים ולפחות חלוץ 1)."
        ),
    })

squad_rating = int(max(48, min(86, base_score - total_penalty)))
rating_color = (
    "#10b981"
    if squad_rating >= 78
    else ("#38bdf8" if squad_rating >= 70 else "#f59e0b")
)

# --- 4. סרגל עליון ומדדים ראשיים ---
h_col1, h_col2 = st.columns([3, 1])
with h_col1:
    st.title(f"⚽ {my_team_name}")
    st.caption(
        f'מנוע החלטות למחזור {next_gw} | קבוצה: <span'
        f' class="ltr-tag"><b>{team_id}</b></span>',
        unsafe_allow_html=True,
    )
with h_col2:
    st.write("")
    if st.button("🔄 החלף קבוצה", use_container_width=True):
        st.session_state.user_team_id = None
        st.query_params.clear()
        st.rerun()

rank_txt = (
    f"{my_rank:,}"
    if isinstance(my_rank, int)
    else (str(my_rank) if my_rank else "—")
)

st.markdown(
    f"""
<div class="kpi-container">
    <div class="kpi-card">
        <div class="kpi-title">ציון סגל מכויל</div>
        <div class="kpi-value" style="color:{rating_color};">{squad_rating} <span style="font-size:13px; color:#64748b;">/ 100</span></div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">תחזית נקודות (xP)</div>
        <div class="kpi-value" style="color:#10b981;">{starting_xp_total:.1f}</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">יתרה בבנק</div>
        <div class="kpi-value"><span class="ltr-tag">£{st.session_state.user_bank:.1f}m</span></div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">דירוג עולמי</div>
        <div class="kpi-value"><span class="ltr-tag">{rank_txt}</span></div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# --- שעון דד-ליין חי ב-HTML/JS ---
clock_html = f"""
<div style="background:#0f172a; border:1px solid #334155; border-radius:10px; padding:10px; text-align:center; direction:rtl; margin-bottom:15px; color:#f8fafc;">
    <div style="font-size:12px; color:#94a3b8; margin-bottom:4px;">⏳ זמן נותר עד נעילת חילופים (GW {next_gw})</div>
    <div id="fpl-clock" style="font-size:22px; font-weight:bold; color:#10b981; direction:ltr;">טוען שעון...</div>
</div>
<script>
    var deadline = new Date("{next_deadline}").getTime();
    var x = setInterval(function() {{
        var now = new Date().getTime();
        var distance = deadline - now;
        
        if (distance < 0) {{
            clearInterval(x);
            document.getElementById("fpl-clock").innerHTML = "הדד-ליין עבר!";
            document.getElementById("fpl-clock").style.color = "#ef4444";
            return;
        }}
        
        var days = Math.floor(distance / (1000 * 60 * 60 * 24));
        var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        var minutes = Math.floor((distance % (1000 * 60)) / (1000 * 60));
        var seconds = Math.floor((distance % (1000 * 60)) / 1000);
        
        document.getElementById("fpl-clock").innerHTML = days + "d " + hours + "h " + minutes + "m " + seconds + "s";
    }}, 1000);
</script>
"""
components.html(clock_html, height=85)


# =====================================================================
# לוגיקת החילופים האינטראקטיביים במגרש הראשי
# =====================================================================
if "swap_state" not in st.session_state:
    st.session_state.swap_state = {"out_id": None}

def handle_swap_click(clicked_id):
    curr_out = st.session_state.swap_state.get("out_id")
    if curr_out is None:
        st.session_state.swap_state["out_id"] = clicked_id
        st.rerun()
    elif curr_out == clicked_id:
        st.session_state.swap_state["out_id"] = None
        st.rerun()
    else:
        p_out_id = curr_out
        p_in_id = clicked_id

        p_o = next((p for p in st.session_state.user_squad if p["element"] == p_out_id), None)
        p_i = next((p for p in st.session_state.user_squad if p["element"] == p_in_id), None)

        if p_o and p_i:
            o_is_starter = (p_o["position"] <= 11)
            i_is_starter = (p_i["position"] <= 11)

            if o_is_starter != i_is_starter:
                starter_p_id = p_out_id if o_is_starter else p_in_id
                bench_p_id = p_in_id if o_is_starter else p_out_id

                sim = [
                    all_players[p["element"]]["pos_code"]
                    for p in st.session_state.user_squad
                    if p["position"] <= 11 and p["element"] != starter_p_id
                ] + [all_players[bench_p_id]["pos_code"]]

                p_o_pos = all_players[p_out_id]["pos_code"]
                p_i_pos = all_players[p_in_id]["pos_code"]

                if (p_o_pos == 1 or p_i_pos == 1) and p_o_pos != p_i_pos:
                    st.toast("⚠️ שוער יכול להתחלף רק מול שוער!", icon="⚠️")
                elif sim.count(1) != 1 or not (3 <= sim.count(2) <= 5) or not (2 <= sim.count(3) <= 5) or not (1 <= sim.count(4) <= 3):
                    st.toast("⚠️ מערך לא חוקי! חובה שוער 1, 3-5 מגנים, 2-5 קשרים וחלוץ 1.", icon="⚠️")
                else:
                    p_o["position"], p_i["position"] = p_i["position"], p_o["position"]
                    st.session_state.swap_state["out_id"] = None
                    st.toast(f"✅ חילוף בוצע: {all_players[p_out_id]['name']} ⇄ {all_players[p_in_id]['name']}", icon="✅")
                    st.rerun()
            else:
                p_o["position"], p_i["position"] = p_i["position"], p_o["position"]
                st.session_state.swap_state["out_id"] = None
                st.toast(f"✅ חילוף בוצע: {all_players[p_out_id]['name']} ⇄ {all_players[p_in_id]['name']}", icon="✅")
                st.rerun()

        st.session_state.swap_state["out_id"] = None
        st.rerun()


# --- 5. טאבים מרכזיים ---
t_squad, t_transfers, t_analysis, t_scout, t_scenarios, t_planner = st.tabs([
    "🟢 הסגל על המגרש",
    "🔄 מעבדת חילופים",
    "📊 ניתוח וחסרונות",
    "🌟 רדאר רכש עילית",
    "🎯 3 תרחישי תקציב",
    "🗓️ מתכנן מחזורים משורשר",
])


def render_player_unit(col, p, is_bench=False):
    """מרנדר כרטיס שחקן עם חולצה בצבעי המועדון - ללא בעיית הזחת Markdown"""
    with col:
        curr_out = st.session_state.swap_state.get("out_id")
        is_sel = (curr_out == p["id"])
        has_sel = (curr_out is not None)

        if is_sel:
            btn_lbl = "✕ ביטול"
            btn_kind = "primary"
        elif has_sel:
            btn_lbl = "⇄ לכאן"
            btn_kind = "secondary"
        else:
            btn_lbl = "⇄ חילוף"
            btn_kind = "secondary"

        if st.button(btn_lbl, key=f"sub_btn_{p['id']}_{'b' if is_bench else 's'}", use_container_width=True, type=btn_kind):
            handle_swap_click(p["id"])

        cap_badge = "👑 " if p.get("is_cap") else ("🥈 " if p.get("is_vc") else "")
        bench_class = "card-bench" if is_bench else ""
        sel_class = "card-selected-sub" if is_sel else ""

        if p["chance"] <= 25 or p["status"] in ["i", "s", "u"]:
            status_class = "card-danger"
            status_pill = f'<div class="prob-badge prob-red">🔴 פצוע {p["start_prob"]}%</div>'
        elif p["chance"] <= 75 or p["status"] == "d":
            status_class = "card-warning"
            status_pill = f'<div class="prob-badge prob-yellow">🟡 בספק {p["start_prob"]}%</div>'
        else:
            status_class = "cap-gold" if p.get("is_cap") else ""
            status_pill = f'<div class="prob-badge prob-green">🟢 {p["start_prob"]}% פותח</div>'

        kit = get_kit(p["team"])
        kit_color = kit["primary"]
        jersey_svg = render_jersey_svg(p["team"])

        # מחרוזת ישירה ללא הזחות של 4 רווחים כדי למנוע הפיכה לבלוק קוד מרוקן
        card_html = (
            f'<div class="p-card-body {status_class} {bench_class} {sel_class}" style="border-top: 3px solid {kit_color} !important;">'
            f'{jersey_svg}'
            f'<div class="p-name">{cap_badge}{p["name"]}</div>'
            f'<div class="p-sub"><span class="ltr-tag">{p["team"]} | £{p["cost"]}m</span></div>'
            f'<div class="badge-fdr fdr-{p["next_fdr"]}"><span class="ltr-tag">{p["next_match"]}</span></div>'
            f'{status_pill}'
            f'<div style="font-size:9.5px; color:#38bdf8; margin-top:2px; font-weight:700;">xP: {p["xp"]}</div>'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)


# טאב 1: מגרש חי
with t_squad:
    st.caption(
        f"מערך: **{pos_counts[2]}-{pos_counts[3]}-{pos_counts[4]}** | סך תוחלת"
        f" נקודות: **{starting_xp_total:.1f}**"
    )

    curr_out = st.session_state.swap_state.get("out_id")
    if curr_out is not None:
        sel_name = all_players.get(curr_out, {}).get("name", "שחקן")
        c_b1, c_b2 = st.columns([5, 1])
        with c_b1:
            st.info(
                f"🔄 **מצב חילופים פעיל:** בחרת ב-**{sel_name}**. לחץ על **⇄ לכאן** בראש שחקן אחר מהמגרש או מהספסל כדי להשלים את החילוף."
            )
        with c_b2:
            if st.button("✕ בטל חילוף", key="cancel_top_banner", use_container_width=True):
                st.session_state.swap_state["out_id"] = None
                st.rerun()

    fwds = [p for p in starters if p["pos_code"] == 4]
    mids = [p for p in starters if p["pos_code"] == 3]
    defs = [p for p in starters if p["pos_code"] == 2]
    gks = [p for p in starters if p["pos_code"] == 1]

    # מיכל מגרש ירוק ממורכז עם עוגן CSS (.pitch-anchor)
    with st.container():
        st.markdown('<div class="pitch-anchor"></div>', unsafe_allow_html=True)

        # 1. חלוצים
        if fwds:
            if len(fwds) == 1:
                _, c_fwd, _ = st.columns([1, 1, 1])
                render_player_unit(c_fwd, fwds[0])
            elif len(fwds) == 2:
                _, c1, c2, _ = st.columns([1, 2, 2, 1])
                render_player_unit(c1, fwds[0])
                render_player_unit(c2, fwds[1])
            else:
                fwd_cols = st.columns(len(fwds))
                for i, p in enumerate(fwds):
                    render_player_unit(fwd_cols[i], p)

        st.write("")

        # 2. קישור
        if mids:
            mid_cols = st.columns(len(mids))
            for i, p in enumerate(mids):
                render_player_unit(mid_cols[i], p)

        st.write("")

        # 3. הגנה
        if defs:
            def_cols = st.columns(len(defs))
            for i, p in enumerate(defs):
                render_player_unit(def_cols[i], p)

        st.write("")

        # 4. שוער
        if gks:
            _, c_gk, _ = st.columns([2, 1, 2])
            render_player_unit(c_gk, gks[0])

    # מיכל ספסל ממורכז עם עוגן CSS (.bench-anchor)
    with st.container():
        st.markdown('<div class="bench-anchor"></div>', unsafe_allow_html=True)
        st.caption("🪑 שחקני הספסל:")
        bench_cols = st.columns(4)
        for i, p in enumerate(bench):
            render_player_unit(bench_cols[i], p, is_bench=True)


# טאב 2: מעבדת חילופים
with t_transfers:
    st.subheader("🔄 מעבדת חילופים מותאמת עמדה ותקציב")
    current_all = starters + bench
    current_pids = [p["id"] for p in current_all]

    def mark_priority(p):
        return (
            p["status"] != "a"
            or p["chance"] < 100
            or p["next_fdr"] >= 4
            or p["form"] < 2.5
        )

    sorted_squad = sorted(
        current_all,
        key=lambda x: (mark_priority(x), x["total_points"]),
        reverse=True,
    )

    def format_transfer_out(pid):
        p = all_players[pid]
        flag = "⚠️ " if mark_priority(p) else ""
        return f"{flag}{p['name']} ({p['pos']} - {p['team']}) | £{p['cost']}m | xP: {p['xp']}"

    col_out, col_in = st.columns(2)
    with col_out:
        st.markdown("#### 1. שחקן למכירה (OUT)")
        sel_out_id = st.selectbox(
            "בחר שחקן להוצאה:",
            [p["id"] for p in sorted_squad],
            format_func=format_transfer_out,
        )
        p_out = all_players[sel_out_id]
        budget_cap = round(p_out["cost"] + st.session_state.user_bank, 1)

    with col_in:
        st.markdown(f"#### 2. שחקן לרכש בעמדת {p_out['pos']} (IN)")
        search_str = (
            st.text_input(
                "חיפוש מהיר:",
                placeholder="הקלד שם או קבוצה באנגלית...",
            )
            .strip()
            .lower()
        )

        eligible = [
            p
            for p in all_players.values()
            if p["pos_code"] == p_out["pos_code"]
            and p["id"] not in current_pids
            and p["status"] == "a"
            and p["cost"] <= budget_cap
        ]
        if search_str:
            eligible = [
                p
                for p in eligible
                if search_str in p["name"].lower() or search_str in p["team"].lower()
            ]

        ranked_recs = [
            x["id"]
            for x in sorted(eligible, key=lambda x: x["score"], reverse=True)[:3]
        ]
        pool = sorted(
            eligible,
            key=lambda x: (x["id"] in ranked_recs, x["total_points"]),
            reverse=True,
        )

        def format_transfer_in(pid):
            p = all_players[pid]
            rec = "⭐ " if pid in ranked_recs else ""
            return f"{rec}{p['name']} ({p['team']}) | £{p['cost']}m | xP: {p['xp']}"

        if pool:
            sel_in_id = st.selectbox(
                "בחר שחקן לקנייה (מסונן לפי עמדה ותקציב):",
                [p["id"] for p in pool],
                format_func=format_transfer_in,
            )
            p_in = all_players[sel_in_id]
        else:
            st.warning("אין שחקנים מתאימים בתקציב זה.")
            p_in = None

    if p_in:
        delta = round(p_in["xp"] - p_out["xp"], 1)
        new_bank = round(
            st.session_state.user_bank + p_out["cost"] - p_in["cost"], 1
        )
        st.markdown(
            f"""
            <div class="accessible-card">
                <div class="split-box">
                    <b>השוואת שחקנים ראש-בראש:</b>
                    <span style="color:#10b981; font-weight:700;">תוספת צפויה: {delta:+} xP</span>
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px; font-size:13px;">
                    <div>
                        <b>🔴 יוצא: {p_out['name']}</b><br>
                        נקודות העונה: {p_out['total_points']} | xP: {p_out['xp']}<br>
                        משחק קרוב: <span class="ltr-tag">{p_out['next_match']}</span>
                    </div>
                    <div>
                        <b>🟢 נכנס: {p_in['name']}</b><br>
                        נקודות העונה: {p_in['total_points']} | xP: {p_in['xp']}<br>
                        משחק קרוב: <span class="ltr-tag">{p_in['next_match']}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        b_act1, b_act2 = st.columns([1, 2])
        with b_act1:
            if st.button("אשר חילוף בסגל 🔁", use_container_width=True):
                for p in st.session_state.user_squad:
                    if p["element"] == p_out["id"]:
                        p["element"] = p_in["id"]
                        break
                st.session_state.user_bank = new_bank
                st.session_state.transfers_log.append(f"{p_out['name']} ⬅️ {p_in['name']}")
                st.rerun()

    if st.session_state.transfers_log:
        st.caption(
            f"חילופים שנשמרו: {', '.join(st.session_state.transfers_log)}"
        )
        if st.button("אפס סגל למקור ↩️"):
            st.session_state.user_squad = [dict(p) for p in raw_picks]
            st.session_state.user_bank = initial_bank
            st.session_state.transfers_log = []
            st.rerun()


# טאב 3: ניתוח וחסרונות
with t_analysis:
    st.subheader("📊 ניתוח עוצמה ונקודות תורפה")
    c_flaw1, c_flaw2 = st.columns([1, 2])
    with c_flaw1:
        st.markdown(
            f"""
            <div class="accessible-card" style="text-align:center;">
                <div style="font-size:13px; color:#94a3b8;">ציון סגל מכויל</div>
                <div style="font-size:38px; font-weight:800; color:{rating_color}; margin:6px 0;">
                    {squad_rating} <span style="font-size:16px; color:#64748b;">/ 100</span>
                </div>
                <div style="font-size:12px; color:#cbd5e1;">תחזית הרכב: <b>{starting_xp_total:.1f}</b> נק׳</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_flaw2:
        st.markdown("<b>מוקדי סיכון שהורידו ניקוד:</b>", unsafe_allow_html=True)
        if squad_flaws:
            for f in squad_flaws:
                st.markdown(
                    f"""
                    <div class="flaw-row">
                        <div><b>[{f['type']}]:</b> {f['text']}</div>
                        <div class="flaw-pen">{f['penalty']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.success("לא אותרו חסרונות בולטים בהרכב!")

    st.write("")
    st.markdown("#### 📋 11 שחקני ההרכב הפותח")
    starters_table = []
    for p in starters:
        starters_table.append({
            "שחקן": f"{p['name']} {'👑' if p.get('is_cap') else ''}",
            "עמדה": p["pos"],
            "קבוצה": p["team"],
            "משחק קרוב": p["next_match"],
            "FDR": p["next_fdr"],
            "סבירות לפתוח": f"{p['start_prob']}%",
            "נקודות עונה": p["total_points"],
            "xP": round(p["xp"] * (2 if p.get("is_cap") else 1), 1),
        })
    st.dataframe(
        pd.DataFrame(starters_table).sort_values(by="xP", ascending=False),
        use_container_width=True,
        hide_index=True,
    )


# טאב 4: רדאר רכש עילית
with t_scout:
    st.subheader(f"🌟 רדאר רכש מוביל למחזור {next_gw}")
    st_fwd, st_mid, st_def, st_gk, st_cap = st.tabs(
        ["חלוצים", "קשרים", "מגנים", "שוערים", "קפטן מגן מול חרב"]
    )

    def display_scout_cards(pos_code, limit=5):
        items = sorted(
            [
                p
                for p in all_players.values()
                if p["pos_code"] == pos_code and p["status"] == "a"
            ],
            key=lambda x: x["score"],
            reverse=True,
        )[:limit]
        for p in items:
            tag = (
                '<span class="meta-chip" style="color:#6ee7b7;">🔥 קנייה בשפל</span>'
                if p["tag"] == "BUY_LOW"
                else (
                    '<span class="meta-chip" style="color:#fca5a5;">⚠️ מעל'
                    " המצופה</span>"
                    if p["tag"] == "OVERPERFORMING_TRAP"
                    else ""
                )
            )
            st.markdown(
                f"""
                <div class="accessible-card">
                    <div class="split-box">
                        <div>
                            <b>{p['name']}</b> <span class="ltr-tag" style="color:#94a3b8;">({p['team']})</span> {tag}
                        </div>
                        <span class="ltr-tag" style="color:#38bdf8;">£{p['cost']}m | xP: {p['xp']}</span>
                    </div>
                    <div style="font-size:12px; color:#cbd5e1; margin-bottom:6px;">💡 {p['reason']}</div>
                    <div style="font-size:11px; color:#94a3b8;">
                        משחק קרוב: <span class="badge-fdr fdr-{p['next_fdr']}"><span class="ltr-tag">{p['next_match']}</span></span> |
                        סבירות לפתוח: <b>{p['start_prob']}%</b> | סך נקודות: <b>{p['total_points']}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with st_fwd:
        display_scout_cards(4)
    with st_mid:
        display_scout_cards(3)
    with st_def:
        display_scout_cards(2)
    with st_gk:
        display_scout_cards(1, 4)

    with st_cap:
        premiums = sorted(
            [
                p
                for p in all_players.values()
                if p["cost"] >= 7.5 and p["status"] == "a"
            ],
            key=lambda x: x["score"],
            reverse=True,
        )
        c_shield = premiums[0]
        diffs = [p for p in premiums if p["selected_by"] < 18]
        c_sword = diffs[0] if diffs else premiums[1]

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown(
                f"""
                <div class="accessible-card" style="border-right: 4px solid #059669;">
                    <span class="meta-chip" style="color:#6ee7b7;">🛡️ קפטן מגן (Shield)</span>
                    <h4 style="margin:8px 0;">{c_shield['name']} <span class="ltr-tag">({c_shield['team']})</span></h4>
                    <div style="font-size:12px; color:#cbd5e1; line-height:1.6;">
                        בעלות: <span class="ltr-tag">{c_shield['selected_by']}%</span> | סבירות פתיחה: {c_shield['start_prob']}%<br>
                        משחק קרוב: <span class="ltr-tag">{c_shield['next_match']}</span> | xP: <b>{c_shield['xp']}</b><br>
                        💡 {c_shield['reason']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_s2:
            st.markdown(
                f"""
                <div class="accessible-card" style="border-right: 4px solid #d97706;">
                    <span class="meta-chip" style="color:#fde68a;">⚔️ קפטן דיפרנשיאל (Sword)</span>
                    <h4 style="margin:8px 0;">{c_sword['name']} <span class="ltr-tag">({c_sword['team']})</span></h4>
                    <div style="font-size:12px; color:#cbd5e1; line-height:1.6;">
                        בעלות: <span class="ltr-tag">{c_sword['selected_by']}% בלבד</span> | סבירות פתיחה: {c_sword['start_prob']}%<br>
                        משחק קרוב: <span class="ltr-tag">{c_sword['next_match']}</span> | xP: <b>{c_sword['xp']}</b><br>
                        💡 {c_sword['reason']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# טאב 5: 3 תרחישי תקציב
with t_scenarios:
    st.subheader("🎯 3 תרחישי חילוף אופטימליים לתקציב הסגל")
    my_full_squad = starters + bench
    my_ids_set = {x["id"] for x in my_full_squad}

    def get_optimal_in(pos_code, budget_limit):
        cands = [
            p
            for p in all_players.values()
            if p["id"] not in my_ids_set
            and p["pos_code"] == pos_code
            and p["cost"] <= budget_limit
            and p["status"] == "a"
        ]
        return max(cands, key=lambda x: x["score"]) if cands else None

    cand_def = min(
        [p for p in my_full_squad if p["pos_code"] == 2],
        key=lambda x: (
            x["score"] if x["status"] == "a" and x["chance"] == 100 else -20
        ),
    )
    cand_mid = min(
        [p for p in my_full_squad if p["pos_code"] == 3],
        key=lambda x: (
            x["score"] if x["status"] == "a" and x["chance"] == 100 else -15
        ),
    )
    fwd_sub = [
        p
        for p in my_full_squad
        if p["pos_code"] == 4 and "Haaland" not in p["name"]
    ]
    cand_fwd = (
        min(fwd_sub, key=lambda x: x["score"])
        if fwd_sub
        else [p for p in my_full_squad if p["pos_code"] == 4][0]
    )

    scenarios_list = [
        {
            "title": "אופציה 1: ייצוב הגנתי / החלפת מוקד פציעה",
            "tag": "הגנה",
            "out": cand_def,
            "in": get_optimal_in(
                2, cand_def["cost"] + st.session_state.user_bank
            ),
        },
        {
            "title": "אופציה 2: שדרוג מנוע הקישור וייצור מצבים",
            "tag": "קישור",
            "out": cand_mid,
            "in": get_optimal_in(
                3, cand_mid["cost"] + st.session_state.user_bank
            ),
        },
        {
            "title": "אופציה 3: רענון חוד ההתקפה",
            "tag": "התקפה",
            "out": cand_fwd,
            "in": get_optimal_in(
                4, cand_fwd["cost"] + st.session_state.user_bank
            ),
        },
    ]

    for item in scenarios_list:
        p_o, p_i = item["out"], item["in"]
        if not p_i:
            continue
        rem = round((p_o["cost"] + st.session_state.user_bank) - p_i["cost"], 1)
        diff_xp = round(p_i["xp"] - p_o["xp"], 1)

        st.markdown(
            f"""
            <div class="accessible-card">
                <div class="split-box">
                    <b>{item['title']}</b>
                    <span style="color:#10b981; font-weight:700;">תוספת: +{diff_xp} xP</span>
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; font-size:12.5px;">
                    <div style="background:#231114; border-right:3px solid #ef4444; padding:8px; border-radius:6px;">
                        🔴 יוצא: <b>{p_o['name']}</b> ({p_o['team']})<br>
                        נקודות: {p_o['total_points']} | xP: {p_o['xp']}
                    </div>
                    <div style="background:#0c2417; border-right:3px solid #10b981; padding:8px; border-radius:6px;">
                        🟢 נכנס: <b>{p_i['name']}</b> ({p_i['team']})<br>
                        נשאר בבנק: <span class="ltr-tag">£{rem}m</span> | xP: {p_i['xp']}
                    </div>
                </div>
                <div style="font-size:11.5px; color:#94a3b8; margin-top:6px;">💡 {p_i['reason']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =====================================================================
# טאב 6: מתכנן מחזורים משורשר ואינטואיטיבי (עד GW 38)
# =====================================================================
with t_planner:
    st.subheader("🗓️ מתכנן מחזורים משורשר וסימולטור צ'יפים (עד Gameweek 38)")
    st.caption(
        "מנוע החלטות אינטראקטיבי: לחץ על **'🔄 החלף'** בראש כרטיס שחקן על המגרש כדי להסירו ולבחור לו מחליף בלחיצה אחת."
    )

    max_possible_horizon = 38 - next_gw + 1
    horizon_options = {
        "5 מחזורים קרובים": 5,
        "8 מחזורים קרובים": min(8, max_possible_horizon),
        "12 מחזורים קרובים": min(12, max_possible_horizon),
        f"כל העונה עד מחזור 38 ({max_possible_horizon} מחזורים)": max_possible_horizon,
    }

    col_setup1, col_setup2, col_setup3 = st.columns([1.5, 1.5, 1])
    with col_setup1:
        st.session_state.planner_starting_fts = st.number_input(
            f"מלאי חילופים התחלתי (למחזור {next_gw}):",
            min_value=1,
            max_value=5,
            value=st.session_state.planner_starting_fts,
            step=1,
        )
    with col_setup2:
        selected_horizon_label = st.selectbox(
            "טווח מחזורים לסימולציה:",
            list(horizon_options.keys()),
            index=0,
        )
        st.session_state.planner_horizon_count = horizon_options[selected_horizon_label]
    with col_setup3:
        st.write("")
        if st.button("🗑️ אפס את כל התוכנית", use_container_width=True):
            st.session_state.planner_plan = {
                g: {"chip": "ללא צ'יפ", "transfers": []}
                for g in range(next_gw, 39)
            }
            st.session_state.planner_sell_id = None
            st.rerun()

    current_horizon_gws = [
        next_gw + i for i in range(st.session_state.planner_horizon_count) if next_gw + i <= 38
    ]

    simulated_gw_data = {}
    current_sim_squad = [dict(p) for p in st.session_state.user_squad]
    current_sim_bank = float(st.session_state.user_bank)
    current_sim_fts = int(st.session_state.planner_starting_fts)

    pre_fh_squad = None

    for idx, g in enumerate(current_horizon_gws):
        gw_plan = st.session_state.planner_plan[g]
        active_chip = gw_plan["chip"]
        planned_transfers = gw_plan["transfers"]

        if pre_fh_squad is not None:
            current_sim_squad = [dict(p) for p in pre_fh_squad]
            pre_fh_squad = None

        if idx == 0:
            available_fts = current_sim_fts
        else:
            prev_gw = g - 1
            prev_chip = st.session_state.planner_plan.get(prev_gw, {}).get("chip", "ללא צ'יפ")
            if prev_chip in ["Wildcard", "Free Hit"]:
                available_fts = 1
            else:
                prev_unused = max(
                    0,
                    simulated_gw_data[prev_gw]["available_fts"]
                    - len(st.session_state.planner_plan[prev_gw]["transfers"]),
                )
                available_fts = min(5, prev_unused + 1)

        if active_chip == "Free Hit" and pre_fh_squad is None:
            pre_fh_squad = [dict(p) for p in current_sim_squad]

        for out_id, in_id in planned_transfers:
            for sp in current_sim_squad:
                if sp["element"] == out_id:
                    p_out_cost = all_players[out_id]["cost"]
                    p_in_cost = all_players[in_id]["cost"]
                    current_sim_bank = round(
                        current_sim_bank + p_out_cost - p_in_cost, 1
                    )
                    sp["element"] = in_id
                    break

        num_transfers = len(planned_transfers)
        if active_chip in ["Wildcard", "Free Hit"]:
            hits_cost = 0
        else:
            extra_transfers = max(0, num_transfers - available_fts)
            hits_cost = extra_transfers * 4

        gw_starters = []
        gw_bench = []
        for p in current_sim_squad:
            pid = p["element"]
            p_data = all_players.get(pid)
            if p_data:
                item = {
                    **p_data,
                    "position": p["position"],
                    "is_cap": p.get("is_captain", False),
                    "is_vc": p.get("is_vice_captain", False),
                }
                if p["position"] <= 11:
                    gw_starters.append(item)
                else:
                    gw_bench.append(item)

        if active_chip == "Triple Captain":
            gw_xp = sum(
                p["xp"] * (3 if p.get("is_cap") else 1) for p in gw_starters
            )
        else:
            gw_xp = sum(
                p["xp"] * (2 if p.get("is_cap") else 1) for p in gw_starters
            )

        if active_chip == "Bench Boost":
            gw_xp += sum(p["xp"] for p in gw_bench)

        gw_xp = round(gw_xp - hits_cost, 1)

        simulated_gw_data[g] = {
            "available_fts": available_fts,
            "transfers_count": num_transfers,
            "hits_cost": hits_cost,
            "bank": current_sim_bank,
            "chip": active_chip,
            "starters": gw_starters,
            "bench": gw_bench,
            "xp": gw_xp,
            "squad_snapshot": [dict(p) for p in current_sim_squad],
        }

    # בורר מחזורים ראשי + כפתורי ניווט
    if "planner_selected_gw" not in st.session_state or st.session_state.planner_selected_gw not in current_horizon_gws:
        st.session_state.planner_selected_gw = current_horizon_gws[0]

    nav_c1, nav_c2, nav_c3 = st.columns([1, 4, 1])
    with nav_c1:
        cur_idx = current_horizon_gws.index(st.session_state.planner_selected_gw)
        if cur_idx > 0:
            if st.button("◀️ מחזור קודם", use_container_width=True):
                st.session_state.planner_selected_gw = current_horizon_gws[cur_idx - 1]
                st.session_state.planner_sell_id = None
                st.rerun()
    with nav_c3:
        if cur_idx < len(current_horizon_gws) - 1:
            if st.button("מחזור הבא ▶️", use_container_width=True):
                st.session_state.planner_selected_gw = current_horizon_gws[cur_idx + 1]
                st.session_state.planner_sell_id = None
                st.rerun()

    with nav_c2:
        selected_gw = st.selectbox(
            "בחר מחזור לתכנון ועריכה:",
            current_horizon_gws,
            index=current_horizon_gws.index(st.session_state.planner_selected_gw),
            format_func=lambda x: f"⚽ Gameweek {x} ({'מחזור נוכחי' if x == next_gw else 'עתידי'}) | FT: {simulated_gw_data[x]['available_fts']} | צ'יפ: {simulated_gw_data[x]['chip']}",
            key="planner_gw_selector_box",
        )
        if selected_gw != st.session_state.planner_selected_gw:
            st.session_state.planner_selected_gw = selected_gw
            st.session_state.planner_sell_id = None
            st.rerun()

    cur_gw_sim = simulated_gw_data[selected_gw]

    pk1, pk2, pk3, pk4, pk5 = st.columns(5)
    with pk1:
        st.metric("חילופים זמינים", f"{cur_gw_sim['available_fts']} FT")
    with pk2:
        st.metric("חילופים שתוכננו", f"{cur_gw_sim['transfers_count']}")
    with pk3:
        hit_label = (
            f"-{cur_gw_sim['hits_cost']} נק׳"
            if cur_gw_sim["hits_cost"] > 0
            else "ללא"
        )
        st.metric("קנס מינוס (Hits)", hit_label)
    with pk4:
        st.metric("יתרה בבנק", f"£{cur_gw_sim['bank']:.1f}m")
    with pk5:
        st.metric("תחזית נקודות (xP)", f"{cur_gw_sim['xp']}")

    ch_col1, ch_col2 = st.columns([1, 2])
    with ch_col1:
        current_chip_val = st.session_state.planner_plan[selected_gw]["chip"]
        chip_opts = ["ללא צ'יפ", "Wildcard", "Free Hit", "Bench Boost", "Triple Captain"]
        chosen_chip = st.selectbox(
            f"🎮 צ'יפ למחזור {selected_gw}:",
            chip_opts,
            index=chip_opts.index(current_chip_val)
            if current_chip_val in chip_opts
            else 0,
            key=f"chip_select_{selected_gw}",
        )
        if chosen_chip != current_chip_val:
            st.session_state.planner_plan[selected_gw]["chip"] = chosen_chip
            st.rerun()

    with ch_col2:
        if st.session_state.planner_plan[selected_gw]["transfers"]:
            st.markdown(f"<b>חילופים פעילים למחזור {selected_gw}:</b>", unsafe_allow_html=True)
            for idx_t, (o_id, i_id) in enumerate(st.session_state.planner_plan[selected_gw]["transfers"]):
                c_pill, c_del = st.columns([4, 1])
                with c_pill:
                    st.markdown(
                        f"""
                        <div class="badge-transfer-pill">
                            🔴 <b>{all_players[o_id]['name']}</b> ⬅️ 🟢 <b>{all_players[i_id]['name']}</b> (£{all_players[i_id]['cost']}m)
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with c_del:
                    if st.button("🗑️ בטל", key=f"del_t_{selected_gw}_{idx_t}"):
                        st.session_state.planner_plan[selected_gw]["transfers"].pop(idx_t)
                        st.rerun()

    # מגירת החלפה מהירה
    if st.session_state.planner_sell_id is not None:
        sell_pid = st.session_state.planner_sell_id
        sell_player = all_players.get(sell_pid)

        if sell_player:
            max_in_budget = round(sell_player["cost"] + cur_gw_sim["bank"], 1)
            cur_gw_all = cur_gw_sim["starters"] + cur_gw_sim["bench"]
            cur_gw_ids = [p["id"] for p in cur_gw_all]

            st.markdown(
                f"""
                <div class="planner-swap-box">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:15px; font-weight:700; color:#38bdf8;">
                            🔄 החלפת שחקן במחזור {selected_gw}: <b>{sell_player['name']}</b> ({sell_player['pos']} - {sell_player['team']})
                        </span>
                        <span style="font-size:13px; color:#cbd5e1;">
                            תקציב לרכש: <b>£{max_in_budget}m</b> (נמכר ב-£{sell_player['cost']}m + £{cur_gw_sim['bank']:.1f}m בבנק)
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            eligible = [
                p
                for p in all_players.values()
                if p["pos_code"] == sell_player["pos_code"]
                and p["id"] not in cur_gw_ids
                and p["cost"] <= max_in_budget
            ]
            ranked_pool = sorted(eligible, key=lambda x: x["score"], reverse=True)

            st.markdown("<b>⭐ 3 המלצות מובילות לרכש בלחיצה אחת:</b>", unsafe_allow_html=True)
            top_3 = ranked_pool[:3]
            if top_3:
                cols_top = st.columns(len(top_3))
                for i, cand in enumerate(top_3):
                    with cols_top[i]:
                        c_fix, c_fdr = cand.get("gw_fixtures_map", {}).get(selected_gw, ("—", 3))
                        cand_kit = get_kit(cand["team"])
                        cand_svg = render_jersey_svg(cand["team"])
                        card_rec_html = (
                            f'<div class="accessible-card" style="padding:10px; text-align:center; margin-bottom:6px; border-top:3px solid {cand_kit["primary"]};">'
                            f'{cand_svg}'
                            f'<div style="font-weight:700; color:#fff;">{cand["name"]} ({cand["team"]})</div>'
                            f'<div style="font-size:11px; color:#94a3b8;">£{cand["cost"]}m | משחק: <span class="badge-fdr fdr-{c_fdr}">{c_fix}</span></div>'
                            f'<div style="font-size:11px; color:#10b981; font-weight:700; margin-top:2px;">xP: {cand["xp"]}</div>'
                            f'</div>'
                        )
                        st.markdown(card_rec_html, unsafe_allow_html=True)
                        if st.button(f"➕ בחר ב-{cand['name']}", key=f"choose_top_{cand['id']}_{selected_gw}", use_container_width=True):
                            st.session_state.planner_plan[selected_gw]["transfers"].append((sell_pid, cand["id"]))
                            st.session_state.planner_sell_id = None
                            st.toast(f"✅ נוסף חילוף: {sell_player['name']} ⬅️ {cand['name']}", icon="✅")
                            st.rerun()

            st.write("")
            s_c1, s_c2, s_c3 = st.columns([2, 3, 1])
            with s_c1:
                search_q = st.text_input("או חפש שחקן אחר באנגלית:", placeholder="שם שחקן או קבוצה...", key="pl_search_in")
            with s_c2:
                filtered = [
                    p for p in ranked_pool
                    if not search_q or search_q.lower() in p["name"].lower() or search_q.lower() in p["team"].lower()
                ]
                if filtered:
                    chosen_manual_id = st.selectbox(
                        "בחר מהרשימה המלאה:",
                        [p["id"] for p in filtered],
                        format_func=lambda x: f"{all_players[x]['name']} ({all_players[x]['team']}) | £{all_players[x]['cost']}m | xP: {all_players[x]['xp']}",
                        key="pl_select_manual",
                    )
                else:
                    st.warning("אין תוצאות מתאימות.")
                    chosen_manual_id = None
            with s_c3:
                st.write("")
                if st.button("➕ בצע חילוף", key="btn_apply_manual", use_container_width=True):
                    if chosen_manual_id:
                        st.session_state.planner_plan[selected_gw]["transfers"].append((sell_pid, chosen_manual_id))
                        st.session_state.planner_sell_id = None
                        st.rerun()

            if st.button("✕ סגור מגירת החלפה", key="close_sell_drawer", use_container_width=True):
                st.session_state.planner_sell_id = None
                st.rerun()

    st.write("---")

    # מגרש ה-Planner בממדים מדויקים וממורכזים (800px)
    st.markdown(f"#### 🏟️ הרכב הקבוצה על המגרש ל-Gameweek {selected_gw}")
    st.caption("לחץ על כפתור **'🔄 החלף'** בראש כל שחקן כדי להחליפו באופן מיידי.")

    def render_planner_card_unit(col, p, target_gw, is_bench=False):
        with col:
            is_being_sold = (st.session_state.planner_sell_id == p["id"])
            btn_lbl = "✕ ביטול" if is_being_sold else "🔄 החלף"
            btn_kind = "primary" if is_being_sold else "secondary"

            if st.button(btn_lbl, key=f"btn_sell_{p['id']}_{target_gw}", use_container_width=True, type=btn_kind):
                if is_being_sold:
                    st.session_state.planner_sell_id = None
                else:
                    st.session_state.planner_sell_id = p["id"]
                st.rerun()

            cap_badge = "👑 " if p.get("is_cap") else ("🥈 " if p.get("is_vc") else "")
            bench_class = "card-bench" if is_bench else ""
            sel_class = "card-selected-sub" if is_being_sold else ""

            gw_map = p.get("gw_fixtures_map", {})
            if target_gw in gw_map:
                fxt_str, fdr_val = gw_map[target_gw]
            else:
                fxt_str, fdr_val = "BLANK", 3

            fxt_mini_html = '<div class="mini-fxt-container">'
            for f_gw in range(target_gw, target_gw + 3):
                if f_gw in gw_map:
                    opp_str, diff_val = gw_map[f_gw]
                    opp_short = opp_str.split(" ")[0][:3]
                    fxt_mini_html += f'<div class="mini-fxt fdr-{diff_val}">{opp_short}</div>'
                else:
                    fxt_mini_html += '<div class="mini-fxt" style="background:#334155;">BLK</div>'
            fxt_mini_html += '</div>'

            kit = get_kit(p["team"])
            kit_color = kit["primary"]
            jersey_svg = render_jersey_svg(p["team"])

            card_html = (
                f'<div class="p-card-body {bench_class} {sel_class}" style="border-top: 3px solid {kit_color} !important;">'
                f'{jersey_svg}'
                f'<div class="p-name">{cap_badge}{p["name"]}</div>'
                f'<div class="p-sub"><span class="ltr-tag">{p["team"]} | £{p["cost"]}m</span></div>'
                f'<div class="badge-fdr fdr-{fdr_val}"><span class="ltr-tag">{fxt_str}</span></div>'
                f'{fxt_mini_html}'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

    p_fwds = [p for p in cur_gw_sim["starters"] if p["pos_code"] == 4]
    p_mids = [p for p in cur_gw_sim["starters"] if p["pos_code"] == 3]
    p_defs = [p for p in cur_gw_sim["starters"] if p["pos_code"] == 2]
    p_gks = [p for p in cur_gw_sim["starters"] if p["pos_code"] == 1]

    with st.container():
        st.markdown('<div class="pitch-anchor"></div>', unsafe_allow_html=True)

        if p_fwds:
            if len(p_fwds) == 1:
                _, c_f, _ = st.columns([1, 1, 1])
                render_planner_card_unit(c_f, p_fwds[0], selected_gw)
            elif len(p_fwds) == 2:
                _, c1, c2, _ = st.columns([1, 2, 2, 1])
                render_planner_card_unit(c1, p_fwds[0], selected_gw)
                render_planner_card_unit(c2, p_fwds[1], selected_gw)
            else:
                p_fwd_cols = st.columns(len(p_fwds))
                for i, p in enumerate(p_fwds):
                    render_planner_card_unit(p_fwd_cols[i], p, selected_gw)

        st.write("")

        if p_mids:
            p_mid_cols = st.columns(len(p_mids))
            for i, p in enumerate(p_mids):
                render_planner_card_unit(p_mid_cols[i], p, selected_gw)

        st.write("")

        if p_defs:
            p_def_cols = st.columns(len(p_defs))
            for i, p in enumerate(p_defs):
                render_planner_card_unit(p_def_cols[i], p, selected_gw)

        st.write("")

        if p_gks:
            _, c_gk, _ = st.columns([2, 1, 2])
            render_planner_card_unit(c_gk, p_gks[0], selected_gw)

    with st.container():
        st.markdown('<div class="bench-anchor"></div>', unsafe_allow_html=True)
        st.caption("🪑 שחקני הספסל למחזור זה:")
        p_bench_cols = st.columns(4)
        for i, p in enumerate(cur_gw_sim["bench"]):
            render_planner_card_unit(p_bench_cols[i], p, selected_gw, is_bench=True)
