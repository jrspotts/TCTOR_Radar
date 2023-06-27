#Calculates and writes statistics and Mann-Whitney-U-Test for two datasets. Returns a dictionary of all of the statistics.

import math
import numpy as np
from scipy.stats import mannwhitneyu as mwu
from scipy.stats import wilcoxon as wcx
from scipy.stats import norm
import os
import math

def calculateGroupStats(group):
    """ Calculates the stats for a group for calculateStats """
    
    
    count = str(len(group))
    minimum = str(min(group))
    firstPercentile = str(np.percentile(group, 25))
    median = str(np.median(group))
    mean = str(np.mean(group))
    secondPrecentile = str(np.percentile(group, 75))
    maximum = str(max(group))
    
    return {'count':count, 'minimum':minimum, '25th-percentile':firstPercentile, 'median':median, 'mean':mean, '75th-percentile':secondPrecentile, 'maximum':maximum}
    
def writeDualStats(group1Stats, group2Stats, writeMode, writeFile):

    """ Write the stats from groups 1 and 2 to writeFile using writeMode. """
    fileExists = os.path.exists(writeFile)
    
    with open(writeFile, writeMode) as fi:
    
        if writeMode.lower() == 'w' or not fileExists:
            fi.write(','.join(['Group1', 'count', 'minimum', '25th-percentile', 'median', 'mean', '75th-percentile', 'maximum', \
                               'Group2', 'count', 'minimum', '25th-percentile', 'median', 'mean', '75th-percentile', 'maximum'])+'\n')  
        fi.write(','.join([group1Stats['name'], group1Stats['count'], group1Stats['minimum'], group1Stats['25th-percentile'], group1Stats['median'], group1Stats['mean'], group1Stats['75th-percentile'], group1Stats['maximum'],\
                           group2Stats['name'], group2Stats['count'], group2Stats['minimum'], group2Stats['25th-percentile'], group2Stats['median'], group2Stats['mean'], group2Stats['75th-percentile'], group2Stats['maximum']])+'\n')
                           
    return
    
def writeSingleStats(stats, groupName, writeMode, writeFile):

    """ Write stats writeFile """
    
    fileExists = os.path.exists(writeFile)
    
    with open(writeFile, writeMode) as fi:
    
        if writeMode.lower() == 'w' or not fileExists:
            fi.write(','.join(['Group', 'count', 'minimum', '25th-percentile', 'median', 'mean', '75th-percentile', 'maximum'])+'\n')
            
        
        fi.write(','.join(map(str, [groupName, stats['count'], stats['minimum'], stats['25th-percentile'], stats['median'], stats['mean'], stats['75th-percentile'], stats['maximum']]))+'\n')
    
    return
    
def calculateStats(group1, group2, group1Name='Group1', group2Name='Group2', writeMode=None, writeFile='stats.csv'):

    """ Calculates the count, minimum, 25th-percentile, median, mean, 75th-percentile, and maximum values for two groups.
        group1Name and group2Name are strings representing an identifier for groups 1 and 2 respectively.
        For writing these statistics to a file, writeMode can be 'w' (write), 'a' (append), or None (don't write; Default). They will be written to a CSV file
        with a name defined by writeFile (default stats.csv).
        
        Returns two dictionaries. Each dictionary contains the statistics of each group.
        
    """
    
    group1Stats = calculateGroupStats(group1)
    group2Stats = calculateGroupStats(group2)
    
    #Add an identifier for each group2 of statistics
    group1Stats['name'] = group1Name
    group2Stats['name'] = group2Name
    
    if writeMode is not None:
        if writeMode.lower() == 'a' or writeMode.lower() == 'w':
            writeDualStats(group1Stats, group2Stats, writeMode, os.path.join('stats', writeFile))
        else:
            if not isinstance(writeMode, str):
                raise TypeError(str(writeMode)+' is not a str')
            elif isinstance(writeMode, str):
                raise ValueError(str(writeMode)+' is not valid. Please use "a" or "w" for writeMode')
                
    print('Calculated', group1Name, 'stats', group1Stats)
    print('Calculated', group2Name, 'stats', group2Stats)
    
    return group1Stats, group2Stats
    
