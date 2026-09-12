import json
import time
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="FPL Elite Scout | Personal Team Engine",
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

  pos_map = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
  processed = {}

  for el_id, el in elements.items():
    if el["status"] == "u":
      continue

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

    score = (
        (form * 1.5)
        + (xgi * 1.4)
        + (threat * 0.015)
        + ((5.2 - avg_fdr) * 1.3)
        + (1.0 if net_transfers > 30000 else 0.0)
    )

    processed[el_id] = {
        "id": el_id,
        "name": el["web_name"],
        "team": teams[el["team"]]["short_name"],
        "pos": pos_map[el["element_type"]],
        "pos_code": el["element_type"],
        "cost": cost,
        "form": form,
        "xgi": xgi,
        "goals_assists": goals_assists,
        "score": round(score, 2),
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

    # בדיקה האם הופעל Free Hit במחזור הקודם
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

# הכנת רשימת השחקנים הבסיסית
current_squad_ids = [p["element"] for p in my_picks]

# --- רכיב עריכת חילופים שבוצעו לקראת GW4 בסרגל הצד ---
st.sidebar.markdown("---")
st.sidebar.subheader("🔄 עדכון חילופים שבוצעו ל-GW4")
st.sidebar.caption("בחר שחקנים שהחלפת לקראת המחזור הקרוב:")

num_transfers = st.sidebar.selectbox(
    "כמה חילופים ביצעת?", [0, 1, 2, 3], index=1
)

# שמות כל שחקני הליגה לבחירה
all_player_names = {
    p["name"] + f" ({p['team']}) - £{p['cost']}m": pid
    for pid, p in all_players.items()
}
player_options = sorted(list(all_player_names.keys()))

transfers_made = []
for i in range(num_transfers):
  st.sidebar.markdown(f"**חילוף #{i+1}**")

  # שחקנים שקיימים כרגע בסגל
  squad_names = [
      all_players[pid]["name"] + f" ({all_players[pid]['team']})"
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
        if all_players[pid]["name"] + f" ({all_players[pid]['team']})"
        == p_out_name
    )
    in_id = all_player_names[p_in_name]
    transfers_made.append((out_id, in_id))

# החלת החילופים על הסגל בפועל ועדכון הבנק
for out_id, in_id in transfers_made:
  for p in my_picks:
    if p["element"] == out_id:
      bank_balance += all_players[out_id]["cost"] - all_players[in_id]["cost"]
      p["element"] = in_id
      break

# הרכבת רשימות 11 פותחים וספסל
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

# תצוגת ראשית
st.title(f"⚽ FPL Command Center | {my_team_name or 'Top 50K Engine'}")
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

tab_squad, tab_transfer, tab_health, tab_chat = st.tabs([
    "🟢 הסגל שלי על המגרש",
    "🎯 מחשבון חילוף נוסף",
    "🚦 רמזור בריאות הסגל",
    "💬 צ'אט בוט אישי (Top 50K)",
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


with tab_squad:
  st.subheader("📋 ההרכב הפותח שלך ל-GW4")
  st.caption("כולל החילופים שהגדרת בסרגל הצד:")

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

with tab_transfer:
  st.subheader("🎯 מחשבון החילוף הטוב ביותר לסגל הנוכחי")
  st.caption("בודק מי החוליה החלשה ביותר שנותרה בסגל שלך מול שחקני הרכש בליגה:")

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
    else:
      st.info("לא נמצא שחקן רכש מתאים בתקציב הנוכחי.")

with tab_health:
  st.subheader("🚦 ניתוח מצב 15 השחקנים שלך")
  greens = [
      p
      for p in all_my_players
      if p["status"] == "a" and p["chance"] == 100 and p["avg_fdr"] <= 2.8
  ]
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
          f' - סטטוס פציעה/שיתוף: {p["chance"]}% | לוח: {p["fixtures"]}</div>',
          unsafe_allow_html=True,
      )
  else:
    st.success("אין פציעות או השעיות ידועות בסגל!")

  st.markdown(f"#### 🟡 שחקנים תחת מעקב / לוח קשה ({len(yellows)})")
  for p in yellows:
    st.markdown(
        f'<div class="health-box health-yellow"><b>{p["name"]} ({p["team"]})</b>'
        f' - כושר: {p["form"]} | 3 משחקים קרובים: {p["fixtures"]} (FDR ממוצע:'
        f' {p["avg_fdr"]})</div>',
        unsafe_allow_html=True,
    )

with tab_chat:
  st.subheader(f"💬 יועץ ה-AI האישי של {my_team_name}")
  st.caption(
      "הסוכן מעודכן ב-15 השחקנים שלך, ביתרת הבנק ובחילופים שהגדרת לקראת מחזור 4."
  )

  if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": (
            f"היי! אני מחובר לסגל המעודכן שלך לקראת מחזור 4 (יתרה בבנק:"
            f" £{bank_balance:.1f}m). שאל אותי כל שאלה: הרכב סופי, קפטן או ספסל."
        ),
    }]

  for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
      st.write(msg["content"])

  if prompt := st.chat_input("שאל את המאמן..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
      st.write(prompt)

    if not api_key:
      reply = "⚠️ נא להזין מפתח Gemini API בסרגל הצד (Sidebar) להפעלת הצ'אט."
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
