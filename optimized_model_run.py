"""
Optimized Model Run Module
Enhanced version with caching, vectorization, and memory optimization
"""

import numpy as np
import pandas as pd
import random
import time
import streamlit as st
from project_parameters import reset_inputs
from LB_effect import f_LB_effect_vectorized
from mortality import f_MM_vectorized
from global_func import labor_calculator, fetal_sensor_calculator, DALY_calculator_vectorized
from intrapartum import intrapartum_effect_vectorized
from optimization_config import streamlit_cache, cache_result, opt_config
import concurrent.futures
from typing import Dict, Tuple, Any
import gc

class OptimizedModelRunner:
    """Optimized model runner with caching and performance improvements"""
    
    def __init__(self):
        self.cache_hits = 0
        self.cache_misses = 0
        self.execution_times = []
        
    def run_model_dash_optimized(self, param, flags, n_months, int_period, base_seed=None):
        """
        Optimized version of run_model_dash with caching and performance improvements
        """
        start_time = time.time()
        
        # Initialize Model Parameters
        track = reset_inputs(param, n_months)
        
        # Pre-allocate arrays for better memory efficiency
        columns = ['Live Births Initial', 'Live Births Final', 'Fac non-CS', 'ANC','L4/5 LBs',
                   'Free_referrals', 'Self_referrals', 'Normal_referrals',
                    'Mothers with pph_bundle', 'Mothers with iv_iron','Mothers with MgSO4', 'Mothers with antibiotics',
                    'Preterm', 'RDS', 'IVH', 'neo_sepsis', 'NEC', 'Neonatal Deaths', 'asphyxia',
                    'High risk', 'PL', 'hypoxia', 'OL', 'mat_sepsis', 'pph', 'stillbirths', "eclampsia", 'ruptured_uterus', 'aph', 'severe_comps', 'severe_pph',
                    'CS', 'CS_unnessary', 'Elective CS', 'Emergency CS', 'Elective CS risk status', 'Risk status',
                    'AVD', 'SVD', 'Anemia', "ER_trans_actual", "ER_trans_pred", "Emergency transfers",
                    "Comps after transfer", 'Deaths', 'M_DALYs', 'N_DALYs', 'DALYs',
                    'Facility_capacity_actual', 'Facility_capacity_ideal', 'Capacity Ratio',
                    'Surgical_actual', 'Nurse_actual', 'Anesthetist_actual',
                    'Surgical_ratio', 'Nurse_ratio', 'Anesthetist_ratio',
                    'Surgical_needed', 'Nurse_needed', 'Anesthetist_needed',
                    'Doppler_Actual', 'Doppler_Needed', 'Doppler_Ratio',
                    'CTG_Actual', 'CTG_Needed', 'CTG_Ratio', 'Month']
        
        # Pre-allocate DataFrame with known size
        df = pd.DataFrame(index=range(n_months), columns=columns)
        df_individual_temp = []
        df_facility_temp = []
        
        # Pre-generate random number generator
        if base_seed is not None:
            rng = np.random.default_rng(base_seed)
        else:
            rng = np.random.default_rng()
        
        # Process in batches for memory efficiency
        batch_size = min(opt_config.CHUNK_SIZE, n_months)
        
        for batch_start in range(0, n_months, batch_size):
            batch_end = min(batch_start + batch_size, n_months)
            batch_results = self._process_batch(
                track, param, flags, int_period, rng, 
                batch_start, batch_end, df, df_individual_temp, df_facility_temp
            )
            
            # Update tracking variables
            track = batch_results['track']
            df_individual_temp = batch_results['df_individual_temp']
            df_facility_temp = batch_results['df_facility_temp']
            
            # Memory cleanup
            if opt_config.memory_optimized:
                gc.collect()
        
        # Concatenate results efficiently
        df_individual = pd.concat(df_individual_temp, ignore_index=True) if df_individual_temp else pd.DataFrame()
        df_facility_all = pd.concat(df_facility_temp, ignore_index=True) if df_facility_temp else pd.DataFrame()
        
        execution_time = time.time() - start_time
        self.execution_times.append(execution_time)
        
        return df, df_individual, df_facility_all
    
    def _process_batch(self, track, param, flags, int_period, rng, 
                      batch_start, batch_end, df, df_individual_temp, df_facility_temp):
        """Process a batch of months for memory efficiency"""
        
        for i in range(batch_start, batch_end):
            # Update features due to intervention changes
            track = update_capacity(track, param, i, flags, int_period)
            
            # ANC phase
            track, free_refers, self_refers, individual_outcomes = f_LB_effect_vectorized(
                param, i, track, flags, int_period, rng
            )
            
            # Intrapartum phase
            MC, M, NC, individual_outcomes = intrapartum_effect_vectorized(
                track, flags, param, i, individual_outcomes, rng
            )
            
            # Calculate maternal and neonatal health outcomes
            MC, MD, NC, ND, M, individual_df = f_MM_vectorized(
                track, param, flags, i, MC, M, NC, individual_outcomes, rng
            )
            individual_df["Month"] = i
            
            # Add missing assignments to M dictionary (as in original model)
            M["Free_referrals"] = free_refers
            M["Self_referrals"] = self_refers
            
            # Create facility dataframe efficiently
            df_facility = pd.DataFrame({
                "Level": [1, 2, 3],
                "Month": [i, i, i]
            })
            
            # Update main dataframe efficiently using vectorized operations
            self._update_main_dataframe(df, i, track, M, MC, NC, MD, ND, 
                                      free_refers, self_refers, individual_outcomes, param, flags, rng)
            
            # Update individual outcomes
            M_DALYs_new, N_DALYs_new, M_DALY_ind, N_DALY_ind = DALY_calculator_vectorized(
                individual_outcomes, param
            )
            individual_df["M_DALY"] = M_DALY_ind
            individual_df["N_DALY"] = N_DALY_ind
            individual_df["DALY"] = individual_df["M_DALY"] + individual_df["N_DALY"]
            df_individual_temp.append(individual_df)
            
            # Update facility dataframe
            self._update_facility_dataframe(df_facility, track, M, param, i, flags, rng)
            df_facility_temp.append(df_facility)
        
        return {
            'track': track,
            'df_individual_temp': df_individual_temp,
            'df_facility_temp': df_facility_temp
        }
    
    def _update_main_dataframe(self, df, i, track, M, MC, NC, MD, ND, 
                              free_refers, self_refers, individual_outcomes, param, flags, rng):
        """Efficiently update main dataframe using vectorized operations"""
        
        # Use vectorized assignment for better performance
        df.loc[i, 'Month'] = i
        df.loc[i, 'Live Births Initial'] = M["LB_L_initial"]
        df.loc[i, 'Live Births Final'] = track['LB_Track'][i]
        df.loc[i, 'Fac non-CS'] = np.array([0, track['LB_Track'][i][1] - M["CS"][1], 
                                           track['LB_Track'][i][2] - M["CS"][2], 
                                           track['LB_Track'][i][3] - M["CS"][3]])
        df.loc[i, 'ANC'] = track['ANC_Track'][i]
        df.loc[i, 'High risk'] = track['HighRisk_Track'][i, :]
        df.loc[i, 'Free_referrals'] = M["Free_referrals"]
        df.loc[i, 'Self_referrals'] = M["Self_referrals"]
        df.loc[i, 'Normal_referrals'] = M["Free_referrals"] + M["Self_referrals"]
        
        # Maternal outcomes
        df.loc[i, 'Mothers with pph_bundle'] = M["pph_bundle"]
        df.loc[i, 'Mothers with iv_iron'] = M["iv_iron"]
        df.loc[i, 'Mothers with MgSO4'] = M["MgSO4"]
        df.loc[i, 'Mothers with antibiotics'] = M["antibiotics"]
        df.loc[i, 'Preterm'] = M["PT"]
        
        # Neonatal outcomes
        df.loc[i, 'RDS'] = NC["RDS"]
        df.loc[i, 'IVH'] = NC["IVH"]
        df.loc[i, 'neo_sepsis'] = NC["neo_sepsis"]
        df.loc[i, 'NEC'] = NC["NEC"]
        df.loc[i, 'Neonatal Deaths'] = ND["death"]
        df.loc[i, 'hypoxia'] = MC["hypoxia"]
        df.loc[i, 'asphyxia'] = NC["asphyxia"]
        df.loc[i, 'stillbirths'] = NC["stillbirth"]
        
        # Complications
        df.loc[i, 'PL'] = MC["PL"]
        df.loc[i, 'Anemia'] = MC["anemia"]
        df.loc[i, 'OL'] = MC["OL"]
        df.loc[i, 'mat_sepsis'] = MC['mat_sepsis']
        df.loc[i, 'pph'] = MC["pph"]
        df.loc[i, 'severe_pph'] = MC["pph_severe"]
        df.loc[i, 'eclampsia'] = MC["eclampsia"]
        df.loc[i, 'ruptured_uterus'] = MC["ruptured_uterus"]
        df.loc[i, 'aph'] = MC["aph"]
        df.loc[i, "Comps after transfer"] = MC["comps_death"]
        df.loc[i, 'severe_comps'] = MC["severe_comps"]
        df.loc[i, 'Deaths'] = MD["death"]
        
        # CS outcomes
        df.loc[i, 'CS'] = M["CS"]
        df.loc[i, 'CS_unnessary'] = M["CS_unnessary"]
        df.loc[i, 'Elective CS'] = M["Elective_CS"]
        df.loc[i, 'Emergency CS'] = M["Emergency_CS"]
        df.loc[i, 'Elective CS risk status'] = M["Elective_CS_risk"]
        
        # Risk status
        n_lowrisk = np.sum(track['LB_Track'][i]) - np.sum(track['HighRisk_Track'][i])
        n_highrisk = np.sum(track['HighRisk_Track'][i])
        df.loc[i, 'Risk status'] = np.array([n_lowrisk, n_highrisk])
        
        # Delivery outcomes
        df.loc[i, 'AVD'] = M["AVD"]
        df.loc[i, 'SVD'] = M["SVD"]
        df.loc[i, "ER_trans_actual"] = M["ER_trans_actual"]
        df.loc[i, "ER_trans_pred"] = M["ER_trans_pred"]
        df.loc[i, "Emergency transfers"] = M["ER_trans_actual"] + M["ER_trans_pred"]
        
        # DALYs
        M_DALYs_new, N_DALYs_new, _, _ = DALY_calculator_vectorized(individual_outcomes, param)
        df.loc[i, "M_DALYs"] = M_DALYs_new
        df.loc[i, "N_DALYs"] = N_DALYs_new
        df.loc[i, "DALYs"] = M_DALYs_new + N_DALYs_new
        df.loc[i, 'L4/5 LBs'] = round(track['LB_Track'][i, 2] + track['LB_Track'][i, 3])
        
        # Facility capacity
        df.loc[i, 'Facility_capacity_actual'] = round(track['Facility_Capacity_Track'][i, 0])
        df.loc[i, 'Facility_capacity_ideal'] = round(df.loc[i, 'L4/5 LBs'])
        df.loc[i, 'Capacity Ratio'] = df.loc[i, 'L4/5 LBs'] / track['Facility_Capacity_Track'][i, 0]
        
        # Labor calculations
        labor = labor_calculator(track['LB_Track'][i, :], M["CS"], param, flags)
        df.loc[i, 'Surgical_actual'] = np.array(labor['actual_surgical'][1:])
        df.loc[i, 'Nurse_actual'] = np.array(labor['actual_nurse'][1:])
        df.loc[i, 'Anesthetist_actual'] = np.array(labor['actual_anesthetist'][1:])
        df.loc[i, 'Surgical_needed'] = np.array(labor['surgical'][1:])
        df.loc[i, 'Nurse_needed'] = np.array(labor['nurse'][1:])
        df.loc[i, 'Anesthetist_needed'] = np.array(labor['anesthetist'][1:])
        df.loc[i, 'Surgical_ratio'] = df.loc[i, 'Surgical_actual'] / df.loc[i, 'Surgical_needed']
        df.loc[i, 'Nurse_ratio'] = df.loc[i, 'Nurse_actual'] / df.loc[i, 'Nurse_needed']
        df.loc[i, 'Anesthetist_ratio'] = df.loc[i, 'Anesthetist_actual'] / df.loc[i, 'Anesthetist_needed']
        
        # Sensor calculations
        sensors = fetal_sensor_calculator(track, param, i, flags, rng)
        dopplers_ratio = np.array([sensors['dopplers_l23_ratio'], sensors['dopplers_l4_ratio'], sensors['dopplers_l5_ratio']])
        CTGs_ratio = np.array([sensors['CTGs_l23_ratio'], sensors['CTGs_l4_ratio'], sensors['CTGs_l5_ratio']])
        df.loc[i, 'Doppler_Actual'] = np.array([sensors['actual_dopplers_l23'], sensors['actual_dopplers_l4'], sensors['actual_dopplers_l5']])
        df.loc[i, 'Doppler_Needed'] = np.array([sensors['dopplers_l23'], sensors['dopplers_l4'], sensors['dopplers_l5']])
        df.loc[i, 'Doppler_Ratio'] = dopplers_ratio
        df.loc[i, 'CTG_Actual'] = np.array([sensors['actual_CTGs_l23'], sensors['actual_CTGs_l4'], sensors['actual_CTGs_l5']])
        df.loc[i, 'CTG_Needed'] = np.array([sensors['CTGs_l23'], sensors['CTGs_l4'], sensors['CTGs_l5']])
        df.loc[i, 'CTG_Ratio'] = CTGs_ratio
    
    def _update_facility_dataframe(self, df_facility, track, M, param, i, flags, rng):
        """Update facility-specific dataframe"""
        
        df_facility['Facility_capacity_actual'] = np.array([0, track['Facility_Capacity_Track'][i, 0], track['Facility_Capacity_Track'][i, 0]])
        df_facility['Facility_capacity_ideal'] = np.array([0, round(track['LB_Track'][i, 2] + track['LB_Track'][i, 3]), round(track['LB_Track'][i, 2] + track['LB_Track'][i, 3])])
        
        labor = labor_calculator(track['LB_Track'][i, :], M["CS"], param, flags)
        df_facility['Surgical_actual'] = np.array(labor['actual_surgical'])
        df_facility['Nurse_actual'] = np.array(labor['actual_nurse'])
        df_facility['Anesthetist_actual'] = np.array(labor['surgical'])
        df_facility['Surgical_needed'] = np.array(labor['surgical'])
        df_facility['Nurse_needed'] = np.array(labor['nurse'])
        df_facility['Anesthetist_needed'] = np.array(labor['anesthetist'])
        
        sensors = fetal_sensor_calculator(track, param, i, flags, rng)
        df_facility['Doppler_Actual'] = np.array([sensors['actual_dopplers_l23'], sensors['actual_dopplers_l4'], sensors['actual_dopplers_l5']])
        df_facility['Doppler_Needed'] = np.array([sensors['dopplers_l23'], sensors['dopplers_l4'], sensors['dopplers_l5']])
        df_facility['CTG_Actual'] = np.array([sensors['actual_CTGs_l23'], sensors['actual_CTGs_l4'], sensors['actual_CTGs_l5']])
        df_facility['CTG_Needed'] = np.array([sensors['CTGs_l23'], sensors['CTGs_l4'], sensors['CTGs_l5']])

