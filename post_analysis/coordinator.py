#This module holds the classes and functions to test the compairsons between tornadic and nontornadic cases.

#Justin Spotts started 7-2-2022 

import sorting
import copy
import math
import stats2
import warnings
import numpy as np

class AxisRanges():

    def __init__(self):
    
        """ Holds the maximum and minimum y-axis values for each group. Having a centralized value can help keep figure axis consistent. 
        
            Attributes:
            ranges (dict): Key is the group (e.g., azshear) and the value represents the maximum and minimum values for the axis. 
                            The maximum and minimum are given as the tuple (min, max)
            masterLists(dict): Key is the group and the value is a running list of all values for that group
            standardDevs(dict): Key is the group and the value is the standard deviation of that group
            means(dict): Key is the group and the value is the mean of that group
        """
        
        self.__ranges = {}
        self.__masterLists = {}
        self.__standardDevs = {}
        self.__means = {}
        
        return
    
    def getGroups(self):
        return list(self.__ranges.keys())
        
    def getRange(self, group):
        return self.__ranges[group]
        
    def setRange(self, group, min, max):
        
        #If the desired group already exists then update the range with the more extreme values
        if group in list(self.__ranges.keys()):
            if min > self.__ranges[group][0]:
                print('Keeping group', group, 'minimum at', self.__ranges[group][0])
                min = self.__ranges[group][0]
            else:
                print('Updating group', group, 'minimum to', min)
            if max < self.__ranges[group][1]:
                print('Keeping group', group, 'maximum at', self.__ranges[group][1])
                max = self.__ranges[group][1]
            else:
                print('Updating group', group, 'maximum to', max)
                
        self.__ranges[group] = (min, max)
        
        return
    def extendList(self, group, extention):
        
        if group in list(self.__masterLists.keys()):
            for item in extention:
                self.__masterLists[group].append(item)
                
        else:
            self.__masterLists[group]=extention
            
        return
        
    def calculateStats(self, group):
        """ Once the master list has been created, calculate the standard deviation and delete the master list to conserve memory """
        
        #Calculate the standard deviation
        print('Calculating stats from', group, self.__masterLists[group])
        self.__standardDevs[group] = np.std(self.__masterLists[group])
        self.__means[group] = np.mean(self.__masterLists[group])
        
        print('Calculated mean', self.__means[group], 'standard deviation of', self.__standardDevs[group], 'for group', group)
        
        #Delete the list to save memory
        del self.__masterLists[group]
        
        return
        
    def getStd(self, group):
        return self.__standardDevs[group]
        
    def getMean(self, group):
        return self.__means[group]
        
    def updateRanges(self, group, maxSD):
        """ Updates the ranges so that they must fall within maxSD standard deviations of the mean. If calculateStats has 
            not been called yet, then a warning is issued and the ranges are not updated.
        """
        
        if not self.__means[group] or not self.__standardDevs[group]:
            warning.warn("Cannot update ranges. One or more stats not available. Please run calculateStats")
            return
            
        ranges = list(self.__ranges[group])
        mean = self.__means[group]
        std = self.__standardDevs[group]
        
        newMin = mean - (maxSD*std)
        newMax = mean + (maxSD*std)
        
        if newMin > ranges[0]:
            ranges[0] = newMin
            
        if newMax < ranges[1]:
            ranges[1] = newMax
          
        print('Uptating ranges for', group, 'from', self.__ranges[group], 'to', ranges)
        self.__ranges[group] = tuple(ranges)

        
        return
        
