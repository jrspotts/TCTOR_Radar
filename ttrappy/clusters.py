#Contains classes for the different clusters and cluster grtoups
#Justin Spotts 3-1-2022

from datetime import datetime
import math
from ttrappy import distance
from ttrappy import error as err

class StormGroup():
    

    def __init__(self, cfg, sg, tc, et, ID):
        """ Contains the clusters and related data for each 0.5 deg sweep. 
            
            This class contains all of the information regarding a particular 0.5 deg (or lowest) sweep. 
            The class is made of individual clusters that represent an area of AzShear, storm, or Echo-Top maximum.
            These clusters are represented by the ShearGroup, TrackCluster, and EchoTopCluster classes respectively.
            The StormBuilder class receives individual time objects and contains the methods to sort through and retrieve the
            individual clusters.
            
            Constructor:
            
            cfg (Config): The configuartion object for this particular 
            sg (ShearGroup): The ShearGroup determined by the StormBuilder
            tc (TrackCluster): The TrackCluster determined by the StormBuilder None if a properly matching TrackCluster is not found).
            et (EchoTopCluster): The EchoTopCluster determined by the StormBuilder (None if a properly matching ET cluster is not found).
            
            Attributes:
            
            shearGroup (ShearGroup): The group of shear clusters for this particular storm group
            trackCluster (TrackCluster): The track cluster (VIL or COMPREF) for this particular storm group
            ETCluster (EchoTopCluster): The cluster that represents the local maximum of echo tops 
            DT (datetime): The datetime of the StormGroup. Typically the same as the 0.5 deg shear cluster.
            
            
            Methods:
            
            getShearGroup(): Returns the StormGroup's ShearGroup
            getTrackCluster(): Returns the StormGroup's TrackCluster
            getETCluster(): Returns the StormGroup's EchoTopCluster
            getDT(): Returns the StormGroup's datetime object
            
        """
        
        self.__shearGroup = sg
        self.__trackCluster = tc
        self.__ETCluster = et
        self.__ID = ID
        
        #Set the StromGroup's datetime to that of the ShearGroup's lowest tilt
        self.DT = self.__shearGroup.getCluster(cfg.tiltList[0]).getDT()
        
        return
        
    def getShearGroup(self):
        return self.__shearGroup
    def getTrackCluster(self):
        return self.__trackCluster
    def getETCluster(self):
        return self.__ETCluster
    def getDT(self):
        return self.__DT
    def getID(self):
        return self.__ID
        
        
class ShearGroup():
    

    
    def __init__(self, cfg, ID):
        """ Class to the lowest shear cluster and any associated shear clusters above it.
            
            This class acts as a container for shear clusters that are associated with each other.
            The clusters are assigned via the StormBuilder class. Each time a cluster is added,
            a the centroid and latest time of the group are updated.
            
            Attributes:
            clusters (dictionary): The clusters for this group sorted by tilt
            centerLatitude (float): The average centroid latitude of all tilts
            centerLongitude (float): The average centroid longitude of all tilts
            latestLatitude (float): The latitude of the centroid of the cluster of the highest tilt in the group
            latestLongitude (float): The longitude of the centroid of the cluster of the highest tilt in the group
            latestTime (datetime): The datetime of the cluster for the highest tilt in the group
            firstTime (datetime): The datetime of the cluster for the lowest tilt in the group
            cfg (Config): TTRAPpy Config object
            ID (string): An identification for this string consiting of the case_n where n is the group number
            nClusters (int): The number of clusters in a group
            isMissing (dictionary): Holds a boolean for each tilt if the tilt was missing. Used later to differentiate missing data from not tilt available.
            
            Methods:
            getCluster(tilt): Returns the ShearCluster for the given tilt
            setCluster(cluster, tilt): Sets the cluster for the given tilt to the cluster argument. Then calls
                                       self.calculateCentroids() and self.calculateTimes()
            calculateCentroids(): Calculates the average centroid of all clusters in the group. Updates the centroid
                                  of the top (latest) cluster
            calculateTimes(): Updates the firstTime and latestTime for the group
            getCentroids(): Returns a tuple consisting of the average latitude and longitude of all clusters
            getCenterLat(): Returns only the average latitude of all cluster centroids
            getCenterLon(): Returns only the average longitude of all cluster centroids
            getLatestCentroid(): Returns a tuple consisting of the latitude and longitude of the centroid of the top cluster
            getLatestLat(): Returns only the latitude of the top cluster's centroid
            getLatestLon(): Returns only the longitude of the top cluster's centroid
            getLatestTime(): Returns the group's latestTime
            getFirstTime(): Returns the group's firstTime
            
        """
        
        
        self.cfg = cfg
        self.ID = ID
        self.firstTime = self.cfg.utc.localize(datetime(year=9999, month=1, day=1, minute=0, second=0))
        self.latestTime = self.cfg.utc.localize(datetime(year=1, month=1, day=1, minute=0, second=0))
        self.__clusters = {}
        self.__isMissing = {}
        
        self.centerLatitude = None
        self.centerLongitude = None
        self.latestLatitude = None
        self.latestLongitude = None
        self.lowestLatitude = None
        self.lowestLongitude = None
        self.lowestIndex = 99999
        self.nClusters = None
        return

    def getClusterDictionary(self):
        return self.__clusters
    def getNClusters(self):
        return self.nClusters
    def getID(self):
        return self.ID
    def getCluster(self, tilt):
        return self.__clusters[tilt]
    def setCluster(self, cluster, tilt):
    
        self.__clusters[tilt] = cluster
        
        self.cfg.error("Set tilt "+tilt+" for shear group "+str(self.ID)+" to "+str(cluster)+" in "+str(self))
        
        if self.cfg.tiltList.index(tilt) < self.lowestIndex:
            self.lowestIndex = self.cfg.tiltList.index(tilt)
            self.lowestLongitude = cluster.getLongitude()[0]
            self.lowestLatitude = cluster.getLatitude()[0]
        
        #Update the group's centroids 
        self.calculateCentroids()
        
        #Update the group's times
        self.calculateTimes()
        
        #Update nClusters
        n = 0
        for tilt in self.cfg.tiltList:
        
            try:
                if self.__clusters[tilt]:
                    n += 1
            except KeyError:
                pass
                
        self.nClusters = n
        return
        
    def setIsMissing(self, value, tilt):
        self.__isMissing[tilt] = value
        self.cfg.log("Set tilt "+str(tilt)+" to "+str(value))
        return
        
    def getIsMissing(self, tilt):
        return self.__isMissing[tilt]
        
    def calculateCentroids(self):
    
        #Determine the average latitude and longitude of all tilts
        
        latTotal = 0
        lonTotal = 0
        
        nClusters = 0
        #Loop through each cluster and add their latitudes and longitudes together
        for cluster in self.__clusters.values():
            
            #Make sure a valid tilt exists
            if cluster:
                latTotal += cluster.getLatitude()[0]
                lonTotal += cluster.getLongitude()[0]
                nClusters += 1
        
        #Calculate the centroids
        self.centerLatitude = latTotal / nClusters
        self.centerLongitude = lonTotal / nClusters
        
        latestCluster = list(self.__clusters.values())[-1]
        
        #Update the latest cluster only if it's a valid cluster
        if latestCluster:
            self.latestLatitude = latestCluster.getLatitude()[0]
            self.latestLongitude = latestCluster.getLongitude()[0]
        
        return
        
    def calculateTimes(self):
        
        #Determine if any of the cluster necessitate a change then
        #apply the change.
        
        for cluster in self.__clusters.values():
            
            if cluster:
                if cluster.getDT() < self.firstTime:
                    self.firstTime = cluster.getDT()
                    #self.cfg.error("firstTime "+str(self.firstTime))
                    
                if cluster.getDT() > self.latestTime:
                    self.latestTime = cluster.getDT()

        return
                
    def getCentroids(self):        
        return self.centerLatitude, self.centerLongitude
    def getCenterLat(self):
        return self.centerLatitude
    def getCenterLon(self):
        return self.centerLongitude
    def getLatestCentroid(self):
        return self.latestLatitude, self.latestLongitude
    def getLatestLat(self):
        return self.latestLatitude
    def getLatestLon(self):
        return self.latestLongitude
    def getLatestTime(self):
        return self.latestTime
    def getFirstTime(self):
        return self.firstTime
    def getLowestLat(self):
        return self.lowestLatitude
    def getLowestLon(self):
        return self.lowestLongitude
        
        
