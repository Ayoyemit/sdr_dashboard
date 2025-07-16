import random
import numpy as np
import math
import streamlit as st
import pandas as pd
from global_func import risk_stratification, move_function, generate_negative_experience_heard

def f_LB_effect_vectorized(param, i, track, flags, int_period, rng):
    LB_base = track['LB_Track'][0]
    #ANC phase - affect LB
    individual_outcomes, negative_experience_heard, CHV_IDs, CHV_negative_experience, CHV_memory_age = f_ANC_LB_effect_vectorized(track, LB_base, param, flags, i, int_period, rng)

    #SDR intervention - shifting of live births to L4/5
    individual_outcomes = shifting_live_births_vectorized(individual_outcomes, param, i, track, flags, int_period, rng, negative_experience_heard, CHV_IDs, CHV_negative_experience, CHV_memory_age)

    # Initialize counters as NumPy arrays (avoid dictionaries)
    n_LB_new = np.zeros(4, dtype=int)
    n_ANC_new = np.zeros(4, dtype=int)
    n_highrisk_new = np.zeros(4, dtype=int)
    n_free_referrals = np.zeros(2, dtype=int)
    n_self_referrals = np.zeros(2, dtype=int)

    #Extract individual outcomes
    i_loc = individual_outcomes['i_loc'].values
    i_risk = individual_outcomes['i_risk'].values
    i_ANC = individual_outcomes['i_ANC'].values
    i_free_referral = individual_outcomes['i_free_referral'].values
    i_self_referral = individual_outcomes['i_self_referral'].values
    i_class = individual_outcomes['i_class'].values

    #Update counters
    np.add.at(n_LB_new, i_loc, 1)
    np.add.at(n_highrisk_new, i_loc, i_risk)
    np.add.at(n_ANC_new, i_loc, i_ANC)
    np.add.at(n_free_referrals, i_class, i_free_referral)
    np.add.at(n_self_referrals, i_class, i_self_referral)

    #update whole county outcomes at time i
    track['LB_Track'][i] = n_LB_new
    track['HighRisk_Track'][i] = n_highrisk_new
    track['ANC_Track'][i] = n_ANC_new

    # st.text(track['LB_Track'][i] / np.sum(track['LB_Track'][i]))

    return track, n_free_referrals, n_self_referrals, individual_outcomes

