#This module contains the distance claculation function

import math

R = 6371 #Radius of the Earth in km

#Calculates the Distance Between 2 points along a great circle
#Based on information from https://www.movable-type.co.uk/scripts/latlong.html

def calculateDistance(lat1, lon1, lat2, lon2):
        lat1r = math.radians(lat1)
        lon1r = math.radians(lon1)
        lat2r = math.radians(lat2)
        lon2r = math.radians(lon2)

        a = (math.sin((lat2r-lat1r)/2)**2)+(math.cos(lat1r)*math.cos(lat2r)*(math.sin((lon2r-lon1r)/2)**2))
        c = 2 * (math.atan2(math.sqrt(a), math.sqrt(1-a)))
        d = R * c

        return d

#Calculate bearing from one location to another. Based on iformation from the same place as above. Returns the atan2 value in degrees for better beaing differences
def calculateBearingAT(lat1, lon1, lat2, lon2):
	lat1r = math.radians(lat1)
	lon1r = math.radians(lon1)
	lat2r = math.radians(lat2)
	lon2r = math.radians(lon2)

	dLon = lon2r-lon1r

	theta = math.atan2(math.sin(dLon)*math.cos(lat2r), (math.cos(lat1r)*math.sin(lat2r))-(math.sin(lat1r)*math.cos(lat2r)*math.cos(dLon)))
	
	return math.degrees(theta)

def calculateBeamHeight(sRange, elevation, earthRadius, antHeight=0):
    """ Calculates the beam height above the radar at a given slant range (m), elevation (deg), and earthRadius (km).
        Follows equation (3.12) in Reinhart (2010) except H0 is neglected by default to give height above radar level instead of above sea level.
        Does not apply 4/3 refraction correction to earthRadius by default. Specify when calling calculateBeamHeight()
    """
    
    earthRadius = (earthRadius*1000)
    
    
    return math.sqrt((sRange**2)+((earthRadius + antHeight)**2)+(2*sRange*(earthRadius)*math.sin(elevation*(math.pi/180)))) - earthRadius
    
    
def calculateSlantRange(antHeight, earthRadius, groundRange):
        """ Calculates the slant range from the ground range. earthRadius is assumed to be (km). antHeight and groundRange assumed to be (m) """
        #Convert radius to m and calculate antenna height from the center of the earth
        earthRadius = earthRadius * 1000
        antHeightEarth = (earthRadius) + antHeight
        return math.sqrt(((antHeightEarth**2) + (earthRadius**2))- (2*antHeightEarth*earthRadius*math.cos(groundRange/earthRadius)))
        

def calculateBeamHeightIter(groundRange, elevation, radius, tolerance=0.1, maxIter=100):
    
    """ Attempts to calculate beam height iteratively using the equations 3 and 4 in Zhang et al. (2005; May be from Doviack and Zrnic 1993).

        Ground range is the range from radar projected to the earth's surface in meters, elevation is the vertical tilt of the radar from the horizon in degrees, and radius is the earth's radius in km (you probably want to provide 4/3 Rearth; This is not calculated).
        
        Tolerence is the error in meters for when iteration stops. maxIter is the maximum permissble iterations. After this many iterations, the value at this point is returned.
        
        The first guess for the iteration is what is calculated using calculateBeamHeight and calculateBeamHeight above. This method assumes that the antenna height is 0 (gives height above radar level). 
        
        """
    
    #Get the first guess
    h = calculateBeamHeight(calculateSlantRange(0, R, groundRange), elevation, radius)
    previousH = h
    print('First guess height', h*3.28084)
    
    radiusM = radius * 1000
    delta = 99999999
    n = 0
    const1 = ((math.sin(groundRange/radiusM)**2)/(math.cos(math.radians(elevation)))**2)
    const2 = ((math.sin(groundRange/radiusM))/(math.cos(math.radians(elevation))))
    while n <  maxIter:
        
        
        term1 = (radiusM + h)**2
        term2 = (radiusM + h)
        #print('const1', const1, 'const2', const2, 'term1', term1, 'term2', term2)
        h = math.sqrt((const1*term1) + (radiusM**2) + (2*const2*term2*radiusM*math.sin(math.radians(elevation)))) - radiusM
        delta = abs(previousH - h)
        print(n, 'Calculated new beam height', h, 'meters delta', delta, 'meters')
        if delta <= tolerance:
            print('Tolerance', tolerance, 'met. Stopping!')
            break
        previousH = h
        n += 1
        
    return h
    
    
def calculateDestination(lat, lon, bearing, dist):

    """ Calculates a "destination point" from the origin given the origin's latitude and longitude (in decimal degrees) and
        the bearing (in degrees) and distance (in km) from the origin to the distnation.
        
        Formula is "Destination point given distance and bearing from start point" from https://www.movable-type.co.uk/scripts/latlong.html 
    """
    
    #Cal
    angDist = dist/R
    
    bearingRad = math.radians(bearing)
    
    latRad = math.radians(lat)
    lonRad = math.radians(lon)
    
    lat2Rad = math.asin((math.sin(latRad)*math.cos(angDist)) + (math.cos(latRad)*math.sin(angDist)*math.cos(bearingRad)))
    lon2Rad = lonRad + math.atan2(math.sin(bearingRad)*math.sin(angDist)*math.cos(latRad), math.cos(angDist) - (math.sin(latRad)*math.sin(lat2Rad)))
    
    lat2Deg = math.degrees(lat2Rad)
    lon2Deg = math.degrees(lon2Rad)
    
    return lat2Deg, lon2Deg