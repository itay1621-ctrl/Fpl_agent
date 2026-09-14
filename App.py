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
# 1. מילון צבעי מדים רשמיים של 20 קבוצות הפרמייר ליג ומחולל חולצות וקטורי
# =====================================================================
TEAM_KIT_COLORS = {
    "ARS": {"primary": "#EF0107", "secondary": "#FFFFFF", "text": "#FFFFFF"},
    "AVL": {"primary": "#670E36", "secondary": "#95BFE5", "text": "#FFFFFF"},
    "BOU": {"primary": "#DA291C", "secondary": "#000000", "text": "#FFFFFF"},
    "BRE": {"primary": "#D00027", "secondary": "#FFFFFF", "text": "#FFFFFF"},
    "BHA": {"primary": "#0057B8", "secondary": "#FFFFFF", "text": "#FFFFFF"},
    "CHE": {"primary": "#034694", "secondary": "#FFFFFF", "text": "#FFFFFF"},
    "CRY": {"primary": "#1B458F", "secondary": "#C4122E", "text": "#FFFFFF"},
    "EVE": {"primary": "#003399", "secondary": "#FFFFFF", "text": "#FFFFFF"},
    "FUL": {"primary": "#FFFFFF", "secondary": "#000000", "text": "#000000"},
    "IPS": {"primary": "#00448A", "secondary": "#FFFFFF", "text": "#FFFFFF"},
    "LEI": {"primary": "#003090", "secondary": "#FDBE11", "text": "#FFFFFF"},
    "LIV": {"primary": "#C8102E", "secondary": "#FFFFFF", "text": "#FFFFFF"},
    "MCI": {"primary": "#6CABDD", "secondary": "#FFFFFF", "text": "#00285E"},
    "MUN": {"primary": "#DA291C", "secondary": "#000000", "text": "#FFFFFF"},
    "NEW": {"primary": "#241F20", "secondary": "#FFFFFF", "text": "#FFFFFF"},
    "NFO": {"primary": "#DD0000", "secondary": "#FFFFFF", "text": "#FFFFFF"},
    "SOU": {"primary": "#D71920", "secondary": "#FFFFFF", "text": "#FFFFFF"},
    "TOT": {"primary": "#FFFFFF", "secondary": "#132257", "text": "#132257"},
    "WHU": {"primary": "#7A263A", "secondary": "#1BB1E7", "text": "#FFFFFF"},
    "WOL": {"primary": "#FDB913", "secondary": "#231F20", "text": "#000000"},
}

def get_jersey_svg(team_code, is_gk=False):
    if is_gk:
        c1, c2 = "#10b981", "#059669"
        stripe_defs = ""
        fill_attr = f'fill="{c1}"'
    else:
        cfg = TEAM_KIT_COLORS.get(team_code, {"primary": "#38bdf8", "secondary": "#0284c7"})
        c1 = cfg["primary"]
        c2 = cfg["secondary"]
        has_stripes = team_code in ["NEW", "BHA", "BRE", "SOU", "BOU"]
        if has_stripes:
            stripe_defs = f'<defs><pattern id="str-{team_code}" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="4" height="8" fill="{c1}"/><rect x="4" width="4" height="8" fill="{c2}"/></pattern></defs>'
            fill_attr = f'fill="url(#str-{team_code})"'
        else:
            stripe_defs = ""
            fill_attr = f'fill="{c1}"'

    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 44 40" width="30" height="26" style="display:block; margin:0 auto 2px auto; filter: drop-shadow(0 2px 3px rgba(0,0,0,0.5));">{stripe_defs}<path d="M14 4 L4 12 L9 18 L14 15 L14 36 L30 36 L30 15 L35 18 L40 12 L30 4 C27 8 17 8 14 4 Z" {fill_attr} stroke="#1e293b" stroke-width="1.2" stroke-linejoin="round"/><path d="M14 4 C17 8 27 8 30 4" fill="none" stroke="{c2}" stroke-width="2"/><path d="M4 12 L9 18 M40 12 L35 18" fill="none" stroke="{c2}" stroke-width="1.5"/></svg>'

# =====================================================================
# 2. עיצוב CSS מלא: נגישות, RTL, מגרש תחום, כפתורי אייקונים עדינים
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

