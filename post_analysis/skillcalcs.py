#Calculates theoretical warning statistics based on best True Skill Score thresholds.

import multirange as mr
import math
import os
import tests
from datetime import datetime as dt
import grapher
import stats2

class Tester:

    __slots__ = 'eligibleCriteria', 'thresholds', 'centralBin', 'secondBin', 'bestThresholds', 'testTypes', 'firstBestThreshold', 'secondBestThreshold', 'minPotentialClusters', 'vrotRadius',\
    'centralBestThreshold', 'secondBestThreshold', 'tiltList', 'maxBeamHeight'
    def __init__(self, centralBin, bestThresholds, tiltList, minPotentialClusters, radius, maxBeamHeight):
    
        self.thresholds = {}
        self.centralBin = str(centralBin)
        self.secondBin = str(int(centralBin) - 1)
        self.minPotentialClusters = minPotentialClusters
        
        self.maxBeamHeight = maxBeamHeight
        self.bestThresholds = bestThresholds
        
        self.vrotRadius = radius
        
        try:
            self.centralBestThreshold = self.bestThresholds[self.centralBin]
        except KeyError:
            raise Exception("Best threshold for time bin "+str(self.centralBin)+" does not exist")
            
        if tests.useSameThreshold:
            self.secondBestThreshold = self.firstBestThreshold
        else:
            try:
                self.secondBestThreshold = self.bestThresholds[self.secondBin]
            except KeyError:
                raise Exception("Best threshold for time bin "+str(self.secondBin)+" does not exist. Change the central bin or use the same threshold with tests.py->useSameThreshold")
        
        self.tiltList = tiltList
        print('Created tester for central bin', self.centralBin, 'and second bin', self.secondBin, 'use same', tests.useSameThreshold)
        
        return
        
  
     
    
    def initCountDict(self, testElements):
    
        newDict = {}
        
        for element in testElements:
            newDict[element] = 0
        
        return newDict
        
    def initBoolDict(self, testElements):
        
        newDict = {}
        
        for element in testElements:
            
            newDict[element] = False
        
        return newDict
        
    def testNegAzShear(self, autoObjects):
    
        for currentAuto in autoObjects:
        
            if not currentAuto.azShear['0.5'].isMax:
                return True
                
        return False
        
        
    def isItWarned(self, autoObjects, testElements, cfg, ignoreExtra=False):
    
        #Define initial return values
        isWarned = False
        noMinSampleCounts = self.initCountDict(testElements)
        secondBinCounts = self.initCountDict(testElements)
        noClusterCounts = self.initCountDict(testElements)
        potentialClusterCounts = self.initCountDict(testElements)
        bhCounts = self.initCountDict(testElements)
        usedSecondBinCounts = self.initCountDict(testElements)
        
        metWarningCriteria = self.initBoolDict(testElements)
        couldBeTested = self.initBoolDict(testElements)
        isNegAzShear = False
        isSuccess = False
        tiltRangeBin = None
        
        caseString = str(autoObjects[0].TC)+'-'+str(autoObjects[0].case)
        #For now we are excluding negative AzShear cases
        if self.testNegAzShear(autoObjects):
            isNegAzShear = True
            print('Case', caseString, 'has neg azshear')
            return isWarned, noMinSampleCounts, secondBinCounts, noClusterCounts, potentialClusterCounts, bhCounts, usedSecondBinCounts, tiltRangeBin, isNegAzShear, isSuccess
            
            
        for currentElement in testElements:
            #Determine if the test element is a for an elevation angle or extra by seeing if it can typecasted into a float
            isTilt = False
            try:
                dummyVar = str(float(currentElement))
                isTilt = True
            except ValueError:
                pass
                
            #Using 0 and 1 instead of True and False to make keeping count easier
            needsSecondBin = 0
            firstBinFound = 0
            noAvailableCluster = 0
            failsMinSamples = 0
            failedPotentialClusters = 0
            failedBH = 0
            usedSecondBin = 0
            
            if isTilt:
                
               
                #Determine which auto has the correct bin
                centralTiltObj = None
                secondTiltObj = None
                for currentAuto in autoObjects:
                    
                    currentTiltObj = currentAuto.azShear[currentElement]
                    
                    if str(currentTiltObj.binNumber) == self.centralBin:
                        if centralTiltObj:
                            if currentTiltObj.rVrots[self.vrotRadius] > centralTiltObj.rVrots[self.vrotRadius]:
                                print('Updating central bin for', caseString)
                                centralTiltObj = currentTiltObj
                        else:
                            centralTiltObj = currentTiltObj
                    if str(currentTiltObj.binNumber) == self.secondBin:
                        if secondTiltObj:
                            if currentTiltObj.rVrots[self.vrotRadius] > secondTiltObj.rVrots[self.vrotRadius]:
                                print('Updating second bin for', caseString)
                                secondTiltObj = currentTiltObj
                        else:       
                            secondTiltObj = currentTiltObj
                        
                if centralTiltObj:
                
                    if centralTiltObj.beamHeights['0'] >= 0 and centralTiltObj.beamHeights['0'] <= self.maxBeamHeight:
                       
                        if centralTiltObj.rVrots[self.vrotRadius]:
                        
                            
                            if (centralTiltObj.potentialClusters <= self.minPotentialClusters) or ignoreExtra:
                            
                                if (centralTiltObj.potentialClusters) < 0:
                                    raise Exception("Central tilt obj gave a negative potential cluster")
                                    
                                bestThresholdObj = self.bestThresholds[str(centralTiltObj.binNumber)]
                                
                                secondThresholdObj = None
                                if tests.useSameThreshold:
                                    secondThresholdObj = self.bestThresholds[str(centralTiltObj.binNumber)]
                                else:
                                    secondThresholdObj = self.bestThresholds[str(self.secondBin)]
                                
                                currentRangeTuple = bestThresholdObj.getRangeTuple(centralTiltObj.groundRanges['0'])
                                if currentRangeTuple == 'high' or currentRangeTuple == 'lower':
                                    raise Exception("Range out of bounds for "+caseString)
                                  
                                metSecondSamples = secondThresholdObj.thresholds[currentElement][currentRangeTuple].metMinSamples
                                
                                
                                targetThreshold = bestThresholdObj.thresholds[currentElement][currentRangeTuple].threshold
                                
                                if (bestThresholdObj.thresholds[currentElement][currentRangeTuple].metMinSamples and metSecondSamples):
                                    
                                    if centralTiltObj.rVrots[self.vrotRadius] >= targetThreshold:
                                        metWarningCriteria[currentElement] = True

                                    couldBeTested[currentElement] = True
                                    
                                    if str(currentElement) == str(self.tiltList[0]):
                                        tiltRangeBin = currentRangeTuple

                                else:
                                    failsMinSamples = 1

                            else:
                                failedPotentialClusters = 1
                        else:
                            raise Exception("Central bin failed rVrots")
                    else:
                        failedBH = 1
                        
                if not tests.useSameThreshold and not couldBeTested[currentElement]:
                    
                    needsSecondBin = 1
                    
                    if secondTiltObj:
                        
                        if secondTiltObj.beamHeights['0'] >= 0 and secondTiltObj.beamHeights['0'] <= self.maxBeamHeight:
                            if secondTiltObj.rVrots[self.vrotRadius]:
                                                            
                                if (secondTiltObj.potentialClusters <= self.minPotentialClusters) or ignoreExtra:
                                    

                                    bestThresholdObj = self.bestThresholds[str(secondTiltObj.binNumber)]
                                    
                                    centralThresholdObj = self.bestThresholds[str(self.centralBin)]
                                    currentRangeTuple = bestThresholdObj.getRangeTuple(secondTiltObj.groundRanges['0'])
                                    
                                    if currentRangeTuple == 'high' or currentRangeTuple == 'lower':
                                        raise Exception("Range out of bounds for "+caseString)
                                        
                                    metCentralSamples = centralThresholdObj.thresholds[currentElement][currentRangeTuple].metMinSamples
                                        
                                    targetThreshold = bestThresholdObj.thresholds[currentElement][currentRangeTuple].threshold
                                    
                                    if bestThresholdObj.thresholds[currentElement][currentRangeTuple].metMinSamples and metCentralSamples:
                                        if secondTiltObj.rVrots[self.vrotRadius] >= targetThreshold:
                                            metWarningCriteria[currentElement] = True

                                        couldBeTested[currentElement] = True
                                        usedSecondBin = 1
                                        
                                        if str(currentElement) == str(self.tiltList[0]):
                                            tiltRangeBin = currentRangeTuple
                                        
                                        if (secondTiltObj.potentialClusters < 0):
                                            #Count as warned if there are no potential clusters listed if ignoring extras
                                            #This is after the central tilt has been determined to be invalid
                                            if ignoreExtra:
                                                couldBeTested[currentElement] = True
                                                metWarningCriteria[currentElement] = True
                                                failedPotentialClusters = 1
                                                print("Second tilt object had negative potential clusters. Ignoring extras.")
                                            else:
                                                raise Exception("Second tilt object had negative potential clusters")
                                            
                                    else:
                                        failsMinSamples = 1

                                else:
                                    failedPotentialClusters = 1
                                    
                            else:
                                raise Exception("Second bin failed rVrots")
                                if not centralTiltObj:
                                    noAvailableCluster = 1
                        
                        else:
                            failedBH = 1
                    else:
                        if not centralTiltObj:
                            noAvailableCluster = 1
                            
                if not couldBeTested[currentElement]:
                    
                    
                    #For now, if we are ignoring extra criteria warn the case if it meets the same beamheight criteria as the real stats
                    if ignoreExtra and not bool(failsMinSamples) and not bool(failedBH):
                        receivedAuto = stats2.checkBeamHeight(autoObjects, self.tiltList, cfg, math.inf)
                        if receivedAuto is not None:
                            metWarningCriteria[currentElement] = True
                            couldBeTested[currentElement] = True
                            
                            #Get and use the range bin tuple assuming the central bin using the assumed auto
                            bestObj = self.bestThresholds[str(self.centralBin)]
                            thisRangeTuple = bestObj.getRangeTuple(receivedAuto.azShear[str(self.tiltList[0])].groundRanges['0'])
                            
                            if thisRangeTuple == 'high' or thisRangeTuple == 'lower':
                                raise Exception("Range out of bounds for "+caseString)
                             
                            if str(currentElement) == str(self.tiltList[0]):
                                tiltRangeBin = thisRangeTuple
  
            else:
                
                #If the test element is not a tilt, then it's VIL or ET. Determine which it is and pull the information for the test
                
                extraPotClusters = None
                extraValue = None
                extraBin = None
                
                if 'ET' in currentElement:
                    
                    for currentAuto in autoObjects:
                        if str(currentAuto.etBinNumber) == self.centralBin:
                        
           
                            if currentAuto.etPotentialClusters > -99900: tempPotClusters = currentAuto.etPotentialClusters
                            if int(currentAuto.etBinNumber) > -99900: tempBin = str(currentAuto.etBinNumber)
                            
                            if 'maxet' in currentElement.lower():
                                if extraValue:
                                    if currentAuto.maxETft > extraValue:
                                        print('Updating central maxet', caseString)
                                        extraValue = currentAuto.maxETft
                                        extraPotClusters = tempPotClusters
                                        extraBin = tempBin
                                else:
                                    extraValue = currentAuto.maxETft
                                    extraPotClusters = tempPotClusters
                                    extraBin = tempBin
                                    
                            elif '90thet' in currentElement.lower():
                                if extraValue:
                                    if currentAuto.top90ETft > extraValue:
                                        print('Updating central 90th ET', caseString)
                                        extraValue = currentAuto.top90ETft
                                        extraPotClusters = tempPotClusters
                                        extraBin = tempBin
                                else:
                                    extraValue = currentAuto.top90ETft
                                    extraPotClusters = tempPotClusters
                                    extraBin = tempBin
                            else:
                                raise Exception("Element "+str(currentElement)+" was not accounted for.")
                                
                                
                            
                            
                    if not extraPotClusters or not extraValue or not extraBin:
                        needsSecondBin = 1
                    
                    if (not extraPotClusters or not extraValue or not extraBin) and not tests.useSameThreshold:
                        
                        for currentAuto in autoObjects:
                            if str(currentAuto.etBinNumber) == self.secondBin:
                            
                                
                                if currentAuto.etPotentialClusters > -99900: tempPotClusters = currentAuto.etPotentialClusters
                                if int(currentAuto.etBinNumber) > -99900: tempBin = str(currentAuto.etBinNumber)
                                
                                if 'maxet' in currentElement.lower():
                                    if extraValue:
                                        if currentAuto.maxETft > extraValue:
                                            print('Updating second maxet', caseString)
                                            extraValue = currentAuto.maxETft
                                            extraPotClusters = tempPotClusters
                                            extraBin = tempBin
                                    else:
                                        extraValue = currentAuto.maxETft
                                        extraPotClusters = tempPotClusters
                                        extraBin = tempBin
                                        
                                elif '90thet' in currentElement.lower():
                                    if extraValue:
                                        if currentAuto.top90ETft > extraValue:
                                            print('Updating second 90th ET', caseString)
                                            extraValue = currentAuto.top90ETft
                                            extraPotClusters = tempPotClusters
                                            extraBin = tempBin
                                    else:
                                        extraValue = currentAuto.top90ETft
                                        extraPotClusters = tempPotClusters
                                        extraBin = tempBin
                                else:
                                    raise Exception("Element "+str(currentElement)+" was not accounted for.")
                                    
                            
                                    
                    #Check to see if values have been assigned. If values have not been assigned, then the valid cluster is likely not present
                    if not extraPotClusters or not extraValue or not extraBin:
                    
                        print('Did not have valid extra data potClusters, value, bin', extraPotClusters, extraValue, extraBin)
                        noAvailableCluster = 1
                        
                elif 'VIL' in currentElement:
                
                    for currentAuto in autoObjects:
                    
                        if str(currentAuto.trackBinNumber) == self.centralBin:
                            if currentAuto.trackPotentialClusters > -99900: tempPotClusters = currentAuto.trackPotentialClusters
                            if int(currentAuto.trackBinNumber) > -99900: tempBin = str(currentAuto.trackBinNumber)
                            
                            if 'maxvil' in currentElement.lower():
                                if extraValue:
                                    if currentAuto.trackMaxVIL > extraValue:
                                        print('Updating central maxvil', caseString)
                                        extraValue = currentAuto.trackMaxVIL
                                        extraPotClusters = tempPotClusters
                                        extraBin = tempBin
                                else:
                                    extraValue = currentAuto.trackMaxVIL
                                    extraPotClusters = tempPotClusters
                                    extraBin = tempBin
                                    
                            elif 'avgvil' in currentElement.lower():
                                if extraValue:
                                    if currentAuto.trackAvgVIL > extraValue:
                                        print('Updating central avgvil', caseString)
                                        extraValue = currentAuto.trackAvgVIL
                                        extraPotClusters = tempPotClusters
                                        extraBin = tempBin
                                else:
                                    extraValue = currentAuto.trackAvgVIL
                                    extraPotClusters = tempPotClusters
                                    extraBin = tempBin
                            else:
                                raise Exception("Element "+str(currentElement)+" was not accounted for.")
                                
                            
                    
                    if not extraPotClusters or not extraValue or not extraBin:
                        needsSecondBin = 1
                        
                    if (not extraPotClusters or not extraValue or not extraBin) and not tests.useSameThreshold:
                    
                        for currentAuto in autoObjects:
                            
                            if str(currentAuto.trackBinNumber) == self.secondBin:
                                if currentAuto.trackPotentialClusters > -99900: tempPotClusters = currentAuto.trackPotentialClusters
                                if int(currentAuto.trackBinNumber) > -99900: tempBin = str(currentAuto.trackBinNumber)
                                
                                if 'maxvil' in currentElement.lower():
                                    if extraValue:
                                        if currentAuto.trackMaxVIL > extraValue:
                                            print('Updating second maxvil', caseString)
                                            extraValue = currentAuto.trackMaxVIL
                                            extraPotClusters = tempPotClusters
                                            extraBin = tempBin
                                    else:
                                        extraValue = currentAuto.trackMaxVIL
                                        extraPotClusters = tempPotClusters
                                        extraBin = tempBin
                                elif 'avgvil' in currentElement.lower():
                                    if extraValue:
                                        if currentAuto.trackAvgVIL > extraValue:
                                            print('Updating second avgvil', caseString)
                                            extraValue = currentAuto.trackAvgVIL
                                            extraPotClusters = tempPotClusters
                                            extraBin = tempBin
                                    else:
                                        extraValue = currentAuto.trackAvgVIL
                                        extraPotClusters = tempPotClusters
                                        extraBin = tempBin
                                else:
                                    raise Exception("Element "+str(currentElement)+" was not accounted for.")
                                    
                                
                                
                    if not extraPotClusters or not extraValue or not extraBin:
                    
                        print('Did not have valid extra data potClusters, value, bin', extraPotClusters, extraValue, extraBin, caseString)
                        noAvailableCluster = 1
                        
                        
                else:
                    raise Exception("Test Element "+str(currentElement)+" was unable to be tested")
                        
                
                
                if not bool(noAvailableCluster):
                    print('Starting with extras', currentElement, extraPotClusters, extraValue, extraBin, caseString)
                    if extraPotClusters and extraValue and extraBin:
                    
                        if extraPotClusters <= self.minPotentialClusters or ignoreExtra:
                            print('Met min clusters')
                            bestThresholdObj = self.bestThresholds[extraBin]
                            otherBestThreshObj = None
                            
                            
                                    
                                    
                            if str(extraBin) == str(self.centralBin):
                                if tests.useSameThreshold:
                                    otherBestThreshObj = self.bestThresholds[str(self.centralBin)]
                                else:
                                    otherBestThreshObj = self.bestThresholds[str(self.secondBin)]
                            elif str(extraBin) == str(self.secondBin):
                                otherBestThreshObj = self.bestThresholds[str(self.centralBin)]
                            else:
                                raise Exception("Something went wrong in the extras!")
                                
                                
                            #Since all VIL/ET thresholds are the same and aren't range dependent, the first range tuple is used
                            defaultRangeTuple = sorted(bestThresholdObj.rangeTuples)[0]
                            targetThreshold = bestThresholdObj.thresholds[currentElement][defaultRangeTuple].threshold
                            
                            otherMetSamples = otherBestThreshObj.thresholds[currentElement][defaultRangeTuple].metMinSamples
                            
                            if bestThresholdObj.thresholds[currentElement][defaultRangeTuple].metMinSamples and otherMetSamples:
                                print('Is eligible. Testing.', extraValue, 'against', targetThreshold)
                                if extraValue >= targetThreshold:
                                    metWarningCriteria[currentElement] = True
                                    
                                couldBeTested[currentElement] = True
                                
                                if extraPotClusters < 0:
                                    failedPotentialClusters = 1
                                    if ignoreExtra:
                                        couldBeTested[currentElement] = True
                                        metWarningCriteria[currentElement] = True
                                    
                                    
                                if bool(needsSecondBin):
                                    usedSecondBin = 1
                                    
                            else:
                                failsMinSamples = 1
                        
                        else:
                            failedPotentialClusters = 1

                    else:
                        noAvailableCluster = 1

            if not couldBeTested[currentElement]:

                if ignoreExtra and not bool(failsMinSamples):
                    metWarningCriteria[currentElement] = True
                    couldBeTested[currentElement] = True
                    
            #With the information now gathered, update the dictionaries and counts
            noMinSampleCounts[currentElement] = failsMinSamples
            secondBinCounts[currentElement] = needsSecondBin
            noClusterCounts[currentElement] = noAvailableCluster
            potentialClusterCounts[currentElement] = failedPotentialClusters
            bhCounts[currentElement] = failedBH
            usedSecondBinCounts[currentElement] = usedSecondBin
            
        
        isWarned = all(list(metWarningCriteria.values()))
        isSuccess = all(list(couldBeTested.values()))
        
        print('For case', caseString, 'warned success', metWarningCriteria, couldBeTested, isWarned, isSuccess)
        
        return isWarned, noMinSampleCounts, secondBinCounts, noClusterCounts, potentialClusterCounts, bhCounts, usedSecondBinCounts, tiltRangeBin, isNegAzShear, isSuccess
        
        
      
