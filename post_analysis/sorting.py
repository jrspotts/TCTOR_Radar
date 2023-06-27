#This module holds functions for sorting auto objects into different groups.


#Justin Spotts 7/3/2022
import math
import copy

def toVrot(azShear, radius):

    return (azShear * radius) * 1.94384
    
def sortTorNoTor(autoObjects):

    """ This function sorts autoObjects into tornadic and nontornadic groups """
    torObjects = {}
    noTorObjects = {}
    print('Sorting TOR and NON TOR objects')
    
    with open('negeftors.csv', 'w') as fi:
    
        fi.write('TC,case,EF\n')
        
        for TC in list(autoObjects.keys()):
        
            torObjects[TC] = {}
            noTorObjects[TC] = {}
            
            for case in list(autoObjects[TC].keys()):
            
                for auto in autoObjects[TC][case]:
                
                    if auto.istor:
                        torObjects[TC][case] = autoObjects[TC][case]
                        if int(auto.efRating) < 0 or int(auto.efRating) > 5:
                            print('Weird EF rating', auto.efRating, 'for', TC, case)
                            fi.write(','.join(map(str, [TC, case, auto.efRating]))+'\n')
                            
                        break
                    else:
                        noTorObjects[TC][case] = autoObjects[TC][case]
                        break
                        
    print('Done!')
    # print('NON TOR', noTorObjects)
    # print('TOR', torObjects)
    
    return torObjects, noTorObjects
    
def sortTDS(autoObjects, tilt, startBin=0, minCount=5, potentialClusters=math.inf, maxBeamHeight=math.inf):
    """ Sort the autoObjects into those groups that do and do not have a TDS.
        The TDS was defined by the w2tds algorithm which simily looks for gates that meet rotational, CC, and Zh requirements.
        
        startBin is the bin to start looking for a TDS in during each case at the tilt.
        
        minCount is the minimum number of TDS pixles required for a TDS to be counted.
        
    """
    
    tdsObjects = {}
    noTdsObjects = {}
    print('Sorting by TDS')
    nTDS = 0 #Number of TDS cases found
    nNoTDS = 0 #Number of not TDS cases
    totalCountByEF = {}
    tdsCountByEF = {}
    zeroBinCount = 0
    zeroEFCount = 0
    for TC in list(autoObjects.keys()):
    
        tdsObjects[TC] = {}
        noTdsObjects[TC] = {}
        
        for case in list(autoObjects[TC].keys()):
        
            foundTDS = False
            meetsOtherCriteria = False #If at least one bin meets the beam height and potential clusters criteria. Then the criteria is met to be counted as no TDS
                                       #This still needs to occur with for each bin for the TDS
            binMeetsOtherCriteria = False
            currentEF = None
            for auto in autoObjects[TC][case]:
            
                tiltObject = auto.azShear[tilt]
                currentEF = auto.efRating

                # print('TDS criteria check', TC, case, int(tiltObject.potentialClusters) <= potentialClusters and int(tiltObject.potentialClusters) >= 0, float(tiltObject.beamHeights['0']) <= maxBeamHeight and float(tiltObject.beamHeights['0']) >= 0, tiltObject.maxShear > -99900)
                # print('TDS check values. PT', tiltObject.potentialClusters, 'BH', tiltObject.beamHeights['0'], 'MS', tiltObject.maxShear)
                if int(tiltObject.potentialClusters) <= potentialClusters and int(tiltObject.potentialClusters) >= 0 and float(tiltObject.beamHeights['0']) <= maxBeamHeight and float(tiltObject.beamHeights['0']) >= 0 and tiltObject.maxShear > -99900:
                    binMeetsOtherCriteria = True
                    meetsOtherCriteria = True
                    if int(tiltObject.binNumber) == 0 and currentEF == '0':
                        zeroBinCount += 1
                    
                else:
                    binMeetsOtherCriteria = False
                if int(tiltObject.binNumber) >= startBin and int(tiltObject.TDScount) >= minCount and binMeetsOtherCriteria:
                    tdsObjects[TC][case] = copy.deepcopy(autoObjects[TC][case])
                    #print(TC, case, 'deemed TDS at bin and count', tiltObject.binNumber, tiltObject.TDScount)
                    foundTDS = True
                    nTDS += 1
                    try:
                        totalCountByEF[currentEF] += 1
                    except KeyError:
                        totalCountByEF[currentEF] = 1
                    try:
                        tdsCountByEF[currentEF] += 1
                    except KeyError:
                        tdsCountByEF[currentEF] = 1
                        
                    break
                    
            if not foundTDS and meetsOtherCriteria:
                #print('No TDS was found for', TC, case)
                noTdsObjects[TC][case] = copy.deepcopy(autoObjects[TC][case])
                nNoTDS += 1
                try:
                    totalCountByEF[currentEF] += 1
                except KeyError:
                    totalCountByEF[currentEF] = 1
            if currentEF == '0' and meetsOtherCriteria:
                zeroEFCount += 1
                
    print('Done!', zeroBinCount, zeroEFCount)
    # print('TDS', tdsObjects)
    # print('NO TDS', noTdsObjects)
    
    return tdsObjects, noTdsObjects, nTDS, nNoTDS, tdsCountByEF, totalCountByEF
    
    
def determineTDS(autoObjects, tilt, startBin=0, minCount=5):
    """
        sortTDS except using only autoObjects from one case rather than the full set of autoObjects.
    """
    print('Checking if it\'s a TDS')
    foundTDS = False
    
    for auto in autoObjects:
            
        tiltObject = auto.azShear[tilt]
        
        if int(tiltObject.binNumber) >= startBin and int(tiltObject.TDScount) >= minCount:
            foundTDS = True
            print('It is!')
            break
    
    if not foundTDS:
        print('It is not.')
    return foundTDS        
    
    
