#Holds functions and data for visualizing the differences


import stats
import math
import matplotlib.pyplot as plt
import os
import numpy as np
from scipy import stats as scistat
from scipy import optimize
import matplotlib.transforms as transforms
import matplotlib.ticker as ticker
from decimal import Decimal

def calculateRelativeFrequencies(data, bins, averageN=None):
    """ Returns the relative frequencies of data. The data is split into the individual bins and
        the a list of the relative frequencies and bins is returned.
        
        Arguments:
        data(list) - A list of data values from which to calculate the relative frequencies from.
        bins(list) - The bins for which to calculate the relative frequencies for.
        
        kwargs:
        averageN(int) - The number of bins to average together. If not specified, no averaging occurs.
        
        Returns:
        (tuple) - (relative frequencies, bins)
        
    """
    
    newBins = []
    if averageN:
        for n in range(0, len(bins)-averageN, averageN):
            newBins.append(np.mean(bins[n:n+averageN]))
            
        bins = newBins
        
    totalValues = len(data)
    binnedData = np.zeros_like(bins)
    #Place each data value into a bin
    for point in data:
        binIndex = -1
        binDiff = math.inf
        for count,bin in enumerate(bins):
            currentDiff = abs(point-bin)
            if currentDiff < binDiff:
                binDiff = currentDiff
                binIndex = count
        
        binnedData[binIndex] += 1
        
    relativeFrequencies = [x/totalValues for x in binnedData]
    
    print('Calculated relative frequencies from', data, '\nNew bins', newBins, '\nand relative frequencies of', relativeFrequencies)
    
    return relativeFrequencies, bins
    
def getOrder(num):
    if num == 0:
        return 0
    else:
        num = abs(num)
        
    return math.floor(math.log10(num))
    
def createFigures(groups, plotTypes, axis, titles, radii):

    """
        Creates different figures depending on what group it is. The group is the key to the groups dictionary.

    """
    radiusInc = (max(radii) - min(radii))/len(radii)
    
    for groupKey in list(groups.keys()):
    
        data = groups[groupKey]
        
        for plotKey,plotValue in zip(list(plotTypes[groupKey].keys()), list(plotTypes[groupKey].values())):
        
            if data[plotKey]:
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
                        if plotKey.lower() != 'azsheardiffs' and plotKey.lower() != 'azsheartopdiffs' and plotKey.lower() != 'azshearbotdiffs':
                            makeHistogram(data[plotKey], axis[groupKey][plotKey], titles[groupKey][plotKey], radii=radii)
                        else:
                            minOrder = 10**getOrder(min(data[plotKey]))
                            maxOrder = 10**getOrder(max(data[plotKey]))
                            
                            binRange = (math.floor(min(data[plotKey])/minOrder)*minOrder, math.ceil(max(data[plotKey])/maxOrder)*maxOrder)
                            
                            print('About to make a histogram for', groupKey, plotKey, '\nwith minmax', min(data[plotKey]), max(data[plotKey]), 'to bin range', binRange)
                            makeHistogram(data[plotKey], axis[groupKey][plotKey], titles[groupKey][plotKey], binRange=binRange)
                    except KeyError as e:
                        print('KeyError while making histogram', str(e))
                if plotValue == 'histogramardius':
                    try:
                        for radius in list(data[plotKey].keys()):
                            makeHistogramRadius(data[plotKey][radius], axis[groupKey][plotKey], titles[groupKey][plotKey], radius, radii=radii)
                    except KeyError as e:
                        print('KeyError while making histogramradius', str(e))
            else:
                print('No data for', groupKey, plotKey)
                
                
    return


