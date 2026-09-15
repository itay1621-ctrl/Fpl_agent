"""
FPL Agent - Stats & Prediction Engine
Handles all advanced calculations for xP, Minutes, Start Probability, and BPS.
"""

def calculate_playing_probabilities(starts, mins, team_matches, chance_of_playing, form, fixtures_congestion=False):
    """
    P0.3 & P0.2 - Advanced Start & Sub Probability
    Calculates exact conditional probabilities based on historical starts/apps.
    """
    # 1. Availability Probability
    p_avail = (chance_of_playing / 100.0) if chance_of_playing is not None else 1.0
    
    # 2. Conditional Probabilities (Historical Base)
    team_matches = max(1, team_matches)
    historical_start_rate = min(1.0, starts / team_matches)
    
    # Estimate sub appearances if we don't have explicit 'appearances'
    estimated_subs = max(0, (mins - (starts * 60)) / 25.0) if starts > 0 else (mins / 25.0)
    historical_sub_rate = min(1.0 - historical_start_rate, estimated_subs / team_matches)
    
    # Form and Congestion Adjustments on Conditional Start Rate
    cond_p_start = historical_start_rate
    if form >= 5.0 and cond_p_start > 0.4:
        cond_p_start = min(1.0, cond_p_start + 0.15)
    if fixtures_congestion and cond_p_start > 0.5:
        cond_p_start *= 0.85
        
    cond_p_sub = min(1.0 - cond_p_start, historical_sub_rate * 1.2) # If rotated, sub chance increases
    
    # 3. Final Probabilities
    p_start = p_avail * cond_p_start
    p_sub = p_avail * cond_p_sub
    
    return p_start, p_sub, p_avail

def calculate_expected_minutes(p_start, p_sub, element_type, starts, mins):
    """
    EV of minutes based on precise starting and subbing probabilities.
    """
    # Estimate typical minutes when starting
    if starts > 0:
        typical_start_mins = min(90.0, max(45.0, mins / starts))
    else:
        typical_start_mins = 90.0 if element_type in [1, 2] else 70.0
        
    # Position based adjustments for typical sub minutes
    typical_sub_mins = 15.0 if element_type in [3, 4] else 5.0
    
    e_mins = (p_start * typical_start_mins) + (p_sub * typical_sub_mins)
    return round(e_mins, 1), typical_start_mins

def calculate_cs_prob(team_xgc_90, opp_fdr, is_home):
    """
    P0.4 - Advanced Clean Sheet Probability
    Combines team's actual xGC/90 with opponent's attacking strength (proxied by FDR) and Home/Away.
    """
    # Base expected goals conceded for the match
    base_xgc = team_xgc_90 if team_xgc_90 > 0 else 1.5
    
    # Opponent attacking modifier based on FDR (2 to 5)
    # FDR 2 -> weak attack (xG multiplier ~0.7)
    # FDR 5 -> strong attack (xG multiplier ~1.4)
    opp_attack_mod = 0.7 + ((opp_fdr - 2) * 0.233)
    
    # Home/Away modifier
    ha_mod = 0.9 if is_home else 1.15
    
    match_xgc = base_xgc * opp_attack_mod * ha_mod
    
    # Convert xGC to Clean Sheet Probability using Poisson distribution (e^(-lambda))
    import math
    cs_prob = math.exp(-match_xgc)
    return max(0.02, min(0.65, cs_prob)) # Cap realistically between 2% and 65%

def calculate_expected_points(element_type, xgi_p90, e_mins, p_start, p_sub, typical_start_mins, cs_prob, form, is_elite_def=False, threat=0.0):
    """
    P0.1 - Robust xP Calculation (True EV)
    """
    if e_mins == 0:
        return 0.0
        
    # 1. Expected Appearance Points
    p_60_plus = p_start if typical_start_mins >= 60 else 0.0
    p_under_60 = (p_start if typical_start_mins < 60 else 0.0) + p_sub
    expected_appearance = (p_60_plus * 2.0) + (p_under_60 * 1.0)
    
    # 2. Expected Attacking Points
    proj_xgi = (xgi_p90 / 90.0) * e_mins
    
    expected_attacking = 0.0
    if element_type in [1, 2]:
        expected_attacking = proj_xgi * 5.0 
    elif element_type == 3:
        expected_attacking = proj_xgi * 5.5 
    elif element_type == 4:
        expected_attacking = proj_xgi * 5.2 
        
    # 3. Expected Defensive Points
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
        
    threat_bonus = (threat * 0.01) * (p_start + p_sub)
        
    final_xp = expected_appearance + expected_attacking + expected_defensive + form_bonus + threat_bonus
    return round(max(0.0, final_xp), 1)

def get_defcon_level(team_short, is_home, next_fdr):
    """
    P1.2 - Defensive Contributions (DefCon)
    Returns a numerical score from 1.0 (lowest) to 5.0 (highest) 
    representing clean sheet potential.
    """
    elite_defenses = ["ARS", "MCI", "LIV", "NEW", "CHE"]
    
    score = 3.0  # Base average score
    if team_short in elite_defenses:
        score += 1.0
        
    if is_home:
        score += 0.5
    else:
        score -= 0.5
        
    if next_fdr <= 2:
        score += 1.0
    elif next_fdr == 4:
        score -= 1.0
    elif next_fdr >= 5:
        score -= 1.5
        
    return round(max(1.0, min(5.0, score)), 1)