def getIndivCaseStatsString(autoObjects, maxPotentialClusters, tiltList, headerString):

    """Returns a CSV format string with 1) the maximum or most favorable value for that variable across the case and 2) the value associated
    with the most variable descriminator """
    
    currentValues = [-math.inf] * len(headerString)
    bestTSSValues = [-math.inf] * len(headerString)
    
    for auto in autoObject:
    
        trackNumber = 0
        
        for tilt in tiltList:
            
            try:
                currentTiltObject = auto.azShear[tilt]
            except KeyError:
                continue
            
            currentAzShear = currentTiltObject.maxShear
            
            #Only looking at cyclonic cases
            if currentAzShear < 0:
                return ['negazshearcase'] * len(headerString)
                
            if currentAzShear > currentValues[trackNumber]:
                currentValues[trackNumber] = currentAzShear

    return
        
        
        
def getAllRangeTuplesAndTypes(bestThresholds):

    allRangeTuples = []
    allTypes = []
    
    for thresholdObj in list(bestThresholds.values()):
        for rangeTuple in thresholdObj.rangeTuples:
            if rangeTuple not in allRangeTuples:
                allRangeTuples.append(rangeTuple)
                
        for type in list(thresholdObj.thresholds.keys()):
        
            if type not in allTypes:
                allTypes.append(type)
                
                
    return allRangeTuples, sorted(allTypes)
    
