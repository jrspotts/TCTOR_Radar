#For a given TC CSV. This program determines which period has the most tornaod warnings. 

import argparse as arg
import nontorentry as nte
import os
import math
from datetime import datetime as dt
from datetime import timedelta as td



def main():

    parser = arg.ArgumentParser(description="Calculates which period contains the maximum number of warning events for a TC")
    parser.add_argument('-w', '--warningfolder', help='The folder containing the CSV of the TC warning. Recommend putting just 1 in the warning folder.')
    parser.add_argument('-p', '--period', help='Number of minutes to search over')
    
    args = parser.parse_args()
    
    nonTorByTC, tcShortNames, tcLongNames, nonTorCount = nte.getNonTors(args.warningfolder)
    
    for TC in list(nonTorByTC.keys()):
    
        maxDensity = 0
        maxPeriodStart = None
        maxPeriodEnd = None
        
        for currentEvent in nonTorByTC[TC]:
            eventsInPeriod = 0
            currentDT = dt(year=currentEvent.year, month=currentEvent.monthUTC, day=currentEvent.dayUTC, hour=currentEvent.hour, minute=currentEvent.minute)
            periodEnd = currentDT + td(minutes=int(args.period))
            
            for event in nonTorByTC[TC]:
            
                eventDT = dt(year=event.year, month=event.monthUTC, day=event.dayUTC, hour=event.hour, minute=event.minute)
                
                if eventDT >= currentDT and eventDT <= periodEnd:
                    eventsInPeriod += 1
                    
                    
            print(currentDT, periodEnd, eventsInPeriod)
            
            if eventsInPeriod > maxDensity:
                maxDensity = eventsInPeriod
                maxPeriodStart = currentDT
                maxPeriodEnd = periodEnd
                
                
        print('-------------------------------------------------------------')
        print('The max density period for TC', TC, 'was from', maxPeriodStart, 'to', maxPeriodEnd, 'with', maxDensity, 'events')
        print('\n\n-----------------------------------------------------------')
            
            




main()
