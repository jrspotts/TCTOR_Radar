#This module contains the functions and classes for loading data for ttrappy and calibration data. 
#Justin Spotts 6-17-2022

from datetime import datetime
import pytz
import os
import math
import copy
    
class Truth:

    def __init__(self, headerList, dataList):
    
        """ Constructs a Truth instance with the data from dataList using headerList as a reference.
            
            Attributes:
                TC (str): The tropical cyclone this instance is asociated with
                ID (str): The case ID for this instance
                istor (bool): Whether or not this instance is associated with a TCTOR
                istds (bool): Whehter or not this instance is associated with a TDS
                DT (datetime): The datetime of the instance
                Vrot (dict of floats): The dictionary of rotational velocities where the key is the tilt. NA or N/A is changed to None
                ET (float): The 20 dBZ echo top for the instance.
        """
        
        
        self.TC = str(dataList[headerList.index('TC')])
        self.case = str(dataList[headerList.index('case')])
        self.istor = bool(int(dataList[headerList.index('istor')]))
        self.istds = bool(int(dataList[headerList.index('istds')]))
        dtString = dataList[headerList.index('DT')]
        if len(dtString.split('/')) > 3:
            pass
        elif len(dtString.split('/')) == 3:
            self.DT = pytz.UTC.localize(datetime.strptime(dtString, '%m/%d/%Y %H%MZ'))
        else:
            print('Something weird happening with the datetime for', self.TC, self.case, '\nNow exiting!')
            exit(0)
            
        self.vrots = {}
        
        #Try and except a series of value errors. If a ValueError was raised, then in all likelihood, the value was NA or N/A. In these cases, set the Vrot value to None
        try:
            self.vrots['0.5'] = float(dataList[headerList.index('0.5')])
        except ValueError:
            self.vrots['0.5'] = None
        try:
            self.vrots['0.9'] = float(dataList[headerList.index('0.9')])
        except ValueError:
            self.vrots['0.9'] = None
        try:
            self.vrots['1.3/1.45'] = float(dataList[headerList.index('1.3/1.45')])
        except ValueError:
            self.vrots['1.3/1.45'] = None
        try:
            self.vrots['1.8'] = float(dataList[headerList.index('1.8')])
        except ValueError:
            self.vrots['1.8'] = None
        try:
            self.vrots['2.4'] = float(dataList[headerList.index('2.4')])
        except ValueError:
            self.vrots['2.4'] = None
            
        self.ET = None
        try:
            self.ET = float(dataList[headerList.index('ET')])
        except ValueError:
            self.ET = None
            
        return
        
        
        
