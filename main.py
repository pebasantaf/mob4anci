from m4a_classes.models import ancillaryService, VirtualPowerPlant, FleetOperator
from pathlib import Path
import os
import pandas as pd

def runTool(mode):

    path = Path(os.getcwd()).parent
    
    fp = FleetOperator()
    fleet = fp.createFleetObjects()
    
    if mode == 0: #run optimizer
        
        vpp = VirtualPowerPlant()
        fp.valuesForOptimization()

    
    elif mode == 1: #run checker
        
        servicelist = ['freq_control', 'redispatch']

        service = ancillaryService()


        freqcontrol = service.getFreqcontrolObject()
        redispatch = service.getRedispatchObject()
        writecols = list(pd.read_excel(path/'outputvalues.xlsx', 'output').columns)[2:] #get columns in which data is to be written in outputvalues. remove 2 initial elements

        for servicetype in servicelist:
            
            for key in fleet:
                
                if servicetype == 'freq_control':
                    
                    checks = fp.compareValues(fleet[key], freqcontrol, servicetype, writecols)
                    
                elif servicetype == 'redispatch':
                    
                    checks = fp.compareValues(fleet[key], redispatch, servicetype, writecols)
    
    return checks

if __name__ == '__main__':

    tool = runTool(0)