def makeHistogramRadius(data, axis, title, radius, radii=None, binRange=None):

    """
        Makes a histogram out of data with the axis labeled and the title
    """

    title = title.replace('/', '-')
    bins=None
    
    print('Creating histogram', title, radius, '\nwith', data)
    if 'echo-top' in title.lower():
        minOrder = 10**getOrder(min(data))
        maxOrder = 10**getOrder(max(data))
        
        binRange = (math.floor(min(data)/minOrder)*minOrder, math.ceil(max(data)/maxOrder)*maxOrder)
        etBins = [x for x in range(int(binRange[0]), int(binRange[1]), 2000)]
      
    fig, ax = plt.subplots(1, 1, figsize=(10, 9))
    
    if radii and 'echo-top' not in title.lower():
        relativeData, bins = calculateRelativeFrequencies(data, radii)
        plt.bar(bins, relativeData, color=['#12b2de'], edgecolor=[0.063, 0.145, 0.902], width=35)
        plt.ylim([0, 0.303])
    elif binRange:
        if 'echo-top' in title.lower():
            plt.hist(data, bins=etBins, range=binRange, weights=np.ones_like(data)/len(data), color=['#12b2de'], edgecolor=[0.063, 0.145, 0.902])
        else:
            plt.hist(data, range=binRange, weights=np.ones_like(data)/len(data), color=['#12b2de'], edgecolor=[0.063, 0.145, 0.902])
    else:
        plt.hist(data, weights=np.ones_like(data)/len(data), color=['#12b2de'], edgecolor=[0.063, 0.145, 0.902])
    
    plt.title(title+ 'R='+str(radius), fontsize=20)
    plt.xlabel(axis, fontsize=18)
    plt.ylabel('Relative Frequency', fontsize=18)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    
    
    if 'echo-top' in title.lower():
        ax.get_xaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: Decimal(x)/10000))
        plt.xlabel("Echo-Top Error (x10$^{4}$ ft)")
        plt.ylim([0, 0.303])
        
    plt.savefig(os.path.join('figures', str(title).replace('$^\circ$', '')+'_'+str(radius)+'.png'), format='png')
    plt.savefig(os.path.join('figures', str(title).replace('$^\circ$', '')+'_'+str(radius)+'.pdf'), format='pdf')
    
    plt.close()
    
    return
    
    
def makeHistogram(data, axis, title, binRange=None, radii=None):

    """
        Makes a histogram out of data with the axis labeled and the title
    """

    title = title.replace('/', '-')
    
    print('Creating histogram', title.replace('$^\circ$', ''), '\nwith', data)
    if 'echo-top' in title.lower():
        minOrder = 10**getOrder(min(data))
        maxOrder = 10**getOrder(max(data))
        
        binRange = (math.floor(min(data)/minOrder)*minOrder, math.ceil(max(data)/maxOrder)*maxOrder)
        etBins = [x for x in range(int(binRange[0]), int(binRange[1]), 2000)]
        
    fig, ax = plt.subplots(1, 1, figsize=(10, 9))
    
    if radii and 'echo-top' not in title.lower():
        relativeData, bins = calculateRelativeFrequencies(data, radii)
        plt.bar(bins, relativeData, color=['#12b2de'], edgecolor=[0.063, 0.145, 0.902], width=35)
        plt.ylim([0, 0.303])
    elif range:
        if 'echo-top' in title.lower():
            plt.hist(data, bins=etBins, range=binRange, weights=np.ones_like(data)/len(data), color=['#12b2de'], edgecolor=[0.063, 0.145, 0.902])
        else:
            plt.hist(data, range=binRange, weights=np.ones_like(data)/len(data), color=['#12b2de'], edgecolor=[0.063, 0.145, 0.902])
    else:
        plt.hist(data, weights=np.ones_like(data)/len(data), color=['#12b2de'], edgecolor=[0.063, 0.145, 0.902])
    
    plt.title(title, fontsize=20)
    plt.xlabel(axis, fontsize=18)
    plt.ylabel('Relative Frequency', fontsize=18)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    
    
    if 'echo-top' in title.lower():
        ax.get_xaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: Decimal(x)/10000))
        plt.xlabel("Echo-Top Error (x10$^{4}$ ft)")
        plt.ylim([0, 0.303])
    
    plt.savefig(os.path.join('figures', str(title).replace('$^\circ$', '')+'.png'), format='png')
    plt.savefig(os.path.join('figures', str(title).replace('$^\circ$', '')+'.pdf'), format='pdf')
    
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
        print('Unable to make scatter plot for', title.replace('$^\circ$', ''), len(xList), len(yList))
        return
        
    xAxisLabel, yAxisLabel = axis.split(',')
    print('Creating scatter', title.replace('$^\circ$', ''), 'with\n', xList, '\n', yList)
    
    plt.scatter(xList, yList, c=np.array([0.834, 0.366, 0.109]))
    
    if 'A-M Versus Size' in title and len(xList) > 3 and len(yList) > 3 and False:
        
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
    plt.xticks(fontsize='x-large')
    plt.yticks(fontsize='x-large')
    
    cCoef = 'NA'
    if len(xList) > 1 and len(yList) > 1:
        cCoef = round(scistat.pearsonr(xList, yList)[0], 3)
        
    plt.annotate('N: '+str(len(xList))+'\nSlope: '+str(round(bestFit[0], 3))+'\nIntercept: '+str(round(bestFit[1], 3))+' knots'\
                +"\nr: "+str(cCoef)\
                +'\nRMSE: '+str(round(rmse, 3))+' knots',\
                (0.15, 0.69), xycoords='figure fraction', fontsize='large')
                
    plt.savefig(os.path.join('figures', str(title).replace('$^\circ$', '')+'.png'), format='png')
    plt.savefig(os.path.join('figures', str(title).replace('$^\circ$', '')+'.pdf'), format='pdf')
    
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
        print('Unable to make scatter plot for', title.replace('$^\circ$', ''), radius, len(xList), len(yList))
        return
        
    xAxisLabel, yAxisLabel = axis.split(',')
    print('Creating scatter', title.replace('$^\circ$', ''), 'with\n', xList, '\n', yList)
    
    plt.scatter(xList, yList, c=np.array([0.834, 0.366, 0.109]))
    
    #Get the best fit estimation
    bestFit = np.polyfit(xList, yList, 1)
    
    bestFitX = np.linspace(np.min(xList), np.max(xList), 100)
    #Plot the best fit line
    plt.plot(bestFitX, np.polyval(bestFit, bestFitX), c=[0, 0, 0])
    
    rmse = stats.getRMSE(yList, np.polyval(bestFit, xList))
    
    plt.legend(labels=['Linear Best Fit', 'V$_{rot}$ Pairs'], loc=4, fontsize='x-large')
    
    plt.title(title+' R='+str(radius)+' m', fontsize='x-large')
    plt.xlabel(xAxisLabel, fontsize='x-large')
    plt.ylabel(yAxisLabel, fontsize='x-large')
    plt.xticks(fontsize='x-large')
    plt.yticks(fontsize='x-large')
    
    
    cCoef = 'NA'
    if len(xList) > 1 and len(yList) > 1:
        cCoef = round(scistat.pearsonr(xList, yList)[0], 3)
        
    #plt.annotate('Assumed Radius = '+str(radius)+'m', (0.15, 0.83), xycoords='figure fraction', fontsize='large')
    plt.annotate('N: '+str(len(xList))+'\nSlope: '+str(round(bestFit[0], 3))+'\nIntercept: '+str(round(bestFit[1], 3))+' knots'\
                +"\nr: "+str(cCoef)\
                +'\nRMSE: '+str(round(rmse, 3))+' knots',\
                (0.15, 0.69), xycoords='figure fraction', fontsize='large')
                
    plt.savefig(os.path.join('figures', str(title).replace('$^\circ$', '')+'_'+str(radius)+'.png'), format='png')
    plt.savefig(os.path.join('figures', str(title).replace('$^\circ$', '')+'_'+str(radius)+'.pdf'), format='pdf')
    
    plt.close()
    
    return
    
