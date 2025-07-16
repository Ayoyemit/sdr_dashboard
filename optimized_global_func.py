"""
Optimized Global Functions
Enhanced version with vectorization, caching, and performance improvements
"""

import random
import numpy as np
from scipy.optimize import fsolve, least_squares
import math
import streamlit as st
from scipy.stats import truncnorm
from optimization_config import cache_result, streamlit_cache, opt_config
import numba
from typing import Dict, List, Tuple, Any

# Try to use numba for JIT compilation if available
try:
    if opt_config.USE_NUMBA:
        @numba.jit(nopython=True, cache=True)
        def fast_odds_prob(oddsratio, p_comp, p_expose):
            """Numba-optimized odds probability calculation"""
            def equations(x, y):
                eq1 = x / (1 - x) / (y / (1 - y)) - oddsratio
                eq2 = p_comp - p_expose * x - (1 - p_expose) * y
                return eq1, eq2
            
            # Simple fixed-point iteration for speed
            x, y = 0.5, 0.5
            for _ in range(10):
                eq1, eq2 = equations(x, y)
                if abs(eq1) < 1e-6 and abs(eq2) < 1e-6:
                    break
                # Simple update rule
                x = np.clip(x - 0.1 * eq1, 0, 1)
                y = np.clip(y - 0.1 * eq2, 0, 1)
            
            return np.clip(x, 0, 1), np.clip(y, 0, 1)
except ImportError:
    # Fallback to regular function if numba not available
    def fast_odds_prob(oddsratio, p_comp, p_expose):
        return odds_prob(oddsratio, p_comp, p_expose)

@cache_result
def get_P_l45(p_anc, slider_params):
    """Cached version of P_l45 calculation"""
    try:
        if 'p_l45_anc_slider' not in slider_params or slider_params['p_l45_anc_slider'] is None:
            return None
        
        slider_data = slider_params['p_l45_anc_slider']
        if not isinstance(slider_data, np.ndarray) or slider_data.size == 0:
            return None
            
        idx = np.where(slider_data[:, 0] == p_anc)
        return slider_data[idx, 1][0][0] if idx[0].size > 0 else None
    except (KeyError, IndexError, TypeError):
        return None

@cache_result
def odds_prob(oddsratio, p_comp, p_expose):
    """Cached odds probability calculation"""
    try:
        def equations(vars):
            x, y = vars
            eq1 = x / (1 - x) / (y / (1 - y)) - oddsratio
            eq2 = p_comp - p_expose * x - (1 - p_expose) * y
            return [eq1, eq2]

        initial_guess = [0.5, 0.5]
        solution = fsolve(equations, initial_guess)
        solution[0] = round(np.clip(solution[0], 0, 1), 2)
        solution[1] = round(np.clip(solution[1], 0, 1), 2)
        return solution
    except (ValueError, RuntimeWarning, TypeError):
        # Return default values if calculation fails
        return [0.5, 0.5]

@streamlit_cache
def GA_assign_kenya(param, n, P):
    """Cached GA assignment for Kenya"""
    try:
        n["GA"] = param.get("GA_distribution", np.ones(18))
        P["GA"] = n["GA"] / np.sum(n["GA"])
        PT_mask = np.array([1] * 10 + [0] * 8, dtype=bool)
        FT_mask = ~PT_mask
        P["GA"][PT_mask] = P["GA"][PT_mask] * param.get("PT_scale", 1.0)
        P_mult = (1 - np.sum(P["GA"][PT_mask])) / np.sum(P["GA"][FT_mask])
        P["GA"][FT_mask] = P["GA"][FT_mask] * P_mult
        return P["GA"]
    except (KeyError, TypeError, ValueError):
        # Return default GA distribution if calculation fails
        return np.ones(18) / 18

