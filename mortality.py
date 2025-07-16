import numpy as np
from global_func import baseline_p_death, P_intervention
import streamlit as st

def initialize_MM_params_vectorized(track, param, flags, i, MC, M, NC):
    MC = MC
    M = M
    NC = NC
    P = {}  # dict to restore probabilities
    n = {}  # dict to restore counts
    E = {}   # dict to restore effects
    OR = {}  # dict to restore odds ratios
    W = {}  # dict to restore weights
    MD = {}  # dict to restore maternal deaths
    ND = {}  # dict to restore neonatal deaths

    n["LB_L"] = track['LB_Track'][i, :].astype(int)  # number of live births by facility level

    # % Death
    P["D_RDS"] = param["D_RDS"]
    P["D_IVH"] = param["D_IVH"]
    P["D_NEC"] = param["D_NEC"]
    P["D_Sepsis"] = param["D_Sepsis"]
    P["D_asphyxia"] = param["D_asphyxia"]
    p_mat_death_baseline, p_neo_death_baseline = baseline_p_death(track, M, param, flags, i, n)
    P["mat_death_labor"] = np.array(p_mat_death_baseline)
    P["neo_death_labor"] = np.array(p_neo_death_baseline)

    # The effect of transfer, severity of complications, planned c-section, emergency c-section
    P['MM_home'] = param['p_MM_home']  # baseline probability of maternal death at home
    P['NM_home'] = param['p_NM_home']  # baseline probability of neonatal death at home
    W["weight_facility_mat"] = param['weight_facility_mat']  # weight of facility in contributing to maternal death
    W["weight_facility_neo"] = param['weight_facility_neo']  # weight of facility in contributing to neonatal death
    OR["MM_CSvsSVD"] = param["OR_MM_CSvsSVD"]  # odds ratio of maternal death for CS vs SVD
    OR["MM_EmCSvsELCS"] = param["OR_MM_EmCSvsELCS"]  # odds ratio of maternal death for emergency CS vs elective CS
    OR['MM_transfer'] = param['OR_MM_transfer']  # odds ratio of maternal death for transfer

    # % Initialize counters
    keys_MD = ["death"]
    keys_ND = ["death"]

    for key in keys_MD:
        MD[key] = np.zeros(4)
    for key in keys_ND:
        ND[key] = np.zeros(4)
    return P, n, MC, M, NC, E, OR, MD, ND, W

