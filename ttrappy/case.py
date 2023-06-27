#Justin Spotts
#Module for hodling case class and method definitions

from datetime import datetime as dt
from datetime import timedelta as td
from ttrappy import ttraprad as rad
import pytz
import os
import pickle
import netCDF4 as nc
	
def loadCases(cfg):

	cfg.log("Creating Cases")

	fi = open(cfg.caseFile, 'r')
	cases = []
	
	header = True
	for line in fi:		
	
		if not header and not line.startswith('#'):
			cases.append(Case(cfg, line))
	
		else:
			header = False

	fi.close()

	return cases


class Case():

    """ Class that holds general information about each individual case for archived cases """



    
    def __init__(self, cfg, fileLine): 



        self.ID = None #ID for the case 
        self.storm = None
        self.year = None
        self.month = None
        self.day = None
        self.hour = None
        self.minute = None
        self.dateTime = None #Datetime object for the case
        self.startTime = None
        self.endTime = None
        self.startLat = None #Latitude where TCTOR begins or Non-Tor warning issuance
        self.startLon = None #Longitude where TCTOR begins or Non-Tor warning issuance
        self.stopLat = None #Latitude where TCTOR ends. Same as startLat for Non-Tor
        self.stopLon = None #Longitude where TCTOR ends. Same as startLon for Non-Tor
        self.topLat = None #North latitude of the domain
        self.topLon = None #West longtiude of the domain
        self.botLat = None #South latitude of the domain
        self.botLon = None #Eastern longitude of the domain
        self.isTor = None
        self.cwa = None #County Warning Area
        self.warning = None #Warning number, if any, associated with the case
        self.sites = [] #List of radar objects to be used in order of closest to furthest
        self.siteNames = []
        self.siteNum = None #Number of sites
        self.distances = [] #List of distances of the nearest radars in order of closest to furthest
        self.hasTDS = None #True if there is a TDS
        self.eFRating = None #F/EF rating if one exists
        self.warningClass = None #Whether the warning is a false alarm (0), hit (1), or miss (2)

        #Define the self contained directories for each case
        self.radDir = None #Directory to L2 radar data
        self.dataDir = None #Directory for processed L2 data
        self.simDir = None #Directory for simulated data
        self.baseDir = None #The base directoies
        self.saveDir = None #Directory to save final output to
        self.clusterDir = None #Directory to save cluster table info to
        self.btrtDir = None #Directory to place the BTRT output
        self.rapDir = None #Directory to place rap files
        self.rapConvDir = None #Directory to place converted rap files
        self.nseDir = None #Directory to place cropped converted rap files
        self.tmpDir = None #Dir to place raw files
        self.reportDir = None #Directory to place reports in
        self.reportTableDir = None #Directory to place converted report to
        self.hailTruthDir = None #Directory to place where the HailTruth csv files are

        #Define product directories for analysis and plotting
        self.refDir = None #Directory for gridded reflectivity data
        self.ref0Dir = None #Directory for single-tilt reflectivity. Due to naming schemes, this can differ from refDir
        self.refTableDir = None #Directory for reflectivity watershed output tables
        self.shearDir = None #Directory for gridded azimuthal shear products
        self.shearTableDir = None #Directory for shear watershed output tables
        self.shearShedDir = None #Diriectory for gridded shear watershed output
        self.refShedDir = None #Directory for gridded reflectivity shed data
        self.velDir = None #Directory for gridded velocity data
        self.vilDir = None #Directory for gridded VIL data
        self.vilTableDir = None #Directory for VIL watershed output tables
        self.vilShedDir = None #Directory for gridded VIL watershed data
        self.etDir = None #Directory for gridded echo top data
        self.clusterTableDir = None
        self.CCDir = None
        self.TDSDir = None
        self.maxShearClusterDir = None
        self.maxShearClusterTableDir = None
        self.minShearClusterDir = None
        self.minShearClusterTableDir = None
        self.ETClusterDir = None
        self.ETClusterTableDir = None
        self.zdrDir = None
        self.swDir = None
        self.logDir = None
        self.radarVCPs = []

        self.dirs = [] #Just a list of all processing directories. Used to check files in folder(s)
        self.hasDir = {} #Dictionary that contains booleans if the directory exists
        self.productVars = {} #Dictionary that contains the variable names of the output products
        self.productDirs = {} #Dictionary that contains the above product directories

        stormGroups = None #The processed frames after running the analysis
    
        splitLine = fileLine.rstrip('\n').split(',')

        self.ID = splitLine[0]
        self.storm = splitLine[1]
        self.year = int(splitLine[2])
        self.month = int(splitLine[3])
        self.day = int(splitLine[4])
        if len(splitLine[5]) < 3:
            self.hour = 0
            self.minute = int(splitLine[5])
        elif len(splitLine[5]) == 3:
            self.hour = int(splitLine[5][0])
            self.minute = int(splitLine[5][1:3])
        elif len(splitLine[5]) == 4:
            self.hour = int(splitLine[5][0:2])
            self.minute = int(splitLine[5][2:4])
        else:
            cfg.log.error(f"Something went wrong with the minute on {self.ID}")

        self.dateTime = cfg.utc.localize(dt(self.year, self.month, self.day, hour=self.hour, minute=self.minute))
        self.startTime = self.dateTime - cfg.radarStart
        self.endTime = self.dateTime + cfg.radarEnd
        self.startLat = float(splitLine[6])
        self.startLon = float(splitLine[7])
        self.stopLat = float(splitLine[8])
        self.stopLon = float(splitLine[9])
        self.isTor = bool(int(splitLine[10]))
        self.eFRating = int(splitLine[11])
        self.warningClass = int(splitLine[12])

        #Use warning start for Non-Tor and Tor midpoint for Tor
        start = self.dateTime - cfg.radarStart
        end = self.dateTime + cfg.radarEnd
        
        #Commented this out because methodology now uses the start point for TORS
        # if self.isTor:
            # midLat = (self.startLat+self.stopLat)/2
            # midLon = (self.startLon+self.stopLon)/2
            # self.sites, self.distances, self.siteNames = rad.findNearestRadars(cfg, midLat, midLon, cfg.numRadars, start, end)

            # self.topLat = round(midLat+float(cfg.latOffset), 2)
            # self.botLat = round(midLat-float(cfg.latOffset), 2)
            # self.topLon = round(midLon-float(cfg.lonOffset), 2)
            # self.botLon = round(midLon+float(cfg.lonOffset), 2)

        # if not self.isTor:
        self.sites, self.distances, self.siteNames = rad.findNearestRadars(cfg, self.startLat, self.startLon, cfg.numRadars, start, end)
        
        self.topLat = round(self.startLat+float(cfg.latOffset), 2)
        self.botLat = round(self.startLat-float(cfg.latOffset), 2)
        self.topLon = round(self.startLon-float(cfg.lonOffset), 2)
        self.botLon = round(self.startLon+float(cfg.lonOffset), 2)

        if cfg.overrideID:
            self.ID = cfg.overrideID
            
            
        self.updateDirs(cfg)
        
        self.hasDir = { 'ref':False, 'ref0':False,'reftable':False, 'refshed':False, 'shear':False, \
            'velocity':False, 'vil':False, 'vilshed':False, 'viltable':False, 'et':False, 'motion':False, 'cluster':False, 'clustertable':False, 'cc':False, 'tds':False, 'hailtruth':False,\
            'maxShearCluster':False, 'minShearCluster':False, 'ETCluster':False, 'maxShearClusterTable':False, 'minShearClusterTable':False, 'ETClusterTable':False, 'Zdr':False, 'SpectrumWidth':False}
        self.productVars = {'ref':'', 'ref0':'', 'shear':'', 'velocity':'', 'vil':'', 'vilshed':'', 'et':'', 'motione':'', 'motions':'', 'cluster':'', 'cc':'', 'tds':'', 'hailtruth':'',\
                            'maxShearCluster':'', 'minShearCluster':'', 'ETCluster':'', 'Zdr':'', 'SpectrumWidth':''}
        
        if cfg.archiveDir:
            self.radDir = archiveDir
            
        self.TIMESBYALT = []
        
        self.sitesNum = len(self.sites)
            
        cfg.log("Created case "+str(self.ID)+" "+str(vars(self))+"\n\n")
        
        return
    
    def updateDirs(self, cfg):
        
        self.baseDir = cfg.baseDir+"/"+self.storm+"/"+cfg.caseDir+"/"+self.ID
        self.logDir = os.path.join(self.baseDir, 'logs')
        self.radDir = str(self.baseDir+"/"+cfg.radarDir)
        self.dataDir = str(self.baseDir+"/"+cfg.dataDir)
        self.simDir = str(self.baseDir+"/"+cfg.simDir)
        self.saveDir = str(self.baseDir+"/"+cfg.saveDir)
        self.clusterDir = str(self.baseDir+'/'+cfg.clusterDir)
        self.rapDir = os.path.join(self.baseDir, cfg.rapDir)
        self.rapConvDir = os.path.join(self.baseDir, cfg.convertedRapDir)
        self.nseDir = os.path.join(self.baseDir, cfg.nseDir)
        self.btrtDir = os.path.join(self.dataDir, 'ClusterBT')
        self.reportDir = os.path.join(self.baseDir, 'Reports')
        self.reportTableDir = os.path.join(self.dataDir)
        self.hailTruthDir = os.path.join(self.dataDir, 'ClusterTruthCSV')
        self.tmpDir = os.path.join(self.baseDir, 'tmp')
        
        #Append directories to directory list (except save dir)
        tempDir = []
        tempDir.append(self.radDir)
        tempDir.append(self.dataDir)
        tempDir.append(self.simDir)
        tempDir.append(self.tmpDir)
        tempDir.append(self.rapDir)
        tempDir.append(self.rapConvDir)
        tempDir.append(self.nseDir)
        tempDir.append(self.tmpDir)
        tempDir.append(self.reportDir)
        tempDir.append(self.btrtDir)
        tempDir.append(self.logDir)
        
        self.dirs = tempDir
        
        #Define the output products dictionaries
        self.productDirs = {'ref':self.refDir, 'reftable':self.refTableDir, 'refshed':self.refShedDir, 'shear':self.shearDir, 'velocity':self.velDir, 'vil':self.vilDir,\
            'vilshed':self.vilShedDir, 'viltable':self.vilTableDir, 'et':self.etDir, 'cluster':self.clusterDir, 'clustertable':self.clusterTableDir, 'cc':self.CCDir, 'tds':self.TDSDir, 'hailtruth':self.hailTruthDir,\
            'maxShearCluster':self.maxShearClusterDir, 'maxShearClusterTable':self.maxShearClusterTableDir,\
            'minShearCluster':self.minShearClusterDir, 'minShearClusterTable':self.minShearClusterTableDir,\
            'ETCluster':self.ETClusterDir, 'ETClusterTableDir':self.ETClusterTableDir, 'Zdr':self.zdrDir, 'SpectrumWidth':self.swDir}
            
        return
    
    def createReport(self, dummy=False):
        """ Create a report and a dummy report for the case. 
            The dummy report is necessary as the w2csv2table eats the most recent one for some reason
        """
        dateTime = self.dateTime
        #dateTime = dt(year=1970, month=1, day=1, hour=0, minute=0, second=0)
        
        #If we are creating the dummy report, add 1 minute to the time to differentiate the files
        if dummy:
            dateTime += td(seconds=60)
            
        with open(os.path.join(self.reportDir, 'Reports_'+dateTime.strftime('%Y%m%d-%H%M%S')+'.csv'), 'w') as reportFile:
            
            #1 Write the header
            reportFile.write('Latitude(Degrees),Longitude(Degrees),Height,Epoch(seconds),RowName\n')
            #Write the info
            reportFile.write(str(self.startLat)+','+str(self.startLon)+',0,'+str(int(dateTime.timestamp()))+',0\n')
        
        #Create a dummy report if we are not already creating one
        if not dummy:
            self.createReport(dummy=True)
        
        return
    
    def getVCPs(self, cfg):
        """ After ingesting the L2 data into netcdf format. Gather the VCPs and their durations from each radar using the AliasedVelocity files """
        
        
        #Do this for each radar
        for site in self.sites:
        
            #First, we want to sort the files by time so that the duration between them can be properly calculated
            targetDir = os.path.join(self.dataDir, site.name, 'AliasedVelocity', cfg.tiltList[0])
            file_list = filter(lambda x: os.path.isfile(os.path.join(targetDir, x)), os.listdir(targetDir))
            
            sortedFiles = sorted(file_list, key = lambda x: os.path.getmtime(os.path.join(targetDir, x)))
            
            cfg.log("Checking files "+str(sortedFiles)+" in case "+str(self.ID)+" for VCPs")
            
            vcps = {}
            for a in range(len(sortedFiles)-1):
            
                currentDataset = nc.Dataset(os.path.join(targetDir, sortedFiles[a]))
                currentVCP = str(int(float(currentDataset.getncattr('vcp-value'))))
                
                nextDataset = nc.Dataset(os.path.join(targetDir, sortedFiles[a+1]))
                nextVCP = str(int(float(nextDataset.getncattr('vcp-value'))))
                
                #Close the datasets because we no longer need them
                currentDataset.close()
                nextDataset.close()
                
                #Get the time difference between the two files
                file1DT = dt.strptime(sortedFiles[a], '%Y%m%d-%H%M%S.netcdf')
                file2DT = dt.strptime(sortedFiles[a+1], '%Y%m%d-%H%M%S.netcdf')
                
                #Now the duration between them
                duration = abs((file2DT - file1DT).total_seconds())
                
                cfg.log("VCP "+str(currentVCP)+" duration chunk "+str(duration))
                
                if currentVCP in list(vcps.keys()):
                    vcps[currentVCP] += duration
                else:
                    vcps[currentVCP] = duration 
                
                if a == len(sortedFiles) - 2:
                    
                    if currentVCP != nextVCP:
                        
                        if nextVCP in list(vcps.keys()):
                            vcps[nextVCP] += 0
                        else:
                            vcps[nextVCP] = 0
                            
            self.radarVCPs.append(vcps)
            
        return
                        
                
    def setDateTime(self, newDateTime):
        self.dateTime = newDateTime
        return
        
    def updateSite(self, newSite):
    
        for a in range(len(self.sites)):
            if self.sites[a].name == newSite.name:
                self.sites[a] = newSite
                break
        return

    def updateOutputDir(self, dirVar, dir):
        """ dirVar is the variable representing that directory e.g. 'ref', 'sheartable', 'vilshed', etc. 
            dir is a string represeting directory itself """
        
        try:
            self.productDirs[dirVar] = dir
            self.hasDir[dirVar] = True
        except KeyError:
            cfg.log('Key not found in updateOutputDir\n'+str(KeyError))
            raise KeyError
        return
        
    def updateProductVar(self, dirVar, product):
        self.productVars[dirVar] = product
        return
        
    def getKeys(self):
        """ Returns a list of keys for hasDir,productVars,saveDirs """
        return self.hasDir.keys(), self.productVars.keys(), self.saveDirs
        
    def setStormGroups(self, groups):
        self.stormGroups = groups
        return
   
    def checkVars(self, cfg,  dir, varFile):
        """ Check to see if the vars exist in dir. If they do, load them and return True. If not, return false """
        fiPath = os.path.join(dir, varFile)
        fileExists = os.path.exists(fiPath)
        if fileExists:
            cfg.log('Loading Vars')
            with open(fiPath, 'rb') as f:
                self.hasDir, self.productVars, self.productDirs = pickle.load(f)
            return fileExists
        else:
            cfg.log('Var File '+fiPath+' not found')
            return fileExists
        return fileExists
        
    def saveVars(self, cfg, dir, varFile):
        cfg.log("Saving vars")
        fiPath = os.path.join(dir, varFile)
        with open(fiPath, 'wb') as f:
            pickle.dump([self.hasDir, self.productVars, self.productDirs], f)
        return
        