def getOverallBestThresholds(bestThresholds, allRangeTuples, allTypes, cfg):
    """ Returns a BestThresholds object for the actual thresholds and another for their corresponding time bins """
    
    bestOverallThresholds = mr.BestThresholds(0, cfg.bestthreshfilebase, cfg.minTSSSamples)
    bestOverallBins = mr.BestThresholds(0, cfg.bestthreshfilebase, cfg.minTSSSamples)
    
    bins = list(bestThresholds.keys())
    
    for rangeTuple in allRangeTuples:
    
        for type in allTypes:
        
            bestTSS = -math.inf
            bestRangeTuple = None
            bestSampleString = ''
            bestThreshold = None
            bestType = None
            bestBin = None
            
            for thresholdObj in list(bestThresholds.values()):
                
                try:
                    currentTSS = float(thresholdObj.thresholds[type][rangeTuple].tss)
                    currentRangeTuple = thresholdObj.thresholds[type][rangeTuple].rangeTuple
                    currentSampleString = thresholdObj.thresholds[type][rangeTuple].samplestring
                    currentThreshold = thresholdObj.thresholds[type][rangeTuple].threshold
                    currentType = thresholdObj.thresholds[type][rangeTuple].type
                    currentBin = str(thresholdObj.bin)
                except KeyError:
                    print('In finding the best threshold, did not find', type, rangeTuple, 'in bin', thresholdObj.bin, '\nTrying next object')
                    continue
                
                if currentTSS > bestTSS and thresholdObj.thresholds[type][rangeTuple].metMinSamples:
                    bestTSS = currentTSS
                    bestRangeTuple = currentRangeTuple
                    bestSampleString = currentSampleString
                    bestThreshold = currentThreshold
                    bestType = currentType
                    bestBin = currentBin
            
            if bestTSS > -math.inf:
                bestOverallThresholds.addThreshold(bestType, bestThreshold, bestTSS, bestSampleString, bestRangeTuple)
                bestOverallBins.addThreshold(bestType, bestBin, '', 'NA', bestRangeTuple)
            
    print('Found best overall threshold and bins\n', repr(bestOverallThresholds), '\n', repr(bestOverallBins), sep='')
    try:
        os.mkdir('best_overall_thresholds')
    except FileExistsError:
        pass
        
    bestOverallThresholds.writeToCSV(alternateWriteFile='best_overall_thresholds/bestoverallthresholds.csv')
    bestOverallBins.writeToCSV(alternateWriteFile='best_overall_thresholds/bestoveralltimebins.csv')
    
    return bestOverallThresholds, bestOverallBins

