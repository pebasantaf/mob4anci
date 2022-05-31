import statistics

class inputInfo:
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
        
        if magnitude == 'energy':
            
            value = self.energy
            
        elif magnitude == 'power':
            
            value = self.power
        
        if flow == 'positive':
            
            realvalue = round(value * self.dischargeefficiency, 4)
            
        elif flow == 'negative':
            
            realvalue = round(value * self.chargeefficiency, 4)
            
        elif flow == 'symmetric':

            realvalue = round(value * statistics.mean([self.chargeefficiency, self.dischargeefficiency]), 4)
            
        else:
            
            raise NameError("Incorrect input string for checkControlReserve")
        
        if connectivity:
            
            realvalue = realvalue * self.getMinConnectivity(self.weeksection, self.timeslice)
        
        return realvalue
    
    
    def getMinConnectivity(self, weeksection,timeslice):
        
        windowtime = 4
        currentwindow = self.connectivity[self.id + "_" + weeksection][(timeslice-1)
        *windowtime:timeslice*windowtime]
        minconnect = min(currentwindow)
        
        return minconnect