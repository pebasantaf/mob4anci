import statistics
import numpy as np
import pandas as pd
import os
from pathlib import Path
import m4a_checker.checkfunctions as pcr
from utils.utils import updateListofLists, writeOutput, getLPFileDirectories, mergeFiles
import cplex
from m4a_optimizer.writeLPfiles import *
from m4a_optimizer.setCS import setCS
from openpyxl import workbook, load_workbook
import scipy.io as scio
from datetime import datetime
import warnings
from functools import reduce

class VirtualPowerPlant:
    
    #filedirectory = os.path.join(os.getcwd(), "data\LPfiles")
    
    def cplexOptimization(self, directories):
        
        # initialize CPLEX object
        cpx = cplex.Cplex()
        
        # read optimization model
        cpx.read(directories['lp'])
        
        # deactivate creation of log-file
        cpx.parameters.output.clonelog.Cur = 4
        
        # choose LP method
        # 0 - Automatic: Let Cplex choose
        # 1 - Primal Simplex
        # 2 - Dual Simplex
        # 3 - Network Simplex
        # 4 - Barrier
        # 5 - Sifting
        # 6 - Concurrent (Dual, Barrier and Primal in opportunistic parallel mode)
        cpx.parameters.lpmethod.Cur = 0
        
        # solve optimization problem
        cpx.solve()
        
        # get variable names and respective solution vector
        """if (isfield(cpx.Solution,'x')):
            cpx_sol = cpx.Solution.x
            cpx_var = cpx.Model.colname
        else:
            error(sprintf(['\nNo optimal soluation available, please adjust optimization model and check command window output for more info!']))
        """
        return cpx
    
