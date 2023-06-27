#Calculates the warning performance for each case based on input thresholds for AzShear or echo tops


import argparse
import dataloader as dl
import math
import skillsconfig
import multirange as mr
import config
import skillcalcs as sc
import sorting
import os
import coordinator as coord
import stats2

def main():

    #Get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-sc', '--skillsconfig', help='Specify the skills config file to use. Default is skill_config.csv')
    parser.add_argument('-t', '--tiltlist', help='Specify the tilts (spearated by commas) to check for use.\n\
                                                 Default 0.5, 0.9, 1.3, 1.45, 1.8, and 2.4')
    parser.add_argument('-s', '--storm', help='Folder containing the cases with the _prelim.csv files')
    parser.add_argument('-c', '--config', help='Specify the config file to use. Default is config.csv')
    args = parser.parse_args()
    

    try:
        os.mkdir('figures/multirange')
    except FileExistsError:
        pass
        
    #Configure arguments
    if not args.storm:
        print('Please define data set using -s or --storm')
        sys.exit()
        
    skillsConfigFile = 'skill_config.csv'
    if args.skillsconfig:
        skillsConfigFile = args.skillsconfig
    tiltList = ['0.5', '0.9', '1.3', '1.45', '1.8', '2.4']
    if args.tiltlist:
        tiltList = sorted(args.tiltlist.split(','))
    
    configFile = 'config.csv'
    if args.config:
        configFile = args.config

    print('Skills config file: ', skillsConfigFile, '\ntilt list: ', tiltList, '\ndataset: ', args.storm, sep='')
    
    #Load config file
    skillsCFG = skillsconfig.Config(skillsConfigFile, tiltList)
    print('Loaded ', skillsConfigFile, '\n', skillsCFG, sep='')
    
    cfg = config.Config(configFile)
    print('Loaded', configFile, '\n', cfg, sep='')
    
    #Load thresholds
    bestThresholdFiles = os.listdir('best_thresholds')
    bestThresholds = {}
    for thresholdFile in sorted(bestThresholdFiles):
        currentBin = str(thresholdFile.split('_')[1].split('.')[0])
        bestThresholds[currentBin] = mr.BestThresholds(currentBin, cfg.bestthreshfilebase, cfg.minTSSSamples)
        bestThresholds[currentBin].readFromCSV()
    
    stormFolder = args.storm
    
    autoObjects = dl.getAutoData(stormFolder, tiltList, cfg.radius)
    
    torObjects, nonTorObjects = sorting.sortTorNoTor(autoObjects)
    
    realWarningStats, realWarningEFStats = stats2.calculateRealStats(nonTorObjects, torObjects, tiltList, cfg)
    
    if cfg.shiftNonTor:
        print('Time shifting NON TOR objects')
        nonTorObjects = coord.timeShiftObjects(nonTorObjects, tiltList, cfg.nontorShiftAmount, cfg)
        
    if cfg.shiftTor:
        print('Time shifting TOR objects')
        torObjects = coord.timeShiftObjects(torObjects, tiltList, cfg.torShiftAmount, cfg)
    
    sc.calcWarnings(bestThresholds, nonTorObjects, torObjects, realWarningStats, tiltList, cfg, skillsCFG)
    
    
    return


main()