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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
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

def render_styled_table(headers, rows, is_rtl=False):
    """רינדור טבלה רספונסיבית מודרנית עם תמיכה מלאה בערכת נושא (Light/Dark) ללא קנבס שחור"""
    align = "right" if is_rtl else "left"
    dir_attr = "rtl" if is_rtl else "ltr"
    th_cells = "".join(f'<th style="padding:10px 12px; text-align:{align}; font-weight:800; font-size:12px; border-bottom:2px solid var(--border-color); color:var(--text-secondary); background:var(--fxt-row-bg); white-space:nowrap;">{h}</th>' for h in headers)
    tr_rows = []
    for row in rows:
        td_cells = "".join(f'<td style="padding:10px 12px; text-align:{align}; border-bottom:1px solid var(--border-color); color:var(--text-primary); vertical-align:middle;">{cell}</td>' for cell in row)
        tr_rows.append(f'<tr style="transition:background 0.15s ease;">{td_cells}</tr>')
    table_body = "".join(tr_rows)
    table_html = f"""
    <div style="width:100%; overflow-x:auto; -webkit-overflow-scrolling:touch; border-radius:12px; border:1px solid var(--border-color); background:var(--bg-card); margin:10px 0; box-shadow:0 4px 14px rgba(0,0,0,0.03); direction:{dir_attr};">
        <table style="width:100%; border-collapse:collapse; font-size:13px; font-family:inherit;">
            <thead>
                <tr>{th_cells}</tr>
            </thead>
            <tbody>
                {table_body}
            </tbody>
        </table>
    </div>
    """
    compact = "".join(line.strip() for line in table_html.splitlines())
    st.markdown(compact, unsafe_allow_html=True)

FPL_SUCCESS_TIPS = [
    {
        "num": 1,
        "icon": "⏳",
        "title_he": "שמירת חילופים (Roll Transfers)",
        "title_en": "Roll Your Free Transfers",
        "desc_he": "אל תבצע חילוף אוטומטי בכל מחזור רק כי יש לך חילוף פנוי. צבירת 2 עד 5 חילופים חינמיים מעניקה גמישות אסטרטגית אדירה למהפכות סגל קטנות ללא קנס נקודות.",
        "desc_en": "Never burn a free transfer just because you have one. Stacking 2 to 5 free transfers provides massive strategic leverage to overhaul multiple positions without taking point hits.",
        "rule_he": "אין מהלך בוער? שמור את החילוף ותהנה מכוח תמרון כפול במחזור הבא.",
        "rule_en": "No urgent move? Roll the transfer and gain double flexibility next week.",
        "tag_he": "סבלנות",
        "tag_en": "Patience",
    },
    {
        "num": 2,
        "icon": "🛡️",
        "title_he": "הימנעות ממינוסים מיותרים (Avoid -4 Hits)",
        "title_en": "Avoid Unnecessary -4 Point Hits",
        "desc_he": "שחקן שנרכש בקנס 4- נקודות נדרש להבקיע או לבשל רק כדי לאפס את העלות שלו. קח מינוס רק במקרה חירום של חוסר 11 שחקנים כשירים או עבור קפטן מובהק לטווח ארוך.",
        "desc_en": "A player bought on a -4 hit must effectively return a goal or assist just to break even. Take hits strictly for injury crises or long-term high-ceiling captains.",
        "rule_he": "מינוסים מצטברים שוחקים את הדירוג: הימנע מהם ככל האפשר.",
        "rule_en": "Point hits erode long-term rank. Take them only for emergencies or long-term holds.",
        "tag_he": "משמעת",
        "tag_en": "Discipline",
    },
    {
        "num": 3,
        "icon": "👑",
        "title_he": "משמעת קפטן ובעלות אפקטיבית (Captaincy)",
        "title_en": "Captaincy Discipline & Effective Ownership",
        "desc_he": "אל תהמר על קפטן הרפתקני רק כדי 'להתחכם'. מעל 60% מהניקוד מגיע מהקפטן; בחר בשחקן המוביל עם ה-xP והבעלות הגבוהים ביותר (כמו האלנד או סלאח).",
        "desc_en": "Don't gamble on wild differential captains. Over 60% of your rank progress relies on the armband; trust high-xP, high-ownership talismans with favorable fixtures.",
        "rule_he": "הקפטן מגן על הדירוג - את הדיפרנציאלים מייצרים בשחקני השדה.",
        "rule_en": "The armband protects your rank - let your outfield picks provide the differential edge.",
        "tag_he": "קפטן",
        "tag_en": "Captaincy",
    },
    {
        "num": 4,
        "icon": "🗓️",
        "title_he": "תכנון בטווחי 3-5 מחזורים (3-5 GW Blocks)",
        "title_en": "Plan in 3-5 Gameweek Horizons",
        "desc_he": "לעולם אל תקנה שחקן בשביל משחק אחד בלבד. בחן תמיד את לוח המשחקים (FDR) של 3 עד 5 המחזורים הבאים כדי להימנע מחילופי 'כיבוי שריפות' שבוע לאחר מכן.",
        "desc_en": "Never buy a player for a single fixture. Always evaluate the upcoming 3 to 5 gameweek run (FDR) to avoid burning future transfers fixing short-term punts.",
        "rule_he": "חשוב תמיד שבועיים-שלושה קדימה לפני כל לחיצה על כפתור הרכש.",
        "rule_en": "Always review the next 3-5 fixtures before confirming any market transfer.",
        "tag_he": "תכנון",
        "tag_en": "Planning",
    },
    {
        "num": 5,
        "icon": "⏱️",
        "title_he": "החלטות סמוך לדדליין (Wait for Press Conferences)",
        "title_en": "Wait for Press Conferences & News",
        "desc_he": "המתן למסיבות העיתונאים של ימי שישי ולעדכוני פציעות אחרונים לפני ביצוע חילוף. העברות מוקדמות באמצע השבוע מסתכנות בפציעות באימונים או בגביעים אירופיים.",
        "desc_en": "Delay transfers until Friday press conferences and verified deadline team news. Mid-week transfers risk training knocks and European rotation surprises.",
        "rule_he": "סבלנות מונעת אסונות: המתן לעדכוני המאמנים הרשמיים לפני חילופים.",
        "rule_en": "Patience prevents blunders: hold transfers until verified press conferences.",
        "tag_he": "תזמון",
        "tag_en": "Timing",
    },
    {
        "num": 6,
        "icon": "🪑",
        "title_he": "ספסל חסכוני ובטוח דקות (Smart Bench Enablers)",
        "title_en": "Smart Bench & Budget Enablers",
        "desc_he": "אל תקבור מיליונים יקרים בספסל. דאג לשחקן ספסל אחד או שניים בטוחים לפתוח במחיר רצפה (£4.0m-£4.5m) שייכנסו אוטומטית בעת הצורך, והשקע את הכסף ב-11 הפותחים.",
        "desc_en": "Do not trap valuable team value on your bench. Keep 1-2 cheap, guaranteed starters (£4.0m-£4.5m) as auto-sub safety nets while maximizing funds on your Starting XI.",
        "rule_he": "ספסל זול עם דקות קבועות מאפשר הרכב פותח עתיר כוכבים.",
        "rule_en": "A cheap bench with secure minutes funds premium heavy hitters in your starting XI.",
        "tag_he": "תקציב",
        "tag_en": "Budget",
    },
    {
        "num": 7,
        "icon": "📊",
        "title_he": "ללא פאניקה - אמון בנתונים (Trust Underlying Data)",
        "title_en": "Avoid Knee-Jerking & Trust Analytics",
        "desc_he": "אל תמכור שחקן איכותי רק כי סיים עם 2 נקודות במחזור בודד, ואל תרוץ לקנות שחקן שהבקיע שער מקרי. סמוך על מדדי ה-xG/xA והנתונים הסטטיסטיים לאורך זמן.",
        "desc_en": "Do not rage-sell premium assets after a single blank, nor chase random defensive flukes. Trust underlying expected metrics (xG, xA, xP) over past variance.",
        "rule_he": "מזל חולף, תוחלת מנצחת: שחקן שמייצר מצבים טובים יחזיר נקודות לאורך זמן.",
        "rule_en": "Variance is temporary, underlying process is permanent: trust high-xG/xA stars.",
        "tag_he": "אנליטיקה",
        "tag_en": "Analytics",
    },
    {
        "num": 8,
        "icon": "🏦",
        "title_he": "שמירה על רזרבה בבנק (£0.5m-£1.0m ITB)",
        "title_en": "Keep Liquidity In The Bank (£0.5m-£1.0m ITB)",
        "desc_he": "השארת סכום צנוע של 0.5-1.0 מיליון ליש\"ט בבנק מעניקה גמישות אדירה לעבור מיד לשחקן פורץ או כוכב בכושר בלי צורך לפרק חצי סגל או לקחת מינוסים.",
        "desc_en": "Maintaining £0.5m-£1.0m in the bank allows you to instantly jump onto emerging breakout stars without requiring multi-transfer squad surgery.",
        "rule_he": "כסף בבנק הוא חופש תמרון שמגן עליך משינויי מחירים מהירים.",
        "rule_en": "Cash in the bank equals agility: it shields you from rapid market price rises.",
        "tag_he": "גמישות",
        "tag_en": "Flexibility",
    },
    {
        "num": 9,
        "icon": "⚡",
        "title_he": "תזמון צ'יפים במחזורים מיוחדים (DGW & BGW)",
        "title_en": "Strategic Chip Timing (DGW & BGW)",
        "desc_he": "שמור את הצ'יפים החזקים (Wildcard, Free Hit, Bench Boost, Triple Captain) למחזורים הכפולים (DGW) והריקים (BGW) בחצי השני של העונה לקצירת עשרות נקודות יתרון.",
        "desc_en": "Preserve high-impact chips (Wildcard, Free Hit, Bench Boost, Triple Captain) for late-season Double (DGW) and Blank (BGW) weeks to exploit massive point swings.",
        "rule_he": "צ'יפ במחזור כפול שווה פי שניים או שלושה לעומת מחזור רגיל.",
        "rule_en": "A chip played in a Double Gameweek yields massively higher returns.",
        "tag_he": "צ'יפים",
        "tag_en": "Chips",
    },
    {
        "num": 10,
        "icon": "🎯",
        "title_he": "דיפרנציאלים מחושבים לטיפוס בליגה (Target Differentials)",
        "title_en": "Target High-Upside Differentials",
        "desc_he": "שחקנים בבעלות של מעל 60% מגנים על הדירוג שלך; אבל כדי לסגור פערים בליגה הפרטית שלך כשאתה רודף מאחור, שחקני מפתח איכותיים בבעלות מתחת ל-10% הם המנוע לניצחון.",
        "desc_en": "High-ownership players protect rank; but to bridge deficits in private mini-leagues, high-upside low-ownership differentials (<10%) are the true accelerators.",
        "rule_he": "שמור על שלד בטוח להגנה על הדירוג, והוסף 1-2 דיפרנציאלים לעקיפה.",
        "rule_en": "Anchor with essential template players, and hunt differentials to bridge gaps.",
        "tag_he": "מיני-ליגות",
        "tag_en": "Mini-Leagues",
    },
]
FPL_TEN_COMMANDMENTS = FPL_SUCCESS_TIPS  # תאימות לאחור

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

    return f'<div style="display:flex;justify-content:center;align-items:center;margin:1px 0;"><svg width="46" height="40" viewBox="0 0 46 42" fill="none" xmlns="http://www.w3.org/2000/svg">{stripe_defs}<path d="M14 6L5 13L10 20L14 17V38H32V17L36 20L41 13L32 6C30 9 27 10 23 10C19 10 16 9 14 6Z" {fill_attr} stroke="#0f172a" stroke-width="1.5" stroke-linejoin="round"/><path d="M14 6C16 9 19 10 23 10C27 10 30 9 32 6C30 4 27 3 23 3C19 3 16 4 14 6Z" fill="{c2}" stroke="#0f172a" stroke-width="1.2"/><path d="M10 20L5 13L9 10" stroke="{c2}" stroke-width="1.5" stroke-linecap="round"/><path d="M36 20L41 13L37 10" stroke="{c2}" stroke-width="1.5" stroke-linecap="round"/></svg></div>'

# =====================================================================
# 3. תמיכה דו-לשונית מלאה (i18n): עברית / אנגלית
# =====================================================================
if "app_lang" not in st.session_state:
    st.session_state.app_lang = "he"
if "app_theme" not in st.session_state:
    st.session_state.app_theme = "light"

