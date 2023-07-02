
## Introduction

Output data from TTRAP can be found in the caseID/results/caseID_prelim.csv files in the results folder for each case. 

## Data

AA2015/NTA and AF2020/202007111931 are the example cases used to create this list. The column letters may be shifted slightly depending on the case. 


Column. Name (if applicable) - Description.

### General Case Information

**A. TC** - "Storm" name.  
**B. case** - The case ID.  
**C. tor** - 1 for tornadic, 0 for nontornadic.  
**D. F-EF-rating** - F or EF rating of the tornado. -1 for unknown (tornadic) or nontornadic.  
**E. class** - 0 for nontornadic (false alarm), 1 if the TCTOR was within a tornado warning at the TCTOR start time, or 2 if it was not. Some older files may have -1 for the class in general.  
**F and G. VCP(a)(b)** - VCP of the radars taken from their corresponding "AliasedVelocity" files where "a" represents the radar with 0 being the closest. "a" increases with increasing distance of radars from the case. "b" is the number of VCPs. If the VCP changes for a radar, a new column should be created.   
**H and I. VCP_duration(a)(c)** - The number of seconds the VCP was active. This is calculated by summing the differences in times between the "AliasedVelocity" files. It may be possible for a file to be left out of this calculation resulting in a slight underestimate. Both the VCPs and their durations are retrieved in the getVCPs method in case.py. "a" and "c" correspond to "a" and "b" for the VCP. <span style="color:red">Note: During the creation of this document, "c" was found to be set to the value of "b" resulting in an incorrect value of c. While this initially does not appear to effect the results, the value of c may be incorrect for some cases in previous analysis. The variable name has been corrected in the pushed version of this code.</span>  

### AzShear-Cluster Data

Columns J through AY represent the data for the 0.5 degree AzShear-cluster data. This set of data is repeated for each elevation angle.  

**J. RowName** - WDSS-II ID for the cluster.  
**K. DateTime** - Date and time associated with that particular elevation angle's sweep.  
**L. Bin** - Five-minute bin relative to TCTOR start time or warning feature-point time (reference time) for that particular sweep.  
**M. BinNumber** - Number of the bin in column L.  
**N. Timedelta** - Number of seconds relative to the reference time of that particular sweep.  
**O and P. Latitude and Longitude** - Latitude and Longitude of the cluster centroid.  
**Q and R. LatRadius and LonRadius** - Radius of the cluster in the latitude and longitude directions.  
**S. Orientation** - WDSS-II output. Not exactly sure and not used.  
**T and U. GroundRange a** - Approximate ground range from radar "a" where 0 is the closest radar used, 1 is the next closest, etc.  
**V. Size** - Area of the cluster.  
**W - Y. MotionEast, MotionSouth, and Speed** - WDSS-II output of the velocity to the East, South, and overall speed respectively. <span style="color:red">Note: This velocity is from the WDSS-II tracking, not TTRAP. If TTRAP switches clusters this motion will not be accurate. <b>Do not use!</b> Use the clusterU and V instead.</span>  
**Z. NumReports** - Number of "reports" (reference points) found by hailtruth_size. Should always be 1.  
**AA. DistToCell**  - Distance from the tracked cluster to the reference point as calculated by hailtruth_size.  
**AB. maxShear** - AzShear value in the cluster closest to positive infinity.  
**AC. minShear** - AzShear value in the cluster closest to negative infinity.  
**AD. 10thShear** - 10th percentile of AzShear values in the cluster.  
**AE. 90thShear** - 90th percentile of AzShear values in the cluster.  
**AF. minZdrTDS** - Minimum differential reflectivity of gates that meet TDS criteria in the cluster.  
**AG. minRhoHV** - Minimum RhoHV in the cluster.  
**AH. AreaVrot** - Estimation of Vrot assuming the cluster is circular and the radius of the circulation is the radius of that circle. The radius is calculated using the Size attribute.  
**AI. maxRefTDS** - Meant to be the maximum reflectivity of gates that meet TDS criteria. May not be implemented.  
**AJ. maxSpectrumWidth** - Maximum spectrum width in the cluster.  
**AK and AL. u and vShear**  - Average 6-km MSL minus surface u and v wind components.  
**AM and AN. clusterU and V** - sin and cos components of the speed of the clusters. If the average motion vector is being used, as it is in the Spotts (2023) analysis, the average motion of the tracking up to that point is used. See stormbuilder.py/calculateShearMotionVector (line 648)  
**AO. TDScount** - Number of pixels that meet TDS criteria in the cluster.  
**AP. TDSMmin** - Minimum RhoHV of pixels that meet TDS criteria in the cluster.  
**AQ and AR. Radar Bearing a** - Approximate heading from radar "a" to the cluster where again, increasing "a" is increasing distance of the radar from the cluster.  
**AS and AT. BeamHeight a** - Approximate beam height of the cluster centroid from radar "a" using the nominal elevation angle (e.g., 0.5 degrees versus 0.482 degrees).  
**AU - AX. foward and back Lat and Lon** - Latitude and longitude of the forward and backward projected points respectively.  
**AY. potentialClusters** - Number of clusters within a search radius of the projected point used in the tracking.  


Echo-top and VIL (Track) clusters have several of the same attributes. The cluster-specific attributes are listed below.  

### VIL (Track)-Cluster Data

**JH. avgVIL** - Average VIL within the VIL cluster.  
**JI. maxVIL** - Maximum VIL within the cluster.  
**JJ. maxREF** - Maximum composite reflectivity within the cluster.  
**JK and JL. u and v6kmMeanWind** - The u and v components of the average of the average 0 to 6 km wind.  

### Echo-Top-Cluster Data

**KF and KG. maxET** - The maximum echo top in the cluster in kilometers and feet.  
**KH and KI. 90thET** - The 90th percentile of echo-top values in the cluster in kilometers and feet.  


## Missing Values

-99900 or a very large number such as 2147483648 are used for missing data.  

-99904 is used if the data is missing, but the elevation angle is not missing in the data.  







