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
# 3. תמיכה דו-לשונית מלאה (i18n): עברית / אנגלית
# =====================================================================
if "app_lang" not in st.session_state:
    st.session_state.app_lang = "he"

TRANSLATIONS = {
    "he": {
        "page_title": "FPL Elite Scout | מנוע החלטות ומרגל סגלים",
        "app_title": "⚽ FPL Elite Scout",
        "app_subtitle": "סוכן בינה, אסטרטגיית הרכב ומרגל מיני-ליגות המכוון ל-Top 50K",
        "gate_desc": "הזן את מספר הקבוצה שלך כדי לטעון ניתוח כשירות, ציון סגל מכויל, חסרונות הרכב, מתכנן מחזורים ומרגל ליגות.",
        "team_id_label": "מספר קבוצה (Team ID):",
        "team_id_placeholder": "למשל: 139453",
        "team_id_help": "המספר שמופיע בכתובת הדפדפן בלשונית Points",
        "login_btn": "🚀 כניסה לסגל שלי",
        "demo_btn": "👀 סגל דמו לדוגמה",
        "where_find_id": "❓ איפה מוצאים את ה-Team ID?",
        "digits_only": "נא להזין ספרות בלבד.",
        "change_team": "🔄 החלף קבוצה",
        "engine_for_gw": "מנוע החלטות למחזור",
        "team_label": "קבוצה:",
        "squad_score": "ציון סגל מכויל",
        "xp_forecast": "תחזית נקודות (xP)",
        "in_bank": "יתרה בבנק",
        "overall_rank": "דירוג כללי",
        "formation": "מערך",
        "total_xp": "תוחלת נקודות להרכב",
        "tab_squad": "🟢 הסגל על המגרש",
        "tab_transfers": "🔄 מעבדת חילופים",
        "tab_analysis": "📊 ניתוח וחסרונות",
        "tab_scout": "🌟 רדאר רכש עילית",
        "tab_scenarios": "🎯 3 תרחישי תקציב",
        "tab_planner": "🗓️ מתכנן מחזורים משורשר",
        "tab_leagues": "🏆 מרגל מיני-ליגות",
        "pos_1": "שוער",
        "pos_2": "הגנה",
        "pos_3": "קישור",
        "pos_4": "חלוץ",
        "pos_1_pl": "שוערים",
        "pos_2_pl": "מגנים",
        "pos_3_pl": "קשרים",
        "pos_4_pl": "חלוצים",
        "btn_select": "בחר",
        "btn_selected": "✓ נבחר",
        "btn_captain": "קפטן (C)",
        "btn_vc": "סגן (VC)",
        "btn_sub": "חילוף ספסל ⇄",
        "btn_transfer": "העברה מהשוק 🔄",
        "btn_cancel": "ביטול",
        "btn_swap_here": "⇄ החלף לכאן",
        "swap_banner_title": "מצב חילוף פעיל:",
        "swap_banner_desc": "בחר שחקן יעד חוקי להחלפה עם",
        "cancel_swap": "✕ ביטול חילוף",
        "action_bar_title": "⚙️ פעולות עבור שחקן:",
        "action_bar_hint": "בחר פעולה:",
        "transfer_drawer_title": "🛒 חלון העברות שוק",
        "selling_player": "מכירת שחקן:",
        "max_budget": "תקציב מקסימלי לרכש:",
        "close_drawer": "✕ סגור חלון",
        "search_placeholder": "חיפוש שחקן (שם או קבוצה באנגלית)...",
        "rec_header": "⭐ שחקנים מומלצים לרכש (Recommended):",
        "buy_player_btn": "➕ קנה שחקן זה",
        "all_cands_label": "או בחר שחקן לרכש מהרשימה המלאה:",
        "confirm_transfer_btn": "➕ אשר העברה",
        "bench_title": "🪑 שחקני ספסל:",
        "rebuild_btn": "🃏 בנה סגל מאפס (WC / FH)",
        "close_rebuild_btn": "✕ סגור מצב בנייה מחדש",
        "rebuild_title": "🛠️ לוח בניית סגל מאפס",
        "rebuild_subtitle": "בחר 15 שחקנים (2 שוערים, 5 מגנים, 5 קשרים, 3 חלוצים) במסגרת התקציב",
        "total_squad_val": "שווי סגל כולל",
        "rem_budget": "תקציב פנוי נותר",
        "players_picked": "שחקנים שנבחרו",
        "avg_per_player": "ממוצע לשחקן",
        "clear_15_btn": "🗑️ רוקן את כל 15 השחקנים",
        "load_existing_btn": "📋 טען שחקנים מסגל קיים",
        "save_rebuild_btn": "💾 אשר ושמור סגל חדש!",
        "empty_slot": "משבצת פנויה",
        "add_slot": "➕ הוסף",
        "remove_btn": "✕ הסר",
        "ft_available": "חילופים זמינים",
        "ft_planned": "חילופים שתוכננו",
        "hit_penalty": "קנס מינוס (Hits)",
        "bank_bal": "יתרה בבנק",
        "xp_pred": "תחזית נקודות (xP)",
        "chip_for_gw": "צ'יפ למחזור",
        "no_chip": "ללא צ'יפ",
        "clear_all_transfers": "🗑️ נקה הכל",
        "planned_transfers_gw": "העברות שתוכננו למחזור",
        "cancel_single_transfer": "✕ בטל",
        "pts": "נק׳",
        "against": "מול:",
        "starters_only_cap": "קפטן להרכב בלבד",
    },
    "en": {
        "page_title": "FPL Elite Scout | Decision Engine & Squad Spy",
        "app_title": "⚽ FPL Elite Scout",
        "app_subtitle": "AI Agent, Lineup Optimizer & Mini-League Spy aimed at Top 50K",
        "gate_desc": "Enter your Team ID to load injury analysis, calibrated squad rating, lineup flaws, gameweek planner, and league spy.",
        "team_id_label": "Team ID:",
        "team_id_placeholder": "e.g., 139103",
        "team_id_help": "The number from your browser URL under the Points tab",
        "login_btn": "🚀 Load My Squad",
        "demo_btn": "👀 Demo Squad",
        "where_find_id": "❓ Where to find your Team ID?",
        "digits_only": "Please enter digits only.",
        "change_team": "🔄 Change Team",
        "engine_for_gw": "Decision Engine for Gameweek",
        "team_label": "Team:",
        "squad_score": "Squad Rating",
        "xp_forecast": "Expected Points (xP)",
        "in_bank": "In the Bank",
        "overall_rank": "Overall Rank",
        "formation": "Formation",
        "total_xp": "Lineup Expected Points",
        "tab_squad": "🟢 Squad on Pitch",
        "tab_transfers": "🔄 Transfers Lab",
        "tab_analysis": "📊 Analysis & Flaws",
        "tab_scout": "🌟 Elite Scout Radar",
        "tab_scenarios": "🎯 3 Budget Scenarios",
        "tab_planner": "🗓️ Gameweek Planner",
        "tab_leagues": "🏆 Mini-League Spy",
        "pos_1": "Goalkeeper",
        "pos_2": "Defender",
        "pos_3": "Midfielder",
        "pos_4": "Forward",
        "pos_1_pl": "Goalkeepers",
        "pos_2_pl": "Defenders",
        "pos_3_pl": "Midfielders",
        "pos_4_pl": "Forwards",
        "btn_select": "Select",
        "btn_selected": "✓ Selected",
        "btn_captain": "Captain (C)",
        "btn_vc": "Vice (VC)",
        "btn_sub": "Substitute ⇄",
        "btn_transfer": "Transfer Out 🔄",
        "btn_cancel": "Cancel",
        "btn_swap_here": "⇄ Swap Here",
        "swap_banner_title": "Substitution Mode Active:",
        "swap_banner_desc": "Select an eligible player to swap with",
        "cancel_swap": "✕ Cancel Swap",
        "action_bar_title": "⚙️ Player Actions:",
        "action_bar_hint": "Select action:",
        "transfer_drawer_title": "🛒 Transfer Market Drawer",
        "selling_player": "Selling Player:",
        "max_budget": "Max Budget Available:",
        "close_drawer": "✕ Close Drawer",
        "search_placeholder": "Search player (name or team)...",
        "rec_header": "⭐ Recommended Replacements:",
        "buy_player_btn": "➕ Buy This Player",
        "all_cands_label": "Or choose from all available players in budget:",
        "confirm_transfer_btn": "➕ Confirm Transfer",
        "bench_title": "🪑 Bench Players:",
        "rebuild_btn": "🃏 Rebuild from Scratch (WC / FH)",
        "close_rebuild_btn": "✕ Close Rebuild Mode",
        "rebuild_title": "🛠️ Rebuild Squad from Scratch",
        "rebuild_subtitle": "Select 15 players (2 GKs, 5 DEFs, 5 MIDs, 3 FWDs) within your budget",
        "total_squad_val": "Total Squad Value",
        "rem_budget": "Remaining Budget",
        "players_picked": "Players Picked",
        "avg_per_player": "Avg per Player",
        "clear_15_btn": "🗑️ Clear All 15 Players",
        "load_existing_btn": "📋 Load Existing Squad",
        "save_rebuild_btn": "💾 Save & Apply New Squad!",
        "empty_slot": "Empty Slot",
        "add_slot": "➕ Add",
        "remove_btn": "✕ Remove",
        "ft_available": "Available FTs",
        "ft_planned": "Planned Transfers",
        "hit_penalty": "Hit Penalty",
        "bank_bal": "Bank Balance",
        "xp_pred": "Points Forecast (xP)",
        "chip_for_gw": "Chip for GW",
        "no_chip": "No Chip",
        "clear_all_transfers": "🗑️ Clear All",
        "planned_transfers_gw": "Planned Transfers for GW",
        "cancel_single_transfer": "✕ Cancel",
        "pts": "pts",
        "against": "vs:",
        "starters_only_cap": "Starters only for Captain",
    }
}