def writeMannWhitney(name1, name2, alternative, statistic, pvalue, writeMode, writeFile):

    didFileExist = os.path.exists(writeFile)
    with open(writeFile, writeMode) as fi:
        if writeMode.lower() == 'w' or not didFileExist:
            fi.write(','.join(['Group1', 'Group2', 'alternative', 'test_statistic', 'p_value'])+'\n')
            
        fi.write(','.join([str(name1), str(name2), str(alternative), str(statistic), str(pvalue)])+'\n')

    return
    
    
def doMannWhitneyU(group1, group2, group1Name='Group1', group2Name='Group2', use_continuity=True, alternative='two-sided', method='auto', nan_policy='propogate', keepdims=False, writeMode=None, writeFile='mannwhitstats.csv'):

    """ Performs the mann-whitney-U-test on groups 1 and 2. group1Name and group2Name are the optional names for the groups. For the remaining kwargs
    
        method: how to calculate the p-value. 'asymptotic' - standard with tie correction
                                              'exact'      - compares U statistics to calculate exact p-value. No tie correction.
                                              'auto'       - exact if sample size is less than 8, asypmtotic otherwise.
        nan_policy: how to handle Nans.       'propogate'  - if there are nans, output a nan
                                              'omit'       - don't use nans. Output nan if sample size is insufficient.
                                              'raise'      - Raise a ValueError if there's a nan
        keepdims:   Keep dimensions
        
        writeMode: 'w' for write, 'a' for append, None for do-not-write
        
        writeFile: The file name to write the statistics CSV to. 
        
        Returns the corresponding MannwhtneyuResult object holding the test statistic and p-value
        
        
    """
    
    if not group1 or not group2:
        print('Group missing from Mann-Whitney-U-Test. Returning None')
        return None
    
    result = mwu(group1, group2, use_continuity=use_continuity, alternative=alternative, method=method)
    
    print('Group1', group1, 'Group2', group2, 'stat', result.statistic, 'pvalue', result.pvalue)
    
    if writeMode is not None:
        if writeMode.lower() == 'a' or writeMode.lower() == 'w':
            writeMannWhitney(group1Name, group2Name, alternative, result.statistic, result.pvalue, writeMode, os.path.join('stats', writeFile))
        else:
            if not isinstance(writeMode, str):
                raise TypeError(str(writeMode)+' is not a str')
            elif isinstance(writeMode, str):
                raise ValueError(str(writeMode)+' is not valid. Please use "a" or "w" for writeMode')
            
            
    return result
    
def writeWilcoxon(dataName, alternative, statistic, pvalue, writeMode, writeFile):

    fileExists = os.path.exists(writeFile)
    with open(writeFile, writeMode) as fi:
        
        if writeMode.lower() == 'w' or not fileExists:
            fi.write('Name,alternative,statistic,p_value\n')
            
        fi.write(','.join(map(str, [dataName, alternative, statistic, pvalue]))+'\n')
    
    print('Wrote wilcoxon')
    
    return
    
    
def doWilcoxon(data, dataName='data', y=None, zero_method='wilcox', correction=False, alternative='two-sided', mode='auto', writeMode=None, writeFile='wilcoxon.csv'):

    """ Performs the Wilcoxon Signed Rank test and returns the result. """
    
    if not any(data) and (zero_method == 'wilcox' or zero_method == 'pratt'):
        print('Warning!!! Wilcoxon test is all zeros and zero_method is', zero_method, '. Skipping tests')
        return None
        
    result = wcx(data, y=None, zero_method=zero_method, correction=correction, alternative=alternative, mode=mode)
    
    print('Performed Wilcoxon test for', dataName, data, 'with statistic', result.statistic, 'and p-value', result.pvalue)
    
    
    if writeMode is not None:
    
        if writeMode.lower() == 'a' or writeMode.lower() == 'w':
            writeWilcoxon(dataName, alternative, result.statistic, result.pvalue, writeMode, os.path.join('stats', writeFile))
        else:
            if not isinstance(writeMode, str):
                raise TypeError(str(writeMode)+' is not a str')
            else:
                raise ValueError(str(writeMode)+' is not valid. Please use "a" or "w" for writeMode')
                
                
    return result
            
