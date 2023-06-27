#This module holds the configuration information for the skills output

import re
import xarray as xr

class Config():

    def __init__(self, configFile, tiltList):
    
        """ Loads configuration information from the configFile csv from the tilts in tiltList. The tilts in tiltList much match what's in the config CSV. """
        
        #Define variables that determine if the particular variable will be checked during the check
        self.__useTilts = {}
        self.__useET = False
        self.__timeBins = []
        
        header = ''
        with open(configFile, 'r') as fi:
        
            for line in fi:
                currentLine = line.strip('\n').strip('#').split(',')
                if header:
                    for tilt in tiltList:
                        self.__useTilts[tilt] = bool(int(currentLine[header.index(tilt)]))
                        
                    self.__useET = bool(int(currentLine[header.index('et')]))
                    self.__timeBins = currentLine[header.index('timebins')].split(',')
                        
                else:
                    header = currentLine
                    
        return
        
    def __str__(self):
        return 'tilts: '+str(self.__useTilts)+'\nuseET: '+str(self.__useET)+'\ntime bins: '+str(self.__timeBins)
        

class Thresholds():

    def __init__(self, thresholdFile, tiltList):
    
        """ Loads the best thresholds for each tilt and echo tops by time and range bin.
        
            Arguments:
            thresholdFile(str): The path to the .csv file containing the thresholds with the format
            
                        ,tilt1,tilt2,tilt3,...et
              tb1(r1-r2),t1,t2,t3,...tet
              tb1(r2-r3),t1,t2,t3,...tet
                     ...,...,...,...,......
              tb1(rx-inf),t1,t2,t3,...tet
              tb2(r1-r2),t1,t2,t3,...tet
                     ...,...,...,...,......
             
             Where tilt is an elevation angle and et is the echo top
             tb is the time bin and r is a range. t is the best threshold for that particular tilt or echo top.
             
             The last range is always inf. If there is only one range bin then only one line for a time bin is used with the range 0-inf
             
             tiltList(list) - The list of elevation angles to use.
             
             
        """
        
        timeBins = []
        ranges = []
        masterData = []
        thresholds = []
        header = None
        self.thresholds = None
        
        with open(thresholdFile, 'r') as fi:
        
            
            for line in fi:
            
                if header is not None:
                    splitLine = line.rstrip('\n').split(',')
                    splitBin = re.split('[\(\)]', splitLine[0])
                    print('Splitline', splitLine, 'splitbin', splitBin)
                    currentTimeBin = int(splitBin[0])
                    
                    #This assumes that all time bins are grouped together and that the ranges are in order
                    if currentTimeBin not in timeBins:
                        timeBins.append(currentTimeBin)
                        if thresholds:
                            masterData.append(thresholds)
                            thresholds = []
                    
                    currentRanges = splitBin[1]
                    if currentRanges not in ranges:
                        ranges.append(currentRanges)
                        
                    thresholds.append(splitLine[1:len(splitLine)])
                else:
                    header = line.lstrip(',').rstrip('\n').split(',')
                    
                    
            masterData.append(thresholds)
                    
        print('The type is', type)            
        xData = {'thresholds':(['time', 'range', 'type'], masterData, {'units':'s^-1', 'long_name':'best azshear threshold'})}
        
        xCoords = {'time':(['time'], timeBins), 'range':(['range'], ranges), 'type':(['type'], header)}
        
        attr = {'description':'This is an xarray for best thresholds at various ranges'}
        
        print('Creating dataset with', masterData, xCoords, attr)
        self.thresholds = xr.Dataset(data_vars=xData, coords=xCoords, attrs=attr)
        
        return
        
    def __str__(self):
        
        if self.thresholds:
            return str(self.thresholds)
        else:
            return 'No thresholds loaded'
            
        