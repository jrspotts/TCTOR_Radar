 #This script is made as a replacement to makefig2.m. The goal is to visualize and create figures using python instead of matlab

from netCDF4 import Dataset
import sys
import numpy as np
import os
from datetime import datetime
from datetime import timedelta
from ttrappy import ttrappy as ttr
from ttrappy import colormaps as cm
import multiprocessing as mp
import tkinter as tk
import time
import multiprocessing
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
import cartopy.feature as cfeature
#from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import matplotlib.ticker as mticker
import math
from metpy.plots import USCOUNTIES
from decimal import Decimal

MATPLOTLIB = True
try:
	import matplotlib.pyplot as plt
	import matplotlib.axes as axs
	import matplotlib as mpl
except ImportError as importErr:
	print(importErr)
	print('Matplotlib failed to import. Turning off figure generating')
	MATPLOTLIB = False


def createAxisTicks(cfg, start, size, spacing):
	
    ticks = []
    for i in range(size):
        if (start > 0):
            ticks.append(start - (spacing*i))
        elif (start < 0):
            ticks.append(start + (spacing*i))
        else:
            cfg.error('WHERE ARE YOU DOING THIS AT?!!')
            exit(7)

    return ticks

		

def getStringDT(cfg, string1, string2):

    #Flag to determine if the time associated with string 2 is greater than or equal to string 1
    greater = False
    
    #Assuming the format YYYYMMDD-HHMMSS
    year1 = int(string1[0:4])
    month1 = int(string1[4:6])
    day1 = int(string1[6:8])
    hour1 = int(string1[9:11])
    minute1 = int(string1[11:13])
    second1 = int(string1[13:])

    year2 = int(string2[0:4])
    month2 = int(string2[4:6])
    day2 = int(string2[6:8])
    hour2 = int(string2[9:11])
    minute2 = int(string2[11:13])
    second2 = int(string2[13:])
        
    #cfg.log('getStringDT()')
    #cfg.log(str(string1)+' '+str(year1)+' '+str(month1)+' '+str(day1)+' '+str(hour1)+' '+str(minute1)+' '+str(second1))
    #cfg.log(str(string2)+' '+str(year2)+' '+str(month2)+' '+str(day2)+' '+str(hour2)+' '+str(minute2)+' '+str(second2))

    dt1 = datetime(year1, month1, day1, hour1, minute1, second1)
    dt2 = datetime(year2, month2, day2, hour2, minute2, second2)
    
    equal = False
    
    if dt2 > dt1:
        greater = True
    else:
        greater = False
        
    if dt2 == dt1:
        equal = True

    delta = dt2 - dt1
    #cfg.log('Resulting Delta = '+str(delta.seconds))
    delta2 = dt1 - dt2
    #cfg.log('Alternate Delta = '+str(delta2.seconds))

    if (delta.seconds < delta2.seconds):
        return delta.seconds, greater, equal
    else:
        return delta2.seconds, greater, equal


def getSpatialAttributes(cfg, nc_data):
	
    lat = nc_data.Latitude
    lon = nc_data.Longitude
    lat_spacing = nc_data.LatGridSpacing
    lon_spacing = nc_data.LonGridSpacing
    lat_size = nc_data.dimensions['Lat'].size
    lon_size = nc_data.dimensions['Lon'].size

    #cfg.log('Retrieved '+str(lat_size)+' '+str(lon_size)+' '+str(lat_spacing)+' '+str(lon_spacing))

    return lat, lon, lat_spacing, lon_spacing, lat_size, lon_size
    
#Index is the index of the statistic of the shed. Deprecated in favor of shear/storm objects 
def retrieveTableInfo(cfg, fi, index, avgLon):

    first = True
    lats = []
    lons = []
    stats = []
    IDs = []

    #cfg.log('(Retrieve Table) '+fi.name)
    for line in fi:
        
        if (not first):
            #cfg.log('(Table) Reading data '+line)
            data = line.rstrip('\n').split(',')
            lats.append(float(data[0]))
            lons.append(float(data[1]))
            stats.append(float(data[index]))
            if ('.' in data[14]):
                if('.' not in data[7]):
                    IDs.append(int(data[7]))
                else:
                    IDs.append(1)
            else:
                IDs.append(int(data[14]))
        else:
            first = False

    return lats, lons, stats, IDs

def plotCities(ax, xticks, yticks, proj):

    minLon = min(xticks)
    maxLon = max(xticks)
    minLat = min(yticks)
    maxLat = max(yticks)
    
    states = {'Alabama':'AL',
              'Alaska':'AK',
              'Arizona':'AZ',
              'Arkansas':'AR',
              'American Samoa':'AS',
              'California':'CA',
              'Colorado':'CO',
              'Connecticut':'CT',
              'Deleware':'DE',
              'District of Columbia':'DC',
              'Florida':'FL',
              'Georgia':'GA',
              'Guam':'GU',
              'Hawaii':'HI',
              'Idaho':'ID',
              'Illinois':'IL',
              'Indiana':'IN',
              'Iowa':'IA',
              'Kansas':'KS',
              'Kentucky':'KY',
              'Louisiana':'LA',
              'Maine':'ME',
              'Maryland':'MD',
              'Massachusetts':'MA',
              'Michigan':'MI',
              'Minnesota':'MN',
              'Mississippi':'MS',
              'Missouri':'MO',
              'Montana':'MT',
              'Nebraska':'NE',
              'Nevada':'NV',
              'New Hampshire':'NH',
              'New Jersey':'NJ',
              'New Mexico':'NM',
              'New York':'NY',
              'North Carolina':'NC',
              'North Dakota':'ND',
              'Northern Mariana Islands':'CM',
              'Ohio':'OH',
              'Oklahoma':'OK',
              'Oregon':'OR',
              'Pennsylvania':'PA',
              'Puerto Rico':'PR',
              'Rhode Island':'RI',
              'South Carolina':'SC',
              'South Dakota':'SD',
              'Tennessee':'TN',
              'Texas':'TX',
              'Trust Territories':'TT',
              'Utah':'UT',
              'Vermont':'VT',
              'Virginia':'VA',
              'Virgin Islands':'VI',
              'Washington':'WA',
              'West Virginia':'WV',
              'Wisconsin':'WI',
              'Wyoming':'WY'}
              
    #Define a dictionary of states and their appreviations for use in the city names
    fname = shpreader.natural_earth(resolution='10m', category='cultural', name='populated_places')
    reader = shpreader.Reader(fname)
    
    cities = []
    xlist = []
    ylist = []
    nameList = []
    
    records = list(reader.records())
    
    for city in records:
        x = city.geometry.x
        y = city.geometry.y
        #print(x, y,  minLon <= x <= maxLon, minLat <= y <= maxLat, city.attributes['POP_MAX'], city.attributes['NAME_EN'])
        if minLon <= x <= maxLon and minLat <= y <= maxLat:
            xlist.append(x)
            ylist.append(y)
            nameList.append(city.attributes['NAME_EN']+','+str(states[city.attributes['ADM1NAME']]))
            
    if len(xlist) > 0 and len(ylist) > 0 and len(nameList) > 0:
        ax.scatter(xlist, ylist, s=40, c='k', edgecolor='white')
        for x, y, name in zip(xlist, ylist, nameList):
            ax.text(x+0.015, y+0.015, name, backgroundcolor=[1,1,1], color=[0,0,0], size='medium')
    
    print('Theoretically plotted cities', nameList)
    return
    
