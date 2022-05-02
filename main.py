from m4a_functions.readwritefunctions import *
from m4a_functions.processfunctions import *
import os
from pathlib import Path

if __name__ == '__main__':

    servicelist = ['freq_control', 'redispatch']
    service = servicelist[0] 
    
    
    path = Path(os.getcwd()).parent

    input = readInput(path/'inputvalues.xlsx')

    ancillarydata = readAnService(path/'ancillaryservicevalues.xlsx', service)

    checks = compareValues(input, ancillarydata, service, weeksection="hol", timeslice=2)

    writeOutput(path/'outputvalues.xlsx', input.id, service, checks)

