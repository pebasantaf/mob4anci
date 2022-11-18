import numpy as np


def writeLPem(filedirectory, cs, em):
    tstep = np.array(range(1,cs.nr_timesteps+1))
    """ objective variables"""

    # open temporary optimization file for objective function
    with open(filedirectory['obj'],'a') as f:
    # check objective function
        if (cs.objective_function==1): # cost optimization
        
            # write optimization variable into file for each time step

            for i in range(cs.nr_timesteps):
                cost = em.price_em[i]   #removed [0] as shape is different in my case
                f.write("+ {:g} P_im_em~{} - {:g} P_ex_em~{}\n".format
                    (cost*cs.time_increment, tstep[i], cost*cs.time_increment, tstep[i]))
            
        elif (cs.objective_function==2): # CO2 optimization
           
            # check if penalty factor is activated
            if (cs.include_penalty==1):
                emission_export = em.ghg_CO2_EX + cs.penalty_factor
            else:
                emission_export = em.ghg_CO2_EX

            
            # write optimization variable into file for each time step
            emission_import = em.ghg_CO2_IM
            for i in range(cs.nr_timesteps):       
                f.write("+ {:g} P_im_em~{} + {:g} P_ex_em~{}\n".format
                    (emission_import*cs.time_increment, tstep[i] ,emission_export*cs.time_increment, tstep[i]))
 
        # close temporary optimization file 
        f.close()
    """ constraints"""
    
    # open temporary optimization file for constraints
    with open(filedirectory['cons'],'a') as f:
    
    # write constraints for operation modes (equations 3.19, 3.20, 3.21 and 3.22)
        P_im_min = em.P_im_min
        for i in range(cs.nr_timesteps):
            f.write("{:g} y_em~{} - P_im_em~{} <= 0\n".format #import power negative or bigger than min
            (P_im_min, tstep[i], tstep[i]))
        P_im_max = em.P_im_max
        for i in range(cs.nr_timesteps):
            f.write(" P_im_em~{} - {:g} y_em~{} <= 0\n".format #import power negative or smaller than max
        (tstep[i], P_im_max, tstep[i]))
        P_ex_min = em.P_ex_min
        for i in range(cs.nr_timesteps):
            f.write("{:g} y_em~{} + P_ex_em~{} >= {:g}\n".format
            (P_ex_min ,tstep[i], tstep[i] ,P_ex_min))        
        P_ex_max = em.P_ex_max
        for i in range(cs.nr_timesteps):
            f.write(" {:g} y_em~{}  + P_ex_em~{} <= {:g}\n".format
            (P_ex_max ,tstep[i], tstep[i], P_ex_max))
        

        # close temporary optimization file 
        f.close()
    """ boundaries"""
    
    # open temporary optimization file for boundary conditions
    with open(filedirectory['bounds'],'a') as f:
    
    # write boundary conditions for market imports into file for each time step
        lb = em.P_im_min
        ub = em.P_im_max
        for i in range(cs.nr_timesteps):
            f.write("{:g} <= P_im_em~{} <= {:g}\n".format( lb ,tstep[i] ,ub))
        
        # write boundary conditions for market exports into file for each time step
        lb = em.P_ex_min
        ub = em.P_ex_max
        for i in range(cs.nr_timesteps):
            f.write("{:g} <= P_ex_em~{} <= {:g}\n".format( lb, tstep[i] ,ub))
        
        # close temporary optimization file 
        f.close()
    
    """ binaries"""
    
    # open temporary optimization file for binaries according to slide 45
    with open(filedirectory['binaries'],'a') as f:
    
        # write binary into file for each time step
        for i in range(cs.nr_timesteps):
            f.write("y_em~{}\n".format(tstep[i]))
        
        # close temporary optimization file 
        f.close()


def writeLPbm(filedirectory, cs, em):
    
    tstep = np.array(range(1,cs.nr_timesteps+1))
    
    # objective variables
    
    # ENERGY
    with open(filedirectory['obj'],'a') as f:
        
        if (cs.objective_function==1): # cost optimization
        
            # write optimization variable into file for each time step
            
            for i in range(cs.nr_timesteps):
                cost_pos = em.price_aFRR_en_pos[i]  
                cost_neg = em.price_aFRR_en_neg[i]
                f.write(" {0:+g} P_pos_bm~{1:}  {2:+g} P_neg_bm~{3:} \n".format
                        (-cost_pos*cs.time_increment, tstep[i] ,-cost_neg*cs.time_increment ,tstep[i])) 
                
                #NOTE: the power is positive an the cost is negative. But we set the minus already in the formula and not in the cost because else we write -+ [number], as we are writing a 
                #string and + and - wont get multiplied
                

            f.close()   
            
    # POWER
    
    with open(filedirectory['obj'],'a') as f:
           
        if (cs.objective_function==1):
            
            for i in range(int(cs.nr_timesteps/4)):
                
                cost_pos = em.price_aFRR_cap_pos[i*4]
                cost_neg = em.price_aFRR_cap_neg[i*4]
                
                f.write(" {0:+g} P_block{1:}_pos_bm  {2:+g} P_block{3:}_neg_bm)\n".format
                        (-cost_pos, tstep[i*4] ,-cost_neg ,tstep[i*4]))
            
            f.close()
            
        
    #constrains
    
    with open(filedirectory['cons'],'a') as f:
        
        # here we must limit the power P_xx_bm to the power of the block, so this power is the same in all the periods
        for i in range(cs.nr_timesteps):
            
            if i%4 == 0:
            
                j = i
            
            f.write("P_pos_bm~{} - P_block{}_pos_bm = 0\n".format #power at a certain time step is equal by the power at that block
                    (tstep[i], tstep[j]))
            
        f.close()
        
    with open(filedirectory['cons'],'a') as f:
        
        # here we must limit the power P_xx_bm to the power of the block, so this power is the same in all the periods
        for i in range(cs.nr_timesteps):
            
            if i%4 == 0:
            
                j = i
            
            f.write("P_neg_bm~{} - P_block{}_neg_bm = 0\n".format #power at a certain time step is equal by the power at that block
                    (tstep[i], tstep[j]))
            
        f.close()
    
        