def writeZPropTest(s1, s2, n1, n2, p1, p2, Z, pValue, group1Name, group2Name, checkValue, alternative, writeMode, writeFile):

    fileExists = os.path.exists(writeFile)
    
    with open(writeFile, writeMode) as fi:
        
        if writeMode.lower() == 'w' or not fileExists:
            fi.write(','.join(['Group 1', 'success1', 'trials1', 'proportion1', 'alternative', 'check_value', 'Group 2', 'success2', 'trials2', 'proportion2', 'Z', 'p_value'])+'\n')
            
        fi.write(','.join(map(str, [group1Name, s1, n1, p1, alternative, checkValue, group2Name, s2, n2, p2, Z, pValue]))+'\n')
        
        
    return 
    
def writeZPropTestFail(check1, anticheck1, check2, anticheck2, check1Fail, check2Fail, group1Name, group2Name, alternative, checkValue, writeMode, writeFile):

    """ Called when one of the checks for the z proportion fails. Puts CF (for check failed) in Z and p_value. The success column has the check value.
        The trials column has the anticheck (variance) check value. The proportion column shows a boolean indicating of that group failed the check.
    """
    
    fileExists = os.path.exists(writeFile)
    
    with open(writeFile, writeMode) as fi:
    
        if writeMode.lower() == 'w' or not fileExists:
            fi.write(','.join(['Group 1', 'success1', 'trials1', 'proportion1', 'alternative', 'check_value', 'Group 2', 'success2', 'trials2', 'proportion2', 'Z', 'p_value'])+'\n')
    
        fi.write(','.join(map(str, [group1Name, check1, anticheck1, check1Fail, alternative, checkValue, group2Name, check2, anticheck2, check2Fail, 'CF', 'CF']))+'\n')
        
    return
            
def propZTest(s1, n1, s2, n2, group1Name='Group1', group2Name='Group2', checkValue=5, alternative='two-sided', writeMode=None, writeFile='ztest.csv'):
    
    """ Following methodology provided by https://stattrek.com/hypothesis-test/difference-in-proportions.
        Tests if s1/n1 == s2/n2.
        Uses a pooled standard error.
        
        s1 - the number of successes in a sample1
        s2 - the number of successes in sample2
        n1 - the number of samples in sample1
        n2 - the number of samples in sample2
        alternative - 'two-sided', 'greater' (s1>s2), 'less' (s1<s2). Default is two-sided if greater or less is not specified.
        group1Name - Name of group1
        group2Name - Name of group2
        writeMode - "w" for write, "a" for append
        writeFile - CSV to write to
        checkValue - what p*n and p*(1-n) must be greater than for a valid test. Failing this test writes to the stats file the test failed if writeMode is "a" or "w".
    """
    
    p1 = s1/n1
    p2 = s2/n2
    
    #Perform the check to ensure correct sample size. 5 used used per Dr. Katzfuss. 
    check1 = p1*n1
    antiCheck1 = (1-p1)*n1
    check2 = p2*n2
    antiCheck2 = (1-p2)*n2
    check1Failed = False
    check2Failed = False
    
    print('Preparing to check prop-Z-test with S1 N1', s1, n1, 'and S2 N2', s2, n2)
    
    if check1 <= checkValue or antiCheck1 <= checkValue:
        print('Z-test: Check on proportion 1 failed with np', check1, 'and p(1-n)', antiCheck1, 'with check value', checkValue)
        check1Failed = True
    
    if check2 <= checkValue or antiCheck2 <= checkValue:
        print('Z-test: Check on proportion 2 failed with np', check2, 'and p(1-n)', antiCheck2, 'with check value', checkValue)
        check2Failed = True
        
    if check1Failed or check2Failed:
        writeZPropTestFail(check1, antiCheck1, check2, antiCheck2, check1Failed, check2Failed, group1Name, group2Name, alternative, checkValue, writeMode, os.path.join('stats', writeFile))
        return None, None
        
    #p = ((p1*n1) + (p2*n2))/(n1+n2) Old weird way of doing it. See next line.
    p = (s1+s2)/(n1+n2)
    
    SE = math.sqrt(p*(1-p)*((1/n1)+(1/n2)))
    
    Z = (p1-p2)/SE
    
    #Calculate the p-value
    if alternative.lower() == 'greater':
        pValue = 1 - norm.cdf(Z)
    elif alternative.lower() == 'less':
        pValue = norm.cdf(Z)
    else:
        
        if Z >= 0:
            pValue = 2 * (1 - norm.cdf(Z))
        else:
            pValue = 2 * norm.cdf(Z)
            
            
    print('Calculated stat', Z, 'with p-value', pValue)
    
    if writeMode is not None:
        
        if writeMode.lower() == 'a' or writeMode.lower() == 'w':
            writeZPropTest(s1, s2, n1, n2, p1, p2, Z, pValue, group1Name, group2Name, checkValue, alternative, writeMode, os.path.join('stats', writeFile))
        else:
            if not isinstance(writeMode, str):
                raise TypeError(str(writeMode)+' is not a str')
            else:
                raise ValueError(str(writeMode)+' is not valid. Please use "a" or "w" for writeMode')
                
    return Z, pValue