class FleetOperator:
    
    path = os.path.join(Path(os.getcwd()).parent, 'inputvalues.xlsx')
    outpath = os.path.join(Path(os.getcwd()).parent, 'outputvalues.xlsx')
    lpfiledirectory = os.path.join(os.getcwd(), "data")
    
    def demand2Excel(self,  matpath, dataset, inputid):
        
        ''' demand from mat file to inputvalues excel'''
        
        matfile = scio.loadmat(matpath)
        
        valuesresolution = matfile[dataset][0,0] #<-- set the array you want to access. 
        keys = matfile[dataset][0,0].dtype.descr

        timeseries = valuesresolution['tincr_60'][0][0]
        matfilecolumns = valuesresolution['tincr_60'][0].dtype.descr
        columns = ['E_d_esp', 'E_d_lep', 'E_d_flex', 'P_d_max', 'P_d_nonopt']
        cols2write = [col + '_' + inputid for col in columns]
        
        #load workbook
        
        wb = load_workbook(self.path)
        sheet = wb['demand']
        
        #get current columns in excel
        currentcols = [element.value for element in list(sheet.rows)[0]]
        
        #get mask that indicates if columns already exist or not
        
        coincidentcols = ['bus1' in col for col in currentcols]
        
        
        for i in range(len(columns)):
            
            maxcol = sheet.max_column
            
            #if there is any true value in coincident columns
            
            if any(coincidentcols): 
                
                colindex = currentcols.index(cols2write[i]) + 1
            
            #if not, the index is just the one of the next empty cell
            else:
                
                colindex = maxcol + 1
                sheet.cell(row=1, column=colindex).value = cols2write[i] #and we create the column name
            
            #NOTE: plus 1 necessary due to different index numbering between excel and python
            
            listofvalues = list(np.concatenate(np.abs(timeseries[i]), axis=0))
            
            #fill in the data
            for j in range(len(listofvalues)):
                
                sheet.cell(row=j+2, column=colindex).value = listofvalues[j]
        
        wb.save(self.path)


    def createFleetObjects(self, cs): 
        
        #read input values for the fleet and demand values
        data = pd.read_excel(self.path, 'input')
        data = data.drop(data[data.readinput==0].index)
        
        demand =  pd.read_excel(self.path, 'demand')
        
        #get number of timesteps to limit size of optimization
        
        limittime = cs.nr_timesteps
        
        dayoption = ['week', 'sat', 'hol'] #workweek, saturday, holiday/sunday
        
        fleetobjects = dict.fromkeys(data.id.values)
        
        for key in fleetobjects:  #for every fleet object name

            fleetobjects[key] = electricFleet() #store the object in the dictionary
            items = fleetobjects[key].__dict__.keys() #get all the attributes of the object


            for variable in items: #iterate over the attributes

                if variable =='connectivity': #if we wanna get the connectivity, we use a special call cause it is a larger dataset

                    cols = [key + '_' + day for day in dayoption]
                    connectivity = pd.read_excel(self.path, 'connectivity', index_col=0).loc[:,cols]

                elif 'E_d' in variable or 'P_d' in variable: # the energy for the optimization also has a specific case
                    
                    #get list of columns with correct id
                    
                    idcolumns = [col for col in demand.columns if 'bus1' in col]
                    currentdf = demand[idcolumns]

                    #get the current variable we are handling from the data of the current id
                    currentvariable = [v for v in idcolumns if variable in v]
                    
                    valueslistoflist = currentdf[currentvariable].values.tolist()[:limittime]
                    
                    goodvalues = [item for sublist in valueslistoflist for item in sublist] #fix format, as valueslistoflist makes list of list and not just a list with values
                    
                    setattr(fleetobjects[key], variable ,goodvalues)

                    
                
                else: #for the rest of the elements, just set the value
                    
                    index = data.index[data['id']==key][0] #get the index position of the corresponding id
                    setattr(fleetobjects[key], variable, data[variable].iloc[index]) #set the attribute in the fleet object

            fleetobjects[key].connectivity = connectivity #apply connectivity

        return fleetobjects
    
    
    
    def compareValues(self, inputdata, servicedata, servicetype, writecols):

        checks = [['-']]*len(writecols)

        # updating inputdata considering negative/positive power balancing

        if servicetype == 'freq_control':
            
            # 4 hours each participation window for frequency control
            windowtime = 4
            index = 0
            limres = False

            # for every of the three frequency reserve products

            for key in servicedata:
                
                realpower = inputdata.getRealValue('power',servicedata[key].reservetype,True)
                
                # get the real energy
                realenergy = inputdata.getRealValue('energy', servicedata[key].reservetype, True)
                
                # check whether mk power = pq power

                mkpower = realenergy/windowtime 

                # checking whether limited storage requirements apply

                if mkpower < inputdata.getRealValue('power', servicedata[key].reservetype, False): #mk power smaller than the real power without considering connectivity

                    print("\nBalancing reserve provider with limited storage capacity. Marketable power of: " + str(mkpower) + "MW")
                    limres = True
                
                
                print("\nAnalyzing " + servicedata[key].product + " product.")
                
                # add product to checks list
                
                checks = updateListofLists(checks, servicedata[key].product, index, writecols.index('product'))
                checks = updateListofLists(checks, servicedata[key].reservetype, index, writecols.index('reservetype'))
                
                #if the input its a dash, store weeksection and timeslice/hour of the max. connectivity because it is the one that is going to be used
                
                if inputdata.weeksection == '-' or inputdata.timeslice == '-': 
                    
                    checks = updateListofLists(checks, inputdata.getMaxWindow()[1][1], index, writecols.index('weeksection'))
                    checks = updateListofLists(checks, inputdata.getMaxWindow()[1][0], index, writecols.index('timeslice'))

                else: # else, you have input a specific timeslice/hour. Therefore, a dash is given as an ouput as that is the value already being used and not a certain maximum is necessary
                    
                    checks = updateListofLists(checks, '-', index, writecols.index('weeksection'))
                    checks = updateListofLists(checks, '-', index, writecols.index('timeslice'))
                    
                
                # CHECK1: check minimum bidding power is fulfilled
                
                checks = pcr.check1freqcontrol(realpower, servicedata[key].minimum_bid_power, index, checks, writecols)

                
                # CHECK2: check if ramping requirement is fulfilled
                
                checks = pcr.check2freqcontrol(inputdata.rampup, servicedata[key].ramp_up, index, checks, writecols)


                # check if there is the reservoir is limited

                if limres:
                    
                    # CHECK3: minimum energy to PQ and MK energy capacity
                    
                    checks = pcr.check3freqcontrol(realenergy, realpower, servicedata[key], index, mkpower, checks, writecols)
                    
                    # CHECK4: Maximum power when limited reservoir
                    
                    checks = pcr.check4freqcontrol(realpower, index, mkpower, checks, writecols)
                    
                index += 1    
             # Check redispatch power
    
        elif servicetype == 'redispatch':
        
            checks = pcr.checkredispatchpower(checks, inputdata, servicedata, writecols)
        
        
        writeOutput(self.outpath, inputdata.id, servicetype, checks)
        
        return checks

    def setValuesForOptimization(self, cs, em):  
        
        #Vpp_name_list =['fleet','em']
        results = []

        #em.setGeneralMarketAttributes()
        #em.setBalancingMarketAttributes()
        
        fleet = self.createFleetObjects(cs)
        
        directories = getLPFileDirectories(self.lpfiledirectory,'VPP')
        
        writeLPem(directories, cs, em)
        writeLPbm(directories, cs, em)
        writeLPadd(directories, cs)
        
        for key in fleet:
            
            writeLPfleet(directories, cs, fleet[key])
            
            mergeFiles(directories)
            
            vpp = VirtualPowerPlant()
            
            results += [vpp.cplexOptimization(directories)]
        
        return results, fleet


    
