#Justin Spotts
#WDSII Module Containing Relevant WDSII programs as functions

from ttrappy import error as err
import subprocess
import time
import os
import shlex
import sys
import multiprocessing as mp
import traceback
import types
from datetime import datetime as dt
from datetime import timedelta as td

def log(message):

    fi = open('wdssi_ttraplog.txt', 'a')
    fi.write(str(time.asctime())+': '+str(message)+'\n')
    fi.close()
    print(str(time.asctime())+': '+str(message))
    
    return
    
def ldm2netcdf(cfg, inputDir, outputDir, site, pattern, logDir, once=False, readOld=False, xml=False, xmlFile="ldm2netcdfConfig.xml", nosails=False, logLevel='info', products='all'):

    """ Converts L2 Data to a WDSII format. Returns subprocess object. 
        inputDir = Directory containing the L2 files to be processed
        outputDir = Directory to place the processed data
        site = the 4 letter identifier of the radar site
        pattern = the file name pattern to be used as input
        once (boolean) = execute once? (not in real time) 
        xml = write this configuration to an xml file
        xmlFile = the name of the xml file
        logLevel = how much stuff to print (severe, unanticipated, harmless, important, info, debug)
    """
    
    cfg.log("Running ldm2netcdf")

    argument = "-i "+str(inputDir)+" -o "+str(outputDir)+" -s "+str(site)+" --verbose "+str(logLevel)+" -p "+str(pattern)+' --outputProducts="'+str(products)+'"'

    if once:
        argument = argument+" -1"
    if readOld:
        argument = argument+" -a"
    if nosails:
        argument += ' -e'
    if xml:
        argument = argument+" -xml=ttrapcfg/functions/"+xmlFile

    cfg.log("ldm2netcdf "+argument)
    

    outFile = str(time.time())+'_ldm2netcdf.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('ldm2netcdf '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')
    

    return proc, f

def makeindex(cfg, directory, logDir, start=None, end=None):

    """ Runs w2makeindex.py to catologue records into .xml format. Returns the subprocess object. 
        directory = directory to make an index from  """

    cfg.log("Running makeindex")

    argument = str(directory)+" -xml=index.xml -v"
    
    if start:
        argument += ' -s='+start
    if end:
        argument += ' -e='+end

    cfg.log("w2makeindex.py "+argument)

    outFile = str(time.time())+'_makeindex.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('w2makeindex.py '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')
    
    return proc, f


