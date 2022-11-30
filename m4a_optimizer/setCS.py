# -*- coding: utf-8 -*-
"""
Created on Thu Feb 24 14:38:38 2022

@author: 47907
"""
import os
import sys
sys.path.append("..")

class setCS():
    def  __init__(
        self,
       time_increment = None,
        nr_timesteps = None,
        ghg_CO2 = None,
        include_penalty = None,
        penalty_factor = None,
        file_directionary = None,
    ):

        # -------------
        # NOTE: 
        
        # time increment (h)
        self.time_increment = 1; # (h)
        
        # number of time steps
        self.nr_timesteps = 7*24;
        
        # objective function
        # (1 - cost optimized, 2 - CO2 optimized)
        self.objective_function = 1;
        
        # include penalty factor (only for CO2 optimization)
        # (1 - yes, 0 - no)
        self.include_penalty = 1;
        self.penalty_factor = 0.001;
        



        self.file_directionary  = os.getcwd()