def getAllTCs(nonTor, tor):
    """Returns a list of all TCs between nonTor and tor """
    
    tcList = []
    for TC in list(nonTor.keys()):
    
        if TC not in tcList:
            tcList.append(TC)
            
    for TC in list(tor.keys()):
        
        if TC not in tcList:
            tcList.append(TC)
            
            
    return tcList
    
def generateHeaderString(tiltList):

    headerString = 'TC,case,date,'
    
    for tilt in tiltList:
        headerString += '{}_maxAzShear,{}_bestAzShear,{}_bestAzShearBin'.format(tilt, tilt, tilt)
        
    headerString += 'max90thET,best90thET,best90thETBin,maxMaxET,bestMaxET,bestMaxETBin,maxAvgVIL,bestAvgVIL,bestAvgVILBin,maxMaxVIL,bestMaxVIL,bestMaxVILBin\n'
    
    return headerString
    
    
def calcIndividualCaseStats(nonTor, tor, tiltList, cfg, skillsCFG):


    tcList = getAllTCs(nonTor, tor)
    
    #TOR and NON TOR sheets are stored separately
    
    headerString = generateHeaderString(tiltList)
    
    for TC in tcList:
        
        nonTorStatStrings = {}
        torStatStrings = {}
        
        for caseID, caseObjects in nonTor[TC].items():
            pass #Production paused in favor of warning stats


    return
    