def w2qcnndp(cfg, inputDir, outputDir, site, logDir, envTable=None, realtime=False, xml=False, xmlFile="w2qcndpConfig.xml", logLevel='info', products='all'):

    """ Runs w2qcnndp as neural network quality control. Returns the subprocess object. 
        inputDir = index file for the input data
        outputDir = directory to place QCed data
        site = the radar site to use 
        xml = write this configuration to an xml file?
        xmlFile = the name of the xml file
        logLevel = how much stuff to print (severe, unanticipated, harmless, important, info, debug)
    """

    cfg.log("Running w2qcnndp")

    argument = "-i "+str(inputDir)+" -o "+str(outputDir)+" -s "+str(site)+" --verbose "+str(logLevel)+" --outputProducts="+str(products)
    
    if envTable:
        argument += ' -T '+str(envTable)
    if realtime:
        argument = argument + ' -r'
    if xml:
        argument = argument + " -xml=ttrapcfg/functions/"+xmlFile

    cfg.log("w2qcnndp "+argument)

    outFile = str(time.time())+'_w2qcnndp.txt'
    
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('w2qcnndp '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')
    

    return proc, f

def w2echotop(cfg, inputDir, outputDir, logDir, inputName="Reflectivity", thresholds='18 30 50', resolution=(0.5, 250, 230), realtime=False, products='all'):

    """ Runs w2echotop to calculate echo tops. Returns the subprocess object. 

        inputDir = index file for the input data
        ouputDir = directory to place the echo tops
        thresholds = tuple of echo top dBz thresholds
        resolution = 3 element tuple containing the azimuthal and range resolutions (degrees and meters respectively) and the maximum range in km
        realtime = run in realtime?
        xml = write this configuration to an xml file
        logLevel = how much stuff to print (severe, unanticipated, harmless, important, info, debug)
    """

    cfg.log("Running w2echotop")

    argument = "-i "+str(inputDir)+" -o "+str(outputDir)+' -I "'+str(inputName)+'" -R "'+str(resolution[0])+"x"+str(resolution[1])+"x"+str(resolution[2])+\
           '" -T '+'"'+str(thresholds)+'" --logSize=2000000 --outputProducts="'+str(products)+'"'
    if realtime:
        argument = argument+' -r'

    cfg.log("w2echotop "+argument)

    outFile = str(time.time())+'_w2echotop.txt'
    
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('w2echotop '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')
    

    return proc, f

def w2simulator(case, cfg, inputDir, outputDir, logDir, endOfDataset=False, simFactor=1, prune=False, notify=1000):

    """ Runs w2simulator. Returns the subprocess object. 
        inputDir = index file for the input data
        outputDir = directory to place simulation results
        endOfDataset = whether to notify algorithms of the end of dataset
        simFactor = ratio to speed up processing of data
        prune = prune the dataset to valid time
        notify = the number of millisecond chunks in which to notify algorithms
    """

    cfg.log("Running w2simulator")

    #Create Start and End Strings for simulation period
     
    start = (case.dateTime-cfg.radarStart)-td(minutes=1)
    start = start.replace(second=0, microsecond=0, minute=0, hour=start.hour)-td(seconds=1)
    end = case.dateTime+cfg.radarEnd+td(minutes=5)#Extra time to allow other algs to finish before issuing End_Of-Dataset signal

    mString = ''
    dString = ''
    hString = ''
    minString = ''
    if start.month < 10:
        mString = '0'
    if start.day < 10:
        dString = '0'
    if start.hour < 10:
        hString = '0'
    if start.minute < 10:
        minString = '0'
        
    startString = str(start.year)+mString+str(start.month)+dString+str(start.day)+'-'+hString+str(start.hour)+minString+str(start.minute)+'00'
    
    mString = ''
    dString = ''
    hString = ''
    minString = ''
    if end.month < 10:
        mString = '0'
    if end.day < 10:
        dString = '0'
    if end.hour < 10:
        hString = '0'
    if end.minute < 10:
        minString = '0'
        
    endString = str(end.year)+mString+str(end.month)+dString+str(end.day)+'-'+hString+str(end.hour)+minString+str(end.minute)+'59'
    
    argument = "-i "+str(inputDir)+" -o "+str(outputDir)+" -r "+str(simFactor)+' -b '+startString+' -e '+endString+' -C '+str(notify)+' --logSize=20000000'
    
    if endOfDataset:
        argument += " -E"
    if prune:
        argument += ' -c'

    cfg.log("w2simulator "+argument)

    outFile = str(time.time())+'_w2simulator.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('w2simulator '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')
    
    return proc, f

def w2merger(cfg, inputDir, outputDir, logDir, algorithms="", noVolume=False, method=7, realtime=False, upperLeft=(37, -100, 20), bottomRight=(30.5, -93, 1), resolution=(0.05, 0.05, 1), inputName="Reflectivity", singleGrid=False, outputTiming=(), refURL=None, refType=None, motionUrl=None, wind=None, zero=False, blendTime=None, sigma=None, xml=False, xmlFile="w2mergerConfig.xml", logLevel='info', products=''):

    """ Runs w2merger. Returns the subprocess object.
        inputDir = index file for the input data
        outputDir = directory to place simulation results
        algorithms = specifies algoritms to run (see w2merger help)
        noVolume = whether to only create prodcuts and not the 3D volume of data
        method = combination method (see w2merger help)
        upperLeft = tuple (lattiude, longitude, and altitude in km) of the upper left corner and top of the domain
        bottomLeft = tuple (lattiude, longitude, and altitude in km) of the bottom right corner and bottom of the domain
        resolution = tuple (zonal, meridional, vertical resolution) in (degrees, degree, km) respectively
        inputName = name of the data being used as input
        outputTiming = tuple (seconds between mergers, merger, out of merger) eg. (60, 1, 4) every 60 seconds 1 out of 4 mergers
        xml = write this configuration to an xml file?
        xmlFile = the name of the xml file
        logLevel = how much stuff to print (severe, unanticipated, harmless, important, info, debug)
    """

    cfg.log("Running w2merger")

    argument = '-i '+str(inputDir)+' -o '+str(outputDir)+' -C '+str(method)+" -t "+'"'+" ".join(map(str, upperLeft))+'"'+" -b "+\
           '"'+" ".join(map(str, bottomRight))+'"'+" -s "+'"'+" ".join(map(str, resolution))+'"'+" -I "+'"'+str(inputName)+'"'+" -e "+":".join(map(str, outputTiming))+" --verbose "+str(logLevel)
    if algorithms:
        argument += ' -a "'+str(algorithms)+'"'
    if refURL:
        argument += ' -Z "'+str(refURL)+'"'
    if refType:
        argument += ' -z "'+str(refType)+'"'
    if motionUrl:
        argument += ' -M "'+str(motionUrl)+'"'
    if singleGrid:
        argument = argument+" -3"
    if noVolume:
        argument = argument+" -V"
    if wind:
        argument += ' -w '+str(wind)
    if blendTime:
        argument += ' -T '+str(blendTime)
    if sigma:
        argument += ' -S "'+str(sigma)+'"'
    if zero:
        argument += ' -0'
    if realtime:
        argument = argument+" -r"
    if xml:
        argument = argument + " -xml=ttrapcfg/functions/"+xmlFile
        
    if products:
        argument += ' --outputProducts="'+str(products)+'"'

    cfg.log("w2merger "+argument)
    
    outFile = str(time.time())+'_w2merger.txt'

    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('w2merger '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')
    
    return proc, f

def dealiasVel(cfg, inputDir, outputDir, site, logDir, realtime=False, soundingTable='SoundingTable', xml=False, xmlFile="dealiasVelConfig.xml"):

    """ Runs dealiasVel. Returns the subprocess object. 
        inputDir = index file for the input data
        outputDir = directory to place dealiased velocity
        site = the radar site
        xml = write this configuration to an xml file?
        xmlFile = name of the xml file
        logLevel = how much stuff to print (severe, unanticipated, harmless, important, info, debug)
    """

    cfg.log("Running dealiasVel")

    argument = "-i "+str(inputDir)+" -o "+str(outputDir)+" -R "+str(site)#+' -S '+str(soundingTable)

    if realtime:
        argument = argument + ' -r'
    if xml:
        argument = argument+" -xml=config/"+xmlFile

    cfg.log("dealiasVel "+argument)

    outFile = str(time.time())+'_dealiasVel.txt'
    
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('dealiasVel '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')
    
    return proc, f

def w2circ(cfg, inputDir, outputDir, logDir, azimuth=True, divergence=False, total=False, dilate=False, startRange=0, azKernel=(2500, 750), divKernel=(750, 1500), variable='Velocity', refType='Reflectivity', writeStamped=False, writeMedian=False, refThreshold=None, refTime=None, noSpike=False, realtime=False, cressman=False, xml=False, xmlFile="w2circConfig.xml", logLevel='info'):

    """ Runs w2circ. Returns the subprocess object.
        inputDir = index file for the input data
        outputDir = directory to place dealiased velocity
        azimuth = calculate azimuthal shear
        divergence = calculate radial divergence
        azKernel = tuple (azimuthal, range) size in m for azimuthual shear
        divKernel = tuple (azimuthal, range) size in m for divergence
        refThreshold = threshold value for reflecitivty
        refTime = max time (seconds) between input and reflectivity field 
        noSpike = perform radial velocity spike removal
        xml = Write this configuration to an xml file?
        xmlFile = name of the xml file
    """

    cfg.log("Running w2circ")

    argument = "-i "+str(inputDir)+" -o "+str(outputDir)+" -v "+'"'+str(variable)+'"'+" -b "+str(startRange)+" --verbose "+str(logLevel)

    if azimuth:
        argument = argument+' -az -ka "'+":".join(map(str, azKernel))+'"'
    if divergence:
        argument = argument+' -div -kd "'+":".join(map(str, divKernel))+'"'
    if total:
        argument = argument+" -tot"
    if cressman:
        argument = argument+" -w cressman"
    if refThreshold is not None:
        argument = argument+' -t "'+str(refThreshold)+'" -z "'+str(refType)+'"'
    if refTime is not None:
        argument = argument+" -tr "+str(refTime)
    if dilate:
        if azimuth and refThreshold:
            argument = argument+" -D"
        else:
            cfg.error("w2circ: azimuth or refThreshold not set. Not dilating!!")
    if writeStamped:
        if azimuth and refThreshold:
            argument = argument+" -S"
        else:
            cfg.error("w2circ: azimuth or refThreshold not set. Not writing stamped!!")
    if writeMedian:
        if azimuth and refThreshold:
            argument = argument+" -m"
        else:
            cfg.error("w2circ: azimuth or refThreshold not set. Not writing stamped!!")
    if noSpike:
        argument = argument + " -sr"
    if xml:
        argument = argument + "-xml=config/"+xmlFile
    if realtime:
        argument = argument + ' -r'


    cfg.log("w2circ "+argument)

    outFile = str(time.time())+'_w2circ.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('w2circ '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')

    return proc, f

def w2localmax(cfg, inputDir, outputDir, inputName, logDir, dataRange=(20, 60, 10), smallestCluster=False, size=10, totalIntensity=2.0, smoothing="", xml=False, xmlFile="w2localmaxConfig.xml"):

    """ Runs w2localmax which uses a watershed algorithm. Returns the subprocess object.
        inputDir = index file of the input data
        outputDir = directory to place tables
        inputName = the name of the product to be processed
        dataRange = tuple (minimum, maximum, and incrment) for the watershed
        smallestCluster = start with the smallest cluster?
        size = minimum number of pixles per cluster
        totalIntenxity = product of cluster size and intesntiy for prunning (see w2localmax help)
        smoothing = smoothing techniques and parameters in string format
        xml = write this configuration to an xml file?
        xmlFile = the name of this file
        logLevel = how much stuff to print (scale of 0-5)
    """

    cfg.log("Running w2localmax")

    argument = "-i "+str(inputDir)+" -o "+str(outputDir)+' -I "'+str(inputName)+'" -d '+'"'+" ".join(map(str, dataRange))+'"'+" -S "+str(size)+" -T "+str(totalIntensity)

    if smallestCluster:
        argument = argument + " -s"
    if smoothing != "":
        argument = argument + " -k "+str(smoothing)
    if xml:
        argument = argument + " -xml=config/"+xmlFile

    cfg.log("w2localmax "+argument)
    
    outFile = str(time.time())+'_w2localmax.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('w2localmax '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')

    return proc, f

def w2smooth(cfg, inputDir, outputDir, inputName, logDir, missing=False, smoothing="", outputName="", xml=False, xmlFile="w2smoothConfig.xml"):

    """ Runs w2smooth to apply image processing like techniques to the data. Returns the subprocess object
        inputDir = index file for the input data
        outputDir = directory to put the smoothed data in
        inputName = the name of the product to be processed
        missing = do not smooth with missing values?
        smoothing = smoothing technique and parameters in string format 
        xml = write this configuration to an an xml file?
        xmlFile = the name of this file
    """

    cfg.log("Running w2smooth")

    argument = "-i "+str(inputDir)+" -o "+str(outputDir)+' -T "'+str(inputName)+'"'

    if missing:
        argument = argument + " -m"
    if smoothing != "":
        argument = argument + " -k "+str(smoothing)
    if xml:
        argument = argument + " -xml=config/"+xmlFile
    if outputName:
        argument = argument + " -t "+str(outputName)

    cfg.log("w2smooth "+argument)
    
    outFile = str(time.time())+'_w2smooth.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('w2smooth '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')

    return proc, f


