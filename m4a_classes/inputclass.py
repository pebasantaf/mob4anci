import statistics

class inputInfo:
    def __init__(self, id=None, storagetype=None, chargetype=None, chargeefficiency=None, dischargeefficiency=None, 
    energy=None, power=None, remotecontrol=None, rampup=None, connectivity=None):
        self.id = id
        self.storagetype = storagetype
        self.chargetype = chargetype
        self.chargeefficiency = chargeefficiency
        self.dischargeefficiency = dischargeefficiency
        self.energy = energy
        self.power = power
        self.remotecontrol = remotecontrol
        self.rampup = rampup
        self.connectivity = connectivity
        
    def getRealPower(self, flow):
        
        if flow == 'discharge':
            
            realpower = round(self.power * self.dischargeefficiency, 4)
            
        elif flow == 'charge':
            
            realpower = round(self.power * self.chargeefficiency, 4)
            
        elif flow == 'symmetric':

            realpower = round(self.power * statistics.mean([self.chargeefficiency, self.dischargeefficiency]), 4)
            
        else:
            
            raise NameError("Incorrect input string for checkControlReserve")
            
        return realpower
    
    def getRealEnergy(self, flow):
        
        if flow == 'discharge':
            
            realenergy = round(self.energy * self.dischargeefficiency, 4)
            
        elif flow == 'charge':
            
            realenergy = round(self.energy * self.chargeefficiency, 4)
            
        elif flow == 'symmetric':

            realenergy = round(self.energy * statistics.mean([self.chargeefficiency, self.dischargeefficiency]),4) 
            
        else:
            
            raise NameError("Incorrect input string for checkControlReserve")
            
        return realenergy
    