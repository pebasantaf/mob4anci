
def compareValues(inputdata, servicedata, servicetype,**kwargs):

    checks = [['-']]*5

    # updating inputdata considering negative/positive power balancing

    inputdata = checkControlReserve(inputdata)

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
            
            print("Analyzing " + row.loc["product"] + "product.\n")
            
            # add product to check list
            
            checks = updateListofLists(checks,row[0],index,0)

            
            # CHECK1: check minimum bidding power is fulfilled

            checkpower = inputdata.power > row.minimum_bid_power
            
            checks = updateListofLists(checks,checkpower,index,1)


            
            # CHECK2: check if ramping requirement is fulfilled

            if row.ramp_up == '-': #no minimum ramp required
                
                checks = updateListofLists(checks,'-',index,2)
                print("No minimum ramp required.")

            else:

                if inputdata.rampup == 'inst.': # if the ramp is instantaneous, then it already passes the check

                    checks = updateListofLists(checks,True,index,2)

                else: #if not, calculate the slopes and compared them
                    
                    # values of input to compare
                    inputslope = float(inputdata.rampup.split('/')[1]) / float(inputdata.rampup.split('/')[0])

                    # values of ancillary service to compare
                    serviceslope = float(row.ramp_up.split('/')[1]) / float(row.ramp_up.split('/')[0])

                    #comparison values. storing 
                    checkrampup = inputslope > serviceslope

                    checks = updateListofLists(checks,checkrampup,index,2)




            # CHECK3: minimum energy to PQ and MK energy capacity

            ''' this part needs updated. I need to check well the formulas as there are things missing, like the 2 in case of symmetric auctioning and so on'''

            # check if there is the reservoir is limited

            if limres:

                # calculate minimum energies with respect to PQ or MK powers

                mincaplist = [s for s in row.keys() if "min_cap" in s]
                mkenergy = []

                for cap in mincaplist: #for every row column that has data about minimum capacity

                    if row.loc[cap] == '-': #if there is an x in the data, meaning that there is no minimum requirement
                        
                        print("No minimum MK" + cap.split('_')[-1] + 
                        " capacity requirement for " + row.loc["product"] + "product.")

                    elif "PQ" in cap: # if PQ is in the minimum capacity column name: if we are dealing with min PQ power conditions

                        pqenergy = inputdata.power * row.loc[cap] # PQ power times time

                    else:

                        mkenergy += [mkpower * row.loc[cap]] #MK power times time

                # multiplier selection, considering that the bidding might be symmetrical
                
                mult = 1
                
                if inputdata.controlreserve == "symmetric":
                    
                    mult = 2
                
                # check which services we are dealing with so we can calculate full MK power

                if row.loc["product"] == "FCR":

                    minMKenergy = mult *(mkenergy[0] + max(mkenergy[1], mkenergy[2]))
                
                else:

                    minMKenergy = mult * mkenergy[0]

                # calcualte checks
                checkPQenergy = inputdata.energy >= pqenergy

                checks = updateListofLists(checks,checkPQenergy,index,3)

                checkMKenergy = inputdata.energy >= minMKenergy

                checks = updateListofLists(checks,checkMKenergy,index,4)

    elif servicetype == "redispatch":

        # here, we only have 2 cases. If the storage is remotelty controllable or not.

        if inputdata.remotecontrol:

            checkpower = inputdata.power > servicedata.minimum_bid_power_1[0]

        elif not inputdata.remotecontrol:

            checkpower = inputdata.power > servicedata.minimum_bid_power_2[0]
            
        checks[1] = [checkpower]

    return checks

def updateListofLists(list,value,index,pos):

    # one index for each freq_control product and one pos for each check
    if index == 0:

        list[pos] = [value]

    elif index > 0:

        list[pos] +=[value]

    return list


def checkTimeWindow(inputdata, weeksection, timeslice):

    # can choose between weekend (week), saturday (sat) and holiday and sunday (hol)

    #calculate the minimum connectivity in each of the hours of the window
    windowtime = 4
    currentwindow = inputdata.connectivity[inputdata.id + "_" + weeksection][(timeslice-1)
    *windowtime:timeslice*windowtime]
    minconnect = min(currentwindow)

    # obtain minimum power and energy available for qualification

    realenergy = inputdata.energy * minconnect
    realpower = inputdata.power * minconnect

    inputdata.energy = realenergy
    inputdata.power = realpower

    return inputdata

def checkControlReserve(data):

    if data.controlreserve == 'positive': # if we want positive control reserve, multiply by discharge efficiency

        data.energy = data.energy * data.dischargeefficiency
        data.power = data.power * data.dischargeefficiency

    elif data.controlreserve == 'negative': #otherwise, by charging one

        data.energy = data.energy * data.chargeefficiency
        data.power = data.power * data.chargeefficiency

    elif data.controlserver == 'symmetric': # if we want both, then calculate both and check the minimum energy/power value. This is what ultimately will qualify

        data.energy = data.energy * min(data.chargeefficiency, data.dischargeefficiency)

        data.power = data.power * min(data.chargeefficiency, data.dischargeefficiency)

    else:

        raise NameError("Incorrect input string for checkControlReserve")

    return data



                






