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

# --- עיצוב CSS מותאם אישית: RTL מלא, כרטיסי מובייל וכרטיסי המלצה חכמים ---
st.markdown(
    """
<style>
.main {
    direction: rtl;
    text-align: right;
    background-color: #080d1a;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
div[data-testid="stMarkdownContainer"] p {
    direction: rtl;
    text-align: right;
}
.ltr-box {
    direction: ltr !important;
    display: inline-block;
    unicode-bidi: embed;
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
.p-name { font-weight: bold; font-size: 11px; color: #f8fafc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.p-team { font-size: 9px; color: #94a3b8; margin: 1px 0; }
.p-fxt { font-size: 9px; font-weight: bold; padding: 1px 4px; border-radius: 3px; display: inline-block; }

.target-card {
    background: #111a28;
    border: 1px solid #1e2e46;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 12px;
}
.tier-1 { border-right: 5px solid #10b981; }
.tier-2 { border-right: 5px solid #38bdf8; }
.tier-3 { border-right: 5px solid #f59e0b; }

.rec-pill {
    background: #0d1e19;
    border: 1px solid #059669;
    border-radius: 8px;
    padding: 8px 10px;
    margin-bottom: 6px;
}

.flaw-card {
    background: #231215;
    border-right: 4px solid #ef4444;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 13px;
    color: #fecaca;
}

.transfer-scenario-card {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 16px;
}

.badge { font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; display: inline-block; }
.badge-buylow { background: #064e3b; color: #6ee7b7; border: 1px solid #059669; }
.badge-trap { background: #450a0a; color: #fca5a5; border: 1px solid #dc2626; }
.fdr-2 { background: #15803d; color: #fff; }
.fdr-3 { background: #475569; color: #fff; }
.fdr-4 { background: #b91c1c; color: #fff; }
.fdr-5 { background: #7f1d1d; color: #fff; }

.health-box { padding: 12px; border-radius: 8px; margin-bottom: 8px; }
.health-green { background: #0c2417; border-right: 4px solid #10b981; }
.health-yellow { background: #26200d; border-right: 4px solid #f59e0b; }
.health-red { background: #2b1114; border-right: 4px solid #ef4444; }
</style>
""",
    unsafe_allow_html=True,
)


# --- 1. משיכת נתוני הליגה וחישוב מודל עילית (Top 50K Algorithm) ---
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
    weighted_fdr = 0.0
    for i, fdr in enumerate(fdr_list[:3]):
      weighted_fdr += (5.3 - fdr) * weights[i]
    avg_fdr = sum(fdr_list) / len(fdr_list) if fdr_list else 3.0

    mins = el.get("minutes", 0)
    actual_gi = el.get("goals_scored", 0) + el.get("assists", 0)
    expected_gi = float(el.get("expected_goal_involvements", 0.0))
    form = float(el.get("form", 0.0))
    cost = el["now_cost"] / 10
    threat = float(el.get("threat", 0.0))

    if mins >= 60:
      xgi_per_90 = (expected_gi / mins) * 90
    else:
      xgi_per_90 = expected_gi

    tag_status = None
    if expected_gi >= 1.2 and actual_gi <= 1:
      tag_status = "BUY_LOW"
      buy_low_bonus = 1.0
    elif actual_gi >= 3 and expected_gi < 0.9:
      tag_status = "OVERPERFORMING_TRAP"
      buy_low_bonus = -0.8
    else:
      buy_low_bonus = 0.0

    mins_per_gw = mins / max(1, (next_gw - 1))
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

    base_appearance = 2.0 if el["status"] == "a" else 0.5
    next_match_fdr = fdr_list[0] if fdr_list else 3
    clean_sheet_probs = {2: 0.45, 3: 0.28, 4: 0.15, 5: 0.08}
    cs_prob = clean_sheet_probs.get(next_match_fdr, 0.22)

    if el["element_type"] in [1, 2]:
      predicted_xp = base_appearance + (cs_prob * 4.0) + (xgi_per_90 * 0.4 * 5.0)
    elif el["element_type"] == 3:
      predicted_xp = base_appearance + (cs_prob * 1.0) + (xgi_per_90 * 5.5)
    else:
      predicted_xp = base_appearance + (xgi_per_90 * 5.2)

    if form >= 5.0:
      predicted_xp += 0.6
    predicted_xp = round(max(1.0, predicted_xp), 1)

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
      if team_short in elite_defenses:
        reason = f"עוגן הגנתי מוביל מקבוצת צמרת עם סיכוי רשת נקייה גבוה."
      else:
        reason = "מגן פעיל התקפית במחיר משתלם ובלוח נוח."
    else:
      if form >= 5.0:
        reason = "כושר כיבוש שיא עם מעורבות ישירה בהתקפה."
      else:
        reason = "נתוני איום שערים יציבים לקראת לוח משחקים ירוק."

    processed[el_id] = {
        "id": el_id,
        "name": el["web_name"],
        "team": team_short,
        "pos": pos_map[el["element_type"]],
        "pos_code": el["element_type"],
        "cost": cost,
        "form": form,
        "xgi": expected_gi,
        "xgi_p90": round(xgi_per_90, 2),
        "selected_by": float(el["selected_by_percent"]),
        "goals_assists": actual_gi,
        "score": round(score, 2),
        "xp": predicted_xp,
        "tag": tag_status,
        "reason": reason,
        "status": el["status"],
        "chance": (
            el["chance_of_playing_next_round"]
            if el["chance_of_playing_next_round"] is not None
            else 100
        ),
        "next_match": upcoming[0] if upcoming else "—",
        "next_fdr": next_match_fdr,
        "avg_fdr": round(avg_fdr, 2),
        "fixtures": " | ".join(upcoming),
    }

  return processed, next_gw