def getETVILValues(data, alias, currentRanges):

    """ Adds maximum and minimum values to the current range object for ET and VIL formats.
    
        Arguments:
        data(dict): The current data dictionary from where values are appended from.
        alias(str): The alias for the data
        currentRanges(AxisRanges): The running AxisRanges object for which to append the values to.
        
        Returns:
        currentRanges: The modified AxisRanges object.
        
    """
    
    #If the dataname is not present, the alias list may not be setup correctly. Stop the program and nontify the user
    for product in list(data.keys()):
    
        runningMax = -math.inf
        runningMin = math.inf
        totalValues = 0

        originalProduct = product
        
        groupName = ''
        
        if stats2.checkAllEqualOr(product.lower(), 'maxet', '90thet') and stats2.checkAllEqualOr(alias.lower(), 'poset', 'et'):
            groupName = 'et'
        elif stats2.checkAllEqualOr(product.lower(), 'avgvil', 'maxvil') and stats2.checkAllEqualOr(alias.lower(), 'posvil', 'vil'):
            groupName = 'vil'
        elif stats2.checkAllEqualOr(product.lower(), 'maxet', '90thet') and stats2.checkAllEqualOr(alias.lower(), 'ettrends', 'posettrends'):
            groupName = 'ettrends'
        elif stats2.checkAllEqualOr(product.lower(), 'avgvil', 'maxvil') and stats2.checkAllEqualOr(alias.lower(), 'viltrends', 'posviltrends'):
            groupName = 'viltrends'
        elif stats2.checkAllEqualOr(product.lower(), 'maxref') and stats2.checkAllEqualOr(alias.lower(), 'posvil', 'vil'):
            groupName = 'maxref'
        elif stats2.checkAllEqualOr(product.lower(), 'maxref') and stats2.checkAllEqualOr(alias.lower(), 'posviltrends', 'viltrends'):
            groupName = 'maxreftrends'
            
        if not groupName:
            raise ValueError("No groupname for "+str(alias)+" "+str(product))
        
        print('Getting range for', groupName)
        currentList = []
        for binList in list(data[originalProduct].values()):
            for item in binList:
                currentList.append(item)
        
        runningMax = max(currentList)
        runningMin = min(currentList)
        totalValues = len(currentList)
        
        print('Found minimum', runningMin, 'and maximum', runningMax, 'from', totalValues, 'values for group', groupName)
        currentRanges.setRange(groupName, runningMin, runningMax)
        currentRanges.extendList(groupName, currentList)
    
    return currentRanges
        

def getAzShearClusterValues(data, alias, tiltList, currentRanges):

    """ Adds maximum and minimum values from the AzShear cluster to the AxisRanges object. 
        
        Arguments:
        data(dict): The current data dictionary from where values are appended from.
        alias(str): The alias for the data
        tiltList(list): The list of elevation angles used. 
        currentRanges(AxisRanges): The running AxisRanges object for which to append the values to.
        
        Returns:
        currentRanges: The modified AxisRanges object. 
        
    """
    
    #Try to get products from the 0.5 deg tilt. Since everything is iterated for each product, products need to be 
    #at the top of the loop.
    for product in list(data[tiltList[0]].keys()):
        
        runningMax = -math.inf
        runningMin = math.inf
        totalValues = 0
        
        originalProduct = product
        
        if stats2.checkAllEqualOr(product.lower(), 'posazshear', 'absshear'):
            product = 'posazshear'
        elif stats2.checkAllEqualOr(product.lower(), 'azshear', '90thazshear', '10thazshear'):
            product = 'azshear'
        elif stats2.checkAllEqualOr(product.lower(), 'spectrumwidth', 'posspectrumwidth'):
            product = 'spectrumwidth'
        elif stats2.checkAllEqualOr(product.lower(), 'vrot', 'posvrot'):
            product = 'vrot'
        
        groupName = alias+product
        
        print('Getting range for', groupName)
        
        currentList = []
        for tilt in tiltList:
            for binList in list(data[tilt][product].values()):
                for item in binList:
                    currentList.append(item)
                
        runningMax = max(currentList)
        runningMin = min(currentList)
        totalValues = len(currentList)
        
        print('Found minimum', runningMin, 'and maximum', runningMax, 'from', totalValues, 'values for group', groupName)
        currentRanges.setRange(groupName, runningMin, runningMax)
        currentRanges.extendList(groupName, currentList)
        
    return currentRanges
            