def t(key):
    lang = st.session_state.get("app_lang", "he")
    return TRANSLATIONS.get(lang, {}).get(key, TRANSLATIONS["he"].get(key, key))

# =====================================================================
# 4. עיצוב CSS מלא: נגישות, RTL / LTR דינמי, רספונסיביות מובייל
# =====================================================================
css_template = """
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
    direction: __DIR__;
    text-align: __ALIGN__;
    background-color: var(--bg-main);
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    color: var(--text-primary);
}

div[data-testid="stMarkdownContainer"] p {
    direction: __DIR__;
    text-align: __ALIGN__;
    line-height: 1.5;
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
    direction: __DIR__;
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
    direction: __DIR__;
}

.rebuild-banner {
    background: linear-gradient(135deg, #111a28 0%, #18283f 100%);
    border: 1px solid #38bdf8;
    border-radius: 12px;
    padding: 12px 16px;
    margin: 10px auto 14px auto;
    max-width: 820px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    direction: __DIR__;
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
"""

is_rtl = (st.session_state.get("app_lang", "he") == "he")
dir_val = "rtl" if is_rtl else "ltr"
align_val = "right" if is_rtl else "left"
rendered_css = css_template.replace("__DIR__", dir_val).replace("__ALIGN__", align_val)
st.markdown(rendered_css, unsafe_allow_html=True)

# =====================================================================
# 4. משיכת נתוני הליגה והגנת API מבוססת כותרות
# =====================================================================
API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

@st.cache_data(ttl=600)
def fetch_league_data():
    base = "https://fantasy.premierleague.com/api/"
    try:
        bootstrap = requests.get(f"{base}bootstrap-static/", headers=API_HEADERS, timeout=12).json()
        fixtures = requests.get(f"{base}fixtures/", headers=API_HEADERS, timeout=12).json()
    except Exception:
        return {}, 4, ""

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

def is_swap_legal(player1_id, player2_id, current_squad_list):
    """
    בדיקה קפדנית לפי חוקי ה-FPL הרשמיים האם חילוף בין שני שחקנים חוקי:
    1. שוער (GK) יכול להתחלף רק עם שוער.
    2. חילוף בין שחקן הרכב לשחקן ספסל חייב להשאיר מערך חוקי:
       - בדיוק 1 שוער
       - בין 3 ל-5 מגנים
       - בין 2 ל-5 קשרים
       - בין 1 ל-3 חלוצים
       - סך הכל בדיוק 11 שחקני הרכב
    """
    p1_entry = next((p for p in current_squad_list if p["element"] == player1_id), None)
    p2_entry = next((p for p in current_squad_list if p["element"] == player2_id), None)
    if not p1_entry or not p2_entry:
        return False, ("שחקן לא נמצא" if st.session_state.app_lang == "he" else "Player not found")
    
    p1_data = all_players.get(player1_id)
    p2_data = all_players.get(player2_id)
    if not p1_data or not p2_data:
        return False, ("חסרים נתוני שחקן" if st.session_state.app_lang == "he" else "Missing player data")
    
    is_p1_starter = (p1_entry["position"] <= 11)
    is_p2_starter = (p2_entry["position"] <= 11)
    
    if is_p1_starter == is_p2_starter:
        return True, ""
    
    if (p1_data["pos_code"] == 1 or p2_data["pos_code"] == 1) and (p1_data["pos_code"] != p2_data["pos_code"]):
        err = "שוער מתחלף רק בשוער" if st.session_state.app_lang == "he" else "GK can only swap with GK"
        return False, err
    
    starter_id = player1_id if is_p1_starter else player2_id
    bench_id = player2_id if is_p1_starter else player1_id
    bench_pos = all_players[bench_id]["pos_code"]
    
    new_pos_codes = [all_players[p["element"]]["pos_code"] for p in current_squad_list if p["position"] <= 11 and p["element"] != starter_id] + [bench_pos]
    gk_cnt = new_pos_codes.count(1)
    def_cnt = new_pos_codes.count(2)
    mid_cnt = new_pos_codes.count(3)
    fwd_cnt = new_pos_codes.count(4)
    
    if gk_cnt != 1:
        return False, ("חובה שוער 1" if st.session_state.app_lang == "he" else "Must have 1 GK")
    if not (3 <= def_cnt <= 5):
        return False, ("דרוש 3-5 מגנים" if st.session_state.app_lang == "he" else "Needs 3-5 DEFs")
    if not (2 <= mid_cnt <= 5):
        return False, ("דרוש 2-5 קשרים" if st.session_state.app_lang == "he" else "Needs 2-5 MIDs")
    if not (1 <= fwd_cnt <= 3):
        return False, ("דרוש לפחות חלוץ 1" if st.session_state.app_lang == "he" else "Needs 1-3 FWDs")
    
    return True, ""

# =====================================================================
# 5. שער כניסה ומסך נחיתה
# =====================================================================
query_params = st.query_params
url_id = query_params.get("team", None)

if "user_team_id" not in st.session_state:
    st.session_state.user_team_id = (
        url_id.strip() if url_id and url_id.strip().isdigit() else None
    )

