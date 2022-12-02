from m4a_classes.models import ancillaryService, VirtualPowerPlant, FleetOperator, electricityMarket
from m4a_optimizer.setCS import setCS
from m4a_optimizer.plotResults import plotResults
from m4a_optimizer.sortresults import sortResults
from pathlib import Path
import os
import pandas as pd
import matplotlib.pyplot as plt

path = Path(os.getcwd()).parent
ancillarydata = os.path.join(path, 'ancillaryservicevalues.xlsx')
servicelist = ['freq_control', 'redispatch']

vpp = VirtualPowerPlant()

service = ancillaryService()
fp = FleetOperator()
em = electricityMarket()
cs = setCS()

#em.dayAheadData2Excel(r"C:\Users\Usuario\Documents\Trabajo\TU Berlin\E-mobility flexiblity potential\mob4anci\data\price_em_year.mat")

#fp.demand2Excel(r"C:\Users\Usuario\Documents\Trabajo\TU Berlin\E-mobility flexiblity potential\mob4anci\data\iLMS2VPP_Depot.mat", 'bus1')



inputs = fp.createFleetObjects()



afrrfile = 'Automatic_Frequency_Restoration_Reserve_202201010000_202201082359' + '.csv'
afrrpath = [os.path.join(path, 'mob4anci', 'data', afrrfile)]

em.setBalancingMarketAttributes()

#em.storeReserveMarketData(afrrpath)


results, fleet, em = fp.setValuesForOptimization()

for res in results:
    i = results.index(res)
    
    cpx_sol = res.solution.get_values()
    cpx_var = res.variables.get_names()
    
    timeseries = sortResults(cs, cpx_sol, cpx_var)
    

    
    plotResults(cs, timeseries, em, fleet)
    

em.setMarketAttributes('price_em')




freqcontrol = service.getFreqcontrolObject()
redispatch = service.getRedispatchObject()
writecols = list(pd.read_excel(path/'outputvalues.xlsx', 'output').columns)[2:] #get columns in which data is to be written in outputvalues. remove 2 initial elements

for service in servicelist:
    
    for key in inputs:
        
        if service == 'freq_control':
            
            checks = fp.compareValues(inputs[key], freqcontrol, service, writecols)
            
        elif service == 'redispatch':
            
            checks = fp.compareValues(inputs[key], redispatch, service, writecols)