TRANSLATIONS = {
    "he": {
        "page_title": "FPL Elite Scout | מנוע החלטות ומרגל סגלים",
        "app_title": "FPL Elite Scout",
        "app_subtitle": "מנוע קבלת החלטות, אופטימיזציית הרכב ומודיעין מיני-ליגות",
        "gate_desc": "הזן את מספר הקבוצה שלך כדי לטעון ניתוח כשירות, ציון סגל מכויל, חסרונות הרכב, מתכנן מחזורים ומרגל ליגות.",
        "team_id_label": "מספר קבוצה (Team ID):",
        "team_id_placeholder": "למשל: 139103",
        "team_id_help": "המספר שמופיע בכתובת הדפדפן בלשונית Points",
        "login_btn": "כניסה לסגל",
        "demo_btn": "סגל לדוגמה",
        "where_find_id": "איפה מוצאים את ה-Team ID?",
        "digits_only": "נא להזין ספרות בלבד.",
        "change_team": "החלף קבוצה",
        "engine_for_gw": "מנוע החלטות למחזור",
        "team_label": "קבוצה:",
        "squad_score": "ציון סגל מכויל",
        "xp_forecast": "תחזית נקודות (xP)",
        "in_bank": "יתרה בבנק",
        "overall_rank": "דירוג כללי",
        "formation": "מערך",
        "total_xp": "תוחלת נקודות להרכב",
        "tab_squad": "הסגל על המגרש",
        "tab_transfers": "מעבדת חילופים",
        "tab_analysis": "ניתוח סגל וחסרונות",
        "tab_scout": "רדאר רכש עילית",
        "tab_scenarios": "תרחישי תקציב",
        "tab_planner": "מתכנן מחזורים",
        "tab_leagues": "מיני-ליגות וראש בראש",
        "tab_tips": "💡 טיפים להצלחה",
        "pos_1": "שוער",
        "pos_2": "הגנה",
        "pos_3": "קישור",
        "pos_4": "חלוץ",
        "pos_1_pl": "שוערים",
        "pos_2_pl": "מגנים",
        "pos_3_pl": "קשרים",
        "pos_4_pl": "חלוצים",
        "btn_select": "בחר",
        "btn_selected": "נבחר",
        "btn_captain": "קפטן (C)",
        "btn_vc": "סגן (VC)",
        "btn_sub": "חילוף",
        "btn_sub_single": "חילוף",
        "cap_select_label": "קפטן (C):",
        "vc_select_label": "סגן קפטן (VC):",
        "swap_active_hint_prefix": "לחץ על שחקן יעד",
        "swap_active_hint_suffix": "להשלמת החילוף",
        "transfer_market_expander": "ביצוע העברה מהשוק",
        "planner_tr_expander": "תכנון העברה מהשוק למחזור זה",
        "btn_transfer": "העברה מהשוק",
        "btn_cancel": "ביטול",
        "btn_swap_here": "החלף לכאן",
        "swap_banner_title": "מצב חילוף פעיל:",
        "swap_banner_desc": "לחץ על שחקן יעד להשלמת החילוף מיד עם",
        "cancel_swap": "ביטול חילוף",
        "action_bar_title": "פעולות עבור שחקן:",
        "action_bar_hint": "בחר פעולה:",
        "transfer_drawer_title": "חלון העברות שוק",
        "selling_player": "מכירת שחקן:",
        "max_budget": "תקציב מקסימלי לרכש:",
        "close_drawer": "סגור חלון",
        "search_placeholder": "חיפוש שחקן (שם או קבוצה באנגלית)...",
        "rec_header": "שחקנים מומלצים לרכש:",
        "buy_player_btn": "קנה שחקן",
        "all_cands_label": "או בחר שחקן לרכש מהרשימה המלאה:",
        "confirm_transfer_btn": "אשר העברה",
        "bench_title": "שחקני ספסל",
        "bench_sub_order": "סדר עדיפות 1-4",
        "rebuild_btn": "בניית סגל מאפס (WC / FH)",
        "close_rebuild_btn": "סגור מצב בנייה מחדש",
        "rebuild_title": "לוח בניית סגל מאפס",
        "rebuild_subtitle": "בחר 15 שחקנים (2 שוערים, 5 מגנים, 5 קשרים, 3 חלוצים) במסגרת התקציב",
        "total_squad_val": "שווי סגל כולל",
        "rem_budget": "תקציב פנוי נותר",
        "players_picked": "שחקנים שנבחרו",
        "avg_per_player": "ממוצע לשחקן",
        "clear_15_btn": "נקה את כל 15 השחקנים",
        "load_existing_btn": "טען שחקנים מסגל קיים",
        "save_rebuild_btn": "שמור סגל חדש",
        "empty_slot": "משבצת פנויה",
        "add_slot": "הוסף",
        "remove_btn": "הסר",
        "ft_available": "חילופים זמינים",
        "ft_planned": "חילופים שתוכננו",
        "hit_penalty": "קנס נקודות (Hits)",
        "bank_bal": "יתרה בבנק",
        "xp_pred": "תחזית נקודות (xP)",
        "chip_for_gw": "צ'יפ למחזור",
        "no_chip": "ללא צ'יפ",
        "clear_all_transfers": "נקה הכל",
        "planned_transfers_gw": "העברות שתוכננו למחזור",
        "cancel_single_transfer": "בטל",
        "pts": "נק׳",
        "against": "מול:",
        "starters_only_cap": "קפטן להרכב בלבד",
        "back_to_id": "חזרה להזנת ID",
        "deadline_time_left": "זמן נותר עד נעילת חילופים",
        "h2h_comp": "השוואת שחקנים ראש-בראש:",
        "expected_add": "תוספת צפויה:",
        "out_label": "יוצא:",
        "in_label": "נכנס:",
        "season_pts_lbl": "נקודות העונה:",
        "next_match_lbl": "משחק קרוב:",
        "left_in_bank": "נשאר בבנק:",
        "starting_11_title": "11 שחקני ההרכב הפותח",
        "th_player": "שחקן",
        "th_pos": "עמדה",
        "th_team": "קבוצה",
        "th_next_match": "משחק קרוב",
        "th_fdr": "FDR",
        "th_start_prob": "סבירות לפתוח",
        "th_season_pts": "נקודות עונה",
        "th_xp": "xP",
        "t2_title": "מעבדת חילופים מותאמת עמדה ותקציב",
        "t2_out_header": "1. שחקן למכירה (OUT)",
        "t2_out_label": "בחר שחקן להוצאה:",
        "t2_in_header": "2. שחקן לרכש בעמדת",
        "t2_quick_search": "חיפוש מהיר:",
        "t2_search_placeholder": "הקלד שם או קבוצה באנגלית...",
        "t2_rec_replacements": "חלופות מומלצות לפי מודל נתונים:",
        "t2_all_pool_label": "או בחר מתוך כל שחקני העמדה העומדים בתקציב:",
        "t2_no_players": "לא נמצאו שחקנים מתאימים במסגרת התקציב בעמדה זו.",
        "t2_confirm_btn": "אשר חילוף בסגל",
        "t2_reset_btn": "אפס סגל למקור",
        "t2_saved_transfers": "חילופים שנשמרו:",
        "t3_title": "ניתוח עומק, חסרונות הרכב ודירוג כשירות",
        "tips_main_title": "10 טיפים להצלחה ב-FPL",
        "tips_main_subtitle": "עקרונות זהב אסטרטגיים של שחקני טופ 10k עולמי לניהול סגל מנצח לאורך העונה",
        "tips_checklist_title": "צ'ק-ליסט 60 שניות לפני דדליין המחזור:",
        "tips_chk_1": "אימות קפטן (C) וסגן (VC) מאובטח למקרה של אי-פתיחה מפתיעה",
        "tips_chk_2": "בדיקת סדר המחליפים בספסל (1-3) לפי סבירות דקות ופוטנציאל",
        "tips_chk_3": "וידוא מסיבות עיתונאים ועדכוני פציעות של הרגע האחרון",
        "tips_chk_4": "שמירת חילוף (Roll FT) אם אין צורך דחוף ומובהק בחילוף",
        "tips_golden_rule": "כלל מפתח:",
        "commandments_title": "10 טיפים להצלחה ב-FPL",
        "commandments_subtitle": "עקרונות זהב אסטרטגיים של שחקני טופ 10k עולמי להצלחה ארוכת טווח",
        "t3_squad_score": "ציון סגל מכויל",
        "t3_forecast": "תחזית הרכב:",
        "t3_flaws_title": "מוקדי סיכון שהורידו ניקוד:",
        "t3_no_flaws": "לא אותרו חסרונות בולטים בהרכב!",
        "t4_title": "רדאר רכש מוביל למחזור",
        "t4_tab_fwd": "חלוצים",
        "t4_tab_mid": "קשרים",
        "t4_tab_def": "מגנים",
        "t4_tab_gk": "שוערים",
        "t4_tab_cap": "קפטן סולידי מול דיפרנשיאל",
        "t4_buy_low": "קנייה בשפל",
        "t4_overperforming": "סכנת דעיכה",
        "t4_cap_shield": "קפטן סולידי (Shield)",
        "t4_cap_sword": "קפטן דיפרנשיאל (Sword)",
        "t4_ownership": "בעלות:",
        "t4_only": "בלבד",
        "t4_start_prob": "סבירות פתיחה:",
        "t4_tot_pts": "סך נקודות:",
        "t5_title": "3 תרחישי חילוף אופטימליים לתקציב הסגל",
        "t5_op1_title": "אופציה 1: ייצוב הגנתי / החלפת מוקד פציעה",
        "t5_op1_tag": "הגנה",
        "t5_op2_title": "אופציה 2: שדרוג מנוע הקישור וייצור מצבים",
        "t5_op2_tag": "קישור",
        "t5_op3_title": "אופציה 3: רענון חוד ההתקפה",
        "t5_op3_tag": "התקפה",
        "t5_diff_xp": "תוספת:",
        "t6_title": "מתכנן מחזורים וסימולטור צ'יפים",
        "t6_caption": "בצע חילופי ספסל והרכב, העברות שחקנים ובחירת קפטן פר מחזור. המערכת מחשבת צבירת חילופים חינמיים (עד 5), השפעת צ'יפים וקנסות.",
        "t6_init_fts": "מלאי חילופים התחלתי:",
        "t6_horizon_label": "טווח מחזורים לתכנון:",
        "t6_horizon_5": "5 מחזורים קרובים",
        "t6_horizon_8": "8 מחזורים קרובים",
        "t6_horizon_all": "כל העונה (עד מחזור 38)",
        "t6_reset_plan": "איפוס תוכנית",
        "t6_export_plan": "ייצוא תוכנית",
        "t6_select_gw": "בחר מחזור לתכנון ועריכה:",
        "t6_chip_active": "צ'יפ פעיל למחזור:",
        "t6_clr_transfers": "נקה העברות מחזור זה",
        "t6_reset_rebuild": "אפס וחזור לסגל המקורי",
        "t7_title": "מודיעין מיני-ליגות וראש בראש",
        "t7_caption": "עקוב אחרי יריביך במיני-ליגה: זהה באילו שחקנים הם מחזיקים, מי בחר איזה קפטן, ואתר דיפרנשיאלים שיקפיצו אותך בדירוג.",
        "t7_choose_league": "בחר מתוך המיני-ליגות של הקבוצה שלך:",
        "t7_enter_id": "הזן קוד מיני-ליגה קלאסית (League ID):",
        "t7_or_search": "או חפש לפי קוד ליגה אחר:",
        "t7_league_table": "טבלת ליגה:",
        "t7_leader": "מוביל הליגה",
        "t7_your_rank": "הדירוג שלך בליגה",
        "t7_rank_pos": "מקום",
        "t7_gap_top": "פער מהפסגה:",
        "t7_not_in_league": "אינך חבר בליגה זו",
        "t7_outside_top_50": "מחוץ ל-50 הראשונים",
        "t7_showing_top_50": "מציג את 50 המובילים בליגה",
        "t7_total_members": "משתתפים בליגה",
        "t7_th_rank": "מיקום",
        "t7_th_team_name": "שם קבוצה",
        "t7_th_manager": "מאמן",
        "t7_th_last_gw": "מחזור אחרון",
        "t7_th_total_pts": "סך נקודות",
        "t7_th_team_id": "ID קבוצה",
        "t7_h2h_title": "ריגול סגל ראש בראש (H2H)",
        "t7_choose_rival": "בחר יריב לריגול מעמיק:",
        "t7_rival_details": "פרטי יריב (מחזור אחרון):",
        "t7_rival_cap": "קפטן יריב:",
        "t7_rival_chip": "צ'יפ פעיל:",
        "t7_differentials": "שחקנים דיפרנציאליים:",
        "t7_you_have": "שחקנים שלך שאין ליריב:",
        "t7_rival_has": "שחקנים של היריב שאין לך:",
        "t7_no_results": "לא נמצאו תוצאות במיני-ליגה זו.",
        "t7_err_fetch": "לא ניתן לטעון את נתוני הליגה. ודא שמספר הליגה תקין.",
        "t7_prompt_enter": "בחר או הזן קוד מיני-ליגה כדי להציג את הטבלה ומנוע הריגול.",
        "t7_h2h_none": "אין",
        "t7_no_chip": "ללא",
        "t2_in_label": "בחר שחקן לקנייה (מסונן לפי עמדה ותקציב):",
        "t2_no_players_budget": "אין שחקנים מתאימים בתקציב זה.",
        "rb_err_limit": "חריגת מכסה: חוק ה-FPL אוסר יותר מ-3 שחקנים ממועדון אחד:",
        "rb_err_budget": "חריגת תקציב של £{val}m: עליך לפנות שחקן או לבחור שחקנים זולים יותר.",
        "rb_saved_toast": "סגל חדש נשמר בהצלחה למחזור",
        "rb_picker_title": "בחירת {pos} לסגל (תקציב פנוי: £{budget}m)",
        "rb_picker_max_price": "מחיר מקסימלי אפשרי לעמדה זו (משריין £4.0m ליתר המשבצות):",
        "rb_recommended": "{pos}ים מומלצים:",
        "rb_all_cands": "או בחר מתוך כל ה{pos}ים הזמינים בתקציב:",
        "rb_no_cands": "לא נמצאו שחקנים מתאימים בעמדת {pos} במסגרת התקציב של £{budget}m.",
        "rb_add_cand": "הוסף שחקן זה",
        "rb_btn_chosen": "נבחר",
        "gw_fixtures_title": "משחקי מחזור {gw}",
        "no_fixtures_gw": "אין משחקים מתוזמנים למחזור זה",
        "matches": "משחקים",
        "theme_dark": "מצב כהה",
        "theme_light": "מצב בהיר",
        "rb_rebuilt_success": "סגל נבנה מחדש מאפס למחזור זה",
        "you_indicator": "(אתה)",
        "from_the_bench": "מהספסל",
        "from_the_xi": "מההרכב",
    },
    "en": {
        "page_title": "FPL Elite Scout | Decision Engine & Squad Intelligence",
        "app_title": "FPL Elite Scout",
        "app_subtitle": "Decision Engine, Lineup Optimization & Mini-League Intelligence",
        "gate_desc": "Enter your Team ID to load injury analysis, calibrated squad rating, lineup flaws, gameweek planner, and league intelligence.",
        "team_id_label": "Team ID:",
        "team_id_placeholder": "e.g., 139103",
        "team_id_help": "The number from your browser URL under the Points tab",
        "login_btn": "Enter Squad",
        "demo_btn": "Demo Squad",
        "where_find_id": "Where to find your Team ID?",
        "digits_only": "Please enter digits only.",
        "change_team": "Change Team",
        "engine_for_gw": "Decision Engine for Gameweek",
        "team_label": "Team:",
        "squad_score": "Squad Rating",
        "xp_forecast": "Expected Points (xP)",
        "in_bank": "In the Bank",
        "overall_rank": "Overall Rank",
        "formation": "Formation",
        "total_xp": "Lineup Expected Points",
        "tab_squad": "Pitch Squad",
        "tab_transfers": "Transfers Lab",
        "tab_analysis": "Team Analysis",
        "tab_scout": "Scout Radar",
        "tab_scenarios": "Transfer Scenarios",
        "tab_planner": "Gameweek Planner",
        "tab_leagues": "Leagues & Head-to-Head",
        "tab_tips": "💡 Success Tips",
        "pos_1": "Goalkeeper",
        "pos_2": "Defender",
        "pos_3": "Midfielder",
        "pos_4": "Forward",
        "pos_1_pl": "Goalkeepers",
        "pos_2_pl": "Defenders",
        "pos_3_pl": "Midfielders",
        "pos_4_pl": "Forwards",
        "btn_select": "Select",
        "btn_selected": "Selected",
        "btn_captain": "Captain (C)",
        "btn_vc": "Vice (VC)",
        "btn_sub": "Sub",
        "btn_sub_single": "Sub",
        "cap_select_label": "Captain (C):",
        "vc_select_label": "Vice-Captain (VC):",
        "swap_active_hint_prefix": "Click target player",
        "swap_active_hint_suffix": "to complete substitution",
        "transfer_market_expander": "Transfer Player from Market",
        "planner_tr_expander": "Plan Market Transfer for this Gameweek",
        "btn_transfer": "Transfer Out",
        "btn_cancel": "Cancel",
        "btn_swap_here": "Swap Here",
        "swap_banner_title": "Substitution Mode Active:",
        "swap_banner_desc": "Click target player to complete swap with",
        "cancel_swap": "Cancel Swap",
        "action_bar_title": "Player Actions:",
        "action_bar_hint": "Select action:",
        "transfer_drawer_title": "Transfer Market Drawer",
        "selling_player": "Selling Player:",
        "max_budget": "Max Budget Available:",
        "close_drawer": "Close Drawer",
        "search_placeholder": "Search player (name or team)...",
        "rec_header": "Recommended Replacements:",
        "buy_player_btn": "Buy Player",
        "all_cands_label": "Or choose from all available players in budget:",
        "confirm_transfer_btn": "Confirm Transfer",
        "bench_title": "Bench Players",
        "bench_sub_order": "Sub Priority 1-4",
        "rebuild_btn": "Rebuild Squad (WC / FH)",
        "close_rebuild_btn": "Close Rebuild Mode",
        "rebuild_title": "Rebuild Squad from Scratch",
        "rebuild_subtitle": "Select 15 players (2 GKs, 5 DEFs, 5 MIDs, 3 FWDs) within your budget",
        "total_squad_val": "Total Squad Value",
        "rem_budget": "Remaining Budget",
        "players_picked": "Players Picked",
        "avg_per_player": "Avg per Player",
        "clear_15_btn": "Clear All 15 Players",
        "load_existing_btn": "Load Existing Squad",
        "save_rebuild_btn": "Save New Squad",
        "empty_slot": "Empty Slot",
        "add_slot": "Add",
        "remove_btn": "Remove",
        "ft_available": "Available FTs",
        "ft_planned": "Planned Transfers",
        "hit_penalty": "Hit Penalty",
        "bank_bal": "Bank Balance",
        "xp_pred": "Points Forecast (xP)",
        "chip_for_gw": "Chip for GW",
        "no_chip": "No Chip",
        "clear_all_transfers": "Clear All",
        "planned_transfers_gw": "Planned Transfers for GW",
        "cancel_single_transfer": "Cancel",
        "pts": "pts",
        "against": "vs:",
        "starters_only_cap": "Starters only for Captain",
        "back_to_id": "Back to ID entry",
        "deadline_time_left": "Time left until deadline",
        "h2h_comp": "Head-to-Head Comparison:",
        "expected_add": "Expected Gain:",
        "out_label": "OUT:",
        "in_label": "IN:",
        "season_pts_lbl": "Season Points:",
        "next_match_lbl": "Next Match:",
        "left_in_bank": "In the Bank:",
        "starting_11_title": "Starting XI Players",
        "th_player": "Player",
        "th_pos": "Pos",
        "th_team": "Team",
        "th_next_match": "Next Match",
        "th_fdr": "FDR",
        "th_start_prob": "Start Prob",
        "th_season_pts": "Season Pts",
        "th_xp": "xP",
        "t2_title": "Position & Budget Transfers Lab",
        "t2_out_header": "1. Player to Sell (OUT)",
        "t2_out_label": "Select player to transfer out:",
        "t2_in_header": "2. Replacement Player (IN) in position",
        "t2_quick_search": "Quick Search:",
        "t2_search_placeholder": "Type name or team in English...",
        "t2_rec_replacements": "Data-Model Recommended Replacements:",
        "t2_all_pool_label": "Or choose from all available players in budget:",
        "t2_no_players": "No eligible players found within budget for this position.",
        "t2_confirm_btn": "Confirm Squad Transfer",
        "t2_reset_btn": "Reset Squad to Original",
        "t2_saved_transfers": "Saved transfers:",
        "t3_title": "Squad Strength & Flaw Analysis",
        "tips_main_title": "10 Pro Tips for FPL Success",
        "tips_main_subtitle": "Top 10k Strategic Golden Rules for Long-Term FPL Mastery",
        "tips_checklist_title": "60-Second Pre-Deadline Checklist:",
        "tips_chk_1": "Confirm Captain (C) and Vice-Captain (VC) safeguards",
        "tips_chk_2": "Check bench order (1-3) prioritized by return upside and minutes",
        "tips_chk_3": "Verify late-breaking press conference injury updates",
        "tips_chk_4": "Roll your free transfer if no critical surgery is required",
        "tips_golden_rule": "Golden Rule:",
        "commandments_title": "10 Pro Tips for FPL Success",
        "commandments_subtitle": "Top 10k Strategic Golden Rules for Long-Term FPL Mastery",
        "t3_squad_score": "Squad Rating",
        "t3_forecast": "Lineup Forecast:",
        "t3_flaws_title": "Risk factors reducing squad rating:",
        "t3_no_flaws": "No significant squad flaws detected!",
        "t4_title": "Elite Scout Radar for Gameweek",
        "t4_tab_fwd": "Forwards",
        "t4_tab_mid": "Midfielders",
        "t4_tab_def": "Defenders",
        "t4_tab_gk": "Goalkeepers",
        "t4_tab_cap": "Captain Shield vs Differential",
        "t4_buy_low": "Buy Low",
        "t4_overperforming": "Regression Risk",
        "t4_cap_shield": "Shield Captain",
        "t4_cap_sword": "Differential Captain (Sword)",
        "t4_ownership": "Ownership:",
        "t4_only": "only",
        "t4_start_prob": "Start Probability:",
        "t4_tot_pts": "Total Points:",
        "t5_title": "3 Optimal Transfer Scenarios for Squad Budget",
        "t5_op1_title": "Option 1: Defensive Stability / Replace Injury Risk",
        "t5_op1_tag": "Defense",
        "t5_op2_title": "Option 2: Upgrade Midfield Engine & Chance Creation",
        "t5_op2_tag": "Midfield",
        "t5_op3_title": "Option 3: Refresh Frontline Attack",
        "t5_op3_tag": "Attack",
        "t5_diff_xp": "Gain:",
        "t6_title": "Gameweek Planner & Chip Simulator",
        "t6_caption": "Perform bench swaps, player transfers, and captain selection per GW. Tracks free transfer accumulation (up to 5), chips, and penalties.",
        "t6_init_fts": "Initial Free Transfers:",
        "t6_horizon_label": "Planning Horizon:",
        "t6_horizon_5": "Next 5 Gameweeks",
        "t6_horizon_8": "Next 8 Gameweeks",
        "t6_horizon_all": "Rest of Season (up to GW 38)",
        "t6_reset_plan": "Reset Plan",
        "t6_export_plan": "Export Plan",
        "t6_select_gw": "Select Gameweek to plan and edit:",
        "t6_chip_active": "Active Chip for GW:",
        "t6_clr_transfers": "Clear Transfers for this GW",
        "t6_reset_rebuild": "Reset to Original Squad",
        "t7_title": "Mini-League Intelligence & Head-to-Head",
        "t7_caption": "Spy on mini-league rivals: see their squad, captain picks, and find differentials to climb ranks.",
        "t7_choose_league": "Select from your team's mini-leagues:",
        "t7_enter_id": "Enter Classic League ID:",
        "t7_or_search": "Or search by another League ID:",
        "t7_league_table": "League Standings:",
        "t7_leader": "League Leader",
        "t7_your_rank": "Your Rank in League",
        "t7_rank_pos": "Rank",
        "t7_gap_top": "Gap from top:",
        "t7_not_in_league": "Not in this league",
        "t7_outside_top_50": "Outside Top 50",
        "t7_showing_top_50": "Showing top 50 managers in this league",
        "t7_total_members": "League Members",
        "t7_th_rank": "Rank",
        "t7_th_team_name": "Team Name",
        "t7_th_manager": "Manager",
        "t7_th_last_gw": "Last GW",
        "t7_th_total_pts": "Total Pts",
        "t7_th_team_id": "Team ID",
        "t7_h2h_title": "Head-to-Head Squad Spy",
        "t7_choose_rival": "Select rival for in-depth spy:",
        "t7_rival_details": "Rival Details (Last GW):",
        "t7_rival_cap": "Rival Captain:",
        "t7_rival_chip": "Active Chip:",
        "t7_differentials": "Differentials:",
        "t7_you_have": "Your differentials (players you own that rival doesn't):",
        "t7_rival_has": "Rival differentials (players rival owns that you don't):",
        "t7_no_results": "No results found in this mini-league.",
        "t7_err_fetch": "Unable to load league data. Please verify the League ID.",
        "t7_prompt_enter": "Select or enter a mini-league code to display the table and spy engine.",
        "t7_h2h_none": "None",
        "t7_no_chip": "None",
        "t2_in_label": "Select player to buy (filtered by pos & budget):",
        "t2_no_players_budget": "No eligible players found within this budget.",
        "rb_err_limit": "Quota exceeded: FPL rules allow a maximum of 3 players from one club:",
        "rb_err_budget": "Budget exceeded by £{val}m: Please remove a player or pick cheaper options.",
        "rb_saved_toast": "New squad successfully saved for Gameweek",
        "rb_picker_title": "Selecting {pos} for Squad (Available budget: £{budget}m)",
        "rb_picker_max_price": "Max allowed price for this position (reserves £4.0m for other empty slots):",
        "rb_recommended": "Recommended {pos}s:",
        "rb_all_cands": "Or choose from all available {pos}s within budget:",
        "rb_no_cands": "No eligible players found in position {pos} within £{budget}m budget.",
        "rb_add_cand": "Add this player",
        "rb_btn_chosen": "Selected",
        "gw_fixtures_title": "Gameweek {gw} Fixtures",
        "no_fixtures_gw": "No fixtures scheduled for this GW",
        "matches": "matches",
        "theme_dark": "Dark Mode",
        "theme_light": "Light Mode",
        "rb_rebuilt_success": "Squad rebuilt from scratch for this GW",
        "you_indicator": "(You)",
        "from_the_bench": "from the Bench",
        "from_the_xi": "from the Starting XI",
    },
}

def t(key):
    lang = st.session_state.get("app_lang", "he")
    return TRANSLATIONS.get(lang, {}).get(key, TRANSLATIONS["he"].get(key, key))

def get_player_reason(p):
    lang = st.session_state.get("app_lang", "he")
    if lang == "en":
        return p.get("reason_en", p.get("reason", ""))
    return p.get("reason_he", p.get("reason", ""))

def get_player_pos(p):
    code = p.get("pos_code", 1)
    return t(f"pos_{code}")

# =====================================================================
# =====================================================================
# 4. עיצוב CSS מלא: נגישות, RTL / LTR דינמי, רספונסיביות מובייל
# =====================================================================
is_light = (st.session_state.get("app_theme", "light") == "light")

if is_light:
    root_vars = """
    --bg-main: #f1f5f9;
    --bg-body-grad: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    --bg-card: #ffffff;
    --bg-card-hover: #f8fafc;
    --border-color: #cbd5e1;
    --text-primary: #1e293b;
    --text-secondary: #475569;
    --text-muted: #64748b;
    --accent-mint: #059669;
    --accent-cyan: #0284c7;
    --accent-magenta: #e11d48;
    --accent-purple: #37003c;
    --accent-gold: #d97706;
    --input-bg: #ffffff;
    --input-border: #cbd5e1;
    --input-text: #1e293b;
    --input-focus-border: #059669;
    --input-focus-shadow: rgba(5, 150, 105, 0.2);
    --tab-bg: #ffffff;
    --tab-border: #cbd5e1;
    --tab-text: #64748b;
    --tab-hover-bg: #f1f5f9;
    --tab-hover-text: #1e293b;
    --tab-active-bg: #059669;
    --tab-active-text: #ffffff;
    --tab-active-border: #059669;
    --tab-active-shadow: rgba(5, 150, 105, 0.25);
    --gate-bg: #ffffff;
    --gate-border: #10b981;
    --gate-shadow: 0 12px 28px rgba(0,0,0,0.06), 0 0 16px rgba(16, 185, 129, 0.08);
    --pitch-border: #15803d;
    --pitch-bg: radial-gradient(ellipse at 50% 50%, #15803d 0%, #166534 100%), repeating-linear-gradient(0deg, #166534 0px, #166534 48px, #14532d 48px, #14532d 96px);
    --pitch-shadow: 0 10px 28px rgba(22, 101, 52, 0.16);
    --pitch-line: rgba(255, 255, 255, 0.45);
    --bench-bg: #ffffff;
    --bench-border: #10b981;
    --bench-shadow: 0 6px 18px rgba(0, 0, 0, 0.05);
    --bench-dugout-badge-bg: #f0fdf4;
    --bench-dugout-badge-border: #10b981;
    --p-card-bg: #ffffff;
    --p-card-border: #cbd5e1;
    --p-card-border-bottom: #cbd5e1;
    --p-card-shadow: 0 3px 10px rgba(0,0,0,0.06);
    --p-name-plate-bg: #f8fafc;
    --p-name-plate-border: #cbd5e1;
    --p-name-plate-text: #1e293b;
    --p-card-btn-bg: #f1f5f9;
    --p-card-btn-border: #cbd5e1;
    --p-card-btn-text: #1e293b;
    --p-card-btn-hover-bg: #e2e8f0;
    --p-card-btn-hover-text: #059669;
    --card-bench-bg: #ffffff;
    --card-bench-border: #10b981;
    --card-bench-btn-bg: #f8fafc;
    --card-bench-btn-border: #10b981;
    --card-bench-btn-text: #059669;
    --btn-general-bg: #ffffff;
    --btn-general-border: #cbd5e1;
    --btn-general-text: #1e293b;
    --btn-general-hover-bg: #f0fdf4;
    --btn-general-hover-text: #059669;
    --fxt-row-bg: #ffffff;
    --fxt-row-border: #e2e8f0;
    --fxt-row-hover: #f1f5f9;
    --fxt-card-bg: #ffffff;
    --fxt-card-border: #cbd5e1;
    --badge-ko-bg: #f1f5f9;
    --badge-mint-bg: rgba(16, 185, 129, 0.1);
    --badge-mint-border: #10b981;
    --metric-bg: #ffffff;
    --metric-border: #cbd5e1;
    --kpi-score-bg: #ffffff;
    --kpi-score-border: #10b981;
    --kpi-score-shadow: rgba(16, 185, 129, 0.1);
    --kpi-xp-bg: #ffffff;
    --kpi-xp-border: #0284c7;
    --kpi-xp-shadow: rgba(2, 132, 199, 0.1);
    --kpi-bank-bg: #ffffff;
    --kpi-bank-border: #d97706;
    --kpi-bank-shadow: rgba(217, 119, 6, 0.1);
    --kpi-rank-bg: #ffffff;
    --kpi-rank-border: #e11d48;
    --kpi-rank-shadow: rgba(225, 29, 72, 0.1);
    """