all_players, next_gw = fetch_league_data()

# הגדרת מספר קבוצה בסרגל הצד (מינימלי)
team_id = st.sidebar.text_input("מספר קבוצה (Team ID):", value="139103")


# --- 2. משיכת הקבוצה משרתי ה-FPL ---
@st.cache_data(ttl=300)
def fetch_user_team(t_id, gw):
  try:
    last_gw = max(1, gw - 1)
    picks_url = (
        f"https://fantasy.premierleague.com/api/entry/{t_id}/event/{last_gw}/picks/"
    )
    entry_url = f"https://fantasy.premierleague.com/api/entry/{t_id}/"

    picks_res = requests.get(picks_url).json()
    entry_res = requests.get(entry_url).json()

    is_fh = picks_res.get("active_chip") == "free_hit"
    if is_fh and last_gw > 1:
      base_gw = last_gw - 1
      base_url = (
          f"https://fantasy.premierleague.com/api/entry/{t_id}/event/{base_gw}/picks/"
      )
      picks_res = requests.get(base_url).json()

    bank = picks_res.get("entry_history", {}).get("bank", 0) / 10
    picks = picks_res.get("picks", [])
    team_name = entry_res.get("name", "Itay7900")
    rank = entry_res.get("summary_overall_rank", "—")
    return picks, bank, team_name, rank
  except Exception:
    return None, 0.0, None, None


raw_picks, initial_bank, my_team_name, my_rank = fetch_user_team(
    team_id, next_gw
)

if not raw_picks:
  st.warning(
      "לא ניתן למשוך את נתוני הקבוצה. אנא ודא שמספר הקבוצה (Team ID) תקין."
  )
  st.stop()

base_squad_ids = [p["element"] for p in raw_picks]
all_player_names = {
    f"{p['name']} ({p['team']}) - £{p['cost']}m": pid
    for pid, p in all_players.items()
}

# --- 3. סנכרון חילופים ידניים מתוך Session State ---
transfers_applied = []
bank_balance = initial_bank
my_picks = [dict(p) for p in raw_picks]

num_active_transfers = st.session_state.get("sel_num_transfers", 0)
for idx in range(num_active_transfers):
  sel_out = st.session_state.get(f"transfer_out_{idx}", "ללא שינוי")
  sel_in = st.session_state.get(f"transfer_in_{idx}", "בחר שחקן...")

  if sel_out != "ללא שינוי" and sel_in != "בחר שחקן...":
    try:
      out_id = next(
          pid
          for pid in base_squad_ids
          if f"{all_players[pid]['name']} ({all_players[pid]['team']}) -"
          f" £{all_players[pid]['cost']}m"
          == sel_out
      )
      in_id = all_player_names[sel_in]
      transfers_applied.append((out_id, in_id))
    except Exception:
      pass

for out_id, in_id in transfers_applied:
  for p in my_picks:
    if p["element"] == out_id:
      bank_balance += all_players[out_id]["cost"] - all_players[in_id]["cost"]
      p["element"] = in_id
      break

starters = []
bench = []
for p in my_picks:
  pid = p["element"]
  p_info = all_players.get(pid)
  if p_info:
    item = {**p_info, "is_cap": p["is_captain"], "is_vc": p["is_vice_captain"]}
    if p["position"] <= 11:
      starters.append(item)
    else:
      bench.append(item)

# חישוב נקודות צפויות
starting_xp_total = 0.0
for p in starters:
  mult = 2 if p.get("is_cap") else 1
  starting_xp_total += p["xp"] * mult

# --- מנוע כיול ציון ריאלי וזיהוי חסרונות הסגל ---
base_rating = 90.0
squad_flaws = []

# 1. פציעות והשעיות בהרכב
for p in starters:
  if p["status"] != "a" or p["chance"] < 100:
    penalty = 8 if p["chance"] == 0 else 5
    base_rating -= penalty
    squad_flaws.append({
        "type": "פציעה/כשירות בהרכב",
        "severity": "high",
        "text": (
            f"<b>{p['name']} ({p['team']})</b> פותח בהרכב אך מוגדר עם"
            f" {p['chance']}% סיכויי כשירות בלבד (סיכון ל-0 נקודות)."
        ),
    })

