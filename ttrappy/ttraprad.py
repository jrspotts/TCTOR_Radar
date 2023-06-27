#Module containing functions related to individual radars

import xml.etree.ElementTree as ET
from ttrappy import distance

import nexradaws

#Sort radars by distance
def sortRadars(sites, distances, names):

    zippedSites = list(sorted(zip(distances, sites, names)))
    sortedSites = [site for _,site,_ in zippedSites]
    sortedDistances = [dist for dist,_,_ in zippedSites]
    sortedNames = [name for _,_,name in zippedSites]
    
    return sortedSites, sortedDistances, sortedNames

def findNearestRadars(cfg, lat, lon, num, start, end):

    """ Returns the nearest num radars to a lattiude and longitude. 
        radars radarNameList"""

    tree = ET.parse(cfg.radarinfo)
    root = tree.getroot()

    sites = []
    closestDistances = []
    distances = [] 
    radars = []

    for radar in root:
        
        #Make sure the radar is a WSR-88D
        if (radar.get('name')[0] == 'K' and radar.get('freqband') == "S"):
            location = radar.find('location')
            radars.append(Radar(radar.get('name'), location.get('lat'), location.get('lon'), location.get('ht')))
            distances.append(distance.calculateDistance(float(location.get('lat')), float(location.get('lon')), float(lat), float(lon)))

    radarsCopy = radars

    conn = nexradaws.NexradAwsInterface()
    sitesNames = []
    appendedSites = 0 #Count the number of sites we've found
    while appendedSites < num:
                
        minDist = min(distances)
        ind = distances.index(minDist)
        
        #Ping AWS to see if the radar exists
        try:
            fileObjects = conn.get_avail_scans_in_range(start, end, radars[ind].name)
        except TypeError as E:
            cfg.error("Radar "+str(radars[ind].name)+' did not appear in AWS (TypeError was raised). Trying the next nearest radar')
            distances.remove(minDist)#Remove the closest radar from the list of distances
            radarsCopy.remove(radars[ind])
        else:
            closestDistances.append(minDist)
            sites.append(radars[ind])
            sitesNames.append(radars[ind].name)
            cfg.log("Appended radar "+str(radars[ind].name)+" at distance "+str(minDist)+ ' km')
            distances.remove(minDist)#Remove the closest radar from the list of distances
            radarsCopy.remove(radars[ind])
            appendedSites += 1
          
  
  
    sortedSites, sortedDistances, sortedNames = sortRadars(sites, closestDistances, sitesNames)
    closestSite = sortedSites[0]
    closestSite.setIsClosest(True)
    sortedSites[0] = closestSite #Make sure the closest radar site knows it's the closest
    
    return sortedSites, sortedDistances, sortedNames			


#Creates a list of radar objects
def getRadarSites(cfg, radarNameList):

    """ Returns Rad objects for the radar sites specified in the name list """

    cfg.log.info("Getting "+str(radarNameList))
    tree = ET.parse(cfg.radarinfo)
    root = tree.getroot()

    sites = []
    distances = []
    radars = []
    lats = []
    lons = []
    siteNames = []
    for radar in root:

        if (radar.get('name') in radarNameList):
            location = radar.find('location')
            radars.append(Radar(radar.get('name'), location.get('lat'), location.get('lon'), location.get('ht')))
            lats.append(float(location.get('lat')))
            lons.append(float(location.get('lon')))
            siteNames.append(radar.get('name'))
            
            
    midLat = sum(lats)/len(lats)
    midLon = sum(lons)/len(lons)
    
    for radar2 in radars:     
        distances.append(distance.calculateDistance(float(radar2.lat), float(radar2.lon), midLat, midLon))
        
    for currentSite in radarNameList:
            if currentSite not in siteNames:
                cfg.log.warning(currentSite+" not included (getRadarSites)!!!")
    
    sortedSites, sortedDistances, _ = sortRadars(radars, distances, siteNames)
    
    return sortedSites, sortedDistances, midLat, midLon
    
    
    

class Radar():


    def __init__(self, name, lat, lon, hgt):

        self.name = name
        self.lat = lat
        self.lon = lon
        self.hgt = hgt
        self.latestScan = None
        self.firstScan = None
        self.active = False #Radar is active when it has new L2 data to process
        self.knownScans = []
        self.distance = None
        self.hasData = False
        self.isClosest = False

    def getLatestScan(self):
        return self.latestScan
    def getScans(self):
        return self.knownScans
    def setLatestScan(self, scan):
        self.latestScan = scan
        self.knownScans.append(scan)
        return
    def setFirstScan(self, scan):
        self.firstScan = scan
        return
    def getFirstScan(self):
        return self.firstScan
    def activate(self):
        self.active = True
        return
    def deactivate(self):
        self.active = False
        return
    def setHasData(self, hasData):
        self.hasData = hasData
        return
    def setIsClosest(self, value):
        self.isClosest = value
    def getIsClosest(self):
        return self.isClosest