def writeTSS(tssDicts, group1Name, group2Name, adjustRanges, adjustThresholds, writeMode, writeFile):

    
    fileExists = os.path.exists(writeFile)
    
    with open(writeFile, writeMode) as fi:
        if writeMode.lower() == 'w' or not fileExists:
            fi.write(','.join(['Group1', 'Group2', 'TSS', 'threshold', 'correct', 'wrong', 'far', 'pod', 'CSI', 'a', 'b', 'c', 'd', 'adjust_ranges', 'adjust_threshold'])+'\n')
        
        for tssDictTuple in tssDicts:
            tssDict = tssDictTuple[1]
            if tssDict is None:
                continue
                
            fi.write(','.join(map(str, [group1Name, group2Name, tssDict['TSS'], tssDict['threshold'], tssDict['correct'], tssDict['wrong'], tssDict['far'], tssDict['pod'],\
                                tssDict['CSI'], tssDict['a'], tssDict['b'], tssDict['c'], tssDict['d'], adjustRanges, adjustThresholds]))+'\n')
                            
    return
    
    
def calculateTSS(expectedLower, expectedHigher, threshold):

    """ Calculates the True Skill Score per Wilks (2019) Equation 9.18. pg. 380. 
        
        Returns a dictionary of the TSS and warning stats.
    """
    
    #Start by defining the components of the warning statistics
    correct = 0 #Number of correct forecasts (a+d)
    wrong = 0 #Number of incorrect forecasts (b+c)
    a = 0 #Hits. Number of expected highers greater than the threshold
    b = 0 #False alarms. Number of expectd lower greater than threshold
    c = 0 #Miss. Number of expected higher less than the threshold.
    d = 0 #Null. Number of expected lower less than the threshold.
    
    #Start by checking the expected lower cases. 
    for value in expectedLower:
        if isinstance(value, tuple):
            raise TypeError("Warning! "+str(value)+" must be an int or float for expectedLower")
            
        if value < threshold:
            d += 1
        else:
            b += 1
    #Now do the expected higher cases. 
    for value in expectedHigher:
        if isinstance(value, tuple):
            raise TypeError("Warning! "+str(value)+" must be an int or float for expectedHigher")
            
        if value < threshold:
            c += 1
        else:
            a += 1
            
    correct = a+d
    wrong = b+c
    try:
        far = b/(a+b)
        pod = a/(a+c)
        CSI = a/(a+b+c)
        TSS = ((a*d) - (b*c))/((a+c)*(b+d))
    except ZeroDivisionError:
        print('Zero Division a,b,c,d', a, b, c, d)
        return None
    
    return {'TSS':TSS, 'threshold':threshold, 'correct':correct, 'wrong':wrong, 'far':far, 'pod':pod, 'CSI':CSI, 'a':a, 'b':b, 'c':c, 'd':d}
    