class Tilt:
    
    """ This class holds the data from individual tilts """
    
    def __init__(self, headerList, dataList, tilt, radii):
    
        self.tilt = tilt
        
        modTilt = tilt
        if float(tilt) < 1:
            modTilt = '(0'+modTilt+'deg)'
        else:
            modTilt = '('+modTilt+'deg)'
            
        self.dateTime = dataList[headerList.index('DateTime'+modTilt)]
        self.minuteBin = dataList[headerList.index('Bin(minutes)'+modTilt)]
        self.binNumber = dataList[headerList.index('BinNumber'+modTilt)]
        self.timeDelta = float(dataList[headerList.index('Timedelta(Seconds)'+modTilt)])
        self.latitude = float(dataList[headerList.index('Latitude(Degrees)'+modTilt)])
        self.longitude = float(dataList[headerList.index('Longitude(Degrees)'+modTilt)])
        self.latRadius = float(dataList[headerList.index('LatRadius(km)'+modTilt)])
        self.lonRadius = float(dataList[headerList.index('LonRadius(km)'+modTilt)])
        self.orientation = float(dataList[headerList.index('Orientation(degrees)'+modTilt)])
        self.size = float(dataList[headerList.index('Size(km2)'+modTilt)])
        if modTilt == '(00.5deg)':
            try:
                self.numReports = int(float(dataList[headerList.index('NumReports'+modTilt)]))
            except ValueError:
                self.numReports = None
            try:
                self.distCell = float(dataList[headerList.index('DistToCell(kilometers)'+modTilt)])
            except ValueError:
                self.distToCell = None
                
        self.maxShear = float(dataList[headerList.index('maxShear(s^-1)'+modTilt)])
        self.minShear = float(dataList[headerList.index('minShear(s^-1)'+modTilt)])
        self.bottom10Shear = float(dataList[headerList.index('10thShear(s^-1)'+modTilt)])
        self.top90Shear = float(dataList[headerList.index('90thShear(s^-1)'+modTilt)])
        self.minZdrTDS = float(dataList[headerList.index('minZdrTDS(dB)'+modTilt)])
        self.minRhoHV = float(dataList[headerList.index('minRhoHV'+modTilt)])
        self.areaVrot = float(dataList[headerList.index('AreaVrot(kts)'+modTilt)])
        self.maxRefTDS = float(dataList[headerList.index('maxRefTDS(dBZ)'+modTilt)])
        self.maxSpectrumWidth = float(dataList[headerList.index('maxSpectrumWidth(m/s)'+modTilt)]) * 1.94384 #Convert to knots
        self.uShear = float(dataList[headerList.index('uShear(m/s)'+modTilt)])
        self.vShear = float(dataList[headerList.index('vShear(m/s)'+modTilt)])
        self.clusterU = float(dataList[headerList.index('clusterU(m/s)'+modTilt)])
        self.clusterV = float(dataList[headerList.index('clusterV(m/s)'+modTilt)])
        self.TDScount = int(float(dataList[headerList.index('TDScount'+modTilt)]))
        self.TDSmin = float(dataList[headerList.index('TDSmin'+modTilt)])
        self.forwardLat = float(dataList[headerList.index('forwardLat(deg)'+modTilt)])
        self.forwardLon = float(dataList[headerList.index('forwardLon(deg)'+modTilt)])
        self.backwardLat = float(dataList[headerList.index('backLat(deg)'+modTilt)])
        self.backwardLon = float(dataList[headerList.index('backLon(deg)'+modTilt)])
        self.potentialClusters = int(float(dataList[headerList.index('potentialClusters(unitless)'+modTilt)]))
        
        self.groundRanges = {}
        self.bearings = {}
        self.beamHeights = {}
        
        if self.maxShear >= 0:
            self.isMax = True
        elif self.maxShear <= -99900:
            self.isMax = None
        else:
            self.isMax = False
        
        for head in headerList:
            if 'GroundRange' in head and modTilt in head:
                self.groundRanges[str(len(self.groundRanges))] = float(dataList[headerList.index(head)])
            if 'Radar Bearing' in head and modTilt in head:
                self.bearings[str(len(self.bearings))] = float(dataList[headerList.index(head)])
            if 'BeamHeight' in head and modTilt in head:
                self.beamHeights[str(len(self.beamHeights))] = float(dataList[headerList.index(head)])
        
        self.tiltBin = None
        self.rangeBin = None
        
        self.topVrot = None
        self.botVrot = None
        
        if self.maxShear > -99900 and (self.minShear < 1000000 and self.minShear > -99900):
            if abs(self.maxShear) >= abs(self.minShear):
                self.absShear = abs(float(self.maxShear))
            else:
                self.absShear = abs(float(self.minShear))
        else:
            self.absShear = None

        #Create Vrot estimation based on the 10th and 90th percentiles
        self.calculateOtherVrots()
        
        self.rVrots = {}
        
        self.calculateRVrots(radii)
        
        return
        
        
    def setTiltBin(self, value):
        self.tiltBin = value
        return
    def setRangeBin(self, value):
        self.rangeBin = value
        return
    def calculateOtherVrots(self):
        
        if float(self.size) > 0:
            r = math.sqrt(self.size/math.pi)*1000
            
            if float(self.top90Shear) > -99900 and float(self.bottom10Shear) < 10000:
                self.topVrot = (abs(self.top90Shear) * r) * 1.94384 #Convert from meters/second to knots
                self.botVrot = (abs(self.bottom10Shear) * r) * 1.94384 #Convert from meters/second to knots
        
        return
        
    def calculateRVrots(self, radii):
        """ Calculate the Vrot values using each radius in radii (please give radii in meters) """
        
        if abs(self.maxShear) >= abs(self.minShear):
            shear = abs(float(self.maxShear))
        else:
            shear = abs(float(self.minShear))
        
        if not isinstance(radii, list):
            radii = [radii]    
            
        for radius in radii:
            if shear < 99900:
                self.rVrots[radius] = (shear * radius) * 1.94384 #Convert from meters/second to knots
            else:
                self.rVrots[radius] = None
            
        return
        
