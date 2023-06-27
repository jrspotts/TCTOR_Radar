#This class contains the methods and attributes needed to create a storm group for clusters across time
#Justin Spotts - 3/3/2022

from ttrappy import clusters as clu
from datetime import timedelta as td
from datetime import datetime
from ttrappy import error as err
from ttrappy import distance
import math
import os

class StormBuilder():

    
    def __init__(self, cfg, case, times):
    
        """ This class creates storm and shear group objects given the clusters of interest and other clusters.
        
            This class begins with the cluster of interest at a given datetime (DT). Interest scores for shear clusters
            for the next tilt up are calculated and the highest score is added to a shear group. The time of the shear
            group is updated to the time of the highest tilt and the location of the shear group is updated to the 
            average of all clusters added thus far. Once no more clusters are available to be added. The interest
            score for the surounding track objects are calcualted, followed by the echo top objects. All objects are
            combined together into a storm group.
            
            Attributes:
            cfg (Config): A copy of the program's Config object
            times (list): A list of time objects containing all the clusters
            case (Case): A copy of the programs Case object
            stormGroups (list): The list of created StormGroup objects
            shearGroups (list): The list of associated ShearGroup objects
            
            Methods:
            
            
        """
    
        self.cfg = cfg
        self.times = times
        self.case = case
        self.stormGroups = None
        self.shearGroups = None
        
        return
    
    def getStormGroups(self):
        return self.stormGroups
    def getShearGroups(self):
        return self.shearGroups
        
    def buildStormGroups(self):
        """ Construct and return the StormGroups objects """
        
        #Make sure we have shear groups. Catch and raise the no model data found error if raised
        try:
            shearGroups = self.buildShearGroups()
        except err.NoModelDataFound:
            raise
        except err.NoReferenceClusterFoundException:
            raise
            
        stormGroups = []
        
        #Go through each time and find the shear group that matches that time
        for n,sg in enumerate(shearGroups):

            #Find the track cluster with the highest interest score and add it to the group 
            bestTrackInterest = 0
            bestTrackCluster = None
            
            bestETInterest = 0
            bestETCluster = None
                
            self.cfg.log("Storm Group checking time "+str(sg.getCluster(self.cfg.tiltList[0]).getDT()))
            
            for time in self.times:
                
                if sg.getFirstTime().strftime('%Y%m%d-%H%M%S') == time.getDT() and time.getTrackClusters():

                    for trackCluster in time.getTrackClusters():
                    
                        currentTrackInterest = self.calculateTrackInterest(sg, trackCluster)
                    
                        if currentTrackInterest:
                            if currentTrackInterest > bestTrackInterest:
                                
                                bestTrackInterest = currentTrackInterest
                                
                                if bestTrackInterest >= self.cfg.minTrackScore:
                                    bestTrackCluster = trackCluster
                    
                    if bestTrackCluster:
                        
                        clusterCountTrack = self.getNearbyClusterCount(sg.getLowestLat(), sg.getLowestLon(), time.getTrackClusters(), self.cfg.maxTrackDist)
                        bestTrackCluster.setPotentialClusterCount(clusterCountTrack)
                        
                        if time.getETClusters():
                            self.cfg.log("Best track cluster was "+str(bestTrackCluster.getID()[0])+" with interest "+str(bestTrackInterest))
                            
                            #Now do the same with the echo tops and the best track cluster if one was found
                        
                            for etCluster in time.getETClusters():
                            
                                currentETInterest = self.calculateETInterest(etCluster, bestTrackCluster)
                                
                                if currentETInterest:
                                    if currentETInterest > bestETInterest:
                                        
                                        bestETInterest = currentETInterest
                                        
                                        if bestETInterest >= self.cfg.minTopScore:
                                        
                                            bestETCluster = etCluster
                                        
                            
                            if bestETCluster:
                                self.cfg.log("Best echo top cluster was "+str(bestETCluster.getID()[0])+" with interest "+str(bestETInterest))
                                clusterCount = self.getNearbyClusterCount(bestTrackCluster.getLatitude()[0], bestTrackCluster.getLongitude()[0], time.getETClusters(), self.cfg.maxTopDist)
                                bestETCluster.setPotentialClusterCount(clusterCount)
                            else:
                                self.cfg.log("No best echo top cluster was available for "+str(time.getDT())+". Max interest "+str(bestETInterest))
                        else:
                            self.cfg.log("No ET Clusters for storm group creation")
                        
                    else:
                        self.cfg.log("No best track available was found for "+str(time.getDT())+". Max interest "+str(bestTrackInterest))
            
            #Check for model data in the track cluster
            if bestTrackCluster:
                
                try:
                    hasModel = self.checkForModel(bestTrackCluster)
                except err.NoModelDataFound as excep:
                    raise
            
            #Print all the shears for debugging purposes real quick
            # for tilt in self.cfg.tiltList:
                # self.cfg.error("sg "+tilt+" "+str(sg.getCluster(tilt))+" "+str(sg)+" from dictionary "+str(hex(id(sg.getClusterDictionary()))))
            stormGroups.append(clu.StormGroup(self.cfg, sg, bestTrackCluster, bestETCluster, str(n)))
            self.cfg.log("Creating storm group "+str(stormGroups[-1])+" with shear group "+str(sg.getID())+" which has "+str(sg.getNClusters())+" clusters")  
                
        self.stormGroups = stormGroups
        
        return stormGroups
                    
    def buildShearGroups(self):
        
        """ Begins the process of building shear group objects.
        
            For each time step, start with the shear object of interest for both maximum/minimum AzShear.
            Calculate the interest score for each cluster at the tilt following the previous tilt if within the maximum time.
            
            
        """
        
        #First, get the clusters of interest
        try:
            orderedMaxShearsOfInterest, orderedMinShearsOfInterest = self.getInterestingClusters()
        except err.NoModelDataFound:
            raise
        except err.NoReferenceClusterFoundException:
            raise
        
        matchedMaxShears, matchedMinShears = self.matchOrderedShears(orderedMaxShearsOfInterest, orderedMinShearsOfInterest)
        
        #Next, determine whether we are using the max or min shears
        interestingShearClusters, isMax = self.determineWinningShear(matchedMaxShears, matchedMinShears)
        
        if isMax:
            interestingShearClusters = orderedMaxShearsOfInterest
        else:
            interestingShearClusters = orderedMinShearsOfInterest
        
        #Make sure the clusters have their average motion vectors. Commented out because motions should be determined during associations
        #interestingMovingClusters = self.calculateShearMotionVector(interestingShearClusters)
        
        #Begin going through every cluster and creating the shear groups.
        shearGroups = []
        
        for n,iCluster in enumerate(interestingShearClusters):
            
            
            #Nuke the current shear group to create new memory references for its attributes
            currentGroup = None
            #Create the new group
            currentGroup = clu.ShearGroup(self.cfg, self.case.ID+"_"+str(n))
            
            currentGroup.setCluster(iCluster, self.cfg.tiltList[0])
            
            latestCluster = iCluster
            
            #Grab a list of tilts from the AzShear_tilt directory to check if the tilt is actually missing, or there just isn't any clusters
            referenceTilts = os.listdir(os.path.join(self.case.productDirs['shear'], self.case.sites[0].name, self.case.productVars['shear']))
            
            if '.working' in referenceTilts:
                referenceTilts.remove('.working')
                
                
            
            #Go through other tilts in the tilt list, determine which one is the cluster of interest, and add it to the group. 
            for tilt in self.cfg.tiltList[1:len(self.cfg.tiltList)]:
                
                try:
                    if isMax:
                        currentClusters = []
                        
                        #self.cfg.error("current cluster check "+str(self.getCorrespondingTime(iCluster).getMaxShearClusters(tilt)))
                        for currentCluster in self.getCorrespondingTime(iCluster).getMaxShearClusters(tilt):
                            currentCluster.setVLat(iCluster.getVLat()[0])
                            currentCluster.setVLon(iCluster.getVLon()[0])
                            currentCluster.setMotionDirection(iCluster.getMotionDirection()[0])
                            currentCluster.setClusterU(iCluster.getClusterU()[0])
                            currentCluster.setClusterV(iCluster.getClusterV()[0])
                            currentClusters.append(currentCluster)
                    else:
                        currentClusters = []
                        
                        for currentCluster in self.getCorrespondingTime(iCluster).getMinShearClusters(tilt):
                            currentCluster.setVLat(iCluster.getVLat()[0])
                            currentCluster.setVLon(iCluster.getVLon()[0])
                            currentCluster.setMotionDirection(iCluster.getMotionDirection()[0])
                            currentCluster.setClusterU(iCluster.getClusterU()[0])
                            currentCluster.setClusterV(iCluster.getClusterV()[0])
                            currentClusters.append(currentCluster)
                            
                except KeyError:
                    self.cfg.error("buildShearGroups(): Tilt "+str(tilt)+" not found for "+str(currentGroup.getID()))
                    
                    #Tell the shear group that this tilt is missing, but only if it wasn't possible for there to be a tilt to begin with
                    if tilt not in referenceTilts:
                        currentGroup.setIsMissing(True, tilt)
                    continue
                    
                bestCluster = None
                bestInterest = 0
                
                self.cfg.log(tilt+" Current Clusters\n"+str(currentClusters))
                for cluster in currentClusters:
                    
                    #currentInterest = self.calculateShearInterest(latestCluster, cluster, iCluster.getMotionDirection()[0])
                    currentInterest = self.calculateShearInterest(iCluster, cluster, iCluster.getMotionDirection()[0], isTilt=True)
                    
                    if not currentInterest:
                        continue
                    
                    if currentInterest > bestInterest:
                    
                        bestInterest = currentInterest
                        
                        if bestInterest >= self.cfg.minShearScore:
                            bestCluster = cluster
                
                #Check that the tilt has a folder in the AzShear folder
                if tilt not in referenceTilts:
                    currentGroup.setIsMissing(True, tilt)
                else:
                    currentGroup.setIsMissing(False, tilt)
                
                if bestCluster:
                    self.cfg.log("Best shear cluster was between"+str(iCluster)+" and "+str(bestCluster)+" with interest "+str(bestInterest)+" on tilt "+str(tilt))
                else:
                    self.cfg.log("No best shear cluster was found for tilt "+str(tilt)+" on group "+str(currentGroup.getID())+". Max interest "+str(bestInterest))
                    self.cfg.error("Added None for tilt "+tilt+" to group "+currentGroup.getID()+" which now has "+str(currentGroup.getNClusters())+" clusters in dictionary "+str(hex(id(currentGroup.getClusterDictionary()))))
                    currentGroup.setCluster(bestCluster, tilt)
                    continue
                    
                
                #One last check for model data for the shear clusters
                try:
                    hasModel = self.checkForModel(bestCluster)
                except err.NoModelDataFound as excep:
                    raise
                    
                if self.cfg.projectReference:
                    dt = abs((iCluster.getDT() - bestCluster.getDT()).total_seconds())
                    projLat, projLon = iCluster.getClusterProjection(dt)
                    clusterCount = self.getNearbyClusterCount(projLat, projLon, currentClusters, self.cfg.maxShearDistTilt)
                    bestCluster.setPotentialClusterCount(clusterCount)
                else:
                    clusterCount = self.getNearbyClusterCount(iCluster.getLatitude()[0], iCluster.getLongitude()[0], currentClusters, self.cfg.maxShearDistTilt)
                    bestCluster.setPotentialClusterCount(clusterCount)
                    
                currentGroup.setCluster(bestCluster, tilt)
                self.cfg.log("Added cluster "+str(vars(bestCluster))+" for tilt "+tilt+" to group "+currentGroup.getID()+" which now has "+str(currentGroup.getNClusters())+" clusters in dictionary "+str(hex(id(currentGroup.getClusterDictionary()))))
                
                latestCluster = bestCluster
                
            
            shearGroups.append(currentGroup)
            
        self.shearGroups = shearGroups
        
        return shearGroups
    
    def calculateETInterest(self, et, tc):
        """ Calculates the interest score between a TrackCluster (tc) and an Echo-Top cluster (et)

            Calculates the interest score using the same parameters as calculateShearInterest 
            except without the intensity term (unless we need to later).
            
        """
        
        #First, calculate the distance term
        distanceBetween = distance.calculateDistance(tc.getLatitude()[0], tc.getLongitude()[0], et.getLatitude()[0], et.getLongitude()[0])
        
        #Check for a disqualifying distance and return None if it is disqualified
        if distanceBetween > self.cfg.maxTopDist:
            return None
            
        distanceTerm = ((self.cfg.maxTopDist - distanceBetween)/self.cfg.maxTopDist) * self.cfg.topDistWeight
        
        #Next, calculate the direction term
        direction = distance.calculateBearingAT(tc.getLatitude()[0], tc.getLongitude()[0], et.getLatitude()[0], et.getLongitude()[0])
        if direction < 0:   
            direction += 360
            
        tc06kmShearDirection = tc.getShearDirection()
        directionDifference = abs(tc06kmShearDirection - direction)
        
        #Make sure that if the bearing are widly different, that the difference is properly calculated
        if directionDifference > 180:
            
            if direction < tc06kmShearDirection:
                directionDifference = abs(tc06kmShearDirection - (direction + 360))
            elif direction > tc06kmShearDirection:
                directionDifference = abs((tc06kmShearDirection + 360) - direction)
            
        directionTerm = ((180 - directionDifference)/180) * self.cfg.topVectorWeight

        #Finally, add them all up 
        interestScore = distanceTerm + directionTerm
        
        self.cfg.log("Calculated echo top interest "+str(interestScore)+" from DT distance, direction,difference and terms terms "+str(et.getDT())+" "+str(distanceBetween)+" "+str(direction)+" "+str(directionDifference)+" "+str(distanceTerm)+","+str(directionTerm))
                
        return interestScore
        
    def calculateTrackInterest(self, sg, tc):
        """ Calculates the interest score between a ShearGroup (sg) and a TrackCluster (tc)

            Calculates the interest score using the same parameters as calculateShearInterest 
            except without the intensity term (unless we need to later).
            
        """
        
        #First, calculate the distance term
        distanceBetween = distance.calculateDistance(sg.getLowestLat(), sg.getLowestLon(), tc.getLatitude()[0], tc.getLongitude()[0])
        
        #Check for a disqualifying distance and return None if it is disqualified
        if distanceBetween > self.cfg.maxTrackDist:
            return None
        
        distanceTerm = ((self.cfg.maxTrackDist - distanceBetween)/self.cfg.maxTrackDist) * self.cfg.trackDistWeight
        
        #Next, calculate the direction term
        direction = distance.calculateBearingAT(sg.getLowestLat(), sg.getLowestLon(), tc.getLatitude()[0], tc.getLongitude()[0])
        if direction < 0:   
            direction += 360
            
        clusterShearDirection = sg.getCluster(self.cfg.tiltList[0]).getShearDirection()
        directionDifference = abs(clusterShearDirection - direction)
        
        #Make sure that if the bearing are widly different, that the difference is properly calculated
        if directionDifference > 180:
            
            if direction < clusterShearDirection:
                directionDifference = abs(clusterShearDirection - (direction + 360))
            elif direction > clusterShearDirection:
                directionDifference = abs((clusterShearDirection + 360) - direction)
                
        directionTerm = ((180 - directionDifference)/180) * self.cfg.trackVectorWeight

        #Finally, add them all up 
        interestScore = distanceTerm + directionTerm
        
        self.cfg.log("Calculated track interest score "+str(interestScore)+" from distance, direction terms "+str(distanceTerm)+","+str(directionTerm))
                
        return interestScore
        
        
    def getCorrespondingTime(self, cluster):
        """ Find which of the time objects corresponds to the cluster """
        
        for time in self.times:
            
            if time.getDT() == cluster.getDT().strftime('%Y%m%d-%H%M%S'):
                return time
        

        #Return None if no closest time was found
        return None
        
    def matchOrderedShears(self, orderedMaxShearsOfInterest, orderedMinShearsOfInterest):
        """ Returns two lists of shear clusters of interest that are matched in time """
        
        matchedOrderedMaxShearsOfInterest = []
        matchedOrderedMinShearsOfInterest = []
        
        if orderedMaxShearsOfInterest and orderedMinShearsOfInterest:
            for maxCluster in orderedMaxShearsOfInterest:
            
                for minCluster in orderedMinShearsOfInterest:
                
                    if maxCluster.getDT() == minCluster.getDT():
                        matchedOrderedMaxShearsOfInterest.append(maxCluster)
                        matchedOrderedMinShearsOfInterest.append(minCluster)
                        
        elif not orderedMaxShearsOfInterest:
            return [], orderedMinShearsOfInterest
        elif not orderedMinShearsOfInterest:
            return orderedMaxShearsOfInterest, []
                    
                    
        return matchedOrderedMaxShearsOfInterest, matchedOrderedMinShearsOfInterest
        
        
    def determineWinningShear(self, orderedMaxShearsOfInterest, orderedMinShearsOfInterest):
        """ Determine whether the maximum (positive) or minimum (negative) shear is the most prevalent and return that group. 
            In the event of a tie, the max shear gets the point. The arguments are max/minShearsOfInterest, but the two groups should be matched by time.
        """
        
        self.cfg.log("Determining winning shear")
        maxShearPoints = 0
        minShearPoints = 0
        
        mismatches = 0
        
        if orderedMaxShearsOfInterest and orderedMinShearsOfInterest:
            for maxS, minS in zip(orderedMaxShearsOfInterest, orderedMinShearsOfInterest):
            
                #Check to determine whether the dateTimes match. If there is one, keep trying. 
                if maxS.getDT() != minS.getDT():
                    self.cfg.error("Warning! Mismatch in times between max and min clusters during winner determination "+str(maxS.getDT())+ " "+str(minS.getDT())+" "+str(self.case.ID)+" mismatch "+str(mismatches))
                    mismatches += 1
                    continue
                
                self.cfg.log("Checking winning cluster "+str(maxS.getDT())+" at "+str(maxS.getLatitude()[0])+" "+str(maxS.getLongitude()[0])+" "+str(abs(maxS.getMaxShear()[0]))+" against "+str(minS.getDT())+" at "+str(minS.getLatitude()[0])+" "+str(minS.getLongitude()[0])+" "+str(abs(minS.getMinShear()[0])))
                if abs(maxS.getMaxShear()[0]) >= abs(minS.getMinShear()[0]):
                    maxShearPoints += 1
                    
                elif abs(maxS.getMaxShear()[0]) < abs(minS.getMinShear()[0]):
                    minShearPoints += 1
                    
                else:
                    self.cfg.error("Something weird happened when determining a winner")
                    
            #Return the winner along with a boolean indicating whether the winner was the positive AzShears or not
            #return orderedMaxShearsOfInterest, True #This line was added to force max shear clusters to be used for testing. Needs to be removed for final analysis 
            if maxShearPoints >= minShearPoints:
                return orderedMaxShearsOfInterest, True
            else:
            
                with open(self.cfg.logName+'_events.csv', 'a') as fi:
                    fi.write(str(self.case.storm)+','+str(self.case.ID)+','+str(self.case.isTor)+',5,NA,The min AzShear won\n')
                    
                return orderedMinShearsOfInterest, False
                
        elif orderedMaxShearsOfInterest and not orderedMinShearsOfInterest:
            
            self.cfg.log("Max shear won with "+str(maxShearPoints)+" points")
            return orderedMaxShearsOfInterest, True
        
        elif orderedMinShearsOfInterest and not orderedMaxShearsOfInterest:
            
            with open(self.cfg.logName+'_events.csv', 'a') as fi:
                fi.write(str(self.case.storm)+','+str(self.case.ID)+','+str(self.case.isTor)+',5,NA,The min AzShear won\n')
            
            self.cfg.log("Min shear won with "+str(minShearPoints)+" points")
            
            return orderedMinShearsOfInterest, False
            
        else:
            return None, False
            

    def calculateShearInterest(self, coi, tc, avgMotion, forward=True, isTilt=False):
    
        """ Calculates the interest score from the cluster of interest to other cluster. 
        
            Calculates the interest scores between the clusterOfInterest and other cluster. The equation used
            to calculate the interest score is a modified version of equation (1) from Skinner et al. (2016) 
            
            DOI: 10.1175/WAF-D-15-0129.1
            
            The equation is modified in that: 1) there is no time component because the correct time was determined before hand,
            2) AzShear is used instead of area, 3) (180 degrees minus the difference in bearing from the cluster motion) / 180 degrees is added
            
            Parameters:
            
            coi (ShearCluster): ShearCluster to calculate the interest score relative to.
            tc (list): List of other ShearCluster objects to calculate the interest score for.
            avgMotion (float): Misleading. Just the reference bearing to use for the direction component
            
            Keyward Arguments:
            forward (boolean): If using projected points for score calculation, do we use the forward or backward projected point. Default is forward.
            isTilt (boolean): Whether or not the interest score is for a tilt-by-tilt association. If it is, we don't want to use the projected point for the score calculation.
            

            Returns:
                float: The interest score
        """
        
        #Points used in the following calculation can vary depending on whether projection is being used or not.
        
        #First, calculate the distance term
        if self.cfg.projectReference and not isTilt:
            self.cfg.log("Calculating IS score with projections")
            if forward:
                self.cfg.log("Calculating distance between "+str(coi.getForwardLat()[0])+" "+str(coi.getForwardLon()[0])+" and "+str(tc.getLatitude()[0])+" "+str(tc.getLongitude()[0]))
                distanceBetween = distance.calculateDistance(coi.getForwardLat()[0], coi.getForwardLon()[0], tc.getLatitude()[0], tc.getLongitude()[0])
            else:
                self.cfg.log("Calculating distance between "+str(coi.getLatitude()[0])+" "+str(coi.getLongitude()[0])+" and "+str(tc.getBackwardLat()[0])+" "+str(tc.getBackwardLon()[0]))
                distanceBetween = distance.calculateDistance(coi.getLatitude()[0], coi.getLongitude()[0], tc.getBackwardLat()[0], tc.getBackwardLon()[0])
        #If this is an isTilt, use the projection from the coi
        elif self.cfg.projectReference and isTilt:
            self.cfg.log("Calculating IS score with projection by tilt")
            #Since we are only projecting foward, we don't need to check if it's foward or backward 
            dt = abs((tc.getDT() - coi.getDT()).total_seconds())
            projLat, projLon = coi.getClusterProjection(dt)
            distanceBetween = distance.calculateDistance(projLat, projLon, tc.getLatitude()[0], tc.getLongitude()[0])
                
        else:
            distanceBetween = distance.calculateDistance(coi.getLatitude()[0], coi.getLongitude()[0], tc.getLatitude()[0], tc.getLongitude()[0])
        
        #Check for a disqualifying distance and return None if it is disqualified
        if (distanceBetween > self.cfg.maxShearDist) and not isTilt and float(self.cfg.shearDistWeight) != 0:
            self.cfg.log("Rejected with distance between "+str(distanceBetween))
            return None
        elif isTilt and (distanceBetween > self.cfg.maxShearDistTilt) and self.cfg.projectReference:
            #If we are calculating the interest score for tilt-by-tilt associations using the projected location, use a different, ideally smaller, rejection distance to hopefully reduce false associations
            self.cfg.log("Rejected tilt with distance between "+str(distanceBetween))
            return None
        
        
        distanceTerm = ((self.cfg.maxShearDist - distanceBetween)/self.cfg.maxShearDist) * self.cfg.shearDistWeight
        
        #Next, calculate the direction term.
        
        if self.cfg.projectReference and not isTilt:
            if forward:
                direction = distance.calculateBearingAT(coi.getForwardLat()[0], coi.getForwardLon()[0], tc.getLatitude()[0], tc.getLongitude()[0])
            else:
                direction = distance.calculateBearingAT(coi.getLatitude()[0], coi.getLongitude()[0], tc.getBackwardLat()[0], tc.getBackwardLon()[0])
                
        elif self.cfg.projectReference and isTilt:
            self.cfg.log("Calculating IS score with projection by tilt")
            #Since we are only projecting foward, we don't need to check if it's foward or backward 
            dt = abs((tc.getDT() - coi.getDT()).total_seconds())
            projLat, projLon = coi.getClusterProjection(dt)
            direction = distance.calculateBearingAT(projLat, projLon, tc.getLatitude()[0], tc.getLongitude()[0])
            
        else:
            direction = distance.calculateBearingAT(coi.getLatitude()[0], coi.getLongitude()[0], tc.getLatitude()[0], tc.getLongitude()[0])
            
        if direction < 0:   
            direction += 360
        
        directionDifference = abs(avgMotion - direction)
        
        
        #Make sure that if the bearing are widly different, that the difference is properly calculated
        if directionDifference > 180:
            
            if direction < avgMotion:
                directionDifference = abs(avgMotion - (direction + 360))
            elif direction > avgMotion:
                directionDifference = abs((avgMotion + 360) - direction)
                
                
        #Also stop calculating in the dirrection difference is greater than that allowed. This rejection should not be used if the weight for the direction term is 0.
        #Also note: using projected points may require higher maximum deviations for tracking to perform properly.
        if directionDifference > self.cfg.maxBearingDev and distanceBetween > (self.cfg.maxShearDist*self.cfg.shearVectorDistanceFactor) and float(self.cfg.shearVectorWeight) != 0:
            self.cfg.log("Rejected with bearing difference "+str(directionDifference)+" bearing "+str(direction)+" "+str(avgMotion)+" at dist "+str(distanceBetween))
            return None
        
        
        directionTerm = ((180 - directionDifference)/180) * self.cfg.shearVectorWeight

        
        #Now calculate the intensity term
        intensityTerm = 0
        if coi.getAbsShear()[0] >= tc.getAbsShear()[0]:
            intensityTerm = (tc.getAbsShear()[0] / coi.getAbsShear()[0]) * self.cfg.shearIntensityWeight
        elif coi.getAbsShear()[0] < tc.getAbsShear()[0]:
            intensityTerm = (coi.getAbsShear()[0] / tc.getAbsShear()[0]) * self.cfg.shearIntensityWeight

        
        #Finally, add them all up 
        self.cfg.log("distance, and distance, direction, and intensity terms "+str(distanceBetween)+","+str(distanceTerm)+","+str(directionTerm)+","+str(intensityTerm))
        interestScore = distanceTerm + directionTerm + intensityTerm
        
        self.cfg.log("Calculated shear interest score "+str(interestScore))
                
        return interestScore
        
    def calculateShearInterestInitial(self, coi):
    
        """ Calculates the interest score from the point of interest to potential clusters of interest. 
        
            Calculates the interest scores between the clusterOfInterest and other cluster. The equation used
            to calculate the interest score is a modified version of equation (1) from Skinner et al. (2016) 
            
            DOI: 10.1175/WAF-D-15-0129.1
            
            The equation is modified in from calculateShearInterest in that there is no direction term and the intensity term is the max shear over 0.005 s^-1
            
            Parameters:
            
            coi (ShearCluster): ShearCluster to calculate the interest score relative to.
            
            

            Returns:
                float: The interest score
        """
        
        #First, calculate the distance term
        distanceBetween = distance.calculateDistance(self.case.startLat, self.case.startLon, coi.getLatitude()[0], coi.getLongitude()[0])
        #self.cfg.error("Checking distance "+str(distanceBetween))
        #Check for a disqualifying distance and return None if it is disqualified
        if distanceBetween > self.cfg.maxShearDistInit:
            return None
            
        distanceTerm = ((self.cfg.maxShearDistInit - distanceBetween)/self.cfg.maxShearDistInit) * self.cfg.shearDistWeight
        
        #Now calculate the intensity term
        intensityTerm = (coi.getAbsShear()[0]/0.005)*self.cfg.shearIntensityWeight
        
        #Finally, add them all up 
        #self.cfg.error("distance and distance and intensity terms "+str(distanceBetween)+" "+str(distanceTerm)+","+str(intensityTerm)+" initial")
        interestScore = distanceTerm + intensityTerm
        
        self.cfg.log("Calculated shear initial interest score "+str(interestScore))
                
        return interestScore

    def getNearbyClusterCount(self, lat, lon, clusters, maxDist):
        """ Returns all clusters from the clusters list within a maximum distance (maxDist) of the lat lon """
        
        clusterCount = 0
        for cluster in clusters:
            distBetween = distance.calculateDistance(lat, lon, cluster.getLatitude()[0], cluster.getLongitude()[0])
            
            if distBetween <= maxDist:
                clusterCount += 1
                
        return clusterCount
        
    def calculateShearMotionVector(self, cluster1, cluster2, motions):

        """ Calculate the motion vector between the first and last cluster of interest and updates all the clusters with 
            that direction
        """
        
        updatedClusters = []
        motionVariables = {}
        #If there is only one cluster (for some reason). Set the horizontal velocity to 0 and the motion vector equal to its shear vector
        if cluster1 == cluster2:
            
            self.cfg.error("calculateShearMotionVector(): Warning! Only one cluster received. Setting motion to 0")
            cluster1.setVLat(0)
            cluster1.setVLon(0)
            cluster1.setMotionDirection(None)
            
            
            
        dLat = cluster2.getLatitude()[0] - cluster1.getLatitude()[0]
        dLon = cluster2.getLongitude()[0] - cluster1.getLongitude()[0]
        
        dt = abs((cluster2.getDT() - cluster1.getDT()).total_seconds())
        
        #Now calculate the velocities in each direction
        vLat = dLat/dt
        vLon = dLon/dt
        
        #Calcualte the direction
        direction = distance.calculateBearingAT(cluster1.getLatitude()[0], cluster1.getLongitude()[0], cluster2.getLatitude()[0], cluster2.getLongitude()[0])
        if direction < 0:
            direction += 360
        if direction > 360:
            direction -= 360
        
        #Calculate the distance
        dist = distance.calculateDistance(cluster1.getLatitude()[0], cluster1.getLongitude()[0], cluster2.getLatitude()[0], cluster2.getLongitude()[0])*1000 #Convert to meters
        
        speed = dist/dt
        
        uMotion = None
        vMotion = None
        
        #Calculate u and v motion vectors
        uMotion = math.sin(math.radians(direction))*speed
        vMotion = math.cos(math.radians(direction))*speed
       
        self.cfg.log("Calculated motion vector\nvLat = "+str(vLat)+" deg/s vLon = "+str(vLon)+" deg/s towards direction "+str(direction)+" deg\n\
                      start ("+str(cluster1.getLatitude()[0])+","+str(cluster1.getLongitude()[0])+") end ("+str(cluster2.getLatitude()[0])+","+str(cluster2.getLongitude()[0])+") uMotion "+str(uMotion)+" vMotion "+str(vMotion))
                      
        
        
        motionVariables['vLat'] = vLat
        motionVariables['vLon'] = vLon
        motionVariables['direction'] = direction
        motionVariables['uMotion'] = uMotion
        motionVariables['vMotion'] = vMotion
        
        #If we're using the mean motion calculate the sum and number of each variable and find the average.
        if self.cfg.useMeanMotion:
            vLatSum = 0
            vLonSum = 0
            uDirSum = 0
            vDirSum = 0
            uMotionSum = 0
            vMotionSum = 0
            n = 0
            
            for motion in motions:
            
                vLatSum += motion['vLat']
                vLonSum += motion['vLon']
                
                #For the direction, break the direction into their components, sum them, and calculate the new direction afterwards.
                currentDir = motion['direction']
                uDirSum += math.sin(math.radians(currentDir))
                vDirSum += math.cos(math.radians(currentDir))
                
                uMotionSum += motion['uMotion']
                vMotionSum += motion['vMotion']
                
                n += 1
                
            vLatSum += vLat
            vLonSum += vLon
            uDirSum += math.sin(math.radians(direction))
            vDirSum += math.cos(math.radians(direction))
            uMotionSum += uMotion
            vMotionSum += vMotion
            
            n += 1
            
            cluster1.setVLat(vLatSum/n)
            cluster1.setVLon(vLonSum/n)
            
            avgDirection = math.degrees(math.atan2(uDirSum, vDirSum))
            if avgDirection < 0:
                avgDirection += 360
            
            self.cfg.log("Averaged motion from "+str(motions))
            cluster1.setMotionDirection(avgDirection)    
            cluster1.setClusterU(uMotionSum/n)
            cluster1.setClusterV(vMotionSum/n)
            
        else:
                
            cluster1.setVLat(vLat)
            cluster1.setVLon(vLon)
            cluster1.setMotionDirection(direction)
            cluster1.setClusterU(uMotion)
            cluster1.setClusterV(vMotion)
        
        #Calculate the projected points
        
        cluster1.projectCluster(dt)
            
        motions.append(motionVariables)
        
        return cluster1, motions

    def checkForModel(self, cluster):
        """ Checks to see if the given cluster has the necessary model data. Raises a NoModelDataFound exception if not """
        
        if cluster.getType() == 'track':
            
            if float(cluster.getu6kmMeanWind()[0]) <= -99900 or float(cluster.getv6kmMeanWind()[0]) <= -99900 or\
                float(cluster.getu10kmWind()[0]) <= -99900 or float(cluster.getv10kmWind()[0]) <= -99900 or\
                float(cluster.getuShear()[0]) <= -99900 or float(cluster.getvShear()[0]) <= -99900:
                raise err.NoModelDataFound("Track cluster "+str(cluster.getID()[0])+" "+str(cluster.getDT())+" "+str(cluster.getLatitude()[0])+\
                    " "+str(cluster.getLongitude()[0])+" did not have 1 or more wind data.")
                    
                return False
                    
        if cluster.getType() == 'shear':
            
            if float(cluster.getuShear()[0]) <= -99900 or float(cluster.getvShear()[0]) <= -99900 or float(cluster.getu6kmMeanWind()[0]) <= -99900 or\
                    float(cluster.getv6kmMeanWind()[0]) <= -99900:
                raise err.NoModelDataFound("Shear cluster "+str(cluster.getID()[0])+" "+str(cluster.getDT())+" "+str(cluster.getLatitude()[0])+\
                    " "+str(cluster.getLongitude()[0])+" did not have 1 or more model data.")
                    
                return False
                    
        return True
        
        
    def getBestCluster(self, refClusters, isMax=True):
        """ Goes through all potential reference clusters and finds which one is the closest to the case start location point """
        
        self.cfg.log("Getting best cluster")
        #Step 1 find the time that is temporally closest to the case point
        closestTimeSeconds = 99999999
        closestTime = None
        for time in refClusters.keys():
            if len(refClusters[time]) > 0:
                dtSeconds = 999999999
                timeDT = self.cfg.utc.localize(datetime.strptime(time.getDT(), '%Y%m%d-%H%M%S'))
                if timeDT >= self.case.dateTime:
                    dtSeconds = (timeDT - self.case.dateTime).seconds
                elif timeDT < self.case.dateTime:
                    dtSeconds = (self.case.dateTime - timeDT).seconds
                else:
                    self.cfg.error('Something went wrong')
                    
                if dtSeconds < closestTimeSeconds:
                    closestTimeSeconds = dtSeconds
                    closestTime = time
        
        if not closestTime:
            self.cfg.error("Warning! No closest time detected. Stopping best cluster check")
            return False, False
            
        highestScore = -1
        referenceCluster = None
        #Step 2, at the closest time, find the closest cluster spatially
        for cluster in refClusters[closestTime]:
            score = self.calculateShearInterestInitial(cluster)
            if score:
                if score >= self.cfg.minShearScore and score > highestScore:
                    highestScore = score
                    referenceCluster = cluster
        
        if not referenceCluster:
            if isMax:
                if not closestTime.getMinShearClusters(self.cfg.tiltList[0]):
                    self.cfg.error("No reference clusters found for lowest level AzShear!")
                    raise err.NoReferenceClusterFoundException("No Reference Clusters Found")
                else:
                    return False, False
            else:
                if not closestTime.getMaxShearClusters(self.cfg.tiltList[0]):
                    self.cfg.error("No reference clusters found for lowest level AzShear!")
                    raise err.NoReferenceClusterFoundException("No Reference Clusters Found")
                else:
                    return False, False
        
        clusterCount = self.getNearbyClusterCount(self.case.startLat, self.case.startLon, refClusters[closestTime], self.cfg.maxShearDistInit)
        referenceCluster.setPotentialClusterCount(clusterCount)
        
        self.cfg.log("Found cluster "+str(referenceCluster.getID()[0])+" at time "+str(closestTime.getDT()))
        
        referenceCluster.setIsReference(True)
        
        #Check to see if the reference cluster has model data
        try:
            hasModel = self.checkForModel(referenceCluster)
        except err.NoModelDataFound as excep:
            raise
        
        return referenceCluster, closestTime
        
        
    def getInterestingClusters(self):
        """ Returns the clusters that appear to be associated with a record """
        
        maxInterestingClusters = []
        maxReferenceCluster = None     #This is the cluster that first contains the report
        maxReferenceTime = None        #This is the time of the reference cluster)
        maxReferenceClusters = {}
        
        lowTilt = self.cfg.tiltList[0]
        
        #Find the max AzShear reference cluster
        for time in self.times:
            clusters = []
            for cluster in time.getMaxShearClusters(lowTilt):
                #self.cfg.error("Cluster "+str(cluster))
                if cluster:
                    #self.cfg.error("Report "+str(cluster.getNumReports()[0]))
                    if cluster.getNumReports()[0] is not None:
                        if int(float(cluster.getNumReports()[0])) > 0: 
                            clusters.append(cluster)
                            maxReferenceTime = time
                            self.cfg.log("Reference cluster found! "+str(len(maxReferenceClusters))+" lat "+str(cluster.getLatitude()[0])+" lon "+str(cluster.getLongitude()[0]))
            
            maxReferenceClusters[time] = clusters
            
        try:
            maxReferenceCluster, maxReferenceTime = self.getBestCluster(maxReferenceClusters, isMax=True)
        except err.NoReferenceClusterFoundException:
            self.cfg.error("No reference clusters found for lowest level AzShear!")
            raise err.NoReferenceClusterFoundException("No Max Reference Clusters Found")
        except err.NoModelDataFound as excep:
            raise
            

        maxOrderedInterestingClusters = None    
        
        keepTracking = True
        #Motion directions for the maximum clusters if we're averaging. We do the same for the anticyclonic (minimum) clusters later
        maxMotions = []
            
        #If a reference cluster is not found, something is wrong. Flag it and stop analysis for case
        if maxReferenceCluster:
            

            
            #Append the reference cluster and time to the running tally
            maxInterestingClusters.append([maxReferenceCluster, maxReferenceTime])
            #Now find all the associated clusters
            currentTrack = maxReferenceCluster.getID()[0]

            timeIndex = self.times.index(maxReferenceTime)
            
            #Calculate the number of seconds to the next time step then calculate the projected points
            
            referenceDT = datetime.strptime(maxReferenceTime.getDT(), '%Y%m%d-%H%M%S')
            nextDT = datetime.strptime(self.times[timeIndex-1].getDT(), '%Y%m%d-%H%M%S')
            
            elapsedTime = abs((referenceDT - nextDT).total_seconds())
            
            maxReferenceCluster.projectCluster(elapsedTime)
            
            #*******************POSITIVE AzShear Backwards***********************************
            #Start by working backwards
            while timeIndex >= 1 and keepTracking:           #Start stop at index 1 because we are checking index - 1
                oldClusters = self.times[timeIndex-1].getMaxShearClusters(lowTilt)
                foundOldTrack = False
                self.cfg.log("Checking clusters at time "+str(self.times[timeIndex-1].getDT()))
                for cluster in oldClusters:
                    #Find the next cluster that needs to be added
                    
                    #First check to see if there is a cluster that matches the current target
                    if cluster.getID()[0] == currentTrack:# and not maxInterestingClusters[-1][0].isReference():    #If the cell from the previous matches the id, that's the one...probably
                        
                        foundOldTrack = True    
                        #If so, check to see if it's valid
                        #Remember to project the reference point for distance and bearing if we have that enabled.
                        projLat, projLon = None, None
                        
                        if self.cfg.projectReference:
                        
                            dt = abs((cluster.getDT() - maxInterestingClusters[-1][0].getDT()).total_seconds())
                            
                            projLat, projLon = maxInterestingClusters[-1][0].getClusterProjection(dt*-1)
                            
                            dist = distance.calculateDistance(cluster.getLatitude()[0], cluster.getLongitude()[0],\
                                        projLat, projLon)
                        
                            bearing = distance.calculateBearingAT(cluster.getLatitude()[0], cluster.getLongitude()[0],\
                                        projLat, projLon)
                                        
                        else:                
                            dist = distance.calculateDistance(cluster.getLatitude()[0], cluster.getLongitude()[0],\
                                            maxInterestingClusters[-1][0].getLatitude()[0], maxInterestingClusters[-1][0].getLongitude()[0])
                            
                            bearing = distance.calculateBearingAT(cluster.getLatitude()[0], cluster.getLongitude()[0],\
                                            maxInterestingClusters[-1][0].getLatitude()[0], maxInterestingClusters[-1][0].getLongitude()[0])
                        
                        if bearing < 0:
                            bearing += 360
                                
                        bearingDev = abs(bearing - maxInterestingClusters[-1][0].getMotionDirection()[0])

                        if bearingDev > 180:
                            bearingDev = 360 - bearingDev
                         
                        if self.cfg.projectReference:
                            self.cfg.log("+backwards Checking next cluster "+str(cluster.getID()[0])+" at "+str(cluster.getLatitude()[0])+" "+str(cluster.getLongitude()[0])+" from projected "+\
                                       str(projLat)+" "+str(projLon)+" "+str(maxInterestingClusters[-1][0].isReference()))
                            self.cfg.log("+backwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(maxInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster.getDT()))
                        else:
                            self.cfg.log("+backwards Checking next cluster "+str(cluster.getID()[0])+" at "+str(cluster.getLatitude()[0])+" "+str(cluster.getLongitude()[0])+" from "+\
                                       str(maxInterestingClusters[-1][0].getID()[0])+" at "+str(maxInterestingClusters[-1][0].getLatitude()[0])+" "+str(maxInterestingClusters[-1][0].getLongitude()[0])+" "+str(maxInterestingClusters[-1][0].isReference()))
                            self.cfg.log("+backwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(maxInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster.getDT()))
                            
                        #If the distance / bearing deviation criteria are met, append the cluster. (Removed the maxInterestingClusters.isReference() check)
                        if dist <= self.cfg.maxShearDist and (bearingDev <= self.cfg.maxBearingDev or dist <= (self.cfg.maxShearDist*self.cfg.shearVectorDistanceFactor)):
                            self.cfg.log("Pass!")
                            clusterA, maxMotions = self.calculateShearMotionVector(cluster, maxInterestingClusters[-1][0], maxMotions)
                            
                            if self.cfg.projectReference:
                                clusterCount = self.getNearbyClusterCount(projLat, projLon, oldClusters, self.cfg.maxShearDist)
                                clusterA.setPotentialClusterCount(clusterCount)
                            else:
                                clusterCount = self.getNearbyClusterCount(maxInterestingClusters[-1][0].getLatitude()[0], maxInterestingClusters[-1][0].getLongitude()[0], oldClusters, self.cfg.maxShearDist)
                                clusterA.setPotentialClusterCount(clusterCount)
                                
                            #Check for model data
                            try:
                                hasModel = self.checkForModel(clusterA)
                            except err.NoModelDataFound as excep:
                                raise
                                
                            maxInterestingClusters.append([clusterA, self.times[timeIndex-1]])
                            timeIndex -= 1
                           
                            currentTrack = clusterA.getID()[0]
                            break
                            
                        else:
                            
                            #If it does not meet the criteria then perform an interest check.
                            bestInterestScore = -99999999
                            bestISCluster = None
                            
                            self.cfg.log("Performing interest check maxBack")
                            
                            for cluster2 in oldClusters:
                                
                                #Note, the cluster2 does not have an updated motion yet so the interest score here won't be ideal
                                #currentScore = self.calculateShearInterest(cluster2, maxInterestingClusters[-1][0], cluster2.getMotionDirection()[0])
                                currentScore = self.calculateShearInterest(cluster2, maxInterestingClusters[-1][0], maxInterestingClusters[-1][0].getMotionDirection()[0], forward=False)
                                
                                self.cfg.log("+backwards Calculated interest score for "+str(cluster2.getID()[0])+" to "+\
                                   str(maxInterestingClusters[-1][0].getID()[0])+" at "+str(maxInterestingClusters[-1][0].getLatitude()[0])+" "+str(maxInterestingClusters[-1][0].getLongitude()[0])+" score "+str(currentScore))
                                   
                                if currentScore:
                                
                                    projLat, projLon = None, None
                                    
                                    if self.cfg.projectReference:
                                    
                                        dt = abs((cluster2.getDT() - maxInterestingClusters[-1][0].getDT()).total_seconds())
                                        
                                        projLat, projLon = maxInterestingClusters[-1][0].getClusterProjection(dt*-1)
                                        
                                        dist = distance.calculateDistance(cluster2.getLatitude()[0], cluster2.getLongitude()[0],\
                                                    projLat, projLon)
                                    
                                        bearing = distance.calculateBearingAT(cluster2.getLatitude()[0], cluster2.getLongitude()[0],\
                                                    projLat, projLon)
                                    
                                    else:
                                        dist = distance.calculateDistance(cluster2.getLatitude()[0], cluster2.getLongitude()[0],\
                                            maxInterestingClusters[-1][0].getLatitude()[0], maxInterestingClusters[-1][0].getLongitude()[0])
                            
                                        bearing = distance.calculateBearingAT(cluster2.getLatitude()[0], cluster2.getLongitude()[0],\
                                            maxInterestingClusters[-1][0].getLatitude()[0], maxInterestingClusters[-1][0].getLongitude()[0])
                                        
                                    if bearing < 0:
                                        bearing += 360
                                        
                                    bearingDev = abs(bearing - maxInterestingClusters[-1][0].getMotionDirection()[0])
                                    
                                    if bearingDev > 180:
                                        bearingDev = 360 - bearingDev
                                        
                                    if self.cfg.projectReference:
                                        self.cfg.log("+backwards Checking next cluster "+str(cluster2.getID()[0])+" at "+str(cluster2.getLatitude()[0])+" "+str(cluster2.getLongitude()[0])+" from projected "+\
                                            str(projLat)+" "+str(projLon)+" "+str(maxInterestingClusters[-1][0].isReference()))
                                        self.cfg.log("+backwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(maxInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster2.getDT()))
                                    else:    
                                        self.cfg.log("+backwards Checking next cluster "+str(cluster2.getID()[0])+" at "+str(cluster2.getLatitude()[0])+" "+str(cluster2.getLongitude()[0])+" from "+\
                                            str(maxInterestingClusters[-1][0].getID()[0])+" at "+str(maxInterestingClusters[-1][0].getLatitude()[0])+" "+str(maxInterestingClusters[-1][0].getLongitude()[0])+" "+str(maxInterestingClusters[-1][0].isReference()))
                                        self.cfg.log("+backwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(maxInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster2.getDT()))
                                        
                                    if currentScore > bestInterestScore and currentScore >= self.cfg.minShearScore and dist <= self.cfg.maxShearDist and (bearingDev <= self.cfg.maxBearingDev or dist <= (self.cfg.maxShearDist*self.cfg.shearVectorDistanceFactor)):
                                        bestInterestScore = currentScore
                                        bestISCluster = cluster2
                                    
                            if bestISCluster:
                                self.cfg.log("Found 1 max! "+str(bestISCluster.getID()[0]))
                                bestISClusterA, maxMotions = self.calculateShearMotionVector(bestISCluster, maxInterestingClusters[-1][0], maxMotions)
                                
                                if self.cfg.projectReference:
                                    clusterCount = self.getNearbyClusterCount(projLat, projLon, oldClusters, self.cfg.maxShearDist)
                                    bestISClusterA.setPotentialClusterCount(clusterCount)
                                else:
                                    clusterCount = self.getNearbyClusterCount(maxInterestingClusters[-1][0].getLatitude()[0], maxInterestingClusters[-1][0].getLongitude()[0], oldClusters, self.cfg.maxShearDist)
                                    bestISClusterA.setPotentialClusterCount(clusterCount)
                                
                                try:
                                    hasModel = self.checkForModel(bestISClusterA)
                                except err.NoModelDataFound as excep:
                                    raise
                                    
                                maxInterestingClusters.append([bestISClusterA, self.times[timeIndex-1]])
                                timeIndex -= 1
                                currentTrack = bestISCluster.getID()[0]
                                break
                            else:
                                self.cfg.log("Didn't find another cluster. Stopping tracking. maxBack")
                                keepTracking = False
                                
                                with open(self.cfg.logName+'_events.csv', 'a') as fi:
                                    fi.write(self.case.storm+','+self.case.ID+','+str(self.case.isTor)+',1,'+str(timeIndex)+',Stopped tracking +backwards with '+str(self.times[timeIndex-1].getDT())+'\n')
                                break
                            
                            
                
                #If we don't have an associated track, then perform the interest check
                if not foundOldTrack:
                    
                    bestInterestScore = -99999999
                    bestISCluster = None
                    
                    self.cfg.log("Performing interest check maxBack2")
                    
                    for cluster2 in oldClusters:
                        #currentScore = self.calculateShearInterest(cluster2, maxInterestingClusters[-1][0], cluster2.getMotionDirection()[0])
                        currentScore = self.calculateShearInterest(cluster2, maxInterestingClusters[-1][0], maxInterestingClusters[-1][0].getMotionDirection()[0], forward=False)
                        if currentScore:
                        
                            projLat, projLon = None, None
                            
                            if self.cfg.projectReference:
                                    
                                dt = abs((cluster2.getDT() - maxInterestingClusters[-1][0].getDT()).total_seconds())
                    
                                projLat, projLon = maxInterestingClusters[-1][0].getClusterProjection(dt*-1)
                                
                                dist = distance.calculateDistance(cluster2.getLatitude()[0], cluster2.getLongitude()[0],\
                                            projLat, projLon)
                            
                                bearing = distance.calculateBearingAT(cluster2.getLatitude()[0], cluster2.getLongitude()[0],\
                                            projLat, projLon)
                            
                            else:
                                dist = distance.calculateDistance(cluster2.getLatitude()[0], cluster2.getLongitude()[0],\
                                    maxInterestingClusters[-1][0].getLatitude()[0], maxInterestingClusters[-1][0].getLongitude()[0])
                    
                                bearing = distance.calculateBearingAT(cluster2.getLatitude()[0], cluster2.getLongitude()[0],\
                                    maxInterestingClusters[-1][0].getLatitude()[0], maxInterestingClusters[-1][0].getLongitude()[0])
                                
                            if bearing < 0:
                                bearing += 360
                                        
                            bearingDev = abs(bearing - maxInterestingClusters[-1][0].getMotionDirection()[0])
     
                            if bearingDev > 180:
                                bearingDev = 360 - bearingDev
                            
                            if self.cfg.projectReference:
                                self.cfg.log("+backwards Checking next cluster "+str(cluster2.getID()[0])+" at "+str(cluster2.getLatitude()[0])+" "+str(cluster2.getLongitude()[0])+" from projected "+\
                                       str(projLat)+" "+str(projLon)+" "+str(maxInterestingClusters[-1][0].isReference()))
                                self.cfg.log("+backwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(maxInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster2.getDT()))
                            else:
                                self.cfg.log("+backwards Checking next cluster "+str(cluster2.getID()[0])+" at "+str(cluster2.getLatitude()[0])+" "+str(cluster2.getLongitude()[0])+" from "+\
                                       str(maxInterestingClusters[-1][0].getID()[0])+" at "+str(maxInterestingClusters[-1][0].getLatitude()[0])+" "+str(maxInterestingClusters[-1][0].getLongitude()[0])+" "+str(maxInterestingClusters[-1][0].isReference()))
                                self.cfg.log("+backwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(maxInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster2.getDT()))
                                        
                            if currentScore > bestInterestScore and currentScore >= self.cfg.minShearScore and dist <= self.cfg.maxShearDist and (bearingDev <= self.cfg.maxBearingDev or dist <= (self.cfg.maxShearDist*self.cfg.shearVectorDistanceFactor)):
                                bestInterestScore = currentScore
                                bestISCluster = cluster2
                            
                    if bestISCluster:
                        self.cfg.log("Found 1 max2! "+str(bestISCluster.getID()[0]))
                        bestISClusterA, maxMotions = self.calculateShearMotionVector(bestISCluster, maxInterestingClusters[-1][0], maxMotions)
                        
                        if self.cfg.projectReference:
                            clusterCount = self.getNearbyClusterCount(projLat, projLon, oldClusters, self.cfg.maxShearDist)
                            bestISClusterA.setPotentialClusterCount(clusterCount)
                        else:
                            clusterCount = self.getNearbyClusterCount(maxInterestingClusters[-1][0].getLatitude()[0], maxInterestingClusters[-1][0].getLongitude()[0], oldClusters, self.cfg.maxShearDist)
                            bestISClusterA.setPotentialClusterCount(clusterCount)
                                    
                        try:
                            hasModel = self.checkForModel(bestISClusterA)
                        except err.NoModelDataFound as excep:
                            raise
                            
                        maxInterestingClusters.append([bestISClusterA, self.times[timeIndex-1]])
                        timeIndex -= 1
                        foundOldTrack = True
                        currentTrack = bestISCluster.getID()[0]
                        
                    else:
                        self.cfg.log("Didn't find another cluster. Stopping tracking maxBack 2")
                        keepTracking = False
                        
                        with open(self.cfg.logName+'_events.csv', 'a') as fi:
                            fi.write(self.case.storm+','+self.case.ID+','+str(self.case.isTor)+',1,'+str(timeIndex)+',Stopped tracking +backwards with '+str(self.times[timeIndex-1].getDT())+'\n')
                                    
                        break
                    
                    
            #********************************POSITIVE AzShear Forwards*****************************
            #Now, work forwards
            timeIndex = self.times.index(maxReferenceTime)
            currentName = maxReferenceCluster.getID()[0]
            
            #self.cfg.error("Listing times")
            # for time in self.times:
                # self.cfg.error(str(time.getDT()))
            #Do a weird and put the reference cluster at the end of the list
            maxInterestingClusters.append(maxInterestingClusters.pop(maxInterestingClusters.index([maxReferenceCluster, maxReferenceTime])))
            
            keepTracking = True
            
            while timeIndex <= (len(self.times) - 2) and keepTracking: #This time we are incrementing foward so we want to stop on the second to last INDEX
                newClusters = self.times[timeIndex+1].getMaxShearClusters(lowTilt)
                # self.cfg.error("Current time "+str(self.times[timeIndex+1].getDT()))
                # self.cfg.error("Previous time "+str(self.times[timeIndex].getDT()))
                # self.cfg.error("Reference time "+str(maxReferenceTime.getDT()))
                foundName = False
                for cluster in newClusters:
                    if cluster.getID()[0] == currentName:# and not cluster.isReference():
                    
                        foundName = True
                        
                        projLat, projLon = None, None
                        
                        if self.cfg.projectReference:
                                    
                            dt = abs((cluster.getDT() - maxInterestingClusters[-1][0].getDT()).total_seconds())
                
                            projLat, projLon = maxInterestingClusters[-1][0].getClusterProjection(dt)
                            
                            dist = distance.calculateDistance(projLat, projLon, cluster.getLatitude()[0], cluster.getLongitude()[0])
                        
                            bearing = distance.calculateBearingAT(projLat, projLon, cluster.getLatitude()[0], cluster.getLongitude()[0])
                        
                        else:
                            dist = distance.calculateDistance(maxInterestingClusters[-1][0].getLatitude()[0], maxInterestingClusters[-1][0].getLongitude()[0],\
                                                            cluster.getLatitude()[0], cluster.getLongitude()[0])
                
                            bearing = distance.calculateBearingAT(maxInterestingClusters[-1][0].getLatitude()[0], maxInterestingClusters[-1][0].getLongitude()[0],\
                                                            cluster.getLatitude()[0], cluster.getLongitude()[0])
                                        
                        
                        if bearing < 0:
                            bearing += 360
                        bearingDev = abs(bearing - maxInterestingClusters[-1][0].getMotionDirection()[0])
                        
                        if self.cfg.projectReference:
                            self.cfg.log("+forwards Checking next cluster "+str(cluster.getID()[0])+" at "+str(cluster.getLatitude()[0])+" "+str(cluster.getLongitude()[0])+" from projected "+\
                                       str(projLat)+" "+str(projLon)+" "+str(maxInterestingClusters[-1][0].isReference()))
                            self.cfg.log("+forwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(maxInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster.getDT()))
                        else:
                            self.cfg.log("+forwards Checking next cluster "+str(cluster.getID()[0])+" at "+str(cluster.getLatitude()[0])+" "+str(cluster.getLongitude()[0])+" from "+\
                                       str(maxInterestingClusters[-1][0].getID()[0])+" at "+str(maxInterestingClusters[-1][0].getLatitude()[0])+" "+str(maxInterestingClusters[-1][0].getLongitude()[0])+" "+str(maxInterestingClusters[-1][0].isReference()))
                            self.cfg.log("+forwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(maxInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster.getDT()))
                        
                        if bearingDev > 180:
                            bearingDev = 360 - bearingDev

                            
                         #If the distance and bearing deviation criteria are met, append the cluster
                        if dist <= self.cfg.maxShearDist and (bearingDev <= self.cfg.maxBearingDev or dist <= (self.cfg.maxShearDist*self.cfg.shearVectorDistanceFactor)):
                            self.cfg.log("Pass!")
                            maxInterestingClusters[-1][0], maxMotions = self.calculateShearMotionVector(maxInterestingClusters[-1][0], cluster, maxMotions)
                            
                            #Because the future cluster's motion is unknown, we'll assume it's the previous cluster's motion for now
                            cluster.setVLat(maxInterestingClusters[-1][0].getVLat()[0])
                            cluster.setVLon(maxInterestingClusters[-1][0].getVLon()[0])
                            cluster.setMotionDirection(maxInterestingClusters[-1][0].getMotionDirection()[0])
                            cluster.setClusterU(maxInterestingClusters[-1][0].getClusterU()[0])
                            cluster.setClusterV(maxInterestingClusters[-1][0].getClusterV()[0])
                            dt = abs((cluster.getDT() - maxInterestingClusters[-1][0].getDT()).total_seconds())
                            cluster.projectCluster(dt)
                            
                            if self.cfg.projectReference:
                                clusterCount = self.getNearbyClusterCount(projLat, projLon, newClusters, self.cfg.maxShearDist)
                                cluster.setPotentialClusterCount(clusterCount)
                            else:
                                clusterCount = self.getNearbyClusterCount(maxInterestingClusters[-1][0].getLatitude()[0], maxInterestingClusters[-1][0].getLongitude()[0], newClusters, self.cfg.maxShearDist)
                                cluster.setPotentialClusterCount(clusterCount)
                                
                            try:
                                hasModel = self.checkForModel(cluster)
                            except err.NoModelDataFound as excep:
                                raise
                                
                            maxInterestingClusters.append([cluster, self.times[timeIndex+1]])
                            timeIndex += 1
                            
                            currentName = cluster.getID()[0]
                            break
                            
                        else:
                            
                            #If it does not meet the criteria then perform an interest check.
                            bestInterestScore = -99999999
                            bestISCluster = None
                            
                            self.cfg.log("Performing interest check maxForward")
                            
                            for cluster2 in newClusters:
                                currentScore = self.calculateShearInterest(maxInterestingClusters[-1][0], cluster2, maxInterestingClusters[-1][0].getMotionDirection()[0], forward=True)
                                if currentScore:
                                    
                                    projLat, projLon = None, None
                                    
                                    if self.cfg.projectReference:
                                    
                                        dt = abs((cluster2.getDT() - maxInterestingClusters[-1][0].getDT()).total_seconds())
                            
                                        projLat, projLon = maxInterestingClusters[-1][0].getClusterProjection(dt)
                                        
                                        dist = distance.calculateDistance(projLat, projLon, cluster2.getLatitude()[0], cluster2.getLongitude()[0])
                                    
                                        bearing = distance.calculateBearingAT(projLat, projLon, cluster2.getLatitude()[0], cluster2.getLongitude()[0])
                                    
                                    else:
                                        dist = distance.calculateDistance(maxInterestingClusters[-1][0].getLatitude()[0], maxInterestingClusters[-1][0].getLongitude()[0],\
                                                                            cluster2.getLatitude()[0], cluster2.getLongitude()[0])
                            
                                        bearing = distance.calculateBearingAT(maxInterestingClusters[-1][0].getLatitude()[0], maxInterestingClusters[-1][0].getLongitude()[0],\
                                                                            cluster2.getLatitude()[0], cluster2.getLongitude()[0])
 
                                    if bearing < 0:
                                        bearing += 360
                                        
                                    bearingDev = abs(bearing - maxInterestingClusters[-1][0].getMotionDirection()[0])
                                    
                                    if bearingDev > 180:
                                        bearingDev = 360 - bearingDev
                                        
                                    if self.cfg.projectReference:    
                                        self.cfg.log("+forwards Checking next cluster "+str(cluster2.getID()[0])+" at "+str(cluster2.getLatitude()[0])+" "+str(cluster2.getLongitude()[0])+" from projected "+\
                                            str(projLat)+" "+str(projLon)+" "+str(maxInterestingClusters[-1][0].isReference()))
                                        self.cfg.log("+forwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(maxInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster2.getDT()))
                                    else:
                                        self.cfg.log("+forwards Checking next cluster "+str(cluster2.getID()[0])+" at "+str(cluster2.getLatitude()[0])+" "+str(cluster2.getLongitude()[0])+" from "+\
                                            str(maxInterestingClusters[-1][0].getID()[0])+" at "+str(maxInterestingClusters[-1][0].getLatitude()[0])+" "+str(maxInterestingClusters[-1][0].getLongitude()[0])+" "+str(maxInterestingClusters[-1][0].isReference()))
                                        self.cfg.log("+forwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(maxInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster2.getDT()))
                                        
                                    if currentScore > bestInterestScore and currentScore >= self.cfg.minShearScore and dist <= self.cfg.maxShearDist and (bearingDev <= self.cfg.maxBearingDev or dist <= (self.cfg.maxShearDist*self.cfg.shearVectorDistanceFactor)):
                                        bestInterestScore = currentScore
                                        bestISCluster = cluster2
                                    
                            if bestISCluster:
                                self.cfg.log("Found 2 max!")
                                
                                maxInterestingClusters[-1][0], maxMotions = self.calculateShearMotionVector(maxInterestingClusters[-1][0], bestISCluster, maxMotions)
                                
                                bestISCluster.setVLat(maxInterestingClusters[-1][0].getVLat()[0])
                                bestISCluster.setVLon(maxInterestingClusters[-1][0].getVLon()[0])
                                bestISCluster.setMotionDirection(maxInterestingClusters[-1][0].getMotionDirection()[0])
                                bestISCluster.setClusterU(maxInterestingClusters[-1][0].getClusterU()[0])
                                bestISCluster.setClusterV(maxInterestingClusters[-1][0].getClusterV()[0])
                                dt = abs((bestISCluster.getDT() - maxInterestingClusters[-1][0].getDT()).total_seconds())
                                bestISCluster.projectCluster(dt)
                                
                                if self.cfg.projectReference:
                                    clusterCount = self.getNearbyClusterCount(projLat, projLon, newClusters, self.cfg.maxShearDist)
                                    bestISCluster.setPotentialClusterCount(clusterCount)
                                else:
                                    clusterCount = self.getNearbyClusterCount(maxInterestingClusters[-1][0].getLatitude()[0], maxInterestingClusters[-1][0].getLongitude()[0], newClusters, self.cfg.maxShearDist)
                                    bestISCluster.setPotentialClusterCount(clusterCount)
                                
                                try:
                                    hasModel = self.checkForModel(bestISCluster)
                                except err.NoModelDataFound as excep:
                                    raise
                                
                                maxInterestingClusters.append([bestISCluster, self.times[timeIndex+1]])
                                timeIndex += 1
                                foundName = True
                                currentName = bestISCluster.getID()[0]
                                break
                            else:
                                self.cfg.log("Didn't find another cluster. Will stop tracking. maxForward")
                                keepTracking = False
                                
                                with open(self.cfg.logName+'_events.csv', 'a') as fi:
                                    fi.write(self.case.storm+','+self.case.ID+','+str(self.case.isTor)+',2,'+str(len(self.times) - int(timeIndex))+',Stopped tracking +forwards with '+str(self.times[timeIndex+1].getDT())+'\n')
                                break
                                
                
                #If we don't have an associated track, then stop looking foward
                if not foundName:
                    
                    bestInterestScore = -99999999
                    bestISCluster = None
                    
                    self.cfg.log("Performing interest check maxForward 2")
                    
                    for cluster2 in newClusters:
                        currentScore = self.calculateShearInterest(maxInterestingClusters[-1][0], cluster2, maxInterestingClusters[-1][0].getMotionDirection()[0], forward=True)
                        if currentScore:
                        
                            projLat, projLon = None, None
                            
                            if self.cfg.projectReference:
                                    
                                dt = abs((cluster2.getDT() - maxInterestingClusters[-1][0].getDT()).total_seconds())
                    
                                projLat, projLon = maxInterestingClusters[-1][0].getClusterProjection(dt)
                                
                                dist = distance.calculateDistance(projLat, projLon, cluster2.getLatitude()[0], cluster2.getLongitude()[0])
                            
                                bearing = distance.calculateBearingAT(projLat, projLon, cluster2.getLatitude()[0], cluster2.getLongitude()[0])
                            
                            else:
                                dist = distance.calculateDistance(maxInterestingClusters[-1][0].getLatitude()[0], maxInterestingClusters[-1][0].getLongitude()[0],\
                                                                    cluster2.getLatitude()[0], cluster2.getLongitude()[0])
                    
                                bearing = distance.calculateBearingAT(maxInterestingClusters[-1][0].getLatitude()[0], maxInterestingClusters[-1][0].getLongitude()[0],\
                                                                      cluster2.getLatitude()[0], cluster2.getLongitude()[0])
                                        
                            if bearing < 0:
                                bearing += 360
                                
                            bearingDev = abs(bearing - maxInterestingClusters[-1][0].getMotionDirection()[0])
                            
                            if bearingDev > 180:
                                bearingDev = 360 - bearingDev
                                
                            
                            if self.cfg.projectReference:
                                self.cfg.log("+forwards Checking next cluster "+str(cluster2.getID()[0])+" at "+str(cluster2.getLatitude()[0])+" "+str(cluster2.getLongitude()[0])+" from projected "+\
                                       str(projLat)+" "+str(projLon)+" "+str(maxInterestingClusters[-1][0].isReference()))
                                self.cfg.log("+forwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(maxInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster2.getDT()))
                            else:
                                self.cfg.log("+forwards Checking next cluster "+str(cluster2.getID()[0])+" at "+str(cluster2.getLatitude()[0])+" "+str(cluster2.getLongitude()[0])+" from "+\
                                       str(maxInterestingClusters[-1][0].getID()[0])+" at "+str(maxInterestingClusters[-1][0].getLatitude()[0])+" "+str(maxInterestingClusters[-1][0].getLongitude()[0])+" "+str(maxInterestingClusters[-1][0].isReference()))
                                self.cfg.log("+forwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(maxInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster2.getDT()))
                                
                            if currentScore > bestInterestScore and currentScore >= self.cfg.minShearScore and dist <= self.cfg.maxShearDist and (bearingDev <= self.cfg.maxBearingDev or dist <= (self.cfg.maxShearDist*self.cfg.shearVectorDistanceFactor)):
                                bestInterestScore = currentScore
                                bestISCluster = cluster2
                            
                    if bestISCluster:
                        self.cfg.log("Found 2 max2 !"+str(bestISCluster.getID()[0]))
                        maxInterestingClusters[-1][0], maxMotions = self.calculateShearMotionVector(maxInterestingClusters[-1][0], bestISCluster, maxMotions)
                                
                        bestISCluster.setVLat(maxInterestingClusters[-1][0].getVLat()[0])
                        bestISCluster.setVLon(maxInterestingClusters[-1][0].getVLon()[0])
                        bestISCluster.setMotionDirection(maxInterestingClusters[-1][0].getMotionDirection()[0])
                        bestISCluster.setClusterU(maxInterestingClusters[-1][0].getClusterU()[0])
                        bestISCluster.setClusterV(maxInterestingClusters[-1][0].getClusterV()[0])
                        dt = abs((bestISCluster.getDT() - maxInterestingClusters[-1][0].getDT()).total_seconds())
                        bestISCluster.projectCluster(dt)
                        
                        if self.cfg.projectReference:
                            clusterCount = self.getNearbyClusterCount(projLat, projLon, newClusters, self.cfg.maxShearDist)
                            bestISCluster.setPotentialClusterCount(clusterCount)
                        else:
                            clusterCount = self.getNearbyClusterCount(maxInterestingClusters[-1][0].getLatitude()[0], maxInterestingClusters[-1][0].getLongitude()[0], newClusters, self.cfg.maxShearDist)
                            bestISCluster.setPotentialClusterCount(clusterCount)
                        
                        try:
                            hasModel = self.checkForModel(bestISCluster)
                        except err.NoModelDataFound as excep:
                            raise
                        
                        maxInterestingClusters.append([bestISCluster, self.times[timeIndex+1]])
                        
                        timeIndex += 1
                        foundName = True
                        currentName = bestISCluster.getID()[0]
                        break
                    else:
                        self.cfg.log("Didn't find another cluster. Stopping tracking. maxForward 2")
                        
                        keepTracking = False
                        
                        with open(self.cfg.logName+'_events.csv', 'a') as fi:
                            fi.write(self.case.storm+','+self.case.ID+','+str(self.case.isTor)+',2,'+str(len(self.times) - int(timeIndex))+',Stopped tracking +forwards with '+str(self.times[timeIndex+1].getDT())+'\n')
                                    
                        break
            
            
            maxOrderedInterestingClusters = [cluster[0] for cluster in self.reorderClusters(maxInterestingClusters)]
            
            #Force a projection on the last cluster.
            time1 = self.times[len(self.times)-2]
            time2 = self.times[len(self.times)-1]
            
            finalElapsedTime = abs((datetime.strptime(time2.getDT(), '%Y%m%d-%H%M%S') - datetime.strptime(time1.getDT(), '%Y%m%d-%H%M%S')).total_seconds())
            
            maxOrderedInterestingClusters[-1].projectCluster(finalElapsedTime)
            
            # for susClus in maxOrderedInterestingClusters:
                # self.cfg.error("max Ordered interesting clusters check "+str(susClus.getDT()))
                
        else:
            self.cfg.error("Warning! Max reference cluster not found for case "+str(self.case.storm)+"/"+str(self.case.ID))
            
        
       
        
        #************************NEGATIVE AzShear Reference***************************
        #Repeat the same chunk of code, but replace all the max tags with min (if I was doing this right, I would make another function)
        minInterestingClusters = []
        minReferenceCluster = None     #This is the cluster that first contains the report
        minReferenceTime = None        #This is the time of the reference cluster)
        minReferenceClusters = {}
        
        lowTilt = self.cfg.tiltList[0]
        
        #Find the min AzShear reference cluster
        for time in self.times:
            clusters = []
            for cluster in time.getMinShearClusters(lowTilt):
                if cluster.getNumReports()[0] is not None:
                    if int(float(cluster.getNumReports()[0])) > 0: 
                        clusters.append(cluster)
                        minReferenceTime = time
                        self.cfg.log("Reference cluster found! "+str(len(minReferenceClusters)))
            
            minReferenceClusters[time] = clusters
            
        try:
            minReferenceCluster, minReferenceTime = self.getBestCluster(minReferenceClusters, isMax=False)
        except err.NoReferenceClusterFoundException:
            self.cfg.error("No min reference clusters found for lowest level AzShear!")
            raise err.NoReferenceClusterFoundException("No Min Reference Clusters Found")
        except err.NoModelDataFound as excep:
            raise
            
        minOrderedInterestingClusters = None    
        minMotions = []
        
        #If a reference cluster is not found, something is wrong. Flag it and stop analysis for case
        if minReferenceCluster:
            
            
            #Append the reference cluster and time to the running tally
            minInterestingClusters.append([minReferenceCluster, minReferenceTime])
            #Now find all the associated clusters
            currentTrack = minReferenceCluster.getID()[0]
            
            timeIndex = self.times.index(minReferenceTime)
            
            keepTracking = True
            
            #Get the neccessary information to project the initial min reference cluster
            referenceDT = datetime.strptime(minReferenceTime.getDT(), '%Y%m%d-%H%M%S')
            nextDT = datetime.strptime(self.times[timeIndex-1].getDT(), '%Y%m%d-%H%M%S')
            
            elapsedTime = abs((referenceDT - nextDT).total_seconds())
            
            minReferenceCluster.projectCluster(elapsedTime)
            
            
            #****************************Negative AzShear Backwards***********************************
            #Start by working backwards
            while timeIndex >= 1 and keepTracking:           #Start stop at index 1 because we are checking index - 1
                oldClusters = self.times[timeIndex-1].getMinShearClusters(lowTilt)
                foundOldTrack = False
                for cluster in oldClusters:
                    if cluster.getID()[0] == currentTrack:# and not minInterestingClusters[-1][0].isReference():    #If the cell from the previous matches the id, that's the one...probably
                        
                        foundOldTrack = True
                        
                        #If so, check to see if it's valid
                        #Remember to project the references if we're setup for that
                        
                        projLat, projLon = None, None
                        
                        if self.cfg.projectReference:
                        
                            dt = abs((cluster.getDT() - minInterestingClusters[-1][0].getDT()).total_seconds())
                
                            projLat, projLon = minInterestingClusters[-1][0].getClusterProjection(dt*-1)
                            
                            dist = distance.calculateDistance(projLat, projLon,\
                                            minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0])
                            
                            
                            bearing = distance.calculateBearingAT(projLat, projLon,\
                                            minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0])
                        else:
                        
                            dist = distance.calculateDistance(cluster.getLatitude()[0], cluster.getLongitude()[0],\
                                            minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0])
                            
                            
                            bearing = distance.calculateBearingAT(cluster.getLatitude()[0], cluster.getLongitude()[0],\
                                            minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0])
                                            
                        if bearing < 0:
                            bearing += 360
                                
                        bearingDev = abs(bearing - minInterestingClusters[-1][0].getMotionDirection()[0])
                        
                        if self.cfg.projectReference:
                            self.cfg.log("-backwards Checking next cluster "+str(cluster.getID()[0])+" at "+str(cluster.getLatitude()[0])+" "+str(cluster.getLongitude()[0])+" from projected "+\
                                       str(projLat)+" "+str(projLon)+" "+str(minInterestingClusters[-1][0].isReference()))
                            self.cfg.log("-backwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(minInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster.getDT()))
                        else:
                            self.cfg.log("-backwards Checking next cluster "+str(cluster.getID()[0])+" at "+str(cluster.getLatitude()[0])+" "+str(cluster.getLongitude()[0])+" from "+\
                                       str(minInterestingClusters[-1][0].getID()[0])+" at "+str(minInterestingClusters[-1][0].getLatitude()[0])+" "+str(minInterestingClusters[-1][0].getLongitude()[0])+" "+str(minInterestingClusters[-1][0].isReference()))
                            self.cfg.log("-backwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(minInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster.getDT()))
                        
                        if bearingDev > 180:
                            bearingDev = 360 - bearingDev
                            
                        #If the distance and bearing deviation criteria  are met, append the cluster
                        if dist <= self.cfg.maxShearDist and (bearingDev <= self.cfg.maxBearingDev or dist <= (self.cfg.maxShearDist*self.cfg.shearVectorDistanceFactor) or dist <= (self.cfg.maxShearDist*self.cfg.shearVectorDistanceFactor)):
                            self.cfg.log("Pass!")
                            cluster, minMotions = self.calculateShearMotionVector(cluster, minInterestingClusters[-1][0], minMotions)
                            
                            if self.cfg.projectReference:
                                clusterCount = self.getNearbyClusterCount(projLat, projLon, oldClusters, self.cfg.maxShearDist)
                                cluster.setPotentialClusterCount(clusterCount)
                            else:
                                clusterCount = self.getNearbyClusterCount(minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0], oldClusters, self.cfg.maxShearDist)
                                cluster.setPotentialClusterCount(clusterCount)
                                
                            try:
                                hasModel = self.checkForModel(cluster)
                            except err.NoModelDataFound as excep:
                                return
                                
                            minInterestingClusters.append([cluster, self.times[timeIndex-1]])
                            timeIndex -= 1
                            
                            currentTrack = cluster.getID()[0]
                            break
                            
                        else:
                            
                            #If it does not meet the criteria then perform an interest check.
                            bestInterestScore = -99999999
                            bestISCluster = None
                            
                            self.cfg.log("Performing interest check minBack")
                            
                            for cluster2 in oldClusters:
                            
                                #Note, the cluster2 does not have an updated motion yet so the interest score here won't be ideal
                                #currentScore = self.calculateShearInterest(cluster2, minInterestingClusters[-1][0], cluster2.getMotionDirection()[0])
                                #currentScore = self.calculateShearInterest(minInterestingClusters[-1][0], cluster2, minInterestingClusters[-1][0].getMotionDirection()[0], forward=False)
                                currentScore = self.calculateShearInterest(cluster2, minInterestingClusters[-1][0], minInterestingClusters[-1][0].getMotionDirection()[0], forward=False)
                                
                                self.cfg.log("-backwards Calculated interest score for "+str(cluster2.getID()[0])+" at "+str(cluster2.getLatitude()[0])+" "+str(cluster2.getLongitude()[0])+" for "+\
                                   str(minInterestingClusters[-1][0].getID()[0])+" at "+str(minInterestingClusters[-1][0].getLatitude()[0])+" "+str(minInterestingClusters[-1][0].getLongitude()[0])+" score "+str(currentScore))
                                   
                                if currentScore:
                                
                                    if self.cfg.projectReference:
                        
                                        dt = abs((cluster2.getDT() - minInterestingClusters[-1][0].getDT()).total_seconds())
                            
                                        projLat, projLon = minInterestingClusters[-1][0].getClusterProjection(dt*-1)
                                        
                                        dist = distance.calculateDistance(projLat, projLon,\
                                                        minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0])
                                        
                                        
                                        bearing = distance.calculateBearingAT(projLat, projLon,\
                                                        minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0])
                                    else:
                                    
                                        dist = distance.calculateDistance(cluster2.getLatitude()[0], cluster2.getLongitude()[0],\
                                                        minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0])
                                        
                                        
                                        bearing = distance.calculateBearingAT(cluster2.getLatitude()[0], cluster2.getLongitude()[0],\
                                                        minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0])
                                        
                                    if bearing < 0:
                                        bearing += 360
                                        
                                    bearingDev = abs(bearing - minInterestingClusters[-1][0].getMotionDirection()[0])
                                    
                                    if bearingDev > 180:
                                        bearingDev = 360 - bearingDev
                                    
                                    if self.cfg.projectReference:
                                        self.cfg.log("-backwards Checking next cluster "+str(cluster2.getID()[0])+" "+str(cluster2.getLatitude()[0])+" "+str(cluster2.getLongitude()[0])+" from projected "+\
                                            str(projLat)+" "+str(projLon)+" "+str(minInterestingClusters[-1][0].isReference()))
                                        self.cfg.log("-backwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(minInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster2.getDT()))
                                        
                                    else:
                                        self.cfg.log("-backwards Checking next cluster "+str(cluster2.getID()[0])+" at "+str(cluster2.getLatitude()[0])+" "+str(cluster2.getLongitude()[0])+" from "+\
                                            str(minInterestingClusters[-1][0].getID()[0])+" at "+str(minInterestingClusters[-1][0].getLatitude()[0])+" "+str(minInterestingClusters[-1][0].getLongitude()[0])+" "+str(minInterestingClusters[-1][0].isReference()))
                                        self.cfg.log("-backwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(minInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster2.getDT()))
                                    
                                    if currentScore > bestInterestScore and currentScore >= self.cfg.minShearScore and dist <= self.cfg.maxShearDist and (bearingDev <= self.cfg.maxBearingDev or dist <= (self.cfg.maxShearDist*self.cfg.shearVectorDistanceFactor)):
                                        bestInterestScore = currentScore
                                        bestISCluster = cluster2
                                    
                            if bestISCluster:
                                self.cfg.log("Found 1 min !"+str(bestISCluster.getID()[0]))
                                
                                bestIsCluster, minMotions = self.calculateShearMotionVector(bestISCluster, minInterestingClusters[-1][0], minMotions)
                                
                                if self.cfg.projectReference:
                                    clusterCount = self.getNearbyClusterCount(projLat, projLon, oldClusters, self.cfg.maxShearDist)
                                    bestISCluster.setPotentialClusterCount(clusterCount)
                                else:
                                    clusterCount = self.getNearbyClusterCount(minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0], oldClusters, self.cfg.maxShearDist)
                                    bestISCluster.setPotentialClusterCount(clusterCount)
                                
                                try:
                                    hasModel = self.checkForModel(bestISCluster)
                                except err.NoModelDataFound as excep:
                                    raise
                                    
                                minInterestingClusters.append([bestISCluster, self.times[timeIndex-1]])
                                timeIndex -= 1
                                foundOldTrack = True
                                currentTrack = bestISCluster.getID()[0]
                                break
                            else:
                                self.cfg.log("Didn't find another cluster. Stopping tracking. minBack")
                                keepTracking = False
                                
                                with open(self.cfg.logName+'_events.csv', 'a') as fi:
                                    fi.write(self.case.storm+','+self.case.ID+','+str(self.case.isTor)+',3,'+str(timeIndex)+',Stopped tracking -backwards with '+str(self.times[timeIndex-1].getDT())+'\n')
                                    
                                break
                            
                            
                
                #If we don't have an associated track, then perform the interest check
                if not foundOldTrack:
                    
                    bestInterestScore = -99999999
                    bestISCluster = None
                    
                    self.cfg.log("Performing interest check minBack2")
                    
                    for cluster2 in oldClusters:
                    
                        #Note, the cluster2 does not have an updated motion yet so the interest score here won't be ideal
                        #currentScore = self.calculateShearInterest(cluster2, minInterestingClusters[-1][0], cluster2.getMotionDirection()[0])
                        #currentScore = self.calculateShearInterest(minInterestingClusters[-1][0], cluster2, minInterestingClusters[-1][0].getMotionDirection()[0], forward=False)
                        currentScore = self.calculateShearInterest(cluster2, minInterestingClusters[-1][0], minInterestingClusters[-1][0].getMotionDirection()[0], forward=False)
                        
                        self.cfg.log("-backwards Calculated interest score for "+str(cluster2.getID()[0])+" at "+str(cluster2.getLatitude()[0])+" "+str(cluster2.getLongitude()[0])+" for "+\
                           str(minInterestingClusters[-1][0].getID()[0])+" at "+str(minInterestingClusters[-1][0].getLatitude()[0])+" "+str(minInterestingClusters[-1][0].getLongitude()[0])+" score "+str(currentScore))
                           
                        if currentScore:
                                
                            projLat, projLon = None, None
                            
                            if self.cfg.projectReference:
                        
                                dt = abs((cluster2.getDT() - minInterestingClusters[-1][0].getDT()).total_seconds())
                    
                                projLat, projLon = minInterestingClusters[-1][0].getClusterProjection(dt*-1)
                                
                                dist = distance.calculateDistance(projLat, projLon,\
                                                minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0])
                                
                                
                                bearing = distance.calculateBearingAT(projLat, projLon,\
                                                minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0])
                            else:
                            
                                dist = distance.calculateDistance(cluster2.getLatitude()[0], cluster2.getLongitude()[0],\
                                                minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0])
                                
                                
                                bearing = distance.calculateBearingAT(cluster2.getLatitude()[0], cluster2.getLongitude()[0],\
                                                minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0])
                                        
                                
                            if bearing < 0:
                                bearing += 360
                                
                            bearingDev = abs(bearing - minInterestingClusters[-1][0].getMotionDirection()[0])
                            
                            if bearingDev > 180:
                                bearingDev = 360 - bearingDev
                             
                            if self.cfg.projectReference:
                                self.cfg.log("-backwards Checking next cluster "+str(cluster2.getID()[0])+" project at "+str(cluster2.getLatitude()[0])+" "+str(cluster2.getLongitude()[0])+" from projected "+\
                                       str(projLat)+" "+str(projLon)+" "+str(minInterestingClusters[-1][0].isReference()))
                                self.cfg.log("-backwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(minInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster2.getDT()))
                            else:
                                self.cfg.log("-backwards Checking next cluster "+str(cluster2.getID()[0])+" at "+str(cluster2.getLatitude()[0])+" "+str(cluster2.getLongitude()[0])+" from "+\
                                       str(minInterestingClusters[-1][0].getID()[0])+" at "+str(minInterestingClusters[-1][0].getLatitude()[0])+" "+str(minInterestingClusters[-1][0].getLongitude()[0])+" "+str(minInterestingClusters[-1][0].isReference()))
                                self.cfg.log("-backwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(minInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster2.getDT()))
                            
                            if currentScore > bestInterestScore and currentScore >= self.cfg.minShearScore and dist <= self.cfg.maxShearDist and (bearingDev <= self.cfg.maxBearingDev or dist <= (self.cfg.maxShearDist*self.cfg.shearVectorDistanceFactor)):
                                bestInterestScore = currentScore
                                bestISCluster = cluster2
                        
                    if bestISCluster:
                        self.cfg.log("Found 1 min2! "+str(bestISCluster.getID()[0]))
                        bestIsCluster, minMotions = self.calculateShearMotionVector(bestISCluster, minInterestingClusters[-1][0], minMotions)
                        
                        if self.cfg.projectReference:
                            clusterCount = self.getNearbyClusterCount(projLat, projLon, oldClusters, self.cfg.maxShearDist)
                            bestISCluster.setPotentialClusterCount(clusterCount)
                        else:
                            clusterCount = self.getNearbyClusterCount(minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0], oldClusters, self.cfg.maxShearDist)
                            bestISCluster.setPotentialClusterCount(clusterCount)
                        
                        try:
                            hasModel = self.checkForModel(bestISCluster)
                        except err.NoModelDataFound as excep:
                            raise
                            
                        minInterestingClusters.append([bestISCluster, self.times[timeIndex-1]])
                        timeIndex -= 1
                        foundOldTrack = True
                        currentTrack = bestISCluster.getID()[0]
                        break
                    else:
                        self.cfg.log("Didn't find another cluster. Stopping tracking minBack 2")
                        keepTracking = False
                        
                        with open(self.cfg.logName+'_events.csv', 'a') as fi:
                            fi.write(self.case.storm+','+self.case.ID+','+str(self.case.isTor)+',3,'+str(timeIndex)+',Stopped tracking -backwards with '+str(self.times[timeIndex-1].getDT())+'\n')
                                    
                        break
                
            #***************************Negative AzShear Forwards*****************************        
            #Now, work forwards
            timeIndex = self.times.index(minReferenceTime)
            currentName = minReferenceCluster.getID()[0]
            
            minInterestingClusters.append(minInterestingClusters.pop(minInterestingClusters.index([minReferenceCluster, minReferenceTime])))
            
            keepTracking = True
            
            while timeIndex <= (len(self.times) - 2) and keepTracking: #This time we are incrementing foward so we want to stop on the second to last INDEX
                newClusters = self.times[timeIndex+1].getMinShearClusters(lowTilt)
                foundName = False
                for cluster in newClusters:
                    if cluster.getID()[0] == currentName:# and not cluster.isReference():
                    
                        foundName = True
                        
                        projLat, projLon = None, None
                        
                        if self.cfg.projectReference:
                                    
                            dt = abs((cluster.getDT() - minInterestingClusters[-1][0].getDT()).total_seconds())
                
                            projLat, projLon = minInterestingClusters[-1][0].getClusterProjection(dt)
                            
                            dist = distance.calculateDistance(projLat, projLon, cluster.getLatitude()[0], cluster.getLongitude()[0])
                        
                            bearing = distance.calculateBearingAT(projLat, projLon, cluster.getLatitude()[0], cluster.getLongitude()[0])
                        
                        else:
                            dist = distance.calculateDistance(minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0],\
                                                            cluster.getLatitude()[0], cluster.getLongitude()[0])
                
                            bearing = distance.calculateBearingAT(minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0],\
                                                            cluster.getLatitude()[0], cluster.getLongitude()[0])
                                        
                        
                        if bearing < 0:
                            bearing += 360
                            
                        bearingDev = abs(bearing - minInterestingClusters[-1][0].getMotionDirection()[0])
                        
                        if self.cfg.projectReference:
                            self.cfg.log("-forwards Checking next cluster "+str(cluster.getID()[0])+" at "+str(cluster.getLatitude()[0])+" "+str(cluster.getLongitude()[0])+" from projected "+\
                                       str(projLat)+" "+str(projLon)+" "+str(minInterestingClusters[-1][0].isReference()))
                            self.cfg.log("-forwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(minInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster.getDT()))
                        
                        else:
                            self.cfg.log("-forwards Checking next cluster "+str(cluster.getID()[0])+" at "+str(cluster.getLatitude()[0])+" "+str(cluster.getLongitude()[0])+" from "+\
                                   str(minInterestingClusters[-1][0].getID()[0])+" at "+str(minInterestingClusters[-1][0].getLatitude()[0])+" "+str(minInterestingClusters[-1][0].getLongitude()[0])+" "+str(minInterestingClusters[-1][0].isReference()))
                            self.cfg.log("-forwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(minInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster.getDT()))
                        
                        if bearingDev > 180:
                            bearingDev = 360 - bearingDev
                            
                        #If the distance and bearing deviation criteria are met, append the cluster
                        if dist <= self.cfg.maxShearDist and (bearingDev <= self.cfg.maxBearingDev or dist <= (self.cfg.maxShearDist*self.cfg.shearVectorDistanceFactor)):
                            minInterestingClusters[-1][0], minMotions = self.calculateShearMotionVector(minInterestingClusters[-1][0], cluster, minMotions)
                            
                            #Because the future cluster's motion is unknown, we'll assume it's the previous cluster's motion for now
                            cluster.setVLat(minInterestingClusters[-1][0].getVLat()[0])
                            cluster.setVLon(minInterestingClusters[-1][0].getVLon()[0])
                            cluster.setMotionDirection(minInterestingClusters[-1][0].getMotionDirection()[0])
                            cluster.setClusterU(minInterestingClusters[-1][0].getClusterU()[0])
                            cluster.setClusterV(minInterestingClusters[-1][0].getClusterV()[0])
                            dt = abs((cluster.getDT() - minInterestingClusters[-1][0].getDT()).total_seconds())
                            cluster.projectCluster(dt)
                                
                            if self.cfg.projectReference:
                                clusterCount = self.getNearbyClusterCount(projLat, projLon, newClusters, self.cfg.maxShearDist)
                                cluster.setPotentialClusterCount(clusterCount)
                            else:
                                clusterCount = self.getNearbyClusterCount(minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0], newClusters, self.cfg.maxShearDist)
                                cluster.setPotentialClusterCount(clusterCount)
                            
                            try:    
                                hasModel = self.checkForModel(cluster)
                            except err.NoModelDataFound as excep:
                                raise
                            
                            minInterestingClusters.append([cluster, self.times[timeIndex+1]])
                            timeIndex += 1
                            
                            currentName = cluster.getID()[0]
                            break
                            
                        else:
                            
                            #If it does not meet the criteria then perform an interest check.
                            bestInterestScore = -99999999
                            bestISCluster = None
                            
                            self.cfg.log("Performing interest check minForward")
                            
                            for cluster2 in newClusters:
                                currentScore = self.calculateShearInterest(minInterestingClusters[-1][0], cluster2, minInterestingClusters[-1][0].getMotionDirection()[0], forward=True)
                                if currentScore:
                                
                                    projLat, projLon = None, None
                        
                                    if self.cfg.projectReference:
                                                
                                        dt = abs((cluster2.getDT() - minInterestingClusters[-1][0].getDT()).total_seconds())
                            
                                        projLat, projLon = minInterestingClusters[-1][0].getClusterProjection(dt)
                                        
                                        dist = distance.calculateDistance(projLat, projLon, cluster2.getLatitude()[0], cluster2.getLongitude()[0])
                                    
                                        bearing = distance.calculateBearingAT(projLat, projLon, cluster2.getLatitude()[0], cluster2.getLongitude()[0])
                                    
                                    else:
                                        dist = distance.calculateDistance(minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0],\
                                                                        cluster2.getLatitude()[0], cluster2.getLongitude()[0])
                            
                                        bearing = distance.calculateBearingAT(minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0],\
                                                                        cluster2.getLatitude()[0], cluster2.getLongitude()[0])
                                    
                                    if self.cfg.projectReference:
                                    
                                        self.cfg.log("-forwards Checking next cluster "+str(cluster2.getID()[0])+" at "+str(cluster2.getLatitude()[0])+" "+str(cluster2.getLongitude()[0])+" from projected "+\
                                            str(projLat)+" "+str(projLon)+" "+str(minInterestingClusters[-1][0].isReference()))
                                        self.cfg.log("-forwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(minInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster2.getDT()))
                                    
                                    else:
                                        self.cfg.log("-forwards Checking next cluster "+str(cluster2.getID()[0])+" at "+str(cluster2.getLatitude()[0])+" "+str(cluster2.getLongitude()[0])+" from "+\
                                            str(minInterestingClusters[-1][0].getID()[0])+" at "+str(minInterestingClusters[-1][0].getLatitude()[0])+" "+str(minInterestingClusters[-1][0].getLongitude()[0])+" "+str(minInterestingClusters[-1][0].isReference()))
                                        self.cfg.log("-forwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(minInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster2.getDT()))
                                        
                                    if currentScore > bestInterestScore and currentScore >= self.cfg.minShearScore and dist <= self.cfg.maxShearDist and (bearingDev <= self.cfg.maxBearingDev or dist <= (self.cfg.maxShearDist*self.cfg.shearVectorDistanceFactor)):
                                        bestInterestScore = currentScore
                                        bestISCluster = cluster2
                                    
                            if bestISCluster:
                                self.cfg.log("Found 2 min!")
                                
                                minInterestingClusters[-1][0], minMotions = self.calculateShearMotionVector(minInterestingClusters[-1][0], bestISCluster, minMotions)
                                
                                bestISCluster.setVLat(minInterestingClusters[-1][0].getVLat()[0])
                                bestISCluster.setVLon(minInterestingClusters[-1][0].getVLon()[0])
                                bestISCluster.setMotionDirection(minInterestingClusters[-1][0].getMotionDirection()[0])
                                bestISCluster.setClusterU(minInterestingClusters[-1][0].getClusterU()[0])
                                bestISCluster.setClusterV(minInterestingClusters[-1][0].getClusterV()[0])
                                dt = abs((bestISCluster.getDT() - minInterestingClusters[-1][0].getDT()).total_seconds())
                                bestISCluster.projectCluster(dt)
                                
                                if self.cfg.projectReference:
                                    clusterCount = self.getNearbyClusterCount(projLat, projLon, newClusters, self.cfg.maxShearDist)
                                    bestISCluster.setPotentialClusterCount(clusterCount)
                                else:
                                    clusterCount = self.getNearbyClusterCount(minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0], newClusters, self.cfg.maxShearDist)
                                    bestISCluster.setPotentialClusterCount(clusterCount)
                            
                                
                                try:
                                    hasModel = self.checkForModel(bestISCluster)
                                except err.NoModelDataFound as excep:
                                    raise
                                    
                                minInterestingClusters.append([bestISCluster, self.times[timeIndex+1]])
                                timeIndex += 1
                                foundName = True
                                currentName = bestISCluster.getID()[0]
                                break
                            else:
                                self.cfg.log("Didn't find another cluster. Stopping tracking. minForward")
                                keepTracking = False
                                
                                with open(self.cfg.logName+'_events.csv', 'a') as fi:
                                    fi.write(self.case.storm+','+self.case.ID+','+str(self.case.isTor)+',4,'+str(len(self.times) - int(timeIndex))+',Stopped tracking -forwards with '+str(self.times[timeIndex+1].getDT())+'\n')
                                    
                                break
                                
                
                #If we don't have an associated track, then stop looking foward
                if not foundName:
                   
                    bestInterestScore = -99999999
                    bestISCluster = None
                    
                    self.cfg.log("Performing interest check minForward 2")
                    
                    for cluster2 in newClusters:
                        currentScore = self.calculateShearInterest(minInterestingClusters[-1][0], cluster2, minInterestingClusters[-1][0].getMotionDirection()[0], forward=True)
                        if currentScore:
                        
                            projLat, projLon = None, None
                        
                            if self.cfg.projectReference:
                                        
                                dt = abs((cluster2.getDT() - minInterestingClusters[-1][0].getDT()).total_seconds())
                    
                                projLat, projLon = minInterestingClusters[-1][0].getClusterProjection(dt)
                                
                                dist = distance.calculateDistance(projLat, projLon, cluster2.getLatitude()[0], cluster2.getLongitude()[0])
                            
                                bearing = distance.calculateBearingAT(projLat, projLon, cluster2.getLatitude()[0], cluster2.getLongitude()[0])
                            
                            else:
                                dist = distance.calculateDistance(minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0],\
                                                                cluster2.getLatitude()[0], cluster2.getLongitude()[0])
                    
                                bearing = distance.calculateBearingAT(minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0],\
                                                                cluster2.getLatitude()[0], cluster2.getLongitude()[0])
                                        
                            if bearing < 0:
                                bearing += 360
                                
                            bearingDev = abs(bearing - minInterestingClusters[-1][0].getMotionDirection()[0])
                            
                            if bearingDev > 180:
                                bearingDev = 360 - bearingDev
                            
                            if self.cfg.projectReference:
                                self.cfg.log("-forwards Checking next cluster "+str(cluster2.getID()[0])+" at "+str(cluster2.getLatitude()[0])+" "+str(cluster2.getLongitude()[0])+" from "+\
                                       str(projLat)+" "+str(projLon)+" "+str(minInterestingClusters[-1][0].isReference()))
                                self.cfg.log("-forwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(minInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster2.getDT()))
                            else:
                                self.cfg.log("-forwards Checking next cluster "+str(cluster2.getID()[0])+" at "+str(cluster2.getLatitude()[0])+" "+str(cluster2.getLongitude()[0])+" from "+\
                                   str(minInterestingClusters[-1][0].getID()[0])+" at "+str(minInterestingClusters[-1][0].getLatitude()[0])+" "+str(minInterestingClusters[-1][0].getLongitude()[0])+" "+str(minInterestingClusters[-1][0].isReference()))
                                self.cfg.log("-forwards Distance "+str(dist)+" bearing "+str(bearing)+" direction "+str(minInterestingClusters[-1][0].getMotionDirection()[0])+" bearing dev "+str(bearingDev)+" DT "+str(cluster2.getDT()))
                                        
                            if currentScore > bestInterestScore and currentScore >= self.cfg.minShearScore and dist <= self.cfg.maxShearDist and (bearingDev <= self.cfg.maxBearingDev or dist <= (self.cfg.maxShearDist*self.cfg.shearVectorDistanceFactor)):
                                bestInterestScore = currentScore
                                bestISCluster = cluster2
                            
                    if bestISCluster:
                        self.cfg.log("Found 2 min2 !"+str(bestISCluster.getID()[0]))
                        minInterestingClusters[-1][0], minMotions = self.calculateShearMotionVector(minInterestingClusters[-1][0], bestISCluster, minMotions)
                                
                        bestISCluster.setVLat(minInterestingClusters[-1][0].getVLat()[0])
                        bestISCluster.setVLon(minInterestingClusters[-1][0].getVLon()[0])
                        bestISCluster.setMotionDirection(minInterestingClusters[-1][0].getMotionDirection()[0])
                        bestISCluster.setClusterU(minInterestingClusters[-1][0].getClusterU()[0])
                        bestISCluster.setClusterV(minInterestingClusters[-1][0].getClusterV()[0])
                        dt = abs((bestISCluster.getDT() - minInterestingClusters[-1][0].getDT()).total_seconds())
                        bestISCluster.projectCluster(dt)
                                
                        if self.cfg.projectReference:
                            clusterCount = self.getNearbyClusterCount(projLat, projLon, newClusters, self.cfg.maxShearDist)
                            bestISCluster.setPotentialClusterCount(clusterCount)
                        else:
                            clusterCount = self.getNearbyClusterCount(minInterestingClusters[-1][0].getLatitude()[0], minInterestingClusters[-1][0].getLongitude()[0], newClusters, self.cfg.maxShearDist)
                            bestISCluster.setPotentialClusterCount(clusterCount)
                        
                        try:
                            hasModel = self.checkForModel(bestISCluster)
                        except err.NoModelDataFound as excep:
                            raise
                            
                        minInterestingClusters.append([bestISCluster, self.times[timeIndex+1]])
                        
                        timeIndex += 1
                        foundName = True
                        currentName = bestISCluster.getID()[0]
                        break
                    else:
                        self.cfg.log("Didn't find another cluster. Stopping tracking. minForward 2")
                        
                        keepTracking = False
                        
                        with open(self.cfg.logName+'_events.csv', 'a') as fi:
                            fi.write(self.case.storm+','+self.case.ID+','+str(self.case.isTor)+',4,'+str(len(self.times) - int(timeIndex))+',Stopped tracking -forwards with '+str(self.times[timeIndex+1].getDT())+'\n')
                                    
                        break
            
            
            minOrderedInterestingClusters = [cluster[0] for cluster in self.reorderClusters(minInterestingClusters)]
            
            
            #Force a projection on the last cluster.
            time1 = self.times[len(self.times)-2]
            time2 = self.times[len(self.times)-1]
            
            finalElapsedTime = abs((datetime.strptime(time2.getDT(), '%Y%m%d-%H%M%S') - datetime.strptime(time1.getDT(), '%Y%m%d-%H%M%S')).total_seconds())
            
            minOrderedInterestingClusters[-1].projectCluster(finalElapsedTime)
            
            self.cfg.log("Finished with max motions "+str(maxMotions)+"\nmin motions "+str(minMotions))
            
        else:
            self.cfg.error("Warning! Min reference cluster not found for case "+str(self.case.storm)+"/"+str(self.case.ID)+"...Skipping Minimum Analysis!")
           
            
        #If we cannot find any reference clusters, then we can't do an anlysis, so let the main loop know and move on
        if not (maxOrderedInterestingClusters or minOrderedInterestingClusters):
            self.cfg.error("No reference clusters found for lowest level AzShear!")
            raise err.NoReferenceClusterFoundException("No Reference Clusters Found")
        
        return maxOrderedInterestingClusters, minOrderedInterestingClusters
    

    
    def reorderClusters(self, unorderedClusters):
    
        orderedClusters = []
        ordered = 0
        orderedIndicies = []

        # for nusClus,time in unorderedClusters:
            # self.cfg.error("Unordered cluster check "+str(nusClus.getDT()))
        while ordered < len(unorderedClusters):
            
            lowestDT = datetime(year=9999, month=1, day=1, hour=0, minute=0, second=0) #Pick a ridiculus time in the future
            lowestIndex = -1
            count = 0
            for currentCluster in unorderedClusters:
                string1 = currentCluster[0].getDT().strftime('%Y%m%d-%H%M%S')
                #self.cfg.error("Checking string "+str(string1))
                year = int(string1[0:4])
                month = int(string1[4:6])
                day = int(string1[6:8])
                hour = int(string1[9:11])
                minute = int(string1[11:13])
                second = int(string1[13:15])
                dt = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
            
                if (dt < lowestDT and (count not in orderedIndicies)):
                    # self.cfg.error("Found lowest DT "+str(currentCluster[0].getDT()))
                    lowestDT = dt
                    lowestIndex = count
                count = count + 1
            
            # self.cfg.error("Added cluster "+str(unorderedClusters[lowestIndex][0].getDT())+" at "+str(lowestIndex))
            orderedClusters.append(unorderedClusters[lowestIndex])
            orderedIndicies.append(lowestIndex)
            ordered += 1 
    
        
        return orderedClusters
        