def plotShearCentroid(cfg, case, plt, ax, tString, tilt, closestString, ax2=None):

    try:
    
        #Now we're going to read through the preliminary analysis and get centroid lat/lons
        fileName = str(case.ID)+'_prelim.csv'
        fullPath = os.path.join(case.saveDir, fileName)
        
        with open(fullPath, 'r') as analysisFi:
            first = True
            DTIndex = None
            latIndex = None
            lonIndex = None
            closestLocIndex = []
            closestLocTDSeconds = 99999999
            closestLat = None
            closestLon = None
            closestU = None
            closestV = None
            uIndex = None
            vIndex = None
            closestUShear = None
            closestVShear = None
            uShearIndex = None
            vShearIndex = None
            beamHeight = None
            range = None
            
            
            

            if float(tilt) < 1:
                modTilt = tilt.rstrip('0')
            else:
                modTilt = tilt.strip('0')
                
            paraModTilt = '('+modTilt+'deg)'
        
            for line in analysisFi:
                lineList = line.rstrip('\n').split(',')
                if first:
                    DTIndex = lineList.index('DateTime'+paraModTilt)
                    latIndex = lineList.index('Latitude(Degrees)'+paraModTilt)
                    lonIndex = lineList.index('Longitude(Degrees)'+paraModTilt)
                    uIndex = lineList.index('clusterU(m/s)'+paraModTilt)
                    vIndex = lineList.index('clusterV(m/s)'+paraModTilt)
                    uShearIndex = lineList.index('uShear(m/s)'+paraModTilt)
                    vShearIndex = lineList.index('vShear(m/s)'+paraModTilt)
                    forwardLatIndex = lineList.index('forwardLat(deg)'+paraModTilt)
                    forwardLonIndex = lineList.index('forwardLon(deg)'+paraModTilt)
                    backwardLatIndex = lineList.index('backLat(deg)'+paraModTilt)
                    backwardLonIndex = lineList.index('backLon(deg)'+paraModTilt)
                    beamHeightIndex = lineList.index('BeamHeight 0 '+paraModTilt+'(feet)')
                    rangeIndex = lineList.index('GroundRange 0 (n mi)'+paraModTilt)
                    first = False
                
                else:
                    if lineList[DTIndex] != '-99900' and lineList[DTIndex] != '-99904':
                        #cfg.error("Plt shear centroid times "+str(tString)+" "+str( lineList[DTIndex]))
                        currentTDSeconds = getStringDT(cfg, tString, lineList[DTIndex])[0]
                        if currentTDSeconds < closestLocTDSeconds:
                            try:
                                closestLat = float(lineList[latIndex])
                                closestLon = float(lineList[lonIndex])
                                closestLocTDSeconds = currentTDSeconds
                                closestU = float(lineList[uIndex])
                                closestV = float(lineList[vIndex])
                                closestUShear = float(lineList[uShearIndex])
                                closestVShear = float(lineList[vShearIndex])
                                forwardLat = float(lineList[forwardLatIndex])
                                forwardLon = float(lineList[forwardLonIndex])
                                backwardLat = float(lineList[backwardLatIndex])
                                backwardLon = float(lineList[backwardLonIndex])
                                beamHeight = float(lineList[beamHeightIndex])
                                range = float(lineList[rangeIndex])
                                
                            except ValueError as VE:
                                cfg.error("Skipping None in shear centroid\n"+str(VE)+" DT "+str(lineList[DTIndex])+" tilt "+str(tilt))
                                continue
                    else:
                        continue
                        
        if closestLocTDSeconds <= (60*cfg.maxAppendTimeV):
            ax.scatter(closestLon, closestLat, s=40, c=cfg.activeColor, edgecolor=[1, 1, 1])
            
            #Plot motion vector
            if (closestU != -99900) and (closestV != -99900) and (closestU or closestUShear == 0) and (closestV or closestV == 0) and (closestU != -99904) and (closestV != -99904) and (closestU != -99903) and (closestV != -99903):
            
                
                scale = 25*float(cfg.hvSpacing) #Scale by which to scale vector lengths
                
                #Create a unit vector for plotting the arrow
                mag = math.sqrt(closestU**2 + closestV**2)
                
                u = (closestU/mag)*scale
                v = (closestV/mag)*scale

                #Plot the motion arrow
                #ax.arrow(x=closestLon,  y=closestLat, dx=u, dy=v, width=0.005, head_width=0.005, head_length=0.005, length_includes_head=True)
                ax.annotate("", xy=(closestLon+u, closestLat+v), xycoords='data', xytext=(closestLon, closestLat), textcoords='data', arrowprops=dict(arrowstyle="simple, head_width=1", color="b"))
                
                
                
            #Plot the shear vector if applicable
            if (closestUShear != -99900) and (closestVShear != -99900) and (closestUShear or closestUShear == 0) and (closestVShear or closestVShear == 0) and (closestU != -99904) and (closestV != -99904) and (closestU != -99903) and (closestV != -99903):
            
                scale = 25*float(cfg.hvSpacing)
                
                #Create a unit vector for plotting the arrow
                mag = math.sqrt(closestUShear**2 + closestVShear**2)
                
                u = (closestUShear/mag)*scale
                v = (closestVShear/mag)*scale
                
                #Plot the shear arrow
                ax.annotate("", xy=(closestLon+u, closestLat+v), xycoords='data', xytext=(closestLon, closestLat), textcoords='data', arrowprops=dict(arrowstyle="simple, head_width=1", color="m"))
                
            #Plot the forward projection if available    
            if forwardLat != -99900 and forwardLon != -99900:
                
                ax.scatter(forwardLon, forwardLat, s=80, c=[0, 0, 0], edgecolor=[1, 1, 1])
                
            #Plot the backward projection if available
            if backwardLat != -99900 and backwardLon != -99900:
                
                ax.scatter(backwardLon, backwardLat, s=85, c=[0, 0, 0], marker='X', edgecolor=[1, 1, 1], linewidth=2)
             
            #Plot beam height and range of centroid in lower right of plot
            
            print('Checking', beamHeight, range, ax2)
            if range != -99900 and range != -99904 and beamHeight != -99900 and beamHeight != -99904 and ax2:
                plt.gcf().text(0.8, 0.04, 'Beam Height: '+str(round(beamHeight))+' ft\nRange '+str(round(range ,1))+' n mi.\nfrom '+str(case.sites[0].name), fontsize=12)
                
             #If the tilt being plotted is not the bottom tilt, plot the centroid for the cluster of interest
            
            if tilt != cfg.tiltList[0]:
            
                #cfg.error("Trying to plot 0.5 deg tilt for tilt "+str(tilt))
                first = True
                
                if float(cfg.tiltList[0]) < 1:
                    modTilt2 = cfg.tiltList[0].rstrip('0')
                else:
                    modTilt2 = cfg.tiltList[0].strip('0')
                    
                paraModTilt2 = '('+modTilt2+'deg)'
                
                closestLat2 = None
                closestLon2 = None
                closestU2 = None
                closestV2 = None
                closestUShear2 = None
                closestVShear2 = None
                currentTDSeconds2 = None
                closestLocTDSeconds2 = 9999999999
                    
                with open(fullPath, 'r') as analysisFi2:

                
                    for line2 in analysisFi2:
                        lineList2 = line2.rstrip('\n').split(',')
                        if first:
                            DTIndex2 = lineList2.index('DateTime'+paraModTilt2)
                            latIndex2 = lineList2.index('Latitude(Degrees)'+paraModTilt2)
                            lonIndex2 = lineList2.index('Longitude(Degrees)'+paraModTilt2)
                            uIndex2 = lineList2.index('clusterU(m/s)'+paraModTilt2)
                            vIndex2 = lineList2.index('clusterV(m/s)'+paraModTilt2)
                            uShearIndex2 = lineList2.index('uShear(m/s)'+paraModTilt2)
                            vShearIndex2 = lineList2.index('vShear(m/s)'+paraModTilt2)
                            first = False
                        
                        else:
                            if lineList[DTIndex] != '-99900' and lineList[DTIndex] != '-99904':
                                currentTDSeconds2, greater, equal = getStringDT(cfg, tString, lineList2[DTIndex2])
                                #cfg.error("Trying with "+str(currentTDSeconds2)+" greater? "+str(greater)+" latIndex2 "+str(latIndex2)+" "+str(paraModTilt2))
                                #Make sure we are getting the closest 0.5 degree sweep BEFORE the current sweep
                                if currentTDSeconds2 < closestLocTDSeconds2 and not greater:
                                    try:
                                        closestLat2 = float(lineList2[latIndex2])
                                        closestLon2 = float(lineList2[lonIndex2])
                                        closestLocTDSeconds2 = currentTDSeconds2
                                        closestU2 = float(lineList2[uIndex2])
                                        closestV2 = float(lineList2[vIndex2])
                                        closestUShear2 = float(lineList2[uShearIndex2])
                                        closestVShear2 = float(lineList2[vShearIndex2])
                                    except ValueError as VE:
                                        cfg.error("Skipping None in shear centroid for lowest tilt addon\n"+str(VE)+" DT "+str(lineList2[DTIndex])+" tilt "+str(modTilt2))
                                        continue
                            else:
                                continue
                             
                #cfg.error("Plotting "+str(closestLon2)+" "+str(closestLat2))         
                ax.scatter(closestLon2, closestLat2, s=75, c=cfg.activeColor, marker="d", edgecolor=[1,1,1])
                    
        else:
            cfg.error("Closest shear centroid time isn't good enough")
            return
            
           
                
            
    except FileNotFoundError:
        cfg.error(fullPath+' not found for shear for tilt '+str(tilt))
                    
    return
    
def plotVILCentroid(cfg, case, plt, ax, tString, closestString):

    try:
    
        #Now we're going to read through the preliminary analysis and get centroid lat/lons
        fileName = str(case.ID)+'_prelim.csv'
        fullPath = os.path.join(case.saveDir, fileName)
        
        with open(fullPath, 'r') as analysisFi:
            first = True
            DTIndex = None
            latIndex = None
            lonIndex = None
            closestLocIndex = []
            closestLocTDSeconds = 99999999
            closestLat = None
            closestLon = None
            closestU = None
            closestV = None
            uIndex = None
            vIndex = None

            for line in analysisFi:
                lineList = line.rstrip('\n').split(',')
                if first:
                    DTIndex = lineList.index('DateTime(Track)')
                    latIndex = lineList.index('Latitude(Degrees)(Track)')
                    lonIndex = lineList.index('Longitude(Degrees)(Track)')
                    uIndex = lineList.index('uShear(m/s)')
                    vIndex = lineList.index('vShear(m/s)')
                    
                    first = False
                
                else:
                    if lineList[DTIndex] != '-99900' and lineList[DTIndex] != '-99904':
                        currentTDSeconds = getStringDT(cfg, tString, lineList[DTIndex])[0]
                        if currentTDSeconds < closestLocTDSeconds:
                            try:
                                closestLat = float(lineList[latIndex])
                                closestLon = float(lineList[lonIndex])
                                closestLocTDSeconds = currentTDSeconds
                                closestU = float(lineList[uIndex])
                                closestV = float(lineList[vIndex])
                            except ValueError as VE:
                                cfg.error("Skipping None in VIL centroid\n"+str(VE)+" DT "+str(lineList[DTIndex])+" tilt "+str(tilt))
                                continue
                    else:
                        continue
                        
                        
            

        if closestLocTDSeconds <= (cfg.maxAppendTimeR*60):
            
            #Plot motion vector
            if (closestU != -99900) and (closestV != -99900) and (closestU != -99904) and (closestV != -99904) and (closestU != -99903) and (closestV != -99903):
            
                scale = 30*float(cfg.hvSpacing) #Scale by which to scale vector lengths
                
                #Create a unit vector for plotting the arrow
                mag = math.sqrt(closestU**2 + closestV**2)
                
                u = (closestU/mag)*scale
                v = (closestV/mag)*scale
                
                #Plot the motion arrow
                ax.annotate("", xy=(closestLon+u, closestLat+v), xycoords='data', xytext=(closestLon, closestLat), textcoords='data', arrowprops=dict(arrowstyle="simple, head_width=1", color="g"))
                
            ax.scatter(closestLon, closestLat, s=60, c=['#B846B9'], edgecolor=[1, 1, 1])
        else:
            cfg.error("Closest VIL cluster time isn't good enough")
            
    except FileNotFoundError:
        cfg.error(fullPath+' not found for VIL')
                    
    return
    
def plotETCentroid(cfg, case, plt, ax, tString, closestString):

    try:
    
        #Now we're going to read through the preliminary analysis and get centroid lat/lons
        fileName = str(case.ID)+'_prelim.csv'
        fullPath = os.path.join(case.saveDir, fileName)
        
        with open(fullPath, 'r') as analysisFi:
            first = True
            DTIndex = None
            latIndex = None
            lonIndex = None
            closestLocIndex = []
            closestLocTDSeconds = 99999999
            closestLat = None
            closestLon = None
            
           
            for line in analysisFi:
                lineList = line.rstrip('\n').split(',')
                if first:
                    DTIndex = lineList.index('DateTime(ET)')
                    latIndex = lineList.index('Latitude(Degrees)(ET)')
                    lonIndex = lineList.index('Longitude(Degrees)(ET)')
                    first = False
                
                else:
                    if lineList[DTIndex] != '-99900' and lineList[DTIndex] != '-99904':
                        currentTDSeconds = getStringDT(cfg, tString, lineList[DTIndex])[0]
                        if currentTDSeconds < closestLocTDSeconds:
                            try:
                                closestLat = float(lineList[latIndex])
                                closestLon = float(lineList[lonIndex])
                                closestLocTDSeconds = currentTDSeconds
                            except ValueError:
                                cfg.error("Skipping None in ET centroid\n"+str(VE)+" DT "+str(lineList[DTIndex])+" tilt "+str(tilt))
                                continue
                    else:
                        continue

        if closestLocTDSeconds <= (60*cfg.maxAppendTimeR):
            ax.scatter(closestLon, closestLat, s=80, c=['#FF1C51'], marker='X', edgecolor=[1, 1, 1], linewidth=1)
        else:
            cfg.error("Closest ET cluster time isn't good enough")
            
    except FileNotFoundError:
        cfg.error(fullPath+' not found for ET')
                    
    return
    
def plotCluster(cfg, case, plt, ax, tString):
    
    if (case.hasDir['cluster']):
 
        clu_shed_files = os.listdir(case.productDirs['cluster']+'/'+case.productVars['cluster']+'/scale_0/')

        nearestTime = 9999999999
        closestIndex = 9999999999
        counter = 0
        closestString = ''

        for fi3 in  clu_shed_files:
            cluShedDString = fi3[0:15]
            currentDT, greater, equal = getStringDT(cfg, tString, cluShedDString)
            if (currentDT < nearestTime):
                nearestTime = currentDT
                closestIndex = counter
                closestString = cluShedDString
            counter = counter + 1
        
        if (nearestTime <= 60):
            clu_shed_nc_data = Dataset(case.productDirs['cluster']+'/'+case.productVars['cluster']+'/scale_0/'+clu_shed_files[closestIndex])
            clu_shed = clu_shed_nc_data.variables[case.productVars['cluster']]
            [vlats, vlons, vlat_spacing, vlon_spacing, vlat_size, vlon_size] = getSpatialAttributes(cfg, clu_shed_nc_data)
            xvticks = createAxisTicks(cfg, vlons, vlon_size, vlon_spacing)
            yvticks = createAxisTicks(cfg, vlats, vlat_size, vlat_spacing)
            XV, YV = np.meshgrid(xvticks, yvticks)
            plt.contour(XV, YV, clu_shed[:], 0, colors=['#B846B9'], linewidths=3) #Purple
            clu_shed_nc_data.close()
            
            plotVILCentroid(cfg, case, plt, ax, tString, closestString)

            #plt.text(0.02, 0.9, 'CLUSTER SHED Time \n'+closestString, color='grey', transform=ax.transAxes)
                
                
    return

