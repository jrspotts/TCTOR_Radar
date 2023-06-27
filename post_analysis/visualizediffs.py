#Holds functions and data for visualizing the differences


import stats
import math
import matplotlib.pyplot as plt
import os
import numpy as np
from scipy import stats as scistat
from scipy import optimize

def createFigures(groups, plotTypes, axis, titles):

    """
        Creates different figures depending on what group it is. The group is the key to the groups dictionary.

    """
    
    for groupKey in list(groups.keys()):
    
        data = groups[groupKey]
        
        for plotKey,plotValue in zip(list(plotTypes[groupKey].keys()), list(plotTypes[groupKey].values())):
            print(plotKey, plotValue)
            if plotValue == 'scatter':
                try:
                    makeScatterPlot(data[plotKey], axis[groupKey][plotKey], titles[groupKey][plotKey])
                except KeyError as e:
                    print('KeyError while making a scatterplot', str(e))
            if plotValue == 'scatterradius':

                try:
                    for radius in list(data[plotKey].keys()):
                        makeScatterPlotRadius(data[plotKey][radius], axis[groupKey][plotKey], titles[groupKey][plotKey], radius)
                except KeyError as e:
                    print('KeyError while making scatterplotradius', str(e))
                    
            if plotValue == 'histogram':
                try:
                    makeHistogram(data[plotKey], axis[groupKey][plotKey], titles[groupKey][plotKey])
                except KeyError as e:
                    print('KeyError while making histogram', str(e))
            if plotValue == 'histogramardius':
                try:
                    for radius in list(data[plotKey].keys()):
                        makeHistogramRadius(data[plotKey][radius], axis[groupKey][plotKey], titles[groupKey][plotKey], radius)
                except KeyError as e:
                    print('KeyError while making histogramradius', str(e))
                
                
    return


def makeHistogramRadius(data, axis, title, radius):

    """
        Makes a histogram out of data with the axis labeled and the title
    """

    title = title.replace('/', '-')
    
    print('Creating scatter', title, radius, '\nwith', data)
    
    plt.hist(data)
    
    plt.title(title+ 'R='+str(radius), fontsize='x-large')
    plt.xlabel(axis, fontsize='x-large')
    plt.ylabel('Count', fontsize='x-large')
    
    plt.savefig(os.path.join('figures', str(title)+'_'+str(radius)+'.png'), format='png')
    plt.savefig(os.path.join('figures', str(title)+'_'+str(radius)+'.pdf'), format='pdf')
    
    plt.close()
    
    return
    
    
def makeHistogram(data, axis, title):

    """
        Makes a histogram out of data with the axis labeled and the title
    """

    title = title.replace('/', '-')
    
    print('Creating scatter', title, '\nwith', data)
    
    plt.hist(data)
    
    plt.title(title, fontsize='x-large')
    plt.xlabel(axis, fontsize='x-large')
    plt.ylabel('Count', fontsize='x-large')
    
    plt.savefig(os.path.join('figures', str(title)+'.png'), format='png')
    plt.savefig(os.path.join('figures', str(title)+'.pdf'), format='pdf')
    
    plt.close()
    
    return
    
    
def makeScatterPlot(pairs, axis, title):


    xList = []
    yList = []
    
    title = title.replace('/', '-')
    
    for pair in pairs:
        x,y = pair
        xList.append(x)
        yList.append(y)
    
    if not xList or not yList or (len(xList) != len(yList)):
        print('Unable to make scatter plot for', title, len(xList), len(yList))
        return
        
    xAxisLabel, yAxisLabel = axis.split(',')
    print('Creating scatter', title, 'with\n', xList, '\n', yList)
    
    plt.scatter(xList, yList, c=np.array([0.834, 0.366, 0.109]))
    
    if 'E-M Versus Size' in title and len(xList) > 3 and len(yList) > 3 and False:
        
        #Try fitting with a+logb
        bestFit = optimize.curve_fit(lambda t,a,b: a+b*np.log(t), xList, yList)[0]
        
        print('Best Ln Fit', bestFit)
        
        bestFitX = np.linspace(np.min(xList), np.max(xList), 100)
        bestFitY = bestFit[0] + bestFit[1]*np.log(bestFitX)
        fittedYValues = bestFit[0] + bestFit[1]*np.log(xList)
        print('Fitted Y', fittedYValues)
        
        #Plot the best fit line
        plt.plot(bestFitX, bestFitY, c=[0, 0, 0])
        
        rmse = stats.getRMSE(yList, fittedYValues)
        #Reverse the list for the annotation
        bestFit = bestFit[::-1]
    else:
        #Get the best fit estimation
        bestFit = np.polyfit(xList, yList, 1)
        
        bestFitX = np.linspace(np.min(xList), np.max(xList), 100)
        #Plot the best fit line
        plt.plot(bestFitX, np.polyval(bestFit, bestFitX), c=[0, 0, 0])
        
        rmse = stats.getRMSE(yList, np.polyval(bestFit, xList))
    
    
    plt.title(title, fontsize='x-large')
    plt.xlabel(xAxisLabel, fontsize='x-large')
    plt.ylabel(yAxisLabel, fontsize='x-large')
    
    cCoef = 'NA'
    if len(xList) > 1 and len(yList) > 1:
        cCoef = round(scistat.pearsonr(xList, yList)[0], 3)
        
    plt.annotate('N: '+str(len(xList))+'\nSlope: '+str(round(bestFit[0], 3))+'\nIntercept: '+str(round(bestFit[1], 3))+' knots'\
                +"\nr: "+str(cCoef)\
                +'\nRMSE: '+str(round(rmse, 3))+' knots',\
                (0.15, 0.700), xycoords='figure fraction', fontsize='large')
                
    plt.savefig(os.path.join('figures', str(title)+'.png'), format='png')
    plt.savefig(os.path.join('figures', str(title)+'.pdf'), format='pdf')
    
    plt.close()
    
    return
    
