import json
import time
import pandas as pd
import requests
import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="FPL Elite Scout | מנוע החלטות",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================================================================
# 1. עיצוב CSS מלא: מגרש, כרטיסי שחקן, וכפתורי חילוף בראש השחקן (FPL HUB STYLE)
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
    line-height: 1.5;
}

/* מגרש כדורגל */
.pitch-container {
    background: radial-gradient(circle, #1a3821 0%, #0d1e12 100%);
    border: 2px solid #234e2c;
    border-radius: 16px;
    padding: 20px 10px;
    margin: 15px 0;
    box-shadow: inset 0 0 40px rgba(0,0,0,0.7);
}

.pitch-row-title {
    text-align: center;
    color: #64748b;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 4px;
}

/* כרטיס שחקן בסיסי */
.player-card-box {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 8px 6px;
    text-align: center;
    transition: all 0.25s ease;
    min-height: 140px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.player-card-box:hover {
    background: var(--bg-card-hover);
    border-color: #334155;
}

/* כרטיס שחקן פצוע (כמו רודון בצילום מסך) */
.player-card-injured {
    border-color: rgba(239, 68, 68, 0.7) !important;
    background: rgba(239, 68, 68, 0.05) !important;
}

/* כרטיס שחקן שנבחר להחלפה (הילה זוהרת תואמת FPL Hub) */
.player-card-selected {
    border: 2px solid var(--accent-blue) !important;
    box-shadow: 0 0 16px rgba(56, 189, 248, 0.6) !important;
    transform: scale(1.02);
}

/* פרטי השחקן בתוך הכרטיס */
.p-name {
    font-size: 13px;
    font-weight: 700;
    color: #f8fafc;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.p-team-cost {
    font-size: 11px;
    color: var(--text-muted);
}
.p-fixture {
    font-size: 10px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    display: inline-block;
    margin: 3px auto;
}
.fix-badge-red {
    background: rgba(239, 68, 68, 0.2);
    color: #fca5a5;
    border: 1px solid rgba(239, 68, 68, 0.4);
}
.fix-badge-gray {
    background: rgba(148, 163, 184, 0.15);
    color: #cbd5e1;
    border: 1px solid rgba(148, 163, 184, 0.3);
}
.p-chance {
    font-size: 10px;
    font-weight: 600;
    border-radius: 4px;
    padding: 2px 4px;
    margin-bottom: 3px;
}
.chance-100 {
    background: rgba(16, 185, 129, 0.18);
    color: #34d399;
}
.chance-0 {
    background: rgba(239, 68, 68, 0.25);
    color: #f87171;
}
.p-xp {
    font-size: 11px;
    font-weight: 700;
    color: var(--accent-blue);
}

/* --- כפתור החילוף בראש השחקן (ממוקם בדיוק מעל הכרטיס) --- */
.sub-button-wrapper {
    display: flex;
    justify-content: center;
    margin-bottom: 4px;
}

div[data-testid="stButton"] button.sub-btn-default {
    background: #162235 !important;
    color: #38bdf8 !important;
    border: 1px solid #1e2e46 !important;
    border-radius: 16px !important;
    padding: 1px 10px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    height: 24px !important;
    line-height: 22px !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stButton"] button.sub-btn-default:hover {
    background: #38bdf8 !important;
    color: #090e17 !important;
    border-color: #38bdf8 !important;
    box-shadow: 0 0 8px rgba(56, 189, 248, 0.7) !important;
    transform: translateY(-1px) !important;
}

/* שחקן שממתין לחילוף (כפתור ביטול אדום מהבהב) */
div[data-testid="stButton"] button.sub-btn-active {
    background: #ef4444 !important;
    color: #ffffff !important;
    border: 1px solid #ef4444 !important;
    border-radius: 16px !important;
    padding: 1px 10px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    height: 24px !important;
    animation: sub-pulse 1.4s infinite !important;
}

@keyframes sub-pulse {
    0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.8); }
    70% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
    100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

/* שחקני יעד אפשריים להחלפה */
div[data-testid="stButton"] button.sub-btn-target {
    background: rgba(16, 185, 129, 0.2) !important;
    color: #34d399 !important;
    border: 1px solid #10b981 !important;
    border-radius: 16px !important;
    padding: 1px 10px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    height: 24px !important;
}

div[data-testid="stButton"] button.sub-btn-target:hover {
    background: #10b981 !important;
    color: #090e17 !important;
}

/* ספסל השחקנים */
.bench-container {
    background: #0d1522;
    border: 1px dashed var(--border-color);
    border-radius: 14px;
    padding: 16px 12px;
    margin-top: 15px;
}
.bench-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--text-muted);
    margin-bottom: 12px;
}