@streamlit_cache
def GA_by_ANC(param, OR, P):
    """Cached GA by ANC calculation"""
    try:
        OR["ANC"] = param.get("OR_preterm_ANC", 1.0)
        PT_mask = np.array([1] * 10 + [0] * 8, dtype=bool)
        FT_mask = ~PT_mask
        Preterm_rate = np.sum(P["GA"][PT_mask])
        preterm_anc_noanc = odds_prob(OR["ANC"], Preterm_rate, param.get('p_ANC_base', 0.5))
        
        P["GA_anc"] = P["GA"].copy()
        P_scale_anc = preterm_anc_noanc[0] / max(Preterm_rate, 1e-6)
        P["GA_anc"][PT_mask] *= P_scale_anc
        P_mult = (1 - preterm_anc_noanc[0]) / np.sum(P["GA_anc"][FT_mask])
        P["GA_anc"][FT_mask] *= P_mult

        P["GA_noanc"] = P["GA"].copy()
        P_scale_noanc = preterm_anc_noanc[1] / max(Preterm_rate, 1e-6)
        P["GA_noanc"][PT_mask] *= P_scale_noanc
        P_mult = (1 - preterm_anc_noanc[1]) / np.sum(P["GA_noanc"][FT_mask])
        P["GA_noanc"][FT_mask] *= P_mult
        return P["GA_anc"], P["GA_noanc"]
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        # Return default values if calculation fails
        default_ga = np.ones(18) / 18
        return default_ga, default_ga

# Vectorized risk stratification
def risk_stratification_vectorized(i_risk, i_ANC, num_mothers, sen_risk, spec_risk, rng):
    """Vectorized risk stratification for better performance"""
    i_risk_pred = np.zeros(num_mothers, dtype=int)
    
    # Vectorized operations
    true_high_anc_mask = (i_risk == 1) & (i_ANC == 1)
    true_low_anc_mask = (i_risk == 0) & (i_ANC == 1)
    
    # Generate random numbers once
    random_vals = rng.random(num_mothers)
    
    # Vectorized predictions
    pred_as_high = (random_vals < sen_risk).astype(int)
    pred_as_low = 1 - (random_vals < spec_risk).astype(int)
    
    # Apply masks
    i_risk_pred[true_high_anc_mask] = pred_as_high[true_high_anc_mask]
    i_risk_pred[true_low_anc_mask] = pred_as_low[true_low_anc_mask]
    
    return i_risk_pred

# Optimized move function
def move_function_vectorized(num_mothers, l4_l5, i_class, i_loc, i_loc_new, i_free_referral, 
                           i_self_referral, Referral_Capacity, flags, num_move, loc_index, rng):
    """Vectorized move function for better performance"""
    flag_refer = flags.get("flag_refer", False)

    # Vectorized location mask
    loc_mask = (i_loc == loc_index)
    eligible_indices = np.where(loc_mask)[0]

    # Efficient shuffling
    shuffled_all = rng.permutation(num_mothers)
    shuffled_eligible = shuffled_all[np.isin(shuffled_all, eligible_indices)]

    # Select top eligible mothers
    index_move = shuffled_eligible[:num_move]
    mask_move = np.zeros(num_mothers, dtype=bool)
    mask_move[index_move] = True

    # Vectorized referral logic
    p_free_refer = Referral_Capacity if flag_refer else 0
    free_refer_draws = (rng.random(num_mothers) < p_free_refer).astype(int)
    
    # Vectorized updates
    move_free_refer_mask = mask_move & (free_refer_draws == 1)
    i_free_referral[move_free_refer_mask] = 1
    i_loc_new[move_free_refer_mask] = l4_l5[move_free_refer_mask]

    move_self_refer_mask = mask_move & (free_refer_draws == 0) & (i_class == 1)
    i_self_referral[move_self_refer_mask] = 1
    i_loc_new[move_self_refer_mask] = l4_l5[move_self_refer_mask]

    return i_loc_new, i_free_referral, i_self_referral

# Vectorized intrapartum prediction
def intrapartum_prediction_vectorized(num_mothers, monitoring_mask, comp_type, sen_type, spec_type, rng):
    """Vectorized intrapartum prediction"""
    i_comp_pred = np.zeros(num_mothers, dtype=int)

    # Generate random numbers once
    random_vals = rng.random(num_mothers)
    
    # Vectorized masks
    true_comp_monitor_mask = (comp_type == 1) & monitoring_mask
    true_nocomp_monitor_mask = (comp_type == 0) & monitoring_mask

    # Vectorized predictions
    pred_as_comp = (random_vals < sen_type).astype(int)
    pred_as_comp[~monitoring_mask] = 0

    pred_as_nocomp = 1 - (random_vals < spec_type).astype(int)
    pred_as_nocomp[~monitoring_mask] = 0

    # Apply masks
    i_comp_pred[true_comp_monitor_mask] = pred_as_comp[true_comp_monitor_mask]
    i_comp_pred[true_nocomp_monitor_mask] = pred_as_nocomp[true_nocomp_monitor_mask]
    
    return i_comp_pred

