import numpy as np
import random
import streamlit as st
import time
import pandas as pd
from global_func import (P_Prolonged, P_Prolonged_vectorized, P_Sepsis_vectorized, P_Sepsis, P_NEC_vectorized, P_NEC,
                         P_IVH_vectorized, P_IVH, comps_riskstatus_vs_lowrisk, \
    sensors_accuracy_vectorized, sensors_accuracy, fetal_sensor_calculator, P_intervention, \
                         intrapartum_prediction, comp_OL_type, comp_severe, emergency_transfer_comps, preterm_complication, SI_reduction)

def initialize_intra_params(individual_outcomes, track, flags, param, i, rng):
    i_GA = individual_outcomes['i_GA'].values
    num_mothers = len(i_GA)
    n_FT = np.count_nonzero(i_GA >= 37)

    # global parameters
    P = {}  # dict to restore probabilities
    n = {}  # dict to restore counts
    E = {}  # dict to restore effects
    S = {}  # dict to restore supplies and capacities

    # maternal complications
    P["FT_all"] = n_FT / num_mothers
    P["severe"] = param["severe"]                                                               # probability of severe complications by risk level
    P["OL"] = param["OL"]                                                                       # probability of obstructed labor if not prolonged vs prolonged
    P["hypoxia"] = param["p_hypoxia"] / P["FT_all"]                                             # probability of hypoxia for full-term live births

    P["OL_by_risk"] = np.array([param["OL_lowrisk"], param["OL_highrisk"]])
    P["hypoxia_by_risk"] = np.array(comps_riskstatus_vs_lowrisk(P["hypoxia"], param['p_highrisk'], param["RR_comp_highrisk_vs_lowrisk"]))
    P["ruptured_by_risk"] = np.array([param["ruptured_uterus_lowrisk"], param["ruptured_uterus_highrisk"]])
    P["aph_by_risk"] = np.array([param["aph_lowrisk"], param["aph_highrisk"]])
    P["eclampsia_by_risk_anemia"] = np.vstack([param["eclampsia_lowrisk_anemia"], param["eclampsia_highrisk_anemia"]])

    # maternal complications with anemia
    P["pph_OL_anemia"] = param["pph_OL_anemia"]
    P["mat_sepsis_OL_anemia"] = param["mat_sepsis_OL_anemia"]
    P["pph_elective_CS_anemia"] = param["pph_elective_CS_anemia"]
    P["mat_sepsis_elective_CS_anemia"] = param["mat_sepsis_elective_CS_anemia"]
    P["pph_emergency_CS_anemia"] = param["pph_emergency_CS_anemia"]
    P["mat_sepsis_emergency_CS_anemia"] = param["mat_sepsis_emergency_CS_anemia"]
    P["pph_other_anemia"] = param["pph_other_anemia"]
    P["mat_sepsis_other_anemia"] = param["mat_sepsis_other_anemia"]

    # neonatal complications by delivery mode
    P["RDS_T"] = param["RDS_T"]
    P["stillbirth_OL"] = param["p_stillbirth_OL"]            # probability of stillbirth by OL
    P["stillbirth_hypoxia"] = param["p_stillbirth_hypoxia"]  # probability of stillbirths by hypoxia
    P["asphyxia_OL"] = param["p_asphyxia_OL"]                # probability of asphyxia by OL
    P["neo_sepsis_OL"] = param["p_neo_sepsis_OL"]            # probability of neonatal sepsis by OL

    #Sensitivity and specificity of traditional monitoring by location
    E["sen_comp_trad"] = np.array([0.5, param["sen_comp_trad"] * 0.8, param["sen_comp_trad"], param[
        "sen_comp_trad"]])
    E["spec_comp_trad"] = np.array([0.5, param["spec_comp_trad"] * 0.8, param["spec_comp_trad"], param[
        "spec_comp_trad"]])

    # Facility capacity
    S["Fac_capacity"] = track['Facility_Capacity_Track'][i, 0]
    CS_Capacity = track['CS_Capacity_Track'][i, 0]
    if flags['flag_capacity']:
        S["CS_capacity"] = np.array([0, 0, CS_Capacity, CS_Capacity])
    else:
        S["CS_capacity"] = param["p_cs_capacity"]

    # CS capacity
    # if flags['flag_capacity'] and flags['flag_intrasensor']:
    #     S["CS_capacity"] = param["p_cs_capacity_sdr_sensor"]
    # elif flags['flag_capacity'] and not flags['flag_intrasensor']:
    #     S["CS_capacity"] = param["p_cs_capacity_sdr"]
    # elif not flags['flag_capacity'] and flags['flag_intrasensor']:
    #     S["CS_capacity"] = param["p_cs_capacity_sensor"]
    # else:
    #     S["CS_capacity"] = param["p_cs_capacity"]
    P["CS_AVD_ratio"] = np.array([param["CS_AVD_ratio"], 1 - param["CS_AVD_ratio"]])

    # Emergency transfer intervention
    P["transfer_rate_severe"] = np.zeros((4, 5))
    P["transfer_rate_notsevere"] = np.zeros((4, 5))
    P["transfer_rate_preterm"] = np.zeros((4, 5))
    flag_transfer = flags['flag_transfer']
    if flag_transfer:
        p_transfer_severe = max(param["HSS"]["P_transfer"], param['t_l23_l45_severe'])
        p_transfer_nonsevere = max(param["HSS"]["P_transfer"], param['t_l23_l45_notsevere'])
        p_transfer_preterm = max(param["HSS"]["P_transfer"], param['t_l23_l45_preterm'])
        t_l4_l4_severe = 0  ##Assume in SDR scenario, not need to transfer from L4 to L5
        t_l4_l5_severe = 0  ##Assume in SDR scenario, not need to transfer from L4 to L5
    else:
        p_transfer_severe = param['t_l23_l45_severe']
        p_transfer_nonsevere = param['t_l23_l45_notsevere']
        p_transfer_preterm = param['t_l23_l45_preterm']
        t_l4_l4_severe = param['t_l4_l4_severe']
        t_l4_l5_severe = param['t_l4_l5_severe']

    f_transfer_rates_severe = np.array([
        [0.00, 0.00, 0.00, 0.00],
        [0.00, 0.00, p_transfer_severe / 2, p_transfer_severe / 2],
        [0.00, 0.00, t_l4_l4_severe, t_l4_l5_severe],
        [0.00, 0.00, 0.00, 0.00]
    ]) / 100

    f_transfer_rates_notsevere = np.array([
        [0.00, 0.00, 0.00, 0.00],
        [0.00, 0.00, p_transfer_nonsevere / 2, p_transfer_nonsevere / 2],
        [0.00, 0.00, 0.00, 0.00],
        [0.00, 0.00, 0.00, 0.00]
    ]) / 100

    f_transfer_rates_preterm = np.array([
        [0.00, 0.00, 0.00, 0.00],
        [0.00, 0.00, p_transfer_preterm / 2, p_transfer_preterm / 2],
        [0.00, 0.00, 0.00, 0.00],
        [0.00, 0.00, 0.00, 0.00]
    ]) / 100

    for k_L in range(4):
        P["transfer_rate_severe"][k_L, 0] = 1 - f_transfer_rates_severe[k_L].sum()
        P["transfer_rate_severe"][k_L, 1:] = f_transfer_rates_severe[k_L]
        P["transfer_rate_notsevere"][k_L, 0] = 1 - f_transfer_rates_notsevere[k_L].sum()
        P["transfer_rate_notsevere"][k_L, 1:] = f_transfer_rates_notsevere[k_L]
        P["transfer_rate_preterm"][k_L, 0] = 1 - f_transfer_rates_preterm[k_L].sum()
        P["transfer_rate_preterm"][k_L, 1:] = f_transfer_rates_preterm[k_L]

    # Intrapartum sensor intervention
    sensors = fetal_sensor_calculator(track, param, i, flags, rng)
    dopplers_ratio = np.array(
        [sensors['dopplers_l23_ratio'], sensors['dopplers_l4_ratio'], sensors['dopplers_l5_ratio']])
    CTGs_ratio = np.array([sensors['CTGs_l23_ratio'], sensors['CTGs_l4_ratio'], sensors['CTGs_l5_ratio']])
    S["dopplers"] = np.array([0, dopplers_ratio[0], dopplers_ratio[1], dopplers_ratio[2]])
    S["dopplers"] = np.clip(S["dopplers"], 0, 1)
    S["CTGs"] = np.array([0, CTGs_ratio[0], CTGs_ratio[1], CTGs_ratio[2]])
    S["CTGs"] = np.clip(S["CTGs"], 0, 1)
    flag_AI = flags['flag_sensor_ai']
    if flag_AI:
        E["sen_prolonged_IS"] = param["E"]["sens_sensor"]
        E["spec_prolonged_IS"] = param["E"]["spec_sensor"]
        E["sen_ol_IS"] = param["E"]["sens_sensor"]
        E["spec_ol_IS"] = param["E"]["spec_sensor"]
        E["sen_hypoxia_IS"] = param["E"]["sens_sensor"]
        E["spec_hypoxia_IS"] = param["E"]["spec_sensor"]
    else:
        E["sen_prolonged_IS"] = param["sen_prolonged_IS"]
        E["spec_prolonged_IS"] = param["spec_prolonged_IS"]
        E["sen_ol_IS"] = param["sen_ol_IS"]
        E["spec_ol_IS"] = param["spec_ol_IS"]
        E["sen_hypoxia_IS"] = param["sen_hypoxia_IS"]
        E["spec_hypoxia_IS"] = param["spec_hypoxia_IS"]

    # Single interventions
    P["knowledge"] = np.array([0, param['base_knowledge_L23'], param['base_knowledge_L45'], param['base_knowledge_L45']])
    if flags['flag_performance']:
        P["knowledge"][2] = param["HSS"]["knowledge"]
        P["knowledge"][3] = param["HSS"]["knowledge"]
    E["int_pph"] = param['E_pph_bundle']
    E["stillbirth_CS"] = param["E_stillbirth_CS"]   # efficacy of timely CS in preventing stillbirth by hypoxia
    E["oxytocin"] = param["E_oxytocin"]  # efficacy of oxytocin
    P["pph_bundle"] = P_intervention('flag_pph_bundle', "pph_bundle", 'S_pph_bundle', flags, param, S, P)
    P["oxytocin"] = P_intervention('flag_oxytocin', "oxytocin", "S_oxytocin", flags, param, S, P)
    E["int_eclampsia"] = param['E_MgSO4']
    E["int_sepsis"] = param['E_antibiotics']
    P["MgSO4"] = P_intervention('flag_MgSO4',"MgSO4", 'S_MgSO4', flags, param, S, P)
    P["antibiotics"] = P_intervention('flag_antibiotics',"antibiotics", 'S_antibiotics', flags, param, S, P)

    # Initialize counters
    MC = {}  # dict to restore maternal complications
    NC = {}  # dict to restore neonatal complications
    M = {}  # dict to restore maternal outcomes

    keys_MC = ["PL", "hypoxia", "OL", "mat_sepsis", "pph", "eclampsia", "ruptured_uterus", "aph", "severe_comps", "pph_severe", "comps_death",
               "anemia"]
    keys_NC = ["stillbirth", "asphyxia", "neo_sepsis", "RDS", "IVH", "NEC"]
    keys_M = ["CS", "CS_unnessary", "AVD", "SVD", "ER_trans_pred", "ER_trans_actual",
              "LB_L_new", "ANC_L_new", "Highrisk_L_new", "Elective_CS", "Emergency_CS",
              "iv_iron", "pph_bundle", "PT", "MgSO4", "antibiotics", "LB_L_initial"]
    for key in keys_MC:
        MC[key] = np.zeros(4)
    for key in keys_NC:
        NC[key] = np.zeros(4)
    for key in keys_M:
        M[key] = np.zeros(4)

    M["Elective_CS_risk"] = np.zeros(2)  # Initialize elective CS by risk level
    M["GA"] = np.zeros((4, len(param['GA_sequence'])))  # Initialize GA distribution by facility levels
    return P, n, E, S, MC, NC, M


