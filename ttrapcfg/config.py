 #Object that contains configuration information for TRAP

import xml.etree.ElementTree as ET
from datetime import timedelta as TD
from string import Template
import sys
import pytz
import time

class Config():
    caseFile = None
    storm = None
    trackCluster = None
    shearCluster = None
    minShearCluster = None
    topCluster = None
    baseDir = None
    caseDir = None
    saveDir = None
    radarDir = None
    dataDir = None
    simDir = None
    rapDir = None
    convertedRapDir = None
    nseDir = None
    radarLocDir = None
    clusterDir = None
    processedInput = None
    modules = None
    simQC = None
    simMerge = None
    notify = None
    latOffset = None
    lonoffset = None
    gridTime = None
    top = None
    vTop = None
    bottom = None
    hSpacing = None
    hvSpacing = None
    vSpacing = None
    vvSpacing = None
    sigma = None
    radarinfo = None
    timeBinIncrement = None
    radarStart = None
    radarEnd = None
    ETThresholds = None
    log = None
    refMethod = None
    velMethod = None
    numVelRadars = None
    overrideID = None
    mergerTimeout = None
    utc = pytz.UTC
    stormTable = None
    shearAltList = None
    ttrapOnly = False
    activeColor = None
    numOfAlts = None
    shedVar = None
    shed = None
    shedAlt = None
    makeFigures = None
    useRap = None
    rapCurrent = None
    rapHistorical = None
    rapOffset = None
    rapTemplate = None
    tiltList = None
    
    minShearScore = None
    minTrackScore = None
    minTopScore = None
    
    useMeanMotion = None
    
    maxShearDistInit = None
    maxShearDist = None
    maxShearDistTilt = None
    maxTrackDist = None
    maxTopDist = None
    
    shearDistWeight = None
    shearVectorWeight = None
    shearIntensityWeight = None
    shearVectorDistanceFactor = None
    
    trackDistWeight = None
    trackVectorWeight = None
    trackIntensityWeight = None
    
    topDistWeight = None
    topVectorWeight = None
    topIntensityWeight = None
    
    maxAppendTimeV = None
    maxAppendTimeR = None
    
    trackClusterMax = None
    trackClusterMin = None
    trackClusterIncrement = None
    trackClusterMaxDepth = None
    trackClusterLambda = None
    trackClusterScale0 = None
    trackClusterScale1 = None
    trackClusterScale2 = None
    trackClusterIsolate = None
    trackClusterCombine0 = None
    trackClusterCombine1 = None
    trackClusterCombine2 = None
    trackClusterTuple = None
    traclScalingString = None
    
    shearClusterMax = None
    shearClusterMin = None
    shearClusterIncrement = None
    shearClusterMaxDepth = None
    shearClusterLambda = None
    shearClusterScale0 = None
    shearClusterScale1 = None
    shearClusterScale2 = None
    shearClusterIsolate = None
    shearClusterCombine0 = None
    shearClusterCombine1 = None
    shearClusterCombine2 = None
    shearClusterTuple = None
    shearScalingString = None
    
    topClusterMax = None
    topClusterMin = None
    topClusterIncrement = None
    topClusterMaxDepth = None
    topClusterLambda = None
    topClusterScale0 = None
    topClusterScale1 = None
    topClusterScale2 = None
    topClusterIsolate = None
    topClusterCombine0 = None
    topClusterCombine1 = None
    topClusterCombine2 = None
    topClusterTuple = None
    topScalingString = None
    
    figurePrefix = ''
    combine = True
    createCache = None
    
    maxBearingDev = None
    useSails = None
    useCrop = None
    useNeighbor = None
    thresholdShear = None
    thresholdValue = None
    
    doIngest = None
    doQC = None
    doAzShearET = None
    doTDS = None
    makeGrids = None
    doCluster = None
    doBTRT = None
    doCSV = None
    
    projectReference = None
    projectFraction = None
    shearCressman = None
    logFile = None
    errorFile = None
    logName = None
    def __init__(self, configFile, logFileName, errorFileName, logName):
       
        #Clear the logfile
        self.logFile = logFileName
        self.errorFile = errorFileName
        self.logName = logName
        
        lfi = open(self.logFile, 'w')
        lfi.close()
        lif2 = open(self.errorFile, 'w')
        lif2.close()

        self.log("Logging Started. Loading Configuration.")

        self.updateConfig(configFile)
        
        return
    
    def log(self, message):
        
        # fi = open(self.logFile, 'a')
        # fi.write(str(time.asctime())+': '+str(message)+'\n')
        # fi.close()
        
        print(str(time.asctime())+': '+str(message))
        with open (self.logFile, 'a') as f:
            print(str(time.asctime())+': '+str(message), file=f)
        
        return
        
    def error(self, message):
        # fi = open(self.errorFile, 'a')
        # fi.write(str(time.asctime())+': '+str(message)+'\n')
        # fi.close()
        
        print(str(time.asctime())+': '+str(message))
        with open(self.errorFile, 'a') as f:
            print(str(time.asctime())+': '+str(message), file=f)
        
        return
        
    def updateConfig(self, configFile):
    
    
        tree = ET.parse(configFile)
        root = tree.getroot()

        currentElement = root.find('Input')
        self.caseFile = currentElement.find('CaseFile').text
        self.storm = currentElement.find('Storm').text
        self.trackCluster = currentElement.find('TrackCluster').text
        self.shearCluster = currentElement.find('ShearCluster').text
        self.minShearCluster = currentElement.find('MinShearCluster').text
        self.topCluster = currentElement.find('TopCluster').text
        currentElement = root.find('Directories')
        self.baseDir = currentElement.find('BaseDir').text

        currentElement = currentElement.find('Case')
        self.caseDir = currentElement.get('name')
        self.radarDir = currentElement.find('Radar').text
        self.dataDir = currentElement.find('Data').text
        self.simDir = currentElement.find('Simulator').text
        self.saveDir = currentElement.find('Save').text
        self.clusterDir = currentElement.find('Cluster').text
        self.rapDir = currentElement.find('RAP').text
        self.convertedRapDir = currentElement.find('RAPConv').text
        self.nseDir = currentElement.find('NSE').text

        currentElement = root.find('Directories')
        self.processedInput = currentElement.find('ProcessedCases').text
        self.modules = currentElement.find('Modules').text

        currentElement = root.find('Processing')
        self.simMerge = currentElement.find('SimFactorMerge').text
        self.notify = currentElement.find('NotifyChunks').text
        self.latOffset = currentElement.find('LatOffset').text
        self.lonOffset = currentElement.find('LonOffset').text
        self.gridTime = currentElement.find('GridTime').text
        self.refMethod = currentElement.find('ReflectivityMethod').text
        self.velMethod = currentElement.find('VelocityMethod').text
        self.stormTable = currentElement.find('StormTable').text.lower()
        if self.stormTable != 'viltable' and self.stormTable != 'reftable' and self.stormTable != 'clustertable':
            self.log.error(self.stormTable+' is not a valid option for StormTable. Please let to viltable, reftable, or clustertable in the config file.')
            exit(8)
        self.shedVar = currentElement.find('ShedVar').text
        self.shedAlt = currentElement.find('ShedAlt').text
        if self.shedVar.lower() == 'ref':
            self.shed = 'MergedReflectivityQC'
            self.shedAlt = ':'+self.shedAlt
        if self.shedVar.lower() == 'refcomp':
            self.shed = 'MergedReflectivityQCComposite'
            self.shedAlt = ':0'+str(self.bottom)+'0'
            
        self.doIngest = bool(int(currentElement.find('DoIngest').text))
        self.doQC = bool(int(currentElement.find('DoQC').text))
        self.doAzShearET = bool(int(currentElement.find('DoAzShearET').text))
        self.doTDS = bool(int(currentElement.find('DoTDS').text))
        self.makeGrids = bool(int(currentElement.find('MakeGrids').text))
        self.doCluster = bool(int(currentElement.find('DoCluster').text))
        self.doBTRT = bool(int(currentElement.find('DoBTRT').text))
        self.doCSV = bool(int(currentElement.find('DoCSV').text))
        self.sigma = currentElement.find('Sigma').text
        self.shearCressman = bool(int(currentElement.find('ShearCressman').text))
        
        currentElement = root.find('Domain')
        self.top = currentElement.find('Top').text
        self.vTop = currentElement.find('VTop').text
        self.bottom = currentElement.find('Bottom').text
        self.hSpacing = currentElement.find('HSpacing').text
        self.hvSpacing = currentElement.find('HVSpacing').text
        self.vSpacing = currentElement.find('VSpacing').text
        self.vvSpacing = currentElement.find('VVSpacing').text
        
        self.tiltList = []
        
        for x in currentElement.find('TiltList').text.split(' '):
            if len(x) == 3:
                self.tiltList.append('0'+x+'0')
            elif len(x) == 4:
                self.tiltList.append('0'+x)
            else:
                self.tiltList.append(x)
            
        currentElement = root.find('Misc')
        self.radarinfo = currentElement.find('Radarinfo').text
        self.timeBinIncrement = float(currentElement.find('TimeBinIncrement').text)
        self.radarStart = TD(minutes=float(currentElement.find('RadarStart').text))
        self.radarEnd = TD(minutes=float(currentElement.find('RadarEnd').text))
        self.ETThresholds = currentElement.find('EchoTop').text
        self.numRadars = int(currentElement.find('NumRadars').text)
        self.numVelRadars = int(currentElement.find('NumVelRadars').text)
        self.useRap = bool(int(currentElement.find('UseRap').text))
        self.rapCurrent = currentElement.find('RAPCurrentLink').text
        self.rapHistorical = currentElement.find('RAPHistoricalLink').text
        self.rapOffset = float(currentElement.find('RAPOffset').text)
        self.rapTemplate = Template(currentElement.find('RAPTemplate').text)
        self.maxBearingDev = float(currentElement.find('MaxBearingDeviation').text)

        self.createCache = bool(int(currentElement.find('CreateCache').text))
        self.useSails = bool(int(currentElement.find('UseSails').text))
        
        self.maxAppendTimeV = float(currentElement.find('MaxAppendTimeV').text)
        self.maxAppendTimeR = float(currentElement.find('MaxAppendTimeR').text)
        self.useCrop = bool(int(currentElement.find('UseCropConv').text))
        self.useNeighbor = bool(int(currentElement.find('NearestNeighbor').text))
        self.thresholdShear = bool(int(currentElement.find('ThresholdAzShear').text))
        self.thresholdValue = float(currentElement.find('ThresholdValue').text)
        
        self.minShearScore = float(currentElement.find('MinInterestShear').text)
        self.minTrackScore = float(currentElement.find('MinInterestTrack').text)
        self.minTopScore = float(currentElement.find('MinInterestTop').text)
        
        self.useMeanMotion = bool(int(currentElement.find('UseMeanMotion').text))
        
        self.maxShearDistInit = float(currentElement.find('MaxInterestDistShearInitial').text)
        self.maxShearDist = float(currentElement.find('MaxInterestDistShear').text)
        self.maxShearDistTilt = float(currentElement.find('MaxInterestDistShearTilt').text)
        self.maxTrackDist = float(currentElement.find('MaxInterestDistTrack').text)
        self.maxTopDist = float(currentElement.find('MaxInterestDistTop').text)
        
        self.projectReference = bool(int(currentElement.find('ProjectReference').text))
        self.projectFraction = float(currentElement.find('ProjectFraction').text)
        
        self.shearDistWeight = float(currentElement.find('ShearInterestDistWeight').text)
        self.shearVectorWeight = float(currentElement.find('ShearInterestVectorWeight').text)
        self.shearIntensityWeight = float(currentElement.find('ShearInterestIntensityWeight').text)
        self.shearVectorDistanceFactor = float(currentElement.find('ShearVectorDistFactor').text)
        
        self.trackDistWeight = float(currentElement.find('TrackInterestDistWeight').text)
        self.trackVectorWeight = float(currentElement.find('TrackInterestVectorWeight').text)
        self.trackIntensityWeight = float(currentElement.find('TrackInterestIntensityWeight').text)
        
        self.topDistWeight = float(currentElement.find('TopInterestDistWeight').text)
        self.topVectorWeight = float(currentElement.find('TopInterestVectorWeight').text)
        self.topIntensityWeight = float(currentElement.find('TopInterestIntensityWeight').text)
        
        self.trackClusterMax = int(currentElement.find('TrackClusterMax').text)
        self.trackClusterMin = int(currentElement.find('TrackClusterMin').text)
        self.trackClusterIncrement = int(currentElement.find('TrackIncrement').text)
        self.trackClusterMaxDepth = float(currentElement.find('TrackClusterMaxDepth').text)
        self.trackClusterLambda = float(currentElement.find('TrackClusterLambda').text)
        self.trackClusterScale0 = currentElement.find('TrackClusterScale0').text
        self.trackClusterScale1 = currentElement.find('TrackClusterScale1').text
        self.trackClusterScale2 = currentElement.find('TrackClusterScale2').text
        self.trackClusterIsolate = currentElement.find('TrackClusterIsolate').text
        self.trackClusterCombine0 = currentElement.find('TrackClusterCombine0').text
        self.trackClusterCombine1 = currentElement.find('TrackClusterCombine1').text
        self.trackClusterCombine2 = currentElement.find('TrackClusterCombine2').text
        self.trackClusterTuple = (self.trackClusterMin, self.trackClusterMax, self.trackClusterIncrement, self.trackClusterMaxDepth, self.trackClusterLambda)
        self.trackScalingString = self.trackClusterScale0+','+self.trackClusterScale1+','+self.trackClusterScale2+':'+self.trackClusterIsolate+':'+self.trackClusterCombine0+','+self.trackClusterCombine1+','+self.trackClusterCombine2
        
        self.shearClusterMax = int(currentElement.find('ShearClusterMax').text)
        self.shearClusterMin = int(currentElement.find('ShearClusterMin').text)
        self.shearClusterIncrement = int(currentElement.find('ShearIncrement').text)
        self.shearClusterMaxDepth = float(currentElement.find('ShearClusterMaxDepth').text)
        self.shearClusterLambda = float(currentElement.find('ShearClusterLambda').text)
        self.shearClusterScale0 = currentElement.find('ShearClusterScale0').text
        self.shearClusterScale1 = currentElement.find('ShearClusterScale1').text
        self.shearClusterScale2 = currentElement.find('ShearClusterScale2').text
        self.shearClusterIsolate = currentElement.find('ShearClusterIsolate').text
        self.shearClusterCombine0 = currentElement.find('ShearClusterCombine0').text
        self.shearClusterCombine1 = currentElement.find('ShearClusterCombine1').text
        self.shearClusterCombine2 = currentElement.find('ShearClusterCombine2').text
        self.shearClusterTuple = (self.shearClusterMin, self.shearClusterMax, self.shearClusterIncrement, self.shearClusterMaxDepth, self.shearClusterLambda)
        self.shearScalingString = self.shearClusterScale0+','+self.shearClusterScale1+','+self.shearClusterScale2+':'+self.shearClusterIsolate+':'+self.shearClusterCombine0+','+self.shearClusterCombine1+','+self.shearClusterCombine2
        
        self.minShearClusterMax = int(currentElement.find('MinShearClusterMax').text)
        self.minShearClusterMin = int(currentElement.find('MinShearClusterMin').text)
        self.minShearClusterIncrement = int(currentElement.find('MinShearIncrement').text)
        self.minShearClusterMaxDepth = float(currentElement.find('MinShearClusterMaxDepth').text)
        self.minShearClusterLambda = float(currentElement.find('MinShearClusterLambda').text)
        self.minShearClusterScale0 = currentElement.find('MinShearClusterScale0').text
        self.minShearClusterScale1 = currentElement.find('MinShearClusterScale1').text
        self.minShearClusterScale2 = currentElement.find('MinShearClusterScale2').text
        self.minShearClusterIsolate = currentElement.find('MinShearClusterIsolate').text
        self.minShearClusterCombine0 = currentElement.find('MinShearClusterCombine0').text
        self.minShearClusterCombine1 = currentElement.find('MinShearClusterCombine1').text
        self.minShearClusterCombine2 = currentElement.find('MinShearClusterCombine2').text
        self.minShearClusterTuple = (self.minShearClusterMin, self.minShearClusterMax, self.minShearClusterIncrement, self.minShearClusterMaxDepth, self.minShearClusterLambda)
        self.minShearScalingString = self.minShearClusterScale0+','+self.minShearClusterScale1+','+self.minShearClusterScale2+':'+self.minShearClusterIsolate+':'+self.minShearClusterCombine0+','+self.minShearClusterCombine1+','+self.minShearClusterCombine2
        
        self.topClusterMax = int(currentElement.find('TopClusterMax').text)
        self.topClusterMin = int(currentElement.find('TopClusterMin').text)
        self.topClusterIncrement = int(currentElement.find('TopIncrement').text)
        self.topClusterMaxDepth = float(currentElement.find('TopClusterMaxDepth').text)
        self.topClusterLambda = float(currentElement.find('TopClusterLambda').text)
        self.topClusterScale0 = currentElement.find('TopClusterScale0').text
        self.topClusterScale1 = currentElement.find('TopClusterScale1').text
        self.topClusterScale2 = currentElement.find('TopClusterScale2').text
        self.topClusterIsolate = currentElement.find('TopClusterIsolate').text
        self.topClusterCombine0 = currentElement.find('TopClusterCombine0').text
        self.topClusterCombine1 = currentElement.find('TopClusterCombine1').text
        self.topClusterCombine2 = currentElement.find('TopClusterCombine2').text
        self.topClusterTuple = (self.topClusterMin, self.topClusterMax, self.topClusterIncrement, self.topClusterMaxDepth, self.topClusterLambda)
        self.topScalingString = self.topClusterScale0+','+self.topClusterScale1+','+self.topClusterScale2+':'+self.topClusterIsolate+':'+self.topClusterCombine0+','+self.topClusterCombine1+','+self.topClusterCombine2
        
        
        self.numOfAlts = int((float(self.vTop)-float(self.bottom))/(float(self.vSpacing)))
        
        self.shearAltList = ['0'+'{:.2f}'.format(a) for a in [float(self.vSpacing)+(b*float(self.vSpacing)) for b in range(self.numOfAlts)]]
        
        self.activeColor = [0.5, 0.5, 0.5]
        
        self.makeFigures = True
        
        return
        
        
        
        
    def setOverrideID(self, ID):
        self.overrideID = ID
        return
        
    def setCaseFile(self, filename):
        self.caseFile = filename
        return
        
    def setTTRAP(self, value):
        self.ttrapOnly = value
        return