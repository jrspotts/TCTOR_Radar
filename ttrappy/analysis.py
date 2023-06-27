#This module contains function and class definitions for analysis of WDSII data 

from datetime import datetime
from datetime import timedelta
from netCDF4 import Dataset
import os
import math
from ttrappy import distance
from ttrappy import ttrappy as ttr
from ttrappy import visualize
from ttrappy import clusters as clu
from ttrappy import stormbuilder as sb
from ttrappy import error as err
import sys
import pickle

#Holds all information relevant to the time in quesiton, the time is set by the cluster, this is because other fields tend to update faster.
class Time():
	
    def __init__(self, DT, maxShearClusters, minShearClusters, trackClusters, ETClusters):
        self.__DT = DT
        self.__maxShearClusters = maxShearClusters
        self.__minShearClusters = minShearClusters
        self.__trackClusters = trackClusters
        self.__etClusters = ETClusters

        # print("Created time "+str(DT)+" with max DT "+str(maxShearClusters['00.50'][0].getDT())+" min DT "+str(minShearClusters['00.50'][0].getDT()))
        
        if trackClusters:
            print("track DT "+str(trackClusters[0].getDT()))
        if ETClusters:
            print("ET DT "+str(ETClusters[0].getDT()))
        return
        
    def getMaxShearClusters(self, tilt):
        return self.__maxShearClusters[tilt]
    def getMinShearClusters(self, tilt):
        return self.__minShearClusters[tilt]
    def getTrackClusters(self):
        return self.__trackClusters
    def getETClusters(self):
        return self.__etClusters
    def getDT(self):
        return self.__DT

#This function determines which file in a string of files is closest in time to the given time string
def getClosestTime(baseTime, files, UNIVDT='2'):


    #Split the base time into its individual elements
    string1 = baseTime
    year1 = int(string1[0:4])
    month1 = int(string1[4:6])
    day1 = int(string1[6:8])
    hour1 = int(string1[9:11])
    minute1 = int(string1[11:13])
    second1 = int(string1[13:15])
    dt1 = datetime(year1, month1, day1, hour1, minute1, second1)

    closestIndex = 999999999
    closestDelta = 999999999
    count2 = 0

    #Loop through the files
    for fi in files:
        string2 = ''
        count = 0
        #Find the index of the beginning of DT string and define the DT string 
        for char in fi:
            if(char == UNIVDT):
                string2 = fi[count:count+15]
                break
            count = count + 1
        
        year2 = int(string2[0:4])
        month2 = int(string2[4:6])
        day2 = int(string2[6:8])
        hour2 = int(string2[9:11])
        minute2 = int(string2[11:13])
        second2 = int(string2[13:15])
        dt2 = datetime(year2, month2, day2, hour2, minute2, second2)

        delta = dt2 - dt1
        if(delta.seconds < closestDelta):
            closestDelta = delta.seconds
            closestIndex = count2
        #print(count2, closestIndex, delta.seconds, closestDelta, string1, string2, fi)
        count2 = count2 + 1

    return closestIndex


def readTableLines(tableFile):
    lines = []

    fi3 = open(tableFile, 'r')
    first = True
    header = []
    for line in fi3:
        if (not first):
            lines.append(line.rstrip('\n').split(','))
        else:
            first = False
            #Make sure there is no # in the beginning
            if '#' in line:
                line.replace('#', '')
            header = line.lstrip('#').rstrip('\n').split(',')
            
    fi3.close()
    return header, lines


def reorderTimes(times):
	
	orderedTimes = []
	ordered = 0
	orderedIndicies = []

	while ordered < len(times):
		
		lowestDT = datetime(9999, 1, 1, 0, 0, 0) #Pick a ridiculus time in the future
		lowestIndex = -1
		count = 0
		for currentTime in times:
			string1 = currentTime.getDT()
			year = int(string1[0:4])
			month = int(string1[4:6])
			day = int(string1[6:8])
			hour = int(string1[9:11])
			minute = int(string1[11:13])
			second = int(string1[13:15])
			dt = datetime(year, month, day, hour, minute, second)
		
			if (dt < lowestDT and (count not in orderedIndicies)):
				lowestDT = dt
				lowestIndex = count
			count = count + 1
		
		orderedTimes.append(times[lowestIndex])
		orderedIndicies.append(lowestIndex)
		ordered = ordered + 1
	
	return orderedTimes
	