def intrapartum_effect_vectorized(track, flags, param, i, individual_outcomes, rng):
    ##-------------------Parameter initialization-------------------##
    #Extract individual outcomes
    i_loc = individual_outcomes['i_loc'].values
    i_ANC = individual_outcomes['i_ANC'].values
    i_risk = individual_outcomes['i_risk'].values
    i_GA = individual_outcomes['i_GA'].values
    i_elec_CS = individual_outcomes['i_elec_CS'].values
    i_jGA = individual_outcomes['i_jGA'].values
    i_anemia_new = individual_outcomes['i_anemia_new'].values
    i_iv_iron = individual_outcomes['i_iv_iron'].values
    i_highrisk = i_risk.copy()
    i_preterm = (i_GA < 37)
    i_FT = (i_GA >= 37)
    i_mod = np.where(i_elec_CS, "ELCS", "SVD")
    num_mothers = i_loc.shape[0]
    binary_outcomes = np.zeros((num_mothers, 13), dtype=int)
    (i_PL, i_OL, i_hypoxia, \
     i_pph, i_mat_sepsis, i_stillbirth, i_asphyxia, i_neo_sepsis, \
     i_RDS, i_IVH, i_NEC, i_transfer_pred, i_transfer_actual) = binary_outcomes.T  # Transpose for easy indexing
    # Initialize other parameters
    P, n, E, S, MC, NC, M = initialize_intra_params(individual_outcomes, track, flags, param, i, rng)

    # Complications not related to intrapartum monitoring - can be preterm or full-term
    i_eclampsia = (rng.random(num_mothers) < P["eclampsia_by_risk_anemia"][i_highrisk, i_anemia_new]).astype(int)
    i_ruptured_uterus = (rng.random(num_mothers) < P["ruptured_by_risk"][i_highrisk]).astype(int)
    i_aph = (rng.random(num_mothers) < P["aph_by_risk"][i_highrisk]).astype(int)

    ####----------------------------Intrapartum Monitoring ---------------------------------####
    i_intra_monitor = (i_FT & (i_elec_CS == 0)).astype(bool) #mothers need intrapartum monitoring
    index_intra_monitor = np.where(i_intra_monitor)[0]

    #**1) Initialize pre-labor complications
    P_PL = P_Prolonged_vectorized(i_GA, param)
    P_OL = P["OL_by_risk"][i_highrisk]
    P_hypoxia = P["hypoxia_by_risk"][i_highrisk]

    PL_true = (rng.random(num_mothers) < P_PL).astype(int)
    i_PL[index_intra_monitor] = PL_true[index_intra_monitor]
    index_ol_mask = np.where(i_intra_monitor & (i_PL == 0))[0]

    OL_true = (rng.random(num_mothers) < P_OL).astype(int)
    i_OL[index_ol_mask] = OL_true[index_ol_mask]

    index_hypoxia_mask = np.where(i_intra_monitor & (i_PL == 0) & (i_OL == 0))[0]
    hypoxia_true = (rng.random(num_mothers) < P_hypoxia).astype(int)
    i_hypoxia[index_hypoxia_mask] = hypoxia_true[index_hypoxia_mask]

    #**2) Fetal monitoring
    # extract sensitivity and specificity for each complication
    sen_PL, spec_PL, sen_OL, spec_OL, sen_hypoxia, spec_hypoxia, i_sensors = sensors_accuracy_vectorized(num_mothers, S, E, i_highrisk, i_loc, rng)

    # calculate TP, FP, TN, FN - only facilities with intrapartum monitoring
    facility_mask = (i_loc > 0)
    monitoring_mask = (facility_mask & i_intra_monitor).astype(bool)   #mothers can really get intrapartum monitoring in facilities

    i_PL_pred = intrapartum_prediction(num_mothers, monitoring_mask, i_PL, sen_PL, spec_PL, rng)
    i_OL_pred = intrapartum_prediction(num_mothers, monitoring_mask, i_OL, sen_OL, spec_OL, rng)
    i_hypoxia_pred = intrapartum_prediction(num_mothers, monitoring_mask, i_hypoxia, sen_hypoxia, spec_hypoxia, rng)

    #**3) Single interventions to reduce prolonged labor
    mother_need_treat = i_intra_monitor & (i_PL == 1) & (i_PL_pred == 1)
    index_treat_mask = np.where(mother_need_treat)[0]
    P_oxytocin = E["oxytocin"] * (P["oxytocin"][i_loc])  # Get effectiveness per facility
    PL_treated =  (rng.random(num_mothers) < P_oxytocin).astype(int)
    PL_removed = 1 - PL_treated
    i_PL_new = i_PL.copy()
    i_PL_pred_new = i_PL_pred.copy()
    i_PL_new[index_treat_mask] = PL_removed[index_treat_mask]
    i_PL_pred_new[index_treat_mask] = PL_removed[index_treat_mask]
    i_oxytocin = np.zeros(num_mothers, dtype=int)
    oxytocin_provided = (rng.random(num_mothers) < P["oxytocin"][i_loc]).astype(int)
    i_oxytocin[index_treat_mask] = oxytocin_provided[index_treat_mask]

    # 4) Initial delivery mode decided by monitoring
    emergency_mask = monitoring_mask & ((i_PL_pred_new == 1) | (i_OL_pred == 1) | (i_hypoxia_pred == 1))
    CS_capacity_mask = rng.random(num_mothers) < S["CS_capacity"][i_loc]                        # Check if CS is available
    emergency_cs_mask = emergency_mask & CS_capacity_mask                                               # emergency with CS capacity
    EmCS_or_AVD = rng.choice(["EmCS", "AVD"], size=num_mothers, p=P["CS_AVD_ratio"])
    i_mod[emergency_cs_mask] = EmCS_or_AVD[emergency_cs_mask]                                            # Assign `EmCS` or `AVD` for Mothers Who Need Emergency Delivery

    # 5) Emergency transfer for predicted complications - in L2/3
    i_loc_new_v1 = i_loc.copy()

    transfer_mask = emergency_mask & (i_mod == "SVD") & (i_loc == 1) # Define Transfer Mask (SVD Mothers with Predicted Complications)
    p_transfer = S["CS_capacity"][2] + S["CS_capacity"][3]
    with_cs_capacity = (rng.random(num_mothers) < p_transfer).astype(int)
    transfer_mask_2 = with_cs_capacity & transfer_mask
    n_transfer = np.sum(transfer_mask_2)

    #**Check facility capacity
    num_L4_L5 = np.count_nonzero(i_loc >= 2)                # Number of mothers in L4/L5
    max_capacity = S["Fac_capacity"].astype(int)            # Maximum Facility Capacity
    available_slots = max(0, max_capacity - num_L4_L5)      # Compute Available Capacity
    # Filter out mothers who need transfer
    shuffled_all = rng.permutation(num_mothers)             # shuffle all mother indices
    transfer_indices = np.where(transfer_mask_2)[0]         # identify mothers who need transfer
    shuffled_transfer = shuffled_all[np.isin(shuffled_all, transfer_indices)]  # filter only those who need transfer from the shuffled list
    # Ensure we only select from the shuffled transfer indices
    mask_can_transfer = np.zeros(num_mothers, dtype=bool)  # Always initialize mask (used or not)
    if available_slots > 0 and n_transfer > 0:             # Proceed only if allowed to transfer
        num_can_transfer = min(n_transfer, available_slots)
        selected_indices = shuffled_transfer[:num_can_transfer]
        mask_can_transfer[selected_indices] = True

    # Apply transfer to selected agents
    p_transfer_relative = np.array([S["CS_capacity"][2], S["CS_capacity"][3]]) / p_transfer
    l4_or_l5_all = rng.choice(np.array([2, 3]), size=num_mothers, p=p_transfer_relative)
    i_loc_new_v1[mask_can_transfer] = l4_or_l5_all[mask_can_transfer]
    i_mod[mask_can_transfer] = "EmCS"
    i_transfer_pred[mask_can_transfer] = 1

    ####----------------------------Home Births---------------------------------####
    home_mask = (i_loc_new_v1 == 0)
    i_mod[home_mask] = "SVD"        # All home births use "SVD"

    ####----------------------------Post-delivery complications---------------------------------####
    PL_lead_OL = ((i_PL_new == 1) & (i_mod == "SVD") & (rng.random(num_mothers) < P["OL"][1])).astype(int) #obstructed labor by prolonged labor
    OL_lead_OL = ((i_OL == 1) & (i_mod == "SVD")).astype(int)                                              #obstructed labor not caused by prolonged labor
    i_OL_final = ((PL_lead_OL == 1) | (OL_lead_OL == 1)).astype(int)                                       #sum of both

    # 1) **OL Complications: PPH, maternal sepsis, stillbirths, asphyxia, neonatal sepsis**
    i_OL_final_mask = (i_OL_final == 1)

    p_pph_ol = P["pph_OL_anemia"][i_anemia_new]
    p_sepsis_ol = P["mat_sepsis_OL_anemia"][i_anemia_new]
    p_stillbirth_ol = P["stillbirth_OL"]
    p_asphyxia_ol = P["asphyxia_OL"]
    p_neo_sepsis_ol = P["neo_sepsis_OL"]

    i_pph = comp_OL_type(num_mothers, i_pph, p_pph_ol, i_OL_final_mask, rng)
    i_mat_sepsis = comp_OL_type(num_mothers, i_mat_sepsis, p_sepsis_ol, i_OL_final_mask, rng)

    i_stillbirth = comp_OL_type(num_mothers, i_stillbirth, p_stillbirth_ol, i_OL_final_mask, rng)
    non_stillbirth_mask = (i_OL_final == 1) & (i_stillbirth == 0)
    i_asphyxia = comp_OL_type(num_mothers, i_asphyxia, p_asphyxia_ol, non_stillbirth_mask, rng)
    i_neo_sepsis = comp_OL_type(num_mothers, i_neo_sepsis, p_neo_sepsis_ol, non_stillbirth_mask, rng)

    # 2) **Emergency CS Complications: PPH and maternal sepsis**
    EmCS_mask = (i_mod == "EmCS")
    p_pph_emcs = P["pph_emergency_CS_anemia"][i_anemia_new]
    p_sepsis_emcs = P["mat_sepsis_emergency_CS_anemia"][i_anemia_new]
    i_pph = comp_OL_type(num_mothers, i_pph, p_pph_emcs, EmCS_mask, rng)
    i_mat_sepsis = comp_OL_type(num_mothers, i_mat_sepsis, p_sepsis_emcs, EmCS_mask, rng)

    # 3) **Hypoxia Complications: stillbirths**
    CS_effect = np.ones(num_mothers, dtype = int)
    hypoxia_cs_mask = (i_mod != "SVD")
    CS_effect[hypoxia_cs_mask] = 1 - E["stillbirth_CS"]
    p_stillbirth_hypoxia = P["stillbirth_hypoxia"] * CS_effect
    i_hypoxia_mask = (i_hypoxia == 1)
    i_stillbirth = comp_OL_type(num_mothers, i_stillbirth, p_stillbirth_hypoxia, i_hypoxia_mask, rng)

    # 4) **Elective CS Complications: PPH and maternal sepsis**
    i_elec_CS_mask = (i_elec_CS == 1)
    p_pph_elcs = P["pph_elective_CS_anemia"][i_anemia_new]
    p_sepsis_elcs = P["mat_sepsis_elective_CS_anemia"][i_anemia_new]
    i_pph = comp_OL_type(num_mothers, i_pph, p_pph_elcs, i_elec_CS_mask, rng)
    i_mat_sepsis = comp_OL_type(num_mothers, i_mat_sepsis, p_sepsis_elcs, i_elec_CS_mask, rng)

    # 5) **Other Cases: (SVD|AVD, ~ OL): PPH and maternal sepsis**
    other_mask = (~i_OL_final_mask) & np.isin(i_mod, ["SVD", "AVD"])
    p_pph_other = P["pph_other_anemia"][i_anemia_new]
    p_sepsis_other = P["mat_sepsis_other_anemia"][i_anemia_new]
    i_pph = comp_OL_type(num_mothers, i_pph, p_pph_other, other_mask, rng)
    i_mat_sepsis = comp_OL_type(num_mothers, i_mat_sepsis, p_sepsis_other, other_mask, rng)

    ####----------------------------Emergency Transfer for complications---------------------------------####
    # ---- Step 1: Pre-transfer complications ----
    i_comp_death_bf = ((i_pph == 1) | (i_mat_sepsis == 1) | (i_eclampsia == 1) | (i_ruptured_uterus == 1) | (i_OL_final == 1) | (i_aph == 1)).astype(int)  #complications before transfer
    p_severe_risk = P["severe"][i_highrisk]
    i_pph_severe = comp_severe(num_mothers, i_pph, p_severe_risk, rng)
    i_sepsis_severe = comp_severe(num_mothers, i_mat_sepsis, p_severe_risk, rng)
    i_eclampsia_severe = comp_severe(num_mothers, i_eclampsia, p_severe_risk, rng)
    i_ol_severe = comp_severe(num_mothers, i_OL_final, p_severe_risk, rng)
    i_ruptured_uterus_severe = comp_severe(num_mothers, i_ruptured_uterus, p_severe_risk, rng)
    i_aph_severe = comp_severe(num_mothers, i_aph, p_severe_risk, rng)

    # ---- Step 2: Emergency Transfer ----
    i_severe_bf = ((i_pph_severe == 1) | (i_sepsis_severe == 1) | (i_eclampsia_severe == 1) | (i_ruptured_uterus_severe == 1) | (i_ol_severe == 1) | (i_aph_severe)).astype(int)
    i_notsevere_bf = (i_comp_death_bf == 1) & (i_severe_bf == 0)
    severe_mask = (i_severe_bf == 1)                        # Transfer Condition 1 - severe
    notsevere_mask = (i_notsevere_bf == 1)                  # Transfer Condition 3 - not severe
    preterm_mask = i_preterm & (~i_comp_death_bf)             # Transfer Condition 3 - preterm
    max_capacity = S["Fac_capacity"].astype(int)            # Maximum Facility Capacity

    i_loc_new_v2, i_transfer_actual = emergency_transfer_comps(i_transfer_actual, num_mothers, i_loc_new_v1, max_capacity, severe_mask, 1, P["transfer_rate_severe"], rng)       # severe transfers from l23 to l45
    i_loc_new_v3, i_transfer_actual = emergency_transfer_comps(i_transfer_actual, num_mothers, i_loc_new_v2, max_capacity, severe_mask, 2, P["transfer_rate_severe"], rng)       # severe transfers from l4 to l45
    i_loc_new_v4, i_transfer_actual = emergency_transfer_comps(i_transfer_actual, num_mothers, i_loc_new_v3, max_capacity, preterm_mask, 1, P["transfer_rate_preterm"], rng)     # preterm transfers from l23 to l45
    i_loc_new_final, i_transfer_actual = emergency_transfer_comps(i_transfer_actual, num_mothers, i_loc_new_v4, max_capacity, notsevere_mask, 1, P["transfer_rate_notsevere"], rng) #not severe transfers from l23 to l45

    # ---- Step 3: Preterm-related complications and treatments ----
    preterm_mask2 = (i_preterm == 1)
    p_treat = param["S_preterm_treat"][i_loc_new_final] * P["knowledge"][i_loc_new_final]
    i_T = (rng.random(num_mothers) < p_treat).astype(int)
    p_RDS = P["RDS_T"][i_T, i_jGA]
    p_IVH = P_IVH_vectorized(i_GA, i_T, param)
    p_NEC = P_NEC_vectorized(i_GA, i_T, param)
    p_neo_sepsis = P_Sepsis_vectorized(i_GA, i_T, param)

    i_RDS = preterm_complication(num_mothers, preterm_mask2, i_RDS, p_RDS, rng)
    i_IVH = preterm_complication(num_mothers, preterm_mask2, i_IVH, p_IVH, rng)
    i_NEC = preterm_complication(num_mothers, preterm_mask2, i_NEC, p_NEC, rng)
    i_neo_sepsis = preterm_complication(num_mothers, preterm_mask2, i_neo_sepsis, p_neo_sepsis, rng)

    # ---- Step 4: Single Interventions for reducing postpartum complications ----
    #pph bundle
    i_pph_new, i_pph_severe_new, i_pph_bundle = SI_reduction(num_mothers, i_loc_new_final, i_pph, i_pph_severe, P["pph_bundle"], E["int_pph"], rng)
    #MGSO4
    i_eclampsia_new, i_eclampsia_severe_new, i_MgSO4 = SI_reduction(num_mothers, i_loc_new_final, i_eclampsia, i_eclampsia_severe, P["MgSO4"], E["int_eclampsia"], rng)
    #antibiotics
    i_mat_sepsis_new, i_sepsis_severe_new, i_antibiotics = SI_reduction(num_mothers, i_loc_new_final, i_mat_sepsis, i_sepsis_severe, P["antibiotics"], E["int_sepsis"], rng)

    # if i == 4:
    #     st.text(i_eclampsia_new[20:40])
    #     st.text(np.sum(i_eclampsia_new))

    i_comp_death_new = ((i_pph_new == 1) | (i_mat_sepsis_new == 1) | (i_eclampsia_new == 1) | (i_ruptured_uterus == 1) | (i_OL_final == 1) | (i_aph == 1)).astype(int)
    i_severe_new = ((i_pph_severe_new == 1) | (i_sepsis_severe_new == 1) | (i_eclampsia_severe_new == 1) | (i_ruptured_uterus_severe == 1) | (i_ol_severe == 1) | (i_aph_severe == 1)).astype(int)

    i_unnecessary_cs = ((i_mod == "EmCS") & ~(i_PL_new | i_OL | i_hypoxia)).astype(int)

    #Update outcomes
    M, MC, NC, track = update_outcomes_vectorized(
        M, MC, NC, track, i_loc_new_final, i_jGA, i_mod, i_highrisk,
        i_PL_new, i_OL, i_hypoxia, i_transfer_pred, i_transfer_actual,
        i_iv_iron, i_pph_bundle, i_MgSO4, i_antibiotics, i_preterm, i_anemia_new, i_severe_new, i_pph_severe_new,
        i_eclampsia_new, i_ruptured_uterus, i_aph, i_OL_final, i_pph_new, i_mat_sepsis_new,
        i_comp_death_new, i_stillbirth, i_asphyxia, i_RDS, i_IVH,
        i_NEC, i_neo_sepsis, i_ANC, i, i_loc, i_unnecessary_cs
    )

    individual_outcomes = update_outcomes_vectorized_individual(i_loc_new_v1, i_loc_new_final, i_mod, i_PL,
                                          i_PL_new, i_OL, i_hypoxia, i_transfer_pred, i_transfer_actual,
                                          i_iv_iron, i_oxytocin, i_pph_bundle, i_MgSO4, i_antibiotics, i_preterm, i_severe_new, i_pph_severe_new,
                                          i_eclampsia, i_eclampsia_new, i_ruptured_uterus, i_aph, i_OL_final, i_pph, i_pph_new, i_mat_sepsis, i_mat_sepsis_new,
                                          i_comp_death_new, i_stillbirth, i_asphyxia, i_RDS, i_IVH,
                                          i_NEC, i_neo_sepsis, individual_outcomes,
                                          i_PL_pred, i_OL_pred, i_hypoxia_pred, i_sensors,
                                          i_sepsis_severe_new, i_eclampsia_severe_new, i_ruptured_uterus_severe, i_ol_severe, i_aph_severe, i_loc, i_unnecessary_cs)

    return MC, M, NC, individual_outcomes