def makeScatterPlotRadius(pairs, axis, title, radius):

    xList = []
    yList = []
    
    title = title.replace('/', '-')
    
    for pair in pairs:
        x,y = pair
        xList.append(x)
        yList.append(y)
        
    if not xList or not yList or (len(xList) != len(yList)):
        print('Unable to make scatter plot for', title, radius, len(xList), len(yList))
        return
        
    xAxisLabel, yAxisLabel = axis.split(',')
    print('Creating scatter', title, 'with\n', xList, '\n', yList)
    
    plt.scatter(xList, yList, c=np.array([0.834, 0.366, 0.109]))
    
    #Get the best fit estimation
    bestFit = np.polyfit(xList, yList, 1)
    
    bestFitX = np.linspace(np.min(xList), np.max(xList), 100)
    #Plot the best fit line
    plt.plot(bestFitX, np.polyval(bestFit, bestFitX), c=[0, 0, 0])
    
    rmse = stats.getRMSE(yList, np.polyval(bestFit, xList))
    
    plt.legend(labels=['Linear Best Fit', 'Vrot Pairs'], loc=4)
    
    plt.title(title+' R='+str(radius)+' m', fontsize='x-large')
    plt.xlabel(xAxisLabel, fontsize='x-large')
    plt.ylabel(yAxisLabel, fontsize='x-large')
    
    cCoef = 'NA'
    if len(xList) > 1 and len(yList) > 1:
        cCoef = round(scistat.pearsonr(xList, yList)[0], 3)
        
    #plt.annotate('Assumed Radius = '+str(radius)+'m', (0.15, 0.83), xycoords='figure fraction', fontsize='large')
    plt.annotate('N: '+str(len(xList))+'\nSlope: '+str(round(bestFit[0], 3))+'\nIntercept: '+str(round(bestFit[1], 3))+' knots'\
                +"\nr: "+str(cCoef)\
                +'\nRMSE: '+str(round(rmse, 3))+' knots',\
                (0.15, 0.700), xycoords='figure fraction', fontsize='large')
                
    plt.savefig(os.path.join('figures', str(title)+'_'+str(radius)+'.png'), format='png')
    plt.savefig(os.path.join('figures', str(title)+'_'+str(radius)+'.pdf'), format='pdf')
    
    plt.close()
    
    return
    
def makeScatterPlotCorrected(xList, yList, title):

    
    title = title.replace('/', '-')
    

    if not xList or not yList or (len(xList) != len(yList)):
        print('Unable to make scatter plot for', title, len(xList), len(yList))
        return
        
   
    print('Creating scatter', title, 'with\n', xList, '\n', yList)
    
    plt.scatter(xList, yList, c=np.array([0.834, 0.366, 0.109]))
    
    #Get the best fit estimation
    bestFit = np.polyfit(xList, yList, 1)
    
    bestFitX = np.linspace(np.min(xList), np.max(xList), 100)
    #Plot the best fit line
    plt.plot(bestFitX, np.polyval(bestFit, bestFitX), c=[0, 0, 0])
    
    rmse = stats.getRMSE(yList, np.polyval(bestFit, xList))
    
    plt.legend(labels=[ 'Linear Best Fit', 'Vrot Pairs'], loc=4)
    
    plt.title(title, fontsize='x-large')
    plt.xlabel('Manual Vrot (kts)', fontsize='x-large')
    plt.ylabel('Estimated Area Vrot (kts)', fontsize='x-large')
    
    cCoef = 'NA'
    if len(xList) > 1 and len(yList) > 1:
        cCoef = round(scistat.pearsonr(xList, yList)[0], 3)
        
    #plt.annotate('Assumed Radius = '+str(radius)+'m', (0.15, 0.83), xycoords='figure fraction', fontsize='large')
    plt.annotate('N: '+str(len(xList))+'\nSlope: '+str(round(bestFit[0], 3))+'\nIntercept: '+str(round(bestFit[1], 3))+' knots'\
                +"\nr: "+str(cCoef)\
                +'\nRMSE: '+str(round(rmse, 3))+' knots',\
                (0.15, 0.700), xycoords='figure fraction', fontsize='large')
                
    plt.savefig(os.path.join('figures', str(title)+'.png'), format='png')
    plt.savefig(os.path.join('figures', str(title)+'.pdf'), format='pdf')
    
    plt.close()
    
    return    