# 2. פציעות והשבתות בספסל
for p in bench:
  if p["status"] != "a" or p["chance"] < 100:
    base_rating -= 4
    squad_flaws.append({
        "type": "ספסל מושבת",
        "severity": "medium",
        "text": (
            f"<b>{p['name']} ({p['team']})</b> בספסל פצוע/מושבת ({p['chance']}%),"
            " מה שמבטל גיבוי אוטומטי במקרה של היעדרות בהרכב."
        ),
    })

# 3. משחקים קשים לשחקני הגנה בהרכב (FDR 4-5)
for p in starters:
  if p["pos_code"] in [1, 2] and p["next_fdr"] >= 4:
    base_rating -= 4.5
    squad_flaws.append({
        "type": "משחק הגנתי קשה",
        "severity": "high",
        "text": (
            f"<b>{p['name']} ({p['pos']})</b> פוגש יריבה קשה"
            f" ({p['next_match']}, FDR {p['next_fdr']}) עם סיכוי נמוך מאוד"
            " לרשת נקייה (Clean Sheet)."
        ),
    })

# 4. שחקני התקפה עם משחקים קשים במיוחד (FDR 5)
for p in starters:
  if p["pos_code"] in [3, 4] and p["next_fdr"] >= 5:
    base_rating -= 3.0
    squad_flaws.append({
        "type": "משחק התקפי קשה",
        "severity": "medium",
        "text": (
            f"<b>{p['name']} ({p['team']})</b> מתמודד מול הגנת ברזל"
            f" ({p['next_match']}), מה שמגביל את תקרת הנקודות הצפויה."
        ),
    })

# 5. שחקנים בכושר ירוד (Form < 2.8) בהרכב
for p in starters:
  if p["status"] == "a" and p["form"] < 2.8 and p["pos_code"] in [3, 4]:
    base_rating -= 2.5
    squad_flaws.append({
        "type": "כושר הבקעה נמוך",
        "severity": "low",
        "text": (
            f"<b>{p['name']}</b> בכושר מדאיג (Form {p['form']}) ותפוקת מעורבות"
            " שערים נמוכה במחזורים האחרונים."
        ),
    })

# 6. מלכודת שחקן שכבש מעל המצופה (Trap)
for p in starters:
  if p["tag"] == "OVERPERFORMING_TRAP":
    base_rating -= 2.0
    squad_flaws.append({
        "type": "סכנת דעיכה לממוצע",
        "severity": "low",
        "text": (
            f"<b>{p['name']}</b> מעל המצופה סטטיסטית (כבש ללא xGI תומך) - סיכון"
            " לנפילת תפוקה במחזורים הקרובים."
        ),
    })

# ציון סופי מכויל
squad_rating = max(42, min(94, int(base_rating)))

if squad_rating >= 83:
  rating_status = "🌟 סגל עילית (Top 50K Ready)"
  rating_color = "#10b981"
elif squad_rating >= 72:
  rating_status = "🟢 סגל תחרותי וחזק (עם נקודות תורפה בודדות)"
  rating_color = "#38bdf8"
elif squad_rating >= 60:
  rating_status = "🟡 סגל סביר עם מוקדי סיכון הדורשים טיפול"
  rating_color = "#f59e0b"
else:
  rating_status = "🔴 סגל במצב חירום (דורש ריענון מיידי / צ'יפ)"
  rating_color = "#ef4444"

# --- שורת מדדים ראשית ---
st.title(f"⚽ FPL Command Center | {my_team_name}")
st.caption(
    f"מנוע אנליטי מבוסס xGI/90 לקראת מחזור {next_gw} | סנכרון חי לסגל: <span"
    f' class="ltr-box"><b>{team_id}</b></span>',
    unsafe_allow_html=True,
)

rank_display = (
    f"{my_rank:,}"
    if isinstance(my_rank, int)
    else (str(my_rank) if my_rank else "—")
)

m1, m2, m3, m4 = st.columns(4)
m1.markdown(
    '<div class="metric-box"><div style="color:#38bdf8; font-size:12px;'
    ' margin-bottom:4px;">ציון עוצמת סגל ריאלי</div><div'
    f' style="font-size:18px; font-weight:bold; color:{rating_color};">{squad_rating}'
    " / 100</div></div>",
    unsafe_allow_html=True,
)
m2.markdown(
    '<div class="metric-box"><div style="color:#10b981; font-size:12px;'
    ' margin-bottom:4px;">תחזית נקודות למחזור</div><div style="font-size:18px;'
    f' font-weight:bold; color:#fff;">{starting_xp_total:.1f} נק׳'
    " צפויות</div></div>",
    unsafe_allow_html=True,
)
m3.markdown(
    '<div class="metric-box"><div style="color:#f59e0b; font-size:12px;'
    ' margin-bottom:4px;">יתרה בבנק מעודכנת</div><div style="font-size:18px;'
    f' font-weight:bold; color:#fff;"><span'
    f' class="ltr-box">£{bank_balance:.1f}m</span></div></div>',
    unsafe_allow_html=True,
)
m4.markdown(
    '<div class="metric-box"><div style="color:#a855f7; font-size:12px;'
    ' margin-bottom:4px;">דירוג כללי</div><div style="font-size:18px;'
    f' font-weight:bold; color:#fff;"><span'
    f' class="ltr-box">{rank_display}</span></div></div>',
    unsafe_allow_html=True,
)

