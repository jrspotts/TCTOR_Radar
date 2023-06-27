#Downloads radar data for a case


import sys
import os
from datetime import datetime as dt
from datetime import timedelta as td
from multiprocessing import Pool
import requests
from bs4 import BeautifulSoup as bs
from ttrappy import error as err

import nexradaws

#Downloads the files
def getRadarFiles(cfg, start, end, radar, radDir):
    
    """ Retrieve and download the files in the given range """
    
    conn = nexradaws.NexradAwsInterface()
    
    fileObjects = [] 
   
    cfg.log("Retrieving radar data for "+radar.name+" between "+str(start)+" and "+str(end))
    try:
        fileObjects = conn.get_avail_scans_in_range(start, end, radar.name)
    except TypeError as E:
        cfg.error('Warning! TypeError '+str(E)+' while downloading data for '+str(radar.name)+'. Take a look at this. Returning!')
        if radar.getIsClosest():
            raise err.RadarNotFoundError("Warning!! this radar is the closest. Cannot continue analysis")
        return radar
        
    radar.activate()
    
    earliestScan = cfg.utc.localize(dt(year=9999, month=12, day=30, hour=0, minute=0, second=0))
    latestScan = cfg.utc.localize(dt(year=1900, month=1, day=1, hour=0, minute=0, second=0))
    for fi in fileObjects:
        if fi.filename not in os.listdir(radDir) and 'MDM' not in fi.filename and (fi.filename.endswith('V06') or fi.filename.endswith('.gz')):
            radar.setLatestScan(fi)
            files = conn.download(fi, radDir)
            if files.success and not radar.hasData:
                radar.setHasData(True)
                
        else:
            cfg.log('File '+fi.filename+' alread exists or it is an MDM file')
            radar.setHasData(True)
            
        if fi.scan_time < earliestScan:
            radar.setFirstScan(fi)
            earliestScan = fi.scan_time
        elif fi.scan_time > latestScan:
            radar.setLatestScan(fi)
            latestScan = fi.scan_time
            
    return radar

def getURL(url, saveFolder, year, month, day):
    
    cfg.log("Trying historical on url")
    URL2 = os.path.join(cfg.rapHistorical, year+month, year+month+day)
    fullURL2 = os.path.join(URL2, fileNames[a])
    
    cfg.log("Attempting download of "+fullURL2)
    r2 = requests.get(fullURL2, stream=True)

    try:
        if '404 Not Found' in r2.content.decode('ASCII'):
            cfg.error("**No luck")
        
        else:
            savePath = os.path.join(case.rapDir, saveFolder, fileNames[a])
            cfg.log('downloaded something. Saving '+savePath)
            with open(savePath, 'wb') as f:
                f.write(r2.content)
                
    except (TypeError, UnicodeDecodeError) as e:
        cfg.error('Exception '+str(e))
        savePath = os.path.join(case.rapDir, saveFolder, fileNames[a])
        cfg.log('downloaded something. Saving '+savePath)
        with open(savePath, 'wb') as f:
            f.write(r2.content)    
            
    return
    
    