def update_outcomes_vectorized(M, MC, NC, track, i_loc_new_final, i_jGA, i_mod, i_highrisk,
                    i_PL_new, i_OL, i_hypoxia, i_transfer_pred, i_transfer_actual,
                    i_iv_iron, i_pph_bundle, i_MgSO4, i_antibiotics, i_preterm, i_anemia_new, i_severe_new, i_pph_severe_new,
                    i_eclampsia_new, i_ruptured_uterus, i_aph, i_OL_final, i_pph_new, i_mat_sepsis_new,
                    i_comp_death_new, i_stillbirth, i_asphyxia, i_RDS, i_IVH,
                    i_NEC, i_neo_sepsis, i_ANC, i, i_loc, i_unnecessary_cs):
    # Batch updates for M (Delivery and maternal outcomes)
    np.add.at(M["GA"], (i_loc_new_final, i_jGA), 1)
    np.add.at(M["CS"], i_loc_new_final, np.isin(i_mod, ["EmCS", "ELCS"]))
    np.add.at(M["Emergency_CS"], i_loc_new_final, i_mod == "EmCS")
    np.add.at(M["CS_unnessary"], i_loc_new_final, i_unnecessary_cs)
    np.add.at(M["Elective_CS_risk"], i_highrisk, i_mod == "ELCS")
    np.add.at(M["Elective_CS"], i_loc_new_final, i_mod == "ELCS")
    np.add.at(M["AVD"], i_loc_new_final, i_mod == "AVD")
    np.add.at(M["SVD"], i_loc_new_final, i_mod == "SVD")
    np.add.at(M["ER_trans_pred"], i_loc_new_final, i_transfer_pred)
    np.add.at(M["ER_trans_actual"], i_loc_new_final, i_transfer_actual)
    np.add.at(M["iv_iron"], i_loc_new_final, i_iv_iron)
    np.add.at(M["pph_bundle"], i_loc_new_final, i_pph_bundle)
    np.add.at(M["MgSO4"], i_loc_new_final, i_MgSO4)
    np.add.at(M["antibiotics"], i_loc_new_final, i_antibiotics)
    np.add.at(M["PT"], i_loc_new_final, i_preterm)

    # Fully vectorized batch updates for MC (Maternal complications)
    np.add.at(MC["anemia"], i_loc_new_final, i_anemia_new)
    np.add.at(MC["severe_comps"], i_loc_new_final, i_severe_new)
    np.add.at(MC["pph_severe"], i_loc_new_final, i_pph_severe_new)
    np.add.at(MC["eclampsia"], i_loc_new_final, i_eclampsia_new)
    np.add.at(MC["ruptured_uterus"], i_loc_new_final, i_ruptured_uterus)
    np.add.at(MC["aph"], i_loc_new_final, i_aph)
    np.add.at(MC["PL"], i_loc_new_final, i_PL_new)
    np.add.at(MC["hypoxia"], i_loc_new_final, i_hypoxia)
    np.add.at(MC["OL"], i_loc_new_final, i_OL_final)
    np.add.at(MC["pph"], i_loc_new_final, i_pph_new)
    np.add.at(MC["mat_sepsis"], i_loc_new_final, i_mat_sepsis_new)
    np.add.at(MC["comps_death"], i_loc_new_final, i_comp_death_new)

    # Fully vectorized batch updates for NC (Neonatal complications)
    np.add.at(NC["stillbirth"], i_loc_new_final, i_stillbirth)
    np.add.at(NC["asphyxia"], i_loc_new_final, i_asphyxia)
    np.add.at(NC["RDS"], i_loc_new_final, i_RDS)
    np.add.at(NC["IVH"], i_loc_new_final, i_IVH)
    np.add.at(NC["NEC"], i_loc_new_final, i_NEC)
    np.add.at(NC["neo_sepsis"], i_loc_new_final, i_neo_sepsis)

    # Fully vectorized updates for Birth and Risk Tracking
    np.add.at(M["LB_L_initial"], i_loc, 1)
    np.add.at(M["LB_L_new"], i_loc_new_final, 1)
    np.add.at(M["ANC_L_new"], i_loc_new_final, i_ANC)
    np.add.at(M["Highrisk_L_new"], i_loc_new_final, i_highrisk)

    # Direct assignment for track tracking (remains unchanged)
    track["LB_Track"][i, :] = M["LB_L_new"]
    track["ANC_Track"][i, :] = M["ANC_L_new"]
    track["HighRisk_Track"][i, :] = M["Highrisk_L_new"]

    return M, MC, NC, track