def adjustThresholds(clusterRange, mainThreshold, adjustRanges, rangeAdjustValues):

    """ Adjusts the threshold based on range from the nearest radar.
        clusterRange - Range of the cluster from the nearest radar in nautical miles
        mainThreshold - The threshold before any adjustment
        adjustRanges - If cluster range is greater than this list of ranges, add the corresponding rangeAdjustValue 
    """
    
    newThreshold = mainThreshold
    
    if len(adjustRanges) != len(rangeAdjustValues):
        raise ValueError("Warning! The length of of adjustRanges ("+str(len(adjustRanges))+") must be equal to the length of rangeAdjustValues ("+str(len(rangeAdjustValues))+")")
        
    for i in range(len(adjustRanges)):
        
        if clusterRange >= adjustRanges[i]:
            newThreshold += rangeAdjustValues[i]
            
            
    if newThreshold != mainThreshold:
        print('Adjusted', mainThreshold, 'to', newThreshold, 'for range', clusterRange, 'n mi')
            
    return newThreshold
    
def calculateTSSRange(expectedLower, expectedHigher, mainThreshold, adjustRanges, rangeAdjustValues):

    #Start by defining the components of the warning statistics
    correct = 0 #Number of correct forecasts (a+d)
    wrong = 0 #Number of incorrect forecasts (b+c)
    a = 0 #Hits. Number of expected highers greater than the threshold
    b = 0 #False alarms. Number of expectd lower greater than threshold
    c = 0 #Miss. Number of expected higher less than the threshold.
    d = 0 #Null. Number of expected lower less than the threshold.
    
    #Start by checking the expected lower cases. 
    for value,clusterRange in expectedLower:
        threshold = adjustThresholds(clusterRange, mainThreshold, adjustRanges, rangeAdjustValues)
        
        if value < threshold:
            d += 1
        else:
            b += 1
    #Now do the expected higher cases. 
    for value,clusterRange in expectedHigher:
        threshold = adjustThresholds(clusterRange, mainThreshold, adjustRanges, rangeAdjustValues)
        
        if value < threshold:
            c += 1
        else:
            a += 1
            
    correct = a+d
    wrong = b+c
    try:
        far = b/(a+b)
        pod = a/(a+c)
        CSI = a/(a+b+c)
        TSS = ((a*d) - (b*c))/((a+c)*(b+d))
        
    except ZeroDivisionError:
        print('Zero Division a,b,c,d', a, b, c, d)
        return None
    
    return {'TSS':TSS, 'threshold':mainThreshold, 'correct':correct, 'wrong':wrong, 'far':far, 'pod':pod, 'CSI':CSI, 'a':a, 'b':b, 'c':c, 'd':d}
    
    
def calculateVrotTSS(expectedLower, expectedHigher, initialThreshold=5, maxThreshold=60, thresholdIncrement=1, adjustRanges=None, rangeAdjustValues=None, writeMode=None, writeFile='tss.csv', group1Name='Group1', group2Name='Group2'):

    """ Calculates the TSS for Vrot. 
    
        The TSS can be calculated in two ways. Direct TSS or range-adjusted TSS.
        
        In the direct TSS case:
        
        expectedLower - The Vrot values of cases where a correct forecast would be less than the threshold.
        expectedHigher - The Vrot values cases where a correct forecast would be greater than the threshold. 
        
        In the range-adjust TSS case:
        
        expectedLower and expectedHigher are lists of tuple where each tuple consists of the same Vrot as in the direct TSS 
        and the second element is range from the radar in nautical miles. 
        
        adjustRanges rangeAdjustValues is an interable or array-like of ranges by where each element of adjustRanges is the range by which to adjust the threshold by 
        the corresponding element of rangeAdjustValues.
        
        The application of rangeAdjustValues is cummulative. For example, if the threshold beyond 40 n mi. needs to be adjusted down by
        5 kts, and 10 kts by 80 n mi. adjustRanges=[40, 80] and rangeAdjustValues=[-5, -5]. Subtract 5 kts at 40 n mi and another 5 kts at 80 n mi for total of 10 kts at 80 n mi.
        
        Returns 
    """
    
    tssStats = []
    for threshold in range(initialThreshold, maxThreshold+thresholdIncrement, thresholdIncrement):
    
        if adjustRanges and rangeAdjustValues:
            print('Calculating TSS with range correction. Group1', group1Name, 'group2', group2Name)
            tssStatDict = calculateTSSRange(expectedLower, expectedHigher, threshold, adjustRanges, rangeAdjustValues)
        else:
            print('Calculating TSS without range correction. Group1', group1Name, 'group2', group2Name)
            tssStatDict = calculateTSS(expectedLower, expectedHigher, threshold)

        tssStats.append((threshold, tssStatDict))
        
        print('Threshold', threshold, 'stats', tssStatDict)
    
    if writeMode is not None:
        if writeMode.lower() == 'w' or writeMode.lower() == 'a':
            writeTSS(tssStats, group1Name, group2Name, adjustRanges, rangeAdjustValues, writeMode, os.path.join('stats', writeFile))
        else:
            if not isinstance(writeMode, str):
                raise TypeError(str(writeMode)+' is not a str')
            else:
                raise ValueError(str(writeMode)+' is not valid. Please use "a" or "w" for writeMode')
                    
        
        
    return tssStats

