import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="FPL Elite Scout | Top 100K Engine",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# עיצוב מתקדם: מגרש, כרטיסי שחקנים וממשק מובייל
st.markdown(
    """
    <style>
    .main { direction: rtl; text-align: right; background-color: #0b0f19; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    
    /* מגרש כדורגל */
    .pitch {
        background: radial-gradient(circle, #1e3a24 0%, #112215 100%);
        border: 2px solid #2d5a35;
        border-radius: 16px;
        padding: 20px 10px;
        margin: 15px 0;
        box-shadow: inset 0 0 40px rgba(0,0,0,0.6);
    }
    .pitch-row {
        display: flex;
        justify-content: space-around;
        margin-bottom: 16px;
        flex-wrap: wrap;
    }
    .player-card {
        background: rgba(15, 23, 42, 0.88);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 8px 6px;
        text-align: center;
        min-width: 85px;
        max-width: 95px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.4);
        backdrop-filter: blur(4px);
    }
    .player-card-cap { border: 2px solid #facc15; }
    .player-name { font-weight: bold; font-size: 11px; color: #f8fafc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .player-team { font-size: 9px; color: #94a3b8; }
    .player-fxt { font-size: 9px; font-weight: bold; padding: 2px 4px; border-radius: 4px; margin-top: 4px; display: inline-block; }
    .fdr-2 { background: #15803d; color: #fff; }
    .fdr-3 { background: #475569; color: #fff; }
    .fdr-4 { background: #b91c1c; color: #fff; }
    .fdr-5 { background: #7f1d1d; color: #fff; }

    /* כרטיסי מידע */
    .trap-card { background: #2a1215; border-right: 4px solid #ef4444; padding: 12px; border-radius: 8px; margin-bottom: 8px; }
    .gem-card { background: #0e2a1b; border-right: 4px solid #10b981; padding: 12px; border-radius: 8px; margin-bottom: 8px; }
    .metric-box { background: #1e293b; border-radius: 10px; padding: 10px; text-align: center; border: 1px solid #334155; }
    </style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=600)
def load_all_fpl_data():
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

  pos_map = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
  all_players = []

  for el in elements:
    if el["status"] == "u":
      continue

    # חישוב FDR ולוח משחקים
    upcoming = []
    fdr_list = []
    for f in fixtures:
      if f["event"] in [next_gw, next_gw + 1, next_gw + 2]:
        if f["team_h"] == el["team"]:
          opp = teams[f["team_a"]]["short_name"]
          diff = f["team_h_difficulty"]
          upcoming.append(f"{opp}(H)")
          fdr_list.append(diff)
        elif f["team_a"] == el["team"]:
          opp = teams[f["team_h"]]["short_name"]
          diff = f["team_a_difficulty"]
          upcoming.append(f"{opp}(A)")
          fdr_list.append(diff)

    avg_fdr = sum(fdr_list) / len(fdr_list) if fdr_list else 3.0
    form = float(el["form"])
    xp = float(el["ep_next"]) if el.get("ep_next") else 0.0
    xgi = float(el.get("expected_goal_involvements", 0.0))
    goals_assists = el["goals_scored"] + el["assists"]
    cost = el["now_cost"] / 10

    # אלגוריתם ציון מאוזן לטווח ארוך
    composite_score = (
        (xp * 1.6) + (form * 1.1) + (xgi * 1.2) + ((5.2 - avg_fdr) * 1.4)
    )

    # מדד "בועה": שחקן שמחזיק בהרבה נקודות/שערים בפועל ביחס ל-xGI נמוך מאוד + לוח קשה שמגיע
    bubble_index = round(
        (goals_assists - xgi) * (avg_fdr / 2.5), 2
    )  # ככל שגבוה = יותר בועתי

    next_match_str = upcoming[0] if upcoming else "—"
    next_fdr = fdr_list[0] if fdr_list else 3

    all_players.append({
        "ID": el["id"],
        "שם": el["web_name"],
        "קבוצה": teams[el["team"]]["short_name"],
        "עמדה": pos_map[el["element_type"]],
        "עמדה_קוד": el["element_type"],
        "מחיר": cost,
        "כושר": form,
        "xGI": xgi,
        "שערים_בישולים": goals_assists,
        "נקודות צפויות": xp,
        "בעלות %": float(el["selected_by_percent"]),
        "סטטוס": el["status"],
        "סיכוי שיתוף": (
            el["chance_of_playing_next_round"]
            if el["chance_of_playing_next_round"] is not None
            else 100
        ),
        "ציון אלגוריתם": round(composite_score, 2),
        "מדד בועה": bubble_index,
        "FDR ממוצע": round(avg_fdr, 2),
        "משחק הבא": next_match_str,
        "next_fdr": next_fdr,
        "3 משחקים": " | ".join(upcoming),
    })

  return pd.DataFrame(all_players), next_gw


df, next_gw = load_all_fpl_data()

# כותרת ראשית ומדדים
st.title("⚽ FPL Elite Decision Engine")
st.caption(f"תוכנית פעולה אסטרטגית לקראת GW{next_gw} | יעד שנתי: Top 100,000")

col1, col2, col3 = st.columns(3)
with col1:
  st.markdown(
      '<div class="metric-box"><div'
      ' style="color:#38bdf8;font-size:12px;">מחזור יעד</div><div'
      f' style="font-size:18px;font-weight:bold;">GW {next_gw}</div></div>',
      unsafe_allow_html=True,
  )
with col2:
  st.markdown(
      '<div class="metric-box"><div'
      ' style="color:#10b981;font-size:12px;">פילוסופיה</div><div'
      ' style="font-size:18px;font-weight:bold;">אנטי-הייפ (EV)</div></div>',
      unsafe_allow_html=True,
  )
with col3:
  st.markdown(
      '<div class="metric-box"><div'
      ' style="color:#f59e0b;font-size:12px;">יעד עולמי</div><div'
      ' style="font-size:18px;font-weight:bold;">Top 100K 🏆</div></div>',
      unsafe_allow_html=True,
  )

st.write("")

# טאבים ראשיים
tab_pitch, tab_trap, tab_captain, tab_strategy = st.tabs([
    "🟢 הרכב מגרש (3-4-3)",
    "🚨 רדאר בועות ומלכודות",
    "👑 זירת הקפטנים",
    "🧭 מפת צ'יפים וחוקי 100K",
])

# סינון שחקנים כשירים
fit_df = df[(df["סטטוס"] == "a") & (df["סיכוי שיתוף"] == 100)]

# --- טאב 1: מגרש כדורגל חי ---
with tab_pitch:
  st.subheader("📋 ההרכב האופטימלי על המגרש (תקציב £100m)")
  st.caption("נבחר על בסיס תוחלת שערים (xGI), לוח משחקים ירוק ויציבות הרכב:")

  best_gk = (
      fit_df[fit_df["עמדה_קוד"] == 1]
      .sort_values(by="ציון אלגוריתם", ascending=False)
      .head(1)
  )
  best_defs = (
      fit_df[fit_df["עמדה_קוד"] == 2]
      .sort_values(by="ציון אלגוריתם", ascending=False)
      .head(3)
  )
  best_mids = (
      fit_df[fit_df["עמדה_קוד"] == 3]
      .sort_values(by="ציון אלגוריתם", ascending=False)
      .head(4)
  )
  best_fwds = (
      fit_df[fit_df["עמדה_קוד"] == 4]
      .sort_values(by="ציון אלגוריתם", ascending=False)
      .head(3)
  )

  def render_card(p, is_cap=False):
    cap_class = "player-card-cap" if is_cap else ""
    cap_badge = "👑 " if is_cap else ""
    fdr_class = f"fdr-{p['next_fdr']}"
    return f"""
        <div class="player-card {cap_class}">
            <div class="player-name">{cap_badge}{p['שם']}</div>
            <div class="player-team">{p['קבוצה']} | £{p['מחיר']}m</div>
            <div class="player-fxt {fdr_class}">{p['משחק הבא']}</div>
        </div>
        """

  # בניית המגרש ב-HTML
  pitch_html = '<div class="pitch">'

  # חלוצים
  pitch_html += '<div class="pitch-row">'
  for _, row in best_fwds.iterrows():
    pitch_html += render_card(row, is_cap=False)
  pitch_html += "</div>"

  # קשרים (הקשר המוביל מקבל קפטן)
  pitch_html += '<div class="pitch-row">'
  for i, (_, row) in enumerate(best_mids.iterrows()):
    pitch_html += render_card(row, is_cap=(i == 0))
  pitch_html += "</div>"

  # בלמים
  pitch_html += '<div class="pitch-row">'
  for _, row in best_defs.iterrows():
    pitch_html += render_card(row, is_cap=False)
  pitch_html += "</div>"

  # שוער
  pitch_html += '<div class="pitch-row">'
  for _, row in best_gk.iterrows():
    pitch_html += render_card(row, is_cap=False)
  pitch_html += "</div>"

  pitch_html += "</div>"
  st.markdown(pitch_html, unsafe_allow_html=True)

# --- טאב 2: רדאר בועות ומלכודות (חשיבה עמוקה על קבוצות מומנטום) ---
with tab_trap:
  st.subheader("🚨 ניתוח בועות: ממי חובה להתרחק עכשיו?")
  st.markdown("""
    מנג'רים ממוצעים רוכשים שחקנים שנמצאים ברצף הבקעות מזליקי. 
    **שחקני טופ 100K יודעים:** כשתפוקת ה-xG/xA נמוכה ולוח המשחקים מול הגנות קשוחות מתקרב – **הנפילה היא בלתי נמנעת**.
    """)

  # איתור בועות מובהקות
  bubbles = (
      df[
          (df["שערים_בישולים"] >= 2)
          & (df["מדד בועה"] > 1.2)
          & (df["בעלות %"] > 6)
      ]
      .sort_values(by="מדד בועה", ascending=False)
      .head(5)
  )

  st.markdown("#### ⚠️ שחקנים בסיכון נסיגה קיצונית (Sell / Avoid)")
  for _, b in bubbles.iterrows():
    st.markdown(
        f"""
        <div class="trap-card">
            <strong style="color:#fca5a5; font-size:14px;">⛔ {b['שם']} ({b['קבוצה']}) - מחיר: £{b['מחיר']}m</strong><br>
            <span style="font-size:11px; color:#cbd5e1;">
            כבש/בישל בפועל: <b>{b['שערים_בישולים']}</b> | סך xGI שייצר: <b>{b['xGI']} בלבד</b><br>
            📅 3 המשחקים הקרובים: <b>{b['3 משחקים']}</b> (FDR ממוצע: {b['FDR ממוצע']})
            </span><br>
            <span style="font-size:10px; color:#ef4444; font-weight:bold;">פסיקת סוכן: בועה בהתהוות. מכור ברווח או הימנע מרכישה!</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.write("")
  st.markdown("#### 💎 מציאות שקטות: שחקנים מתחת לרדאר (Buy)")
  st.caption("שחקנים שמייצרים מצבים איכותיים (xGI גבוה) אך סבלו מחוסר מזל:")

  gems = (
      fit_df[
          (fit_df["xGI"] > fit_df["שערים_בישולים"])
          & (fit_df["FDR ממוצע"] <= 2.8)
          & (fit_df["מחיר"] <= 8.0)
      ]
      .sort_values(by="ציון אלגוריתם", ascending=False)
      .head(4)
  )

  for _, g in gems.iterrows():
    st.markdown(
        f"""
        <div class="gem-card">
            <strong style="color:#6ee7b7; font-size:14px;">✅ {g['שם']} ({g['קבוצה']}) - מחיר: £{g['מחיר']}m</strong><br>
            <span style="font-size:11px; color:#cbd5e1;">
            ייצר xGI של <b>{g['xGI']}</b> (מעל התפוקה בפועל) | לוח קרוב: <b>{g['3 משחקים']}</b>
            </span><br>
            <span style="font-size:10px; color:#10b981; font-weight:bold;">פסיקת סוכן: פוטנציאל התפוצצות נקודות במחזורים הקרובים.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- טאב 3: זירת הקפטנים ---
with tab_captain:
  st.subheader("👑 קרב קפטן ראשי: עוגן מול דיפרנשיאל")

  premiums = fit_df[fit_df["מחיר"] >= 7.5].sort_values(
      by=["נקודות צפויות", "ציון אלגוריתם"], ascending=False
  )
  shield = premiums.iloc[0]
  diff_cand = premiums[premiums["בעלות %"] < 15]
  sword = diff_cand.iloc[0] if not diff_cand.empty else premiums.iloc[1]

  c1, c2 = st.columns(2)
  with c1:
    st.markdown(
        f"""
        <div style="background:#0f2a24; border:1px solid #059669; padding:15px; border-radius:12px;">
            <span style="background:#059669; color:white; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:bold;">🛡️ קפטן מגן (SHIELD)</span>
            <h3 style="margin:8px 0; color:#ecfdf5;">{shield['שם']} ({shield['קבוצה']})</h3>
            <p style="font-size:12px; color:#a7f3d0; margin:0;">
            בעלות עולמית: <b>{shield['בעלות %']}%</b><br>
            נקודות צפויות (xP): <b>{shield['נקודות צפויות']}</b><br>
            משחק הבא: <b>{shield['משחק הבא']}</b>
            </p>
            <hr style="border-color:#065f46; margin:8px 0;">
            <span style="font-size:11px; color:#d1fae5;">הבחירה הבטוחה לשמירה על יציבות ומניעת צניחה בדירוג.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

  with c2:
    st.markdown(
        f"""
        <div style="background:#2a1e0f; border:1px solid #d97706; padding:15px; border-radius:12px;">
            <span style="background:#d97706; color:white; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:bold;">⚔️ קפטן חרב (SWORD)</span>
            <h3 style="margin:8px 0; color:#fffbeb;">{sword['שם']} ({sword['קבוצה']})</h3>
            <p style="font-size:12px; color:#fde68a; margin:0;">
            בעלות עולמית: <b>{sword['בעלות %']}% בלבד</b><br>
            סך xGI: <b>{sword['xGI']}</b><br>
            משחק הבא: <b>{sword['משחק הבא']}</b>
            </p>
            <hr style="border-color:#92400e; margin:8px 0;">
            <span style="font-size:11px; color:#fef3c7;">הימור מחושב במקרה שאתה בפיגור בליגה פרטית.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- טאב 4: מפת צ'יפים וחוקי 100K ---
with tab_strategy:
  st.subheader("🧭 אסטרטגיית מאקרו לטווח ארוך")
  st.markdown("""
    #### 1. חוק צבירת החילופים (Roll Transfers)
    * מנג'רים שמגיעים לטופ 100K מתייחסים לחילוף יחיד כאל "חצי חילוף".
    * שמירה של חילוף אחד מאפשרת לך לבצע חילוף כפול במחזור שאחריו — מה שפותח שינויי מבנה (כמו מימון חלוץ יקר על חשבון בלם).

    #### 2. תזמון הפעלת צ'יפים
    * **Wildcard 1:** מחזורים 6-11, כאשר מועדוני הצמרת משלימים התייצבות הרכבים ומתחילים רצפי משחקים ירוקים.
    * **Triple Captain & Bench Boost:** שמור אך ורק למחזורים כפולים עמוקים (Double Gameweeks) שמתקיימים לקראת סוף העונה.
    * **Free Hit:** נשמר בלעדית לשבוע גביע שבו רוב הקבוצות לא משחקות (Blank Gameweek).

    #### 3. אפס מינוסים
    * כל `-4` שאתה לוקח הוא שער אחד פחות שהסגל שלך צריך להבקיע. ההבדל המצטבר לאורך 38 מחזורים שווה כ-40-50 נקודות — בדיוק המרחק בין מקום 200,000 למקום 80,000 בעולם.
    """)