/* באנר סטטוס חילופים */
.sub-status-banner {
    background: #111a28;
    border: 1px solid var(--accent-blue);
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
</style>
    """,
    unsafe_allow_html=True,
)

# =====================================================================
# 2. ניהול נתוני הקבוצה וה-State של החילופים
# =====================================================================
if "sub_selected_id" not in st.session_state:
    st.session_state.sub_selected_id = None

# אתחול קבוצה התואמת במדויק את שחקני צילום המסך שלך
if "team_players" not in st.session_state:
    st.session_state.team_players = [
        # --- הרכב פותח (11 שחקנים) ---
        {"id": 1, "name": "Verbruggen", "team": "BHA", "price": 4.5, "pos": "GKP", "fix": "ARS (H)", "diff": 4, "chance": 100, "status_text": "100% פותח", "xp": 2.7, "is_starter": True},
        {"id": 2, "name": "N.Williams", "team": "NFO", "price": 4.5, "pos": "DEF", "fix": "BHA (A)", "diff": 3, "chance": 100, "status_text": "100% פותח", "xp": 4.4, "is_starter": True},
        {"id": 3, "name": "Calafiori", "team": "ARS", "price": 5.8, "pos": "DEF", "fix": "COV (H)", "diff": 2, "chance": 100, "status_text": "100% פותח", "xp": 4.2, "is_starter": True},
        {"id": 4, "name": "Maguire", "team": "MUN", "price": 4.5, "pos": "DEF", "fix": "FUL (A)", "diff": 3, "chance": 100, "status_text": "100% פותח", "xp": 3.4, "is_starter": True},
        {"id": 5, "name": "Rogers", "team": "AVL", "price": 5.2, "pos": "MID", "fix": "NEW (H)", "diff": 3, "chance": 100, "status_text": "100% פותח", "xp": 4.8, "is_starter": True},
        {"id": 6, "name": "B.Fernandes", "team": "MUN", "price": 8.4, "pos": "MID", "fix": "FUL (A)", "diff": 2, "chance": 100, "status_text": "100% פותח", "xp": 6.2, "is_starter": True},
        {"id": 7, "name": "Tzolis", "team": "BRU", "price": 5.5, "pos": "MID", "fix": "WOL (H)", "diff": 2, "chance": 100, "status_text": "100% פותח", "xp": 4.1, "is_starter": True},
        {"id": 8, "name": "Elanga", "team": "NFO", "price": 5.3, "pos": "MID", "fix": "BHA (A)", "diff": 3, "chance": 100, "status_text": "100% פותח", "xp": 4.0, "is_starter": True},
        {"id": 9, "name": "Haaland", "team": "MCI", "price": 15.2, "pos": "FWD", "fix": "WHU (A)", "diff": 2, "chance": 100, "status_text": "100% פותח", "xp": 8.9, "is_starter": True},
        {"id": 10, "name": "João Pedro", "team": "BHA", "price": 5.7, "pos": "FWD", "fix": "ARS (H)", "diff": 4, "chance": 100, "status_text": "100% פותח", "xp": 4.6, "is_starter": True},
        {"id": 11, "name": "Calvert-Lewin", "team": "EVE", "price": 6.0, "pos": "FWD", "fix": "BOU (H)", "diff": 2, "chance": 100, "status_text": "100% פותח", "xp": 4.3, "is_starter": True},
        
        # --- שחקני הספסל (4 שחקנים) ---
        {"id": 12, "name": "Kinsky", "team": "TOT", "price": 4.5, "pos": "GKP", "fix": "AVL (H)", "diff": 3, "chance": 100, "status_text": "100% פותח", "xp": 3.1, "is_starter": False, "bench_pos": 0},
        {"id": 13, "name": "M.Sangaré", "team": "BRE", "price": 5.7, "pos": "MID", "fix": "CHE (H)", "diff": 4, "chance": 100, "status_text": "100% פותח", "xp": 4.5, "is_starter": False, "bench_pos": 1},
        {"id": 14, "name": "Rodon", "team": "LEE", "price": 4.4, "pos": "DEF", "fix": "CRY (H)", "diff": 4, "chance": 0, "status_text": "0% פצוע", "xp": 0.0, "is_starter": False, "bench_pos": 2},
        {"id": 15, "name": "Davis", "team": "IPS", "price": 4.0, "pos": "DEF", "fix": "EVE (A)", "diff": 3, "chance": 100, "status_text": "100% פותח", "xp": 4.5, "is_starter": False, "bench_pos": 3},
    ]


# =====================================================================
# 3. מנוע החילופים ובדיקת חוקיות FPL (Formation Rules)
# =====================================================================
def validate_and_swap(p1_id, p2_id):
    """
    מבצע חילוף בין שני שחקנים תוך שמירה על חוקי FPL:
    1. שוער מוחלף אך ורק מול שוער.
    2. ההרכב חייב להכיל לפחות: 1 שוער, 3 שחקני הגנה, 2 קשרים, 1 חלוץ.
    """
    players = st.session_state.team_players
    p1 = next((p for p in players if p["id"] == p1_id), None)
    p2 = next((p for p in players if p["id"] == p2_id), None)

    if not p1 or not p2:
        return False, "שגיאה באיתור השחקנים"

    # בדיקת שוער
    if (p1["pos"] == "GKP" or p2["pos"] == "GKP") and p1["pos"] != p2["pos"]:
        return False, "שוער יכול להתחלף רק עם שוער!"

    # בדיקת חוקיות מערך במקרה של חילוף בין הרכב לספסל
    if p1["is_starter"] != p2["is_starter"]:
        starter_p = p1 if p1["is_starter"] else p2
        bench_p = p2 if p1["is_starter"] else p1

        # חישוב המערך החדש שיווצר
        current_starters = [p for p in players if p["is_starter"]]
        def_count = sum(1 for p in current_starters if p["pos"] == "DEF")
        mid_count = sum(1 for p in current_starters if p["pos"] == "MID")
        fwd_count = sum(1 for p in current_starters if p["pos"] == "FWD")

        if starter_p["pos"] == "DEF": def_count -= 1
        if starter_p["pos"] == "MID": mid_count -= 1
        if starter_p["pos"] == "FWD": fwd_count -= 1

        if bench_p["pos"] == "DEF": def_count += 1
        if bench_p["pos"] == "MID": mid_count += 1
        if bench_p["pos"] == "FWD": fwd_count += 1

        if def_count < 3:
            return False, "מערך לא חוקי: הרכב FPL חייב לכלול לפחות 3 שחקני הגנה!"
        if mid_count < 2:
            return False, "מערך לא חוקי: הרכב FPL חייב לכלול לפחות 2 קשרים!"
        if fwd_count < 1:
            return False, "מערך לא חוקי: הרכב FPL חייב לכלול לפחות חלוץ אחד!"

    # ביצוע ההחלפה
    p1["is_starter"], p2["is_starter"] = p2["is_starter"], p1["is_starter"]
    if "bench_pos" in p1 and "bench_pos" in p2:
        p1["bench_pos"], p2["bench_pos"] = p2["bench_pos"], p1["bench_pos"]

    return True, f"חילוף בוצע בהצלחה: {p1['name']} ⇄ {p2['name']}"


def on_sub_click(player_id):
    """מאזין ללחיצה על כפתור החילוף בראש כרטיס השחקן"""
    if st.session_state.sub_selected_id is None:
        # שחקן ראשון סומן לחילוף
        st.session_state.sub_selected_id = player_id
    elif st.session_state.sub_selected_id == player_id:
        # לחיצה שוב על אותו השחקן מבטלת את הבחירה
        st.session_state.sub_selected_id = None
    else:
        # שחקן שני נבחר -> ביצוע החילוף
        p1_id = st.session_state.sub_selected_id
        success, msg = validate_and_swap(p1_id, player_id)
        if success:
            st.toast(msg, icon="✅")
        else:
            st.error(msg)
        st.session_state.sub_selected_id = None
        st.rerun()


# =====================================================================
# 4. פונקציית רינדור כרטיס שחקן עם כפתור החילוף בראשו
# =====================================================================
def render_player_card(col, player):
    """מרנדר כרטיס שחקן עם כפתור חילוף אלגנטי בראשו (ללא איקסים תחתונים)"""
    with col:
        is_selected = (st.session_state.sub_selected_id == player["id"])
        has_sub_in_progress = (st.session_state.sub_selected_id is not None)

        # טקסט וסגנון כפתור בראש השחקן
        if is_selected:
            btn_label = "✕ בטל"
            btn_help = "בטל סימון חילוף"
        elif has_sub_in_progress:
            btn_label = "⇄ לכאן"
            btn_help = f"החלף עם {player['name']}"
        else:
            btn_label = "⇄ חילוף"
            btn_help = f"סמן את {player['name']} לחילוף"

        # כפתור החילוף ישירות בראש הכרטיס
        st.markdown('<div class="sub-button-wrapper">', unsafe_allow_html=True)
        if st.button(btn_label, key=f"sub_btn_{player['id']}", help=btn_help):
            on_sub_click(player["id"])
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # קביעת סגנון הכרטיס (פצוע, נבחר או רגיל)
        card_classes = ["player-card-box"]
        if player["chance"] == 0:
            card_classes.append("player-card-injured")
        if is_selected:
            card_classes.append("player-card-selected")
        
        fix_badge_class = "fix-badge-red" if player.get("diff", 3) >= 4 else "fix-badge-gray"
        chance_badge_class = "chance-0" if player["chance"] == 0 else "chance-100"

        # תוכן הכרטיס
        st.markdown(
            f"""
            <div class="{' '.join(card_classes)}">
                <div class="p-name">{player['name']}</div>
                <div class="p-team-cost">{player['team']} | £{player['price']}m</div>
                <div>
                    <span class="p-fixture {fix_badge_class}">{player['fix']}</span>
                </div>
                <div>
                    <span class="p-chance {chance_badge_class}">{player['status_text']}</span>
                </div>
                <div class="p-xp">xP: {player['xp']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =====================================================================
# 5. רינדור המגרש, הספסל ובאנר הסטטוס
# =====================================================================
st.title("⚽ הרכב הקבוצה וניהול חילופים")

# באנר אינטראקטיבי כשיש שחקן שנבחר להחלפה
if st.session_state.sub_selected_id is not None:
    sel_p = next((p for p in st.session_state.team_players if p["id"] == st.session_state.sub_selected_id), None)
    if sel_p:
        b_col1, b_col2 = st.columns([5, 1])
        with b_col1:
            st.markdown(
                f"""
                <div class="sub-status-banner">
                    <span style="font-weight: 700; color: #f8fafc;">
                        🔄 מצב חילופים פעיל: בחרת ב-<b>{sel_p['name']}</b> ({sel_p['pos']}). לחץ על <b>"⇄ לכאן"</b> בראש שחקן אחר כדי להשלים את החילוף.
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with b_col2:
            if st.button("✕ בטל חילוף", key="cancel_top_banner"):
                st.session_state.sub_selected_id = None
                st.rerun()

# חלוקת שחקני ההרכב לפי עמדות
starters = [p for p in st.session_state.team_players if p["is_starter"]]
gks = [p for p in starters if p["pos"] == "GKP"]
defs = [p for p in starters if p["pos"] == "DEF"]
mids = [p for p in starters if p["pos"] == "MID"]
fwds = [p for p in starters if p["pos"] == "FWD"]

# --- מגרש הכדורגל (ההרכב הפותח) ---
st.markdown('<div class="pitch-container">', unsafe_allow_html=True)

# 1. שוער (מרכז המגרש)
c_left, c_gk, c_right = st.columns([2, 1, 2])
if gks:
    render_player_card(c_gk, gks[0])

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# 2. הגנה
if defs:
    def_cols = st.columns(len(defs))
    for i, p in enumerate(defs):
        render_player_card(def_cols[i], p)

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# 3. קישור
if mids:
    mid_cols = st.columns(len(mids))
    for i, p in enumerate(mids):
        render_player_card(mid_cols[i], p)

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# 4. התקפה
if fwds:
    # מירכוז חלוצים אם יש פחות מ-3
    if len(fwds) == 1:
        _, fwd_col, _ = st.columns([1, 1, 1])
        render_player_card(fwd_col, fwds[0])
    elif len(fwds) == 2:
        _, f1, f2, _ = st.columns([1, 2, 2, 1])
        render_player_card(f1, fwds[0])
        render_player_card(f2, fwds[1])
    else:
        fwd_cols = st.columns(len(fwds))
        for i, p in enumerate(fwds):
            render_player_card(fwd_cols[i], p)

st.markdown('</div>', unsafe_allow_html=True)

# --- ספסל הקבוצה (4 שחקנים) ---
st.markdown(
    """
    <div class="bench-title">
        🪑 שחקני הספסל:
    </div>
    """,
    unsafe_allow_html=True,
)

bench_players = [p for p in st.session_state.team_players if not p["is_starter"]]
# מיון הספסל: שוער תמיד ראשון, ואז שחקני שדה לפי סדר הספסל
bench_players.sort(key=lambda p: (0 if p["pos"] == "GKP" else 1, p.get("bench_pos", 99)))

bench_cols = st.columns(4)
for idx, p in enumerate(bench_players):
    render_player_card(bench_cols[idx], p)

# =====================================================================
# סוף הקוד - שים לב: כל האיקסים והרדיו הוסרו לחלוטין!
# =====================================================================
