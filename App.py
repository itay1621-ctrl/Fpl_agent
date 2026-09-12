import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="FPL Master Scout",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .main { direction: rtl; text-align: right; }
    div[data-testid="stMetricValue"] { font-size: 20px; }
    th { text-align: right !important; }
    </style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=600)
def load_data():
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

  pos_dict = {1: "שוער (GK)", 2: "הגנה (DEF)", 3: "קישור (MID)", 4: "התקפה (FWD)"}
  rows = []

  for el in elements:
    if el["status"] == "u":
      continue

    upcoming_fdr = []
    upcoming_str = []
    for f in fixtures:
      if f["event"] in [next_gw, next_gw + 1, next_gw + 2]:
        if f["team_h"] == el["team"]:
          opp = teams[f["team_a"]]["short_name"]
          diff = f["team_h_difficulty"]
          upcoming_fdr.append(diff)
          upcoming_str.append(f"{opp}(H)-{diff}")
        elif f["team_a"] == el["team"]:
          opp = teams[f["team_h"]]["short_name"]
          diff = f["team_a_difficulty"]
          upcoming_fdr.append(diff)
          upcoming_str.append(f"{opp}(A)-{diff}")

    avg_fdr = sum(upcoming_fdr) / len(upcoming_fdr) if upcoming_fdr else 3.0
    form = float(el["form"])
    xp = float(el["ep_next"]) if el.get("ep_next") else 0.0
    xgi = float(el.get("expected_goal_involvements", 0.0))
    cost = el["now_cost"] / 10
    score = (xp * 1.5) + (form * 1.0) + (xgi * 0.8) + ((5.0 - avg_fdr) * 1.2)

    rows.append({
        "ID": el["id"],
        "שם": el["web_name"],
        "קבוצה": teams[el["team"]]["short_name"],
        "עמדה_קוד": el["element_type"],
        "עמדה": pos_dict[el["element_type"]],
        "מחיר": cost,
        "כושר (Form)": form,
        "xGI": xgi,
        "נקודות צפויות (xP)": xp,
        "בעלות %": float(el["selected_by_percent"]),
        "סטטוס": el["status"],
        "סיכוי שיתוף": (
            el["chance_of_playing_next_round"]
            if el["chance_of_playing_next_round"] is not None
            else 100
        ),
        "FDR ממוצע קרוב": round(avg_fdr, 2),
        "ציון אלגוריתם": round(score, 2),
        "3 משחקים קרובים": (
            " | ".join(upcoming_str) if upcoming_str else "ממתין"
        ),
    })

  return pd.DataFrame(rows), next_gw


df, next_gw = load_data()

st.title("⚽ FPL Strategy Master")
st.caption(f"מודל EV לקראת מחזור {next_gw} | יעד שנתי: Top 100K")

tab1, tab2, tab3, tab4 = st.tabs(
    ["⭐ ה-15 המומלצים", "👑 קפטן", "🎯 רכש ומכירה", "🧭 עקרונות 100K"]
)

fit_df = df[(df["סטטוס"] == "a") & (df["סיכוי שיתוף"] == 100)]

with tab1:
  gks = (
      fit_df[fit_df["עמדה_קוד"] == 1]
      .sort_values(by="ציון אלגוריתם", ascending=False)
      .head(2)
  )
  defs = (
      fit_df[fit_df["עמדה_קוד"] == 2]
      .sort_values(by="ציון אלגוריתם", ascending=False)
      .head(5)
  )
  mids = (
      fit_df[fit_df["עמדה_קוד"] == 3]
      .sort_values(by="ציון אלגוריתם", ascending=False)
      .head(5)
  )
  fwds = (
      fit_df[fit_df["עמדה_קוד"] == 4]
      .sort_values(by="ציון אלגוריתם", ascending=False)
      .head(3)
  )
  meta_squad = pd.concat([gks, defs, mids, fwds])
  total_cost = round(meta_squad["מחיר"].sum(), 1)

  st.success(f"💰 תקציב סגל מומלץ: £{total_cost}m / £100m")
  st.dataframe(
      meta_squad[[
          "שם",
          "עמדה",
          "קבוצה",
          "מחיר",
          "ציון אלגוריתם",
          "כושר (Form)",
          "xGI",
          "3 משחקים קרובים",
      ]],
      hide_index=True,
      use_container_width=True,
  )

with tab2:
  premiums = fit_df[fit_df["מחיר"] >= 7.5].sort_values(
      by=["נקודות צפויות (xP)", "ציון אלגוריתם"], ascending=False
  )
  safe_c = premiums.iloc[0]
  diff_pool = premiums[premiums["בעלות %"] < 15]
  diff_c = diff_pool.iloc[0] if not diff_pool.empty else premiums.iloc[1]

  c1, c2 = st.columns(2)
  with c1:
    st.success(f"🛡️ **קפטן מגן (Shield): {safe_c['שם']} ({safe_c['קבוצה']})**")
    st.write(
        f"בעלות: {safe_c['בעלות %']}% | xP: {safe_c['נקודות צפויות (xP)']}"
    )
  with c2:
    st.warning(
        f"⚔️ **קפטן דיפרנשיאל (Sword): {diff_c['שם']} ({diff_c['קבוצה']})**"
    )
    st.write(f"בעלות: {diff_c['בעלות %']}% | כושר: {diff_c['כושר (Form)']}")

with tab3:
  col_b, col_s = st.columns(2)
  with col_b:
    st.markdown("#### 🟢 יעדי רכש (Hot Buys)")
    buys = (
        fit_df[fit_df["FDR ממוצע קרוב"] <= 2.67]
        .sort_values(by="ציון אלגוריתם", ascending=False)
        .head(5)
    )
    st.dataframe(
        buys[["שם", "קבוצה", "מחיר", "ציון אלגוריתם", "3 משחקים קרובים"]],
        hide_index=True,
    )
  with col_s:
    st.markdown("#### 🔴 שחקנים למכירה (Traps / Injuries)")
    sells = df[
        (df["בעלות %"] > 10)
        & ((df["סטטוס"] != "a") | (df["FDR ממוצע קרוב"] >= 3.6))
    ].head(5)
    st.dataframe(
        sells[["שם", "קבוצה", "בעלות %", "מחיר", "סטטוס"]], hide_index=True
    )

with tab4:
  st.markdown("""
    * **Roll Transfers:** שמור חילופים כברירת מחדל כדי להגיע עם 2 חילופים לכל מחזור.
    * **אפס מינוסים (-4):** מותר רק במקרה של 3 פציעות חמורות בו-זמנית.
    * **שמירת צ'יפים:** Triple Captain ו-Bench Boost מיועדים למחזורים כפולים גדולים (DGW) בלבד.
    """)