def getAzShearRange(data, alias, tiltList, currentRanges):
    """ Gather the maximum and minimum range from the nearest radar for AzShear clusters and add them to the running AxisRanges object.
    
     Arguments:
        data(dict): The current data dictionary from where values are appended from.
        alias(str): The alias for the data
        tiltList(list): The list of elevation angles used. 
        currentRanges(AxisRanges): The running AxisRanges object for which to append the values to.
        
        Returns:
        currentRanges: The modified AxisRanges object. 
        
    """
    
    #Since we are only retrieving one value from the cluster, we'll just use the 'azshear' product
    
    runningMax = -math.inf
    runningMin = math.inf
    totalValues = 0
    
    print('Getting range for AzShear cluster ranges')
    
    for tilt in tiltList:
        for binList in list(data[tilt]['azshear'].values()):
        
            for values in binList:
                if values[1] < runningMin:
                    runningMin = values[1]
                if values[1] > runningMax:
                    runningMax = values[1]
                
        totalValues += len(binList)
            
    print('Found minimum', runningMin, 'n mi. and maximum', runningMax, 'n mi. from', totalValues, 'total values for range from radar')
    currentRanges.setRange('distrange', runningMin, runningMax)
    
    return currentRanges
    
        
def createAxisRanges(dataList, tiltList, aliases, cfg):
    """ 
       Finds the absolute maximum and minimum value for a particular data type across all data. Stores the result in a AxisRanges object which is returned.
       
       Arguments:
       dataList(list): A list of data dictionaries to check and derive the maximum and minimum from
       tiltList(list): List of elevation angles to loop through. Should match the tilts used as keys in the data dicts
       aliases(dict): Dictionary of aliases for the data categories (e.g., {'Cyclonic Case Echo Tops':'poset'})
       
       Returns:
       AxisRanges
    """
    axisRangesObject = AxisRanges()
        
    #Go through each tilt, then data list, then bin
    for data in dataList:
        
        for dataKey in list(data.keys()):
            
            print('Beginning to check', dataKey)
            
            #If that's not a desired data key then try the next one
            if dataKey not in list(aliases.keys()):
                print(dataKey, 'not in specified aliases. Trying next key.')
                continue
            
            if stats2.checkAllEqualOr(aliases[dataKey].upper(), 'ET', 'POSET', 'VIL', 'POSVIL', 'ETTRENDS', 'POSETTRENDS', 'VILTRENDS', 'POSVILTRENDS') :
                axisRangesObject = getETVILValues(data[dataKey], aliases[dataKey], axisRangesObject)
            elif stats2.checkAllEqualOr(aliases[dataKey].upper(), 'AZSHEAR', 'AZSHEARTRENDS'):
                axisRangesObject = getAzShearClusterValues(data[dataKey], aliases[dataKey], tiltList, axisRangesObject)
            elif aliases[dataKey].upper() == 'AZSHEARRANGE':
                axisRangesObject = getAzShearRange(data[dataKey], aliases[dataKey], tiltList, axisRangesObject)
                
                
                
    #If cfg.SD is sepcified, update the axis for each group (except for those not to be incldued).
    if cfg.SD:
        print('Updating axis ranges with a max SD of', cfg.SD)
        excludeGroups = ['distrange']
        for group in axisRangesObject.getGroups():
            if group not in excludeGroups:
                axisRangesObject.calculateStats(group)
                axisRangesObject.updateRanges(group, cfg.SD)

    return axisRangesObject

