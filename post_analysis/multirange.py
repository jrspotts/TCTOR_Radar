#Extention of grapher.py for calculating and coordinating the performance at multiple time bins and ranges. 

import grapher
import math
import random as rand
import stats2
import os

class BestThresholds:

    class Threshold:
        
        def __init__(self, type, threshold, tss, samplestring, rangeTuple, minSampleSize):
            self.type = type
            self.threshold = threshold 
            self.rangeTuple = rangeTuple 
            self.tss = tss
            self.samplestring = samplestring #The NON TOR/TOR samples used in calculating the best threshold/TSS
            
            #This next part is redundant
            if samplestring.upper() == 'NA': #If NA, we may be using time bins for thresholds. No sample size information
                self.samplestring = ''
                self.nonTorSampleSize = 0
                self.torSampleSize = 0
                self.thresholdString = str(self.threshold)
            else:
                splitSampleString = samplestring.split('-')
                self.nonTorSampleSize = int(splitSampleString[0])
                self.torSampleSize = int(splitSampleString[1])
                self.thresholdString = str(self.threshold)+'/'+str(self.tss)+'/'+str(self.samplestring) #String representation of the threshold
            
            self.bin = None #Optional bin for the threshold to be used with the best overall threshold
            self.metMinSamples = self.nonTorSampleSize >= minSampleSize and self.torSampleSize >= minSampleSize
            
            return
            
    def __init__(self, bin, writeFileBase, minSampleSize):
        
        self.bin = bin
        self.writeDir = 'best_thresholds'
        self.readFile = writeFileBase+'_'+str(bin)+'.csv'
        self.writeFile = os.path.join(self.writeDir, writeFileBase+'_'+str(bin)+'.csv')
        self.rangeTuples = []
        self.minSampleSize = minSampleSize
        
        try:
            os.mkdir(self.writeDir)
        except FileExistsError:
            pass
            
            
        self.thresholds = {}
        
        return
        
    def __repr__(self):
    
        sortedTypes = sorted(list(self.thresholds.keys()))
        sortedRangeTuple = sorted(list(self.rangeTuples))
        
        reprString = '\t\t'+'\t\t'.join(map(str, sortedTypes))+'\n'
        
        for rangeTuple in sortedRangeTuple:
        
            reprString += str(rangeTuple)+'\t'
            
            for type in sortedTypes:
                
                if rangeTuple not in list(self.thresholds[type].keys()):
                    reprString += 'NA\t\t'
                    if type == sortedTypes[-1]:
                        reprString += '\n'
                    continue
                
                
                tssPreString = self.thresholds[type][rangeTuple].tss
                if isinstance(tssPreString, float) or isinstance(tssPreString, int):
                    tssPreString = round(tssPreString, 3)
                    
                reprString += str(self.thresholds[type][rangeTuple].threshold)+\
                                '/'+str(tssPreString)+\
                                '/'+str(self.thresholds[type][rangeTuple].samplestring)+'\t'
                    
                
                if type == sortedTypes[-1]:
                    reprString += '\n'
                    
                    
        return reprString
                    
    def getRangeTuple(self, clusterRange):
    
        maxRange = 0
        for currentRangeTuple in self.rangeTuples:
            if clusterRange >= currentRangeTuple[0] and clusterRange < currentRangeTuple[1]:
                print('Found range tuple', currentRangeTuple, 'for', clusterRange)
                return currentRangeTuple
                
            if currentRangeTuple[1] > maxRange:
                maxRange = currentRangeTuple[1]
                
        if clusterRange > maxRange:
            return 'high'
        elif clusterRange < 0:
            return 'low'
        
        
        
        return None
        
        
    def addThreshold(self, type, threshold, tss, samplestring, rangeTuple):
    
        try:
            self.thresholds[type][rangeTuple] = self.Threshold(type, threshold, tss, samplestring, rangeTuple, self.minSampleSize)
        except KeyError as ke:
            print('addThreshold key error', ke)
            self.thresholds[type] = {rangeTuple:self.Threshold(type, threshold, tss, samplestring, rangeTuple, self.minSampleSize)}
        
        if rangeTuple not in self.rangeTuples:
            self.rangeTuples.append(rangeTuple)
            
        return
    
    def writeToCSV(self, alternateWriteFile=None):
        
        """alternateWriteFile can be specified to write to instead of the default filename. Remember to include the directory."""
        
        
        writeFileName = self.writeFile
        
        if alternateWriteFile:
            writeFileName = alternateWriteFile
            
            
        with open(writeFileName, 'w') as fi:
        
            sortedTypes = sorted(list(self.thresholds.keys()))

            fi.write(','+','.join(map(str, sortedTypes))+'\n')
            
            sortedRangeTuple = sorted(list(self.rangeTuples))
            
            toWriteString = ''
            
            for rangeTuple in sortedRangeTuple:
                
                toWriteString += str(rangeTuple).replace(',', '_')+','
                
                for type in sortedTypes:
                
                    #Handle cases where there is no valid data
                    if rangeTuple not in list(self.thresholds[type].keys()):
                        toWriteString += 'NA,'
                        if type == sortedTypes[-1]:
                            toWriteString += '\n'
                        continue
                    
                    toWriteString += self.thresholds[type][rangeTuple].thresholdString
                    
                    if type == sortedTypes[-1]:
                        toWriteString += '\n'
                    else:
                        toWriteString += ','
                        
            fi.write(toWriteString)
                        
                        
        return
        
        
    def readFromCSV(self):
        
        """Initializes the class from a CSV written in the format of writeToCSV()"""
        
        #Don't allow a BestThresholds object to be double intiated
        if self.thresholds:
            raise Exception("Can only initiate an empty BestThresholds object from CSV. Bin="+str(self.bin))
            
            
        with open(os.path.join(self.writeDir, self.readFile), 'r') as fi:
        
            isFirst = True
            readTypes = []
            
            for line in fi:
                
                if isFirst:
                    
                    readTypes = line.rstrip('\n').split(',')[1:]
                    isFirst = False
                    
                else:
                    
                    splitLine = line.rstrip('\n').split(',')
                    
                    currentRangeTuple = tuple(map(float, splitLine[0].strip('()').split('_')))
                    
                    for currentType in readTypes:
                    
                        typeIndex = readTypes.index(currentType)+1
                        
                        thresholdElements = splitLine[typeIndex].split('/')
                        
                        
                        if 'NA' not in thresholdElements:
                            self.addThreshold(currentType, int(thresholdElements[0]), float(thresholdElements[1]), thresholdElements[2], currentRangeTuple)
                        
        print('Loaded CSV for bin ', self.bin, '\n', repr(self), sep='')
        
        return
                    
        
        