class Auto:
        
    def __init__(self, headerList, dataList, tiltList, radii):
    
        """ This class holds the valuse from the ttrappy analysis """
         
        self.TC = dataList[headerList.index('TC')] 
        self.case = dataList[headerList.index('case')]
        self.efRating = dataList[headerList.index('F-EF-rating')]
        self.warningClass = dataList[headerList.index('class')]
        self.istor = bool(int(dataList[headerList.index('tor')]))
        
        self.vcpNumbers = {}
        self.vcpDurations = {}
        self.trackGroundRanges = {}
        self.etGroundRanges = {}
        
        #For the VCP information we'll need to check for all the VCP info.
        for head in headerList:
        
            if 'VCP' in head:
                if 'duration' in head:
                    self.vcpDurations[head[head.index('('):len(head)]] = dataList[headerList.index(head)]
                else:
                    self.vcpNumbers[head[head.index('('):len(head)]] = dataList[headerList.index(head)]
                    
            if 'GroundRange' in head and '(Track)' in head:
                self.trackGroundRanges[head[head.index(' ')+1]] = float(dataList[headerList.index(head)])
            if 'GroundRange' in head and '(ET)' in head:
                self.etGroundRanges[head[head.index(' ')+1]] = float(dataList[headerList.index(head)])
                
                           
        #Now we get the information from the individual AzShear clusters.
        self.azShear = {}
        for tilt in tiltList:
            self.azShear[tilt] = Tilt(headerList, dataList, tilt, radii)
            
        self.trackDT = dataList[headerList.index('DateTime(Track)')]
        self.trackBin = dataList[headerList.index('Bin(minutes)(Track)')]
        self.trackBinNumber = dataList[headerList.index('BinNumber(Track)')]
        self.trackTimeDelta = float(dataList[headerList.index('Timedelta(Seconds)(Track)')])
        self.trackLatitude = float(dataList[headerList.index('Latitude(Degrees)(Track)')])
        self.trackLongitude = float(dataList[headerList.index('Longitude(Degrees)(Track)')])
        self.trackLatRadius = float(dataList[headerList.index('LatRadius(km)(Track)')])
        self.trackLonRadius = float(dataList[headerList.index('LonRadius(km)(Track)')])
        self.trackOrientation = float(dataList[headerList.index('Orientation(degrees)(Track)')])
        self.size = float(dataList[headerList.index('Size(km2)(Track)')])
        self.trackAvgVIL = float(dataList[headerList.index('avgVIL(kg/m^2)')])
        self.trackMaxVIL = float(dataList[headerList.index('maxVIL(kg/m^2)')])
        self.trackMaxREF = float(dataList[headerList.index('maxREF(dBZ)')])
        self.trackU6kmMeanWind = float(dataList[headerList.index('u6kmMeanWind(m/s)')])
        self.trackV6kmMeanWind = float(dataList[headerList.index('v6kmMeanWind(m/s)')])
        self.trackUShear = float(dataList[headerList.index('uShear(m/s)')])
        self.trackVShear = float(dataList[headerList.index('vShear(m/s)')])
        trackPotentialClusterIndex = headerList.index('potentialClusters(unitless)')
        self.trackPotentialClusters = int(float(dataList[trackPotentialClusterIndex]))
        
        #There's a mistake with the potential clusters in that the track and ET potential clusters
        #aren't labeled. Therefore, we use the first one as the track and find the next one as the 
        #echo-top one
        
        self.etDT = dataList[headerList.index('DateTime(ET)')]
        self.etBin = dataList[headerList.index('Bin(minutes)(ET)')]
        self.etBinNumber = dataList[headerList.index('BinNumber(ET)')]
        self.etTimeDelta = float(dataList[headerList.index('Timedelta(Seconds)(ET)')])
        self.etLatitude = float(dataList[headerList.index('Latitude(Degrees)(ET)')])
        self.etLongitude = float(dataList[headerList.index('Longitude(Degrees)(ET)')])
        self.etLatRadius = float(dataList[headerList.index('LatRadius(km)(ET)')])
        self.etLonRadius = float(dataList[headerList.index('LonRadius(km)(ET)')])
        self.etOrientation = float(dataList[headerList.index('Orientation(degrees)(ET)')])
        self.etSize = float(dataList[headerList.index('Size(km2)(ET)')])
        self.maxETkm = float(dataList[headerList.index('maxET(km)')])
        self.top90ETkm = float(dataList[headerList.index('90thET(km)')])
        self.maxETft = float(dataList[headerList.index('maxET(ft)')])
        self.top90ETft = float(dataList[headerList.index('90thET(ft)')])
        self.etPotentialClusters = int(float(dataList[headerList.index('potentialClusters(unitless)', trackPotentialClusterIndex+1, len(headerList))]))
        
        
        return
        
        
