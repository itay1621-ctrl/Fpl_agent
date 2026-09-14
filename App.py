import json
import time
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

st.set_page_config(
    page_title="FPL Elite Scout | מנוע החלטות ומרגל סגלים",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================================================================
# 1. תגיות PWA ומטא-דאטה מותאמות מובייל
# =====================================================================
st.markdown(
    """
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="theme-color" content="#090e17">
    """,
    unsafe_allow_html=True,
)

# =====================================================================
# 2. מילון צבעי מדים רשמיים ומחולל חולצות וקטורי
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

def render_html(html_str):
    """רינדור בטוח של HTML בסטרימליט ללא באגים של Markdown Indented Code Block"""
    compact = "".join(line.strip() for line in html_str.splitlines())
    st.markdown(compact, unsafe_allow_html=True)

def get_jersey_svg(team_code, is_gk=False):
    if is_gk:
        c1, c2 = "#10b981", "#059669"
        stripe_defs = ""
        fill_attr = f'fill="{c1}"'
    else:
        cfg = TEAM_KIT_COLORS.get(team_code, {"primary": "#38bdf8", "secondary": "#0284c7"})
        c1 = cfg["primary"]
        c2 = cfg["secondary"]
        if team_code in ["NEW", "BHA", "BRE", "SOU", "BOU", "CRY"]:
            stripe_defs = f'<defs><pattern id="str-{team_code}" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="4" height="8" fill="{c1}"/><rect x="4" width="4" height="8" fill="{c2}"/></pattern></defs>'
            fill_attr = f'fill="url(#str-{team_code})"'
        else:
            stripe_defs = ""
            fill_attr = f'fill="{c1}"'

    return f'<div style="display:flex;justify-content:center;align-items:center;margin:1px 0;"><svg width="34" height="30" viewBox="0 0 46 42" fill="none" xmlns="http://www.w3.org/2000/svg">{stripe_defs}<path d="M14 6L5 13L10 20L14 17V38H32V17L36 20L41 13L32 6C30 9 27 10 23 10C19 10 16 9 14 6Z" {fill_attr} stroke="#0f172a" stroke-width="1.5" stroke-linejoin="round"/><path d="M14 6C16 9 19 10 23 10C27 10 30 9 32 6C30 4 27 3 23 3C19 3 16 4 14 6Z" fill="{c2}" stroke="#0f172a" stroke-width="1.2"/><path d="M10 20L5 13L9 10" stroke="{c2}" stroke-width="1.5" stroke-linecap="round"/><path d="M36 20L41 13L37 10" stroke="{c2}" stroke-width="1.5" stroke-linecap="round"/></svg></div>'

# =====================================================================
# 3. עיצוב CSS מלא: נגישות, RTL, רספונסיביות מובייל וכפתורי מיקרו
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
    color: var(--text-primary);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
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
    padding: 24px 18px;
    margin: 16px auto;
    max-width: 560px;
    text-align: center;
    box-shadow: 0 10px 25px rgba(0,0,0,0.4);
}

.kpi-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 8px;
    margin-bottom: 14px;
}
.kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 10px 8px;
    text-align: center;
}
.kpi-title {
    font-size: 11px;
    color: var(--text-muted);
    margin-bottom: 4px;
}
.kpi-value {
    font-size: 18px;
    font-weight: 700;
    color: var(--text-primary);
}