def plotETCluster(cfg, case, plt, ax, tString):

    #Plot the echo top clusters if available
    if (case.hasDir['ETCluster']):
        clu_shed_files = os.listdir(case.productDirs['ETCluster']+'/'+case.productVars['ETCluster']+'/scale_0/')

        cfg.log('ET '+str(clu_shed_files))
         
        nearestTime = 9999999999
        closestIndex = 9999999999
        counter = 0
        closestString = ''

        isEqual = False
        isGreater = False
        
        for fi3 in  clu_shed_files:
            cluShedDString = fi3[0:15]
            currentDT, greater, equal = getStringDT(cfg, tString, cluShedDString)
            if (currentDT < nearestTime):
                nearestTime = currentDT
                closestIndex = counter
                closestString = cluShedDString
                isEqual = equal
                isGreater = greater
            counter = counter + 1
            
        cfg.log('ET '+str(closestIndex))
         
        if nearestTime <= (60*cfg.maxAppendTimeR):
            clu_shed_nc_data = Dataset(case.productDirs['ETCluster']+'/'+case.productVars['ETCluster']+'/scale_0/'+clu_shed_files[closestIndex])
            clu_shed = clu_shed_nc_data.variables[case.productVars['ETCluster']]
            [vlats, vlons, vlat_spacing, vlon_spacing, vlat_size, vlon_size] = getSpatialAttributes(cfg, clu_shed_nc_data)
            xvticks = createAxisTicks(cfg, vlons, vlon_size, vlon_spacing)
            yvticks = createAxisTicks(cfg, vlats, vlat_size, vlat_spacing)
            XV, YV = np.meshgrid(xvticks, yvticks)
            plt.contour(XV, YV, clu_shed[:], 0, colors=['#FF1C51'], linewidths=3) #Red/Pink
            clu_shed_nc_data.close()
            
            plotETCentroid(cfg, case, plt, ax, tString, closestString)
        
    return

def plotShearClusters(cfg, case, plt, ax, tString, tilt, ax2=None):
    
    closestString = ''
     
    if (case.hasDir['maxShearCluster']):
        clu_shed_files = os.listdir(case.productDirs['maxShearCluster']+'/'+tilt+'/'+case.productVars['maxShearCluster']+'/scale_0/')

        
        nearestTime = 9999999999
        closestIndex = 9999999999
        counter = 0
       

        for fi3 in  clu_shed_files:
            cluShedDString = fi3[0:15]
            currentDT, greater, equal = getStringDT(cfg, tString, cluShedDString)
            if (currentDT < nearestTime):
                nearestTime = currentDT
                closestIndex = counter
                closestString = cluShedDString
            counter = counter + 1
        
        cfg.log(case.productDirs['maxShearCluster']+'/'+tilt+'/'+case.productVars['maxShearCluster']+'/scale_0/'+clu_shed_files[closestIndex])
        
        if nearestTime <= (60*cfg.maxAppendTimeV):
            clu_shed_nc_data = Dataset(case.productDirs['maxShearCluster']+'/'+tilt+'/'+case.productVars['maxShearCluster']+'/scale_0/'+clu_shed_files[closestIndex])
            clu_shed = clu_shed_nc_data.variables[case.productVars['maxShearCluster']]
            [vlats, vlons, vlat_spacing, vlon_spacing, vlat_size, vlon_size] = getSpatialAttributes(cfg, clu_shed_nc_data)
            xvticks = createAxisTicks(cfg, vlons, vlon_size, vlon_spacing)
            yvticks = createAxisTicks(cfg, vlats, vlat_size, vlat_spacing)
            XV, YV = np.meshgrid(xvticks, yvticks)
            plt.contour(XV, YV, clu_shed[:], 0, colors=['#98CFCD'], linewidths=3) #Bluish
            clu_shed_nc_data.close()
                
    if (case.hasDir['minShearCluster']):            
        clu_shed_files = os.listdir(case.productDirs['minShearCluster']+'/'+tilt+'/'+case.productVars['minShearCluster']+'/scale_0/')

        nearestTime = 9999999999
        closestIndex = 9999999999
        counter = 0

        for fi3 in  clu_shed_files:
            cluShedDString = fi3[0:15]
            currentDT, greater, equal = getStringDT(cfg, tString, cluShedDString)
            if (currentDT < nearestTime):
                nearestTime = currentDT
                closestIndex = counter
                closestString = cluShedDString
            counter = counter + 1
            
        if nearestTime <= (60*cfg.maxAppendTimeV):
            clu_shed_nc_data = Dataset(case.productDirs['minShearCluster']+'/'+tilt+'/'+case.productVars['minShearCluster']+'/scale_0/'+clu_shed_files[closestIndex])
            clu_shed = clu_shed_nc_data.variables[case.productVars['minShearCluster']]
            [vlats, vlons, vlat_spacing, vlon_spacing, vlat_size, vlon_size] = getSpatialAttributes(cfg, clu_shed_nc_data)
            xvticks = createAxisTicks(cfg, vlons, vlon_size, vlon_spacing)
            yvticks = createAxisTicks(cfg, vlats, vlat_size, vlat_spacing)
            XV, YV = np.meshgrid(xvticks, yvticks)
            plt.contour(XV, YV, clu_shed[:], 0, colors=['#B5C570'], linewidths=3) #Yellow Green
            clu_shed_nc_data.close()    
        
    if closestString:    
        plotShearCentroid(cfg, case, plt, ax, tString, tilt, closestString, ax2=ax2)
        
    return
    
def checkBounds(radar, xticks, yticks):
    
    lat = float(radar.lat)
    lon = float(radar.lon)
    
    if lat >=  min(yticks) and lat <= max(yticks) and lon >= min(xticks) and lon <= max(xticks):
        return True
        
    return False
    
    
    
def plotRadars(cfg, case, xticks, yticks, ax):

    """ If a radar is within the bounds of the figure, plot the radar and location """
    
    for radar in case.sites:
        
        if checkBounds(radar, xticks, yticks):
            
            #plt.scatter(float(radar.lon), float(radar.lat), s=5)
            ax.text(float(radar.lon)-0.015, float(radar.lat), radar.name,  backgroundcolor=[1,1,1], color=[0, 0, 0], size='medium')
            
    return
    
def drawScaleBar(cfg, case):

    return

def axisFormat(x, y):
        
    return '{:.2f}'.format(x)
    
def drawFeaturesWithAxis(cfg, case, plt, ax, ax2, xticks, yticks, xticks2, yticks2, proj):
     
    #ax.coastlines()
    
    ax.add_feature(cfeature.RIVERS, edgecolor='blue')
    
    ax.set_xticks(xticks2, proj)
    ax.set_yticks(yticks2, proj)
    
    # ax2.text(0.1, 0.5, r"Latitude ($^\circ$)", rotation='vertical', va='bottom', ha='center', rotation_mode='anchor', fontsize='x-large')
    # ax2.text(0.5, 0.1, r"Longitude ($^\circ$)", rotation='horizontal', va='bottom', ha='center', rotation_mode='anchor', fontsize='x-large')
    ax.tick_params(axis='x', labelsize='xx-large')
    ax.tick_params(axis='y', labelsize='xx-large')
    ax2.tick_params(axis='both', labelsize='xx-large')
    
        
    # plt.xlabel(r"Longitude ($^\circ$)", fontsize='x-large')
    # plt.ylabel(r"Latitude ($^\circ$)", fontsize='x-large')
    # plt.xticks(fontsize='medium')
    # plt.yticks(fontsize='medium')
        
    plotCities(ax, xticks, yticks, proj)
    
    plotRadars(cfg, case, xticks, yticks, ax)
    
    ax.scatter([case.startLon, case.stopLon], [case.startLat, case.stopLat], s=100, c=[[1, 1, 1], [1, 1, 1]], marker='*', edgecolor=[0,0,0])
    
    plt.xlabel(r"Longitude ($^\circ$)", fontsize=20)
    plt.ylabel(r"Latitude ($^\circ$)", fontsize=20)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
            
    return
    
def setExtent(ax, dataWestLon, dataEastLon, dataSouthLat, dataNorthLat, proj):

    x0, y0 = proj.transform_point(np.array(dataWestLon, dtype='float64'), np.array(dataSouthLat, dtype='float64'), ccrs.Geodetic())
    x1, y1 = proj.transform_point(np.array(dataEastLon, dtype='float64'), np.array(dataNorthLat, dtype='float64'), ccrs.Geodetic())
    
    print('Setting extent to', [x0, x1, y0, y1])
    ax.set_extent([x0, x1, y0, y1], crs=proj)
    
    return
    
    
def createClusterShedPlot(cfg, case):

    try:
    
        altString = ''
        #modBottom = str(float(cfg.bottom)+(round(float(case.sites[0].hgt)/1000,2)))
        modBottom = cfg.bottom
        if len(modBottom) <= 3:
            altString = '0'+modBottom+'0'
        else:
            altString = '0'+modBottom
            
        files = os.listdir(case.productDirs['cluster']+'/'+case.productVars['cluster']+'/scale_0')
        files.sort()
        if '.working' in files:
            files.remove('.working')
            
        for fi in files:
            currentFile = case.productDirs['cluster']+'/'+case.productVars['cluster']+'/scale_0/'+fi
            tString = fi[0:15]
            cfg.log('Creating Cluster Shed Plot for '+currentFile)
            nc_data = Dataset(currentFile, 'r')
            cluster_shed = nc_data.variables[case.productVars['cluster']]
            lat, lon, lat_spacing, lon_spacing, lat_size, lon_size = getSpatialAttributes(cfg, nc_data)
            fig, ax = plt.subplots(1, 1)
            fig.subplots_adjust(right=0.8)
            xticks = createAxisTicks(cfg, lon, lon_size, lon_spacing)
            yticks = createAxisTicks(cfg, lat, lat_size, lat_spacing)
            pcm = ax.pcolormesh(xticks, yticks, cluster_shed, cmap='jet', vmin=0, vmax=np.amax(cluster_shed))

           
            ax.scatter([case.startLon, case.stopLon], [case.startLat, case.stopLat], s=40, c=[[1, 1, 1], [1, 1, 1]], marker='*', edgecolor=[0,0,0])
            plt.title(cfg.storm+' '+case.ID+' '+tString+' cluster_shed', loc='center', fontsize=20)
          

            plt.xlabel(r"Longitude ($^\circ$)", fontsize='x-large')
            plt.ylabel(r"Latitude ($^\circ$)", fontsize='x-large')
            plt.xticks(fontsize='medium')
            plt.yticks(fontsize='medium')
            
            cbar_ax = fig.add_axes([0.82, 0.15, 0.04, 0.7])
            cbar = fig.colorbar(pcm, cax=cbar_ax)
            nc_data.close()
            
            savePath = case.saveDir+'/figs/'+cfg.figurePrefix+str(tString)+'_'+altString+'_cluster_shed.png'
            cfg.log("Saving "+savePath)
            plt.savefig(savePath, format='png')
            
            plt.close()
        
      
        return

    except Exception as E:
        cfg.error("Exception in clusterShedPlot\n"+str(E))
        raise
        


        