def w2segmotionll(cfg, inputDir, outputDir, inputName, logDir, dataRange=(20, 50, 7.5, -1, 0.4), motionInterval=0, motionCompute=0, forecastInterval=0, advectionScale=(1), method='MULTISTAGE', sizefactor=1, disthresh=5, coastframes=3, agethresh=30, cluster=None, smooth=None, scaling='20,200,2000:0:0.8,0.4,0.2', grids='', xml=False, xmlFile="w2segmotionllConfig.xml", products=''):

    """ Runs w2segmotionll to compute motion. Returns subprocess object.
        inputDir = index file for the input data
        outputDir = directory to put the output in
        inputName = the name of the product to be processed
        dataRange = tuple (min, max, incr, maxdpeth, lambda)
        motionInterval = how often (minutes) to make a motion estimate
        motionCompute = how often (minutes) to compute motion
        forecastInterval = how often (minutes) to make a forcast
        xml = write this configuration to an xml file?
        xmlFile = the name of this file
    """

    cfg.log("Running w2segmotionll")

    argument = "-i "+str(inputDir)+" -o "+str(outputDir)+" -T "+'"'+str(inputName)+'"'+" -d "+'"'+" ".join(map(str, dataRange))+'"'+" -E "+str(motionInterval)+" -O "+str(motionCompute)+" -F "+str(forecastInterval)\
    +' -p '+str(scaling)+ ' -m '+str(method)+':'+str(sizefactor)+':'+str(disthresh)+':'+str(coastframes)+':'+str(agethresh)+' --logSize=20000000'

    if xml:
        argument = argument + " -xml=config/"+xmlFile
    if cluster:
        argument = argument + ' -X '+str(cluster)
    if smooth:
        argument = argument + ' -k '+str(smooth)
    if grids:
        argument = argument + ' -f "'+str(grids)+'"'
        
    if products:
        argument += ' --outputProducts="'+str(products)+'"'

    cfg.log("w2segmotionll "+argument)
    
    outFile = str(time.time())+'_w2segmotionll.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('w2segmotionll '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')
    
    return proc, f