class Skip:

    def __init__(self, skipHeader, skipLine):
    
        """
            This class holds information regarding which tilts or echo tops should not be included in the comparison.
        """
        
        self.TC = skipLine[skipHeader.index('TC')]
        self.case = skipLine[skipHeader.index('case')]
        
        self.azShearSkips = {}
        
        self.tilts = ['0.5', '0.9', '1.3/1.45', '1.8', '2.4']
        
        for tilt in self.tilts:
            try:
                self.azShearSkips[tilt] = bool(int(skipLine[skipHeader.index(tilt)]))
            except ValueError:
                self.azShearSkips[tilt] = None
                
        self.etSkip = bool(int(skipLine[skipHeader.index('ET')]))
        
        return
        
class NoSkip:

    def __init__(self, tc, case):
        
        """ 
            This is a replica of the Skip class, except all of the skips are set to False.
        """
        self.TC = tc
        self.case = case
        
        self.azShearSkips = {}
        
        tilts = ['0.5', '0.9', '1.3/1.45', '1.8', '2.4']
        
        for tilt in tilts:
            self.azShearSkips[tilt] = False
            
        self.etSkip = False
        
        
        return
        
        
        
class Diff:

    def __init__(self, truthObject, autoObject, skipObject, radii):
    
        """ 
            Holds the difference in Vrot between the automatic and manual analysis. Also holds the 
            range and tilt bin associated with this particular case.
            
        """
        
        if truthObject.case == autoObject.case and truthObject.TC == autoObject.TC:
            self.case = autoObject.case
            self.TC = autoObject.TC
        else:
            print('Mismatch in difference object between', truthObject.case, 'and', autoObject.case)
            return None
        
        #It says azShear, but it's really vrot
        self.rangeBins = {}
        self.tiltBins = {}
        self.azShearDiffs = {}
        self.azShearPairs = {}
        self.sizePairs = {}
        self.azShearTopDiffs = {}
        self.azShearTopPairs = {}
        self.azShearBotDiffs = {}
        self.azShearBotPairs = {}
        self.azShearTopSizePairs = {}
        self.azShearBotSizePairs = {}
        self.azShearPotentialClusters = {}
        self.azShearDistPairs = {}
        self.azShearDistErrorPairs= {}
        self.isMax = {}
        self.etDiff = None
        self.etPair = None
        self.etPotentialClusters = None
        self.et90Diff = None
        self.et90Pair = None
        
        #Individual radii versions
        self.vrotRDiffs = {}
        self.vrotRPairs = {}
        self.bestRadius = {}
        self.bestRadiusVrotPair = {}
        self.vrotRDistPairs = {}
        self.vrotRDistErrorPairs = {}
        
        for azTilt in list(autoObject.azShear.values()):
           
            currentTilt = azTilt.tilt
            truthTilt = currentTilt
            if currentTilt == '1.3' or currentTilt == '1.45':
                truthTilt = '1.3/1.45'
                
            self.isMax[currentTilt] = azTilt.isMax
            
            #Because if the tilt ends up being 1.3 or 1.45, change to 1.3/1.45 because they are combined.
            if not skipObject.azShearSkips[truthTilt]:
                
                #Make sure the data isn't missing
                if float(azTilt.areaVrot) > -99900 and truthObject.vrots[truthTilt]:
                    self.azShearDiffs[currentTilt] = float(azTilt.areaVrot) - float(truthObject.vrots[truthTilt])
                    self.rangeBins[currentTilt] = azTilt.rangeBin
                    self.tiltBins[currentTilt] = azTilt.tiltBin
                    self.azShearPairs[currentTilt] = (truthObject.vrots[truthTilt], azTilt.areaVrot)
                    self.sizePairs[currentTilt] = (azTilt.size, self.azShearDiffs[currentTilt])
                    self.azShearPotentialClusters[currentTilt] = int(azTilt.potentialClusters)
                    
                    
                    if float(azTilt.topVrot) > -99900 and float(azTilt.botVrot) > -99900:
                        self.azShearTopDiffs[currentTilt] = float(azTilt.topVrot) - float(truthObject.vrots[truthTilt])
                        self.azShearBotDiffs[currentTilt] = float(azTilt.botVrot) - float(truthObject.vrots[truthTilt])
                        self.azShearTopPairs[currentTilt] = (truthObject.vrots[truthTilt], float(azTilt.topVrot))
                        self.azShearBotPairs[currentTilt] = (truthObject.vrots[truthTilt], float(azTilt.botVrot))
                        self.azShearTopSizePairs[currentTilt] = (azTilt.size, self.azShearTopDiffs[currentTilt])
                        self.azShearBotSizePairs[currentTilt] = (azTilt.size, self.azShearBotDiffs[currentTilt])
                        
                    else:
                        self.azShearTopDiffs[currentTilt] = None
                        self.azShearBotDiffs[currentTilt] = None
                        self.azShearTopPairs[currentTilt] = (None, None)
                        self.azShearBotPairs[currentTilt] = (None, None)
                        self.azShearTopSizePairs[currentTilt] = (None, None)
                        self.azShearBotSizePairs[currentTilt] = (None, None)
                    
                else:
                    self.azShearDiffs[currentTilt] = None
                    self.rangeBins[currentTilt] = None
                    self.tiltBins[currentTilt] = None
                    self.azShearPairs[currentTilt] = (None, None)
                    self.sizePairs[currentTilt] = (None, None)
                    self.azShearPotentialClusters[currentTilt] = None
                    
                    
            else:
                self.azShearDiffs[currentTilt] = None
                self.rangeBins[currentTilt] = None
                self.tiltBins[currentTilt] = None
                self.azShearPairs[currentTilt] = (None, None)
                self.sizePairs[currentTilt] = (None, None)
                self.azShearTopDiffs[currentTilt] = None
                self.azShearBotDiffs[currentTilt] = None
                self.azShearTopPairs[currentTilt] = (None, None)
                self.azShearBotPairs[currentTilt] = (None, None)
                self.azShearTopSizePairs[currentTilt] = (None, None)
                self.azShearBotSizePairs[currentTilt] = (None, None)
                self.azShearPotentialClusters[currentTilt] = None
                
                
                
            self.vrotRDiffs[currentTilt] = {}
            self.vrotRPairs[currentTilt] = {}
            self.vrotRDistPairs[currentTilt] = {}
            self.vrotRDistErrorPairs[currentTilt] = {}
            
            self.bestRadius[currentTilt] = None
            self.bestRadiusVrotPair[currentTilt] = None
            
            smallestDifference = 99999999
            
            if not skipObject.azShearSkips[truthTilt]:
                #Now do the vrots calculated at various radii
                for radius in radii:
                    try:
                        #print('Trying ',azTilt.rVrots[radius],'and',truthObject.vrots[currentTilt], currentTilt, radius)
                        if azTilt.rVrots[radius] and truthObject.vrots[truthTilt]:
                        
                            difference = float(azTilt.rVrots[radius]) - float(truthObject.vrots[truthTilt])
                            self.vrotRDiffs[currentTilt][radius] = difference
                            self.vrotRPairs[currentTilt][radius] = (float(truthObject.vrots[truthTilt]), float(azTilt.rVrots[radius]))
                            self.vrotRDistPairs[currentTilt][radius] = (azTilt.groundRanges['0'], azTilt.rVrots[radius])
                            self.vrotRDistErrorPairs[currentTilt][radius] = (azTilt.groundRanges['0'], difference)
                            
                            if abs(difference) < smallestDifference:
                                smallestDifference = abs(difference)
                                self.bestRadius[currentTilt] = radius
                                self.bestRadiusVrotPair[currentTilt] = (self.bestRadius[currentTilt], float(azTilt.rVrots[radius]))
                            
                            
                    except KeyError as e:
                        print('Potentially missing something', str(e), currentTilt, radius)
                        continue
                    
                

        if float(autoObject.maxETft) > -99900 and truthObject.ET and not skipObject.etSkip:
            self.etDiff = float(autoObject.maxETft) - float(truthObject.ET)
            self.etPair = (float(autoObject.maxETft), float(truthObject.ET))
            self.etPotentialClusters = int(autoObject.etPotentialClusters)
            
        if float(autoObject.top90ETft) > -99000 and truthObject.ET and not skipObject.etSkip:
            self.et90Diff = float(autoObject.top90ETft) - float(truthObject.ET)
            self.et90Pair = (float(truthObject.ET), float(autoObject.top90ETft))
            
        return
        
        
        