def getRanges(distRanges, numRangeBins, saveFile=None):

   
    bottomRangeAdjusted = 0 #Changed to 0 since the first bin should start at 0 anyway
    
    topRange = distRanges[1]    
    topRangeAdjusted = math.ceil(topRange/10) * 10
 
    
    print('Splitting ranges', distRanges, 'into', numRangeBins, 'bins from', bottomRangeAdjusted, 'to', topRangeAdjusted)
    
    rangeBreaks = tuple([bottomRangeAdjusted + ((x/numRangeBins)*(topRangeAdjusted - bottomRangeAdjusted)) for x in range(1, numRangeBins)])
    
    if saveFile:
        if not saveFile.endswith('.csv'):
            raise ValueError("saveFile keyword arg in getRanges() must end in .csv")
        
        with open(saveFile, 'w') as fi:
            fi.write(','.join(map(str, rangeBreaks))+'\n')
            
    
    return rangeBreaks, bottomRangeAdjusted, topRangeAdjusted


def determineRangeBin(clusterRange, rangeBreaks):


    for bin in range(1, len(rangeBreaks)):
        if clusterRange >= rangeBreaks[bin-1] and clusterRange < rangeBreaks[bin]:
            return bin
        elif clusterRange < rangeBreaks[0]:
            return 0
        elif clusterRange >= rangeBreaks[len(rangeBreaks)-1]:
            return len(rangeBreaks)
    
    raise ValueError("Could not determine range bin for "+str(clusterRange))
    
    return
            
            
def getStaggeredIndices(bin, lenRangeBreaks):


    index1 = int(bin) - 1
    index2 = int(bin)
    if index1 < 0:
        index1 = index1 + lenRangeBreaks
    if index2 < 0:
        index2 = index2 + lenRangeBreaks
        
    return index1, index2
                
                
def printBinnedCount(binnedData, rangeBreaks):

    print('Total binned dict', binnedData)
    
    for bin,dataList in binnedData.items():
        if int(bin) == 0:
            print('< ', rangeBreaks[int(bin)], 'count is', len(dataList))
        elif int(bin) == len(rangeBreaks):
            print('>=', rangeBreaks[int(bin)-1], 'count is', len(dataList))
        else:

            listLength = len(dataList)
            
            index1, index2 = getStaggeredIndices(bin, len(rangeBreaks))
            
            firstRange = rangeBreaks[index1]
            secondRange = rangeBreaks[index2]
            
            if firstRange > secondRange:
                firstRange, secondRange = secondRange, firstRange
                
                
            print('  ', firstRange, 'to', secondRange, 'count is', listLength)
            
    return
    
    
