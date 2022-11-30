from utils.utils import *
#from m4a_classes.models import ancillaryService

# CHECK1: check minimum bidding power is fulfilled

def check1freqcontrol(realpower, minbidpower, dfindex, checks, writecols):
    
    checkpower = realpower > minbidpower
    valuepower = str(round(realpower,4)) + '/' + str(round(minbidpower,4))
            
    checks = updateListofLists(checks,checkpower,dfindex,writecols.index('minPower'))
    checks = updateListofLists(checks,valuepower,dfindex,writecols.index('minPower_values'))
    
    return checks
    
    
# CHECK2: check if ramping requirement is fulfilled

def check2freqcontrol(rampinput, minramp, dfindex, checks, writecols):
    
    if minramp == '-': #no minimum ramp required
                
        checks = updateListofLists(checks,'-',dfindex,writecols.index('minRamp'))
        checks = updateListofLists(checks,'-',dfindex,writecols.index('minRamp_values'))
        print(" - No minimum ramp required.")

    else:

        if rampinput == 'inst.': # if the ramp is instantaneous, then it already passes the check

            checks = updateListofLists(checks,True,dfindex,writecols.index('minRamp'))
            checks = updateListofLists(checks,'inst.',dfindex,writecols.index('minRamp_values'))

        else: #if not, calculate the slopes and compared them
            
            # values of input to compare
            inputslope = float(rampinput.split('/')[1]) / float(rampinput.split('/')[0])

            # values of ancillary service to compare
            serviceslope = float(minramp.split('/')[1]) / float(minramp.split('/')[0])

            #comparison values. storing 
            checkrampup = inputslope > serviceslope
            valuerampup = str(round(inputslope,4)) + '/' + str(round(serviceslope,4))

            checks = updateListofLists(checks,checkrampup, dfindex, writecols.index('minRamp'))
            checks = updateListofLists(checks,valuerampup, dfindex, writecols.index('minRamp_values'))
            
    return checks
      
            
# CHECK3: minimum energy to PQ and MK energy capacity           
            
def check3freqcontrol(realenergy, realpower, freqproduct, index, mkpower, checks, writecols):

    # calculate minimum energies with respect to PQ or MK powers

    mincaplist = [s for s in freqproduct.__dict__.keys() if "min_cap" in s] #get all the attributes with min_cap in them (minimum capacity)
    mkenergy = []

    for cap in mincaplist: #for every row column that has data about minimum capacity

        if getattr(freqproduct, cap) == '-': #if there is an x in the data, meaning that there is no minimum requirement
            
            print(" - No minimum MK" + cap.split('_')[-1] + 
            " capacity requirement for " + freqproduct.product + "product.")

        elif "PQ" in cap: # if PQ is in the minimum capacity column name: if we are dealing with min PQ power conditions

            pqenergy = realpower * getattr(freqproduct, cap) # PQ power times time

        else:

            mkenergy += [mkpower * getattr(freqproduct, cap)] #MK power times time

    # multiplier selection, considering that the bidding might be symmetrical
    
    mult = 1
    
    if freqproduct.reservetype == "symmetric":
        
        mult = 2
    
    # check which services we are dealing with so we can calculate full MK power

    if freqproduct.product == "FCR":

        minMKenergy = mult *(mkenergy[0] + max(mkenergy[1], mkenergy[2]))
    
    else:

        minMKenergy = mult * mkenergy[0]

    # calcualte checks
    checkPQenergy = realenergy >= pqenergy
    valuePQenergy = str(round(realenergy,4)) + '/' + str(round(pqenergy,4))

    checks = updateListofLists(checks,checkPQenergy,index,writecols.index('minPQenergy'))
    checks = updateListofLists(checks,valuePQenergy,index,writecols.index('minPQenergy_values'))

    checkMKenergy = realenergy >= minMKenergy
    valueMKenergy = str(round(realenergy,4)) + '/' + str(round(minMKenergy,4))

    checks = updateListofLists(checks,checkMKenergy,index,writecols.index('minMKenergy'))
    checks = updateListofLists(checks,valueMKenergy,index,writecols.index('minMKenergy_values'))
    
    return checks
    
    
# CHECK4: Maximum power when limited reservoir

def check4freqcontrol(realpower,index, mkpower, checks, writecols):
    
    checkLRpower = realpower >= mkpower * 1.25
    valueLRpower = str(round(realpower,4)) + '/' + str(round(mkpower*1.25,4))
    
    checks = updateListofLists(checks,checkLRpower,index,writecols.index('minLRpower'))
    checks = updateListofLists(checks,valueLRpower,index,writecols.index('minLRpower_values'))
    
    return checks
    
    
# Check for redispatch power
                
def checkredispatchpower(checks, inputdata, servicedata,  writecols):
    
    # here, we only have 2 cases. If the storage is remotelty controllable or not.
    maxcon = inputdata.getMaxConnectivity()[0]
    powertocheck = inputdata.getRealValue('power', 'symmetric', False) #get power value with symmetric balancing efficiency and no connectivity correction factor
    
    if inputdata.weeksection == '-' or inputdata.timeslice == '-': 
            
        checks = updateListofLists(checks, inputdata.getMaxConnectivity()[1][1], 0, writecols.index('weeksection'))
        checks = updateListofLists(checks, inputdata.getMaxConnectivity()[1][0], 0, writecols.index('timeslice'))
    
    
    
    if inputdata.remotecontrol:
        
        checkpower = powertocheck * maxcon > servicedata['redispatch'].minimum_bid_power_1
        valuepower = str(round((powertocheck * maxcon),4)) + '/' + str(round(servicedata['redispatch'].minimum_bid_power_1,4))

    elif not inputdata.remotecontrol:

        checkpower = powertocheck * maxcon > servicedata['redispatch'].minimum_bid_power_2
        valuepower = str(round((powertocheck * maxcon),4)) + '/' + str(round(servicedata['redispatch'].minimum_bid_power_2,4))
    
    checks = updateListofLists(checks, checkpower, 0, writecols.index('minPower'))
    checks = updateListofLists(checks, valuepower, 0, writecols.index('minPower_values'))
    
    return checks