else:
    root_vars = """
    --bg-main: #0b0714;
    --bg-body-grad: radial-gradient(circle at 50% -10%, rgba(55, 0, 60, 0.45) 0%, transparent 60%);
    --bg-card: rgba(26, 15, 46, 0.85);
    --bg-card-hover: rgba(38, 22, 66, 0.92);
    --border-color: rgba(168, 85, 247, 0.2);
    --text-primary: #ffffff;
    --text-secondary: #e2d9f3;
    --text-muted: #a79bc8;
    --accent-mint: #00ff87;
    --accent-cyan: #02efff;
    --accent-magenta: #e90052;
    --accent-purple: #37003c;
    --accent-gold: #ffd700;
    --input-bg: #140b24;
    --input-border: rgba(168, 85, 247, 0.3);
    --input-text: #ffffff;
    --input-focus-border: #00ff87;
    --input-focus-shadow: rgba(0, 255, 135, 0.3);
    --tab-bg: #110722;
    --tab-border: rgba(168, 85, 247, 0.25);
    --tab-text: #a79bc8;
    --tab-hover-bg: rgba(55, 0, 60, 0.5);
    --tab-hover-text: #ffffff;
    --tab-active-bg: linear-gradient(135deg, #37003c 0%, #580060 100%);
    --tab-active-text: #00ff87;
    --tab-active-border: #00ff87;
    --tab-active-shadow: rgba(0, 255, 135, 0.35);
    --gate-bg: linear-gradient(145deg, #1c0c36 0%, #0f071c 100%);
    --gate-border: rgba(0, 255, 135, 0.4);
    --gate-shadow: 0 16px 36px rgba(0,0,0,0.7), 0 0 28px rgba(0, 255, 135, 0.15);
    --pitch-border: rgba(0, 255, 135, 0.45);
    --pitch-bg: radial-gradient(ellipse at 50% 50%, rgba(16, 92, 45, 0.9) 0%, rgba(6, 44, 20, 0.98) 100%), repeating-linear-gradient(0deg, #104822 0px, #104822 48px, #0c3b1b 48px, #0c3b1b 96px);
    --pitch-shadow: 0 16px 44px rgba(0,0,0,0.8), 0 0 30px rgba(0, 255, 135, 0.12);
    --pitch-line: rgba(255, 255, 255, 0.22);
    --bench-bg: rgba(20, 10, 36, 0.92);
    --bench-border: rgba(0, 255, 135, 0.35);
    --bench-shadow: 0 16px 36px rgba(0,0,0,0.7);
    --bench-dugout-badge-bg: rgba(0, 255, 135, 0.08);
    --bench-dugout-badge-border: rgba(0, 255, 135, 0.3);
    --p-card-bg: rgba(20, 10, 36, 0.92);
    --p-card-border: rgba(168, 85, 247, 0.3);
    --p-card-border-bottom: rgba(168, 85, 247, 0.35);
    --p-card-shadow: 0 6px 20px rgba(0,0,0,0.6);
    --p-name-plate-bg: #1c0f33;
    --p-name-plate-border: rgba(168, 85, 247, 0.35);
    --p-name-plate-text: #ffffff;
    --p-card-btn-bg: rgba(26, 15, 46, 0.95);
    --p-card-btn-border: rgba(168, 85, 247, 0.3);
    --p-card-btn-text: #ffffff;
    --p-card-btn-hover-bg: #00ff87;
    --p-card-btn-hover-text: #05140b;
    --card-bench-bg: rgba(24, 12, 42, 0.88);
    --card-bench-border: rgba(0, 255, 135, 0.4);
    --card-bench-btn-bg: rgba(24, 12, 42, 0.95);
    --card-bench-btn-border: rgba(0, 255, 135, 0.4);
    --card-bench-btn-text: #00ff87;
    --btn-general-bg: rgba(26, 15, 46, 0.85);
    --btn-general-border: #00ff87;
    --btn-general-text: #ffffff;
    --btn-general-hover-bg: rgba(0, 255, 135, 0.15);
    --btn-general-hover-text: #00ff87;
    --fxt-row-bg: rgba(20, 10, 36, 0.7);
    --fxt-row-border: rgba(168, 85, 247, 0.2);
    --fxt-row-hover: rgba(38, 22, 66, 0.85);
    --fxt-card-bg: rgba(26, 15, 46, 0.85);
    --fxt-card-border: rgba(168, 85, 247, 0.2);
    --badge-ko-bg: rgba(55, 0, 60, 0.6);
    --badge-mint-bg: rgba(0, 255, 135, 0.15);
    --badge-mint-border: rgba(0, 255, 135, 0.35);
    --metric-bg: rgba(26, 15, 46, 0.75);
    --metric-border: rgba(168, 85, 247, 0.2);
    --kpi-score-bg: linear-gradient(135deg, rgba(0, 255, 135, 0.15) 0%, rgba(19, 9, 36, 0.95) 100%);
    --kpi-score-border: #00ff87;
    --kpi-score-shadow: rgba(0, 255, 135, 0.25);
    --kpi-xp-bg: linear-gradient(135deg, rgba(2, 239, 255, 0.15) 0%, rgba(19, 9, 36, 0.95) 100%);
    --kpi-xp-border: #02efff;
    --kpi-xp-shadow: rgba(2, 239, 255, 0.25);
    --kpi-bank-bg: linear-gradient(135deg, rgba(250, 204, 21, 0.15) 0%, rgba(19, 9, 36, 0.95) 100%);
    --kpi-bank-border: #facc15;
    --kpi-bank-shadow: rgba(250, 204, 21, 0.25);
    --kpi-rank-bg: linear-gradient(135deg, rgba(233, 0, 82, 0.18) 0%, rgba(55, 0, 60, 0.95) 100%);
    --kpi-rank-border: #ff2882;
    --kpi-rank-shadow: rgba(233, 0, 82, 0.28);
    """

css_template = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=Rubik:wght@400;500;600;700;800;900&display=swap');

/* --- 1. הסתרת מיתוג Streamlit לחלוטין (White-Labeling) --- */
#MainMenu {visibility: hidden !important; display: none !important;}
header {visibility: hidden !important; display: none !important;}
footer {visibility: hidden !important; display: none !important;}
.stDeployButton {display: none !important;}
div[data-testid="stDecoration"] {display: none !important;}
div[data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
div[data-testid="stStatusWidget"] {visibility: hidden !important; display: none !important;}

:root {
__ROOT_VARS__
}

/* --- תמיכה מושלמת ועקבית ב-RTL / LTR, מובייל, ופונט מודרני --- */
.stApp, html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
    direction: __DIR__ !important;
    text-align: __ALIGN__ !important;
    background-color: var(--bg-main) !important;
    background-image: var(--bg-body-grad) !important;
    background-attachment: fixed !important;
    font-family: 'Plus Jakarta Sans', 'Rubik', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    color: var(--text-primary) !important;
    -webkit-font-smoothing: antialiased;
    -webkit-tap-highlight-color: transparent;
}

/* ביטול ריפודים ענקיים מיותרים בראש הדף ובמובייל */
.block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 3rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 1240px !important;
    margin: 0 auto !important;
}

/* ביטול מוחלט של כל רקעים ומרובעים כהים בעמודות ובלוקים פנימיים */
div[data-testid="stVerticalBlock"] {
    direction: __DIR__ !important;
    text-align: __ALIGN__ !important;
    background: transparent !important;
    background-color: transparent !important;
    background-image: none !important;
    border: none !important;
    box-shadow: none !important;
}

div[data-testid="column"],
div[data-testid="column"] > div,
div[data-testid="column"] div[data-testid="stVerticalBlock"],
div[data-testid="stHorizontalBlock"],
div[data-testid="stHorizontalBlock"] > div {
    background: transparent !important;
    background-color: transparent !important;
    background-image: none !important;
    border: none !important;
    box-shadow: none !important;
}

[data-testid="stMarkdownContainer"], 
[data-testid="stMarkdownContainer"] p, 
[data-testid="stMarkdownContainer"] h1, 
[data-testid="stMarkdownContainer"] h2, 
[data-testid="stMarkdownContainer"] h3, 
[data-testid="stMarkdownContainer"] h4, 
[data-testid="stMarkdownContainer"] h5, 
[data-testid="stMarkdownContainer"] h6, 
[data-testid="stMarkdownContainer"] span, 
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] label,
[data-testid="stMarkdownContainer"] div,
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] b {
    direction: __DIR__ !important;
    text-align: __ALIGN__ !important;
    line-height: 1.5;
    color: var(--text-primary) !important;
}

/* החרגה והגנה מלאה על כרטיסי שחקנים במגרש */
[data-testid="stMarkdownContainer"] .p-card-fpl,
[data-testid="stMarkdownContainer"] .p-card-fpl * {
    direction: ltr !important;
    text-align: center !important;
}
[data-testid="stMarkdownContainer"] .p-name-plate,
[data-testid="stMarkdownContainer"] .p-card-fpl .p-name-plate {
    background: var(--p-name-plate-bg) !important;
    border: 1px solid var(--p-name-plate-border) !important;
    border-radius: 6px !important;
    color: var(--p-name-plate-text) !important;
}
[data-testid="stMarkdownContainer"] .p-name-txt,
[data-testid="stMarkdownContainer"] .p-card-fpl .p-name-txt,
[data-testid="stMarkdownContainer"] .p-name-plate span {
    color: var(--p-name-plate-text) !important;
    font-weight: 800 !important;
    font-size: 12.5px !important;
    text-align: center !important;
}

.stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
    color: var(--text-secondary) !important;
    direction: __DIR__ !important;
    text-align: __ALIGN__ !important;
}

div[data-testid="stRadio"] label span,
div[data-testid="stRadio"] label p,
div[data-testid="stRadio"] div {
    color: var(--text-primary) !important;
}

div[data-testid="stExpander"] details summary p,
div[data-testid="stExpander"] details summary span {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
}

div[data-testid="stDataFrame"],
div[data-testid="stDataFrame"] div,
div[data-testid="stDataFrame"] span {
    color: var(--text-primary) !important;
}

h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
}

/* --- 1.2 תיבות בחירה וקלט - הגנה מוחלטת מכל רקע כהה/שחור --- */
div[data-testid="stSelectbox"],
div[data-testid="stTextInput"],
div[data-testid="stNumberInput"] {
    direction: __DIR__ !important;
}

div[data-testid="stWidgetLabel"] label,
div[data-testid="stWidgetLabel"] p,
div[data-testid="stSelectbox"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stRadio"] label {
    direction: __DIR__ !important;
    text-align: __ALIGN__ !important;
    width: 100% !important;
    font-weight: 700 !important;
    color: var(--text-secondary) !important;
    font-size: 13px !important;
    margin-bottom: 4px !important;
}

/* BaseWeb Select Container - הגנה מוחלטת מכל רקע כהה/שחור ב-Light Mode */
div[data-testid="stSelectbox"] div[data-baseweb="select"],
div[data-testid="stSelectbox"] div[data-baseweb="select"] *,
div[data-baseweb="select"],
div[data-baseweb="select"] *,
div[data-baseweb="select"] div,
div[data-baseweb="select"] span,
div[data-baseweb="select"] [role="combobox"],
div[data-baseweb="select"] [role="combobox"] * {
    background-color: var(--input-bg) !important;
    background: var(--input-bg) !important;
    color: var(--input-text) !important;
    border-color: var(--input-border) !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    border: 1.5px solid var(--input-border) !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
    min-height: 38px !important;
    background-color: var(--input-bg) !important;
    background: var(--input-bg) !important;
}

div[data-testid="stSelectbox"] label,
div[data-testid="stSelectbox"] label *,
div[data-testid="stSelectbox"] [data-testid="stWidgetLabel"],
div[data-testid="stSelectbox"] [data-testid="stWidgetLabel"] * {
    background: transparent !important;
    background-color: transparent !important;
    color: var(--text-secondary) !important;
}

div[data-testid="stSelectbox"] svg,
div[data-baseweb="select"] svg {
    fill: var(--input-text) !important;
    color: var(--input-text) !important;
    background: transparent !important;
    background-color: transparent !important;
}

div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input {
    direction: __DIR__ !important;
    text-align: __ALIGN__ !important;
    background-color: var(--input-bg) !important;
    background: var(--input-bg) !important;
    border: 1.5px solid var(--input-border) !important;
    color: var(--input-text) !important;
    border-radius: 10px !important;
    min-height: 38px !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
}

div[data-testid="stSelectbox"]:focus-within div[data-baseweb="select"] > div,
div[data-testid="stTextInput"]:focus-within input,
div[data-testid="stNumberInput"]:focus-within input {
    border-color: var(--input-focus-border) !important;
    box-shadow: 0 0 0 3px var(--input-focus-shadow) !important;
}

/* תפריט נפתח (Dropdown popover & options) */
div[data-baseweb="popover"],
div[data-baseweb="popover"] *,
div[data-baseweb="menu"],
div[data-baseweb="menu"] *,
ul[role="listbox"],
ul[role="listbox"] *,
div[data-testid="stSelectboxVirtualDropdown"],
div[data-testid="stSelectboxVirtualDropdown"] * {
    background-color: var(--bg-card) !important;
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
}

div[data-baseweb="popover"] > div,
ul[role="listbox"] {
    border: 1.5px solid var(--border-color) !important;
    border-radius: 12px !important;
    box-shadow: 0 12px 32px rgba(0,0,0,0.12) !important;
    padding: 4px !important;
}

li[role="option"] {
    background-color: var(--bg-card) !important;
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    font-size: 13px !important;
    border-radius: 8px !important;
    margin: 2px 0 !important;
    padding: 8px 12px !important;
    transition: all 0.15s ease !important;
}

li[role="option"]:hover,
li[role="option"]:hover *,
li[role="option"][aria-selected="true"],
li[role="option"][aria-selected="true"] * {
    background-color: var(--bg-card-hover) !important;
    background: var(--bg-card-hover) !important;
    color: var(--accent-mint) !important;
    font-weight: 700 !important;
}

div[role="radiogroup"] {
    direction: __DIR__ !important;
    justify-content: flex-start !important;
}

[data-testid="stMetric"] {
    direction: __DIR__ !important;
    text-align: __ALIGN__ !important;
    background: var(--metric-bg) !important;
    border: 1px solid var(--metric-border) !important;
    border-radius: 12px !important;
    padding: 10px 14px !important;
}
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"] {
    direction: __DIR__ !important;
    text-align: __ALIGN__ !important;
    justify-content: flex-start !important;
}
[data-testid="stMetricLabel"] {
    color: var(--text-secondary) !important;
}
[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-weight: 900 !important;
}

div[data-testid="stAlert"] {
    direction: __DIR__ !important;
    text-align: __ALIGN__ !important;
    border-radius: 10px !important;
    border: 1px solid var(--border-color) !important;
    background: var(--bg-card) !important;
}

div[data-testid="stExpander"] {
    direction: __DIR__ !important;
    text-align: __ALIGN__ !important;
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
}

div[data-testid="stDataFrame"] {
    direction: __DIR__ !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid var(--border-color) !important;
    background: var(--bg-card) !important;
}

/* בידוד LTR עבור נתונים באנגלית, מספרים, תגיות מחיר ויריבות */
.ltr-tag, .badge-fdr, .mini-fxt, .badge-c, .badge-vc, #fpl-clock {
    direction: ltr !important;
    unicode-bidi: isolate;
    display: inline-block;
}

/* --- 2. טאבים רשמיים --- */
div[data-baseweb="tab-list"] {
    background: var(--tab-bg) !important;
    border-radius: 12px !important;
    padding: 5px 6px !important;
    border: 1px solid var(--tab-border) !important;
    gap: 5px !important;
    overflow-x: auto !important;
    overflow-y: hidden !important;
    white-space: nowrap !important;
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
    margin-bottom: 16px !important;
    direction: __DIR__ !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06) !important;
}
div[data-baseweb="tab-list"]::-webkit-scrollbar {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
}
button[data-baseweb="tab"] {
    border-radius: 8px !important;
    padding: 7px 13px !important;
    color: var(--tab-text) !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    transition: all 0.2s ease !important;
    border: none !important;
    background: transparent !important;
    flex-shrink: 0 !important;
}
button[data-baseweb="tab"]:hover {
    color: var(--tab-hover-text) !important;
    background: var(--tab-hover-bg) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--tab-active-text) !important;
    background: var(--tab-active-bg) !important;
    border: 1.5px solid var(--tab-active-border) !important;
    box-shadow: 0 2px 12px var(--tab-active-shadow) !important;
}
div[data-baseweb="tab-highlight"],
div[data-baseweb="tab-border"] {
    display: none !important;
}

/* ביטול מוחלט של חיצי גלילה, מעברי צבע ומחווני גלילה של טאבים */
div[data-testid="stTabs"] button[data-baseweb="tab-scroll-left"],
div[data-testid="stTabs"] button[data-baseweb="tab-scroll-right"],
div[data-testid="stTabs"] button[aria-label*="scroll" i],
div[data-testid="stTabs"] button[aria-label*="Scroll"],
div[data-testid="stTabs"] button[aria-label*="next" i],
div[data-testid="stTabs"] button[aria-label*="prev" i],
div[data-testid="stTabs"] [class*="ScrollButton"],
div[data-testid="stTabs"] [class*="scrollButton"],
div[data-testid="stTabs"] [class*="StyledScrollButton"],
div[data-testid="stTabs"] [class*="StyledStartEnhancer"],
div[data-testid="stTabs"] [class*="StyledEndEnhancer"],
div[data-testid="stTabs"] [class*="StyledTabScrollButton"],
div[data-testid="stTabs"] div[data-baseweb="tab-list-container"] button:not([data-baseweb="tab"]),
div[data-testid="stTabs"] > div:first-child button:not([data-baseweb="tab"]),
div[data-testid="stTabs"] div[data-baseweb="tab-list"] ~ button,
div[data-testid="stTabs"] div[data-baseweb="tab-list"] ~ div:not([data-baseweb="tab-panel"]) {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    width: 0 !important;
    height: 0 !important;
    max-width: 0 !important;
    max-height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    background: transparent !important;
}

/* --- 3. כרטיס כניסה / שער --- */
.gate-card {
    background: var(--gate-bg);
    border: 1.5px solid var(--gate-border);
    border-radius: 20px;
    padding: 30px 22px;
    margin: 20px auto;
    max-width: 560px;
    text-align: center;
    box-shadow: var(--gate-shadow);
}

/* --- 4. מדדי KPI בראש האתר --- */
.kpi-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 12px;
    margin-bottom: 18px;
}
.kpi-card {
    backdrop-filter: blur(12px);
    border-radius: 14px;
    padding: 14px 12px;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.kpi-card:hover {
    transform: translateY(-2px);
}
.kpi-card-score {
    background: var(--kpi-score-bg) !important;
    border: 1.5px solid var(--kpi-score-border) !important;
    box-shadow: 0 6px 20px var(--kpi-score-shadow) !important;
}
.kpi-card-xp {
    background: var(--kpi-xp-bg) !important;
    border: 1.5px solid var(--kpi-xp-border) !important;
    box-shadow: 0 6px 20px var(--kpi-xp-shadow) !important;
}
.kpi-card-bank {
    background: var(--kpi-bank-bg) !important;
    border: 1.5px solid var(--kpi-bank-border) !important;
    box-shadow: 0 6px 20px var(--kpi-bank-shadow) !important;
}
.kpi-card-rank {
    background: var(--kpi-rank-bg) !important;
    border: 1.5px solid var(--kpi-rank-border) !important;
    box-shadow: 0 6px 20px var(--kpi-rank-shadow) !important;
}
.kpi-title {
    font-size: 11px;
    color: var(--text-secondary);
    margin-bottom: 4px;
    font-weight: 700;
}
.kpi-value {
    font-size: 20px;
    font-weight: 900;
    color: var(--text-primary);
}

/* --- 5. מגרש אצטדיון פרימיום --- */
div[data-testid="stVerticalBlock"]:has(> div .pitch-anchor) {
    max-width: 940px !important;
    margin: 0 auto 12px auto !important;
    background: var(--pitch-bg) !important;
    border: 2px solid var(--pitch-border) !important;
    border-radius: 18px !important;
    padding: 18px 10px !important;
    box-shadow: var(--pitch-shadow) !important;
    position: relative !important;
    text-align: center !important;
}
div[data-testid="column"] div[data-testid="stVerticalBlock"]:has(> div .pitch-anchor) {
    max-width: 100% !important;
}

.pitch-anchor {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
    border: 1.5px solid var(--pitch-line);
    border-radius: 14px;
    margin: 8px;
}
.pitch-anchor::before {
    content: "";
    position: absolute;
    top: 50%;
    left: 0;
    right: 0;
    height: 1.5px;
    background: var(--pitch-line);
    transform: translateY(-50%);
}
.pitch-anchor::after {
    content: "";
    position: absolute;
    top: 50%;
    left: 50%;
    width: 90px;
    height: 90px;
    border: 1.5px solid var(--pitch-line);
    border-radius: 50%;
    transform: translate(-50%, -50%);
}

/* --- 5.2 ספסל מחליפים מובלט (Tactical Dugout) --- */
div[data-testid="stVerticalBlock"]:has(> div .bench-anchor) {
    max-width: 940px !important;
    margin: 14px auto 22px auto !important;
    background: var(--bench-bg) !important;
    border: 2px solid var(--bench-border) !important;
    border-radius: 18px !important;
    padding: 16px 14px !important;
    box-shadow: var(--bench-shadow) !important;
    position: relative !important;
    text-align: center !important;
}
div[data-testid="column"] div[data-testid="stVerticalBlock"]:has(> div .bench-anchor) {
    max-width: 100% !important;
}

.bench-dugout-badge {
    background: var(--bench-dugout-badge-bg);
    border: 1px solid var(--bench-dugout-badge-border);
    border-radius: 10px;
    padding: 7px 14px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    direction: __DIR__;
}

/* --- 6. ביטול מרווחים מוחלט ואיחוד כרטיס שחקן וכפתור לפלאק רציף אחד --- */
div[data-testid="column"]:has(.p-card-fpl) *,
div[data-testid="column"]:has(.card-bench) * {
    text-align: center !important;
}

div[data-testid="column"]:has(.p-card-fpl),
div[data-testid="column"]:has(.card-bench),
div[data-testid="column"]:has(.p-card-fpl) > div,
div[data-testid="column"]:has(.card-bench) > div,
div[data-testid="column"]:has(.p-card-fpl) div[data-testid="stVerticalBlock"],
div[data-testid="column"]:has(.card-bench) div[data-testid="stVerticalBlock"],
div[data-testid="stVerticalBlock"]:has(.pitch-anchor) [data-testid="column"],
div[data-testid="stVerticalBlock"]:has(.bench-anchor) [data-testid="column"] {
    gap: 0 !important;
    row-gap: 0 !important;
    background: transparent !important;
    background-color: transparent !important;
    background-image: none !important;
    border: none !important;
    box-shadow: none !important;
}

div[data-testid="stVerticalBlock"]:has(.pitch-anchor) [data-testid="element-container"],
div[data-testid="stVerticalBlock"]:has(.bench-anchor) [data-testid="element-container"],
div[data-testid="column"]:has(.p-card-fpl) [data-testid="element-container"],
div[data-testid="column"]:has(.card-bench) [data-testid="element-container"] {
    margin: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
}

div[data-testid="stVerticalBlock"]:has(.pitch-anchor) div[data-testid="column"] div[data-testid="stMarkdownContainer"],
div[data-testid="stVerticalBlock"]:has(.bench-anchor) div[data-testid="column"] div[data-testid="stMarkdownContainer"],
div[data-testid="stVerticalBlock"]:has(.pitch-anchor) div[data-testid="column"] div[data-testid="stMarkdownContainer"] > div,
div[data-testid="stVerticalBlock"]:has(.bench-anchor) div[data-testid="column"] div[data-testid="stMarkdownContainer"] > div {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    text-align: center !important;
    margin: 0 auto !important;
    width: 100% !important;
}

div[data-testid="stVerticalBlock"]:has(.pitch-anchor) div[data-testid="column"] div[data-testid="stButton"],
div[data-testid="stVerticalBlock"]:has(.bench-anchor) div[data-testid="column"] div[data-testid="stButton"],
div[data-testid="column"]:has(.p-card-fpl) div[data-testid="stButton"],
div[data-testid="column"]:has(.card-bench) div[data-testid="stButton"] {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    width: 100% !important;
    margin: 0 auto !important;
    margin-top: -3px !important;
    padding: 0 !important;
}

/* --- 6.1 כרטיס שחקן עליון (Top Plaque) - מוגדל ומרווח --- */
.p-card-fpl {
    background: var(--p-card-bg) !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
    border: 1px solid var(--p-card-border) !important;
    border-bottom: 1px solid var(--p-card-border-bottom) !important;
    border-radius: 12px 12px 0 0 !important;
    padding: 5px 4px !important;
    text-align: center !important;
    box-shadow: var(--p-card-shadow) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    overflow: hidden !important;
    position: relative !important;
    width: 100% !important;
    max-width: 126px !important;
    min-width: 0 !important;
    height: 164px !important;
    min-height: 164px !important;
    max-height: 164px !important;
    box-sizing: border-box !important;
    margin: 0 auto !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    align-items: center !important;
    direction: ltr !important;
}

.p-card-fpl * {
    direction: ltr !important;
    text-align: center !important;
}

/* --- 6.2 עיצוב כפתורים כללי - מסגרת סגורה מכל 4 הצדדים עם פינות מעוגלות --- */
div[data-testid="stButton"] button {
    border-radius: 10px !important;
    border: 1.5px solid var(--btn-general-border) !important;
    background: var(--btn-general-bg) !important;
    color: var(--btn-general-text) !important;
    font-weight: 700 !important;
    padding: 6px 14px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

div[data-testid="stButton"] button:hover {
    border-color: var(--accent-mint) !important;
    color: var(--btn-general-hover-text) !important;
    background: var(--btn-general-hover-bg) !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12) !important;
    transform: translateY(-1px);
}

div[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    border: 1.5px solid #10b981 !important;
    color: #ffffff !important;
    font-weight: 900 !important;
    box-shadow: 0 2px 12px rgba(16, 185, 129, 0.4) !important;
}

/* כפתור פעולה תחתון מחובר ומותאם אך ורק לכרטיסי שחקנים במגרש (Bottom Plaque Action Strip) */
div[data-testid="column"]:has(.p-card-fpl) div[data-testid="stButton"] button,
div[data-testid="column"]:has(.card-bench) div[data-testid="stButton"] button,
div[data-testid="stVerticalBlock"]:has(.pitch-anchor) [data-testid="column"] div[data-testid="stButton"] button,
div[data-testid="stVerticalBlock"]:has(.bench-anchor) [data-testid="column"] div[data-testid="stButton"] button {
    height: 32px !important;
    min-height: 32px !important;
    line-height: 1 !important;
    font-size: 11.5px !important;
    font-weight: 700 !important;
    padding: 0 2px !important;
    border-radius: 0 0 12px 12px !important;
    border-top-left-radius: 0 !important;
    border-top-right-radius: 0 !important;
    margin: 0 auto !important;
    margin-top: -2px !important;
    background: var(--p-card-btn-bg) !important;
    border: 1px solid var(--p-card-btn-border) !important;
    border-top: none !important;
    color: var(--p-card-btn-text) !important;
    width: 100% !important;
    max-width: 126px !important;
    min-width: 0 !important;
    text-align: center !important;
    justify-content: center !important;
    display: flex !important;
    align-items: center !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.06) !important;
    transition: all 0.15s ease !important;
}

