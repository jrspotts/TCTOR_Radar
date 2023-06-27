
# Tropical Cyclone Radar Analysis Program (TTRAP)

## 1. Introduction

The is repository holds the code and data used in the analysis of the Spotts (2023) MS thesis (not yet online) and subsequent publications under the name TTRAP. TTRAP is a Python program used to coordinate the downloading, processing, and analysis of NEXRAD Level-II and RAP-analysis data for tropical cyclone tornado (TCTOR) and nontornadic, but tornado warned, events within tropical-cyclone environments. While originally used for TCTOR events, the program can be used with nontornadic events as well. NEXRAD data is downloaded using the [nexradaws](https://github.com/aarande/nexradaws) Python module and both RAP and NEXRAD data are processed using [Warning Decision Support System - Integrated Information](http://wdssii.org/) (WDSS-II) algorithms. The w2segmotionll algorithm is used create "clusters" of potential areas of interest (AzShear, Vertically Integrated Liquid, and Echo Tops) in the radar data, track them across time, and record their attributes. A cluster of interest is then determined, tracked, associated with clusters at different elevation angles, VIL, and echo-top fields. The attributes of each cluster are then recorded for each tracked cluster. 

## 2. Disclaimer

This project was created to perform analysis for the Spotts (2023) Master's Thesis. Having finished this project, I have found that there are improvements that could be made to the code from a readability and efficiency perspective that I am continuing to learn about. I will address the consequences of some of these in the Known and Unknown Issues sections below. Know that I'm working to improve in these areas in my future programming. A few obsolete command-line arguments, comments, and files were removed before pushing to GitHub. 

## 3. Installation

### Required Packages

* [Best Track Real Time](https://github.com/arkweather/BestTrackRT) and required packages (used Python and license files are in the ttrappy folder. The .py files were modified slightly to handle any exceptions. )
* bs4
* cartopy
* matplotlib
* metpy
* netCDF4
* nexradaws
* numpy
* PIL
* psutil
* pyART - For color bars.
* pytz
* requests
* scipy
* xarray - Used in initial prototype code in the post analysis. Could be removed. 

\* The Python code was originally written using Python 3.7.x and WDSS-II v22.3

### WDSS-II

WDSS-II must be obtained separately by contacting the maintainer listed on [wdsii.org](wdssii.org). After setting up WDSS-II on your system, a few configuration files must be changed.

1. Ensure WDSS2/bin is in the system path.
2. Copy WDSS2/w2config/misc/radarinfo.xml to ttrapcfg
3. Increase the queueSize in WDSS2/w2config/misc/notifier. Too small of queue results data being unable to be processed. A size of 5000 was used.
4. Set compression to "false" for the "DataTable" datatype in WDSS2/w2config/misc/dataformat. This will ensure that TTRAP can read the data tables.
5. For the time being, cluster-table configuration files (WDSS2/w2config/algs/clusterTable.xml) have been removed. Separate files are created for echo-top and VIL clusters. TTRAP has options to use w2merger or w2cropconv or to have w2circ threshold the AzShear field by ReflectivityQC. A separate file was created for each elevation angle for each combination of these two options. These files will need to be recreated and placed in a ttrapcfg/clusterCFG folder. 

### General Setup

Once the required packages and WDSS-II are setup, the installation of TTRAP should include cloning the repository into its own directory. Before running runTTRAP.py, a case and configuration file must be created. 

#### Case Files

Case files are CSV files containing information about each case to be processed. A set of test files and files used in the analysis are found in the "case_files" and "case_files_old" folders. Case files to be used should be placed "case_files." The columns are:

> id,storm,year,month,day,time,start_lat,start_lon,stop_lat,stop_lon,istor,F-EF-Rating,class

Where:
* "id" and "storm" identify the case. ID is a subset of storm.
* "year", "month", "day", and "time" are the date and time as integers. Time is in UTC or Zulu. Leading zeros are omitted. 0015z would be entered as "15" in the time column.
* "start" and "stop" "lat" and "lon" are the beginning and endpoints for the tornado's path. For nontornadic cases, these are the same. The analysis is centered around the start point. The stop point is only plotted in figures and not used elsewhere.
* "istor" is 0 (nontornadic) or 1 (tornadic)
* "F-EF-Rating" is the F or EF rating of the tornado. -1 is used for nontornadic cases or tornadic cases with an unknown rating. 
* "class" denotes whether the tornado was included in a tornado warning at its start time (HIT; 1) or not (MISS; 2). 0 is used for nontornadic cases.
* A '#' added to the beginning of a line will result in that case being ignored.

TTRAP will iterate through these cases and process them. 

#### Config Files

Config files for TTRAP are found in ttrapcfg/configs. These include information about where to find various files, weights used in cluster tracking, and options to pass to WDSS-II algorithm. To save space, these options for each are not explained here. A separate README might be made, but for the time being, ignore the first comment in these files. There may a few obsolete options. 

#### Figure Generation Processes

If you opt to use TTRAP to create figures with MATPLOTLIB, it will try to make use of multiple processes to do so. The maximum is set to 14 by default, but smaller machines may wish to use a smaller number. This can be changed at ttrappy/visualize.py line 1975. 

## 4. Usage

TTRAP can be run only in the terminal ("Archive Mode") or from a GUI. Both are launched from runTTRAP.py. 

### Running TTRAP without the GUI

```
python3 runTTRAP.py -A -C ttrapcfg/configs/final_config.xml -c case_files/ALLCASES-1.csv -ln run1
```

This would process the files in ALLCASES-1.csv using the final_config.xml configuration file. "-ln" sets the prefix to the logfiles to "run1" allowing different log names for different runs. Options also exist to skip figure generation or WDSS-II processing.

### Running TTRAP with the GUI

TTRAP can also be run from a GUI. Make sure an X server is running then launch the GUI using.

```
python3 runTTRAP.py -g
```

The resulting GUI will allow you to select a configuration and case file from the dropdown in the upper left. The check boxes can be used to determine if the WDSS-II processing or figure generation is performed. If no data has been processed, the WDSS-II processing will be performed. Processing can be started by clicking "Run Archive."  

In the upper-right of the GUI, generated PNG files can be viewed by selecting the storm, case, then product name. All PNG files under that name are loaded in chronological order and can be navigated using the left and right arrow keys. It may take a moment to load the images after initially selecting the dropdown menu.

## 5. Known Issues

1. The output to the TTRAP and WDSS-II logfiles is quite verbose and can take up quite a bit of storage.
2. TTRAP is not fast.
3. TTRAP has been observed to slow down as cases are processed. The working theory is that the logfile must be opened each time it's used. As the logfile grows, it takes longer to read in. The logging utility was not used as it caused issues with the queues used to run the WDSS-II programs. I recommend running 100 cases at a time if possible. 
4. If a radar is missing data, it may cause an exception to occur.
5. TTRAP was developed before some of the current features of shutil were implemented. It makes use of running commands such as 'cp' on the system which is not best practice. 

## 6. Unknown Issues

1. This code has only been run on its development servers. It has not been tested on other machines.
2. Some very light cleanup was performed prior to pushing to GitHub (although you'll still find some commented-out code around). Everything removed should have been unused, but let us know if anything seems to be missing. Note one correction was made to an incorrect variable name. See Output_Data.MD for details. 
3. Once the methodology was nailed down, further testing of the code using other scenarios did not occur. Changing certain configuration settings may have unintended effects.

## 7. Analysis For Spotts (2023)

### Case Files

The cases used in Spotts (2023) can be found in ALLCASES.csv. Some cases encountered known issue #4 and were removed from the analysis. The resulting cases are split between ALLCASES-1.csv and ALLCASES-2.csv. The removed cases can be found in Removed.csv. 

### Configuration File

The configuration file used in the analysis is final_config.xml.

### Manual Vrot Comparison

The manual_vrot_comparison folder contains the data and code for comparing the Harvey (2017) manual analysis (Nowotarski et al. (2021)) and the estimated Vrot. The TTRAP data can be found in runs/AH2017.HGX-8 while the manual analysis data is found in "truth." An example of running this code is found in "commands.txt"

### Code For TTRAP Analysis

Once TTRAP has been run, the code for creating figures and statistics for the resulting files can be found in the "post_analysis" folder. The "config.csv" file allows you to set the radius used for Vrot estimation, the maximum beam height of of AzShear clusters, whether to time shift tornadic or nontornadic cases by a specific number of seconds or relative to the maximum, whether to include a specific range of time bins, which results to generate, the minimum number of samples needed in True Skill Score (TSS) calculations, and whether to include the extra criteria. 

The runAnalysis.csh and runSkills.csh scripts can be run (in that order) to produce the results. Hypo 1-5 were generated using older code. That code was copied and updated for the inclusion of multirange. Data from the Spotts (2023) analysis can be found in post_analysis/runs/Final_Run_4. 


## 8. Contact

If you use this code or data within, have questions regarding this code, or need to report an issue, please contact the owner of this repository or Dr. Christopher Nowotarski (cjnowotarski@tamu.edu).

## 9. License, Citation, and References

### License

The code in this repository is released under the MIT license although we still ask you contact us when using the code (see section 8 above). Note that WDSS-II is licensed separately is not covered under the license and the license file for Best Track Real Time is included in the ttrappy folder. 

### Citation

If you use this code or data within for further analysis, please cite

	Spotts, J., 2023: Automatically derived radar attributes of tropical cyclone tornadoes from 2013-2020. M.S. thesis, Department of Atmospheric Sciences, Texas A&M University, 76 pp.


### Other References

	Nowotarski, C. J., J. Spotts, R. Edwards, S. Overpeck, and G. R. Woodall, 2021: Tornadoes in Hurricane Harvey. Wea. Forecasting, 36, 1589–1609, https://doi.org/10.1175/WAF-D-20-0196.1.