#Optimzed version
def f_ANC_LB_effect_vectorized(track, LB_base, param, flags, i, int_period, rng):
    ##-------------------Parameter initialization-------------------##
    Capacity = track['Facility_Capacity_Track'][i, 0]
    E_Preterm_LMP = np.zeros(3)
    E_Preterm_LMP[0], E_Preterm_LMP[1] = param['E_Preterm_LMP'][0], param['E_Preterm_LMP'][1]
    E_Preterm_LMP[2] = 1 - (E_Preterm_LMP[0] + E_Preterm_LMP[1])
    E_Postterm_LMP = np.zeros(3)
    E_Postterm_LMP[0], E_Postterm_LMP[1] = param['E_Postterm_LMP'][0], param['E_Postterm_LMP'][1]
    E_Postterm_LMP[2] = 1 - (E_Postterm_LMP[0] + E_Postterm_LMP[1])
    num_mothers = np.sum(LB_base.astype(int))

    ##-------------------Intervention Set Up----------------------##
    flag_ANC = flags["flag_ANC"]
    flag_POCUS = flags["flag_us"]

    # ANC intervention
    P_ANC_base = param['p_ANC_base']
    P_ANC_target = param["HSS"]["P_ANC"]
    if flag_ANC:
        P_ANC = P_ANC_base + (P_ANC_target - P_ANC_base) / (int_period - 1) * i if i < int_period else P_ANC_target
    else:
        P_ANC = P_ANC_base

    # POCUS intervention
    i_pocus = np.zeros(num_mothers, dtype=int)
    if flag_POCUS:
        sen_risk = param['E']["sens_us"]
        spec_risk = param['E']["spec_us"]
    else:
        sen_risk = param["sen_risk_trad"]
        spec_risk = param["spec_risk_trad"]

    if not flag_POCUS:
        p_elec_CS_highrisk = param["p_elec_CS|highrisk"]                  # probability of elective CS given high risk
    else:
        p_elec_CS_highrisk = param["p_elec_CS|highrisk_us"]

    ##-------------------Mothers' Initial Conditions----------------------##
    i_class = (rng.random(num_mothers) < param["class"]).astype(int)       # 1 = high SES, 0 = low SES
    i_risk = (rng.random(num_mothers) < param["p_highrisk"]).astype(int)            # 1 = high risk, 0 = low risk
    i_ANC = (rng.random(num_mothers) < P_ANC).astype(int)                  # 1 = received ANC, 0 = no ANC

    ##-------------------Gestational Age Assignment - based on ANC status----------------------###
    GA_anc_cumsum = np.cumsum(param["GA_anc"])
    GA_noanc_cumsum = np.cumsum(param["GA_noanc"])
    rand_vals = rng.random(num_mothers)
    i_jGA = np.zeros(num_mothers, dtype=int)
    i_jGA[i_ANC == 1] = np.searchsorted(GA_anc_cumsum, rand_vals[i_ANC == 1])
    i_jGA[i_ANC == 0] = np.searchsorted(GA_noanc_cumsum, rand_vals[i_ANC == 0])
    i_GA = param['GA_sequence'][i_jGA]
    i_term_status = np.select([i_GA < 37, i_GA >= 43], [0, 2], default=1) #preterm atterm or postterm

    ##-------------------Risk Stratification in ANC----------------------##
    i_risk_pred = risk_stratification(i_risk, i_ANC, num_mothers, sen_risk, spec_risk, rng)

    ##-------------------Gestational Age Estimation in ANC----------------------##
    # Pre-generate all randomness - ensure both scenarios consume the same amount of seeds
    ga_noise = rng.normal(0, 1, size=num_mothers)  # always draw this
    rand_preterm = rng.random(num_mothers)  # always draw this
    rand_postterm = rng.random(num_mothers)  # always draw this
    if flag_POCUS:
        i_GA_approx = i_GA + param["E_GA_US"][0] + param["E_GA_US"][1] * ga_noise
        i_preterm_pred = (i_GA_approx < 37) & (i_ANC == 1)
        i_postterm_pred = (i_GA_approx >= 43) & (i_ANC == 1)
        i_pocus[i_ANC == 1] = 1
    else:
        i_preterm_pred = (rand_preterm < E_Preterm_LMP[i_term_status]) & (i_ANC == 1)
        i_postterm_pred = (rand_postterm < E_Postterm_LMP[i_term_status]) & (i_ANC == 1)

    # st.text(param["HSS"]['CHV_memory'])

    ##-------------------Delivery Location Selection----------------------##
    negative_experience_heard, CHV_IDs, CHV_negative_experience, CHV_memory_age = generate_negative_experience_heard(
        rng=rng,
        num_mothers=num_mothers,
        n_CHV=param['n_CHV'],
        mothers_per_CHV=param['mothers_per_CHV_permonth'],
        track=track,
        i=i,
        tau_decay=param["HSS"]['tau_decay'],
        p_CHV_soften_spread=param['p_CHV_soften_spread'],
        memory_model=param["HSS"]['CHV_memory']
    )

    P_home_noANC = param["home_noANC"]
    P_L45_noANC = (1 - P_home_noANC) * param["l45_fac"]
    P_L23_noANC = 1 - P_home_noANC - P_L45_noANC
    P_home_lowrisk = param["home_lowrisk"]
    P_close_to_L23 = param["close_to_L23"]
    P_close_to_L45 = 1 - P_close_to_L23
    P_L23_lowrisk = (1 - P_home_lowrisk) * P_close_to_L23
    P_L45_lowrisk = (1 - P_home_lowrisk) * P_close_to_L45
    P_L23_highrisk = param["L23_highrisk"]
    P_L45_highrisk = 1 - P_L23_highrisk
    prob_matrix_noANC = np.array([P_home_noANC, P_L23_noANC, P_L45_noANC])
    prob_matrix_lowrisk = np.array([P_home_lowrisk, P_L23_lowrisk, P_L45_lowrisk])
    prob_matrix_highrisk = np.array([0, P_L23_highrisk, P_L45_highrisk])

    def adjust_probabilities(prob_matrix, RR_l45):
        """Internal function to adjust a probability matrix by Risk Ratio for L4/5"""
        p_home = prob_matrix[0]
        p_l23 = prob_matrix[1]
        p_l45 = prob_matrix[2]

        # Reduce L4/5 probability
        p_l45_new = p_l45 * RR_l45
        loss = p_l45 - p_l45_new
        redistribution_factor = p_home + p_l23
        p_home_new = p_home + loss * (p_home / redistribution_factor)
        p_l23_new = p_l23 + loss * (p_l23 / redistribution_factor)

        adjusted_matrix = np.array([p_home_new, p_l23_new, p_l45_new])
        return adjusted_matrix / adjusted_matrix.sum()

    RR_l45_poorQOC = param['RR_l45_poorQOC']

    # Adjusted probability matrices
    prob_matrix_noANC_adj = adjust_probabilities(prob_matrix_noANC, RR_l45_poorQOC)
    prob_matrix_lowrisk_adj = adjust_probabilities(prob_matrix_lowrisk, RR_l45_poorQOC)
    prob_matrix_highrisk_adj = adjust_probabilities(prob_matrix_highrisk, RR_l45_poorQOC)

    #define the masks for mothers with different ANC and prediction status
    pred_highrisk_mask = ((i_risk_pred == 1) | (i_preterm_pred == 1) | (i_postterm_pred == 1)).astype(bool)
    noanc_mask = (i_ANC == 0).astype(bool)
    anc_highrisk_mask = ((i_ANC == 1) & (pred_highrisk_mask)).astype(bool)
    anc_lowrisk_mask = ((i_ANC == 1) & (~pred_highrisk_mask)).astype(bool)

    # Define experience masks
    positive_mask = (negative_experience_heard == 0)
    negative_mask = (negative_experience_heard == 1)

    # Initialize
    i_loc = np.zeros(num_mothers, dtype=int)

    # No ANC
    i_loc_noanc_pos = rng.choice(3, p=prob_matrix_noANC, size=num_mothers)
    i_loc_noanc_neg = rng.choice(3, p=prob_matrix_noANC_adj, size=num_mothers)

    # ANC Lowrisk
    i_loc_anc_lowrisk_pos = rng.choice(3, p=prob_matrix_lowrisk, size=num_mothers)
    i_loc_anc_lowrisk_neg = rng.choice(3, p=prob_matrix_lowrisk_adj, size=num_mothers)

    # ANC Highrisk
    i_loc_anc_highrisk_pos = rng.choice(3, p=prob_matrix_highrisk, size=num_mothers)
    i_loc_anc_highrisk_neg = rng.choice(3, p=prob_matrix_highrisk_adj, size=num_mothers)

    # Assign locations based on ANC and risk status
    i_loc[noanc_mask & positive_mask] = i_loc_noanc_pos[noanc_mask & positive_mask]
    i_loc[noanc_mask & negative_mask] = i_loc_noanc_neg[noanc_mask & negative_mask]
    i_loc[anc_lowrisk_mask & positive_mask] = i_loc_anc_lowrisk_pos[anc_lowrisk_mask & positive_mask]
    i_loc[anc_lowrisk_mask & negative_mask] = i_loc_anc_lowrisk_neg[anc_lowrisk_mask & negative_mask]
    i_loc[anc_highrisk_mask & positive_mask] = i_loc_anc_highrisk_pos[anc_highrisk_mask & positive_mask]
    i_loc[anc_highrisk_mask & negative_mask] = i_loc_anc_highrisk_neg[anc_highrisk_mask & negative_mask]

    # #draw location assignments for all mothers using each strategy
    # i_loc_noanc_all = rng.choice(3, p=prob_matrix_noANC, size=num_mothers)
    # i_loc_anc_highrisk_all = rng.choice(3, p=prob_matrix_highrisk, size=num_mothers)
    # i_loc_anc_lowrisk_all = rng.choice(3, p=prob_matrix_lowrisk, size=num_mothers)
    # #apply results only to relevant mothers
    # i_loc = np.zeros(num_mothers, dtype=int)
    # i_loc[noanc_mask] = i_loc_noanc_all[noanc_mask]
    # i_loc[anc_highrisk_mask] = i_loc_anc_highrisk_all[anc_highrisk_mask]
    # i_loc[anc_lowrisk_mask] = i_loc_anc_lowrisk_all[anc_lowrisk_mask]

    #Reallocate mothers if overcapacity
    n_l45 = np.count_nonzero(i_loc == 2)
    exceed_lb = max(n_l45 - Capacity, 0)
    shuffled_all = rng.permutation(num_mothers)   # shuffle all mother indices
    l45_indices = np.where(i_loc == 2)[0]         # identify L4/5 mothers
    shuffled_l45 = shuffled_all[np.isin(shuffled_all, l45_indices)]  # filter only those in L4/5 from the shuffled list
    relocate_indices = shuffled_l45[:exceed_lb]                      # select only the top `exceed_lb` mothers to relocate
    mask_relocate_l23 = np.zeros(num_mothers, dtype=bool)            # apply relocation
    mask_relocate_l23[relocate_indices] = True
    i_loc[mask_relocate_l23] = 1

    ##-------------------Elective C-section Decision----------------------##
    elcs_mask1 = (i_loc == 2) & (i_risk_pred == 1) & (i_preterm_pred == 0) & (i_ANC == 1)
    elcs_mask2 = (i_loc == 2) & (i_preterm_pred == 1) & (i_ANC == 1)
    i_elcs_case1 = (rng.random(num_mothers) < p_elec_CS_highrisk).astype(int)
    i_elcs_case2 = (rng.random(num_mothers) < param["p_elec_CS|preterm"]).astype(int)
    i_elec_CS = np.zeros(num_mothers, dtype=int)
    i_elec_CS[elcs_mask1] = i_elcs_case1[elcs_mask1]
    i_elec_CS[elcs_mask2] = i_elcs_case2[elcs_mask2]

    ##-------------------Move some live births from l4 to l5----------------------##
    l4_mask = (i_loc == 2)
    l4_to_l5_mask = (rng.random(num_mothers) <  param['p_l5_l45']).astype(bool)
    l4_to_l5 = l4_mask & l4_to_l5_mask
    i_loc[l4_to_l5] = 3
    i_loc = i_loc.astype(int)
    i_self_referral = (i_loc >= 2).astype(int)
    i_free_referral = np.zeros(num_mothers, dtype=int)

    ##------------------ANC-related single interventions------------------------##
    P_knowledge = np.array(
        [0, param['base_knowledge_L23'], param['base_knowledge_L45'], param['base_knowledge_L45']])
    if flags['flag_performance']:
        P_knowledge[2] = param["HSS"]["knowledge"]
        P_knowledge[3] = param["HSS"]["knowledge"]
    P_close_to_L23 = param["close_to_L23"]
    P_close_to_L45 = 1 - P_close_to_L23
    P_iv_iron = param["S"]["iv_iron"] * (P_knowledge[1] * P_close_to_L23 + P_knowledge[3] * P_close_to_L45)

    i_anemia = (rng.random(num_mothers) < param['p_anemia_anc'][i_ANC]).astype(int) #rng.binomial(1, param['p_anemia_anc'][i_ANC])         # Anemia status for each mother
    i_anemia_new = i_anemia.copy()
    eligible_iv_iron = (i_ANC == 1) & (i_anemia == 1)                                   # Boolean mask for eligible mothers
    i_iv_iron = np.zeros(num_mothers, dtype=int)
    iv_iron_provided = (rng.random(num_mothers) < P_iv_iron).astype(int)  #rng.binomial(1, P["iv_iron"], size=num_mothers)
    i_iv_iron[eligible_iv_iron] = iv_iron_provided[eligible_iv_iron]     # Ensures only eligible mothers can receive it
    anemia_cured = (i_iv_iron == 1) & (rng.random(num_mothers) < (1 - param['E_iv_iron']))  # Boolean mask for cured cases
    i_anemia_new[anemia_cured] = 0                                                          # Cure anemia for affected mothers

    ##-------------------Update indvidual outcomes----------------------##
    i_preterm = (i_GA < 37).astype(int)
    individual_outcomes = pd.DataFrame({
        'i_loc': i_loc.astype(int),
        'i_ANC': i_ANC.astype(int),
        'i_class': i_class.astype(int),
        'i_risk': i_risk.astype(int),
        'i_GA': i_GA.astype(int),
        'i_preterm': i_preterm.astype(int),
        'i_elec_CS': i_elec_CS.astype(int),
        'i_jGA': i_jGA.astype(int),
        'i_risk_pred': i_risk_pred.astype(int),
        'i_preterm_pred': i_preterm_pred.astype(int),
        'i_pocus': i_pocus.astype(int),
        'i_self_referral': i_self_referral.astype(int),
        'i_free_referral': i_free_referral.astype(int),
        'i_anemia': i_anemia.astype(int),
        'i_anemia_new': i_anemia_new.astype(int),
        'i_iv_iron': i_iv_iron.astype(int),
    })
    return individual_outcomes, negative_experience_heard, CHV_IDs, CHV_negative_experience, CHV_memory_age