def getTDSCSI(nonTorObjects, torObjects, tilt, minBin, maxBin, minCount, maxCount, truthCases):

    """ Calculates the Critical Success Index (CSI) of TDS detection.
        The TDS detection method used is looking for a scan that meets the minimum number of TDS pixels (or count) at or after the target bin.
        The target bin is varied from minBin to maxBin. The minimum TDS count is varied from minCount to maxCount.
        truthCases is a list of strings for case IDs that should have a TDS.
        tilt is the elevation angle (probably the lowest) that is checked for the TDS pixels.
        The CSI is calculated according to Wilks 2019 equation 9.8 (CSI = a / (a+b+c))
        Where a is the number of truthCases that had a TDS detection.
        b is the number of TOR and NON TOR cases that had a TDS detection, but no TDS
        c is the number of truthCases that did not have a TDS detection
    """
    print('Starting TDS CSI Calculations')
    
    bestCSI = -1
    bestCSIBin = None
    bestCSICount = None
    
    #Itereate of the number of bins and count
    with open('tdscsi.csv', 'w') as fi:
        fi.write('CSI,bin,minCount\n')
        for bin in range(minBin, maxBin+1):
        
            
            for count in range(minCount, maxCount+1):
            
                a = 0
                b = 0
                c = 0
            
                #Break the tornadic objects into those with and without a TDS
                tdsObjects, noTDSObjects, nTDS = sorting.sortTDS(torObjects, tilt, startBin=bin, minCount=count)
                
                #Do the same thing for the nontor objects just to see how many end up with a TDS
                tdsNonTorObjects, noTDSNonTorObjects, nNonTorTDS = sorting.sortTDS(nonTorObjects, tilt, startBin=bin, minCount=count)
                
                #Get the TDS TOR Objects
                for TC in list(tdsObjects.keys()):
                    
                    for case in list(tdsObjects[TC].keys()):
                    
                        if case in truthCases:
                            a += 1
                            #print(case, 'had a correct TDS')
                        else:
                            b += 1    
                    for case2 in list(noTDSObjects[TC].keys()):
                        
                        if case2 in truthCases:
                            #print(case2, 'should have had a TDS, but did not')
                            c += 1
                            
                    #This case adds to the forecast, but not observed         
                    b += len(list(tdsNonTorObjects[TC].keys()))
                    
                    
                CSI = a/(a+b+c)
                
                if CSI > bestCSI:
                    bestCSI = CSI
                    bestCSIBin = bin
                    bestCSICount = count
                    
                fi.write(str(CSI)+','+str(bin)+','+str(count)+'\n')
                
                print('Calculated CSI', CSI, 'with abc', a, b, c, 'at', bin, count, ' Current best CSI with bin and count', bestCSI, bestCSIBin, bestCSICount)
            
    print('Done! The best CSI with bin and count was', bestCSI, bestCSIBin, bestCSICount)
    
    
    return bestCSI, bestCSIBin, bestCSICount
    
    
                    
def getMaxRotTD(autoObjects, tiltList):
    
    """ Returns the timedelta of the auto object with the maximum 0.5 deg absazshear """
    
    highestAzShear = -math.inf
    theTimedelta = None
    
    for auto in autoObjects:
        lowestTilt = auto.azShear[tiltList[0]]
        if lowestTilt.absShear > highestAzShear:
            highestAzShear = lowestTilt.absShear
            theTimedelta = lowestTilt.timeDelta
        elif lowestTilt.absShear == highestAzShear and abs(lowestTilt.timeDelta) < abs(theTimedelta):
            highestAzShear = lowestTilt.absShear
            theTimedelta = lowestTilt.timeDelta
    
    print('Found highest AzShear with timedelta', theTimedelta)
    
    return theTimedelta

def calculateBin(dt, binSpacing):
    
    dtMinutes = dt/60
    binNumber = round(dtMinutes/binSpacing)
    bin = binNumber * binSpacing
    
    return binNumber, bin
    
