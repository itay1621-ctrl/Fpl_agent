import json
import time
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="FPL Elite Scout | Top 50K Engine",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- עיצוב CSS מותאם מובייל ואייפון (RTL Dark Mode) ---
st.markdown(
    """
<style>
.main { direction: rtl; text-align: right; background-color: #080d1a; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
.metric-box { background: #131c2e; border-radius: 10px; padding: 10px; text-align: center; border: 1px solid #1f2d47; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
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
    width: 86px;
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
    padding: 12px;
    margin-bottom: 10px;
}
.tier-1 { border-right: 4px solid #10b981; }
.tier-2 { border-right: 4px solid #38bdf8; }
.tier-3 { border-right: 4px solid #f59e0b; }

.transfer-scenario-card {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 16px;
}

.badge { font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; display: inline-block; margin-left: 4px; }
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
.stChatMessage { direction: rtl; text-align: right; }
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
          upcoming.append(f"{opp}(H)")
          fdr_list.append(f["team_h_difficulty"])
        elif f["team_a"] == el["team"]:
          opp = teams[f["team_h"]]["short_name"]
          upcoming.append(f"{opp}(A)")
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

    if tag_status == "BUY_LOW":
      reason = f"הזדמנות קנייה בשפל: מייצר שערים צפויים ברצף (xGI: {expected_gi:.1f}) אך טרם תוגמל במספרים בפועל."
    elif tag_status == "OVERPERFORMING_TRAP":
      reason = "זהירות, מעל המצופה: הבקיע מעבר למצבים הממשיים שייצר. סכנת דעיכה לממוצע."
    elif el["element_type"] in [1, 2]:
      if team_short in elite_defenses:
        reason = f"עוגן רשת נקייה מוביל מהגנת {team_short} עם לוח משחקים נוח."
      else:
        reason = "מגן פעיל התקפית במחיר משתלם."
    else:
      if form >= 5.0:
        reason = f"כושר שיא (Form {form}) עם איום שערים קבוע ותפקיד התקפי מרכזי."
      else:
        reason = "נתוני xGI חיוביים עם לוח משחקים אופטימלי לצבירת נקודות."

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
        "tag": tag_status,
        "reason": reason,
        "status": el["status"],
        "chance": (
            el["chance_of_playing_next_round"]
            if el["chance_of_playing_next_round"] is not None
            else 100
        ),
        "next_match": upcoming[0] if upcoming else "—",
        "next_fdr": fdr_list[0] if fdr_list else 3,
        "avg_fdr": round(avg_fdr, 2),
        "fixtures": " | ".join(upcoming),
    }

  return processed, next_gw


all_players, next_gw = fetch_league_data()

# --- 2. סרגל צד והגדרות ---
st.sidebar.header("⚙️ ניהול סגל והגדרות")
team_id = st.sidebar.text_input("מספר קבוצה (Team ID):", value="139103")

secret_key = ""
try:
  secret_key = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
  pass
api_key = st.sidebar.text_input(
    "Google Gemini API Key:", value=secret_key, type="password"
)


# --- 3. משיכת הקבוצה שלך וזיהוי אוטומטי של Free Hit ---
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


my_picks, bank_balance, my_team_name, my_rank = fetch_user_team(
    team_id, next_gw
)

if not my_picks:
  st.warning(
      "לא ניתן למשוך את נתוני הקבוצה. אנא ודא שמספר הקבוצה (Team ID) תקין."
  )
  st.stop()

current_squad_ids = [p["element"] for p in my_picks]

# --- עדכון חילופים שבוצעו לקראת המחזור הקרוב ---
st.sidebar.markdown("---")
st.sidebar.subheader("🔄 עדכון חילופים ידני למחזור")
num_transfers = st.sidebar.selectbox(
    "כמה חילופים ביצעת לקראת המחזור?", [0, 1, 2, 3], index=0
)

all_player_names = {
    f"{p['name']} ({p['team']}) - £{p['cost']}m": pid
    for pid, p in all_players.items()
}
player_options = sorted(list(all_player_names.keys()))

transfers_made = []
for i in range(num_transfers):
  st.sidebar.markdown(f"**חילוף #{i+1}**")
  squad_names = [
      f"{all_players[pid]['name']} ({all_players[pid]['team']})"
      for pid in current_squad_ids
      if pid in all_players
  ]
  p_out_name = st.sidebar.selectbox(
      f"שחקן שיצא (OUT #{i+1}):", ["ללא שינוי"] + squad_names, key=f"out_{i}"
  )
  p_in_name = st.sidebar.selectbox(
      f"שחקן שנכנס (IN #{i+1}):",
      ["בחר שחקן..."] + player_options,
      key=f"in_{i}",
  )

  if p_out_name != "ללא שינוי" and p_in_name != "בחר שחקן...":
    out_id = next(
        pid
        for pid in current_squad_ids
        if f"{all_players[pid]['name']} ({all_players[pid]['team']})"
        == p_out_name
    )
    in_id = all_player_names[p_in_name]
    transfers_made.append((out_id, in_id))

for out_id, in_id in transfers_made:
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

# --- שורת מדדים ראשית ---
st.title(f"⚽ FPL Command Center | {my_team_name}")
st.caption(
    f"מנוע אנליטי מבוסס xGI/90 לקראת מחזור {next_gw} | סנכרון חי לסגל:"
    f" **{team_id}**"
)

rank_display = (
    f"{my_rank:,}"
    if isinstance(my_rank, int)
    else (str(my_rank) if my_rank else "—")
)

m1, m2, m3, m4 = st.columns(4)
m1.markdown(
    '<div class="metric-box"><div style="color:#38bdf8;font-size:11px;">מחזור'
    ' יעד</div><div style="font-size:17px;font-weight:bold;">GW'
    f" {next_gw}</div></div>",
    unsafe_allow_html=True,
)
m2.markdown(
    '<div class="metric-box"><div style="color:#10b981;font-size:11px;">דירוג'
    f' כללי</div><div style="font-size:17px;font-weight:bold;">{rank_display}</div></div>',
    unsafe_allow_html=True,
)
m3.markdown(
    '<div class="metric-box"><div style="color:#f59e0b;font-size:11px;">יתרה'
    ' בבנק מעודכנת</div><div'
    f' style="font-size:17px;font-weight:bold;">£{bank_balance:.1f}m</div></div>',
    unsafe_allow_html=True,
)
m4.markdown(
    '<div class="metric-box"><div style="color:#a855f7;font-size:11px;">יעד'
    ' עולמי</div><div style="font-size:17px;font-weight:bold;">Top 50K'
    " 🏆</div></div>",
    unsafe_allow_html=True,
)

st.write("")

# טאבים מרכזיים
tab_squad, tab_targets, tab_transfer, tab_health, tab_chat = st.tabs([
    "🟢 הסגל על המגרש",
    "🌟 רדאר רכש עילית",
    "🎯 הצעות חילוף לתקציב שלי (3 אופציות)",
    "🚦 רמזור בריאות הסגל",
    "💬 צ'אט AI אישי",
])


def build_card(p, is_bench=False):
  cap_badge = "👑 " if p.get("is_cap") else ("🥈 " if p.get("is_vc") else "")
  cap_class = "cap-border" if p.get("is_cap") else ""
  bench_class = "bench-card" if is_bench else ""
  return (
      f'<div class="p-card {cap_class} {bench_class}">'
      f'<div class="p-name">{cap_badge}{p["name"]}</div>'
      f'<div class="p-team">{p["team"]} | £{p["cost"]}m</div>'
      f'<div class="p-fxt fdr-{p["next_fdr"]}">{p["next_match"]}</div>'
      "</div>"
  )


# --- טאב 1: הסגל על המגרש ---
with tab_squad:
  st.subheader(f"📋 ההרכב הפותח שלך למחזור {next_gw}")
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

# --- טאב 2: רדאר רכש מבוסס מדע (Target Radar) ---
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
                        {p['name']} <span style="font-size:12px; color:#94a3b8;">({p['team']})</span> {tag_badge}
                    </span>
                    <span style="font-size:14px; font-weight:bold; color:#38bdf8;">£{p['cost']}m | ציון: {p['score']}</span>
                </div>
                <div style="margin:6px 0; font-size:12px; color:#cbd5e1;">
                    💡 <b>ניתוח מדעי:</b> {p['reason']}
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; color:#94a3b8; border-top:1px solid #1e293b; padding-top:6px; margin-top:6px;">
                    <span>xGI/90: <b>{p['xgi_p90']}</b> | כושר: <b>{p['form']}</b> | בעלות: <b>{p['selected_by']}%</b></span>
                    <div>משחק קרוב: <span class="badge fdr-{p['next_fdr']}">{p['next_match']}</span> | 3 משחקים: {p['fixtures']}</div>
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
                <h4 style="margin:6px 0; color:#ecfdf5;">{shield['name']} ({shield['team']})</h4>
                <p style="font-size:11px; color:#a7f3d0; margin:0;">
                בעלות: <b>{shield['selected_by']}%</b> | ציון מנוע: <b>{shield['score']}</b><br>
                משחק הבא: <b>{shield['next_match']}</b> | FDR ממוצע: {shield['avg_fdr']}<br>
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
                <h4 style="margin:6px 0; color:#fffbeb;">{sword['name']} ({sword['team']})</h4>
                <p style="font-size:11px; color:#fde68a; margin:0;">
                בעלות: <b>{sword['selected_by']}% בלבד</b> | ציון מנוע: <b>{sword['score']}</b><br>
                משחק הבא: <b>{sword['next_match']}</b> | FDR ממוצע: {sword['avg_fdr']}<br>
                💡 {sword['reason']}
                </p>
            </div>
            """,
          unsafe_allow_html=True,
      )