def getBestCentralBin(bestThresholds, bottomTilt):

    bestBin = None
    bestAvgTSS = -math.inf
    
    with open('centralbins.txt', 'w') as fi:
    
        fi.write('Time bins and average TSS values for eligibile 0.5 degree range bins for run on '+str(dt.now())+'\n')
    
        for currentBin, thresholdObj in bestThresholds.items():
        
            tssSum = 0
            tssCount = 0
            
            thresholdsList = []
            try:
                thresholdsList = list(thresholdObj.thresholds[bottomTilt].values())
            except KeyError:
                continue
            
            for currentThreshold in thresholdsList:
            
                if currentThreshold.metMinSamples:
                    tssSum += float(currentThreshold.tss)
                    tssCount += 1
            
            try:
                currentAverageTSS = tssSum/tssCount
            except ZeroDivisionError:
                currentAverageTSS = -math.inf
                
            fi.write('The average TSS for time bin '+str(currentBin)+' is '+str(currentAverageTSS)+'\n')
            
            if currentAverageTSS > bestAvgTSS:
                bestAvgTSS = currentAverageTSS
                bestBin = currentBin
                
        fi.write('The best time bin was '+str(bestBin)+' with an average TSS of '+str(bestAvgTSS))
        
    return bestBin, bestAvgTSS 