def w2table2csv(cfg, inputDir, outputDir, table, logDir, seperator=",", units=False, header=False, comment="#", xml=False, xmlFile="w2table2csvConfig.xml"):

    """ Runs w2table2csv to convert WDSSII tables to .csv format. Returns the subprocess object.
        cfg = configuration object
        inputDir = index file for the input data
        outputDir = directory to place the tables
        seperator = the seperator in the file
        units = place units in the header?
        header = include a header?
        comment = character representing the start of a comment
        xml = write this configuration to an xml file?
        xmlFile = the name of this file
    """

    cfg.log("Running w2table2csv")

    argument = "-i "+str(inputDir)+" -o "+str(outputDir)+" -s "+str(seperator)+' -C "'+str(comment)+'" -T "'+str(table)+'"'

    if units:
        arugment = argument + " -U"
    if header:
        argument = arugment + " -h"
    if xml:
        argument = argument + " -xml=config/"+xmlFile

    cfg.log("w2table2csv "+argument)
    
    outFile = str(time.time())+'_w2table2csv.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('w2table2csv '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')

    return proc, f

        
def w2clustertable(cfg, inputDir, outputDir, trackingGrid, clusterTableXml, logDir, motionEast='Motion_East', motionSouth='Motion_South', kMeans='KMeans', realtime=False, numScales=4, method='MULTISTAGE', sizefactor=1, disthresh=5, coastframes=3, agethresh=30):

    """ runs w2clustertable calculates attributes for clusters as specified in the clusterTableXml """
    
    cfg.log("Running w2clustertable")
    
    argument = '-i '+str(inputDir)+' -o '+str(outputDir)+' -T '+str(trackingGrid)+' -E '+str(motionEast)+' -S '+str(motionSouth)+' -K '+str(kMeans)+' -s '+str(numScales)+' -X '+str(clusterTableXml)+\
        ' -m '+str(method)+':'+str(sizefactor)+':'+str(disthresh)+':'+str(coastframes)+':'+str(agethresh)
        
    if realtime:
        argument = argument + ' -r'
        
    cfg.log("w2clustertable "+argument)
    
    outFile = str(time.time())+'_w2clustertable.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('w2clustertable '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')

    return proc, f
    
    
def w2scoretrack(cfg, inputDir, outputDir, logDir, inputTable='ClusterTable:scale_1', realtime=False, consistencyAttributes='Size', linearAttributes='Latitude Longitude', growthDecayAttributes=None, idColumn='RowName', maxGapInMinutes=-1, confidenceIntervalMultiplier=0.67):
    
    """ runs w2scoretrack to score how well the tracking in w2clustertable is working """
    
    cfg.log("Running w2scoretrack")
    
    argument = '-i '+str(inputDir)+' -o '+str(outputDir)+' -I '+str(inputTable)+' -c '+str(consistencyAttributes)+' -L '+str(linearAttributes)+' -k '+str(idColumn)+' -G '+str(maxGapInMinutes)+' -C '+str(confidenceIntervalMultiplier)
    
    if realtime:
        argument = argument+ ' -r'
    if growthDecayAttributes:
        argument = argument+ ' -g '+str(growthDecayAttributes)
        
    cfg.log("w2scoretrack "+argument)
        
    outFile = str(time.time())+'_w2scoretrack.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('w2scoretrack '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')

    return proc, f
    
    