def createMotionPlot(cfg, case):

    try:
    
        altString = ''
        #modBottom = str(float(cfg.bottom)+(round(float(case.sites[0].hgt)/1000,2)))
        modBottom = cfg.bottom
        if len(modBottom) <= 3:
            altString = '0'+modBottom+'0'
        else:
            altString = '0'+modBottom
            
        ttrappy = ttr.Processor(cfg, case)
        southDir = os.path.join(case.dataDir, case.productVars['motions'], 'scale_0')
        eastDir = os.path.join(case.dataDir, case.productVars['motione'],'scale_0')

        files = os.listdir(southDir)
        files.sort()
        
        if '.working' in files:
            files.remove('.working')
            
        for fi in files:
            currentSFile = os.path.join(southDir, fi)
            currentEFile = os.path.join(eastDir, fi)
            tString = fi[0:15]
            cfg.log('Creating Motion Plots From '+str(southDir)+' '+str(eastDir))
            s_nc_data = Dataset(currentSFile, 'r')
            e_nc_data = Dataset(currentEFile, 'r')
            southMotion = s_nc_data.variables[case.productVars['motions']]
            eastMotion = e_nc_data.variables[case.productVars['motione']]

            #Flip vectors around
            northMotion = [a*-1 for a in southMotion[:]]
            westMotion = eastMotion[:] #[a*-1 for a in eastMotion[:]]

            #Using south as the standard
            lat, lon, lat_spacing, lon_spacing, lat_size, lon_size = getSpatialAttributes(cfg, s_nc_data)
            fig, ax = plt.subplots(1, 1)
            fig.subplots_adjust(right=0.8)
            xticks = createAxisTicks(cfg, lon, lon_size, lon_spacing)
            yticks = createAxisTicks(cfg, lat, lat_size, lat_spacing)
            XV, YV = np.meshgrid(xticks, yticks)
            pcm = ax.quiver(XV, YV, northMotion[:], westMotion[:], [0, 0, 0])

        
            ax.scatter([case.startLon, case.stopLon], [case.startLat, case.stopLat], s=40, c=[[1, 1, 1], [1, 1, 1]], marker='*', edgecolor=[0,0,0])
            plt.title(cfg.storm+' '+case.ID+' '+tString+' Motion', loc='center', fontsize=20)
      
            plt.xlabel(r"Longitude ($^\circ$)", fontsize='x-large')
            plt.ylabel(r"Latitude ($^\circ$)", fontsize='x-large')
            plt.xticks(fontsize='medium')
            plt.yticks(fontsize='medium')
            
            cbar_ax = fig.add_axes([0.82, 0.15, 0.04, 0.7])
            cbar = fig.colorbar(pcm, cax=cbar_ax)
            s_nc_data.close()
            e_nc_data.close()
            
            savePath = case.saveDir+'/figs/'+cfg.figurePrefix+str(tString)+'_'+altString+'_motion.png'
            cfg.log("Saving "+savePath)
            plt.savefig(savePath, format='png')

            plt.close()
        

        return 
        
    except Exception as E:
        cfg.error("Exception in motionPlot\n"+str(E))
        raise

def createETPlot(cfg, case):

    try:
        ttrap = ttr.Processor(cfg, case)
        altString = ''
        #modBottom = str(float(cfg.bottom)+(round(float(case.sites[0].hgt)/1000,2)))
        modBottom = cfg.bottom
        if len(modBottom) <= 3:
            altString = '0'+modBottom+'0'
        else:
            altString = '0'+modBottom
            
        ETDIR = os.path.join(case.dataDir, case.productVars['et'], altString)
        files = os.listdir(ETDIR)
        files.sort()
        if '.working' in files:
            files.remove('.working')
            
        proj = ccrs.PlateCarree()

        for fi in files:
            currentFile = os.path.join(ETDIR, fi)
            tString = fi[0:15]
            cfg.log('Creating ET Plot for '+currentFile)
            nc_data = Dataset(currentFile, 'r')
            ET = nc_data.variables[case.productVars['et']]
            lat, lon, lat_spacing, lon_spacing, lat_size, lon_size = getSpatialAttributes(cfg, nc_data)
            fig, ax2 = plt.subplots(1, 1, figsize=(10, 8))
            fig.subplots_adjust(right=0.8)
            xticks = createAxisTicks(cfg, lon, lon_size, lon_spacing)
            yticks = createAxisTicks(cfg, lat, lat_size, lat_spacing)
            
            minLon = min(xticks)
            maxLon = max(xticks)
            minLat = min(yticks)
            maxLat = max(yticks)
            
            latTickSpacing = 0.05
            lonTickSpacing = 0.05
            
            xticks2 = [round(round(lon, 1) + xi*lonTickSpacing, 2) for xi in range(int((maxLon-minLon/lonTickSpacing))+1)]
            yticks2 = [round(round(lat, 1) - yi*latTickSpacing, 2) for yi in range(int((maxLat-minLat)/latTickSpacing)+1)]
            
            dataWestLon = lon
            dataEastLon = lon + ((lon_size-1)*lon_spacing)
            dataNorthLat = lat
            dataSouthLat = lat - ((lat_size-1)*(lat_spacing))
            
            #"avgLon" stuff was here
            
            
            
            ax = plt.axes(projection=proj)
            pcm = ax.pcolormesh(xticks, yticks, ET, cmap='cividis', vmin=0, vmax=15, alpha=1, linewidth=0, rasterized=True)
            pcm.set_edgecolor('face')
            
            ax.add_feature(USCOUNTIES.with_scale('20m'), facecolor='none', edgecolor='white')
            drawFeaturesWithAxis(cfg, case, plt, ax, ax2, xticks, yticks, xticks2, yticks2, proj)
            
           
            plt.title(cfg.storm+' '+case.ID+' '+tString+' ET', loc='center', fontsize=20)

            plotCluster(cfg, case, plt, ax, tString)

            plotETCluster(cfg, case, plt, ax, tString)
                

            cbar_ax = fig.add_axes([0.82, 0.15, 0.04, 0.7])
            cbar = fig.colorbar(pcm, cax=cbar_ax)
            cbar.set_label("Echo Top (km)", fontsize=18)
            cbar.ax.tick_params(labelsize='x-large')
            cbar.solids.set_edgecolor('face')
            
            nc_data.close()
            
            setExtent(ax, dataWestLon, dataEastLon, dataSouthLat, dataNorthLat, proj)
            
            savePath = case.saveDir+'/figs/'+cfg.figurePrefix+str(tString)+'_'+altString+'_et.png'
            pdfPath = case.saveDir+'/pdf/'+cfg.figurePrefix+str(tString)+'_'+altString+'_et.pdf'
            cfg.log("Saving "+savePath)
            plt.savefig(savePath, format='png')
            plt.savefig(pdfPath, format='pdf')
            
            plt.close()
        
       
        return 
            
    except Exception as E:
        cfg.error("Exception in echoTopPlot\n"+str(E))
        raise



        
        

def createVILPlot(cfg, case, tilt, count):
	
    try:
    
        altString = ''
        #modBottom = str(float(cfg.bottom)+(round(float(case.sites[0].hgt)/1000,2)))
        modBottom = cfg.bottom
        if len(modBottom) <= 3:
            altString = '0'+modBottom+'0'
        else:
            altString = '0'+modBottom
            
        files = os.listdir(os.path.join(case.dataDir, case.productVars['vil'], altString))
        files.sort()
        
        proj = ccrs.PlateCarree()
        
        titleTilt = str(float(tilt.strip('0')))
        
        for fi in files:
            currentFile = os.path.join(case.dataDir, case.productVars['vil'], altString, fi)
            tString = fi[0:15]
            cfg.log('Creating VIL Plot for '+currentFile)
            nc_data = Dataset(currentFile, 'r')
            VIL = nc_data.variables[case.productVars['vil']]
            lat, lon, lat_spacing, lon_spacing, lat_size, lon_size = getSpatialAttributes(cfg, nc_data)
            fig, ax2 = plt.subplots(1, 1, figsize=(10, 8))
            fig.subplots_adjust(right=0.8)
            
            xticks = createAxisTicks(cfg, lon, lon_size, lon_spacing)
            yticks = createAxisTicks(cfg, lat, lat_size, lat_spacing)
            
            minLon = min(xticks)
            maxLon = max(xticks)
            minLat = min(yticks)
            maxLat = max(yticks)
            
            latTickSpacing = 0.05
            lonTickSpacing = 0.05
            
            xticks2 = [round(round(lon, 1) + xi*lonTickSpacing, 2) for xi in range(int((maxLon-minLon)/lonTickSpacing)+1)]
            yticks2 = [round(round(lat, 1) - yi*latTickSpacing, 2) for yi in range(int((maxLat-minLat)/latTickSpacing)+1)]
            
            
            dataWestLon = lon
            dataEastLon = lon + ((lon_size-1)*lon_spacing)
            dataNorthLat = lat
            dataSouthLat = lat - ((lat_size-1)*(lat_spacing))
            
            #"Avglon" stuff was here
            
            ax = plt.axes(projection=proj)
            pcm = ax.pcolormesh(xticks, yticks, VIL, cmap='plasma', vmin=0, vmax=30, alpha=1, linewidth=0, rasterized=True)
            pcm.set_edgecolor('face')
           
            plt.title(cfg.storm+' '+case.ID+' '+tString+' VIL '+str(titleTilt)+r'$^\circ$ Shear', loc='center', fontsize=20)

            ax.add_feature(USCOUNTIES.with_scale('20m'), facecolor='none', edgecolor='white')

            drawFeaturesWithAxis(cfg, case, plt, ax, ax2, xticks, yticks, xticks2, yticks2, proj)
            

            
            #Plot the VIL clusters if available
            plotCluster(cfg, case, plt, ax, tString)
            
                
            #Plot the max and min shear clusters
            plotShearClusters(cfg, case, plt, ax, tString, tilt, ax2=ax2)
                
            #Plot the echo top clusters if available
            plotETCluster(cfg, case, plt, ax, tString)
            
            cbar_ax = fig.add_axes([0.82, 0.15, 0.04, 0.7])
            cbar = fig.colorbar(pcm, cax=cbar_ax)
            cbar.set_label("VIL (kg $m^{-2}$)", fontsize=18)
            cbar.ax.tick_params(labelsize='x-large')
            cbar.solids.set_edgecolor('face')
            nc_data.close()
            
            setExtent(ax, dataWestLon, dataEastLon, dataSouthLat, dataNorthLat, proj)

            savePath = case.saveDir+'/figs/'+cfg.figurePrefix+str(tString)+'_'+tilt+'_vil.png'
            pdfPath = case.saveDir+'/pdf/'+cfg.figurePrefix+str(tString)+'_'+tilt+'_vil.pdf'
            
            cfg.log("Saving "+savePath)
            plt.savefig(savePath, format='png')
            plt.savefig(pdfPath, format='pdf')

            plt.close()
        
        return 
        
    except Exception as E:
        cfg.error("Exception in vilPlot\n"+str(E))
        raise
        