def sumDictionaries(dict1, dict2):

    """ Adds dict2 to dict1 by each key and returns a new dictionary which is the sum of the two.
    
        Returns a new dictionary which is the sum of the two. 
    """
    
    newDict = {}
    
    for key1 in list(dict1.keys()):
    
        try:
            newDict[key1] = dict1[key1] + dict2[key1]
        except KeyError:
            newDict[key1] = dict1[key1]
            
    #If a key in dict2 is not in dict1, add the key,value from dict2
    for key2 in list(dict2.keys()):
        
        if key2 not in list(dict1.keys()):
            newDict[key2] = dict2[key2]
            
    return newDict
    

def generateRemainingHeader(elementsList):

    returnLists = []
    for element in elementsList:
        strElement = str(element)
        returnLists.append(strElement+' NON TOR No Min,'+strElement+' TOR No Min,'+\
                           strElement+' NON TOR Second Bin,'+strElement+' TOR Second Bin,'+\
                           strElement+' NON TOR No Clusters,'+strElement+' TOR No Clusters,'+\
                           strElement+' NON TOR Potential Clusters,'+strElement+' TOR Potential Clusters,'+\
                           strElement+' NON TOR Beam Height,'+strElement+' TOR Beam Height,'+\
                           strElement+' NON TOR Used Second Bin,'+strElement+' TOR Used SecondBin')
                           
    return ','.join(returnLists)
    

def addElementData(currentData, currentElement):
    
    try:
        return str(currentData[currentElement])
    except KeyError:
        return 'NA'
        
def initBaseStatsDict(rangeTuples):

    newDict = {}
    
    for rangeTuple in rangeTuples:
        newDict[rangeTuple] = {'a':0, 'b':0, 'c':0, 'd':0}
        
    return newDict
    
    