def w2scoreclusters(cfg, inputDir, outputDir, inputData, targetData, logDir, realtime=False, dataRange=(20, 60), targetRange=(20, 60), smooth='none none', size=10, search=(25, 0, 1), timeDiff=0.5):

    cfg.log("Running w2scoreclusters")
    
    argument = '-i '+str(inputDir)+' -o '+str(outputDir)+' -I '+str(inputData)+' -V '+str(targetData)+' -d "'+' '.join(map(str, dataRange))+'" -T "'+' '.join(map(str, targetRange))+'" -k "'+str(smooth)+'" -S '+str(size)+' -s "'+' '.join(map(str, search))+'" -t '+str(timeDiff)+' --logSize=2000000'
    
    if realtime:
        arguement = argument + ' -r'
        
    cfg.log("w2scoreclusters "+argument)
        
    outFile = str(time.time())+'_w2scoreclusters.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')

    proc = subprocess.Popen(shlex.split('w2scoreclusters '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')
    
    return proc, f
    
def netcdf2ldm(cfg, inputDir, outputDir, reflectivity, velocity, spectrumWidth, angularResolution, logDir, useRapic=False):

    cfg.log("Running netcdf2ldm")

    argument = '-i '+str(inputDir)+' -o '+str(outputDir)+' -R '+str(reflectivity)+' -V '+str(velocity)+' -S '+str(spectrumWidth)+' -p '+str(angularResolution)

    if useRapic:
        argument += ' -a'
        
    cfg.log("netcdf2ldm "+argument)

    outFile = str(time.time())+'_netcdf2ldm.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')

    proc = subprocess.Popen(shlex.split('netcdf2ldm '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')
    
    return proc, f
    
def UFIngestor(cfg, inputDir, outputDir, logDir, keepFiles=False, readExisting=False, executeOnce=False, uncompress=False, pattern='', flat=False, destinationDir='', SNG=5, sleep=5):
   
    cfg.log("Running UFIngestor")
    
    argument = '-i '+str(inputDir)+' -o '+str(outputDir)+' -N '+str(SNG)+' -t '+str(sleep)
    
    if keepFiles:
        argument += ' -k'
    if readExisting:
        argument += ' -a'
    if executeOnce:
        argument += ' -1'
    if pattern:
        argument += ' -p '+str(pattern)
        
        
    cfg.log("UFIngestor "+argument)

    outFile = str(time.time())+'_UFIngestor.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')

    proc = subprocess.Popen(shlex.split('UFIngestor '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')
    
    return proc, f 
    
def w2tds(cfg, inputDir, outputDir, logDir, realTime=False, azShearType='AzShear', rhoHVType='RhoHV', reflectivityType='Reflectivity', azShearThreshold=0.008, rhoHVThreshold=0.8, reflectivityThresh=20, products='all'):
    
    cfg.log("Running w2tds")
    
    argument = '-i '+str(inputDir)+' -o '+str(outputDir)+' -a '+str(azShearType)+' -c '+str(rhoHVType)+' -z '+str(reflectivityType)+\
                ' -A '+str(azShearThreshold)+' -C '+str(rhoHVThreshold)+' -Z '+str(reflectivityThresh)+' --logSize=2000000 --outputProducts="'+str(products)+'"'
                
    if realTime:
        agument += ' -r'
        
    cfg.log("w2tds "+argument)
    
    outFile = str(time.time())+'_w2tds.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('w2tds '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')
    
    return proc, f
    
def g2w2(cfg, inputDir, outputDir, logDir, flat=False, uncompressed=False, outputProducts='all'):
    """ Converts grib2 files to WDSSII netcdf format """
    
    cfg.log("Running g2w2")
    
    argument = '-i '+str(inputDir)+' -o '+str(outputDir)+' --logSize=2000000 --outputProducts="'+str(outputProducts)+'"'
    
    if flat:
        argument += ' -f'
    if uncompressed:
        argument += ' -u'
        
    cfg.log("g2w2 "+argument)
    
    outFile = str(time.time())+'_g2w2.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('g2w2 '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')
    
    return proc, f
    
def nse(cfg, inputDir, outputDir, logDir, fields=False, dealiasWind=False, realtime=False, outputProducts=''):
    """ Calculates environmental data from converted grib2 (or grib) model data """
    
    cfg.log("Running nse")
    
    argument = '-i '+str(inputDir)+' -o '+str(outputDir)+' --outputProducts="'+str(outputProducts)+'" --logSize=20000000'
    
    if fields:
        argument += ' -3'
    if dealiasWind:
        argument += ' -D'
    if realtime:
        argument += ' -r'
        
    cfg.log("nse "+argument)
    
    outFile = str(time.time())+'_nse.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('nse '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')
    
    return proc, f
    
def w2radarenv(cfg, inputDir, outputDir, surfaceTemperature, logDir, sourceRadars=None, heartBeatInterval=5):
    """ Finds surface temperature for radar """
    
    cfg.log("Running w2radarenv")
    
    argument = '-i '+str(inputDir)+' -o '+str(outputDir)+' -S '+str(surfaceTemperature)+' -h '+str(heartBeatInterval)
    
    if sourceRadars:
        argument += ' -s '+str(sourceRadars)
        
    cfg.log("w2radarenv argument "+argument)
    
    outFile = str(time.time())+'_w2radarenv.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('w2radarenv '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')
    
    return proc, f
    