def createDiffObjects(truthObjects, binnedAutoObjects, skipObjects, radii):

    """ 
        Creates difference objects between the truth and filtered automaticically-derived objects assuming that they are not flagged to be skipped 
    """
    
    #The keys so far for the truth and auto objects should be [TC][case] with the skipObjects being [TC-case].
    #Therefore, we shall loop through the filtered objects and send the matching truth and skip objects to the difference
    #object to make a difference object.
    
    differenceObjects = {}
    
    for TC in list(binnedAutoObjects.keys()):
        
        differenceObjects[TC] = {}
        for case in list(binnedAutoObjects[TC].keys()):
            differenceObjectList = []
            
            for auto in binnedAutoObjects[TC][case]:
            
                currentSkip = None
                try:
                    currentSkip = skipObjects[TC+'-'+case]
                except KeyError:
                    print('There was no skip object for', TC, case, '\b. Using a NoSkip instead')
                    currentSkip = NoSkip(TC, case)
                    
                #try:
                newDifference = Diff(truthObjects[TC][case], auto, currentSkip, radii)
                # except KeyError as err:
                    # print(TC, case, 'was likely not found for the truth object. Skipping and moving to the next case.', str(err))
                    # continue
                    
                differenceObjectList.append(newDifference)
                print('Created new difference', vars(newDifference))
                
            differenceObjects[TC][case] = differenceObjectList
            
    return differenceObjects
    
    
    
