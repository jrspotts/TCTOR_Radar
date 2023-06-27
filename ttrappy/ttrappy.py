# Algorithm for TTRAP

#Import Modules
from ttrappy import WDSSII as wds
from ttrappy import analysis
from ttrappy import error as err
import subprocess
import multiprocessing as mp
import os
import time
from datetime import datetime as dt
import sys
import traceback
import shutil



class Processor():
    
    """ The Processor class holds methods related to the processing of radar data with WDSSII and the high level functions
        regarding the processing of said data. This was made a class so that attributes, such as the ProcessHandler, can be 
        shared between methods. Takes the current cfg object, case object, and multiprocessing queue to handle interappliciation
        communication
    """
    cfg = None
    case = None
    spm = None #SubProcess Manager. Another name for SubprocessHandler
    
    def __init__(self, cfg, case, q=None, m=None):
    
        self.cfg = cfg
        self.case = case
        self.spm = wds.SubprocessHandler(self.cfg, q, m)
        
        return
    
    def __getstate__(self):
        self_dict = self.__dict__.copy()
        del self_dict['spm']
        return self_dict
    
    def __setstate__(self, self_dict):
        self.__dict__ = self_dict
        return
    
    def updateCase(self, case):
        self.case = case
        return

    def buildInput(self, program, overDir=None, suffix='', individual=False):

        """ Builds the dynamic input string for each case depending on the program
            Program options are:
            simulator: Create input dir string for w2simulator
            merger: Create input dir string for w2merger
            
            An overview directory can be specified as overDir. For example, the default location to find input for w2simulator is the cc dir, but the grid dir can be specified instead.
            The suffix is added to specify a special directory name. For example, for echo tops, the suffix ET may be added.
        """
        returnString = ''
        if program.lower() == 'simulator':
            for a in range(self.case.sitesNum):
                if self.case.sites[a].hasData:
                    if overDir:
                        returnString += overDir+'/'+self.case.sites[a].name+suffix+'/index.xml '
                    else:
                        returnString += self.case.dataDir+'/'+self.case.sites[a].name+suffix+'/index.xml '
            
            
        elif program.lower() == 'merger':
            for b in range(self.case.sitesNum):
                if self.case.sites[b].hasData:
                    if overDir:
                        returnString += overDir+'/'
                    else:
                        returnString += self.case.simDir+'/'
                    for a in range(self.case.sitesNum):
                        if self.case.sites[a].hasData:
                            returnString += self.case.sites[a].name
                    returnString += suffix
                    returnString+='/index_'+str(b)+'.fam '
                
            
                    

        elif program.lower() == 'simulatorvel':
            for a in range(self.cfg.numVelRadars):
                if self.case.sites[a].hasData:
                    if overDir:
                        returnString += overDir+'/'
                    else:
                        returnString += self.case.simDir+'/'
                    if individual:
                        returnString += self.case.sites[a].name
                    else:
                        for b in range(self.cfg.numVelRadars):
                            if self.case.sites[b].hasData:
                                returnString+=self.case.sites[b].name
                    returnString += suffix
                    returnString+='/index.xml '
        

        elif program.lower() == 'mergervel':
            for b in range(self.cfg.numVelRadars):
                if self.case.sites[b].hasData:
                    if overDir:
                        returnString += overDir+'/'
                    else:
                        returnString += case.simDir+'/'
                    for a in range(self.cfg.numVelRadars):
                        if self.case.sites[a].hasData:
                            returnString+=self.case.sites[a].name
                    returnString += suffix
                    returnString+='/index_'+str(b)+'.fam '
                    

            
        else:
            self.cfg.log('Program '+program+' not found for buildInput')
            
        return returnString.rstrip(' ')
        
    def buildOutput(self, program, overDir=None, suffix=''):

        """ Similar to buildInput(), but for the output directory """
        
        returnString = ''
        if program.lower() == 'simulator':
            if overDir:
                returnString += overDir+'/'
            else:
                returnString += self.case.simDir+'/'
            for a in range(self.case.sitesNum):
                if self.case.sites[a].hasData:
                    returnString += self.case.sites[a].name
            returnString += suffix
            

            
        elif program.lower() == 'merger':
            if overDir:
                returnString += overDir+'/'
            else:
                returnString += self.case.dataDir+'/'
            for a in range(self.case.sitesNum):
                if self.case.sites[a].hasData:
                    returnString+=self.case.sites[a].name
            returnString += suffix
            

            
        elif program.lower() == 'simulatorvel':
            if overDir:
                returnString += overDir+'/'
            else:
                returnString += self.case.simDir+'/'
            for a in range(self.cfg.numVelRadars):
                if self.case.sites[a].hasData:
                    returnString+=self.case.sites[a].name
            returnString += suffix
            

            
        elif program.lower() == 'mergervel':
            if overDir:
                returnString += overDir+'/'
            else:
                returnString += self.case.dataDir+'/'
            for a in range(self.cfg.numVelRadars):
                if self.case.sites[a].hasData:
                    returnString+=self.case.sites[a].name
            returnString += suffix
            
            
        else:
            self.cfg.log('Program '+program+' not found for buildOutput')
            return returnString
            
        return returnString.rstrip(' ')

   
        
    # def copyMotion(self):
        # """ Copy the Motion_South and Motion_East directories from motionDir to gridDir and re-index gridDir """
        # mSouth = os.path.join(self.buildOutput('merger', overDir=self.case.motionDir), 'Motion_South')
        # mEast = os.path.join(self.buildOutput('merger', overDir=self.case.motionDir), 'Motion_East')
        # mKmeans = os.path.join(self.buildOutput('merger', overDir=self.case.motionDir), 'KMeans')
        # dest = self.buildOutput('merger')
        
        # #If the path exists, copy it to gridDir
        # if os.path.exists(mSouth):
            # self.cfg.log('cp -vr '+str(mSouth)+' '+str(dest))
            # os.system('cp -vr '+str(mSouth)+' '+str(dest))
        # else:
            # self.cfg.log(str(mSouth)+" does not exist apparently")
        # if os.path.exists(mEast):
            # self.cfg.log('cp -r '+str(mEast)+' '+str(dest))
            # os.system('cp -r '+str(mEast)+' '+str(dest))
        # else:
            # self.cfg.log(str(mEast)+" does not exist apparently")
        # if os.path.exists(mKmeans):
            # self.cfg.log('cp -r '+str(mKmeans)+' '+str(dest))
            # os.system('cp -r '+str(mKmeans)+' '+str(dest))
        # else:
            # self.cfg.log(str(mKmeans)+" does not exist apparently")
            
        # #Re-index grid dir
        # q.put((wds.makeindex(self.cfg, dest), 'cpind'))
        # q.put(SubprocessHandler.waitAll)
        
        # return
    
    def reformatTilt(self, tiltDir, dataDir, isThreshold, tilt):
        """ Break down the individual tilt format and copy back to the data directory """
        
        tiltDirList = tiltDir.split('/')
        product = tiltDirList[-1] #The product we are copying
        tilt = tiltDirList[-2]
        
        altString = ''
        modBottom = str(self.cfg.bottom)
        if len(modBottom) <= 3:
            altString = '0'+modBottom+'0'
        else:
            altString = '0'+modBottom
            
        
        if isThreshold:

            copyFrom = os.path.join(tiltDir, tilt)
            copyTo = os.path.join(dataDir, product+'_tilt', tilt)
            copyToList = copyTo.split('/')
            
        else:
            copyFrom = os.path.join(tiltDir, altString)
            copyTo = os.path.join(dataDir, product+'_tilt', tilt)
            copyToList = copyTo.split('/')
        
        #Make the output directories so cp is happy
        currentDir = ''
        for dir in copyToList:
            currentDir = os.path.join(currentDir, dir)
            try:
                os.mkdir(currentDir)
            except FileExistsError:
                pass
        
        proc = subprocess.run(['cp', '-f', '-R', '-T',  copyFrom, copyTo])
        
        self.cfg.log(str(proc))
        
        #Remove the folder we copied from to save disk space
        proc = subprocess.run(['rm', '-r', copyFrom])
        
        self.cfg.log(str(proc))
        
        return
    
        
        
    #WDSII Processing for TTRAP   
    def wdssii(self):
        
        q = self.spm.getQ() #The queue to put messages for the listener into
        self.spm.startListener()
        
        cfg = self.cfg
        
        startTime = dt.now()
        
        finish = False
        
        logDir = self.case.logDir
        
        #Convert L2 to WDSII netcdf format
        try:
        
            if self.cfg.doIngest:
                self.cfg.log("Ingesting Data")
                #Start by converting the downloaded L2 data into WDSSII netcdf format for each site
                for a in range(self.case.sitesNum):
                    if self.case.sites[a].active:
                        if self.cfg.useSails:
                            q.put((wds.ldm2netcdf, (self.cfg, self.case.radDir, self.case.dataDir+"/"+self.case.sites[a].name, self.case.sites[a].name, self.case.sites[a].name, logDir), {'once':True, 'readOld':True, 'logLevel':'info', 'products':'all'}, 'ldm2netcdf'+self.case.sites[a].name))
                        else:
                            q.put((wds.ldm2netcdf, (self.cfg, self.case.radDir, self.case.dataDir+"/"+self.case.sites[a].name, self.case.sites[a].name, self.case.sites[a].name, logDir), {'once':True, 'readOld':True, 'logLevel':'info', 'nosails':True, 'products':'all'}, 'ldm2netcdf'+self.case.sites[a].name))
                
                #Get folders of rap data to process
                rapFolders = os.listdir(self.case.rapDir)
                if '.working' in rapFolders:
                    rapFolders.remove('.working')
                
                #Convert downloaded RAP grib2 files to WDSSII format
                for hour in rapFolders:
                    q.put((wds.g2w2, (self.cfg, os.path.join(self.case.rapDir, hour), os.path.join(self.case.rapConvDir, hour), logDir), {}, 'g2w2'+hour))
                    
                    
                q.put((wds.w2csv2table, (self.cfg, self.case.reportDir, self.case.reportTableDir, logDir), {'table':'Reports'}, 'csv2table'))
                
                #Put the cache in the w2mergercache folder for w2merger if desired to not save cache in the home directory
                
                if self.cfg.createCache:
                
                    # #Create cache for composite domains
                    for b in range(self.case.sitesNum):
                        if self.case.sites[b].active:
                            q.put((wds.createCache, (self.cfg, 'w2mergercache', self.case.sites[b].name, logDir), {'top':(self.case.topLat, self.case.topLon, self.cfg.top), 'bot':(self.case.botLat, self.case.botLon, self.cfg.bottom), 'spacing':(float(self.cfg.hSpacing), float(self.cfg.hSpacing), float(self.cfg.vSpacing))}, 'createCache'+self.case.sites[b].name+'large'))
                
                    # #Create cache for individual tilt domains
                    q.put((wds.createCache, (self.cfg, 'w2mergercache', self.case.sites[0].name, logDir), {'top':(self.case.topLat, self.case.topLon, self.cfg.top), 'bot':(self.case.botLat, self.case.botLon, self.cfg.bottom), 'spacing':(float(self.cfg.hvSpacing), float(self.cfg.hvSpacing), float(self.cfg.vvSpacing))}, 'createCache'+self.case.sites[0].name+'small'))
                    
                #Wait for them to finish
                q.put('waitAll')
                self.spm.waitForRelease()
                 
                #Create and index.xml for that output
                for b in range(self.case.sitesNum):
                    if self.case.sites[b].active:
                        q.put((wds.makeindex,(self.cfg, self.case.dataDir+"/"+self.case.sites[b].name, logDir), {}, 'LDMmakeindex'+self.case.sites[b].name))
                

                q.put((wds.makeindex, (self.cfg, self.case.dataDir, logDir), {}, 'data_dir'))
                
                for hour in rapFolders:
                    q.put((wds.makeindex, (self.cfg, os.path.join(self.case.rapConvDir, hour), logDir), {}, 'rapconv'))
                
                q.put('waitAll')
                self.spm.waitForRelease()
            
            
                for a in range(self.cfg.numVelRadars):
                    proc = subprocess.run(['cp', '-r', '-f', os.path.join(self.case.dataDir, self.case.sites[a].name, 'AliasedVelocity'), self.case.dataDir])
                    cfg.log(str(proc))
                    proc = subprocess.run(['cp', '-r', '-f', os.path.join(self.case.dataDir, self.case.sites[a].name, 'SpectrumWidth'), self.case.dataDir])
                    cfg.log(str(proc))
                    proc = subprocess.run(['cp', '-r', '-f', os.path.join(self.case.dataDir, self.case.sites[a].name, 'Reflectivity'), self.case.dataDir])
                    cfg.log(str(proc))
                    
                #Calculate environmental indices from the model data
                convFolders = os.listdir(self.case.rapConvDir)
                if '.working' in convFolders:
                    convFolders.remove('.working')
                if 'index.xml' in convFolders:
                    convFolders.remove('index.xml')
                    
                for hour in convFolders:
                    q.put((wds.nse, (self.cfg, os.path.join(self.case.rapConvDir, hour, 'index.xml'), self.case.dataDir, logDir), {'fields':True, 'dealiasWind':True, 'outputProducts':'SoundingTable,UWind3D,VWind3D,SfcUWind,SfcVWind,UWindMean0-6km,VWindMean0-6km'}, 'nse_'+str(hour)))
                
                q.put('waitAll')
                self.spm.waitForRelease()
                
                q.put((wds.makeindex, (self.cfg, self.case.dataDir, logDir), {}, 'makeindex_nse'))
                                
                q.put('waitAll')
                self.spm.waitForRelease()
                
                
                q.put((wds.w2difference, (self.cfg, os.path.join(self.case.dataDir, 'index.xml'), self.case.dataDir, 'UWind3D:06.00', 'SfcUWind:modelanalysis', 'udiff', logDir), {}, 'udiff'))
                q.put((wds.w2difference, (self.cfg, os.path.join(self.case.dataDir, 'index.xml'), self.case.dataDir, 'VWind3D:06.00', 'SfcVWind:modelanalysis', 'vdiff', logDir), {}, 'vdiff'))
                
            
                self.cfg.log("Done!")
                
            else:
                self.cfg.log("Skipping Ingest")
                
            #Set the start time to the time of the latest radar
        
            latestStartString = self.case.sites[0].getFirstScan().scan_time.strftime('%Y%m%d-%H%M%S')
            cfg.log('Latest start string '+latestStartString)
            
            if self.cfg.doQC:
            
                self.cfg.log("Running QC Programs")
                
                #Run the dual-pol quality control algorithm
                for a in range(self.case.sitesNum):
                    if self.case.sites[a].active:
                        q.put((wds.w2qcnndp, (self.cfg, self.case.dataDir+"/"+self.case.sites[a].name+'/index.xml', self.case.dataDir+"/"+self.case.sites[a].name, self.case.sites[a].name, logDir), {'realtime':False,'logLevel':'debug', 'products':'ReflectivityQC'}, 'qcnndp'+self.case.sites[a].name))
               
               #Dealias the velocity
                for a in range(self.cfg.numVelRadars):
                    if self.case.sites[a].active:
                        q.put((wds.dealiasVel, (self.cfg, '"'+self.case.dataDir+'/index.xml"', self.case.dataDir+"/"+self.case.sites[a].name, self.case.sites[a].name, logDir), {'realtime':False}, 'dealiasVel'+self.case.sites[a].name))
                
                
                q.put('waitAll')
                self.spm.waitForRelease()
                
                
                for b in range(self.case.sitesNum):
                    if self.case.sites[b].active:
                        q.put((wds.makeindex, (self.cfg, self.case.dataDir+"/"+self.case.sites[b].name, logDir), {'start':latestStartString}, 'NCmakeindex'+self.case.sites[b].name))
                
                
                q.put('waitAll')
                self.spm.waitForRelease()
                

                self.cfg.log("Completed Data QC")
            else:
                self.cfg.log("Skipping QC")
        
            azShearName = 'AzShear'
            isCrop = False
                
            if self.cfg.doAzShearET:
            
                self.cfg.log("Calculating AzShear and Echo Tops")
                
                if self.cfg.shearCressman:
                    self.cfg.log("Using Cressman weighting for AzShear calculations")
                
               
                #Calculate azimuthal shear. Note that as of the time of this comment, w2circ was not thresholding correctly. Therefore, the thresholding is done via w2threshold if desired
                for a in range(self.cfg.numVelRadars):
                    if self.case.sites[a].active:
                    
                        if self.cfg.thresholdShear:
                            q.put((wds.w2circ, (self.cfg, self.case.dataDir+"/"+self.case.sites[a].name+"/index.xml", self.case.dataDir+"/"+self.case.sites[a].name, logDir), {'divergence':False, 'cressman':self.cfg.shearCressman, 'noSpike':True, 'refThreshold':self.cfg.thresholdValue, 'refType':'ReflectivityQC', 'writeStamped':True, 'dilate':True, 'writeMedian':True, 'logLevel':'debug'}, 'circ'+self.case.sites[a].name+'threshold'))
                        else:
                            q.put((wds.w2circ, (self.cfg, self.case.dataDir+"/"+self.case.sites[a].name+"/index.xml", self.case.dataDir+"/"+self.case.sites[a].name, logDir), {'divergence':False, 'cressman':self.cfg.shearCressman, 'noSpike':True, 'logLevel':'debug'}, 'circ'+self.case.sites[a].name))
                
                    
                #Calculate echo tops
                for a in range(self.case.sitesNum):
                    if self.case.sites[a].active:
                        q.put((wds.w2echotop, (self.cfg, self.case.dataDir+"/"+self.case.sites[a].name+"/index.xml", self.case.dataDir+"/"+self.case.sites[a].name, logDir), {'inputName':"ReflectivityQC", 'thresholds':self.cfg.ETThresholds, 'products':'InterpDbZEchoTop_20'}, 'echotop'+self.case.sites[a].name))
            
            
                q.put('waitAll')
                self.spm.waitForRelease()
                
                
                for b in range(self.case.sitesNum):
                    if self.case.sites[b].active:
                        q.put((wds.makeindex, (self.cfg, self.case.dataDir+"/"+self.case.sites[b].name, logDir), {'start':latestStartString}, 'ETmakeindex'+self.case.sites[b].name))
                    
                q.put('waitAll')
                self.spm.waitForRelease()
            
                self.cfg.log("Done!")
                
            else:
                self.cfg.log("Skipping AzShear and ET calculations")
                
                
            if self.cfg.thresholdShear:
                    azShearName = 'AzShear_Storm'
            
            
           #This block was put in to use w2threshold to threshold AzShear, now we're going to use w2circ again as that's what's used operationally (Brandon Smith; personal communication)
            # if self.cfg.thresholdShear:
                # for a in range(self.cfg.numVelRadars):
                    # if self.case.sites[a].active:
                        # q.put((wds.w2threshold, (self.case.dataDir+"/"+self.case.sites[a].name+"/index.xml", self.case.dataDir+"/"+self.case.sites[a].name, 'AzShear', 'ReflectivityQC', logDir), {'searchRadius':0, 'thresholdValue':self.cfg.thresholdValue, 'wait':True}, 'threshold'+self.case.sites[a].name))
                
                # q.put('waitAll')
                # self.spm.waitForRelease() 
                
                # for b in range(self.cfg.numVelRadars):
                    # if self.case.sites[b].active:
                        # q.put((wds.makeindex, (self.case.dataDir+'/'+self.case.sites[a].name, logDir), {'start':latestStartString}, 'thresholdindex'))
                        
                # q.put('waitAll')
                # self.spm.waitForRelease() 
                        
                # azShearName = 'AzShear_Threshold'
                # isCrop = True
                

            if self.cfg.doTDS:
            
                self.cfg.log("Determing TDS signatures")
                
                #Calculate TDS signatures.
                for a in range(self.cfg.numVelRadars):
                    if self.case.sites[a].active:
                        q.put((wds.w2tds, (self.cfg, self.case.dataDir+'/'+self.case.sites[a].name+'/index.xml', self.case.dataDir+'/'+self.case.sites[a].name, logDir), {'rhoHVThreshold':0.90, 'azShearThreshold':0.0025, 'products':'TDS_CC', 'reflectivityThresh':35, 'azShearType':azShearName}, 'w2tds'))
                
                q.put('waitAll')
                self.spm.waitForRelease() 

                for b in range(self.cfg.numVelRadars):
                    if self.case.sites[b].active:
                        q.put((wds.makeindex, (self.cfg, self.case.dataDir+'/'+self.case.sites[a].name, logDir), {'start':latestStartString}, 'tdsindex'))
                                
                q.put('waitAll')
                self.spm.waitForRelease() 
                
                #Threshold the Zdr and Ref for where CC > 0
                
                for a in range(self.cfg.numVelRadars):
                    if self.case.sites[a].active:
                        q.put((wds.w2threshold, (self.cfg, self.case.dataDir+'/'+self.case.sites[a].name+'/index.xml', self.case.dataDir+'/'+self.case.sites[a].name, 'ReflectivityQC', 'TDS_CC', logDir), {'searchRadius':0, 'thresholdValue':0, 'wait':True}, 'threshold'+self.case.sites[a].name)) 
                        q.put((wds.w2threshold, (self.cfg, self.case.dataDir+'/'+self.case.sites[a].name+'/index.xml', self.case.dataDir+'/'+self.case.sites[a].name, 'Zdr', 'TDS_CC', logDir), {'searchRadius':0, 'thresholdValue':0, 'wait':True}, 'threshold'+self.case.sites[a].name)) 
                
                q.put('waitAll')
                self.spm.waitForRelease() 
                
                for b in range(self.cfg.numVelRadars):
                    if self.case.sites[b].active:
                        q.put((wds.makeindex, (self.cfg, self.case.dataDir+'/'+self.case.sites[a].name, logDir), {'start':latestStartString}, 'threshold_index_'+str(self.case.sites[a].name)))
                        
                q.put('waitAll')
                self.spm.waitForRelease() 
                
                self.cfg.log("Done")
            else:
                self.cfg.log("Skipping TDS calculation")
                
            
            
            if self.cfg.makeGrids:
            
                self.cfg.log("Making grids")
                #Start simulator for rest of products
                q.put((wds.w2simulator, (self.case, self.cfg, '"'+self.buildInput('simulator', overDir=self.case.dataDir)+' '+self.case.dataDir+'/index.xml"', self.buildOutput('simulator'), logDir), {'endOfDataset':True, 'simFactor':self.cfg.simMerge, 'notify':self.cfg.notify}, 'simulator1'))
                
                    
                #Start Echo Top Merger
                ETs = self.cfg.ETThresholds.split(' ')
                q.put((wds.w2merger, (self.cfg, '"'+self.buildInput('merger')+'"', self.case.dataDir, logDir), {'realtime':False, 'algorithms':'Composite', 'noVolume':True, 'method':1, 'upperLeft':(self.case.topLat, self.case.topLon, self.cfg.top), 'bottomRight':(self.case.botLat, self.case.botLon, self.cfg.bottom), 'resolution':(float(self.cfg.hSpacing), float(self.cfg.hSpacing), float(self.cfg.vSpacing)), 'inputName':'InterpDbZEchoTop_'+ETs[0], 'outputTiming':(self.cfg.gridTime, 1, 1), 'logLevel':'debug'}, 'ETmerge'))
                
                #Start Reflectivity Merger 'products':'VIL,MergedReflectivityQCComposite'
                q.put((wds.w2merger, (self.cfg, '"'+self.buildInput('merger')+'"', self.case.dataDir, logDir), {'realtime':False, 'algorithms':'Composite VIL', 'noVolume':True, 'method':self.cfg.refMethod, 'upperLeft':(self.case.topLat, self.case.topLon, self.cfg.top), 'bottomRight':(self.case.botLat, self.case.botLon, self.cfg.bottom), 'resolution':(float(self.cfg.hSpacing), float(self.cfg.hSpacing), float(self.cfg.vSpacing)), 'inputName':'ReflectivityQC', 'outputTiming':(self.cfg.gridTime, 1, 1), 'sigma':self.cfg.sigma, 'logLevel':'debug', 'products':'VIL,MergedReflectivityQCComposite'}, 'refQCmerge1'))
                # q.put((wds.w2merger, ('"'+self.buildInput('merger')+'"', self.case.dataDir), {'realtime':False, 'algorithms':'Composite VIL', 'noVolume':True, 'method':self.cfg.refMethod, 'upperLeft':(self.case.topLat, self.case.topLon, float(self.cfg.top)+(round(float(self.case.sites[0].hgt)/1000,2))), 'bottomRight':(self.case.botLat, self.case.botLon, float(self.cfg.bottom)+(round(float(self.case.sites[0].hgt)/1000,2))), 'resolution':(float(self.cfg.hSpacing), float(self.cfg.hSpacing), float(self.cfg.vSpacing)), 'inputName':'ReflectivityQC', 'outputTiming':(self.cfg.gridTime, 2, 5), 'logLevel':'debug', 'products':'VIL,MergedReflectivityQCComposite'}, 'refQCmerge2'))
                # q.put((wds.w2merger, ('"'+self.buildInput('merger')+'"', self.case.dataDir), {'realtime':False, 'algorithms':'Composite VIL', 'noVolume':True, 'method':self.cfg.refMethod, 'upperLeft':(self.case.topLat, self.case.topLon, float(self.cfg.top)+(round(float(self.case.sites[0].hgt)/1000,2))), 'bottomRight':(self.case.botLat, self.case.botLon, float(self.cfg.bottom)+(round(float(self.case.sites[0].hgt)/1000,2))), 'resolution':(float(self.cfg.hSpacing), float(self.cfg.hSpacing), float(self.cfg.vSpacing)), 'inputName':'ReflectivityQC', 'outputTiming':(self.cfg.gridTime, 3, 5), 'logLevel':'debug', 'products':'VIL,MergedReflectivityQCComposite'}, 'refQCmerge3'))
                # q.put((wds.w2merger, ('"'+self.buildInput('merger')+'"', self.case.dataDir), {'realtime':False, 'algorithms':'Composite VIL', 'noVolume':True, 'method':self.cfg.refMethod, 'upperLeft':(self.case.topLat, self.case.topLon, float(self.cfg.top)+(round(float(self.case.sites[0].hgt)/1000,2))), 'bottomRight':(self.case.botLat, self.case.botLon, float(self.cfg.bottom)+(round(float(self.case.sites[0].hgt)/1000,2))), 'resolution':(float(self.cfg.hSpacing), float(self.cfg.hSpacing), float(self.cfg.vSpacing)), 'inputName':'ReflectivityQC', 'outputTiming':(self.cfg.gridTime, 4, 5), 'logLevel':'debug', 'products':'VIL,MergedReflectivityQCComposite'}, 'refQCmerge4'))
                # q.put((wds.w2merger, ('"'+self.buildInput('merger')+'"', self.case.dataDir), {'realtime':False, 'algorithms':'Composite VIL', 'noVolume':True, 'method':self.cfg.refMethod, 'upperLeft':(self.case.topLat, self.case.topLon, float(self.cfg.top)+(round(float(self.case.sites[0].hgt)/1000,2))), 'bottomRight':(self.case.botLat, self.case.botLon, float(self.cfg.bottom)+(round(float(self.case.sites[0].hgt)/1000,2))), 'resolution':(float(self.cfg.hSpacing), float(self.cfg.hSpacing), float(self.cfg.vSpacing)), 'inputName':'ReflectivityQC', 'outputTiming':(self.cfg.gridTime, 5, 5), 'logLevel':'debug', 'products':'VIL,MergedReflectivityQCComposite'}, 'refQCmerge5'))
                
                if self.cfg.useCrop:
                
                    isCrop = True
                    #Create single-tilt grids using w2cropconv
                    azProductString = azShearName+' Velocity'
                    for type in azProductString.split(' '):
                        #q.put((wds.w2merger, ('"'+self.buildInput('merger')+'"', self.case.dataDir), {'method':self.cfg.velMethod, 'upperLeft':(self.case.topLat, self.case.topLon, float(self.cfg.vTop)), 'bottomRight':(self.case.botLat, self.case.botLon, float(self.cfg.bottom)), 'resolution':(float(self.cfg.hvSpacing), float(self.cfg.hvSpacing), float(self.cfg.vSpacing)), 'inputName':type, 'outputTiming':(self.cfg.gridTime, 1, 1), 'logLevel':'debug'}, type+'merge'))
                        
                        for tilt in self.cfg.tiltList:
                            q.put((wds.w2cropconv, (self.cfg, os.path.join(self.case.dataDir, self.case.sites[0].name, 'index.xml'), os.path.join(self.case.dataDir, 'tilt', tilt), type+':'+tilt, logDir), {'upperLeft':(self.case.topLat, self.case.topLon), 'bottomRight':(self.case.botLat, self.case.botLon), 'resolution':(float(self.cfg.hvSpacing), float(self.cfg.hvSpacing)), 'gateWidth':0.25, 'source':self.case.sites[0].name}, type+tilt+'crop'))
                            
                    for tilt in self.cfg.tiltList:
                        #Get correlation coeffecient only from the nearest radar, not the full data stream
                        q.put((wds.w2cropconv, (self.cfg, os.path.join(self.case.dataDir, self.case.sites[0].name, 'index.xml'), os.path.join(self.case.dataDir, 'tilt', tilt), 'RhoHV:'+tilt, logDir), {'upperLeft':(self.case.topLat, self.case.topLon), 'bottomRight':(self.case.botLat, self.case.botLon), 'resolution':(float(self.cfg.hvSpacing), float(self.cfg.hvSpacing)), 'gateWidth':0.25, 'source':self.case.sites[0].name}, 'cccrop'+str(tilt)))
                        q.put((wds.w2cropconv, (self.cfg, os.path.join(self.case.dataDir, self.case.sites[0].name, 'index.xml'),  os.path.join(self.case.dataDir, 'tilt', tilt), 'TDS_CC:'+tilt, logDir), {'upperLeft':(self.case.topLat, self.case.topLon), 'bottomRight':(self.case.botLat, self.case.botLon), 'resolution':(float(self.cfg.hvSpacing), float(self.cfg.hvSpacing)), 'gateWidth':0.25, 'source':self.case.sites[0].name}, 'tdscrop'+tilt))
                        q.put((wds.w2cropconv, (self.cfg, os.path.join(self.case.dataDir, self.case.sites[0].name, 'index.xml'),  os.path.join(self.case.dataDir, 'tilt', tilt), 'Zdr:'+tilt, logDir), {'upperLeft':(self.case.topLat, self.case.topLon), 'bottomRight':(self.case.botLat, self.case.botLon), 'resolution':(float(self.cfg.hvSpacing), float(self.cfg.hvSpacing)), 'gateWidth':0.25, 'source':self.case.sites[0].name}, 'zdrcrop'+tilt))
                        q.put((wds.w2cropconv, (self.cfg, os.path.join(self.case.dataDir, self.case.sites[0].name, 'index.xml'), os.path.join(self.case.dataDir, 'tilt', tilt), 'ReflectivityQC:'+tilt, logDir), {'upperLeft':(self.case.topLat, self.case.topLon), 'bottomRight':(self.case.botLat, self.case.botLon), 'resolution':(float(self.cfg.hvSpacing), float(self.cfg.hvSpacing)), 'gateWidth':0.25, 'source':self.case.sites[0].name}, 'refcrop'+tilt))
                        q.put((wds.w2cropconv, (self.cfg, os.path.join(self.case.dataDir, self.case.sites[0].name, 'index.xml'), os.path.join(self.case.dataDir, 'tilt', tilt), 'SpectrumWidth:'+tilt, logDir), {'upperLeft':(self.case.topLat, self.case.topLon), 'bottomRight':(self.case.botLat, self.case.botLon), 'resolution':(float(self.cfg.hvSpacing), float(self.cfg.hvSpacing)), 'gateWidth':0.25, 'source':self.case.sites[0].name}, 'spectrumwidthcrop'+tilt))
                        q.put((wds.w2cropconv, (self.cfg, os.path.join(self.case.dataDir, self.case.sites[0].name, 'index.xml'),  os.path.join(self.case.dataDir, 'tilt', tilt), 'Zdr_Threshold:'+tilt, logDir), {'upperLeft':(self.case.topLat, self.case.topLon), 'bottomRight':(self.case.botLat, self.case.botLon), 'resolution':(float(self.cfg.hvSpacing), float(self.cfg.hvSpacing)), 'gateWidth':0.25, 'source':self.case.sites[0].name}, 'zdrcrop'+tilt))
                        q.put((wds.w2cropconv, (self.cfg, os.path.join(self.case.dataDir, self.case.sites[0].name, 'index.xml'), os.path.join(self.case.dataDir, 'tilt', tilt), 'ReflectivityQC_Threshold:'+tilt, logDir), {'upperLeft':(self.case.topLat, self.case.topLon), 'bottomRight':(self.case.botLat, self.case.botLon), 'resolution':(float(self.cfg.hvSpacing), float(self.cfg.hvSpacing)), 'gateWidth':0.25, 'source':self.case.sites[0].name}, 'refcrop'+tilt))
                
                    q.put('waitAll')
                    self.spm.waitForRelease()
                    
                    #Reformat the tilt for the cropped data
                    for tilt in self.cfg.tiltList:
                        self.reformatTilt(os.path.join(self.case.dataDir, 'tilt', tilt, azShearName), self.case.dataDir, isCrop, tilt)
                        self.reformatTilt(os.path.join(self.case.dataDir, 'tilt', tilt, 'RhoHV'), self.case.dataDir, isCrop, tilt)
                        self.reformatTilt(os.path.join(self.case.dataDir, 'tilt', tilt, 'Velocity'), self.case.dataDir, isCrop, tilt)
                        self.reformatTilt(os.path.join(self.case.dataDir, 'tilt', tilt, 'TDS_CC'), self.case.dataDir, isCrop, tilt)
                        self.reformatTilt(os.path.join(self.case.dataDir, 'tilt', tilt, 'Zdr'), self.case.dataDir, isCrop, tilt)
                        self.reformatTilt(os.path.join(self.case.dataDir, 'tilt', tilt, 'ReflectivityQC'), self.case.dataDir, isCrop, tilt)
                        self.reformatTilt(os.path.join(self.case.dataDir, 'tilt', tilt, 'SpectrumWidth'), self.case.dataDir, isCrop, tilt)
                        self.reformatTilt(os.path.join(self.case.dataDir, 'tilt', tilt, 'Zdr_Threshold'), self.case.dataDir, isCrop, tilt)
                        self.reformatTilt(os.path.join(self.case.dataDir, 'tilt', tilt, 'ReflectivityQC_Threshold'), self.case.dataDir, isCrop, tilt)
                        time.sleep(0.25)
                        
                    
                    #Because w2cropconv does not follow the same naming convention as w2merger for it's output, we'll need to define the variables used later separately for the two programs
                    self.case.updateOutputDir('Zdr', self.case.dataDir)
                    self.case.updateProductVar('Zdr', 'Zdr')
                    self.case.updateOutputDir('SpectrumWidth', self.case.dataDir)
                    self.case.updateProductVar('SpectrumWidth', 'SpectrumWidth_tilt')
                    self.case.updateProductVar('shear', azShearName)
                    self.case.updateOutputDir('shear', self.case.dataDir)
                    self.case.updateProductVar('velocity', 'Velocity')
                    self.case.updateOutputDir('velocity', self.case.dataDir)
                    self.case.updateProductVar('cc', 'RhoHV')
                    self.case.updateOutputDir('cc', self.case.dataDir)
                    self.case.updateProductVar('tds', 'TDS_CC')
                    self.case.updateOutputDir('tds', self.case.dataDir)
                    self.case.updateOutputDir('ref0', self.case.dataDir)
                    self.case.updateProductVar('ref0', 'ReflectivityQC')
                        
                else:
                    #Start velocity and tds merger
                    azProductString = azShearName+' Velocity'
                    for type in azProductString.split(' '):
                        #q.put((wds.w2merger, ('"'+self.buildInput('merger')+'"', self.case.dataDir), {'method':self.cfg.velMethod, 'upperLeft':(self.case.topLat, self.case.topLon, float(self.cfg.vTop)), 'bottomRight':(self.case.botLat, self.case.botLon, float(self.cfg.bottom)), 'resolution':(float(self.cfg.hvSpacing), float(self.cfg.hvSpacing), float(self.cfg.vSpacing)), 'inputName':type, 'outputTiming':(self.cfg.gridTime, 1, 1), 'logLevel':'debug'}, type+'merge'))
                        
                        for tilt in self.cfg.tiltList:
                            q.put((wds.w2merger, (self.cfg, '"'+self.buildInput('merger')+'"', os.path.join(self.case.dataDir, 'tilt', tilt), logDir), {'method':self.cfg.velMethod, 'algorithms':'Composite', 'noVolume':True, 'upperLeft':(self.case.topLat, self.case.topLon, self.cfg.vTop), 'bottomRight':(self.case.botLat, self.case.botLon, self.cfg.bottom), 'resolution':(float(self.cfg.hvSpacing), float(self.cfg.hvSpacing), float(self.cfg.vvSpacing)), 'inputName':type+':'+tilt, 'outputTiming':(0, 1, 1), 'logLevel':'debug'}, type+tilt+'merge'))
                            
                    for tilt in self.cfg.tiltList:
                        #Get correlation coeffecient only from the nearest radar, not the full data stream
                        q.put((wds.w2merger, (self.cfg, os.path.join(self.case.dataDir, self.case.sites[0].name, 'index.xml'), os.path.join(self.case.dataDir, 'tilt', tilt), logDir), {'method':self.cfg.velMethod, 'algorithms':'VerticalMinimum', 'noVolume':True, 'upperLeft':(self.case.topLat, self.case.topLon, self.cfg.top), 'bottomRight':(self.case.botLat, self.case.botLon,self.cfg.bottom), 'resolution':(float(self.cfg.hvSpacing), float(self.cfg.hvSpacing), float(self.cfg.vvSpacing)), 'inputName':'RhoHV:'+tilt, 'outputTiming':(0, 1, 1), 'logLevel':'debug'}, 'ccmerge'+str(tilt)))
                        q.put((wds.w2merger, (self.cfg, '"'+self.buildInput('merger')+'"',  os.path.join(self.case.dataDir, 'tilt', tilt), logDir), {'method':self.cfg.velMethod, 'algorithms':'VerticalMinimum', 'noVolume':True, 'upperLeft':(self.case.topLat, self.case.topLon, self.cfg.top), 'bottomRight':(self.case.botLat, self.case.botLon, self.cfg.bottom), 'resolution':(float(self.cfg.hvSpacing), float(self.cfg.hvSpacing), float(self.cfg.vvSpacing)), 'inputName':'TDS_CC:'+tilt, 'outputTiming':(0, 1, 1), 'logLevel':'debug'}, 'tdsmerge'+tilt))
                        q.put((wds.w2merger, (self.cfg, os.path.join(self.case.dataDir, self.case.sites[0].name, 'index.xml'),  os.path.join(self.case.dataDir, 'tilt', tilt), logDir), {'method':self.cfg.velMethod, 'algorithms':'VerticalMinimum', 'noVolume':True, 'upperLeft':(self.case.topLat, self.case.topLon, self.cfg.top), 'bottomRight':(self.case.botLat, self.case.botLon, self.cfg.bottom), 'resolution':(float(self.cfg.hvSpacing), float(self.cfg.hvSpacing), float(self.cfg.vvSpacing)), 'inputName':'Zdr:'+tilt, 'outputTiming':(0, 1, 1), 'logLevel':'debug'}, 'zdrmerge'+tilt))
                        q.put((wds.w2merger, (self.cfg, os.path.join(self.case.dataDir, self.case.sites[0].name, 'index.xml'), os.path.join(self.case.dataDir, 'tilt', tilt), logDir), {'method':self.cfg.velMethod, 'algorithms':'Composite', 'noVolume':True, 'upperLeft':(self.case.topLat, self.case.topLon, self.cfg.top), 'bottomRight':(self.case.botLat, self.case.botLon, self.cfg.bottom), 'resolution':(float(self.cfg.hvSpacing), float(self.cfg.hvSpacing), float(self.cfg.vvSpacing)), 'inputName':'ReflectivityQC:'+tilt, 'outputTiming':(0, 1, 1), 'logLevel':'debug'}, 'refmerge'+tilt))
                        q.put((wds.w2merger, (self.cfg, os.path.join(self.case.dataDir, self.case.sites[0].name, 'index.xml'), os.path.join(self.case.dataDir, 'tilt', tilt), logDir), {'method':self.cfg.velMethod, 'algorithms':'Composite', 'noVolume':True, 'upperLeft':(self.case.topLat, self.case.topLon, self.cfg.top), 'bottomRight':(self.case.botLat, self.case.botLon, round(float(self.cfg.bottom)+(round(float(self.case.sites[0].hgt)/1000,2)), 2)), 'resolution':(float(self.cfg.hvSpacing), float(self.cfg.hvSpacing), float(self.cfg.vvSpacing)), 'inputName':'SpectrumWidth:'+tilt, 'outputTiming':(0, 1, 1), 'logLevel':'debug'}, 'spectrumwidth'+tilt))
                        q.put((wds.w2merger, (self.cfg, os.path.join(self.case.dataDir, self.case.sites[0].name, 'index.xml'), os.path.join(self.case.dataDir, 'tilt', tilt), logDir), {'method':self.cfg.velMethod, 'algorithms':'Composite', 'noVolume':True, 'upperLeft':(self.case.topLat, self.case.topLon, self.cfg.top), 'bottomRight':(self.case.botLat, self.case.botLon, round(float(self.cfg.bottom)+(round(float(self.case.sites[0].hgt)/1000,2)), 2)), 'resolution':(float(self.cfg.hvSpacing), float(self.cfg.hvSpacing), float(self.cfg.vvSpacing)), 'inputName':'ReflectivityQC_Threshold:'+tilt, 'outputTiming':(0, 1, 1), 'logLevel':'debug'}, 'refmerge_thresh'+tilt))
                        q.put((wds.w2merger, (self.cfg, os.path.join(self.case.dataDir, self.case.sites[0].name, 'index.xml'),  os.path.join(self.case.dataDir, 'tilt', tilt), logDir), {'method':self.cfg.velMethod, 'algorithms':'VerticalMinimum', 'noVolume':True, 'upperLeft':(self.case.topLat, self.case.topLon, self.cfg.top), 'bottomRight':(self.case.botLat, self.case.botLon, self.cfg.bottom), 'resolution':(float(self.cfg.hvSpacing), float(self.cfg.hvSpacing), float(self.cfg.vvSpacing)), 'inputName':'Zdr_Threshold:'+tilt, 'outputTiming':(0, 1, 1), 'logLevel':'debug'}, 'zdrmerge_thresh'+tilt))
                        
                    # q.put((wds.w2merger, ('"'+self.buildInput('merger')+'"', self.case.dataDir), {'method':self.cfg.velMethod, 'refURL':self.buildOutput('merger')+'/index.xml', 'refType':'MergedReflectivityQC', 'upperLeft':(self.case.topLat, self.case.topLon, float(self.cfg.vTop)), 'bottomRight':(self.case.botLat, self.case.botLon, float(self.cfg.bottom)), 'resolution':(float(self.cfg.hSpacing), float(self.cfg.hSpacing), float(self.cfg.vSpacing)), 'inputName':'PrecipConfidencePixelwise', 'outputTiming':(self.cfg.gridTime, 1, 1), 'logLevel':'debug'}, type+'merge'))
                
                
                    q.put('waitAll')
                    self.spm.waitForRelease()
                    
                    for tilt in self.cfg.tiltList:
                        self.reformatTilt(os.path.join(self.case.dataDir, 'tilt', tilt, 'Merged'+azShearName+'Composite'), self.case.dataDir, isCrop, tilt)
                        self.reformatTilt(os.path.join(self.case.dataDir, 'tilt', tilt, 'MergedRhoHVCompositeMin'), self.case.dataDir, isCrop, tilt)
                        self.reformatTilt(os.path.join(self.case.dataDir, 'tilt', tilt, 'MergedVelocityComposite'), self.case.dataDir, isCrop, tilt)
                        self.reformatTilt(os.path.join(self.case.dataDir, 'tilt', tilt, 'MergedTDS_CCCompositeMin'), self.case.dataDir, isCrop, tilt)
                        self.reformatTilt(os.path.join(self.case.dataDir, 'tilt', tilt, 'MergedZdrCompositeMin'), self.case.dataDir, isCrop, tilt)
                        self.reformatTilt(os.path.join(self.case.dataDir, 'tilt', tilt, 'MergedReflectivityQCComposite'), self.case.dataDir, isCrop, tilt)
                        self.reformatTilt(os.path.join(self.case.dataDir, 'tilt', tilt, 'MergedSpectrumWidthComposite'), self.case.dataDir, isCrop, tilt)
                        self.reformatTilt(os.path.join(self.case.dataDir, 'tilt', tilt, 'MergedZdr_ThresholdCompositeMin'), self.case.dataDir, isCrop, tilt)
                        self.reformatTilt(os.path.join(self.case.dataDir, 'tilt', tilt, 'MergedReflectivityQC_ThresholdComposite'), self.case.dataDir, isCrop, tilt)
                        time.sleep(0.25)
                     
                     
                    self.case.updateOutputDir('Zdr', self.case.dataDir)
                    self.case.updateProductVar('Zdr', 'MergedZdrCompositeMin')
                    self.case.updateOutputDir('SpectrumWidth', self.case.dataDir)
                    self.case.updateProductVar('SpectrumWidth', 'MergedSpectrumWidthComposite')
                    self.case.updateProductVar('shear', 'Merged'+azShearName+'Composite')
                    self.case.updateOutputDir('shear', self.case.dataDir)
                    self.case.updateProductVar('velocity', 'MergedVelocityComposite')
                    self.case.updateOutputDir('velocity', self.case.dataDir)
                    self.case.updateProductVar('cc', 'MergedRhoHVCompositeMin')
                    self.case.updateOutputDir('cc', self.case.dataDir)
                    self.case.updateProductVar('tds', 'MergedTDS_CCCompositeMin')
                    self.case.updateOutputDir('tds', self.case.dataDir)
                    
                
                q.put((wds.makeindex, (self.cfg, self.case.dataDir, logDir), {}, 'mergecrop1Index'))
                
                q.put('waitAll')
                self.spm.waitForRelease()
                
                self.cfg.log("Done!")
            else:
                self.cfg.log("Skipping grid creating")
            
            #Create xml tables for AzShears at the 0.5 deg tilts
            q.put((wds.w2csv2table, (self.cfg, self.case.reportDir, os.path.join(self.case.dataDir, 'clusters', 'shear', 'max', '00.50'), logDir), {'table':'Reports'}, 'csv2tablemax'))
            q.put((wds.w2csv2table, (self.cfg, self.case.reportDir, os.path.join(self.case.dataDir, 'clusters', 'shear', 'min', '00.50'), logDir), {'table':'Reports'}, 'csv2tablemin'))
            
            self.case.updateOutputDir('vil', self.case.dataDir)
            self.case.updateOutputDir('ref', self.case.dataDir)
            self.case.updateProductVar('vil', 'VIL')
            if self.cfg.shed.endswith('Composite'):
                self.case.updateProductVar('ref', 'MergedReflectivityQCComposite')
            else:
                self.case.updateProductVar('ref', 'MergedReflectivityQC')
                
            
            q.put('waitAll')
            self.spm.waitForRelease()
            
            azShearName2 = azShearName
            if not self.cfg.thresholdShear:
                azShearName2 = 'MergedAzShearComposite_tilt'
            else:
                azShearName2 += '_tilt'

            if self.cfg.doCluster:
            
                clusterSuffix = ''
                vilGrids = ''
                shearGrids = ''
                etGrids = ''
                
                if self.cfg.useCrop and not self.cfg.thresholdShear:
                    clusterSuffix = '_cropnothresh'
                    vilGrids = 'MergedReflectivityQCComposite VIL UWind3D VWind3D UWindMean0-6km VWindMean0-6km udiff vdiff'
                    shearGrids = 'AzShear_tilt TDS_CC_tilt RhoHV_tilt Zdr_Threshold_tilt ReflectivityQC_Threshold_tilt SpectrumWidth_tilt udiff vdiff UWindMean0-6km VWindMean0-6km'
                    etGrids = 'MergedInterpDbZEchoTop_20Composite'
                elif not self.cfg.useCrop and self.cfg.thresholdShear:
                    clusterSuffix = '_threshnocrop'
                    vilGrids = 'MergedReflectivityQCComposite VIL UWind3D VWind3D UWindMean0-6km VWindMean0-6km udiff vdiff'
                    shearGrids = 'MergedAzShear_StormComposite_tilt MergedTDS_CCCompositeMin_tilt MergedRhoHVCompositeMin_tilt MergedZdr_ThresholdCompositeMin_tilt MergedReflectivityQC_ThresholdComposite_tilt MergedSpectrumWidthComposite_tilt udiff vdiff UWindMean0-6km VWindMean0-6km'
                    etGrids = 'MergedInterpDbZEchoTop_20Composite'
                elif self.cfg.useCrop and self.cfg.thresholdShear:
                    clusterSuffix = '_threshcrop'
                    vilGrids = 'MergedReflectivityQCComposite VIL UWind3D VWind3D UWindMean0-6km VWindMean0-6km udiff vdiff'
                    shearGrids = 'AzShear_Storm_tilt TDS_CC_tilt RhoHV_tilt Zdr_Threshold_tilt ReflectivityQC_Threshold_tilt SpectrumWidth_tilt udiff vdiff UWindMean0-6km VWindMean0-6km'
                    etGrids = 'MergedInterpDbZEchoTop_20Composite'
                else:
                    clusterSuffix = ''
                    vilGrids = 'MergedReflectivityQCComposite VIL UWind3D VWind3D UWindMean0-6km VWindMean0-6km udiff vdiff'
                    shearGrids = 'MergedAzShearComposite_tilt MergedTDS_CCCompositeMin_tilt MergedRhoHVCompositeMin_tilt MergedZdr_ThresholdCompositeMin_tilt MergedReflectivityQC_ThresholdComposite_tilt MergedSpectrumWidthComposite_tilt udiff vdiff UWindMean0-6km VWindMean0-6km'
                    etGrids = 'MergedInterpDbZEchoTop_20Composite'

                self.cfg.log("Creating clusters")
                #Now create clusters of VIL, AzShear, and Echo Tops
                q.put((wds.w2segmotionll, (self.cfg, self.case.dataDir+'/index.xml', self.case.dataDir+'/clusters/VIL', 'VIL', logDir), {'dataRange':self.cfg.trackClusterTuple, 'cluster':self.cfg.trackCluster, 'grids':vilGrids, 'smooth':'threshold:95:100:percent,scaling:100:0,percent:75:3:0:3', 'scaling':self.cfg.trackScalingString, 'sizefactor':2, 'disthresh':10, 'coastframes':0, 'products':'TrackClusterTable,ClusterID'}, 'segmotionllTrack'))
                
                for tilt in self.cfg.tiltList:
                    q.put((wds.w2segmotionll, (self.cfg, self.case.dataDir+'/index.xml', self.case.dataDir+'/clusters/shear/max/'+tilt, azShearName2+':'+tilt, logDir), {'dataRange':self.cfg.shearClusterTuple, 'smooth':'threshold:96:100:percent,scaling:1000000:0', 'cluster':self.cfg.shearCluster+tilt+clusterSuffix+'.xml', 'grids':shearGrids, 'scaling':self.cfg.shearScalingString, 'sizefactor':2, 'disthresh':self.cfg.maxShearDist, 'coastframes':0, 'products':'MaxShearClusterTable,ClusterID'}, 'segmotionllMaxShear'+tilt))
                    q.put((wds.w2segmotionll, (self.cfg, self.case.dataDir+'/index.xml', self.case.dataDir+'/clusters/shear/min/'+tilt, azShearName2+':'+tilt, logDir), {'dataRange':self.cfg.minShearClusterTuple, 'smooth':'scaling:-1:0,threshold:96:100:percent,scaling:1000000:0', 'cluster':self.cfg.minShearCluster+tilt+clusterSuffix+'.xml', 'grids':shearGrids, 'scaling':self.cfg.minShearScalingString, 'sizefactor':2, 'disthresh':self.cfg.maxShearDist, 'coastframes':0, 'products':'MinShearClusterTable,ClusterID'}, 'segmotionllMinShear'+tilt))
                    
                q.put((wds.w2segmotionll, (self.cfg, self.case.dataDir+'/index.xml', self.case.dataDir+'/clusters/ET', 'MergedInterpDbZEchoTop_20Composite', logDir), {'dataRange':self.cfg.topClusterTuple, 'smooth':'threshold:72:100:percent,scaling:100:0,percent:50:1:0:1', 'cluster':self.cfg.topCluster, 'grids':etGrids, 'scaling':self.cfg.topScalingString, 'sizefactor':2, 'disthresh':10, 'coastframes':0, 'products':'ETClusterTable,ClusterID'}, 'segmotionllTop'))
                

                #Create output of the smoothed data to see what's happening
                q.put((wds.w2smooth, (self.cfg, self.case.dataDir+'/index.xml', self.case.dataDir, 'MergedInterpDbZEchoTop_20Composite', logDir), {'smoothing':'threshold:72:100:percent,scaling:100:0,percent:50:1:0:1', 'missing':True, 'outputName':'_smoothed1'}, 'tracksmooth1'))

                q.put('waitAll')
                self.spm.waitForRelease()
                
                q.put((wds.makeindex, (self.cfg, self.case.dataDir, logDir), {}, 'clusterMakeIndex1'))
                
                q.put('waitAll')
                self.spm.waitForRelease()
                
                self.cfg.log("Done!")
            else:
                self.cfg.log("Skipping cluster creation")
            
            if self.cfg.doBTRT:
            
                self.cfg.log("Running BTRT")
                
                start = self.case.startTime.strftime('%Y%m%d')
                end = self.case.endTime.strftime('%Y%m%d')
                
                #Make scale directories for BTRT
                try:
                    os.mkdir(os.path.join(self.case.dataDir, 'clusters', 'VIL', 'ClusterBT'))
                except FileExistsError:
                    pass
                
                try:
                    os.mkdir(os.path.join(self.case.dataDir, 'clusters', 'ET', 'ClusterBT'))
                except FileExistsError:
                    pass
                    
                q.put((wds.archiveBTRT, (self.cfg, os.path.join(self.case.dataDir, 'clusters', 'VIL', 'TrackClusterTable', 'scale_0'), os.path.join(self.case.dataDir, 'clusters', 'VIL', 'ClusterBT')+'/', start, end, logDir), {'inType':'xml', 'outType':'xml', 'bufTime':8}, 'archiveBTRTVIL'))
                q.put((wds.archiveBTRT, (self.cfg, os.path.join(self.case.dataDir, 'clusters', 'ET', 'ETClusterTable', 'scale_0'), os.path.join(self.case.dataDir, 'clusters', 'ET', 'ClusterBT')+'/', start, end, logDir), {'inType':'xml', 'outType':'xml', 'bufTime':8}, 'archiveBTRTET'))
                
                for tilt in self.cfg.tiltList:
                    
                    #Also make output directories for archiveBTRT.py here
                    try:
                        os.mkdir(os.path.join(self.case.dataDir, 'clusters', 'shear', 'max', tilt, 'ClusterBT'))
                    except FileExistsError:
                        pass
                        
                    try:
                        os.mkdir(os.path.join(self.case.dataDir, 'clusters', 'shear', 'min', tilt, 'ClusterBT'))
                    except FileExistsError:
                        pass
                        
                    q.put((wds.archiveBTRT, (self.cfg, os.path.join(self.case.dataDir, 'clusters', 'shear', 'max', tilt, 'MaxShearClusterTable', 'scale_0'), os.path.join(self.case.dataDir, 'clusters', 'shear', 'max', tilt, 'ClusterBT')+'/', start, end, logDir), {'inType':'xml', 'outType':'xml', 'bufTime':8, 'bufDist':round(self.cfg.maxShearDist)}, 'archiveBTRTMax'+tilt))
                    q.put((wds.archiveBTRT, (self.cfg, os.path.join(self.case.dataDir, 'clusters', 'shear', 'min', tilt, 'MinShearClusterTable', 'scale_0'), os.path.join(self.case.dataDir, 'clusters', 'shear', 'min', tilt, 'ClusterBT')+'/', start, end, logDir), {'inType':'xml', 'outType':'xml', 'bufTime':8, 'bufDist':round(self.cfg.maxShearDist)}, 'archiveBTRTMin'+tilt))
                
                q.put('waitAll')
                self.spm.waitForRelease()
                
                #Go through a table in the newly created table directory and grab the headers to copy. Some code adapted/taken from BTRT for the maximum 0.5 deg clusters
                maxbtrtTables = os.listdir(os.path.join(self.case.dataDir, 'clusters', 'shear', 'max', '00.50', 'ClusterBT'))
                maxHeaderString = ''
                for table in maxbtrtTables:
                    #Check to make sure it's an xml file
                    if table.endswith('.xml'):
                        tableFile = open(os.path.join(self.case.dataDir, 'clusters', 'shear', 'max', '00.50', 'ClusterBT', table), 'r')
                        for line in tableFile:
                            #Check to see if the line is a data column
                            if line.strip().startswith('<datacolumn '):
                                maxHeaderString += line.strip().split(' ')[1].split('"')[1]+' '
                        
                        maxHeaderString.strip(' ')
                        break
                
                
                #Same thing, but for the minimum clusters
                minbtrtTables = os.listdir(os.path.join(self.case.dataDir, 'clusters', 'shear', 'min', '00.50', 'ClusterBT'))
                minHeaderString = ''
                for table in minbtrtTables:
                    #Check to make sure it's an xml file
                    if table.endswith('.xml'):
                        tableFile = open(os.path.join(self.case.dataDir, 'clusters', 'shear', 'min', '00.50', 'ClusterBT', table), 'r')
                        for line in tableFile:
                            #Check to see if the line is a data column
                            if line.strip().startswith('<datacolumn '):
                                minHeaderString += line.strip().split(' ')[1].split('"')[1]+' '
                        
                        minHeaderString.strip(' ')
                        break
                        
                
                
                q.put((wds.makeindex, (self.cfg, self.case.dataDir, logDir), {}, 'bestTrackIndex'))
                q.put((wds.makeindex, (self.cfg, os.path.join(self.case.dataDir, 'clusters', 'VIL'), logDir), {}, 'vilclusterindex'))
                q.put((wds.makeindex, (self.cfg, os.path.join(self.case.dataDir, 'clusters', 'ET'), logDir), {}, 'etclusterindex'))
                
                for tilt in self.cfg.tiltList:
                    q.put((wds.makeindex, (self.cfg, os.path.join(self.case.dataDir, 'clusters', 'shear', 'max', tilt), logDir), {}, tilt+'maxshearclusterindex'))
                    q.put((wds.makeindex, (self.cfg, os.path.join(self.case.dataDir, 'clusters', 'shear', 'min', tilt), logDir), {}, tilt+'minshearclusterindex'))
                
                
                
                q.put('waitAll')
                self.spm.waitForRelease()
                
                self.cfg.log("Done!")
            else:
                self.cfg.log("Skipping BTRT")
            
            
            if self.cfg.doCSV:
            
                self.cfg.log("Running w2hailtruth_size and converting tables to csv")
                
                q.put((wds.w2hailtruth_size,  (self.cfg, os.path.join(self.case.dataDir, 'clusters', 'shear', 'max', '00.50', 'index.xml'), os.path.join(self.case.dataDir, 'maxtruth'), logDir), {'cellName':'ClusterBT', 'reportName':'Reports', 'reportColumn':'RowName', 'cellMaxAge':480, 'dataColumn':maxHeaderString, 'searchRadius':self.cfg.maxShearDistInit, 'searchMethod':2, 'timeWindow':(-5, 5)}, 'hailtruth_size_max'))
                q.put((wds.w2hailtruth_size,  (self.cfg, os.path.join(self.case.dataDir, 'clusters', 'shear', 'min', '00.50', 'index.xml'), os.path.join(self.case.dataDir, 'mintruth'), logDir), {'cellName':'ClusterBT', 'reportName':'Reports', 'reportColumn':'RowName', 'cellMaxAge':480, 'dataColumn':minHeaderString, 'searchRadius':self.cfg.maxShearDistInit, 'searchMethod':2, 'timeWindow':(-5, 5)}, 'hailtruth_size_min'))
                
                q.put('waitAll')
                self.spm.waitForRelease()
                
                q.put((wds.makeindex, (self.cfg, self.case.dataDir, logDir), {}, 'TruthTableIndex'))
                
                q.put('waitAll')
                self.spm.waitForRelease()
                 
                q.put((wds.w2table2csv, (self.cfg, os.path.join(self.case.dataDir, 'index.xml'), os.path.join(self.case.hailTruthDir, 'maxshear'), 'maxtruth:TruthTable', logDir), {'units':True, 'header':True}, 'maxcluster2csvTruth'))
                q.put((wds.w2table2csv, (self.cfg, os.path.join(self.case.dataDir, 'index.xml'), os.path.join(self.case.hailTruthDir, 'minshear'), 'mintruth:TruthTable', logDir), {'units':True, 'header':True}, 'mincluster2csvTruth'))
                 
                q.put((wds.w2table2csv, (self.cfg, os.path.join(self.case.dataDir, 'clusters', 'VIL', 'index.xml'), os.path.join(self.case.dataDir, 'clusters', 'VIL', 'ClusterCSV'), 'ClusterBT', logDir), {'units':True, 'header':True}, 'vilcluster2csv'))
                q.put((wds.w2table2csv, (self.cfg, os.path.join(self.case.dataDir, 'clusters', 'ET', 'index.xml'), os.path.join(self.case.dataDir, 'clusters', 'ET', 'ClusterCSV'), 'ClusterBT', logDir), {'units':True, 'header':True}, 'et2csv'))
                
                for tilt in self.cfg.tiltList:
                    q.put((wds.w2table2csv, (self.cfg, os.path.join(self.case.dataDir, 'clusters', 'shear', 'max', tilt, 'index.xml'), os.path.join(self.case.dataDir, 'clusters', 'shear', 'max', tilt, 'ClusterCSV'), 'ClusterBT', logDir), {'units':True, 'header':True}, 'maxshear2csv'))
                    q.put((wds.w2table2csv, (self.cfg, os.path.join(self.case.dataDir, 'clusters', 'shear', 'min', tilt, 'index.xml'), os.path.join(self.case.dataDir, 'clusters', 'shear', 'min', tilt, 'ClusterCSV'), 'ClusterBT', logDir), {'units':True, 'header':True}, 'minshear2csv'))
                    
                q.put('waitAll')
                self.spm.waitForRelease()
                
                self.cfg.log("Done")
                
            else:
                self.cfg.log("Skipping w2hailtruth and CSV table creation")
            
            self.case.updateOutputDir('motion', self.case.dataDir)
            self.case.updateProductVar('motione', 'Motion_East')
            self.case.updateProductVar('motions', 'Motion_South')
            self.case.updateOutputDir('cluster',  os.path.join(self.case.dataDir, 'clusters', 'VIL'))
            self.case.updateProductVar('cluster', 'ClusterID')
            self.case.updateOutputDir('maxShearCluster', os.path.join(self.case.dataDir, 'clusters', 'shear', 'max'))
            self.case.updateProductVar('maxShearCluster', 'ClusterID')
            self.case.updateOutputDir('minShearCluster', os.path.join(self.case.dataDir, 'clusters', 'shear', 'min'))
            self.case.updateProductVar('minShearCluster', 'ClusterID')
            self.case.updateOutputDir('ETCluster', os.path.join(self.case.dataDir, 'clusters', 'ET'))
            self.case.updateProductVar('ETCluster', 'ClusterID')
            self.case.updateOutputDir('maxShearClusterTable', os.path.join(self.case.dataDir, 'clusters', 'shear', 'max'))
            self.case.updateProductVar('maxShearClusterTable', 'ClusterCSV')
            self.case.updateOutputDir('minShearClusterTable', os.path.join(self.case.dataDir, 'clusters', 'shear', 'min'))
            self.case.updateProductVar('minShearClusterTable', 'ClusterCSV')
            self.case.updateOutputDir('ETClusterTable', os.path.join(self.case.dataDir, 'clusters', 'ET'))
            self.case.updateProductVar('ETClusterTable', 'ClusterCSV')
            self.case.updateOutputDir('hailtruth', self.case.hailTruthDir)
            self.case.updateProductVar('clustertable', 'TrackClusterTable')
            self.case.updateOutputDir('clustertable', os.path.join(self.case.dataDir, 'clusters', 'VIL', 'ClusterCSV'))
            self.case.updateProductVar('et', 'MergedInterpDbZEchoTop_20Composite')
            self.case.updateOutputDir('et', self.case.dataDir)

            
            finish = True #Let the program know we made it to the end (having an exception would have skipped this)
            
            
        except KeyboardInterrupt:

            self.cfg.log("KeyboardInterrupt in WDSSII")
            
            raise
            
        except Exception as E:
            self.cfg.error("Error for case: "+self.case.ID+'\n'+str(E))
            
            raise
            

        self.case.saveVars(self.cfg, self.case.baseDir, 'vars.pkl')
        
        self.spm.stopListener()
        
        self.cfg = cfg
        
        elapsed = (dt.now() - startTime).seconds
        
        cfg.log("WDSII Complete. Elapsed time "+str(elapsed)+" seconds.")
        
        return self.case, finish

      
    def score(self):
        """ Runs any scoring algorithms. Not actually used/tested. Don't assume it does anything. """
        
        self.cfg.log("Starting scoring")
        
        if not self.spm.listen:
            self.spm.startListener()
            
        q = self.spm.getQ()
        
        try:
        
            q.put((wds.w2scoreclusters, (self.buildOutput('simulator', overDir=self.case.gridDir)+'/index.xml', self.case.baseDir+'/scoreET', self.cfg.shed+self.cfg.shedAlt, self.case.productVars['et']), {'dataRange':(35, 50), 'targetRange':(8, 15), 'size':15, 'search':(25, 0, 3), 'timeDiff':int(float(self.cfg.gridTime)/2)}, 'scoreET'))
            
            q.put('waitAll')
            self.spm.waitForRelease()
            
            q.put((wds.makeindex, (self.case.baseDir+'/scoreET'), {}, 'scoreETind'))
            q.put('waitAll')
            self.spm.waitForRelease()
            
            q.put((wds.w2table2csv, (self.case.baseDir+'/scoreET/index.xml', self.case.baseDir+'/scoreET/error', self.cfg.shed+'AlignmentErrorTable'), {'units':True, 'header':True}, 'scoreETtable'))
            q.put('waitAll')
            self.spm.waitForRelease()
            
            
        except KeyboardInterrupt:
            self.cfg.log("KeyboardInterrupt, killing scores")
            
            q.put(err.StopProcessingException())
            self.spm.stopListener()
            
            raise
            
        except Exception as E:
            self.cfg.log("Exception occured in scores")
            
            raise
            
        self.spm.stopListener()
        
        self.cfg.log("Scoring Complete")
        
        return

    #The actual TTRAP algorithm
    def ttrap(self, cases=None):

        #Pull the VCPs out of the AliasedVelocity files
        self.case.getVCPs(self.cfg)
        
        ana = analysis.Analysis(self.cfg, self.case)
        
        try:
            #Get the frames that have beeen analyzed 
            stormGroups = ana.runPreliminaryAnalysis(self.cfg, self.case)
        except err.NoModelDataFound:
            raise
        except err.NoReferenceClusterFoundException:
            raise
            
        if not stormGroups:
            self.cfg.error("No return from prelim analysis, skipping!")
            return None
        
        if self.cfg.combine:
            ana.runAfterAnalysis(self.cfg, cases)
        else:
            self.cfg.log("Skipping after analysis!")
        
        self.cfg.log("TTRAP Complete!!")
        
        
        return stormGroups
        
        