def update_outcomes_vectorized_individual(i_loc_new_v1, i_loc_new_final, i_mod, i_PL,
                    i_PL_new, i_OL, i_hypoxia, i_transfer_pred, i_transfer_actual,
                    i_iv_iron, i_oxytocin, i_pph_bundle, i_MgSO4, i_antibiotics, i_preterm, i_severe_new, i_pph_severe_new,
                    i_eclampsia, i_eclampsia_new, i_ruptured_uterus, i_aph, i_OL_final, i_pph, i_pph_new, i_mat_sepsis, i_mat_sepsis_new,
                    i_comp_death_new, i_stillbirth, i_asphyxia, i_RDS, i_IVH,
                    i_NEC, i_neo_sepsis, individual_outcomes,
                    i_PL_pred, i_OL_pred, i_hypoxia_pred, i_sensors,
                    i_sepsis_severe_new, i_eclampsia_severe_new, i_ruptured_uterus_severe, i_ol_severe, i_aph_severe, i_loc, i_unnecessary_cs):
    individual_outcomes["i_loc"] = i_loc.astype(int)
    individual_outcomes["i_loc_new_v1"] = i_loc_new_v1.astype(int)
    individual_outcomes["i_loc_new_v2"] = i_loc_new_final.astype(int)
    individual_outcomes["i_mod"] = i_mod.astype(str)
    individual_outcomes["i_PL"] = i_PL.astype(int)
    individual_outcomes["i_PL_new"] = i_PL_new.astype(int)
    individual_outcomes["i_OL"] = i_OL.astype(int)
    individual_outcomes["i_OL_final"] = i_OL_final.astype(int)
    individual_outcomes["i_hypoxia"] = i_hypoxia.astype(int)
    individual_outcomes["i_transfer_pred"] = i_transfer_pred.astype(int)
    individual_outcomes["i_transfer_actual"] = i_transfer_actual.astype(int)
    individual_outcomes["i_iv_iron"] = i_iv_iron.astype(int)
    individual_outcomes["i_oxytocin"] = i_oxytocin.astype(int)
    individual_outcomes["i_pph_bundle"] = i_pph_bundle.astype(int)
    individual_outcomes["i_MgSO4"] = i_MgSO4.astype(int)
    individual_outcomes["i_antibiotics"] = i_antibiotics.astype(int)
    individual_outcomes["i_preterm"] = i_preterm.astype(int)
    individual_outcomes["i_severe_new"] = i_severe_new.astype(int)
    individual_outcomes["i_pph_severe_new"] = i_pph_severe_new.astype(int)
    individual_outcomes["i_eclampsia"] = i_eclampsia.astype(int)
    individual_outcomes["i_eclampsia_new"] = i_eclampsia_new.astype(int)
    individual_outcomes["i_ruptured_uterus"] = i_ruptured_uterus.astype(int)
    individual_outcomes["i_aph"] = i_aph.astype(int)
    individual_outcomes["i_pph"] = i_pph.astype(int)
    individual_outcomes["i_pph_new"] = i_pph_new.astype(int)
    individual_outcomes["i_mat_sepsis"] = i_mat_sepsis.astype(int)
    individual_outcomes["i_mat_sepsis_new"] = i_mat_sepsis_new.astype(int)
    individual_outcomes["i_comp_death_new"] = i_comp_death_new.astype(int)
    individual_outcomes["i_stillbirth"] = i_stillbirth.astype(int)
    individual_outcomes["i_asphyxia"] = i_asphyxia.astype(int)
    individual_outcomes["i_RDS"] = i_RDS.astype(int)
    individual_outcomes["i_IVH"] = i_IVH.astype(int)
    individual_outcomes["i_NEC"] = i_NEC.astype(int)
    individual_outcomes["i_neo_sepsis"] = i_neo_sepsis.astype(int)
    individual_outcomes["i_PL_pred"] = i_PL_pred.astype(int)
    individual_outcomes["i_OL_pred"] = i_OL_pred.astype(int)
    individual_outcomes["i_hypoxia_pred"] = i_hypoxia_pred.astype(int)
    individual_outcomes["i_sensors"] = i_sensors.astype(int)
    individual_outcomes["i_sepsis_severe"] = i_sepsis_severe_new.astype(int)
    individual_outcomes["i_eclampsia_severe"] = i_eclampsia_severe_new.astype(int)
    individual_outcomes["i_ruptured_uterus_severe"] = i_ruptured_uterus_severe.astype(int)
    individual_outcomes["i_ol_severe"] = i_ol_severe.astype(int)
    individual_outcomes["i_aph_severe"] = i_aph_severe.astype(int)
    individual_outcomes["i_unnecessary_cs"] = i_unnecessary_cs.astype(int)

    return individual_outcomes

