#Primary Script for the TCTOR Radar Analaysis Program (TTRAP)

from ttrapcfg import config
from ttrappy.master import Master
import argparse as agp        
import sys
        
def main():

    
    #Get command line arguments 
    parser = agp.ArgumentParser(description="Derive storm attributes for TCs from radar data")
    parser.add_argument("-C", "--config", help="Specify the .xml configuration file")
    parser.add_argument("-I", "--ID", help="Override the case ID to be used if not defined elsewhere")
    parser.add_argument("-c", "--case", help="Case file .csv to create cases from (Overrides config file).")
    parser.add_argument("-A", "--archive-mode", help="Run in archive mode (as opposed to starting with the GUI).", action="store_true")
    parser.add_argument("-t", "--ttrap", help="Run only TTRAP (no WDSSII). Turns off removing logs", action="store_true")
    parser.add_argument("-g", "--gui", help="Run in the TTRAP tkinter GUI", action="store_true")
    parser.add_argument("-s", "--score", help="(Currently Disabled) Score clusters", action="store_true")
    parser.add_argument('-p', '--prefix', help='Prefix to add to output png files')
    parser.add_argument("-nc", "--nocomb", action="store_true", help="(Currently Disabled) Disable combining data from all cases at the end. Useful if processing data in parallel")
    parser.add_argument('-ln', '--logname', help='The prefix for the error and log files. For example, a value of first_run would create the files first_run_log.txt and first_run_error.txt. Default is ttrap_log.txt and ttrap_error.txt')
    parser.add_argument('-sf', '--skipfigures', help='Skip the process of making figures', action='store_true')
    args = parser.parse_args()
    
    if not args.archive_mode and not args.gui:
        print('Warning!!! Must specify -A , -g, or --help')
        exit(10)
    
    #Define variables holding arguments
    configFile = 'ttrapcfg/configs/config.xml'
    
    if args.config:
        configFile = args.config
	
    #Load configuration
    cfg = None
    if args.logname:
        logFile = args.logname+'_log.txt'
        errorFile = args.logname+'_error.txt'
        cfg = config.Config(configFile, logFile, errorFile, args.logname)
    else:
        cfg = config.Config(configFile, 'ttrap_log.txt', 'ttrap_error.txt', 'ttrap')
    
        
    if args.ID:
        cfg.log("Overriding case ID "+args.ID)
        cfg.setOverrideID = args.ID
        
        
    if args.case:
        cfg.log("Setting case file "+args.case)
        cfg.setCaseFile(args.case)

        
    if args.ttrap:
        cfg.setTTRAP(args.ttrap)
        
    if args.score:
        cfg.score=True
        
    if args.prefix:
        cfg.figurePrefix = args.prefix
        
    if args.nocomb:
        cfg.combine = False
        
    if args.skipfigures:
        cfg.makeFigures = False
    
    mstr = Master(cfg)
    
    if args.gui:
        cfg.log("Configuration Loaded")
        cfg.log(vars(cfg))
        
        mstr.startGui()
     
    elif args.archive_mode:
        cfg.log("Configuration Loaded")
        cfg.log(vars(cfg))
        
        mstr.processArchivedCases()
    
            
    
    return

if __name__ == "__main__":
    main()