def calcTheoreticalWarningStats(bestThresholds, nonTor, allTor, tiltList, cfg):

    testers = []
    for bin in tests.centralBin:
        testers.append(Tester(bin, bestThresholds, tiltList, cfg.potentialclusters, cfg.radius, cfg.maxAzShearHeight))
        
    elementsList = sorted(tests.testListTilts + tests.testListExtras)
    allRangeTuples, allTypes = getAllRangeTuplesAndTypes(bestThresholds)
    
    warningStats = {}
    with open(os.path.join(tests.evaluationFolder, 'theoretical_warning_stats.csv'), 'w') as fi:
        with open('rangedStats.csv', 'w') as fi2:
            fi2.write('Test,Range,Bin,pod,far,csi,tss,a,b,c,d\n')
            isFirst = True
            csvHeaderList = []
            
            for tester in testers:
            
                
                warningStats[str(tester.centralBin)] = {}
                
                for n,currentTest in enumerate(tests.testLists):
                
                    #Setup initial values of stats to be tracked
                    a = 0 #Number of tornadic cases warned
                    b = 0 #Number of nontornadic cases warned
                    c = 0 #Number of tornadic cases not warned
                    d = 0 #Number of nontornadic cases not warned
                    
                    rangedStats = initBaseStatsDict(allRangeTuples)
                    
                    #Dictionaries of counts of when the central or second bin does not have the minimum samples
                    nonTorNoMinSamplesCounts = {}
                    torNoMinSamplesCounts = {}
                    
                    #Dictionaries of counts of when the second bin needed to be referenced
                    nonTorSecondBinCounts = {}
                    torSecondBinCounts = {}
                    
                    #Dictionaries of counts of when a cluster was not available for the central or second bin
                    nonTorNoClusterCounts = {}
                    torNoClusterCounts = {}
                    
                    #Counts of clusters failed with too many potential clusters
                    nonTorPotentialClusterCounts = {}
                    torPotentialClusterCounts = {}
                    
                    #Counts for nontor cases out of range
                    nonTorBHCounts = {}
                    torBHCounts = {}
                    
                    #Counts of wehther the second bin was actually used
                    nonTorUsedSecondBinCounts = {}
                    torUsedSecondBinCounts = {}
                    
                    #Neg AzShear counts 
                    nonTorNegAzShearCount = 0
                    torNegAzShearCount = 0
                    
                    #Number of times a NON TOR or TOR case failed
                    nonTorFailCounts = 0
                    torFailCounts = 0
                    
                    #Total number of cases
                    nonTorTotal = 0
                    torTotal = 0
                    
                    for TC in list(nonTor.keys()):
                    
                        for nonTorAutoObjects in list(nonTor[TC].values()):
                        
                            isWarned, noMinSampleCounts, secondBinCounts, noClusterCounts, potentialClusterCounts, bhCounts, usedSecondBins, baseRangeTuple, isNegAzShear, isSuccess = tester.isItWarned(nonTorAutoObjects, currentTest, cfg, ignoreExtra=cfg.ignoreExtra)
                            
                            if isNegAzShear:
                                nonTorNegAzShearCount += 1
                                
                            if isSuccess:
                                print('NON TOR success, Is warned', isWarned, 'rangeTuple', baseRangeTuple)
                                
                                if isWarned:
                                    b += 1
                                    if baseRangeTuple:
                                        rangedStats[baseRangeTuple]['b'] += 1
                                else:
                                    d += 1
                                    if baseRangeTuple:
                                        rangedStats[baseRangeTuple]['d'] += 1
                            else:
                                nonTorFailCounts += 1
                                
                                
                            nonTorNoMinSamplesCounts = sumDictionaries(nonTorNoMinSamplesCounts, noMinSampleCounts)
                            nonTorSecondBinCounts = sumDictionaries(nonTorSecondBinCounts, secondBinCounts)
                            nonTorNoClusterCounts = sumDictionaries(nonTorNoClusterCounts, noClusterCounts)
                            nonTorPotentialClusterCounts = sumDictionaries(nonTorPotentialClusterCounts, potentialClusterCounts)
                            nonTorBHCounts = sumDictionaries(nonTorBHCounts, bhCounts)
                            nonTorUsedSecondBinCounts = sumDictionaries(nonTorUsedSecondBinCounts, usedSecondBins)
                            nonTorTotal += 1
                            
                    for TC in list(allTor.keys()):
                    
                        for torAutoObjects in list(allTor[TC].values()):
                        
                            isWarned, noMinSampleCounts, secondBinCounts, noClusterCounts, potentialClusterCounts, bhCounts, usedSecondBins, baseRangeTuple, isNegAzShear, isSuccess = tester.isItWarned(torAutoObjects, currentTest, cfg, ignoreExtra=cfg.ignoreExtra)
                            
                            if isNegAzShear:
                                torNegAzShearCount += 1
                                
                            if isSuccess:
                                print('TOR success. Is warned', isWarned, 'rangeTuple', baseRangeTuple)
                                if isWarned:
                                    a += 1
                                    if baseRangeTuple:
                                        rangedStats[baseRangeTuple]['a'] += 1
                                else:
                                    c += 1
                                    if baseRangeTuple:
                                        rangedStats[baseRangeTuple]['c'] += 1
                            else:
                                torFailCounts += 1
                                
                            torNoMinSamplesCounts = sumDictionaries(torNoMinSamplesCounts, noMinSampleCounts)
                            torSecondBinCounts = sumDictionaries(torSecondBinCounts, secondBinCounts)
                            torNoClusterCounts = sumDictionaries(torNoClusterCounts, noClusterCounts)
                            torPotentialClusterCounts = sumDictionaries(torPotentialClusterCounts, potentialClusterCounts)
                            torBHCounts = sumDictionaries(torBHCounts, bhCounts)
                            torUsedSecondBinCounts = sumDictionaries(torUsedSecondBinCounts, usedSecondBins)
                            
                            torTotal += 1
                            
                    statsDict = {}
                    writeString = ''
                    #If this is the first run, generate the header for the output CSV.
                    if isFirst:
                        header = 'Test Number,Test,Bin,POD,FAR,CSI,TSS,a,b,c,d,Same Thresholds,Ignore Extra,NON TOR Total,TOR Total,NON TOR Fails,TOR Fails,NON TOR Neg AzShear,TOR Neg AzShear,'
                        header += generateRemainingHeader(elementsList)+'\n'
                        fi.write(header)
                        isFirst = False
                    
                    currentTestToWrite = str(currentTest).replace('[', '').replace(']', '').replace("'", '').replace(', ', '-')

                    print('Calculating stats for', currentTest, 'using abcd', a, b, c, d)
                    try:
                        pod = a/(a+c)
                        far = b/(a+b)
                        csi = a/(a+b+c)
                        tss = ((a*d) - (b*c))/((a+c)*(b+d))
                        statsDict = {'pod':pod, 'far':far, 'csi':csi, 'tss':tss}
                        
                    except ZeroDivisionError:
                        nColumns = 17 + (12*len(elementsList))
                        writeString = str(n)+','+currentTestToWrite+','+','.join(['Zero Division'] * nColumns)+'\n'
                        fi.write(writeString)
                        continue
                        
                        
                    writeString = str(n)+','+currentTestToWrite+','+','.join(map(str, [tester.centralBin, pod, far, csi, tss, a, b, c, d, tests.useSameThreshold, cfg.ignoreExtra, nonTorTotal, torTotal,  nonTorFailCounts, torFailCounts, nonTorNegAzShearCount, torNegAzShearCount]))+','
                    
                    for currentElement in elementsList:
                        strElement = str(currentElement)
                        writeString += addElementData(nonTorNoMinSamplesCounts, strElement)+','
                        writeString += addElementData(torNoMinSamplesCounts, strElement)+','
                        writeString += addElementData(nonTorSecondBinCounts, strElement)+','
                        writeString += addElementData(torSecondBinCounts, strElement)+','
                        writeString += addElementData(nonTorNoClusterCounts, strElement)+','
                        writeString += addElementData(torNoClusterCounts, strElement)+','
                        writeString += addElementData(nonTorPotentialClusterCounts, strElement)+','
                        writeString += addElementData(torPotentialClusterCounts, strElement)+','
                        writeString += addElementData(nonTorBHCounts, strElement)+','
                        writeString += addElementData(torBHCounts, strElement)+','
                        writeString += addElementData(nonTorUsedSecondBinCounts, strElement)+','
                        writeString += addElementData(torUsedSecondBinCounts, strElement)
                        
                        if currentElement == elementsList[-1]:
                            writeString += '\n'
                        else:
                            writeString += ','
                                
                    fi.write(writeString)
                    warningStats[str(tester.centralBin)][str(n)] = statsDict
                        
                    
                    #Calculate and plot the warning stats by bin by test
                
               
                
                    rangedStatsDict = {}
                    statsDict2 = {}
                    currentTestString = ''
                    for thisTest in currentTest:
                        if 'VIL_' in thisTest:
                            thisTest = thisTest.replace('VIL_', '')
                        if 'ET_' in thisTest:
                            thisTest = thisTest.replace('ET_', '')
                            
                        if thisTest != currentTest[-1]:
                            currentTestString += str(thisTest)
                            
                            try:
                                dummyVar = float(thisTest)
                                currentTestString += '$^\circ$'
                            except ValueError:
                                pass
                                
                            
                        else:
                            currentTestString += str(thisTest)
                            
                            try:
                                dummyVar = float(thisTest)
                                currentTestString += '$^\circ$'
                            except ValueError:
                                pass
                            
                        
                            
                    
                    for rangeTuple, rangeBaseStatsDict in rangedStats.items():
                    
                        writeString2 = ','.join(list(map(str, [currentTestString.replace('$^\circ$', '-'), str(rangeTuple).replace(', ', '_'), tester.centralBin])))+','
                        
                        a2 = rangeBaseStatsDict['a']
                        b2 = rangeBaseStatsDict['b']
                        c2 = rangeBaseStatsDict['c']
                        d2 = rangeBaseStatsDict['d']
                        
                        pod2 = None
                        far2 = None
                        csi2 = None
                        tss2 = None
                        
                        try:
                            pod2 = a2/(a2+c2)
                            far2 = b2/(a2+b2)
                            csi2 = a2/(a2+b2+c2)
                            tss2 = ((a2*d2) - (b2*c2))/((a2+c2)*(b2+d2))
                            statsDict2 = {'pod':pod2, 'far':far2, 'csi':csi2, 'tss':tss2}
                            
                        except ZeroDivisionError:
                            writeString2 += ','.join(['Zero Division']*8)+'\n'
                            rangedStatsDict[rangeTuple] = {'pod':-0.05, 'far':-0.05, 'csi':-0.05, 'tss':-0.05}
                            fi2.write(writeString2)
                            continue
                            
                        rangedStatsDict[rangeTuple] = statsDict2
                        
                        writeString2 += ','.join(map(str, [pod2, far2, csi2, tss2, a2, b2, c2, d2]))+'\n'
                        
                        fi2.write(writeString2)
                        
                        title = "Theoertical Warning Stats For "+str(currentTestString)+' at '+str(int(int(tester.centralBin)*cfg.timeBinSize))+" Minutes"
                        
                        grapher.makeMultirangeCombStatPlots(rangedStatsDict, currentTestString, tester.centralBin, title, 'multirange', cfg)
                        
                
    return warningStats
    
    
