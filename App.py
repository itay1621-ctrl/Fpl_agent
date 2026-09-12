import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="FPL Elite Scout | Road to Top 100K",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# עיצוב מותאם מובייל ומגרש ללא בעיות רינדור
st.markdown(
    """
<style>
.main { direction: rtl; text-align: right; background-color: #0b0f19; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }

/* מגרש כדורגל */
.pitch {
    background: radial-gradient(circle, #1a3821 0%, #0d1e12 100%);
    border: 2px solid #234e2c;
    border-radius: 14px;
    padding: 18px 6px;
    margin: 15px 0;
    box-shadow: inset 0 0 35px rgba(0,0,0,0.6);
}
.pitch-row {
    display: flex;
    justify-content: space-around;
    align-items: center;
    margin-bottom: 14px;
    gap: 4px;
}
.p-card {
    background: rgba(15, 23, 42, 0.92);
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px 4px;
    text-align: center;
    width: 82px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.4);
}
.cap-border { border: 2px solid #facc15 !important; }
.p-name { font-weight: bold; font-size: 11px; color: #f8fafc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.p-team { font-size: 9px; color: #94a3b8; margin: 1px 0; }
.p-fxt { font-size: 9px; font-weight: bold; padding: 1px 4px; border-radius: 3px; display: inline-block; }

.fdr-2 { background: #15803d; color: #fff; }
.fdr-3 { background: #475569; color: #fff; }
.fdr-4 { background: #b91c1c; color: #fff; }
.fdr-5 { background: #7f1d1d; color: #fff; }

/* כרטיסי מידע ובועות */
.trap-card { background: #221013; border-right: 4px solid #ef4444; padding: 10px; border-radius: 6px; margin-bottom: 8px; }
.gem-card { background: #0c2417; border-right: 4px solid #10b981; padding: 10px; border-radius: 6px; margin-bottom: 8px; }
.metric-box { background: #1e293b; border-radius: 8px; padding: 8px; text-align: center; border: 1px solid #334155; }
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

    # מדד בועה (פער בין שערים/בישולים ל-xGI + לוח קשה)
    bubble_index = round((goals_assists - xgi) * (avg_fdr / 2.5), 2)

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

st.title("⚽ FPL Elite Decision Engine")
st.caption(f"תוכנית פעולה אסטרטגית לקראת GW{next_gw} | יעד: Top 100,000")

col1, col2, col3 = st.columns(3)
with col1:
  st.markdown(
      '<div class="metric-box"><div'
      ' style="color:#38bdf8;font-size:11px;">מחזור יעד</div><div'
      f' style="font-size:16px;font-weight:bold;">GW {next_gw}</div></div>',
      unsafe_allow_html=True,
  )
with col2:
  st.markdown(
      '<div class="metric-box"><div'
      ' style="color:#10b981;font-size:11px;">פילוסופיה</div><div'
      ' style="font-size:16px;font-weight:bold;">אנטי-הייפ (EV)</div></div>',
      unsafe_allow_html=True,
  )
with col3:
  st.markdown(
      '<div class="metric-box"><div'
      ' style="color:#f59e0b;font-size:11px;">יעד עולמי</div><div'
      ' style="font-size:16px;font-weight:bold;">Top 100K 🏆</div></div>',
      unsafe_allow_html=True,
  )

st.write("")

tab_pitch, tab_trap, tab_captain, tab_strategy = st.tabs([
    "🟢 הרכב מגרש (3-4-3)",
    "🚨 רדאר בועות ומלכודות",
    "👑 זירת הקפטנים",
    "🧭 אסטרטגיה וצ'יפים",
])

fit_df = df[(df["סטטוס"] == "a") & (df["סיכוי שיתוף"] == 100)]

# טאב 1: מגרש
with tab_pitch:
  st.subheader("📋 ההרכב האופטימלי על המגרש (£100m)")
  st.caption("משקלל xGI, כושר ולוח משחקים ירוק:")

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

  def build_card(p, is_cap=False):
    c_cls = "p-card cap-border" if is_cap else "p-card"
    c_badge = "👑 " if is_cap else ""
    return (
        f'<div class="{c_cls}">'
        f'<div class="p-name">{c_badge}{p["שם"]}</div>'
        f'<div class="p-team">{p["קבוצה"]} | £{p["מחיר"]}m</div>'
        f'<div class="p-fxt fdr-{p["next_fdr"]}">{p["משחק הבא"]}</div>'
        "</div>"
    )

  fwds_h = "".join(build_card(r) for _, r in best_fwds.iterrows())
  mids_h = "".join(
      build_card(r, is_cap=(i == 0))
      for i, (_, r) in enumerate(best_mids.iterrows())
  )
  defs_h = "".join(build_card(r) for _, r in best_defs.iterrows())
  gk_h = "".join(build_card(r) for _, r in best_gk.iterrows())

  pitch_html = (
      f'<div class="pitch">'
      f'<div class="pitch-row">{fwds_h}</div>'
      f'<div class="pitch-row">{mids_h}</div>'
      f'<div class="pitch-row">{defs_h}</div>'
      f'<div class="pitch-row">{gk_h}</div>'
      f"</div>"
  )
  st.markdown(pitch_html, unsafe_allow_html=True)

# טאב 2: בועות ומלכודות
with tab_trap:
  st.subheader("🚨 ניתוח בועות: ממי להתרחק עכשיו?")
  st.markdown(
      "אזהרה לגבי שחקנים וקבוצות שנמצאים במומנטום מקרי מעל ה-xGI ומול לוח קשה"
      " מתקרב:"
  )

  bubbles = (
      df[
          (df["שערים_בישולים"] >= 2)
          & (df["מדד בועה"] > 1.2)
          & (df["בעלות %"] > 6)
      ]
      .sort_values(by="מדד בועה", ascending=False)
      .head(5)
  )

  for _, b in bubbles.iterrows():
    st.markdown(
        f'<div class="trap-card"><strong style="color:#fca5a5; font-size:13px;">⛔'
        f" {b['שם']} ({b['קבוצה']}) - £{b['מחיר']}m</strong><br><span"
        f" style=\"font-size:11px; color:#cbd5e1;\">מעורבות בשערים:"
        f" <b>{b['שערים_בישולים']}</b> | סך xGI בפועל: <b>{b['xGI']}</b><br>📅"
        f" משחקים קרובים: <b>{b['3 משחקים']}</b></span><br><span"
        ' style="font-size:10px; color:#ef4444; font-weight:bold;">פסיקת סוכן:'
        " בועה. אל תקנה / שקול מכירה!</span></div>",
        unsafe_allow_html=True,
    )

  st.write("")
  st.subheader("💎 מציאות מתחת לרדאר (Under-performing xGI)")
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
        f'<div class="gem-card"><strong style="color:#6ee7b7; font-size:13px;">✅'
        f" {g['שם']} ({g['קבוצה']}) - £{g['מחיר']}m</strong><br><span"
        f" style=\"font-size:11px; color:#cbd5e1;\">ייצר xGI של <b>{g['xGI']}</b>"
        f" | לוח משחקים: <b>{g['3 משחקים']}</b></span><br><span"
        ' style="font-size:10px; color:#10b981; font-weight:bold;">פסיקת סוכן:'
        " פוטנציאל התפוצצות נקודות קרוב.</span></div>",
        unsafe_allow_html=True,
    )

# טאב 3: קפטן
with tab_captain:
  st.subheader("👑 קרב קפטן ראשי")

  premiums = fit_df[fit_df["מחיר"] >= 7.5].sort_values(
      by=["נקודות צפויות", "ציון אלגוריתם"], ascending=False
  )
  shield = premiums.iloc[0]
  diff_cand = premiums[premiums["בעלות %"] < 15]
  sword = diff_cand.iloc[0] if not diff_cand.empty else premiums.iloc[1]

  c1, c2 = st.columns(2)
  with c1:
    st.markdown(
        f'<div style="background:#0f2a24; border:1px solid #059669; padding:12px;'
        ' border-radius:10px;"><span style="background:#059669; color:white;'
        ' padding:2px 6px; border-radius:3px; font-size:9px;'
        ' font-weight:bold;">🛡️ קפטן מגן</span><h4 style="margin:6px 0;'
        f' color:#ecfdf5;">{shield["שם"]} ({shield["קבוצה"]})</h4><p'
        ' style="font-size:11px; color:#a7f3d0; margin:0;">בעלות:'
        f' <b>{shield["בעלות %"]}%</b> | xP: <b>{shield["נקודות צפויות"]}</b><br>משחק:'
        f' <b>{shield["משחק הבא"]}</b></p></div>',
        unsafe_allow_html=True,
    )

  with c2:
    st.markdown(
        f'<div style="background:#2a1e0f; border:1px solid #d97706; padding:12px;'
        ' border-radius:10px;"><span style="background:#d97706; color:white;'
        ' padding:2px 6px; border-radius:3px; font-size:9px;'
        ' font-weight:bold;">⚔️ קפטן דיפרנשיאל</span><h4 style="margin:6px 0;'
        f' color:#fffbeb;">{sword["שם"]} ({sword["קבוצה"]})</h4><p'
        ' style="font-size:11px; color:#fde68a; margin:0;">בעלות:'
        f' <b>{sword["בעלות %"]}% בלבד</b> | xGI: <b>{sword["xGI"]}</b><br>משחק:'
        f' <b>{sword["משחק הבא"]}</b></p></div>',
        unsafe_allow_html=True,
    )

# טאב 4: אסטרטגיה
with tab_strategy:
  st.subheader("🧭 חוקי המאקרו ל-Top 100K")
  st.markdown("""
    * **צבירת חילופים (Roll Transfers):** השאיפה היא להחזיק תמיד ב-2 חילופים חינמיים כדי לאפשר תמרון כפול בעת הצורך.
    * **אפס מינוסים (-4):** מינוס מותר רק כשיש 3 פציעות בו-זמנית. הימנעות ממינוסים שווה 30-50 נקודות יתרון בעונה.
    * **תזמון צ'יפים:** שמור Triple Captain ו-Bench Boost אך ורק ל-Double Gameweeks בחצי השני של העונה.
    """)

