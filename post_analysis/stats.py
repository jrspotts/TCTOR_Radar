#This class holds the function for calculating statistics and splitting data into different groups.

import math
import numpy as np
from scipy import stats as scistats

def getRMSE(values, predictions):

    return np.sqrt(np.mean((predictions-values)**2))
    
def getBinDiff(differenceObjects, tiltList, radii, tiltBin=None, rangeBin=None, TC=None, selectTilt=None, type='vrot'):

    """ 
        Returns all data objects for a given tilt bin, range bin, TC, or combination of the three.
        None, the default, returns all. Type is azshear or et. Default is azhear. 
        Tilt and range bins and selectTilt are only for azshear. Tilt indicates the which tilt to return.
    """
    
    vrotData = {'azsheardiffs':[], 'azshearpairs':[], 'sizepairs':[], 'potentialclusters':[], 'azsheartopdiffs':[],\
                'azshearbotdiffs':[], 'azsheartoppairs':[], 'azshearbotpairs':[], 'azsheartopsizepairs':[],\
                'azshearbotsizepairs':[], 'vrotrdiffs':{}, 'vrotrpairs':{}, 'bestradiusvrotpairs':[], 'bestradius':[],\
                'vrotdistpairs':{}, 'vrotdisterrorpairs':{}}
    vrotDataCopy = vrotData
    etData = {'etdiff':[], 'etpair':[], 'etpotentialclusters':[], 'et90diff':[], 'et90pair':[]}
    etDataCopy = etData

    
    for radius in radii:
        vrotData['vrotrdiffs'][radius] = []
        vrotData['vrotrpairs'][radius] = []
        vrotData['vrotdistpairs'][radius] = []
        vrotData['vrotdisterrorpairs'][radius] = []
        
    #Start with looping through the TCs
    for TC in list(differenceObjects.keys()):
        
        for case in list(differenceObjects[TC].keys()):
           
            for diff in differenceObjects[TC][case]:
                meetsTC = False
                
                #If criteria was given for a TC or bin, check to see if it's met. If the criterion was not given, then it's assumed to be met
                if TC:
                    
                    if diff.TC == TC:
                        meetsTC = True
                else:
                    meetsTC = True
                
                if type == 'vrot':
                    # repeated = False
                    for tilt in tiltList:
                        truthTilt = tilt 
                        meetsTiltBin = False
                        meetsRangeBin = False
                        meetsTilt = False
                        try:
                            if tilt == '1.3' or tilt == '1.45':
                                # if repeated:
                                    # print('Skipping for', tilt)
                                    # repeated = False
                                    # continue
                                    
                                truthTilt = '1.3/1.45'
                                # repeated = True
                                
                            if tiltBin is not None:
                            
                                if tiltBin == diff.tiltBins[tilt]:
                                    meetsTiltBin = True
                            else:
                                meetsTiltBin = True
                                
                            if rangeBin is not None:
                                
                                if rangeBin == diff.rangeBins[tilt]:
                                    meetsRangeBin = True
                            else:
                                meetsRangeBin = True

                            if selectTilt is not None:
                                if truthTilt == selectTilt:
                                    meetsTilt = True
                            else:
                                meetsTilt = True
                                
                            print('Sorting data by tilt bin=', tiltBin, 'range bin=', rangeBin, 'TC=', TC, 'case=', case, 'select tilt=', selectTilt, 'type=', type, '\n',\
                                  'tilt bin=', diff.tiltBins[tilt], 'range bin=', diff.rangeBins[tilt], 'tilt=', tilt, 'truth tilt=', truthTilt, '\n',\
                                  'meets TC=', meetsTC, 'meets tilt bin=', meetsTiltBin, 'meets range bin=', meetsRangeBin, 'meets tilt=', meetsTilt)
                                
                            if meetsTC and meetsTiltBin and meetsRangeBin and meetsTilt:
                                print('Approved!\n')
                                try:
                                    vrotData['azsheardiffs'].append(diff.azShearDiffs[tilt])
                                    vrotData['azshearpairs'].append(diff.azShearPairs[tilt])
                                    vrotData['sizepairs'].append(diff.sizePairs[tilt])
                                    vrotData['potentialclusters'].append(diff.azShearPotentialClusters[tilt])
                                    vrotData['azsheartopdiffs'].append(diff.azShearTopDiffs[tilt])
                                    vrotData['azshearbotdiffs'].append(diff.azShearBotDiffs[tilt])
                                    vrotData['azsheartoppairs'].append(diff.azShearTopPairs[tilt])
                                    vrotData['azshearbotpairs'].append(diff.azShearBotPairs[tilt])
                                    vrotData['azsheartopsizepairs'].append(diff.azShearTopSizePairs[tilt])
                                    vrotData['azshearbotsizepairs'].append(diff.azShearBotSizePairs[tilt])
                                    
                                
                                    for radius in list(diff.vrotRDiffs[tilt].keys()):
                                        vrotData['vrotrdiffs'][radius].append(diff.vrotRDiffs[tilt][radius])
                                        vrotData['vrotrpairs'][radius].append(diff.vrotRPairs[tilt][radius])
                                        vrotData['vrotdistpairs'][radius].append(diff.vrotRDistPairs[tilt][radius])
                                        vrotData['vrotdisterrorpairs'][radius].append(diff.vrotRDistErrorPairs[tilt][radius])
                                except Exception as err:
                                    print('An error happend in the vrot section of binning', str(err))
                                    continue
                                    
                                    
                                vrotData['bestradiusvrotpairs'].append(diff.bestRadiusVrotPair[tilt])
                                vrotData['bestradius'].append(diff.bestRadius[tilt])
                                continue
                                    
                        except KeyError as e:
                            #print('KeyError in binning', str(e))
                            continue
                            
                            
                 
                
                elif type == 'et' and meetsTC:
                    etData['etdiff'].append(diff.etDiff)
                    etData['etpair'].append(diff.etPair)
                    etData['etpotentialclusters'].append(diff.etPotentialClusters)
                    etData['et90diff'].append(diff.et90Diff)
                    etData['et90pair'].append(diff.et90Pair)
                    
    
   #Once all the data is put together, clean out all of the None instances if azshear

    if type == 'vrot':
        for variable in list(vrotData.keys()):
        
            
            
            if isinstance(vrotData[variable], dict):
                newList = {}
                
                for radius in list(vrotData[variable].keys()):
                    newList[radius] = []
                    
                    for a in range(len(vrotData[variable][radius])):
                        if vrotData[variable][radius][a] is not None:
                            newList[radius].append(vrotData[variable][radius][a])
                
            else:
                newList = []
                for dataPoint in vrotData[variable]:
                    if isinstance(dataPoint, tuple):
                        if None not in dataPoint:
                            newList.append(dataPoint)
                    else:
                        if dataPoint is not None:
                            newList.append(dataPoint)
                        
            #print('Created newlist for', variable, ':  ', newList)
            vrotDataCopy[variable] = newList    
            
        return vrotDataCopy

    elif type == 'et':
        
        for variable in list(etData.keys()):
        
            newList = []
            
            for dataPoint in etData[variable]:
                
                if isinstance(dataPoint, tuple):
                    if None not in dataPoint:
                        newList.append(dataPoint)
                else:
                    if dataPoint is not None:
                        newList.append(dataPoint)
                        
            etDataCopy[variable] = newList
            
        return etDataCopy
        
        
    return None
    
    