def shiftAndBins(dataObjects, tdShift, tiltList, cfg):

    dataObjectsCopy = copy.deepcopy(dataObjects)
    newDataObjects = []
    
    for auto in dataObjectsCopy:
        
        #Adjust the track time/bin
        if int(auto.trackTimeDelta) > -99900:
            print('Adjusting Track', auto.trackTimeDelta, auto.trackBin, auto.trackBinNumber, 'timebinsize', cfg.timeBinSize)
            auto.trackTimeDelta = auto.trackTimeDelta - tdShift
            newTrackBins = calculateBin(auto.trackTimeDelta, cfg.timeBinSize)
            auto.trackBinNumber = newTrackBins[0]
            auto.trackBin = newTrackBins[1]
            print('Now Track', auto.trackTimeDelta, auto.trackBin, auto.trackBinNumber)
        else:
            print('No track to adjust')
        
        
        #Adjust the echo-tops
        if int(auto.etTimeDelta) > -99900:
            print('Adjusting ET', auto.etTimeDelta, auto.etBin, auto.etBinNumber, 'timebinsize', cfg.timeBinSize)
            auto.etTimeDelta  = auto.etTimeDelta - tdShift
            newETBins = calculateBin(auto.etTimeDelta, cfg.timeBinSize)
            auto.etBinNumber = newETBins[0]
            auto.etBin = newETBins[1]
            print('Now ET', auto.etTimeDelta, auto.etBin, auto.etBinNumber)
        else:
            print('No ET to adjust')
        
        #Adjust all tilts
        for tilt in tiltList:
            if int(auto.azShear[tilt].timeDelta) > -99900:
                print('Adjusting tilt', tilt, auto.azShear[tilt].timeDelta, auto.azShear[tilt].minuteBin, auto.azShear[tilt].binNumber, 'timebinsize', cfg.timeBinSize)
                auto.azShear[tilt].timeDelta = auto.azShear[tilt].timeDelta - tdShift
                newTiltBins = calculateBin(auto.azShear[tilt].timeDelta, cfg.timeBinSize)
                auto.azShear[tilt].binNumber = newTiltBins[0]
                auto.azShear[tilt].minuteBin = newTiltBins[1]
                print('Now tilt', tilt, auto.azShear[tilt].timeDelta, auto.azShear[tilt].minuteBin, auto.azShear[tilt].binNumber)
            else:
                print('Tilt', tilt, 'is unavailable to be adjusted')
                
        newDataObjects.append(auto)
        
        
            
    return newDataObjects
    
def timeShiftObjects(dataObjects, tiltList, shiftAmount, cfg):

    """ For each case, find the volume with the maximum abs azshear and shift all timedeltas by that amount.
        With the new timedetlas calculate the new time bins. 
        
        WARNING!!! Object DateTimes are not adjusted, just the time deltas and bins
    """
    
    shiftedObjects = {}
    
    for TC in list(dataObjects.keys()):
        
        shiftedObjects[TC] = {}
        
        #Now loop through all the cases.
        for case in list(dataObjects[TC].keys()):
            
            print('Preparing to adjust case', TC, case)
            
            #Now go and get the timedelta of the case with the maximum absazshear
            tdShift = 0
            if shiftAmount.lower() == 'max':
                tdShift = getMaxRotTD(dataObjects[TC][case], tiltList)
            else:
                tdShift = int(shiftAmount)
            
            shiftedObjects[TC][case] = shiftAndBins(dataObjects[TC][case], tdShift, tiltList, cfg)
            
            
    return shiftedObjects
    
def getMaxRotTDByBin(autoObjects, tiltList, minbin, maxbin):
    
    """ Returns the timedelta of the auto object with the maximum 0.5 deg absazshear """
    
    highestAzShear = -math.inf
    theTimedelta = None
    
    for auto in autoObjects:
        lowestTilt = auto.azShear[tiltList[0]]
        meetsBinCriteria = int(lowestTilt.binNumber) >= minbin and int(lowestTilt.binNumber) <= maxbin
        #print(lowestTilt.binNumber, 'meets bin criteria?', meetsBinCriteria)
        
        if lowestTilt.absShear > highestAzShear and meetsBinCriteria:
            highestAzShear = lowestTilt.absShear
            theTimedelta = lowestTilt.timeDelta
        elif lowestTilt.absShear == highestAzShear and abs(lowestTilt.timeDelta) < abs(theTimedelta) and meetsBinCriteria:
            highestAzShear = lowestTilt.absShear
            theTimedelta = lowestTilt.timeDelta
    
    print('Found highest AzShear with timedelta', theTimedelta)
    
    return theTimedelta
    
