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

# --- עיצוב CSS: נגישות, RTL, וצבעי פציעות מרוככים ---
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

.pitch {
    background: radial-gradient(circle, #1a3821 0%, #0d1e12 100%);
    border: 2px solid #234e2c;
    border-radius: 14px;
    padding: 16px 8px;
    margin: 12px 0;
    box-shadow: inset 0 0 35px rgba(0,0,0,0.6);
}
.pitch-row {
    display: flex;
    justify-content: space-around;
    align-items: center;
    margin-bottom: 12px;
    gap: 4px;
}

.p-card {
    background: rgba(17, 26, 40, 0.95);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 6px 4px;
    text-align: center;
    width: 86px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
}

/* צבעי הפציעות רוככו לצבעי פסטל נעימים יותר */
.cap-gold { border: 2px solid #facc15 !important; }
.card-bench { background: rgba(30, 41, 59, 0.7); border: 1px dashed #475569; }
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
    margin: 2px 0;
}

.badge-fdr {
    font-size: 9px;
    font-weight: 700;
    padding: 1px 5px;
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

/* התראות הפציעה בתגית הותאמו גם כן לצבעים רכים יותר */
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
</style>
""",
    unsafe_allow_html=True,
)


# --- 1. משיכת נתוני הליגה וכיול אלגוריתמי (מעודכן ל-4 מחזורים) ---
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

    for el_id, el in elements.items():
        if el["status"] == "u":
            continue

        team_short = teams[el["team"]]["short_name"]
        upcoming = []
        fdr_list = []
        # תכנון ל-4 מחזורים בשביל ה-Planner
        for f in fixtures:
            if f["event"] in [next_gw, next_gw + 1, next_gw + 2, next_gw + 3]:
                if f["team_h"] == el["team"]:
                    opp = teams[f["team_a"]]["short_name"]
                    upcoming.append(f"{opp} (H)")
                    fdr_list.append(f["team_h_difficulty"])
                elif f["team_a"] == el["team"]:
                    opp = teams[f["team_h"]]["short_name"]
                    upcoming.append(f"{opp} (A)")
                    fdr_list.append(f["team_a_difficulty"])

        weights = [0.50, 0.30, 0.20]
        weighted_fdr = sum(
            (5.3 - fdr) * weights[i] for i, fdr in enumerate(fdr_list[:3])
        )
        avg_fdr = sum(fdr_list[:3]) / min(3, len(fdr_list)) if fdr_list else 3.0

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
        
        # תיקון 100% שחקני עוגן (הולאנד, ברונו)
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
            "upcoming_list": upcoming,
            "fdr_list_full": fdr_list,
        }

    return processed, next_gw, next_deadline


all_players, next_gw, next_deadline = fetch_league_data()

# --- 2. שער כניסה ומסך נחיתה ---
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
        var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        var seconds = Math.floor((distance % (1000 * 60)) / 1000);
        
        document.getElementById("fpl-clock").innerHTML = days + "d " + hours + "h " + minutes + "m " + seconds + "s";
    }}, 1000);
</script>
"""
components.html(clock_html, height=85)


# --- 5. טאבים מרכזיים ---
t_squad, t_transfers, t_analysis, t_scout, t_scenarios, t_planner = st.tabs([
    "🟢 הסגל על המגרש",
    "🔄 מעבדת חילופים",
    "📊 ניתוח וחסרונות",
    "🌟 רדאר רכש עילית",
    "🎯 3 תרחישי תקציב",
    "🗓️ מתכנן מחזורים",
])


def render_pitch_card(p, is_bench=False):
    cap_badge = "👑 " if p.get("is_cap") else ("🥈 " if p.get("is_vc") else "")
    bench_class = "card-bench" if is_bench else ""

    if p["chance"] <= 25 or p["status"] in ["i", "s", "u"]:
        status_class = "card-danger"
        status_pill = (
            f'<div class="prob-badge prob-red">🔴 פצוע {p["start_prob"]}%</div>'
        )
    elif p["chance"] <= 75 or p["status"] == "d":
        status_class = "card-warning"
        status_pill = (
            f'<div class="prob-badge prob-yellow">🟡 בספק {p["start_prob"]}%</div>'
        )
    else:
        status_class = "cap-gold" if p.get("is_cap") else ""
        status_pill = (
            f'<div class="prob-badge prob-green">🟢 {p["start_prob"]}% פותח</div>'
        )

    return (
        f'<div class="p-card {status_class} {bench_class}">'
        f'<div class="p-name">{cap_badge}{p["name"]}</div>'
        f'<div class="p-sub"><span class="ltr-tag">{p["team"]} |'
        f" £{p['cost']}m</span></div>"
        f'<div class="badge-fdr fdr-{p["next_fdr"]}"><span'
        f' class="ltr-tag">{p["next_match"]}</span></div>'
        f"{status_pill}"
        f'<div style="font-size:9px; color:#38bdf8; margin-top:2px;">xP:'
        f" {p['xp']}</div>"
        "</div>"
    )


# טאב 1: מגרש חי
with t_squad:
    st.caption(
        f"מערך: **{pos_counts[2]}-{pos_counts[3]}-{pos_counts[4]}** | סך תוחלת"
        f" נקודות: **{starting_xp_total:.1f}**"
    )

    fwd_h = "".join(
        render_pitch_card(p) for p in starters if p["pos_code"] == 4
    )
    mid_h = "".join(
        render_pitch_card(p) for p in starters if p["pos_code"] == 3
    )
    def_h = "".join(
        render_pitch_card(p) for p in starters if p["pos_code"] == 2
    )
    gk_h = "".join(render_pitch_card(p) for p in starters if p["pos_code"] == 1)

    st.markdown(
        '<div class="pitch">'
        f'<div class="pitch-row">{fwd_h}</div>'
        f'<div class="pitch-row">{mid_h}</div>'
        f'<div class="pitch-row">{def_h}</div>'
        f'<div class="pitch-row">{gk_h}</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    st.caption("🪑 שחקני הספסל:")
    bench_h = "".join(render_pitch_card(p, is_bench=True) for p in bench)
    st.markdown(
        f'<div style="display:flex; justify-content:center; gap:8px;'
        f' margin-bottom:12px;">{bench_h}</div>',
        unsafe_allow_html=True,
    )

    with st.expander("🔄 חילוף מהיר בין שחקן הרכב לשחקן ספסל"):
        starters_opts = {
            p["id"]: (
                f"{p['name']} ({p['pos']}) — {p['start_prob']}% פותח | xP: {p['xp']}"
            )
            for p in starters
        }
        bench_opts = {
            p["id"]: (
                f"{p['name']} ({p['pos']}) — {p['start_prob']}% פותח | xP: {p['xp']}"
            )
            for p in bench
        }

        sc1, sc2, sc3 = st.columns([1.5, 1.5, 1])
        with sc1:
            sub_out_id = st.selectbox(
                "שחקן הרכב שיורד:",
                list(starters_opts.keys()),
                format_func=lambda x: starters_opts[x],
            )
        with sc2:
            sub_in_id = st.selectbox(
                "שחקן ספסל שעולה:",
                list(bench_opts.keys()),
                format_func=lambda x: bench_opts[x],
            )
        with sc3:
            st.write("")
            st.write("")
            if st.button("בצע חילוף 🔁", use_container_width=True):
                sim = [
                    p["pos_code"] for p in starters if p["id"] != sub_out_id
                ] + [all_players[sub_in_id]["pos_code"]]
                if (
                    sim.count(1) != 1
                    or not (3 <= sim.count(2) <= 5)
                    or not (1 <= sim.count(4) <= 3)
                ):
                    st.error("חילוף לא חוקי (חובה שוער 1, 3–5 מגנים ולפחות חלוץ 1).")
                else:
                    p_o = next(
                        p
                        for p in st.session_state.user_squad
                        if p["element"] == sub_out_id
                    )
                    p_i = next(
                        p for p in st.session_state.user_squad if p["element"] == sub_in_id
                    )
                    p_o["position"], p_i["position"] = p_i["position"], p_o["position"]
                    st.rerun()

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

# טאב 6: מתכנן מחזורים אסטרטגי (Planner)
with t_planner:
    st.subheader("🗓️ מתכנן מחזורים אסטרטגי (4 Gameweeks)")
    
    # 1. מנגנון צבירת חילופים (Transfer Bank)
    st.markdown("#### 🔄 צבירת חילופים (Transfer Bank Inventory)")
    st.caption("חוק ברזל ל-Top 100K: תכנון לשמירת חילופים (Roll) מאפשר גמישות ומונע מינוסים עתידיים.")
    
    col_t1, col_t2 = st.columns([1, 2])
    with col_t1:
        available_fts = st.number_input("כמה חילופים חינמיים זמינים לך כרגע?", min_value=1, max_value=5, value=1)
        planned_transfers_this_gw = st.number_input("כמה חילופים אתה מתכנן לבצע השבוע?", min_value=0, max_value=5, value=0)
    
    with col_t2:
        rolled = min(5, max(0, available_fts - planned_transfers_this_gw))
        next_week_fts = min(5, rolled + 1)
        
        status_color = "#10b981" if next_week_fts >= 2 else "#ef4444"
        st.markdown(f"""
        <div style="background:#111a28; border:1px solid #1e2e46; border-radius:10px; padding:15px; margin-top:28px;">
            <div style="font-size:13px; color:#94a3b8;">צפי מלאי חילופים לשבוע הבא:</div>
            <div style="font-size:14px; margin-top:5px;">
                • למחזור הנוכחי (GW {next_gw}): <b>{available_fts} חילופים</b><br>
                • למחזור הבא (GW {next_gw + 1}): <b style="color:{status_color};">{next_week_fts} חילופים זמינים</b> (לאחר צבירה)
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if next_week_fts < 2:
            st.warning("⚠️ לא יישארו לך 2 חילופים לשבוע הבא. שקול לגלגל חילוף (Roll) אלא אם יש פציעת הרכב דחופה.")

    st.write("---")
    st.markdown("#### 📅 לוח משחקים צפוי להרכב שלך (FDR Tracker)")
    
    # 2. טבלת FDR ויזואלית ב-HTML
    table_html = """
    <style>
    .planner-table { width: 100%; border-collapse: collapse; text-align: center; color: white; direction: ltr; margin-top:10px; font-family: sans-serif; }
    .planner-table th { background-color: #1e293b; padding: 10px; border: 1px solid #334155; font-size: 13px; color: #94a3b8; }
    .planner-table td { padding: 8px; border: 1px solid #334155; font-size: 12px; font-weight: 500; }
    .planner-name { text-align: left; padding-left: 10px !important; }
    .fdr-cell { border-radius: 4px; padding: 4px 6px; display: inline-block; width: 100%; box-sizing: border-box; }
    .bg-fdr-2 { background-color: #15803d; color: white; }
    .bg-fdr-3 { background-color: #475569; color: white; }
    .bg-fdr-4 { background-color: #b91c1c; color: white; }
    .bg-fdr-5 { background-color: #7f1d1d; color: white; }
    .bg-blank { background-color: #0f172a; color: #64748b; }
    </style>
    <table class="planner-table">
        <tr>
            <th class="planner-name">Player (Team)</th>
            <th>Pos</th>
            <th>GW {gw1}</th>
            <th>GW {gw2}</th>
            <th>GW {gw3}</th>
            <th>GW {gw4}</th>
        </tr>
    """.format(gw1=next_gw, gw2=next_gw+1, gw3=next_gw+2, gw4=next_gw+3)

    all_my_players_for_planner = starters + bench
    for p in all_my_players_for_planner:
        row_html = f"<tr><td class='planner-name'><b>{p['name']}</b> <span style='font-size:10px;color:#94a3b8;'>({p['team']})</span></td>"
        row_html += f"<td>{p['pos']}</td>"
        
        upcoming_list = p.get("upcoming_list", [])
        fdr_list_full = p.get("fdr_list_full", [])
        
        for i in range(4):
            if i < len(upcoming_list):
                match_str = upcoming_list[i]
                fdr = fdr_list_full[i] if i < len(fdr_list_full) else 3
                row_html += f"<td><div class='fdr-cell bg-fdr-{fdr}'>{match_str}</div></td>"
            else:
                row_html += "<td><div class='fdr-cell bg-blank'>BLANK</div></td>"
                
        row_html += "</tr>"
        table_html += row_html
        
    table_html += "</table>"
    st.markdown(table_html, unsafe_allow_html=True)
