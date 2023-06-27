#This is a quick script that counts skipped cases there are in all of the files in a folder


import os


def main():

    found = False
    while not found:
        folderName = input('What folder shall we search?: ')
        
        try:
            files = [os.path.join(folderName, x) for x in os.listdir(folderName) if x.endswith('skippedcases.csv')]
        except FileNotFoundError:
            print(folderName, 'not found. Try again')
            continue
            
            
        found = True
        break
    
    print('Found files', files)
    
    skippedCount = 0
    
    for currentFi in files:
    
        with open(currentFi, 'r') as fi:
            print('Currently checking', currentFi)
            
            header = ''
            isHeader = True
            
            for line in fi:
                
                if not isHeader:
                    lineList = line.lstrip('#').rstrip('\n').split(',')
                    skippedCount += 1
                else:
                    header = line.lstrip('#').rstrip('\n').split(',')
                    isHeader = False
                    
                    
                    
    print('Out of', len(files), 'files there were', skippedCount, 'skipped cases.')



main()