def w2cropconv(cfg, inputDir, outputDir, inputField, logDir, realtime=False, upperLeft=None, bottomRight=None, resolution=None, source=None, gateWidth=1.0, remap=False, externalCommand=None, addGridCoords=False, nearestNeighbor=False):
    """ Crops a domain to that which is specified """
    
    cfg.log("Running w2cropconv")
    
    argument = '-i '+str(inputDir)+' -o '+str(outputDir)+' -I '+str(inputField)+' -g '+str(gateWidth)
    
    if upperLeft:
        argument += ' -t "'+" ".join(map(str, upperLeft))+'"'
    if bottomRight:
        argument += ' -b "'+" ".join(map(str, bottomRight))+'"'
    if resolution:
        argument += ' -s "'+" ".join(map(str, resolution))+'"'
    if source:
        argument += ' -S "'+str(source)+'"'
    if remap:
        argument += ' -R'
    if externalCommand:
        argument += ' -E "'+str(externalCommand)+'"'
    if addGridCoords:
        argument += ' -G'
    if nearestNeighbor:
        argument += ' -n'
    if realtime:
        argument += ' -r'
    
    argument += ' --logSize=2000000'
    
    cfg.log("w2cropconv "+argument)
    
    outFile = str(time.time())+'_w2cropconv.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('w2cropconv '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+'\n')
    
    return proc, f
    
def w2threshold(cfg, inputDir, outputDir, inputDataType, thresholdDataType, logDir, realtime=False, searchRadius=2, acceptableTimeDiff=10, thresholdValue=0, suffix='_Threshold', blob=False, smoothingKernel='none', wait=False):

    """ Threshsold intputDataType based on thresholdDataType """
    
    cfg.log("Running w2threshold")
    
    argument = '-i '+str(inputDir)+' -o '+str(outputDir)+' -d '+str(inputDataType)+' -t '+str(thresholdDataType)+' -R '+str(searchRadius)+' -T '+str(acceptableTimeDiff)+' -v '+str(thresholdValue)+' -n '+str(suffix)+' -k '+str(smoothingKernel)
        
    if realtime:
        argument += ' -r'
    if blob:
        argument += ' -b'
    if wait:
        argument += ' -w'
        
    argument += ' --logSize=2000000'
    
    cfg.log("w2threshold "+argument)
    
    outFile = str(time.time())+'_w2threshold.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('w2threshold '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+"\n")
    
    return proc, f
    
    
def w2hailtruth_size(cfg, inputDir, outputDir, logDir, cellName=None, reportName=None, realtime=False, dataColumn=None, reportColumn=None, searchMethod=1, searchRadius=5, timeWindow=(-15, 5), sectorWindow=(-90, 90), cellMaxAge=60):
    """ Take in a report and cell and match up the cell to that report and record it's data """
    
    cfg.log("Running w2hailtruth_size")
    
    argument = '-i '+str(inputDir)+' -o '+str(outputDir)+' -s '+str(searchMethod)+' -d '+str(searchRadius)+' -w "'+' '.join(map(str, timeWindow))+'" -p "'+' '.join(map(str, sectorWindow))+'" -A '+str(cellMaxAge)
    
    if realtime:
        argument += ' -r'
    if cellName:
        argument += ' -C '+str(cellName)
    if reportName:
        argument += ' -T '+str(reportName)
    if dataColumn:
        argument += ' -c "'+str(dataColumn)+'"'
    if reportColumn:
        argument += ' -a "'+str(reportColumn)+'"'
        
    argument += ' --logSize=2000000'
    
    cfg.log("w2hailtruth_size "+argument)
    
    outFile = str(time.time())+'_w2hailtruth_size.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('w2hailtruth_size '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+"\n")
    
    return proc, f
    
    
def archiveBTRT(cfg, inputDir, outputDir, start, end, logDir, inType=None, outType=None, bufTime=None, historyTime=None, bufDist=None, convDay=False):

    """ Runs Best Track Real Time (BTRT) [https://github.com/arkweather/BestTrackRT] archiveBTRT.py script.
    
        Parmeters:
        inputDir - Directory where the source files are.
        outputDir - The directory to save the output files to
        start - yyyymmdd for the start of the analysis period
        end - yyymmdd for the end of the anlaysis period
        inType - The file type of the input files (ascii, json, or xml)
        outType - Same as inType for the output files
        bufTime = The time threshold to use when associating cells
        historyTime - The number of minutes to keep cells in memoryview
        bufDist - Distance threshold for associating cells
        convDay - Whether the directory is organized by convective day
        
    """
    
    cfg.log("Running archiveBTRT.py")
    
    argument = str(start)+' '+str(end)+' '+str(inputDir)+' '+str(outputDir)
    
    if inType:
        argument += ' -it '+str(inType)
    if outType:
        argument += ' -ot '+str(outType)
    if bufTime:
        argument += ' -bt '+str(bufTime)
    if historyTime:
        argument += ' -ht '+str(historyTime)
    if bufDist:
        argument += ' -bd '+str(bufDist)
    if convDay:
        argument += ' -cd '+str(convDay)
        
    cfg.log('archiveBTRT.py '+argument)
    
    outFile = str(time.time())+'_archiveBTRT.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('python3 ttrappy/archiveBTRT.py '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+"\n")
    
    return proc, f
    
def w2csv2table(cfg, inputDir, outputDir, logDir, table='MesoTable', pattern='.csv', kill=False):
    """ Converts a .csv table into a WDSSII .xml table.
    
        inputDir - The input index 
        outputDir - The directory to place the output tobytes
        table - The name of the table to process
        pattern - Part of the filename pertaining to those files which should be processed
        kill - Whether to delete the file after processing
        
    """
    
    cfg.log("Running w2csv2table")
    
    argument = '-i '+str(inputDir)+' -o '+str(outputDir)+' -T '+str(table)+' -p '+str(pattern)
    
    if kill:
        argument += ' -K'
        
    cfg.log('w2csv2table '+argument)
    
    outFile = str(time.time())+'_w2csv2table.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('w2csv2table '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+"\n")
    
    return proc, f
        