def makeScatterPlotCorrected(xList, yList, title):

    
    title = title.replace('/', '-')
    

    if not xList or not yList or (len(xList) != len(yList)):
        print('Unable to make scatter plot for', title.replace('$^\circ$', ''), len(xList), len(yList))
        return
        
   
    print('Creating scatter', title.replace('$^\circ$', ''), 'with\n', xList, '\n', yList)
    
    plt.scatter(xList, yList, c=np.array([0.834, 0.366, 0.109]))
    
    #Get the best fit estimation
    bestFit = np.polyfit(xList, yList, 1)
    
    bestFitX = np.linspace(np.min(xList), np.max(xList), 100)
    #Plot the best fit line
    plt.plot(bestFitX, np.polyval(bestFit, bestFitX), c=[0, 0, 0])
    
    rmse = stats.getRMSE(yList, np.polyval(bestFit, xList))
    
    plt.legend(labels=[ 'Linear Best Fit', 'Vrot Pairs'], loc=4, fontsize='x-large')
    
    plt.title(title, fontsize='x-large')
    plt.xlabel('Manual Vrot (kts)', fontsize='x-large')
    plt.ylabel('Automated Area Vrot (kts)', fontsize='x-large')
    plt.xticks(fontsize='x-large')
    plt.yticks(fontsize='x-large')
    
    cCoef = 'NA'
    if len(xList) > 1 and len(yList) > 1:
        cCoef = round(scistat.pearsonr(xList, yList)[0], 3)
        
    #plt.annotate('Assumed Radius = '+str(radius)+'m', (0.15, 0.83), xycoords='figure fraction', fontsize='large')
    plt.annotate('N: '+str(len(xList))+'\nSlope: '+str(round(bestFit[0], 3))+'\nIntercept: '+str(round(bestFit[1], 3))+' knots'\
                +"\nr: "+str(cCoef)\
                +'\nRMSE: '+str(round(rmse, 3))+' knots',\
                (0.15, 0.690), xycoords='figure fraction', fontsize='large')
                
    plt.savefig(os.path.join('figures', str(title).replace('$^\circ$', '')+'.png'), format='png')
    plt.savefig(os.path.join('figures', str(title).replace('$^\circ$', '')+'.pdf'), format='pdf')
    
    plt.close()
    
    return    

