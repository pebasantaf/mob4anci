# -*- coding: utf-8 -*-
"""
Info
----
This file contains the basic functionalities of the plotResults
class.
"""
from ipaddress import collapse_addresses
import matplotlib.pyplot as plt
def plotResults(cs, results, em, fleet):
    """## create electrical power matrices"""
    
    energy_result = []
    
    for i in range(len(results['fleet']['P_d'])):
        
        energy_result += [sum(results['fleet']['P_d'][0:i+1])*fleet['bus1'].chargeefficiency*cs.time_increment] #NEED TO ADD EFFICIENCY AND TIME STEEEEP! 
         
    fig, ax1 = plt.subplots()
    
    ax1.bar(range(cs.nr_timesteps), -results['fleet']['P_d'], label='Fleet demand')
    ax1.bar(range(cs.nr_timesteps), -results['fleet']['P_d_nonopt'], 
            bottom=-results['fleet']['P_d'], label='Non optimized fleet demand')
    ax1.bar(range(cs.nr_timesteps), -results['em']['P_ex'],bottom=-results['fleet']['P_d'] -results['fleet']['P_d_nonopt'],
            label='Market exports')
    
    # Market imports
    
    ax1.bar(range(cs.nr_timesteps), results['bm']['P_neg'], label='Balacing market imports', color='pink')
    ax1.bar(range(cs.nr_timesteps), results['em']['P_im'], bottom=results['bm']['P_neg'], label='Market imports')
    
    #prices
    
    ax2 = ax1.twinx()
    
    ax2.plot(range(cs.nr_timesteps), em.price_em, label='DA market price', color='black', alpha=0.7)
    ax2.plot(range(cs.nr_timesteps), em.price_aFRR_en_neg,'--', label='BM energy price (+)', color='black', alpha=0.7)
    ax2.plot(range(cs.nr_timesteps), em.price_aFRR_cap_neg,':', label='BM capacity price (+)', color='black', alpha=0.7)
    
    
    ax1.set_xlabel('Time (h)')
    ax1.set_ylabel('Power (kW)')
    ax2.set_ylabel('Marke price (€/kWh)')
    ax1.grid()
    
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    
    
    fig2 = plt.figure()
    
    energyesp = []
    
    for i in range(len(results['fleet']['E_d_esp'])):
        
        energyesp += [sum(results['fleet']['E_d_esp'][0:i+1])*fleet['bus1'].chargeefficiency*cs.time_increment]
    
    plt.plot(range(cs.nr_timesteps), fleet['bus1'].E_d_lep, label='E_d_lep')
    plt.plot(range(cs.nr_timesteps), fleet['bus1'].E_d_esp, label='E_d_esp')
    plt.plot(range(cs.nr_timesteps), energy_result, label='E_result')
    #plt.plot(range(len(energyesp)), energyesp, label='Energy esp from results')
    
    plt.legend()
    plt.xlabel('Time (h)')
    plt.ylabel('Energy (kWh)')
    plt.show()
    
    print()