def f_MM_vectorized(track, param, flags, i, MC, M, NC, individual_outcomes, rng):
    # Initialize parameters and counters
    P, n, MC, M, NC, E, OR, MD, ND, W = initialize_MM_params_vectorized(track, param, flags, i, MC, M, NC)

    i_loc_new_v2 = individual_outcomes["i_loc_new_v2"].values
    i_mod = individual_outcomes["i_mod"].values
    i_transfer_pred = individual_outcomes["i_transfer_pred"].values
    i_transfer_actual = individual_outcomes["i_transfer_actual"].values
    i_severe_new = individual_outcomes["i_severe_new"].values
    i_RDS = individual_outcomes["i_RDS"].values
    i_IVH = individual_outcomes["i_IVH"].values
    i_NEC = individual_outcomes["i_NEC"].values
    i_neo_sepsis = individual_outcomes["i_neo_sepsis"].values
    i_asphyxia = individual_outcomes["i_asphyxia"].values
    i_pph_severe = individual_outcomes["i_pph_severe_new"].values
    i_sepsis_severe = individual_outcomes["i_sepsis_severe"].values
    i_eclampsia_severe = individual_outcomes["i_eclampsia_severe"].values
    i_ol_severe = individual_outcomes["i_ol_severe"].values
    i_ruptured_uterus_severe = individual_outcomes["i_ruptured_uterus_severe"].values
    i_aph_severe = individual_outcomes["i_aph_severe"].values
    num_mothers = i_loc_new_v2.shape[0]

    i_transfer = ((i_transfer_pred == 1) | (i_transfer_actual == 1))
    i_CS = np.isin(i_mod, ["EmCS", "ELCS"]).astype(int)

    severe_mask = (i_severe_new == 1)
    home_mask = (i_loc_new_v2 == 0)
    facility_mask = (~home_mask)
    CS_mask = (i_CS == 1)
    EmCS_mask = (i_mod == "EmCS")
    transfer_mask = (i_transfer == 1)
    neo_coms_mask = ((i_RDS == 1) | (i_IVH == 1) | (i_NEC == 1) | (i_neo_sepsis == 1) | (i_asphyxia == 1))

    #Maternal Deaths - different weight version
    death_cause = np.full(num_mothers, "none", dtype=object)

    # Complication risk weights (constant across locations)
    comp_names = ["pph", "sepsis", "eclampsia", "ol", "other", "aph"]
    comp_risks = np.stack([
        i_pph_severe * param["MM_weight_pph"],
        i_sepsis_severe * param["MM_weight_sepsis"],
        i_eclampsia_severe * param["MM_weight_eclampsia"],
        i_ol_severe * param["MM_weight_ol"],
        np.ones(num_mothers, dtype=int) * param["p_MM_others"],
        #i_ruptured_uterus_severe * param["MM_weight_ruptured_uterus"],
        i_aph_severe * param["MM_weight_aph"],
    ], axis=1)

    # Get max risk index and value for each mother
    max_risk_indices = np.argmax(comp_risks, axis=1)
    base_comp_risks = comp_risks[np.arange(num_mothers), max_risk_indices]

    # Location-based modifier
    location_modifier = np.zeros(num_mothers, dtype=float)
    location_modifier[home_mask] = P["MM_home"]
    location_modifier[facility_mask] = W['weight_facility_mat'] * P["mat_death_labor"][i_loc_new_v2[facility_mask]]

    p_death = base_comp_risks * location_modifier

    # **Step 2: Apply Odds Ratios (OR) for CS & EmCS**
    cs_update_mask = severe_mask & CS_mask
    p_death[cs_update_mask] = (
            OR["MM_CSvsSVD"] * p_death[cs_update_mask] /
            ((1 - p_death[cs_update_mask]) + (OR["MM_CSvsSVD"] * p_death[cs_update_mask]))
    )

    # **Step 3: Apply OR for Emergency CS (EmCS)**
    emcs_update_mask = severe_mask & EmCS_mask
    p_death[emcs_update_mask] = (
            OR["MM_EmCSvsELCS"] * p_death[emcs_update_mask] / (
                (1 - p_death[emcs_update_mask]) + (OR["MM_EmCSvsELCS"] * p_death[emcs_update_mask]))
    )

    # **Step 4: Apply OR for Transfers**
    transfer_update_mask = severe_mask & transfer_mask
    p_death[transfer_update_mask] = (
            OR["MM_transfer"] * p_death[transfer_update_mask] / (
                (1 - p_death[transfer_update_mask]) + (OR["MM_transfer"] * p_death[transfer_update_mask]))
    )

    # **Step 3: Clip Death Probabilities & Assign Maternal Deaths**
    p_death = np.clip(p_death, 0, 1)  # Ensure probabilities stay within [0,1]
    # if i == 4:
    #     st.text(p_death[40:60])
    i_mort = (rng.random(num_mothers) < p_death).astype(int) # Assign deaths

    # Assign death cause
    death_cause[i_mort == 1] = np.array(comp_names)[max_risk_indices[i_mort == 1]]

    # Neonatal Deaths -- need recalibration
    # **Step 1: Initialize Neonatal Death Probability & Outcome**
    p_neo_death = np.zeros(num_mothers, dtype=float)

    # **Step 2: Assign baseline probability based on location**
    p_neo_death[home_mask & neo_coms_mask] = P["NM_home"]
    p_neo_facility_death = W['weight_facility_neo'] * (P["neo_death_labor"][i_loc_new_v2])
    p_neo_death[facility_mask & neo_coms_mask] = p_neo_facility_death[facility_mask & neo_coms_mask]

    # **Step 5: Apply Transfer Effect**
    p_neo_death[transfer_mask] = param['OR_NM_transfer'] * p_neo_death[transfer_mask] / (
            (1 - p_neo_death[transfer_mask]) + (param['OR_NM_transfer'] * p_neo_death[transfer_mask])
    )

    # **Step 6: Assign Neonatal Deaths**
    i_ND = (rng.random(num_mothers) < np.clip(p_neo_death, 0, 1)).astype(int)  # Clip & sample ND

    # Update counters
    i_mort = i_mort.astype(int)
    i_ND = i_ND.astype(int)
    np.add.at(MD["death"], i_loc_new_v2, i_mort)  # Update maternal deaths per facility
    np.add.at(ND["death"], i_loc_new_v2, i_ND)  # Update neonatal deaths per facility

    #update individual outcomes
    individual_outcomes["i_mat_death"] = i_mort.astype(int)
    individual_outcomes["i_neo_death"] = i_ND.astype(int)
    individual_outcomes["i_transfer"] = i_transfer.astype(int)
    individual_outcomes["death_cause"] = death_cause.astype(str)

    return MC, MD, NC, ND, M, individual_outcomes