# def intrapartum_effect(track, flags, param, i, planned_CSs, GAs, rng):
#
#     # Initialize parameters
#     P, n, E, S, MC, NC, M = initialize_intra_params(track, flags, param, i, planned_CSs, GAs)
#     #variables for debug
#     n_anc = 0
#     n_risk = 0
#     n_preterm = 0
#     n_FT = 0
#     n_intra_monitor = 0
#     n_PL_origin = 0
#     n_OL_origin = 0
#     n_hypoxia_origin = 0
#     n_PL_pred = 0
#     n_OL_pred = 0
#     n_hypoxia_pred = 0
#     sen_hypoxia_all = 0
#     spec_hypoxia_all = 0
#     n_PL_treated = 0
#     n_EmCS = 0
#     n_pph_severe = 0
#     n_sepsis_severe = 0
#     n_eclampsia_severe = 0
#     n_other_severe = 0
#     n_ol_severe = 0
#
#
#     # Begin simulations
#     for k_L in range(3, -1, -1):            #for each facility level - start from higher level facilities to occupy c-section capacity
#         for k_LB in range(n["LB_L"][k_L]):
#             #Initialize variables
#             (i_PL, i_OL, i_hypoxia, i_eclampsia, i_ruptured_uterus,
#              i_severe, i_comp_death, i_elective_CS, i_intra_monitor, i_OL_final,
#              i_pph, i_mat_sepsis, i_stillbirth, i_asphyxia, i_neo_sepsis,
#              i_anemia, i_RDS, i_IVH, i_NEC, i_transfer_pred,
#              i_transfer_actual) = [0] * 21
#
#             i_loc_new = k_L
#
#             # Mother's characteristics
#             i_ANC = 1 if rng.random() < P["ANC_L"][k_L] else 0                                  # ANC status
#             i_highrisk = 1 if rng.random() < P["highrisk"][k_L] else 0                          # Whether high risk
#             i_jGA = np.searchsorted(np.cumsum(P["GA"][k_L]), rng.random())                      # % actual index of GA
#             i_GA = n['GA_sequence'][i_jGA]                                                                        # % actual GA
#             i_preterm = 1 if i_GA < 37 else 0
#             i_FT = 1 if i_GA >= 37 else 0
#
#             #debug
#             n_anc += i_ANC
#             n_risk += i_highrisk
#             n_preterm += i_preterm
#             n_FT += i_FT
#
#             #check anemia and intervention if available
#             i_anemia = 1 if rng.random() < param['p_anemia_anc'][i_ANC] else 0                        # Whether anemia
#             i_pph_bundle = 0
#             i_iv_iron = 0
#             if i_ANC and i_anemia:  # only mothers with ANC can get intervention 2
#                 i_iv_iron = 1 if rng.random() < P["iv_iron"] else 0
#                 if i_iv_iron == 1 and rng.random() < (1 - E["int_anemia"]):
#                     i_anemia = 0
#
#             # Complications not related to intrapartum monitoring - can be preterm or full-term
#             if i_highrisk:                                                                          # Whether eclampsia
#                 i_eclampsia = rng.binomial(1, P["eclampsia_highrisk_anemia"][i_anemia])
#                 i_ruptured_uterus = rng.binomial(1, P["ruptured_uterus_highrisk"])
#             else:
#                 i_eclampsia = rng.binomial(1, P["eclampsia_lowrisk_anemia"][i_anemia])
#                 i_ruptured_uterus = rng.binomial(1, P["ruptured_uterus_lowrisk"])
#
#             if k_L > 1:
#                 i_elective_CS = rng.binomial(1, P["Elective_CS"][i_highrisk])             # Check whether the mother has planned c-section
#
#             i_intra_monitor = 1 if (i_FT and not i_elective_CS) else 0                             # only mother is full-term and not planned c-section will be monitored
#             i_mod = "ELCS" if i_elective_CS else "SVD"                                             # Initial delivery mode
#
#             n_intra_monitor += i_intra_monitor
#             ####----------------------------Intrapartum monitoring for full-term births---------------------------------####
#             if i_intra_monitor:
#                 #0)Prolonged labor rate based on GA
#                 P_PL = P_Prolonged(i_GA)
#                 #1)Obstructed labor and hypoxia based on risk status
#                 if i_highrisk:
#                     P_OL      = P["OL_highrisk"]
#                     P_hypoxia = P["hypoxia_highrisk"]
#                 else:
#                     P_OL = P["OL_lowrisk"]
#                     P_hypoxia = P["hypoxia_lowrisk"]
#
#                 # whether develop complications based on high or low risk - updated using random choice
#                 if rng.random() < P_PL:
#                     i_PL = 1
#                 elif rng.random() < P_OL:
#                     i_OL = 1
#                 elif rng.random() < P_hypoxia:
#                     i_hypoxia = 1
#
#                 n_OL_origin += i_OL
#                 n_PL_origin += i_PL
#                 n_hypoxia_origin += i_hypoxia
#
#                 #2) Monitoring
#                 sen_PL, spec_PL, sen_OL, spec_OL, sen_hypoxia, spec_hypoxia = sensors_accuracy(S, E, i_highrisk, k_L)
#
#                 # 2) calculate TP, FP, TN, FN - only facilities
#                 if k_L > 0:
#                     if i_PL == 1:
#                         i_PL_pred = 1 if rng.random() < sen_PL else 0
#                     else:
#                         i_PL_pred = 0 if rng.random() < spec_PL else 1
#
#                     if i_OL == 1:
#                         i_OL_pred = 1 if rng.random() < sen_OL  else 0
#                     else:
#                         i_OL_pred = 0 if rng.random() < spec_OL else 1
#
#                     if i_hypoxia == 1:
#                         i_hypoxia_pred = 1 if rng.random() < sen_hypoxia else 0
#                     else:
#                         i_hypoxia_pred = 0 if rng.random() < spec_hypoxia else 1
#
#                     n_PL_pred += i_PL_pred
#                     n_OL_pred += i_OL_pred
#                     n_hypoxia_pred += i_hypoxia_pred
#
#                     # 3) Single interventions to reduce prolonged labor
#                     if i_PL == 1 and i_PL_pred == 1:
#                         if rng.random() < E["oxytocin"] * P["oxytocin"][k_L]:
#                             i_PL = 0
#                             i_PL_pred = 0
#                             n_PL_treated += 1
#
#                     #4) Initial delivery mode
#                     if i_PL_pred or i_OL_pred or i_hypoxia_pred:
#                         i_mod = rng.choice(["EmCS", "AVD"], p = param["CS_AVD_ratio"])
#                     else:
#                         i_mod = "SVD"
#
#                     if i_mod == "EmCS":
#                         if rng.binomial(1, S["CS_capacity"][k_L]):
#                             i_mod = "EmCS"
#                             n_EmCS += 1
#                         else:
#                             i_mod = "SVD"
#
#                     # 5) Emergency transfer for predicted complications
#                     if i_mod == "SVD" and k_L == 1 and (i_PL_pred or i_OL_pred or i_hypoxia_pred):
#                         # Check the facility capacity to see any maternal beds available
#                         if M["LB_L_new"][2] + M["LB_L_new"][3] < S["Fac_capacity"]:
#                             if rng.binomial(1, S["CS_capacity"][2]):
#                                 i_mod = "EmCS"
#                                 i_transfer_pred = 1
#                                 i_loc_new = 2
#                             else:
#                                 if rng.binomial(1, S["CS_capacity"][3]):
#                                     i_mod = "EmCS"
#                                     i_transfer_pred = 1
#                                     i_loc_new = 3
#                                 else:
#                                     i_mod = "SVD"
#                                     i_loc_new = 1
#                                     i_transfer_pred = 0
#                         else:
#                             i_mod = "SVD"
#                             i_transfer_pred = 0
#                             i_loc_new = 1
#                     else:
#                         i_transfer_pred = 0
#                         i_loc_new = k_L
#                 else:
#                     i_mod = "SVD"
#                     i_transfer_pred = 0
#                     i_loc_new = k_L
#
#                 # 6) OL after emergency transfer
#                 i_OL_final = 1 if ((i_PL == 1 and i_mod == "SVD" and (rng.random() < P["OL"][1])) or (i_OL == 1 and i_mod == "SVD")) else 0
#
#                 # 7) Record final complications after delivery mode
#                 if i_OL_final == 1:                                                 #OL induced complications - pathway D and E
#                     i_pph = rng.binomial(1, P["pph_OL_anemia"][i_anemia])
#                     i_mat_sepsis = rng.binomial(1, P["mat_sepsis_OL_anemia"][i_anemia])
#                     i_stillbirth = rng.binomial(1, P["stillbirth_OL"])
#                     if not i_stillbirth:
#                         i_asphyxia = rng.binomial(1, P["asphyxia_OL"])
#                         i_neo_sepsis = rng.binomial(1, P["neo_sepsis_OL"])
#                 elif i_mod == "EmCS":                                               # Emergency CS induced complications - pathway C
#                         i_pph = rng.binomial(1, P["pph_emergency_CS_anemia"][i_anemia])
#                         i_mat_sepsis = rng.binomial(1, P["mat_sepsis_emergency_CS_anemia"][i_anemia])
#                 else:                                                               # PPH and Maternal Sepsis by SVD and AVD
#                     i_pph = rng.binomial(1, P["pph_other_anemia"][i_anemia])
#                     i_mat_sepsis = rng.binomial(1, P["mat_sepsis_other_anemia"][i_anemia])
#
#                 if i_hypoxia:                                                       #Hypoxia induced stillbirths
#                     CS_effect = 1 - E["stillbirth_CS"] if i_mod != "SVD" else 1     #Both CS and AVD can reduce stillbirths
#                     i_stillbirth = rng.binomial(1, P["stillbirth_hypoxia"] * CS_effect)
#             else:
#                 if i_elective_CS:
#                     i_pph = rng.binomial(1, P["pph_elective_CS_anemia"][i_anemia])
#                     i_mat_sepsis = rng.binomial(1, P["mat_sepsis_elective_CS_anemia"][i_anemia])
#                 elif i_mod == "SVD":
#                     i_pph = rng.binomial(1, P["pph_other_anemia"][i_anemia])
#                     i_mat_sepsis = rng.binomial(1, P["mat_sepsis_other_anemia"][i_anemia])
#
#             ####----------------------------Emergency Transfer for complications---------------------------------####
#             # ---- Step 1: Pre-transfer complications ----
#             i_comp_death = i_pph or i_mat_sepsis or i_eclampsia or i_ruptured_uterus or i_OL_final
#             i_pph_severe = 1 if (i_pph == 1 and rng.binomial(1, P["severe"])[i_highrisk] == 1) else 0
#             i_sepsis_severe = 1 if (i_mat_sepsis == 1 and rng.binomial(1, P["severe"][i_highrisk]) == 1) else 0
#             i_eclampsia_severe = 1 if (i_eclampsia == 1 and rng.binomial(1, P["severe"][i_highrisk]) == 1) else 0
#             i_ol_severe = 1 if (i_OL_final == 1 and rng.binomial(1, P["severe"][i_highrisk]) == 1) else 0
#             i_ruptured_uterus_severe = 1 if (i_ruptured_uterus == 1 and rng.binomial(1, P["severe"][i_highrisk]) == 1) else 0
#             if i_pph_severe or i_sepsis_severe or i_eclampsia_severe or i_ruptured_uterus_severe or i_ol_severe:
#                 i_severe = 1
#
#             # ---- Step 2: Emergency Transfer ----
#             if i_comp_death or i_preterm:
#                 if M["LB_L_new"][2] + M["LB_L_new"][3] < S["Fac_capacity"]:
#                     if i_severe and i_comp_death:
#                         i_loc_dest = rng.choice([0, 1, 2, 3, 4], p=P["transfer_rate_severe"][i_loc_new])
#                     elif not i_severe and i_comp_death:
#                         i_loc_dest = rng.choice([0, 1, 2, 3, 4], p=P["transfer_rate_notsevere"][i_loc_new])
#                     elif i_preterm:
#                         i_loc_dest = rng.choice([0, 1, 2, 3, 4], p=P["transfer_rate_preterm"][i_loc_new])
#
#                     i_transfer_actual = 1 if (i_loc_dest != 0 and i_loc_dest > i_loc_new) else 0
#                     i_loc_new = i_loc_new if i_transfer_actual == 0 else (i_loc_dest - 1)
#
#             # ---- Step 3: Preterm-related complications and treatments ----
#             if i_preterm:
#                 i_T = rng.binomial(1, param["S_preterm_treat"][i_loc_new])
#                 i_RDS = rng.binomial(1, P["RDS_T"][i_T][i_jGA])
#                 i_IVH = rng.random() < P_IVH(i_GA, i_T, param)
#                 i_NEC = rng.random() < P_NEC(i_GA, i_T, param)
#                 i_neo_sepsis = rng.random() < P_Sepsis(i_GA, i_T, param)
#
#             # ---- Step 4: Single Interventions for reducing postpartum complications ----
#             if i_pph:
#                 i_pph_bundle = 1 if rng.random() < P["pph_bundle"][i_loc_new] else 0
#                 if i_pph_bundle == 1 and rng.random() < (1 - E["int_pph"]):
#                     i_pph = 0
#                     i_pph_severe = 0
#
#             i_comp_death_new = (i_pph or i_mat_sepsis or i_eclampsia or i_ruptured_uterus or i_OL_final)
#             i_severe_new = (i_pph_severe or i_sepsis_severe or i_eclampsia_severe or i_ruptured_uterus_severe or i_ol_severe)
#
#             n_pph_severe += i_pph_severe
#             n_sepsis_severe += i_sepsis_severe
#             n_eclampsia_severe += i_eclampsia_severe
#             n_other_severe += i_ruptured_uterus_severe
#             n_ol_severe += i_ol_severe
#
#
#             #Update outcomes
#             M, MC, NC, track = update_outcomes(
#                 M, MC, NC, track, i_loc_new, i_jGA, i_mod, i_highrisk,
#                 i_PL, i_OL, i_hypoxia, i_transfer_pred, i_transfer_actual,
#                 i_iv_iron, i_pph_bundle, i_preterm, i_anemia, i_severe_new,
#                 i_eclampsia, i_ruptured_uterus, i_OL_final, i_pph, i_mat_sepsis,
#                 i_comp_death_new, i_stillbirth, i_asphyxia, i_RDS, i_IVH,
#                 i_NEC, i_neo_sepsis, i_ANC, i
#             )
#
#     #Debug
#     num_mothers = np.sum(M["LB_L_new"])
#     # st.text(f'n_intra_monitor_old: {n_intra_monitor}')
#     # st.text(f'n_PL_old: {n_PL_origin}')
#     # st.text(f'n_OL_old: {n_OL_origin}')
#     # st.text(f'n_hypoxia_old: {n_hypoxia_origin}')
#     # st.text(f'n_PL_pred_old: {n_PL_pred}')
#     # st.text(f'n_OL_pred_old: {n_OL_pred}')
#     # st.text(f'n_hypoxia_pred_old: {n_hypoxia_pred}')
#     # st.text(f'n_PL_treated_old: {n_PL_treated}')
#     # st.text(f'n_EmCS_old: {n_EmCS}')
#     # st.text(f'p_EmCS_old: {n_EmCS / num_mothers}')
#     # p_severe_l45 = (MC["severe_comps"][2] + MC["severe_comps"][3]) / (M["LB_L_new"][2] + M["LB_L_new"][3])
#     # st.text(f'p_severe_old_l45: {p_severe_l45}')
#     # p_severe_all = np.sum(MC["severe_comps"]) / np.sum(M["LB_L_new"])
#     # st.text(f'p_severe_old_all: {p_severe_all}')
#
#     # st.text(f'n_pph_severe_old: {n_pph_severe}')
#     # st.text(f'n_sepsis_severe_old: {n_sepsis_severe}')
#     # st.text(f'n_eclampsia_severe_old: {n_eclampsia_severe}')
#     # st.text(f'n_other_severe_old: {n_other_severe}')
#     # st.text(f'n_ol_severe_old: {n_ol_severe}')
#     return MC, M, NC

