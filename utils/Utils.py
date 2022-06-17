import os
import m4a_functions.readwritefunctions as rw
import m4a_functions.processfunctions as prc
from pathlib import Path
import pandas as pd


def updateListofLists(list,value,index,pos):

    # one index for each freq_control product and one pos for each check
    if index == 0:

        list[pos] = [value]

    elif index > 0:

        list[pos] +=[value]

    return list


def runTool():

    servicelist = ['freq_control', 'redispatch']

    
    for service in servicelist:
    
        path = Path(os.getcwd()).parent

        input = rw.readInput(path/'inputvalues.xlsx')
        
        writecols = list(pd.read_excel(path/'outputvalues.xlsx', 'output').columns)[2:] #get columns in which data is to be written in outputvalues. remove 2 initial elements

        ancillarydata = rw.readAnService(path/'ancillaryservicevalues.xlsx', service)

        for i in range(len(input)):
        
            checks = prc.compareValues(input[i], ancillarydata, service, writecols)

            rw.writeOutput(path/'outputvalues.xlsx', input[i].id, service, checks)