def filterAutoObjects(autoObjects, target=0, absolute=True, targetTilt=0.5):

    """ Filters the auto objects for each case that has the 0.5 deg timedelta the closest to the target.
        If absolute is True, then the absolute value of the timedelta is used.
        The target tilt is the elevation angle to compare the timedelta to the target.
        Regarless of the value of absolute, the difference is abs(target - timedelta).
        Absolute only determins if abs(timedelta) is used instead of just timedelta
    """
    
    newAutoObjects = {}
    #Start at the TC level
    for TC in list(autoObjects.keys()):
        newAutoObjects[TC] = {}
        
        #Then loop through each case
        for case in list(autoObjects[TC].keys()):
            
            closestDifference = 999999999
            closestAuto = None
            n = 1
            closestN = None
            for auto in autoObjects[TC][case]:
                if absolute:
                    currentDifference = abs(target - abs(auto.azShear[str(targetTilt)].timeDelta))
                else:
                    currentDifference = abs(target - auto.azShear[str(targetTilt)].timeDelta)
                    
                if currentDifference < closestDifference:
                    closestDifference = currentDifference
                    closestAuto = auto
                    closestN = n
                    
                n += 1
                    
            print('Found closest auto', closestAuto,' for TC', TC, 'case', case, 'at', closestDifference, 'n=', n)    
            newAutoObjects[TC][case] = closestAuto
            
    return newAutoObjects
    
def getByTC(caseList):

    """ Returns a nested dictionary of all of the objects by TC """
    
    objectsByTC = {}
    
    for case in caseList:
        if case.TC not in list(objectsByTC.keys()):
            caseObjects = {}
            caseObjects[case.case] = case
            objectsByTC[case.TC] = caseObjects
        else:
            objectsByTC[case.TC][case.case] = case
        
    return objectsByTC