def sortToBin(dataTuples, rangeBreaks):

    binnedData = {}
    
    for currentData,currentRange in dataTuples:
        currentRangeBin = determineRangeBin(currentRange, rangeBreaks)
        print(currentData, 'with range', currentRange, 'which is bin', currentRangeBin)
        binnedData.setdefault(currentRangeBin, []).append(currentData)
        
    printBinnedCount(binnedData, rangeBreaks)
    
    return binnedData
    
def createTestRangeData(minRange, maxRange, minData, maxData, numSamples):

    return [(minData + (rand.random() * (maxData - minData)), minRange + (rand.random() * (maxRange - minRange))) for x in range(numSamples)]
    
def printTestRangeData(dataList):
    
    for dataTuple in dataList:
        print(dataTuple)
        
    return
    
def generateRangeFigureTitle(dataType, bin, tilt, cfg):

    titleData = ''
    titleTilt = ''
    titleBin = ''
    if dataType == 'posvrot':
        titleData = 'Cyclonic Case Vrot '
    
    titleTilt = str(tilt)+'$^\circ$ '
    
    titleBin = str(int(float(bin) * cfg.timeBinSize))+' Minutes'
    
    return titleTilt+titleData+'at '+titleBin+' Best TSS by Range'

def initBestThresholds(bins, cfg):

    bestThresholds = {}
    
    for bin in sorted(list(bins)):
    
        bestThresholds[bin] = BestThresholds(bin, cfg.bestthreshfilebase, cfg.minTSSSamples)
        
    return bestThresholds

def getBins(nonTor, allTor, dataType, hasTilts=False):

    """ Returns all bins between all tilts for the datatype. hasTilts is True if all tilts need to be checked"""
    
    bins = []
    
    if hasTilts:
        for currentTilt in list(nonTor.keys()):
            
            if currentTilt not in list(allTor.keys()):
                continue
                
            for bin in sorted(list(nonTor[currentTilt][dataType].keys())):
            
                if bin not in bins:
                    bins.append(bin)
                    
        return sorted(bins)
        
    else:
        
        for bin in sorted(list(nonTor[dataType].keys())):
        
            if bin not in list(allTor[dataType].keys()):
                print(bin, 'not in tor datatype', dataType, '. Skipping')
                continue
                
            if bin not in bins:
                bins.append(bin)
                
    return sorted(bins)
        
        
                    
        
def getRangeBinTuple(rangeBinIndex, rangeBreakPoints, minRange, maxRange):

    rangeBinTuple = ()
    if rangeBinIndex == 0:
        rangeBinTuple = (minRange, rangeBreakPoints[0])
    elif rangeBinIndex == len(rangeBreakPoints):
        rangeBinTuple = (rangeBreakPoints[-1], maxRange)
    else:
        rangeBinTuple = (rangeBreakPoints[rangeBinIndex-1], rangeBreakPoints[rangeBinIndex])
                        
    return rangeBinTuple