# --- טאב 3: הצעות חילוף מותאמות לתקציב הסגל שלך (3 אופציות ממוקדות) ---
with tab_transfer:
  st.subheader("🎯 3 הצעות חילוף אופציונליות המותאמות לתקציב שלך")
  st.caption(
      f"מחושב בדיוק לפי 15 השחקנים שלך ויתרת הבנק הנוכחית (£{bank_balance:.1f}m)."
      " כל אפשרות משווה שחקן יוצא מול יעד הרכש הכי איכותי בליגה בעמדתו:"
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
                    <span class="badge" style="background:#1e293b; color:#94a3b8;">{sc['tag']}</span>
                </div>
                <div style="font-size:13px; font-weight:bold; color:{delta_color};">
                    תוספת פוטנציאל: Δ+{delta:.1f} נקודות ({recommendation_badge})
                </div>
            </div>
            <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap;">
                <div style="flex:1; min-width:240px; background:#231114; border-right:4px solid #ef4444; border-radius:8px; padding:10px;">
                    <div style="font-size:11px; color:#fca5a5; font-weight:bold;">🔴 שחקן שיצא (OUT)</div>
                    <div style="font-size:15px; font-weight:bold; color:#fff; margin:2px 0;">{p_out['name']} ({p_out['team']})</div>
                    <div style="font-size:12px; color:#cbd5e1;">עמדה: {p_out['pos']} | מחיר מכירה: £{p_out['cost']}m | ציון: {p_out['score']}</div>
                    <div style="font-size:11px; color:#94a3b8; margin-top:4px;">משחק קרוב: {p_out['next_match']} (FDR {p_out['avg_fdr']})</div>
                </div>
                <div style="flex:1; min-width:240px; background:#0c2417; border-right:4px solid #10b981; border-radius:8px; padding:10px;">
                    <div style="font-size:11px; color:#6ee7b7; font-weight:bold;">🟢 שחקן שיכנס (IN)</div>
                    <div style="font-size:15px; font-weight:bold; color:#fff; margin:2px 0;">{p_in['name']} ({p_in['team']})</div>
                    <div style="font-size:12px; color:#cbd5e1;">מחיר קנייה: £{p_in['cost']}m (נשאר בבנק: <b>£{rem_b:.1f}m</b>) | ציון: {p_in['score']}</div>
                    <div style="font-size:11px; color:#94a3b8; margin-top:4px;">משחק קרוב: <b>{p_in['next_match']}</b> | xGI/90: <b>{p_in['xgi_p90']}</b></div>
                </div>
            </div>
            <div style="font-size:12px; color:#94a3b8; margin-top:8px; background:#0b1120; padding:8px 10px; border-radius:6px;">
                💡 <b>נימוק טקטי:</b> {p_in['reason']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- טאב 4: רמזור בריאות הסגל ---
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
          f'<div class="health-box health-red"><b>{p["name"]} ({p["team"]})</b>'
          f' - סיכוי שיתוף: {p["chance"]}% | לוח: {p["fixtures"]}</div>',
          unsafe_allow_html=True,
      )
  else:
    st.success("אין פציעות או השעיות ידועות בסגל!")

  st.markdown(f"#### 🟡 תחת מעקב / לוח קשה ({len(yellows)})")
  for p in yellows:
    st.markdown(
        f'<div class="health-box health-yellow"><b>{p["name"]} ({p["team"]})</b>'
        f' - כושר: {p["form"]} | לוח: {p["fixtures"]} (FDR ממוצע:'
        f' {p["avg_fdr"]})</div>',
        unsafe_allow_html=True,
    )

# --- טאב 5: צ'אט AI אישי (חסין עומסים 503 עם Exponential Backoff ו-Flash-Lite) ---
with tab_chat:
  st.subheader(f"💬 יועץ ה-AI האישי של {my_team_name}")
  st.caption("הסוכן מעודכן בנתוני ה-xGI/90, ביתרת הבנק ובתוכנית הצ'יפים שלך.")

  if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": (
            f"היי! אני מחובר לסגל שלך ({my_team_name}) עם יתרת בנק של"
            f" £{bank_balance:.1f}m. שאל אותי כל שאלה: חילופים, ניתוח קפטן או"
            " אסטרטגיה למחזורים הקרובים."
        ),
    }]

  for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
      st.write(msg["content"])

  if prompt := st.chat_input("שאל את המאמן (למשל: מי להכניס במקום מגווייר?)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
      st.write(prompt)

    clean_key = api_key.strip() if api_key else ""
    if not clean_key:
      reply = (
          "⚠️ נא להזין מפתח Gemini API בסרגל הצד (Sidebar) או ב-Streamlit"
          " Secrets."
      )
    else:
      my_squad_summary = [
          {
              "name": p["name"],
              "team": p["team"],
              "pos": p["pos"],
              "cost": p["cost"],
              "score": p["score"],
              "xgi_p90": p["xgi_p90"],
              "next": p["next_match"],
          }
          for p in all_my_players
      ]

      system_instruction = f"""
אתה מאמן ואסטרטג FPL ברמת Top 50,000 עולמי.
מחזור נוכחי: {next_gw}.
פרטי קבוצת המשתמש:
שם: {my_team_name}, דירוג: {rank_display}, בנק פנוי: £{bank_balance:.1f}m.
15 השחקנים של המשתמש:
{json.dumps(my_squad_summary, ensure_ascii=False)}

הנחיות לתשובה:
1. היה חד, טקטי ומבוסס מדע (xGI per 90, FDR דועך, תוחלת שערים EV).
2. התייחס לתקציב הפנוי של המשתמש (£{bank_balance:.1f}m).
3. קח בחשבון שימור חילופים (Roll Transfer) מול קנסות מינוס 4.
4. ענה בעברית רהוטה וקולעת.
"""

      combined_prompt = f"{system_instruction}\n\n---\nשאלת המשתמש:\n{prompt}"

      # עדיפות עליונה ל-flash-lite שחסין מעומסי 503, וגיבוי לשאר
      candidate_models = [
          "gemini-2.5-flash-lite",
          "gemini-2.5-flash",
          "gemini-1.5-flash",
      ]

      reply = None
      last_err = ""

      for model_name in candidate_models:
        if reply:
          break
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={clean_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": combined_prompt}]}
            ]
        }

        # מנגנון ניסיונות חוזרים והשהייה מדורגת (Exponential Backoff) להתגברות על עומסי 503
        for attempt in range(3):
          try:
            res = requests.post(url, headers=headers, json=payload, timeout=15)
            if res.status_code == 200:
              data = res.json()
              reply = data["candidates"][0]["content"]["parts"][0]["text"]
              break
            elif res.status_code in [503, 429]:
              # שרת עמוס רגעית - ממתינים ומנסים שוב באותו מודל
              err_msg = (
                  res.json().get("error", {}).get("message", "High demand")
              )
              last_err = f"{model_name}: {err_msg}"
              time.sleep(1.5 * (attempt + 1))
              continue
            else:
              err_msg = (
                  res.json().get("error", {}).get("message", res.status_code)
              )
              last_err = f"{model_name}: {err_msg}"
              break
          except Exception as e:
            last_err = str(e)
            time.sleep(1.0)

      if not reply:
        reply = (
            f"⚠️ שגיאת תקשורת עם ה-AI: {last_err}\n\nנסה שוב בעוד מספר שניות."
        )

    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
      st.write(reply)