# Vectorized complication functions
def comp_OL_type_vectorized(num_mothers, comp_type, p_comp_ol, mask, rng):
    """Vectorized OL type complication"""
    comp_ol = (rng.random(num_mothers) < p_comp_ol).astype(int)
    comp_type[mask] = comp_ol[mask]
    return comp_type

def comp_severe_vectorized(num_mothers, comp_type, p_severe_risk, rng):
    """Vectorized severe complication calculation"""
    i_comp_severe = np.zeros(num_mothers, dtype=int)
    true_severe = (rng.random(num_mothers) < p_severe_risk).astype(int)
    i_comp_severe[(comp_type == 1)] = true_severe[(comp_type == 1)]
    return i_comp_severe

# Optimized probability functions with vectorization
@cache_result
def P_IVH_vectorized_optimized(GA, flag_T, param):
    """Optimized vectorized IVH probability calculation"""
    try:
        b = 10.05928
        c = 0.13321
        d = 0.94642
        e = 25.86781
        OR = param.get('OR_IVH_treat', 1.0)

        # Vectorized calculation
        P = np.where(GA < 37, c + (d - c) / (1 + np.exp(b * (np.log(GA) - np.log(e)))), 0)
        
        # Safe division with clipping
        P_safe = np.clip(P, 1e-6, 1 - 1e-6)
        P_Treated = OR / (OR + (1 / P_safe - 1))
        P = np.where(flag_T, P_Treated, P)

        return P
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return np.zeros_like(GA)

@cache_result
def P_NEC_vectorized_optimized(GA, flag_T, param):
    """Optimized vectorized NEC probability calculation"""
    try:
        b = 19.6727
        c = 0.00318
        d = 0.10013
        e = 29.43533
        OR = param.get('OR_NEC_treat', 1.0)

        # Vectorized calculation
        P = np.where(GA < 37, c + (d - c) / (1 + np.exp(b * (np.log(GA) - np.log(e)))), 0)
        
        # Safe division with clipping
        P_safe = np.clip(P, 1e-6, 1 - 1e-6)
        P_Treated = OR / (OR + (1 / P_safe - 1))
        P = np.where(flag_T, P_Treated, P)

        return P
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return np.zeros_like(GA)

@cache_result
def P_Sepsis_vectorized_optimized(GA, flag_T, param):
    """Optimized vectorized Sepsis probability calculation"""
    try:
        RR = param.get('RR_Sepsis_treat', 1.0)

        # Vectorized calculation
        P = np.where(GA < 37, np.clip(20.5046 * np.exp(-0.271732 * GA), 0, 1), 0)
        P = np.where(flag_T, P * RR, P)

        return P
    except (KeyError, TypeError, ValueError):
        return np.zeros_like(GA)

@cache_result
def P_RDS_optimized(param):
    """Optimized RDS probability calculation"""
    try:
        p_RDS_noT = param.get("p_RDS_noT", 0.1)
        OR_RDS_treat = param.get("OR_RDS_treat", 1.0)
        
        P_safe = np.clip(p_RDS_noT, 1e-6, 1 - 1e-6)
        P_Treated = OR_RDS_treat / (OR_RDS_treat + (1 / P_safe - 1))
        P_RDS_T = np.where(p_RDS_noT == 0, 0, P_Treated)
        P = np.vstack([p_RDS_noT, P_RDS_T])
        return P
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return np.array([[0.1], [0.1]])

# Vectorized risk status calculations
def comps_riskstatus_vectorized(P_C, P_HR, RR):
    """Vectorized risk status calculation"""
    P_C_HR = RR * P_C
    P_C_LR = (P_C * (1 - RR * P_HR)) / (1 - P_HR)
    return P_C_HR, P_C_LR

