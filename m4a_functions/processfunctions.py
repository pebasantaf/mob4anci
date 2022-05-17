import statistics
from m4a_functions.readwritefunctions import *
from m4a_functions.processfunctions import *
import os
from pathlib import Path

def compareValues(inputdata, servicedata, servicetype, writecols,**kwargs):

    checks = [['-']]*12
    

    # updating inputdata considering negative/positive power balancing

    if servicetype == 'freq_control':

        # here I update the inputdata considering the Timewindow for participation in freq regulation
        inputdata = checkTimeWindow(inputdata, kwargs.get("weeksection"), kwargs.get("timeslice"))

        # 4 hours each participation window for frequency control
        windowtime = 4

        # check whether mk power = pq power

        mkpower = inputdata.energy/windowtime 
        limres = False

        # checking whether limited storage requirements apply

        if mkpower < inputdata.power:

            print("Balancing reserve provider with limited storage capacity. Marketable power of: " + str(mkpower) + "MW")
            limres = True

        # for every of the three frequency reserve products

        for index,row in servicedata.iterrows(): 
            
            
            # here efficiencies are applied considering which type of reserve (positive, negative symetric) we are dealing with
            loopdata = checkControlReserve(inputdata, row.reservetype) # we give a new variable name so we are not applying efficiency over efficiency
            
            
            print("\nAnalyzing " + row.loc["product"] + " product.\n")
            
            # add product to check list
            
            checks = updateListofLists(checks, row["product"], index, writecols.index('product'))
            checks = updateListofLists(checks, row["reservetype"], index, writecols.index('reservetype'))

            
            # CHECK1: check minimum bidding power is fulfilled
            
            checks = check1freqcontrol(loopdata, row, index, checks, writecols)

            
            # CHECK2: check if ramping requirement is fulfilled
            
            checks = check2freqcontrol(loopdata, row, index, checks, writecols)

            
            # CHECK3: minimum energy to PQ and MK energy capacity


            # check if there is the reservoir is limited

            if limres:
                
                checks = check3freqcontrol(loopdata, row, index, mkpower, checks, writecols)
                
                #CHECK4: Maximum power when limited reservoir
                
                checks = check4freqcontrol(loopdata, index, mkpower, checks, writecols)
                

    elif servicetype == "redispatch":

        # here, we only have 2 cases. If the storage is remotelty controllable or not.

        if loopdata.remotecontrol:

            checkpower = loopdata.power > servicedata.minimum_bid_power_1[0]

        elif not inputdata.remotecontrol:

            checkpower = loopdata.power > servicedata.minimum_bid_power_2[0]
            
        checks[1] = [checkpower]

    return checks


def check1freqcontrol(inputdata, dfrow, dfindex, checks, writecols):
    
    checkpower = inputdata.power > dfrow.minimum_bid_power
    valuepower = str(round(inputdata.power,4)) + '/' + str(round(dfrow.minimum_bid_power,4))
            
    checks = updateListofLists(checks,checkpower,dfindex,writecols.index('minPower'))
    checks = updateListofLists(checks,valuepower,dfindex,writecols.index('minPower_values'))
    
    return checks
    
    
    
def check2freqcontrol(inputdata, dfrow, dfindex, checks, writecols):
    
    if dfrow.ramp_up == '-': #no minimum ramp required
                
        checks = updateListofLists(checks,'-',dfindex,writecols.index('minRamp'))
        checks = updateListofLists(checks,'-',dfindex,writecols.index('minRamp_values'))
        print(" - No minimum ramp required.")

    else:

        if inputdata.rampup == 'inst.': # if the ramp is instantaneous, then it already passes the check

            checks = updateListofLists(checks,True,dfindex,writecols.index('minRamp'))
            checks = updateListofLists(checks,'inst.',dfindex,writecols.index('minRamp_values'))

        else: #if not, calculate the slopes and compared them
            
            # values of input to compare
            inputslope = float(inputdata.rampup.split('/')[1]) / float(inputdata.rampup.split('/')[0])

            # values of ancillary service to compare
            serviceslope = float(dfrow.ramp_up.split('/')[1]) / float(dfrow.ramp_up.split('/')[0])

            #comparison values. storing 
            checkrampup = inputslope > serviceslope
            valuerampup = str(round(inputslope,4)) + '/' + str(round(serviceslope,4))

            checks = updateListofLists(checks,checkrampup, dfindex, writecols.index('minRamp'))
            checks = updateListofLists(checks,valuerampup, dfindex, writecols.index('minRamp_values'))
            
    return checks
            
            
            
