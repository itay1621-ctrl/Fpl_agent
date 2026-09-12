def calculate_elite_score(el, team_fixtures, next_gw):
  mins = el.get("minutes", 0)
  if mins < 90:  # מעט מדי דקות מדגם
    return 0.0

  # 1. נרמול פר 90 דקות
  xgi_per_90 = (
      float(el.get("expected_goal_involvements", 0.0)) / mins
  ) * 90
  form = float(el.get("form", 0.0))

  # 2. לוח משחקים דועך (50% / 30% / 20%)
  weights = [0.50, 0.30, 0.20]
  fdr_score = 0.0
  for i, fdr in enumerate(team_fixtures[:3]):
    # יתרון למשחק קל (FDR נמוך מעלה ניקוד)
    diff_val = 5.5 - fdr
    fdr_score += diff_val * weights[i]

  # 3. זיהוי תת-ביצוע (מתכון להתפוצצות נקודות קרובה)
  actual_gi = el.get("goals_scored", 0) + el.get("assists", 0)
  expected_gi = float(el.get("expected_goal_involvements", 0.0))
  underperformance_bonus = (
      0.8 if (expected_gi - actual_gi) >= 1.0 else 0.0
  )  # מייצר המון מצבים אך עדיין לא הבקיע

  # 4. בונוס ביטחון דקות (שחקן של 80+ דקות בממוצע)
  mins_per_game = mins / max(1, (next_gw - 1))
  nailed_bonus = 1.2 if mins_per_game >= 75 else 0.7

  # חישוב ציון משוקלל סופי
  final_score = (
      (xgi_per_90 * 3.5)
      + (form * 1.2)
      + (fdr_score * 1.8)
      + underperformance_bonus
  ) * nailed_bonus

  return round(final_score, 2)
