"""
FPL Agent - Stats & Prediction Engine
Handles all advanced calculations for xP, Minutes, Start Probability, and BPS.
"""

def calculate_continuous_minutes(base_mins_per_gw, cost, element_type, is_premium=False):
    """
    P0.2 - Continuous Minutes Projection
    Instead of binary <60 / >=60, project exact minutes based on historical average, 
    price premium (nailedness), and position.
    """
    # Base projection
    proj_mins = base_mins_per_gw
    
    # Premium / Nailed bonus
    if cost >= 8.0 or is_premium:
        proj_mins = max(proj_mins, 80.0) # Premiums rarely get subbed early unless blowout
    
    # Position based decay/boost
    if element_type == 1: # GK
        proj_mins = 90.0 if proj_mins > 45 else proj_mins
    elif element_type == 2: # DEF
        if proj_mins > 60: proj_mins = min(proj_mins + 5, 90.0) # Defs usually play 90 if starting
    elif element_type in [3, 4]: # MID, FWD
        # Attackers are highly prone to 60-70 min substitutions (5 subs rule)
        if proj_mins > 65 and cost < 8.0:
            proj_mins = min(proj_mins, 75.0)
            
    return round(proj_mins, 1)

def calculate_start_probability(tactical_rate, chance_of_playing, form, fixtures_congestion=False):
    """
    P0.3 - Advanced Start Probability
    Incorporates form, injury chance, and tactical nailedness.
    """
    if chance_of_playing == 0:
        return 0
        
    prob = tactical_rate * (chance_of_playing / 100.0)
    
    # High form players are less likely to be rotated
    if form >= 5.0 and prob > 60:
        prob = min(prob + 10, 100)
        
    # Congestion (Europe/Cups) increases rotation risk
    if fixtures_congestion and prob > 50 and prob < 90:
        prob -= 15
        
    return int(max(0, min(100, prob)))

def calculate_expected_points(element_type, xgi_p90, proj_mins, start_prob, cs_prob, form, is_elite_def=False, threat=0.0):
    """
    P0.1 - Robust xP Calculation
    Separates historical xGI from future match xP prediction.
    """
    # 1. Appearance points
    expected_appearance = 0.0
    if proj_mins >= 60:
        expected_appearance = 2.0 * (start_prob / 100.0)
    elif proj_mins > 0:
        expected_appearance = 1.0 * (start_prob / 100.0)
        # Factor in sub appearances
        sub_prob = max(0, 100 - start_prob) / 100.0
        expected_appearance += 1.0 * sub_prob
        
    # 2. Attacking points based on xGI per 90 scaled to projected minutes
    proj_xgi = (xgi_p90 / 90.0) * proj_mins
    
    expected_attacking = 0.0
    if element_type == 1 or element_type == 2: # GK / DEF
        expected_attacking = proj_xgi * 5.0
    elif element_type == 3: # MID
        expected_attacking = proj_xgi * 5.5
    elif element_type == 4: # FWD
        expected_attacking = proj_xgi * 5.2
        
    # 3. Defensive points (Clean Sheets)
    expected_defensive = 0.0
    if element_type in [1, 2]:
        expected_defensive = cs_prob * 4.0
        if is_elite_def:
            expected_defensive *= 1.15
    elif element_type == 3:
        expected_defensive = cs_prob * 1.0
        
    # 4. Form and Threat adjustments
    form_bonus = 0.0
    if form >= 5.0:
        form_bonus = 0.6
    elif form <= 1.0:
        form_bonus = -0.3
        
    threat_bonus = threat * 0.01
        
    # Final xP
    raw_xp = expected_appearance + expected_attacking + expected_defensive + form_bonus + threat_bonus
    
    # Chance of playing multiplier (injury/suspension)
    return round(max(0.0, raw_xp), 1)
