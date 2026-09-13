        # חישוב כשירות רפואית מדויקת מול ה-API
        status = el.get("status", "a")
        chance_raw = el.get("chance_of_playing_next_round")
        if chance_raw is not None:
            chance = int(chance_raw)
        elif status in ["i", "s", "u"]:
            chance = 0
        elif status == "d":
            chance = 50
        else:
            chance = 100

        # חישוב סבירות פתיחה מתוקן (מתחשב בפתיחות בהרכב ובאנקרים)
        total_gws = max(1, next_gw - 1)
        starts = el.get("starts", 0)
        start_ratio = starts / total_gws if total_gws > 0 else 1.0
        mins_per_gw = mins / total_gws

        # שחקני באנקר (פותחים קבועים שמוחלפים מוקדם או משחקים 90 דקות)
        if chance == 0:
            start_prob = 0
        elif start_ratio >= 0.85 or mins_per_gw >= 70:
            # באנקר מובהק בהרכב (הולאנד, ברונו, סאקה, סלאח וכו')
            base_tactical = 99 if start_ratio >= 0.95 else 95
            start_prob = int(round(base_tactical * (chance / 100.0)))
        elif start_ratio >= 0.60 or mins_per_gw >= 50:
            # שחקן הרכב מוביל עם רוטציה קלה
            base_tactical = 85
            start_prob = int(round(base_tactical * (chance / 100.0)))
        elif mins_per_gw >= 25 or starts >= 1:
            # שחקן רוטציה / מחליף ראשון
            base_tactical = 50
            start_prob = int(round(base_tactical * (chance / 100.0)))
        else:
            # שחקן ספסל עמוק
            base_tactical = 15
            start_prob = int(round(base_tactical * (chance / 100.0)))