def writeStats(groups):

    """ Writes statistics for each group and subgroup. Note that the same stats are calculated for each, regardless of whether they make sense or not. """
    
    with open('stats.csv', 'w') as fi:
    
        fi.write('group,datatype,radius,count,min,25th%,median,mean,mode,75th%,max\n')
        
        for group in list(groups.keys()):
            
            for dataType in list(groups[group]):

                if isinstance(groups[group][dataType], dict):
                    #print(dataType, type(dataType), list(map(str, list(groups[group][dataType].keys()))))
                    #We're probably dealing with data sorted by radius
                    for radius in list(groups[group][dataType].keys()):
                    
                        data = groups[group][dataType][radius]
                        if data and not 'pairs' in str(dataType):
                            print('Writing stats for', group, dataType, radius, data)
                            count = str(len(data))
                            minimum = str(min(data))
                            firstPercentile = str(np.percentile(data, 25))
                            median = str(np.median(data))
                            mean = str(np.mean(data))
                            mode = str(scistats.mstats.mode(data).mode[:])
                            secondPercentile = str(np.percentile(data, 75))
                            maximum = str(max(data))
                            
                            fi.write(group+','+dataType+','+str(radius)+','+count+','+minimum+','+firstPercentile+','+median+','+mean+','+mode+','+secondPercentile+','+maximum+'\n')
                        else:
                            fi.write(group+','+dataType+','+str(radius)+',N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A\n')
                        
                        
                elif isinstance(groups[group][dataType], list) and not any(isinstance(dataPoint, tuple) for dataPoint in groups[group][dataType]):
                    data = groups[group][dataType]
                    if data and not 'pairs' in str(dataType):
                        print('Gettings stats for', group, dataType, data)
                        radius = 'N/A'
                        count = str(len(data))
                        minimum = str(min(data))
                        firstPercentile = str(np.percentile(data, 25))
                        median = str(np.median(data))
                        mean = str(np.mean(data))
                        mode = str(scistats.mstats.mode(data).mode[:])
                        secondPercentile = str(np.percentile(data, 75))
                        maximum = str(max(data))
                        
                        fi.write(group+','+dataType+','+radius+','+count+','+minimum+','+firstPercentile+','+median+','+mean+','+mode+','+secondPercentile+','+maximum+'\n')
                    else:
                        fi.write(group+','+dataType+',N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A\n')
                else:
                    print('Probably a tuple')
                
                
    print('Done writing stats')
    return
                
                
            
