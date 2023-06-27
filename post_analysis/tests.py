#Specification of which combination of variables evaluated for warning performance

import os
import math
import copy

centralBin = [-2] #The time bin to do the evaluation on. Enter as a list.
evaluationFolder = 'warning_evaluation' #Folder the evaluation results will stored in
updateCentralBin = True #Automatically update the central bin based on the best average 0.5 Vrot valid TSS
useSameThreshold = False #Use only the best thrsholds for the centralBin. If false, will raise an exception if the previous bin raises a KeyError

#Create that folder
try:
    os.mkdir(evaluationFolder)
except FileExistsError:
    pass
    
    
outputData = os.path.join(evaluationFolder, str(centralBin)+'.csv') #CSV to put the evaulation results in

#This is a list of lists where each list contains the evaluation criteria
#Current options are 0.5, 0.9, 1.3, 1.45, 1.8, 2.4, ET_90thet, ET_maxet, VIL_avgvil, VIL_maxvil
#The elevation angles are tested using the estimated Vrot
#testListTilts are the elevation angles to be tested. All tilts below a given elevation angle must be included for that 
#tilt to be tested (e.g., if 0.5 and 0.9 are in the list, 0.9 can't be tested alone)/
testListTilts = ['0.5', '0.9', '1.3', '1.8', '2.4'] #Change this line


testListTilts = sorted(list(map(str, testListTilts)))

#Other items to add that aren't tilts to be tested 
testListExtras = ['VIL_maxvil'] #Change this line


testLists = []
for n in range(len(testListTilts)):
    testLists.append(testListTilts[0:n+1])
    
#Once the tilts are created go through and add the combinations of the extras
startingTestLists = copy.deepcopy(testLists)
for test in startingTestLists:
    
    numExtras = len(testListExtras)
    for n in range(numExtras):
        
        for a in range(numExtras):
            toAppend = copy.deepcopy(test)

            for item in testListExtras[n:a+1]:
                toAppend.append(item)
             
            if a >= n: 
                testLists.append(toAppend)
        

    
    
print('Created test lists', testLists)