def getObjectsByBin(autoObjects, tiltList, cfg, isTDS=False, isTOR=False, maxPotentialClusters=math.inf):

    """ Sorts individual tilts, echo-top clusters, and track clusters by time bin.
        Returns the a dictionary for:
        Tilts by tilt then desired data then time bin,
        Echo-tops or track clusters by time bin, then desired data.
        
        There are also versions for the time-bins between and by EF rating. 
    """
    
    tiltData = {}
    tiltTrendData = {}
    tiltDataEF = {}
    tiltDataRangeEF = {}
    tiltTrendDataEF = {}
    tiltDataVCP = {}
    tiltDataRange = {}
    
    etData = {'90thet':{}, 'maxet':{}}
    posETData = {'90thet':{}, 'maxet':{}}
    etDataVCP = {'90thet':{}, 'maxet':{}}
    posETDataVCP = {'90thet':{}, 'maxet':{}}
    posTrackData = {'avgvil':{}, 'maxvil':{}, 'maxref':{}}
    trackData = {'avgvil':{}, 'maxvil':{}, 'maxref':{}}
    trackDataVCP = {'avgvil':{}, 'maxvil':{}, 'maxref':{}}
    posTrackDataVCP = {'avgvil':{}, 'maxvil':{}, 'maxref':{}}
    etTrendData = {'90thet':{}, 'maxet':{}}
    etTrendDataVCP = {'90thet':{}, 'maxet':{}}
    trackTrendData = {'avgvil':{}, 'maxvil':{}, 'maxref':{}}
    trackTrendDataVCP = {'avgvil':{}, 'maxvil':{}, 'maxref':{}}
    posETTrendData = {'90thet':{}, 'maxet':{}}
    posETTrendDataVCP = {'90thet':{}, 'maxet':{}}
    posTrackTrendData = {'avgvil':{}, 'maxvil':{}, 'maxref':{}}
    posTrackTrendDataVCP = {'avgvil':{}, 'maxvil':{}, 'maxref':{}}
    
    missingCount = {}
    missingCountEF = {}
    negativeAzShearCases = []
    
    for tilt in tiltList:
    
        tiltData[str(tilt)] = {'azshear':{},\
                                    'posazshear':{},\
                                    'absshear':{},\
                                    '90thazshear':{},\
                                    '10thazshear':{},\
                                    'vrot':{},\
                                    'posvrot':{},\
                                    'spectrumwidth':{},\
                                    'posspectrumwidth':{},\
                                    'mintdscc': {},\
                                    'posmintds':{}}
                                    
        tiltDataRange[str(tilt)] = {'azshear':{},\
                                    'posazshear':{},\
                                    'absshear':{},\
                                    'vrot':{},\
                                    '90thvrot':{},\
                                    'posvrot':{}}
                                    
        tiltDataRangeEF[str(tilt)] = {'posvrot':{},\
                                      '90thvrot':{}}

        
        missingCount[str(tilt)] = {'azshear':{},\
                                    '90thazshear':{},\
                                    '10thazshear':{},\
                                    'spectrumwidth':{},\
                                    'mintdscc': {}}
                                    
        missingCountEF[str(tilt)] = {'azshear':{},\
                                    '90thazshear':{},\
                                    '10thazshear':{},\
                                    'spectrumwidth':{},\
                                    'mintdscc': {}}
                                
        tiltTrendData[str(tilt)] = {'azshear':{},\
                                    'posazshear':{},\
                                    'absshear':{},\
                                    '90thazshear':{},\
                                    '10thazshear':{},\
                                    'vrot':{},\
                                    'posvrot':{},\
                                    'posspectrumwidth':{},\
                                    'spectrumwidth':{}}
                                    
        tiltDataEF[str(tilt)] = {'azshear':{},\
                                    'posazshear':{},\
                                    'absshear':{},\
                                    'vrot':{},\
                                    'posvrot':{},\
                                    'spectrumwidth':{},\
                                    'mintdscc':{}}   
                                
        tiltTrendDataEF[str(tilt)] = {'azshear':{},\
                                    'posazshear':{},\
                                    'absshear':{},\
                                    'vrot':{},\
                                    'posvrot':{}}
                                
                                

    skippedCount = 0
    
    totalNegAzShearLT = 0
    totalCases = 0
        
    for TC in list(autoObjects.keys()):
        
        
        for case in list(autoObjects[TC].keys()):
            
            isNegAzShear = False
            
            print('\nStarting to sort TC', TC, 'case', case, totalCases, '\n')
            totalCases += 1
            etDict = {'90thet':{}, 'maxet':{}}
            posETDict = {'90thet':{}, 'maxet':{}}
            etDictVCP = {'90thet':{}, 'maxet':{}}
            posETDictVCP = {'90thet':{}, 'maxet':{}}
            trackDict = {'avgvil':{}, 'maxvil':{}, 'maxref':{}}
            trackDictVCP = {'avgvil':{}, 'maxvil':{}, 'maxref':{}}
            posTrackDict = {'avgvil':{}, 'maxvil':{}, 'maxref':{}}
            posTrackDictVCP = {'avgvil':{}, 'maxvil':{}, 'maxref':{}}
            etTrendDict = {'90thet':{}, 'maxet':{}}
            etTrendDictVCP = {'90thet':{}, 'maxet':{}}
            trackTrendDict = {'avgvil':{}, 'maxvil':{}, 'maxref':{}}
            trackTrendDictVCP = {'avgvil':{}, 'maxvil':{}, 'maxref':{}}
            posETTrendDict = {'90thet':{}, 'maxet':{}}
            posETTrendDictVCP = {'90thet':{}, 'maxet':{}}
            posTrackTrendDict = {'avgvil':{}, 'maxvil':{}, 'maxref':{}}
            posTrackTrendDictVCP = {'avgvil':{}, 'maxvil':{}, 'maxref':{}}
            
            #Have a loop here just for the ETs and VIL to avoid repeating the analysis on each tilt
            for auto3 in autoObjects[TC][case]:
                currentETBin = int(auto3.etBinNumber)
                etPotentialClusters = auto3.etPotentialClusters
                #print('VCPs', auto3.vcpNumbers)
                vcpString3 = ''
                for vcp in list(auto3.vcpNumbers.keys()):
                    vcpString3 += str(auto3.vcpNumbers[vcp])+'-'
                vcpString3 = vcpString3.rstrip('-')
                if currentETBin > -99900 and etPotentialClusters <= maxPotentialClusters and etPotentialClusters >= 0:
                    if auto3.maxETft >= 0:
                        try:
                            etDict['maxet'][currentETBin].append(auto3.maxETft)
                        except KeyError:
                            etDict['maxet'][currentETBin] = [auto3.maxETft]
                        
                        try:
                            etDictVCP['maxet'][currentETBin].setdefault(vcpString3, []).append(auto3.maxETft)
                        except KeyError as K:
                            print('Key0 maxet', K, currentETBin, vcpString3)
                            try:
                                etDictVCP['maxet'][currentETBin][vcpString3] = [auto3.maxETft]
                            except KeyError:
                                etDictVCP['maxet'][currentETBin] = {vcpString3:[auto3.maxETft]}
                                    
                        if auto3.azShear['0.5'].maxShear >= 0:
                            try:
                                posETDict['maxet'][currentETBin].append(auto3.maxETft)
                            except KeyError:
                                posETDict['maxet'][currentETBin] = [auto3.maxETft]
                                
                            try:
                                posETDictVCP['maxet'][currentETBin].setdefault(vcpString3, []).append(auto3.maxETft)
                            except KeyError as K:
                                print('Key0 posmaxet', K, currentETBin, vcpString3)
                                try:
                                    posETDictVCP['maxet'][currentETBin][vcpString3] = [auto3.maxETft]
                                except KeyError:
                                    posETDictVCP['maxet'][currentETBin] = {vcpString3:[auto3.maxETft]}
                                
                                
                    if auto3.top90ETft >= 0:
                        try:
                            etDict['90thet'][currentETBin].append(auto3.top90ETft)
                        except KeyError:
                            etDict['90thet'][currentETBin] = [auto3.top90ETft]
                    
                        try:
                            etDictVCP['90thet'][currentETBin].setdefault(vcpString3, []).append(auto3.top90ETft)
                        except KeyError as K:
                            print('Key0 90thet', K, currentETBin, vcpString3)
                            try:
                                etDictVCP['90thet'][currentETBin][vcpString3] = [auto3.top90ETft]
                            except KeyError:
                                etDictVCP['90thet'][currentETBin] = {vcpString3:[auto3.top90ETft]}
                                
                        if auto3.azShear['0.5'].maxShear >= 0:
                            try:
                                posETDict['90thet'][currentETBin].append(auto3.top90ETft)
                            except KeyError:
                                posETDict['90thet'][currentETBin] = [auto3.top90ETft]
                                
                            try:
                                posETDictVCP['90thet'][currentETBin].setdefault(vcpString3, []).append(auto3.top90ETft)
                            except KeyError as K:
                                print('Key0 pos90thet', K, currentETBin, vcpString3)
                                try:
                                    posETDictVCP['90thet'][currentETBin][vcpString3] = [auto3.top90ETft]
                                except KeyError:
                                    posETDictVCP['90thet'][currentETBin] = {vcpString3:[auto3.top90ETft]}
                                
                                
                            
                    
                        
                currentTrackBin = int(auto3.trackBinNumber)
                trackPotentialClusters = auto3.trackPotentialClusters
                if currentTrackBin > -99900 and trackPotentialClusters <= maxPotentialClusters and trackPotentialClusters >= 0:
                    if auto3.trackAvgVIL >= 0:
                        try:
                            trackDict['avgvil'][currentTrackBin].append(auto3.trackAvgVIL)
                        except KeyError:
                            trackDict['avgvil'][currentTrackBin] = [auto3.trackAvgVIL]
                            
                        try:
                            trackDictVCP['avgvil'][currentTrackBin].setdefault(vcpString3, []).append(auto3.trackAvgVIL)
                        except KeyError as K:
                            print('Key0 avgvil', K, currentTrackBin, vcpString3)
                            try:
                                trackDictVCP['avgvil'][currentTrackBin][vcpString3] = [auto3.trackAvgVIL]
                            except KeyError:
                                trackDictVCP['avgvil'][currentTrackBin] = {vcpString3:[auto3.trackAvgVIL]}
                            
                        
                        if auto3.azShear['0.5'].maxShear >= 0:
                            try:
                                posTrackDict['avgvil'][currentTrackBin].append(auto3.trackAvgVIL)
                                #print('Added', auto3.trackAvgVIL, 'using AzShear', auto3.azShear['0.5'].maxShear)
                            except KeyError:
                                posTrackDict['avgvil'][currentTrackBin] = [auto3.trackAvgVIL]
                                #print('Added', auto3.trackAvgVIL, 'using AzShear', auto3.azShear['0.5'].maxShear)
                                
                            try:
                                posTrackDictVCP['avgvil'][currentTrackBin].setdefault(vcpString3, []).append(auto3.trackAvgVIL)
                            except KeyError as K:
                                print('Key0 posavgvil', K, currentTrackBin, vcpString3)
                                try:
                                    posTrackDictVCP['avgvil'][currentTrackBin][vcpString3] = [auto3.trackAvgVIL]
                                except KeyError:
                                    posTrackDictVCP['avgvil'][currentTrackBin] = {vcpString3:[auto3.trackAvgVIL]}
                                
                    if auto3.trackMaxVIL >= 0:
                        try:
                            trackDict['maxvil'][currentTrackBin].append(auto3.trackMaxVIL)
                        except KeyError:
                            trackDict['maxvil'][currentTrackBin] = [auto3.trackMaxVIL]
                            
                        try:
                            trackDictVCP['maxvil'][currentTrackBin].setdefault(vcpString3, []).append(auto3.trackMaxVIL)
                        except KeyError as K:
                            print('Key0 maxvil', K, currentTrackBin, vcpString3)
                            try:
                                trackDictVCP['maxvil'][currentTrackBin][vcpString3] = [auto3.trackMaxVIL]
                            except KeyError:
                                trackDictVCP['maxvil'][currentTrackBin] = {vcpString3:[auto3.trackMaxVIL]}
                        
                        if auto3.azShear['0.5'].maxShear >= 0:
                            try:
                                posTrackDict['maxvil'][currentTrackBin].append(auto3.trackMaxVIL)
                            except KeyError:
                                posTrackDict['maxvil'][currentTrackBin] = [auto3.trackMaxVIL]
                                
                            try:
                                posTrackDictVCP['maxvil'][currentTrackBin].setdefault(vcpString3, []).append(auto3.trackMaxVIL)
                            except KeyError as K:
                                print('Key0 posmaxvil', K, currentTrackBin, vcpString3)
                                try:
                                    posTrackDictVCP['maxvil'][currentTrackBin][vcpString3] = [auto3.trackMaxVIL]
                                except KeyError:
                                    posTrackDictVCP['maxvil'][currentTrackBin] = {vcpString3:[auto3.trackMaxVIL]}
                                
                                
                    if auto3.trackMaxREF >= 0:
                        try:
                            trackDict['maxref'][currentTrackBin].append(auto3.trackMaxREF)
                        except KeyError:
                            trackDict['maxref'][currentTrackBin] = [auto3.trackMaxREF]
                            
                        try:
                            trackDictVCP['maxref'][currentTrackBin].setdefault(vcpString3, []).append(auto3.trackMaxREF)
                        except KeyError as K:
                            print('Key0 maxref', K, currentTrackBin, vcpString3)
                            try:
                                trackDictVCP['maxref'][currentTrackBin][vcpString3] = [auto3.trackMaxREF]
                            except KeyError:
                                trackDictVCP['maxref'][currentTrackBin] = {vcpString3:[auto3.trackMaxREF]}
                            
                        if auto3.azShear['0.5'].maxShear >= 0:
                            try:
                                posTrackDict['maxref'][currentTrackBin].append(auto3.trackMaxREF)
                            except KeyError:
                                posTrackDict['maxref'][currentTrackBin] = [auto3.trackMaxREF]
                                
                            try:
                                posTrackDictVCP['maxref'][currentTrackBin].setdefault(vcpString3, []).append(auto3.trackMaxREF)
                            except KeyError as K:
                                print('Key0 posmaxref', K, currentTrackBin, vcpString3)
                                try:
                                    posTrackDictVCP['maxref'][currentTrackBin][vcpString3] = [auto3.trackMaxREF]
                                except KeyError:
                                    posTrackDictVCP['maxref'][currentTrackBin] = {vcpString3:[auto3.trackMaxREF]}
                                
                
                #Now get the trends
                for auto2 in autoObjects[TC][case]:
                    secondETBin = int(auto2.etBinNumber)
                    secondETPotentialClusters = auto2.etPotentialClusters
                    isPositive = auto3.azShear['0.5'].maxShear >= 0 and auto2.azShear['0.5'].maxShear >= 0
                    vcpString2 = ''
                    for vcp in list(auto2.vcpNumbers.keys()):
                        vcpString2 += str(auto2.vcpNumbers[vcp])+'-'
                    vcpString2 = vcpString2.rstrip('-')
                    vcpStringComb = vcpString3+'-'+vcpString2
                    
                    if secondETBin > -99900 and currentETBin > -99900 and etPotentialClusters <= maxPotentialClusters and etPotentialClusters >= 0\
                        and secondETPotentialClusters <= maxPotentialClusters and secondETPotentialClusters >= 0:
                        if secondETBin > currentETBin:
                            etBinTuple = (currentETBin, secondETBin) #Tuple representing the range of tilts
                            #Max ET Trend
                            if auto2.maxETft >= 0 and auto3.maxETft >= 0 :
                                maxETTrend = auto2.maxETft - auto3.maxETft
                                if etBinTuple not in list(etTrendDict['maxet'].keys()): 
                                    etTrendDict['maxet'][etBinTuple] = maxETTrend 
                                else:
                                    #If we already looked at this trend, use the stronger trend
                                    if abs(maxETTrend) > abs(etTrendDict['maxet'][etBinTuple]):
                                        etTrendDict['maxet'][etBinTuple] = maxETTrend
                                        
                                if etBinTuple not in list(etTrendDictVCP['maxet'].keys()):
                                    etTrendDictVCP['maxet'][etBinTuple] = {vcpStringComb:maxETTrend}
                                else:
                                    if abs(maxETTrend) > abs(etTrendDictVCP['maxet'][etBinTuple][vcpStringComb]):
                                        etTrendDictVCP['maxet'][etBinTuple][vcpStringComb] = maxETTrend
                                        
                                if isPositive:
                                    if etBinTuple not in list(posETTrendDict['maxet'].keys()):
                                        posETTrendDict['maxet'][etBinTuple] = maxETTrend
                                    else:
                                        if abs(maxETTrend) > posETTrendDict['maxet'][etBinTuple]:
                                            posETTrendDict['maxet'][etBinTuple] = maxETTrend
                                            
                                    if etBinTuple not in list(posETTrendDictVCP['maxet'].keys()):
                                        posETTrendDictVCP['maxet'][etBinTuple] = {vcpStringComb:maxETTrend}
                                    else:
                                        if abs(maxETTrend) > abs(posETTrendDictVCP['maxet'][etBinTuple][vcpStringComb]):
                                            posETTrendDictVCP['maxet'][etBinTuple][vcpStringComb] = maxETTrend
                            
                            #90th Percentile ET Trend
                            if auto2.top90ETft >= 0 and auto3.top90ETft >= 0:
                                top90ETTrend = auto2.top90ETft - auto3.top90ETft
                                if etBinTuple not in list(etTrendDict['90thet'].keys()):
                                    etTrendDict['90thet'][etBinTuple] = top90ETTrend
                                else:
                                    if abs(top90ETTrend) > abs(etTrendDict['90thet'][etBinTuple]):
                                        etTrendDict['90thet'][etBinTuple] = top90ETTrend
                                
                                if etBinTuple not in list(etTrendDictVCP['90thet'].keys()):
                                    etTrendDictVCP['90thet'][etBinTuple] = {vcpStringComb:top90ETTrend}
                                else:
                                    if abs(top90ETTrend) > abs(etTrendDictVCP['90thet'][etBinTuple][vcpStringComb]):
                                        etTrendDictVCP['90thet'][etBinTuple][vcpStringComb] = top90ETTrend
                                        
                                if isPositive:
                                    if etBinTuple not in list(posETTrendDict['90thet'].keys()):
                                        posETTrendDict['90thet'][etBinTuple] = top90ETTrend
                                    else:
                                        if abs(top90ETTrend) > abs(posETTrendDict['90thet'][etBinTuple]):
                                            posETTrendDict['90thet'][etBinTuple] = top90ETTrend
                                    
                                    if etBinTuple not in list(posETTrendDictVCP['90thet'].keys()):
                                        posETTrendDictVCP['90thet'][etBinTuple] = {vcpStringComb:top90ETTrend}
                                    else:
                                        if abs(top90ETTrend) > abs(posETTrendDictVCP['90thet'][etBinTuple][vcpStringComb]):
                                            posETTrendDictVCP['90thet'][etBinTuple][vcpStringComb] = top90ETTrend
                                            
                    
                    secondTrackBin = int(auto2.trackBinNumber)
                    secondTrackPotenetialClusters = auto2.trackPotentialClusters
                    if secondTrackBin > -99900 and currentTrackBin > -99900 and trackPotentialClusters <= maxPotentialClusters and trackPotentialClusters >= 0\
                        and secondTrackPotenetialClusters <= maxPotentialClusters and secondTrackPotenetialClusters >= 0:
                        if secondTrackBin > currentTrackBin:
                            trackBinTuple = (currentTrackBin, secondTrackBin)
                            
                            #Avg VIL trend
                            if auto2.trackAvgVIL >= 0 and auto3.trackAvgVIL >= 0:
                                avgVILTrend = auto2.trackAvgVIL - auto3.trackAvgVIL
                                if trackBinTuple not in list(trackTrendDict['avgvil'].keys()):
                                    trackTrendDict['avgvil'][trackBinTuple] = avgVILTrend
                                else:
                                    if abs(avgVILTrend) > abs(trackTrendDict['avgvil'][trackBinTuple]):
                                        trackTrendDict['avgvil'][trackBinTuple] = avgVILTrend
                                
                                if trackBinTuple not in list(trackTrendDictVCP['avgvil'].keys()):
                                    trackTrendDictVCP['avgvil'][trackBinTuple] = {vcpStringComb:avgVILTrend}
                                else:
                                    if abs(avgVILTrend) > abs(trackTrendDictVCP['avgvil'][trackBinTuple][vcpStringComb]):
                                        trackTrendDictVCP['avgvil'][trackBinTuple][vcpStringComb] = avgVILTrend
                                        
                                if isPositive:
                                    if trackBinTuple not in list(posTrackTrendDict['avgvil'].keys()):
                                        posTrackTrendDict['avgvil'][trackBinTuple] = avgVILTrend
                                    else:
                                        if abs(avgVILTrend) > abs(posTrackTrendDict['avgvil'][trackBinTuple]):
                                            posTrackTrendDict['avgvil'][trackBinTuple] = avgVILTrend
                                            
                                    if trackBinTuple not in list(posTrackTrendDictVCP['avgvil'].keys()):
                                        posTrackTrendDictVCP['avgvil'][trackBinTuple] = {vcpStringComb:avgVILTrend}
                                    else:
                                        if abs(avgVILTrend) > abs(posTrackTrendDictVCP['avgvil'][trackBinTuple][vcpStringComb]):
                                            posTrackTrendDictVCP['avgvil'][trackBinTuple][vcpStringComb] = avgVILTrend
                                            
                                        
                            if auto2.trackMaxVIL >= 0 and auto3.trackMaxVIL >= 0:
                                maxVILTrend = auto2.trackMaxVIL - auto3.trackMaxVIL
                                if trackBinTuple not in list(trackTrendDict['maxvil'].keys()):
                                    trackTrendDict['maxvil'][trackBinTuple] = maxVILTrend
                                else:
                                    if abs(maxVILTrend) > abs(trackTrendDict['maxvil'][trackBinTuple]):
                                        trackTrendDict['maxvil'][trackBinTuple] = maxVILTrend
                                
                                if trackBinTuple not in list(trackTrendDictVCP['maxvil'].keys()):
                                    trackTrendDictVCP['maxvil'][trackBinTuple] = {vcpStringComb:maxVILTrend}
                                else:
                                    if abs(maxVILTrend) > abs(trackTrendDictVCP['maxvil'][trackBinTuple][vcpStringComb]):
                                        trackTrendDictVCP['maxvil'][trackBinTuple][vcpStringComb] = maxVILTrend
                                        
                                if isPositive:
                                    if trackBinTuple not in list(posTrackTrendDict['maxvil'].keys()):
                                        posTrackTrendDict['maxvil'][trackBinTuple] = maxVILTrend
                                    else:
                                        if abs(maxVILTrend) > abs(posTrackTrendDict['maxvil'][trackBinTuple]):
                                            posTrackTrendDict['maxvil'][trackBinTuple] = maxVILTrend
                                            
                                    if trackBinTuple not in list(posTrackTrendDictVCP['maxvil'].keys()):
                                        posTrackTrendDictVCP['maxvil'][trackBinTuple] = {vcpStringComb:maxVILTrend}
                                    else:
                                        if abs(maxVILTrend) > abs(posTrackTrendDictVCP['maxvil'][trackBinTuple][vcpStringComb]):
                                            posTrackTrendDictVCP['maxvil'][trackBinTuple][vcpStringComb] = maxVILTrend
                                            
                            if auto2.trackMaxREF >= 0 and auto3.trackMaxREF >= 0:
                                maxREFTrend = auto2.trackMaxREF - auto3.trackMaxREF
                                if trackBinTuple not in list(trackTrendDict['maxref'].keys()):
                                    trackTrendDict['maxref'][trackBinTuple] = maxREFTrend
                                else:
                                    if abs(maxREFTrend) > trackTrendDict['maxref'][trackBinTuple]:
                                        trackTrendDict['maxref'][trackBinTuple] = maxREFTrend
                                
                                if trackBinTuple not in list(trackTrendDictVCP['maxref'].keys()):
                                    trackTrendDictVCP['maxref'][trackBinTuple] = {vcpStringComb:maxREFTrend}
                                else:
                                    if abs(maxREFTrend) > abs(trackTrendDictVCP['maxref'][trackBinTuple][vcpStringComb]):
                                        trackTrendDictVCP['maxref'][trackBinTuple][vcpStringComb] = maxREFTrend
                                        
                                if isPositive:
                                    if trackBinTuple not in list(posTrackTrendDict['maxref'].keys()):
                                        posTrackTrendDict['maxref'][trackBinTuple] = maxREFTrend
                                    else:
                                        if abs(maxREFTrend) > abs(posTrackTrendDict['maxref'][trackBinTuple]):
                                            posTrackTrendDict['maxref'][trackBinTuple] = maxREFTrend
                                            
                                    if trackBinTuple not in list(posTrackTrendDictVCP['maxref'].keys()):
                                        posTrackTrendDictVCP['maxref'][trackBinTuple] = {vcpStringComb:maxREFTrend}
                                    else:
                                        if abs(maxREFTrend) > abs(posTrackTrendDictVCP['maxref'][trackBinTuple][vcpStringComb]):
                                            posTrackTrendDictVCP['maxref'][trackBinTuple][vcpStringComb] = maxREFTrend
                                
                                
            # print('ET/VIL values for TC', TC, 'case', case, '\nmaxet', etDict['maxet'], '\nposet', posETDict['maxet'], '\n90thet', etDict['90thet'], '\npos90thet', posETDict['90thet'], '\navgvil', trackDict['avgvil'], '\nposavgvil', posTrackDict['avgvil'], \
                # '\nmaxvil', trackDict['maxvil'], '\nposmaxvil', posTrackDict['maxvil'], '\nmaxref', trackDict['maxref'], '\nposmaxref', posTrackDict['maxref'])           
            # print('ET/VIL trends for TC', TC, 'case', case, '\nmaxet', etTrendDict['maxet'], '\nposet', posETTrendDict['maxet'], '\n90thet', etTrendDict['90thet'], '\npos90thet', posETTrendDict['90thet'],  '\navgvil', trackTrendDict['avgvil'],\
                # '\nposavgvil', posTrackTrendDict['avgvil'], '\nmaxvil', trackTrendDict['maxvil'], '\nposmaxvil', posTrackTrendDict['maxvil'], '\nmaxref', trackTrendDict['maxref'], '\nposmaxref', posTrackTrendDict['maxref'])
            
            # print('VCP ET/VIL values for TC', TC, 'case', case, '\nmaxet', etDictVCP['maxet'], '\nposet', posETDictVCP['maxet'], '\n90thet', etDictVCP['90thet'], '\npos90thet', posETDictVCP['90thet'], '\navgvil', trackDictVCP['avgvil'], '\nposavgvil', posTrackDictVCP['avgvil'], \
                # '\nmaxvil', trackDictVCP['maxvil'], '\nposmaxvil', posTrackDictVCP['maxvil'], '\nmaxref', trackDictVCP['maxref'], '\nposmaxref', posTrackDictVCP['maxref'])           
            # print('VCP ET/VIL trends for TC', TC, 'case', case, '\nmaxet', etTrendDictVCP['maxet'], '\nposet', posETTrendDictVCP['maxet'], '\n90thet', etTrendDictVCP['90thet'], '\npos90thet', posETTrendDictVCP['90thet'],  '\navgvil', trackTrendDictVCP['avgvil'],\
                # '\nposavgvil', posTrackTrendDictVCP['avgvil'], '\nmaxvil', trackTrendDictVCP['maxvil'], '\nposmaxvil', posTrackTrendDictVCP['maxvil'], '\nmaxref', trackTrendDictVCP['maxref'], '\nposmaxref', posTrackTrendDictVCP['maxref'])
                
            #Get master ET/VIL values
            for etBin in list(etDict['maxet'].keys()):
                try:
                    etData['maxet'][etBin].append(max(etDict['maxet'][etBin]))
                except KeyError:
                    etData['maxet'][etBin] = [max(etDict['maxet'][etBin])]
            for etBin in list(etDictVCP['maxet'].keys()):
                for vcpString in list(etDictVCP['maxet'][etBin].keys()):
                    try:
                        etDataVCP['maxet'][etBin].setdefault(vcpString, []).append(max(etDictVCP['maxet'][etBin][vcpString]))
                    except KeyError as K:
                        print('Key-1 maxet', K, etBin, vcpString)
                        try:
                            etDataVCP['maxet'][etBin][vcpString] = [max(etDictVCP['maxet'][etBin][vcpString])]
                        except KeyError:
                            etDataVCP['maxet'][etBin] = {vcpString:[max(etDictVCP['maxet'][etBin][vcpString])]}
                            
            for etBin in list(posETDict['maxet'].keys()):
                try:
                    posETData['maxet'][etBin].append(max(posETDict['maxet'][etBin]))
                except KeyError:
                    posETData['maxet'][etBin] = [max(posETDict['maxet'][etBin])]
                    
            for etBin in list(posETDictVCP['maxet'].keys()):
                for vcpString in list(posETDictVCP['maxet'][etBin].keys()):
                    try:
                        posETDataVCP['maxet'][etBin].setdefault(vcpString, []).append(max(posETDictVCP['maxet'][etBin][vcpString]))
                    except KeyError as K:
                        print('Key-1 posmaxet', K, etBin, vcpString)
                        try:
                            posETDataVCP['maxet'][etBin][vcpString] = [max(posETDictVCP['maxet'][etBin][vcpString])]
                        except KeyError:
                            posETDataVCP['maxet'][etBin] = {vcpString:[max(posETDictVCP['maxet'][etBin][vcpString])]}
                            
                    
            for etBin in list(etDict['90thet'].keys()):
                try:
                    etData['90thet'][etBin].append(max(etDict['90thet'][etBin]))
                except KeyError:
                    etData['90thet'][etBin] = [max(etDict['90thet'][etBin])]
                    
            for etBin in list(etDictVCP['90thet'].keys()):
                for vcpString in list(etDictVCP['90thet'][etBin].keys()):
                    try:
                        etDataVCP['90thet'][etBin].setdefault(vcpString, []).append(max(etDictVCP['90thet'][etBin][vcpString]))
                    except KeyError as K:
                        print('Key-1 90thet', K, etBin, vcpString)
                        try:
                            etDataVCP['90thet'][etBin][vcpString] = [max(etDictVCP['90thet'][etBin][vcpString])]
                        except KeyError:
                            etDataVCP['90thet'][etBin] = {vcpString:[max(etDictVCP['90thet'][etBin][vcpString])]}
                            
                    
            for etBin in list(posETDict['90thet'].keys()):
                try:
                    posETData['90thet'][etBin].append(max(posETDict['90thet'][etBin]))
                except KeyError:
                    posETData['90thet'][etBin] = [max(posETDict['90thet'][etBin])]
                    
            for etBin in list(posETDictVCP['90thet'].keys()):
                for vcpString in list(posETDictVCP['90thet'][etBin].keys()):
                    try:
                        posETDataVCP['90thet'][etBin].setdefault(vcpString, []).append(max(posETDictVCP['90thet'][etBin][vcpString]))
                    except KeyError as K:
                        print('Key-1 pos90thet', K, etBin, vcpString)
                        try:
                            posETDataVCP['90thet'][etBin][vcpString] = [max(posETDictVCP['90thet'][etBin][vcpString])]
                        except KeyError:
                            posETDataVCP['90thet'][etBin] = {vcpString:[max(posETDictVCP['90thet'][etBin][vcpString])]}
            
            
            for trackBin in list(trackDict['avgvil'].keys()):
                try:
                    trackData['avgvil'][trackBin].append(max(trackDict['avgvil'][trackBin]))
                except KeyError:
                    trackData['avgvil'][trackBin] = [max(trackDict['avgvil'][trackBin])]
                    
            for trackBin in list(trackDictVCP['avgvil'].keys()):
                for vcpString in list(trackDictVCP['avgvil'][trackBin].keys()):
                    try:
                        trackDataVCP['avgvil'][trackBin].setdefault(vcpString, []).append(max(trackDictVCP['avgvil'][trackBin][vcpString]))
                    except KeyError as K:
                        print('Key-1 avgvil', K, trackBin, vcpString)
                        try:
                            trackDataVCP['avgvil'][trackBin][vcpString] = [max(trackDictVCP['avgvil'][trackBin][vcpString])]
                        except KeyError:
                            trackDataVCP['avgvil'][trackBin] = {vcpString:[max(trackDictVCP['avgvil'][trackBin][vcpString])]}
                    
            for trackBin in list(posTrackDict['avgvil'].keys()):
                try:
                    posTrackData['avgvil'][trackBin].append(max(posTrackDict['avgvil'][trackBin]))
                except KeyError:
                    posTrackData['avgvil'][trackBin] = [max(posTrackDict['avgvil'][trackBin])]
                    
            for trackBin in list(posTrackDictVCP['avgvil'].keys()):
                for vcpString in list(posTrackDictVCP['avgvil'][trackBin].keys()):
                    try:
                        posTrackDataVCP['avgvil'][trackBin].setdefault(vcpString, []).append(max(posTrackDictVCP['avgvil'][trackBin][vcpString]))
                    except KeyError as K:
                        print('Key-1 posavgvil', K, trackBin, vcpString)
                        try:
                            posTrackDataVCP['avgvil'][trackBin][vcpString] = [max(posTrackDictVCP['avgvil'][trackBin][vcpString])]
                        except KeyError:
                            posTrackDataVCP['avgvil'][trackBin] = {vcpString:[max(posTrackDictVCP['avgvil'][trackBin][vcpString])]}
                    
            for trackBin in list(trackDict['maxvil'].keys()):
                try:
                    trackData['maxvil'][trackBin].append(max(trackDict['maxvil'][trackBin]))
                except KeyError:
                    trackData['maxvil'][trackBin] = [max(trackDict['maxvil'][trackBin])]
                    
            for trackBin in list(trackDictVCP['maxvil'].keys()):
                for vcpString in list(trackDictVCP['maxvil'][trackBin].keys()):
                    try:
                        trackDataVCP['maxvil'][trackBin].setdefault(vcpString, []).append(max(trackDictVCP['maxvil'][trackBin][vcpString]))
                    except KeyError as K:
                        print('Key-1 maxvil', K, trackBin, vcpString)
                        try:
                            trackDataVCP['maxvil'][trackBin][vcpString] = [max(trackDictVCP['maxvil'][trackBin][vcpString])]
                        except KeyError:
                            trackDataVCP['maxvil'][trackBin] = {vcpString:[max(trackDictVCP['maxvil'][trackBin][vcpString])]}
                      
                    
            for trackBin in list(posTrackDict['maxvil'].keys()):
                try:
                    posTrackData['maxvil'][trackBin].append(max(posTrackDict['maxvil'][trackBin]))
                except KeyError:
                    posTrackData['maxvil'][trackBin] = [max(posTrackDict['maxvil'][trackBin])]
                    
            for trackBin in list(posTrackDictVCP['maxvil'].keys()):
                for vcpString in list(posTrackDictVCP['maxvil'][trackBin].keys()):
                    try:
                        posTrackDataVCP['maxvil'][trackBin].setdefault(vcpString, []).append(max(posTrackDictVCP['maxvil'][trackBin][vcpString]))
                    except KeyError as K:
                        print('Key-1 posmaxvil', K, trackBin, vcpString)
                        try:
                            posTrackDataVCP['maxvil'][trackBin][vcpString] = [max(posTrackDictVCP['maxvil'][trackBin][vcpString])]
                        except KeyError:
                            posTrackDataVCP['maxvil'][trackBin] = {vcpString:[max(posTrackDictVCP['maxvil'][trackBin][vcpString])]}
                            
                    
            for trackBin in list(trackDict['maxref'].keys()):
                try:
                    trackData['maxref'][trackBin].append(max(trackDict['maxref'][trackBin]))
                except KeyError:
                    trackData['maxref'][trackBin] = [max(trackDict['maxref'][trackBin])]
                    
            for trackBin in list(trackDictVCP['maxref'].keys()):
                for vcpString in list(trackDictVCP['maxref'][trackBin].keys()):
                    try:
                        trackDataVCP['maxref'][trackBin].setdefault(vcpString, []).append(max(trackDictVCP['maxref'][trackBin][vcpString]))
                    except KeyError as K:
                        print('Key-1 maxref', K, trackBin, vcpString)
                        try:
                            trackDataVCP['maxref'][trackBin][vcpString] = [max(trackDictVCP['maxref'][trackBin][vcpString])]
                        except KeyError:
                            trackDataVCP['maxref'][trackBin] = {vcpString:[max(trackDictVCP['maxref'][trackBin][vcpString])]}
                    
            for trackBin in list(posTrackDict['maxref'].keys()):
                try:
                    posTrackData['maxref'][trackBin].append(max(posTrackDict['maxref'][trackBin]))
                except KeyError:
                    posTrackData['maxref'][trackBin] = [max(posTrackDict['maxref'][trackBin])]
                    
            for trackBin in list(posTrackDictVCP['maxref'].keys()):
                for vcpString in list(posTrackDictVCP['maxref'][trackBin].keys()):
                    try:
                        posTrackDataVCP['maxref'][trackBin].setdefault(vcpString, []).append(max(posTrackDictVCP['maxref'][trackBin][vcpString]))
                    except KeyError as K:
                        print('Key-1 posmaxref', K, trackBin, vcpString)
                        try:
                            posTrackDataVCP['maxref'][trackBin][vcpString] = [max(posTrackDictVCP['maxref'][trackBin][vcpString])]
                        except KeyError:
                            posTrackDataVCP['maxref'][trackBin] = {vcpString:[max(posTrackDictVCP['maxref'][trackBin][vcpString])]}
                    
            
            #Get master ET/VIL trend data
            for etTrendBin in list(etTrendDict['maxet'].keys()):
                try:
                    etTrendData['maxet'][etTrendBin].append(etTrendDict['maxet'][etTrendBin])
                except KeyError:
                    etTrendData['maxet'][etTrendBin] = [etTrendDict['maxet'][etTrendBin]]
            
            for etTrendBin in list(etTrendDictVCP['maxet'].keys()):
                for vcpString in list(etTrendDictVCP['maxet'][etTrendBin].keys()):
                    try:
                        etTrendDataVCP['maxet'][etTrendBin].setdefault(vcpString, []).append(etTrendDictVCP['maxet'][etTrendBin][vcpString])
                    except KeyError as K:
                        print('Key-2 maxet', K, etTrendBin, vcpString)
                        try:
                            etTrendDataVCP['maxet'][etTrendBin][vcpString] = [etTrendDictVCP['maxet'][etTrendBin][vcpString]]
                        except KeyError:
                            etTrendDataVCP['maxet'][etTrendBin] = {vcpString:[etTrendDictVCP['maxet'][etTrendBin][vcpString]]}
                            
            for etTrendBin in list(posETTrendDict['maxet'].keys()):
                try:
                    posETTrendData['maxet'][etTrendBin].append(posETTrendDict['maxet'][etTrendBin])
                except KeyError:
                    posETTrendData['maxet'][etTrendBin] = [posETTrendDict['maxet'][etTrendBin]]
                    
            for etTrendBin in list(posETTrendDictVCP['maxet'].keys()):
                for vcpString in list(posETTrendDictVCP['maxet'][etTrendBin].keys()):
                    try:
                        posETTrendDataVCP['maxet'][etTrendBin].setdefault(vcpString, []).append(posETTrendDictVCP['maxet'][etTrendBin][vcpString])
                    except KeyError as K:
                        print('Key-2 posmaxet', K, etTrendBin, vcpString)
                        try:
                            posETTrendDataVCP['maxet'][etTrendBin][vcpString] = [posETTrendDictVCP['maxet'][etTrendBin][vcpString]]
                        except KeyError:
                            posETTrendDataVCP['maxet'][etTrendBin] = {vcpString:[posETTrendDictVCP['maxet'][etTrendBin][vcpString]]}
                    
            for etTrendBin in list(etTrendDict['90thet'].keys()):
                try:
                    etTrendData['90thet'][etTrendBin].append(etTrendDict['90thet'][etTrendBin])
                except KeyError:
                    etTrendData['90thet'][etTrendBin] = [etTrendDict['90thet'][etTrendBin]]
                    
            for etTrendBin in list(etTrendDictVCP['90thet'].keys()):
                for vcpString in list(etTrendDictVCP['90thet'][etTrendBin].keys()):
                    try:
                        etTrendDataVCP['90thet'][etTrendBin].setdefault(vcpString, []).append(etTrendDictVCP['90thet'][etTrendBin][vcpString])
                    except KeyError:
                        print('Key-2 90thet', etTrendBin, vcpString)
                        try:
                            etTrendDataVCP['90thet'][etTrendBin][vcpString] = [etTrendDictVCP['90thet'][etTrendBin][vcpString]]
                        except KeyError:
                            etTrendDataVCP['90thet'][etTrendBin] = {vcpString:[etTrendDictVCP['90thet'][etTrendBin][vcpString]]}
                            
                            
            for etTrendBin in list(posETTrendDict['90thet'].keys()):
                try:
                    posETTrendData['90thet'][etTrendBin].append(posETTrendDict['90thet'][etTrendBin])
                except KeyError:
                    posETTrendData['90thet'][etTrendBin] = [posETTrendDict['90thet'][etTrendBin]]
            
            for etTrendBin in list(posETTrendDictVCP['90thet'].keys()):
                for vcpString in list(posETTrendDictVCP['90thet'][etTrendBin].keys()):
                    try:
                        posETTrendDataVCP['90thet'][etTrendBin].setdefault(vcpString, []).append(posETTrendDictVCP['90thet'][etTrendBin][vcpString])
                    except KeyError as K:
                        print('Key-2 pos90thet', K, etTrendBin, vcpString)
                        try:
                            posETTrendDataVCP['90thet'][etTrendBin][vcpString] = [posETTrendDictVCP['90thet'][etTrendBin][vcpString]]
                        except KeyError:
                            posETTrendDataVCP['90thet'][etTrendBin] = {vcpString:[posETTrendDictVCP['90thet'][etTrendBin][vcpString]]}
                            
                            
            for trackBinTuple in list(trackTrendDict['avgvil'].keys()):
                try:    
                    trackTrendData['avgvil'][trackBinTuple].append(trackTrendDict['avgvil'][trackBinTuple])
                except KeyError:
                    trackTrendData['avgvil'][trackBinTuple] = [trackTrendDict['avgvil'][trackBinTuple]]
                    
            for trackBinTuple in list(trackTrendDictVCP['avgvil'].keys()):
                for vcpString in list(trackTrendDictVCP['avgvil'][trackBinTuple].keys()):
                    try:
                        trackTrendDataVCP['avgvil'][trackBinTuple].setdefault(vcpString, []).append(trackTrendDictVCP['avgvil'][trackBinTuple][vcpString])
                    except KeyError as K:
                        print('Key-2 avgvil', K, trackBinTuple, vcpString)
                        try:
                            trackTrendDataVCP['avgvil'][trackBinTuple][vcpString] = [trackTrendDictVCP['avgvil'][trackBinTuple][vcpString]]
                        except KeyError:
                            trackTrendDataVCP['avgvil'][trackBinTuple] = {vcpString:[trackTrendDictVCP['avgvil'][trackBinTuple][vcpString]]}
                    
            for trackBinTuple in list(posTrackTrendDict['avgvil'].keys()):
                try:
                    posTrackTrendData['avgvil'][trackBinTuple].append(posTrackTrendDict['avgvil'][trackBinTuple])
                except KeyError:
                    posTrackTrendData['avgvil'][trackBinTuple] = [posTrackTrendDict['avgvil'][trackBinTuple]]
                    
            for trackBinTuple in list(posTrackTrendDictVCP['avgvil'].keys()):
                for vcpString in list(posTrackTrendDictVCP['avgvil'][trackBinTuple].keys()):
                    try:
                        posTrackTrendDataVCP['avgvil'][trackBinTuple].setdefault(vcpString, []).append(posTrackTrendDictVCP['avgvil'][trackBinTuple][vcpString])
                    except KeyError as K:
                        print('Key-2 posavgvil', K, trackBinTuple, vcpString)
                        try:
                            posTrackTrendDataVCP['avgvil'][trackBinTuple][vcpString] = [posTrackTrendDictVCP['avgvil'][trackBinTuple][vcpString]]
                        except KeyError:
                            posTrackTrendDataVCP['avgvil'][trackBinTuple] = {vcpString:[posTrackTrendDictVCP['avgvil'][trackBinTuple][vcpString]]}
                            
                    
            for trackBinTuple in list(trackTrendDict['maxvil'].keys()):
                try:
                    trackTrendData['maxvil'][trackBinTuple].append(trackTrendDict['maxvil'][trackBinTuple])
                except KeyError:
                    trackTrendData['maxvil'][trackBinTuple] = [trackTrendDict['maxvil'][trackBinTuple]]
                    
            for trackBinTuple in list(trackTrendDictVCP['maxvil'].keys()):
                for vcpString in list(trackTrendDictVCP['maxvil'][trackBinTuple].keys()):
                    try:
                        trackTrendDataVCP['maxvil'][trackBinTuple].setdefault(vcpString, []).append(trackTrendDictVCP['maxvil'][trackBinTuple][vcpString])
                    except KeyError as K:
                        print('Key-2 maxvil', K, trackBinTuple, vcpString)
                        try:
                            trackTrendDataVCP['maxvil'][trackBinTuple][vcpString] = [trackTrendDictVCP['maxvil'][trackBinTuple][vcpString]]
                        except KeyError:
                            trackTrendDataVCP['maxvil'][trackBinTuple] = {vcpString:[trackTrendDictVCP['maxvil'][trackBinTuple][vcpString]]}
                            
                    
            for trackBinTuple in list(posTrackTrendDict['maxvil'].keys()):
                try:
                    posTrackTrendData['maxvil'][trackBinTuple].append(posTrackTrendDict['maxvil'][trackBinTuple])
                except KeyError:
                    posTrackTrendData['maxvil'][trackBinTuple] = [posTrackTrendDict['maxvil'][trackBinTuple]]
                    
            for trackBinTuple in list(posTrackTrendDictVCP['maxvil'].keys()):
                for vcpString in list(posTrackTrendDictVCP['maxvil'][trackBinTuple].keys()):
                    try:
                        posTrackTrendDataVCP['maxvil'][trackBinTuple].setdefault(vcpString, []).append(posTrackTrendDictVCP['maxvil'][trackBinTuple][vcpString])
                    except KeyError as K:
                        print('Key-2 posmaxvil', K, trackBinTuple, vcpString)
                        try:
                            posTrackTrendDataVCP['maxvil'][trackBinTuple][vcpString] = [posTrackTrendDictVCP['maxvil'][trackBinTuple][vcpString]]
                        except KeyError:
                            posTrackTrendDataVCP['maxvil'][trackBinTuple] = {vcpString:[posTrackTrendDictVCP['maxvil'][trackBinTuple][vcpString]]}
                    
            for trackBinTuple in list(trackTrendDict['maxref'].keys()):
                try:
                    trackTrendData['maxref'][trackBinTuple].append(trackTrendDict['maxref'][trackBinTuple])
                except KeyError:
                    trackTrendData['maxref'][trackBinTuple] = [trackTrendDict['maxref'][trackBinTuple]]
                    
            for trackBinTuple in list(trackTrendDictVCP['maxref'].keys()):
                for vcpString in list(trackTrendDictVCP['maxref'][trackBinTuple].keys()):
                    try:
                        trackTrendDataVCP['maxref'][trackBinTuple].setdefault(vcpString, []).append(trackTrendDictVCP['maxref'][trackBinTuple][vcpString])
                    except KeyError as K:
                        print('Key-2 maxref', K, trackBinTuple, vcpString)
                        try:
                            trackTrendDataVCP['maxref'][trackBinTuple][vcpString] = [trackTrendDictVCP['maxref'][trackBinTuple][vcpString]]
                        except KeyError:
                            trackTrendDataVCP['maxref'][trackBinTuple] = {vcpString:[trackTrendDictVCP['maxref'][trackBinTuple][vcpString]]}
            
            for trackBinTuple in list(posTrackTrendDict['maxref'].keys()):
                try:
                    posTrackTrendData['maxref'][trackBinTuple].append(posTrackTrendDict['maxref'][trackBinTuple])
                except KeyError:
                    posTrackTrendData['maxref'][trackBinTuple] = [posTrackTrendDict['maxref'][trackBinTuple]]
            
            for trackBinTuple in list(posTrackTrendDictVCP['maxref'].keys()):
                for vcpString in list(posTrackTrendDictVCP['maxref'][trackBinTuple].keys()):
                    try:
                        posTrackTrendDataVCP['maxref'][trackBinTuple].setdefault(vcpString, []).append(posTrackTrendDictVCP['maxref'][trackBinTuple][vcpString])
                    except KeyError as K:
                        print('Key-2 posmaxref', K, trackBinTuple, vcpString)
                        try:
                            posTrackTrendDataVCP['maxref'][trackBinTuple][vcpString] = [posTrackTrendDictVCP['maxref'][trackBinTuple][vcpString]]
                        except KeyError:
                            posTrackTrendDataVCP['maxref'][trackBinTuple] = {vcpString:[posTrackTrendDictVCP['maxref'][trackBinTuple][vcpString]]}
            
            
            # print('ET/VIL master values for TC', TC, 'case', case, '\nmaxet', etData['maxet'], '\nposet', posETData['maxet'], '\n90thet', etData['90thet'], '\npos90thet', posETData['90thet'], '\navgvil',
                  # trackData['avgvil'], '\nposavgvil', posTrackData['avgvil'], '\nmaxvil', trackData['maxvil'],  '\nposmaxvil', posTrackData['maxvil'], '\nmaxref', trackData['maxref'], '\nposmaxref', posTrackData['maxref'])
            # print('ET/VIL master trends for TC', TC, 'case', case, '\nmaxet', etTrendData['maxet'], '\nposet', posETTrendData['maxet'], '\n90thet', etTrendData['90thet'], '\npos90thet', posETTrendData['90thet'], '\navgvil',\
            # trackTrendData['avgvil'], '\nposavgvil', posTrackTrendData['avgvil'], '\nmaxvil', trackTrendData['maxvil'], '\nposmaxvil', posTrackTrendData['maxvil'], '\nmaxref', trackTrendData['maxref'], '\nposmaxref', posTrackTrendData['maxref'])
            
            # print('ET/VIL VCP master values for TC', TC, 'case', case, '\nmaxet', etDataVCP['maxet'], '\nposet', posETDataVCP['maxet'], '\n90thet', etDataVCP['90thet'], '\npos90thet', posETDataVCP['90thet'], '\navgvil',
                 # trackDataVCP['avgvil'], '\nposavgvil', posTrackDataVCP['avgvil'], '\nmaxvil', trackDataVCP['maxvil'],  '\nposmaxvil', posTrackDataVCP['maxvil'], '\nmaxref', trackDataVCP['maxref'], '\nposmaxref', posTrackDataVCP['maxref'])
            # print('ET/VIL VCP master trends for TC', TC, 'case', case, '\nmaxet', etTrendDataVCP['maxet'], '\nposet', posETTrendDataVCP['maxet'], '\n90thet', etTrendDataVCP['90thet'], '\npos90thet', posETTrendDataVCP['90thet'], '\navgvil',\
            # trackTrendDataVCP['avgvil'], '\nposavgvil', posTrackTrendDataVCP['avgvil'], '\nmaxvil', trackTrendDataVCP['maxvil'], '\nposmaxvil', posTrackTrendDataVCP['maxvil'], '\nmaxref', trackTrendDataVCP['maxref'], '\nposmaxref', posTrackTrendDataVCP['maxref'])
                
            for tilt in tiltList:
                
                azShearDict = {}
                azShearRangeDict = {}
                azShearEFDict = {}
                posAzShearDict = {}
                posAzShearEFDict = {}
                posAzShearRangeDict = {}
                absAzShearDict = {}
                absAzShearRangeDict = {}
                absAzShearEFDict = {}
                top90AzShearDict = {}
                bottom10AzShearDict = {}
                vrotDict = {}
                vrotRangeDict = {}
                topPosVrotRangeDict = {}
                vrotPosDict = {}
                vrotEFDict = {}
                vrotPosEFDict = {}
                vrotPosRangeDict = {}
                vrotPosRangeEFDict = {}
                topPosVrotRangeEFDict = {}
                spectrumWidthDict = {}
                posSpectrumWidthDict = {}#    Max spectrum width for a +AzShear cluster
                
                minTDSDict = {}
                posMinTDSDict = {}#    Minimum TDS spectrum width for a +AzShear cluster
                currentEFRating = None
                
                #Now begin calculating trends for each data type.
                azShearTrendDict = {}
                azShearEFTrendDict = {}
                posAzShearTrendDict = {}
                posAzShearEFTrendDict = {}
                absAzShearTrendDict = {}
                absAzShearEFTrendDict = {}
                top90AzShearTrendDict = {}
                bottom10AzShearTrendDict = {}
                vrotTrendDict = {}
                vrotPosTrendDict = {}
                vrotEFTrendDict = {}
                vrotPosEFTrendDict = {}
                spectrumWidthTrendDict = {}
                posSpectrumWidthTrendDict = {}#    Max spectrum width for a +AzShear cluster
                
                halfCurrentBin = None
                for auto in autoObjects[TC][case]:
                
                    if isTOR:
                        currentEFRating = auto.efRating
                        
                    try:
                        currentTiltObject = auto.azShear[tilt]
                    except KeyError:
                        continue
                        
                    currentBH = currentTiltObject.beamHeights['0']
                    meetsBH = currentBH <= cfg.maxAzShearHeight and currentBH >= 0
                    currentBin = int(currentTiltObject.binNumber)
                    potentialClusters = currentTiltObject.potentialClusters
                   
                    halfCurrentBin = int(auto.azShear['0.5'].binNumber)
                    
                    #Going to try to retrieve the maximum (or minimum/most favorable value) from each bin
                    #Vrot variables also need to be less than the maximum beam height. Set the maximum beamheight in config.csv. Negative values indicate infinity
                    
                    #Check for missing values before adding the criteria for beam height as the BH would be -99904
                    if currentTiltObject.maxShear == -99904 and halfCurrentBin is not None:
                            
                            try:
                                missingCount[str(tilt)]['azshear'][str(halfCurrentBin)] += 1
                            except KeyError:
                                missingCount[str(tilt)]['azshear'][str(halfCurrentBin)] = 1
                            
                            if isTOR:
                                try:
                                    missingCountEF[str(tilt)]['azshear'][str(halfCurrentBin)][currentEFRating] += 1
                                except KeyError:
                                    try:
                                        missingCountEF[str(tilt)]['azshear'][str(halfCurrentBin)][currentEFRating] = 1
                                    except KeyError:
                                        missingCountEF[str(tilt)]['azshear'][str(halfCurrentBin)] = {currentEFRating:1}
                    if currentTiltObject.top90Shear == -99904 and halfCurrentBin is not None:
                            try:
                                missingCount[str(tilt)]['90thazshear'][str(halfCurrentBin)] += 1
                            except KeyError:
                                missingCount[str(tilt)]['90thazshear'] = {str(halfCurrentBin):1}
                            
                            if isTOR:
                                try:
                                    missingCountEF[str(tilt)]['90thazshear'][str(halfCurrentBin)][currentEFRating] += 1
                                except KeyError:
                                    try:
                                        missingCountEF[str(tilt)]['90thazshear'][str(halfCurrentBin)][currentEFRating] = 1
                                    except KeyError:
                                        missingCountEF[str(tilt)]['90thazshear'][str(halfCurrentBin)] = {currentEFRating:1}
                                    
                    if currentTiltObject.bottom10Shear == -99904 and halfCurrentBin is not None:
                        try:
                            missingCount[str(tilt)]['10thazshear'][str(halfCurrentBin)] += 1
                        except KeyError:
                            missingCount[str(tilt)]['10thazshear'] = {str(halfCurrentBin):1}
                            
                        if isTOR:
                            try:
                                missingCountEF[str(tilt)]['10thazshear'][str(halfCurrentBin)][currentEFRating] += 1
                            except KeyError:
                                try:
                                    missingCountEF[str(tilt)]['10thazshear'][str(halfCurrentBin)][currentEFRating] = 1
                                except KeyError:
                                    missingCountEF[str(tilt)]['10thazshear'][str(halfCurrentBin)] = {currentEFRating:1}
                                    
                    if currentTiltObject.maxSpectrumWidth == -99904 and halfCurrentBin is not None:
                        try:
                            missingCount[str(tilt)]['spectrumwidth'][str(halfCurrentBin)] += 1
                        except KeyError:
                            missingCount[str(tilt)]['spectrumwidth'][str(halfCurrentBin)] = 1
                            
                        if isTOR:
                            try:
                                missingCountEF[str(tilt)]['spectrumwidth'][str(halfCurrentBin)][currentEFRating] += 1
                            except KeyError:
                                try:
                                    missingCountEF[str(tilt)]['spectrumwidth'][str(halfCurrentBin)][currentEFRating] = 1
                                except KeyError:
                                    missingCountEF[str(tilt)]['spectrumwidth'][str(halfCurrentBin)] = {currentEFRating:1}
                                        
                        if currentTiltObject.TDSmin == -99904 and halfCurrentBin is not None:
                            try:
                                missingCount[str(tilt)]['mintdscc'][str(halfCurrentBin)] += 1
                            except KeyError:
                                missingCount[str(tilt)]['mintdscc'][str(halfCurrentBin)] = 1
                                
                            if isTOR:
                                try:
                                    missingCountEF[str(tilt)]['mintdscc'][str(halfCurrentBin)][currentEFRating] += 1
                                except KeyError:
                                    try:
                                        missingCountEF[str(tilt)]['mintdscc'][str(halfCurrentBin)][currentEFRating] = 1
                                    except KeyError:
                                        missingCountEF[str(tilt)]['mintdscc'][str(halfCurrentBin)] = {currentEFRating:1}
                     

                    #Start actually binning 
                    if int(currentBin) > -99900 and meetsBH and potentialClusters <= maxPotentialClusters and potentialClusters >= 0:
                        if currentTiltObject.maxShear > -99900 and meetsBH:
                            appendShear = currentTiltObject.maxShear
                            # if appendShear < 0:
                                # appendShear = currentTiltObject.minShear
                                
                            try:
                                azShearDict[str(currentBin)].append(appendShear)
                                azShearRangeDict[str(currentBin)].append((appendShear, currentTiltObject.groundRanges['0']))
                            except KeyError:
                                azShearDict[str(currentBin)] = [appendShear]
                                azShearRangeDict[str(currentBin)] = [(appendShear, currentTiltObject.groundRanges['0'])]
                                
                            if isTOR:
                                #print('starthere', azShearEFDict)
                                try:
                                    azShearEFDict[str(currentBin)][currentEFRating].append(appendShear)
                                except KeyError:
                                    try:
                                        azShearEFDict[str(currentBin)][currentEFRating] = [appendShear]
                                    except KeyError:
                                        azShearEFDict[str(currentBin)] = {currentEFRating:[appendShear]}

                        if currentTiltObject.absShear is not None and meetsBH:
                            try:
                                absAzShearDict[str(currentBin)].append(currentTiltObject.absShear)
                                absAzShearRangeDict[str(currentBin)].append((currentTiltObject.absShear, currentTiltObject.groundRanges['0']))
                            except KeyError:
                                absAzShearDict[str(currentBin)] = [currentTiltObject.absShear]
                                absAzShearRangeDict[str(currentBin)] = [(currentTiltObject.absShear, currentTiltObject.groundRanges['0'])]
                                
                            if isTOR:
                                
                                try:
                                    absAzShearEFDict[str(currentBin)][currentEFRating].append(currentTiltObject.absShear)
                                except KeyError:
                                    try:
                                        absAzShearEFDict[str(currentBin)][currentEFRating] = [currentTiltObject.absShear]
                                    except KeyError:
                                        absAzShearEFDict[str(currentBin)] = {currentEFRating:[currentTiltObject.absShear]}
                                       
                                        
                                        
                        if currentTiltObject.maxShear >= 0 and meetsBH:
                            try:
                                posAzShearDict[str(currentBin)].append(currentTiltObject.maxShear)
                                posAzShearRangeDict[str(currentBin)].append((currentTiltObject.maxShear, currentTiltObject.groundRanges['0']))
                            except KeyError:
                                posAzShearDict[str(currentBin)] = [currentTiltObject.maxShear]
                                posAzShearRangeDict[str(currentBin)] = [(currentTiltObject.maxShear, currentTiltObject.groundRanges['0'])]
                                
                            if isTOR:
                                
                                try:
                                    posAzShearEFDict[str(currentBin)][currentEFRating].append(currentTiltObject.maxShear)
                                except KeyError:
                                    try:
                                        posAzShearEFDict[str(currentBin)][currentEFRating] = [currentTiltObject.maxShear]
                                    except KeyError:
                                        posAzShearEFDict[str(currentBin)] = {currentEFRating:[currentTiltObject.maxShear]}
                                             
                            if currentTiltObject.maxSpectrumWidth >= 0: #Spectrum width should not be negative
                                try:
                                    posSpectrumWidthDict[str(currentBin)].append(currentTiltObject.maxSpectrumWidth)
                                except KeyError:
                                    posSpectrumWidthDict[str(currentBin)] = [currentTiltObject.maxSpectrumWidth]
                            else:
                                print('Weird. Spectrum width was negative', TC, case)
                                    
                                    
                            if currentTiltObject.TDSmin >= 0 and meetsBH and currentTiltObject.TDSmin <= 1.5:
                                try:
                                    posMinTDSDict[str(currentBin)].append(currentTiltObject.TDSmin)
                                except KeyError:
                                    posMinTDSDict[str(currentBin)] = [currentTiltObject.TDSmin]
                                    
                            if currentTiltObject.top90Shear > -99900 and meetsBH:
                                try:
                                    top90AzShearDict[str(currentBin)].append(currentTiltObject.top90Shear)
                                except KeyError:
                                    top90AzShearDict[str(currentBin)] = [currentTiltObject.top90Shear]
                                    
                            
                                
                                
                        else:
                            if not isNegAzShear:
                                totalNegAzShearLT += 1
                                isNegAzShear = True
                                if case not in negativeAzShearCases:
                                    negativeAzShearCases.append((TC, case))
                            
                        
                        if currentTiltObject.bottom10Shear < 0 and currentTiltObject.bottom10Shear > -99900 and currentTiltObject.maxShear < 0 and meetsBH:
                            try:
                                bottom10AzShearDict[str(currentBin)].append(currentTiltObject.bottom10Shear)
                            except KeyError:
                                bottom10AzShearDict[str(currentBin)] = [currentTiltObject.bottom10Shear]
                            
                        
                                
                        if currentTiltObject.rVrots[cfg.radius] and meetsBH:
                            try:
                                vrotDict[str(currentBin)].append(currentTiltObject.rVrots[cfg.radius])
                                vrotRangeDict[str(currentBin)].append((currentTiltObject.rVrots[cfg.radius], currentTiltObject.groundRanges['0']))
                            except KeyError:
                                vrotDict[str(currentBin)] = [currentTiltObject.rVrots[cfg.radius]]
                                vrotRangeDict[str(currentBin)] = [(currentTiltObject.rVrots[cfg.radius], currentTiltObject.groundRanges['0'])]
                                
                            if isTOR:
                                try:
                                    vrotEFDict[str(currentBin)][currentEFRating].append(currentTiltObject.rVrots[cfg.radius])
                                except KeyError:
                                    try:    
                                        vrotEFDict[str(currentBin)][currentEFRating] = [currentTiltObject.rVrots[cfg.radius]]
                                    except KeyError:
                                        vrotEFDict[str(currentBin)] = {currentEFRating:[currentTiltObject.rVrots[cfg.radius]]}
                                
                        if currentTiltObject.maxShear >= 0 and meetsBH:
                            topVrot = toVrot(currentTiltObject.top90Shear, cfg.radius)
                            try:
                                vrotPosDict[str(currentBin)].append(currentTiltObject.rVrots[cfg.radius])
                                vrotPosRangeDict[str(currentBin)].append((currentTiltObject.rVrots[cfg.radius], currentTiltObject.groundRanges['0']))
                                topPosVrotRangeDict[str(currentBin)].append((topVrot, currentTiltObject.groundRanges['0']))
                            except KeyError:
                                vrotPosDict[str(currentBin)] = [currentTiltObject.rVrots[cfg.radius]] 
                                vrotPosRangeDict[str(currentBin)] = [(currentTiltObject.rVrots[cfg.radius], currentTiltObject.groundRanges['0'])]
                                topPosVrotRangeDict[str(currentBin)] = [(topVrot, currentTiltObject.groundRanges['0'])]
                                
                            
                            if isTOR:
                                try:
                                    vrotPosEFDict[str(currentBin)][currentEFRating].append(currentTiltObject.rVrots[cfg.radius])
                                    vrotPosRangeEFDict[str(currentBin)][currentEFRating].append((currentTiltObject.rVrots[cfg.radius], currentTiltObject.groundRanges['0']))
                                    topPosVrotRangeEFDict[str(currentBin)][currentEFRating].append((topVrot, currentTiltObject.groundRanges['0']))
                                except KeyError:
                                    try:    
                                        vrotPosEFDict[str(currentBin)][currentEFRating] = [currentTiltObject.rVrots[cfg.radius]]
                                        vrotPosRangeEFDict[str(currentBin)][currentEFRating] = [(currentTiltObject.rVrots[cfg.radius], currentTiltObject.groundRanges['0'])]
                                        topPosVrotRangeEFDict[str(currentBin)][currentEFRating] = [(topVrot, currentTiltObject.groundRanges['0'])]
                                    except KeyError:
                                        vrotPosEFDict[str(currentBin)] = {currentEFRating:[currentTiltObject.rVrots[cfg.radius]]}
                                        vrotPosRangeEFDict[str(currentBin)] = {currentEFRating:[(currentTiltObject.rVrots[cfg.radius], currentTiltObject.groundRanges['0'])]}
                                        topPosVrotRangeEFDict[str(currentBin)] = {currentEFRating:[(topVrot, currentTiltObject.groundRanges['0'])]}
                                
                        if currentTiltObject.maxSpectrumWidth >= 0 and meetsBH: #Again, spectrum width shouldn't be negative
                            try:
                                spectrumWidthDict[str(currentBin)].append(currentTiltObject.maxSpectrumWidth)
                            except KeyError:
                                spectrumWidthDict[str(currentBin)] = [currentTiltObject.maxSpectrumWidth]
                                
                                
                        if currentTiltObject.TDSmin >= 0 and meetsBH and currentTiltObject.TDSmin <= 1.5:
                            try:
                                minTDSDict[str(currentBin)].append(currentTiltObject.TDSmin)
                            except KeyError:
                                minTDSDict[str(currentBin)] = [currentTiltObject.TDSmin]
                        

                    
                        for auto4 in autoObjects[TC][case]:
                            try:
                                secondTiltObject = auto4.azShear[tilt]
                            except KeyError:
                                continue
                            
                            secondBin = int(secondTiltObject.binNumber)
                            secondBH = secondTiltObject.beamHeights['0']
                            secondMeetsBH = secondBH <= cfg.maxAzShearHeight and secondBH >= 0
                            secondEFRating = None
                            secondPotentialClusters = secondTiltObject.potentialClusters
                            if isTOR:
                                secondEFRating = auto4.efRating
                                
                                if secondEFRating == currentEFRating:
                                    pass
                                else:
                                    print('EF rating mismatch in trend')
                                    continue
                                    
                            if secondBin > -99900 and secondMeetsBH and secondPotentialClusters <= maxPotentialClusters and secondPotentialClusters >= 0\
                                and potentialClusters <= maxPotentialClusters and potentialClusters >= 0:
                                if secondBin > currentBin:
                                    trendTuple = (currentBin, secondBin)
                                else:
                                    continue
                                if secondTiltObject.maxShear > -99900 and currentTiltObject.maxShear > -99900:
                                    maxAzShearTrend = secondTiltObject.maxShear - currentTiltObject.maxShear
                                    if secondTiltObject.maxShear < 0 and currentTiltObject.maxShear < 0:
                                        maxAzShearTrend = maxAzShearTrend * -1
                                        
                                    if trendTuple not in list(azShearTrendDict.keys()):
                                        azShearTrendDict[trendTuple] = maxAzShearTrend
                                    else:
                                        if abs(maxAzShearTrend) > abs(azShearTrendDict[trendTuple]):
                                            azShearTrendDict[trendTuple] = maxAzShearTrend
                                    
                                    if isTOR:
                                        try:
                                            if trendTuple not in list(azShearEFTrendDict.keys()):
                                                azShearEFTrendDict[trendTuple][secondEFRating] = maxAzShearTrend
                                            else:
                                                if abs(maxAzShearTrend) > abs(azShearEFTrendDict[trendTuple][secondEFRating]):
                                                     azShearEFTrendDict[trendTuple][secondEFRating] = maxAzShearTrend
                                        except KeyError:
                                            if trendTuple not in list(azShearEFTrendDict.keys()):
                                                azShearEFTrendDict[trendTuple] = {secondEFRating:maxAzShearTrend}
                                            else:
                                                if abs(maxAzShearTrend) > abs(azShearEFTrendDict[trendTuple][secondEFRating]):
                                                      azShearEFTrendDict[trendTuple] = {secondEFRating:maxAzShearTrend}
                                                      
                                if secondTiltObject.absShear is not None and currentTiltObject.absShear is not None:
                                    absShearTrend = secondTiltObject.absShear - currentTiltObject.absShear
                                    if trendTuple not in list(absAzShearTrendDict.keys()):
                                        absAzShearTrendDict[trendTuple] = absShearTrend
                                    else:
                                        if abs(absShearTrend) > abs(absAzShearTrendDict[trendTuple]):
                                            absAzShearTrendDict[trendTuple] = absShearTrend
                                            
                                    if isTOR:
                                        try:
                                            if trendTuple not in list(absAzShearEFTrendDict.keys()):
                                                absAzShearEFTrendDict[trendTuple][secondEFRating] = absShearTrend
                                            else:
                                                if abs(absShearTrend) > abs(absAzShearEFTrendDict[trendTuple][secondEFRating]):
                                                    absAzShearEFTrendDict[trendTuple][secondEFRating] = absShearTrend
                                        except KeyError:
                                            if trendTuple not in list(absAzShearEFTrendDict.keys()):
                                                absAzShearEFTrendDict[trendTuple] = {secondEFRating:absShearTrend}
                                            else:
                                                if abs(absShearTrend) > abs(absAzShearEFTrendDict[trendTuple][secondEFRating]):
                                                    absAzShearEFTrendDict[trendTuple] = {secondEFRating:absShearTrend}
                                                     
                                if secondTiltObject.maxShear >= 0 and currentTiltObject.maxShear >= 0:
                                    posAzShearTrend = secondTiltObject.maxShear - currentTiltObject.maxShear
                                    if trendTuple not in list(posAzShearTrendDict.keys()):
                                        posAzShearTrendDict[trendTuple] = posAzShearTrend
                                    else:
                                        if abs(posAzShearTrend) > abs(posAzShearTrendDict[trendTuple]):
                                            posAzShearTrendDict[trendTuple] = posAzShearTrend
                                            
                                    if isTOR:
                                        try:
                                            if trendTuple not in list(posAzShearEFTrendDict.keys()):
                                                posAzShearEFTrendDict[trendTuple][secondEFRating] = posAzShearTrend
                                            else:
                                                if abs(posAzShearTrend) > abs(posAzShearEFTrendDict[trendTuple][secondEFRating]):
                                                    posAzShearEFTrendDict[trendTuple][secondEFRating] = posAzShearTrend
                                        except KeyError:
                                            if trendTuple not in list(posAzShearEFTrendDict.keys()):
                                                posAzShearEFTrendDict[trendTuple] = {secondEFRating:posAzShearTrend}
                                            else:
                                                if abs(posAzShearTrend) > abs(posAzShearEFTrendDict[trendTuple][secondEFRating]):
                                                    posAzShearEFTrendDict[trendTuple] = {secondEFRating:posAzShearTrend}
                                                    
                                    if secondTiltObject.maxSpectrumWidth >= 0 and currentTiltObject.maxSpectrumWidth >= 0:
                                        posSpectrumWidthTrend = secondTiltObject.maxSpectrumWidth - currentTiltObject.maxSpectrumWidth
                                        if trendTuple not in list(posSpectrumWidthTrendDict.keys()):
                                            posSpectrumWidthTrendDict[trendTuple] = posSpectrumWidthTrend
                                        else:
                                            if abs(posSpectrumWidthTrend) > abs(posSpectrumWidthTrendDict[trendTuple]):
                                                posSpectrumWidthTrendDict[trendTuple] = posSpectrumWidthTrend
                                                
                                    if secondTiltObject.top90Shear >= 0 and currentTiltObject.top90Shear >= 0:
                                        top90ShearTrend = secondTiltObject.top90Shear - currentTiltObject.top90Shear
                                        if trendTuple not in list(top90AzShearTrendDict.keys()):
                                            top90AzShearTrendDict[trendTuple] = top90ShearTrend
                                        else:
                                            if abs(top90ShearTrend) > abs(top90AzShearTrendDict[trendTuple]):
                                                top90AzShearTrendDict[trendTuple] = top90ShearTrend
                                #Put bottom90 azshear trend here
                                if secondTiltObject.bottom10Shear < 0 and secondTiltObject.bottom10Shear > -99900 and\
                                    secondTiltObject.maxShear < 0 and currentTiltObject.maxShear < 0 and\
                                    currentTiltObject.bottom10Shear < 0 and currentTiltObject.bottom10Shear > -99900:
                                    
                                    bottom10ShearTrend = secondTiltObject.bottom10Shear - currentTiltObject.bottom10Shear
                                    
                                    if trendTuple not in list(bottom10AzShearDict.keys()):
                                        bottom10AzShearTrendDict[trendTuple] = bottom10ShearTrend
                                    else:
                                        if abs(bottom10ShearTrend) > abs(bottom10AzShearTrendDict[trendTuple]):
                                            bottom10AzShearTrendDict[trendTuple] = bottom10ShearTrend
                                            
                                if secondTiltObject.rVrots[cfg.radius] and currentTiltObject.rVrots[cfg.radius]:
                                    vrotTrend = secondTiltObject.rVrots[cfg.radius] - currentTiltObject.rVrots[cfg.radius]
                                    if trendTuple not in list(vrotTrendDict.keys()):
                                        vrotTrendDict[trendTuple] = vrotTrend
                                    else:
                                        if abs(vrotTrend) > abs(vrotTrendDict[trendTuple]):
                                            vrotTrendDict[trendTuple] = vrotTrend
                                            
                                    if isTOR:
                                        try:
                                            if trendTuple not in list(vrotEFTrendDict.keys()):
                                                vrotEFTrendDict[trendTuple][secondEFRating] = vrotTrend
                                            else:
                                                if abs(vrotTrend) > abs(vrotEFTrendDict[trendTuple][secondEFRating]):
                                                    vrotEFTrendDict[trendTuple][secondEFRating] = vrotTrend
                                        except KeyError:
                                            if trendTuple not in list(vrotEFTrendDict.keys()):
                                                vrotEFTrendDict[trendTuple] = {secondEFRating:vrotTrend}
                                            else:
                                                if abs(vrotTrend) > abs(vrotEFTrendDict[trendTuple][secondEFRating]):
                                                    vrotEFTrendDict[trendTuple] = {secondEFRating:vrotTrend}
                                                    
                                if secondTiltObject.maxShear >= 0 and currentTiltObject.maxShear >= 0:
                                    posVrotTrend = secondTiltObject.rVrots[cfg.radius] - currentTiltObject.rVrots[cfg.radius]
                                    if trendTuple not in list(vrotPosTrendDict.keys()):
                                        vrotPosTrendDict[trendTuple] = posVrotTrend
                                    else:
                                        if abs(posVrotTrend) > abs(vrotPosTrendDict[trendTuple]):
                                            vrotPosTrendDict[trendTuple] = posVrotTrend
                                    if isTOR:
                                        try:
                                            if trendTuple not in list(vrotPosEFTrendDict.keys()):
                                                vrotPosEFTrendDict[trendTuple][secondEFRating] = posVrotTrend
                                            else:
                                                if abs(vrotTrend) > abs(vrotPosEFTrendDict[trendTuple][secondEFRating]):
                                                    vrotPosEFTrendDict[trendTuple][secondEFRating] = posVrotTrend
                                        except KeyError:
                                            if trendTuple not in list(vrotPosEFTrendDict.keys()):
                                                vrotPosEFTrendDict[trendTuple] = {secondEFRating:posVrotTrend}
                                            else:
                                                if abs(posVrotTrend) > abs(vrotPosEFTrendDict[trendTuple][secondEFRating]):
                                                    vrotPosEFTrendDict[trendTuple] = {secondEFRating:posVrotTrend}
                                                    
                                if secondTiltObject.maxSpectrumWidth >= 0 and currentTiltObject.maxSpectrumWidth >= 0:
                                    spectrumWidthTrend = secondTiltObject.maxSpectrumWidth - currentTiltObject.maxSpectrumWidth
                                    if trendTuple not in list(spectrumWidthTrendDict.keys()):
                                        spectrumWidthTrendDict[trendTuple] = spectrumWidthTrend
                                    else:
                                        if abs(spectrumWidthTrend) > abs(spectrumWidthTrendDict[trendTuple]):
                                            spectrumWidthTrendDict[trendTuple] = spectrumWidthTrend

                                                
                    else:
                        print('Skipped', TC, case, tilt, 'for invalid bin number or beam height')
                        skippedCount += 1
                        
                # print('azshear', azShearDict, '\ntop90shear', top90AzShearDict, '\nposazshear', posAzShearDict, '\nabsazshear', absAzShearDict,'\nvrotDict', vrotDict, '\nbottom10azshear', bottom10AzShearDict, '\nspectrumWidthDict', spectrumWidthDict, '\nminTDSDict', minTDSDict)
                # print('azshearefdict', azShearEFDict)
                # print('trend data azshear', azShearTrendDict, '\nabsazshear', absAzShearTrendDict, '\nbottom10azshear', bottom10AzShearTrendDict, '\ntop90shear', top90AzShearTrendDict, '\nposazshear', posAzShearTrendDict)
                # print('EF rating trends azshearef', azShearEFTrendDict, '\nabsazshearef', absAzShearEFTrendDict)
                # print('Range Dictionaries azshear', azShearRangeDict, '\nposazshear', posAzShearRangeDict, '\nabsazshear', absAzShearRangeDict,\
                    # '\nvrot', vrotRangeDict, '\nposvrot', vrotPosRangeDict)
                
                
                #Add each to the master lists
                for bin in list(azShearDict.keys()):
                    chosenIndex = azShearDict[bin].index(max(azShearDict[bin]))
                    try:
                        tiltData[str(tilt)]['azshear'][bin].append(azShearDict[bin][chosenIndex])
                        tiltDataRange[str(tilt)]['azshear'][bin].append(azShearRangeDict[bin][chosenIndex])
                    except KeyError:
                        tiltData[str(tilt)]['azshear'][bin] = [azShearDict[bin][chosenIndex]]
                        tiltDataRange[str(tilt)]['azshear'][bin] = [azShearRangeDict[bin][chosenIndex]]
                        
                for bin in list(azShearEFDict.keys()):
                    if isTOR:
                        for EF in list(azShearEFDict[bin].keys()):
                            try:
                                tiltDataEF[str(tilt)]['azshear'][bin].setdefault(EF, []).append(max(azShearEFDict[bin][EF]))
                            except KeyError as K:
                                print('Key 3', str(K), tilt, 'azshear', bin, EF)
                                try:
                                    tiltDataEF[str(tilt)]['azshear'][bin] = {EF:[max(azShearEFDict[bin][EF])]}
                                except KeyError as K2:
                                    print('Key 4', str(K2), 'azshear', bin, EF)
                                    tiltDataEF[str(tilt)]['azshear'] = {bin:{EF:[max(azShearEFDict[bin][EF])]}}
                            
                for bin in list(posAzShearDict.keys()):
                    chosenIndex = posAzShearDict[bin].index(max(posAzShearDict[bin]))
                    
                    try:
                        tiltData[str(tilt)]['posazshear'][bin].append(posAzShearDict[bin][chosenIndex])
                        tiltDataRange[str(tilt)]['posazshear'][bin].append(posAzShearRangeDict[bin][chosenIndex])
                    except KeyError:
                        tiltData[str(tilt)]['posazshear'][bin] = [posAzShearDict[bin][chosenIndex]]
                        tiltDataRange[str(tilt)]['posazshear'][bin] = [posAzShearRangeDict[bin][chosenIndex]]
                
                for bin in list(posAzShearEFDict.keys()):
                    if isTOR:
                        for EF in list(posAzShearEFDict[bin].keys()):
                            try:
                                tiltDataEF[str(tilt)]['posazshear'][bin].setdefault(EF, []).append(max(posAzShearEFDict[bin][EF]))
                            except KeyError as K:
                                print('Key 3', str(K), tilt, 'posazshear', bin, EF)
                                try:
                                    tiltDataEF[str(tilt)]['posazshear'][bin] = {EF:[max(posAzShearEFDict[bin][EF])]}
                                except KeyError:
                                    tiltDataEF[str(tilt)]['posazshear'] = {bin:{EF:[max(azShearEFDict[bin][EF])]}}
                                    
                for bin in list(absAzShearDict.keys()):
                    chosenIndex = absAzShearDict[bin].index(max(absAzShearDict[bin]))
                    
                    try:
                        tiltData[str(tilt)]['absshear'][bin].append(absAzShearDict[bin][chosenIndex])
                        tiltDataRange[str(tilt)]['absshear'][bin].append(absAzShearRangeDict[bin][chosenIndex])
                    except KeyError:
                        tiltData[str(tilt)]['absshear'][bin] = [absAzShearDict[bin][chosenIndex]]
                        tiltDataRange[str(tilt)]['absshear'][bin] = [absAzShearRangeDict[bin][chosenIndex]]
                        
                
                for bin in list(absAzShearEFDict.keys()):
                    if isTOR:
                        for EF in list(absAzShearEFDict[bin].keys()):
                            try:
                                tiltDataEF[str(tilt)]['absshear'][bin].setdefault(EF, []).append(max(absAzShearEFDict[bin][EF]))
                            except KeyError as K:
                                print('Key 3', str(K), tilt, 'absazshear', bin, EF)
                                try:
                                    tiltDataEF[str(tilt)]['absshear'][bin] = {EF:[max(absAzShearEFDict[bin][EF])]}
                                except KeyError:
                                    tiltDataEF[str(tilt)]['absshear'] = {bin:{EF:[max(absAzShearEFDict[bin][EF])]}}
                
                for bin in list(vrotPosDict.keys()):
                    chosenIndex = vrotPosDict[bin].index(max(vrotPosDict[bin]))
                    try:
                        tiltData[str(tilt)]['posvrot'][bin].append(vrotPosDict[bin][chosenIndex])
                        tiltDataRange[str(tilt)]['posvrot'][bin].append(vrotPosRangeDict[bin][chosenIndex])
                    except KeyError:
                        tiltData[str(tilt)]['posvrot'][bin] = [vrotPosDict[bin][chosenIndex]]
                        tiltDataRange[str(tilt)]['posvrot'][bin] = [vrotPosRangeDict[bin][chosenIndex]]
                
                for bin in list(vrotEFDict.keys()):
                    if isTOR:
                        for EF in list(vrotEFDict[bin].keys()):
                            #print('Trying vrot', bin, EF) 
                            try:
                                tiltDataEF[str(tilt)]['vrot'][bin].setdefault(EF, []).append(max(vrotEFDict[bin][EF]))
                            except KeyError as K1:
                                print('Key 1', str(K1), tilt, 'vrot', bin, EF)
                                try:
                                    tiltDataEF[str(tilt)]['vrot'][bin] = {EF:[max(vrotEFDict[bin][EF])]}
                                except KeyError as K2:
                                    #print('Key2', str(K2))
                                    tiltDataEF[str(tilt)]['vrot'] = {bin:{EF:[max(vrotEFDict[bin][EF])]}}
                for bin in list(vrotPosEFDict.keys()):
                    if isTOR:
                        for EF in list(vrotPosEFDict[bin].keys()):
                            chosenIndex = vrotPosEFDict[bin][EF].index(max(vrotPosEFDict[bin][EF]))
                            
                            try:
                                tiltDataEF[str(tilt)]['posvrot'][bin].setdefault(EF, []).append(vrotPosEFDict[bin][EF][chosenIndex])
                                tiltDataRangeEF[str(tilt)]['posvrot'][bin].setdefault(EF, []).append(vrotPosRangeEFDict[bin][EF][chosenIndex])
                            except KeyError as K:
                                print('Key 3', str(K), tilt, 'posvrot', bin, EF, chosenIndex)
                                try:
                                    tiltDataEF[str(tilt)]['posvrot'][bin] = {EF:[vrotPosEFDict[bin][EF][chosenIndex]]}
                                    tiltDataRangeEF[str(tilt)]['posvrot'][bin] = {EF:[vrotPosRangeEFDict[bin][EF][chosenIndex]]}
                                except KeyError:
                                    tiltDataEF[str(tilt)]['posvrot'] = {bin:{EF:[vrotPosEFDict[bin][EF][chosenIndex]]}}
                                    tiltDataRangeEF[str(tilt)]['posvrot'] = {bin:{EF:[vrotPosRangeEFDict[bin][EF][chosenIndex]]}}
                
                for bin in list(topPosVrotRangeDict.keys()):
                    topVrotValues = [x[0] for x in topPosVrotRangeDict[bin]]
                    chosenIndex = topVrotValues.index(max(topVrotValues))
                    try:
                        tiltDataRange[str(tilt)]['90thvrot'][bin].append(topPosVrotRangeDict[bin][chosenIndex])
                    except KeyError:
                        tiltDataRange[str(tilt)]['90thvrot'][bin] = [topPosVrotRangeDict[bin][chosenIndex]]
                        
                for bin in list(topPosVrotRangeEFDict.keys()):
                    if isTOR:
                        for EF in list(topPosVrotRangeEFDict[bin].keys()):
                            topPosVrotValues = [x[0] for x in topPosVrotRangeEFDict[bin][EF]]
                            chosenIndex = topPosVrotValues.index(max(topPosVrotValues))
                            
                            try:
                                tiltDataRangeEF[str(tilt)]['90thvrot'][bin].setdefault(EF, []).append(topPosVrotRangeEFDict[bin][EF][chosenIndex])
                            except KeyError as K:
                                try:
                                    tiltDataRangeEF[str(tilt)]['90thvrot'][bin] = {EF:[topPosVrotRangeEFDict[bin][EF][chosenIndex]]}
                                except KeyError:
                                    tiltDataRangeEF[str(tilt)]['90thvrot'] = {bin:{EF:[topPosVrotRangeEFDict[bin][EF][chosenIndex]]}}
                                    
                for bin in list(top90AzShearDict.keys()):    
                    try:
                        tiltData[str(tilt)]['90thazshear'][bin].append(max(top90AzShearDict[bin]))
                    except KeyError:
                        tiltData[str(tilt)]['90thazshear'][bin] = [max(top90AzShearDict[bin])]
                
                for bin in list(bottom10AzShearDict.keys()):
                    try:
                        tiltData[str(tilt)]['10thazshear'][bin].append(max(bottom10AzShearDict[bin]))
                    except KeyError:
                        tiltData[str(tilt)]['10thazshear'][bin] = [max(bottom10AzShearDict[bin])]
                        
                for bin in list(vrotDict.keys()):
                    chosenIndex = vrotDict[bin].index(max(vrotDict[bin]))
                    
                    try:
                        tiltData[str(tilt)]['vrot'][bin].append(vrotDict[bin][chosenIndex])
                        tiltDataRange[str(tilt)]['vrot'][bin].append(vrotRangeDict[bin][chosenIndex])
                        
                    except KeyError:
                        tiltData[str(tilt)]['vrot'][bin] = [vrotDict[bin][chosenIndex]]
                        tiltDataRange[str(tilt)]['vrot'][bin] = [vrotRangeDict[bin][chosenIndex]]
                        
                for bin in list(spectrumWidthDict.keys()):
                    try:
                        tiltData[str(tilt)]['spectrumwidth'][bin].append(max(spectrumWidthDict[bin]))
                    except KeyError:
                        tiltData[str(tilt)]['spectrumwidth'][bin] = [max(spectrumWidthDict[bin])]
                for bin in list(minTDSDict.keys()):
                    try:
                        tiltData[str(tilt)]['mintdscc'][bin].append(min(minTDSDict[bin]))
                    except KeyError:
                        tiltData[str(tilt)]['mintdscc'][bin] = [min(minTDSDict[bin])]
                
                for bin in list(posSpectrumWidthDict.keys()):
                    try:
                        tiltData[str(tilt)]['posspectrumwidth'][bin].append(max(posSpectrumWidthDict[bin]))
                    except KeyError:
                        tiltData[str(tilt)]['posspectrumwidth'][bin] = [max(posSpectrumWidthDict[bin])]
                        
                for bin in list(posMinTDSDict.keys()):
                    try:
                        tiltData[str(tilt)]['posmintds'][bin].append(min(posMinTDSDict[bin]))
                    except KeyError:
                        tiltData[str(tilt)]['posmintds'][bin] = [min(posMinTDSDict[bin])]
                        
                # print(tilt, 'masterAzShear', tiltData[str(tilt)]['azshear'], '\nmaster90thazshear', tiltData[str(tilt)]['90thazshear'], '\n10thmasterazshear', tiltData[str(tilt)]['10thazshear'], '\nmastervrot', tiltData[str(tilt)]['vrot'], '\nmasterspectrumwidth', tiltData[str(tilt)]['spectrumwidth'], '\nmastermintdscc', tiltData[str(tilt)]['mintdscc'],\
                        # '\nmasterposshear', tiltData[str(tilt)]['posazshear'], '\nmasterabsshear', tiltData[str(tilt)]['absshear'],\
                        # '\nvrotposmaster', tiltData[str(tilt)]['posvrot'], '\nposspectrumwidthmaster', tiltData[str(tilt)]['posspectrumwidth'])
                # print(tilt, 'range data masterrangeazshear', tiltDataRange[str(tilt)]['azshear'], '\nmasterrangeposazshear', tiltDataRange[str(tilt)]['posazshear'], \
                    # '\nmasterrangeabsshear', tiltDataRange[str(tilt)]['absshear'], '\nmasterrangevrot', tiltDataRange[str(tilt)]['vrot'], '\nmasterrangeposvrot', tiltDataRange[str(tilt)]['posvrot'])
                # print('tiltDataEF', tiltDataEF)

                for trendTuple2 in list(azShearTrendDict.keys()):
                    try:
                        tiltTrendData[str(tilt)]['azshear'][trendTuple2].append(azShearTrendDict[trendTuple2])
                    except KeyError:
                        tiltTrendData[str(tilt)]['azshear'][trendTuple2] = [azShearTrendDict[trendTuple2]]
                        
                for trendTuple2 in list(absAzShearTrendDict.keys()):
                    try:
                        tiltTrendData[str(tilt)]['absshear'][trendTuple2].append(absAzShearTrendDict[trendTuple2])
                    except KeyError:
                        tiltTrendData[str(tilt)]['absshear'][trendTuple2] = [absAzShearTrendDict[trendTuple2]]
                for trendTuple2 in list(posAzShearTrendDict.keys()):
                    try:
                        tiltTrendData[str(tilt)]['posazshear'][trendTuple2].append(posAzShearTrendDict[trendTuple2])
                    except KeyError:
                        tiltTrendData[str(tilt)]['posazshear'][trendTuple2] = [posAzShearTrendDict[trendTuple2]]
                for trendTuple2 in list(vrotTrendDict.keys()):
                    try:
                        tiltTrendData[str(tilt)]['vrot'][trendTuple2].append(vrotTrendDict[trendTuple2])
                    except KeyError:
                        tiltTrendData[str(tilt)]['vrot'][trendTuple2] = [vrotTrendDict[trendTuple2]]
                for trendTuple2 in list(vrotPosTrendDict.keys()):
                    try:
                        tiltTrendData[str(tilt)]['posvrot'][trendTuple2].append(vrotPosTrendDict[trendTuple2])
                    except KeyError:
                        tiltTrendData[str(tilt)]['posvrot'][trendTuple2] = [vrotPosTrendDict[trendTuple2]]
                for trendTuple2 in list(spectrumWidthTrendDict.keys()):
                    try:
                        tiltTrendData[str(tilt)]['spectrumwidth'][trendTuple2].append(spectrumWidthTrendDict[trendTuple2])
                    except KeyError:
                        tiltTrendData[str(tilt)]['spectrumwidth'][trendTuple2] = [spectrumWidthTrendDict[trendTuple2]]
                for trendTuple2 in list(posSpectrumWidthTrendDict.keys()):
                    try:
                        tiltTrendData[str(tilt)]['posspectrumwidth'][trendTuple2].append(posSpectrumWidthTrendDict[trendTuple2])
                    except KeyError:
                        tiltTrendData[str(tilt)]['posspectrumwidth'][trendTuple2] = [posSpectrumWidthTrendDict[trendTuple2]]
                for trendTuple2 in list(bottom10AzShearTrendDict.keys()):
                    try:
                        tiltTrendData[str(tilt)]['10thazshsear'][trendTuple2].append(bottom10AzShearTrendDict[trendTuple2])
                    except KeyError:
                        tiltTrendData[str(tilt)]['10thazshear'][trendTuple2] = [bottom10AzShearTrendDict[trendTuple2]]
                for trendTuple2 in list(top90AzShearTrendDict.keys()):
                    try:
                        tiltTrendData[str(tilt)]['90thazshear'][trendTuple2].append(top90AzShearTrendDict[trendTuple2])
                    except KeyError:
                        tiltTrendData[str(tilt)]['90thazshear'][trendTuple2] = [top90AzShearTrendDict[trendTuple2]]
                           
                if isTOR:
                    for trendTuple2 in list(azShearEFTrendDict.keys()):
                        for efRating in list(azShearEFTrendDict[trendTuple2].keys()):
                            try:
                                tiltTrendDataEF[str(tilt)]['azshear'][trendTuple2].setdefault(efRating, []).append(azShearEFTrendDict[trendTuple2][efRating])
                            except KeyError as K:
                                try:
                                    print('Key 5', str(K), 'azshear', bin, EF)
                                    tiltTrendDataEF[str(tilt)]['azshear'][trendTuple2] = {efRating:[azShearEFTrendDict[trendTuple2][efRating]]}
                                except KeyError:
                                     tiltTrendDataEF[str(tilt)]['azshear'] = {trendTuple2:{efRating:[azShearEFTrendDict[trendTuple2][efRating]]}}
                                     
                    for trendTuple2 in list(absAzShearEFTrendDict.keys()):
                        for efRating in list(absAzShearEFTrendDict[trendTuple2].keys()):
                            try:
                                tiltTrendDataEF[str(tilt)]['absshear'][trendTuple2].setdefault(efRating, []).append(absAzShearEFTrendDict[trendTuple2][efRating])
                            except KeyError as K:
                                try:
                                    print('Key 5', str(K), 'absshear', bin, EF)
                                    tiltTrendDataEF[str(tilt)]['absshear'][trendTuple2] = {efRating:[absAzShearEFTrendDict[trendTuple2][efRating]]}
                                except KeyError:
                                    tiltTrendDataEF[str(tilt)]['absshear'] = {trendTuple2:{efRating:[absAzShearEFTrendDict[trendTuple2][efRating]]}}
                                    
                    for trendTuple2 in list(posAzShearEFTrendDict.keys()):
                        for efRating in list(posAzShearEFTrendDict[trendTuple2].keys()):
                            try:
                                tiltTrendDataEF[str(tilt)]['posazshear'][trendTuple2].setdefault(efRating, []).append(posAzShearEFTrendDict[trendTuple2][efRating])
                            except KeyError as K:
                                try:
                                    print('Key 5', str(K), 'posazshear', bin, EF)
                                    tiltTrendDataEF[str(tilt)]['posazshear'][trendTuple2] = {efRating:[posAzShearEFTrendDict[trendTuple2][efRating]]}
                                except KeyError:
                                    tiltTrendDataEF[str(tilt)]['posazshear'] = {trendTuple2:{efRating:[posAzShearEFTrendDict[trendTuple2][efRating]]}}
                                    
                    for trendTuple2 in list(vrotEFTrendDict.keys()):
                        for efRating in list(vrotEFTrendDict[trendTuple2].keys()):
                            try:
                                tiltTrendDataEF[str(tilt)]['vrot'][trendTuple2].setdefault(efRating, []).append(vrotEFTrendDict[trendTuple2][efRating])
                            except KeyError as K:
                                print('Key 5', str(K), 'vrot', bin, EF)
                                try:
                                    tiltTrendDataEF[str(tilt)]['vrot'][trendTuple2] = {efRating:[vrotEFTrendDict[trendTuple2][efRating]]}
                                except KeyError:
                                    tiltTrendDataEF[str(tilt)]['vrot'] = {trendTuple2:{efRating:[vrotEFTrendDict[trendTuple2][efRating]]}}
                                    
                    for trendTuple2 in list(vrotPosEFTrendDict.keys()):
                        for efRating in list(vrotPosEFTrendDict[trendTuple2].keys()):
                            try:
                                tiltTrendDataEF[str(tilt)]['posvrot'][trendTuple2].setdefault(efRating, []).append(vrotPosEFTrendDict[trendTuple2][efRating])
                            except KeyError as K:
                                print('Key 5', str(K), 'posvrot', bin, EF)
                                try:
                                    tiltTrendDataEF[str(tilt)]['posvrot'][trendTuple2] = {efRating:[vrotPosEFTrendDict[trendTuple2][efRating]]}
                                except KeyError:
                                    tiltTrendDataEF[str(tilt)]['posvrot'] = {trendTuple2:{efRating:[vrotPosEFTrendDict[trendTuple2][efRating]]}}
                        
                            
                    # print(tilt, 'masterAzShear Trend', tiltTrendData[str(tilt)]['azshear'], '\nmaster90thazshear Trend', tiltTrendData[str(tilt)]['90thazshear'], '\n10thazshear Trend', tiltTrendData[str(tilt)]['10thazshear'], \
                                # '\nmastervrot Trend', tiltTrendData[str(tilt)]['vrot'], '\nmasterspectrumwidth trend', tiltTrendData[str(tilt)]['spectrumwidth'],\
                                # '\nmasterposshear trend', tiltTrendData[str(tilt)]['posazshear'], '\nmasterabsshear Trend', tiltTrendData[str(tilt)]['absshear'],\
                                # '\nmastervrotpos trend', tiltTrendData[str(tilt)]['posvrot'], '\nposspectrumwidth trend', tiltTrendData[str(tilt)]['posspectrumwidth'])
                                
                    # print('tiltTrendDataEF', tiltTrendDataEF)
                    
                    # print('Master range data masterazshear', tiltDataRange[str(tilt)]['azshear'], '\nposazshear', tiltDataRange[str(tilt)]['posazshear'],\
                        # '\nabsshear', tiltDataRange[str(tilt)]['absshear'], '\nvrot', tiltDataRange[str(tilt)]['vrot'], '\nposvrot', tiltDataRange[str(tilt)]['posvrot'])
                    
                    # print('Missing Counts\nmissingCount', missingCount, '\nmissingCountEF', missingCountEF)
            
                    
    #print(tiltData)   
    #print(etTrendData)
    print('Total number of cases', totalCases)
    print('Total number of negative AzShear', totalNegAzShearLT)
    
    print('Skipped', skippedCount, 'for bin number or beam height issues')
    print('The negative AzShear cases were', negativeAzShearCases)
    
    # if isTOR and maxPotentialClusters:
        # print('This is a tor with max potential clusters', maxPotentialClusters, isTDS, 'and the azshear at ef0 bin 0 is', len(tiltDataEF['0.5']['azshear']['0']['0']))
    
    returnData = {\
    
    'Echo Tops':etData,\
    'Cyclonic Case Echo Tops':posETData,\
    'Echo Tops by VCP':etDataVCP,\
    'Cyclonic Case Echo Tops by VCP':posETDataVCP,\
    'Storm Data':trackData,\
    'Cyclonic Case Storm Data':posTrackData,\
    'Storm Data by VCP':trackDataVCP,\
    'Cyclonic Case Storm Data by VCP':posTrackDataVCP,\
    'Echo Top Trends':etTrendData,\
    'Echo Top Trends by VCP':etTrendDataVCP,\
    'Storm Data Trends':trackTrendData,\
    'Storm Data Trends by VCP':trackTrendDataVCP,\
    'Cyclonic Case Echo Top Trends':posETTrendData,\
    'Cyclonic Case Echo Top Trends by VCP':posETTrendDataVCP,\
    'Cyclonic Case Storm Data Trends':posTrackTrendData,\
    'Cyclonic Case Storm Data Trends by VCP':posTrackTrendDataVCP,\
    'AzShear Clusters by Tilt':tiltData,\
    'AzShear Clusters by Tilt and Range':tiltDataRange,\
    'AzShear Clusters by Tilt and Range and EF':tiltDataRangeEF,\
    'Missing Tilt Count':missingCount,\
    'Missing Tilt Count by EF Rating':missingCountEF,\
    'AzShear Cluster Trends by Tilt':tiltTrendData,\
    'AzShear Cluster by Tilt and EF':tiltDataEF,\
    'AzShear Cluster Trends by Tilt and EF':tiltTrendDataEF}
    
    return returnData, totalCases, totalNegAzShearLT, negativeAzShearCases
    
    
    
#Defining a dictionary to serve as an alias for what's above minums VCP and others not used. 
generalAliases = {'Echo Tops': 'ET',\
            'Cyclonic Case Echo Tops': 'POSET',\
            'Storm Data':'VIL',\
            'Cyclonic Case Storm Data':'POSVIL',\
            'Echo Top Trends':'ETTRENDS',\
            'Storm Data Trends':'VILTRENDS',\
            'Cyclonic Case Echo Top Trends':'POSETTRENDS',\
            'Cyclonic Case Storm Data Trends':'POSVILTRENDS',\
            'AzShear Clusters by Tilt':'AZSHEAR',\
            'AzShear Cluster Trends by Tilt':'AZSHEARTRENDS',\
            'AzShear Clusters by Tilt and Range':'AZSHEARRANGE'}
            