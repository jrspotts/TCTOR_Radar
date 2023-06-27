#This program loops through every cases and compiles the final analysis and statistics of each case.

import dataloader as dl
import stats as st
import argparse as arg
import os
import config
import coordinator as coord
import grapher
import sorting
import stats2

def main():

    parser = arg.ArgumentParser(description="Compiles statistics and creates figures for TTRAPpy output")
    parser.add_argument("-s", "--storms", help="Path to folder containing all of the TCs and cases to loop through")
    parser.add_argument("-t", "--tilts", help='The list of tilts to be used separated by spaces "0.5 0.9 1.3/1.45 etc." The default is "0.5 0.9 1.3/1.45 1.8 2.4"')
    parser.add_argument("-C", "--config", help='Path to the configuration .csv file. Default is config.csv')
    parser.add_argument("-sd", "--standarddev", help='Maximum standard deviation for y-axis ranges. Default is to not apply.')
    
    args = parser.parse_args()
    
    #Rest the errors log
    errorFi = open('errors.txt', 'w')
    errorFi.close()
    
    if not args.storms:
        print('Please provide the path to the storms folder with the -s argument')
        exit(1)
    if args.tilts:
        tiltList = args.tilts.split(' ')
        print('Using tilt list', tiltList)
    else:
        tiltList = ['0.5', '0.9', '1.3', '1.45', '1.8', '2.4']
        print('No tilt list given. Using default', tiltList)
    if args.config:
        configFile = args.config
        print('Using config file', configFile)
    else:
        configFile = 'config.csv'
        print('Using default config file', configFile)
        
    
        
    #Make necessary output directories if needed
    try:
        os.mkdir('figures')
    except FileExistsError:
        pass
    try:
        os.mkdir('figures/h1')
    except FileExistsError:
        pass
    try:
        os.mkdir('figures/h2')
    except FileExistsError:
        pass
        
    try:
        os.mkdir('figures/h3')
    except FileExistsError:
        pass
        
    try:
        os.mkdir('figures/h4')
    except FileExistsError:
        pass
        
    try:
        os.mkdir('figures/h5')
    except FileExistsError:
        pass
        
    try:
        os.mkdir('figures/multirange')
    except FileExistsError:
        pass
        
    try:
        os.mkdir('stats')
    except FileExistsError:
        pass
    
    #Load the configuration
    cfg = config.Config(configFile)
    
    if args.standarddev:
        cfg.SD = float(args.standarddev)
        
    if cfg.shiftNonTor:
        print('Time Shifting NON TOR enabled!!!', cfg.nontorShiftAmount)
    if cfg.shiftTor:
        print('Time Shifting TOR enabled!!!', cfg.torShiftAmount)
    if cfg.prunebins:
        print('Bin limits enabled!!!', cfg.minbin, cfg.maxbin)
        
    stormFolder = args.storms

    autoObjects = dl.getAutoData(stormFolder, tiltList, cfg.radius)
    
    torObjects, nonTorObjects = sorting.sortTorNoTor(autoObjects)
    
    realWarningStats, realWarningEFStats = stats2.calculateRealStats(nonTorObjects, torObjects, tiltList, cfg)
    
    #Before the main analysis, run the other analysis using time shifts only with the N21-like criteria
    binnedData, caseCounts, negAzShearCounts, tdsCountDict  = coord.getSortedData(autoObjects, tiltList, cfg)
    
    #Run the analysis on the set with not potential-cluster limitation
    axisRanges = coord.createAxisRanges([binnedData['nontor3'], binnedData['alltor3'], binnedData['tds3'], binnedData['notds3']], tiltList, sorting.generalAliases, cfg)
    print(vars(axisRanges))
    
    grapher.beginAnalysis(binnedData['nontor3'], binnedData['alltor3'], binnedData['tds3'], binnedData['notds3'], cfg, realWarningStats, realWarningEFStats, axRanges=axisRanges, potentialClusters=str(cfg.potentialclusters))
    
    #Do the H2 Z-test separately
    grapher.doH2ZTest(tdsCountDict)
    
    return

if __name__ == '__main__':
    main()
    print('Run Analysis Complete!!!')