# def initialize_MM_params(track, param, flags, i, MC, M, NC):
#     MC = MC
#     M = M
#     NC = NC
#     P = {}  # dict to restore probabilities
#     n = {}  # dict to restore counts
#     E = {}   # dict to restore effects
#     OR = {}  # dict to restore odds ratios
#     W = {}  # dict to restore weights
#     MD = {}  # dict to restore maternal deaths
#     ND = {}  # dict to restore neonatal deaths
#
#     n["LB_L"] = track['LB_Track'][i, :].astype(int)  # number of live births by facility level
#     PT_mask = np.array([1] * 10 + [0] * 8, dtype=bool)
#     FT_mask = ~PT_mask
#     P["GA"] = np.zeros((4, len(param['GA_sequence'])))
#     P["PT"] = np.zeros(4)
#     P["FT"] = np.zeros(4)
#     n["PT"] = np.zeros(4)
#     n["FT"] = np.zeros(4)
#     n["GA_sequence"] = param['GA_sequence']
#     for k in range(4):
#         P["GA"][k] = M["GA"][k] / np.sum(M["GA"][k])  # probability of GA by facility level
#         P["PT"][k] = np.sum(P["GA"][k][PT_mask])  # probability of preterm by facility level
#         P["FT"][k] = np.sum(P["GA"][k][FT_mask])  # probability of full-term by facility level
#         n["PT"][k] = np.sum(M["GA"][k][PT_mask])  # number of preterm by facility level
#         n["FT"][k] = np.sum(M["GA"][k][FT_mask])  # number of full-term by facility level
#
#     P["CS"] = M["CS"] / n[
#         "LB_L"]  # / n_FT                                                    # probability of getting CS by facility level among full-term
#     P["EmCS|CS"] = np.where(M["CS"] > 0, M["Emergency_CS"] / M["CS"],
#                             0)                                               # probability of getting emergency CS by facility level among CS
#
#     # % Death
#     P["D_RDS"] = param["D_RDS"]
#     P["D_IVH"] = param["D_IVH"]
#     P["D_NEC"] = param["D_NEC"]
#     P["D_Sepsis"] = param["D_Sepsis"]
#     P["D_asphyxia"] = param["D_asphyxia"]
#     p_mat_death_baseline, p_neo_death_baseline = baseline_p_death(track, M, param, flags, i, n)
#     P["mat_death_labor"] = np.array(p_mat_death_baseline)
#     P["neo_death_labor"] = np.array(p_neo_death_baseline)
#
#     # The effect of transfer, severity of complications, planned c-section, emergency c-section
#     P['MM_home'] = param['p_MM_home']  # baseline probability of maternal death at home
#     P['NM_home'] = param['p_NM_home']  # baseline probability of neonatal death at home
#     W["weight_facility_mat"] = param['weight_facility_mat']  # weight of facility in contributing to maternal death
#     W["weight_facility_neo"] = param['weight_facility_neo']  # weight of facility in contributing to neonatal death
#     OR["MM_CSvsSVD"] = param["OR_MM_CSvsSVD"]  # odds ratio of maternal death for CS vs SVD
#     OR["MM_EmCSvsELCS"] = param["OR_MM_EmCSvsELCS"]  # odds ratio of maternal death for emergency CS vs elective CS
#     OR['MM_transfer'] = param['OR_MM_transfer']  # odds ratio of maternal death for transfer
#
#     # The probability of getting complications by facility level
#     P["pph"] = MC['pph'] / n["LB_L"]                    # probability of getting PPH by facility level
#     P["sepsis"] = MC['mat_sepsis'] / n["LB_L"]          # probability of getting maternal sepsis
#     P["eclampsia"] = MC['eclampsia'] / n["LB_L"]        # probability of getting eclampsia by facility level
#     P["OL"] = MC["OL"] / n["LB_L"]                      # probability of getting obstructed labor
#     P["ruptured_uterus"] = MC["ruptured_uterus"] / n["LB_L"]          # probability of getting other complications by facility level
#     P["severe"] = np.where(MC["comps_death"] > 0,
#                            MC["severe_comps"] / MC["comps_death"],
#                            0)                           # probability of getting severe complications by facility level given complications
#     P["severe"] = np.clip(P["severe"], 0, 1)
#     P["RDS"] = NC["RDS"] / n["PT"]                      # probability of RDS by preterm by facility level
#     P["IVH"] = NC["IVH"] / n["LB_L"]                    # probability of IVH by facility level
#     P["NEC"] = NC["NEC"] / n["LB_L"]                    # probability of NEC by facility level
#     P["neo_sepsis"] = NC["neo_sepsis"] / n["LB_L"]      # probability of neonatal sepsis by facility level
#
#     # Probability of emergency transfer
#     P["ER_transfer"] = M["ER_trans_actual"] / n["LB_L"]
#
#     # % Initialize counters
#     M["LB_L_old"] = n["LB_L"]
#     keys_MD = ["death"]
#     keys_ND = ["death"]
#
#     for key in keys_MD:
#         MD[key] = np.zeros(4)
#     for key in keys_ND:
#         ND[key] = np.zeros(4)
#     return P, n, MC, M, NC, E, OR, MD, ND, W

