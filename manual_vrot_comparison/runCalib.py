#Calibration script comparing ttrappy data to a manual analysis


import argparse as arg
import dataloader as dl
import stats
import visualizediffs as viz
import os
import numpy as np

def main():

    parser = arg.ArgumentParser(description="Used to compare ttrappy with a manual analysis")
    parser.add_argument("-s", "--storms", help="The storms folder containing the output data from ttrappy")
    parser.add_argument("-rb", "--rangebins", help='The ranges in km to determine where the cutoffs are for the different range bins separated by spaces (e.g., "73.5 120" will divide cases into\
                                              <73.5 km, 73.5-120 km, and >= 120 km). The value is included in the new bin')
    parser.add_argument("-t", "--tilts", help='The list of tilts to be used separated by spaces "0.5 0.9 1.3/1.45 etc." The default is "0.5 0.9 1.3/1.45 1.8 2.4"')
    #parser.add_argument("-c", "--cyclonic", help="Use this flag to indicate that only cyclonic (positve) AzShear should be compared")
    parser.add_argument("-tb", "--tiltbins", help="The same concept as -rb, but for tilts. A value of 1.8 wit the default list would create two bins: <1.8 deg and 1.8 and 2.4 deg")
    parser.add_argument("-m", "--manual", help="The CSV file representing the manual analysis.")
    parser.add_argument("-sf", "--skipfile", help='The CSV file with the TC/cases to skipp. Use "all" next to a TC to skip the entire TC. The columns should be TC,case')
    parser.add_argument("-sr", "--startradius", help="The lowest radius in meters to estimate vrot")
    parser.add_argument("-mr", "--maxradius", help="The maximum radius in meters used to estimate vrot")
    parser.add_argument("-rs", "--radiusstep", help="How much to increment the radius used to estimate vrot from startradius to maxradius")
    
    args = parser.parse_args()
    
    if args.tilts:
        tiltList = args.tilts.split(' ')
    else:
        tiltList = ['0.5', '0.9', '1.3', '1.45', '1.8', '2.4']
        print('No tilt list provided, going with default', tiltList)
    
    if not args.manual:
        print('Please provide the manual file with -m')
        exit(1)
    if not args.storms:
        print('Please provide the storms folder with -s')
        exit(2)
    if not args.skipfile:
        print('Please provide a CSV of the cases with skipped variables and which variables those are.\n',\
                'You only need the header TC,case,0.5,0.9,1.3/1.45,1.8,2.4 and don\'t need to actually provide any cases. Just do it please.')
        exit(3)
    if not args.startradius or not args.maxradius or not args.radiusstep:
        print('Please provide radius arguments for vrot information')
        exit(4)
    if float(args.startradius) >= float(args.maxradius):
        print('Start radius is greater than max radius. Please try again')
        exit(5)
        
        
                
    
    try:
        os.mkdir('figures')
    except FileExistsError:
        pass
    
    #Create list of radii for vrot estimation
    radii = [float(args.startradius) + (r*float(args.radiusstep)) for r in range(int((float(args.maxradius)-float(args.startradius))/float(args.radiusstep))+1)]
    print('Create radii', radii)
    
    manualFile = args.manual
    stormFolder = args.storms
    
    autoObjects, truthObjects = dl.getData(manualFile, stormFolder, tiltList, radii)
    #print('rawAuto----', autoObjects)
    filteredAutoObjects = dl.filterAutoObjects(autoObjects)
    
    
        
    #print('----', truthObjects)
    
    print(len(list(filteredAutoObjects[list(filteredAutoObjects.keys())[0]].keys())),\
            len(list(truthObjects[list(truthObjects.keys())[0]].keys())))
            
            
    #Create the list of boundaires
    tiltBoundaries = []
    rangeBoundaries = []
    
    if args.tiltbins:
        tiltBoundaries = list(map(float, args.tiltbins.split(' ')))
    if args.rangebins:
        rangeBoundaries = list(map(float, args.rangebins.split(' ')))
    
    print('Tilt Boundaries', tiltBoundaries)
    print('Range Boundaries', rangeBoundaries)
    binnedAutoObjects, tiltBins, rangeBins = dl.assignTiltRangeBins(filteredAutoObjects, rangeBoundaries, tiltBoundaries)
    
    skipObjects, skipCount = dl.getSkipObjects(args.skipfile)
    print('Skip Count ---', skipCount)
    differenceObjects = dl.createDiffObjects(truthObjects, binnedAutoObjects, skipObjects, radii)
    
    nDiff = 0
    for TC in list(differenceObjects.keys()):
        
        for diff in list(differenceObjects[TC].values()):
            
            if diff:
                if diff[0] and len(diff) >= 1:
                    nDiff += 1
                
                
    print('Number of difference objects', nDiff)
    
    
    for TC in list(filteredAutoObjects.keys()):

        #These are not in order so we'll need to do a nested loop
        for truth in list(truthObjects[TC].values()):
            fullMatch = False
            if truth:
                print('Truth', str(vars(truth)))
                for filteredAuto in list(filteredAutoObjects[TC].values()):
                    if len(filteredAuto) > 1:
                        print('####################################')
                    if len(filteredAuto) == 0:
                        print('Length of filtered auto is 0')
                        continue
                        
                    if filteredAuto[0]:
                        if truth.TC == filteredAuto[0].TC and truth.case == filteredAuto[0].case:
                            print('Auto', str(vars(filteredAuto[0])))
                            for azTilt in list(filteredAuto[0].azShear.values()):
                                print('Tilt', azTilt.tilt, str(vars(azTilt)))
                                
                            for skip in list(skipObjects.values()):
                            
                                if skip:
                                    if skip.TC == truth.TC and skip.case == truth.case:
                                        print('SKIP', str(vars(skip)))
                                        
                            for diff in list(differenceObjects[TC].values()):
                                if len(diff) > 1:
                                    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                                if len(diff) == 0:
                                    #print('Diff length of 0')
                                    continue
                                    
                                if diff[0]:
                                    if diff[0].TC == truth.TC and diff[0].case == truth.case:
                                        print('Difference', str(vars(diff[0])))
                                        fullMatch = True    
                                        break
                            
                    if fullMatch:
                        break
                

                print('----------------------------------------------------------')
       

    #print('Made difference objects', differenceObjects)
    
    #Get the various groups ready to send to make the figures and statistics
    
    groups = {}
    plotTypes = {}
    axis = {}
    titles = {}
    
    #stats.writeDiffs(binnedAutoObjects, truthObjects, differenceObjects)
    
    for rangeBin in list(rangeBins.keys()):
    
        for tilt in sorted(list(tiltBins.keys())):
        
            groups['Vrot '+str(rangeBin)+' '+str(tilt)] = stats.getBinDiff(\
                differenceObjects, tiltList, radii, tiltBin=tiltBins[tilt], rangeBin=rangeBins[rangeBin], type='vrot')
            plotTypes['Vrot '+str(rangeBin)+' '+str(tilt)] = {\
                'azsheardiffs':'histogram',\
                'azshearpairs':'scatter',\
                'sizepairs':'scatter',\
                'potentialclusters':None,\
                'azsheartopdiffs':'histogram',\
                'azshearbotdiffs':'histogram',\
                'azsheartoppairs':'scatter',\
                'azshearbotpairs':'scatter',\
                'azsheartopsizepairs':'scatter',\
                'azshearbotsizepairs':'scatter',\
                'vrotrdiffs':'histogramradius',\
                'vrotrpairs':'scatterradius',\
                'bestradiusvrotpairs':'scatter',\
                'bestradius':'histogram'}
            
            #Axis are axis labels for the plots. Historgram has one unit. Scatter has x,y 
            #e.g., 'Manaual Vrot (kts),Automatic Vrot(kts)' for the x and y axis labels respectively
            
            axis['Vrot '+str(rangeBin)+' '+str(tilt)] = {\
                'azsheardiffs':'A-M V$_{rot}$ (kts)',\
                'azshearpairs':'Manual V$_{rot}$ (kts),Automated Area V$_{rot}$ (kts)',\
                'sizepairs':'Cluster Area (km${^2}$),A-M Area V$_{rot}$ (kts)',\
                'potentialclusters':None,\
                'azsheartopdiffs':'90th Percentile A-M V$_{rot}$ (kts)',\
                'azshearbotdiffs':'10th Percentile A-M V$_{rot}$ (kts)',\
                'azshearbotpairs':'Manual V$_{rot}$ (kts),Automated 10th Percentile Area V$_{rot}$ (kts)',\
                'azsheartoppairs':'Manual V$_{rot}$ (kts),Automated 90th Percentile Area V$_{rot}$ (kts)',\
                'azsheartopsizepairs':'Cluster Area (km${^2}$),90th Percentile A-M Area V$_{rot}$ (kts)',\
                'azshearbotsizepairs':'Cluster Area (km${^2}$),10th Percentile A-M Area V$_{rot}$ (kts)',\
                'vrotrdiffs':'Constant Radius V$_{rot}$ Differences (kts)',\
                'vrotrpairs':'Manual V$_{rot}$ (kts),Automated V$_{rot}$ (kts)',\
                'bestradiusvrotpairs':'Best Radius (m),Automated V$_{rot}$ (kts)',\
                'bestradius':'Best Radius (m)'}
                
            #Titles are what the plot title will be
            
            titles['Vrot '+str(rangeBin)+' '+str(tilt)] = {\
                'azsheardiffs':'Area V$_{rot}$ '+str(rangeBin)+' '+str(tilt)+'$^\circ$ A-M',\
                'azshearpairs':'Area V$_{rot}$ '+str(rangeBin)+' '+str(tilt)+'$^\circ$ vs Manual V$_{rot}$',\
                'sizepairs':'Area V$_{rot}$ '+str(rangeBin)+' '+str(tilt)+'$^\circ$ A-M Versus Size',\
                'potentialclusters':None,\
                'azsheartopdiffs':'90th Area V$_{rot}$ '+str(rangeBin)+' '+str(tilt)+'^$\circ$ A-M',\
                'azshearbotdiffs':'10th Area V$_{rot}$ '+str(rangeBin)+' '+str(tilt)+'$^\circ$ A-M',\
                'azsheartoppairs':'90th Area V$_{rot}$ '+str(rangeBin)+' '+str(tilt)+ '$^\circ$ vs Manual V$_{rot}$',\
                'azshearbotpairs':'10th V$_{rot}$ '+str(rangeBin)+' '+str(tilt)+ '$^\circ$ vs Manual V$_{rot}$',\
                'azsheartopsizepairs':'90th Area V$_{rot}$ '+str(rangeBin)+' '+str(tilt)+'$^\circ$ A-M Versus Size',\
                'azshearbotsizepairs':'10th Area V$_{rot}$ '+str(rangeBin)+' '+str(tilt)+'$^\circ$ A-M Versus Size',\
                'vrotrdiffs':'Automated-Manual '+str(rangeBin)+' '+str(tilt)+'$^\circ$',\
                'vrotrpairs':'Automated Versus Manual V$_{rot}$ '+str(rangeBin)+' '+str(tilt)+'$^\circ$',\
                'bestradiusvrotpairs':'Automated V$_{rot}$ Versus Radius of Least Error '+str(rangeBin)+' '+str(tilt)+'$^\circ$',\
                'bestradius':'Best Radius '+str(rangeBin)+' '+str(tilt)+'$^\circ$'}
                
                
            #Print out the data of each group
            for plotKey in list(groups['Vrot '+str(rangeBin)+' '+str(tilt)].keys()):
            
                print('Vrot '+str(rangeBin)+' '+str(tilt), plotKey, groups['Vrot '+str(rangeBin)+' '+str(tilt)][plotKey])
                
                
    #Now just get by tilt
    repeated = False
    
    for tilt in sorted(tiltList):
    
        if tilt == '1.3' or tilt == '1.45':
            if repeated:
                repeated = False
            
            repeated = True
            tilt = '1.3/1.45'
            
        if tilt != '1.3' and tilt != '1.45':
            repeated = False
            
        groups['Vrot '+str(tilt)] = stats.getBinDiff(differenceObjects, tiltList, radii, selectTilt=tilt, type='vrot')
        
        plotTypes['Vrot '+str(tilt)] = {\
                'azsheardiffs':'histogram',\
                'azshearpairs':'scatter',\
                'sizepairs':'scatter',\
                'potentialclusters':None,\
                'azsheartopdiffs':'histogram',\
                'azshearbotdiffs':'histogram',\
                'azsheartoppairs':'scatter',\
                'azshearbotpairs':'scatter',\
                'azsheartopsizepairs':'scatter',\
                'azshearbotsizepairs':'scatter',\
                'vrotrdiffs':'histogramradius',\
                'vrotrpairs':'scatterradius',\
                'bestradiusvrotpairs':'scatter',\
                'bestradius':'histogram',\
                'vrotdistpairs':'scatterradius',\
                'vrotdisterrorpairs':'scatterradius'}
                
        axis['Vrot '+str(tilt)] = {\
                'azsheardiffs':'A-M V$_{rot}$ (kts)',\
                'azshearpairs':'Manual V$_{rot}$ (kts),Automated Area V$_{rot}$ (kts)',\
                'sizepairs':'Cluster Area (km${^2}$),A-M Area V$_{rot}$ (kts)',\
                'potentialclusters':None,\
                'azsheartopdiffs':'90th Percentile A-M V$_{rot}$ (kts)',\
                'azshearbotdiffs':'10th Percentile A-M V$_{rot}$ (kts)',\
                'azshearbotpairs':'Manual V$_{rot}$ (kts),Automated 10th Percentile Area V$_{rot}$ (kts)',\
                'azsheartoppairs':'Manual V$_{rot}$ (kts),Automated 90th Percentile Area V$_{rot}$ (kts)',\
                'azsheartopsizepairs':'Cluster Area (km${^2}$),90th Percentile A-M Area V$_{rot}$ (kts)',\
                'azshearbotsizepairs':'Cluster Area (km${^2}$),10th Percentile A-M Area V$_{rot}$ (kts)',\
                'vrotrdiffs':'Constant Radius V$_{rot}$ Differences (kts)',\
                'vrotrpairs':'Manual V$_{rot}$ (kts),Automated V$_{rot}$ (kts)',\
                'bestradiusvrotpairs':'Best Radius (m),Automated V$_{rot}$ (kts)',\
                'bestradius':'Best Radius (m)',\
                'vrotdistpairs':'Range (n mi),Automated V$_{rot}$ (kts)',\
                'vrotdisterrorpairs':'Range (n mi),A-M V$_{rot}$ (kts)'}
                
        titles['Vrot '+str(tilt)] = {\
                'azsheardiffs':'Area V$_{rot}$ '+str(tilt)+'$^\circ$ A-M',\
                'azshearpairs':'Area V$_{rot}$ vs Manual V$_{rot}$ '+str(tilt)+'$^\circ$',\
                'sizepairs':'Area V$_{rot}$ '+str(tilt)+'$^\circ$ A-M Versus Size',\
                'potentialclusters':None,\
                'azsheartopdiffs':'90th Area V$_{rot}$ '+str(tilt)+'$^\circ$ A-M',\
                'azshearbotdiffs':'10th Area V$_{rot}$ '+str(tilt)+'$^\circ$ A-M',\
                'azsheartoppairs':'90th Area V$_{rot}$ '+str(tilt)+'$^\circ$ vs Manual V$_{rot}$',\
                'azshearbotpairs':'10th Area V$_{rot}$ '+str(tilt)+'$^\circ$ vs Manual V$_{rot}$',\
                'azsheartopsizepairs':'90th Area V$_{rot}$ '+str(tilt)+'$^\circ$ A-M Versus Size',\
                'azshearbotsizepairs':'10th Area V$_{rot}$ '+str(tilt)+'$^\circ$ A-M Versus Size',\
                'vrotrdiffs':'Automated-Manual V$_{rot}$ '+str(tilt)+'$^\circ$',\
                'vrotrpairs':'Automated Versus Manual V$_{rot}$ '+str(tilt)+'$^\circ$',\
                'bestradiusvrotpairs':'Automated V$_{rot}$ Versus Radius of Least Error '+str(tilt)+'$^\circ$',\
                'bestradius':'Best Radius '+str(tilt)+'$^\circ$',\
                'vrotdistpairs':'Automated V$_{rot}$ with Range '+str(tilt)+'$^\circ$',\
                'vrotdisterrorpairs':'A-M V$_{rot}$ with Range '+str(tilt)+'$^\circ$'}
                
                
                
        for plotKey in list(groups['Vrot '+str(tilt)].keys()):
            
                print('Vrot '+str(tilt), plotKey, groups['Vrot '+str(tilt)][plotKey])
                
                
        #For this next part, we firt a curve to the error by size and apply a correction to the area vrots to see how it looks
        x1List = []
        y1List = []
        
        for x1,y1 in groups['Vrot '+str(tilt)]['sizepairs']:
            x1List.append(x1)
            y1List.append(y1)
        
        if x1List and y1List and (len(x1List) == len(y1List)):
            bestFit = np.polyfit(x1List, y1List, 1)
            
            x2List = []
            y2List = []
            
            n = 0
            
            for x2,y2 in groups['Vrot '+str(tilt)]['azshearpairs']:
                
                correctedVrot = y2 - np.polyval(bestFit, x1List[n])
                print('Corrected', y2, 'by', np.polyval(bestFit, x1List[n]), 'for', correctedVrot, 'with', x1List[n], 'compared with', x2, bestFit)
                x2List.append(x2)
                y2List.append(correctedVrot)
                n += 1
                
            viz.makeScatterPlotCorrected(x2List, y2List, 'Vrot '+str(tilt)+'$^\circ$ Estimated Vrot vs Man Cor')
        else:
            print('Unequal list lengths for correction')
            
    groups['all'] = stats.getBinDiff(\
            differenceObjects, tiltList, radii, type='vrot')
    plotTypes['all'] = {\
        'azsheardiffs':'histogram',\
        'azshearpairs':'scatter',\
        'sizepairs':'scatter',\
        'potentialclusters':None,\
        'azsheartopdiffs':'histogram',\
        'azshearbotdiffs':'histogram',\
        'azsheartoppairs':'scatter',\
        'azshearbotpairs':'scatter',\
        'azsheartopsizepairs':'scatter',\
        'azshearbotsizepairs':'scatter',\
        'vrotrdiffs':'histogramradius',\
        'vrotrpairs':'scatterradius',\
        'bestradiusvrotpairs':'scatter',\
        'bestradius':'histogram',\
        'vrotdistpairs':'scatterradius',\
        'vrotdisterrorpairs':'scatterradius'}
    
    #Axis are axis labels for the plots. Historgram has one unit. Scatter has x,y 
    #e.g., 'Manaual Vrot (kts),Automatic Vrot(kts)' for the x and y axis labels respectively
    
    axis['all'] = {\
        'azsheardiffs':'A-M Vrots (kts)',\
        'azshearpairs':'Manual V$_{rot}$ (kts),Automated Area V$_{rot}$ (kts)',\
        'sizepairs':'Cluster Area (km${^2}$),A-M Area V$_{rot}$ (kts)',\
        'potentialclusters':None,\
        'azsheartopdiffs':'90th Percentile A-M V$_{rot}$ (kts)',\
        'azshearbotdiffs':'10th Percentile A-M V$_{rot}$ (kts)',\
        'azshearbotpairs':'Manual V$_{rot}$ (kts),Automated 10th Percentile Area V$_{rot}$ (kts)',\
        'azsheartoppairs':'Manual V$_{rot}$ (kts),Automated 90th Percentile Area V$_{rot}$ (kts)',\
        'azsheartopsizepairs':'Cluster Area (km${^2}$),90th Percentile A-M Area V$_{rot}$ (kts)',\
        'azshearbotsizepairs':'Cluster Area (km${^2}$),10th Percentile A-M Area V$_{rot}$ (kts)',\
        'vrotrdiffs':'Constant Radius V$_{rot}$ Differences (kts)',\
        'vrotrpairs':'Manual V$_{rot}$ (kts),Automated V$_{rot}$ (kts)',\
        'bestradiusvrotpairs':'Best Radius (m),A V$_{rot}$ (kts)',\
        'bestradius':'Best Radius (m)',\
        'vrotdistpairs':'Range (n mi),Automated V$_{rot}$ (kts)',\
        'vrotdisterrorpairs':'Range (n mi),A-M V$_{rot}$ (kts)'}
        
    #Titles are what the plot title will be
    
    titles['all'] = {\
        'azsheardiffs':'Area V$_{rot}$ All A-M',\
        'azshearpairs':'Area V$_{rot}$ All',\
        'sizepairs':'Area V$_{rot}$ All A-M Versus Size',\
        'potentialclusters':None,\
        'azsheartopdiffs':'90th Area V$_{rot}$ All A-M',\
        'azshearbotdiffs':'10th Area V$_{rot}$ All A-M',\
        'azsheartoppairs':'90th Area V$_{rot}$ All vs Manual V$_{rot}$',\
        'azshearbotpairs':'10th V$_{rot}$ All vs Manual V$_{rot}$',\
        'azsheartopsizepairs':'90th Area V$_{rot}$ All A-M Versus Size',\
        'azshearbotsizepairs':'10th Area V$_{rot}$ All A-M Versus Size',\
        'vrotrdiffs':'Automated-Manual All',\
        'vrotrpairs':'Automated Versus Manual V$_{rot}$ All',\
        'bestradiusvrotpairs':'Automated V$_{rot}$ Versus Radius of Least Error All',\
        'bestradius':'Best Radius All',\
        'vrotdistpairs':'Automated V$_{rot}$ with Range All',\
        'vrotdisterrorpairs':'A-M V$_{rot}$ with Range All'}
        
        
    groups['et'] = stats.getBinDiff(differenceObjects, tiltList, radii, type='et')
    
    plotTypes['et'] = {'etdiff':'histogram', 'et90diff':'histogram'}
    axis['et'] = {'etdiff':'A-M Echo Tops', 'et90diff':'A-M 90th% Echo Tops'}
    titles['et'] = {'etdiff':'Echo-Top Error', 'et90diff':'A-M 90th Percentile Echo-Top Error'}
        
    viz.createFigures(groups, plotTypes, axis, titles, radii)
    
    viz.makeErrorsBoxplots(groups, tiltList)
    
    stats.writeStats(groups)
    
    print('Program finished WHOO!')
    
    return
    
main()