class TrackCluster():

    def __init__(self, cfg, case, clusterList, clusterHeaderList, fileName):

        #Here, we will go through the expected data we get from the cluster file and assign them to attributes
        #The format is index of the desired data from the clusterHeader and get that data from the clusterLine
        
        self.__cfg = cfg
        self.__case = case
        
        self.__reportDT = None
        self.__reportTD = None
        self.__reportTDSeconds = None
        self.__type = 'track'
        
        #We'll start by defining the labels for each variable
        
        self.__ageLabel = 'Age(s)'
        self.__latRadiusLabel = 'LatRadius(km)'
        self.__latitudeLabel = 'Latitude(Degrees)'
        self.__lonRadiusLabel = 'LonRadius(km)'
        self.__longitudeLabel = 'Longitude(Degrees)'
        self.__eastMotionLabel = 'MotionEast(MetersPerSecond)'
        self.__southMotionLabel = 'MotionSouth(MetersPerSecond)'
        self.__oldTrackLabel = 'OldTrack'
        self.__orientationLabel = 'Orientation(degrees)'
        self.__IDLabel = 'RowName'
        self.__sizeLabel = 'Size(km2)'
        self.__speedLabel = 'Speed(MetersPerSecond)'
        self.__startTimeLabel = 'StartTime'
        self.__maxREFLabel = 'maxREF(dBZ)'
        self.__maxVILLabel = 'maxVIL(kg/m^2)'
        self.__avgVILLabel = 'avgVIL(kg/m^2)'
        self.__u10kmWindLabel = 'u10kmWind(m/s)'
        self.__v10kmWindLabel = 'v10kmWind(m/s)'
        self.__u6kmMeanWindLabel = 'u6kmMeanWind(m/s)'
        self.__v6kmMeanWindLabel = 'v6kmMeanWind(m/s)'
        self.__10kmRelativeWindDirectionLabel = '10kmRelativeWindDirection(deg)'
        self.__u10kmRelativeWindLabel = 'u10kmRelativeWind(m/s)'
        self.__v10kmRelativeWindLabel = 'v10kmRelativeWind(m/s)'
        self.__uShearLabel = 'uShear(m/s)'
        self.__vShearLabel = 'vShear(m/s)'
        self.__potentialClustersLabel = 'potentialClusters(unitless)'
        
        
        #Next, we'll get the actual values
        self.__DT = cfg.utc.localize(datetime.strptime(fileName[-19:-4], '%Y%m%d-%H%M%S'))
        self.__age = float(clusterList[clusterHeaderList.index(self.__ageLabel)])
        self.__latRadius = float(clusterList[clusterHeaderList.index(self.__latRadiusLabel)])
        self.__latitude = float(clusterList[clusterHeaderList.index(self.__latitudeLabel)])
        self.__lonRadius = float(clusterList[clusterHeaderList.index(self.__lonRadiusLabel)])
        self.__longitude = float(clusterList[clusterHeaderList.index(self.__longitudeLabel)])
        self.__eastMotion = float(clusterList[clusterHeaderList.index(self.__eastMotionLabel)])
        self.__southMotion = float(clusterList[clusterHeaderList.index(self.__southMotionLabel)])
        self.__oldTrack = clusterList[clusterHeaderList.index(self.__oldTrackLabel)]
        self.__orientnation = float(clusterList[clusterHeaderList.index(self.__orientationLabel)])
        self.__ID = clusterList[clusterHeaderList.index(self.__IDLabel)]
        self.__size = float(clusterList[clusterHeaderList.index(self.__sizeLabel)])
        self.__speed = float(clusterList[clusterHeaderList.index(self.__speedLabel)])
        self.__startTime = clusterList[clusterHeaderList.index(self.__startTimeLabel)]
        self.__orientation = clusterList[clusterHeaderList.index(self.__orientationLabel)]
        self.__u10kmWind = float(clusterList[clusterHeaderList.index(self.__u10kmWindLabel)])
        self.__v10kmWind = float(clusterList[clusterHeaderList.index(self.__v10kmWindLabel)])
        self.__u6kmMeanWind = float(clusterList[clusterHeaderList.index(self.__u6kmMeanWindLabel)])
        self.__v6kmMeanWind = float(clusterList[clusterHeaderList.index(self.__v6kmMeanWindLabel)])
        self.__uShear = float(clusterList[clusterHeaderList.index(self.__uShearLabel)])
        self.__vShear = float(clusterList[clusterHeaderList.index(self.__vShearLabel)])
        
        self.__potentialClusters = None
        
        self.__u10kmRelativeWind = self.__u10kmWind - self.__u6kmMeanWind
        self.__v10kmRelativeWind = self.__v10kmWind - self.__v6kmMeanWind
        
        self.__10kmRelativeWindDirection = math.degrees(math.atan2(self.__u10kmRelativeWind, self.__v10kmRelativeWind))
        if self.__10kmRelativeWindDirection < 0:
            self.__10kmRelativeWindDirection += 360
            
            
        self.__shearDirection = math.degrees(math.atan2(self.__uShear, self.__vShear))
        if self.__shearDirection < 0:
            self.__shearDirection += 360
        
        self.__groundRanges = [distance.calculateDistance(float(case.sites[a].lat), float(case.sites[a].lon), float(self.__latitude), float(self.__longitude))*1000 for a in range(len(case.sites))] #Convert to meters
        self.__slantRanges = [distance.calculateSlantRange(float(case.sites[a].hgt), distance.R, self.__groundRanges[a]) for a in range(len(case.sites))]
        
      
        self.__maxVIL = clusterList[clusterHeaderList.index(self.__maxVILLabel)]
        self.__avgVIL = clusterList[clusterHeaderList.index(self.__avgVILLabel)]
        self.__maxREF = clusterList[clusterHeaderList.index(self.__maxREFLabel)]
        
        


        
        return
        
    @staticmethod
    def getHeaderList(case):
    
        """ Returns the header list when other options aren't working. Important to remember to update this method when changing the header in the preliminary .csv file """
        trackLabel = '(Track)'
        return ['RowName', 'DateTime'+trackLabel,'Bin(minutes)'+trackLabel,'BinNumber'+trackLabel,'Timedelta(Seconds)'+trackLabel, 'Latitude(Degrees)'+trackLabel, 'Longitude(Degrees)'+trackLabel]+\
                              ['LatRadius(km)'+trackLabel, 'LonRadius(km)'+trackLabel, 'Orientation(degrees)'+trackLabel, ['GroundRange '+str(a)+' (n mi)'+trackLabel for a in range(len(case.sites))]]+\
                              ['Size(km2)'+trackLabel, 'MotionEast(MetersPerSecond)'+trackLabel, 'MotionSouth(MetersPerSecond)'+trackLabel,'Speed(MetersPerSecond)'+trackLabel, 'avgVIL(kg/m^2)', 'maxVIL(kg/m^2)', 'maxREF(dBZ)', 'u6kmMeanWind(m/s)', 'v6kmMeanWind(m/s)',\
                              'uShear(m/s)', 'vShear(m/s)', 'potentialClusters(unitless)']
    def getDT(self):
        return self.__DT
    def getAge(self):
        return (self.__age, self.__ageLabel)
    
    def getLatRadius(self):
        return (self.__latRadius, self.__latRadiusLabel)
    def getLatitude(self):
        return (self.__latitude, self.__latitudeLabel)
    def getLonRadius(self):
        return (self.__lonRadius, self.__lonRadiusLabel)
    def getLongitude(self):
        return (self.__longitude, self.__longitudeLabel)
    def getEastMotion(self):
        return (self.__eastMotion, self.__eastMotionLabel)
    def getSouthMotion(self):
        return (self.__southMotion, self.__southMotionLabel)
    def getOldTrack(self):
        return (self.__oldTrack, self.__oldTrackLabel)
    def getOrientation(self):
        return (self.__orientation, self.__orientationLabel)
    def getID(self):
        return (self.__ID, self.__IDLabel)
    def getSize(self):
        return (self.__size, self.__sizeLabel)
    def getSpeed(self):
        return (self.__speed, self.__speedLabel)
    def getStartTime(self):
        return (self.__startTime, self.__startTimeLabel)
    def getAvgVIL(self):
        return (self.__avgVIL, self.__avgVILLabel)
   
    def getMaxREF(self):
        return (self.__maxREF, self.__maxREFLabel)
    def getMaxVIL(self):
        return (self.__maxVIL, self.__maxVILLabel)
    def getu10kmWind(self):
        return (self.__u10kmWind, self.__u10kmWindLabel)
    def getv10kmWind(self):
        return (self.__v10kmWind, self.__v10kmWindLabel)
    def get10kmRelativeWindDirection(self):
        return (self.__10kmRelativeWindDirection, self.__10kmRelativeWindDirectionLabel)
    def getu10kmRelativeWind(self):
        return (self.__u10kmRelativeWind, self.__u10kmRelativeWindLabel)
    def getv10kmRelativeWind(self):
        return (self.__v10kmRelativeWind, self.__v10kmRelativeWindLabel)
    def getu6kmMeanWind(self):
        return (self.__u6kmMeanWind, self.__u6kmMeanWind)
    def getv6kmMeanWind(self):
        return (self.__v6kmMeanWind, self.__v6kmMeanWind)
        
    def getuShear(self):
        return (self.__uShear, self.__uShearLabel)
    def getvShear(self):
        return (self.__vShear, self.__vShearLabel)
    def getShearDirection(self):
        return self.__shearDirection

    
    def setReportTD(self, reportDT):
    
        self.__reportDT = reportDT
        if self.__DT >= reportDT:
            self.__reportTD = self.__DT - reportDT #Subtract the report time from self to get time relative to report
            reportTDMinutes = self.__reportTD.seconds/60
            self.__reportTDSeconds = self.__reportTD.seconds
        else:
            self.__reportTD = reportDT - self.__DT
            reportTDMinutes = -self.__reportTD.seconds/60
            self.__reportTDSeconds = -self.__reportTD.seconds
        
        self.__binNumber = round(reportTDMinutes/self.__cfg.timeBinIncrement)
        self.__bin = self.__binNumber * self.__cfg.timeBinIncrement
        return
        
    def getReportTD(self):
        return self.__reportTD
        
    def getBinNumber(self):
        return self.__binNumber
    def getBin(self):
        return self.__bin
    def getReportTDSeconds(self):
        return self.__reportTDSeconds
    def getReportDT(self):
        return self.__reportDT
    
    def getGroundRange(self, siteNum):
        return self.__groundRanges[siteNum]
    def getSlantRange(self, siteNum):
        return self.__slantRanges[siteNum]
        
    def getType(self):
        return self.__type
    def setPotentialClusterCount(self, value):
        self.__potentialClusters = value
        return
    def getPotentialClusterCount(self):
        return (self.__potentialClusters, self.__potentialClustersLabel)
        
        
