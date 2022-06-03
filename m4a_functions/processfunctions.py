import statistics
from m4a_functions.readwritefunctions import *
from m4a_functions.processfunctions import *
import os
from pathlib import Path

def compareValues(inputdata, servicedata, servicetype, writecols,**kwargs):

    checks = [['-']]*12
    

    # updating inputdata considering negative/positive power balancing

    if servicetype == 'freq_control':
        
        # 4 hours each participation window for frequency control
        windowtime = 4
        
        limres = False

        # for every of the three frequency reserve products

        for index,row in servicedata.iterrows(): 
            
            realpower = inputdata.getRealValue('power',row['reservetype'],True)
            
            # get the real energy
            realenergy = inputdata.getRealValue('energy', row['reservetype'], True)
            
            # check whether mk power = pq power

            mkpower = realenergy/windowtime 

            # checking whether limited storage requirements apply

            if mkpower < inputdata.getRealValue('power', row['reservetype'], False):

                print("Balancing reserve provider with limited storage capacity. Marketable power of: " + str(mkpower) + "MW")
                limres = True
            
            
            print("\nAnalyzing " + row.loc["product"] + " product.\n")
            
            # add product to check list
            
            checks = updateListofLists(checks, row["product"], index, writecols.index('product'))
            checks = updateListofLists(checks, row["reservetype"], index, writecols.index('reservetype'))

            
            # CHECK1: check minimum bidding power is fulfilled
            
            checks = check1freqcontrol(realpower, row, index, checks, writecols)

            
            # CHECK2: check if ramping requirement is fulfilled
            
            checks = check2freqcontrol(inputdata.rampup, row, index, checks, writecols)


            # check if there is the reservoir is limited

            if limres:
                
                # CHECK3: minimum energy to PQ and MK energy capacity
                
                checks = check3freqcontrol(realenergy, realpower, row, index, mkpower, checks, writecols)
                
                #CHECK4: Maximum power when limited reservoir
                
                checks = check4freqcontrol(realpower, index, mkpower, checks, writecols)
                

    elif servicetype == "redispatch":

        # here, we only have 2 cases. If the storage is remotelty controllable or not.

        if inputdata.remotecontrol:

            checkpower = inputdata.power > servicedata.minimum_bid_power_1[0]

        elif not inputdata.remotecontrol:

            checkpower = inputdata.power > servicedata.minimum_bid_power_2[0]
            
        checks[1] = [checkpower]

    return checks



def check1freqcontrol(realpower, product, dfindex, checks, writecols):
    
    checkpower = realpower > product.minimum_bid_power
    valuepower = str(round(realpower,4)) + '/' + str(round(product.minimum_bid_power,4))
            
    checks = updateListofLists(checks,checkpower,dfindex,writecols.index('minPower'))
    checks = updateListofLists(checks,valuepower,dfindex,writecols.index('minPower_values'))
    
    return checks
    
    
def check2freqcontrol(rampup, product, dfindex, checks, writecols):
    
    if product.ramp_up == '-': #no minimum ramp required
                
        checks = updateListofLists(checks,'-',dfindex,writecols.index('minRamp'))
        checks = updateListofLists(checks,'-',dfindex,writecols.index('minRamp_values'))
        print(" - No minimum ramp required.")

    else:

        if rampup == 'inst.': # if the ramp is instantaneous, then it already passes the check

            checks = updateListofLists(checks,True,dfindex,writecols.index('minRamp'))
            checks = updateListofLists(checks,'inst.',dfindex,writecols.index('minRamp_values'))

        else: #if not, calculate the slopes and compared them
            
            # values of input to compare
            inputslope = float(rampup.split('/')[1]) / float(rampup.split('/')[0])

            # values of ancillary service to compare
            serviceslope = float(product.ramp_up.split('/')[1]) / float(product.ramp_up.split('/')[0])

            #comparison values. storing 
            checkrampup = inputslope > serviceslope
            valuerampup = str(round(inputslope,4)) + '/' + str(round(serviceslope,4))

            checks = updateListofLists(checks,checkrampup, dfindex, writecols.index('minRamp'))
            checks = updateListofLists(checks,valuerampup, dfindex, writecols.index('minRamp_values'))
            
    return checks
            
            
            
def check3freqcontrol(realenergy, realpower, product, dfindex, mkpower, checks, writecols):

    # calculate minimum energies with respect to PQ or MK powers

    mincaplist = [s for s in product.keys() if "min_cap" in s]
    mkenergy = []

    for cap in mincaplist: #for every row column that has data about minimum capacity

        if product.loc[cap] == '-': #if there is an x in the data, meaning that there is no minimum requirement
            
            print(" - No minimum MK" + cap.split('_')[-1] + 
            " capacity requirement for " + product.loc["product"] + "product.")

        elif "PQ" in cap: # if PQ is in the minimum capacity column name: if we are dealing with min PQ power conditions

            pqenergy = realpower * product.loc[cap] # PQ power times time

        else:

            mkenergy += [mkpower * product.loc[cap]] #MK power times time

    # multiplier selection, considering that the bidding might be symmetrical
    
    mult = 1
    
    if product.reservetype == "symmetric":
        
        mult = 2
    
    # check which services we are dealing with so we can calculate full MK power

    if product.loc["product"] == "FCR":

        minMKenergy = mult *(mkenergy[0] + max(mkenergy[1], mkenergy[2]))
    
    else:

        minMKenergy = mult * mkenergy[0]

    # calcualte checks
    checkPQenergy = realenergy >= pqenergy
    valuePQenergy = str(round(realenergy,4)) + '/' + str(round(pqenergy,4))

    checks = updateListofLists(checks,checkPQenergy,dfindex,writecols.index('minPQenergy'))
    checks = updateListofLists(checks,valuePQenergy,dfindex,writecols.index('minPQenergy_values'))

    checkMKenergy = realenergy >= minMKenergy
    valueMKenergy = str(round(realenergy,4)) + '/' + str(round(minMKenergy,4))

    checks = updateListofLists(checks,checkMKenergy,dfindex,writecols.index('minMKenergy'))
    checks = updateListofLists(checks,valueMKenergy,dfindex,writecols.index('minMKenergy_values'))
    
    return checks
    

def check4freqcontrol(realpower,dfindex, mkpower, checks, writecols):
    
    checkLRpower = realpower >= mkpower * 1.25
    valueLRpower = str(round(realpower,4)) + '/' + str(round(mkpower*1.25,4))
    
    checks = updateListofLists(checks,checkLRpower,dfindex,writecols.index('minLRpower'))
    checks = updateListofLists(checks,valueLRpower,dfindex,writecols.index('minLRpower_values'))
    
    return checks
    

def updateListofLists(list,value,index,pos):

    # one index for each freq_control product and one pos for each check
    if index == 0:

        list[pos] = [value]

    elif index > 0:

        list[pos] +=[value]

    return list


def runTool():

    servicelist = ['freq_control', 'redispatch']
    service = servicelist 
    
    
    path = Path(os.getcwd()).parent

    input = readInput(path/'inputvalues.xlsx')
    
    writecols = list(pd.read_excel(path/'outputvalues.xlsx', 'output').columns)[2:] #get columns in which data is to be written in outputvalues. remove 2 initial elements

    ancillarydata = readAnService(path/'ancillaryservicevalues.xlsx', service)

    for i in range(len(input)):
    
        checks = compareValues(input[i], ancillarydata, service, writecols, weeksection="hol", timeslice=1)

        writeOutput(path/'outputvalues.xlsx', input[i].id, service, checks)
                