# def update_outcomes(M, MC, NC, track, i_loc_new, i_jGA, i_mod, i_highrisk,
#                     i_PL, i_OL, i_hypoxia, i_transfer_pred, i_transfer_actual,
#                     i_iv_iron, i_pph_bundle, i_preterm, i_anemia, i_severe_new,
#                     i_eclampsia, i_ruptured_uterus, i_OL_final, i_pph, i_mat_sepsis,
#                     i_comp_death_new, i_stillbirth, i_asphyxia, i_RDS, i_IVH,
#                     i_NEC, i_neo_sepsis, i_ANC, i):
#
#     # Delivery and maternal outcomes
#     M["GA"][i_loc_new, i_jGA] += 1
#     M["CS"][i_loc_new] += i_mod in ["EmCS", "ELCS"]
#     M["Emergency_CS"][i_loc_new] += (i_mod == "EmCS")
#     M["CS_unnessary"][i_loc_new] += (i_mod == "EmCS") and not (i_PL or i_OL or i_hypoxia)
#     M["Elective_CS_risk"][i_highrisk] += i_mod == "ELCS"
#     M["Elective_CS"][i_loc_new] += i_mod == "ELCS"
#     M["AVD"][i_loc_new] += i_mod == "AVD"
#     M["SVD"][i_loc_new] += i_mod == "SVD"
#     M["ER_trans_pred"][i_loc_new] += i_transfer_pred
#     M["ER_trans_actual"][i_loc_new] += i_transfer_actual
#     M["iv_iron"][i_loc_new] += i_iv_iron
#     M["pph_bundle"][i_loc_new] += i_pph_bundle
#     M["PT"][i_loc_new] += i_preterm
#
#     # Maternal complications
#     MC_updates = {
#         "anemia": i_anemia,
#         "severe_comps": i_severe_new,
#         "eclampsia": i_eclampsia,
#         "ruptured_uterus": i_ruptured_uterus,
#         "PL": i_PL,
#         "hypoxia": i_hypoxia,
#         "OL": i_OL_final,
#         "pph": i_pph,
#         "mat_sepsis": i_mat_sepsis,
#         "comps_death": i_comp_death_new
#     }
#     for key, value in MC_updates.items():
#         MC[key][i_loc_new] += value
#
#     # Neonatal complications
#     NC_updates = {
#         "stillbirth": i_stillbirth,
#         "asphyxia": i_asphyxia,
#         "RDS": i_RDS,
#         "IVH": i_IVH,
#         "NEC": i_NEC,
#         "neo_sepsis": i_neo_sepsis
#     }
#     for key, value in NC_updates.items():
#         NC[key][i_loc_new] += value
#
#     # Birth and risk tracking
#     M["LB_L_new"][i_loc_new] += 1
#     M["ANC_L_new"][i_loc_new] += i_ANC
#     M["Highrisk_L_new"][i_loc_new] += i_highrisk
#
#     # Update tracking in track
#     track["LB_Track"][i, :] = M["LB_L_new"]
#     track["ANC_Track"][i, :] = M["ANC_L_new"]
#     track["HighRisk_Track"][i, :] = M["Highrisk_L_new"]
#
#     return M, MC, NC, track