class ShearCluster():

    def __init__(self, cfg, case, DT, clusterList, clusterHeaderList, tilt, fileName, hailTruthList=None, hailTruthHeaderList=None):

        #Here, we will go through the expected data we get from the cluster file and assign them to attributes
        #The format is index of the desired data from the clusterHeader and get that data from the clusterLine
        
        self.__cfg = cfg
        self.__case = case
        self.__reportDT = None
        self.__reportTD = None
        self.__reportTDSeconds = None
        self.__tilt = tilt
        self.__beamHeights = []
        self.__type = 'shear'
        
        #We'll start by defining the labels for each variable
        
        self.__ageLabel = 'Age(s)'
        self.__cellNameLabel = 'CellName'
        self.__distToCellLabel = 'DistToCell(kilometers)'
        self.__epochLabel = 'Epoch(seconds)'
        self.__latRadiusLabel = 'LatRadius(km)'
        self.__latitudeLabel = 'Latitude(Degrees)'
        self.__lonRadiusLabel = 'LonRadius(km)'
        self.__longitudeLabel = 'Longitude(Degrees)'
        self.__eastMotionLabel = 'MotionEast(MetersPerSecond)'
        self.__southMotionLabel = 'MotionSouth(MetersPerSecond)'
        self.__numReportsLabel = 'NumReports'
        self.__oldTrackLabel = 'OldTrack'
        self.__orientationLabel = 'Orientation(degrees)'
        self.__IDLabel = 'RowName'
        self.__sizeLabel = 'Size(km2)'
        self.__speedLabel = 'Speed(MetersPerSecond)'
        self.__startTimeLabel = 'StartTime'
        self.__timeToCellLabel = 'TimeToCell(seconds)'
        self.__TDSCountLabel = 'TDScount'
        self.__TDSminLabel = 'TDSmin'
        self.__maxReflectivityLabel = 'maxRefTDS(dBZ)'
        self.__maxShearLabel = 'maxShear(s^-1)'
        self.__minRhoHVLabel = 'minRhoHV'
        self.__minShearLabel = 'minShear(s^-1)'
        self.__minZdrLabel = 'minZdrTDS(dB)'
        self.__bottom10ShearLabel = '10thShear(s^-1)'
        self.__top90ShearLabel = '90thShear(s^-1)'
        self.__uShearLabel = 'uShear(m/s)'
        self.__vShearLabel = 'vShear(m/s)'
        self.__areaVrotLabel = 'AreaVrot(kts)'
        self.__motionDirectionLabel = 'motionDirection(deg)'
        self.__vLonLabel = 'lonMotion(deg/s)'
        self.__vLatLabel = 'latMotion(deg/s)'
        self.__absShearLabel = 'absShear(s^-1)'
        self.__maxSpectrumWidthLabel = 'maxSpectrumWidth(m/s)'
        self.__u6kmMeanWindLabel = 'u6kmMeanWind(m/s)'
        self.__v6kmMeanWindLabel = 'v6kmMeanWind(m/s)'
        self.__clusterULabel = 'clusterU(m/s)'
        self.__clusterVLabel = 'clusterV(m/s)'
        self.__forwardProjectedLatLabel = 'forwardLat(deg)'
        self.__forwardProjectedLonLabel = 'forwardLon(deg)'
        self.__backProjectedLatLabel = 'backLat(deg)'
        self.__backProjectedLonLabel  = 'backLon(deg)'
        self.__potentialClustersLabel = 'potentialClusters(unitless)'
        
        #Next, we'll get the actual values
        self.__DT = cfg.utc.localize(datetime.strptime(DT, '%Y%m%d-%H%M%S'))
        self.__age = float(clusterList[clusterHeaderList.index(self.__ageLabel)])
        self.__latRadius = float(clusterList[clusterHeaderList.index(self.__latRadiusLabel)])
        self.__latitude = float(clusterList[clusterHeaderList.index(self.__latitudeLabel)])
        self.__lonRadius = float(clusterList[clusterHeaderList.index(self.__lonRadiusLabel)])
        self.__longitude = float(clusterList[clusterHeaderList.index(self.__longitudeLabel)])
        self.__eastMotion = float(clusterList[clusterHeaderList.index(self.__eastMotionLabel)])
        self.__southMotion = float(clusterList[clusterHeaderList.index(self.__southMotionLabel)])
        self.__oldTrack = clusterList[clusterHeaderList.index(self.__oldTrackLabel)]
        self.__orientnation = float(clusterList[clusterHeaderList.index(self.__orientationLabel)])
        self.__ID = clusterList[clusterHeaderList.index(self.__IDLabel)]
        self.__size = float(clusterList[clusterHeaderList.index(self.__sizeLabel)])
        self.__speed = float(clusterList[clusterHeaderList.index(self.__speedLabel)])
        self.__startTime = clusterList[clusterHeaderList.index(self.__startTimeLabel)]
        self.__TDSCount = float(clusterList[clusterHeaderList.index(self.__TDSCountLabel)])
        self.__TDSmin = float(clusterList[clusterHeaderList.index(self.__TDSminLabel)])
        self.__maxReflectivity = float(clusterList[clusterHeaderList.index(self.__maxReflectivityLabel)])
        self.__maxShear = float(clusterList[clusterHeaderList.index(self.__maxShearLabel)])
        self.__minRhoHV = float(clusterList[clusterHeaderList.index(self.__minRhoHVLabel)])
        self.__minShear = float(clusterList[clusterHeaderList.index(self.__minShearLabel)])
        self.__minZdr = float(clusterList[clusterHeaderList.index(self.__minZdrLabel)])
        self.__bottom10Shear = float(clusterList[clusterHeaderList.index(self.__bottom10ShearLabel)])
        self.__top90Shear = float(clusterList[clusterHeaderList.index(self.__top90ShearLabel)])
        self.__uShear = float(clusterList[clusterHeaderList.index(self.__uShearLabel)])
        self.__vShear = float(clusterList[clusterHeaderList.index(self.__vShearLabel)])
        self.__maxSpectrumWidth = float(clusterList[clusterHeaderList.index(self.__maxSpectrumWidthLabel)])
        self.__orientation = float(clusterList[clusterHeaderList.index(self.__orientationLabel)])
        self.__u6kmMeanWind = float(clusterList[clusterHeaderList.index(self.__u6kmMeanWindLabel)])
        self.__v6kmMeanWind = float(clusterList[clusterHeaderList.index(self.__v6kmMeanWindLabel)])
        
        self.__potentialClusters = None
        self.__forwardProjectedLat = -99900
        self.__forwardProjectedLon = -99900
        self.__backProjectedLat = -99900
        self.__backProjectedLon = -99900
        
        self.__isDefaultMotion = True
        self.__motionDirection = math.degrees(math.atan2(self.__u6kmMeanWind, self.__v6kmMeanWind))
        if self.__motionDirection < 0:
            self.__motionDirection += 360
        self.__vLat = None
        self.__vLon = None
        self.__clusterU = self.__u6kmMeanWind
        self.__clusterV = self.__v6kmMeanWind
        self.__absShear = None
        
        self.__shearDirection = math.degrees(math.atan2(self.__uShear, self.__vShear))
        if self.__shearDirection < 0:
            self.__shearDirection += 360
        
        self.__groundRanges = [distance.calculateDistance(float(case.sites[a].lat), float(case.sites[a].lon), float(self.__latitude), float(self.__longitude))*1000 for a in range(len(case.sites))] #Convert to meters
        self.__slantRanges = [distance.calculateSlantRange(float(case.sites[a].hgt), distance.R, self.__groundRanges[a]) for a in range(len(case.sites))]
        
        for a in range(len(case.sites)):
            self.__beamHeights.append(distance.calculateBeamHeightIter(self.__groundRanges[a], float(tilt), distance.R*(4/3))*3.28) #Convert to feet
        
        self.__radarBearings = []
        for a in range(len(case.sites)):
            bearing = distance.calculateBearingAT(float(case.sites[a].lat), float(case.sites[a].lon), float(self.__latitude), float(self.__longitude))
            if bearing < 0:
                bearing += 360
            self.__radarBearings.append(bearing)
            
        #Next, we'll assign everything that is in the hailtruth tables
        if hailTruthList:
            self.__cellName = hailTruthList[hailTruthHeaderList.index(self.__cellNameLabel)]
            self.__distToCell = hailTruthList[hailTruthHeaderList.index(self.__distToCellLabel)]
            if len(self.__distToCell.split(' ')) > 1: #Fix for weird instance where 2 distances are appended to the same attribute by hailtruth
                self.__distToCell = self.__distToCell.split(' ')[0]
            self.__epoch = hailTruthList[hailTruthHeaderList.index(self.__epochLabel)]
            self.__numReports = hailTruthList[hailTruthHeaderList.index(self.__numReportsLabel)]
            self.__timeToCell = hailTruthList[hailTruthHeaderList.index(self.__timeToCellLabel)]
            
            if self.__cellName != self.__ID:
                cfg.error("Warning! CellName and ID mismatch "+str(self.__cellName)+' '+str(self.__ID))
        else:
            self.__cellName = None
            self.__distToCell = None
            self.__epoch = None
            self.__numReports = None
            self.__timeToCell = None
         
        self.__isReference = False
        
        self.calculateAreaVrot()
        

        return
        
        
    def getDT(self):
        return self.__DT
    def getAge(self):
        return (self.__age, self.__ageLabel)
    def getCellName(self):
        return (self.__cellName, self.__cellNameLabel)
    def getDistToCell(self):
        return (self.__distToCell, self.__distToCellLabel)
    def getEpoch(self):
        return (self.__epoch, self.__epochLabel)
    def getLatRadius(self):
        return (self.__latRadius, self.__latRadiusLabel)
    def getLatitude(self):
        return (self.__latitude, self.__latitudeLabel)
    def getLonRadius(self):
        return (self.__lonRadius, self.__lonRadiusLabel)
    def getLongitude(self):
        return (self.__longitude, self.__longitudeLabel)
    def getEastMotion(self):
        return (self.__eastMotion, self.__eastMotionLabel)
    def getSouthMotion(self):
        return (self.__southMotion, self.__southMotionLabel)
    def getNumReports(self):
        return (self.__numReports, self.__numReportsLabel)
    def getOldTrack(self):
        return (self.__oldTrack, self.__oldTrackLabel)
    def getOrientation(self):
        return (self.__orientation, self.__orientationLabel)
    def getID(self):
        return (self.__ID, self.__IDLabel)
    def getSize(self):
        return (self.__size, self.__sizeLabel)
    def getSpeed(self):
        return (self.__speed, self.__speedLabel)
    def getStartTime(self):
        return (self.__startTime, self.__startTimeLabel)
    def getTimeToCell(self):
        return (self.__timeToCell, self.__timeToCellLabel)
    def getBottom10Shear(self):
        return (self.__bottom10Shear, self.__bottom10ShearLabel)
    def getTop90Shear(self):
        return (self.__top90Shear, self.__top90ShearLabel)
    def getTDSCount(self):
        return (self.__TDSCount, self.__TDSCountLabel)
    def getTDSMin(self):
        return (self.__TDSmin, self.__TDSminLabel)
    def getMaxReflectivity(self):
        return (self.__maxReflectivity, self.__maxReflectivityLabel)
    def getMaxShear(self):
        return (self.__maxShear, self.__maxShearLabel)
    def getMinRhoHV(self):
        return (self.__minRhoHV, self.__minRhoHVLabel)
    def getMinShear(self):
        return (self.__minShear, self.__minShearLabel)
    def getMinZdr(self):
        return (self.__minZdr, self.__minZdrLabel)
    def getuShear(self):
        return (self.__uShear, self.__uShearLabel)
    def getvShear(self):
        return (self.__vShear, self.__vShearLabel)
    def getShearDirection(self):
        return self.__shearDirection
    def setMotionDirection(self, direction):
        self.__isDefaultMotion = False
        self.__motionDirection = direction
        self.__cfg.log("Set motion for "+str(self.__ID)+" "+str(self.__motionDirection))
        return
    def getMotionDirection(self):
        return (self.__motionDirection, self.__motionDirectionLabel)
    def setVLat(self, vLat):
        self.__vLat = vLat
        return
    def setVLon(self, vLon):
        self.__vLon = vLon
        return
    def getVLat(self):
        return (self.__vLat, self.__vLatLabel)
    def getVLon(self):
        return (self.__vLon, self.__vLonLabel)
    def getAbsShear(self):
        return (self.__absShear, self.__absShearLabel)
    def getMaxSpectrumWidth(self):
        return (self.__maxSpectrumWidth, self.__maxSpectrumWidthLabel)
    def getu6kmMeanWind(self):
        return (self.__u6kmMeanWind, self.__u6kmMeanWind)
    def getv6kmMeanWind(self):
        return (self.__v6kmMeanWind, self.__v6kmMeanWind)
    def isDefaultMotion(self):
        """ Is the motion vector for the cluster from the 0-6km mean wind (default) or from other clusters """
        
        return self.isDefaultMotion
    
    def setReportTD(self, reportDT):
    
        self.__reportDT = reportDT
        if self.__DT >= reportDT:
            self.__reportTD = self.__DT - reportDT #Subtract the report time from self to get time relative to report
            reportTDMinutes = self.__reportTD.seconds/60
            self.__reportTDSeconds = self.__reportTD.seconds
        else:
            self.__reportTD = reportDT - self.__DT
            reportTDMinutes = -self.__reportTD.seconds/60
            self.__reportTDSeconds = -self.__reportTD.seconds
        
        self.__binNumber = round(reportTDMinutes/self.__cfg.timeBinIncrement)
        self.__bin = self.__binNumber * self.__cfg.timeBinIncrement
        return
        
    def getReportTD(self):
        return self.__reportTD
        
    def getBinNumber(self):
        return self.__binNumber
    def getBin(self):
        return self.__bin
    def getReportTDSeconds(self):
        return self.__reportTDSeconds
    def getReportDT(self):
        return self.__reportDT
        
        
    def getGroundRange(self, siteNum):
        return self.__groundRanges[siteNum]
    def getSlantRange(self, siteNum):
        return self.__slantRanges[siteNum]
    def getBeamHeight(self, siteNum):
        return self.__beamHeights[siteNum]
    def getRadarBearing(self, siteNum):
        return self.__radarBearings[siteNum]
        
    def calculateAreaVrot(self):
        """ Calculates Vrot from AzShear assuming a radius from a circle with an area equal to that of the clusters."""
        
        #Solve for the radius of the circle
        r = math.sqrt(self.__size/math.pi)*1000 #Convert from km to m
        
        azShear = None
        
        #Set the AzShear used in the calclation to the absolute value of whichever is greatest
        if abs(self.__maxShear) >= abs(self.__minShear):
            azShear = abs(self.__maxShear)
        elif abs(self.__minShear) > abs(self.__maxShear):
            azShear = abs(self.__minShear)
            
        self.__absShear = azShear
        
        #Calculate the Vrot using the relation in Mahalik et al. (2019)
        self.__areaVrot = (azShear * r) * 1.94384 #Convert from meters/second to knots
        
        return
        
    def getAreaVrot(self):
        return (self.__areaVrot, self.__areaVrotLabel)
    def isReference(self):
        return self.__isReference
    def setIsReference(self, value):
        self.__isReference = value
        return
    def getType(self):
        return self.__type
    def setClusterU(self, value):
        self.__clusterU = value
    def setClusterV(self, value):
        self.__clusterV = value
    def getClusterU(self):
        return (self.__clusterU, self.__clusterULabel)
    def getClusterV(self):
        return (self.__clusterV, self.__clusterVLabel)
    def projectCluster(self, timeStep):
        
        """ Projects a cluster forwards or backward in time based of the current motion vector and timeStep.
            The timeStep is the number of seconds to advect the cluster. The projection is done fowards and backwards
            using the timeStep provided.
            
            From 1 test the projections may be off by a few 3 to 5 thousandths of a degree.
            """
            

        #Step 1, calculate the total distance change expected for each component.
        self.__cfg.log("Projecting cluster "+str(self.__ID)+" using timestep "+str(timeStep)+" seconds.")
        du1 = self.__clusterU * timeStep
        dv1 = self.__clusterV * timeStep
        du2 = self.__clusterU * -timeStep
        dv2 = self.__clusterV * -timeStep
        
        #Step 2, calcualte the bearing and distance. The distances along the projection where the point is placed
        #is multiplied by the ProjectFraction variable in the configuration file.
        
        d1 = (math.sqrt(du1**2 + dv1**2) * self.__cfg.projectFraction)/1000 #Convert to km
        bearing1 = math.degrees(math.atan2(du1, dv1))
        
        d2 = (math.sqrt(du2**2 + dv2**2) * self.__cfg.projectFraction)/1000 #Convert to km
        bearing2 = math.degrees(math.atan2(du2, dv2))
        
        if bearing1 < 0:
            bearing1 += 360
        
        if bearing2 < 0:
            bearing2 += 360
            

        #Project forwards
        self.__forwardProjectedLat, self.__forwardProjectedLon = distance.calculateDestination(self.__latitude, self.__longitude, bearing1, d1)
        
        #Project backwards
        self.__backProjectedLat, self.__backProjectedLon = distance.calculateDestination(self.__latitude, self.__longitude, bearing2, d2)
            
        self.__cfg.log("New Projections forward lat: "+str(self.__forwardProjectedLat)+" lon: "+str(self.__forwardProjectedLon)+\
                    "\nbackward lat: "+str(self.__backProjectedLat)+" backward lon: "+str(self.__backProjectedLon)+\
                    "\nfrom modified d1 bearing1 modified d2 bearing2: "+str(d1)+" "+str(bearing1)+" "+str(d2)+" "+str(bearing2)+\
                    "\nfrom du1 dv1 du2 dv2: "+str(du1)+" "+str(dv1)+" "+str(du2)+" "+str(dv2))
        return
        
    def getClusterProjection(self, timeStep):
        """ This method is similar to project cluster, except it returns a projection of this cluster using the provided time step """
        self.__cfg.log("Getting cluster projection of "+str(self.__ID)+" using timestep "+str(timeStep)+" seconds.")
        
        du = self.__clusterU * timeStep
        dv = self.__clusterV * timeStep
        
        d = (math.sqrt(du**2 + dv**2) * self.__cfg.projectFraction)/1000 #Convert to km
        bearing = math.degrees(math.atan2(du, dv))
        
        if bearing < 0:
            bearing += 360
            
        projLat, projLon = distance.calculateDestination(self.__latitude, self.__longitude, bearing, d)
        
        self.__cfg.log("New Projections  lat: "+str(projLat)+" forward lon: "+str(projLon)+\
                    "\nfrom modified d bearing : "+str(d)+" "+str(bearing)+\
                    "\nfrom du dv: "+str(du)+" "+str(dv))
                    
        return projLat, projLon
        
    def getForwardLat(self):
        return (self.__forwardProjectedLat, self.__forwardProjectedLatLabel)
    def getForwardLon(self):
        return (self.__forwardProjectedLon, self.__forwardProjectedLonLabel)
    def getBackwardLat(self):
        return (self.__backProjectedLat, self.__backProjectedLatLabel)
    def getBackwardLon(self):
        return (self.__backProjectedLon, self.__backProjectedLonLabel)
    def setForwardProj(self, lat, lon):
        self.__forwardProjectedLat = lat
        self.__forwardProjectedLon = lon
        return
        
    def setPotentialClusterCount(self, value):
        self.__potentialClusters = value
        return 
    def getPotentialClusterCount(self):
        if self.__potentialClusters:
            return (self.__potentialClusters, self.__potentialClustersLabel)
        else:
            return (-99900, self.__potentialClustersLabel)
        