/* הבהוב והרמה במעבר עכבר - איחוד מלא בין הכרטיס לכפתור תחת שחקן */
div[data-testid="column"]:has(.p-card-fpl):hover .p-card-fpl {
    border-color: var(--accent-mint) !important;
    box-shadow: 0 6px 18px rgba(0,0,0,0.18), 0 0 14px rgba(16, 185, 129, 0.25) !important;
    transform: translateY(-2px);
}
div[data-testid="column"]:has(.p-card-fpl):hover div[data-testid="stButton"] button {
    border-color: var(--accent-mint) !important;
    color: var(--p-card-btn-hover-text) !important;
    background: var(--p-card-btn-hover-bg) !important;
    transform: translateY(-2px);
}

/* מצב שחקן נבחר לחילוף */
.p-card-selected {
    border: 2px solid var(--accent-mint) !important;
    border-bottom: 1px solid var(--accent-mint) !important;
    box-shadow: 0 0 18px rgba(16, 185, 129, 0.6) !important;
}
.p-card-transfer-selected {
    border: 2px solid #e11d48 !important;
    border-bottom: 1px solid #e11d48 !important;
    box-shadow: 0 0 18px rgba(225, 29, 72, 0.6) !important;
}

div[data-testid="column"]:has(.p-card-fpl) div[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    border: 1.5px solid #10b981 !important;
    border-top: none !important;
    color: #ffffff !important;
    font-weight: 900 !important;
    box-shadow: 0 0 16px rgba(16, 185, 129, 0.5) !important;
}

/* כרטיסים וכפתורים בספסל */
.card-bench {
    background: var(--card-bench-bg) !important;
    border: 1.5px solid var(--card-bench-border) !important;
    border-bottom: 1px solid var(--p-card-border-bottom) !important;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08) !important;
}
div[data-testid="column"]:has(.card-bench) div[data-testid="stButton"] button {
    background: var(--card-bench-btn-bg) !important;
    border: 1.5px solid var(--card-bench-btn-border) !important;
    border-top: none !important;
    border-radius: 0 0 12px 12px !important;
    color: var(--card-bench-btn-text) !important;
}

