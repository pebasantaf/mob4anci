import csv
import numpy as np
import sys
sys.path.append("..")
from setCS import setCS

### SUPER CLASS: super class virtual power plant that will contain the fleet and market classes

class Vpp_base(object):
    def __init__(self,
                 P_g_max=None,
                 P_g_min=None,
                 ghg_CO2=None,
                 cost=None,
                 ):
        
        

        
        # max. generation (kW)
        self.P_g_max = P_g_max;

        # min. generaton (kW)
        self.P_g_min = P_g_min;
        
        # variable generation cost (EUR/kWh)
        self.cost = 0.5*0.09;

        #greenhouse gas emissions (gCO2/kWh)
        self.ghg_CO2 = ghg_CO2
        
    def printcost(self):
        print(self.cost)
        
       
    # get photovoltaic, household and industrial load power profiles    
    def powerread(self,profilename):
        CSset =setCS()
        limittime = CSset.nr_timesteps
        power = []
        current_directionary = CSset.file_directionary 
        file_directionary = current_directionary + '\\' + 'profiles'+'\\'+profilename
        with open(file_directionary) as csvfile:

            reader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC) # change contents to floats

            for row in reader: # each row is a list

                power.append(row)

        return np.array(power[:limittime])
    
    # get electric vehicle fleet flexibility profiles
    def fleetread(self,profilename):
        CSset =setCS()
        limittime = CSset.nr_timesteps
        E_sum = []
        E_dep = []       
        E_arr = []     
        P_max = []     
        P_notOpt = []    
        current_directionary = CSset.file_directionary
        file_directionary = current_directionary + '\\' + 'profiles'+'\\'+profilename
        with open(file_directionary) as csvfile:

            reader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC) # change contents to floats
            
            for row in reader: # each row is a list                   
                    E_sum.append(row[0])      
                    E_dep.append(row[1])
                    E_arr.append(row[2])
                    P_max.append(row[3])
                    P_notOpt.append(row[4])
        return E_sum[:limittime] ,E_dep[:limittime], E_arr[:limittime], P_max[:limittime] , P_notOpt[:limittime]
    # get energy market price profiles
    def priceread(self,profilename):
         CSset =setCS()
         limittime = CSset.nr_timesteps
         price = []
         current_directionary = CSset.file_directionary
         file_directionary = current_directionary + '\\' + 'profiles'+'\\'+profilename
         with open(file_directionary) as csvfile:

             reader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC) # change contents to floats

             for row in reader: # each row is a list

                 price.append(row)

         return price[:limittime]   


### SUBCLASSES


class fleetAttributes(Vpp_base):
    def __init__(
        self,
        eff = None, 
        cost = None,
        ghg_CO2 = None,
        nr_vehicles = None,
        E_d_esp = None, 
        E_d_lep = None,      
        E_d_flex = None,    
        P_d_max = None,   
        P_d_nonopt = None, 
    ):
        
        # Call to super class
        super(fleetAttributes, self).__init__(
             ghg_CO2, cost
            )
        """
        Info
        ----
        This class provides a model with the basic attributes of a
        electric vehicle fleet flexibilities.
        """

        # efficiency (p.u.)
        self.eff = 0.9;
        
        # variable discharging/charging cost (EUR/kWh)
        self.cost = 0.10;
         
        # greenhouse gas emissions (gCO2/kWh)
        self.ghg_CO2 = 0.001;
        
        # number of vehicles in fleet
        # NOTE: This attribute is not required in the code as the flexibility
        # profiles already contain the total energy demand. This is just FYI. 
        self.nr_vehicles = 185; 
        self.E_d_esp , self.E_d_lep, self.E_d_flex, self.P_d_max , self.P_d_nonopt = self.fleetread("flex_fleet.csv")
        
        
class emAttributes(Vpp_base):
    def __init__(
        self,
        P_im_min = None,
        P_im_max = None,
        P_ex_min = None,
        P_ex_max = None,
        ghg_CO2_IM = None,
        ghg_CO2_EX = None,
        price_em = None
    ):
        
        # Call to super class
        super(emAttributes, self).__init__(
            )
        """
        Info
        ----
        This class provides a model with the basic attributes of a
        energy market.
        """
        # min. power import (kW)
        self.P_im_min = 0;
        
        # max. power import (kW)
        self.P_im_max = 1000000;
        
        # min. power export (kW)
        self.P_ex_min = 0;
        
        # max. power export (kW)
        self.P_ex_max = 1000000;
        
        # greenhouse gas emissions for market import (gCO2/kWh)
        self.ghg_CO2_IM = 559;
        
        # greenhouse gas emissions for market export (gCO2/kWh)
        self.ghg_CO2_EX = 0.001;

        self.price_em =  self.priceread('price_em.csv')