# def f_MM(track, param, flags, i, MC, M, NC):
#     # Initialize parameters and counters
#     P, n, MC, M, NC, E, OR, MD, ND, W = initialize_MM_params(track, param, flags, i, MC, M, NC)
#
#     # Begin simulations
#     for k_L in range(4):
#         for k_LB in range(n["LB_L"][k_L]):
#             #Initialize variables
#             #i_FT = np.random.binomial(1, P["FT"][k_L])
#             (i_MgSO4, i_antibiotics, i_pph, i_sepsis, i_eclampsia, i_ol, i_ruptured_uterus,
#              i_mort, i_severe, i_emCS, i_transfer, i_ND) = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
#
#             i_jGA = np.searchsorted(np.cumsum(P["GA"][k_L]), np.random.rand())                      # % actual index of GA
#             i_GA = n["GA_sequence"][i_jGA]  # % actual GA                                                           # % actual GA
#             i_preterm = 1 if i_GA < 37 else 0
#
#             i_transfer = np.random.binomial(1, P["ER_transfer"][k_L])
#             i_CS = np.random.binomial(1, P["CS"][k_L])
#             if i_CS:
#                 i_emCS = np.random.binomial(1, P["EmCS|CS"][k_L])
#             i_pph = np.random.binomial(1, P["pph"][k_L])
#             i_sepsis = np.random.binomial(1, P["sepsis"][k_L])
#             i_eclampsia = np.random.binomial(1, P["eclampsia"][k_L])
#             i_ol = np.random.binomial(1, P["OL"][k_L])
#             i_ruptured_uterus = np.random.binomial(1, P["ruptured_uterus"][k_L])
#             if i_preterm:
#                 i_RDS = np.random.binomial(1, P["RDS"][k_L])
#             else:
#                 i_RDS = 0
#             i_IVH = np.random.binomial(1, P["IVH"][k_L])
#             i_NEC = np.random.binomial(1, P["NEC"][k_L])
#             i_neo_sepsis = np.random.binomial(1, P["neo_sepsis"][k_L])
#
#
#             #Maternal Deaths and Interventions
#             if i_pph or i_sepsis or i_eclampsia or i_ol or i_ruptured_uterus:
#                 i_severe = np.random.binomial(1, P["severe"][k_L])
#                 if i_severe:
#                     if k_L == 0:
#                         p_death_i = P["MM_home"]
#                     else:
#                         p_death_i = W["weight_facility"] * P["mat_death_labor"][k_L]
#                     if i_CS:
#                         #(OR * P0) / ((1 - P0) + (OR * P0))
#                         p_death_i = OR["MM_CSvsSVD"] * p_death_i / ((1 - p_death_i) + (OR["MM_CSvsSVD"] * p_death_i))
#                         if i_emCS:
#                             p_death_i = OR["MM_EmCSvsELCS"] * p_death_i / ((1 - p_death_i) + (OR["MM_EmCSvsELCS"] * p_death_i))
#                     if i_transfer:
#                         p_death_i = OR['MM_transfer'] * p_death_i / ((1 - p_death_i) + (OR['MM_transfer'] * p_death_i))
#
#                     #Single interventions
#                     if i_sepsis:
#                         if np.random.binomial(1, P["antibiotics"][k_L]):
#                             i_antibiotics = 1
#                             p_death_i = p_death_i * E["int_sepsis"]
#                     if i_eclampsia:
#                         if np.random.binomial(1, P["MgSO4"][k_L]):
#                             i_MgSO4 = 1
#                             p_death_i = p_death_i * E["int_eclampsia"]
#
#                     p_death_i = np.clip(p_death_i, 0, 1)
#                     i_mort = np.random.binomial(1, p_death_i)
#                 else:
#                     i_mort = 0
#
#             #Neonatal Deaths -- need recalibration
#             if k_L < 2:  # % home or L2/3
#                 ND_scale = param["D_scale_fac"]  # facility reduces death by 29%
#             else:
#                 ND_scale = 1
#
#             if i_RDS:
#                 p_neo_death_i = P["D_RDS"][0] if i_GA < 32 else P["D_RDS"][1]
#             elif i_IVH:
#                 p_neo_death_i = P["D_IVH"]
#             elif i_NEC:
#                 p_neo_death_i = P["D_NEC"]
#             elif i_neo_sepsis:
#                 p_neo_death_i = P["D_Sepsis"]
#             else:
#                 p_neo_death_i = 0
#             p_neo_death_i = ND_scale * p_neo_death_i
#             if i_transfer:
#                 p_neo_death_i = param['OR_NM_transfer'] * p_neo_death_i / ((1 - p_neo_death_i) + (param['OR_NM_transfer'] * p_neo_death_i))
#
#             if p_neo_death_i > 0:
#                 i_ND = np.random.binomial(1, p_neo_death_i)
#
#             #Update counters
#             M["MgSO4"][k_L] += i_MgSO4
#             M["antibiotics"][k_L] += i_antibiotics
#             MD["death"][k_L] += i_mort
#             ND["death"][k_L] += i_ND
#     return MC, MD, NC, ND, M