def getNonTiltBestThresholds(thresholdObjects, nonTor, allTor, dataTypes, generalType, rangeBreakPoints, minRange, maxRange, cfg, minThreshold=0, maxThreshold=50000, thresholdIncrement=50):

    """Updates thresholdObjects (a dictionary of BestThresholds objects with time bin keys) using dataTypes from nonTor and allTor.
    generalType is used in the file naming. For calculating the TSS, min and maxThreshold define the range to check and thresholdIncrement is the increment.
    Returns the updated thresholdObjects.
    """
    if nonTor and allTor:

        if generalType.upper() != 'ET' and generalType.upper() != 'VIL':
            raise Exception('Unknown generalType for getNonTiltBestThresholds() '+str(generalType)+'. Must be ET or VIL.')
            
        for dataType in dataTypes:
            bins = getBins(nonTor, allTor, dataType, hasTilts=False)
            
            for bin in bins:
                tssStats = stats2.calculateVrotTSS(nonTor[dataType][bin], allTor[dataType][bin],\
                                                    initialThreshold=minThreshold, maxThreshold=maxThreshold, thresholdIncrement=thresholdIncrement,\
                                                    writeMode='w', writeFile=str(generalType)+'_TSS_'+str(dataType)+'_'+str(bin)+'.csv',
                                                    group1Name='NON TOR', group2Name='TOR')
                                                    
                unpackedTSSStats = grapher.unpackTSS(tssStats)
                maxTSS = max(unpackedTSSStats[0])
                maxTSSIndex = unpackedTSSStats[0].index(maxTSS)
                tssThresholdMax = unpackedTSSStats[4][maxTSSIndex]
                print('Found max TSS', maxTSS, 'at threshold', tssThresholdMax, 'for', generalType, dataType, 'and time bin', bin)
                
                numNonTor = len(nonTor[dataType][bin])
                numTor = len(allTor[dataType][bin])
                
                #Non-Tilt variables are not range dependent, but the same values are entered for each range bin
                for rangeBinIndex in range(len(rangeBreakPoints)+1):
                    rangeTuple = getRangeBinTuple(rangeBinIndex, rangeBreakPoints, minRange, maxRange)
                    try:
                        thresholdObjects[str(bin)].addThreshold(str(generalType)+'_'+str(dataType), tssThresholdMax, maxTSS,\
                                                        str(numNonTor)+'-'+str(numTor), rangeTuple)
                    except KeyError:
                        thresholdObjects[str(bin)] = BestThresholds(bin, cfg.besthreshfilebase)
                        thresholdObjects[str(bin)].addThreshold(str(generalType)+'_'+str(dataType), tssThresholdMax, maxTSS,\
                                                        str(numNonTor)+'-'+str(numTor), rangeTuple)
                                                       
                                                       
        return thresholdObjects
        
    else:
        raise ValueError('nonTor or allTor missing from getNonTiltBestThresholds')
            
    return

    
def processRangeData(nonTorRot, allTorRot, dataTypes, cfg, rangeBreakPoints, minRange, maxRange, nonTorET=None, allTorET=None, nonTorVIL=None, allTorVIL=None, vilDataTypes=None, etDataTypes=None):

    """ Calculates an writes best descriminators and generates scatterplots for the multi-range data"""
    
    
    bestThresholdObjects = {}
    bestThresholdStats = {}
    for dataType in dataTypes:
        
        binsForTilts = getBins(nonTorRot, allTorRot, dataType, hasTilts=True)
        print('Bins for', dataType, 'is', binsForTilts)
        bestThresholdObjects = initBestThresholds(binsForTilts, cfg)
        
        bestThresholdStats[dataType] = {}
        
        for currentTilt in list(nonTorRot.keys()):
            if currentTilt not in list(allTorRot.keys()):
                print('Warning!', currentTilt, 'tilt not in allTorRot. Skipping')
                continue
            
            bestThresholdStats[dataType][currentTilt] = {}
            
            for bin in binsForTilts:

                bestThresholdStats[dataType][currentTilt][str(bin)] = {}
                
                if bin not in list(allTorRot[currentTilt][dataType].keys()):
                    print('Warning!', bin, 'time bin not in allTorRot tilt', currentTilt,' Skipping!')
                    continue
                
                nonTorBinned1 = sortToBin(nonTorRot[currentTilt][dataType][bin], rangeBreakPoints)
                torBinned1 = sortToBin(allTorRot[currentTilt][dataType][bin], rangeBreakPoints)
                
                rangeBinnedTSSThresholds = {}
                for rangeBinIndex in range(len(rangeBreakPoints)+1):
                    if rangeBinIndex not in list(nonTorBinned1.keys()) or rangeBinIndex not in list(torBinned1.keys()):
                        print('Warning!', rangeBinIndex, 'not in sorted keys. Skipping TSS calculation for this range bin')
                        continue
                    
                    
                    rangeBinTuple = getRangeBinTuple(rangeBinIndex, rangeBreakPoints, minRange, maxRange)
                    
                    print('Calculating TSS for tilt', currentTilt, 'time bin', bin, 'and range bin', rangeBinIndex)
                    currentTSSStats = stats2.calculateVrotTSS(nonTorBinned1[rangeBinIndex], torBinned1[rangeBinIndex], writeMode='w', writeFile='RangedTSSStats_'+currentTilt+'_'+str(bin)+'_'+str(rangeBinIndex)+'.csv', group1Name='NON TOR', group2Name='TOR')
                    unpackedTSSStats = grapher.unpackTSS(currentTSSStats)
                    maxTSS = max(unpackedTSSStats[0])
                    maxTSSIndex = unpackedTSSStats[0].index(maxTSS)
                    tssThresholdMax = unpackedTSSStats[4][maxTSSIndex]
                    farThresholdMax = unpackedTSSStats[1][maxTSSIndex]
                    podThresholdMax = unpackedTSSStats[2][maxTSSIndex]
                    csiThresholdMax = unpackedTSSStats[3][maxTSSIndex]
                    
                    
                    
                    print('Found max TSS', maxTSS, 'at threshold', tssThresholdMax, 'for tilt', currentTilt, 'and time bin', bin)
                    rangeBinnedTSSThresholds[rangeBinIndex] = tssThresholdMax
                    
                    numNonTor = len(nonTorBinned1[rangeBinIndex])
                    numTor = len(torBinned1[rangeBinIndex])
                    bestThresholdObjects[bin].addThreshold(currentTilt, tssThresholdMax, maxTSS,\
                                                           str(numNonTor)+'-'+str(numTor), rangeBinTuple)
                                                           
                    bestThresholdStats[dataType][currentTilt][str(bin)][rangeBinTuple] = {\
                    'far':farThresholdMax, 'pod':podThresholdMax, 'csi':csiThresholdMax, 'tss':maxTSS, 'threshold':tssThresholdMax,\
                    'nontor':numNonTor, 'tor':numTor}
                    
                    
                
                currentTitle = generateRangeFigureTitle(dataType, bin, currentTilt, cfg)
                
                grapher.makeMultiRangePlots(nonTorRot[currentTilt][dataType][bin], allTorRot[currentTilt][dataType][bin], currentTitle, 'Range (n mi.)', 'V$_{rot}$ (kts)', currentTilt, 'multirange', rangeBinnedTSSThresholds, rangeBreakPoints)
    
                if dataType.lower() == 'posvrot':
               
                    grapher.makeMultirangeBinStatPlots(bestThresholdStats[dataType][currentTilt], currentTilt, 'kts', 'multirange', cfg)
                    
    #Calculate VIL and ET best thresholds and update the threshold objects
    bestThresholdObjects = getNonTiltBestThresholds(bestThresholdObjects, nonTorET, allTorET, etDataTypes, 'ET', rangeBreakPoints, minRange, maxRange, cfg,\
                                                    minThreshold=10000, maxThreshold=40000, thresholdIncrement=500)
    bestThresholdObjects = getNonTiltBestThresholds(bestThresholdObjects, nonTorVIL, allTorVIL, vilDataTypes, 'VIL', rangeBreakPoints, minRange, maxRange, cfg,\
                                                    minThreshold=0, maxThreshold=40, thresholdIncrement=1)
            
    
    for thresholdObj in list(bestThresholdObjects.values()):
        print('Repr for bin', thresholdObj.bin)
        print(repr(thresholdObj))
        
        #Only write to CSV if there are values to write
        if thresholdObj.thresholds:
            thresholdObj.writeToCSV()
    
    return 
    
    