def createCCPlotTilt(cfg, case, tilt, index):
	
    try:
        
        altString = ''
        #modBottom = str(float(cfg.bottom)+(round(float(case.sites[0].hgt)/1000,2)))
        modBottom = cfg.bottom
        if len(modBottom) <= 3:
            altString = '0'+modBottom+'0'
        else:
            altString = '0'+modBottom
            
        currentDir = os.path.join(case.productDirs['cc'], case.productVars['cc']+'_tilt', tilt)
        files = os.listdir(currentDir)
        if '.working' in files:
            files.remove('.working')
        
        files.sort()
        
        proj = ccrs.PlateCarree()
        
        titleTilt = str(float(tilt.strip('0')))
        
        for fi in files:
            currentFile = os.path.join(currentDir, fi)
            tString = fi[0:15]
            cfg.log('Creating cc Plot for '+currentFile)
            nc_data = Dataset(currentFile, 'r')
            cc = nc_data.variables[case.productVars['cc']]
            lat, lon, lat_spacing, lon_spacing, lat_size, lon_size = getSpatialAttributes(cfg, nc_data)
            fig, ax2 = plt.subplots(1, 1, figsize=(10, 8))
            fig.subplots_adjust(right=0.8)
            
            xticks = createAxisTicks(cfg, lon, lon_size, lon_spacing)
            yticks = createAxisTicks(cfg, lat, lat_size, lat_spacing)
            
            minLon = min(xticks)
            maxLon = max(xticks)
            minLat = min(yticks)
            maxLat = max(yticks)
            
            latTickSpacing = 0.05
            lonTickSpacing = 0.05
            
            xticks2 = [round(round(lon, 1) + xi*lonTickSpacing, 2) for xi in range(int((maxLon-minLon)/lonTickSpacing)+1)]
            yticks2 = [round(round(lat, 1) - yi*latTickSpacing, 2) for yi in range(int((maxLat-minLat)/latTickSpacing)+1)]
            
            dataWestLon = lon
            dataEastLon = lon + ((lon_size-1)*lon_spacing)
            dataNorthLat = lat
            dataSouthLat = lat - ((lat_size-1)*(lat_spacing))
            
            ax = plt.axes(projection=proj)
            pcm = ax.pcolormesh(xticks, yticks, cc, cmap='jet', vmin=0.6, vmax=1, alpha=1, linewidth=0, rasterized=True)
            pcm.set_edgecolor('face')
          
            ax.add_feature(USCOUNTIES.with_scale('20m'), facecolor='none', edgecolor='grey')
            
            drawFeaturesWithAxis(cfg, case, plt, ax, ax2, xticks, yticks, xticks2, yticks2, proj)
            
            plt.title(cfg.storm+' '+case.ID+' '+tString+' RhoHV Tilt '+str(titleTilt)+r'$^\circ$', loc='center', fontsize=20)
            
            plotCluster(cfg, case, plt, ax, tString)
                
            plotShearClusters(cfg, case, plt, ax, tString, tilt, ax2=ax2)
                
                
            cbar_ax = fig.add_axes([0.82, 0.15, 0.04, 0.7])
            cbar = fig.colorbar(pcm, cax=cbar_ax)
            ax.set_xlim(xmin=min(xticks), xmax=max(xticks))
            ax.set_ylim(ymin=min(yticks), ymax=max(yticks))
            cbar.set_label("RhoHV", fontsize=18)
            cbar.ax.tick_params(labelsize='x-large')
            cbar.solids.set_edgecolor('face')
            nc_data.close()

            setExtent(ax, dataWestLon, dataEastLon, dataSouthLat, dataNorthLat, proj)
            
            savePath = case.saveDir+'/figs/'+cfg.figurePrefix+str(tString)+'_'+str(tilt)+'_cc_tilt.png'
            pdfPath = case.saveDir+'/pdf/'+cfg.figurePrefix+str(tString)+'_'+str(tilt)+'_cc_tilt.pdf'
            
            cfg.log("Saving "+savePath)
            plt.savefig(savePath, format='png')
            plt.savefig(pdfPath, format='pdf')

            plt.close()
        
        return 
        
    except Exception as E:
        cfg.error("Exception in CC plot\n"+str(E))
        raise
        
def createTDSPlotTilt(cfg, case, tilt, index):
	
    try:
    
        altString = ''
        #modBottom = str(float(cfg.bottom)+(round(float(case.sites[0].hgt)/1000,2)))
        modBottom = cfg.bottom
        
        if len(modBottom) <= 3:
            altString = '0'+modBottom+'0'
        else:
            altString = '0'+modBottom
            
        currentDir = os.path.join(case.productDirs['tds'], case.productVars['tds']+'_tilt', tilt)
        files = os.listdir(currentDir)
        files.sort()
        
        proj = ccrs.PlateCarree()
        
        titleTilt = str(float(tilt.strip('0')))
        
        for fi in files:
            currentFile = os.path.join(currentDir, fi)
            tString = fi[0:15]
            cfg.log('Creating tds Plot for '+currentFile)
            nc_data = Dataset(currentFile, 'r')
            tds = nc_data.variables[case.productVars['tds']]
            lat, lon, lat_spacing, lon_spacing, lat_size, lon_size = getSpatialAttributes(cfg, nc_data)
            
            fig, ax2 = plt.subplots(1, 1, figsize=(10, 8))
            fig.subplots_adjust(right=0.8)
            
            xticks = createAxisTicks(cfg, lon, lon_size, lon_spacing)
            yticks = createAxisTicks(cfg, lat, lat_size, lat_spacing)
            
            minLon = min(xticks)
            maxLon = max(xticks)
            minLat = min(yticks)
            maxLat = max(yticks)
            
            latTickSpacing = 0.05
            lonTickSpacing = 0.05
            
            xticks2 = [round(round(lon, 1) + xi*lonTickSpacing, 2) for xi in range(int((maxLon-minLon)/lonTickSpacing)+1)]
            yticks2 = [round(round(lat, 1) - yi*latTickSpacing, 2) for yi in range(int((maxLat-minLat)/latTickSpacing)+1)]
            
            dataWestLon = lon
            dataEastLon = lon + ((lon_size-1)*lon_spacing)
            dataNorthLat = lat
            dataSouthLat = lat - ((lat_size-1)*(lat_spacing))
            
            ax = plt.axes(projection=proj)
            pcm = ax.pcolormesh(xticks, yticks, tds, cmap='gnuplot2', vmin=0.4, vmax=1, alpha=1, linewidth=0, rasterized=True)

            ax.add_feature(USCOUNTIES.with_scale('20m'), facecolor='none', edgecolor='white')
            
            drawFeaturesWithAxis(cfg, case, plt, ax, ax2, xticks, yticks, xticks2, yticks2, proj)
            
            
            plt.title(cfg.storm+' '+case.ID+' '+tString+' TDS RhoHV Tilt '+str(titleTilt)+r'$^\circ$', loc='center', fontsize=20)

            
            plotCluster(cfg, case, plt, ax, tString)
            plotShearClusters(cfg, case, plt, ax, tString, tilt, ax2=ax2)    

            cbar_ax = fig.add_axes([0.82, 0.15, 0.04, 0.7])
            cbar = fig.colorbar(pcm, cax=cbar_ax)
            ax.set_xlim(xmin=min(xticks), xmax=max(xticks))
            ax.set_ylim(ymin=min(yticks), ymax=max(yticks))
            cbar.set_label("TDS RhoHV", fontsize=18)
            cbar.ax.tick_params(labelsize='x-large')
            cbar.solids.set_edgecolor('face')
            
            nc_data.close()

            setExtent(ax, dataWestLon, dataEastLon, dataSouthLat, dataNorthLat, proj)
            
            
            savePath = case.saveDir+'/figs/'+cfg.figurePrefix+str(tString)+'_'+str(tilt)+'_tds.png'
            pdfPath = case.saveDir+'/pdf/'+cfg.figurePrefix+str(tString)+'_'+str(tilt)+'_tds.pdf'
            
            cfg.log("Saving "+savePath)
            plt.savefig(savePath, format='png')
            plt.savefig(pdfPath, format='pdf')

            plt.close()
        
        return 
        
    except Exception as E:
        cfg.error("Exception in TDSPlot\n"+str(E))
        raise



        
def createVelocityPlotTilt(cfg, case, tilt, index):

    try:
    
        altString = ''
        #modBottom = str(float(cfg.bottom)+(round(float(case.sites[0].hgt)/1000,2)))
        modBottom = cfg.bottom
        if len(modBottom) <= 3:
            altString = '0'+modBottom+'0'
        else:
            altString = '0'+modBottom
            
        currentDir = os.path.join(case.productDirs['velocity'], case.productVars['velocity']+'_tilt', tilt)
        # if 'Composite' not in case.productVars['velocity']:
            # currentDir = os.path.join(currentDir+'Composite', altString)
        # else:
            # currentDir = os.path.join(currentDir, tilt)
            
        files = os.listdir(currentDir)
        if '.working' in files:
            files.remove('.working')
        files.sort()
        
        proj = ccrs.PlateCarree()
        
        titleTilt = str(float(tilt.strip('0')))
        
        for fi in files:
            
            currentFile = os.path.join(currentDir, fi)
            tString = fi[0:15]
            cfg.log('Creating Velocity Plot for '+currentFile)
            nc_data = Dataset(currentFile)
            velocity = nc_data.variables[case.productVars['velocity']]
            lat, lon, lat_spacing, lon_spacing, lat_size, lon_size = getSpatialAttributes(cfg, nc_data)
            
            fig, ax2 = plt.subplots(1, 1, figsize=(10, 8))
            fig.subplots_adjust(right=0.8)
            
            
            xticks = createAxisTicks(cfg, lon, lon_size, lon_spacing)
            yticks = createAxisTicks(cfg, lat, lat_size, lat_spacing)
            
            minLon = min(xticks)
            maxLon = max(xticks)
            minLat = min(yticks)
            maxLat = max(yticks)
            
            latTickSpacing = 0.05
            lonTickSpacing = 0.05
            
            xticks2 = [round(round(lon, 1) + xi*lonTickSpacing, 2) for xi in range(int((maxLon-minLon)/lonTickSpacing)+1)]
            yticks2 = [round(round(lat, 1) - yi*latTickSpacing, 2) for yi in range(int((maxLat-minLat)/latTickSpacing)+1)]
            
            dataWestLon = lon
            dataEastLon = lon + ((lon_size-1)*lon_spacing)
            dataNorthLat = lat
            dataSouthLat = lat - ((lat_size-1)*(lat_spacing))
            
            
            colorMap = cm.TtrappyColormap()
            #cmap = colorMap.cmaps["velocity"]
            cmap = plt.get_cmap('pyart_balance')
            ax = plt.axes(projection=proj)
            pcm = ax.pcolormesh(xticks, yticks, velocity, cmap=cmap, vmin=-50, vmax=50, alpha=1, linewidth=0, rasterized=True)
            pcm.set_edgecolor('face')

            ax.add_feature(USCOUNTIES.with_scale('20m'), facecolor='none', edgecolor='grey')
            
            drawFeaturesWithAxis(cfg, case, plt, ax, ax2, xticks, yticks, xticks2, yticks2, proj)
            
            plt.title(cfg.storm+' '+case.ID+' '+tString+' Velocity Tilt '+str(titleTilt)+r'$^\circ$', loc='center', fontsize=20)

                
            plotShearClusters(cfg, case, plt, ax, tString, tilt, ax2=ax2)
            
            
            cbar_ax = fig.add_axes([0.82, 0.15, 0.04, 0.7])
            cbar = fig.colorbar(pcm, cax=cbar_ax)
            cbar.set_label("Radial Velocity (m s$^{-1}$)", fontsize=18)
            cbar.ax.tick_params(labelsize='x-large')
            cbar.solids.set_edgecolor('face')
            
            nc_data.close()
            
            setExtent(ax, dataWestLon, dataEastLon, dataSouthLat, dataNorthLat, proj)
            
            savePath = case.saveDir+'/figs/'+cfg.figurePrefix+str(tString)+'_'+tilt+'_velocity_tilt.png'
            pdfPath = case.saveDir+'/pdf/'+cfg.figurePrefix+str(tString)+'_'+tilt+'_velocity_tilt.pdf'
            
            cfg.log("Saving "+savePath)
            plt.savefig(savePath, format='png')
            plt.savefig(pdfPath, format='pdf')
            
            plt.close()
        

        return 

    except Exception as E:
        cfg.error("Exception in velocity tilt plot\n"+str(E))
        raise