def w2difference(cfg, inputDir, outputDir, gridX, gridY, outputName, logDir, timeDifference=None, linearScaling=None, realtime=False):

    """ Calcualtes the difference between gridX and gridY. This difference can be weighted by changing the linear scaling """
    
    cfg.log("Running w2difference")

    argument = '-i '+str(inputDir)+' -o '+str(outputDir)+' -X '+str(gridX)+' -Y '+str(gridY)+' -O '+str(outputName)
    
    if timeDifference:
        argument += ' -t '+str(timeDifference)
    if linearScaling:
        argument += ' -L "'+' '.join(map(str, linearScaling))+'"'
    if realtime:
        argument += ' -r'
     
    cfg.log('w2difference '+argument)
    
    outFile = str(time.time())+'_w2difference.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('w2difference '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    cfg.log("Writing to "+outFile+"\n")
    
    return proc, f
    
def createCache(cfg, outputDir, radarName, logDir, terrainFile=None, top=(37, -100, 20), bot=(30.5, -93, 1), spacing=(0.05, 0.05, 1), beamWidth=1.0, range=460, vcp=None, verbose=False, extractDir=None, coverage=False, zero=False, interpolation=None, partitioning=None):

    cfg.log("Running createCache")
    
    argument = '-o '+str(outputDir)+' -i '+str(radarName)+' -t "'+' '.join(map(str, top))+'" -b "'+' '.join(map(str, bot))+'" -s "'+' '.join(map(str, spacing))+'" -w '+str(beamWidth)+' -R '+str(range)
    
    if vcp:
        argument += ' -v '+str(vcp)
    if extractDir:
        argument += ' -e '+str(extractDir)
    if coverage:
        argument += ' -c'
    if zero:
        argument += ' -0'
    if interpolation:
        argument += ' -I '+str(interpolation)
    if partitioning:
        argument += ' -P '+str(paritioning)
    if verbose:
        argumetn += ' --verbose'
        
    cfg.log("createCache "+argument)
    
    outFile = str(time.time())+'_createCache.txt'
    
    f = open(os.path.join(logDir, outFile), 'w')
    
    proc = subprocess.Popen(shlex.split('createCache '+argument), stderr=subprocess.STDOUT, stdout=f)
    
    return proc, f
#Class for handling ttrappy subprocess objects.

