import statistics
import numpy as np
from pyrsistent import s

class inputInfo:
    
    windowtime = 4
    
    def __init__(self):
        self.id = None
        self.storagetype = None
        self.chargetype = None
        self.chargeefficiency = None
        self.dischargeefficiency = None
        self.energy = None
        self.power = None
        self.remotecontrol = None
        self.rampup = None
        self.weeksection = None
        self.timeslice = None
        self.connectivity = None
        
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
        

        