/* תחום מגרש מוגבל רוחב למניעת מריחה במסכים רחבים */
div[data-testid="stVerticalBlock"]:has(.pitch-anchor) {
    max-width: 840px !important;
    margin: 0 auto 16px auto !important;
    background: radial-gradient(circle at center, #1b4d27 0%, #103819 70%, #0c2b13 100%) !important;
    border: 2px solid #285e35 !important;
    border-radius: 16px !important;
    padding: 16px 12px !important;
    box-shadow: 0 12px 30px rgba(0,0,0,0.5), inset 0 0 40px rgba(0,0,0,0.5) !important;
}

div[data-testid="stVerticalBlock"]:has(.bench-anchor) {
    max-width: 720px !important;
    margin: 0 auto 16px auto !important;
    background: rgba(15, 23, 42, 0.75) !important;
    border: 1px dashed #334155 !important;
    border-radius: 14px !important;
    padding: 14px 10px !important;
}

/* עיצוב כפתורי אייקונים בראש השחקן - מתוחם אך ורק למגרש ולספסל */
div[data-testid="stVerticalBlock"]:has(.pitch-anchor) div[data-testid="stButton"] button,
div[data-testid="stVerticalBlock"]:has(.bench-anchor) div[data-testid="stButton"] button {
    height: 26px !important;
    min-height: 26px !important;
    line-height: 1 !important;
    font-size: 13px !important;
    padding: 0 2px !important;
    border-radius: 6px !important;
    margin-bottom: 2px !important;
    background: rgba(15, 23, 42, 0.9) !important;
    border: 1px solid #334155 !important;
    color: #94a3b8 !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
}

div[data-testid="stVerticalBlock"]:has(.pitch-anchor) div[data-testid="stButton"] button:hover,
div[data-testid="stVerticalBlock"]:has(.bench-anchor) div[data-testid="stButton"] button:hover {
    background: #1e293b !important;
    border-color: #38bdf8 !important;
    color: #38bdf8 !important;
    transform: scale(1.06) !important;
}

div[data-testid="stVerticalBlock"]:has(.pitch-anchor) div[data-testid="stButton"] button[kind="primary"],
div[data-testid="stVerticalBlock"]:has(.bench-anchor) div[data-testid="stButton"] button[kind="primary"] {
    background: #ef4444 !important;
    border-color: #f87171 !important;
    color: #ffffff !important;
    font-weight: 800 !important;
}

/* כרטיס שחקן עשיר בגרפיקת חולצה ונתונים */
.p-card-fpl {
    background: rgba(17, 26, 40, 0.95);
    border: 1px solid #1e2e46;
    border-radius: 9px;
    padding: 5px 3px;
    text-align: center;
    box-shadow: 0 4px 10px rgba(0,0,0,0.4);
    transition: transform 0.2s ease, border-color 0.2s ease;
    overflow: hidden;
    position: relative;
    max-width: 130px;
    margin: 0 auto;
}
.p-card-fpl:hover {
    transform: translateY(-2px);
    border-color: #38bdf8;
}
.p-card-selected {
    border: 2px solid #38bdf8 !important;
    box-shadow: 0 0 15px rgba(56, 189, 248, 0.7) !important;
    background: rgba(20, 40, 70, 0.95) !important;
}
.p-card-transfer-selected {
    border: 2px solid #ef4444 !important;
    box-shadow: 0 0 15px rgba(239, 68, 68, 0.7) !important;
    background: rgba(50, 20, 30, 0.95) !important;
}

.cap-gold { border: 2px solid #facc15 !important; }
.card-bench { background: rgba(30, 41, 59, 0.75); border: 1px dashed #475569; }
.card-danger { border: 2px solid #f87171 !important; background: rgba(248, 113, 113, 0.15) !important; }
.card-warning { border: 2px solid #fbd38d !important; background: rgba(251, 211, 141, 0.15) !important; }

.p-name {
    font-weight: 700;
    font-size: 11px;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.p-sub {
    font-size: 9px;
    color: var(--text-muted);
    margin: 1px 0;
}

.badge-fdr {
    font-size: 8.5px;
    font-weight: 700;
    padding: 1px 4px;
    border-radius: 4px;
    display: inline-block;
}
.fdr-2 { background: #15803d; color: #fff; }
.fdr-3 { background: #475569; color: #fff; }
.fdr-4 { background: #b91c1c; color: #fff; }
.fdr-5 { background: #7f1d1d; color: #fff; }

.prob-badge {
    font-size: 8px;
    font-weight: 700;
    padding: 1px 4px;
    border-radius: 4px;
    margin: 2px auto 0 auto;
    width: fit-content;
}
.prob-red { background: rgba(248, 113, 113, 0.2); color: #fca5a5; border: 1px solid #f87171; }
.prob-yellow { background: rgba(251, 211, 141, 0.2); color: #fde68a; border: 1px solid #fbd38d; }
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
    line-height: 1; 
    text-shadow: 0 1px 1px rgba(0,0,0,0.5);
}

.transfer-drawer {
    background: #0d1726;
    border: 1px solid #38bdf8;
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.6);
}
</style>
""",
    unsafe_allow_html=True,
)

# =====================================================================
# 3. משיכת נתוני הליגה וכיול אלגוריתמי
# =====================================================================
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

    target_gws = [next_gw + i for i in range(35)]

    for el_id, el in elements.items():
        if el["status"] == "u":
            continue

        team_short = teams[el["team"]]["short_name"]
        gw_fixtures_map = {}
        upcoming = []
        fdr_list = []

        for f in fixtures:
            ev = f.get("event")
            if ev in target_gws:
                if f["team_h"] == el["team"]:
                    opp = teams[f["team_a"]]["short_name"]
                    diff = f["team_h_difficulty"]
                    gw_fixtures_map[ev] = (f"{opp} (H)", diff)
                elif f["team_a"] == el["team"]:
                    opp = teams[f["team_h"]]["short_name"]
                    diff = f["team_a_difficulty"]
                    gw_fixtures_map[ev] = (f"{opp} (A)", diff)

        for g in target_gws:
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

# =====================================================================
# 4. שער כניסה ומסך נחיתה
# =====================================================================
query_params = st.query_params
url_id = query_params.get("team", None)

if "user_team_id" not in st.session_state:
    st.session_state.user_team_id = (
        url_id.strip() if url_id and url_id.strip().isdigit() else None
    )

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
            if st.button("🚀 כניסה לסגל שלי", use_container_width=True):
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

# =====================================================================
# 5. משיכת נתוני הקבוצה מה-API
# =====================================================================
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

raw_picks, initial_bank, my_team_name, my_rank = fetch_user_team(team_id, next_gw)
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

# ניהול מצבי בחירה וחילופים
if "squad_swap_id" not in st.session_state:
    st.session_state.squad_swap_id = None

if "planner_plan" not in st.session_state:
    st.session_state.planner_plan = {
        g: {"chip": "ללא צ'יפ", "transfers": []} for g in range(next_gw, 39)
    }
if "planner_starting_fts" not in st.session_state:
    st.session_state.planner_starting_fts = 1

if "planner_swap_out" not in st.session_state:
    st.session_state.planner_swap_out = None

if "planner_transfer_out" not in st.session_state:
    st.session_state.planner_transfer_out = None

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
            "המערך הנוכחי אינו חוקי (חובה שוער 1, 3–5 מגנים, 2–5 קשרים ולפחות חלוץ 1)."
        ),
    })

squad_rating = int(max(48, min(86, base_score - total_penalty)))
rating_color = (
    "#10b981"
    if squad_rating >= 78
    else ("#38bdf8" if squad_rating >= 70 else "#f59e0b")
)

# =====================================================================
# 6. סרגל עליון ומדדים ראשיים
# =====================================================================
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

# שעון דד-ליין חי ב-HTML/JS
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
        var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        var seconds = Math.floor((distance % (1000 * 60)) / 1000);
        
        document.getElementById("fpl-clock").innerHTML = days + "d " + hours + "h " + minutes + "m " + seconds + "s";
    }}, 1000);
</script>
"""
components.html(clock_html, height=85)

# =====================================================================
# 7. פונקציות עזר לרינדור כרטיס שחקן עשיר ב-HTML
# =====================================================================
def render_player_card_html(p, is_bench=False, is_selected=False, is_transfer_selected=False, target_gw=None):
    cap_badge = "👑 " if p.get("is_cap") else ("🥈 " if p.get("is_vc") else "")
    bench_class = "card-bench" if is_bench else ""
    sel_class = "p-card-selected" if is_selected else ("p-card-transfer-selected" if is_transfer_selected else "")

    if p["chance"] <= 25 or p["status"] in ["i", "s", "u"]:
        status_class = "card-danger"
        status_pill = f'<div class="prob-badge prob-red">🔴 פצוע {p["start_prob"]}%</div>'
    elif p["chance"] <= 75 or p["status"] == "d":
        status_class = "card-warning"
        status_pill = f'<div class="prob-badge prob-yellow">🟡 בספק {p["start_prob"]}%</div>'
    else:
        status_class = "cap-gold" if p.get("is_cap") else ""
        status_pill = f'<div class="prob-badge prob-green">🟢 {p["start_prob"]}% פותח</div>'

    jersey_svg = get_jersey_svg(p["team"], is_gk=(p["pos_code"] == 1))
    club_cfg = TEAM_KIT_COLORS.get(p["team"], {"primary": "#38bdf8"})
    top_color_bar = f'<div style="height:3px; background:{club_cfg["primary"]}; border-radius:3px 3px 0 0; margin:-5px -3px 4px -3px;"></div>'

    if target_gw is not None:
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
        fixture_html = f'<div class="badge-fdr fdr-{fdr_val}"><span class="ltr-tag">{fxt_str}</span></div>{fxt_mini_html}'
    else:
        fixture_html = f'<div class="badge-fdr fdr-{p["next_fdr"]}"><span class="ltr-tag">{p["next_match"]}</span></div>'

    return (
        f'<div class="p-card-fpl {status_class} {bench_class} {sel_class}">'
        f'{top_color_bar}'
        f'{jersey_svg}'
        f'<div class="p-name">{cap_badge}{p["name"]}</div>'
        f'<div class="p-sub"><span class="ltr-tag">{p["team"]} | £{p["cost"]}m</span></div>'
        f'{fixture_html}'
        f'{status_pill}'
        f'<div style="font-size:9px; color:#38bdf8; font-weight:700; margin-top:2px;">xP: {p["xp"]}</div>'
        f'</div>'
    )

# =====================================================================
# 8. טאבים ראשיים
# =====================================================================
t_squad, t_transfers, t_analysis, t_scout, t_scenarios, t_planner = st.tabs([
    "🟢 הסגל על המגרש",
    "🔄 מעבדת חילופים",
    "📊 ניתוח וחסרונות",
    "🌟 רדאר רכש עילית",
    "🎯 3 תרחישי תקציב",
    "🗓️ מתכנן מחזורים משורשר",
])

# ---------------------------------------------------------------------
# טאב 1: מגרש חי עם כפתורי חילוף קומפקטיים (⇄) בראש השחקן
# ---------------------------------------------------------------------
with t_squad:
    st.caption(
        f"מערך: **{pos_counts[2]}-{pos_counts[3]}-{pos_counts[4]}** | סך תוחלת נקודות: **{starting_xp_total:.1f}** | "
        "לחץ על סימן החילוף **⇄** בראש שחקן להחלפה מהירה בין הרכב לספסל."
    )

    if st.session_state.squad_swap_id is not None:
        p_sel = all_players.get(st.session_state.squad_swap_id)
        if p_sel:
            c_b1, c_b2 = st.columns([3, 1])
            with c_b1:
                st.info(f"🔄 **{p_sel['name']}** סומן לחילוף. כעת לחץ על **⇄** בראש שחקן אחר כדי לבצע את ההחלפה.")
            with c_b2:
                if st.button("✕ ביטול חילוף", key="cancel_squad_swap", use_container_width=True):
                    st.session_state.squad_swap_id = None
                    st.rerun()

    def handle_squad_swap(target_id):
        if st.session_state.squad_swap_id is None:
            st.session_state.squad_swap_id = target_id
            st.rerun()
        elif st.session_state.squad_swap_id == target_id:
            st.session_state.squad_swap_id = None
            st.rerun()
        else:
            p_out_id = st.session_state.squad_swap_id
            p_in_id = target_id
            p_o = next(x for x in st.session_state.user_squad if x["element"] == p_out_id)
            p_i = next(x for x in st.session_state.user_squad if x["element"] == p_in_id)

            is_o_starter = p_o["position"] <= 11
            is_i_starter = p_i["position"] <= 11
            valid = True
            if is_o_starter != is_i_starter:
                starter_obj = all_players[p_out_id if is_o_starter else p_in_id]
                bench_obj = all_players[p_in_id if is_i_starter else p_out_id]
                curr_pos_codes = [all_players[x["element"]]["pos_code"] for x in st.session_state.user_squad if x["position"] <= 11 and x["element"] != starter_obj["id"]] + [bench_obj["pos_code"]]
                if curr_pos_codes.count(1) != 1 or not (3 <= curr_pos_codes.count(2) <= 5) or not (2 <= curr_pos_codes.count(3) <= 5) or not (1 <= curr_pos_codes.count(4) <= 3):
                    valid = False

            if not valid:
                st.error("חילוף לא חוקי! הרכב חייב לכלול שוער 1, 3-5 מגנים, 2-5 קשרים ולפחות חלוץ 1.")
            else:
                p_o["position"], p_i["position"] = p_i["position"], p_o["position"]
                st.session_state.squad_swap_id = None
                st.toast(f"✅ חילוף בוצע בהצלחה: {all_players[p_out_id]['name']} ⇄ {all_players[p_in_id]['name']}")
                st.rerun()

    # רינדור מגרש תחום
    with st.container():
        st.markdown('<div class="pitch-anchor"></div>', unsafe_allow_html=True)

        # שורת חלוצים (FWD)
        fwds = [p for p in starters if p["pos_code"] == 4]
        if fwds:
            fwd_cols = st.columns(len(fwds))
            for i, p in enumerate(fwds):
                with fwd_cols[i]:
                    is_active = (st.session_state.squad_swap_id == p["id"])
                    btn_lbl = "✕" if is_active else "⇄"
                    btn_type = "primary" if is_active else "secondary"
                    if st.button(btn_lbl, key=f"sq_btn_{p['id']}", help=f"חילוף עבור {p['name']}", type=btn_type, use_container_width=True):
                        handle_squad_swap(p["id"])
                    st.markdown(render_player_card_html(p, is_selected=is_active), unsafe_allow_html=True)

        st.write("")
        # שורת קשרים (MID)
        mids = [p for p in starters if p["pos_code"] == 3]
        if mids:
            mid_cols = st.columns(len(mids))
            for i, p in enumerate(mids):
                with mid_cols[i]:
                    is_active = (st.session_state.squad_swap_id == p["id"])
                    btn_lbl = "✕" if is_active else "⇄"
                    btn_type = "primary" if is_active else "secondary"
                    if st.button(btn_lbl, key=f"sq_btn_{p['id']}", help=f"חילוף עבור {p['name']}", type=btn_type, use_container_width=True):
                        handle_squad_swap(p["id"])
                    st.markdown(render_player_card_html(p, is_selected=is_active), unsafe_allow_html=True)

        st.write("")
        # שורת מגנים (DEF)
        defs = [p for p in starters if p["pos_code"] == 2]
        if defs:
            def_cols = st.columns(len(defs))
            for i, p in enumerate(defs):
                with def_cols[i]:
                    is_active = (st.session_state.squad_swap_id == p["id"])
                    btn_lbl = "✕" if is_active else "⇄"
                    btn_type = "primary" if is_active else "secondary"
                    if st.button(btn_lbl, key=f"sq_btn_{p['id']}", help=f"חילוף עבור {p['name']}", type=btn_type, use_container_width=True):
                        handle_squad_swap(p["id"])
                    st.markdown(render_player_card_html(p, is_selected=is_active), unsafe_allow_html=True)

        st.write("")
        # שורת שוער (GK)
        gks = [p for p in starters if p["pos_code"] == 1]
        if gks:
            gk_c = st.columns([2, 1, 2])[1]
            with gk_c:
                p = gks[0]
                is_active = (st.session_state.squad_swap_id == p["id"])
                btn_lbl = "✕" if is_active else "⇄"
                btn_type = "primary" if is_active else "secondary"
                if st.button(btn_lbl, key=f"sq_btn_{p['id']}", help=f"חילוף עבור {p['name']}", type=btn_type, use_container_width=True):
                    handle_squad_swap(p["id"])
                st.markdown(render_player_card_html(p, is_selected=is_active), unsafe_allow_html=True)

    # ספסל
    st.caption("🪑 שחקני הספסל:")
    with st.container():
        st.markdown('<div class="bench-anchor"></div>', unsafe_allow_html=True)
        bench_cols = st.columns(len(bench))
        for i, p in enumerate(bench):
            with bench_cols[i]:
                is_active = (st.session_state.squad_swap_id == p["id"])
                btn_lbl = "✕" if is_active else "⇄"
                btn_type = "primary" if is_active else "secondary"
                if st.button(btn_lbl, key=f"sq_btn_{p['id']}", help=f"חילוף עבור {p['name']}", type=btn_type, use_container_width=True):
                    handle_squad_swap(p["id"])
                st.markdown(render_player_card_html(p, is_bench=True, is_selected=is_active), unsafe_allow_html=True)

# ---------------------------------------------------------------------
# טאב 2: מעבדת חילופים (Transfers Lab)
# ---------------------------------------------------------------------
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

# ---------------------------------------------------------------------
# טאב 3: ניתוח וחסרונות (Analysis & Flaws)
# ---------------------------------------------------------------------
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

# ---------------------------------------------------------------------
# טאב 4: רדאר רכש עילית (Scout Radar)
# ---------------------------------------------------------------------
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

# ---------------------------------------------------------------------
# טאב 5: 3 תרחישי תקציב (3 Budget Scenarios)
# ---------------------------------------------------------------------
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

# ---------------------------------------------------------------------
# טאב 6: מתכנן מחזורים משורשר (Planner) - אייקונים ⇄ ו-🔄 ושוק העברות מלא
# ---------------------------------------------------------------------
with t_planner:
    st.subheader("🗓️ מתכנן מחזורים משורשר וסימולטור צ'יפים (עד מחזור 38)")
    st.caption(
        "בצע חילופי ספסל והרכב עם **⇄**, או מכור ורכוש שחקן מחוץ לסגל עם **🔄**. "
        "האלגוריתם מחשב צבירת חילופים חינמיים (עד 5), השפעת צ'יפים וקנסות נקודות."
    )

    col_setup1, col_setup2, col_setup3 = st.columns([1, 1, 1])
    with col_setup1:
        st.session_state.planner_starting_fts = st.number_input(
            f"מלאי חילופים התחלתי (למחזור {next_gw}):",
            min_value=1,
            max_value=5,
            value=st.session_state.planner_starting_fts,
            step=1,
        )
    with col_setup2:
        horizon_choice = st.selectbox(
            "טווח מחזורים לתכנון:",
            ["5 מחזורים קרובים", "8 מחזורים קרובים", "כל העונה (עד מחזור 38)"],
            index=0,
        )
        if horizon_choice == "5 מחזורים קרובים":
            max_sim_gw = min(38, next_gw + 4)
        elif horizon_choice == "8 מחזורים קרובים":
            max_sim_gw = min(38, next_gw + 7)
        else:
            max_sim_gw = 38

    with col_setup3:
        st.write("")
        if st.button("🗑️ אפס את כל תוכנית ה-Planner", use_container_width=True):
            st.session_state.planner_plan = {
                g: {"chip": "ללא צ'יפ", "transfers": []}
                for g in range(next_gw, 39)
            }
            st.session_state.planner_swap_out = None
            st.session_state.planner_transfer_out = None
            st.rerun()

    # וידוא שכל המחזורים בטווח קיימים בתוכנית
    for g in range(next_gw, max_sim_gw + 1):
        if g not in st.session_state.planner_plan:
            st.session_state.planner_plan[g] = {"chip": "ללא צ'יפ", "transfers": []}

    # חישוב סימולציה משורשרת
    simulated_gw_data = {}
    current_sim_squad = [dict(p) for p in st.session_state.user_squad]
    current_sim_bank = float(st.session_state.user_bank)
    current_sim_fts = int(st.session_state.planner_starting_fts)
    pre_fh_squad = None

    for idx, g in enumerate(range(next_gw, max_sim_gw + 1)):
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
            prev_chip = st.session_state.planner_plan[prev_gw]["chip"]
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
                    current_sim_bank = round(current_sim_bank + p_out_cost - p_in_cost, 1)
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
            gw_xp = sum(p["xp"] * (3 if p.get("is_cap") else 1) for p in gw_starters)
        else:
            gw_xp = sum(p["xp"] * (2 if p.get("is_cap") else 1) for p in gw_starters)

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

    # בורר מחזורים
    gw_options = list(range(next_gw, max_sim_gw + 1))
    selected_gw = st.radio(
        "בחר מחזור לתכנון ועריכה:",
        gw_options,
        format_func=lambda x: f"GW {x} ({'נוכחי' if x == next_gw else 'עתידי'})",
        horizontal=True,
    )

    cur_gw_sim = simulated_gw_data[selected_gw]

    # מדדי מחזור
    pk1, pk2, pk3, pk4, pk5 = st.columns(5)
    with pk1:
        st.metric("חילופים זמינים", f"{cur_gw_sim['available_fts']} FT")
    with pk2:
        st.metric("חילופים שתוכננו", f"{cur_gw_sim['transfers_count']}")
    with pk3:
        hit_label = f"-{cur_gw_sim['hits_cost']} נק׳" if cur_gw_sim["hits_cost"] > 0 else "ללא"
        st.metric("קנס מינוס (Hits)", hit_label)
    with pk4:
        st.metric("יתרה בבנק", f"£{cur_gw_sim['bank']:.1f}m")
    with pk5:
        st.metric("תחזית נקודות (xP)", f"{cur_gw_sim['xp']}")

    st.write("---")

    # ניהול צ'יפים
    c_cp1, c_cp2 = st.columns([1, 2])
    with c_cp1:
        current_chip_val = st.session_state.planner_plan[selected_gw]["chip"]
        chip_opts = ["ללא צ'יפ", "Wildcard", "Free Hit", "Bench Boost", "Triple Captain"]
        chosen_chip = st.selectbox(
            f"🎮 צ'יפ למחזור {selected_gw}:",
            chip_opts,
            index=chip_opts.index(current_chip_val) if current_chip_val in chip_opts else 0,
            key=f"chip_select_{selected_gw}",
        )
        if chosen_chip != current_chip_val:
            st.session_state.planner_plan[selected_gw]["chip"] = chosen_chip
            st.rerun()

    with c_cp2:
        if st.session_state.planner_plan[selected_gw]["transfers"]:
            st.markdown(f"**העברות שתוכננו ל-GW {selected_gw}:**")
            tr_texts = []
            for o_id, i_id in st.session_state.planner_plan[selected_gw]["transfers"]:
                tr_texts.append(f"{all_players[o_id]['name']} ⬅️ {all_players[i_id]['name']}")
            st.caption(", ".join(tr_texts))
            if st.button("🗑️ נקה העברות מחזור זה", key=f"clr_tr_{selected_gw}"):
                st.session_state.planner_plan[selected_gw]["transfers"] = []
                st.session_state.planner_transfer_out = None
                st.rerun()

    # -----------------------------------------------------------------
    # מגירת שוק העברות ייעודית (Transfer Drawer) בלחיצה על 🔄
    # -----------------------------------------------------------------
    if st.session_state.planner_transfer_out is not None:
        p_tr_out = all_players[st.session_state.planner_transfer_out]
        max_tr_budget = round(p_tr_out["cost"] + cur_gw_sim["bank"], 1)
        cur_squad_ids = [p["id"] for p in cur_gw_sim["starters"] + cur_gw_sim["bench"]]

        st.markdown(
            f"""
            <div class="transfer-drawer">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <div>
                        <span style="font-size:16px; font-weight:700; color:#38bdf8;">🛒 חלון העברות למחזור {selected_gw}</span>
                        <div style="font-size:13px; color:#cbd5e1;">
                            מכירת שחקן: <b style="color:#ef4444;">{p_tr_out['name']}</b> ({p_tr_out['pos']} - £{p_tr_out['cost']}m) | 
                            תקציב מקסימלי לרכש: <b style="color:#10b981;">£{max_tr_budget}m</b>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        b_close_col, b_sch_col = st.columns([1, 3])
        with b_close_col:
            if st.button("✕ סגור חלון העברות", key="close_tr_drawer", type="primary", use_container_width=True):
                st.session_state.planner_transfer_out = None
                st.rerun()
        with b_sch_col:
            tr_search = st.text_input("חיפוש שחקן לרכש (שם או קבוצה):", key=f"tr_search_{selected_gw}", placeholder="הקלד שם או קבוצה...").strip().lower()

        # סינון שחקנים מתאימים בעמדה
        eligible_pool = [
            p for p in all_players.values()
            if p["pos_code"] == p_tr_out["pos_code"]
            and p["id"] not in cur_squad_ids
            and p["cost"] <= max_tr_budget
            and p["status"] == "a"
        ]
        if tr_search:
            eligible_pool = [p for p in eligible_pool if tr_search in p["name"].lower() or tr_search in p["team"].lower()]

        # 1. שחקנים מומלצים תחילה (Recommended)
        recommended_picks = sorted(eligible_pool, key=lambda x: x["score"], reverse=True)[:3]

        if recommended_picks:
            st.markdown("##### ⭐ שחקנים מומלצים לרכש (Recommended):")
            rec_cols = st.columns(len(recommended_picks))
            for r_idx, r_p in enumerate(recommended_picks):
                with rec_cols[r_idx]:
                    r_jersey = get_jersey_svg(r_p["team"], is_gk=(r_p["pos_code"] == 1))
                    st.markdown(
                        f"""
                        <div class="accessible-card" style="text-align:center; padding:10px;">
                            {r_jersey}
                            <b>{r_p['name']}</b> ({r_p['team']})<br>
                            <span class="ltr-tag" style="color:#38bdf8;">£{r_p['cost']}m | xP: {r_p['xp']}</span>
                            <div style="font-size:10px; color:#cbd5e1; margin:4px 0;">{r_p['reason']}</div>
                            <div class="badge-fdr fdr-{r_p['next_fdr']}"><span class="ltr-tag">{r_p['next_match']}</span></div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button("➕ קנה שחקן זה", key=f"buy_rec_{r_p['id']}_{selected_gw}", use_container_width=True):
                        st.session_state.planner_plan[selected_gw]["transfers"].append(
                            (p_tr_out["id"], r_p["id"])
                        )
                        st.session_state.planner_transfer_out = None
                        st.toast(f"✅ נרכש בהצלחה: {r_p['name']}!")
                        st.rerun()

        st.write("")
        # 2. כל השחקנים בעמדה ממוינים לפי סך נקודות מהגבוה לנמוך
        st.markdown(f"##### 📊 כל השחקנים בעמדת {p_tr_out['pos']} (לפי נקודות מהגבוה לנמוך):")
        all_sorted_by_pts = sorted(eligible_pool, key=lambda x: x["total_points"], reverse=True)

        if all_sorted_by_pts:
            pick_opts = {p["id"]: f"{p['name']} ({p['team']}) | £{p['cost']}m | {p['total_points']} נק׳ | xP: {p['xp']} | מול: {p['next_match']}" for p in all_sorted_by_pts}
            c_sel_p, c_btn_p = st.columns([3, 1])
            with c_sel_p:
                chosen_pool_id = st.selectbox(
                    "בחר שחקן לרכש מהרשימה המלאה:",
                    list(pick_opts.keys()),
                    format_func=lambda x: pick_opts[x],
                    key=f"pool_sel_{selected_gw}",
                )
            with c_btn_p:
                st.write("")
                if st.button("➕ בצע העברה", key=f"confirm_pool_{selected_gw}", use_container_width=True):
                    st.session_state.planner_plan[selected_gw]["transfers"].append(
                        (p_tr_out["id"], chosen_pool_id)
                    )
                    st.session_state.planner_transfer_out = None
                    st.toast(f"✅ בוצעה העברה: {p_tr_out['name']} ⬅️ {all_players[chosen_pool_id]['name']}!")
                    st.rerun()
        else:
            st.warning("לא נמצאו שחקנים מתאימים במסגרת התקציב.")

    # -----------------------------------------------------------------
    # מגרש כדורגל חי למחזור הנבחר עם אייקוני ⇄ (חילוף) ו-🔄 (העברה)
    # -----------------------------------------------------------------
    st.markdown(f"#### 🏟️ הרכב הסגל על המגרש עבור Gameweek {selected_gw}")

    if st.session_state.planner_swap_out is not None:
        p_sw_name = all_players[st.session_state.planner_swap_out]["name"]
        c_sw1, c_sw2 = st.columns([3, 1])
        with c_sw1:
            st.info(f"🔄 **{p_sw_name}** סומן לחילוף הרכב/ספסל. לחץ על **⇄** בראש שחקן אחר כדי להחליף ביניהם.")
        with c_sw2:
            if st.button("✕ ביטול", key="cancel_pl_swap", use_container_width=True):
                st.session_state.planner_swap_out = None
                st.rerun()

    def handle_planner_bench_swap(target_id):
        if st.session_state.planner_swap_out is None:
            st.session_state.planner_swap_out = target_id
            st.session_state.planner_transfer_out = None
            st.rerun()
        elif st.session_state.planner_swap_out == target_id:
            st.session_state.planner_swap_out = None
            st.rerun()
        else:
            p_out_id = st.session_state.planner_swap_out
            p_in_id = target_id
            snap = cur_gw_sim["squad_snapshot"]
            p_o = next((x for x in snap if x["element"] == p_out_id), None)
            p_i = next((x for x in snap if x["element"] == p_in_id), None)
            if p_o and p_i:
                p_o["position"], p_i["position"] = p_i["position"], p_o["position"]
                # שמירה בסגל הבסיס אם זה המחזור הנוכחי
                if selected_gw == next_gw:
                    orig_o = next((x for x in st.session_state.user_squad if x["element"] == p_out_id), None)
                    orig_i = next((x for x in st.session_state.user_squad if x["element"] == p_in_id), None)
                    if orig_o and orig_i:
                        orig_o["position"], orig_i["position"] = orig_i["position"], orig_o["position"]
                st.session_state.planner_swap_out = None
                st.toast(f"✅ חילוף בוצע: {all_players[p_out_id]['name']} ⇄ {all_players[p_in_id]['name']}")
                st.rerun()

    def handle_planner_transfer_click(target_id):
        if st.session_state.planner_transfer_out == target_id:
            st.session_state.planner_transfer_out = None
        else:
            st.session_state.planner_transfer_out = target_id
            st.session_state.planner_swap_out = None
        st.rerun()

    # מגרש
    with st.container():
        st.markdown('<div class="pitch-anchor"></div>', unsafe_allow_html=True)

        # שורת חלוצים (FWD)
        pl_fwds = [p for p in cur_gw_sim["starters"] if p["pos_code"] == 4]
        if pl_fwds:
            fwd_cols = st.columns(len(pl_fwds))
            for i, p in enumerate(pl_fwds):
                with fwd_cols[i]:
                    is_sw_active = (st.session_state.planner_swap_out == p["id"])
                    is_tr_active = (st.session_state.planner_transfer_out == p["id"])
                    
                    b1, b2 = st.columns(2)
                    with b1:
                        sub_lbl = "✕" if is_sw_active else "⇄"
                        sub_type = "primary" if is_sw_active else "secondary"
                        if st.button(sub_lbl, key=f"pl_sw_{p['id']}_{selected_gw}", help=f"חילוף הרכב/ספסל עבור {p['name']}", type=sub_type, use_container_width=True):
                            handle_planner_bench_swap(p["id"])
                    with b2:
                        tr_lbl = "✕" if is_tr_active else "🔄"
                        tr_type = "primary" if is_tr_active else "secondary"
                        if st.button(tr_lbl, key=f"pl_tr_{p['id']}_{selected_gw}", help=f"העברה: מכירת {p['name']} ורכש שחקן חדש", type=tr_type, use_container_width=True):
                            handle_planner_transfer_click(p["id"])

                    st.markdown(render_player_card_html(p, is_selected=is_sw_active, is_transfer_selected=is_tr_active, target_gw=selected_gw), unsafe_allow_html=True)

        st.write("")
        # שורת קשרים (MID)
        pl_mids = [p for p in cur_gw_sim["starters"] if p["pos_code"] == 3]
        if pl_mids:
            mid_cols = st.columns(len(pl_mids))
            for i, p in enumerate(pl_mids):
                with mid_cols[i]:
                    is_sw_active = (st.session_state.planner_swap_out == p["id"])
                    is_tr_active = (st.session_state.planner_transfer_out == p["id"])
                    
                    b1, b2 = st.columns(2)
                    with b1:
                        sub_lbl = "✕" if is_sw_active else "⇄"
                        sub_type = "primary" if is_sw_active else "secondary"
                        if st.button(sub_lbl, key=f"pl_sw_{p['id']}_{selected_gw}", help=f"חילוף הרכב/ספסל עבור {p['name']}", type=sub_type, use_container_width=True):
                            handle_planner_bench_swap(p["id"])
                    with b2:
                        tr_lbl = "✕" if is_tr_active else "🔄"
                        tr_type = "primary" if is_tr_active else "secondary"
                        if st.button(tr_lbl, key=f"pl_tr_{p['id']}_{selected_gw}", help=f"העברה: מכירת {p['name']} ורכש שחקן חדש", type=tr_type, use_container_width=True):
                            handle_planner_transfer_click(p["id"])

                    st.markdown(render_player_card_html(p, is_selected=is_sw_active, is_transfer_selected=is_tr_active, target_gw=selected_gw), unsafe_allow_html=True)

        st.write("")
        # שורת מגנים (DEF)
        pl_defs = [p for p in cur_gw_sim["starters"] if p["pos_code"] == 2]
        if pl_defs:
            def_cols = st.columns(len(pl_defs))
            for i, p in enumerate(pl_defs):
                with def_cols[i]:
                    is_sw_active = (st.session_state.planner_swap_out == p["id"])
                    is_tr_active = (st.session_state.planner_transfer_out == p["id"])
                    
                    b1, b2 = st.columns(2)
                    with b1:
                        sub_lbl = "✕" if is_sw_active else "⇄"
                        sub_type = "primary" if is_sw_active else "secondary"
                        if st.button(sub_lbl, key=f"pl_sw_{p['id']}_{selected_gw}", help=f"חילוף הרכב/ספסל עבור {p['name']}", type=sub_type, use_container_width=True):
                            handle_planner_bench_swap(p["id"])
                    with b2:
                        tr_lbl = "✕" if is_tr_active else "🔄"
                        tr_type = "primary" if is_tr_active else "secondary"
                        if st.button(tr_lbl, key=f"pl_tr_{p['id']}_{selected_gw}", help=f"העברה: מכירת {p['name']} ורכש שחקן חדש", type=tr_type, use_container_width=True):
                            handle_planner_transfer_click(p["id"])

                    st.markdown(render_player_card_html(p, is_selected=is_sw_active, is_transfer_selected=is_tr_active, target_gw=selected_gw), unsafe_allow_html=True)

        st.write("")
        # שורת שוער (GK)
        pl_gks = [p for p in cur_gw_sim["starters"] if p["pos_code"] == 1]
        if pl_gks:
            gk_c = st.columns([2, 1, 2])[1]
            with gk_c:
                p = pl_gks[0]
                is_sw_active = (st.session_state.planner_swap_out == p["id"])
                is_tr_active = (st.session_state.planner_transfer_out == p["id"])
                
                b1, b2 = st.columns(2)
                with b1:
                    sub_lbl = "✕" if is_sw_active else "⇄"
                    sub_type = "primary" if is_sw_active else "secondary"
                    if st.button(sub_lbl, key=f"pl_sw_{p['id']}_{selected_gw}", help=f"חילוף הרכב/ספסל עבור {p['name']}", type=sub_type, use_container_width=True):
                        handle_planner_bench_swap(p["id"])
                with b2:
                    tr_lbl = "✕" if is_tr_active else "🔄"
                    tr_type = "primary" if is_tr_active else "secondary"
                    if st.button(tr_lbl, key=f"pl_tr_{p['id']}_{selected_gw}", help=f"העברה: מכירת {p['name']} ורכש שחקן חדש", type=tr_type, use_container_width=True):
                        handle_planner_transfer_click(p["id"])

                st.markdown(render_player_card_html(p, is_selected=is_sw_active, is_transfer_selected=is_tr_active, target_gw=selected_gw), unsafe_allow_html=True)

    # ספסל ב-Planner
    st.markdown("**🪑 שחקני ספסל:**")
    with st.container():
        st.markdown('<div class="bench-anchor"></div>', unsafe_allow_html=True)
        pl_bench_cols = st.columns(len(cur_gw_sim["bench"]))
        for i, p in enumerate(cur_gw_sim["bench"]):
            with pl_bench_cols[i]:
                is_sw_active = (st.session_state.planner_swap_out == p["id"])
                is_tr_active = (st.session_state.planner_transfer_out == p["id"])
                
                b1, b2 = st.columns(2)
                with b1:
                    sub_lbl = "✕" if is_sw_active else "⇄"
                    sub_type = "primary" if is_sw_active else "secondary"
                    if st.button(sub_lbl, key=f"pl_sw_{p['id']}_{selected_gw}", help=f"חילוף הרכב/ספסל עבור {p['name']}", type=sub_type, use_container_width=True):
                        handle_planner_bench_swap(p["id"])
                with b2:
                    tr_lbl = "✕" if is_tr_active else "🔄"
                    tr_type = "primary" if is_tr_active else "secondary"
                    if st.button(tr_lbl, key=f"pl_tr_{p['id']}_{selected_gw}", help=f"העברה: מכירת {p['name']} ורכש שחקן חדש", type=tr_type, use_container_width=True):
                        handle_planner_transfer_click(p["id"])

                st.markdown(render_player_card_html(p, is_bench=True, is_selected=is_sw_active, is_transfer_selected=is_tr_active, target_gw=selected_gw), unsafe_allow_html=True)