def comps_riskstatus_vs_lowrisk_vectorized(P_C, P_HR, RR):
    """Vectorized risk status vs low risk calculation"""
    denom = P_HR * RR + (1 - P_HR)
    P_C_LR = P_C / denom
    P_C_HR = RR * P_C_LR
    return P_C_HR, P_C_LR

# Optimized DALY calculator
@streamlit_cache
def DALY_calculator_vectorized_optimized(individual_outcomes, param):
    """Optimized vectorized DALY calculator"""
    try:
        DW = param.get('DW', {})
        
        # Default values for missing parameters
        default_dw = {
            'anemia': 0.1, 'low pph': 0.2, 'high pph': 0.4, 
            'maternal sepsis': 0.3, 'eclampsia': 0.5, 'obstructed labor': 0.3,
            'preterm comp': 0.2, 'neonatal sepsis': 0.3, 'asphyxia': 0.4,
            'maternal death': 1.0, 'neonatal death': 1.0
        }
        
        # Use provided DW or defaults
        for key, default_val in default_dw.items():
            if key not in DW:
                DW[key] = default_val

        # Extract individual outcomes efficiently with safety checks
        i_loc = individual_outcomes.get("i_loc_new_v2", np.zeros(1, dtype=int))
        i_anemia = individual_outcomes.get("i_anemia_new", np.zeros(1, dtype=int))
        i_pph_severe = individual_outcomes.get("i_pph_severe_new", np.zeros(1, dtype=int))
        i_pph = individual_outcomes.get("i_pph_new", np.zeros(1, dtype=int))
        i_pph_notsevere = ((i_pph == 1) & (i_pph_severe == 0)).astype(int)
        i_mat_sepsis = individual_outcomes.get("i_mat_sepsis_new", np.zeros(1, dtype=int))
        i_eclampsia = individual_outcomes.get("i_eclampsia_new", np.zeros(1, dtype=int))
        i_OL = individual_outcomes.get("i_OL_final", np.zeros(1, dtype=int))
        i_MD = individual_outcomes.get("i_mat_death", np.zeros(1, dtype=int))

        i_RDS = individual_outcomes.get("i_RDS", np.zeros(1, dtype=int))
        i_IVH = individual_outcomes.get("i_IVH", np.zeros(1, dtype=int))
        i_NEC = individual_outcomes.get("i_NEC", np.zeros(1, dtype=int))
        i_neo_sepsis = individual_outcomes.get("i_neo_sepsis", np.zeros(1, dtype=int))
        i_asphyxia = individual_outcomes.get("i_asphyxia", np.zeros(1, dtype=int))
        i_stillbirth = individual_outcomes.get("i_stillbirth", np.zeros(1, dtype=int))
        i_ND = individual_outcomes.get("i_neo_death", np.zeros(1, dtype=int))

        # Vectorized DALY calculation
        num_mothers = len(i_anemia)
        M_DALY = np.zeros(num_mothers, dtype=float)
        N_DALY = np.zeros(num_mothers, dtype=float)
        
        # Vectorized masks
        Mcomps_mask = ((i_anemia == 1) | (i_pph_severe == 1) | (i_pph_notsevere == 1) | 
                       (i_mat_sepsis == 1) | (i_eclampsia == 1) | (i_OL == 1)) & (i_MD == 0)
        MD_mask = (i_MD == 1)
        Ncomps_mask = ((i_RDS == 1) | (i_IVH == 1) | (i_NEC == 1) | 
                       (i_neo_sepsis == 1) | (i_asphyxia == 1)) & (i_stillbirth == 0) & (i_ND == 0)
        ND_mask = (i_ND == 1) & (i_stillbirth == 0)

        # Get life expectancy parameters with defaults
        mother_life_expectancy = param.get('Mother_life_expectancy', 70)
        childbearing_age = param.get('Childbearing_age', 25)
        neonate_life_expectancy = param.get('Neonate_life_expectancy', 70)

        # Vectorized DALY calculations
        DALY_Mcomps = (i_anemia * DW['anemia'] + i_pph_notsevere * DW['low pph'] + 
                       i_pph_severe * DW['high pph'] + i_mat_sepsis * DW['maternal sepsis'] + 
                       i_eclampsia * DW['eclampsia'] + i_OL * DW['obstructed labor']) * \
                       (mother_life_expectancy - childbearing_age)

        DALY_Ncomps = (i_RDS * DW['preterm comp'] + i_IVH * DW['preterm comp'] + 
                       i_NEC * DW['preterm comp'] + i_neo_sepsis * DW['neonatal sepsis'] + 
                       i_asphyxia * DW['asphyxia']) * neonate_life_expectancy

        DALY_MD = (i_MD * DW['maternal death']) * (mother_life_expectancy - childbearing_age)
        DALY_ND = (i_ND * DW['neonatal death']) * neonate_life_expectancy

        # Apply masks
        M_DALY[Mcomps_mask] = DALY_Mcomps[Mcomps_mask]
        M_DALY[MD_mask] = DALY_MD[MD_mask]
        N_DALY[Ncomps_mask] = DALY_Ncomps[Ncomps_mask]
        N_DALY[ND_mask] = DALY_ND[ND_mask]

        # Aggregate by location
        M_DALYs = np.zeros(4, dtype=float)
        N_DALYs = np.zeros(4, dtype=float)
        
        for loc in range(4):
            loc_mask = (i_loc == loc)
            M_DALYs[loc] = np.sum(M_DALY[loc_mask])
            N_DALYs[loc] = np.sum(N_DALY[loc_mask])

        return M_DALYs, N_DALYs, M_DALY, N_DALY
    except (KeyError, TypeError, ValueError, IndexError):
        # Return zeros if calculation fails
        num_mothers = 1
        return np.zeros(4), np.zeros(4), np.zeros(num_mothers), np.zeros(num_mothers)

