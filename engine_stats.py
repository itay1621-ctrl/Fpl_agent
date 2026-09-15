"""
FPL Agent - Stats & Prediction Engine
Handles all advanced calculations for xP, Minutes, Start Probability, and BPS.
"""

def calculate_continuous_minutes(base_mins_per_gw, element_type):
    """
    P0.2 - Continuous Minutes Projection
    Projects exact minutes based on historical average and position trends.
    Removed artificial "Premium = 80 min" hack.
    """
    proj_mins = base_mins_per_gw
    
    # Position based decay/boost trends (historical regression averages)
    if element_type == 1: # GK
        proj_mins = min(proj_mins + 5, 90.0) if proj_mins > 45 else proj_mins
    elif element_type == 2: # DEF
        if proj_mins > 65: 
            proj_mins = min(proj_mins + 5, 90.0) # Nailed defs usually finish the 90
    elif element_type in [3, 4]: # MID, FWD
        # Attackers are highly prone to 60-80 min substitutions
        pass
            
    return round(proj_mins, 1)

def calculate_start_probability(proj_mins, chance_of_playing, form, fixtures_congestion=False):
    """
    P0.3 - Advanced Start Probability
    Uses a continuous function instead of hard step cliffs (74 mins vs 75 mins).
    Incorporates form, injury chance, and tactical nailedness.
    """
    if chance_of_playing == 0:
        return 0
        
    # Continuous tactical rate: scales smoothly based on projected minutes
    # 80+ mins average -> ~100% tactical rate
    # 40 mins average -> ~50% tactical rate
    tactical_rate = min(100.0, max(0.0, (proj_mins / 80.0) * 100.0))
    
    prob = tactical_rate * (chance_of_playing / 100.0)
    
    # High form players are less likely to be rotated
    if form >= 5.0 and prob > 60:
        prob = min(prob + 10, 100)
        
    # Congestion (Europe/Cups) increases rotation risk
    if fixtures_congestion and prob > 50 and prob < 90:
        prob -= 15
        
    return int(max(0, min(100, prob)))

def calculate_expected_points(element_type, xgi_p90, proj_mins, start_prob, chance_of_playing, cs_prob, form, is_elite_def=False, threat=0.0):
    """
    P0.1 - Robust xP Calculation
    Proper Expected Value (EV) math.
    Injuries and benchings affect expected minutes (e_mins), which linearly scales attacking/defensive returns.
    """
    p_start = start_prob / 100.0
    
    # Probability of sub appearance: 
    # chance_of_playing is overall availability. If available but not starting, they might sub.
    # We estimate a 40% chance of subbing in if they don't start but are available.
    p_avail = chance_of_playing / 100.0
    p_sub = max(0.0, p_avail - p_start) * 0.4 
    
    # Expected minutes conditional on starting vs subbing
    expected_mins_if_start = max(proj_mins, 60.0) if p_start > 0.5 else proj_mins
    expected_mins_if_sub = 15.0
    
    # True Expected Minutes (EV)
    e_mins = (p_start * expected_mins_if_start) + (p_sub * expected_mins_if_sub)
    if e_mins == 0:
        return 0.0
        
    # 1. Expected Appearance Points
    p_60_plus = p_start if expected_mins_if_start >= 60 else 0.0
    p_under_60 = (p_start if expected_mins_if_start < 60 else 0.0) + p_sub
    expected_appearance = (p_60_plus * 2.0) + (p_under_60 * 1.0)
    
    # 2. Expected Attacking Points (scaled precisely by true expected minutes)
    proj_xgi = (xgi_p90 / 90.0) * e_mins
    
    expected_attacking = 0.0
    if element_type in [1, 2]: # GK / DEF
        expected_attacking = proj_xgi * 5.0 
    elif element_type == 3: # MID
        expected_attacking = proj_xgi * 5.5 
    elif element_type == 4: # FWD
        expected_attacking = proj_xgi * 5.2 
        
    # 3. Expected Defensive Points (scaled by probability of playing 60+ mins)
    expected_defensive = 0.0
    if element_type in [1, 2]:
        expected_defensive = p_60_plus * cs_prob * 4.0
        if is_elite_def:
            expected_defensive *= 1.15 
    elif element_type == 3:
        expected_defensive = p_60_plus * cs_prob * 1.0
        
    # 4. Form and Threat adjustments
    form_bonus = 0.0
    if form >= 5.0:
        form_bonus = 0.6
    elif form <= 1.0:
        form_bonus = -0.3
        
    # Scale threat bonus by p_avail
    threat_bonus = (threat * 0.01) * p_avail
        
    # Final True EV xP
    final_xp = expected_appearance + expected_attacking + expected_defensive + form_bonus + threat_bonus
    
    return round(max(0.0, final_xp), 1)

def get_defcon_level(team_short, is_home, next_fdr):
    """
    P1.2 - Defensive Contributions (DefCon)
    Returns a string level (High/Med/Low) based on team defensive strength and fixture.
    """
    elite_defenses = ["ARS", "MCI", "LIV", "NEW", "CHE"]
    
    score = 0
    if team_short in elite_defenses:
        score += 2
    if is_home:
        score += 1
    if next_fdr <= 2:
        score += 2
    elif next_fdr == 3:
        score += 1
        
    if score >= 4:
        return "High"
    elif score >= 2:
        return "Medium"
    else:
        return "Low"