def getMaximumTSS(tssValues):

    bestValue = 0
    bestIndex = None
    
    for n, tss in enumerate(tssValues):
        if abs(tss) > abs(bestValue):
            bestValue = tss
            bestIndex = n
    
    print('Found best TSS', bestValue, 'at index', bestIndex)
    
    return bestValue, bestIndex
    
    
def calculateCIBound(data, percentile):

    """ Calculates the confidence for the given percentile."""
    
    #Use norm.ppf with correct mean and scale
    
    if percentile > 1 or percentile < 0:
        raise ValueError("percentile must be between 0 and 1")
        
    return norm.ppf(percentile, loc=np.mean(data), scale=np.std(data))

def checkBeamHeight(autos, tiltList, cfg, potentialClusters):

    """ Checks to ensure the case meets the beam-height requirement at zero-minutes. If zero-minutes is not available, then the smallest absolute value bin number is checked with a bias for the negative in the event of a tie.
        The number of potential clusters is also checked to be consistent.
        Returns the Auto object that met the criteria. Otherwise returns None
    """
    
    binAndHeights = []
    for auto in autos:
        currentTiltObject = auto.azShear[tiltList[0]]
        beamHeight = currentTiltObject.beamHeights['0']
        
        #If the bin number is 0, then just check the beam height
        if int(currentTiltObject.binNumber) == 0:
            if beamHeight <= cfg.maxAzShearHeight and beamHeight >= 0 and currentTiltObject.potentialClusters <= potentialClusters and currentTiltObject.potentialClusters >= 0:
                return auto
            else:
                print('A zero bin did not meet the criteria', beamHeight)
                return None
                
        else:
            binAndHeights.append((auto, int(currentTiltObject.binNumber), beamHeight <= cfg.maxAzShearHeight and beamHeight >= 0 and currentTiltObject.potentialClusters <= potentialClusters and currentTiltObject.potentialClusters >= 0))
            
    #Now check for the smallest absolue-value bin. If there's a tie, give it to the the negative one
    bestBinTuple = None
    bestBin = math.inf
    for autoTuple in binAndHeights:
        print('Checking', binAndHeights)
        if abs(autoTuple[1]) < abs(bestBin):
            bestBin = autoTuple[1]
            bestBinTuple = autoTuple
            
        elif abs(autoTuple[1]) == abs(bestBin) and autoTuple[1] < 0 and bestBin >= 0:
            print('Overwritting', bestBin, 'with', autoTuple[1])
            bestBin = autoTuple[1]
            bestBinTuple = autoTuple
            
    if bestBinTuple is not None:
        if bestBinTuple[2]:
            print('Bin', bestBinTuple[1], 'meets the criteira with', bestBinTuple[0].azShear[tiltList[0]].beamHeights['0'], 'ft and ', bestBinTuple[0].azShear[tiltList[0]].potentialClusters, 'potential clusters.')
            return bestBinTuple[0]
        else:
            print('Bin', bestBinTuple[1], 'did not meet the criteria with', bestBinTuple[0].azShear[tiltList[0]].beamHeights['0'], 'ft and ', bestBinTuple[0].azShear[tiltList[0]].potentialClusters, 'potential clusters.')
            return None
            
    else:
        print('There was no best bin tuple. Returning None.')
        return None
        
    print('Congratulations! You found a forbidden return')
    return None
        
        
