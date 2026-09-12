import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="FPL Elite Scout | Top 100K Engine",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
.main { direction: rtl; text-align: right; background-color: #0b0f19; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }

/* מגרש כדורגל */
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
    width: 84px;
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

/* כרטיסים */
.scout-card { background: #0e2a38; border-right: 4px solid #38bdf8; padding: 10px; border-radius: 6px; margin-bottom: 8px; }
.trap-card { background: #221013; border-right: 4px solid #ef4444; padding: 10px; border-radius: 6px; margin-bottom: 8px; }
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

  # 1. חישוב עוצמת התקפה קבוצתית (סך שערים שהקבוצה כבשה עד כה)
  team_goals = {t_id: 0 for t_id in teams}
  for el in elements:
    team_goals[el["team"]] += el["goals_scored"]

  pos_map = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
  all_players = []

  for el in elements:
    if el["status"] == "u":
      continue

    # לוח משחקים
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
    xgi = float(el.get("expected_goal_involvements", 0.0))
    threat = float(el.get("threat", 0.0))
    cost = el["now_cost"] / 10

    # מומנטום רשתות וסקאוט: קניות נטו של שחקנים למחזור הנוכחי
    net_transfers = el.get("transfers_in_event", 0) - el.get(
        "transfers_out_event", 0
    )
    # נרמול מומנטום סקאוט (0 עד 3 נקודות)
    scout_buzz = max(-2.0, min(3.5, net_transfers / 50000.0))

    # מקדם התקפה קבוצתית (צ'לסי, סיטי, ארסנל וכו')
    t_goals = team_goals.get(el["team"], 0)
    team_attack_boost = 1.3 if t_goals >= 5 else 1.0

    # אלגוריתם משוקלל: מומנטום סקאוט + עוצמת התקפה קבוצתית + איום ממשי (Threat) + xGI
    composite_score = (
        (xgi * 1.5)
        + (threat * 0.02)
        + (form * 1.1)
        + scout_buzz
        + ((5.2 - avg_fdr) * 1.3)
    ) * (team_attack_boost if el["element_type"] in [3, 4] else 1.0)

    # מדד בועה (פער קיצוני בין שערים בפועל ל-xGI)
    goals_assists = el["goals_scored"] + el["assists"]
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
        "איום_Opta": threat,
        "קניות_נטו": net_transfers,
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
st.caption(
    f"מודל EV משולב סנטימנט סקאוט ועוצמת התקפה לקראת GW{next_gw} | יעד: Top 100K"
)

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
      ' style="color:#10b981;font-size:11px;">שקלול שוק</div><div'
      ' style="font-size:16px;font-weight:bold;">Opta + Scout Buzz</div></div>',
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

tab_pitch, tab_scout, tab_trap, tab_captain = st.tabs([
    "🟢 הרכב מגרש (3-4-3)",
    "🔥 מוקדי סקאוט ורשתות",
    "🚨 רדאר בועות ומלכודות",
    "👑 זירת הקפטנים",
])

fit_df = df[(df["סטטוס"] == "a") & (df["סיכוי שיתוף"] == 100)]

# טאב 1: מגרש
with tab_pitch:
  st.subheader("📋 ההרכב האופטימלי על המגרש (£100m)")
  st.caption("משקלל כוח התקפה קבוצתי, מומנטום קניות ואיום ממשי:")

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

# טאב 2: סקאוט ורשתות
with tab_scout:
  st.subheader("🔥 השחקנים המטורגטים ביותר ע״י קהילת הסקאוט והרשתות")
  st.markdown("שחקנים שנמצאים במומנטום קניות נטו חיובי חזק לקראת המחזור:")

  scout_targets = fit_df.sort_values(by="קניות_נטו", ascending=False).head(6)

  for _, s in scout_targets.iterrows():
    st.markdown(
        f'<div class="scout-card"><strong style="color:#7dd3fc; font-size:13px;">⭐'
        f" {s['שם']} ({s['קבוצה']}) - {s['עמדה']} | £{s['מחיר']}m</strong><br><span"
        f" style=\"font-size:11px; color:#e2e8f0;\">קניות נטו המחזור:"
        f" <b>+{s['קניות_נטו']:,}</b> | בעלות: <b>{s['בעלות %']}%</b><br>📅"
        f" משחקים קרובים: <b>{s['3 משחקים']}</b></span><br><span"
        ' style="font-size:10px; color:#38bdf8; font-weight:bold;">פסיקת'
        " קונצנזוס: יעד רכש מובהק של מנג'רי הטופ.</span></div>",
        unsafe_allow_html=True,
    )

# טאב 3: רדאר בועות
with tab_trap:
  st.subheader("🚨 אזהרת בועות: ממי להתרחק למרות ההייפ?")
  bubbles = (
      df[
          (df["שערים_בישולים"] >= 2)
          & (df["מדד בועה"] > 1.1)
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
        f" <b>{b['שערים_בישולים']}</b> | סך xGI שייצר: <b>{b['xGI']}</b><br>📅"
        f" משחקים קרובים: <b>{b['3 משחקים']}</b></span><br><span"
        ' style="font-size:10px; color:#ef4444; font-weight:bold;">פסיקת סוכן:'
        " בועה. לא מומלץ לקנייה.</span></div>",
        unsafe_allow_html=True,
    )

# טאב 4: קפטן
with tab_captain:
  st.subheader("👑 קרב קפטן: עוגן מול דיפרנשיאל")

  premiums = fit_df[fit_df["מחיר"] >= 7.5].sort_values(
      by=["ציון אלגוריתם", "כושר"], ascending=False
  )
  shield = premiums.iloc[0]
  diff_cand = premiums[premiums["בעלות %"] < 18]
  sword = diff_cand.iloc[0] if not diff_cand.empty else premiums.iloc[1]

  c1, c2 = st.columns(2)
  with c1:
    st.markdown(
        f'<div style="background:#0f2a24; border:1px solid #059669; padding:12px;'
        ' border-radius:10px;"><span style="background:#059669; color:white;'
        ' padding:2px 6px; border-radius:3px; font-size:9px;'
        ' font-weight:bold;">🛡️ קפטן מגן (Shield)</span><h4 style="margin:6px'
        f' 0; color:#ecfdf5;">{shield["שם"]} ({shield["קבוצה"]})</h4><p'
        ' style="font-size:11px; color:#a7f3d0; margin:0;">בעלות:'
        f' <b>{shield["בעלות %"]}%</b> | ציון שוק: <b>{shield["ציון אלגוריתם"]}</b><br>משחק:'
        f' <b>{shield["משחק הבא"]}</b></p></div>',
        unsafe_allow_html=True,
    )

  with c2:
    st.markdown(
        f'<div style="background:#2a1e0f; border:1px solid #d97706; padding:12px;'
        ' border-radius:10px;"><span style="background:#d97706; color:white;'
        ' padding:2px 6px; border-radius:3px; font-size:9px;'
        ' font-weight:bold;">⚔️ קפטן דיפרנשיאל (Sword)</span><h4'
        f' style="margin:6px 0; color:#fffbeb;">{sword["שם"]}'
        f' ({sword["קבוצה"]})</h4><p style="font-size:11px; color:#fde68a;'
        f' margin:0;">בעלות: <b>{sword["בעלות %"]}% בלבד</b> | xGI:'
        f' <b>{sword["xGI"]}</b><br>משחק: <b>{sword["משחק הבא"]}</b></p></div>',
        unsafe_allow_html=True,
    )