def getRapFiles(cfg, case, start, end):
    """ Downloads rap files from the NCEI archive for the given case """
    
    #Determine the period we will attempt to pull data from
    startDT = start - td(seconds=cfg.rapOffset*60)
    endDT = end + td(seconds=cfg.rapOffset*60)
    
    #Determine if we need to use current or historical link
    startHist = False
    endHist = False
    #Step 1: Download the content for the current link
    currentR = requests.get(cfg.rapCurrent, stream=True)
    #Step 2: Open the file in BeautifulSoup
    soup = bs(currentR.content, 'html.parser')
    linkTags = soup.find_all('a')
    #Step 3: Loop through the list of link targs and attempt to create dt objects
    
    monthStart = startDT.month
    if monthStart < 10:
        monthStart = '0'+str(monthStart)
    monthEnd = endDT.month
    if monthEnd < 10:
        monthEnd = '0'+str(monthEnd)
      
    startDT2 = str(startDT.year)+str(monthStart)
    endDT2 = str(endDT.year)+str(monthEnd)
    
    elements = [x.string.rstrip('/') for x in linkTags]
    if startDT2 not in elements:
        startHist = True
    else:
        #If not already flagged as needing to be historical
        nextLayerStart = requests.get(os.path.join(cfg.rapCurrent, startDT2), stream=True)
        soupStart1 = bs(nextLayerStart.content, 'html.parser')
        start1Tags = soupStart1.find_all('a')
        elements2 = [x.string.rstrip('/') for x in start1Tags]
        day = startDT.day
        if day < 10:
            day = '0'+str(day)
        startDT3 = startDT2+str(day)
        if startDT3 not in elements2:
            startHist = True
            
    if endDT2 not in elements:
        endHist = True
    else:
        #If not already flagged as needing to be historical
        nextLayerStart = requests.get(os.path.join(cfg.rapCurrent, endDT2), stream=True)
        soupEnd1 = bs(nextLayerStart.content, 'html.parser')
        end1Tags = soupStart1.find_all('a')
        elements2 = [x.string.rstrip('/') for x in start1Tags]
        day = startDT.day
        if day < 10:
            day = '0'+str(day)
        endDT3 = endDT2+str(day)
        if endDT3 not in elements2:
            endHist = True
            
   
    #Make list of filenames we think we will need
    fileNames = []
    fileDTs = []
    currentDT = startDT.replace(second=0, microsecond=0, minute=0, hour=startDT.hour)+td(hours=startDT.minute//30)-td(hours=1)
    
    while currentDT <= (endDT.replace(second=0, microsecond=0, minute=0, hour=endDT.hour)+td(hours=endDT.minute//30)):
        year = currentDT.year
        month = currentDT.month
        if month < 10:
            month = '0'+str(month)
        day = currentDT.day
        if day < 10:
            day = '0'+str(day)
        hour = currentDT.hour
        if hour < 10:
            hour = '0'+str(hour)
            
        fileNames.append(cfg.rapTemplate.substitute(year=year, month=month, day=day, hour=hour))
        fileDTs.append(currentDT)
        currentDT += td(seconds=3600)

    #Round up the end datetime if needed
    endDT = endDT.replace(second=0, microsecond=0, minute=0, hour=endDT.hour)+td(hours=endDT.minute//30)
    
    #Build links for start and end times
    startURL = ''
    endURL = ''
    
    startMonth = startDT.month
    if startMonth < 10:
        startMonth = '0'+str(startMonth)

    startDay = startDT.day
    if startDay < 10:
        startDay = '0'+str(startDay)
   
    endMonth = endDT.month
    if endMonth < 10:
        endMonth = '0'+str(endMonth)
        
    endDay = endDT.day
    if endDay < 10:
        endDay = '0'+str(endDay)
            
    if startHist:
        startURL = os.path.join(cfg.rapHistorical, str(startDT.year)+str(startMonth), str(startDT.year)+str(startMonth)+str(startDay))
    else:
        startURL = os.path.join(cfg.rapCurrent, str(startDT.year)+str(startMonth), str(startDT.year)+str(startMonth)+str(startDay))

    
    if endHist:
        endURL = os.path.join(cfg.rapHistorical, str(endDT.year)+str(endMonth), str(endDT.year)+str(endMonth)+str(endDay))
    else:
        endURL = os.path.join(cfg.rapCurrent, str(endDT.year)+str(endMonth), str(endDT.year)+str(endMonth)+str(endDay))
        
    #Download them
    for a in range(len(fileNames)):
    
         
        saveFolder = fileNames[a][9:21]
        saveFolderPath = os.path.join(case.rapDir, saveFolder)
        savePath = os.path.join(case.rapDir, saveFolder, fileNames[a])
        if os.path.exists(saveFolderPath):
            if fileNames[a] in os.listdir(saveFolderPath):
                cfg.log(savePath+' exists. Skipping.')
                continue
                
        if fileDTs[a].year == startDT.year and fileDTs[a].month == startDT.month and fileDTs[a].day == startDT.day:
            fullURL = os.path.join(startURL, fileNames[a])
        else:
            fullURL = os.path.join(endURL, fileNames[a])
            
        cfg.log("Attempting download of "+fullURL)
        r = requests.get(fullURL, stream=True)
        
       
        
        #Make the save folder
        try:
            os.mkdir(os.path.join(case.rapDir, saveFolder))
        except FileExistsError:
            pass
            
        try:
            if '404 Not Found' in r.content.decode('ASCII'):
                cfg.error(str(fileNames[a]+' was found to be a not binary file.'))
                
                #If it was the startURL using the current link, try the historical link
                if (startURL in fullURL) and (not startHist):
                    getURL(startURL, saveFolder, str(startDT.year), str(startMonth), str(startDay))
                    
                            
                #Same thing if it was the endURL with current link
                if (endURL in fullURL) and (not endHist):
                    getURL(endURL, saveFolder, str(endDT.year), str(endMonth), str(endDay))
                        
            else:
               
                cfg.log('downloaded something. Saving '+savePath)
                
                with open(savePath, 'wb') as f:
                    f.write(r.content)
                    
        except (TypeError, UnicodeDecodeError) as e:
            cfg.error('Exception '+str(e))
            cfg.log('downloaded something. Saving '+savePath)
            with open(savePath, 'wb') as f:
                f.write(r.content)
    return
    
def downloadData(cfg, case):

    """ Downloads level 2 data to be used in the algorithm. Returns two threads used to download the data 
        firstRun (bool) uses the back search time from config to determine searech period """ 
   
    start = case.dateTime-cfg.radarStart
    end = case.dateTime+cfg.radarEnd

    
    processNumber = len(case.sites)
    pool = Pool(processNumber)
 
    args = []
    for a in range(processNumber):
        args.append((cfg, start, end, case.sites[a], case.radDir))
    #cfg.log('\n'+str(args))
    
    try:
        
      asyncObj = pool.starmap_async(getRadarFiles, args)
      if cfg.useRap:
        getRapFiles(cfg, case, start, end)
      else:
        cfg.log("Skipping download of RAP files")
        
    except Exception as E:
        cfg.error("An exception occured while downloading data: "+str(E))
        pool.close()
        if isinstance(E, err.RadarNotFoundError):
            raise E
            exit(5)
    
        
    return asyncObj, pool
    