def multirange(nonTorRot, allTorRot, dataTypes, cfg, axRanges, nonTorET=None, allTorET=None, nonTorVIL=None, allTorVIL=None, vilDataTypes=None, etDataTypes=None):

    if not cfg.multirange:
        print('Multirange is disabled. Skipping!')
        return
    
    print('Starting multirange')
    
    if nonTorET:
        print('nonTorET loaded.')
    if allTorET:
        print('allTorET loaded.')
    if (nonTorET and not allTorET) or (allTorET and not nonTorET):
        raise Exception('Need both NON TOR and ALL TOR ET loaded.')
    if (nonTorET or allTorET) and not etDataTypes:
        raise Exception('ET data types not loaded.')
    if nonTorVIL:
        print('nonTorVIL loaded.')
    if allTorVIL:
        print('allTorVIL loaded.')
    if (nonTorVIL and not allTorVIL) or (allTorVIL and not nonTorVIL):
        raise Exception('Need both NON TOR and ALL TOR VIL loaded.')
    if (nonTorVIL or allTorVIL) and not vilDataTypes:
        raise Exception('VIL data types not loaded.')
        
    
    rangeBreakPoints, minRange, maxRange = getRanges(axRanges.getRange('distrange'), cfg.rangebins, saveFile='rangebreaks.csv')
    print('Multirange has found range breakpoints', rangeBreakPoints)

    processRangeData(nonTorRot, allTorRot, dataTypes, cfg, rangeBreakPoints, minRange, maxRange, nonTorET=nonTorET, allTorET=allTorET, nonTorVIL=nonTorVIL, allTorVIL=allTorVIL, vilDataTypes=vilDataTypes, etDataTypes=etDataTypes)
    
    
    
    return

