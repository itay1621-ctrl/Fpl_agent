import json
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="FPL Top 50K Engine & AI Chat",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
.main { direction: rtl; text-align: right; background-color: #0b0f19; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
.metric-box { background: #162032; border-radius: 8px; padding: 8px; text-align: center; border: 1px solid #243550; }
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
.badge-fdr-2 { background: #15803d; color: #fff; }
.badge-fdr-3 { background: #475569; color: #fff; }
.badge-fdr-4 { background: #b91c1c; color: #fff; }
.badge-fdr-5 { background: #7f1d1d; color: #fff; }
.stChatMessage { direction: rtl; text-align: right; }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=600)
def load_top50k_data():
  base = "https://fantasy.premierleague.com/api/"
  bootstrap = requests.get(f"{base}bootstrap-static/").json()
  fixtures = requests.get(f"{base}fixtures/").json()

  teams = {t["id"]: t for t in bootstrap["teams"]}
  elements = bootstrap["elements"]

  next_gw = 4
  for ev in bootstrap["events"]:
    if ev.get("is_next"):
      next_gw = ev["id"]
      break

  elite_defenses = ["ARS", "MCI", "LIV", "NEW", "CHE"]
  pos_map = {1: "שוערים", 2: "הגנה", 3: "קישור", 4: "התקפה"}
  records = []

  for el in elements:
    if el["status"] != "a":
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

    def_boost = (
        1.3
        if (el["element_type"] in [1, 2] and team_short in elite_defenses)
        else 0.85
    )
    att_boost = (
        1.2
        if (el["element_type"] in [3, 4] and (form >= 4.5 or goals_assists >= 2))
        else 1.0
    )

    score = (
        (form * 1.4)
        + (xgi * 1.3)
        + (threat * 0.015)
        + ((5.3 - avg_fdr) * 1.4)
        + (1.2 if net_transfers > 35000 else 0.0)
    )
    score *= def_boost if el["element_type"] in [1, 2] else att_boost

    if el["element_type"] == 1:
      reason = "שוער יציב מאחורי הגנה חזקה"
    elif el["element_type"] == 2:
      reason = (
          "מגן תוקף עם איום הבקעה/בישול"
          if threat > 40
          else "עוגן רשת נקייה מהגנת צמרת"
      )
    elif el["element_type"] in [3, 4]:
      reason = (
          "כושר הבקעה לוהט"
          if form >= 5.5
          else ("יוצר מדדי xG/xA גבוהים" if xgi >= 1.4 else "לוח נוח ומומנטום")
      )

    records.append({
        "ID": el["id"],
        "שם": el["web_name"],
        "קבוצה": team_short,
        "עמדה_שם": pos_map[el["element_type"]],
        "עמדה_קוד": el["element_type"],
        "מחיר": cost,
        "כושר": form,
        "xGI": xgi,
        "מעורבות_בשערים": goals_assists,
        "בעלות %": float(el["selected_by_percent"]),
        "ציון": round(score, 2),
        "נימוק": reason,
        "משחק_קרוב": upcoming[0] if upcoming else "—",
        "fdr_קרוב": fdr_list[0] if fdr_list else 3,
        "לוח_3_משחקים": " | ".join(upcoming),
    })

  return pd.DataFrame(records), next_gw


df, next_gw = load_top50k_data()

# סרגל צד - חיבור מפתח API
st.sidebar.header("🤖 הגדרות סוכן AI")
api_key = st.sidebar.text_input(
    "הזן Google Gemini API Key:",
    type="password",
    help="מפתח חינמי מ-Google AI Studio",
)

st.title("🏆 FPL Top 50K Engine & AI Assistant")
st.caption(f"הכנה למחזור {next_gw} | רדאר רכש + סוכן שיחה טקטי")

# טאבים כולל צ'אט בוט
tab_fwds, tab_mids, tab_defs, tab_gks, tab_captain, tab_chat = st.tabs([
    "⚡ חלוצים",
    "🎯 קשרים",
    "🛡️ הגנה",
    "🧤 שוערים",
    "👑 קפטן",
    "💬 צ'אט בוט AI",
])


def display_targets(pos_code, top_n=6):
  subset = (
      df[df["עמדה_קוד"] == pos_code]
      .sort_values(by="ציון", ascending=False)
      .head(top_n)
  )
  for i, (_, p) in enumerate(subset.iterrows()):
    tier_class = "tier-1" if i < 2 else ("tier-2" if i < 4 else "tier-3")
    fdr_badge = f'<span class="badge badge-fdr-{p["fdr_קרוב"]}">{p["משחק_קרוב"]}</span>'
    st.markdown(
        f"""
        <div class="target-card {tier_class}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:bold; font-size:15px; color:#f8fafc;">
                    {p['שם']} <span style="font-size:12px; color:#94a3b8;">({p['קבוצה']})</span>
                </span>
                <span style="font-size:14px; font-weight:bold; color:#38bdf8;">£{p['מחיר']}m</span>
            </div>
            <div style="margin: 6px 0; font-size:12px; color:#cbd5e1;">
                💡 <b>נימוק:</b> {p['נימוק']}
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; color:#94a3b8; border-top: 1px solid #1e293b; padding-top:6px; margin-top:6px;">
                <span>כושר: <b>{p['כושר']}</b> | xGI: <b>{p['xGI']}</b> | בעלות: <b>{p['בעלות %']}%</b></span>
                <div>3 משחקים: {p['לוח_3_משחקים']} {fdr_badge}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with tab_fwds:
  st.subheader("החלוצים המובילים")
  display_targets(4, top_n=6)

with tab_mids:
  st.subheader("הקשרים המובילים")
  display_targets(3, top_n=7)

with tab_defs:
  st.subheader("שחקני ההגנה המובילים")
  display_targets(2, top_n=6)

with tab_gks:
  st.subheader("השוערים המובילים")
  display_targets(1, top_n=4)

with tab_captain:
  st.subheader("👑 בחירת קפטן למחזור הקרוב")
  premiums = df[df["מחיר"] >= 7.5].sort_values(
      by=["ציון", "כושר"], ascending=False
  )
  shield = premiums.iloc[0]
  diff_cand = premiums[premiums["בעלות %"] < 18]
  sword = diff_cand.iloc[0] if not diff_cand.empty else premiums.iloc[1]

  col_a, col_b = st.columns(2)
  with col_a:
    st.markdown(
        f'<div style="background:#0f2a24; border:1px solid #059669; padding:12px;'
        ' border-radius:10px;"><span style="background:#059669; color:white;'
        ' padding:2px 6px; border-radius:3px; font-size:9px;'
        ' font-weight:bold;">🛡️ קפטן מגן</span><h4 style="margin:6px 0;'
        f' color:#ecfdf5;">{shield["שם"]} ({shield["קבוצה"]})</h4><p'
        ' style="font-size:11px; color:#a7f3d0; margin:0;">בעלות:'
        f' <b>{shield["בעלות %"]}%</b> | מחיר: £{shield["מחיר"]}m<br>משחק הבא:'
        f' <b>{shield["משחק_קרוב"]}</b><br>💡 נימוק:'
        f' {shield["נימוק"]}</p></div>',
        unsafe_allow_html=True,
    )
  with col_b:
    st.markdown(
        f'<div style="background:#2a1e0f; border:1px solid #d97706; padding:12px;'
        ' border-radius:10px;"><span style="background:#d97706; color:white;'
        ' padding:2px 6px; border-radius:3px; font-size:9px;'
        ' font-weight:bold;">⚔️ קפטן דיפרנשיאל</span><h4 style="margin:6px 0;'
        f' color:#fffbeb;">{sword["שם"]} ({sword["קבוצה"]})</h4><p'
        ' style="font-size:11px; color:#fde68a; margin:0;">בעלות:'
        f' <b>{sword["בעלות %"]}% בלבד</b> | מחיר: £{sword["מחיר"]}m<br>משחק'
        f' הבא: <b>{sword["משחק_קרוב"]}</b><br>💡 נימוק:'
        f' {sword["נימוק"]}</p></div>',
        unsafe_allow_html=True,
    )

# --- טאב צ'אט בוט AI ---
with tab_chat:
  st.subheader("💬 שאל את סוכן ה-Top 50K")
  st.caption(
      "הסוכן מסתמך על נתוני ה-xGI, מחירי השחקנים ולוח המשחקים המעודכנים"
      " באפליקציה."
  )

  if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": (
            "שלום! אני סוכן ה-FPL שלך ל-Top 50K. שאל אותי כל שאלה: התלבטות בין"
            " שחקנים, המלצות לפי תקציב, חילופים או צ'יפים."
        ),
    }]

  # הצגת היסטוריית שיחה
  for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
      st.write(msg["content"])

  # קבלת שאלה מהמשתמש
  if prompt := st.chat_input("שאל שאלה טקטית (למשל: את מי להביא עד 6.5 מיליון?)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
      st.write(prompt)

    if not api_key:
      reply = (
          "⚠️ **נא להזין מפתח Gemini API בסרגל הצד (Sidebar)** כדי להפעיל את"
          " מנוע השיחה החינמי."
      )
    else:
      # הכנת תקציר נתוני השחקנים החמים כהקשר ל-AI
      top_context = (
          df.sort_values(by="ציון", ascending=False)
          .head(25)[
              [
                  "שם",
                  "קבוצה",
                  "עמדה_שם",
                  "מחיר",
                  "כושר",
                  "xGI",
                  "לוח_3_משחקים",
                  "נימוק",
              ]
          ]
          .to_dict(orient="records")
      )

      system_instruction = f"""
            אתה סוכן AI מומחה ואסטרטג עליון ב-Fantasy Premier League המכוון ל-Top 50,000 בעולם.
            מחזור היעד הקרוב הוא מחזור {next_gw}.
            ענה בעברית בצורה חדה, ממוקדת, מקצועית ומבוססת נתונים (EV, xGI, מחיר ולוח משחקים).
            להלן נתוני השחקנים המובילים בליגה כרגע:
            {json.dumps(top_context, ensure_ascii=False)}
            """

      url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
      headers = {"Content-Type": "application/json"}
      payload = {
          "contents": [
              {"role": "user", "parts": [{"text": system_instruction}]},
              {"role": "user", "parts": [{"text": prompt}]},
          ]
      }

      try:
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200:
          reply = res.json()["candidates"][0]["content"]["parts"][0]["text"]
        else:
          reply = f"שגיאה בתקשורת עם ה-AI (קוד {res.status_code}). ודא שהמפתח תקין."
      except Exception as e:
        reply = "שגיאת רשת בעת פנייה למודל."

    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
      st.write(reply)