def createShearPlotTilt(cfg, case, tilt, index):

    try:
        altString = ''
        #modBottom = str(float(cfg.bottom)+(round(float(case.sites[0].hgt)/1000,2)))
        modBottom = cfg.bottom
        if len(modBottom) <= 3:
            altString = '0'+modBottom+'0'
        else:
            altString = '0'+modBottom
            
        currentDir = os.path.join(case.productDirs['shear'], case.productVars['shear']+'_tilt', tilt)
        # if 'Composite' not in case.productVars['shear']:
            # currentDir = os.path.join(currentDir+'Composite', altString)
        # else:
            # currentDir = os.path.join(currentDir, tilt)
            
        files = os.listdir(currentDir)
        if '.working' in files:
            files.remove('.working')
        files.sort()
        cfg.log('Shear Plot '+str(tilt)+' '+str(files))
        
        proj = ccrs.PlateCarree()
          
        titleTilt = str(float(tilt.strip('0')))
        
        for fi in files:

            currentFile = os.path.join(currentDir, fi)
            tString = fi[0:15]
            cfg.log('Creating Shear Plot for '+currentFile)
            nc_data = Dataset(currentFile)
            shear = nc_data.variables[case.productVars['shear']]
            lat, lon, lat_spacing, lon_spacing, lat_size, lon_size = getSpatialAttributes(cfg, nc_data)
            
           
            fig, ax2 = plt.subplots(1,1, figsize=(10, 8))
            fig.subplots_adjust(right=0.8)
            
            
             
            xticks = createAxisTicks(cfg, lon, lon_size, lon_spacing)
            yticks = createAxisTicks(cfg, lat, lat_size, lat_spacing)
            
            
            
            #shape_reader = shpreader.Reader('shape/county_shapefile/cb_2018_us_county_500k.shp')
            
            #counties = list(shape_reader.geometries())
            
            #COUNTIES = cfeature.ShapelyFeature(counties, ccrs.PlateCarree(central_longitude=np.array(lon, dtype='float64')))
            
            minLon = min(xticks)
            maxLon = max(xticks)
            minLat = min(yticks)
            maxLat = max(yticks)
            
            latTickSpacing = 0.05
            lonTickSpacing = 0.05
            
            xticks2 = [round(round(lon, 1) + xi*lonTickSpacing, 2) for xi in range(int((maxLon-minLon)/lonTickSpacing)+1)]
            yticks2 = [round(round(lat, 1) - yi*latTickSpacing, 2) for yi in range(int((maxLat-minLat)/latTickSpacing)+1)]
            
            dataWestLon = lon
            dataEastLon = lon + ((lon_size-1)*lon_spacing)
            dataNorthLat = lat
            dataSouthLat = lat - ((lat_size-1)*(lat_spacing))
            
            avgLon = min(xticks2) #(min(xticks2) + max(xticks2))/2
            avgLon2 = (min(xticks2) + max(xticks2))/2
            avgLat2 = (min(yticks2) + max(yticks2))/2
            
            ax = plt.axes(projection=proj)
            pcm = ax.pcolormesh(xticks, yticks, shear, cmap='seismic', vmin=-0.02, vmax=0.02, alpha=1, linewidth=0, rasterized=True)
            pcm.set_edgecolor('face')
            #pcm = None
            
            ax.add_feature(USCOUNTIES.with_scale('20m'), facecolor='none', edgecolor='grey')

            drawFeaturesWithAxis(cfg, case, plt, ax, ax2, xticks, yticks, xticks2, yticks2, proj)
            
            # ax2.text(0.1, 0.5, r"Latitude ($^\circ$)", rotation='vertical', va='bottom', ha='center', rotation_mode='anchor', fontsize='x-large')
            # ax2.text(0.5, 0.1, r"Longitude ($^\circ$)", rotation='horizontal', va='bottom', ha='center', rotation_mode='anchor', fontsize='x-large')

             
            dataType = 'AzShear'
            if '_abs' in case.productVars['shear']:
                dataType = '|AzShear|'

            plt.title(cfg.storm+' '+case.ID+' '+tString+' '+dataType+' Tilt '+titleTilt+r"$^\circ$", loc='center', fontsize=20)

                
            

            #Plot the VIL clusters if available
            plotCluster(cfg, case, plt, ax, tString)
                
            #Plot the max shear clusters if available
            plotShearClusters(cfg, case, plt, ax, tString, tilt, ax2=ax2)
            
            try:
                #plt.legend(['Counties', 'Cities', 'Case Start/End Points', 'Cluster Centroids', '+Clusters', '-Clusters'])
                cbar_ax = fig.add_axes([0.82, 0.15, 0.04, 0.7])
                cbar = fig.colorbar(pcm, cax=cbar_ax)
                cbar.set_label("Az Shear (s$^{-1}$)", fontsize=18)
                cbar.ax.tick_params(labelsize='x-large')
                cbar.solids.set_edgecolor("face")
            except Exception:
                pass
                
            nc_data.close()
            
          
            setExtent(ax, dataWestLon, dataEastLon, dataSouthLat, dataNorthLat, proj)
            
            
            savePath = case.saveDir+'/figs/'+cfg.figurePrefix+str(tString)+'_'+tilt+'_shear_tilt.png'
            pdfPath = case.saveDir+'/pdf/'+cfg.figurePrefix+str(tString)+'_'+tilt+'_shear_tilt.pdf'
            
            cfg.log("Saving "+savePath)
            plt.savefig(savePath, format='png')
            plt.savefig(pdfPath, format='pdf')
            
            plt.close()
            
            #cfg.error("Finished shear plot "+tString+" "+str(tilt))
        
        return 
        
    except Exception as E:
        cfg.error("Exception in shear tilt plot\n"+str(E))
        raise

def createZdrPlotTilt(cfg, case, tilt, index):

    try:
        altString = ''
        #modBottom = str(float(cfg.bottom)+(round(float(case.sites[0].hgt)/1000,2)))
        modBottom = cfg.bottom
        
        if len(modBottom) <= 3:
            altString = '0'+modBottom+'0'
        else:
            altString = '0'+modBottom
            
        currentDir = os.path.join(case.productDirs['Zdr'], case.productVars['Zdr']+'_tilt', tilt)
        # if 'Composite' not in case.productVars['shear']:
            # currentDir = os.path.join(currentDir+'Composite', altString)
        # else:
            # currentDir = os.path.join(currentDir, tilt)
            
        files = os.listdir(currentDir)
        if '.working' in files:
            files.remove('.working')
        files.sort()

        proj = ccrs.PlateCarree()
        
        titleTilt = str(float(tilt.strip('0')))
        
        for fi in files:

            currentFile = os.path.join(currentDir, fi)
            tString = fi[0:15]
            cfg.log('Creating Zdr Plot for '+currentFile)
            nc_data = Dataset(currentFile)
            shear = nc_data.variables[case.productVars['Zdr']]
            lat, lon, lat_spacing, lon_spacing, lat_size, lon_size = getSpatialAttributes(cfg, nc_data)
            
            fig, ax2 = plt.subplots(1, 1, figsize=(10, 8))
            fig.subplots_adjust(right=0.8)
            
            xticks = createAxisTicks(cfg, lon, lon_size, lon_spacing)
            yticks = createAxisTicks(cfg, lat, lat_size, lat_spacing)
            
            minLon = min(xticks)
            maxLon = max(xticks)
            minLat = min(yticks)
            maxLat = max(yticks)
            
            latTickSpacing = 0.05
            lonTickSpacing = 0.05
            
            xticks2 = [round(round(lon, 1) + xi*lonTickSpacing, 2) for xi in range(int((maxLon-minLon)/lonTickSpacing)+1)]
            yticks2 = [round(round(lat, 1) - yi*latTickSpacing, 2) for yi in range(int((maxLat-minLat)/latTickSpacing)+1)]
            
            dataWestLon = lon
            dataEastLon = lon + ((lon_size-1)*lon_spacing)
            dataNorthLat = lat
            dataSouthLat = lat - ((lat_size-1)*(lat_spacing))
            
            ax = plt.axes(projection=proj)
            pcm = ax.pcolormesh(xticks, yticks, shear, cmap='pyart_BuOrR14', vmin=-5, vmax=5)
            pcm.set_edgecolor('face')
            
            dataType = 'Zdr'
            
            ax.add_feature(USCOUNTIES.with_scale('20m'), facecolor='none', edgecolor='grey')

            drawFeaturesWithAxis(cfg, case, plt, ax, ax2, xticks, yticks, xticks2, yticks2, proj)

            plt.title(cfg.storm+' '+case.ID+' '+tString+' '+dataType+' Tilt '+titleTilt+r'$^\circ$', loc='center', fontsize=20)

                
            plotShearClusters(cfg, case, plt, ax, tString, tilt, ax2=ax2)
                
            
            cbar_ax = fig.add_axes([0.82, 0.15, 0.04, 0.7])
            cbar = fig.colorbar(pcm, cax=cbar_ax)
            cbar.set_label("Differential Reflectivity (dB)", fontsize=18)
            cbar.ax.tick_params(labelsize='x-large')
            cbar.solids.set_edgecolor('face')
            nc_data.close()
                
            savePath = case.saveDir+'/figs/'+cfg.figurePrefix+str(tString)+'_'+tilt+'_zdr_tilt.png'
            pdfPath =  case.saveDir+'/pdf/'+cfg.figurePrefix+str(tString)+'_'+tilt+'_zdr_tilt.pdf'
            
            cfg.log("Saving "+savePath)
            plt.savefig(savePath, format='png')
            plt.savefig(pdfPath, format='pdf')
            
            plt.close()
        
        return 
        
    except Exception as E:
        cfg.error("Exception in zdr tilt plot\n"+str(E))
        raise