/* מגרש תחום ורספונסיבי */
div[data-testid="stVerticalBlock"]:has(.pitch-anchor) {
    max-width: 820px !important;
    margin: 0 auto 10px auto !important;
    background: radial-gradient(circle at center, #1b4d27 0%, #103819 70%, #0c2b13 100%) !important;
    border: 2px solid #285e35 !important;
    border-radius: 14px !important;
    padding: 14px 8px !important;
    box-shadow: 0 12px 30px rgba(0,0,0,0.5), inset 0 0 40px rgba(0,0,0,0.5) !important;
}

div[data-testid="stVerticalBlock"]:has(.bench-anchor) {
    max-width: 720px !important;
    margin: 10px auto 16px auto !important;
    background: rgba(15, 23, 42, 0.75) !important;
    border: 1px dashed #334155 !important;
    border-radius: 12px !important;
    padding: 10px 8px !important;
}

/* שורת פעולות וחילוף מתחת למגרש */
.action-bar-under-pitch {
    background: linear-gradient(135deg, #111a28 0%, #18283f 100%);
    border: 1px solid #38bdf8;
    border-radius: 12px;
    padding: 12px 14px;
    margin: 10px auto 14px auto;
    max-width: 820px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.55);
    direction: rtl;
}

/* כפתורי פעולה בודדים ונוחים במגרש ובספסל */
div[data-testid="stVerticalBlock"]:has(.pitch-anchor) div[data-testid="stButton"] button,
div[data-testid="stVerticalBlock"]:has(.bench-anchor) div[data-testid="stButton"] button {
    height: 26px !important;
    min-height: 26px !important;
    line-height: 1 !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    padding: 0 4px !important;
    border-radius: 5px !important;
    margin: 3px auto 0 auto !important;
    background: rgba(15, 23, 42, 0.92) !important;
    border: 1px solid #334155 !important;
    color: #cbd5e1 !important;
    width: 100% !important;
    transition: all 0.15s ease !important;
}

div[data-testid="stVerticalBlock"]:has(.pitch-anchor) div[data-testid="stButton"] button:hover,
div[data-testid="stVerticalBlock"]:has(.bench-anchor) div[data-testid="stButton"] button:hover {
    background: #1e293b !important;
    border-color: #38bdf8 !important;
    color: #38bdf8 !important;
}

div[data-testid="stVerticalBlock"]:has(.pitch-anchor) div[data-testid="stButton"] button[kind="primary"],
div[data-testid="stVerticalBlock"]:has(.bench-anchor) div[data-testid="stButton"] button[kind="primary"] {
    background: #38bdf8 !important;
    border-color: #7dd3fc !important;
    color: #090e17 !important;
    font-weight: 800 !important;
}

/* כרטיס שחקן במגרש */
.p-card-fpl {
    background: rgba(17, 26, 40, 0.95);
    border: 1px solid #1e2e46;
    border-radius: 8px;
    padding: 5px 3px;
    text-align: center;
    box-shadow: 0 4px 8px rgba(0,0,0,0.4);
    transition: transform 0.15s ease, border-color 0.15s ease;
    overflow: hidden;
    position: relative;
    max-width: 120px;
    margin: 0 auto;
}
.p-card-fpl:hover {
    transform: translateY(-2px);
    border-color: #38bdf8;
}
.p-card-selected {
    border: 2px solid #38bdf8 !important;
    box-shadow: 0 0 14px rgba(56, 189, 248, 0.8) !important;
    background: rgba(20, 45, 75, 0.98) !important;
}
.p-card-transfer-selected {
    border: 2px solid #ef4444 !important;
    box-shadow: 0 0 14px rgba(239, 68, 68, 0.8) !important;
    background: rgba(55, 20, 30, 0.98) !important;
}

.cap-gold { border: 2px solid #facc15 !important; }
.vc-silver { border: 2px solid #94a3b8 !important; }
.card-bench { background: rgba(30, 41, 59, 0.75); border: 1px dashed #475569; }
.card-danger { border: 2px solid #f87171 !important; background: rgba(248, 113, 113, 0.15) !important; }
.card-warning { border: 2px solid #fbd38d !important; background: rgba(251, 211, 141, 0.15) !important; }

/* תגיות C ו-VC רשמיות */
.badge-c {
    background: #facc15;
    color: #000000;
    font-weight: 900;
    font-size: 10px;
    line-height: 1;
    padding: 2px 5px;
    border-radius: 4px;
    margin-left: 3px;
    display: inline-block;
    box-shadow: 0 1px 3px rgba(0,0,0,0.5);
    vertical-align: middle;
}

.badge-vc {
    background: #94a3b8;
    color: #000000;
    font-weight: 900;
    font-size: 10px;
    line-height: 1;
    padding: 2px 4px;
    border-radius: 4px;
    margin-left: 3px;
    display: inline-block;
    box-shadow: 0 1px 3px rgba(0,0,0,0.5);
    vertical-align: middle;
}

.p-name {
    font-weight: 700;
    font-size: 10.5px;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 2px;
}
.p-sub {
    font-size: 8.5px;
    color: var(--text-muted);
    margin: 1px 0;
}

.badge-fdr {
    font-size: 8px;
    font-weight: 700;
    padding: 1px 4px;
    border-radius: 3px;
    display: inline-block;
}
.fdr-2 { background: #15803d; color: #fff; }
.fdr-3 { background: #475569; color: #fff; }
.fdr-4 { background: #b91c1c; color: #fff; }
.fdr-5 { background: #7f1d1d; color: #fff; }

.prob-badge {
    font-size: 7.5px;
    font-weight: 700;
    padding: 1px 3px;
    border-radius: 3px;
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
    padding: 12px 14px;
    margin-bottom: 10px;
}
.accessible-card:hover {
    background: var(--bg-card-hover);
}
.split-box {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #1e293b;
    padding-bottom: 6px;
    margin-bottom: 8px;
}
.meta-chip {
    font-size: 11px;
    background: #1e293b;
    color: var(--text-muted);
    padding: 2px 7px;
    border-radius: 5px;
}

.flaw-row {
    background: #1c1518;
    border-right: 4px solid var(--accent-red);
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 6px;
    font-size: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.flaw-pen {
    background: #7f1d1d;
    color: #fecaca;
    padding: 2px 5px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 10.5px;
}

.mini-fxt-container { 
    display: flex; 
    justify-content: center; 
    gap: 2px; 
    margin-top: 3px; 
}
.mini-fxt { 
    font-size: 7.5px; 
    font-weight: 800; 
    text-transform: uppercase; 
    padding: 1px 2px; 
    border-radius: 2px; 
    color: white; 
    line-height: 1; 
    text-shadow: 0 1px 1px rgba(0,0,0,0.5);
}

.transfer-drawer {
    background: #0d1726;
    border: 1px solid #38bdf8;
    border-radius: 12px;
    padding: 14px;
    margin: 10px auto 16px auto;
    max-width: 820px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.6);
}

/* התאמות מובייל קפדניות (Mobile Media Queries) */
@media (max-width: 640px) {
    div[data-testid="stVerticalBlock"]:has(.pitch-anchor) {
        padding: 6px 2px !important;
        border-radius: 8px !important;
    }
    div[data-testid="column"] {
        padding: 0 1px !important;
        min-width: 0 !important;
    }
    .p-card-fpl {
        padding: 3px 1px !important;
        border-radius: 6px !important;
        max-width: 78px !important;
    }
    .p-name {
        font-size: 8.5px !important;
    }
    .p-sub, .badge-fdr, .mini-fxt {
        font-size: 7px !important;
    }
    .badge-c, .badge-vc {
        font-size: 8px !important;
        padding: 1px 3px !important;
    }
    div[data-testid="stVerticalBlock"]:has(.pitch-anchor) div[data-testid="stButton"] button,
    div[data-testid="stVerticalBlock"]:has(.bench-anchor) div[data-testid="stButton"] button {
        height: 24px !important;
        min-height: 24px !important;
        font-size: 10px !important;
        padding: 0 1px !important;
    }
    .kpi-container {
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 6px !important;
    }
    .kpi-card {
        padding: 6px 4px !important;
    }
    .kpi-title {
        font-size: 10px !important;
    }
    .kpi-value {
        font-size: 15px !important;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

# =====================================================================
# 4. משיכת נתוני הליגה והגנת API מבוססת כותרות
# =====================================================================
API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

@st.cache_data(ttl=600)
def fetch_league_data():
    base = "https://fantasy.premierleague.com/api/"
    r_boot = requests.get(base + "bootstrap-static/", headers=API_HEADERS, timeout=15)
    if r_boot.status_code != 200:
        return None, None
    boot = r_boot.json()
    r_fix = requests.get(base + "fixtures/", headers=API_HEADERS, timeout=15)
    fix = r_fix.json() if r_fix.status_code == 200 else []
    return boot, fix

boot_data, fixtures_data = fetch_league_data()
if not boot_data:
    st.error("שגיאה במשיכת נתוני הליגה הרשמיים. אנא רענן את הדף בעוד מספר שניות.")
    st.stop()

# =====================================================================
# 5. ניהול סשן ו-Login Gate
# =====================================================================
if "active_team_id" not in st.session_state:
    st.session_state.active_team_id = None
if "user_squad" not in st.session_state:
    st.session_state.user_squad = None
if "user_bank" not in st.session_state:
    st.session_state.user_bank = 0.0
if "transfers_log" not in st.session_state:
    st.session_state.transfers_log = []

# מסך כניסה
if not st.session_state.active_team_id:
    st.markdown(
        """
        <div class="gate-card">
            <h2 style="color:#38bdf8; margin-bottom:6px;">⚽ FPL Elite Scout</h2>
            <p style="color:#94a3b8; font-size:14px; margin-bottom:14px;">
                מערכת קבלת החלטות מסחרית לקראת מחזורי הפרמיירליג: מגרש חי עם תגיות C/VC, סימולטור צ'יפים והעברות, ומנוע ריגול למיני-ליגות.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_g1, col_g2, col_g3 = st.columns([1, 1.2, 1])
    with col_g2:
        in_team = st.text_input(
            "הזן FPL Team ID:",
            value="10469619",
            help="מזהה הקבוצה הרשמי מתוך ה-URL באתר ה-FPL הרשמי",
        )
        if st.button("🚀 טען סגל ופתח מערכת", use_container_width=True, type="primary"):
            clean_id = in_team.strip()
            if clean_id.isdigit():
                st.session_state.active_team_id = clean_id
                st.rerun()
            else:
                st.error("אנא הזן מספר מזהה תקין.")
    st.stop()

team_id = st.session_state.active_team_id

# =====================================================================
# 6. משיכת נתוני הקבוצה הספציפית
# =====================================================================
events = boot_data.get("events", [])
next_gw = 1
for ev in events:
    if ev.get("is_next"):
        next_gw = ev.get("id", 1)
        break
else:
    for ev in events:
        if ev.get("is_current"):
            next_gw = min(38, ev.get("id", 1) + 1)
            break

target_history_gw = max(1, next_gw - 1)

@st.cache_data(ttl=300)
def fetch_user_team(t_id, gw):
    try:
        url_picks = f"https://fantasy.premierleague.com/api/entry/{t_id}/event/{gw}/picks/"
        r_p = requests.get(url_picks, headers=API_HEADERS, timeout=12)
        url_entry = f"https://fantasy.premierleague.com/api/entry/{t_id}/"
        r_e = requests.get(url_entry, headers=API_HEADERS, timeout=12)
        if r_p.status_code != 200:
            return None, None
        return r_p.json(), (r_e.json() if r_e.status_code == 200 else {})
    except Exception:
        return None, None

user_picks_data, user_entry_data = fetch_user_team(team_id, target_history_gw)
if not user_picks_data or "picks" not in user_picks_data:
    st.error(f"לא ניתן למשוך את נתוני קבוצה {team_id} למחזור {target_history_gw}.")
    if st.button("החלף Team ID ↩️"):
        st.session_state.active_team_id = None
        st.rerun()
    st.stop()

raw_picks = user_picks_data["picks"]
initial_bank = user_picks_data.get("entry_history", {}).get("bank", 0) / 10.0

if st.session_state.user_squad is None:
    st.session_state.user_squad = [dict(p) for p in raw_picks]
    st.session_state.user_bank = initial_bank

# =====================================================================
# 7. עיבוד מודל השחקנים ולוח המשחקים
# =====================================================================
teams_dict = {t["id"]: t for t in boot_data.get("teams", [])}
elements_list = boot_data.get("elements", [])
element_types = {et["id"]: et["singular_name_short"] for et in boot_data.get("element_types", [])}

team_fixtures = {t_id: [] for t_id in teams_dict}
for f in fixtures_data:
    event = f.get("event")
    if event and event >= next_gw:
        t_h, t_a = f["team_h"], f["team_a"]
        diff_h = f.get("team_h_difficulty", 3)
        diff_a = f.get("team_a_difficulty", 3)
        opp_a = teams_dict.get(t_a, {}).get("short_name", "OPP")
        opp_h = teams_dict.get(t_h, {}).get("short_name", "OPP")
        team_fixtures[t_h].append({
            "gw": event,
            "match": f"{opp_a} (H)",
            "fdr": diff_h,
            "is_home": True,
        })
        team_fixtures[t_a].append({
            "gw": event,
            "match": f"{opp_h} (A)",
            "fdr": diff_a,
            "is_home": False,
        })

elite_defenses = ["ARS", "MCI", "LIV"]
all_players = {}

for el in elements_list:
    pid = el["id"]
    t_id = el["team"]
    team_obj = teams_dict.get(t_id, {})
    team_short = team_obj.get("short_name", "UNK")
    f_list = sorted(team_fixtures.get(t_id, []), key=lambda x: x["gw"])

    upcoming = []
    fdr_list = []
    gw_fixtures_map = {}
    for g in range(next_gw, next_gw + 10):
        m_gw = [x for x in f_list if x["gw"] == g]
        if m_gw:
            m_strs = [m["match"] for m in m_gw]
            max_fdr = max(m["fdr"] for m in m_gw)
            upcoming.append(" & ".join(m_strs))
            fdr_list.append(max_fdr)
            gw_fixtures_map[g] = (" & ".join(m_strs), max_fdr)
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
            "יוצר מצבים מרכזי ומעורב בשערים."
            if xgi_p90 >= 0.45
            else "שחקן הרכב סדיר עם משחק נוח."
        )

    all_players[pid] = {
        "id": pid,
        "name": el["web_name"],
        "team": team_short,
        "pos": element_types.get(el["element_type"], ""),
        "pos_code": el["element_type"],
        "cost": cost,
        "score": round(score, 2),
        "xp": pred_xp,
        "chance": chance,
        "start_prob": start_prob,
        "status": status,
        "news": el.get("news", ""),
        "next_match": upcoming[0] if upcoming else "None",
        "next_fdr": next_fdr,
        "avg_fdr": round(avg_fdr, 2),
        "tag": tag_status,
        "reason": reason,
        "total_points": el.get("total_points", 0),
        "selected_by": float(el.get("selected_by_percent", 0.0)),
        "form": form,
        "gw_fixtures_map": gw_fixtures_map,
    }

# =====================================================================
# 8. ניהול סגל, חילופי מגרש והתקנה ראשונית
# =====================================================================
if "squad_swap_id" not in st.session_state:
    st.session_state.squad_swap_id = None

if "planner_plan" not in st.session_state:
    st.session_state.planner_plan = {
        g: {"chip": "ללא צ'יפ", "transfers": []} for g in range(next_gw, 39)
    }
if "planner_captains" not in st.session_state:
    st.session_state.planner_captains = {}

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
            "type": "התקפה קרה",
            "penalty": f"-{pen:.1f}",
            "text": (
                f"<b>{p['name']}</b> בכושר ירוד (Form {p['form']}) ללא שער/בישול"
                " לאחרונה."
            ),
        })

squad_rating = int(round(max(30.0, min(99.0, base_score - total_penalty))))
rating_color = (
    "#10b981"
    if squad_rating >= 80
    else ("#facc15" if squad_rating >= 65 else "#ef4444")
)

# Header עליון ומדדי KPI
st.markdown(
    f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; flex-wrap:wrap; gap:10px;">
        <div>
            <h2 style="margin:0; color:#38bdf8;">⚽ FPL Elite Scout</h2>
            <div style="font-size:12px; color:#94a3b8;">
                קבוצה: <b>{user_entry_data.get('name', team_id)}</b> | 
                מאמן: <b>{user_entry_data.get('player_first_name', '')} {user_entry_data.get('player_last_name', '')}</b> | 
                מחזור קרוב: <b>GW {next_gw}</b>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

c_ch1, c_ch2 = st.columns([4, 1])
with c_ch2:
    if st.button("החלף קבוצה 🔁", use_container_width=True):
        st.session_state.active_team_id = None
        st.session_state.user_squad = None
        st.session_state.transfers_log = []
        st.session_state.planner_swap_out = None
        st.session_state.planner_transfer_out = None
        st.rerun()

st.markdown(
    f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-title">ציון סגל מכויל</div>
            <div class="kpi-value" style="color:{rating_color};">{squad_rating} <span style="font-size:12px; color:#64748b;">/100</span></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">תוחלת הרכב (xP)</div>
            <div class="kpi-value" style="color:#38bdf8;">{starting_xp_total:.1f}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">יתרה בבנק</div>
            <div class="kpi-value" style="color:#10b981;">£{st.session_state.user_bank:.1f}m</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">מערך הרכב</div>
            <div class="kpi-value">{pos_counts[2]}-{pos_counts[3]}-{pos_counts[4]}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# פונקציית רינדור כרטיס שחקן נקייה ואטומה לבאגי Markdown
def render_player_card_html(p, is_bench=False, is_selected=False, is_transfer_selected=False, target_gw=None, custom_cap=None, custom_vc=None):
    is_c = custom_cap if custom_cap is not None else p.get("is_cap", False)
    is_v = custom_vc if custom_vc is not None else p.get("is_vc", False)

    cap_badge = '<span class="badge-c">C</span>' if is_c else ('<span class="badge-vc">VC</span>' if is_v else "")
    bench_class = "card-bench" if is_bench else ""
    sel_class = "p-card-selected" if is_selected else ("p-card-transfer-selected" if is_transfer_selected else "")

    if p["chance"] <= 25 or p["status"] in ["i", "s", "u"]:
        status_class = "card-danger"
        status_pill = f'<div class="prob-badge prob-red">🔴 פצוע {p["start_prob"]}%</div>'
    elif p["chance"] <= 75 or p["status"] == "d":
        status_class = "card-warning"
        status_pill = f'<div class="prob-badge prob-yellow">🟡 בספק {p["start_prob"]}%</div>'
    else:
        status_class = "cap-gold" if is_c else ("vc-silver" if is_v else "")
        status_pill = f'<div class="prob-badge prob-green">🟢 {p["start_prob"]}% פותח</div>'

    jersey_svg = get_jersey_svg(p["team"], is_gk=(p["pos_code"] == 1))
    club_cfg = TEAM_KIT_COLORS.get(p["team"], {"primary": "#38bdf8"})
    top_color_bar = f'<div style="height:3px;background:{club_cfg["primary"]};border-radius:3px 3px 0 0;margin:-5px -3px 3px -3px;"></div>'

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

    xp_mult = 2 if is_c else 1
    xp_val = round(p["xp"] * xp_mult, 1)

    card_html = (
        f'<div class="p-card-fpl {status_class} {bench_class} {sel_class}">'
        f'{top_color_bar}'
        f'{jersey_svg}'
        f'<div class="p-name">{cap_badge}{p["name"]}</div>'
        f'<div class="p-sub"><span class="ltr-tag">{p["team"]} | £{p["cost"]}m</span></div>'
        f'{fixture_html}'
        f'{status_pill}'
        f'<div style="font-size:9px; color:#38bdf8; font-weight:700; margin-top:2px;">xP: {xp_val}</div>'
        f'</div>'
    )
    return "".join(line.strip() for line in card_html.splitlines())

# =====================================================================
# 9. שבעת הטאבים המרכזיים
# =====================================================================
t_squad, t_transfers, t_analysis, t_scout, t_scenarios, t_planner, t_leagues = st.tabs([
    "🟢 הסגל על המגרש",
    "🔄 מעבדת חילופים",
    "📊 ניתוח וחסרונות",
    "🌟 רדאר רכש עילית",
    "🎯 3 תרחישי תקציב",
    "🗓️ מתכנן מחזורים משורשר",
    "🏆 מרגל מיני-ליגות",
])

# ---------------------------------------------------------------------
# טאב 1: מגרש חי עם סימוני C ו-VC רשמיים, ושורת חילוף מתחת למגרש
# ---------------------------------------------------------------------
with t_squad:
    st.caption(
        f"מערך: **{pos_counts[2]}-{pos_counts[3]}-{pos_counts[4]}** | סך תוחלת נקודות: **{starting_xp_total:.1f}** | "
        "לחץ על שחקן כדי לפתוח את **שורת החילוף והניהול מתחת למגרש** לבחירת קפטן (C), סגן (VC) או ביצוע חילוף."
    )

    def execute_squad_swap(p_out_id, p_in_id):
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
            st.toast(f"✅ חילוף בוצע: {all_players[p_out_id]['name']} ⇄ {all_players[p_in_id]['name']}")
            st.rerun()

    def handle_squad_card_click(target_id):
        if st.session_state.squad_swap_id is None:
            st.session_state.squad_swap_id = target_id
            st.rerun()
        elif st.session_state.squad_swap_id == target_id:
            st.session_state.squad_swap_id = None
            st.rerun()
        else:
            execute_squad_swap(st.session_state.squad_swap_id, target_id)

    def set_squad_captain(target_id):
        for sp in st.session_state.user_squad:
            sp["is_captain"] = (sp["element"] == target_id)
            if sp["is_captain"]:
                sp["is_vice_captain"] = False
        st.session_state.squad_swap_id = None
        st.toast(f"👑 {all_players[target_id]['name']} נבחר לקפטן (C)!")
        st.rerun()

    def set_squad_vice_captain(target_id):
        for sp in st.session_state.user_squad:
            sp["is_vice_captain"] = (sp["element"] == target_id)
            if sp["is_vice_captain"]:
                sp["is_captain"] = False
        st.session_state.squad_swap_id = None
        st.toast(f"🥈 {all_players[target_id]['name']} נבחר לסגן קפטן (VC)!")
        st.rerun()

    # רינדור שורת מגרש נקייה
    def render_clean_squad_row(player_list):
        if not player_list:
            return
        cols = st.columns(len(player_list))
        for i, p in enumerate(player_list):
            with cols[i]:
                is_active = (st.session_state.squad_swap_id == p["id"])
                st.markdown(render_player_card_html(p, is_selected=is_active), unsafe_allow_html=True)
                
                # כפתור בחירה יחיד וקומפקטי
                btn_lbl = "✓ נבחר" if is_active else ("C" if p.get("is_cap") else ("VC" if p.get("is_vc") else "בחר"))
                btn_type = "primary" if is_active else "secondary"
                if st.button(btn_lbl, key=f"sq_pick_{p['id']}", use_container_width=True, type=btn_type):
                    handle_squad_card_click(p["id"])

    # המגרש הראשי
    with st.container():
        st.markdown('<div class="pitch-anchor"></div>', unsafe_allow_html=True)
        # חלוצים
        render_clean_squad_row([p for p in starters if p["pos_code"] == 4])
        st.write("")
        # קשרים
        render_clean_squad_row([p for p in starters if p["pos_code"] == 3])
        st.write("")
        # מגנים
        render_clean_squad_row([p for p in starters if p["pos_code"] == 2])
        st.write("")
        # שוער
        gks = [p for p in starters if p["pos_code"] == 1]
        if gks:
            gk_col = st.columns([2, 1, 2])[1]
            with gk_col:
                p = gks[0]
                is_active = (st.session_state.squad_swap_id == p["id"])
                st.markdown(render_player_card_html(p, is_selected=is_active), unsafe_allow_html=True)
                btn_lbl = "✓ נבחר" if is_active else ("C" if p.get("is_cap") else ("VC" if p.get("is_vc") else "בחר"))
                btn_type = "primary" if is_active else "secondary"
                if st.button(btn_lbl, key=f"sq_pick_{p['id']}", use_container_width=True, type=btn_type):
                    handle_squad_card_click(p["id"])

    # -----------------------------------------------------------------
    # שורת החילוף והניהול - ממוקמת בלעדית מתחת למגרש!
    # -----------------------------------------------------------------
    if st.session_state.squad_swap_id is not None:
        p_sel = all_players.get(st.session_state.squad_swap_id)
        if p_sel:
            is_starter = any(p["element"] == p_sel["id"] for p in starters)
            render_html(
                f"""
                <div class="action-bar-under-pitch">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
                        <div>
                            <span style="font-size:14px; font-weight:700; color:#38bdf8;">⚙️ שורת חילוף וניהול:</span>
                            <b style="color:#ffffff; margin-right:6px; font-size:14px;">{p_sel['name']}</b>
                            <span class="ltr-tag" style="color:#94a3b8; font-size:12px;">({p_sel['team']} | {p_sel['pos']} | £{p_sel['cost']}m | xP: {p_sel['xp']})</span>
                        </div>
                        <div style="font-size:11px; color:#cbd5e1;">
                            {'לחץ על שחקן נוסף להחלפה, או בחר פעולה:' if is_starter else 'לחץ על שחקן הרכב להחלפה ביניהם:'}
                        </div>
                    </div>
                </div>
                """
            )

            col_a1, col_a2, col_a3, col_a4 = st.columns([1.2, 1.2, 2.5, 1])
            with col_a1:
                if is_starter:
                    if st.button("🅲 קפטן (C)", key="bar_cap_btn", use_container_width=True, type="primary"):
                        set_squad_captain(p_sel["id"])
                else:
                    st.button("🅲 רק להרכב", disabled=True, use_container_width=True)
            with col_a2:
                if is_starter:
                    if st.button("🆅 סגן (VC)", key="bar_vc_btn", use_container_width=True):
                        set_squad_vice_captain(p_sel["id"])
                else:
                    st.button("🆅 רק להרכב", disabled=True, use_container_width=True)
            with col_a3:
                eligible_targets = bench if is_starter else starters
                swap_dict = {p["id"]: f"{p['name']} ({p['pos']} - {p['team']}) | xP: {p['xp']}" for p in eligible_targets}
                chosen_target_id = st.selectbox("בחר יעד לחילוף:", list(swap_dict.keys()), format_func=lambda x: swap_dict[x], key="action_bar_swap_sel", label_visibility="collapsed")
                if st.button("בצע חילוף ⇄", key="exec_bar_swap", use_container_width=True):
                    execute_squad_swap(p_sel["id"], chosen_target_id)
            with col_a4:
                if st.button("✕ ביטול", key="bar_cancel_btn", use_container_width=True):
                    st.session_state.squad_swap_id = None
                    st.rerun()

    # ספסל נקי ומרווח מתחת למגרש
    st.markdown("**🪑 שחקני הספסל:**")
    with st.container():
        st.markdown('<div class="bench-anchor"></div>', unsafe_allow_html=True)
        bench_cols = st.columns(len(bench))
        for i, p in enumerate(bench):
            with bench_cols[i]:
                is_active = (st.session_state.squad_swap_id == p["id"])
                st.markdown(render_player_card_html(p, is_bench=True, is_selected=is_active), unsafe_allow_html=True)
                btn_lbl = "✓ נבחר" if is_active else "בחר לחילוף"
                btn_type = "primary" if is_active else "secondary"
                if st.button(btn_lbl, key=f"sq_bench_{p['id']}", use_container_width=True, type=btn_type):
                    handle_squad_card_click(p["id"])

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
            "שחקן": f"{p['name']} {'👑' if p.get('is_cap') else ('🥈' if p.get('is_vc') else '')}",
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
# טאב 6: מתכנן מחזורים משורשר (Planner) - אייקונים, שוק, ייצוא ושמירה
# ---------------------------------------------------------------------
with t_planner:
    st.subheader("🗓️ מתכנן מחזורים משורשר וסימולטור צ'יפים (עד מחזור 38)")
    st.caption(
        "בצע חילופי ספסל והרכב עם **⇄**, מכור ורכוש שחקן עם **🔄**, ובחר קפטן פר מחזור. "
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
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            if st.button("🗑️ איפוס תוכנית", use_container_width=True):
                st.session_state.planner_plan = {
                    g: {"chip": "ללא צ'יפ", "transfers": []}
                    for g in range(next_gw, 39)
                }
                st.session_state.planner_captains = {}
                st.session_state.planner_swap_out = None
                st.session_state.planner_transfer_out = None
                st.rerun()
        with col_res2:
            # ייצוא תוכנית כ-JSON
            plan_export_data = {
                "team_id": team_id,
                "exported_at": datetime.now().isoformat(),
                "plan": st.session_state.planner_plan,
                "captains": st.session_state.planner_captains,
            }
            st.download_button(
                "💾 ייצוא תוכנית",
                data=json.dumps(plan_export_data, indent=2, ensure_ascii=False),
                file_name=f"fpl_plan_team_{team_id}.json",
                mime="application/json",
                use_container_width=True,
            )

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

        # קפטן מותאם אישית למחזור
        gw_cap_dict = st.session_state.planner_captains.get(g, {})
        custom_cap_id = gw_cap_dict.get("cap")
        custom_vc_id = gw_cap_dict.get("vc")

        gw_starters = []
        gw_bench = []
        for p in current_sim_squad:
            pid = p["element"]
            p_data = all_players.get(pid)
            if p_data:
                is_c = (pid == custom_cap_id) if custom_cap_id else p.get("is_captain", False)
                is_v = (pid == custom_vc_id) if custom_vc_id else p.get("is_vice_captain", False)
                item = {
                    **p_data,
                    "position": p["position"],
                    "is_cap": is_c,
                    "is_vc": is_v,
                }
                if p["position"] <= 11:
                    gw_starters.append(item)
                else:
                    gw_bench.append(item)

        cap_mult = 3 if active_chip == "Triple Captain" else 2
        gw_xp = sum(p["xp"] * (cap_mult if p.get("is_cap") else 1) for p in gw_starters)

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

    # פונקציות עזר למגרש הפלנר
    def execute_planner_bench_swap(p_out_id, p_in_id):
        snap = cur_gw_sim["squad_snapshot"]
        p_o = next((x for x in snap if x["element"] == p_out_id), None)
        p_i = next((x for x in snap if x["element"] == p_in_id), None)
        if p_o and p_i:
            p_o["position"], p_i["position"] = p_i["position"], p_o["position"]
            if selected_gw == next_gw:
                orig_o = next((x for x in st.session_state.user_squad if x["element"] == p_out_id), None)
                orig_i = next((x for x in st.session_state.user_squad if x["element"] == p_in_id), None)
                if orig_o and orig_i:
                    orig_o["position"], orig_i["position"] = orig_i["position"], orig_o["position"]
            st.session_state.planner_swap_out = None
            st.session_state.planner_transfer_out = None
            st.toast(f"✅ חילוף בוצע ב-GW {selected_gw}: {all_players[p_out_id]['name']} ⇄ {all_players[p_in_id]['name']}")
            st.rerun()

    def handle_planner_card_click(target_id):
        if st.session_state.planner_swap_out is None:
            st.session_state.planner_swap_out = target_id
            st.rerun()
        elif st.session_state.planner_swap_out == target_id:
            st.session_state.planner_swap_out = None
            st.rerun()
        else:
            execute_planner_bench_swap(st.session_state.planner_swap_out, target_id)

    def set_planner_captain(target_id):
        if selected_gw not in st.session_state.planner_captains:
            st.session_state.planner_captains[selected_gw] = {}
        st.session_state.planner_captains[selected_gw]["cap"] = target_id
        if st.session_state.planner_captains[selected_gw].get("vc") == target_id:
            st.session_state.planner_captains[selected_gw]["vc"] = None
        st.session_state.planner_swap_out = None
        st.toast(f"👑 {all_players[target_id]['name']} נבחר לקפטן (C) ב-GW {selected_gw}!")
        st.rerun()

    def set_planner_vice_captain(target_id):
        if selected_gw not in st.session_state.planner_captains:
            st.session_state.planner_captains[selected_gw] = {}
        st.session_state.planner_captains[selected_gw]["vc"] = target_id
        if st.session_state.planner_captains[selected_gw].get("cap") == target_id:
            st.session_state.planner_captains[selected_gw]["cap"] = None
        st.session_state.planner_swap_out = None
        st.toast(f"🥈 {all_players[target_id]['name']} נבחר לסגן קפטן (VC) ב-GW {selected_gw}!")
        st.rerun()

    # רינדור שורת מגרש נקייה בפלנר
    def render_clean_planner_row(player_list):
        if not player_list:
            return
        cols = st.columns(len(player_list))
        for i, p in enumerate(player_list):
            with cols[i]:
                is_sw_active = (st.session_state.planner_swap_out == p["id"])
                is_tr_active = (st.session_state.planner_transfer_out == p["id"])
                st.markdown(render_player_card_html(p, is_selected=is_sw_active, is_transfer_selected=is_tr_active, target_gw=selected_gw), unsafe_allow_html=True)
                btn_lbl = "✓ נבחר" if (is_sw_active or is_tr_active) else ("C" if p.get("is_cap") else ("VC" if p.get("is_vc") else "בחר"))
                btn_type = "primary" if (is_sw_active or is_tr_active) else "secondary"
                if st.button(btn_lbl, key=f"pl_pick_{p['id']}_{selected_gw}", use_container_width=True, type=btn_type):
                    handle_planner_card_click(p["id"])

    # מגרש הפלנר
    with st.container():
        st.markdown('<div class="pitch-anchor"></div>', unsafe_allow_html=True)
        # חלוצים
        render_clean_planner_row([p for p in cur_gw_sim["starters"] if p["pos_code"] == 4])
        st.write("")
        # קשרים
        render_clean_planner_row([p for p in cur_gw_sim["starters"] if p["pos_code"] == 3])
        st.write("")
        # מגנים
        render_clean_planner_row([p for p in cur_gw_sim["starters"] if p["pos_code"] == 2])
        st.write("")
        # שוער
        pl_gks = [p for p in cur_gw_sim["starters"] if p["pos_code"] == 1]
        if pl_gks:
            gk_c = st.columns([2, 1, 2])[1]
            with gk_c:
                p = pl_gks[0]
                is_sw_active = (st.session_state.planner_swap_out == p["id"])
                is_tr_active = (st.session_state.planner_transfer_out == p["id"])
                st.markdown(render_player_card_html(p, is_selected=is_sw_active, is_transfer_selected=is_tr_active, target_gw=selected_gw), unsafe_allow_html=True)
                btn_lbl = "✓ נבחר" if (is_sw_active or is_tr_active) else ("C" if p.get("is_cap") else ("VC" if p.get("is_vc") else "בחר"))
                btn_type = "primary" if (is_sw_active or is_tr_active) else "secondary"
                if st.button(btn_lbl, key=f"pl_pick_{p['id']}_{selected_gw}", use_container_width=True, type=btn_type):
                    handle_planner_card_click(p["id"])

    # -----------------------------------------------------------------
    # שורת ניהול והעברות בפלנר - ממוקמת בלעדית מתחת למגרש!
    # -----------------------------------------------------------------
    if st.session_state.planner_swap_out is not None:
        p_pl_sel = all_players.get(st.session_state.planner_swap_out)
        if p_pl_sel:
            is_pl_starter = any(p["element"] == p_pl_sel["id"] for p in cur_gw_sim["starters"])
            render_html(
                f"""
                <div class="action-bar-under-pitch">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
                        <div>
                            <span style="font-size:14px; font-weight:700; color:#38bdf8;">⚙️ שורת ניהול והעברות (GW {selected_gw}):</span>
                            <b style="color:#ffffff; margin-right:6px; font-size:14px;">{p_pl_sel['name']}</b>
                            <span class="ltr-tag" style="color:#94a3b8; font-size:12px;">({p_pl_sel['team']} | {p_pl_sel['pos']} | £{p_pl_sel['cost']}m)</span>
                        </div>
                        <div style="font-size:11px; color:#cbd5e1;">
                            בחר פעולה עבור שחקן זה במחזור {selected_gw}:
                        </div>
                    </div>
                </div>
                """
            )

            c_pa1, c_pa2, c_pa3, c_pa4, c_pa5 = st.columns([1, 1, 1.3, 1.2, 0.8])
            with c_pa1:
                if is_pl_starter:
                    if st.button("🅲 קפטן (C)", key=f"pl_set_c_{selected_gw}", use_container_width=True, type="primary"):
                        set_planner_captain(p_pl_sel["id"])
                else:
                    st.button("🅲 רק להרכב", disabled=True, use_container_width=True)
            with c_pa2:
                if is_pl_starter:
                    if st.button("🆅 סגן (VC)", key=f"pl_set_vc_{selected_gw}", use_container_width=True):
                        set_planner_vice_captain(p_pl_sel["id"])
                else:
                    st.button("🆅 רק להרכב", disabled=True, use_container_width=True)
            with c_pa3:
                is_drawer_open = (st.session_state.planner_transfer_out == p_pl_sel["id"])
                tr_btn_lbl = "✕ סגור שוק" if is_drawer_open else "🔄 העברה מהשוק"
                if st.button(tr_btn_lbl, key=f"pl_open_tr_{selected_gw}", use_container_width=True):
                    if is_drawer_open:
                        st.session_state.planner_transfer_out = None
                    else:
                        st.session_state.planner_transfer_out = p_pl_sel["id"]
                    st.rerun()
            with c_pa4:
                eligible_pl_swaps = cur_gw_sim["bench"] if is_pl_starter else cur_gw_sim["starters"]
                pl_swap_dict = {p["id"]: f"{p['name']} ({p['pos']})" for p in eligible_pl_swaps}
                target_pl_id = st.selectbox("החלף עם:", list(pl_swap_dict.keys()), format_func=lambda x: pl_swap_dict[x], key="pl_quick_swap_sel", label_visibility="collapsed")
                if st.button("בצע חילוף ⇄", key=f"pl_do_swap_{selected_gw}", use_container_width=True):
                    execute_planner_bench_swap(p_pl_sel["id"], target_pl_id)
            with c_pa5:
                if st.button("✕ ביטול", key=f"pl_cancel_{selected_gw}", use_container_width=True):
                    st.session_state.planner_swap_out = None
                    st.session_state.planner_transfer_out = None
                    st.rerun()

    # מגירת שוק העברות ייעודית (מוצגת מתחת למגרש ולשורת הניהול)
    if st.session_state.planner_transfer_out is not None:
        p_tr_out = all_players[st.session_state.planner_transfer_out]
        max_tr_budget = round(p_tr_out["cost"] + cur_gw_sim["bank"], 1)
        cur_squad_ids = [p["id"] for p in cur_gw_sim["starters"] + cur_gw_sim["bench"]]

        render_html(
            f"""
            <div class="transfer-drawer">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <div>
                        <span style="font-size:15px; font-weight:700; color:#38bdf8;">🛒 חלון העברות שוק למחזור {selected_gw}</span>
                        <div style="font-size:12px; color:#cbd5e1;">
                            מכירת שחקן: <b style="color:#ef4444;">{p_tr_out['name']}</b> ({p_tr_out['pos']} - £{p_tr_out['cost']}m) | 
                            תקציב מקסימלי לרכש: <b style="color:#10b981;">£{max_tr_budget}m</b>
                        </div>
                    </div>
                </div>
            </div>
            """
        )

        b_close_col, b_sch_col = st.columns([1, 3])
        with b_close_col:
            if st.button("✕ סגור חלון העברות", key="close_tr_drawer", type="primary", use_container_width=True):
                st.session_state.planner_transfer_out = None
                st.rerun()
        with b_sch_col:
            tr_search = st.text_input("חיפוש שחקן לרכש (שם או קבוצה):", key=f"tr_search_{selected_gw}", placeholder="הקלד שם או קבוצה באנגלית...").strip().lower()

        eligible_pool = [
            p for p in all_players.values()
            if p["pos_code"] == p_tr_out["pos_code"]
            and p["id"] not in cur_squad_ids
            and p["cost"] <= max_tr_budget
            and p["status"] == "a"
        ]
        if tr_search:
            eligible_pool = [p for p in eligible_pool if tr_search in p["name"].lower() or tr_search in p["team"].lower()]

        # שחקנים מומלצים תחילה
        recommended_picks = sorted(eligible_pool, key=lambda x: x["score"], reverse=True)[:3]

        if recommended_picks:
            st.markdown("##### ⭐ שחקנים מומלצים לרכש (Recommended):")
            rec_cols = st.columns(len(recommended_picks))
            for r_idx, r_p in enumerate(recommended_picks):
                with rec_cols[r_idx]:
                    r_jersey = get_jersey_svg(r_p["team"], is_gk=(r_p["pos_code"] == 1))
                    render_html(
                        f"""
                        <div class="accessible-card" style="text-align:center; padding:10px;">
                            {r_jersey}
                            <b>{r_p['name']}</b> ({r_p['team']})<br>
                            <span class="ltr-tag" style="color:#38bdf8;">£{r_p['cost']}m | xP: {r_p['xp']}</span>
                            <div style="font-size:10px; color:#cbd5e1; margin:4px 0;">{r_p['reason']}</div>
                            <div class="badge-fdr fdr-{r_p['next_fdr']}"><span class="ltr-tag">{r_p['next_match']}</span></div>
                        </div>
                        """
                    )
                    if st.button(f"רכוש את {r_p['name']} 🛒", key=f"buy_rec_{r_p['id']}_{selected_gw}", use_container_width=True, type="primary"):
                        st.session_state.planner_plan[selected_gw]["transfers"].append((p_tr_out["id"], r_p["id"]))
                        st.session_state.planner_transfer_out = None
                        st.session_state.planner_swap_out = None
                        st.toast(f"✅ רכש הושלם: {p_tr_out['name']} ⬅️ {r_p['name']}")
                        st.rerun()

        st.markdown("##### 📋 כלל השחקנים הזמינים לרכש (ממוינים לפי נקודות):")
        sorted_pool = sorted(eligible_pool, key=lambda x: x["total_points"], reverse=True)
        if sorted_pool:
            table_records = []
            for sp in sorted_pool[:25]:
                table_records.append({
                    "id": sp["id"],
                    "שחקן": sp["name"],
                    "קבוצה": sp["team"],
                    "מחיר": f"£{sp['cost']}m",
                    "נקודות עונה": sp["total_points"],
                    "xP צפוי": sp["xp"],
                    "משחק קרוב": sp["next_match"],
                    "FDR": sp["next_fdr"],
                })
            df_pool = pd.DataFrame(table_records)
            st.dataframe(df_pool.drop(columns=["id"]), use_container_width=True, hide_index=True)

            pool_dict = {p["id"]: f"{p['name']} ({p['team']}) - £{p['cost']}m | {p['total_points']} נק׳ | xP: {p['xp']}" for p in sorted_pool}
            chosen_buy_id = st.selectbox("בחר שחקן לרכישה מתוך הרשימה:", list(pool_dict.keys()), format_func=lambda x: pool_dict[x], key=f"pick_buy_sel_{selected_gw}")
            if st.button("בצע רכישה סופית 🛒", key=f"confirm_pool_buy_{selected_gw}", use_container_width=True):
                st.session_state.planner_plan[selected_gw]["transfers"].append((p_tr_out["id"], chosen_buy_id))
                st.session_state.planner_transfer_out = None
                st.session_state.planner_swap_out = None
                st.toast(f"✅ רכש הושלם: {p_tr_out['name']} ⬅️ {all_players[chosen_buy_id]['name']}")
                st.rerun()
        else:
            st.warning("לא נמצאו שחקנים מתאימים במסגרת התקציב.")

    # ספסל ב-Planner
    st.markdown("**🪑 שחקני ספסל:**")
    with st.container():
        st.markdown('<div class="bench-anchor"></div>', unsafe_allow_html=True)
        pl_bench_cols = st.columns(len(cur_gw_sim["bench"]))
        for i, p in enumerate(cur_gw_sim["bench"]):
            with pl_bench_cols[i]:
                is_sw_active = (st.session_state.planner_swap_out == p["id"])
                is_tr_active = (st.session_state.planner_transfer_out == p["id"])
                st.markdown(render_player_card_html(p, is_bench=True, is_selected=is_sw_active, is_transfer_selected=is_tr_active, target_gw=selected_gw), unsafe_allow_html=True)
                btn_lbl = "✓ נבחר" if (is_sw_active or is_tr_active) else "בחר לחילוף"
                btn_type = "primary" if (is_sw_active or is_tr_active) else "secondary"
                if st.button(btn_lbl, key=f"pl_bench_{p['id']}_{selected_gw}", use_container_width=True, type=btn_type):
                    handle_planner_card_click(p["id"])

# ---------------------------------------------------------------------
# טאב 7: 🏆 מרגל מיני-ליגות (Mini-League Spy)
# ---------------------------------------------------------------------
with t_leagues:
    st.subheader("🏆 מרגל מיני-ליגות פרטיות (Mini-League Spy)")
    st.caption("עקוב אחרי יריביך במיני-ליגה: זהה באילו שחקנים הם מחזיקים, מי בחר איזה קפטן, ואתר דיפרנשיאלים שיקפיצו אותך בדירוג.")

    @st.cache_data(ttl=180)
    def fetch_classic_league_standings(l_id):
        try:
            url = f"https://fantasy.premierleague.com/api/leagues-classic/{l_id}/standings/"
            res = requests.get(url, headers=API_HEADERS, timeout=12).json()
            return res
        except Exception:
            return None

    # בחירת ליגה מתוך הליגות הקיימות של הקבוצה או הזנה ידנית
    user_classic_leagues = user_entry_data.get("leagues", {}).get("classic", [])
    user_league_map = {l["id"]: l["name"] for l in user_classic_leagues if l.get("league_type") == "x"}

    col_l1, col_l2 = st.columns([2, 1])
    with col_l1:
        if user_league_map:
            chosen_league_id = st.selectbox(
                "בחר מיני-ליגה פרטית של הקבוצה שלך:",
                options=list(user_league_map.keys()),
                format_func=lambda x: f"{user_league_map[x]} (ID: {x})",
            )
        else:
            chosen_league_id = None
            st.info("לא נמצאו מיני-ליגות פרטיות מקושרות אוטומטית. באפשרותך להזין מזהה ידנית.")

    with col_l2:
        manual_league_input = st.text_input("או הזן League ID ידנית:", placeholder="למשל 123456").strip()
        if manual_league_input.isdigit():
            chosen_league_id = int(manual_league_input)

    if chosen_league_id:
        standings_data = fetch_classic_league_standings(chosen_league_id)
        if standings_data and "standings" in standings_data:
            st.markdown(f"### 🏆 טבלת הליגה: **{standings_data.get('league', {}).get('name', 'Classic League')}**")
            results = standings_data["standings"].get("results", [])

            if results:
                leader_score = results[0]["total"]
                rows = []
                for r in results[:30]:
                    gap = r["total"] - leader_score
                    gap_str = f"{gap}" if gap != 0 else "מוביל 🥇"
                    is_me = (str(r["entry"]) == str(team_id))
                    rows.append({
                        "מקום": f"{'👉 ' if is_me else ''}{r['rank']}",
                        "קבוצה": r["entry_name"],
                        "מאמן": r["player_name"],
                        "GW אחרון": r["event_total"],
                        "סך נקודות": r["total"],
                        "פער מהפסגה": gap_str,
                        "Team ID": r["entry"],
                    })

                df_standings = pd.DataFrame(rows)
                st.dataframe(df_standings.drop(columns=["Team ID"]), use_container_width=True, hide_index=True)

                st.write("---")
                st.markdown("#### 🕵️ כלי ריגול ראש-בראש מול יריב (Head-to-Head Spy)")
                rival_choices = {r["entry"]: f"{r['player_name']} ({r['entry_name']}) - מקום {r['rank']}" for r in results if str(r["entry"]) != str(team_id)}

                if rival_choices:
                    chosen_rival_id = st.selectbox(
                        "בחר יריב לריגול והשוואת שחקנים:",
                        options=list(rival_choices.keys()),
                        format_func=lambda x: rival_choices[x],
                    )
                    
                    @st.cache_data(ttl=300)
                    def fetch_rival_picks(r_id, gw):
                        try:
                            last_g = max(1, gw - 1)
                            url = f"https://fantasy.premierleague.com/api/entry/{r_id}/event/{last_g}/picks/"
                            return requests.get(url, headers=API_HEADERS, timeout=12).json()
                        except Exception:
                            return None

                    rival_picks_res = fetch_rival_picks(chosen_rival_id, next_gw)
                    if rival_picks_res and "picks" in rival_picks_res:
                        rival_pids = [p["element"] for p in rival_picks_res["picks"]]
                        my_pids = [p["element"] for p in st.session_state.user_squad]

                        my_diffs = [all_players[pid]["name"] for pid in my_pids if pid not in rival_pids and pid in all_players]
                        rival_diffs = [all_players[pid]["name"] for pid in rival_pids if pid not in my_pids and pid in all_players]
                        
                        r_cap_obj = next((all_players[p["element"]]["name"] for p in rival_picks_res["picks"] if p.get("is_captain")), "—")
                        r_chip = rival_picks_res.get("active_chip", "ללא צ'יפ")

                        col_spy1, col_spy2 = st.columns(2)
                        with col_spy1:
                            st.markdown(
                                f"""
                                <div class="accessible-card">
                                    <b>פרטי יריב (מחזור אחרון):</b><br>
                                    👑 קפטן יריב: <b style="color:#facc15;">{r_cap_obj}</b><br>
                                    🎮 צ'יפ פעיל: <b>{r_chip or 'ללא'}</b>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        with col_spy2:
                            st.markdown(
                                f"""
                                <div class="accessible-card">
                                    <b>🎯 הדיפרנשיאלים שלך (שחקנים שאין לו):</b><br>
                                    <span style="color:#10b981; font-size:12px;">{', '.join(my_diffs[:6]) if my_diffs else 'אין'}</span><br><br>
                                    <b>⚠️ שחקני מפתח אצל היריב (שאין לך):</b><br>
                                    <span style="color:#ef4444; font-size:12px;">{', '.join(rival_diffs[:6]) if rival_diffs else 'אין'}</span>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
            else:
                st.info("לא נמצאו תוצאות במיני-ליגה זו.")
        else:
            st.error("לא ניתן לטעון את נתוני הליגה. ודא שמספר הליגה תקין.")
    else:
        st.info("בחר או הזן קוד מיני-ליגה כדי להציג את הטבלה ומנוע הריגול.")