def check3freqcontrol(inputdata, dfrow, dfindex, mkpower, checks, writecols):

    # calculate minimum energies with respect to PQ or MK powers

    mincaplist = [s for s in dfrow.keys() if "min_cap" in s]
    mkenergy = []

    for cap in mincaplist: #for every row column that has data about minimum capacity

        if dfrow.loc[cap] == '-': #if there is an x in the data, meaning that there is no minimum requirement
            
            print(" - No minimum MK" + cap.split('_')[-1] + 
            " capacity requirement for " + dfrow.loc["product"] + "product.")

        elif "PQ" in cap: # if PQ is in the minimum capacity column name: if we are dealing with min PQ power conditions

            pqenergy = inputdata.power * dfrow.loc[cap] # PQ power times time

        else:

            mkenergy += [mkpower * dfrow.loc[cap]] #MK power times time

    # multiplier selection, considering that the bidding might be symmetrical
    
    mult = 1
    
    if dfrow.reservetype == "symmetric":
        
        mult = 2
    
    # check which services we are dealing with so we can calculate full MK power

    if dfrow.loc["product"] == "FCR":

        minMKenergy = mult *(mkenergy[0] + max(mkenergy[1], mkenergy[2]))
    
    else:

        minMKenergy = mult * mkenergy[0]

    # calcualte checks
    checkPQenergy = inputdata.energy >= pqenergy
    valuePQenergy = str(round(inputdata.energy,4)) + '/' + str(round(pqenergy,4))

    checks = updateListofLists(checks,checkPQenergy,dfindex,writecols.index('minPQenergy'))
    checks = updateListofLists(checks,valuePQenergy,dfindex,writecols.index('minPQenergy_values'))

    checkMKenergy = inputdata.energy >= minMKenergy
    valueMKenergy = str(round(inputdata.energy,4)) + '/' + str(round(minMKenergy,4))

    checks = updateListofLists(checks,checkMKenergy,dfindex,writecols.index('minMKenergy'))
    checks = updateListofLists(checks,valueMKenergy,dfindex,writecols.index('minMKenergy_values'))
    
    return checks
    

def check4freqcontrol(inputdata,dfindex, mkpower, checks, writecols):
    
    checkLRpower = inputdata.power >= mkpower * 1.25
    valueLRpower = str(round(inputdata.power,4)) + '/' + str(round(mkpower*1.25,4))
    
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


def checkTimeWindow(inputdata, weeksection, timeslice):

    outdata = inputdata
    # can choose between weekend (week), saturday (sat) and holiday and sunday (hol)

    #calculate the minimum connectivity in each of the hours of the window
    windowtime = 4
    currentwindow = outdata.connectivity[inputdata.id + "_" + weeksection][(timeslice-1)
    *windowtime:timeslice*windowtime]
    minconnect = min(currentwindow)

    # obtain minimum power and energy available for qualification

    realenergy = outdata.energy * minconnect
    realpower = outdata.power * minconnect

    outdata.energy = realenergy
    outdata.power = realpower

    return outdata

def checkControlReserve(data, product):

    outdata = data #necessary due to the way variables work in python. This way, it will not modify also the values of the input data even when assigning a different variable to the function
    # This way the input data "data" and what we give to return can become independen
    
    
    if product == 'positive': # if we want positive control reserve, multiply by discharge efficiency

        outdata.energy = outdata.energy * outdata.dischargeefficiency
        outdata.power = outdata.power * outdata.dischargeefficiency

    elif product == 'negative': #otherwise, by charging one

        outdata.energy = outdata.energy * outdata.chargeefficiency
        outdata.power = outdata.power * outdata.chargeefficiency
        

    elif product == 'symmetric': # if we want both, then calculate both and check the minimum energy/power value. This is what ultimately will qualify

        
        outdata.energy = outdata.energy * statistics.mean([outdata.chargeefficiency, outdata.dischargeefficiency])

        outdata.power = outdata.power * statistics.mean([outdata.chargeefficiency, outdata.dischargeefficiency])

    else:

        raise NameError("Incorrect input string for checkControlReserve")

    return outdata


def runTool():

    servicelist = ['freq_control', 'redispatch']
    service = servicelist[0] 
    
    
    path = Path(os.getcwd()).parent

    input = readInput(path/'inputvalues.xlsx')
    
    writecols = list(pd.read_excel(path/'outputvalues.xlsx', 'output').columns)[2:] #get columns in which data is to be written in outputvalues. remove 2 initial elements

    ancillarydata = readAnService(path/'ancillaryservicevalues.xlsx', service)

    for i in range(len(input)):
    
        checks = compareValues(input[i], ancillarydata, service, writecols, weeksection="hol", timeslice=1)

        writeOutput(path/'outputvalues.xlsx', input[i].id, service, checks)
                