class electricFleet:
    
    windowtime = 4
    
    def __init__(self):
        self.id = None
        self.storagetype = None
        self.chargetype = None
        self.nr_vehicles = None
        self.chargeefficiency = None
        self.dischargeefficiency = None
        self.energy = None
        self.power = None
        self.remotecontrol = None
        self.rampup = None
        self.weeksection = None
        self.timeslice = None
        self.connectivity = None
        self.E_d_esp = None
        self.E_d_lep = None
        self.E_d_flex = None
        self.P_d_max = None
        self.P_d_nonopt = None
        self.cost = None
        self.ghg_CO2 = None
        self.task = None
    
        
    def getRealValue(self, magnitude, flow, connectivity):
        
        #energy or power
        if magnitude == 'energy':
            
            value = self.energy
            
        elif magnitude == 'power':
            
            value = self.power
        
        #positive, negative or symmetric
        if flow == 'positive':
            
            realvalue = round(value * self.dischargeefficiency, 4)
            
        elif flow == 'negative':
            
            realvalue = round(value * self.chargeefficiency, 4)
            
        elif flow == 'symmetric':

            realvalue = round(value * statistics.mean([self.chargeefficiency, self.dischargeefficiency]), 4)
            
        else:
            
            raise NameError("Incorrect input string for checkControlReserve")
        
        # if we want also the multiplication times connectivity, set True
        if connectivity:
            
            # if we dont select time slice or weeksection, get the best value
            
            if self.weeksection == '-' or self.timeslice == '-':
                
                realvalue = realvalue * self.getMaxWindow()[0]
                
            else:
                
                realvalue = realvalue * self.getMinConnectivityinWindow()
        
        return realvalue
    
    def getMaxConnectivity(self):
        
        #get the maxium connectivity value of all value
        maxcon = max(self.connectivity.max())
        maxcon_loc = [self.connectivity.where(self.connectivity==maxcon).dropna().index[0], 
                      self.connectivity.where(self.connectivity==maxcon).dropna().columns[0].split('_')[1]]
        
        return maxcon, maxcon_loc
    
    def getMinConnectivityinWindow(self):
        
        #get the minimum value of a 4 hour window of connectivity
        currentwindow = self.connectivity[self.id + "_" + self.weeksection][(self.timeslice-1)
        *self.windowtime:self.timeslice*self.windowtime]
        minconnect = min(currentwindow)
        
        return minconnect

        
    def getMaxWindow(self): #check all the slots, for each slot find the minimum value of a certain slot and get the value of the slot with the highest minimum value
        
        #initialize maximum value and calculate slots (6 slots)
        fullmax = 0
        slots = int(self.connectivity.shape[0]/self.windowtime)
        
        #for each slot
        for i in range(slots):
            
            # we get 6 4x3 matrices. For each slot, we want to know the minimum for each column (1x3 vector) BUT we want the maximum of that
            # This way, we initially get the limiting connectivity which will determine the energy, but we get the highest minimum
            aktmax = max(self.connectivity[i*self.windowtime:(i+1)*self.windowtime].min(axis=0))
            
            #get the index, it being [slot, weeksection]
            aktindexmax = [i, self.connectivity.columns[np.argmax(self.connectivity[i*self.windowtime:(i+1)*self.windowtime].min(axis=0))].split('_')[1]]

            
            
            # update if we find a higher value
            if aktmax > fullmax:
                
                fullmax = aktmax
                fullindexmax = aktindexmax
        
        
             
        return fullmax, fullindexmax
        


        
