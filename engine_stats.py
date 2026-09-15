def calculate_playing_probabilities(starts, mins, team_matches, chance_of_playing, form, fixtures_congestion=False):
    """
    P0.3 & P0.2 - Advanced Start & Sub Probability
    Calculates exact conditional probabilities based on historical starts/apps.
    """
    # 1. Availability Probability
    p_avail = (chance_of_playing / 100.0) if chance_of_playing is not None else 1.0
    
    # 2. Conditional Probabilities (Historical Base)
    # Heuristic for sub appearances (fallback since API doesn't cleanly expose sub appearances without history parsing)
    estimated_subs = max(0, (mins - (starts * 60)) / 25.0) if starts > 0 else (mins / 25.0)
    
    # Prevent punishing winter transfers or returning injured players with a massive denominator
    effective_matches = min(max(1, team_matches), max(3, starts + estimated_subs + (2 if form > 3.0 else 5)))
    historical_start_rate = min(1.0, starts / effective_matches)
    historical_sub_rate = min(1.0 - historical_start_rate, estimated_subs / effective_matches)
    
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
    P0.4 - Poisson Clean Sheet Probability.
    Future Enhancement: Replace opp_fdr with Opponent xG/90 + Recent Attacking Strength.
    Currently uses FDR as a rough proxy for opponent attacking strength.
    """
    # Base expected goals conceded for the match
    base_xgc = team_xgc_90 if team_xgc_90 > 0 else 1.5
    
    # Opponent attacking modifier based on FDR (2 to 5)
    opp_attack_mod = 0.7 + ((opp_fdr - 2) * 0.233)
    
    # Home/Away modifier
    ha_mod = 0.9 if is_home else 1.15
    
    match_xgc = base_xgc * opp_attack_mod * ha_mod
    
    # Convert xGC to Clean Sheet Probability using Poisson distribution
    import math
    cs_prob = math.exp(-match_xgc)
    return max(0.02, min(0.65, cs_prob))

def calculate_expected_points(element_type, xg_90, xa_90, bps_90, e_mins, p_start, p_sub, typical_start_mins, cs_prob, is_elite_def=False, threat=0.0):
    """
    P0.1 - True FPL Scoring Engine
    Separates Goals, Assists, CS, and projects Bonus Points System (BPS).
    """
    if e_mins == 0:
        return 0.0
        
    # 1. Appearance Points
    p_60_plus = p_start if typical_start_mins >= 60 else 0.0
    p_under_60 = (p_start if typical_start_mins < 60 else 0.0) + p_sub
    expected_appearance = (p_60_plus * 2.0) + (p_under_60 * 1.0)
    
    # 2. Attacking Points (Separated xG and xA)
    proj_goals = (xg_90 / 90.0) * e_mins
    proj_assists = (xa_90 / 90.0) * e_mins
    
    goal_pts_map = {1: 6, 2: 6, 3: 5, 4: 4}
    expected_attacking = (proj_goals * goal_pts_map.get(element_type, 4)) + (proj_assists * 3.0)
        
    # 3. Defensive Points
    expected_defensive = 0.0
    if element_type in [1, 2]:
        expected_defensive = p_60_plus * cs_prob * 4.0
        if is_elite_def:
            expected_defensive *= 1.15 
    elif element_type == 3:
        expected_defensive = p_60_plus * cs_prob * 1.0
        
    # 4. Expected Bonus Proxy (Approximation)
    # Note: True BPS ranking requires matching against all 21 players in a match.
    # This proxy approximates bonus chance based on raw BPS generation rate.
    # Future enhancement: Add actual DefCon (CBI + Recoveries) when element-summary data is available.
    proj_bps = (bps_90 / 90.0) * e_mins
    expected_bonus = 0.0
    if proj_bps > 25:
        expected_bonus = 1.2
    elif proj_bps > 20:
        expected_bonus = 0.6
    elif proj_bps > 15:
        expected_bonus = 0.2
        
    # 5. Threat / Set Pieces / Penalties proxy
    threat_bonus = (threat * 0.01) * (p_start + p_sub)
        
    # Note: Explicit form_bonus was removed to avoid double counting, as form already boosts e_mins.
    
    final_xp = expected_appearance + expected_attacking + expected_defensive + expected_bonus + threat_bonus
    return round(max(0.0, final_xp), 1)
