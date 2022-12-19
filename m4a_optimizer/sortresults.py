# -*- coding: utf-8 -*-
import numpy as np
import re

"""
Info
----
This file contains the basic functionalities of the sortResults
class.
"""
def sortResults(cs, cpx_sol, cpx_var):
   
    
    results = {'em': {'P_im':[],
                         'P_ex':[],

                         }, 
               'fleet': {'P_d_nonopt':[],
                         'P_d':[],
                         'E_d_esp':[]},
               
               'bm': {
                      'P_neg':[]},
               }
    
    for key1 in results:
        
        for key2 in results[key1]:
            
            name = key2 + '_' + key1
            mask = [name in var for var in cpx_var]
            
            results[key1][key2] = np.array(cpx_sol)[mask]
            assert len(results[key1][key2]) == cs.nr_timesteps
    
    return results       

    
    
    
    
    
    
    
    
        