def calcWarnings(bestThresholds, nonTor, allTor, realWarningStats, tiltList, cfg, skillsCFG):

    #Determine overall best thresholds
    allRangeTuples, allTypes = getAllRangeTuplesAndTypes(bestThresholds)
    overallBestThresholds, overallBestBins = getOverallBestThresholds(bestThresholds, allRangeTuples, allTypes, cfg)
    
    #Get individual case stats (put on hold)
    
    #Calculate theoretical warning stats
    
    if tests.updateCentralBin:
        bestCentralBin, bestAvgTSS = getBestCentralBin(bestThresholds, tiltList[0])
        tests.centralBin = [bestCentralBin]
        
    else:
        with open('centralbins.txt', 'w') as fi:
            fi.write('For the run of '+str(dt.now())+' the best central time bin was not calculated.')
            
    warningStats = calcTheoreticalWarningStats(bestThresholds, nonTor, allTor, tiltList, cfg)     
    print('The warning stats are', warningStats)
            
    grapher.makeMultirangeWarningBarPlots(warningStats, realWarningStats, 'multirange', cfg)
    
    #Now create the replacement bar graphs with observed, M17, and these warning stats. M17 is hardcoaded from posvrot_0.5_m17tss from the thesis
    
    #1) Reformat the above stats
    statsDict = warningStats['-2']['0']
    normalStats = {'far':statsDict['far'], 'pod':statsDict['pod'], 'CSI':statsDict['csi']}
    m17Stats = {'far':0.469387755, 'pod':0.718894009, 'CSI':0.43943662}
    
    grapher.makeWarningBarPlots(normalStats, True, m17Stats, realWarningStats,\
                                'Theoretical Warning Stats at -10 Minutes',\
                                'multirange', cfg, bestThresholdLabel='0.5$^\circ$Best Thresholds')
                                
    return
    
    