class electricityMarket:
    
    file = pd.ExcelFile(os.path.join(Path(os.getcwd()).parent, 'electricitymarketvalues.xlsx'))
    bmdatapath = os.path.join(os.getcwd(), 'data\\bmdata\\')
    
    def __init__(
        self,
        P_im_min = None,
        P_im_max = None,
        P_ex_min = None,
        P_ex_max = None,
        ghg_CO2_IM = None,
        ghg_CO2_EX = None,
        price_em = None,
        price_FCR_cap=None,
        price_aFRR_cap_pos= None,
        price_aFRR_cap_neg= None,
        price_mFRR_cap = None,
        price_aFRR_en_pos = None,
        price_aFRR_en_neg = None,
        price_mFRR_en = None
        
    ):
        
        # Call to super class
        #super(emAttributes, self).__init__(
         #   )
        """
        Info
        ----
        This class provides a model with the basic attributes of a
        energy market.
        """
        # min. power import (kW)
        self.P_im_min = 0;
        
        # max. power import (kW)
        self.P_im_max = 1000000;
        
        # min. power export (kW)
        self.P_ex_min = 0;
        
        # max. power export (kW)
        self.P_ex_max = 1000000;
        
        # greenhouse gas emissions for market import (gCO2/kWh)
        self.ghg_CO2_IM = 559;
        
        # greenhouse gas emissions for market export (gCO2/kWh)
        self.ghg_CO2_EX = 0.001;

        self.price_em =  None
        
        self.price_FCR_cap = None
        self.price_aFRR_cap_pos = None
        self.price_aFRR_cap_neg = None
        self.price_mFRR_cap = None
        self.price_aFRR_en_pos = None
        self.price_aFRR_en_neg = None
        self.price_mFRR_en = None
    
    def dayAheadData2Excel(self, matfile, startdate, numstamps):
        
        matfile = scio.loadmat(matfile)
        
        #find in which position is dayahead market
        
        descriptions = [text[0] for text in matfile['description_em'][0]]
        mask = ['Day-Ahead' in name for name in descriptions]
        
        price = [round(values[mask][0], 4) for values in matfile['price_em']]
        dates = pd.date_range(start=startdate,periods=numstamps, freq="60min")
        
        wb = load_workbook(self.file)
        sheet = wb['spot_market']
        
        
        for i in range(numstamps):
            
            sheet.cell(row=i+2, column=1).value = str(dates[i]).split(' ')[0]
            sheet.cell(row=i+2, column=2).value = str(dates[i]).split(' ')[1]
            sheet.cell(row=i+2, column=3).value = price[i*4]
            
        wb.save(self.file)


        
    
    def setGeneralMarketAttributes(self, initdata, cs):
        
        ''' set the general market attributes and the day ahead price from excel in the object'''
        
        generaldata = pd.read_excel(self.file, 'general_data')
        
        for key in generaldata.columns:
            
            setattr(self, key, generaldata.loc[0,key])
            
        #set market price
        
        limittime = cs.nr_timesteps
        price = pd.read_excel(self.file, 'spot_market')
        mask = price.date == initdata
        initindex = mask.idxmax()

        self.price_em = price.spot_price.values.tolist()[initindex: initindex + limittime]

        
        
    
    def balancingMarketData2Excel(self, bmtype='aFRR', quart2hour=False):
        
        ''' stored the data obtained from SMARD application with balancing market data'''
        
        #get all the files in the corresponding bmtype folder
        
        bmfiles = os.listdir(os.path.join(self.bmdatapath, bmtype))
        bmfiles.sort() #make sure they go from oldest to newest
        
        bmdf_list = []
        
        # store excel and sheet where to store the data
        
        targetdf = pd.read_excel(self.file, 'balancing_market')
        
        # load workbook to work on it but overlay previous content and not delete it
        
        excel_workbook = load_workbook(self.file)
        
        with pd.ExcelWriter(self.file, engine='openpyxl', mode="a", if_sheet_exists='overlay') as writer:
            
            writer.book = excel_workbook
            #writer.sheets = dict((ws.title, ws) for ws in excel_workbook.worksheets)
        
            for bmdata in bmfiles:
                
                fullpath = os.path.join(self.bmdatapath, bmtype, bmdata)
                
                #apply one or the other depending if the file is xlsx or csv
                
                if bmdata.split('.')[-1:][0] == 'xlsx':
                    
                    # im catching a warning here cause it seems to be kind of useless warning and it is the only way that it does not appear
                    
                    with warnings.catch_warnings(record=True):
                        warnings.simplefilter("always")
                        data = pd.read_excel(fullpath, header=9, engine="openpyxl") 
                        
                    
                elif bmdata.split('.')[-1:][0 ]== 'csv':
                    
                    data = pd.read_csv(fullpath, sep=';')
                
                #CLEANING THE DATA AND SETTING CORRECT DATA TYPES
                
                data = data.replace('-',np.nan, regex=True) #replace - with nans
                
                # turn date and time into datetime format
                
                data['Date'] = pd.to_datetime(data['Date'])
                
                data['Start'] = pd.to_datetime(data['Start']).dt.time
                
                data = data.drop(['End'], axis=1)
                
                # turn every object into numeric
                
                for col in data.columns[2:]:
                    
                    datatype = data[col].dtype
                    
                    if datatype == 'O':
                        
                        try:
                        
                            data[col] = pd.to_numeric(data[col])
                        
                        except ValueError:
                            
                            data[col] = data[col].str.replace(',', '').astype(float)
                    
                    colmean = round(data[col].mean(), 3) #calculate mean of column
                    data[col] = data[col].fillna(colmean) #fill nans with that mean
                
                # TURN 15MIN DATA INTO HOUR
                
                #if quarter hour files were downloaded, set True. I did this and in between SMARD gave the option of download hourly values for balancing data (they do the calculation), so happy times
                
                if quart2hour:
                    
                    #NOTE: Add data 4 by 4 to get hourly. then store. Important: Values change so much every 15 min cause volume if bidded for 4 hours but might be activated or not. 

                    hourlydata = pd.DataFrame(columns=data.columns)
                    
                    timestamps =  pd.date_range(datetime.combine(data["Date"][0].date(), data["Start"][0]), periods=7*24, freq="60min")
                    
                    hourlydata["Date"] = timestamps.date
                    hourlydata["Start"] = timestamps.time
                    
                    
                    #select columns: columns with power or energy, we add. columns with price, we make an average
                    
                    powermask = ['Volume' in col for col in data.columns]
                    powercols = data.columns[powermask]
                    
                    pricemask = ['price' in col for col in data.columns]
                    pricecols = data.columns[pricemask]
                    
                    for index,row in hourlydata.iterrows():
                
                        row[powercols] = sum(data.loc[index*4:(index+1)*4-1,powercols].values)
                        row[pricecols] =  np.mean(data.loc[(index)*4:(index+1)*4-1,pricecols].values, axis=0)
                    
                else:
                        
                    hourlydata = data
                
                #change names in hourlydata columns so we can match it with the names in hourlydata
                
                hourlydata.columns = [text.replace('MW', 'kW') for text in hourlydata.columns]
                
                #REMOVE EXTRA DAY FOR LONG YEARS
                
                if hourlydata.shape[0] > 8760:
                    
                    mask = hourlydata["Date"] == datetime(hourlydata.loc[0,'Date'].year,2,29)
                    
                    hourlydata.drop(hourlydata[mask].index, inplace=True)
                    
                    hourlydata.reset_index(inplace=True, drop=True)


                #store dataframes in dictionary    
                bmdf_list += [hourlydata] 
            
            
            #mAKE THE AVERAGE OF ALL THE YEARS INCLUDED AND STORE IT IN DATAFRAME
              
            if len(bmdf_list)  > 2:
                 
                dfvalues = [frame.iloc[:,2:].values for frame in bmdf_list]
                
                valuesaddition = sum(dfvalues)
                
                valuesavg = valuesaddition/len(bmdf_list)
                
                hourlydata.iloc[:, 2:] = valuesavg
                
                #remove year from date as we have several dates
                
                hourlydata.Date = hourlydata.Date.dt.strftime('%m-%d')
            
            targetdf = targetdf.reindex(range(hourlydata.shape[0]))
            
            # NOTE: change here how to store the values considering new setup
            
            # different cases for FCR, aFRR and mFRR     
            
            targetdf.date = hourlydata["Date"]

            targetdf.time = hourlydata["Start"]
            
            if bmtype == 'aFRR':                     
                
                for col in hourlydata.columns[2:]:
                    
                    if '€' in col:
                    
                        targetdf['aFRR-' + col] = hourlydata[col]/1000 #we change MW to kW
                        
                    else:
                        
                        targetdf['aFRR-' + col] = hourlydata[col]*1000

            #change MW to kW in column names
            
            targetdf.to_excel(writer, 'balancing_market', index=False)
            
            #writer.save() #Adding this line produces a corruppted excel that must be repaired
                    
            return targetdf
            
            
    def setBalancingMarketAttributes(self, bmtype, initdate, cs):
        
        bmdata = pd.read_excel(self.file, 'balancing_market')
        
        mask = bmdata['date']==initdate
        
        #get first true value 
        
        initindex = mask.idxmax()
        
        dftimelimited = bmdata.iloc[initindex:initindex + cs.nr_timesteps, :]
        
        #this is momentaneously hardcoded
        
        self.price_aFRR_cap_pos = dftimelimited[bmtype + '-Procurement price (+) [€/kW]'].values
        self.price_aFRR_cap_neg = dftimelimited[bmtype + '-Procurement price (-) [€/kW]'].values
        
        self.price_aFRR_en_pos = dftimelimited[bmtype + '-Activation price (+) [€/kWh]'].values
        self.price_aFRR_en_neg = dftimelimited[bmtype + '-Activation price (-) [€/kWh]'].values
            


        