def timeShiftByBin(dataObjects, tiltList, shiftAmount, minbin, maxbin, cfg):
    """ 
        Performs a time shift, but only on objects who's lowest tilt is between and including minbinb and maxbin 
   """
   
    print('Starting time shift by bin')
   
    shiftedObjects = {}

    for TC in list(dataObjects.keys()):

        shiftedObjects[TC] = {}

        #Loop through cases.
        for case in list(dataObjects[TC].keys()):

            print('Preparing to adjust case', TC, case, 'minbin maxbin', minbin, maxbin)
            
            #Get the TD of the maximum AzShear within the time bins
            tdShift = getMaxRotTDByBin(dataObjects[TC][case], tiltList, minbin, maxbin)
            
            #Now shift the objects. If shift is none, then just set the auto objects to an empty list for that case
            if tdShift is not None:
                shiftedObjects[TC][case] = shiftAndBins(dataObjects[TC][case], tdShift, tiltList, cfg)
            else:
                print('Shift was', tdShift, '. Setting to empty list')
                shiftedObjects[TC][case] = []
        
    return shiftedObjects
    
    
def getSortedData(autoObjects, tiltList, cfg):

    """
        This function will be used to call all of the functions necessary to test hypothese for Spotts (2022). This includes:
        1) Sorting all autoObject cases into tornadic and nontornadic groups
        2) Sorting all tornadic groups into TDS and NO TDS (determination of TDS previously determined)
        3) Sorting each group into their respective time bins
        4) Create boxplots for each tilt of the four categories and ALL for each time bin
        5) Create boxplots for each time bin on one plot (i.e., The x-axis is time, and at each time bin, there is a group of four boxplots)
        
    """
    
    #Break the objects into tornadic and nontornadic groups
    torObjects, nonTorObjects = sorting.sortTorNoTor(autoObjects)
    
    
    #Break the tornadic objects into those with and without a TDS
    print('Sorting by TDS for all tor')
    tdsObjects, noTDSObjects, nTDS, nNoTDS, tdsCountByEF, totalCountByEF = sorting.sortTDS(torObjects, tiltList[0], minCount=25, startBin=0)
    
    print('Sorting by TDS for Z-test')
    tdsObjects3, noTDSObjects3, nTDS3, nNoTDS3, tdsCountByEF3, totalCountByEF3 = sorting.sortTDS(torObjects, tiltList[0], minCount=25, startBin=0, potentialClusters=3, maxBeamHeight=cfg.maxAzShearHeight)
    
    tdsCountByEFDict = {'tdscount':tdsCountByEF3, 'totalcount':totalCountByEF3}
    
    #Do the same thing for the nontor objects just to see how many end up with a TDS
    print('Sorting by TDS for NON TOR')
    tdsNonTorObjects, noTDSNonTorObjects, nNonTorTDS, nNonTorNoTDS, nonTorTdsCountByEF, nonTorTotalCountByEF = sorting.sortTDS(nonTorObjects, tiltList[0], minCount=25, startBin=0, potentialClusters=3)
    
    #If desired, timeshift the objects before doing the final sorting of the data.
    #This happens after the TDS sorting since that sorting uses the zero-bin
    
    #Start with NON TOR
    if cfg.shiftNonTor:
        print('NON TOR time shifting...')
        nonTorObjects = timeShiftObjects(nonTorObjects, tiltList, cfg.nontorShiftAmount, cfg)
        print('NON TOR time shifting complete!')
        
    #If we want to time shift the TOR cases, we need to apply it to TOR, TOR TDS, and TOR NO TDS
    if cfg.shiftTor:
        print('TOR time shifting...')
        torObjects = timeShiftObjects(torObjects, tiltList, cfg.torShiftAmount, cfg)
        print('TDS time shifting...')
        tdsObjects = timeShiftObjects(tdsObjects, tiltList, cfg.torShiftAmount, cfg)
        print('NO TDS time shifting...')
        notdsObjects = timeShiftObjects(noTDSObjects, tiltList, cfg.torShiftAmount, cfg)
        print('TDS3 time shifting...')
        tdsObjects3 = timeShiftObjects(tdsObjects3, tiltList, cfg.torShiftAmount, cfg)
        print('NO TDS3 time shifting...')
        noTDSObjects3 = timeShiftObjects(noTDSObjects3, tiltList, cfg.torShiftAmount, cfg)
        
    #Print the number of TOR and NON TOR cases with a TDS
    print(nTDS3, 'TOR cases were found to have a TDS.', nNoTDS3, 'cases did not. TDS by EF', tdsCountByEF3, 'total by EF', totalCountByEF3)
    print(nNonTorTDS, 'NON TOR cases were found to have a TDS.', nNonTorNoTDS, 'cases did not. TDS by EF', nonTorTdsCountByEF, 'total by EF', nonTorTotalCountByEF)
    
    with open('case_numbers.csv', 'w') as fi:
        #Sort each group into individual time bins
        fi.write('group,casecount,negativecount,negativecases\n')
        print('Binning NON TOR--------------------------------')
        noTorBinned, ntCaseCount, noTorNegAzShearCount, ntNegAzShearCases = sorting.getObjectsByBin(nonTorObjects, tiltList, cfg)
        print('NON TOR BINNED', noTorBinned)
        fi.write(','.join(map(str, ['NON TOR', ntCaseCount, noTorNegAzShearCount, ntNegAzShearCases]))+'\n')
        print('Binning ALL TOR--------------------------------')
        torBinned, torCaseCount, torNegAzShearCount, torNegAzShearCases = sorting.getObjectsByBin(torObjects, tiltList, cfg, isTOR=True)
        print('TOR BINNED', torBinned)
        fi.write(','.join(map(str, ['ALL TOR', torCaseCount, torNegAzShearCount, torNegAzShearCases]))+'\n')
        print('Binning TOR TDS--------------------------------')
        tdsBinned, tdsCaseCount, tdsNegAzShearCount, tdsNegAzShearCases = sorting.getObjectsByBin(tdsObjects, tiltList, cfg, isTDS=True, isTOR=True)
        print('TDS BINNED', tdsBinned)
        fi.write(','.join(map(str, ['TOR TDS', tdsCaseCount, tdsNegAzShearCount, tdsNegAzShearCases]))+'\n')
        print('Binning TOR NO TDS-----------------------------')
        noTdsBinned, noTdsCaseCount, noTdsNegAzShearCount, noTDSNegAzShearCases = sorting.getObjectsByBin(noTDSObjects, tiltList, cfg, isTOR=True)
        print('NO TDS BINNED', noTdsBinned)
        fi.write(','.join(map(str, ['TOR NO TDS', noTdsCaseCount, noTdsNegAzShearCount, noTDSNegAzShearCases]))+'\n')
        
        #Sort each group into individual time bins, but only if there is 3 potential clusters
        print('Binning NON TOR Max 3--------------------------------')
        noTorBinnedOne, ntCaseCountOne, noTorNegAzShearCountOne, noTorNegAzShearCasesThree = sorting.getObjectsByBin(nonTorObjects, tiltList, cfg, maxPotentialClusters=3)
        print('NON TOR BINNED 3', noTorBinnedOne)
        fi.write(','.join(map(str, ['NON TOR 3', ntCaseCountOne, noTorNegAzShearCountOne, noTorNegAzShearCasesThree]))+'\n')
        print('Binning ALL TOR Max 3--------------------------------')
        torBinnedOne, torCaseCountOne, torNegAzShearCountOne, torNegAzShearCasesThree = sorting.getObjectsByBin(torObjects, tiltList, cfg, isTOR=True, maxPotentialClusters=3)
        print('TOR BINNED 3', torBinnedOne)
        fi.write(','.join(map(str, ['ALL TOR 3', torCaseCountOne, torNegAzShearCountOne, torNegAzShearCasesThree]))+'\n')
        print('Binning TOR TDS Max 3--------------------------------')
        tdsBinnedOne, tdsCaseCountOne, tdsNegAzShearCountOne, tdsNegAzShearCasesThree = sorting.getObjectsByBin(tdsObjects, tiltList, cfg, isTDS=True, isTOR=True, maxPotentialClusters=3)
        print('TDS TOR BINNED 3', tdsBinnedOne)
        fi.write(','.join(map(str, ['TOR TDS 3', tdsCaseCountOne, tdsNegAzShearCountOne, tdsNegAzShearCasesThree]))+'\n')
        print('Binning TOR NO TDS Max 3-----------------------------')
        noTdsBinnedOne, noTdsCaseCountOne, noTdsNegAzShearCountOne, noTDSNegAzShearCasesThree = sorting.getObjectsByBin(noTDSObjects, tiltList, cfg, isTOR=True, maxPotentialClusters=3)
        print('NO TDS TOR BINNED 3', noTdsBinnedOne)
        fi.write(','.join(map(str, ['TOR NO TDS 3', noTdsCaseCountOne, noTdsNegAzShearCountOne, noTDSNegAzShearCasesThree]))+'\n')
        
        
        #Calculate the CSI TDS. Only works if all TDS cases are known. Comment out for final analysis
        #getTDSCSI(nonTorObjects, torObjects, tiltList[0], -4, 4, 1, 30, ['615666', '615668', '615669', '615671', '615673', '615681', '615685', '615695',\
         #                                                                '615699', '615701', '615707', '615710', '615714', '615715', '615716', '615717', '615718'])
                                                                         
        totalCaseCount = ntCaseCount + torCaseCount
        totalNegAzShearCount = noTorNegAzShearCount + torNegAzShearCount
        fi.write(','.join(map(str, ['TOTAL', totalCaseCount, totalNegAzShearCount])))
        
    
    print('The grand total of cases is', totalCaseCount)
    print('The grand total cases for negative azshear at at least 1 tilt is', totalNegAzShearCount)
    
    binnedDataDict = {'nontor':noTorBinned, 'alltor':torBinned, 'tds':tdsBinned, 'notds':noTdsBinned, 'nontor3':noTorBinnedOne, 'alltor3':torBinnedOne, 'tds3':tdsBinnedOne, 'notds3':noTdsBinnedOne}
    caseCountDict = {'nontor':ntCaseCount, 'alltor':torCaseCount, 'tds':tdsCaseCount, 'notds':noTdsCaseCount, 'nontor3':ntCaseCountOne, 'alltor3':torCaseCountOne, 'tds3':tdsCaseCountOne, 'notds3':noTdsCaseCountOne}
    negCountDict = {'nontor':noTorNegAzShearCount, 'alltor':torNegAzShearCount, 'tds':tdsNegAzShearCount, 'notds':noTdsNegAzShearCount, 'nontor3':noTorNegAzShearCountOne, 'alltor3':torNegAzShearCountOne, 'tds3':tdsNegAzShearCountOne, 'notds3':noTdsNegAzShearCountOne}
    
    print('Case count dict', caseCountDict)
    return binnedDataDict, caseCountDict, negCountDict, tdsCountByEFDict
    