st.write("")

# --- טאבים ראשיים ---
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
  cap_badge = "👑 " if p.get("is_cap") else ("🥈 " if p.get("is_vc") else "")
  cap_class = "cap-border" if p.get("is_cap") else ""
  bench_class = "bench-card" if is_bench else ""
  return (
      f'<div class="p-card {cap_class} {bench_class}">'
      f'<div class="p-name">{cap_badge}{p["name"]}</div>'
      f'<div class="p-team"><span class="ltr-box">{p["team"]} |'
      f' £{p["cost"]}m</span></div>'
      f'<div class="p-fxt fdr-{p["next_fdr"]}"><span'
      f' class="ltr-box">{p["next_match"]}</span></div>'
      f'<div style="font-size:9px; color:#38bdf8; margin-top:2px;">צפי:'
      f' {p["xp"]} נק׳</div>'
      "</div>"
  )


# --- טאב 1: הסגל על המגרש ---
with tab_squad:
  st.subheader(f"📋 ההרכב הפותח שלך למחזור {next_gw}")
  st.caption(
      f"ההרכב צפוי להניב **{starting_xp_total:.1f}** נקודות (כולל בונוס קפטן"
      " כפול):"
  )

  gk_line = [p for p in starters if p["pos_code"] == 1]
  def_line = [p for p in starters if p["pos_code"] == 2]
  mid_line = [p for p in starters if p["pos_code"] == 3]
  fwd_line = [p for p in starters if p["pos_code"] == 4]

  fwd_h = "".join(build_card(p) for p in fwd_line)
  mid_h = "".join(build_card(p) for p in mid_line)
  def_h = "".join(build_card(p) for p in def_line)
  gk_h = "".join(build_card(p) for p in gk_line)

  st.markdown(
      f'<div class="pitch"><div class="pitch-row">{fwd_h}</div><div'
      f' class="pitch-row">{mid_h}</div><div'
      f' class="pitch-row">{def_h}</div><div class="pitch-row">{gk_h}</div></div>',
      unsafe_allow_html=True,
  )

  st.subheader("🪑 ספסל")
  bench_h = "".join(build_card(p, is_bench=True) for p in bench)
  st.markdown(
      f'<div style="display:flex; justify-content:center;'
      f' gap:8px;">{bench_h}</div>',
      unsafe_allow_html=True,
  )