def getManualData(manualFile):
    
    print('Loading manual values')
    
    isHeader = True
    header = ''
    truthObjects = []
    
    with open(manualFile, 'r') as fi:
        for line in fi:
            if not isHeader:
                truthObjects.append(Truth(header, line.rstrip('\n').split(',')))
                print('Added ', str(vars(truthObjects[-1])))
            else:
                header = line.lstrip('#').rstrip('\n').split(',')
                isHeader = False
                
    print('Done!')
    
    return truthObjects

def getAutoData(stormFolder, tiltList, radii):

    print('Loading Auto values')
    #First, we'll start by going the storms folder and listing TCs
    tcNames = os.listdir(stormFolder)
    
    autoObjects = {}
    
    #Then we'll go through each TC and list all of the cases
    for TC in tcNames:
        autoObjects[TC] = {}
        
        currentCasesPath = os.path.join(stormFolder, TC, 'cases')
        caseNames = os.listdir(currentCasesPath)
        
        casesAutoObjects = {}
         
        #Now go through each case and get the _prelim.csv file
        for case in caseNames:

            prelimCSV = os.path.join(currentCasesPath, case, 'results', case+'_prelim.csv')
            casesAutoObjects[case] = []
            header = ''
            isHeader = True
            try:
                with open(prelimCSV, 'r') as fi:
                    n = 0
                    for line in fi:
                        if not isHeader:
                            casesAutoObjects[case].append(Auto(header, line.rstrip('\n').split(','), tiltList, radii))
                            print('Added Auto', TC, case, n)
                        else:
                            header = line.lstrip('#').rstrip('\n').split(',')
                            isHeader = False
                        n += 1    
                        
            except FileNotFoundError as err:
                print(err, 'and continuing!')
                
        autoObjects[TC] = casesAutoObjects
        
    print('Done!')
    
    return autoObjects

def getSkipObjects(skipFile):

    skipObjects = {}
    
    print('Making skip objects')

    header = ''
    isHeader = True
    skipCount = {}
    with open(skipFile, 'r') as fi:
    
        for line in fi:
            if not isHeader:
                currentSkip = Skip(header, line.rstrip('\n').split(','))
                skipObjects[currentSkip.TC+'-'+currentSkip.case] = currentSkip
                print('Added Skip', vars(currentSkip))
                for tilt in currentSkip.tilts:
                    try:
                        if currentSkip.azShearSkips[tilt]:
                            skipCount[tilt] += 1
                    except KeyError:
                        skipCount[tilt] = 1
                        
                try:
                    if currentSkip.etSkip:
                        skipCount['et'] += 1
                except KeyError:
                    skipCount['et'] = 1
            else:
                header = line.lstrip('#').rstrip('\n').split(',')
                isHeader = False
                
                
    return skipObjects, skipCount
            
