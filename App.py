import json
import time
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="FPL Elite Scout | Top 50K Engine",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- עיצוב CSS: RTL מלא, התאמה למובייל ומסך נחיתה ---
st.markdown(
    """
<style>
.main {
    direction: rtl;
    text-align: right;
    background-color: #080d1a;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
div[data-testid="stMarkdownContainer"] p { direction: rtl; text-align: right; }
.ltr-box { direction: ltr !important; display: inline-block; unicode-bidi: embed; }

/* כרטיס מסך נחיתה */
.landing-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 16px;
    padding: 24px;
    margin: 20px auto;
    max-width: 600px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    text-align: center;
}

.metric-box {
    background: #131c2e;
    border-radius: 10px;
    padding: 12px;
    text-align: center;
    border: 1px solid #1f2d47;
    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
}
.pitch {
    background: radial-gradient(circle, #1a3821 0%, #0d1e12 100%);
    border: 2px solid #234e2c;
    border-radius: 14px;
    padding: 16px 6px;
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
    background: rgba(15, 23, 42, 0.94);
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px 4px;
    text-align: center;
    width: 88px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.4);
}
.cap-border { border: 2px solid #facc15 !important; }
.bench-card { background: rgba(30, 41, 59, 0.7); border: 1px dashed #64748b; }

.card-injured {
    border: 2px solid #ef4444 !important;
    background: rgba(69, 10, 10, 0.95) !important;
    box-shadow: 0 0 10px rgba(239, 68, 68, 0.5) !important;
}
.card-doubt {
    border: 2px solid #f59e0b !important;
    background: rgba(69, 45, 10, 0.95) !important;
    box-shadow: 0 0 10px rgba(245, 158, 11, 0.4) !important;
}

.prob-pill {
    font-size: 8.5px;
    font-weight: bold;
    padding: 1px 4px;
    border-radius: 4px;
    margin: 2px auto;
    width: fit-content;
}
.pill-red { background: #450a0a; color: #fca5a5; border: 1px solid #dc2626; }
.pill-yellow { background: #451a03; color: #fde68a; border: 1px solid #d97706; }
.pill-green { background: #064e3b; color: #6ee7b7; border: 1px solid #059669; }

.p-name { font-weight: bold; font-size: 11px; color: #f8fafc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.p-team { font-size: 9px; color: #94a3b8; margin: 1px 0; }
.p-fxt { font-size: 9px; font-weight: bold; padding: 1px 4px; border-radius: 3px; display: inline-block; }

.compare-card {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px;
    margin: 12px 0;
}
.stat-pill {
    background: #1e293b;
    border-radius: 6px;
    padding: 6px 10px;
    margin: 4px 0;
    display: flex;
    justify-content: space-between;
    font-size: 13px;
}
.flaw-card {
    background: #231215;
    border-right: 4px solid #ef4444;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 13px;
    color: #fca5a5;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.penalty-tag {
    background: #7f1d1d;
    color: #fecaca;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 11px;
}
.badge { font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; display: inline-block; }
.badge-buylow { background: #064e3b; color: #6ee7b7; border: 1px solid #059669; }
.badge-trap { background: #450a0a; color: #fca5a5; border: 1px solid #dc2626; }
.fdr-2 { background: #15803d; color: #fff; }
.fdr-3 { background: #475569; color: #fff; }
.fdr-4 { background: #b91c1c; color: #fff; }
.fdr-5 { background: #7f1d1d; color: #fff; }
.health-box { padding: 12px; border-radius: 8px; margin-bottom: 8px; }
.health-yellow { background: #26200d; border-right: 4px solid #f59e0b; }
.health-red { background: #2b1114; border-right: 4px solid #ef4444; }
</style>
""",
    unsafe_allow_html=True,
)