def setBPLineWidth(boxes, width):

    plt.setp(boxes['boxes'], linewidth=width)
    plt.setp(boxes['medians'], linewidth=width)
    plt.setp(boxes['whiskers'], linewidth=width)
    plt.setp(boxes['fliers'], linewidth=width)
    
    return
    
def makeErrorsBoxplots(groups, tiltList):
 
    """ This is a custom function added specificially for the thesis """\
    
    
    #Make a boxplot 
    xTickLabels = ['0.5$^\circ$', '0.9$^\circ$', '1.3/1.45$^\circ$', '1.8$^\circ$', '2.4$^\circ$', 'ALL']
    xticks = [2*x for x in range(len(xTickLabels))]
    desiredRadii = [1300.0, 1300.0, 1200.0, 1700.0, 1450.0]
    boxGroupList = []
    sampleNumbers = []
    
    print('Looping through', tiltList, desiredRadii)
    radiusCount = 0
    for tilt in tiltList:
        if tilt == '1.3':
            tilt = '1.3/1.45'
        elif tilt == '1.45':
            continue
            
        boxGroupList.append(groups['Vrot '+str(tilt)]['vrotrdiffs'][desiredRadii[radiusCount]])
        sampleNumbers.append(len(groups['Vrot '+str(tilt)]['vrotrdiffs'][desiredRadii[radiusCount]]))
        radiusCount += 1
        
    boxGroupList.append(groups['all']['vrotrdiffs'][1300.0])
    sampleNumbers.append(len(groups['all']['vrotrdiffs'][1300.0]))
    desiredRadii.append(1300.0)
    radiiToPlot = list(map(str, list(map(int, desiredRadii))))
    
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    print(len(boxGroupList), list(xticks))
    
    vrotBoxPlots = plt.boxplot(boxGroupList, positions=xticks, sym='k.', showmeans=True, meanprops={'markersize':10})
    setBPLineWidth(vrotBoxPlots, 2)
    
    trans = transforms.blended_transform_factory(ax.transData, ax.transAxes)
    for xPos1, n1, radius in zip(xticks, sampleNumbers, radiiToPlot):
        plt.text(xPos1-0.25, 0.01, n1, fontsize=16, weight='bold', transform=trans)
        plt.text(xPos1-0.35, 0.85, radius, fontsize=16, weight='bold', transform=trans)
        
    ylims = ax.get_ylim()
    if ylims[0] <= 0 and ylims[1] >= 0:
        plt.axhline(y=0, color='b')
    plt.title('Automated - Manual $V_{rot}$ by Tilt', fontsize='xx-large')
    plt.xticks(ticks=xticks, labels=xTickLabels, fontsize='xx-large')
    plt.ylabel("$V_{rot}$ Errors (Knots)", fontsize='xx-large')
    plt.xlabel('Tilt', fontsize='xx-large')
    plt.yticks(fontsize='xx-large')
    
    plt.savefig(os.path.join('figures', 'vrot_error_boxes.png'), format='png')
    plt.savefig(os.path.join('figures', 'vrot_error_boxes.pdf'), format='pdf')
    
    plt.close()
    
    #Now do it with the echo tops
    
    xTickLabels = ['Max Echo Tops', '90$^{th}$% Echo Tops']
    xticks = [2*x for x in range(len(xTickLabels))]
    boxGroupList = [groups['et']['etdiff'], groups['et']['et90diff']]
    sampleNumbers = [len(groups['et']['etdiff']), len(groups['et']['et90diff'])]
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    etBoxPlots = plt.boxplot(boxGroupList, positions=xticks, sym='k.', showmeans=True, meanprops={'markersize':10})
    setBPLineWidth(etBoxPlots, 2)
    
    for xPos2, n2 in zip(xticks, sampleNumbers):
        plt.text((xPos2*4)+0.5, 0.01, n2, fontsize=16, weight='bold', transform=trans)
    
    ylims = ax.get_ylim()
    if ylims[0] <= 0 and ylims[1] >= 0:
        plt.axhline(y=0, color='b')
        
    plt.title('Automated - Manual 20-dBZ Echo Tops', fontsize='xx-large')
    plt.xticks(ticks=xticks, labels=xTickLabels, fontsize='xx-large')
    ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: Decimal(x)/10000))
    plt.ylabel("Echo Top Errors (x10$^{4}$ ft)", fontsize='xx-large')
    plt.yticks(fontsize='xx-large')
    
    plt.savefig(os.path.join('figures', 'et_error_boxes.png'), format='png')
    plt.savefig(os.path.join('figures', 'et_error_boxes.pdf'), format='pdf')
    
    plt.close()
    
    return