def assignTiltRangeBins(autoObjects, rangeBoundaries, tiltBoundaries):

    binnedAutoObjects = {}
    rangeBins = {}
    tiltBins = {}
    
    print('Assigning range and tilt bins')
    for tc in list(autoObjects.keys()):
    
        binnedAutoObjects[tc] = {}
        
        for case in list(autoObjects[tc].keys()):
        
            newAutos = []
            if not isinstance(autoObjects[tc][case], list):
                autoObjects[tc][case] = [autoObjects[tc][case]]
                
            for auto in autoObjects[tc][case]:
                if auto:
                    
                    autoCopy = copy.deepcopy(auto)
                    for azTilt in list(auto.azShear.values()):
                        azTiltKey = list(auto.azShear.keys())[list(auto.azShear.values()).index(azTilt)]
                        
                        #Make sure we have an azTilt
                        if azTilt:
                            #Convert the range from the closest radar to km
                            currentRange = azTilt.groundRanges['0'] * 1.852
                            if currentRange < 0:
                                print('Likely missing range detected for tilt', azTilt.tilt, '\b .Continuing')
                                continue 
                            currentTilt = float(azTilt.tilt)
                            
                            #For each boundary set, we need to check if boundaries were set to begin with
                            if rangeBoundaries:
                                for r in range(len(rangeBoundaries)):
                                    
                                    if r == 0:
                                        if currentRange < rangeBoundaries[r]:
                                            azTilt.setRangeBin(r)
                                            rangeBins['r < '+str(round(rangeBoundaries[r], 2))+' km'] = r
                                            print('1Set', autoCopy.case, azTilt.tilt, 'at range', currentRange, 'km to bin', r)
                                            break
                                        elif len(rangeBoundaries) == 1 and currentRange >= rangeBoundaries[r]:
                                            azTilt.setRangeBin(r+1)
                                            print('2Set', autoCopy.case, azTilt.tilt, 'at range', currentRange, 'km to bin', r+1)
                                            rangeBins['r >= '+str(round(rangeBoundaries[r], 2))+' km'] = r+1
                                            break
                                    elif currentRange >= rangeBoundaries[r-1] and currentRange < rangeBoundaries[r]:
                                        azTilt.setRangeBin(r)
                                        print('3Set', autoCopy.case, azTilt.tilt, 'at range', currentRange, 'km to bin', r)
                                        rangeBins[str(round(rangeBoundaries[r-1], 2))+' km >= r < '+str(round(rangeBoundaries[r], 2))+' km'] = r
                                        break
                                    elif r == (len(rangeBoundaries)-1):
                                        if currentRange > rangeBoundaries[r]:
                                            azTilt.setRangeBin(r+1)
                                            print('4Set', autoCopy.case, azTilt.tilt, 'at range', currentRange, 'km to bin', r+1)
                                            rangeBins['r > '+str(round(rangeBoundaries[r], 2))+' km'] = r+1
                                            break
                                    else:
                                        print('Something weird happening with the range bins')
                            else:
                                azTilt.setRangeBin(None)
                                print('Set', azTilt.tilt, 'range bin to None')
                                    
                            #Now repeat for the tilt boundaires
                            if tiltBoundaries:    
                                for t in range(len(tiltBoundaries)):
                                    
                                    if t == 0:
                                        if currentTilt < tiltBoundaries[t]:
                                            azTilt.setTiltBin(t)
                                            print('1Set', autoCopy.case, azTilt.tilt, 'to tilt bin', t)
                                            tiltBins['Tilt < '+str(round(tiltBoundaries[t], 2))+' deg'] = t
                                            break
                                        elif len(tiltBoundaries) == 1 and currentTilt >= tiltBoundaries[t]:
                                            azTilt.setTiltBin(t+1)
                                            print('2Set', autoCopy.case, azTilt.tilt, 'to tilt bin', t+1)
                                            tiltBins['Tilt >= '+str(round(tiltBoundaries[t], 2))+' deg'] = t+1
                                            break
                                    elif currentTilt >= tiltBoundaires[t-1] and currentTilt < tiltBoundaries[t]:
                                        azTilt.setTiltBin(t)
                                        print('3Set', autoCopy.case, azTilt.tilt, 'to tilt bin', t)
                                        tiltBins[str(round(tiltBoundaires[t-1], 2))+' deg >= tilt < '+str(round(tiltBoundaries[t], 2))+' deg'] = t
                                        break
                                    elif t == (len(tiltBoundaires)-1):
                                        if currentTilt >= tiltBoundaries[t]:
                                            azTilt.setTiltBin(t+1)
                                            print('4Set', autoCopy.case, azTilt.tilt, 'to tilt bin', t+1)
                                            tiltBins['Tilt > '+str(round(tiltBoundaries[t], 2))+' deg'] = t+1
                                            break
                                    else:
                                        print('Something weird happening with the tilt bins.')
                            else:
                                azTilt.setTiltBin(None)
                                print('Set', azTilt.tilt, 'tilt bin to None')
                                
                            autoCopy.azShear[azTiltKey] = azTilt
                                
                        else:
                            pass
                            
                            
                    newAutos.append(autoCopy)
                else:
                    print('For some reason', tc, case, 'had an auto with NoneType. Not adding to new autos.')
                    
            binnedAutoObjects[tc][case] = newAutos
        
                
    return binnedAutoObjects, tiltBins, rangeBins
    
    
def getData(manualFile, stormFolder, tiltList, radii):

    """ Retrieves the data from the manual and automated analysis and returns the corresponding Truth and Auto objects
        tiltList is the list of elevation angles to check. Radii are the list of radii to estimate vrot form
        
    """
    

    truthObjectsByTC = getByTC(getManualData(manualFile))
    autoObjectsByTC = getAutoData(stormFolder, tiltList, radii)
    

    return autoObjectsByTC, truthObjectsByTC