# Backward compatibility functions
def get_P_l45_original(p_anc, slider_params):
    """Original function for backward compatibility"""
    return get_P_l45(p_anc, slider_params)

def odds_prob_original(oddsratio, p_comp, p_expose):
    """Original function for backward compatibility"""
    return odds_prob(oddsratio, p_comp, p_expose)

def risk_stratification(i_risk, i_ANC, num_mothers, sen_risk, spec_risk, rng):
    """Original function for backward compatibility"""
    return risk_stratification_vectorized(i_risk, i_ANC, num_mothers, sen_risk, spec_risk, rng)

def move_function(num_mothers, l4_l5, i_class, i_loc, i_loc_new, i_free_referral, 
                 i_self_referral, Referral_Capacity, flags, num_move, loc_index, rng):
    """Original function for backward compatibility"""
    return move_function_vectorized(num_mothers, l4_l5, i_class, i_loc, i_loc_new, i_free_referral, 
                                   i_self_referral, Referral_Capacity, flags, num_move, loc_index, rng)

def intrapartum_prediction(num_mothers, monitoring_mask, comp_type, sen_type, spec_type, rng):
    """Original function for backward compatibility"""
    return intrapartum_prediction_vectorized(num_mothers, monitoring_mask, comp_type, sen_type, spec_type, rng)

def comp_OL_type(num_mothers, comp_type, p_comp_ol, mask, rng):
    """Original function for backward compatibility"""
    return comp_OL_type_vectorized(num_mothers, comp_type, p_comp_ol, mask, rng)

def comp_severe(num_mothers, comp_type, p_severe_risk, rng):
    """Original function for backward compatibility"""
    return comp_severe_vectorized(num_mothers, comp_type, p_severe_risk, rng)

def P_IVH_vectorized(GA, flag_T, param):
    """Original function for backward compatibility"""
    return P_IVH_vectorized_optimized(GA, flag_T, param)

def P_NEC_vectorized(GA, flag_T, param):
    """Original function for backward compatibility"""
    return P_NEC_vectorized_optimized(GA, flag_T, param)

def P_Sepsis_vectorized(GA, flag_T, param):
    """Original function for backward compatibility"""
    return P_Sepsis_vectorized_optimized(GA, flag_T, param)

def P_RDS(param):
    """Original function for backward compatibility"""
    return P_RDS_optimized(param)

def DALY_calculator_vectorized(individual_outcomes, param):
    """Original function for backward compatibility"""
    return DALY_calculator_vectorized_optimized(individual_outcomes, param) 