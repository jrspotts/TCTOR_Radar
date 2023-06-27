#This program checks for duplicate of cases by ID and TC then creates a CSV of the results

import argparse as agp


def main():

    arg = agp.ArgumentParser(description="Check for duplicate cases by ID and TC")
    arg.add_argument("-i", "--input", help="The case file to check")
    args = arg.parse_args()
    
    allCases = []
    duplicateCases = []
    
    with open(args.input, 'r') as fi:
    
        header = ''
        isHeader = True
        for line in fi:
            ID = ''
            storm = ''
            if not isHeader:
                lineList = line.lstrip('#').rstrip('\n').split(',')
                ID = lineList[header.index('id')]
                storm = lineList[header.index('storm')]
            else:
                header = line.lstrip('#').rstrip('\n').split(',')
                isHeader = False
                
            idTuple = (ID, storm)
            
            if idTuple in allCases:
                if idTuple not in duplicateCases:
                    print('Found duplicate case', idTuple)
                    duplicateCases.append(idTuple)
                    
            allCases.append(idTuple)
    
    with open('duplicates.csv', 'w') as fi2:
        
        fi2.write('id,storm,count\n')
        
        for idTuple2 in duplicateCases:
        
            fi2.write(str(idTuple2[0])+','+str(idTuple2[1])+','+str(allCases.count(idTuple2))+'\n')
            
            
    if not duplicateCases:
        print('No duplicate cases! :)')
        
    return
    
    
    
main()
            