#Updated - add CHV effect
def shifting_live_births_vectorized(individual_outcomes, param, i, track, flags, int_period, rng, negative_experience_heard, CHV_IDs, CHV_negative_experience, CHV_memory_age):
    if not flags["flag_LB"]:
        # Dummy RNG usage to consume same number of random draws
        num_mothers = individual_outcomes.shape[0]
        _ = rng.permutation(num_mothers)
        _ = rng.random(num_mothers)
        _ = rng.permutation(num_mothers)
        _ = rng.choice([2, 3], size=num_mothers, p=[0.5, 0.5])
        _ = rng.random(num_mothers)

        individual_outcomes['i_neg_exp_heard'] = negative_experience_heard.astype(int)
        individual_outcomes['i_neg_exp_owned'] = np.zeros(num_mothers, dtype=int)

        return individual_outcomes
    else:
        ##-------------------Parameter initialization-------------------##
        i_loc = individual_outcomes['i_loc'].values
        i_class = individual_outcomes['i_class'].values
        i_self_referral = individual_outcomes['i_self_referral'].values
        i_free_referral = individual_outcomes['i_free_referral'].values
        num_mothers = i_loc.shape[0]
        LB_base = track["LB_Track"][0]
        Facility_Capacity = track['Facility_Capacity_Track'][i, 0]
        Referral_Capacity = track['Referral_Capacity_Track'][i, 0]
        p_l5_l45 = param['p_l5_l45']
        p_lb_l23to45 = param['p_lb_l23_45']
        tau_decay = param["HSS"]['tau_decay']
        RR_l45_poorQOC = param['RR_l45_poorQOC']

        ##-------------------Shifting of live births-------------------##
        # Step 1: Compute expected L45 target
        p_l45_base = (LB_base[2] + LB_base[3]) / num_mothers
        p_l45_pre_base = p_l45_base - p_lb_l23to45
        l45_target_growth = (param["HSS"]["P_L45"] - p_l45_pre_base)  # targeted live birth growth at l4/5 before transfer

        if i < int_period:
            p_l45_exp_actual = (p_l45_pre_base + (l45_target_growth / (int_period - 1) * i))
        else:
            p_l45_exp_actual = (p_l45_pre_base + l45_target_growth)

        # st.text("p_l45_exp_actual: " + str(p_l45_exp_actual))
        # p_negative = np.mean(negative_experience_heard)  # Probability of negative experience heard
        # st.text("p_negative: " + str(p_negative))

        # Step 2: Find mothers need to shift to L4/5
        def select_mothers_for_shift(i_loc, num_mothers, p_l45_exp_actual, Facility_Capacity,
                                        rng, negative_experience_heard, RR_l45_poorQOC):
            """
            Updated version:
            - No separate permutation.
            - Fully global random numbers control.
            """

            # Step 1: Identify mothers at home or L2/3
            home_l23_mask = (i_loc == 0) | (i_loc == 1)

            # Step 2: Compute total expected movers
            num_l45_exp = np.ceil(p_l45_exp_actual * num_mothers).astype(int)
            num_l45_bf_shift = np.count_nonzero((i_loc == 2) | (i_loc == 3))
            num_l45_exp_new = max(num_l45_exp - num_l45_bf_shift, 0)

            # Step 3: Random numbers for everyone
            move_random_draw = rng.random(num_mothers)

            # Step 4: Among eligible (home/L2/3) mothers, pick based on random numbers (smallest first)
            eligible_indices = np.where(home_l23_mask)[0]
            eligible_random = move_random_draw[eligible_indices]

            sorted_eligible_indices = eligible_indices[np.argsort(eligible_random)]
            selected_indices = sorted_eligible_indices[:min(num_l45_exp_new, len(sorted_eligible_indices))]

            mothers_need_shift = np.zeros(num_mothers, dtype=int)
            mothers_need_shift[selected_indices] = 1

            # Step 5: Apply negative experience adjustment
            p_move = np.ones(num_mothers)
            p_move[negative_experience_heard == 1] *= RR_l45_poorQOC

            # Step 6: Random draw again for move intention
            final_shift_mask = (move_random_draw < p_move) & (mothers_need_shift == 1)

            # Step 7: Facility capacity constraint
            movers_intended_indices = np.where(final_shift_mask)[0]
            move_random_draw_intended = move_random_draw[movers_intended_indices]

            sorted_movers_indices = movers_intended_indices[np.argsort(move_random_draw_intended)]

            num_intended = len(movers_intended_indices)
            num_l45_max = int(np.floor(Facility_Capacity - num_l45_bf_shift))
            num_select_final = min(num_l45_max, num_intended)

            allowed_indices = sorted_movers_indices[:num_select_final]
            constrained_indices = sorted_movers_indices[num_select_final:]

            mothers_allowed_shift = np.zeros(num_mothers, dtype=int)
            mothers_constrained_shift = np.zeros(num_mothers, dtype=int)
            mothers_allowed_shift[allowed_indices] = 1
            mothers_constrained_shift[constrained_indices] = 1

            negative_experience_owned = np.zeros(num_mothers, dtype=int)
            negative_experience_owned[mothers_constrained_shift == 1] = 1

            return mothers_need_shift, final_shift_mask, mothers_allowed_shift, negative_experience_owned

        # def select_mothers_for_shift(i_loc, num_mothers, p_l45_exp_actual, Facility_Capacity,
        #                              rng, negative_experience_heard, RR_l45_poorQOC):
        #     """
        #     Select mothers who intend to shift to L4/5, apply risk ratio adjustment if they heard negative experience.
        #     """
        #
        #     # Step 1: Identify mothers at home or L2/3
        #     home_l23_mask = (i_loc == 0) | (i_loc == 1)                 # Boolean mask for mothers at home or L2/3
        #
        #     # Step 2: Compute total expected movers
        #     num_l45_exp = np.ceil(p_l45_exp_actual * num_mothers).astype(int)   # expected number of live births at L4/5
        #     num_l45_bf_shift = np.count_nonzero((i_loc == 2) | (i_loc == 3))    # number of mothers already at L4/5
        #     num_l45_exp_new = max(num_l45_exp - num_l45_bf_shift, 0)            # expected number of live births at L4/5 after accounting for those already there
        #
        #     # Step 3: Find eligible home/L2/3 mothers
        #     eligible_indices = np.where(home_l23_mask)[0]
        #     perm_eligible = rng.permutation(num_mothers)
        #     perm_home_l23 = perm_eligible[np.isin(perm_eligible, eligible_indices)]
        #     num_eligible = len(perm_home_l23)
        #     num_select_initial = min(num_l45_exp_new, num_eligible)
        #
        #     # Step 4: Select initial mothers needing to move
        #     selected_indices = perm_home_l23[:num_select_initial]
        #     mothers_need_shift = np.zeros(num_mothers, dtype=int)
        #     mothers_need_shift[selected_indices] = 1
        #
        #     # Step 5: Apply risk ratio adjustment for negative experience
        #     p_move = np.ones(num_mothers)
        #     negative_mask = (negative_experience_heard == 1)
        #     p_move[negative_mask] *= RR_l45_poorQOC
        #
        #     # Step 6: Random draw only among selected mothers
        #     move_random_draw = rng.random(num_mothers)
        #     final_shift_mask = (move_random_draw < p_move) & (mothers_need_shift == 1)
        #
        #     # Step 7: Facility capacity constraint
        #     movers_intended_indices = np.where(final_shift_mask == 1)[0]
        #     perm_indices_full = rng.permutation(num_mothers)
        #     perm_movers_intended = perm_indices_full[np.isin(perm_indices_full, movers_intended_indices)]
        #     num_intended = len(movers_intended_indices)
        #     num_l45_max = np.floor(Facility_Capacity - num_l45_bf_shift).astype(int)
        #     num_select_final = min(num_l45_max, num_intended)
        #     allowed_indices = perm_movers_intended[:num_select_final]
        #     constrained_indices = perm_movers_intended[num_select_final:]
        #
        #     mothers_allowed_shift = np.zeros(num_mothers, dtype=int)
        #     mothers_constrained_shift = np.zeros(num_mothers, dtype=int)
        #     mothers_allowed_shift[allowed_indices] = 1
        #     mothers_constrained_shift[constrained_indices] = 1
        #
        #     negative_experience_owned = np.zeros(num_mothers, dtype=int)  # 0 = no negative experience, 1 = negative experience
        #     negative_experience_owned[mothers_constrained_shift == 1] = 1
        #
        #     return mothers_need_shift, final_shift_mask, mothers_allowed_shift, negative_experience_owned

        mothers_need_shift, final_shift_mask, mothers_allowed_shift, negative_experience_owned = select_mothers_for_shift(i_loc, num_mothers, p_l45_exp_actual, Facility_Capacity,
                                     rng, negative_experience_heard, RR_l45_poorQOC)

        # p_reduced_intention = np.sum(final_shift_mask.astype(int)) / np.sum(mothers_need_shift.astype(int))
        # p_allowed = np.sum(mothers_allowed_shift.astype(int)) / np.sum(final_shift_mask.astype(int))
        # st.text(f'month {i}')
        # st.text(f'p_intended: {p_reduced_intention}')
        # st.text(f'p_allowed: {p_allowed}')

        # Step 3: Shift the mothers who are allowed to shift
        i_loc_new = i_loc.copy()
        p_l4_l5 = np.array([(1 - p_l5_l45), p_l5_l45])
        l4_l5 = rng.choice([2, 3], p=p_l4_l5, size=num_mothers)

        def move_function(num_mothers, l4_l5, i_class, i_loc_new,
                          i_free_referral, i_self_referral, Referral_Capacity, flags,
                          mothers_allowed_shift, rng, negative_experience_owned):
            """
                Move allowed mothers to L4/5. Handle referral constraints.
            """
            flag_refer = flags["flag_refer"]
            allowed_mask = (mothers_allowed_shift == 1)

            p_free_refer = Referral_Capacity if flag_refer else 0

            # Random draw for free referral
            free_refer_draws = rng.random(num_mothers)
            move_free_refer_mask = allowed_mask & (free_refer_draws < p_free_refer)

            i_free_referral[move_free_refer_mask] = 1
            i_loc_new[move_free_refer_mask] = l4_l5[move_free_refer_mask]

            # Self-referral for high SES
            no_free_referral_mask = allowed_mask & (~move_free_refer_mask)
            self_referral_possible_mask = no_free_referral_mask & (i_class == 1)

            i_self_referral[self_referral_possible_mask] = 1
            i_loc_new[self_referral_possible_mask] = l4_l5[self_referral_possible_mask]

            # Mothers who fail to move because of no transport
            failed_referral_mask = no_free_referral_mask & (i_class != 1)
            negative_experience_owned[failed_referral_mask] = 1  # Mark these mothers as having negative experience

            return i_loc_new, i_free_referral, i_self_referral, negative_experience_owned

        i_loc_new, i_free_referral, i_self_referral, negative_experience_owned = move_function(num_mothers, l4_l5, i_class, i_loc_new,
                          i_free_referral, i_self_referral, Referral_Capacity, flags,
                          mothers_allowed_shift, rng, negative_experience_owned)

        ##-------------------Apply negative feedback to CHVs-------------------##
        # Extract previous CHV negative experience and memory age
        CHV_negative_experience_prev = track['CHV_negative_Track'][i-1, :].copy()    # Retrieve previous CHV negative experience
        CHV_memory_age_prev = track['CHV_memory_Track'][i - 1, :].copy()
        CHV_negative_experience = CHV_negative_experience_prev.copy()
        CHV_memory_age = CHV_memory_age_prev.copy()

        # Mothers who had new negative experience
        mothers_with_negative = (negative_experience_owned == 1)
        linked_CHVs = CHV_IDs[mothers_with_negative]
        linked_CHVs = linked_CHVs[linked_CHVs >= 0]   # Filter valid CHVs only
        CHV_negative_experience[np.unique(linked_CHVs)] = 1                     # Update CHV negative experience

        # Detect CHVs who newly received negative experience this month
        new_infections = (CHV_negative_experience == 1) & (CHV_negative_experience_prev == 0)
        CHV_memory_age[new_infections] = 0 # Reset memory for newly infected CHVs
        already_infected = (CHV_negative_experience_prev == 1)
        CHV_memory_age[already_infected] += 1

        ##-------------------Update parameters-------------------##
        track['CHV_negative_Track'][i, :] = CHV_negative_experience.copy()
        track['CHV_memory_Track'][i, :] = CHV_memory_age.copy()
        individual_outcomes['i_loc'] = i_loc_new.astype(int)
        individual_outcomes['i_free_referral'] = i_free_referral.astype(int)
        individual_outcomes['i_self_referral'] = i_self_referral.astype(int)
        individual_outcomes['i_neg_exp_heard'] = negative_experience_heard.astype(int)
        individual_outcomes['i_neg_exp_owned'] = negative_experience_owned.astype(int)

        return individual_outcomes