def createRefPlotTilt(cfg, case, tilt, index):

    print('Attempting ref plot tilt', tilt, 'case', case.ID)
    
    try:
        altString = ''
        #modBottom = str(float(cfg.bottom)+(round(float(case.sites[0].hgt)/1000,2)))
        modBottom = cfg.bottom
        
        if len(modBottom) <= 3:
            altString = '0'+modBottom+'0'
        else:
            altString = '0'+modBottom
            
        currentDir = os.path.join(case.productDirs['ref0'], case.productVars['ref0']+'_tilt', tilt)
        # if 'Composite' not in case.productVars['shear']:
            # currentDir = os.path.join(currentDir+'Composite', altString)
        # else:
            # currentDir = os.path.join(currentDir, tilt)
            
        files = os.listdir(currentDir)
        if '.working' in files:
            files.remove('.working')
        files.sort()
        cfg.log('Ref Plot '+str(tilt)+' '+str(files))
        
        proj = ccrs.PlateCarree()
        
        titleTilt = str(float(tilt.strip('0')))
        
        for fi in files:

            currentFile = os.path.join(currentDir, fi)
            tString = fi[0:15]
            cfg.log('Creating Ref Plot for '+currentFile)
            nc_data = Dataset(currentFile)
            ref = nc_data.variables[case.productVars['ref0']]
            lat, lon, lat_spacing, lon_spacing, lat_size, lon_size = getSpatialAttributes(cfg, nc_data)
            
            fig, ax2 = plt.subplots(1, 1, figsize=(10, 8))
            fig.subplots_adjust(right=0.8)
            
            xticks = createAxisTicks(cfg, lon, lon_size, lon_spacing)
            yticks = createAxisTicks(cfg, lat, lat_size, lat_spacing)
            
            minLon = min(xticks)
            maxLon = max(xticks)
            minLat = min(yticks)
            maxLat = max(yticks)
            
            latTickSpacing = 0.05
            lonTickSpacing = 0.05
            
            xticks2 = [round(round(lon, 1) + xi*lonTickSpacing, 2) for xi in range(int((maxLon-minLon)/lonTickSpacing)+1)]
            yticks2 = [round(round(lat, 1) - yi*latTickSpacing, 2) for yi in range(int((maxLat-minLat)/latTickSpacing)+1)]
            
            dataWestLon = lon
            dataEastLon = lon + ((lon_size-1)*lon_spacing)
            dataNorthLat = lat
            dataSouthLat = lat - ((lat_size-1)*(lat_spacing))
            
            ax = plt.axes(projection=proj)
            cmap = plt.get_cmap('pyart_HomeyerRainbow')
            pcm = ax.pcolormesh(xticks, yticks, ref, cmap=cmap, vmin=0, vmax=70, alpha=1, linewidth=0, rasterized=True)
            pcm.set_edgecolor('face')
            
            dataType = 'ZQC'
            

            ax.add_feature(USCOUNTIES.with_scale('20m'), facecolor='none', edgecolor='grey')

            drawFeaturesWithAxis(cfg, case, plt, ax, ax2, xticks, yticks, xticks2, yticks2, proj)
            
            plt.title(cfg.storm+' '+case.ID+' '+tString+' '+dataType+' Tilt '+titleTilt+r'$^\circ$', loc='center', fontsize=20)


            #Plot the VIL clusters if available
            
            plotCluster(cfg, case, plt, ax, tString)
            
            plotShearClusters(cfg, case, plt, ax, tString, tilt, ax2=ax2)
            
            
            cbar_ax = fig.add_axes([0.82, 0.15, 0.04, 0.7])
            cbar = fig.colorbar(pcm, cax=cbar_ax)
            cbar.set_label("Reflectivity (dBZ)", fontsize=18)
            cbar.ax.tick_params(labelsize='x-large')
            cbar.solids.set_edgecolor('face')
            
            nc_data.close()
            
            setExtent(ax, dataWestLon, dataEastLon, dataSouthLat, dataNorthLat, proj)
                
            savePath = case.saveDir+'/figs/'+cfg.figurePrefix+str(tString)+'_'+tilt+'_ref_tilt.png'
            pdfPath = case.saveDir+'/pdf/'+cfg.figurePrefix+str(tString)+'_'+tilt+'_ref_tilt.pdf'
            
            cfg.log("Saving "+savePath)
            plt.savefig(savePath, format='png')
            plt.savefig(pdfPath, format='pdf')
            
            plt.close()
        
        return 
        
    except Exception as E:
        cfg.error("Exception in ref tilt plot\n"+str(E))
        raise

        
def createRefPlot(cfg, case, alt):

    try:
    
        altString = ''
        #modBottom = str(float(cfg.bottom)+(round(float(case.sites[0].hgt)/1000,2)))
        modBottom = cfg.bottom
        if len(modBottom) <= 3:
            altString = '0'+modBottom+'0'
        else:
            altString = '0'+modBottom
            
        if 'Composite' in cfg.shed:
            alt = altString
            
        files = os.listdir(os.path.join(case.dataDir, case.productVars['ref'], alt))
        files.sort()
        if '.working' in files:
            files.remove('.working')
        fileCount = 0

        proj = ccrs.PlateCarree()
        
        
        for fi in files:
            currentFile = os.path.join(case.dataDir, case.productVars['ref'], alt, fi)
            refTString = fi[0:15]
            cfg.log('Creating Ref Plot for '+currentFile)
            nc_data = Dataset(currentFile, 'r')
            ref = nc_data.variables[case.productVars['ref']]
            
            cent_lat, cent_lon, lat_spacing, lon_spacing, lat_size, lon_size = getSpatialAttributes(cfg, nc_data)
            fig, ax2 = plt.subplots(1, 1, figsize=(10, 8))
            fig.subplots_adjust(right=0.8)
            
            xticks = createAxisTicks(cfg, cent_lon, lon_size, lon_spacing)
            yticks = createAxisTicks(cfg, cent_lat, lat_size, lat_spacing)
            
            
            minLon = min(xticks)
            maxLon = max(xticks)
            minLat = min(yticks)
            maxLat = max(yticks)
            
            latTickSpacing = 0.05
            lonTickSpacing = 0.05
            
            xticks2 = [round(round(cent_lon, 1) + xi*lonTickSpacing, 2) for xi in range(int((maxLon-minLon)/lonTickSpacing)+1)]
            yticks2 = [round(round(cent_lat, 1) - yi*latTickSpacing, 2) for yi in range(int((maxLat-minLat)/latTickSpacing)+1)]
            
            dataWestLon = cent_lon
            dataEastLon = cent_lon + ((lon_size-1)*lon_spacing)
            dataNorthLat = cent_lat
            dataSouthLat = cent_lat - ((lat_size-1)*(lat_spacing))
            
            ax = plt.axes(projection=proj)
            colorMap = cm.TtrappyColormap()
            #cmap = colorMap.cmaps["reflectivity"]
            cmap = plt.get_cmap('pyart_HomeyerRainbow')
            pcm = ax.pcolormesh(xticks, yticks, ref, cmap=cmap, vmin=0, vmax=70, alpha=1, linewidth=0, rasterized=True) 
            
            ax.add_feature(USCOUNTIES.with_scale('20m'), facecolor='none', edgecolor='grey')

            drawFeaturesWithAxis(cfg, case, plt, ax, ax2, xticks, yticks, xticks2, yticks2, proj)
            
            plt.title(cfg.storm+' '+case.ID+' '+refTString+' '+'COMPREFQC', loc='center', fontsize=20)

            

            if (case.hasDir['cluster']):
                clu_shed_files = os.listdir(case.productDirs['cluster']+'/'+case.productVars['cluster']+'/scale_0/')

                nearestTime = 9999999999
                closestIndex = 9999999999
                counter = 0
                closestString = ''

                for fi3 in  clu_shed_files:
                    cluShedDString = fi3[0:15]
                    currentDT, greater, equal = getStringDT(cfg, refTString, cluShedDString)
                    if (currentDT < nearestTime and (greater or equal)):
                        nearestTime = currentDT
                        closestIndex = counter
                        closestString = cluShedDString
                    counter = counter + 1


                clu_shed_nc_data = Dataset(case.productDirs['cluster']+'/'+case.productVars['cluster']+'/scale_0/'+clu_shed_files[closestIndex])
                clu_shed = clu_shed_nc_data.variables[case.productVars['cluster']]
                [vlats, vlons, vlat_spacing, vlon_spacing, vlat_size, vlon_size] = getSpatialAttributes(cfg, clu_shed_nc_data)
                xvticks = createAxisTicks(cfg, vlons, vlon_size, vlon_spacing)
                yvticks = createAxisTicks(cfg, vlats, vlat_size, vlat_spacing)
                XV, YV = np.meshgrid(xvticks, yvticks)
                plt.contour(XV, YV, clu_shed[:], 0, linewidths=3)
                clu_shed_nc_data.close()
                
                
                
                
                    
                #plt.text(0.02, 0.9, 'CLUSTER SHED Time \n'+closestString, color='grey', transform=ax.transAxes)
            
            cbar_ax = fig.add_axes([0.82, 0.15, 0.04, 0.7])
            cbar = fig.colorbar(pcm, cax=cbar_ax)
            ax.set_xlim(xmin=min(xticks), xmax=max(xticks))
            ax.set_ylim(ymin=min(yticks), ymax=max(yticks))
            cbar.set_label("Reflectivity (dBZ)", fontsize=18)
            cbar.ax.tick_params(labelsize='x-large')
            cbar.solids.set_edgecolor('face')
            
            nc_data.close()

            savePath = case.saveDir+'/figs/'+cfg.figurePrefix+str(refTString)+'_'+alt+'_ref.png'
            pdfPath = case.saveDir+'/pdf/'+cfg.figurePrefix+str(refTString)+'_'+alt+'_ref.pdf'
   
            plt.savefig(savePath, format='png')
            plt.savefig(pdfPath, format='pdf')
            cfg.log("Saving "+savePath)    
            plt.close()
        
        return 

    except Exception as E:
        cfg.error("Exception in refPlot\n"+str(E))
        raise
        
        
def createPlots(cfg, case):

    
    args = []
    targets = []

    #Add this to disable attempts to connect to X Server
    mpl.use('AGG')
    
    if (case.hasDir['ref'] and MATPLOTLIB):
        for alt in cfg.shearAltList:
            args.append((cfg, case, alt))
            targets.append(createRefPlot)
    # if (case.hasDir['refshed'] and MATPLOTLIB):
        # for alt in cfg.shearAltList:
            # args.append((cfg, case, alt))
            # targets.append(createRefShedPlot)
    # if (case.hasDir['shear'] and MATPLOTLIB):
        # count = 0
        # for alt in cfg.shearAltList:
            # args.append((cfg, case, alt, count))
            # targets.append(createShearPlot)
            # count = count + 1
    # if (case.hasDir['velocity'] and MATPLOTLIB):
        # count = 0
        # for alt in cfg.shearAltList:
            # args.append((cfg, case, alt, count))
            # targets.append(createVelocityPlot)
            # count = count + 1
    # if (case.hasDir['shearshed'] and MATPLOTLIB):
        # count = 0
        # for alt in cfg.shearAltList:
            # args.append((cfg, case, alt, count))
            # targets.append(createShearShedPlots)
            # count = count + 1
    # if (case.hasDir['vil'] and MATPLOTLIB):
        # args.append((cfg, case))
        # targets.append(createVILPlot)
        
    # if (case.hasDir['cc'] and MATPLOTLIB):
        # args.append((cfg, case))
        # targets.append(createCCPlot)
        
    # if (case.hasDir['tds'] and MATPLOTLIB):
        # args.append((cfg, case))
        # targets.append(createTDSPlot)
        
    # if (case.hasDir['vilshed'] and MATPLOTLIB):
        # args.append((cfg, case))
        # targets.append(createVILShedPlot)
        
    if (case.hasDir['et'] and MATPLOTLIB):
        args.append((cfg, case))
        targets.append(createETPlot)
        
    # if (case.hasDir['motion'] and MATPLOTLIB):
        # args.append((cfg, case))
        # targets.append(createMotionPlot)
        
    if (case.hasDir['clustertable'] and MATPLOTLIB):
        args.append((cfg, case))
        targets.append(createClusterShedPlot)
        
    if (cfg.tiltList and MATPLOTLIB):
        count = 0
        for tilt in cfg.tiltList:
            if case.hasDir['velocity']:
                args.append((cfg, case, tilt, count))
                targets.append(createVelocityPlotTilt)
            if case.hasDir['shear']:
                args.append((cfg, case, tilt, count))
                targets.append(createShearPlotTilt)
            if case.hasDir['cc']:
                args.append((cfg, case, tilt, count))
                targets.append(createCCPlotTilt)
            if case.hasDir['tds']:
                args.append((cfg, case, tilt, count))
                targets.append(createTDSPlotTilt)
            if (case.hasDir['vil'] and MATPLOTLIB):
                args.append((cfg, case, tilt, count))
                targets.append(createVILPlot)
            if (case.hasDir['Zdr'] and MATPLOTLIB):
                args.append((cfg, case, tilt, count))
                targets.append(createZdrPlotTilt)
            if (case.hasDir['ref0'] and MATPLOTLIB):
                print('Added tilt', tilt, 'for ref plot tilt')
                args.append((cfg, case, tilt, count))
                targets.append(createRefPlotTilt)
                print(targets[-1], args[-1])
        count += 1
            
    
    try:
        #Try to limit the number of processes to 16
        
        procs = []
        results= []
        
        maxProcesses = 14
        a = 0
        while a < len(targets):
            if len(procs) < maxProcesses:
                p = mp.Process(target=targets[a], args=args[a])
                p.start()
                procs.append(p)
                
                
                print('Starting', targets[a], 'with args', args[a])
                
                a += 1
            
            if len(procs) >= maxProcesses:
                while (len(procs) >= maxProcesses):
                    
                    procs2 = procs
                    #Go through each process and see if it is alive
                    for p in procs:
                        if not p.is_alive():
                        
                            #If the process is dead, join it and remove it from procs2
                            p.join()
                            #We remove the process from a copy of the process list to avoid modifying something we
                            #are iterating over.
                            procs2.remove(p)
                
                    procs = procs2
                    time.sleep(3)
                    
            if a == (len(targets) - 1):
            
                while (len(procs) > 0):
                
                    for p in procs:
                        if not p.is_alive():
                        
                            p.join()
                            
                            procs2.remove(p)
                            
                    procs = procs2
                    time.sleep(3)
                    
                    
            time.sleep(1)
    except Exception as E:
        cfg.log("Exception in plotting "+str(E))
        for p in procs:
            p.terminate()
            p.join()
        raise
    
    for p in procs:
        p.join()

    cfg.log("End of plotting")
    
    return