class ancillaryService:
    
    path = os.path.join(Path(os.getcwd()).parent, 'ancillaryservicevalues.xlsx')

        
    def getFreqcontrolObject(self):
        
        #get data for frquency control
        data = pd.read_excel(self.path, 'freq_control')
        
        #get names for initializing dictionary
        a = data["product"].values.tolist()
        b = [s[0:3] for s in data.reservetype.values.tolist()]
        dictnames = ["{}_{}".format(a_, b_) for a_, b_ in zip(a, b)]
        
        productdict = dict.fromkeys(dictnames, None)

        #create an object for each product and store its attributes
        
        for key in productdict:
            
            productdict[key] = freqControl()
            items = list(productdict[key].__dict__.keys())
            
            for element in items:
                
                index = dictnames.index(key)
                setattr(productdict[key], element, data[element].iloc[index])
                

        return productdict
    
     
    def getRedispatchObject(self):
        
        #get data for frquency control
        data = pd.read_excel(self.path, 'redispatch')

        product = redispatch()
        product.minimum_bid_power_1 = data[list(product.__dict__.keys())[0]][0]
        product.minimum_bid_power_2 = data[list(product.__dict__.keys())[1]][0]
        productdict = dict.fromkeys(data["product"], product)
        
        return productdict
        

        
class freqControl(ancillaryService):
    
    def __init__(self):
        
        self.product = None
        self.reservetype = None
        self.max_load_time = None
        self.minimum_bid_power = None
        self.ramp_up = None
        self.min_cap_PQ=None
        self.min_cap_MK_1=None
        self.min_cap_MK_2=None
        self.min_cap_MK_3=None
        
        
class redispatch(ancillaryService):
    
    def __init__(self):
        
        self.minimum_bid_power_1 = None
        self.minimum_bid_power_2 = None

        
    
        
        
        

        
        