#Rational - all mothers can know negative feedback
# def shifting_live_births_vectorized(individual_outcomes, param, i, track, flags, int_period, rng):
#     if not flags["flag_LB"]:
#         # Dummy RNG usage to consume same number of random draws
#         num_mothers = individual_outcomes.shape[0]
#         _ = rng.choice([2, 3], size=num_mothers, p=[0.5, 0.5])
#         _ = rng.permutation(num_mothers)
#         _ = rng.random(num_mothers)
#         _ = rng.permutation(num_mothers)
#         _ = rng.random(num_mothers)
#         return individual_outcomes
#     else:
#         ##-------------------Parameter initialization-------------------##
#         i_loc = individual_outcomes['i_loc'].values
#         i_class = individual_outcomes['i_class'].values
#         i_self_referral = individual_outcomes['i_self_referral'].values
#         i_free_referral = individual_outcomes['i_free_referral'].values
#         num_mothers = i_loc.shape[0]
#         LB_base = track["LB_Track"][0]
#         Facility_Capacity = track['Facility_Capacity_Track'][i, 0]
#         Referral_Capacity = track['Referral_Capacity_Track'][i, 0]
#         p_l5_l45 = param['p_l5_l45']
#         p_lb_l23to45 = param['p_lb_l23_45']
#         alpha_feedback = param["HSS"]['alpha_feedback']  # Strength of negative feedback (adjustable)
#         tau_decay = param["HSS"]['tau_decay']
#         T_memory = min(i, tau_decay)  # Ensure we only take available history
#
#         ##-------------------Shifting of live births-------------------##
#         # Step 1: Compute expected L45 target
#         p_l45_base = (LB_base[2] + LB_base[3]) / num_mothers
#         p_l45_pre_base = p_l45_base - p_lb_l23to45
#         l45_target_growth = (param["HSS"]["P_L45"] - p_l45_pre_base)  # targeted live birth growth at l4/5 before transfer
#
#         # Step 2: Retrieve past constraints
#         past_constraints = track['Constraint_Ratio_Track'][max(0, i - T_memory):i, 0]
#         past_constraints = np.pad(past_constraints, (tau_decay - past_constraints.shape[0], 0), constant_values=1)
#
#         # Step 4: Calculate memory weights
#         memory_weights = np.exp(-np.arange(tau_decay)[::-1] / tau_decay)
#         memory_weights /= memory_weights.sum()  # Normalize weights to sum to 1
#
#         # Step 5: Compute overall constraint ratio (blending past & current)
#         constraint_ratio = np.sum(memory_weights * past_constraints)
#         feedback_factor = constraint_ratio ** alpha_feedback  # Strength of the effect
#
#         # Step 6: Compute adjusted expected probability of L4/5 live births at time i
#         if i < int_period:
#             p_l45_exp_actual = (p_l45_pre_base + (l45_target_growth / (int_period - 1) * i) * feedback_factor)
#         else:
#             p_l45_exp_actual = (p_l45_pre_base + l45_target_growth * feedback_factor)
#
#         p_l45_exp_nofb = (p_l45_pre_base + (l45_target_growth / (int_period - 1) * i)) \
#             if i < int_period else (
#                     p_l45_pre_base + l45_target_growth)  # expected proportion of live births at L4/5 without negative feedback
#
#         # Step 7: Compute allowed live births at L4/L5
#         num_l45_exp = np.ceil(p_l45_exp_actual * num_mothers).astype(int)  # expected number of live births at L4/5
#         num_l45_max = np.ceil(Facility_Capacity).astype(int)
#         num_l45_allowed = min(num_l45_exp, num_l45_max)
#
#         # Step 8: Calculate how many need to shift from home and L2/3
#         n_home_origin = np.count_nonzero(i_loc == 0)
#         n_l23_origin = np.count_nonzero(i_loc == 1)
#         n_l45_origin = np.count_nonzero((i_loc == 2) | (i_loc == 3))
#
#         num_move_total = max(num_l45_allowed - n_l45_origin, 0)
#         prop_home = n_home_origin / (n_home_origin + n_l23_origin)
#         num_home_move = np.ceil(num_move_total * prop_home).astype(int)
#         num_l23_move = num_move_total - num_home_move
#         p_l4_l5 = np.array([(1 - p_l5_l45), p_l5_l45])
#         l4_l5 = rng.choice([2, 3], p=p_l4_l5, size=num_mothers)
#
#         ##-------------------True move based on referral network-------------------##
#         i_loc_new = i_loc.copy()
#         if num_home_move > 0:
#             i_loc_new, i_free_referral, i_self_referral = move_function(num_mothers, l4_l5, i_class, i_loc, i_loc_new, i_free_referral, i_self_referral, Referral_Capacity, flags, num_home_move, 0, rng)
#         else:
#             _ = rng.permutation(num_mothers)
#             _ = rng.random(num_mothers)
#
#         if num_l23_move > 0:
#             i_loc_new, i_free_referral, i_self_referral = move_function(num_mothers, l4_l5, i_class, i_loc, i_loc_new, i_free_referral, i_self_referral, Referral_Capacity, flags, num_l23_move, 1, rng)
#         else:
#             _ = rng.permutation(num_mothers)
#             _ = rng.random(num_mothers)
#
#         ##-------------------Negative Feedback of Facility Overcapacity-------------------##
#         l45_exp_nofb = np.ceil(p_l45_exp_nofb * num_mothers).astype(int)
#         l45_actual = np.count_nonzero((i_loc_new == 2) | (i_loc_new == 3))
#
#         constraint_ratio_i = 1 - (l45_exp_nofb - l45_actual) / l45_exp_nofb
#         # the proportion of negative feedback among mothers who were expected to move
#
#         ##-------------------Update parameters-------------------##
#         track['Num_Exp_L45_Track'][i] = num_l45_exp
#         track['Constraint_Ratio_Track'][i] = np.clip(constraint_ratio_i, 0, 1)
#         individual_outcomes['i_loc'] = i_loc_new.astype(int)
#         individual_outcomes['i_free_referral'] = i_free_referral.astype(int)
#         individual_outcomes['i_self_referral'] = i_self_referral.astype(int)
#
#         return individual_outcomes

