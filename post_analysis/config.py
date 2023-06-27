#Python object to hold any configuration information from config.csv

import math

class Config:

    def __init__(self, configFile):
    
        header = ''
        isHeader = True
        
        self.SD = None #The max standard deviation factor for the y-axis ranges. Set with a command line argument.
        
        with open(configFile, 'r') as fi:
            
            for line in fi:
                if not isHeader:
                    dataList = line.lstrip('#').rstrip('\n').split(',')
                    self.vrotA = float(dataList[header.index('vrota')])
                    self.vrotB = float(dataList[header.index('vrotb')])
                    self.radius = int(dataList[header.index('vrotr')])
                    self.maxAzShearHeight = float(dataList[header.index('maxAzShearHeight')])
                    if self.maxAzShearHeight < 0:
                        self.maxAzShearHeight = math.inf
                    self.ignoreExtra = bool(int(dataList[header.index('ignoreextracriteria')]))
                    self.shiftNonTor = bool(int(dataList[header.index('timeshiftnontor')]))
                    self.nontorShiftAmount = dataList[header.index('nontortimeshiftamount')]
                    self.shiftTor = bool(int(dataList[header.index('timeshifttor')]))
                    self.torShiftAmount = dataList[header.index('tortimeshiftamount')]
                    self.timeBinSize = float(dataList[header.index('binsizeminutes')])
                    self.minbin = int(dataList[header.index('minbin')])
                    self.maxbin = int(dataList[header.index('maxbin')])
                    self.prunebins = bool(int(dataList[header.index('prunebins')]))
                    self.potentialclusters = int(dataList[header.index('potentialclusters')])
                    self.rangebins = int(dataList[header.index('rangebins')])
                    self.bestthreshfilebase = dataList[header.index('besthreshfilebase')]
                    self.hypo1 = bool(int(dataList[header.index('hypo1')]))
                    self.hypo2 = bool(int(dataList[header.index('hypo2')]))
                    self.hypo3 = bool(int(dataList[header.index('hypo3')]))
                    self.hypo4 = bool(int(dataList[header.index('hypo4')]))
                    self.hypo5 = bool(int(dataList[header.index('hypo5')]))
                    self.hypo5ef = bool(int(dataList[header.index('hypo5ef')]))
                    self.multirange = bool(int(dataList[header.index('multirange')]))
                    self.minTSSSamples = int(dataList[header.index('mintsssamples')])
                    
                else:
                    header = line.lstrip('#').rstrip('\n').split(',')
                    isHeader = False
                    
        return
        
        
                