class SubprocessHandler():

    
    def __init__(self, cfg, q, m):
    
        self.activeProcs = {}
        self.cfg = cfg
        if q:
            self.q = q
        else:
            self.q = None
        if m:
            self.m = m
            self.waitQ = self.m.Queue() #Separate Queue for communicating between the waitforrelease and the class
        else:
            self.m = None
            self.waitQ = None
        self.listenProc = mp.Process(target=self.listener, name='listener')
        self.openFiles = {}
        self.pidCount = 0 #Extra step to prevent duplicate processes
        
        self.listen = False
        
        return
        
    def cleanAll(self):
    
        """ Remove a subprocess from the active list if it has terminated """
        keys_copy = list(self.activeProcs.keys())
        self.cfg.log("Initiating cleaning of "+str(len(keys_copy))+" processes")
        for k in list(keys_copy):
            if self.activeProcs[k].poll() is not None :
                self.cfg.log("Cleaning subprocess "+str(k))
                try:
                    self.openFiles[k].flush()
                    self.openFiles[k].close()
                except ValueError:
                    self.cfg.error("Tried to flush a closed file")
                del self.activeProcs[k]
                del self.openFiles[k]
        
        return 
        
    def waitForRelease(self):
        
        #Pauses the program until wait or waitAll is finished
        startWait = dt.now()
        self.cfg.log("Waiting for release")
        blockRelease = False
        while True:
            if not self.waitQ.empty():
            
                qResult = self.waitQ.get_nowait()
                
                if qResult.lower() != 'released':
                    self.cfg.log("Waiting for release")
                    self.waitQ.put(qResult) #If the result is neither of the two things we are looking for, put it back in the queue
                    self.cfg.log("Queue is now "+str(self.waitQ.qsize())+" in length")

                
                else:
                   self.cfg.log("Release detected!")
                   break
                
                startWait = dt.now()
                
            else:
                # if (dt.now() - startWait).seconds > 120:
                    # self.cfg.log("Waiting timeout")
                    # break
                pass
                
            time.sleep(0.5)
             
        self.cfg.log("Released")
        
        return
        
    def waitAll(self):
    
        """ Despite the name, does not call wait, but rather checks to see if all active processes have finished.

            return True of so, False if not. This has the benifit of wait/communicate without holding up the listener"""
            
        keys_copy = list(self.activeProcs.keys())
        status = []
        for k in keys_copy:
            #self.cfg.log(str(k)+" poll "+str(self.activeProcs[k].poll()))
            status.append(self.activeProcs[k].poll() is None)
        #print(status)
        if any(status):
            return False
        else:

            self.cleanAll()
            self.waitQ.put('released')
        
            return True
        
    def wait(self, name):

        """ Call wait on a specific subprocess """
        try:
            self.activeProcs[name].communicate()
        except KeyError:
            self.cfg.log("No active process "+str(name)+" found ")
        
        self.cleanAll()
        
        self.waitQ.put('released')
        
        return
        
        
    def addProcess(self, subproc, name):
        """ Add a subprocess to the manager """
        
        if not subproc[0].poll():
            self.activeProcs[name] = subproc[0]
            self.openFiles[name] = subproc[1]
        else:
            self.cfg.log("Subprocess for call "+str(name)+" has already terminated. Not adding to active procs.")
        
        return
        
        
    def terminiate(self, name):
        """ Terminate a process """
        try:
            if not self.activeProcs[name].poll():
                self.cfg.log("Terminating subprocess "+str(name))
                self.activeProcs[name].terminate()
                self.openFiles[name].close()
                self.cleanAll()
            else:
                self.cfg.log("Subprocess "+str(name)+" was already terminated")
        except KeyError:
            self.cfg.log("Could not find subprocess "+str(name))
        
        return
    
    
    def terminateAll(self):
        """ Terminates all active processes """
        
        keys_copy = list(self.activeProcs.keys())
        for k in keys_copy:
            if self.activeProcs[k].poll() == None:
                self.cfg.log("Terminating subprocess "+str(k))
                self.activeProcs[k].terminate()
                self.openFiles[k].flush()
                self.openFiles[k].close()
            else:
                self.cfg.log("Subprocess "+str(k)+" was already terminated")
                
        self.cleanAll()
        return
        
    def getProcess(self, name):
        """ Returns the desired process """
        try:
            return self.activeProcs[name]
        except KeyError:
            self.cfg.log("Could not get process "+str(name)+". Process not found.")
            
        return None
            
    def listener(self, timeout=600):
        """ Listens for an exception to be placed in queue q and executes self.terminateAll upon receipt. 
            """
        lastUpdate = dt.now()
        #Call waitAll as a multiprocess to allow for the listener to continue listening
        
        waiting = False
        elapsedTime = 0
        self.q.put('STOP') #Add an initial sential for the qlist
        while self.listen:
            try:
               
                qList = []
                #If there is something in the queue, process the number of items in the q, check for timeout
                #print(self.q, self.q.empty(), self.q.qsize(), elapsedTime)
                for i in iter(self.q.get, 'STOP'):
                        qList.append(i)
                #print('qList', qList)        
                if qList:
                
                    for exc in qList:
                       
                        #self.cfg.log(str(exc))
                        if any(isinstance(x, err.StopProcessingException) for x in qList):
                            self.cfg.log("Listener StopProcessingException found!!! Stopping")
                            self.terminateAll()
                            self.listen = False
                            raise err.StopProcessingException("")
                        elif str(exc) == 'waitAll':
                            waiting = True
                        elif isinstance(exc[0], types.FunctionType):
                            if len(exc) > 1:
                                if not isinstance(exc[3], str):
                                    self.cfg.log("Tried to add process with no name. Stopping")
                                    self.terminateAll()
                                    self.listen = False
                                    raise TypeError("String not found in adding subprocess")
                                func = exc[0]
                                args = exc[1]
                                kwargs = exc[2]
                                pString = exc[3]
                            if (isinstance(args, str) and not kwargs):
                                self.addProcess(func(args), pString+'_'+str(self.pidCount))
                            elif (isinstance(args, tuple) and not kwargs):
                                self.addProcess(func(*args), pString+'_'+str(self.pidCount))
                            elif (isinstance(args, str) and kwargs):
                                self.addProcess(func(args, **kwargs), pString+'_'+str(self.pidCount))
                            elif (isinstance(args, tuple) and kwargs):
                                self.addProcess(func(*args, **kwargs), pString+'_'+str(self.pidCount))
                            else:    
                                self.addProcess(func(), pString+'_'+str(self.pidCount))
                                
                            self.pidCount += 1
                                
                        elif exc.lower() == 'stoplistener':
                            self.terminateAll()
                            self.listen = False
                            break
                            
                        lastUpdate = dt.now()
                else:
                    elapsedTime = (dt.now() - lastUpdate).seconds
                    if elapsedTime >= timeout:
                        self.cfg.error("Listener timed out. Stopping listener")
                        self.listen = False
                        self.terminateAll()
                        raise err.StopProcessingException("Timed Out")
                
                if waiting:
                    waiting = not self.waitAll()
                    
                    
                time.sleep(0.25)
            except KeyboardInterrupt:
                self.cfg.error("Listener Keyboard interupt. Stopping")
                self.listen = False
                self.terminateAll()

                break
            except err.StopProcessingException:
                break
            except Exception as E:
                self.cfg.error("Listener Exception. Stopping\n"+str(traceback.print_exc())+'\n'+str(E))
                self.listen = False
                self.waitQ.put('released')
                self.terminateAll()
                self.q.put('listenerexception')

                break
                
            #Place  the next sential in the q and reset the q list
            self.q.put('STOP')
        
        self.cfg.log("Returning listener")
        self.waitQ.put('released') #Release waitForRelease if running
        self.q.put('listenerstopped')
        sys.exit(0) #Actually stop the listener
        return
        
    def startListener(self):
        self.cfg.log("Starting listener")
        try:
            self.listen = True
            self.listenProc.start()
        except Exception as e:
            self.cfg.log("Unable to start listener")
        else:
            self.cfg.log("Listener started")
        return
        
    def stopListener(self):
        self.cfg.log("Stopping listener")
        self.listen = False
        try:
            self.q.put('stoplistener')
            self.listenProc.join()
            self.listenProc.close()
        except Exception as e:
            self.cfg.log("Unable to stop listener")
        else:
            self.cfg.log("Listener stopped")
        return
    
    def getQ(self):
        return self.q
        
    def getWaitQ(self):
        return self.waitQ