if not st.session_state.user_team_id:
    c_gate_top1, c_gate_top2 = st.columns([5, 1])
    with c_gate_top2:
        if st.button("🌐 English" if st.session_state.app_lang == "he" else "🌐 עברית", key="gate_lang_btn", use_container_width=True):
            st.session_state.app_lang = "en" if st.session_state.app_lang == "he" else "he"
            st.rerun()

    st.markdown(
        f"""
    <div class="gate-card">
        <h1 style="color:#38bdf8; margin-bottom:6px;">{t('app_title')}</h1>
        <div style="font-size:15px; color:#94a3b8; margin-bottom:18px;">
            {t('app_subtitle')}
        </div>
        <p style="font-size:13px; color:#cbd5e1; line-height:1.6; margin-bottom:20px;">
            {t('gate_desc')}
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    c_form = st.columns([1, 2, 1])[1]
    with c_form:
        input_val = st.text_input(
            t("team_id_label"),
            placeholder=t("team_id_placeholder"),
            help=t("team_id_help"),
        )
        b1, b2 = st.columns(2)
        with b1:
            if st.button(t("login_btn"), use_container_width=True):
                if input_val.strip().isdigit():
                    st.session_state.user_team_id = input_val.strip()
                    st.query_params["team"] = input_val.strip()
                    st.rerun()
                else:
                    st.error(t("digits_only"))
        with b2:
            if st.button(t("demo_btn"), use_container_width=True):
                st.session_state.user_team_id = "1"
                st.query_params["team"] = "1"
                st.rerun()

        with st.expander(t("where_find_id")):
            st.markdown(
                """
            1. fantasy.premierleague.com  
            2. Points Tab  
            3. entry/XXXXXX/event  
            """,
                unsafe_allow_html=True,
            )
    st.stop()

team_id = st.session_state.user_team_id

# =====================================================================
# 6. משיכת נתוני הקבוצה מה-API
# =====================================================================
@st.cache_data(ttl=300)
def fetch_user_team(t_id, gw):
    try:
        last_gw = max(1, gw - 1)
        base = "https://fantasy.premierleague.com/api/"
        picks_url = f"{base}entry/{t_id}/event/{last_gw}/picks/"
        picks_res = requests.get(picks_url, headers=API_HEADERS, timeout=12).json()
        entry_url = f"{base}entry/{t_id}/"
        entry_res = requests.get(entry_url, headers=API_HEADERS, timeout=12).json()

        if picks_res.get("active_chip") == "free_hit" and last_gw > 1:
            base_gw = last_gw - 1
            base_url = f"{base}entry/{t_id}/event/{base_gw}/picks/"
            picks_res = requests.get(base_url, headers=API_HEADERS, timeout=12).json()

        bank = picks_res.get("entry_history", {}).get("bank", 0) / 10
        picks = picks_res.get("picks", [])
        team_name = entry_res.get("name", f"Team {t_id}")
        rank = entry_res.get("summary_overall_rank", "—")
        leagues = entry_res.get("leagues", {}).get("classic", [])
        return picks, bank, team_name, rank, leagues
    except Exception:
        return None, 0.0, None, None, []

raw_picks, initial_bank, my_team_name, my_rank, my_leagues = fetch_user_team(team_id, next_gw)
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

# ניהול מצבי בחירה, חילוף והעברות
if "squad_selected_id" not in st.session_state:
    st.session_state.squad_selected_id = None
if "squad_swap_active" not in st.session_state:
    st.session_state.squad_swap_active = False
if "squad_transfer_active" not in st.session_state:
    st.session_state.squad_transfer_active = False

if "planner_plan" not in st.session_state:
    st.session_state.planner_plan = {
        g: {"chip": "ללא צ'יפ", "transfers": []} for g in range(next_gw, 39)
    }
if "planner_captains" not in st.session_state:
    st.session_state.planner_captains = {}

if "planner_starting_fts" not in st.session_state:
    st.session_state.planner_starting_fts = 1

if "planner_selected_id" not in st.session_state:
    st.session_state.planner_selected_id = None
if "planner_swap_active" not in st.session_state:
    st.session_state.planner_swap_active = False
if "planner_transfer_out" not in st.session_state:
    st.session_state.planner_transfer_out = None

if "planner_rebuild_active" not in st.session_state:
    st.session_state.planner_rebuild_active = None

if "planner_rebuild_picks" not in st.session_state:
    st.session_state.planner_rebuild_picks = []

if "planner_rebuild_target_pos" not in st.session_state:
    st.session_state.planner_rebuild_target_pos = None

if "planner_rebuild_total_budget" not in st.session_state:
    st.session_state.planner_rebuild_total_budget = 100.0

starters = []
bench = []
for p in st.session_state.user_squad:
    pid = p["element"]
    p_info = all_players.get(pid)
    if p_info:
        item = {
            **p_info,
            "element": pid,
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
# 7. סרגל עליון ומדדים ראשיים
# =====================================================================
h_col1, h_col2, h_col3 = st.columns([3, 1, 1])
with h_col1:
    st.title(f"⚽ {my_team_name}")
    st.caption(
        f'{t("engine_for_gw")} {next_gw} | {t("team_label")} <span class="ltr-tag"><b>{team_id}</b></span>',
        unsafe_allow_html=True,
    )
with h_col2:
    st.write("")
    if st.button("🌐 English" if st.session_state.app_lang == "he" else "🌐 עברית", key="hdr_lang_toggle", use_container_width=True):
        st.session_state.app_lang = "en" if st.session_state.app_lang == "he" else "he"
        st.rerun()
with h_col3:
    st.write("")
    if st.button(t("change_team"), use_container_width=True):
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
        <div class="kpi-title">{t('squad_score')}</div>
        <div class="kpi-value" style="color:{rating_color};">{squad_rating} <span style="font-size:12px; color:#64748b;">/ 100</span></div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">{t('xp_forecast')}</div>
        <div class="kpi-value" style="color:#10b981;">{starting_xp_total:.1f}</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">{t('in_bank')}</div>
        <div class="kpi-value"><span class="ltr-tag">£{st.session_state.user_bank:.1f}m</span></div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">{t('overall_rank')}</div>
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
    <div id="fpl-clock" style="font-size:20px; font-weight:bold; color:#10b981; direction:ltr;">טוען שעון...</div>
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
components.html(clock_html, height=80)

# =====================================================================
# 8. פונקציות עזר לרינדור כרטיס שחקן עשיר ב-HTML
# =====================================================================
def render_player_card_html(p, is_bench=False, is_selected=False, is_transfer_selected=False, target_gw=None, custom_cap=None, custom_vc=None):
    is_c = custom_cap if custom_cap is not None else p.get("is_cap", False)
    is_v = custom_vc if custom_vc is not None else p.get("is_vc", False)

    cap_badge = '<span class="badge-c">C</span>' if is_c else ('<span class="badge-vc">VC</span>' if is_v else "")
    bench_class = "card-bench" if is_bench else ""
    sel_class = "p-card-selected" if is_selected else ("p-card-transfer-selected" if is_transfer_selected else "")

    lang = st.session_state.get("app_lang", "he")
    lbl_inj = "🔴 פצוע" if lang == "he" else "🔴 Injured"
    lbl_dbt = "🟡 בספק" if lang == "he" else "🟡 Doubt"
    lbl_str = "🟢 פותח" if lang == "he" else "🟢 Starts"

    if p["chance"] <= 25 or p["status"] in ["i", "s", "u"]:
        status_class = "card-danger"
        status_pill = f'<div class="prob-badge prob-red">{lbl_inj} {p["start_prob"]}%</div>'
    elif p["chance"] <= 75 or p["status"] == "d":
        status_class = "card-warning"
        status_pill = f'<div class="prob-badge prob-yellow">{lbl_dbt} {p["start_prob"]}%</div>'
    else:
        status_class = "cap-gold" if is_c else ("vc-silver" if is_v else "")
        status_pill = f'<div class="prob-badge prob-green">{lbl_str} {p["start_prob"]}%</div>'

    jersey_svg = get_jersey_svg(p["team"], is_gk=(p["pos_code"] == 1))
    club_cfg = TEAM_KIT_COLORS.get(p["team"], {"primary": "#38bdf8"})
    top_color_bar = f'<div style="height:3px; background:{club_cfg["primary"]}; border-radius:3px 3px 0 0; margin:-5px -3px 3px -3px;"></div>'

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
    t("tab_squad"),
    t("tab_transfers"),
    t("tab_analysis"),
    t("tab_scout"),
    t("tab_scenarios"),
    t("tab_planner"),
    t("tab_leagues"),
])

# ---------------------------------------------------------------------
# טאב 1: מגרש חי עם חילופים מודרכים, סימוני C ו-VC, והעברות שוק
# ---------------------------------------------------------------------
with t_squad:
    st.caption(
        f"{t('formation')}: **{pos_counts[2]}-{pos_counts[3]}-{pos_counts[4]}** | {t('total_xp')}: **{starting_xp_total:.1f}**"
    )

    def execute_squad_swap(p_out_id, p_in_id):
        legal, err_msg = is_swap_legal(p_out_id, p_in_id, st.session_state.user_squad)
        if not legal:
            st.error(f"⚠️ {err_msg}")
            return
        p_o = next((x for x in st.session_state.user_squad if x["element"] == p_out_id), None)
        p_i = next((x for x in st.session_state.user_squad if x["element"] == p_in_id), None)
        if p_o and p_i:
            p_o["position"], p_i["position"] = p_i["position"], p_o["position"]
            st.session_state.squad_selected_id = None
            st.session_state.squad_swap_active = False
            st.toast(f"✅ {all_players[p_out_id]['name']} ⇄ {all_players[p_in_id]['name']}")
            st.rerun()

    def set_squad_captain(target_id):
        for sp in st.session_state.user_squad:
            sp["is_captain"] = (sp["element"] == target_id)
            if sp["is_captain"]:
                sp["is_vice_captain"] = False
        st.session_state.squad_selected_id = None
        st.toast(f"👑 {all_players[target_id]['name']} (C)")
        st.rerun()

    def set_squad_vice_captain(target_id):
        for sp in st.session_state.user_squad:
            sp["is_vice_captain"] = (sp["element"] == target_id)
            if sp["is_vice_captain"]:
                sp["is_captain"] = False
        st.session_state.squad_selected_id = None
        st.toast(f"🥈 {all_players[target_id]['name']} (VC)")
        st.rerun()

    # באנר מצב חילוף פעיל
    if st.session_state.squad_swap_active and st.session_state.squad_selected_id:
        p_sw_from = all_players.get(st.session_state.squad_selected_id)
        if p_sw_from:
            c_sw_info, c_sw_canc = st.columns([4, 1])
            with c_sw_info:
                st.info(f"🔁 **{t('swap_banner_title')}** {t('swap_banner_desc')} **{p_sw_from['name']}** ({p_sw_from['team']} | {p_sw_from['pos']})")
            with c_sw_canc:
                if st.button(t("cancel_swap"), key="sq_cancel_swap_top", use_container_width=True, type="primary"):
                    st.session_state.squad_swap_active = False
                    st.session_state.squad_selected_id = None
                    st.rerun()

    def render_clean_squad_row(player_list, is_bench=False):
        if not player_list:
            return
        if len(player_list) == 1:
            cols = [st.columns([2, 1, 2])[1]]
        else:
            cols = st.columns(len(player_list))
        for i, p in enumerate(player_list):
            with cols[i]:
                is_this_selected = (st.session_state.squad_selected_id == p["id"])
                st.markdown(render_player_card_html(p, is_bench=is_bench, is_selected=is_this_selected), unsafe_allow_html=True)
                
                if st.session_state.squad_swap_active:
                    if is_this_selected:
                        if st.button(t("btn_selected"), key=f"sq_b_{p['id']}", use_container_width=True, type="primary"):
                            st.session_state.squad_swap_active = False
                            st.session_state.squad_selected_id = None
                            st.rerun()
                    else:
                        legal, reason = is_swap_legal(st.session_state.squad_selected_id, p["id"], st.session_state.user_squad)
                        if legal:
                            if st.button(t("btn_swap_here"), key=f"sq_b_{p['id']}", use_container_width=True, type="primary"):
                                execute_squad_swap(st.session_state.squad_selected_id, p["id"])
                        else:
                            st.button(f"✕ {reason}", key=f"sq_b_{p['id']}", use_container_width=True, disabled=True)
                else:
                    btn_lbl = t("btn_selected") if is_this_selected else ("C" if p.get("is_cap") else ("VC" if p.get("is_vc") else t("btn_select")))
                    btn_type = "primary" if is_this_selected else "secondary"
                    if st.button(btn_lbl, key=f"sq_b_{p['id']}", use_container_width=True, type=btn_type):
                        if is_this_selected:
                            st.session_state.squad_selected_id = None
                            st.session_state.squad_transfer_active = False
                        else:
                            st.session_state.squad_selected_id = p["id"]
                            st.session_state.squad_transfer_active = False
                        st.rerun()

    # מגרש ראשי
    with st.container():
        st.markdown('<div class="pitch-anchor"></div>', unsafe_allow_html=True)
        render_clean_squad_row([p for p in starters if p["pos_code"] == 4])
        st.write("")
        render_clean_squad_row([p for p in starters if p["pos_code"] == 3])
        st.write("")
        render_clean_squad_row([p for p in starters if p["pos_code"] == 2])
        st.write("")
        gks = [p for p in starters if p["pos_code"] == 1]
        if gks:
            render_clean_squad_row(gks)

    # שורת פעולות מתחת למגרש (בבחירת שחקן)
    if st.session_state.squad_selected_id is not None and not st.session_state.squad_swap_active and not st.session_state.squad_transfer_active:
        p_sel = all_players.get(st.session_state.squad_selected_id)
        if p_sel:
            is_starter = any(p["id"] == p_sel["id"] for p in starters)
            j_svg = get_jersey_svg(p_sel["team"], is_gk=(p_sel["pos_code"] == 1))
            render_html(
                f"""
                <div class="action-bar-under-pitch">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            {j_svg}
                            <div>
                                <span style="font-size:13px; font-weight:700; color:#38bdf8;">{t('action_bar_title')}</span>
                                <b style="color:#ffffff; font-size:14px; margin:0 4px;">{p_sel['name']}</b>
                                <span class="ltr-tag" style="color:#94a3b8; font-size:12px;">({p_sel['team']} | {p_sel['pos']} | £{p_sel['cost']}m | xP: {p_sel['xp']})</span>
                            </div>
                        </div>
                        <div style="font-size:11px; color:#cbd5e1;">
                            {t('action_bar_hint')}
                        </div>
                    </div>
                </div>
                """
            )
            col_a1, col_a2, col_a3, col_a4, col_a5 = st.columns([1, 1, 1.2, 1.2, 0.8])
            with col_a1:
                if is_starter:
                    if st.button(f"👑 {t('btn_captain')}", key="bar_cap_btn", use_container_width=True, type="primary"):
                        set_squad_captain(p_sel["id"])
                else:
                    st.button(f"👑 {t('btn_captain')}", disabled=True, help=t("starters_only_cap"), use_container_width=True)
            with col_a2:
                if is_starter:
                    if st.button(f"🥈 {t('btn_vc')}", key="bar_vc_btn", use_container_width=True):
                        set_squad_vice_captain(p_sel["id"])
                else:
                    st.button(f"🥈 {t('btn_vc')}", disabled=True, help=t("starters_only_cap"), use_container_width=True)
            with col_a3:
                if st.button(t("btn_sub"), key="bar_sub_btn", use_container_width=True, type="primary"):
                    st.session_state.squad_swap_active = True
                    st.rerun()
            with col_a4:
                if st.button(t("btn_transfer"), key="bar_tr_btn", use_container_width=True):
                    st.session_state.squad_transfer_active = True
                    st.rerun()
            with col_a5:
                if st.button(f"✕ {t('btn_cancel')}", key="bar_cancel_btn", use_container_width=True):
                    st.session_state.squad_selected_id = None
                    st.session_state.squad_swap_active = False
                    st.session_state.squad_transfer_active = False
                    st.rerun()

    # מגירת שוק העברות בטאב 1
    if st.session_state.squad_transfer_active and st.session_state.squad_selected_id:
        p_tr_out = all_players.get(st.session_state.squad_selected_id)
        if p_tr_out:
            max_budget = round(p_tr_out["cost"] + st.session_state.user_bank, 1)
            cur_pids = [x["element"] for x in st.session_state.user_squad]
            
            render_html(
                f"""
                <div class="transfer-drawer">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:10px;">
                        <div>
                            <span style="font-size:15px; font-weight:700; color:#38bdf8;">{t('transfer_drawer_title')}</span>
                            <div style="font-size:12px; color:#cbd5e1;">
                                {t('selling_player')} <b style="color:#ef4444;">{p_tr_out['name']}</b> ({p_tr_out['pos']} | £{p_tr_out['cost']}m) | 
                                {t('max_budget')} <b style="color:#10b981;">£{max_budget:.1f}m</b>
                            </div>
                        </div>
                    </div>
                </div>
                """
            )
            c_cls, c_sch = st.columns([1, 3])
            with c_cls:
                if st.button(t("close_drawer"), key="sq_close_tr_btn", type="primary", use_container_width=True):
                    st.session_state.squad_transfer_active = False
                    st.rerun()
            with c_sch:
                tr_search_q = st.text_input(t("search_placeholder"), key="sq_tr_search_inp").strip().lower()
            
            cands = [
                p for p in all_players.values()
                if p["pos_code"] == p_tr_out["pos_code"]
                and p["id"] not in cur_pids
                and p["cost"] <= max_budget
                and p["status"] == "a"
            ]
            if tr_search_q:
                cands = [p for p in cands if tr_search_q in p["name"].lower() or tr_search_q in p["team"].lower()]
            
            recs = sorted(cands, key=lambda x: x["score"], reverse=True)[:3]
            if recs:
                st.markdown(f"##### {t('rec_header')}")
                r_cols = st.columns(len(recs))
                for r_i, r_p in enumerate(recs):
                    with r_cols[r_i]:
                        r_j = get_jersey_svg(r_p["team"], is_gk=(r_p["pos_code"] == 1))
                        render_html(
                            f"""
                            <div class="accessible-card" style="text-align:center; padding:10px;">
                                {r_j}
                                <b>{r_p['name']}</b> ({r_p['team']})<br>
                                <span class="ltr-tag" style="color:#38bdf8;">£{r_p['cost']:.1f}m | xP: {r_p['xp']}</span>
                                <div style="font-size:10px; color:#cbd5e1; margin:4px 0;">{r_p['reason']}</div>
                                <div class="badge-fdr fdr-{r_p['next_fdr']}"><span class="ltr-tag">{r_p['next_match']}</span></div>
                            </div>
                            """
                        )
                        if st.button(t("buy_player_btn"), key=f"sq_buy_rec_{r_p['id']}", use_container_width=True):
                            for sp in st.session_state.user_squad:
                                if sp["element"] == p_tr_out["id"]:
                                    sp["element"] = r_p["id"]
                                    break
                            st.session_state.user_bank = round(st.session_state.user_bank + p_tr_out["cost"] - r_p["cost"], 1)
                            st.session_state.transfers_log.append(f"{p_tr_out['name']} ⬅️ {r_p['name']}")
                            st.session_state.squad_transfer_active = False
                            st.session_state.squad_selected_id = None
                            st.toast(f"✅ {p_tr_out['name']} ⬅️ {r_p['name']}")
                            st.rerun()
            
            st.write("")
            all_sorted = sorted(cands, key=lambda x: x["total_points"], reverse=True)
            if all_sorted:
                cand_map = {p["id"]: f"{p['name']} ({p['team']}) | £{p['cost']:.1f}m | {p['total_points']} {t('pts')} | xP: {p['xp']} | {t('against')} {p['next_match']}" for p in all_sorted}
                c_c1, c_c2 = st.columns([3, 1])
                with c_c1:
                    chosen_p_id = st.selectbox(t("all_cands_label"), list(cand_map.keys()), format_func=lambda x: cand_map[x], key="sq_tr_pool_sel")
                with c_c2:
                    st.write("")
                    if st.button(t("confirm_transfer_btn"), key="sq_confirm_pool_tr", use_container_width=True):
                        chosen_p = all_players[chosen_p_id]
                        for sp in st.session_state.user_squad:
                            if sp["element"] == p_tr_out["id"]:
                                sp["element"] = chosen_p_id
                                break
                        st.session_state.user_bank = round(st.session_state.user_bank + p_tr_out["cost"] - chosen_p["cost"], 1)
                        st.session_state.transfers_log.append(f"{p_tr_out['name']} ⬅️ {chosen_p['name']}")
                        st.session_state.squad_transfer_active = False
                        st.session_state.squad_selected_id = None
                        st.toast(f"✅ {p_tr_out['name']} ⬅️ {chosen_p['name']}")
                        st.rerun()

    # ספסל נקי ומרווח מתחת למגרש
    st.markdown(f"**{t('bench_title')}**")
    with st.container():
        st.markdown('<div class="bench-anchor"></div>', unsafe_allow_html=True)
        render_clean_squad_row(bench, is_bench=True)

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
                st.session_state.planner_selected_id = None
                st.session_state.planner_swap_active = False
                st.session_state.planner_transfer_out = None
                st.session_state.planner_rebuild_active = None
                st.session_state.planner_rebuild_picks = []
                st.session_state.planner_rebuild_target_pos = None
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
    pre_fh_bank = current_sim_bank
    active_lineup_positions = None

    for idx, g in enumerate(range(next_gw, max_sim_gw + 1)):
        gw_plan = st.session_state.planner_plan[g]
        active_chip = gw_plan["chip"]
        planned_transfers = gw_plan["transfers"]

        if pre_fh_squad is not None:
            current_sim_squad = [dict(p) for p in pre_fh_squad]
            current_sim_bank = pre_fh_bank
            pre_fh_squad = None

        if active_chip == "Free Hit" and pre_fh_squad is None:
            pre_fh_squad = [dict(p) for p in current_sim_squad]
            pre_fh_bank = current_sim_bank

        if gw_plan.get("rebuilt_squad"):
            current_sim_squad = [dict(p) for p in gw_plan["rebuilt_squad"]]
            current_sim_bank = float(gw_plan.get("rebuilt_bank", current_sim_bank))
            active_lineup_positions = None

        if gw_plan.get("lineup_positions"):
            active_lineup_positions = dict(gw_plan["lineup_positions"])

        if active_lineup_positions:
            for sp in current_sim_squad:
                if sp["element"] in active_lineup_positions:
                    sp["position"] = active_lineup_positions[sp["element"]]

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

        for out_id, in_id in planned_transfers:
            for sp in current_sim_squad:
                if sp["element"] == out_id:
                    p_out_cost = all_players[out_id]["cost"]
                    p_in_cost = all_players[in_id]["cost"]
                    current_sim_bank = round(current_sim_bank + p_out_cost - p_in_cost, 1)
                    sp["element"] = in_id
                    break

        num_transfers = len(planned_transfers)
        if active_chip in ["Wildcard", "Free Hit"] or gw_plan.get("rebuilt_squad"):
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
                    "element": pid,
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
        st.metric(t("ft_available"), f"{cur_gw_sim['available_fts']} FT")
    with pk2:
        st.metric(t("ft_planned"), f"{cur_gw_sim['transfers_count']}")
    with pk3:
        hit_label = f"-{cur_gw_sim['hits_cost']} {t('pts')}" if cur_gw_sim["hits_cost"] > 0 else "0"
        st.metric(t("hit_penalty"), hit_label)
    with pk4:
        st.metric(t("bank_bal"), f"£{cur_gw_sim['bank']:.1f}m")
    with pk5:
        st.metric(t("xp_pred"), f"{cur_gw_sim['xp']}")

    st.write("---")

    # ניהול צ'יפים ובנייה מחדש
    c_cp1, c_cp2, c_cp3 = st.columns([1, 1.2, 1.2])
    with c_cp1:
        current_chip_val = st.session_state.planner_plan[selected_gw]["chip"]
        chip_opts = ["ללא צ'יפ", "Wildcard", "Free Hit", "Bench Boost", "Triple Captain"]
        chosen_chip = st.selectbox(
            f"🎮 {t('chip_for_gw')} {selected_gw}:",
            chip_opts,
            index=chip_opts.index(current_chip_val) if current_chip_val in chip_opts else 0,
            key=f"chip_select_{selected_gw}",
        )
        if chosen_chip != current_chip_val:
            st.session_state.planner_plan[selected_gw]["chip"] = chosen_chip
            st.rerun()

    with c_cp2:
        if st.session_state.planner_plan[selected_gw]["transfers"]:
            st.markdown(f"**{t('planned_transfers_gw')} {selected_gw}:**")
            for tr_idx, (o_id, i_id) in enumerate(list(st.session_state.planner_plan[selected_gw]["transfers"])):
                c_tr_t, c_tr_b = st.columns([3.5, 1.5])
                with c_tr_t:
                    st.caption(f"🔴 {all_players[o_id]['name']} ⬅️ 🟢 {all_players[i_id]['name']}")
                with c_tr_b:
                    if st.button(f"✕ {t('cancel_single_transfer')}", key=f"del_tr_{selected_gw}_{tr_idx}", use_container_width=True):
                        st.session_state.planner_plan[selected_gw]["transfers"].pop(tr_idx)
                        st.session_state.planner_transfer_out = None
                        st.rerun()
            if st.button(t("clear_all_transfers"), key=f"clr_tr_{selected_gw}", use_container_width=True):
                st.session_state.planner_plan[selected_gw]["transfers"] = []
                st.session_state.planner_transfer_out = None
                st.rerun()
        elif st.session_state.planner_plan[selected_gw].get("rebuilt_squad"):
            st.success("✅ סגל נבנה מחדש מאפס למחזור זה" if st.session_state.app_lang == "he" else "✅ Squad rebuilt from scratch for this GW")
            if st.button("↩️ אפס וחזור לסגל המקורי" if st.session_state.app_lang == "he" else "↩️ Reset to original squad", key=f"clr_rebuild_{selected_gw}"):
                del st.session_state.planner_plan[selected_gw]["rebuilt_squad"]
                if "rebuilt_bank" in st.session_state.planner_plan[selected_gw]:
                    del st.session_state.planner_plan[selected_gw]["rebuilt_bank"]
                st.rerun()

    with c_cp3:
        st.write("")
        is_rebuilding_this_gw = (st.session_state.get("planner_rebuild_active") == selected_gw)
        btn_rebuild_lbl = t("close_rebuild_btn") if is_rebuilding_this_gw else t("rebuild_btn")
        btn_rebuild_type = "secondary" if is_rebuilding_this_gw else "primary"
        if st.button(btn_rebuild_lbl, key=f"toggle_rebuild_{selected_gw}", type=btn_rebuild_type, use_container_width=True):
            if is_rebuilding_this_gw:
                st.session_state.planner_rebuild_active = None
                st.session_state.planner_rebuild_target_pos = None
            else:
                st.session_state.planner_rebuild_active = selected_gw
                snap_squad = cur_gw_sim["squad_snapshot"]
                team_val = sum(all_players[p["element"]]["cost"] for p in snap_squad if p["element"] in all_players)
                st.session_state.planner_rebuild_total_budget = round(team_val + cur_gw_sim["bank"], 1)
                st.session_state.planner_rebuild_picks = []
                st.session_state.planner_rebuild_target_pos = None
            st.rerun()

    # פונקציות עזר למגרש הפלנר
    def execute_planner_bench_swap(p_out_id, p_in_id):
        legal, err_msg = is_swap_legal(p_out_id, p_in_id, cur_gw_sim["squad_snapshot"])
        if not legal:
            st.error(f"⚠️ {err_msg}")
            return
        snap = cur_gw_sim["squad_snapshot"]
        p_o = next((x for x in snap if x["element"] == p_out_id), None)
        p_i = next((x for x in snap if x["element"] == p_in_id), None)
        if p_o and p_i:
            p_o["position"], p_i["position"] = p_i["position"], p_o["position"]
            if "lineup_positions" not in st.session_state.planner_plan[selected_gw]:
                st.session_state.planner_plan[selected_gw]["lineup_positions"] = {}
            for sp in snap:
                st.session_state.planner_plan[selected_gw]["lineup_positions"][sp["element"]] = sp["position"]

            if selected_gw == next_gw:
                orig_o = next((x for x in st.session_state.user_squad if x["element"] == p_out_id), None)
                orig_i = next((x for x in st.session_state.user_squad if x["element"] == p_in_id), None)
                if orig_o and orig_i:
                    orig_o["position"], orig_i["position"] = orig_i["position"], orig_o["position"]
            st.session_state.planner_selected_id = None
            st.session_state.planner_swap_active = False
            st.toast(f"✅ {all_players[p_out_id]['name']} ⇄ {all_players[p_in_id]['name']}")
            st.rerun()

    def set_planner_captain(target_id):
        if selected_gw not in st.session_state.planner_captains:
            st.session_state.planner_captains[selected_gw] = {}
        st.session_state.planner_captains[selected_gw]["cap"] = target_id
        st.session_state.planner_selected_id = None
        st.toast(f"👑 {all_players[target_id]['name']} (C) GW {selected_gw}")
        st.rerun()

    def set_planner_vice_captain(target_id):
        if selected_gw not in st.session_state.planner_captains:
            st.session_state.planner_captains[selected_gw] = {}
        st.session_state.planner_captains[selected_gw]["vc"] = target_id
        st.session_state.planner_selected_id = None
        st.toast(f"🥈 {all_players[target_id]['name']} (VC) GW {selected_gw}")
        st.rerun()

    # רינדור מגרש פלנר נקי
    def render_clean_planner_row(player_list, is_bench=False):
        if not player_list:
            return
        if len(player_list) == 1:
            cols = [st.columns([2, 1, 2])[1]]
        else:
            cols = st.columns(len(player_list))
        for i, p in enumerate(player_list):
            with cols[i]:
                is_this_selected = (st.session_state.planner_selected_id == p["id"])
                is_tr_selected = (st.session_state.planner_transfer_out == p["id"])
                st.markdown(render_player_card_html(p, is_bench=is_bench, is_selected=is_this_selected, is_transfer_selected=is_tr_selected, target_gw=selected_gw), unsafe_allow_html=True)
                
                if st.session_state.planner_swap_active:
                    if is_this_selected:
                        if st.button(t("btn_selected"), key=f"pl_b_{p['id']}_{selected_gw}", use_container_width=True, type="primary"):
                            st.session_state.planner_swap_active = False
                            st.session_state.planner_selected_id = None
                            st.rerun()
                    else:
                        legal, reason = is_swap_legal(st.session_state.planner_selected_id, p["id"], cur_gw_sim["squad_snapshot"])
                        if legal:
                            if st.button(t("btn_swap_here"), key=f"pl_b_{p['id']}_{selected_gw}", use_container_width=True, type="primary"):
                                execute_planner_bench_swap(st.session_state.planner_selected_id, p["id"])
                        else:
                            st.button(f"✕ {reason}", key=f"pl_b_{p['id']}_{selected_gw}", use_container_width=True, disabled=True)
                else:
                    btn_lbl = t("btn_selected") if is_this_selected else ("C" if p.get("is_cap") else ("VC" if p.get("is_vc") else t("btn_select")))
                    btn_type = "primary" if is_this_selected else "secondary"
                    if st.button(btn_lbl, key=f"pl_b_{p['id']}_{selected_gw}", use_container_width=True, type=btn_type):
                        if is_this_selected:
                            st.session_state.planner_selected_id = None
                            st.session_state.planner_transfer_out = None
                        else:
                            st.session_state.planner_selected_id = p["id"]
                            st.session_state.planner_transfer_out = None
                        st.rerun()

    # בדיקה האם נמצאים במצב בנייה מחדש מאפס עבור מחזור זה
    if st.session_state.get("planner_rebuild_active") == selected_gw:
        rebuild_picks = st.session_state.get("planner_rebuild_picks", [])
        total_budget = st.session_state.get("planner_rebuild_total_budget", 100.0)
        spent = sum(all_players[pid]["cost"] for pid in rebuild_picks if pid in all_players)
        rem_budget = round(total_budget - spent, 1)
        num_picks = len(rebuild_picks)
        empty_slots = 15 - num_picks
        avg_budget = round(rem_budget / max(1, empty_slots), 1) if empty_slots > 0 else 0.0

        pos_counts_rb = {1: 0, 2: 0, 3: 0, 4: 0}
        team_counts_rb = {}
        for pid in rebuild_picks:
            if pid in all_players:
                p_item = all_players[pid]
                pos_counts_rb[p_item["pos_code"]] += 1
                t = p_item["team"]
                team_counts_rb[t] = team_counts_rb.get(t, 0) + 1

        over_limit_teams = [f"{t} ({c}/3)" for t, c in team_counts_rb.items() if c > 3]
        budget_color = "#10b981" if rem_budget >= 0 else "#ef4444"

        render_html(
            f"""
            <div class="rebuild-banner">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:8px;">
                    <div>
                        <span style="font-size:16px; font-weight:800; color:#38bdf8;">🛠️ לוח בניית סגל מאפס — Gameweek {selected_gw}</span>
                        <div style="font-size:12px; color:#94a3b8;">בחר 15 שחקנים (2 שוערים, 5 מגנים, 5 קשרים, 3 חלוצים) במסגרת התקציב</div>
                    </div>
                    <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
                        <div style="text-align:center; background:#111a28; border:1px solid #1e2e46; padding:5px 10px; border-radius:8px;">
                            <div style="font-size:10px; color:#94a3b8;">שווי סגל כולל</div>
                            <div style="font-size:14px; font-weight:700; color:#f8fafc;"><span class="ltr-tag">£{total_budget:.1f}m</span></div>
                        </div>
                        <div style="text-align:center; background:#111a28; border:1px solid {budget_color}; padding:5px 10px; border-radius:8px;">
                            <div style="font-size:10px; color:#94a3b8;">תקציב פנוי נותר</div>
                            <div style="font-size:16px; font-weight:800; color:{budget_color};"><span class="ltr-tag">£{rem_budget:.1f}m</span></div>
                        </div>
                        <div style="text-align:center; background:#111a28; border:1px solid #1e2e46; padding:5px 10px; border-radius:8px;">
                            <div style="font-size:10px; color:#94a3b8;">שחקנים שנבחרו</div>
                            <div style="font-size:14px; font-weight:700; color:#38bdf8;">{num_picks} / 15</div>
                        </div>
                        <div style="text-align:center; background:#111a28; border:1px solid #1e2e46; padding:5px 10px; border-radius:8px;">
                            <div style="font-size:10px; color:#94a3b8;">ממוצע לשחקן</div>
                            <div style="font-size:14px; font-weight:700; color:#f8fafc;"><span class="ltr-tag">£{avg_budget:.1f}m</span></div>
                        </div>
                    </div>
                </div>
            </div>
            """
        )

        if over_limit_teams:
            st.error(f"⚠️ חריגת מכסה! חוק ה-FPL אוסר יותר מ-3 שחקנים ממועדון אחד: {', '.join(over_limit_teams)}")
        if rem_budget < 0:
            st.error(f"⚠️ חריגת תקציב של £{abs(rem_budget):.1f}m! עליך לפנות שחקן או לבחור שחקנים זולים יותר.")

        c_rb_act1, c_rb_act2, c_rb_act3, c_rb_act4 = st.columns([1, 1.2, 1.4, 1])
        with c_rb_act1:
            if st.button("🗑️ רוקן את כל 15 השחקנים", key="rb_clear_all", use_container_width=True):
                st.session_state.planner_rebuild_picks = []
                st.session_state.planner_rebuild_target_pos = None
                st.rerun()
        with c_rb_act2:
            if st.button("📋 טען שחקנים מסגל קיים", key="rb_load_existing", use_container_width=True):
                st.session_state.planner_rebuild_picks = [p["element"] for p in cur_gw_sim["squad_snapshot"]]
                st.session_state.planner_rebuild_target_pos = None
                st.rerun()
        with c_rb_act3:
            is_ready_to_save = (num_picks == 15 and rem_budget >= 0 and not over_limit_teams and pos_counts_rb[1] == 2 and pos_counts_rb[2] == 5 and pos_counts_rb[3] == 5 and pos_counts_rb[4] == 3)
            if is_ready_to_save:
                if st.button("💾 אשר ושמור סגל חדש!", key="rb_save_squad", type="primary", use_container_width=True):
                    rb_gks = [p for p in rebuild_picks if all_players[p]["pos_code"] == 1]
                    rb_defs = [p for p in rebuild_picks if all_players[p]["pos_code"] == 2]
                    rb_mids = [p for p in rebuild_picks if all_players[p]["pos_code"] == 3]
                    rb_fwds = [p for p in rebuild_picks if all_players[p]["pos_code"] == 4]

                    rb_gks_sorted = sorted(rb_gks, key=lambda x: all_players[x]["xp"], reverse=True)
                    starter_gk = [rb_gks_sorted[0]]
                    bench_gk = [rb_gks_sorted[1]]

                    rb_defs_sorted = sorted(rb_defs, key=lambda x: all_players[x]["xp"], reverse=True)
                    rb_mids_sorted = sorted(rb_mids, key=lambda x: all_players[x]["xp"], reverse=True)
                    rb_fwds_sorted = sorted(rb_fwds, key=lambda x: all_players[x]["xp"], reverse=True)

                    guaranteed_starters = rb_defs_sorted[:3] + rb_mids_sorted[:2] + rb_fwds_sorted[:1]
                    leftover_pool = sorted(rb_defs_sorted[3:] + rb_mids_sorted[2:] + rb_fwds_sorted[1:], key=lambda x: all_players[x]["xp"], reverse=True)

                    additional_starters = []
                    bench_outfield = []
                    d_cnt, m_cnt, f_cnt = 3, 2, 1
                    for pid in leftover_pool:
                        pos = all_players[pid]["pos_code"]
                        if len(additional_starters) < 4:
                            if pos == 2 and d_cnt < 5:
                                additional_starters.append(pid); d_cnt += 1
                            elif pos == 3 and m_cnt < 5:
                                additional_starters.append(pid); m_cnt += 1
                            elif pos == 4 and f_cnt < 3:
                                additional_starters.append(pid); f_cnt += 1
                            else:
                                bench_outfield.append(pid)
                        else:
                            bench_outfield.append(pid)

                    all_starters_ids = starter_gk + guaranteed_starters + additional_starters
                    all_bench_ids = bench_gk + bench_outfield

                    sorted_by_xp = sorted(all_starters_ids, key=lambda x: all_players[x]["xp"], reverse=True)
                    cap_id = sorted_by_xp[0]
                    vc_id = sorted_by_xp[1]

                    final_rebuilt_squad = []
                    pos_counter = 1
                    for pid in all_starters_ids:
                        final_rebuilt_squad.append({
                            "element": pid,
                            "position": pos_counter,
                            "is_captain": (pid == cap_id),
                            "is_vice_captain": (pid == vc_id),
                        })
                        pos_counter += 1
                    for pid in all_bench_ids:
                        final_rebuilt_squad.append({
                            "element": pid,
                            "position": pos_counter,
                            "is_captain": False,
                            "is_vice_captain": False,
                        })
                        pos_counter += 1

                    st.session_state.planner_plan[selected_gw]["rebuilt_squad"] = final_rebuilt_squad
                    st.session_state.planner_plan[selected_gw]["rebuilt_bank"] = rem_budget

                    if st.session_state.planner_plan[selected_gw]["chip"] == "ללא צ'יפ":
                        st.session_state.planner_plan[selected_gw]["chip"] = "Wildcard"

                    st.session_state.planner_rebuild_active = None
                    st.session_state.planner_rebuild_picks = []
                    st.session_state.planner_rebuild_target_pos = None
                    st.toast(f"🎉 סגל חדש נשמר בהצלחה למחזור {selected_gw}!")
                    st.rerun()
            else:
                st.button(f"💾 אשר ושמור סגל ({num_picks}/15)", disabled=True, use_container_width=True)
        with c_rb_act4:
            if st.button("✕ סגור ללא שמירה", key="rb_cancel_btn", use_container_width=True):
                st.session_state.planner_rebuild_active = None
                st.session_state.planner_rebuild_target_pos = None
                st.rerun()

        st.write("")

        # פריסת המשבצות לפי עמדות
        pos_cfg = [
            {"code": 1, "name": "שוערים", "singular": "שוער", "req": 2, "icon": "🧤"},
            {"code": 2, "name": "מגנים", "singular": "מגן", "req": 5, "icon": "🛡️"},
            {"code": 3, "name": "קשרים", "singular": "קשר", "req": 5, "icon": "👟"},
            {"code": 4, "name": "חלוצים", "singular": "חלוץ", "req": 3, "icon": "🎯"},
        ]

        def remove_rebuild_player(pid_to_remove):
            if pid_to_remove in st.session_state.planner_rebuild_picks:
                st.session_state.planner_rebuild_picks.remove(pid_to_remove)
                st.rerun()

        def select_target_rebuild_pos(pos_code):
            st.session_state.planner_rebuild_target_pos = pos_code
            st.rerun()

        for sec in pos_cfg:
            p_code = sec["code"]
            sec_name = sec["name"]
            sing_name = sec["singular"]
            req_cnt = sec["req"]
            icon = sec["icon"]
            cur_pids = [pid for pid in rebuild_picks if pid in all_players and all_players[pid]["pos_code"] == p_code]
            cur_cnt = len(cur_pids)

            st.markdown(f"**{icon} {sec_name} ({cur_cnt}/{req_cnt}):**")
            cols = st.columns(req_cnt)
            for slot_idx in range(req_cnt):
                with cols[slot_idx]:
                    if slot_idx < len(cur_pids):
                        pid = cur_pids[slot_idx]
                        p_data = all_players[pid]
                        st.markdown(render_player_card_html(p_data, target_gw=selected_gw), unsafe_allow_html=True)
                        if st.button(f"✕ הסר", key=f"rb_rem_{pid}_{slot_idx}", use_container_width=True):
                            remove_rebuild_player(pid)
                    else:
                        is_active_pos = (st.session_state.get("planner_rebuild_target_pos") == p_code)
                        border_color = "#38bdf8" if is_active_pos else "#334155"
                        bg_color = "rgba(56, 189, 248, 0.12)" if is_active_pos else "rgba(15, 23, 42, 0.6)"

                        render_html(
                            f"""
                            <div style="background:{bg_color}; border:2px dashed {border_color}; border-radius:8px; padding:18px 4px; text-align:center; margin:0 auto 4px auto; max-width:120px;">
                                <div style="font-size:22px; opacity:0.6;">{icon}</div>
                                <div style="font-size:10px; color:#94a3b8; font-weight:700; margin-top:2px;">משבצת פנויה</div>
                            </div>
                            """
                        )
                        btn_lbl = "✓ נבחרה" if is_active_pos else f"➕ הוסף {sing_name}"
                        btn_t = "primary" if is_active_pos else "secondary"
                        if st.button(btn_lbl, key=f"rb_add_{p_code}_{slot_idx}", type=btn_t, use_container_width=True):
                            select_target_rebuild_pos(p_code)
            st.write("")

        # מגירת בחירת שחקן לעמדה
        active_pos = st.session_state.get("planner_rebuild_target_pos")
        if active_pos is not None:
            pos_dict_names = {1: "שוער", 2: "מגן", 3: "קשר", 4: "חלוץ"}
            pos_title = pos_dict_names[active_pos]

            other_empty_slots = max(0, empty_slots - 1)
            reserved_funds = other_empty_slots * 4.0
            max_allowed_price = round(rem_budget - reserved_funds, 1)

            render_html(
                f"""
                <div class="transfer-drawer">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:8px;">
                        <div>
                            <span style="font-size:15px; font-weight:800; color:#38bdf8;">🛒 בחירת {pos_title} לסגל (תקציב פנוי: £{rem_budget:.1f}m)</span>
                            <div style="font-size:11px; color:#cbd5e1;">מחיר מקסימלי אפשרי לעמדה זו (משריין £4.0m ליתר המשבצות): <b style="color:#10b981;">£{max_allowed_price:.1f}m</b></div>
                        </div>
                    </div>
                </div>
                """
            )

            c_cl_btn, c_sch_inp = st.columns([1, 3])
            with c_cl_btn:
                if st.button("✕ סגור מגירה", key="rb_close_picker", use_container_width=True, type="primary"):
                    st.session_state.planner_rebuild_target_pos = None
                    st.rerun()
            with c_sch_inp:
                rb_search = st.text_input("חיפוש שחקן (שם או קבוצה באנגלית):", key=f"rb_search_{selected_gw}_{active_pos}").strip().lower()

            candidates = [
                p for p in all_players.values()
                if p["pos_code"] == active_pos
                and p["id"] not in rebuild_picks
                and p["cost"] <= max_allowed_price
                and team_counts_rb.get(p["team"], 0) < 3
                and p["status"] == "a"
            ]
            if rb_search:
                candidates = [p for p in candidates if rb_search in p["name"].lower() or rb_search in p["team"].lower()]

            rb_recs = sorted(candidates, key=lambda x: x["score"], reverse=True)[:3]
            if rb_recs:
                st.markdown(f"##### ⭐ {pos_title}ים מומלצים (Recommended):")
                rec_cols = st.columns(len(rb_recs))
                for r_idx, r_p in enumerate(rb_recs):
                    with rec_cols[r_idx]:
                        r_jersey = get_jersey_svg(r_p["team"], is_gk=(r_p["pos_code"] == 1))
                        render_html(
                            f"""
                            <div class="accessible-card" style="text-align:center; padding:10px;">
                                {r_jersey}
                                <b>{r_p['name']}</b> ({r_p['team']})<br>
                                <span class="ltr-tag" style="color:#38bdf8;">£{r_p['cost']:.1f}m | xP: {r_p['xp']}</span>
                                <div style="font-size:10px; color:#cbd5e1; margin:4px 0;">{r_p['reason']}</div>
                                <div class="badge-fdr fdr-{r_p['next_fdr']}"><span class="ltr-tag">{r_p['next_match']}</span></div>
                            </div>
                            """
                        )
                        if st.button(f"➕ הוסף את {r_p['name']}", key=f"rb_pick_rec_{r_p['id']}", use_container_width=True):
                            st.session_state.planner_rebuild_picks.append(r_p["id"])
                            updated_pos_count = sum(1 for pid in st.session_state.planner_rebuild_picks if all_players[pid]["pos_code"] == active_pos)
                            req_for_pos = {1: 2, 2: 5, 3: 5, 4: 3}[active_pos]
                            if updated_pos_count >= req_for_pos:
                                st.session_state.planner_rebuild_target_pos = None
                            st.rerun()

            st.write("")
            all_cands_sorted = sorted(candidates, key=lambda x: x["total_points"], reverse=True)
            if all_cands_sorted:
                cand_opts = {p["id"]: f"{p['name']} ({p['team']}) | £{p['cost']:.1f}m | {p['total_points']} נק׳ | xP: {p['xp']} | מול: {p['next_match']}" for p in all_cands_sorted}
                c_c_sel, c_c_btn = st.columns([3, 1])
                with c_c_sel:
                    chosen_cand_id = st.selectbox(
                        f"או בחר מתוך כל ה{pos_title}ים הזמינים בתקציב:",
                        list(cand_opts.keys()),
                        format_func=lambda x: cand_opts[x],
                        key=f"rb_pool_sel_{active_pos}",
                    )
                with c_c_btn:
                    st.write("")
                    if st.button("➕ הוסף שחקן זה", key=f"rb_add_chosen_{active_pos}", use_container_width=True):
                        st.session_state.planner_rebuild_picks.append(chosen_cand_id)
                        updated_pos_count = sum(1 for pid in st.session_state.planner_rebuild_picks if all_players[pid]["pos_code"] == active_pos)
                        req_for_pos = {1: 2, 2: 5, 3: 5, 4: 3}[active_pos]
                        if updated_pos_count >= req_for_pos:
                            st.session_state.planner_rebuild_target_pos = None
                        st.rerun()
            else:
                st.warning(f"לא נמצאו שחקנים מתאימים בעמדת {pos_title} במסגרת התקציב של £{max_allowed_price:.1f}m.")
    else:
        # מגרש פלנר
        if st.session_state.planner_swap_active and st.session_state.planner_selected_id:
            p_pl_sw_from = all_players.get(st.session_state.planner_selected_id)
            if p_pl_sw_from:
                c_sw_info, c_sw_canc = st.columns([4, 1])
                with c_sw_info:
                    st.info(f"🔁 **{t('swap_banner_title')}** {t('swap_banner_desc')} **{p_pl_sw_from['name']}** ({p_pl_sw_from['team']} | {p_pl_sw_from['pos']})")
                with c_sw_canc:
                    if st.button(t("cancel_swap"), key=f"pl_cancel_swap_top_{selected_gw}", use_container_width=True, type="primary"):
                        st.session_state.planner_swap_active = False
                        st.session_state.planner_selected_id = None
                        st.rerun()

        st.markdown(f"#### 🏟️ {t('tab_squad')} — Gameweek {selected_gw}")
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
                render_clean_planner_row(pl_gks)

        # -----------------------------------------------------------------
        # שורת ניהול והעברות בפלנר - ממוקמת בלעדית מתחת למגרש!
        # -----------------------------------------------------------------
        if st.session_state.planner_selected_id is not None and not st.session_state.planner_swap_active and not st.session_state.planner_transfer_out:
            p_pl_sel = all_players.get(st.session_state.planner_selected_id)
            if p_pl_sel:
                is_pl_starter = any(p["id"] == p_pl_sel["id"] for p in cur_gw_sim["starters"])
                j_svg_pl = get_jersey_svg(p_pl_sel["team"], is_gk=(p_pl_sel["pos_code"] == 1))
                render_html(
                    f"""
                    <div class="action-bar-under-pitch">
                        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                            <div style="display:flex; align-items:center; gap:8px;">
                                {j_svg_pl}
                                <div>
                                    <span style="font-size:13px; font-weight:700; color:#38bdf8;">{t('action_bar_title')} (GW {selected_gw}):</span>
                                    <b style="color:#ffffff; font-size:14px; margin:0 4px;">{p_pl_sel['name']}</b>
                                    <span class="ltr-tag" style="color:#94a3b8; font-size:12px;">({p_pl_sel['team']} | {p_pl_sel['pos']} | £{p_pl_sel['cost']}m | xP: {p_pl_sel['xp']})</span>
                                </div>
                            </div>
                            <div style="font-size:11px; color:#cbd5e1;">
                                {t('action_bar_hint')}
                            </div>
                        </div>
                    </div>
                    """
                )

                c_pa1, c_pa2, c_pa3, c_pa4, c_pa5 = st.columns([1, 1, 1.2, 1.2, 0.8])
                with c_pa1:
                    if is_pl_starter:
                        if st.button(f"👑 {t('btn_captain')}", key=f"pl_set_c_{selected_gw}", use_container_width=True, type="primary"):
                            set_planner_captain(p_pl_sel["id"])
                    else:
                        st.button(f"👑 {t('btn_captain')}", disabled=True, help=t("starters_only_cap"), use_container_width=True)
                with c_pa2:
                    if is_pl_starter:
                        if st.button(f"🥈 {t('btn_vc')}", key=f"pl_set_vc_{selected_gw}", use_container_width=True):
                            set_planner_vice_captain(p_pl_sel["id"])
                    else:
                        st.button(f"🥈 {t('btn_vc')}", disabled=True, help=t("starters_only_cap"), use_container_width=True)
                with c_pa3:
                    if st.button(t("btn_sub"), key=f"pl_open_sub_{selected_gw}", use_container_width=True, type="primary"):
                        st.session_state.planner_swap_active = True
                        st.rerun()
                with c_pa4:
                    if st.button(t("btn_transfer"), key=f"pl_open_tr_{selected_gw}", use_container_width=True):
                        st.session_state.planner_transfer_out = p_pl_sel["id"]
                        st.rerun()
                with c_pa5:
                    if st.button(f"✕ {t('btn_cancel')}", key=f"pl_cancel_{selected_gw}", use_container_width=True):
                        st.session_state.planner_selected_id = None
                        st.session_state.planner_swap_active = False
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
                            <span style="font-size:15px; font-weight:700; color:#38bdf8;">{t('transfer_drawer_title')} (GW {selected_gw})</span>
                            <div style="font-size:12px; color:#cbd5e1;">
                                {t('selling_player')} <b style="color:#ef4444;">{p_tr_out['name']}</b> ({p_tr_out['pos']} - £{p_tr_out['cost']}m) | 
                                {t('max_budget')} <b style="color:#10b981;">£{max_tr_budget:.1f}m</b>
                            </div>
                        </div>
                    </div>
                </div>
                """
            )

            b_close_col, b_sch_col = st.columns([1, 3])
            with b_close_col:
                if st.button(t("close_drawer"), key=f"close_tr_drawer_{selected_gw}", type="primary", use_container_width=True):
                    st.session_state.planner_transfer_out = None
                    st.rerun()
            with b_sch_col:
                tr_search = st.text_input(t("search_placeholder"), key=f"tr_search_{selected_gw}").strip().lower()

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
                st.markdown(f"##### {t('rec_header')}")
                rec_cols = st.columns(len(recommended_picks))
                for r_idx, r_p in enumerate(recommended_picks):
                    with rec_cols[r_idx]:
                        r_jersey = get_jersey_svg(r_p["team"], is_gk=(r_p["pos_code"] == 1))
                        render_html(
                            f"""
                            <div class="accessible-card" style="text-align:center; padding:10px;">
                                {r_jersey}
                                <b>{r_p['name']}</b> ({r_p['team']})<br>
                                <span class="ltr-tag" style="color:#38bdf8;">£{r_p['cost']:.1f}m | xP: {r_p['xp']}</span>
                                <div style="font-size:10px; color:#cbd5e1; margin:4px 0;">{r_p['reason']}</div>
                                <div class="badge-fdr fdr-{r_p['next_fdr']}"><span class="ltr-tag">{r_p['next_match']}</span></div>
                            </div>
                            """
                        )
                        if st.button(f"{t('buy_player_btn')} {r_p['name']}", key=f"buy_rec_{r_p['id']}_{selected_gw}", use_container_width=True):
                            st.session_state.planner_plan[selected_gw]["transfers"].append(
                                (p_tr_out["id"], r_p["id"])
                            )
                            st.session_state.planner_transfer_out = None
                            st.session_state.planner_selected_id = None
                            st.session_state.planner_swap_active = False
                            st.toast(f"✅ {r_p['name']} ({r_p['team']})")
                            st.rerun()

            st.write("")
            all_sorted_by_pts = sorted(eligible_pool, key=lambda x: x["total_points"], reverse=True)

            if all_sorted_by_pts:
                pick_opts = {p["id"]: f"{p['name']} ({p['team']}) | £{p['cost']:.1f}m | {p['total_points']} {t('pts')} | xP: {p['xp']} | {t('against')} {p['next_match']}" for p in all_sorted_by_pts}
                c_sel_p, c_btn_p = st.columns([3, 1])
                with c_sel_p:
                    chosen_pool_id = st.selectbox(
                        t("all_cands_label"),
                        list(pick_opts.keys()),
                        format_func=lambda x: pick_opts[x],
                        key=f"pool_sel_{selected_gw}",
                    )
                with c_btn_p:
                    st.write("")
                    if st.button(t("confirm_transfer_btn"), key=f"confirm_pool_{selected_gw}", use_container_width=True):
                        st.session_state.planner_plan[selected_gw]["transfers"].append(
                            (p_tr_out["id"], chosen_pool_id)
                        )
                        st.session_state.planner_transfer_out = None
                        st.session_state.planner_selected_id = None
                        st.session_state.planner_swap_active = False
                        st.toast(f"✅ {p_tr_out['name']} ⬅️ {all_players[chosen_pool_id]['name']}")
                        st.rerun()
            else:
                st.warning("לא נמצאו שחקנים מתאימים במסגרת התקציב." if st.session_state.app_lang == "he" else "No eligible players found within budget.")

        # ספסל ב-Planner
        st.markdown(f"**{t('bench_title')}**")
        with st.container():
            st.markdown('<div class="bench-anchor"></div>', unsafe_allow_html=True)
            render_clean_planner_row(cur_gw_sim["bench"], is_bench=True)

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
    user_league_options = {l["id"]: l["name"] for l in my_leagues if l.get("league_type") == "x" or "League" in l.get("name", "")}

    col_l1, col_l2 = st.columns([2, 1])
    with col_l1:
        if user_league_options:
            sel_user_lid = st.selectbox(
                "בחר מתוך המיני-ליגות של הקבוצה שלך:",
                list(user_league_options.keys()),
                format_func=lambda x: user_league_options[x],
            )
            league_id_input = str(sel_user_lid)
        else:
            league_id_input = st.text_input("הזן קוד מיני-ליגה קלאסית (League ID):", placeholder="למשל: 314 או קוד הליגה של החברים").strip()
    with col_l2:
        st.write("")
        custom_lid = st.text_input("או חפש לפי קוד ליגה אחר:", placeholder="קוד ליגה ידני...").strip()
        if custom_lid and custom_lid.isdigit():
            league_id_input = custom_lid

    if league_id_input and league_id_input.isdigit():
        league_data = fetch_classic_league_standings(int(league_id_input))
        if league_data and "standings" in league_data:
            l_info = league_data.get("league", {})
            results = league_data["standings"].get("results", [])

            st.markdown(f"#### 🏅 טבלת ליגה: **{l_info.get('name', 'Classic League')}**")

            if results:
                leader = results[0]
                my_entry = next((r for r in results if str(r["entry"]) == str(team_id)), None)

                c_lg1, c_lg2, c_lg3 = st.columns(3)
                with c_lg1:
                    st.metric("מוביל הליגה", f"{leader['entry_name']}", f"{leader['total']} נק׳")
                with c_lg2:
                    if my_entry:
                        gap = leader["total"] - my_entry["total"]
                        st.metric("המיקום שלך בליגה", f"מקום {my_entry['rank']}", f"פער מהפסגה: -{gap} נק׳")
                    else:
                        st.metric("הקבוצה שלך", "לא משתתפת בליגה זו")
                with c_lg3:
                    st.metric("סך משתתפים בליגה", f"{len(results)}")

                # טבלת תוצאות מעוצבת
                table_rows = []
                for r in results[:20]:
                    is_me = (str(r["entry"]) == str(team_id))
                    prefix = "👉 " if is_me else ""
                    table_rows.append({
                        "מיקום": r["rank"],
                        "שם קבוצה": f"{prefix}{r['entry_name']}",
                        "מאמן": r["player_name"],
                        "מחזור אחרון": r["event_total"],
                        "סך נקודות": r["total"],
                        "ID קבוצה": r["entry"],
                    })
                st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

                # כלי ריגול ראש בראש מול יריב
                st.write("---")
                st.markdown("#### 🕵️ ריגול סגל מול יריב (Head-to-Head Spy)")
                rival_opts = {r["entry"]: f"מקום {r['rank']} - {r['entry_name']} ({r['player_name']})" for r in results if str(r["entry"]) != str(team_id)}
                if rival_opts:
                    chosen_rival_id = st.selectbox("בחר יריב לריגול מעמיק:", list(rival_opts.keys()), format_func=lambda x: rival_opts[x])
                    
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
