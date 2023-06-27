#Class for containing the NONTOR entries
#Author: Justin Spotts 4-9-2022

import os

def getNonTors(warningFolder):

    #Loop through each NON TOR entry, retrieve the NON TOR objects, and save the TC names
    warningFiles = sorted(os.listdir(warningFolder))
    nonTorByTC = {}
    tcShortNames = []
    tcLongNames = []
    duplicateCount = 0
    nonTorCount = 0
    for fileName in sorted(warningFiles):
    
        accumulatedIDs = []
        
        #Make sure we're loading a CSV file
        if fileName.endswith('.csv'):
            pass
        else:
            #Skip to the next file
            continue
        
        #Since we're dealing with the atlantic, All TCs will start with A
        fileNameList = fileName.split('_')
        print(fileName, 'becomes', fileNameList)
        tcShortName = 'A'+fileNameList[0][0].upper()+fileNameList[1]
        if tcShortName in tcShortNames:
            tcShortName = tcShortName+'-'+str(tcShortNames.count(tcShortName)+1)
        tcLongName = fileNameList[0]+'-'+fileNameList[1][2:len(fileNameList[1])]
        print('Retrieveing warnings from', tcShortName, tcLongName)
        tcShortNames.append(tcShortName)
        tcLongNames.append(tcLongName)
        
        currentFilePath = os.path.join(warningFolder, fileName)
        currentHeader = ''
        isHeader = True
        
        nonTorByTC[tcLongName] = []
        with open(currentFilePath, 'r') as fi:
            
            for line in fi:
                if not isHeader:
                    entryList = line.lstrip('#').rstrip('\n').split(',')
                    currentNonTor = NonTOREntry(entryList, currentHeader, tcShortName)
                    if currentNonTor.isValid:
                            nonTorByTC[tcLongName].append(currentNonTor)
                            accumulatedIDs.append(currentNonTor.ID)
                            nonTorCount += 1
                            
                else:
                    currentHeader = line.lstrip('#').rstrip('\n').split(',')
                    isHeader = False
                    
    print('The duplicate count for all TCs was', duplicateCount)
    
    return nonTorByTC, tcShortNames, tcLongNames, nonTorCount
                    
class NonTOREntry:


    def __init__(self, entryList, entryHeader, tcShortName):
    
    
        try:
            self.ID = entryList[entryHeader.index('CELL IDS')]
        except ValueError:
            self.ID = entryList[entryHeader.index('CELL ID')]
        
        # #Do a check on the ID to make sure it's a nontor by starting with NT or HNT
        # if self.ID.startswith('NT') or self.ID.startswith('HNT'):
            # pass
        # else:
            # print('Not a nontor')
            # self.isValid = False
            # return
        
        try:
            self.year = int(entryList[entryHeader.index('Year (UTC)')])
        except ValueError:
            try:
                self.year = int(entryList[entryHeader.index('Year')])
            except ValueError:
                self.isValid = False
                return
            
        self.monthUTC = int(entryList[entryHeader.index('Month')])
        self.dayUTC = int(entryList[entryHeader.index('Day')])
        
        fullTime = entryList[entryHeader.index('Time (UTC)')]
        self.fullTime = fullTime
        
        if len(fullTime) == 4:
            self.hour = int(fullTime[0:2])
            self.minute = int(fullTime[2:4])
        elif len(fullTime) == 3:
            self.hour = int(fullTime[0])
            self.minute = int(fullTime[1:3])
        elif len(fullTime) < 3:
            self.hour = 0
            self.minute = int(fullTime)
        else:
            print('Something weird happened here')
            self.isValid = False
            return
            
        self.latitude = float(entryList[entryHeader.index('Latitude')])
        self.longitude = float(entryList[entryHeader.index('Longitude')])
        
        self.cwa = entryList[entryHeader.index('CWA')]
        
        #self.warningNumber = int(entryList[entryHeader.index('Tor Warning #')])
        
        self.tcShortName = tcShortName
        
        self.isValid = True
        
        print('Loaded', vars(self))
        return
        
    def writeInputFormat(self):
        inputFormatList = [self.ID, self.tcShortName, self.year, self.monthUTC, self.dayUTC, self.fullTime, self.latitude, self.longitude, self.latitude, self.longitude, 0, -1, 0]
        
        return ','.join(map(str, inputFormatList))+'\n'
        