# --- 1. טעינת נתוני ליגה ומודל קבלת החלטות ---
@st.cache_data(ttl=600)
def fetch_league_data():
  base = "https://fantasy.premierleague.com/api/"
  bootstrap = requests.get(f"{base}bootstrap-static/").json()
  fixtures = requests.get(f"{base}fixtures/").json()
  teams = {t["id"]: t for t in bootstrap["teams"]}
  elements = {el["id"]: el for el in bootstrap["elements"]}

  next_gw = 4
  for ev in bootstrap["events"]:
    if ev.get("is_next"):
      next_gw = ev["id"]
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
    for f in fixtures:
      if f["event"] in [next_gw, next_gw + 1, next_gw + 2]:
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
    avg_fdr = sum(fdr_list) / len(fdr_list) if fdr_list else 3.0

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
    if mins_per_gw >= 75:
      tactical_rate = 95
    elif mins_per_gw >= 55:
      tactical_rate = 85
    elif mins_per_gw >= 35:
      tactical_rate = 65
    elif mins_per_gw > 0:
      tactical_rate = 40
    else:
      tactical_rate = 20

    start_prob = int(round(tactical_rate * (chance / 100.0)))
    if chance == 0:
      start_prob = 0

    xgi_per_90 = (expected_gi / mins) * 90 if mins >= 60 else expected_gi

    tag_status = None
    if expected_gi >= 1.2 and actual_gi <= 1:
      tag_status = "BUY_LOW"
      buy_low_bonus = 1.0
    elif actual_gi >= 3 and expected_gi < 0.9:
      tag_status = "OVERPERFORMING_TRAP"
      buy_low_bonus = -0.8
    else:
      buy_low_bonus = 0.0

    nailed_mult = 1.15 if mins_per_gw >= 75 else 0.85
    score = (
        (xgi_per_90 * 3.2)
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

    base_appearance = 2.0 if chance >= 75 else (1.0 if chance >= 25 else 0.0)
    next_match_fdr = fdr_list[0] if fdr_list else 3
    cs_prob = {2: 0.45, 3: 0.28, 4: 0.15, 5: 0.08}.get(next_match_fdr, 0.22)

    if el["element_type"] in [1, 2]:
      predicted_xp = (
          base_appearance + (cs_prob * 4.0) + (xgi_per_90 * 0.4 * 5.0)
      )
    elif el["element_type"] == 3:
      predicted_xp = base_appearance + (cs_prob * 1.0) + (xgi_per_90 * 5.5)
    else:
      predicted_xp = base_appearance + (xgi_per_90 * 5.2)

    if form >= 5.0:
      predicted_xp += 0.6
    if chance < 100:
      predicted_xp *= chance / 100.0
    predicted_xp = round(max(0.0, predicted_xp), 1)

    if tag_status == "BUY_LOW":
      reason = (
          "הזדמנות קנייה בשפל: מייצר מצבי כיבוש ברצף אך טרם תוגמל במספרים בפועל."
      )
    elif tag_status == "OVERPERFORMING_TRAP":
      reason = (
          "זהירות, מעל המצופה: כבש מעבר למצבים הממשיים שייצר. סכנת דעיכה"
          " לממוצע."
      )
    elif el["element_type"] in [1, 2]:
      reason = (
          "עוגן הגנתי מוביל מקבוצת צמרת עם סיכוי רשת נקייה גבוה."
          if team_short in elite_defenses
          else "מגן פעיל התקפית במחיר משתלם ובלוח נוח."
      )
    else:
      reason = (
          "כושר כיבוש שיא עם מעורבות ישירה בהתקפה."
          if form >= 5.0
          else "נתוני איום שערים יציבים לקראת לוח משחקים ירוק."
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
        "xgi": expected_gi,
        "xgi_p90": round(xgi_per_90, 2),
        "selected_by": float(el["selected_by_percent"]),
        "goals_assists": actual_gi,
        "score": round(score, 2),
        "xp": predicted_xp,
        "tag": tag_status,
        "reason": reason,
        "status": status,
        "chance": chance,
        "start_prob": start_prob,
        "next_match": upcoming[0] if upcoming else "—",
        "next_fdr": next_match_fdr,
        "avg_fdr": round(avg_fdr, 2),
        "fixtures": " | ".join(upcoming),
    }

  return processed, next_gw


all_players, next_gw = fetch_league_data()

# --- 2. שער כניסה ומסך נחיתה ראשי (Team ID Gatekeeper) ---
query_params = st.query_params
url_team_id = query_params.get("team", None)

if "user_team_id" not in st.session_state:
  if url_team_id and url_team_id.strip().isdigit():
    st.session_state.user_team_id = url_team_id.strip()
  else:
    st.session_state.user_team_id = None

# אם טרם הוזן Team ID — הצגת מסך הנחיתה בלבד ועצירת ריצה
if not st.session_state.user_team_id:
  st.write("")
  st.markdown(
      """
    <div class="landing-card">
        <h1 style="color:#38bdf8; margin-bottom:4px;">⚽ FPL Elite Scout</h1>
        <div style="font-size:16px; color:#94a3b8; margin-bottom:18px;">
            סוכן בינה ואסטרטגיית הרכב לקראת מחזור המכוון ל-<b>Top 50K</b>
        </div>
        <p style="font-size:13px; color:#cbd5e1; line-height:1.6; margin-bottom:20px;">
            ניתוח עומק מתקדם של הסגל שלך: בדיקת כשירות וסיכויי פתיחה, כיול ציון סגל ריאלי מול בנצ'מרק עולמי, 
            זיהוי שחקנים מעל המצופה (מלכודות) והמלצות רכש המותאמות לתקציב הבנק שלך.
        </p>
    </div>
    """,
      unsafe_allow_html=True,
  )

  col_center = st.columns([1, 2, 1])[1]
  with col_center:
    input_id = st.text_input(
        "הזן את מספר הקבוצה (Team ID):",
        placeholder="למשל: 139103",
        help="המספר שמופיע בכתובת האתר בלשונית Points",
    )
    b_col1, b_col2 = st.columns(2)
    with b_col1:
      if st.button("🚀 כניסה וניתוח סגל", use_container_width=True):
        if input_id.strip().isdigit():
          st.session_state.user_team_id = input_id.strip()
          st.query_params["team"] = input_id.strip()
          st.rerun()
        else:
          st.error("נא להזין מספר ID תקין המכיל ספרות בלבד.")
    with b_col2:
      if st.button("👀 נסה קבוצת דמו", use_container_width=True):
        st.session_state.user_team_id = "139103"
        st.query_params["team"] = "139103"
        st.rerun()

    with st.expander("❓ איפה מוצאים את ה-Team ID שלי?"):
      st.markdown("""
            1. פתח את אתר הפנטזי הרשמי: **fantasy.premierleague.com** והתחבר.
            2. לחץ על לשונית **Points** (נקודות).
            3. הסתכל על שורת הכתובת בדפדפן:  
               `https://fantasy.premierleague.com/entry/XXXXXX/event/...`  
               המספר שמופיע במקום ה-`XXXXXX` הוא ה-**Team ID** שלך!
            """)

  st.stop()

team_id = st.session_state.user_team_id


# --- 3. משיכת נתוני הקבוצה מה-API ---
@st.cache_data(ttl=300)
def fetch_user_team(t_id, gw):
  try:
    last_gw = max(1, gw - 1)  #[span_1](start_span)[span_1](end_span)
    base_url = "https://fantasy.premierleague.com/api/"  #[span_2](start_span)[span_2](end_span)
    picks_res = requests.get(
        f"{base_url}entry/{t_id}/event/{last_gw}/picks/"
    ).json()  #[span_3](start_span)[span_3](end_span)
    entry_res = requests.get(f"{base_url}entry/{t_id}/").json()  #[span_4](start_span)[span_4](end_span)

    if picks_res.get("active_chip") == "free_hit" and last_gw > 1:  #[span_5](start_span)[span_5](end_span)
      picks_res = requests.get(
          f"{base_url}entry/{t_id}/event/{last_gw - 1}/picks/"
      ).json()  #[span_6](start_span)[span_6](end_span)

    bank = picks_res.get("entry_history", {}).get("bank", 0) / 10  #[span_7](start_span)[span_7](end_span)
    picks = picks_res.get("picks", [])  #[span_8](start_span)[span_8](end_span)
    team_name = entry_res.get("name", f"Team {t_id}")
    rank = entry_res.get("summary_overall_rank", "—")  #[span_9](start_span)[span_9](end_span)
    return picks, bank, team_name, rank  #[span_10](start_span)[span_10](end_span)
  except Exception:
    return None, 0.0, None, None  #[span_11](start_span)[span_11](end_span)


raw_picks, initial_bank, my_team_name, my_rank = fetch_user_team(
    team_id, next_gw
)  #[span_12](start_span)[span_12](end_span)
if not raw_picks:
  st.error(
      f"❌ לא ניתן למשוך את נתוני הקבוצה עבור ID: {team_id}. אנא ודא שהמספר"
      " תקין."
  )
  if st.button("🔄 חזרה למסך הזנת ID"):
    st.session_state.user_team_id = None
    st.query_params.clear()
    st.rerun()
  st.stop()

# --- 4. ניהול סגל גלובלי ב-Session State ---
if (
    "user_squad" not in st.session_state
    or st.session_state.get("synced_team_id") != team_id
):
  st.session_state.user_squad = [dict(p) for p in raw_picks]
  st.session_state.user_bank = initial_bank
  st.session_state.synced_team_id = team_id
  st.session_state.transfers_log = []

starters = []  #[span_13](start_span)[span_13](end_span)
bench = []  #[span_14](start_span)[span_14](end_span)
for p in st.session_state.user_squad:
  pid = p["element"]  #[span_15](start_span)[span_15](end_span)
  p_info = all_players.get(pid)  #[span_16](start_span)[span_16](end_span)
  if p_info:
    item = {
        **p_info,
        "is_cap": p.get("is_captain", False),  #[span_17](start_span)[span_17](end_span)
        "is_vc": p.get("is_vice_captain", False),  #[span_18](start_span)[span_18](end_span)
        "position": p["position"],  #[span_19](start_span)[span_19](end_span)
    }
    if p["position"] <= 11:  #[span_20](start_span)[span_20](end_span)
      starters.append(item)  #[span_21](start_span)[span_21](end_span)
    else:
      bench.append(item)  #[span_22](start_span)[span_22](end_span)

pos_counts = {1: 0, 2: 0, 3: 0, 4: 0}  #[span_23](start_span)[span_23](end_span)
for p in starters:  #[span_24](start_span)[span_24](end_span)
  pos_counts[p["pos_code"]] += 1  #[span_25](start_span)[span_25](end_span)

formation_is_valid = (  #[span_26](start_span)[span_26](end_span)
    pos_counts[1] == 1  #[span_27](start_span)[span_27](end_span)
    and (3 <= pos_counts[2] <= 5)  #[span_28](start_span)[span_28](end_span)
    and (2 <= pos_counts[3] <= 5)  #[span_29](start_span)[span_29](end_span)
    and (1 <= pos_counts[4] <= 3)  #[span_30](start_span)[span_30](end_span)
    and len(starters) == 11  #[span_31](start_span)[span_31](end_span)
)

starting_xp_total = sum(
    p["xp"] * (2 if p.get("is_cap") else 1) for p in starters
)

# --- 5. כיול ציון סגל ריאליסטי (72–82) וניתוח חסרונות ---
benchmark_xp = 60.0
base_score = (starting_xp_total / benchmark_xp) * 84.0

squad_flaws = []
total_penalty = 0.0

for p in starters:
  if p["status"] != "a" or p["chance"] < 100:
    pen = 6.5 if p["chance"] <= 25 else 4.0
    total_penalty += pen
    squad_flaws.append({
        "type": "סיכון כשירות בהרכב הפותח",
        "penalty": f"-{pen:.1f}",
        "text": (
            f"<b>{p['name']} ({p['team']})</b> פותח בהרכב אך בספק/פצוע"
            f" ({p['chance']}% כשירות רפואית | {p['start_prob']}% סבירות"
            " לפתוח)."
        ),
    })

for bp in bench:
  if bp["status"] != "a" or bp["chance"] < 100:
    pen = 3.0
    total_penalty += pen
    squad_flaws.append({
        "type": "ספסל מושבת (ללא גיבוי)",
        "penalty": f"-{pen:.1f}",
        "text": (
            f"<b>{bp['name']} ({bp['team']})</b> בספסל אינו כשיר"
            f" ({bp['chance']}%) - אין רשת ביטחון לחילוף אוטומטי במקרה של"
            " היעדרות."
        ),
    })

for p in starters:
  if p["pos_code"] in [1, 2] and p["next_fdr"] >= 4:
    pen = 4.0
    total_penalty += pen
    squad_flaws.append({
        "type": "משחק הגנה בסיכון ספיגה גבוה",
        "penalty": f"-{pen:.1f}",
        "text": (
            f"<b>{p['name']} ({p['pos']})</b> פוגש יריבה קשה ({p['next_match']},"
            f" דרגת קושי FDR {p['next_fdr']}) - סיכוי נמוך לרשת נקייה."
        ),
    })

for p in starters:
  if p["pos_code"] in [3, 4] and p["next_fdr"] >= 5:
    pen = 2.5
    total_penalty += pen
    squad_flaws.append({
        "type": "משחק התקפי קשה במיוחד",
        "penalty": f"-{pen:.1f}",
        "text": (
            f"<b>{p['name']} ({p['team']})</b> מתמודד מול הגנת ברזל"
            f" ({p['next_match']}) - תקרת נקודות מוגבלת."
        ),
    })

for p in starters:
  if p["status"] == "a" and p["form"] < 2.5 and p["pos_code"] in [3, 4]:
    pen = 2.0
    total_penalty += pen
    squad_flaws.append({
        "type": "כושר הבקעה נמוך",
        "penalty": f"-{pen:.1f}",
        "text": (
            f"<b>{p['name']}</b> בתקופת בצורת (כושר {p['form']}) ותפוקה דלה"
            " במחזורים האחרונים."
        ),
    })

for p in starters:
  if p["tag"] == "OVERPERFORMING_TRAP":
    pen = 1.5
    total_penalty += pen
    squad_flaws.append({
        "type": "סכנת דעיכה לממוצע (Trap)",
        "penalty": f"-{pen:.1f}",
        "text": (
            f"<b>{p['name']}</b> הבקיע מעבר למצבים הממשיים שייצר - צפויה נסיגה"
            " בתפוקת הנקודות."
        ),
    })

if not formation_is_valid:
  pen = 8.0
  total_penalty += pen
  squad_flaws.append({
      "type": "מערך לא חוקי",
      "penalty": f"-{pen:.1f}",
      "text": (
          "המערך הנוכחי אינו חוקי לפי חוקי FPL (חובה שוער 1, 3–5 מגנים ולפחות"
          " חלוץ 1)."
      ),
  })

squad_rating = int(max(48, min(86, base_score - total_penalty)))

if squad_rating >= 80:
  rating_status = "🌟 סגל עילית מכויל (מוכן ל-Top 50K)"
  rating_color = "#10b981"
elif squad_rating >= 72:
  rating_status = "🟢 סגל תחרותי וחזק (עם נקודות תורפה קלות)"
  rating_color = "#38bdf8"
elif squad_rating >= 62:
  rating_status = "🟡 סגל מאוזן עם מוקדי סיכון הדורשים טיפול"
  rating_color = "#f59e0b"
else:
  rating_status = "🔴 סגל במצב חירום (דורש ריענון מיידי)"
  rating_color = "#ef4444"

# --- 6. כותרת עליונה, החלפת קבוצה ומדדים ראשיים ---
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
  st.title(f"⚽ FPL Command Center | {my_team_name}")
  st.caption(
      f'מנוע אנליטי לקראת מחזור {next_gw} | מחובר לסגל: <span'
      f' class="ltr-box"><b>{team_id}</b></span>',
      unsafe_allow_html=True,
  )
with header_col2:
  st.write("")
  if st.button("🔄 החלף קבוצה", use_container_width=True):
    st.session_state.user_team_id = None
    st.query_params.clear()
    st.rerun()

rank_disp = (
    f"{my_rank:,}"
    if isinstance(my_rank, int)
    else (str(my_rank) if my_rank else "—")
)
m1, m2, m3, m4 = st.columns(4)
m1.markdown(
    f'<div class="metric-box"><div'
    ' style="color:#38bdf8;font-size:12px;margin-bottom:4px;">ציון סגל (מכויל'
    f' ריאלי)</div><div'
    f' style="font-size:20px;font-weight:bold;color:{rating_color};">{squad_rating}'
    ' / 100</div></div>',
    unsafe_allow_html=True,
)
m2.markdown(
    '<div class="metric-box"><div'
    ' style="color:#10b981;font-size:12px;margin-bottom:4px;">תחזית נקודות'
    ' למחזור (xP)</div><div'
    ' style="font-size:20px;font-weight:bold;color:#fff;">'
    f"{starting_xp_total:.1f} נק׳</div></div>",
    unsafe_allow_html=True,
)
m3.markdown(
    '<div class="metric-box"><div'
    ' style="color:#f59e0b;font-size:12px;margin-bottom:4px;">יתרה'
    ' בבנק</div><div style="font-size:20px;font-weight:bold;color:#fff;"><span'
    f' class="ltr-box">£{st.session_state.user_bank:.1f}m</span></div></div>',
    unsafe_allow_html=True,
)
m4.markdown(
    '<div class="metric-box"><div'
    ' style="color:#a855f7;font-size:12px;margin-bottom:4px;">דירוג'
    ' כללי</div><div style="font-size:20px;font-weight:bold;color:#fff;"><span'
    f' class="ltr-box">{rank_disp}</span></div></div>',
    unsafe_allow_html=True,
)

st.write("")

# --- 7. טאבים ראשיים ---
tab_squad, tab_manual, tab_projection, tab_targets, tab_transfer, tab_health = (
    st.tabs([
        "🟢 הסגל על המגרש",
        "🔄 עדכון חילופים מהיר",
        "📊 מדד עוצמה וחסרונות הסגל",
        "🌟 רדאר רכש עילית",
        "🎯 הצעות חילוף לתקציב שלי",
        "🚦 רמזור בריאות הסגל",
    ])
)


def build_card(p, is_bench=False):
  cap_badge = (
      "👑 " if p.get("is_cap") else ("🥈 " if p.get("is_vc") else "")
  )  #[span_32](start_span)[span_32](end_span)
  bench_class = "bench-card" if is_bench else ""  #[span_33](start_span)[span_33](end_span)

  if p["chance"] <= 25 or p["status"] in ["i", "s", "u"]:
    status_class = "card-injured"
    status_pill = (
        f'<div class="prob-pill pill-red">🔴 פצוע {p["start_prob"]}%</div>'
    )
  elif p["chance"] <= 75 or p["status"] == "d":
    status_class = "card-doubt"
    status_pill = (
        f'<div class="prob-pill pill-yellow">🟡 בספק {p["start_prob"]}%</div>'
    )
  else:
    status_class = "cap-border" if p.get("is_cap") else ""
    status_pill = (
        f'<div class="prob-pill pill-green">🟢 {p["start_prob"]}% פותח</div>'
    )

  if p.get("is_cap") and p["chance"] > 75:  #[span_34](start_span)[span_34](end_span)
    status_class = "cap-border"

  return (
      f'<div class="p-card {status_class} {bench_class}">'
      f'<div class="p-name">{cap_badge}{p["name"]}</div>'
      f'<div class="p-team"><span class="ltr-box">{p["team"]} |'
      f" £{p['cost']}m</span></div>"
      f'<div class="p-fxt fdr-{p["next_fdr"]}"><span'
      f' class="ltr-box">{p["next_match"]}</span></div>'
      f"{status_pill}"
      f'<div style="font-size:9px;color:#38bdf8;margin-top:1px;">xP:'
      f" {p['xp']}</div>"
      "</div>"
  )


# טאב 1: מגרש חי וחילופי הרכב-ספסל
with tab_squad:
  st.subheader(f"📋 ההרכב הפותח למחזור {next_gw}")
  st.caption(
      f"מערך: **{pos_counts[2]}-{pos_counts[3]}-{pos_counts[4]}** | תחזית:"
      f" **{starting_xp_total:.1f}** נקודות צפויות [אדום = פצוע | צהוב = בספק]"
  )

  fwd_h = "".join(
      build_card(p) for p in starters if p["pos_code"] == 4
  )  #[span_35](start_span)[span_35](end_span)
  mid_h = "".join(
      build_card(p) for p in starters if p["pos_code"] == 3
  )  #[span_36](start_span)[span_36](end_span)
  def_h = "".join(
      build_card(p) for p in starters if p["pos_code"] == 2
  )  #[span_37](start_span)[span_37](end_span)
  gk_h = "".join(
      build_card(p) for p in starters if p["pos_code"] == 1
  )  #[span_38](start_span)[span_38](end_span)

  st.markdown(
      '<div class="pitch"><div class="pitch-row">'  #[span_39](start_span)[span_39](end_span)
      f"{fwd_h}</div><div"  #[span_40](start_span)[span_40](end_span)
      f' class="pitch-row">{mid_h}</div><div'  #[span_41](start_span)[span_41](end_span)
      f' class="pitch-row">{def_h}</div><div'  #[span_42](start_span)[span_42](end_span)
      f' class="pitch-row">{gk_h}</div></div>',  #[span_43](start_span)[span_43](end_span)
      unsafe_allow_html=True,
  )

  st.subheader("🪑 ספסל")
  bench_h = "".join(build_card(p, is_bench=True) for p in bench)
  st.markdown(
      '<div style="display:flex;justify-content:center;gap:8px;">'
      f"{bench_h}</div>",
      unsafe_allow_html=True,
  )

  st.write("---")
  st.markdown("### 🔄 חילוף מהיר בין שחקן הרכב לשחקן ספסל")
  st.caption(
      "בחר שחקן להורדה ושחקן להעלאה. הניקוד, תחזית ה-xP וציון הסגל יתעדכנו"
      " מיידית:"
  )

  starters_map = {
      p["id"]: (
          f"[{p['total_points']} נק׳] {p['name']} ({p['pos']} | {p['team']}) —"
          f" {p['start_prob']}% פותח"
      )
      for p in starters
  }
  bench_map = {
      p["id"]: (
          f"[{p['total_points']} נק׳] {p['name']} ({p['pos']} | {p['team']}) —"
          f" {p['start_prob']}% פותח"
      )
      for p in bench
  }

  cs1, cs2, cs3 = st.columns([1.5, 1.5, 1])
  with cs1:
    s_out_id = st.selectbox(
        "שחקן הרכב שיורד לספסל:",
        options=list(starters_map.keys()),
        format_func=lambda x: starters_map[x],
    )
  with cs2:
    b_in_id = st.selectbox(
        "שחקן ספסל שעולה להרכב:",
        options=list(bench_map.keys()),
        format_func=lambda x: bench_map[x],
    )
  with cs3:
    st.write("")
    st.write("")
    if st.button("בצע חילוף בהרכב 🔁", use_container_width=True):
      sim_pos = [
          p["pos_code"] for p in starters if p["id"] != s_out_id
      ] + [all_players[b_in_id]["pos_code"]]
      if (
          sim_pos.count(1) != 1
          or not (3 <= sim_pos.count(2) <= 5)
          or not (1 <= sim_pos.count(4) <= 3)
      ):
        st.error(
            "חילוף נדחה: המערך שיווצר אינו חוקי (חובה שוער 1, 3–5 מגנים ולפחות"
            " חלוץ 1)!"
        )
      else:
        p_out = next(
            p for p in st.session_state.user_squad if p["element"] == s_out_id
        )
        p_in = next(
            p for p in st.session_state.user_squad if p["element"] == b_in_id
        )
        p_out["position"], p_in["position"] = (
            p_in["position"],
            p_out["position"],
        )
        st.success("החילוף בוצע בהצלחה!")
        st.rerun()

# טאב 2: עדכון חילוף מהיר בשוק
with tab_manual:
  st.subheader("🔄 עדכון חילוף בשוק (ממוין לפי נקודות ומסונן עמדה)")
  all_current = starters + bench
  current_ids = [p["id"] for p in all_current]

  def is_risky(p):
    return (
        p["status"] != "a"
        or p["chance"] < 100
        or p["next_fdr"] >= 4
        or p["form"] < 2.5
        or p["tag"] == "OVERPERFORMING_TRAP"
    )

  risky_out = sorted(
      [p for p in all_current if is_risky(p)],
      key=lambda x: x["total_points"],
      reverse=True,
  )
  safe_out = sorted(
      [p for p in all_current if not is_risky(p)],
      key=lambda x: x["total_points"],
      reverse=True,
  )
  sorted_out_squad = risky_out + safe_out

  def format_out(pid):
    p = all_players[pid]
    badge = "⚠️ [מומלץ למכור] " if is_risky(p) else ""
    return (
        f"{badge}[{p['total_points']} נק׳] {p['name']} ({p['team']} -"
        f" {p['pos']}) | {p['start_prob']}% פותח | £{p['cost']}m | xP:"
        f" {p['xp']}"
    )

  c_out, c_in = st.columns(2)

  with c_out:
    st.markdown("#### 🔴 1. בחר שחקן למכירה (OUT)")
    sel_out = st.selectbox(
        "שחקן יוצא:",
        options=[p["id"] for p in sorted_out_squad],
        format_func=format_out,
        key="market_out_select",
    )
    p_out = all_players[sel_out]
    max_budget = p_out["cost"] + st.session_state.user_bank

  with c_in:
    st.markdown(f"#### 🟢 2. בחר שחקן לרכש בעמדת {p_out['pos']} (IN)")
    search_kw = (
        st.text_input(
            "חיפוש חופשי (הקלד שם או קבוצה):",
            placeholder="למשל: Palmer, Saka, Konsa...",
        )
        .strip()
        .lower()
    )

    avail = [
        p
        for p in all_players.values()
        if p["pos_code"] == p_out["pos_code"]
        and p["id"] not in current_ids
        and p["status"] == "a"
        and p["cost"] <= max_budget
    ]
    if search_kw:
      avail = [
          p
          for p in avail
          if search_kw in p["name"].lower() or search_kw in p["team"].lower()
      ]

    top_recs_ids = [
        r["id"]
        for r in sorted(avail, key=lambda x: x["score"], reverse=True)[:3]
    ]
    recs_list = sorted(
        [p for p in avail if p["id"] in top_recs_ids],
        key=lambda x: x["total_points"],
        reverse=True,
    )
    others_list = sorted(
        [p for p in avail if p["id"] not in top_recs_ids],
        key=lambda x: x["total_points"],
        reverse=True,
    )
    final_in = recs_list + others_list

    def format_in(pid):
      p = all_players[pid]
      tag = "⭐ [מומלץ] " if pid in top_recs_ids else ""
      return (
          f"{tag}[{p['total_points']} נק׳] {p['name']} ({p['team']}) |"
          f" £{p['cost']}m | xP: {p['xp']} | {p['start_prob']}% פותח"
      )

    if final_in:
      sel_in = st.selectbox(
          "שחקן נכנס (מסונן לתקציב ולעמדה):",
          options=[p["id"] for p in final_in],
          format_func=format_in,
          key="market_in_select",
      )
      p_in = all_players[sel_in]
    else:
      st.warning("לא נמצאו מועמדים תואמים בתקציב זה.")
      p_in = None

  if p_in:
    st.markdown('<div class="compare-card">', unsafe_allow_html=True)
    st.markdown("#### ⚖️ השוואת חילוף ראש-בראש")
    cp1, cp2, cp3 = st.columns([1.2, 1.2, 1])
    with cp1:
      st.markdown(f"**🔴 שחקן יוצא: {p_out['name']}**")
      st.markdown(
          '<div class="stat-pill"><span>סך נקודות'
          f' העונה:</span><b>{p_out["total_points"]}</b></div>',
          unsafe_allow_html=True,
      )
      st.markdown(
          '<div class="stat-pill"><span>סבירות'
          f' לפתוח:</span><b>{p_out["start_prob"]}%</b></div>',
          unsafe_allow_html=True,
      )
      st.markdown(
          '<div class="stat-pill"><span>תוחלת נקודות'
          f' (xP):</span><b>{p_out["xp"]}</b></div>',
          unsafe_allow_html=True,
      )
    with cp2:
      st.markdown(f"**🟢 שחקן נכנס: {p_in['name']}**")
      st.markdown(
          '<div class="stat-pill"><span>סך נקודות'
          f' העונה:</span><b>{p_in["total_points"]}</b></div>',
          unsafe_allow_html=True,
      )
      st.markdown(
          '<div class="stat-pill"><span>סבירות'
          f' לפתוח:</span><b>{p_in["start_prob"]}%</b></div>',
          unsafe_allow_html=True,
      )
      st.markdown(
          '<div class="stat-pill"><span>תוחלת נקודות'
          f' (xP):</span><b>{p_in["xp"]}</b></div>',
          unsafe_allow_html=True,
      )
    with cp3:
      delta_xp = round(p_in["xp"] - p_out["xp"], 1)
      new_bank = round(
          st.session_state.user_bank + p_out["cost"] - p_in["cost"], 1
      )
      st.markdown(
          '<div class="stat-pill"><span>תוספת xP:</span><b'
          f' style="color:#10b981;">{delta_xp:+} נק׳</b></div>',
          unsafe_allow_html=True,
      )
      st.markdown(
          '<div class="stat-pill"><span>יתרה'
          f" מעודכנת:</span><b>£{new_bank:.1f}m</b></div>",
          unsafe_allow_html=True,
      )
      if st.button("אשר ובצע חילוף בסגל 🔁", use_container_width=True):
        for p in st.session_state.user_squad:
          if p["element"] == p_out["id"]:
            p["element"] = p_in["id"]
            break
        st.session_state.user_bank = new_bank
        st.session_state.transfers_log.append(f"{p_out['name']} ⬅️ {p_in['name']}")
        st.success(f"החילוף בוצע בהצלחה! {p_in['name']} צורף לסגל.")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

  if st.session_state.transfers_log:
    st.info(
        f"חילופים שבוצעו בריצה זו: {', '.join(st.session_state.transfers_log)}"
    )
    if st.button("בטל חילופים ואפס לסגל המקורי ↩️"):
      st.session_state.user_squad = [dict(p) for p in raw_picks]
      st.session_state.user_bank = initial_bank
      st.session_state.transfers_log = []
      st.rerun()

# טאב 3: מדד עוצמה וחסרונות הסגל
with tab_projection:
  st.subheader(f"📊 ניתוח עומק: ציון סגל ופירוט החסרונות (GW {next_gw})")
  c_rate1, c_rate2 = st.columns([1, 2])
  with c_rate1:
    st.markdown(
        '<div style="background:#111a28;border:1px solid'
        " #1e2e46;border-radius:12px;padding:16px;text-align:center;color:#94a3b8;font-size:13px;\">ציון"
        " סגל מכויל (מחושב מול בנצ'מרק)<div"
        f' style="font-size:36px;font-weight:bold;color:{rating_color};margin:8px'
        f' 0;">{squad_rating} <span'
        ' style="font-size:16px;color:#64748b;">/ 100</span></div><div'
        f' style="font-size:12px;font-weight:bold;color:{rating_color};">{rating_status}</div></div>',
        unsafe_allow_html=True,
    )
  with c_rate2:
    st.markdown(
        '<div style="background:#111a28;border:1px solid'
        ' #1e2e46;border-radius:12px;padding:16px;"><div'
        ' style="color:#94a3b8;font-size:13px;margin-bottom:6px;">תחזית נקודות'
        ' למחזור הקרוב (11 פותחים)</div><div'
        ' style="font-size:26px;font-weight:bold;color:#10b981;margin-bottom:8px;">'
        f"{starting_xp_total:.1f} נקודות צפויות</div>"
        '<div style="font-size:12px;color:#cbd5e1;line-height:1.6;">•'
        " <b>התקפה וקישור:</b> מייצרים"
        f" כ-<b>{sum(p['xp'] for p in starters if p['pos_code'] in [3,4]):.1f}</b>"
        " נקודות צפויות.<br>• <b>הגנה ושוער:</b> מייצרים"
        f" כ-<b>{sum(p['xp'] for p in starters if p['pos_code'] in [1,2]):.1f}</b>"
        " נקודות צפויות.<br>• <b>בונוס קפטן:</b> תוספת של"
        f" <b>+{next((p['xp'] for p in starters if p.get('is_cap')), 5.0):.1f}</b>"
        " נקודות על סרט הקפטן.</div></div>",
        unsafe_allow_html=True,
    )

  st.write("")
  st.markdown(
      "#### ⚠️ חסרונות הסגל שהורידו נקודות מהציון"
      f" ({len(squad_flaws)} מוקדים אותרו)"
  )
  if squad_flaws:
    for f in squad_flaws:
      st.markdown(
          f'<div class="flaw-card"><div><b>[{f["type"]}]:</b>'
          f' {f["text"]}</div><div class="penalty-tag">{f["penalty"]}'
          " נק׳</div></div>",
          unsafe_allow_html=True,
      )
  else:
    st.success("לא זוהו חסרונות בסגל הנוכחי! הסגל מאוזן ויציב לחלוטין.")

  st.write("")
  st.markdown("#### 📋 פירוט שחקני ההרכב הפותח")
  xp_rows = []
  for p in starters:
    is_c = " 👑 (קפטן)" if p.get("is_cap") else ""  #[span_44](start_span)[span_44](end_span)
    mult = 2 if p.get("is_cap") else 1  #[span_45](start_span)[span_45](end_span)
    xp_rows.append({
        "שחקן": f"{p['name']}{is_c}",  #[span_46](start_span)[span_46](end_span)
        "עמדה": p["pos"],  #[span_47](start_span)[span_47](end_span)
        "קבוצה": p["team"],  #[span_48](start_span)[span_48](end_span)
        "סך נקודות העונה": p["total_points"],
        "סבירות פתיחה": f"{p['start_prob']}%",
        "משחק קרוב": p["next_match"],  #[span_49](start_span)[span_49](end_span)
        "דרגת קושי": f"FDR {p['next_fdr']}",  #[span_50](start_span)[span_50](end_span)
        "xGI ל-90 דק׳": p["xgi_p90"],
        "נקודות צפויות": round(p["xp"] * mult, 1),  #[span_51](start_span)[span_51](end_span)
    })
  st.dataframe(
      pd.DataFrame(xp_rows).sort_values(
          by="סך נקודות העונה", ascending=False
      ),
      use_container_width=True,
      hide_index=True,
  )

# טאב 4: רדאר רכש עילית
with tab_targets:
  st.subheader(
      f"🌟 יעדי רכש מובילים למחזור {next_gw} (Top 50K Algorithm)"
  )  #[span_52](start_span)[span_52](end_span)
  sub_fwd, sub_mid, sub_def, sub_gk, sub_cap = st.tabs([
      "⚡ חלוצים (FWD)",
      "🎯 קשרים (MID)",
      "🛡️ הגנה (DEF)",
      "🧤 שוערים (GK)",
      "👑 קפטן מגן מול חרב",
  ])

  def render_targets(pos_code, count=6):
    targets = sorted(
        [
            p
            for p in all_players.values()
            if p["pos_code"] == pos_code and p["status"] == "a"
        ],
        key=lambda x: x["score"],
        reverse=True,
    )[:count]
    for i, p in enumerate(targets):
      tier = "tier-1" if i < 2 else ("tier-2" if i < 4 else "tier-3")
      tag_badge = (
          '<span class="badge badge-buylow">🔥 קנייה בשפל</span>'
          if p["tag"] == "BUY_LOW"
          else (
              '<span class="badge badge-trap">⚠️ מעל המצופה</span>'
              if p["tag"] == "OVERPERFORMING_TRAP"
              else ""
          )
      )
      st.markdown(
          '<div style="background:#111a28;border:1px solid'
          ' #1e2e46;border-radius:10px;padding:12px;margin-bottom:10px;"><div'
          ' style="display:flex;justify-content:space-between;align-items:center;"><span'
          ' style="font-weight:bold;font-size:15px;color:#f8fafc;">['
          f"{p['total_points']} נק׳] {p['name']} <span class=\"ltr-box\""
          f' style="font-size:12px;color:#94a3b8;">({p["team"]})</span>'
          f' {tag_badge}</span><span class="ltr-box"'
          ' style="font-size:14px;font-weight:bold;color:#38bdf8;">£'
          f"{p['cost']}m | ציון: {p['score']}</span></div><div"
          ' style="margin:6px 0;font-size:12px;color:#cbd5e1;">💡'
          f' <b>ניתוח מדעי:</b> {p["reason"]}</div><div'
          ' style="display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#94a3b8;border-top:1px'
          ' solid #1e293b;padding-top:4px;"><span>סבירות פתיחה:'
          f" <b>{p['start_prob']}%</b> | xP: <b>{p['xp']}</b> | כושר:"
          f" <b>{p['form']}</b></span><div>משחק הבא: <span class=\"badge"
          f' fdr-{p["next_fdr"]}"><span'
          f' class="ltr-box">{p["next_match"]}</span></span></div></div></div>',
          unsafe_allow_html=True,
      )

  with sub_fwd:
    render_targets(4)
  with sub_mid:
    render_targets(3)
  with sub_def:
    render_targets(2)
  with sub_gk:
    render_targets(1, 4)

  with sub_cap:
    premiums = sorted(
        [
            p
            for p in all_players.values()
            if p["cost"] >= 7.5 and p["status"] == "a"
        ],
        key=lambda x: x["score"],
        reverse=True,
    )
    shield = premiums[0]
    diff_pool = [p for p in premiums if p["selected_by"] < 18]
    sword = diff_pool[0] if diff_pool else premiums[1]

    ca, cb = st.columns(2)
    with ca:
      st.markdown(
          '<div style="background:#0f2a24;border:1px solid'
          ' #059669;padding:12px;border-radius:10px;"><span'
          ' style="background:#059669;color:white;padding:2px'
          ' 6px;border-radius:3px;font-size:9px;font-weight:bold;">🛡️ קפטן מגן'
          ' (Shield)</span><h4 style="margin:6px 0;color:#ecfdf5;">['
          f"{shield['total_points']} נק׳] {shield['name']} <span"
          f' class="ltr-box">({shield["team"]})</span></h4><p'
          ' style="font-size:11px;color:#a7f3d0;margin:0;line-height:1.5;">בעלות:'
          ' <span class="ltr-box"><b>'
          f"{shield['selected_by']}%</b></span> | סבירות פתיחה:"
          f" <b>{shield['start_prob']}%</b><br>משחק הבא: <span"
          f' class="ltr-box"><b>{shield["next_match"]}</b></span> | xP קרוב:'
          f" <b>{shield['xp']}</b><br>💡 {shield['reason']}</p></div>",
          unsafe_allow_html=True,
      )
    with cb:
      st.markdown(
          '<div style="background:#2a1e0f;border:1px solid'
          ' #d97706;padding:12px;border-radius:10px;"><span'
          ' style="background:#d97706;color:white;padding:2px'
          ' 6px;border-radius:3px;font-size:9px;font-weight:bold;">⚔️ קפטן'
          ' דיפרנשיאל (Sword)</span><h4 style="margin:6px'
          f" 0;color:#fffbeb;\">[{sword['total_points']} נק׳] {sword['name']}"
          f' <span class="ltr-box">({sword["team"]})</span></h4><p'
          ' style="font-size:11px;color:#fde68a;margin:0;line-height:1.5;">בעלות:'
          ' <span class="ltr-box"><b>'
          f"{sword['selected_by']}% בלבד</b></span> | סבירות פתיחה:"
          f" <b>{sword['start_prob']}%</b><br>משחק הבא: <span"
          f' class="ltr-box"><b>{sword["next_match"]}</b></span> | xP קרוב:'
          f" <b>{sword['xp']}</b><br>💡 {sword['reason']}</p></div>",
          unsafe_allow_html=True,
      )

# טאב 5: הצעות חילוף מותאמות לתקציב
with tab_transfer:
  st.subheader(
      "🎯 3 הצעות חילוף אופציונליות המותאמות לתקציב שלך"
  )  #[span_53](start_span)[span_53](end_span)
  all_my = starters + bench
  my_ids = [x["id"] for x in all_my]

  def find_best_in(pos_code, max_budget):
    cands = [
        p
        for p in all_players.values()
        if p["id"] not in my_ids
        and p["pos_code"] == pos_code
        and p["cost"] <= max_budget
        and p["status"] == "a"
    ]
    return max(cands, key=lambda x: x["score"]) if cands else None

  out_def = min(
      [p for p in all_my if p["pos_code"] == 2],
      key=lambda x: (
          x["score"] if x["status"] == "a" and x["chance"] == 100 else -20
      ),
  )
  out_mid = min(
      [p for p in all_my if p["pos_code"] == 3],
      key=lambda x: (
          x["score"] if x["status"] == "a" and x["chance"] == 100 else -15
      ),
  )
  fwd_pool = [
      p for p in all_my if p["pos_code"] == 4 and "Haaland" not in p["name"]
  ]
  out_fwd = (
      min(fwd_pool, key=lambda x: x["score"])
      if fwd_pool
      else [p for p in all_my if p["pos_code"] == 4][0]
  )

  scenarios = [
      {
          "title": "אופציה 1: שיפוץ הגנתי / החלפת מוקד קושי",
          "tag": "🛡️ עדיפות הגנתית",
          "out": out_def,
          "in": find_best_in(
              2, out_def["cost"] + st.session_state.user_bank
          ),
      },
      {
          "title": "אופציה 2: שדרוג מנוע הקישור וייצור מצבים",
          "tag": "🎯 תוספת איום התקפי",
          "out": out_mid,
          "in": find_best_in(
              3, out_mid["cost"] + st.session_state.user_bank
          ),
      },
      {
          "title": "אופציה 3: רענון חוד ההתקפה",
          "tag": "⚡ חוד ההתקפה",
          "out": out_fwd,
          "in": find_best_in(
              4, out_fwd["cost"] + st.session_state.user_bank
          ),
      },
  ]

  for sc in scenarios:
    p_o, p_i = sc["out"], sc["in"]
    if not p_i:
      continue
    rem_b = (p_o["cost"] + st.session_state.user_bank) - p_i["cost"]
    delta_xp = round(p_i["xp"] - p_o["xp"], 1)
    rec_text = (
        "🔥 מומלץ מאוד לביצוע" if delta_xp >= 2.0 else "⚖️ שדרוג שקול"
    )

    st.markdown(
        '<div class="compare-card"><div'
        ' style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px'
        ' solid #1e2e46;padding-bottom:8px;margin-bottom:10px;"><div><span'
        f' style="font-weight:bold;font-size:16px;color:#f8fafc;">{sc["title"]}</span>'
        f' <span class="badge"'
        f' style="background:#1e293b;color:#94a3b8;">{sc["tag"]}</span></div><div'
        f' style="font-size:13px;font-weight:bold;color:#10b981;">תוספת תוחלת:'
        f' +{delta_xp} xP ({rec_text})</div></div><div'
        ' style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;"><div'
        ' style="flex:1;min-width:240px;background:#231114;border-right:4px'
        ' solid #ef4444;border-radius:8px;padding:10px;"><div'
        ' style="font-size:11px;color:#fca5a5;font-weight:bold;">🔴 יוצא:'
        f' {p_o["name"]} ({p_o["team"]})</div><div'
        ' style="font-size:12px;color:#cbd5e1;">סך נקודות:'
        f" <b>{p_o['total_points']}</b> | סבירות פתיחה:"
        f" <b>{p_o['start_prob']}%</b> | xP: {p_o['xp']}</div></div><div"
        ' style="flex:1;min-width:240px;background:#0c2417;border-right:4px'
        ' solid #10b981;border-radius:8px;padding:10px;"><div'
        ' style="font-size:11px;color:#6ee7b7;font-weight:bold;">🟢 נכנס:'
        f' {p_i["name"]} ({p_i["team"]})</div><div'
        ' style="font-size:12px;color:#cbd5e1;">סך נקודות:'
        f" <b>{p_i['total_points']}</b> | סבירות פתיחה:"
        f" <b>{p_i['start_prob']}%</b> (בנק:"
        f" <b>£{rem_b:.1f}m</b>) | xP:"
        f' {p_i["xp"]}</div></div></div><div'
        ' style="font-size:12px;color:#94a3b8;margin-top:8px;">💡'
        f' <b>נימוק:</b> {p_i["reason"]}</div></div>',
        unsafe_allow_html=True,
    )

# טאב 6: רמזור בריאות הסגל
with tab_health:
  st.subheader("🚦 רמזור בריאות ומוקשי הרכב")  #[span_54](start_span)[span_54](end_span)
  reds = [
      p for p in all_my if p["status"] != "a" or p["chance"] < 100
  ]  #[span_55](start_span)[span_55](end_span)
  yellows = [
      p
      for p in all_my
      if p["status"] == "a"
      and p["chance"] == 100
      and (p["avg_fdr"] > 2.8 or p["form"] < 2.5)
  ]

  st.markdown(f"#### 🔴 מוקדי חירום בסגל ({len(reds)})")  #[span_56](start_span)[span_56](end_span)
  if reds:
    for p in reds:
      st.markdown(
          '<div class="health-box health-red"><b>['
          f"{p['total_points']} נק׳] {p['name']} <span"
          f' class="ltr-box">({p["team"]})</span></b> — כשירות רפואית:'
          f" {p['chance']}% | סבירות לפתוח: <b>{p['start_prob']}%</b> | לוח:"
          f' <span class="ltr-box">{p["fixtures"]}</span></div>',
          unsafe_allow_html=True,
      )
  else:
    st.success("אין פציעות או השעיות ידועות בסגל!")  #[span_57](start_span)[span_57](end_span)

  st.markdown(f"#### 🟡 תחת מעקב / לוח קשה ({len(yellows)})")  #[span_58](start_span)[span_58](end_span)
  for p in yellows:
    st.markdown(
        '<div class="health-box health-yellow"><b>['
        f"{p['total_points']} נק׳] {p['name']} <span"
        f' class="ltr-box">({p["team"]})</span></b> — סבירות פתיחה:'
        f" <b>{p['start_prob']}%</b> | כושר: {p['form']} | לוח: <span"
        f' class="ltr-box">{p["fixtures"]}</span> (FDR ממוצע:'
        f" {p['avg_fdr']})</div>",
        unsafe_allow_html=True,
    )