def writeLPfleet(filedirectory, cs, fleet):
    tstep = np.array(range(1,cs.nr_timesteps+1))
    """objective variables"""
    
    # open temporary optimization file for objective function
    with open(filedirectory['obj'],'a') as f:
    
    # check objective function
        if (cs.objective_function==1): # cost optimization
        
            # write optimization variable into file for each time step
            cost = fleet.cost
            for i in range(cs.nr_timesteps):
                f.write("- {:g} P_d_fleet~{} - {:g} P_d_nonopt_fleet~{} \n".format
                    (cost*cs.time_increment, tstep[i] ,cost*cs.time_increment ,tstep[i]))
            
        elif (cs.objective_function==2): # CO2 optimization
            
            # write optimization variable into file for each time step
            emission = fleet.ghg_CO2
            for i in range(cs.nr_timesteps):
                f.write("+ {:g} P_d_fleet~{} + {:g} P_d_nonopt_fleet~{} \n\n".format
                    (emission*cs.time_increment, tstep[i], emission*cs.time_increment, tstep[i]))
            
        # close temporary optimization file 
        f.close()
        
    """ constraints"""
    
    # open temporary optimization file for constraints
    with open(filedirectory['cons'],'a') as f:
    
        # get vectors for time increment, time steps and efficiency
        tincr =cs.time_increment
        eff = fleet.chargeefficiency
        
        # write non optimized charging power constraint (equation 7.06)
        for i in range(cs.nr_timesteps):
            f.write("P_d_nonopt_fleet~{} = {:g}\n".format(tstep[i], fleet.P_d_nonopt[i]))
        
        # write initial condition for cumulated max. coverable energy demand
        f.write("E_d_esp_fleet~1 = {:g}\n".format(fleet.E_d_esp[0]))
        
        # iterate time steps of optimization period in order to write 
        # constraint of continous recalculation of cumulated max. 
        # coverable energy demand (equation 7.08)
        P_d_esp_string = ''
        for k in range(1,cs.nr_timesteps):
            
            # expand string
            P_d_esp_string = P_d_esp_string + "+ {:g} P_d_fleet~{} ".format(cs.time_increment * eff, k)
            
            # write constraint into file
            f.write("E_d_esp_fleet~{} ".format(k+1) +  P_d_esp_string +"= {:g}\n".format (fleet.E_d_esp[k]))
                
    
        # write constraint for upper limit of cumulated max. 
        # coverable energy demand (equation 7.09)
        for i in range(cs.nr_timesteps):
            f.write("{:g} P_d_fleet~{} - E_d_esp_fleet~{} <= 0\n".format
            (tincr*eff ,tstep[i], tstep[i]))
        
        # iterate time steps of optimization period in order to 
        # write constraint of latest possible energy demand for 
        # every time step (equation 7.10)
        P_d_lep_string = ''
        for k in range(cs.nr_timesteps):
            if (k==0):
                P_d_lep_string = P_d_lep_string + "{:g} P_d_fleet~{} ".format(cs.time_increment*eff ,k+1)
            else:
                P_d_lep_string = P_d_lep_string + "+ {:g} P_d_fleet~{} ".format(cs.time_increment*eff ,k+1)

           
            # write constraint into file
            f.write(P_d_lep_string + ">= {:g}\n".format(fleet.E_d_lep[k]))

        
    # write time frame constraint (equation 7.11)
        for i in range(cs.nr_timesteps):
            f.write("{:g} P_d_fleet~{} <= {:g}\n".format(tincr*eff, tstep[i], fleet.E_d_flex[i]))
        
        # close temporary optimization file 
        f.close()
    """ boundaries"""
    
    # open temporary optimization file for boundary conditions
    with open(filedirectory['bounds'],'a') as f:
    
    # write boundary conditions for optimized power demand into file (equation# 7.07)

        lb = 0
        ub = fleet.P_d_max
        for i in range(cs.nr_timesteps):
            f.write("{:g} <= P_d_fleet~{} + P_pos_bm~{} + P_neg_bm~{} <= {:g}\n".format(lb ,tstep[i], tstep[i], tstep[i], ub[i]))
        
       
        # close temporary optimization file 
        f.close()
    """binaries"""
    
    # --> NO BINARIES




def writeLPadd(filedirectory, cs):


    tstep = np.array(range(1,cs.nr_timesteps+1))
    """ power equilibrium constraints"""
     
    # open temporary optimization file for constraints
    with open(filedirectory['cons'],'a') as f:
    
    # write power equilibrium constraint into file for each time step
        power_eqa ='P_im_em~{} - P_ex_em~{} - P_d_fleet~{} - P_neg_bm~{} + P_pos_bm~{} = 0\n'
        for i in range(cs.nr_timesteps):
            f.write( power_eqa.format(tstep[i], tstep[i], tstep[i], tstep[i] ,tstep[i] ,tstep[i] ,tstep[i] ,tstep[i] ,tstep[i] ,tstep[i] ,tstep[i] ,tstep[i]))

        '''        # write EnFluRi constraint (equation 3.24)
        for i in range(cs.nr_timesteps):
            f.write( "y_bat~{} + y_em~{} =1\n".format(tstep[i] ,tstep[i]))
        # close temporary optimization file
        
        '''
        f.close()