# def f_LB_effect(param, i, track, flags, int_period, rng):
#     LB_base = track['LB_Track'][0]
#
#     n = {}
#     n["LB_L"], n["highrisk"], n["ANC"], n["Free_referrals"], n["Self_referrals"], n["Elective_CS"], n["GA"] \
#         = f_ANC_LB_effect(track, LB_base, param, flags, i, int_period)
#
#     if flags['flag_LB']:
#         track_LB, track_highrisk, track_ANC, free_refers, self_refers, planned_CSs, GA_PDFs = shifting_live_births(n["LB_L"], n["highrisk"], n["ANC"],
#                                                                                     n["Free_referrals"], n["Self_referrals"], n["Elective_CS"], n["GA"],
#                                                                                     param, i, track,
#                                                                                     flags, int_period)
#     else:
#         track_LB, track_highrisk, track_ANC, free_refers, self_refers, planned_CSs, GA_PDFs = n["LB_L"], n["highrisk"], n["ANC"], n["Free_referrals"], n["Self_referrals"], n["Elective_CS"], n["GA"]
#
#     #update whole county outcomes at time i
#     track['LB_Track'][i] = track_LB
#     track['HighRisk_Track'][i] = track_highrisk
#     track['ANC_Track'][i] = track_ANC
#
#     return track, free_refers, self_refers, planned_CSs, GA_PDFs
#
# #New version - adding gestational age estimation in ANC_LB effect
# def f_ANC_LB_effect(track, LB_base, param, flags, i, int_period, rng):
#     P = {}  # dict to restore probabilities
#     n = {}  # dict to restore counts
#     E = {}  # dict to restore effects
#     OR = {}  # dict to restore odds ratio
#     M = {}  # dict to restore maternal outcomes
#
#     LB_tot = LB_base.astype(int)
#     flag_ANC = flags["flag_ANC"]
#     if flag_ANC:
#         if i < int_period:
#             P["ANC"] = param['p_ANC_base'] + (param["HSS"]["P_ANC"] - param['p_ANC_base']) / (int_period-1) * i
#         else:
#             P["ANC"] = param["HSS"]["P_ANC"]
#     else:
#         P["ANC"] = param['p_ANC_base']
#
#     #Parameters for risk stratification
#     P["p_highrisk"] = param["p_highrisk"]                                 # high risk pregnancies among all live births
#     E["Sen_US"] = param['E']["sens_us"]                                   # sensitivity of US
#     E["Spec_US"] = param['E']["spec_us"]                                  # specificity of US
#     P["refer"] = track['Referral_Capacity_Track'][i, 0]                      # referral capacity
#     P["class"] = param["class"]                                           # SES status
#     P['p_l5_l45'] = param['p_l5_l45']                                     # probability of delivering at l5 if delivering at L45
#     P["close_to_L23"] = param["close_to_L23"]                             # probability of mothers having cloest distance to L2/3 facility
#     P["close_to_L45"] = 1- P["close_to_L23"]                                # probability of mothers having cloest distance to L4/5 facility
#     P["p_elec_CS|highrisk"] = param["p_elec_CS|highrisk"]
#     Capacity = track['Facility_Capacity_Track'][i, 0]
#
#     #Effect of gestational age estimation
#     E["GA_US"] = param["E_GA_US"]                                         #% Normal distribution parameters for GA error | US
#     E["Preterm_LMP"] = param["E_Preterm_LMP"]
#     E["Postterm_LMP"] = param["E_Postterm_LMP"]
#
#     # Six parameters - calibrated using simulating annealing
#     P["home_noANC"] = param["home_noANC"]                               # probability of home delivery without ANC
#     P["L45_fac"] = param["l45_fac"]                                     # probability of delivery at L4/5 facility if chosing deliver at facilities and without ANC
#     P["home_lowrisk"] = param["home_lowrisk"]                           # probability of home delivery if predicted as low risk
#     P["L23_highrisk"] = param["L23_highrisk"]                           # probability of delivery at L2/3 facility if predicted as high risk
#     E["sen_risk_trad"] = param["sen_risk_trad"]                         # sensitivity of traditional ANC monitoring
#     E["spec_risk_trad"] = param["spec_risk_trad"]                       # probability of elective CS given high risk - calibrated using optimization(method='Nelder-Mead')
#
#     P["GA_anc"], P["GA_noanc"] = param["GA_anc"], param["GA_noanc"]
#
#     # Initialize counters
#     n["highrisk"] = np.zeros(4)                                           #number of high-risk pregnancies by facility levels
#     n["ANC"] = np.zeros(4)                                                #number of 4+ANC by facility levels
#     n["LB_L"] = np.zeros(4)                                               #number of delivery location by facility levels
#     n["LB_ANC"] = np.zeros(4)                                             #number of live births given with 4+ANCs
#     n["Free_referrals"] = np.zeros(2)                                     #number of free referrals by SES status
#     n["Self_referrals"] = np.zeros(2)                                     #number of self referrals by SES status
#     n["Elective_CS"] = np.zeros(2)
#     M["Preterm"] = np.zeros(4)
#     M["Postterm"] = np.zeros(4)
#     M["GA"] = np.zeros((4, len(param['GA_sequence'])))                    #GA distributions by facility levels
#
#     #Set up flags
#     flag_POCUS = flags["flag_us"]
#     flag_refer = flags["flag_refer"]
#     if not flag_POCUS:
#         P["ELCS|highrisk"] = param["p_elec_CS|highrisk"]                  # probability of elective CS given high risk
#     else:
#         P["ELCS|highrisk"] = param["p_elec_CS|highrisk_us"]
#
#     if flag_refer:
#         P["refer"] = track['Referral_Capacity_Track'][i, 0]
#     else:
#         P["refer"] = 0
#
#     #debug
#     n_lb_noanc = np.zeros(4)
#     n_lb_lowrisk = np.zeros(4)
#     n_lb_highrisk = np.zeros(4)
#     n_pred_highrisk = 0
#     n_pred_preterm = 0
#     n_pred_postterm = 0
#     n_preterm = 0
#     n_atterm = 0
#     n_postterm = 0
#
#
#     for k_LB in range(np.sum(LB_tot)):
#         i_class = rng.binomial(1, P["class"])            #1 = high SES, 0 = low SES
#         i_risk = rng.binomial(1, P["p_highrisk"])
#         i_ANC = rng.binomial(1, P["ANC"])
#         P_fac_noANC = 1 - P["home_noANC"]
#         P_L45_noANC = P_fac_noANC * P["L45_fac"]
#         P_L23_noANC = P_fac_noANC - P_L45_noANC
#         i_elec_CS = 0
#         i_free_refer = 0
#         if i_ANC:
#             P_GA = P["GA_anc"]
#         else:
#             P_GA = P["GA_noanc"]
#
#         i_jGA = np.searchsorted(np.cumsum(P_GA), rng.random())  # % actual index of GA
#         i_GA = param['GA_sequence'][i_jGA]                          # % actual GA
#
#         if i_GA < 37:
#             i_term_status = 0   #% 0 = preterm, 1 = full term, 2 = post-term
#         elif i_GA >= 43:
#             i_term_status = 2
#         else:
#             i_term_status = 1
#
#         n_preterm += (i_term_status == 0)
#         n_atterm += (i_term_status == 1)
#         n_postterm += (i_term_status == 2)
#
#         if i_ANC == 0:
#             # Delivery location selection based on conditional probabilities
#             if (n["LB_L"][2] + n["LB_L"][3]) < Capacity:
#                 i_loc = rng.choice([0, 1, 2], p=[P["home_noANC"], P_L23_noANC, P_L45_noANC]) #delivery location without ANC - home, L2/3, L4/5
#             else:
#                 i_loc = rng.choice([0, 1, 1], p=[P["home_noANC"], P_L23_noANC, P_L45_noANC])
#
#             if i_loc == 2 and rng.random() < P['p_l5_l45']:
#                 i_loc = 3
#
#             i_self_refer = 1 if i_loc > 1 else 0  # no free referrals, every referral is self referral
#
#             n_lb_noanc[i_loc] += 1
#         else:
#             # Risk stratification
#             if flag_POCUS:
#                 if i_risk == 1:
#                     i_risk_pred = 1 if rng.random() < E["Sen_US"] else 0
#                 else:
#                     i_risk_pred = 0 if rng.random() < E["Spec_US"] else 1
#             else:
#                 if i_risk == 1:
#                     i_risk_pred = 1 if rng.random() < E["sen_risk_trad"] else 0
#                 else:
#                     i_risk_pred = 0 if rng.random() < E["spec_risk_trad"] else 1
#
#
#
#             # Gestational age estimation
#             if flag_POCUS:
#                 i_GA_approx = i_GA + E["GA_US"][0] + E["GA_US"][1] * rng.normal(0, 1, size=1)
#                 i_preterm_pred = 1 if i_GA_approx < 37 else 0
#                 i_postterm_pred = 1 if i_GA_approx >= 43 else 0
#             else:
#                 i_preterm_pred = 1 if rng.random() < E["Preterm_LMP"][i_term_status] else 0
#                 i_postterm_pred = 1 if rng.random() < E["Postterm_LMP"][i_term_status] else 0
#
#
#             # Normal referrals
#             if (n["LB_L"][2] + n["LB_L"][3]) < Capacity: #if live births in L4/5 is less than facility capacity
#                 if (i_risk_pred == 1) or (i_preterm_pred == 1) or (i_postterm_pred == 1):
#                     i_loc = rng.choice([0, 1, 2], p=[0, P["L23_highrisk"], 1 - P["L23_highrisk"]]) #0 = home, 1 = L2/3, 2 = L4/5
#                 else:
#                     i_loc = rng.choice([0, 1, 2], p=[P["home_lowrisk"], (1 - P["home_lowrisk"]) * P["close_to_L23"], (1 - P["home_lowrisk"]) * P["close_to_L45"]])
#             else:
#                 if (i_risk_pred == 1) or (i_preterm_pred == 1) or (i_postterm_pred == 1):
#                     i_loc = rng.choice([0, 1, 1], p=[0, P["L23_highrisk"], 1 - P["L23_highrisk"]])
#                 else:
#                     i_loc = rng.choice([0, 1, 1], p=[P["home_lowrisk"], (1 - P["home_lowrisk"]) * P["close_to_L23"], (1 - P["home_lowrisk"]) * P["close_to_L45"]])
#
#             n_lb_lowrisk[i_loc] += (i_risk_pred == 0 and i_preterm_pred == 0 and i_postterm_pred == 0)
#             n_lb_highrisk[i_loc] += (i_risk_pred == 1 or i_preterm_pred == 1 or i_postterm_pred == 1)
#             n_pred_highrisk += i_risk_pred == 1
#             n_pred_preterm += i_preterm_pred
#             n_pred_postterm += i_postterm_pred
#
#             if i_loc > 1:
#                 i_self_refer = 1
#             else:
#                 i_self_refer = 0
#
#             if i_loc == 2 and rng.random() < P['p_l5_l45']:
#                 i_loc = 3
#
#             # Elective CS
#             if i_loc > 1 and (i_risk_pred == 1 or i_preterm_pred == 1):
#                 # elective CS
#                 if i_loc > 1 and (i_risk_pred or i_preterm_pred):
#                     if i_risk_pred:
#                         i_elec_CS = rng.binomial(1, P["ELCS|highrisk"])
#                     elif i_preterm_pred:
#                         i_elec_CS = rng.binomial(1, param["p_elec_CS|preterm"])
#
#
#         # restore results
#         n["highrisk"][i_loc] += i_risk
#         n["ANC"][i_loc]      += i_ANC
#         n["LB_L"][i_loc]     += 1
#         n["Free_referrals"][i_class] += i_free_refer
#         n["Self_referrals"][i_class] += i_self_refer
#         n["Elective_CS"][i_risk] += i_elec_CS
#         M["GA"][i_loc, i_jGA] += 1
#         M["Preterm"][i_loc] += i_term_status == 0
#         M["Postterm"][i_loc] += i_term_status == 2
#
#         #make n["LB_L"] as integers
#         n["LB_L"] = n["LB_L"].astype(int)
#
#     #Debug
#     #st.text(f'n_preterm {np.sum(M["Preterm"]) / np.sum(LB_tot)}') - correct
#     # p_lb_noanc = n_lb_noanc / (np.sum(n["LB_L"]) - np.sum(n["ANC"])) - correct
#     # st.text(f'p_lb_noanc_old: {p_lb_noanc}') - correct
#     # st.text(f'p_lb_lowrisk_old: {n_lb_lowrisk / np.sum(n_lb_lowrisk)}') - correct
#     # st.text(f'p_lb_highrisk_old: {n_lb_highrisk / np.sum(n_lb_highrisk)}') - correct
#     # st.text(n_preterm)
#     # st.text(n_atterm)
#     # st.text(n_postterm)
#     # st.text(f'n_pred_highrisk_old: {n_pred_highrisk}')
#     # st.text(f'n_pred_preterm_old: {n_pred_preterm}')
#     # st.text(f'n_pred_postterm_old: {n_pred_postterm}')
#     # st.text(f'n_elcs: {np.sum(n["Elective_CS"])}')
#
#     return n["LB_L"], n["highrisk"], n["ANC"], n["Free_referrals"], n["Self_referrals"], n["Elective_CS"], M["GA"]
#
#
# def shifting_live_births(LB_L, n_risk, n_ANC, n_free_refer, n_self_refer, n_elec_CS, n_GAs, param, i, track, flags, int_period, rng):
#
#     # Initialize parameters
#     LB_base = track["LB_Track"][0]
#     Facility_Capacity = track['Facility_Capacity_Track'][i, 0]
#     p_l5_l45 = param['p_l5_l45']
#     p_lb_l23to45 = param["p_lb_l23to45"]
#
#     # Compute high-risk and ANC probabilities
#     P_highrisk = n_risk / LB_L
#     P_ANC = n_ANC / LB_L
#
#     # Compute Elective CS Probabilities
#     p_elec_cs_lowrisk = n_elec_CS[0] / (np.sum(LB_L[2:]) - np.sum(n_risk[2:]))
#     p_elec_cs_highrisk = n_elec_CS[1] / np.sum(n_risk[2:])
#     P_Elective_CS = np.array([p_elec_cs_lowrisk, p_elec_cs_highrisk])
#
#     # Normalize GA distributions
#     GA_sequence = param['GA_sequence']
#     GA_probabilities = np.zeros((4, len(GA_sequence)))
#     for k in range(4):
#         GA_probabilities[k] = n_GAs[k] / np.sum(n_GAs[k])
#
#     # Calculate expected L45 probability
#     l45_base = (LB_base[2] + LB_base[3]) / np.sum(LB_base)
#     l45_pre_base = l45_base - p_lb_l23to45
#     exp_l45_i = (
#         l45_pre_base + (param["HSS"]["P_L45"] - l45_pre_base) / (int_period - 1) * i
#         if i < int_period else param["HSS"]["P_L45"]
#     )
#
#     max_l45_i = Facility_Capacity / np.sum(LB_base)
#     l45_i = min(exp_l45_i, max_l45_i)
#     home_i = (1 - l45_i) * LB_L[0] / (LB_L[0] + LB_L[1])
#     l23_i = 1 - l45_i - home_i
#     l4_l45 = 1 - p_l5_l45
#
#     # Compute number of mothers to move to L4/5
#     move = max(0, l45_i * np.sum(LB_L) - (LB_L[2] + LB_L[3]))
#     denominator = home_i + l23_i
#     if denominator == 0:
#         total_base = LB_L[0] + LB_L[1]
#         home_move = np.floor(move * LB_L[0] / total_base).astype(int)
#         l23_move = move - home_move
#     else:
#         home_move = np.floor(move * home_i / denominator).astype(int)
#         l23_move = move - home_move
#
#     # Initialize counters as NumPy arrays (avoid dictionaries)
#     LB_new = np.zeros(4, dtype=int)
#     risk_new = np.zeros(4, dtype=int)
#     ANC_new = np.zeros(4, dtype=int)
#     Free_referrals = np.zeros(2, dtype=int) + n_free_refer
#     Self_referrals = np.zeros(2, dtype=int) + n_self_refer
#     Elective_CS = np.zeros(2, dtype=int)
#     GA_new = np.zeros((4, len(GA_sequence)), dtype=int)
#
#     # Flags
#     flag_refer = flags["flag_refer"]
#
#     # Simulation Loop (Delivery Events)
#     for k_L in range(3, -1, -1):
#         for _ in range(LB_L[k_L]):
#             i_class = rng.binomial(1, param["class"])
#             i_risk = rng.binomial(1, P_highrisk[k_L])
#             i_ANC = rng.binomial(1, P_ANC[k_L])
#             i_loc = k_L
#             i_free_referral, i_self_referral, i_refer = 0, 0, 0
#             i_elective_CS = rng.binomial(1, P_Elective_CS[i_risk]) if k_L > 1 else 0
#             i_jGA = np.searchsorted(np.cumsum(GA_probabilities[k_L]), rng.random())  # Assign GA index
#
#             # Facility Capacity Constraint
#             if (LB_new[2] + LB_new[3]) >= Facility_Capacity:
#                 i_loc = k_L
#             else:
#                 # Decide delivery location based on risk and ANC status
#                 if i_loc == 0 and home_move > 0:
#                     if flag_refer:
#                         i_refer = rng.binomial(1, track['Referral_Capacity_Track'][i, 0])
#                         i_free_referral = 1 if i_refer else 0
#
#                     if not i_refer and i_class:
#                         i_self_referral = 1
#                         i_refer = 1
#
#                     if i_refer:
#                         i_loc = 2 if rng.random() < l4_l45 else 3
#                         home_move -= 1
#                     else:
#                         i_loc = 0
#
#                 if i_loc == 1 and l23_move > 0:
#                     if flag_refer:
#                         i_refer = rng.binomial(1, track['Referral_Capacity_Track'][i, 0])
#                         i_free_referral = 1 if i_refer else 0
#
#                     if not i_refer and i_class:
#                         i_self_referral = 1
#                         i_refer = 1
#
#                     if i_refer:
#                         i_loc = 2 if rng.random() < l4_l45 else 3
#                         l23_move -= 1
#                     else:
#                         i_loc = 1
#
#             # Update Counters
#             LB_new[i_loc] += 1
#             risk_new[i_loc] += i_risk
#             ANC_new[i_loc] += i_ANC
#             Free_referrals[i_class] += i_free_referral
#             Self_referrals[i_class] += i_self_referral
#             Elective_CS[i_risk] += i_elective_CS
#             GA_new[i_loc, i_jGA] += 1
#
#     return LB_new, risk_new, ANC_new, Free_referrals, Self_referrals, Elective_CS, GA_new