def writeDiffs(autoObjects, truthObjects, differenceObjects):

    """ 
        This functions simply writes some of the data to comparison.csv.
    """
    
    with open('data.txt', 'w') as fi:
        tiltTruthHeader = ''
        tiltAreaHeader = ''
        tiltList = ['0.5', '0.9', '1.3/1.45', '1.8', '2.4']
        
        for tilt in tiltList:
            tiltTruthHeader=str(tilt)+' vrot,'
            
        #Write the header
        fi.write('TC,case,'+tiltTruthHeader+'0.5,0.9,1.3,1.45,1.8,2.4,ET Truth, ET Estimated\n')
        
        #Find matching truth objects and write that data and the coresponding auto and differences
        
        for TC in list(truthObjects.keys()):
            for truth in list(truthObjects[TC].values()):
            
                for auto in list(autoObjects[TC].values()):
                    
                    if truth.case == auto.case and truth.TC == auto.TC:
                        
                        for diff in list(differenceObjects[TC].values()):
                            
                            if auto.TC == diff.TC and auto.case == diff.case:
                            
                                fi.write(','.join(map(str, [auto.TC, auto.case, truth.vrots['0.5'], truth.vrots['0.9'], truth.vrots['1.3/1.45'], truth.vrots['1.8'], truth.vrots['2.4'],\
                                                            auto.azShear['0.5'].areaVrot, auto.azShear['0.9'].areaVrot, auto.azShear['1.3/1.45'].areaVrot, auto.azShear['1.8'].areaVrot, auto.azShear['2.4'].areaVrot, truth.ET, auto.maxETft]))+'\n')
                                                            
                                break
                                
                        break
                    
                    
                    
    return
    
    

        
        
        