def calculateRealStats(nonTor, tor, tiltList, cfg, potentialClusters=math.inf):

    """ Calculates the real statistics based on the number of nontorandic, and the number of 1 and 2 classes for tornadic cases.
    
        FAR = b/(a+b)
        POD = a/(a+c)
        CSI = a/(a+b+c)
        
        Where b is the number of NON TOR events,
        c is the number of class 2 TORs, and
        a is the number of class 1 TORs.
        
        returns a dictionary with the calculated metrics and a, b, and c
        
        For a fair comparison, only cases where the lowest elevation angle meets the beam-height requirement at the zero-bin are counted.
    """
    
    #Give everythign an intial value
    a = 0
    b = 0
    c = 0
    FAR = None
    POD = None
    CSI = None
    
    #Also have a set of metrics for NON TOR + EF0 and EF1+
    aEF = 0
    bEF = 0
    cEF = 0
    FARef = None
    PODef = None
    CSIef = None
    
    #Get the number of nontor cases
    for TC in list(nonTor.keys()):
    
        for case in list(nonTor[TC].keys()):
            
            receivedAuto = checkBeamHeight(nonTor[TC][case], tiltList, cfg, potentialClusters)
            if receivedAuto is not None:
                b += 1
                bEF += 1
            
    #Get the number of Hit/Miss
    for TC in list(tor.keys()):
    
        for case in list(tor[TC].keys()):
        
            receivedAuto = checkBeamHeight(tor[TC][case], tiltList, cfg, potentialClusters)
            meetsCriteria = receivedAuto is not None
            
            for auto in list(tor[TC][case]):
            
                #Assuming that the warning class is the same for each auto objects (which it should be),
                #add one to a or c based on.
                if int(auto.warningClass) == 1 and meetsCriteria:
                    a += 1
                    if int(auto.efRating) >= 1:
                        aEF += 1
                    else:
                        bEF += 1
                        
                elif int(auto.warningClass) == 2 and meetsCriteria:
                    c += 1
                    if int(auto.efRating) >= 1:
                        cEF += 1
                else:
                    if not meetsCriteria:
                        break
                    raise ValueError("The warning class for "+str(TC)+" "+str(case)+" should only be 1 or 2 not "+str(auto.warningClass))
                
                break
                
    realStats = {}
    realEFStats = {}
    try:
        FAR = b/(a+b)
        POD = a/(a+c)
        CSI = a/(a+b+c)
    except ZeroDivisionError:
        print('Zero Division in realstats a b c', a, b, c)
        realStats = None
    else:
        realStats = {'FAR':FAR, 'POD':POD, 'CSI':CSI, 'a':a, 'b':b, 'c':c}
        
    try:
        FARef = bEF/(aEF+bEF)
        PODef = aEF/(aEF+cEF)
        CSIef = aEF/(aEF+bEF+cEF)
    except ZeroDivisionError:
        print('Zero Division in realstatsef aEF bEF cEF', aEF, bEF, cEF)
        realEFStats = None
    else:
        realEFStats = {'FAR':FARef, 'POD':PODef, 'CSI':CSIef, 'a':aEF, 'b':bEF, 'c':cEF}
        
    print('Calculated real FAR', FAR, 'POD', POD, 'and CSI', CSI, 'with a b c', a, b, c)
    print('Calculated real EF FAR', FARef, 'POD', PODef, 'and CSI', CSIef, 'with a b c', aEF, bEF, cEF)
    
    return realStats, realEFStats
        
        
        
def checkAllEqualOr(value, *toCheck):
    
    """ Checks to see any of the toCheck values match value. Returns True if so, False if not.
    
        Argument:
        value: What to check
        toCheck: A variable number of arguments to check
        
        Returns:
        True if one of the toCheck values matches value, False if none of them match
        
    """
    
    results = []
    
    for checker in toCheck:
        results.append(value == checker)
        
    return any(results)
    