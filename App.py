import json
import time
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="FPL Elite Scout | Personal Team & Targets",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.main { direction: rtl; text-align: right; background-color: #0b0f19; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
.metric-box { background: #162032; border-radius: 8px; padding: 10px; text-align: center; border: 1px solid #243550; }
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
    background: rgba(15, 23, 42, 0.92);
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

.badge { font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; display: inline-block; margin-left: 4px; }
.fdr-2 { background: #15803d; color: #fff; }
.fdr-3 { background: #475569; color: #fff; }
.fdr-4 { background: #b91c1c; color: #fff; }
.fdr-5 { background: #7f1d1d; color: #fff; }

.health-box { padding: 10px; border-radius: 8px; margin-bottom: 8px; }
.health-green { background: #0c2417; border-right: 4px solid #10b981; }
.health-yellow { background: #26200d; border-right: 4px solid #f59e0b; }
.health-red { background: #2b1114; border-right: 4px solid #ef4444; }
.stChatMessage { direction: rtl; text-align: right; }
</style>
""",
    unsafe_allow_html=True,
)


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

    avg_fdr = sum(fdr_list) / len(fdr_list) if fdr_list else 3.0
    form = float(el["form"])
    xgi = float(el.get("expected_goal_involvements", 0.0))
    threat = float(el.get("threat", 0.0))
    cost = el["now_cost"] / 10
    goals_assists = el["goals_scored"] + el["assists"]
    net_transfers = el.get("transfers_in_event", 0) - el.get(
        "transfers_out_event", 0
    )

    # מקדם התאמה ל-Top 50K
    def_boost = (
        1.3
        if (el["element_type"] in [1, 2] and team_short in elite_defenses)
        else 0.85
    )
    att_boost = (
        1.25
        if (el["element_type"] in [3, 4] and (form >= 4.5 or goals_assists >= 2))
        else 1.0
    )

    score = (
        (form * 1.5)
        + (xgi * 1.4)
        + (threat * 0.015)
        + ((5.3 - avg_fdr) * 1.3)
        + (1.2 if net_transfers > 30000 else 0.0)
    )
    score *= def_boost if el["element_type"] in [1, 2] else att_boost

    # נימוק אנליטי לכל שחקן
    if el["element_type"] == 1:
      reason = (
          "שוער יציב מאחורי הגנה איכותית"
          if team_short in elite_defenses
          else "פוטנציאל הצלות גבוה"
      )
    elif el["element_type"] == 2:
      if threat > 40:
        reason = "מגן תוקף מסוכן עם איום שער/בישול + סיכוי לקלין שיט"
      elif team_short in elite_defenses:
        reason = "עוגן רשת נקייה מקבוצת צמרת מובילה"
      else:
        reason = "מחיר נוח עם לוח משחקים ירוק"
    elif el["element_type"] in [3, 4]:
      if form >= 5.5 or goals_assists >= 3:
        reason = "כושר כיבוש שיא ומומנטום התקפי קטלני"
      elif xgi >= 1.5:
        reason = "מייצר מצבי הבקעה ברציפות (xGI גבוה)"
      elif net_transfers > 50000:
        reason = "מוקד רכש לוהט וביקוש שיא בקהילה"
      else:
        reason = "משקל התקפי מרכזי ולוח נוח"

    processed[el_id] = {
        "id": el_id,
        "name": el["web_name"],
        "team": team_short,
        "pos": pos_map[el["element_type"]],
        "pos_code": el["element_type"],
        "cost": cost,
        "form": form,
        "xgi": xgi,
        "selected_by": float(el["selected_by_percent"]),
        "goals_assists": goals_assists,
        "score": round(score, 2),
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

# סרגל צד
st.sidebar.header("⚙️ הגדרות משתמש")
team_id = st.sidebar.text_input("מספר קבוצה (Team ID):", value="139103")
api_key = st.sidebar.text_input("Google Gemini API Key:", type="password")


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

    # בדיקת Free Hit
    is_fh = picks_res.get("active_chip") == "free_hit"
    if is_fh and last_gw > 1:
      base_gw = last_gw - 1
      base_url = (
          f"https://fantasy.premierleague.com/api/entry/{t_id}/event/{base_gw}/picks/"
      )
      picks_res = requests.get(base_url).json()

    bank = picks_res.get("entry_history", {}).get("bank", 0) / 10
    picks = picks_res.get("picks", [])
    team_name = entry_res.get("name", "הקבוצה שלי")
    rank = entry_res.get("summary_overall_rank", "—")
    return picks, bank, team_name, rank
  except Exception:
    return None, 0.0, None, None


my_picks, bank_balance, my_team_name, my_rank = fetch_user_team(
    team_id, next_gw
)

if not my_picks:
  st.warning("לא ניתן למשוך את נתוני הקבוצה. ודא שמספר הקבוצה תקין.")
  st.stop()

current_squad_ids = [p["element"] for p in my_picks]

# עדכון חילופים ידני ל-GW4 בסרגל הצד
st.sidebar.markdown("---")
st.sidebar.subheader("🔄 עדכון חילופים שבוצעו ל-GW4")
num_transfers = st.sidebar.selectbox(
    "כמה חילופים ביצעת?", [0, 1, 2, 3], index=0
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

# תצוגה ראשית
st.title(f"⚽ FPL Command Center | {my_team_name or 'Top 50K'}")
st.caption(f"הכנה למחזור {next_gw} | סנכרון חי לסגל: **{team_id}**")

rank_display = (
    f"{my_rank:,}"
    if isinstance(my_rank, int)
    else (str(my_rank) if my_rank else "—")
)

m1, m2, m3, m4 = st.columns(4)
m1.markdown(
    '<div class="metric-box"><div style="color:#38bdf8;font-size:11px;">מחזור'
    ' יעד</div><div style="font-size:16px;font-weight:bold;">GW'
    f" {next_gw}</div></div>",
    unsafe_allow_html=True,
)
m2.markdown(
    '<div class="metric-box"><div style="color:#10b981;font-size:11px;">דירוג'
    f' כללי</div><div style="font-size:16px;font-weight:bold;">{rank_display}</div></div>',
    unsafe_allow_html=True,
)
m3.markdown(
    '<div class="metric-box"><div style="color:#f59e0b;font-size:11px;">יתרה'
    ' בבנק מעודכנת</div><div'
    f' style="font-size:16px;font-weight:bold;">£{bank_balance:.1f}m</div></div>',
    unsafe_allow_html=True,
)
m4.markdown(
    '<div class="metric-box"><div style="color:#a855f7;font-size:11px;">יעד'
    ' עולמי</div><div style="font-size:16px;font-weight:bold;">Top 50K'
    " 🏆</div></div>",
    unsafe_allow_html=True,
)

st.write("")

# טאבים ראשיים - כולל המלצות רכש בולטות
tab_squad, tab_targets, tab_transfer, tab_health, tab_chat = st.tabs([
    "🟢 הסגל שלי",
    "🌟 שחקנים מומלצים לרכש",
    "🎯 מחשבון חילוף אישי",
    "🚦 בריאות הסגל",
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


# --- טאב 1: הסגל שלי ---
with tab_squad:
  st.subheader("📋 ההרכב הפותח שלך ל-GW4")
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

# --- טאב 2: שחקנים מומלצים לרכש (Target Radar) ---
with tab_targets:
  st.subheader(f"🌟 רדאר רכש מומלץ למחזור {next_gw} (Top 50K Standards)")
  st.caption("השחקנים המדורגים בראש הרשימה בכל עמדה, כולל נימוק מקצועי לבחירה:")

  sub_fwd, sub_mid, sub_def, sub_gk, sub_cap = st.tabs([
      "⚡ חלוצים (FWD)",
      "🎯 קשרים (MID)",
      "🛡️ הגנה (DEF)",
      "🧤 שוערים (GK)",
      "👑 בחירת קפטן",
  ])

  def render_recommendation_cards(pos_num, count=6):
    targets = [
        p
        for p in all_players.values()
        if p["pos_code"] == pos_num and p["status"] == "a"
    ]
    targets = sorted(targets, key=lambda x: x["score"], reverse=True)[:count]

    for i, p in enumerate(targets):
      tier = "tier-1" if i < 2 else ("tier-2" if i < 4 else "tier-3")
      st.markdown(
          f"""
            <div class="target-card {tier}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:bold; font-size:15px; color:#f8fafc;">
                        {p['name']} <span style="font-size:12px; color:#94a3b8;">({p['team']})</span>
                    </span>
                    <span style="font-size:14px; font-weight:bold; color:#38bdf8;">£{p['cost']}m</span>
                </div>
                <div style="margin:6px 0; font-size:12px; color:#cbd5e1;">
                    💡 <b>נימוק:</b> {p['reason']}
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; color:#94a3b8; border-top:1px solid #1e293b; padding-top:6px; margin-top:6px;">
                    <span>כושר: <b>{p['form']}</b> | xGI: <b>{p['xgi']}</b> | בעלות: <b>{p['selected_by']}%</b></span>
                    <div>משחק קרוב: <span class="badge fdr-{p['next_fdr']}">{p['next_match']}</span> | 3 משחקים: {p['fixtures']}</div>
                </div>
            </div>
            """,
          unsafe_allow_html=True,
      )

  with sub_fwd:
    render_recommendation_cards(4, 6)
  with sub_mid:
    render_recommendation_cards(3, 7)
  with sub_def:
    render_recommendation_cards(2, 6)
  with sub_gk:
    render_recommendation_cards(1, 4)

  with sub_cap:
    st.markdown("#### 👑 המלצות קפטן למחזור הקרוב")
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
                בעלות: <b>{shield['selected_by']}%</b> | מחיר: £{shield['cost']}m<br>
                משחק הבא: <b>{shield['next_match']}</b><br>
                💡 נימוק: {shield['reason']}
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
                בעלות: <b>{sword['selected_by']}% בלבד</b> | מחיר: £{sword['cost']}m<br>
                משחק הבא: <b>{sword['next_match']}</b><br>
                💡 נימוק: {sword['reason']}
                </p>
            </div>
            """,
          unsafe_allow_html=True,
      )

# --- טאב 3: מחשבון חילוף אישי ---
with tab_transfer:
  st.subheader("🎯 מחשבון החילוף הטוב ביותר לסגל שלך")
  all_my_players = starters + bench
  weak_link = min(
      all_my_players,
      key=lambda x: (
          x["score"] if x["status"] == "a" and x["chance"] == 100 else -10
      ),
  )
  max_budget = weak_link["cost"] + bank_balance

  best_replacement = None
  highest_score = -1
  for p in all_players.values():
    if (
        p["id"] not in [x["id"] for x in all_my_players]
        and p["pos_code"] == weak_link["pos_code"]
        and p["cost"] <= max_budget
        and p["status"] == "a"
    ):
      if p["score"] > highest_score:
        highest_score = p["score"]
        best_replacement = p

  c_out, c_in = st.columns(2)
  with c_out:
    st.markdown(
        f'<div class="health-box health-red"><strong style="color:#fca5a5;'
        f' font-size:14px;">🔴 שחקן מומלץ למכירה (OUT)</strong><br><h4'
        f' style="margin:4px 0; color:#fff;">{weak_link["name"]}'
        f' ({weak_link["team"]})</h4><span style="font-size:12px;'
        f' color:#cbd5e1;">עמדה: {weak_link["pos"]} | מחיר:'
        f' £{weak_link["cost"]}m<br>כושר: {weak_link["form"]} | FDR קרוב:'
        f' {weak_link["avg_fdr"]}</span></div>',
        unsafe_allow_html=True,
    )
  with c_in:
    if best_replacement:
      rem_bank = max_budget - best_replacement["cost"]
      st.markdown(
          f'<div class="health-box health-green"><strong style="color:#6ee7b7;'
          f' font-size:14px;">🟢 שחקן מומלץ לרכש (IN)</strong><br><h4'
          f' style="margin:4px 0; color:#fff;">{best_replacement["name"]}'
          f' ({best_replacement["team"]})</h4><span style="font-size:12px;'
          f' color:#cbd5e1;">מחיר: £{best_replacement["cost"]}m (נשאר בבנק:'
          f' £{rem_bank:.1f}m)<br>כושר: {best_replacement["form"]} | משחק'
          f' הבא: {best_replacement["next_match"]}</span></div>',
          unsafe_allow_html=True,
      )

# --- טאב 4: בריאות הסגל ---
with tab_health:
  st.subheader("🚦 רמזור בריאות הסגל")
  yellows = [
      p
      for p in all_my_players
      if p["status"] == "a"
      and p["chance"] == 100
      and (p["avg_fdr"] > 2.8 or p["form"] < 3.0)
  ]
  reds = [
      p for p in all_my_players if p["status"] != "a" or p["chance"] < 100
  ]

  st.markdown(f"#### 🔴 מוקדי חירום לטיפול מיידי ({len(reds)})")
  if reds:
    for p in reds:
      st.markdown(
          f'<div class="health-box health-red"><b>{p["name"]} ({p["team"]})</b>'
          f' - סיכוי שיתוף: {p["chance"]}% | לוח: {p["fixtures"]}</div>',
          unsafe_allow_html=True,
      )
  else:
    st.success("אין פציעות או השעיות ידועות בסגל!")

  st.markdown(f"#### 🟡 שחקנים תחת מעקב / לוח קשה ({len(yellows)})")
  for p in yellows:
    st.markdown(
        f'<div class="health-box health-yellow"><b>{p["name"]} ({p["team"]})</b>'
        f' - כושר: {p["form"]} | לוח: {p["fixtures"]} (FDR ממוצע:'
        f' {p["avg_fdr"]})</div>',
        unsafe_allow_html=True,
    )

# --- טאב 5: צ'אט AI ---
with tab_chat:
  st.subheader(f"💬 יועץ ה-AI האישי של {my_team_name}")
  if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": (
            f"היי! אני מחובר לסגל שלך ({my_team_name}) לקראת מחזור {next_gw}."
            " שאל אותי כל שאלה: חילופים, קפטן או ניהול ספסל."
        ),
    }]

  for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
      st.write(msg["content"])

  if prompt := st.chat_input("שאל שאלה טקטית..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
      st.write(prompt)

    if not api_key:
      reply = "⚠️ נא להזין מפתח Gemini API בסרגל הצד להפעלת הצ'אט."
    else:
      my_squad_summary = [
          {
              "name": p["name"],
              "team": p["team"],
              "pos": p["pos"],
              "cost": p["cost"],
              "form": p["form"],
              "chance": p["chance"],
              "next": p["next_match"],
          }
          for p in all_my_players
      ]
      system_instruction = f"""
אתה מאמן ואסטרטג FPL מוביל בעולם המכוון למקום ב-Top 50,000.
מחזור המשחקים הקרוב: {next_gw}.
פרטי הקבוצה המעודכנת לקראת מחזור {next_gw}:
שם קבוצה: {my_team_name}, דירוג נוכחי: {rank_display}, יתרה בבנק: £{bank_balance:.1f}m.
15 השחקנים של המשתמש:
{json.dumps(my_squad_summary, ensure_ascii=False)}

ענה בעברית, בצורה ממוקדת, חדה, טקטית ומבוססת נתונים (xGI, Form, FDR).
"""
      models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash"]
      reply = None
      for model_name in models_to_try:
        if reply:
          break
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": system_instruction}]},
                {"role": "user", "parts": [{"text": prompt}]},
            ]
        }
        for attempt in range(3):
          try:
            res = requests.post(url, headers=headers, json=payload, timeout=12)
            if res.status_code == 200:
              reply = res.json()["candidates"][0]["content"]["parts"][0]["text"]
              break
            elif res.status_code in [503, 429]:
              time.sleep(1.5)
              continue
            else:
              break
          except Exception:
            time.sleep(1.0)
            continue

      if not reply:
        reply = "⚠️ עומס רגעי בשרת. נסה שוב בעוד מספר שניות."

    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
      st.write(reply)