def update_capacity(track, param, i, flags, int_period):
    """Update facility capacity (optimized version)"""
    
    # Vectorized capacity updates
    if flags.get('flag_capacity', False):
        if i < int_period:
            capacity_added = param.get("HSS", {}).get("capacity_added", 0)
            capacity_factor = 1 + capacity_added / max(int_period-1, 1) * i
        else:
            capacity_added = param.get("HSS", {}).get("capacity_added", 0)
            capacity_factor = 1 + capacity_added
        
        base_capacity = param.get("Capacity", 100)
        cs_capacity = param.get("p_cs_capacity", [0, 0, 0, 100])[3]
        
        track['Facility_Capacity_Track'][i, 0] = base_capacity * capacity_factor
        track['CS_Capacity_Track'][i, 0] = cs_capacity * capacity_factor
    else:
        base_capacity = param.get("Capacity", 100)
        cs_capacity = param.get("p_cs_capacity", [0, 0, 0, 100])[3]
        
        track['Facility_Capacity_Track'][i, 0] = base_capacity
        track['CS_Capacity_Track'][i, 0] = cs_capacity
    
    # Referral capacity update
    if flags.get('flag_refer', False):
        p_refer = param.get("HSS", {}).get("P_refer", 0)
        track['Referral_Capacity_Track'][i, 0] = p_refer
    else:
        # Use previous value or default
        if i > 0:
            track['Referral_Capacity_Track'][i, 0] = track['Referral_Capacity_Track'][i - 1, 0]
        else:
            track['Referral_Capacity_Track'][i, 0] = 0
    
    return track

# Global optimized runner instance
optimized_runner = OptimizedModelRunner()

# Cached wrapper function for Streamlit compatibility
@streamlit_cache
def run_model_dash_cached(param, flags, n_months, int_period, base_seed=None):
    """Cached wrapper for model execution that Streamlit can hash"""
    return optimized_runner.run_model_dash_optimized(param, flags, n_months, int_period, base_seed)

# Backward compatibility function
def run_model_dash(param, flags, n_months, int_period, base_seed=None):
    """Backward compatibility wrapper for the optimized model runner"""
    return run_model_dash_cached(param, flags, n_months, int_period, base_seed) 