.cap-gold { border: 2px solid #eab308 !important; border-bottom: 1px solid rgba(234, 179, 8, 0.4) !important; box-shadow: 0 0 14px rgba(234, 179, 8, 0.35) !important; }
.vc-silver { border: 2px solid #94a3b8 !important; border-bottom: 1px solid rgba(148, 163, 184, 0.4) !important; }
.card-danger { border: 2px solid #e11d48 !important; border-bottom: 1px solid rgba(225, 29, 72, 0.4) !important; background: rgba(225, 29, 72, 0.12) !important; }
.card-warning { border: 2px solid #eab308 !important; border-bottom: 1px solid rgba(234, 179, 8, 0.4) !important; background: rgba(234, 179, 8, 0.12) !important; }

/* תגיות C ו-VC רשמיות */
.badge-c {
    background: #eab308;
    color: #0f172a;
    font-weight: 900;
    font-size: 9.5px;
    line-height: 1;
    padding: 2px 4px;
    border-radius: 4px;
    margin-left: 3px;
    display: inline-block;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3);
    vertical-align: middle;
}

.badge-vc {
    background: #94a3b8;
    color: #ffffff;
    font-weight: 900;
    font-size: 9.5px;
    line-height: 1;
    padding: 2px 4px;
    border-radius: 4px;
    margin-left: 3px;
    display: inline-block;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3);
    vertical-align: middle;
}

/* לוחית שם שחקן - מותאמת ערכת נושא */
.p-name-plate,
[data-testid="stMarkdownContainer"] .p-name-plate {
    background: var(--p-name-plate-bg) !important;
    border: 1px solid var(--p-name-plate-border) !important;
    border-radius: 6px !important;
    padding: 3px 6px !important;
    margin: 3px 0 2px 0 !important;
    width: 96% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 3px !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
}

.p-name-txt,
[data-testid="stMarkdownContainer"] .p-name-txt,
.p-card-fpl .p-name-txt {
    font-weight: 800 !important;
    font-size: 12.5px !important;
    color: var(--p-name-plate-text) !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    line-height: 1.2 !important;
    text-align: center !important;
    direction: ltr !important;
    display: inline-block !important;
}

.p-sub {
    font-size: 9px;
    color: var(--text-muted);
    margin: 1px 0;
    width: 100%;
    text-align: center;
    direction: ltr;
}

.p-card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 92%;
    margin-top: auto;
    padding-top: 2px;
    border-top: 1px solid var(--border-color);
}
.p-card-cost {
    font-size: 9.5px;
    font-weight: 700;
    color: var(--text-secondary);
    direction: ltr;
}
.p-card-xp {
    font-size: 11px;
    font-weight: 900;
    color: var(--accent-mint);
    direction: ltr;
}

.badge-fdr {
    font-size: 8.5px;
    font-weight: 800;
    padding: 1px 5px;
    border-radius: 4px;
    display: inline-block;
    line-height: 1.2;
    text-align: center;
    border: 1px solid rgba(0, 0, 0, 0.1);
}
.fdr-2 { background: #15803d; color: #ffffff; }
.fdr-3 { background: #475569; color: #ffffff; }
.fdr-4 { background: #b91c1c; color: #ffffff; }
.fdr-5 { background: #7f1d1d; color: #ffffff; }

.prob-badge {
    font-size: 8px;
    font-weight: 800;
    padding: 1px 4px;
    border-radius: 3px;
    margin: 1px auto 0 auto;
    width: fit-content;
    line-height: 1.1;
}
.prob-red { background: rgba(225, 29, 72, 0.18); color: #e11d48; border: 1px solid #e11d48; }
.prob-yellow { background: rgba(234, 179, 8, 0.18); color: #d97706; border: 1px solid #eab308; }

.mini-fxt-container { 
    display: flex !important; 
    justify-content: center !important; 
    align-items: center !important;
    gap: 3px !important; 
    margin: 2px auto 0 auto !important; 
    direction: ltr !important;
    width: 100% !important;
}
.mini-fxt { 
    font-size: 8px !important; 
    font-weight: 800 !important; 
    text-transform: uppercase !important; 
    padding: 1px 3px !important; 
    border-radius: 3px !important; 
    color: #ffffff !important; 
    line-height: 1.1 !important; 
    text-shadow: 0 1px 1px rgba(0,0,0,0.4) !important;
    direction: ltr !important;
    display: inline-block !important;
}

/* --- 7. מערכת כרטיסים גלובלית ואחידה לכל הקטגוריות (Tabs 2-7) --- */
.accessible-card {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 14px !important;
    padding: 16px 18px !important;
    margin-bottom: 14px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06) !important;
    transition: all 0.2s ease !important;
    direction: __DIR__ !important;
}
.accessible-card:hover {
    background: var(--bg-card-hover) !important;
    border-color: var(--accent-mint) !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1) !important;
}

.split-box {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    border-bottom: 1px solid var(--border-color) !important;
    padding-bottom: 8px !important;
    margin-bottom: 10px !important;
    direction: __DIR__ !important;
}

.meta-chip {
    font-size: 11px !important;
    font-weight: 700 !important;
    background: var(--badge-mint-bg) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
    padding: 2px 8px !important;
    border-radius: 6px !important;
    display: inline-block !important;
}

.flaw-row {
    background: rgba(225, 29, 72, 0.08) !important;
    border: 1px solid rgba(225, 29, 72, 0.25) !important;
    border-right: 4px solid #e11d48 !important;
    border-left: 4px solid #e11d48 !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    margin-bottom: 8px !important;
    font-size: 12.5px !important;
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    direction: __DIR__ !important;
    color: var(--text-primary) !important;
}
.flaw-pen {
    background: rgba(225, 29, 72, 0.2) !important;
    border: 1px solid rgba(225, 29, 72, 0.4) !important;
    color: #e11d48 !important;
    padding: 2px 8px !important;
    border-radius: 6px !important;
    font-weight: 800 !important;
    font-size: 11px !important;
    direction: ltr !important;
}

.comparison-panel-out {
    background: rgba(225, 29, 72, 0.08) !important;
    border: 1px solid rgba(225, 29, 72, 0.25) !important;
    border-radius: 10px !important;
    padding: 10px 12px !important;
    line-height: 1.5 !important;
    direction: __DIR__ !important;
    color: var(--text-primary) !important;
}
.comparison-panel-in {
    background: rgba(16, 185, 129, 0.08) !important;
    border: 1px solid rgba(16, 185, 129, 0.25) !important;
    border-radius: 10px !important;
    padding: 10px 12px !important;
    line-height: 1.5 !important;
    direction: __DIR__ !important;
    color: var(--text-primary) !important;
}

.transfer-drawer {
    background: var(--bg-card) !important;
    border: 1.5px solid var(--accent-mint) !important;
    border-radius: 14px !important;
    padding: 16px !important;
    margin: 12px auto 18px auto !important;
    max-width: 940px !important;
    box-shadow: 0 12px 36px rgba(0,0,0,0.1) !important;
    direction: __DIR__ !important;
}

.rebuild-banner {
    background: var(--bg-card) !important;
    border: 1.5px solid var(--accent-mint) !important;
    border-radius: 14px !important;
    padding: 14px 18px !important;
    margin: 12px auto 16px auto !important;
    max-width: 940px !important;
    box-shadow: 0 10px 28px rgba(0,0,0,0.1) !important;
    direction: __DIR__ !important;
}

/* --- פאנל משחקי מחזור LiveFPL (Gameweek Fixtures Panel) --- */
.gw-fixtures-card {
    background: var(--fxt-card-bg) !important;
    border: 1.5px solid var(--fxt-card-border) !important;
    border-radius: 16px !important;
    padding: 14px 16px !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08) !important;
    direction: ltr !important;
    margin-bottom: 16px !important;
}

.gw-fixtures-header {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    padding-bottom: 10px !important;
    margin-bottom: 12px !important;
    border-bottom: 1px solid var(--border-color) !important;
    direction: __DIR__ !important;
}

.gw-fixtures-scroll {
    max-height: 600px !important;
    overflow-y: auto !important;
    padding-right: 4px !important;
    scrollbar-width: thin !important;
}

.fxt-date-header {
    font-size: 11.5px !important;
    font-weight: 800 !important;
    color: var(--text-secondary) !important;
    margin: 12px 0 6px 2px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    direction: __DIR__ !important;
    text-align: __ALIGN__ !important;
}

.fxt-match-row {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    background: var(--fxt-row-bg) !important;
    border: 1px solid var(--fxt-row-border) !important;
    border-radius: 10px !important;
    padding: 7px 10px !important;
    margin-bottom: 6px !important;
    transition: all 0.15s ease !important;
    direction: ltr !important;
}

.fxt-match-row:hover {
    background: var(--fxt-row-hover) !important;
    border-color: var(--accent-mint) !important;
    transform: translateY(-1px) !important;
}

.fxt-team {
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
    flex: 1 !important;
    direction: ltr !important;
}

.fxt-home {
    justify-content: flex-end !important;
}

.fxt-away {
    justify-content: flex-start !important;
}

.fxt-team-name {
    font-size: 12.5px !important;
    font-weight: 800 !important;
    color: var(--text-primary) !important;
    letter-spacing: 0.3px !important;
}

.fxt-jersey svg {
    width: 28px !important;
    height: 24px !important;
    display: block !important;
}

.fxt-mid {
    min-width: 72px !important;
    text-align: center !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    direction: ltr !important;
}

.fxt-mid-time {
    font-size: 11.5px !important;
    font-weight: 800 !important;
    color: var(--text-primary) !important;
    background: var(--badge-ko-bg) !important;
    padding: 2px 8px !important;
    border-radius: 6px !important;
    letter-spacing: 0.5px !important;
    border: 1px solid var(--border-color) !important;
}

.fxt-mid-score {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    gap: 2px !important;
}

.fxt-score-num {
    font-size: 13.5px !important;
    font-weight: 900 !important;
    color: var(--text-primary) !important;
    letter-spacing: 1px !important;
}

.fxt-score-live {
    color: #ef4444 !important;
}

.fxt-status-badge {
    font-size: 8.5px !important;
    font-weight: 800 !important;
    color: var(--text-muted) !important;
    text-transform: uppercase !important;
}

.fxt-badge-live {
    color: #ef4444 !important;
    background: rgba(239, 68, 68, 0.15) !important;
    padding: 1px 5px !important;
    border-radius: 3px !important;
}

/* מגרש כדורגל וספסל - שורות שחקנים רספונסיביות ללא שבירת עמודות */
div[data-testid="stVerticalBlock"]:has(.pitch-anchor) div[data-testid="stHorizontalBlock"],
div[data-testid="stVerticalBlock"]:has(.bench-anchor) div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    justify-content: center !important;
    align-items: stretch !important;
    gap: 4px !important;
    margin: 0 auto !important;
    width: 100% !important;
    max-width: 100% !important;
}

div[data-testid="stVerticalBlock"]:has(.pitch-anchor) div[data-testid="column"],
div[data-testid="stVerticalBlock"]:has(.bench-anchor) div[data-testid="column"] {
    min-width: 0 !important;
    flex: 1 1 0px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: flex-start !important;
    padding: 0 2px !important;
}

/* מרכז טופס הכניסה לשער */
div[data-testid="stVerticalBlock"]:has(.gate-form-anchor) {
    max-width: 480px !important;
    margin: 0 auto !important;
    width: 100% !important;
}

/* מתכנן מחזורים - פריסה אנכית במכשירים עם מסך עד 900px */
@media (max-width: 900px) {
    div[data-testid="stVerticalBlock"]:has(.planner-split-anchor) > div[data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        flex-wrap: wrap !important;
    }
    div[data-testid="stVerticalBlock"]:has(.planner-split-anchor) > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        flex: 1 1 100% !important;
    }
}

/* --- 8. התאמות מובייל קפדניות (Mobile Media Queries) --- */
@media (max-width: 640px) {
    .block-container {
        padding-top: 0.6rem !important;
        padding-bottom: max(2rem, env(safe-area-inset-bottom)) !important;
        padding-left: 0.4rem !important;
        padding-right: 0.4rem !important;
    }
    div[data-testid="stVerticalBlock"]:has(.pitch-anchor) {
        padding: 6px 2px !important;
        border-radius: 12px !important;
    }
    div[data-testid="stVerticalBlock"]:has(.bench-anchor) {
        padding: 6px 2px !important;
        border-radius: 12px !important;
    }
    div[data-testid="stVerticalBlock"]:has(.pitch-anchor) div[data-testid="stHorizontalBlock"],
    div[data-testid="stVerticalBlock"]:has(.bench-anchor) div[data-testid="stHorizontalBlock"] {
        gap: 2px !important;
        flex-wrap: nowrap !important;
    }
    div[data-testid="column"] {
        padding: 0 1px !important;
        min-width: 0 !important;
    }
    .p-card-fpl {
        padding: 3px 2px !important;
        border-radius: 8px 8px 0 0 !important;
        max-width: 70px !important;
        width: 100% !important;
        height: 134px !important;
        min-height: 134px !important;
        max-height: 134px !important;
    }
    .p-card-fpl svg {
        width: 32px !important;
        height: 28px !important;
    }
    .p-name-plate {
        padding: 2px 2px !important;
        border-radius: 4px !important;
        margin: 2px 0 1px 0 !important;
        width: 98% !important;
        background: var(--p-name-plate-bg) !important;
        border: 1px solid var(--p-name-plate-border) !important;
    }
    .p-name-txt {
        font-size: 9px !important;
        font-weight: 800 !important;
        color: var(--p-name-plate-text) !important;
    }
    .p-sub, .badge-fdr, .mini-fxt {
        font-size: 7px !important;
        padding: 1px 2px !important;
    }
    .badge-c, .badge-vc {
        font-size: 7px !important;
        padding: 1px 2px !important;
    }
    .p-card-cost {
        font-size: 8px !important;
    }
    .p-card-xp {
        font-size: 9px !important;
    }
    div[data-testid="column"]:has(.p-card-fpl) div[data-testid="stButton"] button,
    div[data-testid="column"]:has(.card-bench) div[data-testid="stButton"] button {
        height: 26px !important;
        min-height: 26px !important;
        font-size: 9.5px !important;
        padding: 0 1px !important;
        border-radius: 0 0 8px 8px !important;
        max-width: 70px !important;
        width: 100% !important;
        margin-top: -3px !important;
    }
    .kpi-container {
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 8px !important;
    }
    .kpi-card {
        padding: 10px 8px !important;
    }
    .kpi-title {
        font-size: 10px !important;
    }
    .kpi-value {
        font-size: 17px !important;
    }
    div[data-baseweb="tab-list"] {
        -webkit-overflow-scrolling: touch !important;
        padding: 4px !important;
    }
    button[data-baseweb="tab"] {
        padding: 6px 10px !important;
        font-size: 11.5px !important;
    }
    div[data-testid="stButton"] button {
        padding: 5px 8px !important;
        font-size: 11.5px !important;
    }
    .fxt-team-name {
        font-size: 10.5px !important;
    }
    .fxt-jersey svg {
        width: 20px !important;
        height: 18px !important;
    }
    .fxt-mid {
        min-width: 50px !important;
    }
    .fxt-mid-time {
        font-size: 9.5px !important;
        padding: 1px 4px !important;
    }
    [data-testid="stMetric"] {
        padding: 6px 8px !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 11px !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 16px !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: 11px !important;
    }
    div:has(> .comparison-panel-out) {
        grid-template-columns: 1fr !important;
        gap: 8px !important;
    }
}
</style>
"""

is_rtl = (st.session_state.get("app_lang", "he") == "he")
dir_val = "rtl" if is_rtl else "ltr"
align_val = "right" if is_rtl else "left"
rendered_css = css_template.replace("__ROOT_VARS__", root_vars).replace("__DIR__", dir_val).replace("__ALIGN__", align_val)
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
        return {}, 4, "", {}

    teams = {t["id"]: t for t in bootstrap["teams"]}
    elements = {el["id"]: el for el in bootstrap["elements"]}

    gw_fixtures_by_event = {}
    for f in fixtures:
        ev = f.get("event")
        if ev is not None:
            if ev not in gw_fixtures_by_event:
                gw_fixtures_by_event[ev] = []
            h_team = teams.get(f["team_h"], {}).get("short_name", "H")
            a_team = teams.get(f["team_a"], {}).get("short_name", "A")
            gw_fixtures_by_event[ev].append({
                "id": f.get("id"),
                "team_h": h_team,
                "team_a": a_team,
                "team_h_diff": f.get("team_h_difficulty", 3),
                "team_a_diff": f.get("team_a_difficulty", 3),
                "team_h_score": f.get("team_h_score"),
                "team_a_score": f.get("team_a_score"),
                "started": f.get("started", False),
                "finished": f.get("finished", False),
                "kickoff_time": f.get("kickoff_time", ""),
            })

    for ev in gw_fixtures_by_event:
        gw_fixtures_by_event[ev].sort(key=lambda x: x["kickoff_time"] or "")

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
        team_short = teams.get(el["team"], {}).get("short_name", "FPL")
        gw_fixtures_map = {}
        upcoming = []
        fdr_list = []

        for f in fixtures:
            ev = f.get("event")
            if ev in target_gws:
                if f.get("team_h") == el["team"]:
                    opp = teams.get(f.get("team_a"), {}).get("short_name", "A")
                    diff = f.get("team_h_difficulty", 3)
                    gw_fixtures_map[ev] = (f"{opp} (H)", diff)
                elif f.get("team_a") == el["team"]:
                    opp = teams.get(f.get("team_h"), {}).get("short_name", "H")
                    diff = f.get("team_a_difficulty", 3)
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
            reason_he = "מייצר מצבים ברצף (xGI גבוה) אך טרם תוגמל במספרים. פוטנציאל התפוצצות."
            reason_en = "High xGI without returns yet. High haul potential."
        elif tag_status == "OVERPERFORMING_TRAP":
            reason_he = "כבש מעבר למצבים הממשיים שייצר. סכנת ירידה לממוצע ולוח מתקשה."
            reason_en = "Outperforming expected stats with toughening fixtures."
        elif el["element_type"] in [1, 2]:
            if team_short in elite_defenses:
                reason_he = "עוגן רשת נקייה מוביל מקבוצה בכירה."
                reason_en = "Top clean sheet anchor from an elite defense."
            else:
                reason_he = "מגן פעיל התקפית בלוח ירוק."
                reason_en = "Attacking defender entering a green fixture run."
        else:
            if form >= 5.0:
                reason_he = "כושר שיא עם מעורבות ישירה בהתקפה."
                reason_en = "In peak form with direct attacking involvement."
            else:
                reason_he = "תוחלת שערים יציבה לקראת משחקים נוחים."
                reason_en = "Reliable goal threat facing favorable upcoming matches."

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
            "reason": reason_he,
            "reason_he": reason_he,
            "reason_en": reason_en,
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

    return processed, next_gw, next_deadline, gw_fixtures_by_event

all_players, next_gw, next_deadline, gw_fixtures_by_event = fetch_league_data()

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

if url_id and url_id.strip().isdigit():
    if st.session_state.get("user_team_id") != url_id.strip():
        st.session_state.user_team_id = url_id.strip()
elif "user_team_id" not in st.session_state:
    st.session_state.user_team_id = None

if not st.session_state.user_team_id:
    c_gate_top1, c_gate_theme, c_gate_top2 = st.columns([4, 1.2, 1])
    with c_gate_theme:
        theme_btn_lbl = t("theme_dark") if st.session_state.get("app_theme", "light") == "light" else t("theme_light")
        if st.button(theme_btn_lbl, key="gate_theme_btn", use_container_width=True):
            st.session_state.app_theme = "dark" if st.session_state.get("app_theme", "light") == "light" else "light"
            st.rerun()
    with c_gate_top2:
        if st.button("English" if st.session_state.app_lang == "he" else "עברית", key="gate_lang_btn", use_container_width=True):
            st.session_state.app_lang = "en" if st.session_state.app_lang == "he" else "he"
            st.rerun()

    st.markdown(
        f"""
    <div class="gate-card">
        <h1 style="color:var(--accent-mint); font-size:28px; font-weight:900; margin-bottom:6px; letter-spacing:-0.5px;">{t('app_title')}</h1>
        <div style="font-size:14px; color:var(--text-secondary); font-weight:500; margin-bottom:14px;">
            {t('app_subtitle')}
        </div>
        <div style="height:1px; background:linear-gradient(90deg, transparent, var(--border-color), transparent); margin:12px 0 16px 0;"></div>
        <p style="font-size:13px; color:var(--text-muted); line-height:1.6; margin-bottom:8px;">
            {t('gate_desc')}
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown('<div class="gate-form-anchor"></div>', unsafe_allow_html=True)
        input_val = st.text_input(
            t("team_id_label"),
            placeholder=t("team_id_placeholder"),
            help=t("team_id_help"),
        )
        b1, b2 = st.columns(2)
        with b1:
            if st.button(t("login_btn"), use_container_width=True, type="primary"):
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

        bank = (picks_res.get("entry_history") or {}).get("bank", 0) / 10
        picks = picks_res.get("picks", []) or []
        team_name = entry_res.get("name", f"Team {t_id}") if entry_res else f"Team {t_id}"
        rank = entry_res.get("summary_overall_rank", "—") if entry_res else "—"
        leagues = (entry_res.get("leagues") or {}).get("classic", []) if entry_res else []
        return picks, bank, team_name, rank, leagues
    except Exception:
        return None, 0.0, None, None, []

raw_picks, initial_bank, my_team_name, my_rank, my_leagues = fetch_user_team(team_id, next_gw)
if not raw_picks:
    err_msg = f"Unable to fetch data for ID {team_id}. Please verify ID." if st.session_state.app_lang == "en" else f"לא ניתן למשוך נתונים עבור מזהה {team_id}. ודא שהמספר תקין."
    st.error(err_msg)
    if st.button(t("back_to_id")):
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
    st.session_state.squad_selected_id = None
    st.session_state.squad_swap_active = False
    st.session_state.squad_transfer_active = False
    st.session_state.planner_plan = {
        g: {"chip": "no_chip", "transfers": []} for g in range(next_gw, 39)
    }
    st.session_state.planner_captains = {}
    st.session_state.planner_selected_id = None
    st.session_state.planner_swap_active = False
    st.session_state.planner_transfer_out = None
    st.session_state.planner_rebuild_active = None
    st.session_state.planner_rebuild_picks = []
    st.session_state.planner_rebuild_target_pos = None

# ניהול מצבי בחירה, חילוף והעברות
if "squad_selected_id" not in st.session_state:
    st.session_state.squad_selected_id = None
if "squad_swap_active" not in st.session_state:
    st.session_state.squad_swap_active = False
if "squad_transfer_active" not in st.session_state:
    st.session_state.squad_transfer_active = False

if "planner_plan" not in st.session_state:
    st.session_state.planner_plan = {
        g: {"chip": "no_chip", "transfers": []} for g in range(next_gw, 39)
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
    if not p_info:
        p_info = {
            "id": pid,
            "name": f"Player {pid}",
            "team": "FPL",
            "pos_code": 2,
            "cost": 4.0,
            "xp": 0.0,
            "status": "u",
            "chance": 0,
            "start_prob": 0,
            "next_match": "-",
            "next_fdr": 3,
            "total_points": 0,
            "tag": "",
            "form": 0.0,
        }
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
is_en = (st.session_state.app_lang == "en")

for p in starters:
    if p["status"] != "a" or p["chance"] < 100:
        pen = 6.5 if p["chance"] <= 25 else 4.0
        total_penalty += pen
        f_type = "🚑 Starting Fitness" if is_en else "🚑 כשירות בהרכב"
        f_txt = (
            f"<b>{p['name']}</b> doubtful/injured ({p['chance']}% fitness | {p['start_prob']}% start probability)."
            if is_en
            else f"<b>{p['name']}</b> בספק/פצוע ({p['chance']}% כשירות רפואית | {p['start_prob']}% סבירות לפתוח)."
        )
        squad_flaws.append({"type": f_type, "penalty": f"-{pen:.1f}", "text": f_txt})

for bp in bench:
    if bp["status"] != "a" or bp["chance"] < 100:
        pen = 3.0
        total_penalty += pen
        f_type = "🚑 Bench Disabled" if is_en else "🚑 ספסל מושבת"
        f_txt = (
            f"<b>{bp['name']}</b> injured/disabled ({bp['chance']}%) - no auto-sub cover."
            if is_en
            else f"<b>{bp['name']}</b> פצוע/מושבת ({bp['chance']}%) - אין גיבוי אוטומטי בהיעדרות."
        )
        squad_flaws.append({"type": f_type, "penalty": f"-{pen:.1f}", "text": f_txt})

for p in starters:
    if p["pos_code"] in [1, 2] and p["next_fdr"] >= 4:
        pen = 4.0
        total_penalty += pen
        f_type = "⚠️ Defense Conceding Risk" if is_en else "⚠️ הגנה בסיכון ספיגה"
        f_txt = (
            f"<b>{p['name']}</b> facing tough fixture (<span class='ltr-tag'>{p['next_match']}</span>, FDR {p['next_fdr']})."
            if is_en
            else f"<b>{p['name']}</b> מול יריבה קשה (<span class='ltr-tag'>{p['next_match']}</span>, FDR {p['next_fdr']})."
        )
        squad_flaws.append({"type": f_type, "penalty": f"-{pen:.1f}", "text": f_txt})

for p in starters:
    if p["status"] == "a" and p["form"] < 2.5 and p["pos_code"] in [3, 4]:
        pen = 2.0
        total_penalty += pen
        f_type = "⚠️ Cold Attacking Form" if is_en else "⚠️ כושר התקפי דל"
        f_txt = (
            f"<b>{p['name']}</b> in goal drought (form {p['form']}) in recent GWs."
            if is_en
            else f"<b>{p['name']}</b> בבצורת (כושר {p['form']}) במחזורים האחרונים."
        )
        squad_flaws.append({"type": f_type, "penalty": f"-{pen:.1f}", "text": f_txt})

for p in starters:
    if p["tag"] == "OVERPERFORMING_TRAP":
        pen = 1.5
        total_penalty += pen
        f_type = "⚠️ Regression Risk" if is_en else "⚠️ סכנת דעיכה (מלכודת)"
        f_txt = (
            f"<b>{p['name']}</b> scored beyond expected goal involvements (low xGI)."
            if is_en
            else f"<b>{p['name']}</b> הבקיע מעבר למצבי השער שייצר (xGI נמוך)."
        )
        squad_flaws.append({"type": f_type, "penalty": f"-{pen:.1f}", "text": f_txt})

if not formation_valid:
    pen = 8.0
    total_penalty += pen
    f_type = "⚠️ Illegal Formation" if is_en else "⚠️ מערך לא חוקי"
    f_txt = (
        "Current formation is illegal (must have 1 GK, 3-5 DEFs, 2-5 MIDs, 1-3 FWDs)."
        if is_en
        else "המערך הנוכחי אינו חוקי (חובה שוער 1, 3–5 מגנים, 2–5 קשרים ולפחות חלוץ 1)."
    )
    squad_flaws.append({"type": f_type, "penalty": f"-{pen:.1f}", "text": f_txt})

squad_rating = int(max(48, min(86, base_score - total_penalty)))
rating_color = (
    "#00ff87"
    if squad_rating >= 78
    else ("#02efff" if squad_rating >= 70 else "#facc15")
)

# =====================================================================
# 7. סרגל עליון ומדדים ראשיים
# =====================================================================
h_col1, h_col_theme, h_col2, h_col3 = st.columns([3, 1.1, 1, 1])
with h_col1:
    render_html(
        f"""
        <div style="display:flex; align-items:center; gap:10px; padding:4px 0;">
            <div>
                <div style="font-size:22px; font-weight:900; color:var(--text-primary); letter-spacing:-0.3px; line-height:1.2;">{my_team_name}</div>
                <div style="font-size:12px; color:var(--text-secondary); margin-top:2px;">
                    {t("engine_for_gw")} <b style="color:var(--accent-mint);">{next_gw}</b> | {t("team_label")} <span class="ltr-tag"><b>{team_id}</b></span>
                </div>
            </div>
        </div>
        """
    )
with h_col_theme:
    theme_btn_lbl = t("theme_dark") if st.session_state.get("app_theme", "light") == "light" else t("theme_light")
    if st.button(theme_btn_lbl, key="hdr_theme_toggle", use_container_width=True):
        st.session_state.app_theme = "dark" if st.session_state.get("app_theme", "light") == "light" else "light"
        st.rerun()
with h_col2:
    if st.button("English" if st.session_state.app_lang == "he" else "עברית", key="hdr_lang_toggle", use_container_width=True):
        st.session_state.app_lang = "en" if st.session_state.app_lang == "he" else "he"
        st.rerun()
with h_col3:
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
    <div class="kpi-card kpi-card-score">
        <div class="kpi-title">{t('squad_score')}</div>
        <div class="kpi-value" style="color:{rating_color};">{squad_rating} <span style="font-size:12px; color:var(--accent-mint);">/ 100</span></div>
    </div>
    <div class="kpi-card kpi-card-xp">
        <div class="kpi-title">{t('xp_forecast')}</div>
        <div class="kpi-value" style="color:var(--accent-cyan);">{starting_xp_total:.1f}</div>
    </div>
    <div class="kpi-card kpi-card-bank">
        <div class="kpi-title">{t('in_bank')}</div>
        <div class="kpi-value" style="color:var(--accent-gold);"><span class="ltr-tag">£{st.session_state.user_bank:.1f}m</span></div>
    </div>
    <div class="kpi-card kpi-card-rank">
        <div class="kpi-title">{t('overall_rank')}</div>
        <div class="kpi-value" style="color:var(--accent-magenta);"><span class="ltr-tag">{rank_txt}</span></div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# שעון דד-ליין חי ב-HTML/JS
clock_title = f"{t('deadline_time_left')} (GW {next_gw})"
clock_loading = "טוען שעון..." if st.session_state.app_lang == "he" else "Loading clock..."
clock_expired = "הדד-ליין עבר!" if st.session_state.app_lang == "he" else "Deadline Passed!"
clock_dir = "rtl" if st.session_state.app_lang == "he" else "ltr"

is_lt = (st.session_state.get("app_theme", "light") == "light")
clock_bg = "#ffffff" if is_lt else "rgba(26, 15, 46, 0.95)"
clock_border = "#10b981" if is_lt else "#00ff87"
clock_title_col = "#334155" if is_lt else "#e2d9f3"
clock_num_col = "#059669" if is_lt else "#00ff87"
clock_shadow = "0 4px 14px rgba(0,0,0,0.06)" if is_lt else "0 4px 18px rgba(0, 255, 135, 0.25)"

clock_html = f"""
<div style="background:{clock_bg}; border:1.5px solid {clock_border}; border-radius:12px; padding:10px 14px; text-align:center; direction:{clock_dir}; margin-bottom:15px; color:{clock_num_col}; box-shadow:{clock_shadow}; font-family:'Plus Jakarta Sans','Rubik',sans-serif;">
    <div style="font-size:12px; color:{clock_title_col}; font-weight:700; margin-bottom:4px;">{clock_title}</div>
    <div id="fpl-clock" style="font-size:20px; font-weight:900; color:{clock_num_col}; direction:ltr; letter-spacing:1.5px;">{clock_loading}</div>
</div>
<script>
    var deadline = new Date("{next_deadline}").getTime();
    var x = setInterval(function() {{
        var now = new Date().getTime();
        var distance = deadline - now;
        
        if (distance < 0) {{
            clearInterval(x);
            document.getElementById("fpl-clock").innerHTML = "{clock_expired}";
            document.getElementById("fpl-clock").style.color = "#e90052";
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
# 8. פונקציות עזר לרינדור משחקים וכרטיס שחקן עשיר ב-HTML
# =====================================================================
def parse_fixture_datetime(ko_str):
    if not ko_str:
        return "", ""
    try:
        dt = datetime.fromisoformat(ko_str.replace("Z", "+00:00"))
        months_he = {1: "ינו'", 2: "פבר'", 3: "מרץ", 4: "אפר'", 5: "מאי", 6: "יוני", 7: "יולי", 8: "אוג'", 9: "ספט'", 10: "אוק'", 11: "נוב'", 12: "דצמ'"}
        months_en = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
        days_he = {0: "שני", 1: "שלישי", 2: "רביעי", 3: "חמישי", 4: "שישי", 5: "שבת", 6: "ראשון"}
        days_en = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
        lang = st.session_state.get("app_lang", "he")
        
        if lang == "he":
            d_name = days_he.get(dt.weekday(), "")
            m_name = months_he.get(dt.month, "")
            date_label = f"{d_name}, {dt.day} ב{m_name}"
        else:
            d_name = days_en.get(dt.weekday(), "")
            m_name = months_en.get(dt.month, "")
            date_label = f"{d_name} {dt.day} {m_name}"
            
        time_label = dt.strftime("%H:%M")
        return date_label, time_label
    except Exception:
        return "", ko_str[11:16] if len(ko_str) >= 16 else ""

def render_gw_fixtures_panel(gw_num):
    fxts = gw_fixtures_by_event.get(gw_num, [])
    fxt_title = t("gw_fixtures_title").replace("{gw}", str(gw_num))
    
    if not fxts:
        empty_msg = t("no_fixtures_gw")
        render_html(
            f"""
            <div class="gw-fixtures-card">
                <div class="gw-fixtures-header">
                    <span style="font-size:14px; font-weight:800; color:var(--text-primary);">{fxt_title}</span>
                </div>
                <div style="text-align:center; padding:30px 10px; color:var(--text-muted); font-size:13px;">
                    {empty_msg}
                </div>
            </div>
            """
        )
        return

    grouped = {}
    for fx in fxts:
        d_lbl, t_lbl = parse_fixture_datetime(fx.get("kickoff_time", ""))
        fx["_time_label"] = t_lbl
        if d_lbl not in grouped:
            grouped[d_lbl] = []
        grouped[d_lbl].append(fx)

    group_blocks = []
    for d_lbl, day_fixtures in grouped.items():
        rows_html = []
        for fx in day_fixtures:
            h_team = fx["team_h"]
            a_team = fx["team_a"]
            h_diff = fx.get("team_h_diff", 3)
            a_diff = fx.get("team_a_diff", 3)
            h_jersey = get_jersey_svg(h_team)
            a_jersey = get_jersey_svg(a_team)
            
            if fx.get("finished"):
                h_sc = fx.get("team_h_score", 0)
                a_sc = fx.get("team_a_score", 0)
                mid_html = f'<div class="fxt-mid-score"><span class="fxt-score-num">{h_sc} - {a_sc}</span><span class="fxt-status-badge">FT</span></div>'
            elif fx.get("started"):
                h_sc = fx.get("team_h_score", 0)
                a_sc = fx.get("team_a_score", 0)
                mid_html = f'<div class="fxt-mid-score"><span class="fxt-score-num fxt-score-live">{h_sc} - {a_sc}</span><span class="fxt-status-badge fxt-badge-live">LIVE</span></div>'
            else:
                mid_html = f'<div class="fxt-mid-time">{fx["_time_label"]}</div>'

            row = f"""
            <div class="fxt-match-row">
                <div class="fxt-team fxt-home">
                    <span class="fxt-team-name">{h_team}</span>
                    <span class="badge-fdr fdr-{h_diff}">{h_diff}</span>
                    <div class="fxt-jersey">{h_jersey}</div>
                </div>
                <div class="fxt-mid">
                    {mid_html}
                </div>
                <div class="fxt-team fxt-away">
                    <div class="fxt-jersey">{a_jersey}</div>
                    <span class="badge-fdr fdr-{a_diff}">{a_diff}</span>
                    <span class="fxt-team-name">{a_team}</span>
                </div>
            </div>
            """
            rows_html.append(row)

        date_hdr = f'<div class="fxt-date-header">{d_lbl}</div>' if d_lbl else ""
        group_blocks.append(f'{date_hdr}{"".join(rows_html)}')

    all_content = "".join(group_blocks)
    panel_html = f"""
    <div class="gw-fixtures-card">
        <div class="gw-fixtures-header">
            <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-size:15px; font-weight:800; color:var(--text-primary);">{fxt_title}</span>
            </div>
            <span class="meta-chip">{len(fxts)} {t('matches')}</span>
        </div>
        <div class="gw-fixtures-scroll">
            {all_content}
        </div>
    </div>
    """
    render_html(panel_html)

def render_player_card_html(p, is_bench=False, is_selected=False, is_transfer_selected=False, target_gw=None, custom_cap=None, custom_vc=None):
    is_c = custom_cap if custom_cap is not None else p.get("is_cap", False)
    is_v = custom_vc if custom_vc is not None else p.get("is_vc", False)

    cap_badge = '<span class="badge-c">C</span>' if is_c else ('<span class="badge-vc">VC</span>' if is_v else "")
    bench_class = "card-bench" if is_bench else ""
    sel_class = "p-card-selected" if is_selected else ("p-card-transfer-selected" if is_transfer_selected else "")

    lang = st.session_state.get("app_lang", "he")
    lbl_inj = "פצוע" if lang == "he" else "Injured"
    lbl_dbt = "בספק" if lang == "he" else "Doubt"

    if p["chance"] <= 25 or p["status"] in ["i", "s", "u"]:
        status_class = "card-danger"
        status_pill = f'<div class="prob-badge prob-red">🚑 {lbl_inj} {p["start_prob"]}%</div>'
    elif p["chance"] <= 75 or p["status"] == "d":
        status_class = "card-warning"
        status_pill = f'<div class="prob-badge prob-yellow">🩹 {lbl_dbt} {p["start_prob"]}%</div>'
    else:
        status_class = "cap-gold" if is_c else ("vc-silver" if is_v else "")
        status_pill = ""

    jersey_svg = get_jersey_svg(p["team"], is_gk=(p["pos_code"] == 1))
    club_cfg = TEAM_KIT_COLORS.get(p["team"], {"primary": "#38bdf8"})
    c_primary = club_cfg["primary"]
    top_color_bar = f'<div style="height:3px; background:{c_primary}; border-radius:12px 12px 0 0; margin:-4px -4px 2px -4px; width:calc(100% + 8px);"></div>'

    if target_gw is not None:
        gw_map = p.get("gw_fixtures_map", {})
        if target_gw in gw_map:
            fxt_str, fdr_val = gw_map[target_gw]
        else:
            fxt_str, fdr_val = "BLANK", 3
        
        fxt_mini_html = '<div class="mini-fxt-container">'
        for f_gw in range(target_gw + 1, target_gw + 3):
            if f_gw in gw_map:
                opp_str, diff_val = gw_map[f_gw]
                opp_short = opp_str.split(" ")[0][:3]
                fxt_mini_html += f'<div class="mini-fxt fdr-{diff_val}">{opp_short}</div>'
            else:
                fxt_mini_html += '<div class="mini-fxt" style="background:#334155;">-</div>'
        fxt_mini_html += '</div>'
        fixture_html = f'<div class="badge-fdr fdr-{fdr_val}"><span class="ltr-tag">{fxt_str}</span></div>{fxt_mini_html}'
    else:
        fdr_num = p["next_fdr"]
        fixture_html = f'<div class="badge-fdr fdr-{fdr_num}"><span class="ltr-tag">{p["next_match"]}</span></div>'

    xp_mult = 2 if is_c else 1
    xp_val = round(p["xp"] * xp_mult, 1)

    card_html = (
        f'<div class="p-card-fpl {status_class} {bench_class} {sel_class}">'
        f'{top_color_bar}'
        f'<div style="display:flex; justify-content:center; align-items:center; width:100%; margin:2px 0;">{jersey_svg}</div>'
        f'<div class="p-name-plate" style="background:var(--p-name-plate-bg) !important; border:1px solid var(--p-name-plate-border) !important;">{cap_badge}<span class="p-name-txt" style="color:var(--p-name-plate-text) !important; font-size:12.5px !important; font-weight:800 !important; text-align:center !important;">{p["name"]}</span></div>'
        f'<div style="display:flex; flex-direction:column; align-items:center; justify-content:center; width:100%; margin:2px 0;">{fixture_html}</div>'
        f'{status_pill}'
        f'<div class="p-card-footer">'
        f'<span class="p-card-cost"><span class="ltr-tag">£{p["cost"]}m</span></span>'
        f'<span class="p-card-xp"><span class="ltr-tag">xP {xp_val}</span></span>'
        f'</div>'
        f'</div>'
    )
    return "".join(line.strip() for line in card_html.splitlines())

# =====================================================================
# 9. שמונת הטאבים המרכזיים
# =====================================================================
t_squad, t_transfers, t_analysis, t_scout, t_scenarios, t_planner, t_leagues, t_tips = st.tabs([
    t("tab_squad"),
    t("tab_transfers"),
    t("tab_analysis"),
    t("tab_scout"),
    t("tab_scenarios"),
    t("tab_planner"),
    t("tab_leagues"),
    t("tab_tips"),
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
            st.error(err_msg)
            return
        p_o = next((x for x in st.session_state.user_squad if x["element"] == p_out_id), None)
        p_i = next((x for x in st.session_state.user_squad if x["element"] == p_in_id), None)
        if p_o and p_i:
            p_o["position"], p_i["position"] = p_i["position"], p_o["position"]
            if p_o.get("is_captain") and p_o["position"] > 11:
                p_o["is_captain"] = False
                p_i["is_captain"] = True
            elif p_i.get("is_captain") and p_i["position"] > 11:
                p_i["is_captain"] = False
                p_o["is_captain"] = True

            if p_o.get("is_vice_captain") and p_o["position"] > 11:
                p_o["is_vice_captain"] = False
                p_i["is_vice_captain"] = True
            elif p_i.get("is_vice_captain") and p_i["position"] > 11:
                p_i["is_vice_captain"] = False
                p_o["is_vice_captain"] = True

            st.session_state.squad_selected_id = None
            st.session_state.squad_swap_active = False
            st.toast(f"{all_players[p_out_id]['name']} ⇄ {all_players[p_in_id]['name']}")
            st.rerun()

    def set_squad_captain(target_id):
        for sp in st.session_state.user_squad:
            sp["is_captain"] = (sp["element"] == target_id)
            if sp["is_captain"]:
                sp["is_vice_captain"] = False
        st.session_state.squad_selected_id = None
        st.toast(f"{all_players[target_id]['name']} (C)")
        st.rerun()

    def set_squad_vice_captain(target_id):
        for sp in st.session_state.user_squad:
            sp["is_vice_captain"] = (sp["element"] == target_id)
            if sp["is_vice_captain"]:
                sp["is_captain"] = False
        st.session_state.squad_selected_id = None
        st.toast(f"{all_players[target_id]['name']} (VC)")
        st.rerun()

    # -----------------------------------------------------------------
    # סרגל בחירת קפטן וסגן מהיר מעל המגרש
    # -----------------------------------------------------------------
    starter_dict = {p["id"]: f"{p['name']} ({p['team']}) — xP: {p['xp']}" for p in starters}
    current_cap_id = next((p["id"] for p in starters if p.get("is_cap")), starters[0]["id"] if starters else None)
    current_vc_id = next((p["id"] for p in starters if p.get("is_vc")), starters[1]["id"] if len(starters) > 1 else None)

    with st.container():
        c_cap_col, c_vc_col = st.columns(2)
        with c_cap_col:
            new_cap_pick = st.selectbox(
                t("cap_select_label"),
                list(starter_dict.keys()),
                index=list(starter_dict.keys()).index(current_cap_id) if current_cap_id in starter_dict else 0,
                format_func=lambda x: starter_dict[x],
                key="tab1_cap_select",
            )
            if new_cap_pick != current_cap_id:
                set_squad_captain(new_cap_pick)
        with c_vc_col:
            vc_candidates = {k: v for k, v in starter_dict.items() if k != current_cap_id}
            new_vc_pick = st.selectbox(
                t("vc_select_label"),
                list(vc_candidates.keys()),
                index=list(vc_candidates.keys()).index(current_vc_id) if current_vc_id in vc_candidates else 0,
                format_func=lambda x: vc_candidates[x],
                key="tab1_vc_select",
            )
            if new_vc_pick != current_vc_id:
                set_squad_vice_captain(new_vc_pick)

    # באנר מצב חילוף פעיל
    if st.session_state.squad_swap_active and st.session_state.squad_selected_id:
        p_sw_from = all_players.get(st.session_state.squad_selected_id)
        if p_sw_from:
            is_from_starter = any(p["id"] == p_sw_from["id"] for p in starters)
            target_area_text = t("from_the_bench") if is_from_starter else t("from_the_xi")
            p_pos_txt = get_player_pos(p_sw_from)
            c_sw_info, c_sw_canc = st.columns([4, 1])
            with c_sw_info:
                st.info(f"**{t('swap_banner_title')}** {p_sw_from['name']} ({p_sw_from['team']} | {p_pos_txt}) — **{t('swap_active_hint_prefix')} {target_area_text} {t('swap_active_hint_suffix')}**")
            with c_sw_canc:
                if st.button(t("cancel_swap"), key="sq_cancel_swap_top", use_container_width=True, type="primary"):
                    st.session_state.squad_swap_active = False
                    st.session_state.squad_selected_id = None
                    st.rerun()

    def render_clean_squad_row(player_list, is_bench=False):
        if not player_list:
            return
        cols = st.columns(len(player_list))

        for i, p in enumerate(player_list):
            with cols[i]:
                is_this_selected = (st.session_state.squad_selected_id == p["id"])
                st.markdown(render_player_card_html(p, is_bench=is_bench, is_selected=is_this_selected), unsafe_allow_html=True)
                
                if st.session_state.squad_swap_active:
                    if is_this_selected:
                        if st.button(t("btn_cancel"), key=f"sq_b_{p['id']}", use_container_width=True, type="secondary"):
                            st.session_state.squad_swap_active = False
                            st.session_state.squad_selected_id = None
                            st.rerun()
                    else:
                        legal, reason = is_swap_legal(st.session_state.squad_selected_id, p["id"], st.session_state.user_squad)
                        if legal:
                            if st.button(t("btn_swap_here"), key=f"sq_b_{p['id']}", use_container_width=True, type="primary"):
                                execute_squad_swap(st.session_state.squad_selected_id, p["id"])
                        else:
                            st.button(reason, key=f"sq_b_{p['id']}", use_container_width=True, disabled=True)
                else:
                    if st.button(t("btn_sub_single"), key=f"sq_b_{p['id']}", use_container_width=True):
                        st.session_state.squad_selected_id = p["id"]
                        st.session_state.squad_swap_active = True
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

    # חלון העברות שוק במגרש (נפתח לפי דרישה)
    with st.expander(t("transfer_market_expander")):
        all_cur_squad = starters + bench
        p_tr_options = {p["id"]: f"{p['name']} ({get_player_pos(p)} | £{p['cost']}m | {p['team']})" for p in all_cur_squad}
        sel_tr_out_id = st.selectbox(t("selling_player"), list(p_tr_options.keys()), format_func=lambda x: p_tr_options[x], key="sq_tr_expander_sel")
        p_tr_out = all_players[sel_tr_out_id]
        max_budget = round(p_tr_out["cost"] + st.session_state.user_bank, 1)
        cur_pids = [x["element"] for x in st.session_state.user_squad]
        pos_name = get_player_pos(p_tr_out)
        st.caption(f"{t('selling_player')} **{p_tr_out['name']}** ({pos_name} - £{p_tr_out['cost']}m) | {t('max_budget')} **£{max_budget:.1f}m** | {t('in_bank')}: **£{st.session_state.user_bank:.1f}m**")

        tr_search_q = st.text_input(t("search_placeholder"), key="sq_tr_search_inp").strip().lower()
        t1_rem_teams = {}
        for sp in st.session_state.user_squad:
            if sp["element"] != sel_tr_out_id:
                p_item = all_players.get(sp["element"])
                if p_item:
                    t_code = p_item["team"]
                    t1_rem_teams[t_code] = t1_rem_teams.get(t_code, 0) + 1

        cands = [
            p for p in all_players.values()
            if p["pos_code"] == p_tr_out["pos_code"]
            and p["id"] not in cur_pids
            and p["cost"] <= max_budget
            and p["status"] == "a"
            and t1_rem_teams.get(p["team"], 0) < 3
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
                            <span class="ltr-tag" style="color:var(--accent-cyan);">£{r_p['cost']:.1f}m | xP: {r_p['xp']}</span>
                            <div style="font-size:10px; color:var(--text-secondary); margin:4px 0;">{get_player_reason(r_p)}</div>
                            <div class="badge-fdr fdr-{r_p['next_fdr']}"><span class="ltr-tag">{r_p['next_match']}</span></div>
                        </div>
                        """
                    )
                    if st.button(f"{t('buy_player_btn')} {r_p['name']}", key=f"buy_rec_t1_{r_p['id']}", use_container_width=True):
                        for sp in st.session_state.user_squad:
                            if sp["element"] == p_tr_out["id"]:
                                sp["element"] = r_p["id"]
                                break
                        st.session_state.user_bank = round(st.session_state.user_bank + p_tr_out["cost"] - r_p["cost"], 1)
                        st.session_state.transfers_log.append(f"{p_tr_out['name']} -> {r_p['name']}")
                        st.toast(f"{p_tr_out['name']} -> {r_p['name']}")
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
                    st.session_state.transfers_log.append(f"{p_tr_out['name']} -> {chosen_p['name']}")
                    st.toast(f"{p_tr_out['name']} -> {chosen_p['name']}")
                    st.rerun()

    # ספסל מואר ומובלט בעיצוב Dugout
    st.write("")
    with st.container():
        st.markdown(
            f"""
            <div class="bench-anchor"></div>
            <div class="bench-dugout-badge">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-weight:800; font-size:14px; color:var(--accent-mint);">{t('bench_title')}</span>
                </div>
                <span style="font-size:11px; color:var(--accent-mint); background:var(--badge-mint-bg); padding:2px 10px; border-radius:6px; font-weight:700; border:1px solid var(--badge-mint-border);">{t('bench_sub_order')}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_clean_squad_row(bench, is_bench=True)

# ---------------------------------------------------------------------
# טאב 2: מעבדת חילופים (Transfers Lab)
# ---------------------------------------------------------------------
with t_transfers:
    st.subheader(t("t2_title"))
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
        pos_str = get_player_pos(p)
        flag = "🚑 " if (p["status"] != "a" or p["chance"] < 100) else ("⚠️ " if mark_priority(p) else "")
        return f"{flag}{p['name']} ({pos_str} - {p['team']}) | £{p['cost']}m | xP: {p['xp']}"

    col_out, col_in = st.columns(2)
    with col_out:
        st.markdown(f"#### {t('t2_out_header')}")
        sel_out_id = st.selectbox(
            t("t2_out_label"),
            [p["id"] for p in sorted_squad],
            format_func=format_transfer_out,
        )
        p_out = all_players[sel_out_id]
        budget_cap = round(p_out["cost"] + st.session_state.user_bank, 1)

    with col_in:
        in_pos_str = t(f"pos_{p_out['pos_code']}")
        st.markdown(f"#### {t('t2_in_header')} {in_pos_str} (IN)")
        search_str = (
            st.text_input(
                t("t2_quick_search"),
                placeholder=t("t2_search_placeholder"),
            )
            .strip()
            .lower()
        )

        t2_rem_teams = {}
        for sp in current_all:
            if sp["id"] != sel_out_id:
                t2_rem_teams[sp["team"]] = t2_rem_teams.get(sp["team"], 0) + 1

        eligible = [
            p
            for p in all_players.values()
            if p["pos_code"] == p_out["pos_code"]
            and p["id"] not in current_pids
            and p["status"] == "a"
            and p["cost"] <= budget_cap
            and t2_rem_teams.get(p["team"], 0) < 3
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
            rec = "[Top] " if pid in ranked_recs else ""
            return f"{rec}{p['name']} ({p['team']}) | £{p['cost']}m | xP: {p['xp']}"

        if pool:
            sel_in_id = st.selectbox(
                t("t2_in_label"),
                [p["id"] for p in pool],
                format_func=format_transfer_in,
            )
            p_in = all_players[sel_in_id]
        else:
            st.warning(t("t2_no_players_budget"))
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
                    <b style="color:var(--text-primary); font-size:14px;">{t('h2h_comp')}</b>
                    <span style="color:#10b981; font-weight:800; font-size:13.5px;">{t('expected_add')} {delta:+} xP</span>
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px; font-size:12.5px;">
                    <div class="comparison-panel-out">
                        <div style="color:var(--accent-pink); font-weight:800; margin-bottom:4px;">{t('out_label')} {p_out['name']} <span class="ltr-tag">({p_out['team']})</span></div>
                        <div style="color:var(--text-primary); font-size:12px;">{t('season_pts_lbl')} <b>{p_out['total_points']}</b> | xP: <b style="color:#ef4444;">{p_out['xp']}</b></div>
                        <div style="color:var(--text-secondary); font-size:11px; margin-top:2px;">{t('next_match_lbl')} <span class="ltr-tag">{p_out['next_match']}</span></div>
                    </div>
                    <div class="comparison-panel-in">
                        <div style="color:var(--accent-mint); font-weight:800; margin-bottom:4px;">{t('in_label')} {p_in['name']} <span class="ltr-tag">({p_in['team']})</span></div>
                        <div style="color:var(--text-primary); font-size:12px;">{t('season_pts_lbl')} <b>{p_in['total_points']}</b> | xP: <b style="color:#10b981;">{p_in['xp']}</b></div>
                        <div style="color:var(--text-secondary); font-size:11px; margin-top:2px;">{t('next_match_lbl')} <span class="ltr-tag">{p_in['next_match']}</span></div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        b_act1, b_act2 = st.columns([1, 2])
        with b_act1:
            if st.button(t("t2_confirm_btn"), use_container_width=True):
                for p in st.session_state.user_squad:
                    if p["element"] == p_out["id"]:
                        p["element"] = p_in["id"]
                        break
                st.session_state.user_bank = new_bank
                st.session_state.transfers_log.append(f"{p_out['name']} -> {p_in['name']}")
                st.rerun()

    if st.session_state.transfers_log:
        st.caption(
            f"{t('t2_saved_transfers')} {', '.join(st.session_state.transfers_log)}"
        )
        if st.button(t("t2_reset_btn")):
            st.session_state.user_squad = [dict(p) for p in raw_picks]
            st.session_state.user_bank = initial_bank
            st.session_state.transfers_log = []
            st.rerun()

# ---------------------------------------------------------------------
# טאב 3: ניתוח וחסרונות (Analysis & Flaws)
# ---------------------------------------------------------------------
with t_analysis:
    st.subheader(t("t3_title"))
    c_flaw1, c_flaw2 = st.columns([1, 2])
    with c_flaw1:
        st.markdown(
            f"""
            <div class="accessible-card" style="text-align:center;">
                <div style="font-size:13px; color:var(--text-secondary);">{t('t3_squad_score')}</div>
                <div style="font-size:38px; font-weight:800; color:{rating_color}; margin:6px 0;">
                    {squad_rating} <span style="font-size:16px; color:var(--text-muted);">/ 100</span>
                </div>
                <div style="font-size:12px; color:var(--text-primary);">{t('t3_forecast')} <b>{starting_xp_total:.1f}</b> {t('pts')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_flaw2:
        st.markdown(f"<b>{t('t3_flaws_title')}</b>", unsafe_allow_html=True)
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
            st.success(t("t3_no_flaws"))

    st.write("")
    with st.expander(f"💡 {t('tips_main_title')} — {t('tips_main_subtitle')}", expanded=False):
        c_cmd1, c_cmd2 = st.columns(2)
        half = len(FPL_SUCCESS_TIPS) // 2
        with c_cmd1:
            for item in FPL_SUCCESS_TIPS[:half]:
                c_title = item["title_en"] if is_en else item["title_he"]
                c_desc = item["desc_en"] if is_en else item["desc_he"]
                c_tag = item["tag_en"] if is_en else item["tag_he"]
                c_icon = item.get("icon", "💡")
                st.markdown(
                    f"""
                    <div class="accessible-card" style="margin-bottom:10px; padding:12px;">
                        <div class="split-box">
                            <div style="display:flex; align-items:center; gap:8px;">
                                <span style="background:var(--badge-mint-bg); color:var(--accent-mint); border:1px solid var(--badge-mint-border); font-weight:900; font-size:12px; width:22px; height:22px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center;">{item['num']}</span>
                                <b style="color:var(--text-primary); font-size:13.5px;">{c_icon} {c_title}</b>
                            </div>
                            <span class="meta-chip" style="color:var(--accent-cyan);">{c_tag}</span>
                        </div>
                        <div style="font-size:12.5px; color:var(--text-secondary); margin-top:6px; line-height:1.6;">
                            {c_desc}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        with c_cmd2:
            for item in FPL_SUCCESS_TIPS[half:]:
                c_title = item["title_en"] if is_en else item["title_he"]
                c_desc = item["desc_en"] if is_en else item["desc_he"]
                c_tag = item["tag_en"] if is_en else item["tag_he"]
                c_icon = item.get("icon", "💡")
                st.markdown(
                    f"""
                    <div class="accessible-card" style="margin-bottom:10px; padding:12px;">
                        <div class="split-box">
                            <div style="display:flex; align-items:center; gap:8px;">
                                <span style="background:var(--badge-mint-bg); color:var(--accent-mint); border:1px solid var(--badge-mint-border); font-weight:900; font-size:12px; width:22px; height:22px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center;">{item['num']}</span>
                                <b style="color:var(--text-primary); font-size:13.5px;">{c_icon} {c_title}</b>
                            </div>
                            <span class="meta-chip" style="color:var(--accent-cyan);">{c_tag}</span>
                        </div>
                        <div style="font-size:12.5px; color:var(--text-secondary); margin-top:6px; line-height:1.6;">
                            {c_desc}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.write("")
    st.markdown(f"#### {t('starting_11_title')}")
    headers_s11 = [
        t("th_player"),
        t("th_pos"),
        t("th_team"),
        t("th_next_match"),
        t("th_fdr"),
        t("th_start_prob"),
        t("th_season_pts"),
        t("th_xp"),
    ]
    sorted_starters = sorted(starters, key=lambda x: round(x["xp"] * (2 if x.get("is_cap") else 1), 1), reverse=True)
    rows_s11 = []
    for p in sorted_starters:
        if p.get("is_cap"):
            role_badge = '<span class="badge-c" style="margin-right:4px;">C</span>'
        elif p.get("is_vc"):
            role_badge = '<span class="badge-vc" style="margin-right:4px;">VC</span>'
        else:
            role_badge = ""

        if p["chance"] <= 25 or p["status"] in ["i", "s", "u"]:
            health_icon = '<span style="color:#ef4444; font-weight:700;">🚑 </span>'
        elif p["chance"] <= 75 or p["status"] == "d":
            health_icon = '<span style="color:#f59e0b; font-weight:700;">🩹 </span>'
        else:
            health_icon = ""

        pos_str = t(f"pos_{p['pos_code']}")
        prob_color = "#10b981" if p["start_prob"] == 100 else "#f59e0b"
        xp_calc = round(p["xp"] * (2 if p.get("is_cap") else 1), 1)

        rows_s11.append([
            f"{health_icon}{role_badge}<b>{p['name']}</b>",
            f'<span style="font-weight:700; font-size:12px;">{pos_str}</span>',
            f'<span class="ltr-tag" style="font-weight:700;">{p["team"]}</span>',
            f'<span class="badge-fdr fdr-{p["next_fdr"]}"><span class="ltr-tag">{p["next_match"]}</span></span>',
            f'<span class="ltr-tag" style="font-weight:800;">{p["next_fdr"]}</span>',
            f'<span style="color:{prob_color}; font-weight:700;">{p["start_prob"]}%</span>',
            f'<span class="ltr-tag" style="font-weight:700;">{p["total_points"]}</span>',
            f'<span class="ltr-tag" style="color:var(--accent-mint); font-weight:800; font-size:13.5px;">{xp_calc}</span>',
        ])
    
    render_styled_table(headers_s11, rows_s11, is_rtl=(st.session_state.app_lang == "he"))

# ---------------------------------------------------------------------
# טאב 4: רדאר רכש עילית (Scout Radar)
# ---------------------------------------------------------------------
with t_scout:
    st.subheader(f"{t('t4_title')} {next_gw}")
    st_fwd, st_mid, st_def, st_gk, st_cap = st.tabs(
        [t("t4_tab_fwd"), t("t4_tab_mid"), t("t4_tab_def"), t("t4_tab_gk"), t("t4_tab_cap")]
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
                f'<span class="meta-chip" style="color:#6ee7b7;">{t("t4_buy_low")}</span>'
                if p["tag"] == "BUY_LOW"
                else (
                    f'<span class="meta-chip" style="color:#fca5a5;">{t("t4_overperforming")}</span>'
                    if p["tag"] == "OVERPERFORMING_TRAP"
                    else ""
                )
            )
            st.markdown(
                f"""
                <div class="accessible-card">
                    <div class="split-box">
                        <div>
                            <b>{p['name']}</b> <span class="ltr-tag" style="color:var(--text-secondary);">({p['team']})</span> {tag}
                        </div>
                        <span class="ltr-tag" style="color:var(--accent-cyan);">£{p['cost']}m | xP: {p['xp']}</span>
                    </div>
                    <div style="font-size:12px; color:var(--text-secondary); margin-bottom:6px;">{get_player_reason(p)}</div>
                    <div style="font-size:11px; color:var(--text-muted);">
                        {t('next_match_lbl')} <span class="badge-fdr fdr-{p['next_fdr']}"><span class="ltr-tag">{p['next_match']}</span></span> |
                        {t('t4_start_prob')} <b>{p['start_prob']}%</b> | {t('t4_tot_pts')} <b>{p['total_points']}</b>
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
                <div class="accessible-card" style="border: 1px solid var(--border-color); border-inline-start: 4px solid #10b981; background: var(--bg-card);">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span class="meta-chip" style="color:#10b981; background:rgba(16, 185, 129, 0.12); border-color:rgba(16, 185, 129, 0.3);">{t('t4_cap_shield')}</span>
                        <span class="ltr-tag" style="color:var(--accent-cyan); font-weight:800; font-size:13px;">xP: {c_shield['xp']}</span>
                    </div>
                    <h4 style="margin:4px 0 8px 0; color:var(--text-primary);">{c_shield['name']} <span class="ltr-tag" style="color:var(--text-secondary); font-size:13px;">({c_shield['team']})</span></h4>
                    <div style="font-size:12px; color:var(--text-secondary); line-height:1.6;">
                        {t('t4_ownership')} <span class="ltr-tag"><b>{c_shield['selected_by']}%</b></span> | {t('t4_start_prob')} <b>{c_shield['start_prob']}%</b><br>
                        {t('next_match_lbl')} <span class="ltr-tag"><b>{c_shield['next_match']}</b></span><br>
                        <div style="margin-top:6px; font-size:11.5px; color:var(--text-muted);">{get_player_reason(c_shield)}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_s2:
            st.markdown(
                f"""
                <div class="accessible-card" style="border: 1px solid var(--border-color); border-inline-start: 4px solid #f59e0b; background: var(--bg-card);">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span class="meta-chip" style="color:#d97706; background:rgba(245, 158, 11, 0.12); border-color:rgba(245, 158, 11, 0.3);">{t('t4_cap_sword')}</span>
                        <span class="ltr-tag" style="color:var(--accent-cyan); font-weight:800; font-size:13px;">xP: {c_sword['xp']}</span>
                    </div>
                    <h4 style="margin:4px 0 8px 0; color:var(--text-primary);">{c_sword['name']} <span class="ltr-tag" style="color:var(--text-secondary); font-size:13px;">({c_sword['team']})</span></h4>
                    <div style="font-size:12px; color:var(--text-secondary); line-height:1.6;">
                        {t('t4_ownership')} <span class="ltr-tag"><b>{c_sword['selected_by']}% {t('t4_only')}</b></span> | {t('t4_start_prob')} <b>{c_sword['start_prob']}%</b><br>
                        {t('next_match_lbl')} <span class="ltr-tag"><b>{c_sword['next_match']}</b></span><br>
                        <div style="margin-top:6px; font-size:11.5px; color:var(--text-muted);">{get_player_reason(c_sword)}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ---------------------------------------------------------------------
# טאב 5: 3 תרחישי תקציב (3 Budget Scenarios)
# ---------------------------------------------------------------------
with t_scenarios:
    st.subheader(t("t5_title"))
    my_full_squad = starters + bench
    my_ids_set = {x["id"] for x in my_full_squad}

    def get_optimal_in(pos_code, budget_limit, p_out_id=None):
        sc_rem_teams = {}
        for sp in my_full_squad:
            if sp["id"] != p_out_id:
                sc_rem_teams[sp["team"]] = sc_rem_teams.get(sp["team"], 0) + 1
        cands = [
            p
            for p in all_players.values()
            if p["id"] not in my_ids_set
            and p["pos_code"] == pos_code
            and p["cost"] <= budget_limit
            and p["status"] == "a"
            and sc_rem_teams.get(p["team"], 0) < 3
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
            "title": t("t5_op1_title"),
            "tag": t("t5_op1_tag"),
            "out": cand_def,
            "in": get_optimal_in(
                2, cand_def["cost"] + st.session_state.user_bank, cand_def["id"]
            ),
        },
        {
            "title": t("t5_op2_title"),
            "tag": t("t5_op2_tag"),
            "out": cand_mid,
            "in": get_optimal_in(
                3, cand_mid["cost"] + st.session_state.user_bank, cand_mid["id"]
            ),
        },
        {
            "title": t("t5_op3_title"),
            "tag": t("t5_op3_tag"),
            "out": cand_fwd,
            "in": get_optimal_in(
                4, cand_fwd["cost"] + st.session_state.user_bank, cand_fwd["id"]
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
                    <b style="color:var(--text-primary); font-size:14px;">{item['title']}</b>
                    <span style="color:#10b981; font-weight:800; font-size:13.5px;">{t('t5_diff_xp')} +{diff_xp} xP</span>
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px; font-size:12.5px;">
                    <div class="comparison-panel-out">
                        <div style="color:var(--accent-pink); font-weight:800; margin-bottom:4px;">{t('out_label')} <b>{p_o['name']}</b> <span class="ltr-tag">({p_o['team']})</span></div>
                        <div style="color:var(--text-primary); font-size:12px;">{t('season_pts_lbl')} <b>{p_o['total_points']}</b> | xP: <b style="color:#ef4444;">{p_o['xp']}</b></div>
                    </div>
                    <div class="comparison-panel-in">
                        <div style="color:var(--accent-mint); font-weight:800; margin-bottom:4px;">{t('in_label')} <b>{p_i['name']}</b> <span class="ltr-tag">({p_i['team']})</span></div>
                        <div style="color:var(--text-primary); font-size:12px;">{t('left_in_bank')} <span class="ltr-tag"><b>£{rem}m</b></span> | xP: <b style="color:#10b981;">{p_i['xp']}</b></div>
                    </div>
                </div>
                <div style="font-size:11.5px; color:var(--text-muted); margin-top:8px; line-height:1.4;">{get_player_reason(p_i)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------
# טאב 6: מתכנן מחזורים משורשר (Planner) - אייקונים, שוק, ייצוא ושמירה
# ---------------------------------------------------------------------
with t_planner:
    st.subheader(t("t6_title"))
    st.caption(t("t6_caption"))

    col_setup1, col_setup2, col_setup3 = st.columns([1, 1, 1])
    with col_setup1:
        st.session_state.planner_starting_fts = st.number_input(
            f"{t('t6_init_fts')} (GW {next_gw}):",
            min_value=1,
            max_value=5,
            value=st.session_state.planner_starting_fts,
            step=1,
        )
    with col_setup2:
        h_opts = ["5", "8", "all"]
        h_labels = {
            "5": t("t6_horizon_5"),
            "8": t("t6_horizon_8"),
            "all": t("t6_horizon_all"),
        }
        horizon_choice = st.selectbox(
            t("t6_horizon_label"),
            h_opts,
            format_func=lambda x: h_labels[x],
            index=0,
        )
        if horizon_choice == "5":
            max_sim_gw = min(38, next_gw + 4)
        elif horizon_choice == "8":
            max_sim_gw = min(38, next_gw + 7)
        else:
            max_sim_gw = 38

    with col_setup3:
        st.write("")
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            if st.button(t("t6_reset_plan"), use_container_width=True):
                st.session_state.planner_plan = {
                    g: {"chip": "no_chip", "transfers": []}
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
                t("t6_export_plan"),
                data=json.dumps(plan_export_data, indent=2, ensure_ascii=False),
                file_name=f"fpl_plan_team_{team_id}.json",
                mime="application/json",
                use_container_width=True,
            )

    # וידוא שכל המחזורים בטווח קיימים בתוכנית
    for g in range(next_gw, max_sim_gw + 1):
        if g not in st.session_state.planner_plan:
            st.session_state.planner_plan[g] = {"chip": "no_chip", "transfers": []}

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
            if not p_data:
                p_data = {
                    "id": pid,
                    "name": f"Player {pid}",
                    "team": "FPL",
                    "pos_code": 2,
                    "cost": 4.0,
                    "xp": 0.0,
                    "status": "u",
                    "chance": 0,
                    "start_prob": 0,
                    "next_match": "-",
                    "next_fdr": 3,
                    "total_points": 0,
                    "tag": "",
                    "form": 0.0,
                }
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
    curr_lbl = "Current" if st.session_state.app_lang == "en" else "נוכחי"
    fut_lbl = "Future" if st.session_state.app_lang == "en" else "עתידי"
    selected_gw = st.radio(
        t("t6_select_gw"),
        gw_options,
        format_func=lambda x: f"GW {x} ({curr_lbl if x == next_gw else fut_lbl})",
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
        chip_keys = ["no_chip", "Wildcard", "Free Hit", "Bench Boost", "Triple Captain"]
        chip_map = {
            "no_chip": t("no_chip"),
            "Wildcard": "Wildcard",
            "Free Hit": "Free Hit",
            "Bench Boost": "Bench Boost",
            "Triple Captain": "Triple Captain",
        }
        norm_chip = "no_chip" if current_chip_val in ["ללא צ'יפ", "No Chip", "no_chip"] else current_chip_val
        chosen_chip_key = st.selectbox(
            f"{t('chip_for_gw')} {selected_gw}:",
            chip_keys,
            index=chip_keys.index(norm_chip) if norm_chip in chip_keys else 0,
            format_func=lambda x: chip_map[x],
            key=f"chip_select_{selected_gw}",
        )
        new_chip_val = "no_chip" if chosen_chip_key == "no_chip" else chosen_chip_key
        if new_chip_val != current_chip_val:
            st.session_state.planner_plan[selected_gw]["chip"] = new_chip_val
            st.rerun()

    with c_cp2:
        if st.session_state.planner_plan[selected_gw]["transfers"]:
            st.markdown(f"**{t('planned_transfers_gw')} {selected_gw}:**")
            for tr_idx, (o_id, i_id) in enumerate(list(st.session_state.planner_plan[selected_gw]["transfers"])):
                c_tr_t, c_tr_b = st.columns([3.5, 1.5])
                with c_tr_t:
                    st.caption(f"{all_players[o_id]['name']} -> {all_players[i_id]['name']}")
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
            st.success(t("rb_rebuilt_success"))
            if st.button(t("t6_reset_rebuild"), key=f"clr_rebuild_{selected_gw}"):
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
            st.error(f"{err_msg}")
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

            # אם שחקן שקיבל סרט קפטן/סגן במחזור זה יורד לספסל, הסרט עובר למחליף
            if selected_gw not in st.session_state.planner_captains:
                st.session_state.planner_captains[selected_gw] = {}
            cur_cap = st.session_state.planner_captains[selected_gw].get("cap")
            cur_vc = st.session_state.planner_captains[selected_gw].get("vc")

            if p_o["position"] > 11:
                if cur_cap == p_out_id:
                    st.session_state.planner_captains[selected_gw]["cap"] = p_in_id
                if cur_vc == p_out_id:
                    st.session_state.planner_captains[selected_gw]["vc"] = p_in_id
            elif p_i["position"] > 11:
                if cur_cap == p_in_id:
                    st.session_state.planner_captains[selected_gw]["cap"] = p_out_id
                if cur_vc == p_in_id:
                    st.session_state.planner_captains[selected_gw]["vc"] = p_out_id

            if selected_gw == next_gw:
                orig_o = next((x for x in st.session_state.user_squad if x["element"] == p_out_id), None)
                orig_i = next((x for x in st.session_state.user_squad if x["element"] == p_in_id), None)
                if orig_o and orig_i:
                    orig_o["position"], orig_i["position"] = orig_i["position"], orig_o["position"]
                    if orig_o.get("is_captain") and orig_o["position"] > 11:
                        orig_o["is_captain"] = False
                        orig_i["is_captain"] = True
                    elif orig_i.get("is_captain") and orig_i["position"] > 11:
                        orig_i["is_captain"] = False
                        orig_o["is_captain"] = True

                    if orig_o.get("is_vice_captain") and orig_o["position"] > 11:
                        orig_o["is_vice_captain"] = False
                        orig_i["is_vice_captain"] = True
                    elif orig_i.get("is_vice_captain") and orig_i["position"] > 11:
                        orig_i["is_vice_captain"] = False
                        orig_o["is_vice_captain"] = True

            st.session_state.planner_selected_id = None
            st.session_state.planner_swap_active = False
            st.toast(f"{all_players[p_out_id]['name']} ⇄ {all_players[p_in_id]['name']}")
            st.rerun()

    def set_planner_captain(target_id):
        if selected_gw not in st.session_state.planner_captains:
            st.session_state.planner_captains[selected_gw] = {}
        st.session_state.planner_captains[selected_gw]["cap"] = target_id
        st.session_state.planner_selected_id = None
        st.toast(f"{all_players[target_id]['name']} (C) GW {selected_gw}")
        st.rerun()

    def set_planner_vice_captain(target_id):
        if selected_gw not in st.session_state.planner_captains:
            st.session_state.planner_captains[selected_gw] = {}
        st.session_state.planner_captains[selected_gw]["vc"] = target_id
        st.session_state.planner_selected_id = None
        st.toast(f"{all_players[target_id]['name']} (VC) GW {selected_gw}")
        st.rerun()

    # רינדור מגרש פלנר נקי וממורכז
    def render_clean_planner_row(player_list, is_bench=False):
        if not player_list:
            return
        cols = st.columns(len(player_list))

        for i, p in enumerate(player_list):
            with cols[i]:
                is_this_selected = (st.session_state.planner_selected_id == p["id"])
                is_tr_selected = (st.session_state.planner_transfer_out == p["id"])
                st.markdown(render_player_card_html(p, is_bench=is_bench, is_selected=is_this_selected, is_transfer_selected=is_tr_selected, target_gw=selected_gw), unsafe_allow_html=True)
                
                if st.session_state.planner_swap_active:
                    if is_this_selected:
                        if st.button(f"✕ {t('btn_cancel')}", key=f"pl_b_{p['id']}_{selected_gw}", use_container_width=True, type="secondary"):
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
                    if st.button(f"⇄ {t('btn_sub_single')}", key=f"pl_b_{p['id']}_{selected_gw}", use_container_width=True):
                        st.session_state.planner_selected_id = p["id"]
                        st.session_state.planner_swap_active = True
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
                        <span style="font-size:16px; font-weight:800; color:var(--accent-cyan);">{t('rebuild_title')} — Gameweek {selected_gw}</span>
                        <div style="font-size:12px; color:var(--text-secondary);">{t('rebuild_subtitle')}</div>
                    </div>
                    <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
                        <div style="text-align:center; background:var(--bg-main); border:1px solid var(--border-color); padding:5px 10px; border-radius:8px;">
                            <div style="font-size:10px; color:var(--text-secondary);">{t('total_squad_val')}</div>
                            <div style="font-size:14px; font-weight:700; color:var(--text-primary);"><span class="ltr-tag">£{total_budget:.1f}m</span></div>
                        </div>
                        <div style="text-align:center; background:var(--bg-main); border:1px solid {budget_color}; padding:5px 10px; border-radius:8px;">
                            <div style="font-size:10px; color:var(--text-secondary);">{t('rem_budget')}</div>
                            <div style="font-size:16px; font-weight:800; color:{budget_color};"><span class="ltr-tag">£{rem_budget:.1f}m</span></div>
                        </div>
                        <div style="text-align:center; background:var(--bg-main); border:1px solid var(--border-color); padding:5px 10px; border-radius:8px;">
                            <div style="font-size:10px; color:var(--text-secondary);">{t('players_picked')}</div>
                            <div style="font-size:14px; font-weight:700; color:var(--accent-cyan);">{num_picks} / 15</div>
                        </div>
                        <div style="text-align:center; background:var(--bg-main); border:1px solid var(--border-color); padding:5px 10px; border-radius:8px;">
                            <div style="font-size:10px; color:var(--text-secondary);">{t('avg_per_player')}</div>
                            <div style="font-size:14px; font-weight:700; color:var(--text-primary);"><span class="ltr-tag">£{avg_budget:.1f}m</span></div>
                        </div>
                    </div>
                </div>
            </div>
            """
        )

        if over_limit_teams:
            st.error(f"{t('rb_err_limit')} {', '.join(over_limit_teams)}")
        if rem_budget < 0:
            st.error(t("rb_err_budget").replace("{val}", f"{abs(rem_budget):.1f}"))

        c_rb_act1, c_rb_act2, c_rb_act3, c_rb_act4 = st.columns([1, 1.2, 1.4, 1])
        with c_rb_act1:
            if st.button(t("clear_15_btn"), key="rb_clear_all", use_container_width=True):
                st.session_state.planner_rebuild_picks = []
                st.session_state.planner_rebuild_target_pos = None
                st.rerun()
        with c_rb_act2:
            if st.button(t("load_existing_btn"), key="rb_load_existing", use_container_width=True):
                st.session_state.planner_rebuild_picks = [p["element"] for p in cur_gw_sim["squad_snapshot"]]
                st.session_state.planner_rebuild_target_pos = None
                st.rerun()
        with c_rb_act3:
            is_ready_to_save = (num_picks == 15 and rem_budget >= 0 and not over_limit_teams and pos_counts_rb[1] == 2 and pos_counts_rb[2] == 5 and pos_counts_rb[3] == 5 and pos_counts_rb[4] == 3)
            if is_ready_to_save:
                if st.button(t("save_rebuild_btn"), key="rb_save_squad", type="primary", use_container_width=True):
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

                    if st.session_state.planner_plan[selected_gw]["chip"] in ["ללא צ'יפ", "No Chip", "no_chip"]:
                        st.session_state.planner_plan[selected_gw]["chip"] = "Wildcard"

                    st.session_state.planner_rebuild_active = None
                    st.session_state.planner_rebuild_picks = []
                    st.session_state.planner_rebuild_target_pos = None
                    st.toast(f"{t('rb_saved_toast')} {selected_gw}!")
                    st.rerun()
            else:
                st.button(f"{t('save_rebuild_btn')} ({num_picks}/15)", disabled=True, use_container_width=True)
        with c_rb_act4:
            if st.button(t("close_rebuild_btn"), key="rb_cancel_btn", use_container_width=True):
                st.session_state.planner_rebuild_active = None
                st.session_state.planner_rebuild_target_pos = None
                st.rerun()

        st.write("")

        # פריסת המשבצות לפי עמדות
        pos_cfg = [
            {"code": 1, "name": t("pos_1_pl"), "singular": t("pos_1"), "req": 2},
            {"code": 2, "name": t("pos_2_pl"), "singular": t("pos_2"), "req": 5},
            {"code": 3, "name": t("pos_3_pl"), "singular": t("pos_3"), "req": 5},
            {"code": 4, "name": t("pos_4_pl"), "singular": t("pos_4"), "req": 3},
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
            cur_pids = [pid for pid in rebuild_picks if pid in all_players and all_players[pid]["pos_code"] == p_code]
            cur_cnt = len(cur_pids)

            st.markdown(f"**{sec_name} ({cur_cnt}/{req_cnt}):**")
            if req_cnt == 2:
                cols = st.columns([1.5, 2, 2, 1.5])[1:3]
            elif req_cnt == 3:
                cols = st.columns([1, 2, 2, 2, 1])[1:4]
            else:
                cols = st.columns(req_cnt)

            for slot_idx in range(req_cnt):
                with cols[slot_idx]:
                    if slot_idx < len(cur_pids):
                        pid = cur_pids[slot_idx]
                        p_data = all_players[pid]
                        st.markdown(render_player_card_html(p_data, target_gw=selected_gw), unsafe_allow_html=True)
                        if st.button(t("remove_btn"), key=f"rb_rem_{pid}_{slot_idx}", use_container_width=True):
                            remove_rebuild_player(pid)
                    else:
                        is_active_pos = (st.session_state.get("planner_rebuild_target_pos") == p_code)
                        border_color = "var(--primary-color)" if is_active_pos else "var(--border-color)"
                        bg_color = "rgba(56, 189, 248, 0.08)" if is_active_pos else "var(--bg-main)"

                        render_html(
                            f"""
                            <div style="background:{bg_color}; border:2px dashed {border_color}; border-radius:10px; width:110px; height:158px; display:flex; flex-direction:column; justify-content:center; align-items:center; margin:0 auto 3px auto; box-sizing:border-box;">
                                <div style="font-size:11px; color:var(--text-secondary); font-weight:700; margin-top:4px;">{t('empty_slot')}</div>
                            </div>
                            """
                        )
                        btn_lbl = t("rb_btn_chosen") if is_active_pos else f"{t('add_slot')} {sing_name}"
                        btn_t = "primary" if is_active_pos else "secondary"
                        if st.button(btn_lbl, key=f"rb_add_{p_code}_{slot_idx}", type=btn_t, use_container_width=True):
                            select_target_rebuild_pos(p_code)
            st.write("")

        # מגירת בחירת שחקן לעמדה
        active_pos = st.session_state.get("planner_rebuild_target_pos")
        if active_pos is not None:
            pos_dict_names = {1: t("pos_1"), 2: t("pos_2"), 3: t("pos_3"), 4: t("pos_4")}
            pos_title = pos_dict_names[active_pos]

            other_empty_slots = max(0, empty_slots - 1)
            reserved_funds = other_empty_slots * 4.0
            max_allowed_price = round(rem_budget - reserved_funds, 1)

            drawer_title_str = t("rb_picker_title").replace("{pos}", pos_title).replace("{budget}", f"{rem_budget:.1f}")
            max_price_desc_str = t("rb_picker_max_price")

            render_html(
                f"""
                <div class="transfer-drawer">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:8px;">
                        <div>
                            <span style="font-size:15px; font-weight:800; color:var(--accent-cyan);">{drawer_title_str}</span>
                            <div style="font-size:11px; color:var(--text-secondary);">{max_price_desc_str} <b style="color:#10b981;">£{max_allowed_price:.1f}m</b></div>
                        </div>
                    </div>
                </div>
                """
            )

            c_cl_btn, c_sch_inp = st.columns([1, 3])
            with c_cl_btn:
                if st.button(t("close_drawer"), key="rb_close_picker", use_container_width=True, type="primary"):
                    st.session_state.planner_rebuild_target_pos = None
                    st.rerun()
            with c_sch_inp:
                rb_search = st.text_input(t("search_placeholder"), key=f"rb_search_{selected_gw}_{active_pos}").strip().lower()

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
                st.markdown(f"##### {t('rb_recommended').replace('{pos}', pos_title)}")
                rec_cols = st.columns(len(rb_recs))
                for r_idx, r_p in enumerate(rb_recs):
                    with rec_cols[r_idx]:
                        r_jersey = get_jersey_svg(r_p["team"], is_gk=(r_p["pos_code"] == 1))
                        render_html(
                            f"""
                            <div class="accessible-card" style="text-align:center; padding:10px;">
                                {r_jersey}
                                <b>{r_p['name']}</b> ({r_p['team']})<br>
                                <span class="ltr-tag" style="color:var(--accent-cyan);">£{r_p['cost']:.1f}m | xP: {r_p['xp']}</span>
                                <div style="font-size:10px; color:var(--text-secondary); margin:4px 0;">{get_player_reason(r_p)}</div>
                                <div class="badge-fdr fdr-{r_p['next_fdr']}"><span class="ltr-tag">{r_p['next_match']}</span></div>
                            </div>
                            """
                        )
                        if st.button(f"{t('add_slot')} {r_p['name']}", key=f"rb_pick_rec_{r_p['id']}", use_container_width=True):
                            st.session_state.planner_rebuild_picks.append(r_p["id"])
                            updated_pos_count = sum(1 for pid in st.session_state.planner_rebuild_picks if all_players[pid]["pos_code"] == active_pos)
                            req_for_pos = {1: 2, 2: 5, 3: 5, 4: 3}[active_pos]
                            if updated_pos_count >= req_for_pos:
                                st.session_state.planner_rebuild_target_pos = None
                            st.rerun()

            st.write("")
            all_cands_sorted = sorted(candidates, key=lambda x: x["total_points"], reverse=True)
            if all_cands_sorted:
                cand_opts = {p["id"]: f"{p['name']} ({p['team']}) | £{p['cost']:.1f}m | {p['total_points']} {t('pts')} | xP: {p['xp']} | {t('against')} {p['next_match']}" for p in all_cands_sorted}
                c_c_sel, c_c_btn = st.columns([3, 1])
                with c_c_sel:
                    chosen_cand_id = st.selectbox(
                        t("rb_all_cands").replace("{pos}", pos_title),
                        list(cand_opts.keys()),
                        format_func=lambda x: cand_opts[x],
                        key=f"rb_pool_sel_{active_pos}",
                    )
                with c_c_btn:
                    st.write("")
                    if st.button(t("rb_add_cand"), key=f"rb_add_chosen_{active_pos}", use_container_width=True):
                        st.session_state.planner_rebuild_picks.append(chosen_cand_id)
                        updated_pos_count = sum(1 for pid in st.session_state.planner_rebuild_picks if all_players[pid]["pos_code"] == active_pos)
                        req_for_pos = {1: 2, 2: 5, 3: 5, 4: 3}[active_pos]
                        if updated_pos_count >= req_for_pos:
                            st.session_state.planner_rebuild_target_pos = None
                        st.rerun()
            else:
                st.warning(t("rb_no_cands").replace("{pos}", pos_title).replace("{budget}", f"{max_allowed_price:.1f}"))
    else:
        # בורר קפטנים מהיר למחזור הנבחר
        pl_starter_dict = {p["id"]: f"{p['name']} ({p['team']}) — xP: {p['xp']}" for p in cur_gw_sim["starters"]}
        cur_pl_cap = next((p["id"] for p in cur_gw_sim["starters"] if p.get("is_cap")), cur_gw_sim["starters"][0]["id"] if cur_gw_sim["starters"] else None)
        cur_pl_vc = next((p["id"] for p in cur_gw_sim["starters"] if p.get("is_vc")), cur_gw_sim["starters"][1]["id"] if len(cur_gw_sim["starters"]) > 1 else None)

        with st.container():
            c_pl_c1, c_pl_c2 = st.columns(2)
            with c_pl_c1:
                new_pl_c = st.selectbox(
                    f"{t('cap_select_label')} (GW {selected_gw})",
                    list(pl_starter_dict.keys()),
                    index=list(pl_starter_dict.keys()).index(cur_pl_cap) if cur_pl_cap in pl_starter_dict else 0,
                    format_func=lambda x: pl_starter_dict[x],
                    key=f"pl_cap_select_{selected_gw}",
                )
                if new_pl_c != cur_pl_cap:
                    set_planner_captain(new_pl_c)
            with c_pl_c2:
                pl_vc_cand = {k: v for k, v in pl_starter_dict.items() if k != cur_pl_cap}
                new_pl_vc = st.selectbox(
                    f"{t('vc_select_label')} (GW {selected_gw})",
                    list(pl_vc_cand.keys()),
                    index=list(pl_vc_cand.keys()).index(cur_pl_vc) if cur_pl_vc in pl_vc_cand else 0,
                    format_func=lambda x: pl_vc_cand[x],
                    key=f"pl_vc_select_{selected_gw}",
                )
                if new_pl_vc != cur_pl_vc:
                    set_planner_vice_captain(new_pl_vc)

        # באנר חילוף פעיל בפלנר
        if st.session_state.planner_swap_active and st.session_state.planner_selected_id:
            p_pl_sw_from = all_players.get(st.session_state.planner_selected_id)
            if p_pl_sw_from:
                is_pl_starter = any(p["id"] == p_pl_sw_from["id"] for p in cur_gw_sim["starters"])
                target_area_text = t("from_the_bench") if is_pl_starter else t("from_the_xi")
                c_sw_info, c_sw_canc = st.columns([4, 1])
                with c_sw_info:
                    st.info(f"**{t('swap_banner_title')}** {p_pl_sw_from['name']} ({p_pl_sw_from['team']} | {get_player_pos(p_pl_sw_from)}) — **{t('swap_active_hint_prefix')} {target_area_text} {t('swap_active_hint_suffix')}** (GW {selected_gw})")
                with c_sw_canc:
                    if st.button(t("cancel_swap"), key=f"pl_cancel_swap_top_{selected_gw}", use_container_width=True, type="primary"):
                        st.session_state.planner_swap_active = False
                        st.session_state.planner_selected_id = None
                        st.rerun()

        st.markdown('<div class="planner-split-anchor"></div>', unsafe_allow_html=True)
        col_pl_pitch, col_pl_fixtures = st.columns([1.65, 1.0], gap="medium")
        with col_pl_pitch:
            st.markdown(f"#### {t('tab_squad')} — Gameweek {selected_gw}")
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

            # ספסל מואר ומובלט בעיצוב Dugout ב-Planner
            st.write("")
            with st.container():
                st.markdown(
                    f"""
                    <div class="bench-anchor"></div>
                    <div class="bench-dugout-badge">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span style="font-weight:800; font-size:14px; color:var(--accent-mint);">{t('bench_title')}</span>
                        </div>
                        <span style="font-size:11px; color:var(--accent-mint); background:var(--badge-mint-bg); padding:2px 10px; border-radius:6px; font-weight:700; border:1px solid var(--badge-mint-border);">{t('bench_sub_order')}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                render_clean_planner_row(cur_gw_sim["bench"], is_bench=True)

        with col_pl_fixtures:
            render_gw_fixtures_panel(selected_gw)

        # חלון תכנון העברות שוק בפלנר
        with st.expander(f"{t('planner_tr_expander')} (GW {selected_gw})"):
            all_sim_players = cur_gw_sim["starters"] + cur_gw_sim["bench"]
            pl_tr_map = {p["id"]: f"{p['name']} ({get_player_pos(p)} | £{p['cost']}m | {p['team']})" for p in all_sim_players}
            sel_pl_tr_out = st.selectbox(f"{t('selling_player')} (GW {selected_gw}):", list(pl_tr_map.keys()), format_func=lambda x: pl_tr_map[x], key=f"pl_tr_sel_out_{selected_gw}")
            p_tr_out = all_players[sel_pl_tr_out]
            max_tr_budget = round(p_tr_out["cost"] + cur_gw_sim["bank"], 1)
            cur_squad_ids = [p["id"] for p in all_sim_players]
            pos_name = t(f"pos_{p_tr_out['pos_code']}")
            st.caption(f"{t('selling_player')} **{p_tr_out['name']}** ({pos_name} - £{p_tr_out['cost']}m) | {t('max_budget')} **£{max_tr_budget:.1f}m** | {t('bank_bal')}: **£{cur_gw_sim['bank']:.1f}m**")

            tr_search = st.text_input(t("search_placeholder"), key=f"tr_search_{selected_gw}").strip().lower()
            pl_rem_teams = {}
            for sp in all_sim_players:
                if sp["id"] != p_tr_out["id"]:
                    pl_rem_teams[sp["team"]] = pl_rem_teams.get(sp["team"], 0) + 1

            eligible_pool = [
                p for p in all_players.values()
                if p["pos_code"] == p_tr_out["pos_code"]
                and p["id"] not in cur_squad_ids
                and p["cost"] <= max_tr_budget
                and p["status"] == "a"
                and pl_rem_teams.get(p["team"], 0) < 3
            ]
            if tr_search:
                eligible_pool = [p for p in eligible_pool if tr_search in p["name"].lower() or tr_search in p["team"].lower()]

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
                                <span class="ltr-tag" style="color:var(--accent-cyan);">£{r_p['cost']:.1f}m | xP: {r_p['xp']}</span>
                                <div style="font-size:10px; color:var(--text-secondary); margin:4px 0;">{get_player_reason(r_p)}</div>
                                <div class="badge-fdr fdr-{r_p['next_fdr']}"><span class="ltr-tag">{r_p['next_match']}</span></div>
                            </div>
                            """
                        )
                        if st.button(f"{t('buy_player_btn')} {r_p['name']}", key=f"buy_rec_{r_p['id']}_{selected_gw}", use_container_width=True):
                            st.session_state.planner_plan[selected_gw]["transfers"].append(
                                (p_tr_out["id"], r_p["id"])
                            )
                            st.toast(f"{r_p['name']} ({r_p['team']})")
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
                        st.toast(f"{p_tr_out['name']} -> {all_players[chosen_pool_id]['name']}")
                        st.rerun()

# ---------------------------------------------------------------------
# טאב 7: 🏆 מרגל מיני-ליגות (Mini-League Spy)
# ---------------------------------------------------------------------
with t_leagues:
    st.subheader(t("t7_title"))
    st.caption(t("t7_caption"))

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
                t("t7_choose_league"),
                list(user_league_options.keys()),
                format_func=lambda x: user_league_options[x],
            )
            league_id_input = str(sel_user_lid)
        else:
            league_id_input = st.text_input(t("t7_enter_id"), placeholder="e.g. 314").strip()
    with col_l2:
        st.write("")
        custom_lid = st.text_input(t("t7_or_search"), placeholder="...").strip()
        if custom_lid and custom_lid.isdigit():
            league_id_input = custom_lid

    if league_id_input and league_id_input.isdigit():
        league_data = fetch_classic_league_standings(int(league_id_input))
        if league_data and "standings" in league_data:
            l_info = league_data.get("league", {})
            results = league_data["standings"].get("results", [])

            st.markdown(f"#### {t('t7_league_table')} **{l_info.get('name', 'Classic League')}**")

            if results:
                leader = results[0]
                my_entry = next((r for r in results if str(r["entry"]) == str(team_id)), None)
                my_league_item = next((l for l in my_leagues if str(l.get("id")) == str(league_id_input)), None)

                c_lg1, c_lg2, c_lg3 = st.columns(3)
                with c_lg1:
                    st.metric(t("t7_leader"), f"{leader['entry_name']}", f"{leader['total']} {t('pts')}")
                with c_lg2:
                    if my_entry:
                        gap = leader["total"] - my_entry["total"]
                        st.metric(t("t7_your_rank"), f"{t('t7_rank_pos')} {my_entry['rank']}", f"{t('t7_gap_top')} -{gap} {t('pts')}")
                    elif my_league_item and my_league_item.get("entry_rank"):
                        st.metric(t("t7_your_rank"), f"{t('t7_rank_pos')} {my_league_item['entry_rank']}", t("t7_outside_top_50"))
                    else:
                        st.metric(t("t7_your_rank"), "—", t("t7_not_in_league"))
                with c_lg3:
                    has_more = league_data.get("standings", {}).get("has_next", False)
                    tot_count = f"{len(results)}+" if has_more else f"{len(results)}"
                    st.metric(t("t7_total_members"), tot_count)

                st.caption(t("t7_showing_top_50"))

                # טבלת תוצאות מעוצבת
                headers_lg = [
                    t("t7_th_rank"),
                    t("t7_th_team_name"),
                    t("t7_th_manager"),
                    t("t7_th_last_gw"),
                    t("t7_th_total_pts"),
                    t("t7_th_team_id"),
                ]
                rows_lg = []
                for r in results[:20]:
                    is_me = (str(r["entry"]) == str(team_id))
                    prefix = f"{t('you_indicator')} " if is_me else ""
                    name_color = "var(--accent-mint)" if is_me else "inherit"
                    rows_lg.append([
                        f"<b>#{r['rank']}</b>",
                        f'<span style="font-weight:700; color:{name_color};">{prefix}{r["entry_name"]}</span>',
                        f"<span>{r['player_name']}</span>",
                        f'<span class="ltr-tag">{r["event_total"]} {t("pts")}</span>',
                        f'<span class="ltr-tag" style="font-weight:800; color:var(--accent-cyan);">{r["total"]} {t("pts")}</span>',
                        f'<span class="ltr-tag" style="color:var(--text-muted); font-size:11px;">#{r["entry"]}</span>',
                    ])
                render_styled_table(headers_lg, rows_lg, is_rtl=(st.session_state.app_lang == "he"))

                # כלי ריגול ראש בראש מול יריב
                st.write("---")
                st.markdown(f"#### {t('t7_h2h_title')}")
                rival_opts = {r["entry"]: f"{t('t7_rank_pos')} {r['rank']} - {r['entry_name']} ({r['player_name']})" for r in results if str(r["entry"]) != str(team_id)}
                if rival_opts:
                    chosen_rival_id = st.selectbox(t("t7_choose_rival"), list(rival_opts.keys()), format_func=lambda x: rival_opts[x])
                    
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

                        r_cap_obj = next((all_players[p["element"]]["name"] for p in rival_picks_res["picks"] if p.get("is_captain") and p["element"] in all_players), "—")
                        r_chip = rival_picks_res.get("active_chip", t("t7_no_chip"))
                        chip_txt = r_chip if r_chip else t("t7_no_chip")
                        my_diffs = [all_players[p]["name"] for p in my_pids if p not in rival_pids and p in all_players]
                        rival_diffs = [all_players[p]["name"] for p in rival_pids if p not in my_pids and p in all_players]
                        my_diffs_str = ', '.join(my_diffs[:6]) if my_diffs else t("t7_h2h_none")
                        rival_diffs_str = ', '.join(rival_diffs[:6]) if rival_diffs else t("t7_h2h_none")

                        col_spy1, col_spy2 = st.columns(2)
                        with col_spy1:
                            st.markdown(
                                f"""
                                <div class="accessible-card">
                                    <div class="split-box">
                                        <b style="color:var(--text-primary); font-size:13.5px;">{t('t7_rival_details')}</b>
                                        <span class="meta-chip" style="color:var(--accent-cyan);">GW {next_gw - 1}</span>
                                    </div>
                                    <div style="font-size:13px; color:var(--text-secondary); line-height:1.7;">
                                        {t('t7_rival_cap')} <b style="color:var(--text-primary);">{r_cap_obj}</b><br>
                                        {t('t7_rival_chip')} <span class="ltr-tag" style="background:rgba(16, 185, 129, 0.12); color:#10b981; padding:1px 6px; border-radius:4px; font-weight:700;">{chip_txt}</span>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        with col_spy2:
                            st.markdown(
                                f"""
                                <div class="accessible-card">
                                    <div class="split-box">
                                        <b style="color:var(--text-primary); font-size:13.5px;">{t('t7_differentials')}</b>
                                        <span class="meta-chip" style="color:#10b981; background:rgba(16, 185, 129, 0.12); border:1px solid rgba(16, 185, 129, 0.3);">H2H Edge</span>
                                    </div>
                                    <div style="font-size:11.5px; color:var(--text-secondary); margin-bottom:4px;">{t('t7_you_have')}</div>
                                    <div style="color:#10b981; font-size:12px; font-weight:700; background:rgba(16, 185, 129, 0.1); border:1px solid rgba(16, 185, 129, 0.25); padding:5px 8px; border-radius:6px; margin-bottom:8px;">{my_diffs_str}</div>
                                    <div style="font-size:11.5px; color:var(--text-secondary); margin-bottom:4px;">{t('t7_rival_has')}</div>
                                    <div style="color:#ef4444; font-size:12px; font-weight:700; background:rgba(239, 68, 68, 0.1); border:1px solid rgba(239, 68, 68, 0.25); padding:5px 8px; border-radius:6px;">{rival_diffs_str}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
            else:
                st.info(t("t7_no_results"))
        else:
            st.error(t("t7_err_fetch"))
    else:
        st.info(t("t7_prompt_enter"))

# ---------------------------------------------------------------------
# טאב 8: טיפים להצלחה ב-FPL (10 עקרונות זהב וצ'ק-ליסט דדליין)
# ---------------------------------------------------------------------
with t_tips:
    is_en_tips = (st.session_state.app_lang == "en")

    # כרטיס ראשי (Hero Card)
    tips_title_txt = t("tips_main_title")
    tips_sub_txt = t("tips_main_subtitle")
    st.markdown(
        f"""
        <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:14px; padding:20px 22px; margin-bottom:18px; box-shadow:0 4px 16px rgba(0,0,0,0.04);">
            <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px;">
                <div>
                    <h3 style="margin:0 0 6px 0; color:var(--text-primary); font-size:22px; font-weight:800; display:flex; align-items:center; gap:10px;">
                        <span>💡</span> <span>{tips_title_txt}</span>
                    </h3>
                    <div style="color:var(--text-secondary); font-size:13.5px; line-height:1.5;">
                        {tips_sub_txt}
                    </div>
                </div>
                <div style="display:flex; gap:8px; flex-wrap:wrap;">
                    <span class="meta-chip" style="background:var(--badge-mint-bg); color:var(--accent-mint); border:1px solid var(--badge-mint-border); font-weight:800; padding:6px 12px; font-size:12px;">🏆 Top 10k Mindset</span>
                    <span class="meta-chip" style="background:rgba(2, 132, 199, 0.1); color:var(--accent-cyan); border:1px solid rgba(2, 132, 199, 0.25); font-weight:800; padding:6px 12px; font-size:12px;">📊 Data-Driven Strategy</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # צ'ק-ליסט 60 שניות לפני הדדליין
    chk_title = t("tips_checklist_title")
    chk_1 = t("tips_chk_1")
    chk_2 = t("tips_chk_2")
    chk_3 = t("tips_chk_3")
    chk_4 = t("tips_chk_4")
    st.markdown(
        f"""
        <div class="accessible-card" style="border-right: 4px solid var(--accent-mint); border-left: 4px solid var(--accent-mint); margin-bottom: 20px;">
            <div class="split-box" style="margin-bottom: 12px;">
                <b style="color:var(--text-primary); font-size:14.5px; display:flex; align-items:center; gap:8px;">
                    <span>⏱️</span> {chk_title}
                </b>
                <span class="meta-chip" style="color:var(--accent-mint); background:var(--badge-mint-bg); border:1px solid var(--badge-mint-border);">Pre-Deadline</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 10px;">
                <div style="display:flex; align-items:flex-start; gap:8px; font-size:13px; color:var(--text-primary); background:var(--fxt-row-bg); padding:10px 12px; border-radius:8px; border:1px solid var(--border-color);">
                    <span style="color:#10b981; font-weight:900;">✓</span>
                    <span>{chk_1}</span>
                </div>
                <div style="display:flex; align-items:flex-start; gap:8px; font-size:13px; color:var(--text-primary); background:var(--fxt-row-bg); padding:10px 12px; border-radius:8px; border:1px solid var(--border-color);">
                    <span style="color:#10b981; font-weight:900;">✓</span>
                    <span>{chk_2}</span>
                </div>
                <div style="display:flex; align-items:flex-start; gap:8px; font-size:13px; color:var(--text-primary); background:var(--fxt-row-bg); padding:10px 12px; border-radius:8px; border:1px solid var(--border-color);">
                    <span style="color:#10b981; font-weight:900;">✓</span>
                    <span>{chk_3}</span>
                </div>
                <div style="display:flex; align-items:flex-start; gap:8px; font-size:13px; color:var(--text-primary); background:var(--fxt-row-bg); padding:10px 12px; border-radius:8px; border:1px solid var(--border-color);">
                    <span style="color:#10b981; font-weight:900;">✓</span>
                    <span>{chk_4}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 10 כרטיסי טיפים מסודרים בשתי עמודות
    c_tip_col1, c_tip_col2 = st.columns(2)
    half_tips = len(FPL_SUCCESS_TIPS) // 2
    rule_label = t("tips_golden_rule")

    with c_tip_col1:
        for tip in FPL_SUCCESS_TIPS[:half_tips]:
            tip_title = tip["title_en"] if is_en_tips else tip["title_he"]
            tip_desc = tip["desc_en"] if is_en_tips else tip["desc_he"]
            tip_tag = tip["tag_en"] if is_en_tips else tip["tag_he"]
            tip_rule = tip.get("rule_en", "") if is_en_tips else tip.get("rule_he", "")
            tip_icon = tip.get("icon", "💡")
            num_val = tip["num"]
            st.markdown(
                f"""
                <div class="accessible-card" style="margin-bottom:14px; padding:16px;">
                    <div class="split-box">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <span style="background:var(--badge-mint-bg); color:var(--accent-mint); border:1px solid var(--badge-mint-border); font-weight:900; font-size:13px; width:26px; height:26px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center;">{num_val}</span>
                            <b style="color:var(--text-primary); font-size:14.5px;">{tip_icon} {tip_title}</b>
                        </div>
                        <span class="meta-chip" style="color:var(--accent-cyan);">{tip_tag}</span>
                    </div>
                    <div style="font-size:13px; color:var(--text-secondary); margin-top:8px; line-height:1.65;">
                        {tip_desc}
                    </div>
                    <div style="margin-top:10px; background:var(--fxt-row-bg); border:1px solid var(--border-color); border-radius:8px; padding:8px 10px; font-size:12px; color:var(--text-primary);">
                        <b style="color:var(--accent-mint);">{rule_label}</b> {tip_rule}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with c_tip_col2:
        for tip in FPL_SUCCESS_TIPS[half_tips:]:
            tip_title = tip["title_en"] if is_en_tips else tip["title_he"]
            tip_desc = tip["desc_en"] if is_en_tips else tip["desc_he"]
            tip_tag = tip["tag_en"] if is_en_tips else tip["tag_he"]
            tip_rule = tip.get("rule_en", "") if is_en_tips else tip.get("rule_he", "")
            tip_icon = tip.get("icon", "💡")
            num_val = tip["num"]
            st.markdown(
                f"""
                <div class="accessible-card" style="margin-bottom:14px; padding:16px;">
                    <div class="split-box">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <span style="background:var(--badge-mint-bg); color:var(--accent-mint); border:1px solid var(--badge-mint-border); font-weight:900; font-size:13px; width:26px; height:26px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center;">{num_val}</span>
                            <b style="color:var(--text-primary); font-size:14.5px;">{tip_icon} {tip_title}</b>
                        </div>
                        <span class="meta-chip" style="color:var(--accent-cyan);">{tip_tag}</span>
                    </div>
                    <div style="font-size:13px; color:var(--text-secondary); margin-top:8px; line-height:1.65;">
                        {tip_desc}
                    </div>
                    <div style="margin-top:10px; background:var(--fxt-row-bg); border:1px solid var(--border-color); border-radius:8px; padding:8px 10px; font-size:12px; color:var(--text-primary);">
                        <b style="color:var(--accent-mint);">{rule_label}</b> {tip_rule}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