class EchoTopCluster():

    def __init__(self, cfg, case, clusterList, clusterHeaderList, fileName):

        #Here, we will go through the expected data we get from the cluster file and assign them to attributes
        #The format is index of the desired data from the clusterHeader and get that data from the clusterLine
        
        self.__cfg = cfg
        self.__case = case
        self.__reportDT = None
        self.__reportTD = None
        self.__reportTDSeconds = None
        self.__type = 'echotop'
       
        
        #We'll start by defining the labels for each variable
        
        self.__ageLabel = 'Age(s)'
        self.__latRadiusLabel = 'LatRadius(km)'
        self.__latitudeLabel = 'Latitude(Degrees)'
        self.__lonRadiusLabel = 'LonRadius(km)'
        self.__longitudeLabel = 'Longitude(Degrees)'
        self.__eastMotionLabel = 'MotionEast(MetersPerSecond)'
        self.__southMotionLabel = 'MotionSouth(MetersPerSecond)'
        self.__numReportsLabel = 'NumReports'
        self.__oldTrackLabel = 'OldTrack'
        self.__orientationLabel = 'Orientation(degrees)'
        self.__IDLabel = 'RowName'
        self.__sizeLabel = 'Size(km2)'
        self.__speedLabel = 'Speed(MetersPerSecond)'
        self.__startTimeLabel = 'StartTime'
        self.__timeToCellLabel = 'TimeToCell(seconds)'
        self.__maxETLabel = 'maxET(km)'
        self.__top90ETLabel = '90thET(km)'
        self.__potentialClustersLabel = 'potentialClusters(unitless)'

        
        
        #Next, we'll get the actual values
        self.__DT = cfg.utc.localize(datetime.strptime(fileName[-19:-4], '%Y%m%d-%H%M%S'))
        self.__age = float(clusterList[clusterHeaderList.index(self.__ageLabel)])
        self.__latRadius = float(clusterList[clusterHeaderList.index(self.__latRadiusLabel)])
        self.__latitude = float(clusterList[clusterHeaderList.index(self.__latitudeLabel)])
        self.__lonRadius = float(clusterList[clusterHeaderList.index(self.__lonRadiusLabel)])
        self.__longitude = float(clusterList[clusterHeaderList.index(self.__longitudeLabel)])
        self.__eastMotion = float(clusterList[clusterHeaderList.index(self.__eastMotionLabel)])
        self.__southMotion = float(clusterList[clusterHeaderList.index(self.__southMotionLabel)])
        self.__oldTrack = clusterList[clusterHeaderList.index(self.__oldTrackLabel)]
        self.__orientation = float(clusterList[clusterHeaderList.index(self.__orientationLabel)])
        self.__ID = clusterList[clusterHeaderList.index(self.__IDLabel)]
        self.__size = float(clusterList[clusterHeaderList.index(self.__sizeLabel)])
        self.__speed = float(clusterList[clusterHeaderList.index(self.__speedLabel)])
        self.__startTime = clusterList[clusterHeaderList.index(self.__startTimeLabel)]
        self.__orientatation = clusterList[clusterHeaderList.index(self.__orientationLabel)]
        
        self.__groundRanges = [distance.calculateDistance(float(case.sites[a].lat), float(case.sites[a].lon), float(self.__latitude), float(self.__longitude))*1000 for a in range(len(case.sites))] #Convert to meters
        self.__slantRanges = [distance.calculateSlantRange(float(case.sites[a].hgt), distance.R, self.__groundRanges[a]) for a in range(len(case.sites))]
        
        self.__potentialClusters = None
        
        #For the variables at multiple altitudes or tilts, we want to create lists of their values and column names        
        self.__maxET = clusterList[clusterHeaderList.index(self.__maxETLabel)]
        
        #If the maxET is missing, set the converted ET to missing
        if self.__maxET == -99900:
            self.__maxETFeet = -99900.00
        else:
            self.__maxETFeet = float(self.__maxET) * 3280.84 #Convert km to Feet
        
        self.__top90ET = float(clusterList[clusterHeaderList.index(self.__top90ETLabel)])
        
        
        #Same thing with the top 90 ET
        if self.__top90ET == -99900:
            self.__top90ETFeet = -99900.00
        else:
            self.__top90ETFeet = self.__top90ET * 3280.84 #Convert km to Feet
        
        return
        
    @staticmethod
    def getHeaderList(case):
    
        etLabel = '(ET)'
        
        return ['RowName'+etLabel, 'DateTime'+etLabel,'Bin(minutes)'+etLabel,'BinNumber'+etLabel,'Timedelta(Seconds)'+etLabel, 'Latitude(Degrees)'+etLabel, 'Longitude(Degrees)'+etLabel]+\
                           ['LatRadius(km)'+etLabel, 'LonRadius(km)'+etLabel, 'Orientation(degrees)'+etLabel, ['GroundRange '+str(a)+' (n mi)'+etLabel for a in range(len(case.sites))]]+\
                           ['Size(km2)'+etLabel, 'MotionEast(MetersPerSecond)'+etLabel, 'MotionSouth(MetersPerSecond)'+etLabel, 'Speed(MetersPerSecond)'+etLabel, 'maxET(km)', 'maxET(ft)', '90thET(km)', '90thET(ft)', 'potentialClusters(unitless)']
    def getDT(self):
        return self.__DT
    def getAge(self):
        return (self.__age, self.__ageLabel)
    def getLatRadius(self):
        return (self.__latRadius, self.__latRadiusLabel)
    def getLatitude(self):
        return (self.__latitude, self.__latitudeLabel)
    def getLonRadius(self):
        return (self.__lonRadius, self.__lonRadiusLabel)
    def getLongitude(self):
        return (self.__longitude, self.__longitudeLabel)
    def getEastMotion(self):
        return (self.__eastMotion, self.__eastMotionLabel)
    def getSouthMotion(self):
        return (self.__southMotion, self.__southMotionLabel)
    def getOldTrack(self):
        return (self.__oldTrack, self.__oldTrackLabel)
    def getOrientation(self):
        return (self.__orientation, self.__orientationLabel)
    def getID(self):
        return (self.__ID, self.__IDLabel)
    def getSize(self):
        return (self.__size, self.__sizeLabel)
    def getSpeed(self):
        return (self.__speed, self.__speedLabel)
    def getStartTime(self):
        return (self.__startTime, self.__startTimeLabel)
    def getMaxET(self):
        return (self.__maxET, self.__maxETLabel)
    def getMaxETFeet(self):
        return (self.__maxETFeet, 'maxET(ft)')
    def getTop90ET(self):
        return (self.__top90ET, self.__top90ETLabel)
    def getTop90ETFeet(self):
        return (self.__top90ETFeet, '90thET(ft)')
    
    def setReportTD(self, reportDT):
    
        self.__reportDT = reportDT
        if self.__DT >= reportDT:
            self.__reportTD = self.__DT - reportDT #Subtract the report time from self to get time relative to report
            reportTDMinutes = self.__reportTD.seconds/60
            self.__reportTDSeconds = self.__reportTD.seconds
        else:
            self.__reportTD = reportDT - self.__DT
            reportTDMinutes = -self.__reportTD.seconds/60
            self.__reportTDSeconds = -self.__reportTD.seconds
        
        self.__binNumber = round(reportTDMinutes/self.__cfg.timeBinIncrement)
        self.__bin = self.__binNumber * self.__cfg.timeBinIncrement
        return
    def getReportTD(self):
        return self.__reportTD
        
    def getBinNumber(self):
        return self.__binNumber
    def getBin(self):
        return self.__bin
    def getReportTDSeconds(self):
        return self.__reportTDSeconds
    def getReportDT(self):
        return self.__reportDT

    def getGroundRange(self, siteNum):
        return self.__groundRanges[siteNum]
    def getSlantRange(self, siteNum):
        return self.__slantRanges[siteNum]
    def getEchoTop(self):
        return self.__type
        
    def setPotentialClusterCount(self, value):
        self.__potentialClusters = value
        return
    def getPotentialClusterCount(self):
        return (self.__potentialClusters, self.__potentialClustersLabel)