#Below here are the definitions for the visualzation application

class Visualizer(tk.Frame):

    
    def __init__(self, master=None):
        super().__init__(master)
        self.__master = master
                
        return

class Figure():
    """ Holds the path, figure type, and time of figure. Requires the filename format match the original 
    naming scheme YYYYMMDD-HHMMSS_0alt0_type  where type could be velocity, shear, vil, shear_shed, etc."""
    
    def __init__(self, path, fName):
        
        self.__path = path
        self.__fName = fName
        
        dashIndex = fName.index('-')
        timeString = fName[dashIndex-8:dashIndex+7]
        self.__dt = datetime.strptime(timeString, '%Y%m%d-%H%M%S')
        self.__alt = fName[dashIndex+8:dashIndex+13]
        self.__type = fName[dashIndex+14:-4]
        
        return
        
    def isActive(self):
        return self.__isActive
        
    def activate(self):
        self.__isActive = True
        return
    def deactivate(self):
        self.__isActive = False
    def getPath(self):
        return self.__path
    def getFullPath(self):
        return os.path.join(self.__path, self.__fName)
    def getFileName(self):
        return self.__fName
    def getDateTime(self):
        return self.__dt
    def getAlt(self):
        return self.__alt
    def getType(self):
        return self.__type
    

    
class CaseFigures():

    
    def __init__(self, cfg, saveDir, name):
        
        figurePath = os.path.join(saveDir, 'figs')
        figuresExist = os.path.exists(figurePath)
        self.__name = name
        
        if figuresExist:
        
            self.__hasFigures = True
            figureFileNames = os.listdir(figurePath)
            
            #Create all the figure objects
            self.__allFigures = []
            self.__allFiles = []
            self.__figuresByType = {}
            self.__orderedFigs = {}
            
            for fName in figureFileNames:
                self.__allFigures.append(Figure(figurePath, fName))
                currentType = self.__allFigures[-1].getAlt()+'_'+self.__allFigures[-1].getType()
                self.__allFiles.append(self.__allFigures[-1].getFullPath())
                if currentType not in self.__figuresByType.keys():
                    self.__figuresByType[currentType] = []
                    self.__orderedFigs[currentType] = []
            
            #Sort all the figure objects into their chronological lists
            for type in self.__figuresByType.keys():
                for fig in self.__allFigures:
                    fullType = fig.getAlt()+'_'+fig.getType()
                    if fullType == type:
                        self.__figuresByType[type].append(fig)
                        
            for currentType in self.__figuresByType.keys():
                self.__orderedFigs[currentType] = self.orderFigs(self.__figuresByType[currentType])
                
        else:
            cfg.log("No figures detected. Please start TTRAP or run an archived case")
            self.__hasFigures = False
            
        return
        

    def orderFigs(self, figs):

        bestFigs = []
        figsCopy = figs
        first = True
        for a in range(len(figs)):
           
            startDT = datetime.now() + timedelta(seconds=99999999)
            bestFig = None
            for fig in figsCopy:
                if fig.getDateTime() < startDT:
                    bestFig = fig
                    startDT = bestFig.getDateTime()

            bestFigs.append(bestFig)
            
            figsCopy.remove(bestFig)

        return bestFigs        

    
        
    def getOrderedFigs(self):
        return self.__orderedFigs
    def getTypes(self):
        return self.__orderedFigs.keys()
    def hasFigures(self):
        return self.__hasFigures
    def getFiles(self):
        return self.__allFiles
        
        
class StormFigures():

    def __init__(self, name):
        self.__cases = {}
        self.__name = name
        return
        
        
    def addCase(self, case, name):
        self.__cases[name] = case
        return
        
    def getCases(self):
        return self.__cases
    def getCase(self, caseName):
        return self.__cases[caseName]
    def getName(self):
        return self.__name
        
class FigManager():

    """ Holds information regarding the figures to be displayed in the gui """
    
    def __init__(self, cfg):
        
        self.__cfg = cfg
        self.__storms = {}
        self.__figures = [None, None, None, None]
        self.__images = [None, None, None, None]
        self.__canvases = [None, None, None, None]
        self.__originalWidth = 640
        self.__originalHeight = 640
        self.__currentWidth = self.__originalWidth
        self.__currentHeight = self.__originalHeight
        self.__currentX = 0
        self.__currentY = 0
        
        
        self.__activeIndex = 0
        
        stormsExist = self.checkStorms(cfg)
        if stormsExist:
            self.__hasStorms = True
        else:
            self.__hasStorms = False
            cfg.log("Warning! No storms detected for FigManager")
            
    def checkStorms(self, cfg):
        return os.path.exists(cfg.baseDir)
        
    def createStorms(self, cfg):
        stormDirs = os.listdir(cfg.baseDir)
        for storm in stormDirs:
            newStorm = StormFigures(storm)
            casesDir = os.path.join(cfg.baseDir, storm, cfg.caseDir)
            caseDirs = os.listdir(casesDir)
            for caseName in caseDirs:
                saveDir = os.path.join(casesDir, caseName, cfg.saveDir)
                newStorm.addCase(CaseFigures(cfg, saveDir, caseName), caseName)
            
            self.__storms[storm] = newStorm
            
        return
        
    def hasStorms(self):
        return self.__hasStorms
    
    def getStorms(self):
        return  self.__storms
        
    def getStorm(self, name):
        return self.__storms[name]
        
    def setSlot(self, cfg, figs, number):
        if number > 4 or number < 0:
            cfg.log("Warning. "+str(number)+" Not a valid slot!")
        else:
            self.__figures[number] = figs
        return
    def setCanvas(self, cfg, canvas, number):
        if number > 4 or number < 0:
            cfg.log("Warning. "+str(number)+" Not a valid slot!")
        else:
            self.__canvases[number] = canvas
        return
        
    def setImages(self, cfg, images, number):
        if number > 4 or number < 0:
            cfg.log("Warning. "+str(number)+" Not a valid slot!")
        else:
            self.__images[number] = images
        return
        
    def removeSlot(self, cfg, number):
        if number > 4 or number < 0:
            cfg.log("Warning. "+str(number)+" Not a valid slot!")
        else:
            self.__figures[number] = None
        return
        
    def removeCanvas(self, cfg, number):
        if number > 4 or number < 0:
            cfg.log("Warning. "+str(number)+" Not a valid slot!")
        else:
            self.__canvases[number] = None
        return
        
    def removeImages(self, cfg, number):
        if number > 4 or number < 0:
            cfg.log("Warning. "+str(number)+" Not a valid slot!")
        else:
            self.__images[number] = None
        return
        
    def getSlot(self, cfg, number):
        if number > 4 or number < 0:
            cfg.log("Warning. "+str(number)+" Not a valid slot!")
        else:
            return self.__figures[number]
        return 
        
    def getCanvas(self, cfg, number):
        if number > 4 or number < 0:
            cfg.log("Warning. "+str(number)+" Not a valid slot!")
        else:
            return self.__canvases[number]
        return None
        
    def getCanvases(self):
        return self.__canvases
        
    def getImages(self, cfg, number):
        if number > 4 or number < 0:
            cfg.log("Warning. "+str(number)+" Not a valid slot!")
        else:
            return self.__images[number]
        return None
        
    def getActiveImage(self, cfg, number):
        if number > 4 or number < 0:
            cfg.log("Warning. "+str(number)+" Not a valid slot!")
        else:
            if self.__activeIndex >= len(self.__images[number]):
                self.__activeIndex = len(self.__images[number])-1
                
            return self.__images[number][self.__activeIndex]
        return None
      
    def setActiveImage(self, cfg, image, number):
        if number > 4 or number < 0:
            cfg.log("Warning. "+str(number)+" Not a valid slot!")
        else:
            self.__images[number][self.__activeIndex] = image
            
        return
        
    def incrementTime(self, indices):
        self.__activeIndex += 1
        for i in indices:
            if self.__activeIndex >= len(self.__images[i]):
                self.__activeIndex = len(self.__images[i]) - 1                
        return
        
    def decreaseTime(self, indices):
        self.__activeIndex -= 1
        for i in indices:
            if self.__activeIndex <= 0:
                self.__activeIndex = 0
        return
        
    def getCurrentWidth(self):
        return self.__currentWidth
    def setCurrentWidth(self, newWidth):
        self.__currentWidth = newWidth
        return
        
    def getCurrentHeight(self):
        return self.__currentHeight
    def setCurrentHeight(self, newHeight):
        self.__currentHeight = newHeight
        
    def getCurrentX(self):
        return self.__currentX
    def setCurrentX(self, newX):
        self.__currentX = newX
        return
        
    def getCurrentY(self):
        return self.__currentY
    def setCurrentY(self, newY):
        self.__currentY = newY
        
    def setDimensions(self, newX, newY, newWidth, newHeight):
        self.__currentX = newX
        self.__currentY = newY
        self.__currentWidth = newWidth
        self.__currentHeight = newHeight
        return
        
    def getOriginalWidth(self):
        return self.__originalWidth
    def getOriginalHeight(self):
        return self.__originalHeight
        
class ComboBoxes():
    
    def __init__(self):
        self.__stormBox = None
        self.__caseBox = None
        self.__figBox = None
    
    def setStorm(self, sBox):
        self.__stormBox = sBox
        return
    def setCase(self, cBox):
        self.__caseBox = cBox
        return
    def setFig(self, fBox):
        self.__figBox = fBox
        return
        
    def getStorm(self):
        return self.__stormBox
    def getCase(self):
        return self.__caseBox
    def getFig(self):
        return self.__figBox