# --- טאב 2: עדכון חילופים מהיר + המלצות חכמות בצד ---
with tab_manual:
  st.subheader("🔄 עדכון חילופים שביצעת (כולל המלצות חכמות בצד)")

  base_squad_names = [
      f"{all_players[pid]['name']} ({all_players[pid]['team']}) - £{all_players[pid]['cost']}m"
      for pid in base_squad_ids
      if pid in all_players
  ]

  num_tx = st.selectbox(
      "כמה חילופים ביצעת לקראת המחזור?",
      [0, 1, 2, 3],
      index=st.session_state.get("sel_num_transfers", 0),
      key="sel_num_transfers",
  )

  for i in range(num_tx):
    st.markdown(f"--- \n#### חילוף #{i+1}")
    c_out, c_rec, c_in = st.columns([1.1, 1.3, 1.2])

    with c_out:
      sel_out_player = st.selectbox(
          f"🔴 שחקן שיצא (OUT #{i+1}):",
          ["ללא שינוי"] + base_squad_names,
          key=f"transfer_out_{i}",
      )
      if sel_out_player != "ללא שינוי":
        out_pid = next(
            pid
            for pid in base_squad_ids
            if f"{all_players[pid]['name']} ({all_players[pid]['team']}) -"
            f" £{all_players[pid]['cost']}m"
            == sel_out_player
        )
        out_p = all_players[out_pid]
        max_budget_for_this = out_p["cost"] + bank_balance
        st.markdown(
            f"""
            <div style="background:#1e1418; border-right:3px solid #ef4444; border-radius:6px; padding:8px; font-size:12px; margin-top:8px;">
                <b>עמדה:</b> {out_p['pos']} | <b>שווי:</b> £{out_p['cost']}m<br>
                <b>תקציב מקסימלי לרכש:</b> <span class="ltr-box" style="color:#38bdf8; font-weight:bold;">£{max_budget_for_this:.1f}m</span><br>
                <b>משחק קרוב:</b> {out_p['next_match']} (FDR {out_p['next_fdr']})
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_rec:
      if sel_out_player == "ללא שינוי":
        st.info("👈 בחר שחקן יוצא כדי לראות כאן המלצות רכש (Recommended IN).")
      else:
        out_pid = next(
            pid
            for pid in base_squad_ids
            if f"{all_players[pid]['name']} ({all_players[pid]['team']}) -"
            f" £{all_players[pid]['cost']}m"
            == sel_out_player
        )
        out_p = all_players[out_pid]
        max_budget_for_this = out_p["cost"] + bank_balance

        pos_candidates = [
            p
            for p in all_players.values()
            if p["pos_code"] == out_p["pos_code"]
            and p["id"] not in base_squad_ids
            and p["status"] == "a"
            and p["cost"] <= max_budget_for_this
        ]
        top_recs = sorted(
            pos_candidates, key=lambda x: x["score"], reverse=True
        )[:3]

        st.markdown(
            "<b>🌟 שחקנים מומלצים להחלפה זו (Recommended):</b>",
            unsafe_allow_html=True,
        )
        if top_recs:
          for rank_idx, rp in enumerate(top_recs, 1):
            delta_val = rp["score"] - out_p["score"]
            st.markdown(
                f"""
                <div class="rec-pill">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:bold; font-size:12px; color:#fff;">
                            #{rank_idx} {rp['name']} <span style="font-size:10px; color:#94a3b8;">({rp['team']})</span>
                        </span>
                        <span class="ltr-box" style="font-size:11px; font-weight:bold; color:#38bdf8;">£{rp['cost']}m</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:10px; color:#cbd5e1; margin-top:3px;">
                        <span>משחק: <b>{rp['next_match']}</b> | נק׳ צפויות: <b>{rp['xp']}</b></span>
                        <span style="color:#10b981; font-weight:bold;">Δ+{delta_val:.1f}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
          st.warning("לא נמצאו מועמדים מתאימים בתקציב זה.")

    with c_in:
      if sel_out_player != "ללא שינוי":
        out_pid = next(
            pid
            for pid in base_squad_ids
            if f"{all_players[pid]['name']} ({all_players[pid]['team']}) -"
            f" £{all_players[pid]['cost']}m"
            == sel_out_player
        )
        out_p = all_players[out_pid]

        search_query = st.text_input(
            f"🔍 חיפוש (עמדת {out_p['pos']}):",
            key=f"search_{i}",
            placeholder="הקלד שם או קבוצה...",
        ).strip()

        all_pos_players = [
            p
            for p in all_players.values()
            if p["pos_code"] == out_p["pos_code"]
            and p["id"] not in base_squad_ids
            and p["status"] == "a"
        ]

        if search_query:
          all_pos_players = [
              p
              for p in all_pos_players
              if search_query.lower() in p["name"].lower()
              or search_query.lower() in p["team"].lower()
          ]

        all_pos_players = sorted(
            all_pos_players, key=lambda x: x["score"], reverse=True
        )
        candidate_options = [
            f"{p['name']} ({p['team']}) - £{p['cost']}m"
            for p in all_pos_players
        ]

        st.selectbox(
            f"🟢 שחקן שיכנס (IN #{i+1}):",
            ["בחר שחקן..."] + candidate_options,
            key=f"transfer_in_{i}",
        )
      else:
        st.write("")

  if transfers_applied:
    st.success(
        f"✅ הוחלו {len(transfers_applied)} חילופים! יתרת הבנק עודכנה ל-"
        f" £{bank_balance:.1f}m, וכל ההרכב בכל הטאבים מוצג לפי השינוי."
    )

# --- טאב 3: מדד עוצמה ריאלי + הצגת חסרונות הסגל ---
with tab_projection:
  st.subheader(f"📊 ניתוח עומק: עוצמת סגל ריאלית וחסרונות (GW {next_gw})")

  c_rate1, c_rate2 = st.columns([1, 2])
  with c_rate1:
    st.markdown(
        f"""
        <div style="background:#111a28; border:1px solid #1e2e46; border-radius:12px; padding:16px; text-align:center;">
            <div style="color:#94a3b8; font-size:13px;">ציון עוצמת סגל משוקלל</div>
            <div style="font-size:36px; font-weight:bold; color:{rating_color}; margin:8px 0;">{squad_rating} <span style="font-size:16px; color:#64748b;">/ 100</span></div>
            <div style="font-size:12px; font-weight:bold; color:{rating_color};">{rating_status}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with c_rate2:
    st.markdown(
        f"""
        <div style="background:#111a28; border:1px solid #1e2e46; border-radius:12px; padding:16px;">
            <div style="color:#94a3b8; font-size:13px; margin-bottom:6px;">תחזית נקודות למחזור הקרוב (11 פותחים)</div>
            <div style="font-size:26px; font-weight:bold; color:#10b981; margin-bottom:8px;">{starting_xp_total:.1f} נקודות צפויות</div>
            <div style="font-size:12px; color:#cbd5e1; line-height:1.6;">
                • <b>התקפה וקישור:</b> מייצרים כ-<b>{sum(p['xp'] for p in starters if p['pos_code'] in [3,4]):.1f}</b> נקודות צפויות.<br>
                • <b>הגנה ושוער:</b> מייצרים כ-<b>{sum(p['xp'] for p in starters if p['pos_code'] in [1,2]):.1f}</b> נקודות צפויות.<br>
                • <b>בונוס קפטן:</b> תוספת של <b>+{next((p['xp'] for p in starters if p.get('is_cap')), 5.0):.1f}</b> נקודות על סרט הקפטן.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.write("")

  # בלוק חסרונות הסגל המודגש
  st.markdown(
      f"#### ⚠️ חסרונות ונקודות תורפה בסגל שמשכו את הציון למטה"
      f" ({len(squad_flaws)})"
  )
  st.caption("הגורמים המרכזיים שמגבילים את הציון שלך ומייצרים סיכון נקודות:")

  if squad_flaws:
    for f in squad_flaws:
      st.markdown(
          f"""
            <div class="flaw-card">
                <b>[{f['type']}]:</b> {f['text']}
            </div>
            """,
          unsafe_allow_html=True,
      )
  else:
    st.success("לא זוהו חסרונות משמעותיים בסגל הנוכחי! סגל מאוזן ומושלם.")

  st.write("")
  st.markdown("#### 📋 פירוט נקודות צפויות לפי שחקני ההרכב הפותח")

  xp_rows = []
  for p in starters:
    is_c = " 👑 (קפטן)" if p.get("is_cap") else ""
    mult = 2 if p.get("is_cap") else 1
    xp_rows.append({
        "שחקן": f"{p['name']}{is_c}",
        "עמדה": p["pos"],
        "קבוצה": p["team"],
        "משחק קרוב": p["next_match"],
        "דרגת קושי": f"FDR {p['next_fdr']}",
        "xGI ל-90 דק׳": p["xgi_p90"],
        "נקודות צפויות": round(p["xp"] * mult, 1),
    })

  xp_df = pd.DataFrame(xp_rows)
  st.dataframe(xp_df, use_container_width=True, hide_index=True)

# --- טאב 4: רדאר רכש עילית ---
with tab_targets:
  st.subheader(f"🌟 יעדי רכש מובילים למחזור {next_gw} (Top 50K Algorithm)")
  st.caption(
      "דירוג מבוסס xGI ל-90 דקות, לוח משחקים דועך וזיהוי סטטיסטי של קנייה בשפל"
      " (Buy Low):"
  )

  sub_fwd, sub_mid, sub_def, sub_gk, sub_cap = st.tabs([
      "⚡ חלוצים (FWD)",
      "🎯 קשרים (MID)",
      "🛡️ הגנה (DEF)",
      "🧤 שוערים (GK)",
      "👑 קפטן מגן מול חרב",
  ])

  def render_cards(pos_num, count=6):
    targets = [
        p
        for p in all_players.values()
        if p["pos_code"] == pos_num and p["status"] == "a"
    ]
    targets = sorted(targets, key=lambda x: x["score"], reverse=True)[:count]

    for i, p in enumerate(targets):
      tier = "tier-1" if i < 2 else ("tier-2" if i < 4 else "tier-3")
      tag_badge = ""
      if p["tag"] == "BUY_LOW":
        tag_badge = '<span class="badge badge-buylow">🔥 קנייה בשפל</span>'
      elif p["tag"] == "OVERPERFORMING_TRAP":
        tag_badge = '<span class="badge badge-trap">⚠️ מעל המצופה</span>'

      st.markdown(
          f"""
            <div class="target-card {tier}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:bold; font-size:15px; color:#f8fafc;">
                        {p['name']} <span class="ltr-box" style="font-size:12px; color:#94a3b8;">({p['team']})</span> {tag_badge}
                    </span>
                    <span class="ltr-box" style="font-size:14px; font-weight:bold; color:#38bdf8;">£{p['cost']}m | ציון: {p['score']}</span>
                </div>
                <div style="margin:8px 0; font-size:12px; color:#cbd5e1;">
                    💡 <b>ניתוח מדעי:</b> {p['reason']}
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; color:#94a3b8; border-top:1px solid #1e293b; padding-top:6px; margin-top:6px;">
                    <span><span class="ltr-box">xGI/90: <b>{p['xgi_p90']}</b></span> | כושר: <b>{p['form']}</b> | בעלות: <span class="ltr-box"><b>{p['selected_by']}%</b></span></span>
                    <div>משחק קרוב: <span class="badge fdr-{p['next_fdr']}"><span class="ltr-box">{p['next_match']}</span></span> | <span class="ltr-box">{p['fixtures']}</span></div>
                </div>
            </div>
            """,
          unsafe_allow_html=True,
      )

  with sub_fwd:
    render_cards(4, 6)
  with sub_mid:
    render_cards(3, 7)
  with sub_def:
    render_cards(2, 6)
  with sub_gk:
    render_cards(1, 4)

  with sub_cap:
    st.markdown("#### 👑 המלצות קפטן מדעיות")
    premiums = [
        p
        for p in all_players.values()
        if p["cost"] >= 7.5 and p["status"] == "a"
    ]
    premiums = sorted(premiums, key=lambda x: x["score"], reverse=True)
    shield = premiums[0]
    diff_pool = [p for p in premiums if p["selected_by"] < 18]
    sword = diff_pool[0] if diff_pool else premiums[1]

    ca, cb = st.columns(2)
    with ca:
      st.markdown(
          f"""
            <div style="background:#0f2a24; border:1px solid #059669; padding:12px; border-radius:10px;">
                <span style="background:#059669; color:white; padding:2px 6px; border-radius:3px; font-size:9px; font-weight:bold;">🛡️ קפטן מגן (Shield)</span>
                <h4 style="margin:6px 0; color:#ecfdf5;">{shield['name']} <span class="ltr-box">({shield['team']})</span></h4>
                <p style="font-size:11px; color:#a7f3d0; margin:0; line-height:1.5;">
                בעלות: <span class="ltr-box"><b>{shield['selected_by']}%</b></span> | ציון מנוע: <b>{shield['score']}</b><br>
                משחק הבא: <span class="ltr-box"><b>{shield['next_match']}</b></span> | נק׳ צפויות: <b>{shield['xp']}</b><br>
                💡 {shield['reason']}
                </p>
            </div>
            """,
          unsafe_allow_html=True,
      )
    with cb:
      st.markdown(
          f"""
            <div style="background:#2a1e0f; border:1px solid #d97706; padding:12px; border-radius:10px;">
                <span style="background:#d97706; color:white; padding:2px 6px; border-radius:3px; font-size:9px; font-weight:bold;">⚔️ קפטן דיפרנשיאל (Sword)</span>
                <h4 style="margin:6px 0; color:#fffbeb;">{sword['name']} <span class="ltr-box">({sword['team']})</span></h4>
                <p style="font-size:11px; color:#fde68a; margin:0; line-height:1.5;">
                בעלות: <span class="ltr-box"><b>{sword['selected_by']}% בלבד</b></span> | ציון מנוע: <b>{sword['score']}</b><br>
                משחק הבא: <span class="ltr-box"><b>{sword['next_match']}</b></span> | נק׳ צפויות: <b>{sword['xp']}</b><br>
                💡 {sword['reason']}
                </p>
            </div>
            """,
          unsafe_allow_html=True,
      )

# --- טאב 5: הצעות חילוף לתקציב הסגל שלך ---
with tab_transfer:
  st.subheader("🎯 3 הצעות חילוף אופציונליות המותאמות לתקציב שלך")
  st.caption(
      f"מחושב בדיוק לפי 15 השחקנים שלך ויתרת הבנק הנוכחית (<span"
      f' class="ltr-box">£{bank_balance:.1f}m</span>):',
      unsafe_allow_html=True,
  )

  all_my_players = starters + bench
  my_ids = [x["id"] for x in all_my_players]

  def find_best_in(pos_code, max_budget):
    candidates = [
        p
        for p in all_players.values()
        if p["id"] not in my_ids
        and p["pos_code"] == pos_code
        and p["cost"] <= max_budget
        and p["status"] == "a"
    ]
    if not candidates:
      return None
    return max(candidates, key=lambda x: x["score"])

  def_pool = [p for p in all_my_players if p["pos_code"] == 2]
  out_def = min(
      def_pool,
      key=lambda x: (
          x["score"] if x["status"] == "a" and x["chance"] == 100 else -20
      ),
  )

  mid_pool = [p for p in all_my_players if p["pos_code"] == 3]
  out_mid = min(
      mid_pool,
      key=lambda x: (
          x["score"] if x["status"] == "a" and x["chance"] == 100 else -15
      ),
  )

  fwd_pool = [
      p for p in all_my_players if p["pos_code"] == 4 and "Haaland" not in p["name"]
  ]
  out_fwd = (
      min(fwd_pool, key=lambda x: x["score"])
      if fwd_pool
      else [p for p in all_my_players if p["pos_code"] == 4][0]
  )

  scenarios = [
      {
          "title": "אופציה 1: טיפול במוקד החירום / שיפוץ הגנתי",
          "tag": "🛡️ עדיפות הגנתית",
          "out_player": out_def,
          "in_player": find_best_in(2, out_def["cost"] + bank_balance),
      },
      {
          "title": "אופציה 2: שדרוג מנוע הקישור וייצור שערים",
          "tag": "🎯 תוספת איום התקפי",
          "out_player": out_mid,
          "in_player": find_best_in(3, out_mid["cost"] + bank_balance),
      },
      {
          "title": "אופציה 3: רענון חוד ההתקפה / פונט התקפי",
          "tag": "⚡ חוד ההתקפה",
          "out_player": out_fwd,
          "in_player": find_best_in(4, out_fwd["cost"] + bank_balance),
      },
  ]

  for i, sc in enumerate(scenarios, 1):
    p_out = sc["out_player"]
    p_in = sc["in_player"]

    if not p_in:
      continue

    max_b = p_out["cost"] + bank_balance
    rem_b = max_b - p_in["cost"]
    delta = p_in["score"] - p_out["score"]

    delta_color = "#10b981" if delta >= 2.5 else "#38bdf8"
    recommendation_badge = (
        "🔥 מומלץ מאוד לביצוע"
        if delta >= 3.0
        else (
            "⚖️ שדרוג נקודתי"
            if delta >= 1.5
            else "💡 עדיף לשמור חילוף (Roll)"
        )
    )

    st.markdown(
        f"""
        <div class="transfer-scenario-card">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b; padding-bottom:8px; margin-bottom:12px;">
                <div>
                    <span style="font-weight:bold; font-size:16px; color:#f8fafc;">{sc['title']}</span>
                    <span class="badge" style="background:#1e293b; color:#94a3b8; margin-right:6px;">{sc['tag']}</span>
                </div>
                <div style="font-size:13px; font-weight:bold; color:{delta_color};">
                    תוספת פוטנציאל: <span class="ltr-box">Δ+{delta:.1f}</span> ({recommendation_badge})
                </div>
            </div>
            <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap;">
                <div style="flex:1; min-width:240px; background:#231114; border-right:4px solid #ef4444; border-radius:8px; padding:10px;">
                    <div style="font-size:11px; color:#fca5a5; font-weight:bold;">🔴 שחקן שיצא (OUT)</div>
                    <div style="font-size:15px; font-weight:bold; color:#fff; margin:2px 0;">{p_out['name']} <span class="ltr-box">({p_out['team']})</span></div>
                    <div style="font-size:12px; color:#cbd5e1;">עמדה: {p_out['pos']} | מכירה: <span class="ltr-box">£{p_out['cost']}m</span> | ציון: {p_out['score']}</div>
                    <div style="font-size:11px; color:#94a3b8; margin-top:4px;">משחק קרוב: <span class="ltr-box">{p_out['next_match']}</span> (FDR {p_out['avg_fdr']})</div>
                </div>
                <div style="flex:1; min-width:240px; background:#0c2417; border-right:4px solid #10b981; border-radius:8px; padding:10px;">
                    <div style="font-size:11px; color:#6ee7b7; font-weight:bold;">🟢 שחקן שיכנס (IN)</div>
                    <div style="font-size:15px; font-weight:bold; color:#fff; margin:2px 0;">{p_in['name']} <span class="ltr-box">({p_in['team']})</span></div>
                    <div style="font-size:12px; color:#cbd5e1;">קנייה: <span class="ltr-box">£{p_in['cost']}m</span> (בנק: <span class="ltr-box"><b>£{rem_b:.1f}m</b></span>) | ציון: {p_in['score']}</div>
                    <div style="font-size:11px; color:#94a3b8; margin-top:4px;">משחק קרוב: <span class="ltr-box"><b>{p_in['next_match']}</b></span> | נק׳ צפויות: <b>{p_in['xp']}</b></div>
                </div>
            </div>
            <div style="font-size:12px; color:#94a3b8; margin-top:8px; background:#0b1120; padding:8px 10px; border-radius:6px;">
                💡 <b>נימוק טקטי:</b> {p_in['reason']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- טאב 6: רמזור בריאות הסגל ---
with tab_health:
  st.subheader("🚦 רמזור בריאות ומוקשי הרכב")
  reds = [
      p for p in all_my_players if p["status"] != "a" or p["chance"] < 100
  ]
  yellows = [
      p
      for p in all_my_players
      if p["status"] == "a"
      and p["chance"] == 100
      and (p["avg_fdr"] > 2.8 or p["form"] < 3.0)
  ]

  st.markdown(f"#### 🔴 מוקדי חירום בסגל ({len(reds)})")
  if reds:
    for p in reds:
      st.markdown(
          f'<div class="health-box health-red"><b>{p["name"]} <span'
          f' class="ltr-box">({p["team"]})</span></b> - סיכוי שיתוף:'
          f' {p["chance"]}% | לוח: <span'
          f' class="ltr-box">{p["fixtures"]}</span></div>',
          unsafe_allow_html=True,
      )
  else:
    st.success("אין פציעות או השעיות ידועות בסגל!")

  st.markdown(f"#### 🟡 תחת מעקב / לוח קשה ({len(yellows)})")
  for p in yellows:
    st.markdown(
        f'<div class="health-box health-yellow"><b>{p["name"]} <span'
        f' class="ltr-box">({p["team"]})</span></b> - כושר: {p["form"]} | לוח:'
        f' <span class="ltr-box">{p["fixtures"]}</span> (FDR ממוצע:'
        f' {p["avg_fdr"]})</div>',
        unsafe_allow_html=True,
    )