class Analysis():

    def __init__(self, cfg, case):
        self.UNIVDT = str(case.dateTime.year)[0] #This is the number that indicates the start of the DT string. Change to first digit of the year in question. For example, '2' for 2xxx or '1' for 1xxx
        self.TIMES = [] #A list of lists of time objects that can be accessed from anywhere in the program. Each index is from a different altitude
        # self.statFile = case.saveDir+'_'+case.ID+'.csv'
        # self.activeFile = case.saveDir+'_'+case.ID+'_active.csv'
        

        
    def writeInterestingClusters(self, cfg, case, stormGroups):
        """ Writes the out the desired info to a .csv to be used at the end for a final analysis"""
        
        outFileName = str(case.ID)+'_prelim.csv'
        outFileFull = os.path.join(case.saveDir, outFileName)
        
        
        with open(outFileFull, 'w') as outFi:
        
            #1st write the header
            headCl = stormGroups[0].getShearGroup().getCluster(cfg.tiltList[0])
            
            tilt = cfg.tiltList[0]
            
            if float(tilt) < 1:
                modTilt = tilt.rstrip('0')
            else:
                modTilt = tilt.strip('0')
                    
            paraModTilt = '('+modTilt+'deg)'
            
            vcpNumberHeaderString = ''
            vcpDurationHeaderString = ''
            
            for a in range(len(case.radarVCPs)):
                for b in range(len(list(case.radarVCPs[a].keys()))):
                    vcpNumberHeaderString += 'VCP('+str(a)+')('+str(b)+'),'
                    
                for c in range(len(list(case.radarVCPs[a].values()))):
                    vcpDurationHeaderString += 'VCP_duration('+str(a)+')('+str(c)+'),'
                    
            vcpNumberHeaderString = vcpNumberHeaderString.rstrip(',').rstrip(',')
            vcpDurationHeaderString = vcpDurationHeaderString.rstrip(',').rstrip(',')
            
            print(vcpNumberHeaderString)
            print(vcpDurationHeaderString)
            
            lowestTiltHeaderList = ['TC','case','tor','F-EF-rating', 'class', vcpNumberHeaderString, vcpDurationHeaderString, headCl.getID()[1]+paraModTilt, 'DateTime'+paraModTilt,'Bin(minutes)'+paraModTilt,'BinNumber'+paraModTilt,'Timedelta(Seconds)'+paraModTilt, headCl.getLatitude()[1]+paraModTilt,headCl.getLongitude()[1]+paraModTilt]+\
                                  [headCl.getLatRadius()[1]+paraModTilt, headCl.getLonRadius()[1]+paraModTilt, headCl.getOrientation()[1]+paraModTilt, ['GroundRange '+str(a)+' (n mi)'+paraModTilt for a in range(len(case.sites))]]+\
                                  [headCl.getSize()[1]+paraModTilt, headCl.getEastMotion()[1]+paraModTilt, headCl.getSouthMotion()[1]+paraModTilt, headCl.getSpeed()[1]+paraModTilt, headCl.getNumReports()[1]+paraModTilt, headCl.getDistToCell()[1]+paraModTilt]+\
                                  [headCl.getMaxShear()[1]+paraModTilt, headCl.getMinShear()[1]+paraModTilt, headCl.getBottom10Shear()[1]+paraModTilt, headCl.getTop90Shear()[1]+paraModTilt, headCl.getMinZdr()[1]+paraModTilt, headCl.getMinRhoHV()[1]+paraModTilt]+\
                                  [headCl.getAreaVrot()[1]+paraModTilt, headCl.getMaxReflectivity()[1]+paraModTilt, headCl.getMaxSpectrumWidth()[1]+paraModTilt, headCl.getuShear()[1]+paraModTilt, headCl.getvShear()[1]+paraModTilt, headCl.getClusterU()[1]+paraModTilt, headCl.getClusterV()[1]+paraModTilt, headCl.getTDSCount()[1]+paraModTilt]+\
                                  [headCl.getTDSMin()[1]+paraModTilt, ['Radar Bearing '+str(a)+' ('+str(modTilt)+'deg)(degrees)' for a in range(len(case.sites))], ['BeamHeight '+str(a)+' ('+str(modTilt)+'deg)(feet)' for a in range(len(case.sites))], headCl.getForwardLat()[1]+paraModTilt, headCl.getForwardLon()[1]+paraModTilt, headCl.getBackwardLat()[1]+paraModTilt, headCl.getBackwardLon()[1]+paraModTilt, headCl.getPotentialClusterCount()[1]+paraModTilt]
                        
            headerList = lowestTiltHeaderList
            
            tiltHeaderList = []
            
            #Repeat for the rest of the tilts, but modified not to include the cluster-of-interest variables              
            for tilt in cfg.tiltList[1:len(cfg.tiltList)]:
                
                if float(tilt) < 1:
                    modTilt = tilt.rstrip('0')
                else:
                    modTilt = tilt.strip('0')
                
                paraModTilt = '('+modTilt+'deg)'
                
                tiltHeaderList = [headCl.getID()[1]+paraModTilt, 'DateTime'+paraModTilt,'Bin(minutes)'+paraModTilt,'BinNumber'+paraModTilt,'Timedelta(Seconds)'+paraModTilt, headCl.getLatitude()[1]+paraModTilt,headCl.getLongitude()[1]+paraModTilt]+\
                                  [headCl.getLatRadius()[1]+paraModTilt, headCl.getLonRadius()[1]+paraModTilt, headCl.getOrientation()[1]+paraModTilt, ['GroundRange '+str(a)+' (n mi)'+paraModTilt for a in range(len(case.sites))]]+\
                                  [headCl.getSize()[1]+paraModTilt, headCl.getEastMotion()[1]+paraModTilt, headCl.getSouthMotion()[1]+paraModTilt, headCl.getSpeed()[1]+paraModTilt]+\
                                  [headCl.getMaxShear()[1]+paraModTilt, headCl.getMinShear()[1]+paraModTilt, headCl.getBottom10Shear()[1]+paraModTilt, headCl.getTop90Shear()[1]+paraModTilt, headCl.getMinZdr()[1]+paraModTilt, headCl.getMinRhoHV()[1]+paraModTilt]+\
                                  [headCl.getAreaVrot()[1]+paraModTilt, headCl.getMaxReflectivity()[1]+paraModTilt, headCl.getMaxSpectrumWidth()[1]+paraModTilt, headCl.getuShear()[1]+paraModTilt, headCl.getvShear()[1]+paraModTilt, headCl.getClusterU()[1]+paraModTilt, headCl.getClusterV()[1]+paraModTilt, headCl.getTDSCount()[1]+paraModTilt]+\
                                  [headCl.getTDSMin()[1]+paraModTilt, ['Radar Bearing '+str(a)+' ('+str(modTilt)+'deg)(degrees)' for a in range(len(case.sites))], ['BeamHeight '+str(a)+' ('+str(modTilt)+'deg)(feet)' for a in range(len(case.sites))], headCl.getForwardLat()[1]+paraModTilt, headCl.getForwardLon()[1]+paraModTilt, headCl.getBackwardLat()[1]+paraModTilt, headCl.getBackwardLon()[1]+paraModTilt, headCl.getPotentialClusterCount()[1]+paraModTilt]
                
                headerList += tiltHeaderList
                
            #Now we write the headers for the track cluster
            
            #For the purposes of writing the header, try to get a group that has a valid TrackCluster
            headTrackCl = None
            trackHeaderList = []
            for group in stormGroups:
                headTrackCl = group.getTrackCluster()
                if headTrackCl:
                    break
                    
            if trackHeaderList:
                trackLabel = '(Track)'
                
                trackHeaderList = [headTrackCl.getID()[1]+trackLabel, 'DateTime'+trackLabel,'Bin(minutes)'+trackLabel,'BinNumber'+trackLabel,'Timedelta(Seconds)'+trackLabel, headTrackCl.getLatitude()[1]+trackLabel,headTrackCl.getLongitude()[1]+trackLabel]+\
                                  [headTrackCl.getLatRadius()[1]+trackLabel, headTrackCl.getLonRadius()[1]+trackLabel, headTrackCl.getOrientation()[1]+trackLabel, ['GroundRange '+str(a)+' (n mi)'+trackLabel for a in range(len(case.sites))]]+\
                                  [headTrackCl.getSize()[1]+trackLabel, headTrackCl.getEastMotion()[1]+trackLabel, headTrackCl.getSouthMotion()[1]+trackLabel, headTrackCl.getSpeed()[1]+trackLabel, headTrackCl.getAvgVIL()[1], headTrackCl.getMaxVIL()[1], headTrackCl.getMaxREF()[1], headTrackCl.getu6kmMeanWind()[1], headTrackCl.getv6kmMeanWind()[1],\
                                  headTrackCl.getuShear()[1], headTrackCl.getvShear()[1], headTrackCl.getPotentialClusterCount()[1]]
            else:
                cfg.error("Using Default Track Cluster")
                trackHeaderList = clu.TrackCluster.getHeaderList(case)
            
            headerList += trackHeaderList    
            
            #Now do the same for the ET Clusters
            headETCl = None
            etHeaderList = []
            
            for group in stormGroups:
                headETCl = group.getETCluster()
                if headETCl:
                    break
            
            if etHeaderList:
                etLabel = '(ET)'
                               
                etHeaderList = [headETCl.getID()[1]+etLabel, 'DateTime'+etLabel,'Bin(minutes)'+etLabel,'BinNumber'+etLabel,'Timedelta(Seconds)'+etLabel, headETCl.getLatitude()[1]+etLabel,headETCl.getLongitude()[1]+etLabel]+\
                               [headETCl.getLatRadius()[1]+etLabel, headETCl.getLonRadius()[1]+etLabel, headETCl.getOrientation()[1]+etLabel, ['GroundRange '+str(a)+' (n mi)'+etLabel for a in range(len(case.sites))]]+\
                               [headETCl.getSize()[1]+etLabel, headETCl.getEastMotion()[1]+etLabel, headETCl.getSouthMotion()[1]+etLabel, headETCl.getSpeed()[1]+etLabel, headETCl.getMaxET()[1], headETCl.getMaxETFeet()[1], headETCl.getTop90ET()[1], headETCl.getTop90ETFeet()[1], headETCl.getPotentialClusterCount()[1]]
            else:
                cfg.error("Using default ET Header")
                etHeaderList = clu.EchoTopCluster.getHeaderList(case)
                
            headerList += etHeaderList
            
            headerString = ','.join(map(str, headerList))+'\n'
            headerString = headerString.replace('#', '')
            headerString = headerString.replace('[', '').replace("'", '')
            headerString = headerString.replace(']', '')
            headerString = '#'+headerString
            outFi.write(headerString)
            
            #Now go through each storm group and write the data
            
            
            for group in stormGroups:
                
                dataList = []
                
                currentShearGroup = group.getShearGroup()
                cluster = currentShearGroup.getCluster(cfg.tiltList[0])
                
                vcpNumberString = ''
                vcpDurationString = ''
                
                for a in range(len(case.radarVCPs)):
                    for vcp in list(case.radarVCPs[a].keys()):
                        vcpNumberString += str(vcp)+','
                        
                    for duration in list(case.radarVCPs[a].values()):
                        vcpDurationString += str(duration)+','
                        
                vcpNumberString = vcpNumberString.rstrip(',').rstrip(',')
                vcpDurationString = vcpDurationString.rstrip(',').rstrip(',')
            
                #[str(b) for b in list(case.radarVCPs[a].keys()) for a in range(len(case.radarVCPs))] [b for b in list(case.radarVCPs[a].values()) for a in range(len(case.radarVCPs))],
                #cfg.error("Writing for tilt "+str(cfg.tiltList[0])+" group "+str(group)+" shear group "+str(currentShearGroup)+" and cluster "+str(cluster))
                dataList = [case.storm, case.ID, int(case.isTor), case.eFRating, case.warningClass, vcpNumberString, vcpDurationString, cluster.getID()[0], cluster.getDT().strftime('%Y%m%d-%H%M%S'), cluster.getBin(), cluster.getBinNumber(), cluster.getReportTDSeconds(), cluster.getLatitude()[0], cluster.getLongitude()[0]]+\
                           [cluster.getLatRadius()[0], cluster.getLonRadius()[0], cluster.getOrientation()[0], [cluster.getGroundRange(a)/1852 for a in range(len(case.sites))]]+[cluster.getSize()[0], cluster.getEastMotion()[0], cluster.getSouthMotion()[0], cluster.getSpeed()[0], cluster.getNumReports()[0]]+\
                           [cluster.getDistToCell()[0], cluster.getMaxShear()[0], cluster.getMinShear()[0], cluster.getBottom10Shear()[0], cluster.getTop90Shear()[0], cluster.getMinZdr()[0], cluster.getMinRhoHV()[0], cluster.getAreaVrot()[0], cluster.getMaxReflectivity()[0], cluster.getMaxSpectrumWidth()[0], cluster.getuShear()[0], cluster.getvShear()[0]]+\
                           [cluster.getClusterU()[0], cluster.getClusterV()[0], cluster.getTDSCount()[0], cluster.getTDSMin()[0], [cluster.getRadarBearing(a) for a in range(len(case.sites))], [cluster.getBeamHeight(a) for a in range(len(case.sites))], cluster.getForwardLat()[0], cluster.getForwardLon()[0], cluster.getBackwardLat()[0], cluster.getBackwardLon()[0], cluster.getPotentialClusterCount()[0]]
                
                for tilt in cfg.tiltList[1:len(cfg.tiltList)]:
                
                    cluster = currentShearGroup.getCluster(tilt)
                    #cfg.error("Writing group "+str(group)+" shear group "+str(currentShearGroup)+" cluster "+str(cluster)+" for tilt "+tilt)
                    
                    #Only attempt to write values if we have a valid cluster. Else, write missing values
                    if cluster:
                        dataList += [cluster.getID()[0], cluster.getDT().strftime('%Y%m%d-%H%M%S'), cluster.getBin(), cluster.getBinNumber(), cluster.getReportTDSeconds(), cluster.getLatitude()[0], cluster.getLongitude()[0]]+\
                                    [cluster.getLatRadius()[0], cluster.getLonRadius()[0], cluster.getOrientation()[0], [cluster.getGroundRange(a)/1852 for a in range(len(case.sites))]]+[cluster.getSize()[0], cluster.getEastMotion()[0], cluster.getSouthMotion()[0], cluster.getSpeed()[0]]+\
                                    [cluster.getMaxShear()[0], cluster.getMinShear()[0], cluster.getBottom10Shear()[0], cluster.getTop90Shear()[0], cluster.getMinZdr()[0], cluster.getMinRhoHV()[0], cluster.getAreaVrot()[0], cluster.getMaxReflectivity()[0], cluster.getMaxSpectrumWidth()[0], cluster.getuShear()[0], cluster.getvShear()[0]]+\
                                    [cluster.getClusterU()[0], cluster.getClusterV()[0], cluster.getTDSCount()[0], cluster.getTDSMin()[0], [cluster.getRadarBearing(a) for a in range(len(case.sites))], [cluster.getBeamHeight(a) for a in range(len(case.sites))], cluster.getForwardLat()[0], cluster.getForwardLon()[0], cluster.getBackwardLat()[0], cluster.getBackwardLon()[0], cluster.getPotentialClusterCount()[0]]
                    elif not cluster and not currentShearGroup.getIsMissing(tilt):
                        cfg.error(tilt+" tilt not found when constructing data list, but is not missing")
                        
                        #Write -99904 for to indicate that the tilt was present, but no cluster was found
                        dataList += [-99904] * (len(tiltHeaderList)+3)
                    else:
                        cfg.error(tilt+" tilt was not found because it was missing")
                        dataList += [-99900] * (len(tiltHeaderList)+3)
                        
                
                
                #Now add the track data
                trackCluster = group.getTrackCluster()
                
                if trackCluster:
                    dataList += [trackCluster.getID()[0], trackCluster.getDT().strftime('%Y%m%d-%H%M%S'), trackCluster.getBin(), trackCluster.getBinNumber(),  trackCluster.getReportTDSeconds(), trackCluster.getLatitude()[0],trackCluster.getLongitude()[0]]+\
                                [trackCluster.getLatRadius()[0], trackCluster.getLonRadius()[0], trackCluster.getOrientation()[0], [trackCluster.getGroundRange(a)/1852 for a in range(len(case.sites))]]+\
                                [trackCluster.getSize()[0], trackCluster.getEastMotion()[0], trackCluster.getSouthMotion()[0], trackCluster.getSpeed()[0], trackCluster.getAvgVIL()[0], trackCluster.getMaxVIL()[0], trackCluster.getMaxREF()[0], trackCluster.getu6kmMeanWind()[0], trackCluster.getv6kmMeanWind()[0],\
                                trackCluster.getuShear()[0], trackCluster.getvShear()[0], trackCluster.getPotentialClusterCount()[0]]
                else:
                    dataList += [-99900] * (len(trackHeaderList)+1)
                    
                
                #Next add the ET cluster data
                
                etCluster = group.getETCluster()
                
                if etCluster:
                
                    dataList += [etCluster.getID()[0], etCluster.getDT().strftime('%Y%m%d-%H%M%S'), etCluster.getBin(), etCluster.getBinNumber(), etCluster.getReportTDSeconds(), etCluster.getLatitude()[0],etCluster.getLongitude()[0]]+\
                                [etCluster.getLatRadius()[0], etCluster.getLonRadius()[0], etCluster.getOrientation()[0], [etCluster.getGroundRange(a)/1852 for a in range(len(case.sites))]]+\
                                [etCluster.getSize()[0], etCluster.getEastMotion()[0], etCluster.getSouthMotion()[0], etCluster.getSpeed()[0], etCluster.getMaxET()[0], etCluster.getMaxETFeet()[0], etCluster.getTop90ET()[0], etCluster.getTop90ETFeet()[0], trackCluster.getPotentialClusterCount()[0]]
                              
                else:
                    
                    dataList += [-99900] * (len(etHeaderList)+1)
                    
                dataString = ','.join(map(str, dataList))+'\n'
                dataString = dataString.replace('[', '')
                dataString = dataString.replace(']', '')
                outFi.write(dataString)
                
        
        #Finally, pickle the storm groups to be used later if needed
        with open(os.path.join(case.saveDir, 'groups.pick'), 'wb') as fi:
            pickle.dump(stormGroups, fi)
        
        return
    
    def loadETClusters(self, cfg, case, clusterFiles, clusterTableDir):
    
        clusterDTs = []
        clusters = []
        
        #First, load the max and min
        for fiS in clusterFiles:
            currentClusterFile = os.path.join(clusterTableDir, fiS)
            
            #cfg.log("Checking ET File "+currentClusterFile)
            #Find the clusterDT
            count0 = 0
            clusterDT = ''
            for char in fiS:
                if(char == self.UNIVDT):
                    clusterDT = fiS[count0:count0+15]
                    clusterDTs.append(clusterDT)
                    break
                count0 += 1
                
            #Now find the corresponding HailTruth table, if it exists
            
            try:
                clusterHeader, clusterLines = readTableLines(currentClusterFile)
            except FileNotFoundError:
                cfg.error("loadETClusters(): file not found for "+currentClusterFile)
                return False, False

            appendClusters = []
            
            for cLine in clusterLines:
                appendCluster = clu.EchoTopCluster(cfg, case, cLine, clusterHeader, fiS)
                appendCluster.setReportTD(case.dateTime) #Set the time delta of the cluster based of the time of interest from the case

                appendClusters.append(appendCluster)
                # cfg.log(str(vars(appendCluster)))
            
            clusters.append(appendClusters)
            
        #cfg.log(str(clusters))
        if clusters and clusterDTs:
            return [clusters, clusterDTs]
        
        return False, False
            
    def loadTrackClusters(self, cfg, case, clusterFiles, clusterTableDir):
    
        clusterDTs = []
        clusters = []
        
        #First, load the max and min
        for fiS in clusterFiles:
            currentClusterFile = os.path.join(clusterTableDir, fiS)
            # cfg.log("Checking track file "+currentClusterFile)
            #Find the clusterDT
            count0 = 0
            clusterDT = ''
            for char in fiS:
                if(char == self.UNIVDT):
                    clusterDT = fiS[count0:count0+15]
                    clusterDTs.append(clusterDT)
                    break
                count0 += 1
                
          
            clusterHeader, clusterLines = readTableLines(currentClusterFile)

            appendClusters = []
            
            for cLine in clusterLines:
                appendCluster = clu.TrackCluster(cfg, case, cLine, clusterHeader, fiS)
                appendCluster.setReportTD(case.dateTime) #Set the time delta of the cluster based of the time of interest from the case

                appendClusters.append(appendCluster)
                # cfg.log(str(vars(appendCluster)))
            
            clusters.append(appendClusters)
            
        #cfg.log(str(clusters))

        return [clusters, clusterDTs]
        
            
            
    def loadShearClustersTruth(self, cfg, case, clusterFiles, clusterTableDir, truthFiles, truthTableDir, tilt):

        clusterDTs = []
        clusters = []
        
        #First, load the max and min
        for fiS in clusterFiles:
            currentClusterFile = os.path.join(clusterTableDir, fiS)
            
            #Find the clusterDT
            count0 = 0
            clusterDT = ''
            for char in fiS:
                if(char == self.UNIVDT):
                    clusterDT = fiS[count0:count0+15]
                    clusterDTs.append(clusterDT)
                    break
                count0 += 1
                
            #Now find the corresponding HailTruth table, if it exists
            
            closestHTFile = ''
            for htFi in truthFiles:
                count0 = 0
                htDT = ''
                for char in htFi:
                    if(char == self.UNIVDT):
                        htDT = htFi[count0:count0+15]
                        break
                    count0 += 1
                if (visualize.getStringDT(cfg, clusterDT, htDT)[0] == 0):
                    closestHTFile = os.path.join(truthTableDir, htFi)
                    break
            
            clusterHeader, clusterLines = readTableLines(currentClusterFile)
            
            #If we actuallly found the closest file
            if closestHTFile:
                truthHeader, truthLines = readTableLines(closestHTFile)
                # cfg.error("Closest hailtruth file "+fiS+" "+closestHTFile)
            else:
                #Or else set them to none
                truthHeader = None
                truthLines = [None] * len(clusterLines)
                
            iterable = zip(clusterLines, truthLines)
            
            appendClusters = []
            
            for cLine,htLine in iterable:
                appendCluster = clu.ShearCluster(cfg, case, clusterDT, cLine, clusterHeader, tilt, fiS, hailTruthList=htLine, hailTruthHeaderList=truthHeader)
                appendCluster.setReportTD(case.dateTime) #Set the time delta of the cluster based of the time of interest from the case
             
                appendClusters.append(appendCluster)
                # cfg.log(str(vars(appendCluster)))
                
            clusters.append(appendClusters)
                
        if clusters and clusterDTs:
            return [clusters, clusterDTs]
        
        return False, False
        
            
    def loadShearClusters(self, cfg, case, clusterFiles, clusterTableDir, tilt):

        clusterDTs = []
        clusters = []
        
        #First, load the max and min
        for fiS in clusterFiles:
            currentClusterFile = os.path.join(clusterTableDir, fiS)
            
            #Find the clusterDT
            count0 = 0
            clusterDT = ''
            for char in fiS:
                if(char == self.UNIVDT):
                    clusterDT = fiS[count0:count0+15]
                    clusterDTs.append(clusterDT)
                    break
                count0 += 1

            try:
                clusterHeader, clusterLines = readTableLines(currentClusterFile)
            except FileNotFoundError:
                cfg.error("loadShearClusters(): No file found for "+currentClusterFile+". Returning None")
                return False, False
            

            appendClusters = []
            
            for cLine in clusterLines:
                appendCluster = clu.ShearCluster(cfg, case, clusterDT, cLine, clusterHeader, tilt, fiS)
                appendCluster.setReportTD(case.dateTime) #Set the time delta of the cluster based of the time of interest from the case
             
                appendClusters.append(appendCluster)
                #cfg.log(str(vars(appendCluster)))
                
            clusters.append(appendClusters)
            
        if clusters and clusterDTs:
            return [clusters, clusterDTs]
        
        return False, False
            
    def loadTime(self, cfg, DT, maxShearClusters, minShearClusters, trackClusters, ETClusters):
    
        cfg.log("Loading time "+str(DT))
        #Find the set of VIL clusters temporally.
        timeDifference = 99999999
        closestTrackClusters = None
        #cfg.error("Checking track clusters in time "+str(trackClusters))
        
        if trackClusters:
            for i,trackCluster in enumerate(trackClusters):
            
                if trackCluster:
                    currentDifference = visualize.getStringDT(cfg, DT, trackCluster[0].getDT().strftime('%Y%m%d-%H%M%S'))[0]
                    # cfg.error("Track "+str(DT)+" "+str(trackCluster[0].getDT().strftime('%Y%m%d-%H%M%S'))+" "+str(currentDifference))
                    if currentDifference < timeDifference and (currentDifference <= cfg.maxAppendTimeR*60):
                    
                        timeDifference = currentDifference
                        closestTrackClusters = trackCluster
        else:
            cfg.error("No Track Clusters Found")
            
        #Find the ET clusters at or after the VIL cluster

        timeDifference = 999999999
        closestETClusters = None
        #cfg.error("Checking ET Clusters in time "+str(ETClusters))
        
        if ETClusters and trackClusters:
            for i,etCluster in enumerate(ETClusters):
            
                if etCluster and closestTrackClusters:
                    currentDifference, greater, equal = visualize.getStringDT(cfg, closestTrackClusters[0].getDT().strftime('%Y%m%d-%H%M%S'), etCluster[0].getDT().strftime('%Y%m%d-%H%M%S'))
                    # cfg.error("ET "+str(DT)+" "+str(etCluster[0].getDT().strftime('%Y%m%d-%H%M%S'))+" "+str(currentDifference)+" "+str(greater)+" "+str(equal))

                    if currentDifference < timeDifference and (currentDifference <= cfg.maxAppendTimeR*60): #Removed (equal or greater) from this check to avoid missed ETs that were close to, but before the VIL time
                        
                        timeDifference = currentDifference
                        closestETClusters = etCluster
        else:
            cfg.error("No ET Clusters Available")
                
                
        # #If no closest ET is found. The closest remains None
        # if closestTrackClusters:
            # cfg.error("Added track "+str(closestTrackClusters[0].getDT())+" to "+str(DT))
        # if closestETClusters:
            # cfg.error("Added ET "+str(closestETClusters[0].getDT())+" to "+str(DT))
            
        return Time(DT, maxShearClusters, minShearClusters, closestTrackClusters, closestETClusters)
    
    def getClustersByDT(self, cfg, DT, clusters, isByTilt=False):
        """ Creates a list of all clusters that are in proper relation to the 0.5 deg datetime (DT).
        
            Checks every cluster's datetime (DT) relative to a datetime created from the DT string. 
            If the clusters being checked are sorted by tilt, then the clusters are added to a dictionary 
            by tilt where every elevation angle is closest time after the previous tilt. Should the clusters
            not be sorted by tilt, the cluster closest to the input DT is used.
            
            Requires:
            visualize module
            
            Parameters:
            cfg (Config Object): Configuration object from ttrapcfg/config.py
            DT (string):    Datetime string of the format %Y%m%d-%H%M%S for the 0.5 degree tilt sweep
            clusters: The clusters to be sorted
            clusterDTs (list/dictionary): DTs associated with each. Dictionary has tilt attributes.
            
            Keyword Arguments
            isByTilt (boolean): Are these clusters sorted by tilt?
            
            Returns:
            The set of clusters that are the closest to the DT
            
            OR
            
            dictionary: The dictionary of cluster sets that meet time criteria for each tilt relative to DT
        """
        
        if not clusters:
            return []
            
        targetClusterSet = {}
        
        if isByTilt:
           
            
            #Initialize the dictionary with a list for every tilt
            
            for tilt in cfg.tiltList:
                targetClusterSet[tilt] = []
                
            #Begin looping through each each tilt...
            for tilt in cfg.tiltList:
                
                closestCluster = None
                closestTimeDifference = 999999
                #cfg.log("Cluster check! "+str(tilt)+" "+str(clusters[tilt]))
                #First, determine what the closest time difference is
                if clusters[tilt]:
                    #Then loop through DT
                   
                    for cluster in clusters[tilt]:
                    
                        if cluster:
                            #Check if the clusters are the closest
                            currentDifference, greater, equal = visualize.getStringDT(cfg, DT, cluster[0].getDT().strftime('%Y%m%d-%H%M%S'))
                            
                            if currentDifference < closestTimeDifference and (greater or equal) and (currentDifference <= (cfg.maxAppendTimeV*60)):
                                
                                closestTimeDifference = currentDifference
                            
                            
                    #Repeat, but now add clusters that are less than or equal (in other words, equal) to the closeset time difference
                    
                    for cluster in clusters[tilt]:
                        
                        if cluster:
                            currentDifference, greater, equal = visualize.getStringDT(cfg, DT, cluster[0].getDT().strftime('%Y%m%d-%H%M%S'))
                            
                            if currentDifference <= closestTimeDifference and (greater or equal) and (currentDifference <= (cfg.maxAppendTimeV*60)):
                                #cfg.log("Added "+str(len(cluster))+" clusters for "+str(tilt)+" "+str(DT)+" "+cluster[0].getDT().strftime('%Y%m%d-%H%M%S')+" "+str(currentDifference)+" "+str(closestTimeDifference))
                                targetClusterSet[tilt] = cluster
                                #cfg.log("Append!")
            
                
            #cfg.log("End DT by Tilt")
                
        else:
        
            if clusters:
            
                closestCluster = None
                
                for cluster in clusters:
                
                    if cluster:
                        #Check if the clusters are the closest
                        currentDifference, greater, equal = visualize.getStringDT(cfg, DT, cluster[0].getDT().strftime('%Y%m%d-%H%M%S'))
                        
                        if currentDifference < timeDifference:
                            
                            timeDifference = currentDifference
                            closestClusters = cluster
                    
                targetClustserSet = closestCluster
            else:
                cfg.error("getClustersByDT(): No non-tilt clusters found ")
            
            #cfg.log("Not by tilt")
        return targetClusterSet
        
    def runPreliminaryAnalysis(self, cfg, case):

        cfg.log("Starting analysis for case: "+case.ID)
        
        try:

            times = []
            
            #List files for each cluster
            trackClusterDir = case.productDirs['clustertable']
            trackClusterFiles = os.listdir(trackClusterDir)
            
            maxHailTruthDir = os.path.join(case.productDirs['hailtruth'], 'maxshear')
            maxHailTruthFiles = os.listdir(maxHailTruthDir)
            
            minHailTruthDir = os.path.join(case.productDirs['hailtruth'], 'minshear')
            minHailTruthFiles = os.listdir(minHailTruthDir)
            
            maxShearClusterDirs = {}
            maxShearClusterFiles = {}
            maxShearDTs = {}

            
            minShearClusterDirs = {}
            minShearClusterFiles = {}
            minShearDTs = {}
            
            #For the AzShear clusters, load them by tilt
            for tilt in cfg.tiltList:
            
                try:
                    maxShearClusterDirs[tilt] = os.path.join(case.productDirs['maxShearClusterTable'], tilt, case.productVars['maxShearClusterTable'])
                    maxShearClusterFiles[tilt] = os.listdir(maxShearClusterDirs[tilt])
                except FileNotFoundError:
                    cfg.error("max shear tilt "+str(tilt)+" not found")
                    
                try:
                    minShearClusterDirs[tilt] = os.path.join(case.productDirs['minShearClusterTable'], tilt, case.productVars['minShearClusterTable'])
                    minShearClusterFiles[tilt] = os.listdir(minShearClusterDirs[tilt])
                except FileNotFoundError:
                    cfg.error("min shear tilt "+str(tilt)+" not found")
            
            maxShearClusters = {}
            minShearClusters = {}
            
            ETClusterDir = os.path.join(case.productDirs['ETClusterTable'], case.productVars['ETClusterTable'])
            ETClusterFiles = os.listdir(ETClusterDir)
            
            lowestTilt = cfg.tiltList[0]
            
            #Create AzShear objects for the 0.5 deg tilts separate since they include the w2hailtruth_size information
            cfg.log("Retrieving Shear Clusters for tilt 00.50")
            maxShearClusters[lowestTilt], maxShearDTs[lowestTilt] = self.loadShearClustersTruth(cfg, case, maxShearClusterFiles[lowestTilt], maxShearClusterDirs[lowestTilt], maxHailTruthFiles, maxHailTruthDir, lowestTilt)
            minShearClusters[lowestTilt], minShearDTs[lowestTilt] = self.loadShearClustersTruth(cfg, case, minShearClusterFiles[lowestTilt], minShearClusterDirs[lowestTilt], minHailTruthFiles, minHailTruthDir, lowestTilt)
            
            #Create the rest of the AzShear objects for the other tilts
            for tilt in cfg.tiltList[1:len(cfg.tiltList)]:
                cfg.log("Retrieving Shear Clusters for tilt "+tilt)
                maxShearClusters[tilt], maxShearDTs[tilt] = self.loadShearClusters(cfg, case, maxShearClusterFiles[tilt], maxShearClusterDirs[tilt], tilt)
                minShearClusters[tilt], minShearDTs[tilt] = self.loadShearClusters(cfg, case, minShearClusterFiles[tilt], minShearClusterDirs[tilt], tilt)
                
            #Create VIL/ET objects    
            cfg.log("Retrieving track clusters")
         
            trackClusters, trackDTs = self.loadTrackClusters(cfg, case, trackClusterFiles, trackClusterDir)
            cfg.log("Retrieving echo top clusters")

            etClusters, etDTs = self.loadETClusters(cfg, case, ETClusterFiles, ETClusterDir)
            
            emptyDictionary = {}
            for tilt2 in cfg.tiltList:
                emptyDictionary[tilt2] = []
                
            #cfg.log(str(maxShearDTs[lowestTilt]))
            #Create time ojbects
            if maxShearDTs[lowestTilt]:
            
                for i,DT in enumerate(maxShearDTs[lowestTilt]):
                
                    try:
                        #If the DTs don't match. Make an error and continue

                        if DT != minShearDTs[lowestTilt][minShearDTs[lowestTilt].index(DT)]:
                            cfg.error("Max/Min DTs don't match")
                            continue
                            
                    except (ValueError, AttributeError):
                        cfg.error("Min shear DT "+str(DT)+" not found. Setting min shear to empty")
                        
                        cfg.log("Going the max AzShear only route")
                        
                        appendTime = self.loadTime(cfg, DT, \
                        self.getClustersByDT(cfg, DT, maxShearClusters, isByTilt=True),\
                        emptyDictionary,\
                        trackClusters, etClusters)
                        
                        times.append(appendTime)
                        continue
                    else:
                        cfg.log("Trying both min and max AzShear")
                        
                    appendTime = self.loadTime(cfg, DT, \
                    self.getClustersByDT(cfg, DT, maxShearClusters, isByTilt=True),\
                    self.getClustersByDT(cfg, DT, minShearClusters, isByTilt=True),\
                    trackClusters, etClusters)
                    
                    #cfg.error("Appending time "+str(appendTime.getDT()))
                    
                    times.append(appendTime)
                    
            elif minShearDTs[lowestTilt]:
            
                cfg.error("Trying negative AzShears only")
                
                cfg.log("Trying min AzShear only")
                
                for i,DT in enumerate(minShearDTs[lowestTilt]):

                    appendTime = self.loadTime(cfg, DT, \
                    emptyDictionary,\
                    self.getClustersByDT(cfg, DT, minShearClusters, isByTilt=True),\
                    trackClusters, etClusters)
                    
                    times.append(appendTime)
                    
                    
            else:
                cfg.error("No cluster DTs found, moving onto the next case")
                raise err.NoReferenceClusterFoundException("No clusters found while sorting")
                    

                
            # cfg.error("Listing times 1")
            # for time in times:
                # cfg.error(str(time.getDT()))
                
            orderedTimes = reorderTimes(times)
            
            cfg.log("Created times "+str(orderedTimes))
            
            # cfg.error("Listing times 2")
            # for time in orderedTimes:
                # cfg.error(str(time.getDT()))
            
            #Build the storms
            stormBuilder = sb.StormBuilder(cfg, case, orderedTimes)
            stormGroups = stormBuilder.buildStormGroups()
            #stormGroups = stormBuilder.getStormGroups()
                
            self.writeInterestingClusters(cfg, case, stormGroups)
        
        except err.NoModelDataFound:
            raise
        except Exception as E:
            cfg.error("Exception running analysis")
            raise
                
        return stormGroups  
        
    #Save QC for final analysis
    def runAfterAnalysis(self, cfg, cases):
        return None
        