#
# def shifting_live_births(LB_L, n_risk, n_ANC, n_free_refer, n_self_refer, n_elec_CS, n_GAs, param, i, track, flags, int_period, rng):
#
#     P = {}  # dict to restore probabilities
#     n = {}  # dict to restore counts
#
#     #Initialize parameters
#     n["LB_base"] = track["LB_Track"][0]
#     n["Capacity"] = track['Facility_Capacity_Track'][i, 0]
#     P["l45_base"] = (n["LB_base"][2] + n["LB_base"][3]) / np.sum(n["LB_base"])
#     P["highrisk"] = n_risk / LB_L
#     P["ANC"] = n_ANC / LB_L
#     p_elec_cs_lowrisk = n_elec_CS[0] / (np.sum(LB_L[2:]) - np.sum(n_risk[2:]))
#     p_elec_cs_highrisk = n_elec_CS[1] / np.sum(n_risk[2:])
#     P["Elective_CS"] = [p_elec_cs_lowrisk, p_elec_cs_highrisk]
#     n["GA"] = n_GAs
#     P["GA"] = np.zeros((4, len(param['GA_sequence'])))
#     for k in range(4):
#         P["GA"][k] = n["GA"][k] / np.sum(n["GA"][k])   # normalize GA distribution by facility levels
#
#     P["refer"] = track['Referral_Capacity_Track'][i, 0]
#     P["class"] = param["class"]
#     P['p_l5_l45'] = param['p_l5_l45']
#
#     #calculate expected p_l45 at time i - pretransfer
#     P["l45_pre_base"] = P["l45_base"] - param["p_lb_l23to45"]
#     if i < int_period:
#         P["exp_l45_i"] = P["l45_pre_base"] + (param["HSS"]["P_L45"] - P["l45_pre_base"]) / (int_period-1) * i
#     else:
#         P["exp_l45_i"] = param["HSS"]["P_L45"]
#
#     P["max_l45_i"] = n["Capacity"] / np.sum(n["LB_base"])
#     P["l45_i"] = min(P["exp_l45_i"], P["max_l45_i"])
#     P["home_i"] = (1 - P["l45_i"]) * LB_L[0] / (LB_L[0] + LB_L[1])
#     P["l23_i"] = 1 - P["l45_i"] - P["home_i"]
#     P["l4_l45"] = 1 - param['p_l5_l45']
#
#     #calculate the number of mothers need to move to L4/5
#     n["move"] = max(0, P["l45_i"] * np.sum(LB_L) - (LB_L[2] + LB_L[3]))
#     denominator = P["home_i"] + P["l23_i"]
#     if denominator == 0:
#         total_base = LB_L[0] + LB_L[1]
#         n["home_move"] = math.floor(n["move"] * LB_L[0] / total_base)
#         n["l23_move"] = n["move"] - n["home_move"]
#     else:
#         n["home_move"] = math.floor(n["move"] * P["home_i"] / denominator)
#         n["l23_move"] = n["move"] - n["home_move"]
#
#     #Initialize counters
#     n["LB_new"] = np.zeros(4)
#     n["risk_new"] = np.zeros(4)
#     n["ANC_new"] = np.zeros(4)
#     n["Free_referrals"] = np.zeros(2) + n_free_refer
#     n["Self_referrals"] = np.zeros(2) + n_self_refer
#     n["Elective_CS"] = np.zeros(2)
#     n["GA_new"] = np.zeros((4, len(param['GA_sequence'])))  # GA distributions by facility levels
#
#     #Initialize flags
#     flag_refer = flags["flag_refer"]
#
#     #Begin Simulation
#     for k_L in range(3, -1, -1):
#         for k_LB in range(LB_L[k_L]):
#             i_class = rng.binomial(1, P["class"])
#             i_risk = rng.binomial(1, P["highrisk"][k_L])
#             i_ANC = rng.binomial(1, P["ANC"][k_L])
#             i_loc = k_L
#             i_free_referral = 0
#             i_self_referral = 0
#             i_refer = 0
#             i_elective_CS = rng.binomial(1, P["Elective_CS"][i_risk]) if k_L > 1 else 0
#             i_jGA = np.searchsorted(np.cumsum(P["GA"][k_L]), rng.random())  # % actual index of GA
#             i_GA = n["GA"][k_L, i_jGA]  # % actual GA
#
#             if (n["LB_new"][2] + n["LB_new"][3]) >= n["Capacity"]:
#                 i_loc = k_L
#             else:
#                 if i_loc == 0:
#                     if n["home_move"] > 0:
#                         if flag_refer:
#                             i_refer = rng.binomial(1, P["refer"])
#                             i_free_referral = 1 if i_refer else 0
#
#                         if not i_refer:
#                             if i_class:
#                                 i_self_referral = 1
#                                 i_refer = 1
#
#                         if i_refer:
#                             if random.random() < P["l4_l45"]:
#                                 i_loc = 2
#                             else:
#                                 i_loc = 3
#                             n["home_move"] -= 1
#                         else:
#                             i_loc = 0
#                     else:
#                         i_loc = 0
#
#                 if i_loc == 1:
#                     if n["l23_move"] > 0:
#                         if flag_refer:
#                             i_refer = rng.binomial(1, P["refer"])
#                             i_free_referral = 1 if i_refer else 0
#
#                         if not i_refer:
#                             if i_class:
#                                 i_self_referral = 1
#                                 i_refer = 1
#
#                         if i_refer:
#                             if random.random() < P["l4_l45"]:
#                                 i_loc = 2
#                             else:
#                                 i_loc = 3
#                             n["l23_move"] -= 1
#                         else:
#                             i_loc = 1
#                     else:
#                         i_loc = 1
#
#             n["LB_new"][i_loc] += 1
#             n["risk_new"][i_loc] += 1 if i_risk == 1 else 0
#             n["ANC_new"][i_loc] += 1 if i_ANC == 1 else 0
#             n["Free_referrals"][i_class] += i_free_referral
#             n["Self_referrals"][i_class] += i_self_referral
#             n["Elective_CS"][i_risk] += i_elective_CS
#             n["GA_new"][i_loc, i_jGA] += 1
#
#     return n["LB_new"], n["risk_new"], n["ANC_new"], n["Free_referrals"], n["Self_referrals"], n["Elective_CS"], n["GA_new"]
#

