#This module contains the classes and functions for making figures for the results of ttrappy



import stats2
from matplotlib import pyplot as plt
import matplotlib.transforms as transforms
import matplotlib.ticker as ticker
import numpy as np
import os
import math
import copy
from scipy.stats import spearmanr
from decimal import Decimal, getcontext
import sorting
import coordinator as coord
import multirange
import matplotlib as mpl
mpl.use('Agg')
        
        
#Begin definitions for a global AxisRanges object to be acessible to all the functions
globalAxis = None #Start with none until defined later

def getGlobalAx(group):
    """ Returns a tuple for the minimum and maximum range for that group.
    
        Arguments:
        group(str): Which group to return the range from.
        
        Returns:
        (tuple): A tuple (min, max) for the range of data for that particular group.
        
    """
    
    global globalAxis
    
    return globalAxis.getRange(group)
    
def setGlobalAx(currentYAxis):

    """ Sets the globalAxis object to currentYAxis.
    
        Arguments:
        currentYAxis(AxisRanges): The AxisRanges object to set the global object to.
        
        Returns:
        None
    """
    
    global globalAxis
    globalAxis = currentYAxis
    
    return

def getOrder(num):
    
    """ Returns the order of magnitude of num """
    
    if num == 0:
        return 0
    elif num < 0:
        num = abs(num)
        
    return math.floor(math.log10(num))
    
    
def roundRange(ranges, order=None):

    """ Takes the minimum and maximum values from range and uses floor and ceil respectively to round to the nearest order ... of magnitude. If order is None, the largest value is used.
    
        Arguments:
        ranges(tuple) - a tuple for the range for the format (min, max)
        order(int) - the order of magintude to use to round (e.g., 0.01, 0.1, 1, 10, 100, etc.). The largest possible value for that number is used if order is None (default).
        
        Returns:
        (tuple) - The same format as ranges, but with the rounded values.
        
    """
    
    #Make sure the range formating is correct
    if ranges[0] > ranges[1]:
        raise ValueError("Minimum is greater than maximum")
    
    if order:
        exponentMin = 10**order
        exponentMax = 10**order
    else:
        exponentMin = 10**getOrder(ranges[0])
        exponentMax = 10**getOrder(ranges[1])
    
    newMin = math.floor(ranges[0]/exponentMin)*exponentMin
    newMax = math.ceil(ranges[1]/exponentMax)*exponentMax
    newAvg = (newMin+newMax)/2
    
    margin = 0.2
    if newMin < 0:
        newMin = newMin - (newAvg*margin)
    elif newMin == 0:
        newMin = -(newAvg) * margin
    else:
        newMin = newMin - (newAvg*margin)
    
    if newMax < 0:
        newMax = newMax - (newAvg*margin)
    elif newMax == 0:
        newMax = -(newAvg) * margin
    else:
        newMax = newMax + (newAvg*margin)
        
    print(ranges, 'is now', (newMin, newMax))
    
    return (newMin, newMax)
     
def set_box_color(bp, color):
    plt.setp(bp['boxes'], color=color)
    plt.setp(bp['whiskers'], color=color)
    plt.setp(bp['caps'], color=color)
    plt.setp(bp['medians'], color=color)
    
def add(a, b):
    return a + b

def convertToAzShear(vrot, radius):

    """ Converts estimated Vrot to azimuthal shear for a given radius """
    
    return (vrot*0.514)/radius #Convert vrot to m/s then divide by the radius
    
def azShearAxisFormat(x, pos):

    return "{value}x10$^{{-2}}$".format(value=round(Decimal(x), 3)*100)

def unpackTextList(listOfTexts):

    return [x.get_text() for x in list(listOfTexts)]
    
    
def make_time_x_label(cfg):
    """ Makes an xlabel for plots with time as the x-axis """
    
    xlabel = 'Time Bin Relative to '
    if cfg.shiftNonTor:
        if cfg.nontorShiftAmount.lower() == 'max':
            if cfg.shiftTor and cfg.torShiftAmount.lower() == 'max':
                xlabel += 'Max Rotation (Minutes)'
                return xlabel
            elif cfg.shiftTor and cfg.torShiftAmount.lower() != 'max':
                xlabel += 'NON TOR Max Rot. or TOR '+str(int(cfg.torShiftAmount) * -1)+' Seconds (Minutes)'
                return xlabel
            else:
                xlabel += 'NON TOR Max Rot. or TCTOR (Minutes)'
        else:
            xlabel+= 'NON TOR '+str(int(cfg.nontorShiftAmount)*-1)+' Seconds '
            if cfg.shiftTor and cfg.torShiftAmount.lower() == 'max':
                xlabel += 'TOR Max Rotation (Minutes)'
                return xlabel
            elif cfg.shiftTor and cfg.torShiftAmount.lower() != 'max':
                xlabel += 'or TOR '+str(int(cfg.torShiftAmount) * -1)+' Seconds (Minutes)'
                return xlabel
            else:
                xlabel += 'or TCTOR (Minutes)'
    else:
        xlabel += 'NON TOR Warning or '
        if cfg.shiftTor and cfg.torShiftAmount.lower() == 'max':
            xlabel += 'TOR Max Rot. (Minutes)'
            return xlabel
        elif cfg.shiftTor and cfg.torShiftAmount.lower() != 'max':
            xlabel += 'TOR '+str(int(cfg.torShiftAmount) * -1)+' Seconds (Minutes)'
            return xlabel
        else:
            xlabel += 'TCTOR (Minutes)'
            return xlabel
            
    print('Congratulations Sailor! You found the forbidden return')
    
    return xlabel
            
    
def makeEFBoxPlots(tor, torTDS, torNoTDS, title, ylabel, bin, timeIncrement, hypothesis, significantRatings=None, significantEFs=None):

    #title += '\n'
    
    xticks = []
    for EF in list(tor.keys()):
        xticks.append(EF)
        # if int(EF) < 0:
            # print('Warning! Potential nontor detected!')
            # exit()
        
    xticks = list(map(str, sorted(list(map(int, xticks)))))
    xticksEF = []
    for x in xticks:
        if int(x) < 0:
            xticksEF.append('EF Unknown')
        else:
            xticksEF.append('EF '+str(int(x)))
            
    
    #Start getting the data
    torGroup = []
    torTDSGroup = []
    torNoTDSGroup = []
    
    torSampleNumbers = []
    torTDSSampleNumbers = []
    torNoTDSSampleNumbers = []
    isSignificant = []

        
    for EF in xticks:
        
        if significantEFs:
            if EF in list(significantEFs.keys()):
                isSignificant.append(True)
            else:
                isSignificant.append(False)
        else:
            isSignificant.append(False)
        
        if EF in list(tor.keys()):
            torGroup.append(tor[EF])
            torSamples = str(len(tor[EF]))
            if tor[EF] == []:
                torSamples = '0'
            torSampleNumbers.append(torSamples)
            #print('Just got the number of samples for all tor at  bin', bin, 'and EF', EF, torSamples, '\nfrom', tor[EF])
        else:
            torGroup.append([])
            torSampleNumbers.append('')
            
        if EF in list(torTDS.keys()):
            torTDSGroup.append(torTDS[EF])
            tdsSamples = str(len(torTDS[EF]))
            if torTDS[EF] == []:
                tdsSamples = '0'
                
            torTDSSampleNumbers.append(tdsSamples)
        else:
            torTDSGroup.append([])
            torTDSSampleNumbers.append('')
        
        if EF in list(torNoTDS.keys()):
            torNoTDSGroup.append(torNoTDS[EF])
            noTDSSamples = str(len(torNoTDS[EF]))
            if torNoTDS[EF] == []:
                noTDSSamples = '0'
            torNoTDSSampleNumbers.append(noTDSSamples)
        else:
            torNoTDSGroup.append([])
            torNoTDSSampleNumbers.append('')
            
            
    print('Now making EF Box Plots for', title, 'with tor', torGroup, 'TDS', torTDSGroup, 'NO TDS', torNoTDSGroup, 'with EFs', xticks)
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 9))
    
    torPositions = [(x*3) - 0.63 for x in range(len(xticks))]
    tdsPositions = [(x*3) for x in range(len(xticks))]
    noTDSPositions = [(x*3) + 0.63 for x in range(len(xticks))]
    
    transformer = ax.transData + ax.transAxes.inverted()
    
    # yLevel = ax.transData.inverted().transform(fig.transFigure.transform((0, 0.10)))[1]
    # yLevelHigh = ax.transData.inverted().transform(fig.transFigure.transform((0, 0.85)))[1]
    yLevel = transformer.transform((0, 0.08))[1]
    yLevelHigh = transformer.transform((0, 0.8))[1]
    
    
    trans = transforms.blended_transform_factory(ax.transData, ax.transAxes)
    
    torGroupBoxes = None
    tdsGroupBoxes = None
    noTDSGroupBoxes = None
    
    if torGroup:
        torGroupBoxes = plt.boxplot(torGroup, positions=torPositions, sym='r.', widths=0.4, patch_artist=True)
        counter = 0
        for xPos1, n1 in zip(torPositions, torSampleNumbers):
            plt.text(xPos1-0.29, 0.01, n1, fontsize=14, weight='bold', transform=trans)
            #plt.text(xPos1, 0.9, 'ALL\nTOR', fontsize=10, transform=trans)
            
            if significantRatings:
                efString = ''
                for testTuple in list(significantRatings.keys()):
                    xTickIndex1 = xticks.index(str(testTuple[0]))
                    print('Testing EF diffs', xTickIndex1, counter , testTuple[0], xticks)
                    if xTickIndex1 != counter:
                        continue
                        
                    xTickIndex2 = xticks.index(str(testTuple[1]))
                    print('EF diffs 2', xTickIndex1, xTickIndex2, torGroup, torGroup[xTickIndex2], torGroup[xTickIndex1])
                    if torGroup[xTickIndex1] and torGroup[xTickIndex2]:
                        efString += 'EF'+str(testTuple[1])+' '
                        print('New EF String', efString)
                        
                plt.text(xPos1+0.05, 0.90, efString, fontsize=14, weight='bold', transform=trans)
                
            counter += 1
                
        set_box_color(torGroupBoxes, 'red')
        plt.setp(torGroupBoxes['boxes'], fill=False)
        
        
        
    if torTDSGroup:
        tdsGroupBoxes = plt.boxplot(torTDSGroup, positions=tdsPositions, sym='r.', widths=0.4, patch_artist=True)

        for xPos2, n2 in zip(tdsPositions, torTDSSampleNumbers):
            plt.text(xPos2-0.21, 0.01, n2, fontsize=14, weight='bold', transform=trans)
            #plt.text(xPos2, 0.9, 'TOR\nTDS', fontsize=10, transform=trans)

        set_box_color(tdsGroupBoxes, 'red')
        plt.setp(tdsGroupBoxes['boxes'], facecolor=[0.957, 0.561, 0.592, 0.5])
        
        if significantEFs:
            for n, box in enumerate(tdsGroupBoxes['boxes']):
                print('EF tds plots n, isSig, group', n, isSignificant, torTDSGroup, tdsGroupBoxes)
                if isSignificant[n] and torTDSGroup[n]:
                    plt.setp(tdsGroupBoxes['boxes'][n], linewidth=4)
                    plt.setp(tdsGroupBoxes['medians'][n], linewidth=4)
                    
        
    if torNoTDSGroup:
        noTDSGroupBoxes = plt.boxplot(torNoTDSGroup, positions=noTDSPositions, sym='r.', widths=0.4, patch_artist=True)
        for xPos3, n3 in zip(noTDSPositions, torNoTDSSampleNumbers):
            plt.text(xPos3-0.21, 0.01, n3, fontsize=14, weight='bold', transform=trans)
            #plt.text(xPos3, 0.9, 'TOR\nNO\nTDS', fontsize=10, transform=trans)

        set_box_color(noTDSGroupBoxes, 'red')
        plt.setp(noTDSGroupBoxes['boxes'], facecolor=[0.933, 0.169, 0.189, 1])
        plt.setp(noTDSGroupBoxes['boxes'], fill=False)
        for box in noTDSGroupBoxes['boxes']:
            box.set_hatch('...')
            
        if significantEFs:
            for n, box in enumerate(noTDSGroupBoxes['boxes']):
                if isSignificant[n] and torNoTDSGroup[n]:
                    plt.setp(noTDSGroupBoxes['boxes'][n], linewidth=4)
                    plt.setp(noTDSGroupBoxes['medians'][n], linewidth=4)
    
    legendBoxes = []
    legendLabels = []
    if torGroupBoxes:
        legendBoxes.append(torGroupBoxes['boxes'][0])
        legendLabels.append('ALL TOR')
    
    if tdsGroupBoxes:
        legendBoxes.append(tdsGroupBoxes['boxes'][0])
        legendLabels.append('TOR TDS')
        
    if torNoTDSGroup:
        legendBoxes.append(noTDSGroupBoxes['boxes'][0])
        legendLabels.append('TOR NO TDS')
        
    ylims = ax.get_ylim()
    if ylims[0] <= 0 and ylims[1] >= 0:
        plt.axhline(y=0, color='k')
     
    yRanges = None
    if 'AzShear' in ylabel or 'Echo Tops' in ylabel:
        plt.ticklabel_format(axis='y', style='scientfic', scilimits=(0, 0), useMathText=True)
        ax.yaxis.get_offset_text().set_fontsize(16)
        fig.canvas.draw()
        if 'AzShear' in ylabel:
            #If we have global y-axis ranges, use them for the y-axis limits
            if 'Cyclonic' in title:
                yRanges = (-10**(getOrder(getGlobalAx('AZSHEARposazshear')[0])), getGlobalAx('AZSHEARposazshear')[1])
            else:
                yRanges = getGlobalAx('AZSHEARazshear')

            ylabel = 'AzShear (X 10$^{-2}$ s$^{-1}$)'
            print(title, 'ylabels', unpackTextList(ax.get_yticklabels()))
            getcontext().prec = 3
            ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: Decimal(x)*100))
        elif 'Echo Tops' in ylabel:
            yRanges = getGlobalAx('et')
            ylabel = 'Echo Tops (X 10$^{4}$ ft)'
            yRanges = None
            yRanges = getGlobalAx('et')
                
            
            ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: (x/10000)))
        
        fig.canvas.draw()
    if 'rot' in ylabel:
        yRanges = (-10**(getOrder(getGlobalAx('AZSHEARvrot')[0])), getGlobalAx('AZSHEARvrot')[1])
        
    if yRanges:
        yRanges = roundRange(yRanges)
        plt.ylim(*yRanges)
        print('Updated EF Box yranges to', *yRanges)    
        
    ylims = ax.get_ylim()
    if ylims[0] <= 0 and ylims[1] >= 0:
        plt.axhline(y=0, color='k')
        
    plt.legend(legendBoxes, legendLabels, fontsize=16, loc='upper right')
    
    plt.title(title, fontsize=20)
    plt.ylabel(ylabel, fontsize=20)
    plt.xticks(ticks=[add(int(x), abs(min(list(map(int, xticks)))))*3 for x in xticks], labels=xticksEF, fontsize=18)
    plt.yticks(fontsize=18)
    
    plt.savefig(os.path.join('figures', hypothesis, title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace('|', '').replace(' ', '_').replace('\n', '')+'_box.png'), format='png')
    plt.savefig(os.path.join('figures', hypothesis, title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace('|', '').replace(' ', '_').replace('\n', '')+'_box.pdf'), format='pdf')
    
    plt.close()
        
    return
    
def makeIncrementalTrendBoxPlots(group1, group2, title, ylabel, timeIncrement, hypothesis, cfg, nonTorSignificantBins=None, torSignificantBins=None, trendSignificantBins=None):

    """ Makes boxplots for the incremental groups. """
    
    #title += '\n'
    
    #Get the initial xticks 
    xticks = []
    print('Trying group1', list(group1.keys()), group1, '\ngroup2', list(group2.keys()), group2, '\nin inc boxplots for', title)
    
    #Only use a group with available data:
    if list(group1.keys()) is not None:
        sortedList1 = sorted(list(group1.keys()), key=lambda tup: tup[0])
        
        for trendTuple in sortedList1:
            if (int(trendTuple[0]) >= cfg.minbin and int(trendTuple[1]) <= cfg.maxbin) or not cfg.prunebins:
                xticks.append(trendTuple)
        
        if not xticks:
            print(title, 'did not have xticks that met the bin bounds for list one. Trying group2 only.')
            sortedList2 = sorted(list(group2.keys()), key=lambda t: t[0])
            for trendTuple2 in sortedList2:
                if trendTuple2 is not None:
                    if (int(trendTuple2[0]) >= cfg.minbin and int(trendTuple2[1]) <= cfg.maxbin) or not cfg.prunebins:
                        xticks.append(trendTuple2)
                    else:
                        print('Warning! A trendTuple2 was', trendTuple2)
        else:            
            if list(group2.keys()) is not None:
                sortedList2 = sorted(list(group2.keys()), key=lambda t: t[0])
                for trendTuple2 in sortedList2:
                    if trendTuple2 is not None:
                        #Check to see if there is an earlier one and append it if not
                        if int(trendTuple2[0]) < int(xticks[0][0]) and ((int(trendTuple2[0]) >= cfg.minbin and int(trendTuple2[1]) <= cfg.maxbin) or not cfg.prunebins):
                            print('Adjust incremental boxplot xticks', xticks, 'based on', trendTuple2, 'backwards')
                            
                            xticks = [trendTuple2]+xticks
                        
                        #Now do the same thing in the forwards direction
                        elif int(trendTuple2[0]) > int(xticks[-1][1]) and ((int(trendTuple2[0]) >= cfg.minbin and int(trendTuple2[1]) <= cfg.maxbin) or not cfg.prunebins):
                            print('Adjust incremental boxplot xticks', xticks, 'based on', trendTuple2, 'forwards')
                            
                            xticks.append(trendTuple2)
                    else:
                        print('Warning!! Trend Tuple 2 was', trendTuple2)
            else:
                print('Warning! Group2 was missing from incremental boxplots for', title, group2)
                
        if not xticks:
            print('Warning!', title, 'did not have any xticks. Aborting plot making for this figure.')
            return
            
    else:
        print('Warning! No group1 in incremntal box plots for', title, group1, '\n. Trying group2 only.')
        if list(group2.keys()) is not None:
        
            if None in list(group2.keys()):
                 print('Warning! For some reason there is None in group2', list(group2.keys()))
            
            sortedList2 = sorted(list(group2.keys()), key=lambda t: t[0])
            for trendTuple in sortedList2:
                if (int(trendTuple[0]) >= cfg.minBin and int(trendTuple[1]) <= cfg.maxbin) or not cfg.prunebins:
                    xticks.append(trendTuple)
        else:
            print('Unable to make incremental boxplots', title, group2)
            return
                
            
    if xticks is None:
        print('Warning!!! xticks is None in incremntal box plots!', title)
        return    
        
    #Redo the xticks so they are in strings with time
    xticksTime = [str(int(x1)*timeIncrement)+'>'+str(int(x2)*timeIncrement) for x1, x2 in xticks]
    
    #Now make the groups that are to be plotted
    group1Group = []
    group1SampleNumbers = []
    group2Group = []
    group2SampleNumbers = []
    nonTorIsSignificant = []
    torIsSignificant = []
    areTrendsSignificant = []
    
    for trendTuple in xticks:
        
        if nonTorSignificantBins:
        
            try:
                if trendTuple in list(nonTorSignificantBins[trendTuple[0]].keys()):
                    nonTorIsSignificant.append(True)
                else:
                    nonTorIsSignificant.append(False)
            except KeyError:
                nonTorIsSignificant.append(False)
                
        else:
            nonTorIsSignificant.append(False)
            
        if torSignificantBins:
            try:
                if trendTuple in list(torSignificantBins[trendTuple[0]].keys()):
                    torIsSignificant.append(True)
                else:
                    torIsSignificant.append(False)
            except KeyError:
                torIsSignificant.append(False)
                
        else:
            torIsSignificant.append(False)
            
        if trendSignificantBins:
        
            try:
                if trendTuple in list(trendSignificantBins[trendTuple[0]].keys()):
                    areTrendsSignificant.append(True)
                else:
                    areTrendsSignificant.append(False)
            except KeyError:
                areTrendsSignificant.append(False)
        else:
            areTrendsSignificant.append(False)
            
            
        if trendTuple in list(group1.keys()):
            group1Group.append(group1[trendTuple])
            group1SampleNumbers.append(str(len(group1[trendTuple])))
        else:
            group1Group.append([])
            group1SampleNumbers.append('')
            
        if trendTuple in list(group2.keys()):
            group2Group.append(group2[trendTuple])
            group2SampleNumbers.append(str(len(group2[trendTuple])))
        else:
            group2Group.append([])
            group2SampleNumbers.append('')
            
            
    print('Now making trend incremental boxplots for', title, 'with group1', group1, 'group2', group2, 'bins', xticks)
    print('Incremnetal significants nontor', nonTorIsSignificant, 'tor', torIsSignificant, '\n',\
           nonTorSignificantBins, torSignificantBins)
    fig, ax = plt.subplots(1, 1, figsize=(10, 9))
    
    group1Positions = [(x*2) - 0.43 for x in range(len(xticks))]
    group2Positions = [(x*2) + 0.43 for x in range(len(xticks))]
    
    group1Boxes = None
    group2Boxes = None
    
    trans = transforms.blended_transform_factory(ax.transData, ax.transAxes)
    if group1Group:
        group1Boxes = plt.boxplot(group1Group, positions=group1Positions, sym='b.', widths=0.6, patch_artist=True)
        print('Just made incremental', group1Boxes, 'for', title, 'out of', group1Group)
        for xPos1, n1 in zip(group1Positions, group1SampleNumbers):
            plt.text(xPos1-0.27, 0.01, n1, fontsize=14, weight='bold', transform=trans)
        
        set_box_color(group1Boxes, 'blue')
        
        if nonTorSignificantBins:
            for n, box in enumerate(group1Boxes['boxes']):
                if nonTorIsSignificant[n] and group1Group[n]:
                    plt.setp(group1Boxes['boxes'][n], facecolor=[0.30196, 0.58039, 1.00000, 0.25])

                else:
                    plt.setp(group1Boxes['boxes'][n], fill=False)
                
                if areTrendsSignificant[n] and group1Group[n]:
                    plt.setp(group1Boxes['boxes'][n], linewidth=3)
                    plt.setp(group1Boxes['medians'][n], linewidth=3)
                    
        if trendSignificantBins:
            for n, box in enumerate(group1Boxes['boxes']):
                if areTrendsSignificant[n] and group1Group[n]:
                    plt.setp(group1Boxes['boxes'][n], linewidth=3)
                    plt.setp(group1Boxes['medians'][n], linewidth=3)

    if group2Group:
        group2Boxes = plt.boxplot(group2Group, positions=group2Positions, sym='r.', widths=0.6, patch_artist=True)
        print('Just made incremental', group2Boxes, 'for', title, 'out of', group2Group)
        for xPos2, n2 in zip(group2Positions, group2SampleNumbers):
            plt.text(xPos2-0.26, 0.01, n2, fontsize=14, weight='bold', transform=trans)
        
        set_box_color(group2Boxes, 'red')        
        
        if torSignificantBins:
             
            for n, box in enumerate(group2Boxes['boxes']):
                if torIsSignificant[n] and group2Group[n]:
                    print('group2 is significant', torIsSignificant)
                    plt.setp(group2Boxes['boxes'][n], facecolor=[0.933, 0.169, 0.189, 0.25])
                else:
                    plt.setp(group2Boxes['boxes'][n], fill=False)
        
        if trendSignificantBins:
            for n, box in enumerate(group2Boxes['boxes']):
                if areTrendsSignificant[n] and group2Group[n]:
                    plt.setp(group2Boxes['boxes'][n], linewidth=3)
                    plt.setp(group2Boxes['medians'][n], linewidth=3)
                    
        
    ylims = ax.get_ylim()
    if ylims[0] <= 0 and ylims[1] >= 0:
        plt.axhline(y=0, color='k')
        
    yRanges = None
    if 'AzShear' in ylabel or 'Echo Tops' in ylabel:
        plt.ticklabel_format(axis='y', style='scientfic', scilimits=(0, 0), useMathText=True)
        ax.yaxis.get_offset_text().set_fontsize(16)
        fig.canvas.draw()
        
        if 'AzShear' in ylabel:
            if 'Cyclonic' in title:
                yRanges = getGlobalAx('AZSHEARTRENDSposazshear')
            else:
                yRanges = getGlobalAx('AZSHEARTRENDSazshear')
                
            ylabel = '$\Delta$AzShear (X 10$^{-2}$ s$^{-1}$)'
            print(title, 'ylabels', unpackTextList(ax.get_yticklabels()))
            getcontext().prec = 3
            ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: Decimal(x)*100))
        elif 'Echo Tops' in ylabel:
            yRanges = getGlobalAx('ettrends')
                
            ylabel = '$\Delta$Echo Tops (X 10$^{4}$ ft)'
     
        fig.canvas.draw()
        
    if 'Maximum Composite Reflectivity' in title:
        yRanges = getGlobalAx('maxreftrends')
    if 'VIL' in ylabel:
        yRanges = getGlobalAx('viltrends')
    if 'Spectrum Width' in ylabel:
        yRanges = getGlobalAx('AZSHEARTRENDSspectrumwidth')
    if 'vrot' in ylabel:
        yRanges = getGlobalAx('AZSHEARTRENDSvrot')
        
    if yRanges:
        yRanges = roundRange(yRanges)
        plt.ylim(*yRanges)
        print('Updated incremntal trends y-axis range to', *yRanges)
    
    legendBoxes = []
    legendLabels = []
    if group1Boxes:
        legendBoxes.append(group1Boxes['boxes'][0])
        legendLabels.append('NON TOR')
    if group2Boxes:
        legendBoxes.append(group2Boxes['boxes'][0])
        legendLabels.append('ALL TOR')
        
    plt.legend(legendBoxes, legendLabels, fontsize=16, loc=(0.02, 0.1))
    
    plt.title(title, fontsize=20)
    plt.ylabel(ylabel, fontsize=20)
    plt.xticks(ticks=[x*2 for x in range(len(xticks))], labels=xticksTime, fontsize=18)
    plt.xlabel(make_time_x_label(cfg), fontsize=20)
    plt.yticks(fontsize=18)
    
    #Save the figure
    plt.savefig(os.path.join('figures', hypothesis, title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace('|', '').replace(' ', '_').replace('\n', '')+'_box.png'), format='png')
    plt.savefig(os.path.join('figures', hypothesis, title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace('|', '').replace(' ', '_').replace('\n', '')+'_box.pdf'), format='pdf')
    
    plt.close()
            
       
    return
    
def makeGreaterTrendBoxPlots(group1, group2, title, ylabel, bin, timeIncrement, hypothesis, cfg, nonTorSignificantBins=None, torSignificantBins=None, trendSignificantBins=None):

    """ Makes boxplots for the incremental groups. """
    
    #title += '\n'
    
    currentTimeBinTime = str(int(bin)*timeIncrement)+' Minutes'
    title += " from "+currentTimeBinTime
    
    #Get the initial xticks 
    xticks = []
    print('Trying group1', list(group1.keys()), group1, '\ngroup2', list(group2.keys()), group2, '\nin greater boxplots for', title)
    
    #Only use a group with available data:
    if list(group1.keys()) is not None:
        sortedList1 = sorted(list(group1.keys()), key=lambda tup: tup[1])
        
        for trendTuple in sortedList1:
            if (int(trendTuple[0]) >= cfg.minbin and int(trendTuple[1]) <= cfg.maxbin) or not cfg.prunebins:
                xticks.append(trendTuple)
        
        if not xticks:
            print(title, 'did not have xticks that met the bin bounds for list one. Trying group2 only')
            sortedList2 = sorted(list(group2.keys()), key=lambda t: t[1])
            for trendTuple2 in sortedList2:
                if trendTuple2 is not None:
                    if (int(trendTuple2[0]) >= cfg.minbin and int(trendTuple2[1]) <= cfg.maxbin) or not cfg.prunebins:
                        xticks.append(trendTuple2)
                else:
                    print('Warning! trendTuple2 was', trendTuple2)
        else:
                    
            if list(group2.keys()) is not None:
                sortedList2 = sorted(list(group2.keys()), key=lambda t: t[1])
                for trendTuple2 in sortedList2:
                    
                    if trendTuple2 is not None:
                        #Check to see if there is an earlier one and append it if not
                        if int(trendTuple2[1]) < int(xticks[0][1]) and ((int(trendTuple2[0]) >= cfg.minbin and int(trendTuple2[1]) <= cfg.maxbin) or not cfg.prunebins):
                            print('Adjust greater boxplot xticks', xticks, 'based on', trendTuple2, 'backwards')
                            
                            xticks = [trendTuple2]+xticks
                        
                        #Now do the same thing in the forwards direction
                        elif int(trendTuple2[1]) > int(xticks[-1][1]) and ((int(trendTuple2[0]) >= cfg.minbin and int(trendTuple2[1]) <= cfg.maxbin) or not cfg.prunebins):
                            print('Adjust greater boxplot xticks', xticks, 'based on', trendTuple2, 'forwards')
                            
                            xticks.append(trendTuple2)
                    else:
                        print('Warning!! Trend Tuple 2 was', trendTuple2, )
            else:
                print('Warning! Group2 was missing from greater boxplots for', title, group2)
                
        if not xticks:
            print('Warning!', title, 'did not have any xticks. Aborting plot making for this figure.')
            return
    else:
        print('Warning! No group1 in incremntal box plots for', title, group1, '\n. Trying group2 only.')
        if list(group2.keys()) is not None:
        
            if None in list(group2.keys()):
                 print('Warning! For some reason there is None in group2', list(group2.keys()))
            
            sortedList2 = sorted(list(group2.keys()), key=lambda t: t[1])
            for trendTuple in sortedList2:
                if (int(trendTuple[0]) >= cfg.minbin and int(trendTuple[1]) <= cfg.maxbin) or not cfg.prunebins:
                    xticks.append(trendTuple)
        else:
            print('Unable to make greater boxplots', title, group2)
            return
                
            
    if xticks is None:
        print('Warning!!! xticks is None in greater box plots!', title)
        return    
        
    #Redo the xticks so they are in strings with time
    print('Greater xticks', xticks)
    xticksTime = [str(int(x1)*timeIncrement)+'->'+str(int(x2)*timeIncrement) for x1, x2 in xticks]
    
    #Now make the groups that are to be plotted
    group1Group = []
    group1SampleNumbers = []
    group2Group = []
    group2SampleNumbers = []
    nonTorIsSignificant = []
    torIsSignificant = []
    areTrendsSignificant = []
    
    for trendTuple in xticks:
        
        if nonTorSignificantBins:
            try:
                if trendTuple in list(nonTorSignificantBins[trendTuple[0]].keys()):
                    nonTorIsSignificant.append(True)
                else:
                    nonTorIsSignificant.append(False)
            except KeyError:
                nonTorIsSignificant.append(False)
                
        else:
            nonTorIsSignificant.append(False)
            
        if torSignificantBins:
            try:
                if trendTuple in list(torSignificantBins[trendTuple[0]].keys()):
                    torIsSignificant.append(True)
                else:
                    torIsSignificant.append(False)
            except KeyError:
                torIsSignificant.append(False)
        else:
            torIsSignificant.append(False)
            

        if trendSignificantBins:
            try:
                if trendTuple in list(trendSignificantBins[trendTuple[0]].keys()):
                    areTrendsSignificant.append(True)
                else:
                    areTrendsSignificant.append(False)
            except KeyError:
                areTrendsSignificant.append(False)
        else:
            areTrendsSignificant.append(False)
            
        if trendTuple in list(group1.keys()):
            group1Group.append(group1[trendTuple])
            group1SampleNumbers.append(len(group1[trendTuple]))
        else:
            group1Group.append([])
            group1SampleNumbers.append('')
            
        if trendTuple in list(group2.keys()):
            group2Group.append(group2[trendTuple])
            group2SampleNumbers.append(len(group2[trendTuple]))
        else:
            group2Group.append([])
            group2SampleNumbers.append('')
            
            
    print('Now making trend greater boxplots for', title, 'with group1', group1, 'group2', group2, 'bins', xticks)
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 9))
    
    group1Positions = [(x*2) - 0.43 for x in range(len(xticks))]
    group2Positions = [(x*2) + 0.43 for x in range(len(xticks))]
    
    group1Boxes = None
    group2Boxes = None
    
    trans = transforms.blended_transform_factory(ax.transData, ax.transAxes)
    
    if group1Group:
        group1Boxes = plt.boxplot(group1Group, positions=group1Positions, sym='b.', widths=0.6, patch_artist=True)
        for xPos1, n1 in zip(group1Positions, group1SampleNumbers):
            plt.text(xPos1-0.27, 0.01, n1, fontsize=14, weight='bold', transform=trans)
        
        set_box_color(group1Boxes, 'blue')
        
        if nonTorSignificantBins:
            for n, box in enumerate(group1Boxes['boxes']):
                print('Greater Trends non  tor n, is sig, boxes, group', n, nonTorIsSignificant, group1Boxes['boxes'], group1Group)
                if nonTorIsSignificant[n] and group1Group[n]:
                    plt.setp(group1Boxes['boxes'][n], facecolor=[0.30196, 0.58039, 1.00000, 0.25])
                    
                else:
                    plt.setp(group1Boxes['boxes'][n], fill=False)
                    
        if trendSignificantBins:
            for n, box in enumerate(group1Boxes['boxes']):
                print('are significant', areTrendsSignificant, group1Group, group1Boxes['boxes'])
                if areTrendsSignificant[n] and group1Group[n]:
                    plt.setp(group1Boxes['boxes'][n], linewidth=3)
                    plt.setp(group1Boxes['medians'][n], linewidth=3)
        
    if group2Group:
        group2Boxes = plt.boxplot(group2Group, positions=group2Positions, sym='r.', widths=0.6, patch_artist=True)
        for xPos2, n2 in zip(group2Positions, group2SampleNumbers):
            plt.text(xPos2-0.26, 0.01, n2, fontsize=14, weight='bold', transform=trans)
        
        set_box_color(group2Boxes, 'red')
        
        if torSignificantBins:
            for n, box in enumerate(group2Boxes['boxes']):
                print('Checking', title, 'group2 signifiance', n, torIsSignificant, group2Group)
                if torIsSignificant[n] and group2Group[n]:
                    plt.setp(group2Boxes['boxes'][n], facecolor=[0.933, 0.169, 0.189, 0.25])
                    
                else:
                    plt.setp(group2Boxes['boxes'][n], fill=False)
                    
        if trendSignificantBins:
            for n, box in enumerate(group2Boxes['boxes']):
                if areTrendsSignificant[n] and group2Group[n]:
                    plt.setp(group2Boxes['boxes'][n], linewidth=3)
                    plt.setp(group2Boxes['medians'][n], linewidth=3)
                    
        
        
    ylims = ax.get_ylim()
    if ylims[0] <= 0 and ylims[1] >= 0:
        plt.axhline(y=0, color='k')
    
    yRanges = None
    if 'AzShear' in ylabel or 'Echo Tops' in ylabel:
        plt.ticklabel_format(axis='y', style='scientfic', scilimits=(0, 0), useMathText=True)
        ax.yaxis.get_offset_text().set_fontsize(16)
        fig.canvas.draw()
        if 'AzShear' in ylabel:
            if 'Cyclonic' in title:
                yRanges = getGlobalAx('AZSHEARTRENDSposazshear')
            else:
                yRanges = getGlobalAx('AZSHEARTRENDSazshear')
                
            ylabel = '$\Delta$AzShear (X 10$^{-2}$ s$^{-1}$)'
            print(title, 'ylabels', unpackTextList(ax.get_yticklabels()))
            getcontext().prec = 3
            ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: Decimal(x)*100))
        elif 'Echo Tops' in ylabel:
            yRanges = getGlobalAx('ettrends')
            
            ylabel = '$\Delta$Echo Tops (X 10$^{4}$ ft)'
            ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: (x/10000)))
        
        fig.canvas.draw()
        
    if 'Maximum Composite Reflectivity' in title:
        yRanges = getGlobalAx('maxreftrends')
    if 'VIL' in ylabel:
        yRanges = getGlobalAx('viltrends')
    if 'Spectrum Width' in ylabel:
        yRanges = getGlobalAx('AZSHEARTRENDSspectrumwidth')
    if 'rot' in ylabel:
        yRanges = getGlobalAx('AZSHEARTRENDSvrot')
        
    if yRanges:
        yRanges = roundRange(yRanges)
        plt.ylim(*yRanges)
        print('Updated greater trends y-axis range to', *yRanges)
        
    legendBoxes = []
    legendLabels = []
    
    if group1Boxes:
        legendBoxes.append(group1Boxes['boxes'][0])
        legendLabels.append('NON TOR')
    if group2Boxes:
        legendBoxes.append(group2Boxes['boxes'][0])
        legendLabels.append('ALL TOR')
        
        
    plt.legend(legendBoxes, legendLabels, fontsize=16, loc=(0.02, 0.1))
    
    plt.title(title, fontsize=20)
    plt.ylabel(ylabel, fontsize=20)
    plt.xticks(ticks=[x*2 for x in range(len(xticks))], labels=xticksTime, fontsize=18)
    plt.xlabel(make_time_x_label(cfg), fontsize=20)
        
    plt.yticks(fontsize=18)
    
    #Save the figure
    plt.savefig(os.path.join('figures', hypothesis, title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace('|', '').replace(' ', '_').replace('\n', '')+'_box.png'), format='png')
    plt.savefig(os.path.join('figures', hypothesis, title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace('|', '').replace(' ', '_').replace('\n', '')+'_box.pdf'), format='pdf')
    
    plt.close()
            
       
    return
    
    
def makeGroupedBoxPlots(group1Data, group2Data, title, ylabel, hypothesis, cfg, timeBinIncrement=5, significantBins=None):

    """ Makes a grouped boxplot based on bin number.
        Takes the """
    
    #title += '\n'
        
    #Create the xticks for each bin
    xticks = []
    for bin in list(group1Data.keys()):
         if (int(bin) >= cfg.minbin and int(bin) <= cfg.maxbin) or not cfg.prunebins:
            xticks.append(bin)
        
    #Now make sure we're not missing anything from group2Data
    for bin in list(group2Data.keys()):
        if bin not in xticks and ((int(bin) >= cfg.minbin and int(bin) <= cfg.maxbin) or not cfg.prunebins):
            xticks.append(bin)
            
    #Sort the bins
    xticks = list(map(str, sorted(list(map(int, xticks)))))
    #Create the xticks in terms of minutes relative to 
    xticksTime = [str(int(x)*timeBinIncrement) for x in xticks]
    
    print('Made xticks', xticks, xticksTime)
    #Create the data for to plot
    group1Group = []
    group2Group = []
    group1SampleNumbers = []
    group2SampleNumbers = []
    isSignificant = []
    
    for bin in xticks:
        if significantBins:
            if bin in list(significantBins.keys()):
                isSignificant.append(True)
            else:
                isSignificant.append(False)
        else:
            isSignificant.append(False)
            
        if bin in list(group1Data.keys()):
            group1Group.append(group1Data[bin])
            group1SampleNumbers.append(str(len(group1Data[bin])))
        else:
            group1Group.append([])
            group1SampleNumbers.append('')
            
        if bin in list(group2Data.keys()):
            group2Group.append(group2Data[bin])
            group2SampleNumbers.append(str(len(group2Data[bin])))
        else:
            group2Group.append([])
            group2SampleNumbers.append('')
                
                
    if not xticks:
        print('Warning!!! xticks in group box plots is None!', title)
        return
            
    print('Now making grouped boxplots for', title, 'with group1', group1Group, 'group2', group2Group, 'bins', xticks,'\n',\
            'significant bins', significantBins)
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 9))
    
    group1Positions = [(x*2) - 0.43 for x in range(len(xticks))]
    group2Positions = [(x*2) + 0.43 for x in range(len(xticks))]
    
     
    group1Boxes = None
    group2Boxes = None
    
    trans = transforms.blended_transform_factory(ax.transData, ax.transAxes)
    
    if group1Group:  
        group1Boxes = plt.boxplot(group1Group, positions=group1Positions, sym='b.', widths=0.6)
        #plt.plot([], color='blue', label='NON TOR')
        for xPos1, n1 in zip(group1Positions, group1SampleNumbers):
            plt.text(xPos1-0.27, 0.01, n1, fontsize=14, weight='bold', transform=trans)
            
        set_box_color(group1Boxes, 'blue')
        if significantBins:
            for n,box in enumerate(group1Boxes['boxes']):
                if isSignificant[n] and group1Group[n]:
                    print('group1', n, 'is significant', isSignificant, list(significantBins.keys()))
                    plt.setp(group1Boxes['boxes'][n], linewidth=3)
                    plt.setp(group1Boxes['medians'][n], linewidth=3)
        
    if group2Group:    
        group2Boxes = plt.boxplot(group2Group, positions=group2Positions, sym='r.', widths=0.6)
        #plt.plot([], color='red', label='ALL TOR')
        
        for xPos2, n2 in zip(group2Positions, group2SampleNumbers):
            plt.text(xPos2-0.26, 0.01, n2, fontsize=14, weight='bold', transform=trans)
        
        set_box_color(group2Boxes, 'red')
        
        if significantBins:
            for n,box in enumerate(group2Boxes['boxes']):
                if isSignificant[n] and group2Group[n]:
                    plt.setp(group2Boxes['boxes'][n], linewidth=3)
                    plt.setp(group2Boxes['medians'][n], linewidth=3)
        
    refLine = None    
    if '0' in xticks:
        refLine = plt.axvline(x=(xticks.index('0')*2), color='k', label='0 Minutes', linestyle='--')
    
    yRanges = None
    if 'AzShear' in ylabel or 'Echo Tops' in ylabel:
        plt.ticklabel_format(axis='y', style='scientific', scilimits=(0, 0), useMathText=True)
        ax.yaxis.get_offset_text().set_fontsize(16)
        fig.canvas.draw()
        if 'AzShear' in ylabel:
            if 'Cyclonic' in title:
                yRanges = (-10**(getOrder(getGlobalAx('AZSHEARposazshear')[0])), getGlobalAx('AZSHEARposazshear')[1])
            else:
                yRanges = getGlobalAx('AZSHEARazshear')
                
            ylabel = 'AzShear (X 10$^{-2}$ s$^{-1}$)'
            print(title, 'ylabels', unpackTextList(ax.get_yticklabels()))
            getcontext().prec = 3
            ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: Decimal(x)*100))
        elif 'Echo Tops' in ylabel:
            yRanges = getGlobalAx('et')
            
            ylabel = 'Echo Tops (X 10$^{4}$ ft)'
            ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: (x/10000)))
        
        
        fig.canvas.draw()
    
    if 'Maximum Composite Reflectivity' in title:
        yRanges = getGlobalAx('maxref')
    if 'VIL' in ylabel:
        yRanges = getGlobalAx('vil')
    if 'Spectrum Width' in ylabel:
        yRanges = getGlobalAx('AZSHEARspectrumwidth')
    if 'rot' in ylabel:
        yRanges = (-10**(getOrder(getGlobalAx('AZSHEARvrot')[0])), getGlobalAx('AZSHEARvrot')[1])
    
    if yRanges:
        yRanges = roundRange(yRanges)
        plt.ylim(*yRanges)
        print('Updated group box y range to', *yRanges)
        
    ylims = ax.get_ylim()
    if ylims[0] <= 0 and ylims[1] >= 0:
        plt.axhline(y=0, color='k')
    
    legendBoxes = []
    legendLabels = []
    if group1Boxes:
        legendBoxes.append(group1Boxes['boxes'][0])
        legendLabels.append('NON TOR')
    if group2Boxes:
        legendBoxes.append(group2Boxes['boxes'][0])
        legendLabels.append('ALL TOR')
    if refLine:
        legendBoxes.append(refLine)
        legendLabels.append('0 Minutes')
        
    plt.legend(legendBoxes, legendLabels, fontsize=16)
    
    
    
    plt.title(title, fontsize=20)
    plt.ylabel(ylabel, fontsize=20)
    plt.xticks(ticks=[add(int(x), abs(min(list(map(int, xticks)))))*2 for x in xticks], labels=xticksTime, fontsize=18)
    plt.xlabel(make_time_x_label(cfg), fontsize=20)
    plt.yticks(fontsize=18)
    
    #Save the figure
    plt.savefig(os.path.join('figures', hypothesis, title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace('|', '').replace(' ', '_').replace('\n', '')+'_box.png'), format='png')
    plt.savefig(os.path.join('figures', hypothesis, title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace('|', '').replace(' ', '_').replace('\n', '')+'_box.pdf'), format='pdf')
    
    plt.close()
    
    return

def makeGroupedLinePlot(group1Data, group2Data, title, ylabel, hypothesis, cfg, timeBinIncrement=5):

    """ Makes a grouped boxplot based on bin number. """
    
    #title += '\n'
        
    #Create the xticks for each bin
    xticks = []
    for bin in list(group1Data.keys()):
        if (int(bin) >= cfg.minbin and int(bin) <= cfg.maxbin) or not cfg.prunebins:
            xticks.append(bin)
        
    #Now make sure we're not missing anything from group2Data
    for bin in list(group2Data.keys()):
        if bin not in xticks and ((int(bin) >= cfg.minbin and int(bin) <= cfg.maxbin) or not cfg.prunebins):
            xticks.append(bin)
    
    if xticks is None:
        print('Warning!!! xticks is None in grouped line plot', title)
        return
        
    #Sort the bins
    xticksInt = sorted(list(map(int, xticks)))
    xticks = list(map(str, xticksInt))
    #Create the xticks in terms of minutes relative to 
    xticksTime = [str(int(x)*timeBinIncrement) for x in xticks]
    
    #Create the data for to plot
    group1Means = []
    group1Tops = []
    group1TopMasks = []
    group1Bottoms = []
    group1BottomMasks = []
    group2Means = []
    group2Tops = []
    group2Bottoms = []
    group2TopMasks = []
    group2BottomMasks = []
    group1SampleNumbers = []
    group2SampleNumbers = []
    
    for bin in xticks:
        if bin in list(group1Data.keys()) and ((int(bin) >= cfg.minbin and int(bin) <= cfg.maxbin) or not cfg.prunebins):
            group1Means.append(np.mean(group1Data[bin]))
           #group1Tops.append(np.percentile(group1Data[bin], 97.5))
            #group1Bottoms.append(np.percentile(group1Data[bin], 2.5))
            group1SampleNumbers.append(str(len(group1Data[bin])))
            if len(group1Data[bin]) >= 50:
                group1Tops.append(stats2.calculateCIBound(group1Data[bin], 0.975))
                group1Bottoms.append(stats2.calculateCIBound(group1Data[bin], 0.025))
                group1TopMasks.append(False)
                group1BottomMasks.append(False)
            else:
                group1Tops.append(math.nan)
                group1Bottoms.append(math.nan)
                group1TopMasks.append(True)
                group1BottomMasks.append(True)
            
        else:
            group1Means.append(math.nan)
            group1Tops.append(math.nan)
            group1Bottoms.append(math.nan)
            group1SampleNumbers.append('')
            group1TopMasks.append(True)
            group1BottomMasks.append(True)
            
        if bin in list(group2Data.keys()):
            group2Means.append(np.mean(group2Data[bin]))
            #group2Tops.append(np.percentile(group2Data[bin], 0.975))
            #group2Bottoms.append(np.percentile(group2Data[bin], 0.025))
            group2SampleNumbers.append(str(len(group2Data[bin])))
            
            if len(group2Data[bin]) >= 50:
                group2Tops.append(stats2.calculateCIBound(group2Data[bin], 0.975))
                group2Bottoms.append(stats2.calculateCIBound(group2Data[bin], 0.025))
                group2TopMasks.append(False)
                group2BottomMasks.append(False)
            else:
                group2Tops.append(math.nan)
                group2Bottoms.append(math.nan)
                group2TopMasks.append(True)
                group2BottomMasks.append(True)
        else:
            group2Means.append(math.nan)
            group2Tops.append(math.nan)
            group2Bottoms.append(math.nan)
            group2SampleNumbers.append('')
            group2TopMasks.append(True)
            group2BottomMasks.append(True)
            
    group1TopPlotData = np.ma.masked_array(group1Tops, mask=group1TopMasks)
    group1BottomPlotData = np.ma.masked_array(group1Bottoms, mask=group1BottomMasks)
    group2TopPlotData = np.ma.masked_array(group2Tops, mask=group2TopMasks)
    group2BottomPlotData = np.ma.masked_array(group2Bottoms, mask=group2BottomMasks)
            
    print('Now making grouped lineplots for', title, 'with means group1', group1Means, 'group2', group2Means, 'bins', xticks)
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 9))
    
    if not group1Means or not group2Means:
        print('Warning, one of the group means is missing for', title,'. Skipping the making of this figure.')
        plt.close()
        return
   
    if group1Tops and group1Bottoms:
        group1TopPlot = plt.plot(xticksInt, group1TopPlotData, color='blue', linestyle='--', label='NON TOR 95% CI')
        group1BottomPlot = plt.plot(xticksInt, group1BottomPlotData, color='blue', linestyle='--')
    
    group1Plot = plt.plot(xticksInt, group1Means, color='blue', marker='o', label='NON TOR Mean')
    
    if group2Tops and group2Bottoms:
        group2TopPlot = plt.plot(xticksInt, group2TopPlotData, color='red', linestyle='--', label='TOR 95% CI')
        group2BottomPlot = plt.plot(xticksInt, group2BottomPlotData, color='red', linestyle='--')
    
    group2Plot = plt.plot(xticksInt, group2Means, color='red', marker='o', label='ALL TOR Mean') 
    
    yRanges = None
    if 'AzShear' in ylabel or 'Echo Tops' in ylabel:
    
        if 'Cyclonic' in title:
            yRanges = (-10**(getOrder(getGlobalAx('AZSHEARposazshear')[0])), getGlobalAx('AZSHEARposazshear')[1])
        else:
            yRanges = getGlobalAx('AZSHEARazshear')
            
        plt.ticklabel_format(axis='y', style='scientific', scilimits=(0, 0), useMathText=True)
        ax.yaxis.get_offset_text().set_fontsize(16)
        fig.canvas.draw()
        if 'AzShear' in ylabel:
            ylabel = 'AzShear (X 10$^{-2}$ s$^{-1}$)'
            print(title, 'ylabels', unpackTextList(ax.get_yticklabels()))
            getcontext().prec = 3
            ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: Decimal(x)*100))
        elif 'Echo Tops' in ylabel:
            yRanges = getGlobalAx('et')
            
            ylabel = 'Echo Tops (X 10$^{4}$ ft)'
            ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: (x/10000)))
            
        
        fig.canvas.draw()
        
        
    plt.axvline(x=0, color='k', label='0 Minutes', linestyle='--')
    
    if 'Maximum Composite Reflectivity' in title:
        yRanges = getGlobalAx('maxref')
    if 'VIL' in ylabel:
        yRanges = getGlobalAx('vil')
    if 'Spectrum Width' in ylabel:
        yRanges = getGlobalAx('AZSHEARspectrumwidth')
    if 'rot' in ylabel:
        yRanges = (-10**(getOrder(getGlobalAx('AZSHEARvrot')[0])), getGlobalAx('AZSHEARvrot')[1])    
        
    if yRanges:
        yRanges = roundRange(yRanges)
        plt.ylim(*yRanges)
        print('Updated line plot y range to', *yRanges)
        
        
    ylims = ax.get_ylim()
    if ylims[0] <= 0 and ylims[1] >= 0:
        plt.axhline(y=0, color='k')
    
    plt.legend(fontsize=16)
    
    #Plot the sample sizes for each group
    yLevel = ax.transData.inverted().transform(fig.transFigure.transform((0, 0.12)))[1]
    for xPos1, n1 in zip(xticksInt, group1SampleNumbers):
        print('(1) Attempting to plot', n1, 'at', xPos1, yLevel)
        plt.text(xPos1-0.305, yLevel, n1, fontsize=14, weight='bold', color='blue')
    for xPos2, n2 in zip(xticksInt, group2SampleNumbers):
        plt.text(xPos2+0.005, yLevel, n2, fontsize=14, weight='bold', color='red')
        print('(2) Attempting to plot', n2, 'at', xPos2, yLevel)
    
    plt.title(title, fontsize=20)
    plt.ylabel(ylabel, fontsize=20)
    plt.xticks(ticks=xticksInt, labels=xticksTime, fontsize=18)
    plt.xlabel(make_time_x_label(cfg), fontsize=20)
    plt.yticks(fontsize=18)
    
    #Save the figure
    plt.savefig(os.path.join('figures', hypothesis, title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace('|', '').replace(' ', '_').replace('\n', '')+'_line.png'), format='png')
    plt.savefig(os.path.join('figures', hypothesis, title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace('|', '').replace(' ', '_').replace('\n', '')+'_line.pdf'), format='pdf')
    
    plt.close()
    
    return

def createTSSPlot(tssData, title, xlabel, dataUnits, hypothesis, cfg):

    """ Creates plots of TSS versus threshold and shows the best one with stats """
    
    #title += '\n'
    
    thresholds = []
    tssValues = []
    csiValues = []
    correctNumbers = []
    wrongNumbers = []
    farNumbers = []
    podNumbers = []
    
    for tss in tssData:
        if tss[1] is not None:
            thresholds.append(tss[1]['threshold'])
            tssValues.append(tss[1]['TSS'])
            csiValues.append(tss[1]['CSI'])
            correctNumbers.append(tss[1]['correct'])
            wrongNumbers.append(tss[1]['wrong'])
            farNumbers.append(tss[1]['far'])
            podNumbers.append(tss[1]['pod'])
            
            
    bestTSS, indexOfBest = stats2.getMaximumTSS(tssValues)
    if indexOfBest is not None:
        bestThreshold = thresholds[indexOfBest]
        bestCSI = csiValues[indexOfBest]
        bestCorrect = correctNumbers[indexOfBest]
        bestWrong = wrongNumbers[indexOfBest]
        bestFar = farNumbers[indexOfBest]
        bestPod = podNumbers[indexOfBest]
        azShearEqiv = str(round(round(convertToAzShear(float(bestThreshold), float(cfg.radius)), 3)*100, 3)) #Multiply by 100 for scientific notation
        print(title, 'AzShear equiv', azShearEqiv)
        
        statsString = 'Best Threshold: '+str(round(bestThreshold, 3))+' '+str(dataUnits)+\
                      '\nBest TSS: '+str(round(bestTSS, 3))+\
                      '\nAzShear : '+azShearEqiv+'x10$^{-2}$s$^{-1}$'+\
                      '\nCorrect: '+str(bestCorrect)+\
                      '\nWrong: '+str(bestWrong)+\
                      '\nFAR: '+str(round(bestFar, 3))+\
                      '\nPOD: '+str(round(bestPod, 3))+\
                      '\nCSI: '+str(round(bestCSI, 3))
                  
    fig, ax = plt.subplots(1, 1, figsize=(10, 9))
    
    #Make the plots
    plt.plot(thresholds, tssValues, color='b', linewidth=2)
    if indexOfBest is not None:
        plt.axvline(x=thresholds[indexOfBest], color='k', label='Best Threshold/TSS', linestyle='--')
        plt.axhline(y=tssValues[indexOfBest], color='k', linestyle='--')
        plt.text(0.675, 0.70, statsString, fontsize=14, weight='bold', color='green', transform=ax.transAxes)
    
    plt.xlim(min(thresholds), max(thresholds))
    plt.ylim(-0.2, 1.03)
    plt.axhline(y=0, color='k')
    plt.title(title, fontsize=20)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.ylabel('True Skill Score', fontsize=20)
    plt.xlabel(xlabel, fontsize=20)
    plt.legend(fontsize=16, loc='upper left')
    
    #Save the figure
    plt.savefig(os.path.join('figures', hypothesis, title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace('|', '').replace(' ', '_').replace('\n', '').replace('$^+$', '+')+'_line.png'), format='png')
    plt.savefig(os.path.join('figures', hypothesis,  title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace('|', '').replace(' ', '_').replace('\n', '').replace('$^+$', '+')+'_line.pdf'), format='pdf')
    
    plt.close()
    
    return

def reverseAxis(data):
    
    """ Takes a list of tuples (data) and returns a list of tuples with the elements reversed """
    
    return [(y, x) for x, y in data]

def splitTuples(data):

    x = []
    y = []
    
    for a, b in data:
        x.append(a)
        y.append(b)
        
    return x, y
    
def makeRangePlots(nonTor, torTDS, torNoTDS, title, xlabel, ylabel, tilt, hypothesis, bestTSSValue, bestTSSValue2):
    """ Takes (data, range) data and creates a scatter plot of it. Criteria is a list of tuples where
        each tuple is (minvalue, maxvalue, datavalue) of horizontal lines to put on the scatter plot.
        colors are the corresponding colors and labels are the corresponding labels. Criteria, colors, and labels
        must all be the same length.
        
    """
    
    nontorRanges, nonTorValues = splitTuples(reverseAxis(nonTor))
    tdsRanges, tdsValues = splitTuples(reverseAxis(torTDS))
    noTDSRanges, noTDSValues = splitTuples(reverseAxis(torNoTDS))
    
    #title += '\n'
    
    print('Plotting range plots nontor', (nontorRanges, nonTorValues), '\ntds', (tdsRanges, tdsValues), '\nnotds', (noTDSRanges, noTDSValues))
    
    fig, ax = plt.subplots(1, 1, figsize=(9.8, 7.9))
    correlationCoeffecientString = '$r_s$ Values:\n'
    
    if nonTor:
        plt.scatter(nontorRanges, nonTorValues, color='b', label='NON TOR', marker='o', facecolors='none', alpha=0.60)

    if torTDS:
        plt.scatter(tdsRanges, tdsValues, color='r', label='TOR TDS', alpha=0.65)
        
    if torNoTDS:
        plt.scatter(noTDSRanges, noTDSValues, color='r', label='TOR NO TDS', marker='o', facecolors='none', alpha=0.65)
    
    
    allRanges = copy.deepcopy(list(set(nontorRanges+tdsRanges+noTDSRanges)))
    
    allRanges.extend(tdsRanges)
    allRanges.extend(noTDSRanges)

    xRanges = getGlobalAx('distrange')
    if xRanges:
        plt.xlim(0, xRanges[1])
    else:
        plt.xlim(np.min(allRanges), np.max(allRanges))
    
    xlim = ax.get_xlim()
    
    bestFitXValues = np.linspace(xlim[0], xlim[1], 100)
    #If applicable, plot the best fit lines
    if nonTor:
        
        
        nonTorRs, nonTorRsP = spearmanr(nontorRanges, nonTorValues)
        #nonTorBestFit = np.polyfit(nontorRanges, nonTorValues, 1)
        
        #plt.plot(bestFitXValues, np.polyval(nonTorBestFit, bestFitXValues), color='k', linestyle='--', label='NON TOR Linear Fit', linewidth=2)
        
        correlationCoeffecientString += 'NON TOR: '+str(round(nonTorRs, 3))+'\n'
        
    if torTDS:
        
        tdsTorRs, TDSTorRsP = spearmanr(tdsRanges, tdsValues)
        
        #torTDSBestFit = np.polyfit(tdsRanges, tdsValues, 1)
        
        #plt.plot(bestFitXValues, np.polyval(torTDSBestFit, bestFitXValues), color='red', label='TOR TDS Linear Fit', linewidth=2)
        
        correlationCoeffecientString += 'TOR TDS: '+str(round(tdsTorRs, 3))+'\n'
        
    if torNoTDS:
        
        
        noTDSTorRs, noTDSTorRsP = spearmanr(noTDSRanges, noTDSValues)
        #noTDSBestFit = np.polyfit(noTDSRanges, noTDSValues, 1)

        #plt.plot(bestFitXValues, np.polyval(noTDSBestFit, bestFitXValues), color='red', label='TOR NO TDS Linear Fit', linestyle='--', linewidth=2)
        
        correlationCoeffecientString += 'TOR NO TDS: '+str(round(noTDSTorRs, 3))+'\n'
        
    plt.text(0.01, 0.82, correlationCoeffecientString, fontsize=14, transform=ax.transAxes)
    
    fig.canvas.draw()
    tssXValues1 = np.linspace(0, 40, 10)
    tssXValues2 = np.linspace(40, xRanges[1], 10)
    plt.plot(tssXValues1, np.ones(10)*bestTSSValue, color='#04b015', label='Best TSS', linewdith=3)
    plt.plot(tssXvalues2, np.ones(10)*bestTSSValue2, color='#04b015', linewidth=3)
    plt.axhline(y=0, color='k')
    
    yRanges = None
    if 'rot' in ylabel:
        if tilt == '0.5':
            tssXValues3 = np.linspace(0, 40, 10)
            tssXvalues4 = np.linspace(40, xRanges[1], 10)
            plt.plot(tssXValues3, 20*np.ones(10), color='#bcbf04', label='M17 Criteria', linewidth=3)
            plt.plot(tssXvalues4, 15*np.ones(10), color='#bcbf04', linewdith=3)
        
        yRanges = (-10**(getOrder(getGlobalAx('AZSHEARvrot')[0])), getGlobalAx('AZSHEARvrot')[1])
        
    if 'AzShear' in ylabel or 'Echo Tops' in ylabel:
        plt.ticklabel_format(axis='y', style='scientfic', scilimits=(0, 0), useMathText=True)
        ax.yaxis.get_offset_text().set_fontsize(16)
        fig.canvas.draw()
        if 'AzShear' in ylabel:
            if 'Cyclonic' in title:
                yRanges = (0, getGlobalAx('AZSHEARposazshear')[1])
            else:
                yRanges = getGlobalAx('AZSHEARazshear')
                
            ylabel = 'AzShear (X 10$^{-2}$ s$^{-1}$)'
            print(title, 'ylabels', unpackTextList(ax.get_yticklabels()))
            getcontext().prec = 3
            ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: Decimal(x)*100))
        elif 'Echo Tops' in ylabel:
            yRanges = getGlobalAx('et')
            
            ylabel = 'Echo Tops (X 10$^{4}$ ft)'
            ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: (x/10000)))
            
        
        fig.canvas.draw()
    
    if 'Maximum Composite Reflectivity' in title:
        yRanges = getGlobalAx('maxref')
    if 'VIL' in ylabel:
        yRanges = getGlobalAx('vil')
    if 'Spectrum Width' in ylabel:
        yRanges = getGlobalAx('AZSHEARspectrumwidth')
        
    if yRanges:
        yRanges = roundRange(yRanges)
        plt.ylim(*yRanges)
        print('Updated line plot y range to', *yRanges)
        
        
    ylims = ax.get_ylim()
    if ylims[0] <= 0 and ylims[1] >= 0:
        plt.axhline(y=0, color='k')
        
        
    plt.legend(loc='upper right', fontsize=16)
    plt.title(title, fontsize=20)
    plt.xlabel(xlabel, fontsize=20)
    plt.ylabel(ylabel, fontsize=20)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    
    #Save the figure
    plt.savefig(os.path.join('figures', hypothesis, title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace('|', '').replace(' ', '_').replace('\n', '')+'_scatter.png'), format='png')
    plt.savefig(os.path.join('figures', hypothesis,  title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace('|', '').replace(' ', '_').replace('\n', '')+'_scatter.pdf'), format='pdf')
    
    plt.close()
    
    return

def plotBestTSSLines(binnedTSS, rangeBreakPoints, xlims):

    for bin in list(binnedTSS.keys()):
        if bin == 0:
            xValues = np.linspace(0, rangeBreakPoints[0], 100)
            plt.plot(xValues, binnedTSS[bin]*np.ones(100), linewidth=3, color='#04b015', label='Best TSS')
        elif bin == len(rangeBreakPoints):
            xValues = np.linspace(rangeBreakPoints[-1], xlims[1], 100)
            plt.plot(xValues, binnedTSS[bin]*np.ones(100), linewidth=3, color='#04b015')
        else:

            index1, index2 = multirange.getStaggeredIndices(bin, len(rangeBreakPoints))
            
            minRange = rangeBreakPoints[index1]
            maxRange = rangeBreakPoints[index2]
            
            if minRange > maxRange:
                minRange, maxRange = maxRange, minRange
                
            xValues = np.linspace(minRange, maxRange, 100)
            plt.plot(xValues, binnedTSS[bin]*np.ones(100), linewidth=3, color='#04b015')
    
    return
    
    
def makeMultiRangePlots(nonTor, allTor, title, xlabel, ylabel, tilt, hypothesis, binnedTSSThresholds, rangeBreaks):
    """ Multirange version of makeRangePlots(). Takes (data, range) data and creates a scatter plot of it. Criteria is a list of tuples where
        each tuple is (minvalue, maxvalue, datavalue) of horizontal lines to put on the scatter plot.
        colors are the corresponding colors and labels are the corresponding labels. Criteria, colors, and labels
        must all be the same length. 
        
        rangeBreaks are the breakpoints for each bin whereas binnedTSSThresholds are the best thresholds for each bin. 
        
    """
    nontorRanges, nonTorValues = splitTuples(reverseAxis(nonTor))
    allTorRanges, allTorValues = splitTuples(reverseAxis(allTor))
    
    
    print('Plotting range plots nontor', (nontorRanges, nonTorValues), '\nalltor', (allTorRanges, allTorValues))
    
    fig, ax = plt.subplots(1, 1, figsize=(9.8, 7.9))
    correlationCoeffecientString = '$r_s$ Values:\n'
    
    
    if nonTor:
        plt.scatter(nontorRanges, nonTorValues, color='b', label='NON TOR', marker='o', facecolors='none', alpha=0.60)

    if allTor:
        plt.scatter(allTorRanges, allTorValues, color='r', label='TOR', marker='o', facecolors='none', alpha=0.60)

    allRanges = copy.deepcopy(list(set(nontorRanges+allTorRanges)))
    
    xRanges = getGlobalAx('distrange')
    
    if xRanges:
        plt.xlim(0, xRanges[1])
    else:
        plt.xlim(np.min(allRanges), np.max(allRanges))
    
    xlim = ax.get_xlim()
    bestFitXValues = np.linspace(xlim[0], xlim[1], 100)
    #If applicable, plot the best fit lines
    if nonTor:
        
        
        nonTorRs, nonTorRsP = spearmanr(nontorRanges, nonTorValues)
        #nonTorBestFit = np.polyfit(nontorRanges, nonTorValues, 1)
        
        #plt.plot(bestFitXValues, np.polyval(nonTorBestFit, bestFitXValues), color='k', linestyle='--', label='NON TOR Linear Fit', linewidth=2)
        
        correlationCoeffecientString += 'NON TOR: '+str(round(nonTorRs, 3))+'\n'
        
    if allTor:
        
        allTorRs, allTorRsP = spearmanr(allTorRanges, allTorValues)
        
        #torTDSBestFit = np.polyfit(tdsRanges, tdsValues, 1)
        
        #plt.plot(bestFitXValues, np.polyval(torTDSBestFit, bestFitXValues), color='red', label='TOR TDS Linear Fit', linewidth=2)
        
        correlationCoeffecientString += 'TOR: '+str(round(allTorRs, 3))+'\n'

        
    plt.text(0.01, 0.82, correlationCoeffecientString, fontsize=14, transform=ax.transAxes)
    
    fig.canvas.draw()
    plotBestTSSLines(binnedTSSThresholds, rangeBreaks, xlim)
    plt.axhline(y=0, color='k')
    
    yRanges = None
    if 'rot' in ylabel:
                
        yRanges = (-10**(getOrder(getGlobalAx('AZSHEARvrot')[0])), getGlobalAx('AZSHEARvrot')[1])
        
    if 'AzShear' in ylabel or 'Echo Tops' in ylabel:
        plt.ticklabel_format(axis='y', style='scientfic', scilimits=(0, 0), useMathText=True)
        ax.yaxis.get_offset_text().set_fontsize(16)
        fig.canvas.draw()
        if 'AzShear' in ylabel:
            if 'Cyclonic' in title:
                yRanges = (0, getGlobalAx('AZSHEARposazshear')[1])
            else:
                yRanges = getGlobalAx('AZSHEARazshear')
                
            ylabel = 'AzShear (X 10$^{-2}$ s$^{-1}$)'
            print(title, 'ylabels', unpackTextList(ax.get_yticklabels()))
            getcontext().prec = 3
            ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: Decimal(x)*100))
        elif 'Echo Tops' in ylabel:
            yRanges = getGlobalAx('et')
            
            ylabel = 'Echo Tops (X 10$^{4}$ ft)'
            ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: (x/10000)))
            
        
        fig.canvas.draw()
    
    if 'Maximum Composite Reflectivity' in title:
        yRanges = getGlobalAx('maxref')
    if 'VIL' in ylabel:
        yRanges = getGlobalAx('vil')
    if 'Spectrum Width' in ylabel:
        yRanges = getGlobalAx('AZSHEARspectrumwidth')
        
    if yRanges:
        yRanges = roundRange(yRanges)
        plt.ylim(*yRanges)
        print('Updated line plot y range to', *yRanges)
        
        
    ylims = ax.get_ylim()
    if ylims[0] <= 0 and ylims[1] >= 0:
        plt.axhline(y=0, color='k')
            
    plt.legend(loc='upper right', fontsize=16)
    plt.title(title, fontsize=20)
    plt.xlabel(xlabel, fontsize=20)
    plt.ylabel(ylabel, fontsize=20)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    
    #Save the figure
    plt.savefig(os.path.join('figures', hypothesis, title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace('|', '').replace(' ', '_').replace('\n', '')+'_multirange_scatter.png'), format='png')
    plt.savefig(os.path.join('figures', hypothesis,  title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace('|', '').replace(' ', '_').replace('\n', '')+'_multirange_scatter.pdf'), format='pdf')
    
    plt.close()
    
    return

def makeWarningStatsPlot(tssData, title, xlabel, hypothesis, cfg):

    thresholds = []
    csiValues = []
    farNumbers = []
    podNumbers = []
    
    #title += '\n'
    
    for tss in tssData:
        if tss[1] is not None:
            thresholds.append(tss[1]['threshold'])
            csiValues.append(tss[1]['CSI'])
            farNumbers.append(tss[1]['far'])
            podNumbers.append(tss[1]['pod'])
    
    if not thresholds:
        print('Warning! When making warning stats plots, there were not thresholds. Aborting the making of this figure.')
        return
    fig, ax = plt.subplots(1, 1, figsize=(10, 9))
    
    plt.plot(thresholds, podNumbers, color='b', linewidth=2, label='POD', )
    plt.plot(thresholds, farNumbers, color='r', linewidth=2, label='FAR')
    plt.plot(thresholds, csiValues, color='k', linewidth=2, label='CSI')
    
    plt.xlim(np.min(thresholds), np.max(thresholds))
    plt.ylim(0, 1.03)
    
    ylim = ax.get_ylim()
    plt.axhline(y=0, color='k')
    plt.title(title, fontsize=20)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    #plt.ylabel('Statistic (unitless)', fontsize=20)
    plt.xlabel(xlabel, fontsize=20)
    plt.legend(fontsize=16)
    
    #Save the figure
    plt.savefig(os.path.join('figures', hypothesis, title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace('|', '').replace(' ', '_').replace('\n', '').replace('$^+$', '+')+'_line.png'), format='png')
    plt.savefig(os.path.join('figures', hypothesis,  title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace('|', '').replace(' ', '_').replace('\n', '').replace('$^+$', '+')+'_line.pdf'), format='pdf')
    
    plt.close()
    
            
    return
    

def makeWarningBarPlots(normalStats, bestThreshold, m17Stats, realStats, title, hypothesis, cfg, bestThresholdLabel=None):

    """ Make bar plots of FAR, POD, and CSI for the provided group, Martinaitis (2017), and actual statistics (see stats2.calculateRealStats) """
    
    #title += '\n'
    
    #Add something here to handle nones
    if normalStats is None:
        normalStats = {'far':-0.05, 'pod':-0.05, 'CSI':-0.05}
    if m17Stats is None:
        m17Stats = {'far':-0.05, 'pod':-0.05, 'CSI':-0.05}
    if realStats is None:
        realStats = {'far':-0.05, 'pod':-0.05, 'CSI':-0.05}
        
    FARs = [normalStats['far'], m17Stats['far'], realStats['FAR']]
    PODs = [normalStats['pod'], m17Stats['pod'], realStats['POD']]
    CSIs = [normalStats['CSI'], m17Stats['CSI'], realStats['CSI']]
    
    bestThresholdString = ''
    if bestThreshold is not None:
        if bestThresholdLabel:
            bestThresholdString = bestThresholdLabel
        else:
            bestThresholdString = 'Best Threshold '+str(bestThreshold)+' Kts'
    else:
        print('Warning Bars do not have a best threshold for', title,'. Aborting figure making!')
        return
        
    xticks = [bestThresholdString, 'M17 $V_{rot}$ Criteria', 'Observed']
    xPos = [x*3 for x in range(len(xticks))]
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 9))
    width = 0.4
    plt.bar([pos-width for pos in xPos], FARs, width, color='r', align='center', label='FAR')
    plt.bar([pos for pos in xPos], PODs, width, color='b', align='center', label='POD')
    plt.bar([pos+width for pos in xPos], CSIs, width, color='k', align='center', label='CSI')
    plt.ylim(0, 1.03)
    
    plt.legend(fontsize=16)
    plt.title(title, fontsize=20)
    plt.xticks(ticks=xPos, labels=xticks, fontsize=18)
    plt.yticks(fontsize=18)
    #plt.ylabel('Statistic (Unitless)', fontsize=20)
    
    plt.savefig(os.path.join('figures', hypothesis, title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace(',', '').replace('|', '').replace(' ', '_').replace(' TSS', '').replace('\n', '').replace('$^+$', '+')+'_bar.png'), format='png')
    plt.savefig(os.path.join('figures', hypothesis,  title.replace(r'$^\circ$', '').replace("$V_{rot}$", 'Vrot').replace(',', '').replace('|', '').replace(' ', '_').replace(' TSS', '').replace('\n', '').replace('$^+$', '+')+'_bar.pdf'), format='pdf')
    
    plt.close()
    
    return
    
    
    
def makeMultirangeWarningBarPlots(data, realWarningStats, hypothesis, cfg):

    """ Make bar plots of FAR, POD, and CSI for the provided group, Martinaitis (2017), and actual statistics (see stats2.calculateRealStats) """
    
    #title += '\n'
    realStats = {'pod': realWarningStats['POD'] , 'far': realWarningStats['FAR'], 'csi': realWarningStats['CSI']}
    
    
    for bin in list(data.keys()):


        FARs = [realStats['far']]
        PODs = [realStats['pod']]
        CSIs = [realStats['csi']]
        TSSs = [0]
        
        xTicks = ['Observed']
        xPos = [0]
        
        
        
        numTests = len(data[bin].keys())
        
        for testNum,statsDict in data[bin].items():
                

            xTicks.append(str(testNum))
            xPos.append((int(testNum)+1)*numTests)
            FARs.append(statsDict['far'])
            PODs.append(statsDict['pod'])
            CSIs.append(statsDict['csi'])
            TSSs.append(statsDict['tss'])
            
        fig, ax = plt.subplots(1, 1, figsize=(10, 9))
        width = 1*(numTests/8)
        plt.bar([pos-(width*1.5) for pos in xPos], FARs, width, color='r', align='center', label='FAR')
        plt.bar([pos-(width/2) for pos in xPos], PODs, width, color='b', align='center', label='POD')
        plt.bar([pos+(width/2) for pos in xPos], CSIs, width, color='k', align='center', label='CSI')
        plt.bar([pos+(width*1.5) for pos in xPos], TSSs, width, color='g', align='center', label='TSS')
        
        plt.ylim(0, 1.03)
        
        title = 'Warning Statistics Using Best Thresholds at '+str(int(int(bin)*cfg.timeBinSize))+' Minutes'
        
        plt.legend(fontsize=16)
        plt.title(title, fontsize=20)
        plt.xticks(ticks=xPos, labels=xTicks, fontsize=18)
        plt.yticks(fontsize=18)
        #plt.ylabel('Statistic (Unitless)', fontsize=20)
        
        plt.savefig(os.path.join('figures', hypothesis, 'multirange_stats_'+str(bin)+'_bar.png'), format='png')
        plt.savefig(os.path.join('figures', hypothesis,  'multirange_stats_'+str(bin)+'_bar.pdf'), format='pdf')
        
        plt.close()
    
    return
    
def makeMultirangeBinStatPlots(data, currentTilt, units, hypothesis, cfg):

    """ Make bar plots of FAR, POD, and CSI for the provided group, Martinaitis (2017), and actual statistics (see stats2.calculateRealStats) """
    
    #title += '\n'
   
    
    
    for bin in list(data.keys()):


        FARs = []
        PODs = []
        CSIs = []
        TSSs = []
        
        xTicks = []
        xPos = []
        
        
        
        numTests = len(data[bin].keys())
        counter = 0
        lowSamplesPos = []
        for rangeTuple,statsDict in data[bin].items():
                
            currentThreshold = statsDict['threshold']
            if currentThreshold:
                xTicks.append(str(rangeTuple[0])+'->'+str(rangeTuple[1])+'\n'+\
                              str(currentThreshold)+'('+str(units)+')')
            else:
                xTicks.append('N/A')
                          
            currentXPos = int(counter)*numTests
            xPos.append(currentXPos)
            FARs.append(statsDict['far'])
            PODs.append(statsDict['pod'])
            CSIs.append(statsDict['csi'])
            TSSs.append(statsDict['tss'])
            
            counter += 1
            
            if statsDict['nontor'] < cfg.minTSSSamples or statsDict['tor'] < cfg.minTSSSamples:
                lowSamplesPos.append(currentXPos)
                
        title = 'Warning Statistics by Range Bin at '+str(int(int(bin)*cfg.timeBinSize))+' Minutes and '+str(currentTilt)+'$^\circ$'
            
        fig, ax = plt.subplots(1, 1, figsize=(10, 9))
        width = 1*(numTests/8)
        plt.bar([pos-(width*1.5) for pos in xPos], FARs, width, color='r', align='center', label='FAR')
        plt.bar([pos-(width/2) for pos in xPos], PODs, width, color='b', align='center', label='POD')
        plt.bar([pos+(width/2) for pos in xPos], CSIs, width, color='k', align='center', label='CSI')
        plt.bar([pos+(width*1.5) for pos in xPos], TSSs, width, color='g', align='center', label='TSS')
        
        #Plot stars above the bins with less than the minimum samples for TSS
        if lowSamplesPos:
            yValues = 0.9*np.ones(len(lowSamplesPos))
            
            plt.scatter(lowSamplesPos, yValues, color=['#D9594C'], s=150, marker='o', edgecolors='black', label='Low TSS Samples')
        
        plt.ylim(0, 1.03)
        
        plt.legend(fontsize=16)
        plt.title(title, fontsize=20)
        plt.xticks(ticks=xPos, labels=xTicks, fontsize=15)
        plt.xlabel('Range Bin (n mi.)', fontsize=15)
        plt.yticks(fontsize=18)
        #plt.ylabel('Statistic (Unitless)', fontsize=20)
        
        plt.savefig(os.path.join('figures', hypothesis, 'multirange_stats_'+str(bin)+'_'+str(currentTilt).replace(',', '_')+'_by_range_bar.png'), format='png')
        plt.savefig(os.path.join('figures', hypothesis,  'multirange_stats_'+str(bin)+'_'+str(currentTilt).replace(',', '_')+'_by_range_bar.pdf'), format='pdf')
        
        plt.close()
    
    return
    
    
def makeMultirangeCombStatPlots(data, currentTest, bin, title, hypothesis, cfg):

    """ Make bar plots of FAR, POD, and CSI for the provided group, Martinaitis (2017), and actual statistics (see stats2.calculateRealStats) """
    
    #title += '\n'
   
    
    


    FARs = []
    PODs = []
    CSIs = []
    TSSs = []
    
    xTicks = []
    xPos = []
    
    
    
    numBins = len(data.keys())
    counter = 0
    lowSamplesPos = []
    for rangeTuple,statsDict in data.items():
            
        if rangeTuple:
            xTicks.append(str(rangeTuple[0])+'->'+str(rangeTuple[1]))
        else:
            xTicks.append('N/A')
                      
        currentXPos = int(counter)*numBins
        xPos.append(currentXPos)
        FARs.append(statsDict['far'])
        PODs.append(statsDict['pod'])
        CSIs.append(statsDict['csi'])
        TSSs.append(statsDict['tss'])
        
        counter += 1
        
            
        
    fig, ax = plt.subplots(1, 1, figsize=(10, 9))
    width = 1*(numBins/8)
    plt.bar([pos-(width*1.5) for pos in xPos], FARs, width, color='r', align='center', label='FAR')
    plt.bar([pos-(width/2) for pos in xPos], PODs, width, color='b', align='center', label='POD')
    plt.bar([pos+(width/2) for pos in xPos], CSIs, width, color='k', align='center', label='CSI')
    plt.bar([pos+(width*1.5) for pos in xPos], TSSs, width, color='g', align='center', label='TSS')
    
    plt.ylim(0, 1.03)
    
    plt.legend(fontsize=16)
    plt.title(title, fontsize=20)
    plt.xticks(ticks=xPos, labels=xTicks, fontsize=15)
    plt.xlabel('Range Bin (n mi.)', fontsize=15)
    plt.yticks(fontsize=18)
    #plt.ylabel('Statistic (Unitless)', fontsize=20)
    
    plt.savefig(os.path.join('figures', hypothesis, 'multirange_combined_stats_'+str(bin)+'_'+str(currentTest).replace('$^\circ$', '').replace('&', '')+'_by_range_bar.png'), format='png')
    plt.savefig(os.path.join('figures', hypothesis,  'multirange_combined_stats_'+str(bin)+'_'+str(currentTest).replace('$^\circ$', '').replace('&', '')+'_by_range_bar.pdf'), format='pdf')
    
    plt.close()
    
    return
    
    
    
#-----------------Begin section on coordinating the analysis--------------------------------
def doKeyCheck(key1, keys2, keys3, keys4):
    """ Checks to see if key1 is in keys2-4 """
    
    if key1 in keys2 and key1 in keys3 and key1 in keys4:
        return True
    
    return False
    
def doH2ZTest(tdsCountDict):
    """ Performs a Z test on proportions on the TDSs for a given EF rating be less than the ratings above it. """
    
    efList = list(tdsCountDict['tdscount'].keys())
    for EF1 in efList:
        
        for EF2 in efList:
            
            if int(EF2) > int(EF1):
            
                if int(EF2) < 0 or int(EF1) < 0:
                    print('EF1', EF1, 'EF2', EF2, ' one is < 0. Skipping')
                    continue
                    
                Z, pValue = stats2.propZTest(tdsCountDict['tdscount'][EF1], tdsCountDict['totalcount'][EF1],\
                                            tdsCountDict['tdscount'][EF2], tdsCountDict['totalcount'][EF2],
                                            group1Name='EF '+str(EF1), group2Name='EF '+str(EF2),\
                                            alternative='less', writeMode='a', writeFile='h2ztest.csv')
                                            
    return
    
    
def beginAnalysis(nonTor, tor, tds, notds, cfg, realStats, realEFStats, axRanges=None, potentialClusters=''):
    """ Acts as the starting point for an analysis for each category.
        potentialClusters is a string of the integer number of potential clusters of that applies to the analysis.
    """
    
    #If we have the AxisRanges object, update the global version for plotting functions to use
    if axRanges:
        global globalAxis
        globalAxis = axRanges
        
    #Loop through each key of the nonTor dictionary.
    for key1 in nonTor.keys():
        #Do a check for the key in the rest of the lists
        keyExists = doKeyCheck(key1, list(tor.keys()), list(tds.keys()), list(notds.keys()))
        if not keyExists:
            print('Warning!', key1, 'not in all categories')
            with open('errors.txt', 'a') as fi:
                fi.write(f"{key1} not in all lists\n")
            continue
                
        #Start checking the key and assign data to a hypothesis 
        if key1.lower() == 'azshear clusters by tilt':
            hypothesis1(nonTor[key1], tor[key1], key1, potentialClusters, cfg)
            
            pass            
        elif key1.lower() == 'azshear cluster by tilt and ef':
            hypothesis2(tor[key1], tds[key1], notds[key1], key1, potentialClusters, cfg)
            pass
        elif key1.lower() == 'azshear cluster trends by tilt':   
            hypothesis4(nonTor[key1], tor[key1], key1,\
                        ['azshear', 'posazshear', 'absazshear', 'vrot', 'posvrot', 'spectrumwidth', 'posspectrumwidth', '90thazshear'],\
                        potentialClusters, cfg)
            
        elif key1.lower() == 'azshear clusters by tilt and range':
            hypothesis5(nonTor[key1], tor[key1], tds[key1], notds[key1], key1, ['vrot', 'posvrot', 'absshear', 'posazshear', '90thvrot'], potentialClusters, cfg, realStats)
            multirange.multirange(nonTor[key1], tor[key1], ['posvrot'], cfg, axRanges, nonTorET=nonTor['Cyclonic Case Echo Tops'], allTorET=tor['Cyclonic Case Echo Tops'], etDataTypes=['90thet', 'maxet'],\
                                   nonTorVIL=nonTor['Cyclonic Case Storm Data'], allTorVIL=tor['Cyclonic Case Storm Data'], vilDataTypes=['avgvil', 'maxvil'])
            pass
        elif key1.lower() == 'echo tops' or key1.lower() == 'cyclonic case echo tops':
            hypothesis3(nonTor[key1], tor[key1], key1, ['90thet', 'maxet'], potentialClusters, cfg)
            pass
        elif key1.lower() == 'storm data' or key1.lower() == 'cyclonic case storm data':
            hypothesis3(nonTor[key1], tor[key1], key1, ['maxvil', 'avgvil', 'maxref'], potentialClusters, cfg)
            pass
        elif key1.lower() == 'echo top trends' or key1.lower() == 'cyclonic case echo top trends':
            hypothesis4(nonTor[key1], tor[key1], key1, ['maxet', '90thet'], potentialClusters, cfg)
            pass
        elif key1.lower() == 'storm data trends' or key1.lower() == 'cyclonic case storm data trends':
            hypothesis4(nonTor[key1], tor[key1], key1, ['maxvil', 'avgvil', 'maxref'], potentialClusters, cfg)
            pass
        elif key1.lower() == 'azshear clusters by tilt and range and ef':
            hypothesis5EF(nonTor['AzShear Clusters by Tilt and Range'], tor[key1], tds[key1], notds[key1], key1, ['posvrot', '90thvrot'], potentialClusters, cfg, realStats, sortByTDS=True,\
                        includeNonTorInTDS=True)
            hypothesis5EF(nonTor['AzShear Clusters by Tilt and Range'], tor[key1], tds[key1], notds[key1], key1, ['posvrot', '90thvrot'], potentialClusters, cfg, realEFStats, \
                        lowerEFBoundaries=[-2, 0], higherEFBoundaries=[1, 5])
                        
            
    return
            
def doHypothesis1Tests(nonTor, tor, dataType, tilt, cfg, levelOfSignificance=0.05, potentialClusters=''):

    """ Runs through the Mann-Whitney-U Test for Hypothesis 1 and return the bins that are signifiant at the levelOfSignificance.
        Also calculates the general stats for nonTor and tor.
    """
    
    
    allBins = []
    for bin in list(nonTor.keys()):
        allBins.append(bin)
        
    for bin in list(tor.keys()):
        if bin not in allBins:
            allBins.append(bin)
            
    allBins = list(map(str, sorted(list(map(int, allBins)))))
    significantBins = {} # bin that was significant and it's p-value
    stats = {}
    for bin in allBins:
        
        try:
            #Write the general stats, then do the Mann-Whitney-U test
            stats[bin] = stats2.calculateStats(nonTor[bin], tor[bin], group1Name='NON TOR '+str(tilt)+' '+str(dataType)+' '+str(bin)+' '+potentialClusters,\
                              group2Name='ALL TOR '+str(tilt)+' '+str(dataType)+' '+str(bin)+' '+potentialClusters,\
                              writeMode='a', writeFile='h1stats.csv')
                              
            testResult = stats2.doMannWhitneyU(nonTor[bin], tor[bin], group1Name='NON TOR '+str(tilt)+' '+str(dataType)+' '+str(bin)+' '+potentialClusters,\
                                                group2Name='ALL TOR '+str(tilt)+' '+str(dataType)+' '+str(bin)+' '+potentialClusters,\
                                                use_continuity=True, alternative='less', writeMode='a', writeFile='mannwhitneyh1.csv')
            if testResult is not None:
                if testResult.pvalue <= levelOfSignificance:
                    significantBins[bin] = testResult.pvalue
                    print('Found a significant H1', dataType, 'bin is', bin, 'p-value', testResult.pvalue)
        except KeyError:
            print(bin, 'was likely not present for both nontor and tor for the Mann-Whitney-U test. Trying next bin')
            continue
            
            
    return significantBins, stats

def makePlotsForH1(nonTor, tor, dataType, ylabel, tilt, title1, title2, potentialClusters, cfg, minThreshold=0.005):


    #Do the hypothesis tests by bin
    significantBins, stats = doHypothesis1Tests(nonTor, tor, dataType, tilt, cfg, potentialClusters=potentialClusters)
    
    
    print('About to make group box plots for', tilt, dataType)    
    makeGroupedBoxPlots(nonTor,\
                        tor,\
                        title1,\
                        ylabel,\
                        'h1',\
                        cfg,\
                        significantBins=significantBins)
    
    print('About to make group line plots for', tilt, dataType)
    makeGroupedLinePlot(nonTor,\
                        tor,\
                        title2,\
                        ylabel,\
                        'h1',\
                        cfg)
    
    if dataType == 'posazshear':
        newNonTor = {}
        newTor = {}

        for bin in list(nonTor.keys()):
            print('Appending nontor', bin, nonTor[bin])
            for value in nonTor[bin]:
                if value >= minThreshold:
                    try:
                        newNonTor[bin].append(value)
                    except KeyError:
                        newNonTor[bin] = [value]
        print('Rebinning for TOR', tor)            
        for bin in list(tor.keys()):
            print('Appending tor', bin, tor[bin])
            for value in tor[bin]:
                if value >= minThreshold:
                    try:
                        newTor[bin].append(value)
                    except KeyError:
                        newTor[bin] = [value]
                    
        title3 = title1 + ' >= '+str(minThreshold)+' s$^{-1}$'
        title4 = title2 + ' >= '+str(minThreshold)+' s$^{-1}$'
        
        newSignificantBins, stats = doHypothesis1Tests(newNonTor, newTor, dataType+'minthresh'+str(minThreshold), tilt, cfg, potentialClusters=potentialClusters)
        
        makeGroupedBoxPlots(newNonTor, newTor, title3, ylabel, 'h1', cfg, significantBins=newSignificantBins)
        makeGroupedLinePlot(newNonTor, newTor, title4, ylabel, 'h1', cfg)
        
        
    return


def cumulativeMannWhitney(cumulativeNonTor, cumulativeTor):
    
    posAzShearResult = stats2.doMannWhitneyU(cumulativeNonTor['posazshear'], cumulativeTor['posazshear'], \
                                            group1Name='NON TOR Cumulative Cyclonic AzShear',\
                                            group2Name='ALL TOR Cumulative Cyclonic AzShear',\
                                            use_continuity=True,\
                                            alternative='less',\
                                            writeMode='a',\
                                            writeFile='cumulativemannwhitney.csv')
                                            
    posVrotResult = stats2.doMannWhitneyU(cumulativeNonTor['posvrot'], cumulativeTor['posvrot'], \
                                            group1Name='NON TOR Cumulative Cyclonic Vrot',\
                                            group2Name='ALL TOR Cumulative Cyclonic Vrot',\
                                            use_continuity=True,\
                                            alternative='less',\
                                            writeMode='a',\
                                            writeFile='cumulativemannwhitney.csv')
                                            
    posSWResult = stats2.doMannWhitneyU(cumulativeNonTor['posspectrumwidth'], cumulativeTor['posspectrumwidth'], \
                                            group1Name='NON TOR Cumulative Cyclonic Spectrum Width',\
                                            group2Name='ALL TOR Cumulative Cyclonic Spectrum Width',\
                                            use_continuity=True,\
                                            alternative='less',\
                                            writeMode='a',\
                                            writeFile='cumulativemannwhitney.csv')
                                            
                                            
    return posAzShearResult, posVrotResult, posSWResult

def hypothesis1(nonTor, tor, dataKey, potentialClusters, cfg):

    """ Creates graphs and figures for testing Hypothesis 1.
        Tests to see if Vrot, AzShear, and spectrum width are different between time-bins for each tilt.
    """
    
    if not cfg.hypo1:
        print('Hypothesis 1 is disabled. Skipping!')
        return
        
    print('Starting h1')
    
    #Start going through each tilt
    for tilt in list(nonTor.keys()):
        if tilt not in list(tor.keys()):
            with open('errors.txt', 'a') as fi:
                fi.write(f"{tilt} not in tor tilts in hypothesis 1")
            print(f"{tilt} tilt not in tor tilts in hypothesis 1")
            continue
        
        #Keep track of the cumulative values for generalized test
        cumulativeNonTor = {'posazshear':[], 'posspectrumwidth':[], 'posvrot':[]}
        cumulativeTor = {'posazshear':[], 'posspectrumwidth':[], 'posvrot':[]}
        #On each tilt loop through the variables and send to the appropriate plotting function
        for dataType,data in nonTor[tilt].items():
        
            if dataType == 'azshear':
            
                title1 = f"All AzShear by Time Bin Tilt {tilt}$^\circ$"
                title2 = f"All AzShear by Time Bin Tilt {tilt}$^\circ$"
                
                #Add potential clusters to the title if needed
                # if potentialClusters:
                    # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    
                    
                makePlotsForH1(nonTor[tilt][dataType], tor[tilt][dataType], dataType, "AzShear (s$^{-1}$)", tilt, title1, title2, potentialClusters, cfg)

            if dataType == 'absshear':
                
                title1 = f"Greater |AzShear| by Time Bin Tilt {tilt}$^\circ$"
                title2 = f"Greater |AzShear| by Time Bin Tilt {tilt}$^\circ$"
                # if potentialClusters:
                    # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    
                makePlotsForH1(nonTor[tilt][dataType], tor[tilt][dataType], dataType, "AzShear (s$^{-1}$)", tilt, title1, title2, potentialClusters, cfg)
                                    
                                    
            if dataType == 'posazshear':
                
                title1 = f"Cyclonic AzShear by Time Bin Tilt {tilt}$^\circ$"
                title2 = f"Cyclonic AzShear by Time Bin Tilt {tilt}$^\circ$"
                
                # if potentialClusters:
                    # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    
                    
                makePlotsForH1(nonTor[tilt][dataType], tor[tilt][dataType], dataType, "AzShear (s$^{-1}$)", tilt, title1, title2, potentialClusters, cfg)
       
                for bin in list(nonTor[tilt][dataType].keys()):
                    cumulativeNonTor['posazshear'].extend(nonTor[tilt][dataType][bin]) 
                for bin in list(tor[tilt][dataType].keys()):
                    cumulativeTor['posazshear'].extend(tor[tilt][dataType][bin])
                
            if dataType == 'vrot':
                
                title1 = f"Automated $V_{{rot}}$ by Time Bin Tilt {tilt}$^\circ$"
                title2 = f"Automated $V_{{rot}}$ by Time Bin Tilt {tilt}$^\circ$"
                
                # if potentialClusters:
                    # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
       
                makePlotsForH1(nonTor[tilt][dataType], tor[tilt][dataType], dataType, "Automated $V_{{rot}}$ (Knots)", tilt, title1, title2, potentialClusters, cfg)
                
            if dataType == 'posvrot':
                
                title1 = f"Automated Cyclonic $V_{{rot}}$ by Time Bin Tilt {tilt}$^\circ$"
                title2 = f"Automated Cyclonic $V_{{rot}}$ by Time Bin Tilt {tilt}$^\circ$"
                
                # if potentialClusters:
                    # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                                       
                makePlotsForH1(nonTor[tilt][dataType], tor[tilt][dataType], dataType, "Automated $V_{{rot}}$ (Knots)", tilt, title1, title2, potentialClusters, cfg)
                
                for bin in list(nonTor[tilt][dataType].keys()):
                    cumulativeNonTor['posvrot'].extend(nonTor[tilt][dataType][bin])
                for bin in list(tor[tilt][dataType].keys()):
                    cumulativeTor['posvrot'].extend(tor[tilt][dataType][bin])
                
            if dataType == 'spectrumwidth':
                
                title1 = f"Spectrum Width by Time Bin Tilt {tilt}$^\circ$"
                title2 = f"Spectrum Width by Time Bin Tilt {tilt}$^\circ$"
                
                # if potentialClusters:
                    # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    
                                    
                makePlotsForH1(nonTor[tilt][dataType], tor[tilt][dataType], dataType, "Spectrum Width (Knots)", tilt, title1, title2, potentialClusters, cfg)
                
            if dataType == 'posspectrumwidth':
                
                title1 = f"Cyclonic Spectrum Width by Time Bin Tilt {tilt}$^\circ$"
                title2 = f"Cyclonic Spectrum Width by Time Bin Tilt {tilt}$^\circ$"
                
                # if potentialClusters:
                    # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    
                makePlotsForH1(nonTor[tilt][dataType], tor[tilt][dataType], dataType, "Spectrum Width (Knots)", tilt, title1, title2, potentialClusters, cfg)
                
                for bin in list(nonTor[tilt][dataType].keys()):
                    cumulativeNonTor['posspectrumwidth'].extend(nonTor[tilt][dataType][bin])
                for bin in list(tor[tilt][dataType].keys()):
                    cumulativeTor['posspectrumwidth'].extend(tor[tilt][dataType][bin])
                
            if dataType == '90thazshear':
            
                title1 = f"Cyclonic 90th-% AzShear by Time Bin Tilt {tilt}$^\circ$"
                title2 = f"Cyclonic 90th-% AzShear by Time Bin Tilt {tilt}$^\circ$"
                
                # if potentialClusters:
                    # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                                    
                makePlotsForH1(nonTor[tilt][dataType], tor[tilt][dataType], dataType, "AzShear (s$^{-1}$)", tilt, title1, title2, potentialClusters, cfg)
                                    
            if dataType == '10thazshear':
            
                title1 = f"Anti-Cyclonic 10th-% AzShear by Time Bin Tilt {tilt}$^\circ$"
                title2 = f"Anti-Cyclonic 10th-% AzShear by Time Bin Tilt {tilt}$^\circ$"
                
                # if potentialClusters:
                    # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                                    
                makePlotsForH1(nonTor[tilt][dataType], tor[tilt][dataType], dataType, "AzShear (s$^{-1}$)", tilt, title1, title2, potentialClusters, cfg)
        
        
        #Perform the Mann-Whitney-U test on the accumulatived variables
        cumulativeMannWhitney(cumulativeNonTor, cumulativeTor)
        
        
    return

def doHypothesis2Tests(tor, torTDS, torNoTDS, dataType, tilt, bin, levelOfSignificance=0.05, potentialClusters=''):

    """ Does the Mann-Whitney-U test for All TORs between EF ratings.
        Also does Mann-Whitney-U test of TDS vs No TDS.    
    """
    
    significantRatings = {}
    stats = {}
    for EF1 in list(tor.keys()):
        
        for EF2 in list(tor.keys()):
            
            if int(EF2) > int(EF1):
                try:
                    testTuple = (EF1, EF2)
                    
                    stats[testTuple] = stats2.calculateStats(tor[EF1], tor[EF2],\
                                                            group1Name='ALL TOR EF '+str(tilt)+' '+str(EF1)+' '+str(dataType)+' '+str(bin)+' pot. clusters '+str(potentialClusters),\
                                                            group2Name='ALL TOR EF '+str(tilt)+' '+str(EF2)+' '+str(dataType)+' '+str(bin)+' pot. clusters '+str(potentialClusters),\
                                                            writeMode='a', writeFile='h2stats.csv')
                                                            
                    testResult = stats2.doMannWhitneyU(tor[EF1], tor[EF2],\
                                                       group1Name='ALL TOR EF '+str(tilt)+' '+str(EF1)+' '+str(dataType)+' '+str(bin)+' pot. clusters '+str(potentialClusters),\
                                                       group2Name='ALL TOR EF '+str(tilt)+' '+str(EF2)+' '+str(dataType)+' '+str(bin)+' pot. clusters '+str(potentialClusters),\
                                                       use_continuity=True, alternative='less', writeMode='a', writeFile='mannwhitneyh2.csv')
                    
                    if testResult is not None:                                   
                        if testResult.pvalue <= float(levelOfSignificance):
                            significantRatings[testTuple] = testResult.pvalue
                            print('Found a significant H2', tilt, dataType,'EFs are', testTuple, 'p-value', testResult.pvalue)
                        
                except KeyError:
                    print('One or more', testTuple, 'EF ratings were not present for the Mann-Whitney-U test in H2. Trying next pair')
                    continue
                    
                    
    #Now repeat the tests for TDS v. NO TDS
    significantTDSRatings = {}
    tdsGroupStats = {}
    
    for EF in list(torNoTDS.keys()):
        
        if EF not in list(torTDS.keys()):
            print('EF', EF, 'is not in TDS for H2 test. Trying next EF.')
            continue
            
        testResult = stats2.doMannWhitneyU(torNoTDS[EF], torTDS[EF],\
                            group1Name=f"TOR NO TDS EF {EF} {tilt} {dataType} {bin}",\
                            group2Name=f"TOR TDS {EF} {tilt} {dataType} {bin}",\
                            alternative='less',\
                            use_continuity=True,\
                            writeMode='a',\
                            writeFile=f"tdsmannwhit{dataType}_{tilt}_{potentialClusters}.csv")
                            
        if testResult is not None:
            if testResult.pvalue <= levelOfSignificance:
                try:
                    significantTDSRatings[EF] = testResult.pvalue
                except KeyError:
                    significantTDSRatings[EF] = testResult.pvalue

    return significantRatings, stats, significantTDSRatings
    
def makePlotsForH2(tor, torTDS, torNoTDS, dataType, ylabel, tilt, bin, title1, potentialClusters, timeBinIncrement):

    significantBins, stats, sigTDSRatings = doHypothesis2Tests(tor, torTDS, torNoTDS, dataType, tilt, bin, potentialClusters=potentialClusters)
    
    makeEFBoxPlots(tor, torTDS, torNoTDS, title1, ylabel, bin, timeBinIncrement, 'h2', significantEFs=sigTDSRatings, significantRatings=significantBins)
    
    return

def hypothesis2(tor, torTDS, torNoTDS, dataKey, potentialClusters, cfg, timeBinIncrement=5):

    """ Provides the starting point for testing Hypothesis 2.
    
        Hypothesis 2 is similar to Hypothesis 1, except for each time/tilt bin, EF ratings are compared. 
        
        
    """
    
    if not cfg.hypo2:
        print('Hypothesis 2 disabled. Skipping!')
        return
        
    print('Starting h2')
    
    for tilt in list(tor.keys()):
        if tilt not in list(torTDS.keys()) or tilt not in list(torNoTDS.keys()):
            with open('errors.txt', 'a') as fi:
                fi.write(f"{tilt} not in tor tilts in hypothesis 2")
            print(f"{tilt} tilt not in tor tilts in hypothesis 2")
            continue
            
            
        for dataType in list(tor[tilt].keys()):
            
            #Since we are looking at things by EF rating at each bin, we need to loop through create graphs at each bin
            
            # print('TOR', tilt, tor[tilt][dataType])
            # print('TDS', tilt, torTDS[tilt][dataType])
            # print('NO TDS', tilt, torNoTDS[tilt][dataType])
                
            for bin in list(tor[tilt][dataType].keys()):
                currentTimeBinTime = str(int(bin)*timeBinIncrement)

                #Test each to determine if there is a bin, if there is not a bin, make it an empty list
                try:
                    if not tor[tilt][dataType][bin]:
                        pass
                except KeyError:
                    print('Changing TOR', tilt, dataType, bin, 'to empty dict/list')
                    tor[tilt][dataType][bin] = {bin:[]}
                try:
                    if not torTDS[tilt][dataType][bin]:
                        pass
                except KeyError:
                    print('Changing TOR TDS', tilt, dataType, bin, 'to empty dict/list')
                    torTDS[tilt][dataType][bin] = {bin:[]}
                
                try:
                    if not torNoTDS[tilt][dataType][bin]:
                        pass
                except KeyError:
                    print('Changing TOR NO TDS', tilt, dataType, bin, 'to empty dict/list')
                    torNoTDS[tilt][dataType][bin] = {bin:[]}
                    
                    
                    
                if dataType == 'azshear':
                    
                    title1 = f"All AzShear by TDS and EF Rating\nTilt {tilt}$^\circ$ at Bin {currentTimeBinTime} Minutes"
                    title2 = f"All AzShear by TDS and EF Rating\nTilt {tilt}$^\circ$ at Bin {currentTimeBinTime} Minutes"
                    
                    # print('ALL SHEAR checkpoint. The length of EF0 at tilt', tilt, 'bin', bin, 'is', len(tor[tilt]['azshear'][bin]['0']))
                    # if potentialClusters:
                        # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        
                    makePlotsForH2(tor[tilt][dataType][bin], torTDS[tilt][dataType][bin], torNoTDS[tilt][dataType][bin],\
                                   dataType, "AzShear (s$^{-1}$)", tilt, bin, title1, potentialClusters, timeBinIncrement)
                                   
                if dataType == 'posazshear':
                    
                    title1 = f"Cyclonic AzShear by TDS and EF Rating\nTilt {tilt}$^\circ$ at Bin {currentTimeBinTime} Minutes"
                    
                    # if potentialClusters:
                        # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        
                    makePlotsForH2(tor[tilt][dataType][bin], torTDS[tilt][dataType][bin], torNoTDS[tilt][dataType][bin],\
                                   dataType, "AzShear (s$^{-1}$)", tilt, bin, title1, potentialClusters, timeBinIncrement)
                                   
                if dataType == 'absshear':
                
                    title1 = f"Greater |AzShear| by TDS and EF Rating\nTilt {tilt}$^\circ$ at Bin {currentTimeBinTime} Minutes"
                    
                    # if potentialClusters:
                        # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        
                        
                    makePlotsForH2(tor[tilt][dataType][bin], torTDS[tilt][dataType][bin], torNoTDS[tilt][dataType][bin],\
                                   dataType, "AzShear (s$^{-1}$)", tilt, bin, title1, potentialClusters, timeBinIncrement)
                                   
                if dataType == 'vrot':
                    
                    title1 = f"Automated $V_{{rot}}$ by TDS and EF Rating\nTilt {tilt}$^\circ$ at Bin {currentTimeBinTime} Minutes"
                    
                    # if potentialClusters:
                        # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        
                    makePlotsForH2(tor[tilt][dataType][bin], torTDS[tilt][dataType][bin], torNoTDS[tilt][dataType][bin],\
                                   dataType, "Automated $V_{{rot}}$ (Knots)", tilt, bin, title1, potentialClusters, timeBinIncrement)
                                   
                if dataType == 'posvrot':
                
                    title1 = f"Cyclonic Automated $V_{{rot}}$ by TDS and EF Rating\nTilt {tilt}$^\circ$ at Bin {currentTimeBinTime} Minutes"
                    
                    # if potentialClusters:
                        # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        
                    makePlotsForH2(tor[tilt][dataType][bin], torTDS[tilt][dataType][bin], torNoTDS[tilt][dataType][bin],\
                                   dataType, "Automated $V_{{rot}}$ (Knots)", tilt, bin, title1, potentialClusters, timeBinIncrement)
                                   
                                   
                
    return
    
def hypothesis3(nonTor, tor, dataKey, testDataTypes, potentialClusters, cfg, levelOfSignificance=0.05):
    
    if not cfg.hypo3:
        print('Hypothesis 3 is disabled. Skipping!')
        return
        
    print('Starting Hypothesis 3')
    
    for dataType in testDataTypes:
    
        if (dataType == 'maxet' or dataType == '90thet') and (dataKey.lower() == 'echo tops' or dataKey.lower() == 'cyclonic case echo tops'):
        
            #Do hypothesis testing
            significantETBins = {}
            etStats  = {}
            
            for bin in list(nonTor[dataType].keys()):
                
                if bin not in list(tor[dataType].keys()):
                    print('Bin', bin, dataType, 'not in tor for h3 ET. Trying next bin')
                    continue
                    
                underDataKey = dataKey.replace(' ', '_')
                
                testResult = stats2.doMannWhitneyU(nonTor[dataType][bin], tor[dataType][bin],\
                                                   group1Name=f"NON TOR {dataKey} {dataType} {bin} {potentialClusters}",\
                                                   group2Name=f"TOR {dataKey} {dataType} {bin} {potentialClusters}",\
                                                   alternative='two-sided',\
                                                   use_continuity=True,\
                                                   writeMode='a',\
                                                   writeFile=f"{underDataKey}_{dataType}_{potentialClusters}_mannwhit.csv")
                                                   
                etStats[str(bin)] = stats2.calculateStats(nonTor[dataType][bin], tor[dataType][bin],\
                                                   group1Name=f"NON TOR {dataKey} {dataType} {bin} {potentialClusters}",\
                                                   group2Name=f"TOR {dataKey} {dataType} {bin} {potentialClusters}",\
                                                   writeMode='a',\
                                                   writeFile=f"{underDataKey}_{dataType}_{potentialClusters}_stats.csv")
            
                if testResult is not None:
                    if testResult.pvalue <= levelOfSignificance:
                        significantETBins[str(bin)] = testResult.pvalue
                        
            
            title1 = ''
            if dataKey.lower() == 'cyclonic case echo tops':
                title1 += f"Cyclonic Case "
            if dataType == 'maxet':
                title1 += f"Maximum 20-dBZ Echo Tops by Time Bin"
            elif dataType == '90thet':
                title1 += f"90th% 20-dBZ Echo Tops by Time Bin"
                
            # if potentialClusters:
                # title1 += f" <= {potentialClusters} Pot. Clusters"
            
            print('Found significant ET bins', significantETBins)
            
            #Make sure bins are strings to be consistant with the plotting functions
            nonTorInput = {str(bin):value for bin, value in nonTor[dataType].items()}
            torInput = {str(bin):value for bin, value in tor[dataType].items()}
            
            makeGroupedBoxPlots(nonTorInput, torInput, title1, "Echo Tops (ft)", 'h3', cfg, significantBins=significantETBins)
            makeGroupedLinePlot(nonTorInput, torInput, title1, "Echo Tops (ft)", 'h3', cfg) 
        
        #Currently holding off on the VCP stuff
        if (dataType == 'maxet' or dataType == '90thet') and dataKey.lower() == 'echo tops by vcp':
            
            significantETVCPBins = {}
            
            for bin in list(nonTor[dataType].keys()):
                
                if bin not in list(tor[dataType].keys()):
                    print('Bin', bin, dataType,  'not in tor for h3 ET VCP. Trying next bin.')
                    continue
                
                for VCP in list(nonTor[dataType][bin].keys()):
                    
                    if VCP not in list(tor[dataType][bin].keys()):
                        print('VCP', VCP, 'not in tors for h3 ET VCP. Trying next VCP')
                        
                    underDataKey = dataKey.replace(' ', '_')
                    
                    testResult = stats2.doMannWhitneyU(nonTor[dataType][bin], tor[dataType][bin],\
                                                       group1Name=f"NON TOR {dataKey} {dataType} {bin} {VCP} {potentialClusters}",\
                                                       group2Name=f"TOR {dataKey} {dataType} {bin} {VCP} {potentialClusters}",\
                                                       alternative='two-sided',\
                                                       use_continuity=True,\
                                                       writeMode='a',\
                                                       writeFile=f"{underDataKey}_{dataType}_{bin}_{potentialClusters}_{VCP}_mannwhit.csv")
                
                    if testResult is not None:
                        if testResult.pvalue <= levelOfSignificance:
                            significantETVCPBins[bin] = testResult.pvalue
                            
        if (dataType == 'maxvil' or dataType == 'avgvil' or dataType == 'maxref') and (dataKey.lower() == 'storm data' or dataKey.lower() == 'cyclonic case storm data'):
            
            significantTrackBins = {}
            trackStats = {}
            
            for bin in list(nonTor[dataType].keys()):
                
                if bin not in list(tor[dataType].keys()):
                    print('Bin', bin, dataType, 'not in tor for h3 Track data. Trying next bin')
                    continue
                
                underDataKey = dataKey.replace(' ', '_')
                
                testResult = stats2.doMannWhitneyU(nonTor[dataType][bin], tor[dataType][bin],\
                                                       group1Name=f"NON TOR {dataKey} {dataType} {bin} {potentialClusters}",\
                                                       group2Name=f"TOR {dataKey} {dataType} {bin} {potentialClusters}",\
                                                       alternative='two-sided',\
                                                       use_continuity=True,\
                                                       writeMode='a',\
                                                       writeFile=f"{underDataKey}_{dataType}_{potentialClusters}_mannwhit.csv")
                                                       
                trackStats[str(bin)] = stats2.calculateStats(nonTor[dataType][bin], tor[dataType][bin],\
                                                       group1Name=f"NON TOR {dataKey} {dataType} {bin} {potentialClusters}",\
                                                       group2Name=f"TOR {dataKey} {dataType} {bin} {potentialClusters}",\
                                                       writeMode='a',\
                                                       writeFile=f"{underDataKey}_{dataType}_{potentialClusters}_stats.csv")                                       
                if testResult is not None:
                    if testResult.pvalue <= levelOfSignificance:
                        significantTrackBins[str(bin)] = testResult.pvalue
            
            title1 = ''
            ylabel = ''
            if dataKey.lower() == 'cyclonic case storm data':
                title1 += f"Cyclonic Case "
            if dataType == 'maxvil':
                title1 += f"Maximum VIL by Time Bin"
                ylabel = f"VIL (kg $m^{{-2}}$)"
            elif dataType == 'avgvil':
                title1 += f"Average VIL by Time Bin"
                ylabel = f"VIL (kg $m^{{-2}}$)"
            elif dataType == 'maxref':
                title1 += f"Maximum Composite Reflectivity by Time Bin"
                ylabel = f"Composite Reflectivity (dBZ)"
                
            # if potentialClusters:
                # title1 += f" <= {potentialClusters} Pot. Clusters"
                
            #Make sure bins are string to be consistant with the plotting functions
            nonTorInput = {str(bin):value for bin, value in nonTor[dataType].items()}
            torInput = {str(bin):value for bin, value in tor[dataType].items()}
            
            print('H3 Sig bins', dataType, significantTrackBins)
            makeGroupedBoxPlots(nonTorInput, torInput, title1, ylabel, 'h3', cfg, significantBins=significantTrackBins)
            makeGroupedLinePlot(nonTorInput, torInput, title1, ylabel, 'h3', cfg)
                
            
    return
    
def getIncrementalBins(data):

    """ Goes through the trend tuples and return which ones are incremental (e.g., -2 to -1, 0 to 1, 2 to 3, etc.) """
    
    incrementalBins = {}
    
    for trendTuple in list(data.keys()):
        if int(trendTuple[1]) == (int(trendTuple[0])+1):
            incrementalBins[trendTuple] = copy.deepcopy(data[trendTuple])
            
    return incrementalBins
    
    
def getTrendsForGreater(data, startingBin):

    """ Creates a group from trends each starting from the starting bin.
        For example, if startingBin is -2, the trends that are returned are (-2, -1), (-2, 0), (-2, 1), (-2, 2), (-2, 3), etc.
    """
    
    binGroup = {}
    
    for trendTuple in list(data.keys()):
        if int(trendTuple[0]) == int(startingBin) and int(trendTuple[1]) > int(startingBin) and trendTuple not in list(binGroup.keys()):
            binGroup[trendTuple] = copy.deepcopy(data[trendTuple])
    
    return binGroup


def doHypothesis4Tests(nonTorInc, nonTorGreater, torInc, torGreater, tilt, dataKey, dataType, potentialClusters, levelOfSignificance=0.05):

    """ Does the Wilcoxon-sign-rank test between tor and nontor trends in each group."""
    
    #Only really need to do stats on the "Greater" trends as doing them on the incremental trends would be redundant.
    #Just testing to see if the trends are significantly different than 0
    
    sigNonTorTrends = {}
    sigTorTrends = {} #Trends that are significant, not significant tornadoes
    
    nonTorStats = {}
    
    for startingBin in sorted(list(nonTorGreater.keys())):
        
        for trendTuple in list(nonTorGreater[startingBin].keys()):
            
            dataname1 = 'Data '+str(dataKey)+' '+str(tilt)+' '+str(dataType)+' sb '+str(startingBin)+' tt '+str(trendTuple).replace(',', '')+' pot. clusters'+str(potentialClusters)
            testResult = stats2.doWilcoxon(nonTorGreater[startingBin][trendTuple],\
                                            dataName=dataname1,\
                                            correction=True,\
                                            writeMode='a', writeFile='h4nontorwilcoxon'+str(tilt)+'.csv')
                                            
                                            
            currentNonTorStats = stats2.calculateGroupStats(nonTorGreater[startingBin][trendTuple])
            
            try:
                currentNonTorStats[startingBin][trendTuple] = currentNonTorStats
            except KeyError:
                currentNonTorStats[startingBin] = {trendTuple:currentNonTorStats}
                
            stats2.writeSingleStats(currentNonTorStats, dataname1, 'a', os.path.join('stats', 'h4nontorstats'+str(tilt)+'.csv'))
             
            if testResult is not None:
                if testResult.pvalue <= levelOfSignificance:
                    try:
                        sigNonTorTrends[startingBin][trendTuple] = testResult.pvalue
                    except KeyError:
                        sigNonTorTrends[startingBin] = {trendTuple:testResult.pvalue}
                    
    torStats = {}                                        
    #Repeat for tornadic cases
    for startingBin in sorted(list(torGreater.keys())):
    
        for trendTuple in list(torGreater[startingBin].keys()):
            
            dataname2 = 'Data '+str(dataKey)+' '+str(tilt)+' '+str(dataType)+' sb '+str(startingBin)+' tt '+str(trendTuple).replace(',', '')+' pot. clusters'+str(potentialClusters)
            testResult = stats2.doWilcoxon(torGreater[startingBin][trendTuple],\
                                           dataName=dataname2,\
                                           correction=True,\
                                           writeMode='a', writeFile='h4torwilcoxon'+str(tilt)+'.csv')
                                           
            
            currentTorStats = stats2.calculateGroupStats(torGreater[startingBin][trendTuple])
            
            
            try:
                torStats[startingBin][trendTuple] = currentTorStats
            except KeyError:
                torStats[startingBin] = {trendTuple:currentTorStats}
                
            stats2.writeSingleStats(currentTorStats, dataname2, 'a', os.path.join('stats', 'h4torstats'+str(tilt)+'.csv'))
            
            if testResult is not None:
                if testResult.pvalue <= levelOfSignificance:
                    try:
                        sigTorTrends[startingBin][trendTuple] = testResult.pvalue
                    except KeyError:
                        sigTorTrends[startingBin] = {trendTuple:testResult.pvalue}
                    
    print('Found significant nontor trends', sigNonTorTrends)
    print('Found significant tor trends', sigTorTrends)
    
    trendSignificantBins = {}
    trendSignificantStats = {}
    
    #Now do the Mann-Whitney-U test on the two distributions at each bin
    for startingBin in sorted(list(nonTorGreater.keys())):
        
        if startingBin not in list(torGreater.keys()):
            print('H4 MWU does not have a common starting bin', startingBin, '. Trying next bin.')
            continue
            
        for trendTuple in list(nonTorGreater[startingBin].keys()):
        
            if trendTuple not in list(torGreater[startingBin].keys()):
                print('H4 MWU does not have a common trend tuple', trendTuple, '. Trying next tuple.')
                continue
            
            if type(tilt) is tuple:
                tilt = ''
            
            
            testResult = stats2.doMannWhitneyU(nonTorGreater[startingBin][trendTuple], torGreater[startingBin][trendTuple],\
                                               group1Name=f"NON TOR {dataKey} {dataType} {tilt} sb {startingBin} tt {str(trendTuple).replace(',','').replace(' ', '-')} pot. clusters {potentialClusters}",\
                                               group2Name=f"TOR {dataKey} {dataType} {tilt} sb {startingBin} tt {str(trendTuple).replace(',','').replace(' ', '-')} pot. clusters {potentialClusters}",\
                                               use_continuity=True,\
                                               alternative='two-sided',\
                                               writeMode='a',\
                                               writeFile=f"{dataKey}_{dataType}_{tilt}_{potentialClusters}_mannwhitneyh4.csv")
            
            currentStats = stats2.calculateStats(nonTorGreater[startingBin][trendTuple], torGreater[startingBin][trendTuple],\
                                               group1Name=f"NON TOR {dataKey} {dataType} {tilt} sb {startingBin} tt {str(trendTuple).replace(',','').replace(' ', '-')} pot. clusters {potentialClusters}",\
                                               group2Name=f"TOR {dataKey} {dataType} {tilt} sb {startingBin} tt {str(trendTuple).replace(',','').replace(' ', '-')} pot. clusters {potentialClusters}",\
                                               writeMode='a', writeFile= f"{dataKey}_{dataType}_{tilt}_statsh4.csv")
            if testResult is not None:
                if testResult.pvalue <= levelOfSignificance:
                    try:
                        trendSignificantBins[startingBin][trendTuple] = testResult.pvalue
                    except KeyError:
                        trendSignificantBins[startingBin] = {trendTuple:testResult.pvalue}
                        
                                               
            try:
                trendSignificantStats[startingBin][trendTuple] = currentStats
            except KeyError:
                trendSignificantStats[startingBin] = {trendTuple:currentStats}
                
    print('Found significant between cateogry trends', trendSignificantBins)
    
    
    
    return sigNonTorTrends, nonTorStats, sigTorTrends, torStats, trendSignificantBins, trendSignificantStats

def getSortedBinList(group1, group2):
        
    """ Returns the total number of bins in groups 1 and 2 """
    
    totalAccumulatedBins = []
    
    for bin in list(group1.keys()):
        if bin not in totalAccumulatedBins:
            totalAccumulatedBins.append(bin)
            
    for bin2 in list(group2.keys()):
        if bin2 not in totalAccumulatedBins:
            totalAccumulatedBins.append(bin2)
            
    return sorted(totalAccumulatedBins)
    
    
def hypothesis4(nonTor, tor, dataKey, testDataTypes, potentialClusters, cfg, timeIncrement=5):

    """ Serves as the launching point for testing the temporal trends. Can be called multiple times. Varies based on dataKey.
    
    """
    
    if not cfg.hypo4:
        print('Hypothesis 4 is disabled. Skipping!')
        return
        
        
    print('Starting h4')
    stopAfter1 = False #If we're dealing with storm attributes rather than AzShear clusters, the "tilts" are actually the data types and we'll want to 
                       #stop after 1 tilt.
    for tilt in list(nonTor.keys()):
        
        if tilt not in list(tor.keys()):
            with open('errors.txt', 'a') as fi:
            
                fi.write(f"{tilt} not in tor tilts in hypothesis 4")
                
            print(f"{tilt} not in tor tilts in hypothesis 4")
            
        
        
        nonTorIncTrends = {}
        nonTorGreaterTrends = {}
        torIncTrends = {}
        torGreaterTrends = {}
            
        
        for dataType in testDataTypes:
                
             #Put the data into their trend-tuple bins for the boxplots
            if dataKey.lower() == 'echo top trends' or dataKey.lower() == 'storm data trends' or dataKey.lower() == 'cyclonic case echo top trends' or\
                dataKey.lower() == 'cyclonic case storm data trends':
                
                #Only do 1 pass through the tilt loop and set tilt to empty string
                stopAfter1 = True
                tilt = ''
                
                try:
                
                    nonTorIncTrends = getIncrementalBins(nonTor[dataType])
                    print('Created nontor incremental trends', nonTorIncTrends, 'for', dataKey, dataType)
                    
                    bins = []
                    for trendTuple in sorted(list(nonTor[dataType].keys())):
                        if trendTuple[0] not in bins:
                            bins.append(trendTuple[0])
                            
                    for bin in bins:
                        nonTorGreaterTrends[bin] = getTrendsForGreater(nonTor[dataType], bin)
                        
                    print('Created nontor greater trends', nonTorGreaterTrends, 'for', dataKey, dataType)
                except KeyError:
                    print(dataKey, dataType, 'was not available for nontor trend sorting. Setting to empty list')
                    print('Keys and items', nonTor[dataType].keys(), nonTor[dataType])
                    nonTor[dataType] = []
                    
                    
                try:
                    torIncTrends = getIncrementalBins(tor[dataType])
                    print('Created tor incremental trends', torIncTrends, 'for', dataKey, dataType)
                    
                    bins = []
                    for trendTuple in sorted(list(tor[dataType].keys())):
                        if trendTuple[0] not in bins:
                            bins.append(trendTuple[0])
                            
                    for bin in bins:
                        torGreaterTrends[bin] = getTrendsForGreater(tor[dataType], bin)
                        
                    print('Created tor greater trends', torGreaterTrends, 'for', dataKey, dataType)
                    
                except KeyError:
                    print(dataKey, dataType, 'was not available for tor trend sorting. Setting to empty list')
                    print('Keys and items', tor[dataType].keys(), tor[dataType])
                    tor[dataType] = []
                    
                    
            else:    
                try:
                    nonTorIncTrends = getIncrementalBins(nonTor[tilt][dataType])
                    print('Created nontor incremental trends', nonTorIncTrends, 'for', tilt, dataType)
                    
                    #Create a list of bins
                    bins = []
                    for trendTuple in sorted(list(nonTor[tilt][dataType].keys())):
                        if trendTuple[0] not in bins:
                            bins.append(trendTuple[0])
                    
                    for bin in bins:
                        nonTorGreaterTrends[bin] = getTrendsForGreater(nonTor[tilt][dataType], bin)
                        
                    print('Created nontor greater trends', nonTorGreaterTrends, 'for', tilt, dataType)
                except KeyError:
                    print(tilt, dataType, 'was not available for nontor trend sorting. Setting to empty list')
                    nonTor[tilt][dataType] = []
                
                
                try:
                    torIncTrends = getIncrementalBins(tor[tilt][dataType])
                    print('Created tor incremental trends', torIncTrends, 'for', tilt, dataType)
                    
                    bins = []
                    for trendTuple in sorted(list(tor[tilt][dataType].keys())):
                        if trendTuple[0] not in bins:
                            bins.append(trendTuple[0])
                            
                    for bin in bins:
                        torGreaterTrends[bin] = getTrendsForGreater(tor[tilt][dataType], bin)
                        
                    print('Created tor greater trends', torGreaterTrends, 'for', tilt, dataType)
                    
                except KeyError:
                    print(tilt, dataType, 'was not available for tor trend sorting. Setting to empty list')
                    tor[tilt][dataType] = []
                    
                
                    
            sigNonTorTrend, nonTorStats, sigTorTrends, torStats, trendSignificantBins, trendSignificantStats = doHypothesis4Tests(nonTorIncTrends, nonTorGreaterTrends,\
                                                                                        torIncTrends, torGreaterTrends, tilt, \
                                                                                        dataKey, dataType, potentialClusters) 
                                                                                    
            sortedBinList = getSortedBinList(nonTorGreaterTrends, torGreaterTrends)
            
            #Start by making a title and calling make-figure functions
            if dataType == 'azshear':
                title1 = f"All AzShear Incremental Trends Tilt {tilt}$^\circ$"
                title2 = f"All AzShear Trends Tilt {tilt}$^\circ$"
                
                # if potentialClusters:
                    # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    
                    
                makeIncrementalTrendBoxPlots(nonTorIncTrends, torIncTrends, title1, "$\Delta$AzShear (s$^{-1}$)", timeIncrement, 'h4',\
                                            cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                            trendSignificantBins=trendSignificantBins)
                
                for bin in sortedBinList:
                    if bin in list(nonTorGreaterTrends.keys()):
                        nonTorTrends = nonTorGreaterTrends[bin]
                    else:
                        nonTorTrends = {}
                        
                    if bin in list(torGreaterTrends.keys()):
                        torTrends = torGreaterTrends[bin]
                    else:
                        torTrends = {}
                        
                    makeGreaterTrendBoxPlots(nonTorTrends, torTrends, title2, "$\Delta$AzShear (s$^{-1}$)", bin, timeIncrement, 'h4',\
                                            cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                            trendSignificantBins=trendSignificantBins)
                    
            if dataType == 'posazshear':
                title1 = f"Cyclonic AzShear Incremental Trends Tilt {tilt}$^\circ$"
                title2 = f"Cyclonic AzShear Trends Tilt {tilt}$^\circ$"
                
                # if potentialClusters:
                    # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    
                    
                makeIncrementalTrendBoxPlots(nonTorIncTrends, torIncTrends, title1, "$\Delta$AzShear (s$^{-1}$)", timeIncrement, 'h4',\
                                            cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                            trendSignificantBins=trendSignificantBins)
                
                for bin in sortedBinList:
                
                    if bin in list(nonTorGreaterTrends.keys()):
                        nonTorTrends = nonTorGreaterTrends[bin]
                    else:
                        nonTorTrends = {}
                        
                    if bin in list(torGreaterTrends.keys()):
                        torTrends = torGreaterTrends[bin]
                    else:
                        torTrends = {}
                        
                    makeGreaterTrendBoxPlots(nonTorTrends, torTrends, title2, "$\Delta$AzShear (s$^{-1}$)", bin, timeIncrement, 'h4',\
                                            cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                            trendSignificantBins=trendSignificantBins)
                    
                    
            if dataType == 'absazshear':
                title1 = f"Greater |AzShear| Trends Incremental for Tilt {tilt}$^\circ$"
                title2 = f"Greater |AzShear| Trends for Tilt {tilt}$^\circ$"
                
                # if potentialClusters:
                    # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    
                    
                makeIncrementalTrendBoxPlots(nonTorIncTrends, torIncTrends, title1, "$\Delta$AzShear (s$^{-1}$)", timeIncrement, 'h4',\
                                            cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                            trendSignificantBins=trendSignificantBins)
                
                for bin in sortedBinList:
                
                    if bin in list(nonTorGreaterTrends.keys()):
                        nonTorTrends = nonTorGreaterTrends[bin]
                    else:
                        nonTorTrends = {}
                        
                    if bin in list(torGreaterTrends.keys()):
                        torTrends = torGreaterTrends[bin]
                    else:
                        torTrends = {}
                        
                    makeGreaterTrendBoxPlots(nonTorTrends, torTrends, title2, "$\Delta$AzShear (s$^{-1}$)", bin, timeIncrement, 'h4',\
                                             cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                             trendSignificantBins=trendSignificantBins)
                    
            if dataType == '90thazshear':
                title1 = f"90th% AzShear Trends Incremental Tilt {tilt}$^\circ$"
                title2 = f"90th% AzShear Trends Tilt {tilt}$^\circ$"
                
                # if potentialClusters:
                    # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    
                    
                makeIncrementalTrendBoxPlots(nonTorIncTrends, torIncTrends, title1, "$\Delta$AzShear (s$^{-1}$)", timeIncrement, 'h4',\
                                            cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                            trendSignificantBins=trendSignificantBins)
                
                for bin in sortedBinList:
                
                    if bin in list(nonTorGreaterTrends.keys()):
                        nonTorTrends = nonTorGreaterTrends[bin]
                    else:
                        nonTorTrends = {}
                        
                    if bin in list(torGreaterTrends.keys()):
                        torTrends = torGreaterTrends[bin]
                    else:
                        torTrends = {}
                        
                    makeGreaterTrendBoxPlots(nonTorTrends, torTrends, title2, "$\Delta$AzShear (s$^{-1}$)", bin, timeIncrement, 'h4',\
                                             cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                             trendSignificantBins=trendSignificantBins)
                                             
            if dataType == 'vrot':
                title1 = f"Automated $V_{{rot}}$ Incremental Trends Tilt {tilt}$^\circ$"
                title2 = f"Automated $V_{{rot}}$ Trends Tilt {tilt}$^\circ$"
                
                # if potentialClusters:
                    # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    
                    
                makeIncrementalTrendBoxPlots(nonTorIncTrends, torIncTrends, title1, "$\Delta$ Automated $V_{{rot}}$ (Knots)", timeIncrement, 'h4',\
                                             cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                             trendSignificantBins=trendSignificantBins)
                
                for bin in sortedBinList:
                
                    if bin in list(nonTorGreaterTrends.keys()):
                        nonTorTrends = nonTorGreaterTrends[bin]
                    else:
                        nonTorTrends = {}
                        
                    if bin in list(torGreaterTrends.keys()):
                        torTrends = torGreaterTrends[bin]
                    else:
                        torTrends = {}
                        
                    makeGreaterTrendBoxPlots(nonTorTrends, torTrends, title2, "$\Delta$ Automated $V_{{rot}}$ (Knots)", bin, timeIncrement, 'h4',\
                                             cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                             trendSignificantBins=trendSignificantBins)
                    
            if dataType == 'posvrot':
                title1 = f"Cyclonic Incremental Automated $V_{{rot}}$ Trends Tilt {tilt}$^\circ$"
                title2 = f"Cyclonic Automated $V_{{rot}}$ Trends Tilt {tilt}$^\circ$"
                
                # if potentialClusters:
                    # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    
                
                        
                makeIncrementalTrendBoxPlots(nonTorIncTrends, torIncTrends, title1, "$\Delta$ Automated $V_{{rot}}$ (Knots)", timeIncrement, 'h4',\
                                             cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                             trendSignificantBins=trendSignificantBins)
                
                for bin in sortedBinList:
                
                    if bin in list(nonTorGreaterTrends.keys()):
                        nonTorTrends = nonTorGreaterTrends[bin]
                    else:
                        nonTorTrends = {}
                        
                    if bin in list(torGreaterTrends.keys()):
                        torTrends = torGreaterTrends[bin]
                    else:
                        torTrends = {}
                        
                    makeGreaterTrendBoxPlots(nonTorTrends, torTrends, title2, "$\Delta$ Automated $V_{{rot}}$ (Knots)", bin, timeIncrement, 'h4',\
                                            cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                            trendSignificantBins=trendSignificantBins)
                    
            if dataType == 'spectrumwidth':
                title1 = f"Spectrum Width Incremental Trends Tilt {tilt}$^\circ$"
                title2 = f"Spectrum Width Trends Tilt {tilt}$^\circ$"
                
                # if potentialClusters:
                    # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
 
 
                makeIncrementalTrendBoxPlots(nonTorIncTrends, torIncTrends, title1, "$\Delta$Spectrum Width (Knots)", timeIncrement, 'h4',\
                                            cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                            trendSignificantBins=trendSignificantBins)
                
                for bin in sortedBinList:
                
                    if bin in list(nonTorGreaterTrends.keys()):
                        nonTorTrends = nonTorGreaterTrends[bin]
                    else:
                        nonTorTrends = {}
                        
                    if bin in list(torGreaterTrends.keys()):
                        torTrends = torGreaterTrends[bin]
                    else:
                        torTrends = {}
                        
                    makeGreaterTrendBoxPlots(nonTorTrends, torTrends, title2, "$\Delta$Spectrum Width (Knots)", bin, timeIncrement, 'h4',\
                                            cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                            trendSignificantBins=trendSignificantBins)
                    
            if dataType == 'posspectrumwidth':
                title1 = f"Cyclonic Spectrum Width Incremental Trends Tilt {tilt}$^\circ$"
                title2 = f"Cyclonic Spectrum Width Trends Tilt {tilt}$^\circ$"
                
                # if potentialClusters:
                    # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                    
                    
                makeIncrementalTrendBoxPlots(nonTorIncTrends, torIncTrends, title1, "$\Delta$Spectrum Width (Knots)", timeIncrement, 'h4',\
                                            cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                            trendSignificantBins=trendSignificantBins)
                
                for bin in sortedBinList:
                
                    if bin in list(nonTorGreaterTrends.keys()):
                        nonTorTrends = nonTorGreaterTrends[bin]
                    else:
                        nonTorTrends = {}
                        
                    if bin in list(torGreaterTrends.keys()):
                        torTrends = torGreaterTrends[bin]
                    else:
                        torTrends = {}
                        
                    makeGreaterTrendBoxPlots(nonTorTrends, torTrends, title2, "$\Delta$Spectrum Width (Knots)", bin, timeIncrement, 'h4',\
                                            cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                            trendSignificantBins=trendSignificantBins)
                
            if dataKey.lower() == 'echo top trends' or dataKey.lower() == 'cyclonic case echo top trends':
            
                if dataType == 'maxet' or dataType == '90thet':
                    title1 = ''
                    title2  = ''
                    ylabel = ''
                    
                    if dataKey.lower() == 'cyclonic case echo top trends':
                        title1 += f"Cyclonic Cases "
                        title2 += f"Cyclonic Cases "
                        
                    if dataType == 'maxet':
                        title1 += f"Maximum 20-dBZ Echo-Top Incremental Trends"
                        title2 += f"Maximum 20-dBZ Echo-Top Trends"
                        ylabel = f"$\Delta$Echo Tops (ft)"
                    elif dataType == '90thet':
                        title1 += f"90th% 20-dBZ Echo-Top Incremental Trends"
                        title2 += f"90th% 20-dBZ Echo-Top Trends"
                        ylabel = f"$\Delta$Echo Tops (ft)"
                        
                    # if potentialClusters:
                        # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        
                    print('About to make ET plots', nonTorIncTrends, torIncTrends)
                    makeIncrementalTrendBoxPlots(nonTorIncTrends, torIncTrends, title1, ylabel, timeIncrement, 'h4',\
                                                cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                                trendSignificantBins=trendSignificantBins)
                                                
                                                
                    for bin in sortedBinList:
                    
                        if bin in list(nonTorGreaterTrends.keys()):
                            nonTorTrends = nonTorGreaterTrends[bin]
                        else:
                            nonTorTrends = {}
                            
                        if bin in list(torGreaterTrends.keys()):
                            torTrends = torGreaterTrends[bin]
                        else:
                            torTrends = {}
                            
                        makeGreaterTrendBoxPlots(nonTorTrends, torTrends, title2, ylabel, bin, timeIncrement, 'h4',\
                                                cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                                trendSignificantBins=trendSignificantBins)
                                                
            if dataKey.lower() == 'storm data trends' or dataKey.lower() == 'cyclonic case storm data trends':
            
                if dataType == 'maxvil' or dataType == 'avgvil' or dataType == 'maxref':
                
                    title1 = ''
                    title2  = ''
                    ylabel = ''
                    
                if dataKey.lower() == 'cyclonic case storm data trends':
                    title1 += f"Cyclonic Cases "
                    title2 += f"Cyclonic Cases "
                    
                if dataType == 'maxvil':
                    title1 += f"Maximum VIL Incremental Trends"
                    title2 += f"Maximum VIL Trends"
                    ylabel = f"$\Delta$ VIL (kg $m^{{-2}}$)"
                elif dataType == 'avgvil':
                    title1 += f"Average VIL Incremental Trends"
                    title2 += f"Average VIL Trends"
                    ylabel = f"$\Delta$ VIL (kg $m^{{-2}}$)"
                elif dataType == 'maxref':
                    title1 += f"Maximum Composite Reflectivity Incremental Trends"
                    title2 += f"Maximum Composite Reflectivity Trends"
                    ylabel = f"$\Delta$ Composite Reflectivity (dBZ)"
                    
                # if potentialClusters:
                        # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        
                makeIncrementalTrendBoxPlots(nonTorIncTrends, torIncTrends, title1, ylabel, timeIncrement, 'h4',\
                                                cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                                trendSignificantBins=trendSignificantBins)
                                                
                                                
                for bin in sortedBinList:
                
                    if bin in list(nonTorGreaterTrends.keys()):
                        nonTorTrends = nonTorGreaterTrends[bin]
                    else:
                        nonTorTrends = {}
                        
                    if bin in list(torGreaterTrends.keys()):
                        torTrends = torGreaterTrends[bin]
                    else:
                        torTrends = {}
                        
                    makeGreaterTrendBoxPlots(nonTorTrends, torTrends, title2, ylabel, bin, timeIncrement, 'h4',\
                                            cfg, nonTorSignificantBins=sigNonTorTrend, torSignificantBins=sigTorTrends,\
                                            trendSignificantBins=trendSignificantBins)
                    
                    
                    
                        
        if stopAfter1:
            break
            
            
    return
    
def unpackTSS(tssData):

    """ Return a list of TSS data """
    
    tssValues = []
    tssThresholds = []
    farValues = []
    podValues = []
    csiValues = []
    
    for tss in tssData:
        if tss[1] is not None:
            tssValues.append(tss[1]['TSS'])
            tssThresholds.append(tss[1]['threshold'])
            farValues.append(tss[1]['far'])
            podValues.append(tss[1]['pod'])
            csiValues.append(tss[1]['CSI'])
            
            
    return tssValues, farValues, podValues, csiValues, tssThresholds
    
    
def hypothesis5(nonTor, tor, torTDS, torNoTDS, dataKey, testDataTypes, potentialClusters, cfg, realWarningStats, timeIncrement=5, label='',\
                specificBins=None):

    """ Calculates TSS for each tilt and bin and make plots for TSS by threshold and values by range """
    
    if not cfg.hypo5:
        print('Hypothesis 5 is disabled. Skipping!')
        return
        
        
    print('Starting h5', label)
    
    if label:
        label += ' '
    
    for tilt in list(nonTor.keys()):
        
        if tilt not in list(tor.keys()):
            
            with open('errors.txt', 'a') as fi:
                
                fi.write(f"{tilt} not in tor tilts in hypothesis 5", label)
                
            print(f"{tilt} not in tor tilts in hypothesis 5", label)
            
        #Calculate the TSS data and determine the best thresholds up here to make things consistent
        
        vrotTSSData = {}
        posvrotTSSData = {}
        vrotBestThresholds = {}
        topvrotTSSData = {}
        posvrotBestThresholds = {}
        topvrotBestThresholds = {}
        
        for bin in list(nonTor[tilt]['vrot'].keys()):
                    
            if bin not in list(tor[tilt]['vrot'].keys()):
                print('Bin', bin, 'not in the keys for tor in H5 vrot. Trying next bin', label)
                continue
            
            if specificBins:
                if int(bin) not in specificBins:
                    continue
                    
            vrotTSSData[bin] = stats2.calculateVrotTSS(nonTor[tilt]['vrot'][bin], tor[tilt]['vrot'][bin], adjustRanges=[40],\
                                                                rangeAdjustValues=[-5], writeMode='a', writeFile=label.replace(' ', '_')+'vrot_'+str(tilt)+'_tss.csv',\
                                                                group1Name=label+'NON TOR vrot bin '+str(bin)+" tilt "+str(tilt),\
                                                                group2Name=label+'TOR vrot bin '+str(bin)+" tilt "+str(tilt))
                                                                
            #We need to make sure we calculate and record the stats using M17 criteria to compare 
            vrotMartinaitisTSS = stats2.calculateTSSRange(nonTor[tilt]['vrot'][bin], tor[tilt]['vrot'][bin], 20,\
                                                    adjustRanges=[40], rangeAdjustValues=[-5])
                                                    
            vrotTSSValues, vrotFarValues, vrotPodValues, vrotCSIValues, vrotThresholds = unpackTSS(vrotTSSData[bin])
            vrotBestTSS, vrotBestTSSIndex = stats2.getMaximumTSS(vrotTSSValues)
            if vrotBestTSSIndex is None:
                print('Warning! A None vrotBestTSSIndex was found. Setting values to slightly negative.')
                vrotBestThresholds[bin] = None
                vrotSkills = {'far':-0.05, 'pod':-0.05, 'CSI':-0.05}
            else:
                vrotBestThresholds[bin] = vrotThresholds[vrotBestTSSIndex]
                vrotSkills = {'far':vrotFarValues[vrotBestTSSIndex], 'pod':vrotPodValues[vrotBestTSSIndex], 'CSI':vrotCSIValues[vrotBestTSSIndex]}
            
            
            stats2.writeTSS([(20, vrotMartinaitisTSS)], label+'M17 NON TOR '+str('vrot')+" bin "+str(bin)+" tilt "+str(tilt),\
                            label+'M17 TOR '+str('vrot')+" bin "+str(bin)+" tilt "+str(tilt),\
                            [40], [-5], 'a', os.path.join('stats', label.replace(' ', '_')+'vrot'+'_'+str(tilt)+'_m17tss.csv'))
        
            title2 = "Warning Stats for Best Threshold "+label+" Automated $V_{rot}$ \n Tilt "+str(tilt)+"$^\circ$ and Bin "+str(int(bin)*timeIncrement)+" Minutes"
            makeWarningBarPlots(vrotSkills, vrotBestThresholds[bin], vrotMartinaitisTSS, realWarningStats, title2, 'h5', cfg)
            
        #Now with cylconic only vrot
        for bin in list(nonTor[tilt]['posvrot'].keys()):

            if bin not in list(tor[tilt]['posvrot'].keys()):
                print('Bin', bin, 'not in the keys for tor in H5 posvrot. Trying next bin')
                continue
            
            if specificBins:
                if int(bin) not in specificBins:
                    continue
                    
            posvrotTSSData[bin] = stats2.calculateVrotTSS(nonTor[tilt]['posvrot'][bin], tor[tilt]['posvrot'][bin], adjustRanges=[40],\
                                                                rangeAdjustValues=[-5], writeMode='a', writeFile=label.replace(' ', '_')+'posvrot_'+str(tilt)+'_tss.csv',\
                                                                group1Name=label+'NON TOR posvrot bin '+str(bin)+" tilt "+str(tilt),\
                                                                group2Name=label+'TOR posvrot bin '+str(bin)+" tilt "+str(tilt))
            
            posvrotTSSValues, posvrotFarValues, posvrotPodValues, posvrotCSIValues, posvrotThresholds = unpackTSS(posvrotTSSData[bin])
            posvrotBestTSS, posvrotBestTSSIndex = stats2.getMaximumTSS(posvrotTSSValues)
            if posvrotBestTSSIndex is None:
                print('Warning! A None posvrotBestTSSIndex was found. Setting values to slightly negative.')
                posvrotSkills = {'far':-0.05, 'pod':-0.05, 'CSI':-0.05}
                posvrotBestThresholds[bin] = None
            else:
                posvrotBestThresholds[bin] = posvrotThresholds[posvrotBestTSSIndex]
                posvrotSkills = {'far':posvrotFarValues[posvrotBestTSSIndex], 'pod':posvrotPodValues[posvrotBestTSSIndex], 'CSI':posvrotCSIValues[posvrotBestTSSIndex]}
            
            posvrotMartinaitisTSS = stats2.calculateTSSRange(nonTor[tilt]['posvrot'][bin], tor[tilt]['posvrot'][bin], 20,\
                                                    adjustRanges=[40], rangeAdjustValues=[-5])
            
            stats2.writeTSS([(20, posvrotMartinaitisTSS)], label+'M17 NON TOR '+str('posvrot')+" bin "+str(bin)+" tilt "+str(tilt),\
                            label+'M17 TOR '+str('posvrot')+" bin "+str(bin)+" tilt "+str(tilt),\
                            [40], [-5], 'a', os.path.join('stats', label.replace(' ', '_')+'posvrot'+'_'+str(tilt)+'_m17tss.csv'))
                            
            title2 = "Warning Stats for Best Threshold "+label+" Cyclonic Automated $V_{rot}$ \n Tilt "+str(tilt)+"$^\circ$ and Bin "+str(int(bin)*timeIncrement)+" Minutes"
            makeWarningBarPlots(posvrotSkills, posvrotBestThresholds[bin], posvrotMartinaitisTSS, realWarningStats, title2, 'h5', cfg)
            
                            
        for bin in list(nonTor[tilt]['90thvrot'].keys()):
        
            if bin not in list(tor[tilt]['90thvrot'].keys()):
                print('Bin', bin, 'not in the keys for to in H5 90thvrot. Trying next bin')
                continue
                
            if specificBins:
                if int(bin) not in specificBins:
                    continue
                    
            topvrotTSSData[bin] = stats2.calculateVrotTSS(nonTor[tilt]['90thvrot'][bin], tor[tilt]['90thvrot'][bin], adjustRanges=[40],\
                                                        rangeAdjustValues=[-5], writeMode='a', writeFile=label.replace(' ', '_')+'90thvrot_'+str(tilt)+'_tss.csv',\
                                                        group1Name=label+'NON TOR 90thvrot bin '+str(bin)+' tilt '+str(tilt),\
                                                        group2Name=label+'TOR 90thvrot bin '+str(bin)+' tilt '+str(tilt))
                                                        
            topvrotTSSValues, topvrotFarValues, topvrotPodValues, topvrotCSIValues, topvrotThresholds = unpackTSS(topvrotTSSData[bin])
            topvrotBestTSS, topvrotBestTSSIndex = stats2.getMaximumTSS(topvrotTSSValues)
            if topvrotBestTSSIndex is None:
                print('Warning! A None topvrotBestTSSIndex was found. Setting values to slightly negative.')
                topvrotSkill = {'far':-0.05, 'pod':-0.05, 'CSI':-0.05}
                topvrotBestThresholds[bin] = None
            else:
                topvrotSkill = {'far':topvrotFarValues[topvrotBestTSSIndex], 'pod':topvrotPodValues[topvrotBestTSSIndex], 'CSI':topvrotCSIValues[topvrotBestTSSIndex]}
                topvrotBestThresholds[bin] = topvrotThresholds[topvrotBestTSSIndex]
            
            
            topvrotMartinaitisTSS = stats2.calculateTSSRange(nonTor[tilt]['90thvrot'][bin], tor[tilt]['90thvrot'][bin], 20, \
                                                            adjustRanges=[40], rangeAdjustValues=[-5])
                                                            
            stats2.writeTSS([(20, topvrotMartinaitisTSS)], label+'M17 NON TOR '+str('90thvrot')+" bin "+str(bin)+" tilt "+str(tilt),\
                            label+'M17 TOR '+str('90thvrot')+" bin "+str(bin)+" tilt "+str(tilt),\
                            [40], [-5], 'a', os.path.join('stats', label.replace(' ', '_')+'90thvrot'+'_'+str(tilt)+'_m17tss.csv'))
                                                        

            title2 = "Warning Stats for Best Threshold "+label+" 90$^{th}$ Percentile Automated $V_{rot}$ \n Tilt "+str(tilt)+"$^\circ$ and Bin "+str(int(bin)*timeIncrement)+" Minutes"
            makeWarningBarPlots(topvrotSkill, topvrotBestThresholds[bin], topvrotMartinaitisTSS, realWarningStats, title2, 'h5', cfg)
            
        for dataType in testDataTypes:
        
            if dataType == 'vrot':
                
                #Create bins for vrot including both groups. If a bin does not exist in a group, don't calculate TSS
                for bin in list(nonTor[tilt][dataType].keys()):
                    
                    if bin not in list(tor[tilt][dataType].keys()):
                        print('Bin', bin, 'not in the keys for tor in H5 vrot. Trying next bin')
                        continue
                        
                    if specificBins:
                        if int(bin) not in specificBins:
                            continue
                        
                    title1 = label+f"Automated $V_{{rot}}$ TSS Tilt {tilt}$^\circ$ at {int(bin)*timeIncrement} Minutes"
                    title2 = label+f"Automated $V_{{rot}}$ by Range Tilt {tilt}$^\circ$ at {int(bin)*timeIncrement} Minutes"
                    title3 = label+f"Automated $V_{{rot}}$ TDS Only TSS \nTilt {tilt}$^\circ$ at {int(bin)*timeIncrement} Minutes"
                    title4 = label+f"Automated $V_{{rot}}$ Warning Stats \nTilt {tilt}$^\circ$ at {int(bin)*timeIncrement} Minutes"
                    title5 = label+f"Automated $V_{{rot}}$ Warning Stats TDS Only \nTilt {tilt}$^\circ$ at {int(bin)*timeIncrement} Minutes"
                    # if potentialClusters:
                        # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        # title3 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        # title4 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        # title5 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        
                   
                    
                    
                                    
                    createTSSPlot(vrotTSSData[bin], title1, 'Automated $V_{{rot}}$ Threshold (Knots)', 'kts', 'h5', cfg)
                    makeWarningStatsPlot(vrotTSSData[bin], title4, 'Automated $V_{{rot}}$ Threshold (Knots)', 'h5', cfg)
                    
                    tdsData = None
                    if bin not in list(torTDS[tilt][dataType].keys()):
                        print(bin, dataType, 'not in tor tds h5')
                        tdsData = []
                    else:
                        tdsData = torTDS[tilt][dataType][bin]
                    
                    noTDSData = None
                    
                    if bin not in list(torNoTDS[tilt][dataType].keys()):
                        print(bin, dataType, 'not in tor no tds h5', list(torNoTDS[tilt][dataType].keys()))
                        noTDSData = []
                    else:
                        noTDSData = torNoTDS[tilt][dataType][bin]

                    makeRangePlots(nonTor[tilt][dataType][bin], tdsData, noTDSData,\
                                    title2, "Range From Nearest Radar (n. mi.)", "Automated $V_{{rot}}$ (Knots)", tilt, 'h5', vrotBestThresholds[bin],\
                                    vrotBestThresholds[bin]-5)
                                    
                    
                                    
                    #Now make a TSS plots doing NON TOR versus TDS tor
                    
                    if bin in list(torTDS[tilt][dataType].keys()):
                        tdsTSSData = stats2.calculateVrotTSS(nonTor[tilt][dataType][bin], torTDS[tilt][dataType][bin], adjustRanges=[40],\
                                                                rangeAdjustValues=[-5], writeMode='a', writeFile=label.replace(' ', '_')+dataType+'_'+str(tilt)+'_tdstss.csv',\
                                                                group1Name=label+'NON TOR '+str(dataType)+" bin "+str(bin)+" tilt "+str(tilt),\
                                                                group2Name=label+'TDS TOR '+str(dataType)+" bin "+str(bin)+" tilt "+str(tilt))
                        

                        createTSSPlot(tdsTSSData, title3, 'Automated $V_{{rot}}$ Threshold (Knots)', 'kts', 'h5', cfg)
                        makeWarningStatsPlot(tdsTSSData, title5, 'Automated $V_{{rot}}$ Threshold (Knots)', 'h5', cfg)
                    
                    
            if dataType == 'posvrot':
                
                for bin in list(nonTor[tilt][dataType].keys()):
                    
                    if bin not in list(tor[tilt][dataType].keys()):
                        print('Bin', bin, 'not in the keys for tor in H5 psvrot. Trying next bin')
                        continue
    
                    if specificBins:
                        if int(bin) not in specificBins:
                            continue
                    
                    title1 = label+f"Cyclonic Automated $V_{{rot}}$ TSS Tilt {tilt}$^\circ$ at {int(bin)*timeIncrement} Minutes"
                    title2 = label+f"Cyclonic Automated $V_{{rot}}$ by Range Tilt {tilt}$^\circ$ at {int(bin)*timeIncrement} Minutes"
                    title3 = label+f"Cyclonic Automated $V_{{rot}}$ TDS Only TSS \nTilt {tilt}$^\circ$ at {int(bin)*timeIncrement} Minutes"
                    title4 = label+f"Warning Stats for Cyclonic Automated $V_{{rot}}$ \nTilt {tilt}$^\circ$ at {int(bin)*timeIncrement} Minutes"
                    title5 = label+f"Warning Stats for Cyclonic Automated $V_{{rot}}$ TDS Only \nTilt {tilt}$^\circ$ at {int(bin)*timeIncrement} Minutes"
                    # if potentialClusters:
                        # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        # title3 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        # title4 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        # title5 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                                                            
                    createTSSPlot(posvrotTSSData[bin], title1, 'Automated $V_{{rot}}$ Threshold (Knots)', 'kts', 'h5', cfg)
                    makeWarningStatsPlot(posvrotTSSData[bin], title4, 'Automated $V_{{rot}}$ Threshold (Knots)', 'h5', cfg)
                    
                    tdsData = None
                    if bin not in list(torTDS[tilt][dataType].keys()):
                        print(bin, dataType, 'not in tor tds h5')
                        tdsData = []
                    else:
                        tdsData = torTDS[tilt][dataType][bin]
                    
                    noTDSData = None
                    
                    if bin not in list(torNoTDS[tilt][dataType].keys()):
                        print(bin, dataType, 'not in tor no tds h5', list(torNoTDS[tilt][dataType].keys()))
                        noTDSData = []
                    else:
                        noTDSData = torNoTDS[tilt][dataType][bin]

                    makeRangePlots(nonTor[tilt][dataType][bin], tdsData, noTDSData,\
                                    title2, "Range From Nearest Radar (n mi.)", "Automated $V_{{rot}}$ (Knots)", tilt, 'h5', posvrotBestThresholds[bin], posvrotBestThresholds[bin]-5)
                                    
                    if bin in list(torTDS[tilt][dataType].keys()):
                        tdsTSSData = stats2.calculateVrotTSS(nonTor[tilt][dataType][bin], torTDS[tilt][dataType][bin], adjustRanges=[40],\
                                                                rangeAdjustValues=[-5], writeMode='a', writeFile=label.replace(' ', '_')+dataType+'_'+str(tilt)+'_tdstss.csv',\
                                                                group1Name=label+'NON TOR '+str(dataType)+" bin "+str(bin)+" tilt "+str(tilt),\
                                                                group2Name=label+'TDS TOR '+str(dataType)+" bin "+str(bin)+" tilt "+str(tilt))
                        

                        createTSSPlot(tdsTSSData, title3, 'Automated $V_{{rot}}$ Threshold (Knots)', 'kts', 'h5', cfg)
                        makeWarningStatsPlot(tdsTSSData, title5, 'Automated $V_{{rot}}$ Threshold (Knots)', 'h5', cfg)
                                    
                                    
            if dataType == 'absshear':
            
                for bin in list(nonTor[tilt][dataType].keys()):
                    
                    if bin not in list(tor[tilt][dataType].keys()):
                        print('Bin', bin, 'not in the keys for tor in H5 psvrot. Trying next bin')
                        continue
                        
                        
                    if specificBins:
                        if int(bin) not in specificBins:
                            continue
                    
                    title2 = label+f"Greater |AzShear| by Range for Tilt {tilt}$^\circ$ at {int(bin)*timeIncrement} Minutes"   

                    # if potentialClusters:
                        # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                        
                    tdsData = None
                    if bin not in list(torTDS[tilt][dataType].keys()):
                        print(bin, dataType, 'not in tor tds h5')
                        tdsData = []
                    else:
                        tdsData = torTDS[tilt][dataType][bin]
                    
                    noTDSData = None
                    
                    if bin not in list(torNoTDS[tilt][dataType].keys()):
                        print(bin, dataType, 'not in tor no tds h5', list(torNoTDS[tilt][dataType].keys()))
                        noTDSData = []
                    else:
                        noTDSData = torNoTDS[tilt][dataType][bin]

                                                            
                    bestThresholdShear = convertToAzShear(vrotBestThresholds[bin], cfg.radius)
                    thresholdDecrease = convertToAzShear(5, cfg.radius)
                    
                    makeRangePlots(nonTor[tilt][dataType][bin], tdsData, noTDSData,\
                                    title2, "Range From Nearest Radar (n mi.)", "AzShear (s$^{-1}$)", tilt, 'h5', bestThresholdShear,\
                                    bestThresholdShear-thresholdDecrease)
                                    
                if dataType == 'posazshear':
            
                    for bin in list(nonTor[tilt][dataType].keys()):
                        
                        if bin not in list(tor[tilt][dataType].keys()):
                            print('Bin', bin, 'not in the keys for tor in H5 psvrot. Trying next bin')
                            continue
                    
                        title2 = label+f"Cyclonic AzShear by Range for Tilt {tilt}$^\circ$ at {int(bin)*timeIncrement} Minutes"

                        # if potentialClusters:
                            # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                            
                        tdsData = None
                        if bin not in list(torTDS[tilt][dataType].keys()):
                            print(bin, dataType, 'not in tor tds h5')
                            tdsData = []
                        else:
                            tdsData = torTDS[tilt][dataType][bin]
                        
                        noTDSData = None
                        
                        if bin not in list(torNoTDS[tilt][dataType].keys()):
                            print(bin, dataType, 'not in tor no tds h5', list(torNoTDS[tilt][dataType].keys()))
                            noTDSData = []
                        else:
                            noTDSData = torNoTDS[tilt][dataType][bin]

                        bestThresholdShear = convertToAzShear(posvrotBestThresholds[bin], cfg.radius)
                        thresholdDecrease = convertToAzShear(5, cfg.radius)
                    
                        makeRangePlots(nonTor[tilt][dataType][bin], tdsData, noTDSData,\
                                        title2, "Range From Nearest Radar (n mi.)", "AzShear (s$^{-1}$)", tilt, 'h5', bestThresholdShear,\
                                        bestThresholdShear-thresholdDecrease)
                if dataType == '90thvrot':
                
                    for bin in list(nonTor[tilt][dataType].keys()):
                        
                        if bin not in list(tor[tilt][dataType].keys()):
                            print('Bin', bin, 'not in the keys for tor in H5 psvrot. Trying next bin')
                            continue
                            
                        if specificBins:
                            if int(bin) not in specificBins:
                                continue
        
                        title1 = label+f"90th% Cyclonic Automated $V_{{rot}}$ TSS Tilt {tilt}$^\circ$ at {int(bin)*timeIncrement} Minutes"
                        title2 = label+f"90th% Cyclonic Automated $V_{{rot}}$ by Range Tilt {tilt}$^\circ$ at {int(bin)*timeIncrement} Minutes"
                        title3 = label+f"90th% Cyclonic Automated $V_{{rot}}$ TDS Only TSS \nTilt {tilt}$^\circ$ at {int(bin)*timeIncrement} Minutes"
                        title4 = label+f"Warning Stats for 90th% Cyclonic Automated $V_{{rot}}$ \nTilt {tilt}$^\circ$ at {int(bin)*timeIncrement} Minutes"
                        title5 = label+f"Warning Stats for 90th% Cyclonic Automated $V_{{rot}}$ TDS Only \nTilt {tilt}$^\circ$ at {int(bin)*timeIncrement} Minutes"
                        # if potentialClusters:
                            # title1 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                            # title2 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                            # title3 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                            # title4 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                            # title5 += ' <= '+str(potentialClusters)+' Pot. Clusters'
                                                                
                        createTSSPlot(topvrotTSSData[bin], title1, 'Automated $V_{{rot}}$ Threshold (Knots)', 'kts', 'h5', cfg)
                        makeWarningStatsPlot(topvrotTSSData[bin], title4, 'Automated $V_{{rot}}$ Threshold (Knots)', 'h5', cfg)
                        
                        tdsData = None
                        if bin not in list(torTDS[tilt][dataType].keys()):
                            print(bin, dataType, 'not in tor tds h5')
                            tdsData = []
                        else:
                            tdsData = torTDS[tilt][dataType][bin]
                        
                        noTDSData = None
                        
                        if bin not in list(torNoTDS[tilt][dataType].keys()):
                            print(bin, dataType, 'not in tor no tds h5', list(torNoTDS[tilt][dataType].keys()))
                            noTDSData = []
                        else:
                            noTDSData = torNoTDS[tilt][dataType][bin]

                        makeRangePlots(nonTor[tilt][dataType][bin], tdsData, noTDSData,\
                                        title2, "Range From Nearest Radar (n mi.)", "Automated $V_{{rot}}$ (Knots)", tilt, 'h5', posvrotBestThresholds[bin], posvrotBestThresholds[bin]-5)
                                        
                        if bin in list(torTDS[tilt][dataType].keys()):
                            tdsTSSData = stats2.calculateVrotTSS(nonTor[tilt][dataType][bin], torTDS[tilt][dataType][bin], adjustRanges=[40],\
                                                                    rangeAdjustValues=[-5], writeMode='a', writeFile=label.replace(' ', '_')+dataType+'_'+str(tilt)+'_tdstss.csv',\
                                                                    group1Name=label+'NON TOR '+str(dataType)+" bin "+str(bin)+" tilt "+str(tilt),\
                                                                    group2Name=label+'TDS TOR '+str(dataType)+" bin "+str(bin)+" tilt "+str(tilt))
                            

                            createTSSPlot(tdsTSSData, title3, 'Automated $V_{{rot}}$ Threshold (Knots)', 'kts', 'h5', cfg)
                            makeWarningStatsPlot(tdsTSSData, title5, 'Automated $V_{{rot}}$ Threshold (Knots)', 'h5', cfg)
                                    
    return


def getGroupsByTDS(nonTor, tds, notds, dataType, tilt, bin, includeNonTor, cfg):

    tiltLoopList = []
    tdsData = []
    otherData = []
   
    #Get the EF ratings 
    try:
        efList = list(notds[tilt][dataType][bin].keys())
        efList.extend(list(tds[tilt][dataType][bin].keys()))
        efSet = sorted(set(efList))
    except KeyError as K:
        print('Bin', K, 'not in groubytds ef sorting', bin, tilt)
        #If we have a key error here, just return None, None and let the calling function handle it.
        return None, None
        
    for EF in efSet:
        #Loop through the EF ratings and extend the data. Remove unknown EF ratings
        if int(EF) != -1:
            tdsToAppend = None
            try:
                tdsToAppend = tds[tilt][dataType][bin][EF]
                print('Now extending to tds', tdsToAppend, 'for EF', bin, EF)
                tdsData.extend(tdsToAppend)
            except KeyError as K:
                print('Bin or EF', K, 'not in groupbytds tds', tilt, bin, EF)
                
            otherDataToAppend = None
            
            try:
                otherDataToAppend = notds[tilt][dataType][bin][EF]
                print('Extending other data', otherDataToAppend, 'for EF', bin, EF)
                otherData.extend(otherDataToAppend)
            except KeyError as K:
                print('Bin or EF', K, 'not in groupbytds notds', tilt, bin, EF)
            
    if includeNonTor:
        try:
            print('Adding NON TOR', nonTor[tilt][dataType][bin], 'now with', otherDataToAppend)
            otherData.extend(nonTor[tilt][dataType][bin])
        except KeyError as K:
            print('Bin', K, 'not in groupbytds nontor', tilt, bin)
            return tdsData, None
                
    return tdsData, otherData
    

def getH5EFTitle(dataType, dataKey, tilt, bin, lowerEFBoundaries, higherEFBoundaries, sortByTDS, includeNonTor, potentialClusters, timeBinIncrement):

    title = ''
    
    if dataType == 'vrot':
        title += 'Automated $V_{rot}$ TSS'
    elif dataType == 'posvrot':
        title += f"Cyclonic Automated $V_{{rot}}$ TSS "
    elif dataType == '90thvrot':
        title += f"Cyclonic 90th% Automated $V_{{rot}}$ TSS "
    
    if sortByTDS:
        title += 'TDS '
    
    title += 'Tilt '+str(tilt)+'$^\circ$ at Bin '+str(int(bin)*timeBinIncrement)+' Minutes'
    
    if lowerEFBoundaries:
        pass
        # if includeNonTor or (int(lowerEFBoundaries[0]) <= -2 and int(lowerEFBoundaries[1]) >= -2) :
            # title += 'NON TOR and '
        # if lowerEFBoundaries[0] < 0 and lowerEFBoundaries[1] >= 0:
            # if lowerEFBoundaries[1] == 0:
                # title += 'EF 0'
            # else:
                # title += 'EF 0 to EF '+str(lowerEFBoundaries[1])
        # else:
            # title += 'EF '+str(lowerEFBoundaries[0])+ ' to EF '+str(lowerEFBoundaries[1])
    if higherEFBoundaries:
        title += ' for EF'+str(higherEFBoundaries[0])+'+'
    # if potentialClusters:
        # title += ' <= '+str(potentialClusters)+' Pot. Clusters'
        
    
        
    return title
    
    
def hypothesis5EF(nonTor, tor, tds, notds, dataKey, testDataTypes, potentialClusters, cfg, realWarningStats, lowerEFBoundaries=None, higherEFBoundaries=None, sortByTDS=False,\
                 includeNonTorInTDS=False, timeBinIncrement=5, label='', specificBins=None):

    """ Calculates TSS between two groups of mixed NON TOR and ALL TOR or by TDS and no TDS. Similar to hypothesis5().
        lower/higherEFBoundaries are lists that define where the EF-rating boundaries for each group. 
        For example, [-2, 0] will include nontors (-2), unkonwn EF cases (-1), and EF0 case in the group.
    """
    
    if not cfg.hypo5ef:
        print('Hypothesis 5 EF is disabled. Skipping!')
        return
        
        
    print('Starting h5 EF with nontor', label)#, nonTor, '\ntds', tds, '\nnotds', notds)
    
    if label:
        label += ' '
    
    #Check to see if we're dividing by group
    if lowerEFBoundaries and higherEFBoundaries:
        
        print('Sorting by bondaries')
        
        for dataType in testDataTypes:
            
            tiltLoopList = []
            
            for tilt in list(tor.keys()):
                
                binLoopList = list(tor[tilt][dataType].keys())
                binLoopList.extend(nonTor[tilt][dataType].keys())
                binLoopSet = sorted(set(binLoopList))
                
                for bin in binLoopSet:
                    
                    try:
                        efSet = sorted(set(list(tor[tilt][dataType][bin].keys())))
                    except KeyError as K:
                        print('Bin', K, 'not in efSet candidate. Trying next bin')
                        continue
        
                    #Check to see if there is a specific bin. If not, continue
                    if specificBins:
                        if int(bin) not in specificBins:
                            print(bin, 'not in', specificBins, '. Continuing.')
                            continue
                            
                    expectedHigher = []
                    expectedLower = []
                    
                    for EF in efSet:
                        
                        currentEF = int(EF)
                        print('Now looking at', EF)
                        if currentEF >= higherEFBoundaries[0] and currentEF <= higherEFBoundaries[1] and currentEF != -1:
                            try:
                                expectedHigher.extend(tor[tilt][dataType][bin][EF])
                                print('Added to higher')
                            except KeyError as K:
                                print('There was a key error in expected higher', K, tilt, dataType, '. Data not extended')
                                
                        if currentEF >= lowerEFBoundaries[0] and currentEF <= lowerEFBoundaries[1] and currentEF != -1:
                            try:
                                expectedLower.extend(tor[tilt][dataType][bin][EF])
                                print('Added to lower')
                            except KeyError as K:
                                print('There was a key error in expected lower', K, tilt, dataType, '. Data not extended')
                                
                    haveNonTor = False            
                    #Now add the NON TORs
                    if (lowerEFBoundaries[0] <= -2 and lowerEFBoundaries[1] >= -2) or (higherEFBoundaries[0] <= -2 and higherEFBoundaries[1] >= -2):
                        try:
                            expectedLower.extend(nonTor[tilt][dataType][bin])
                            haveNonTor = True
                        except KeyError as K:
                            print('There was a key error in nontor expected lower', K, tilt, dataType, '. Data not extended')
                        
                        
                    #Now calculate TSS scores and the stats
                    
                    title = label+getH5EFTitle(dataType, dataKey, tilt, bin, lowerEFBoundaries, higherEFBoundaries, sortByTDS, includeNonTorInTDS, potentialClusters, timeBinIncrement)
                    group1Name = label
                    group2Name = label
                    if 'cyclonic' in dataKey.lower():
                        group1Name += 'Cyclonic '
                        group2Name += 'Cyclonic '
                        
                    group1Name += str(dataType)+' '
                    group2Name += str(dataType)+' '
                    
                    if haveNonTor:
                        group1Name += 'NON TOR and '
                    
                    group1Name += f"EF {lowerEFBoundaries[0]} to EF {lowerEFBoundaries[1]} tilt {tilt} bin {bin}"
                    group2Name += f"EF {higherEFBoundaries[0]} to EF {higherEFBoundaries[1]} tilt {tilt} bin {bin}"
                    efStr = f"{lowerEFBoundaries[0]}_{lowerEFBoundaries[1]}_{higherEFBoundaries[0]}_{higherEFBoundaries[1]}"
                    
                    tssData = stats2.calculateVrotTSS(expectedLower, expectedHigher, adjustRanges=[40], rangeAdjustValues=[-5], writeMode='a',\
                                                    writeFile=label.replace(' ', '_')+str(dataType)+'_'+str(tilt)+'_tdsEF'+str(efStr)+'.csv',\
                                                    group1Name=group1Name, group2Name=group2Name)
                                                    
                    tssValues, farValues, podValues, csiValues, thresholds = unpackTSS(tssData)
                    bestTSS, bestTSSIndex = stats2.getMaximumTSS(tssValues)
                    if bestTSSIndex is None:
                        print('Warning! A None bestTSSIndex was found. Setting values to slightly negative.')
                        skills = {'far':-0.05, 'pod':-0.05, 'CSI':-0.05}
                        bestThreshold = None
                    else:
                        skills = {'far':farValues[bestTSSIndex], 'pod':podValues[bestTSSIndex], 'CSI':csiValues[bestTSSIndex]}
                        bestThreshold = thresholds[bestTSSIndex]
                        
                    
                    m17tss = stats2.calculateTSSRange(expectedLower, expectedHigher, 20, adjustRanges=[40], rangeAdjustValues=[-5])
                    
                    stats2.writeTSS([(20, m17tss)], group1Name, group2Name, [40], [-5], 'a', os.path.join('stats', label.replace(' ', '_')+dataType+'_'+str(tilt)+'_tdsEF'+str(efStr)+'.csv'))
                    
                    createTSSPlot(tssData, title, 'Automated $V_{{rot}}$ Threshold (Knots)', 'kts', 'h5', cfg)
                    makeWarningStatsPlot(tssData, 'Warning Stats For '+title.replace(' TSS', ''), 'Automated $V_{{rot}}$ Threshold (Knots)', 'h5', cfg)
                    
                    title2 = "Warning Stats for Best Threshold "+title.replace(' TSS', '')
                    
                    makeWarningBarPlots(skills, bestThreshold, m17tss, realWarningStats, title2, 'h5', cfg)
        return
                
    elif not sortByTDS:
        raise ValueError("lowerEFBoundaries and higherEFBoundaries must both be None or not None")
            
    if sortByTDS:
        #Begin looping through the data
        print('Sorting by TDS')
        
        for dataType in testDataTypes:
            
            tiltLoopList = []
            
            if includeNonTorInTDS:
                tiltLoopList = sorted(list(nonTor.keys()))
            else:
                tiltLoopList = sorted(list(notds.keys()))
                
            for tilt in tiltLoopList:
                
                binLoopList = []
                if includeNonTorInTDS:
                    binLoopList = list(nonTor[tilt][dataType].keys())
                    binLoopList.extend(list(notds[tilt][dataType].keys()))
                    binLoopList = set(sorted(binLoopList))
                else:
                    binLoopList = sorted(list(notds[tilt][dataType].keys()))
                    
                print('Beginning to loop through h5', dataType, 'bins', binLoopList, 'for tilt', tilt)
                for bin in binLoopList:
                
                    #Start by defining the title we are going to use
                    title = label+getH5EFTitle(dataType, dataKey, tilt, bin, lowerEFBoundaries, higherEFBoundaries, sortByTDS, includeNonTorInTDS, potentialClusters, timeBinIncrement)
                    tdsData, otherData = getGroupsByTDS(nonTor, tds, notds, dataType, tilt, bin, includeNonTorInTDS, cfg)
                    
                    if not tdsData or not otherData:
                        print('In TSS by TDS, at least one category', tilt, bin)
                        continue
                    
                    #Check to see if there is a specific bin. If not, continue
                    if specificBins:
                        if int(bin) not in specificBins:
                            print(bin, 'not in', specificBins, '. Continuing.')
                            continue
                            
                    group1Name = label
                    group2Name = label
                    if 'cyclonic' in dataKey.lower():
                        group1Name += 'Cyclonic '
                        group2Name += 'Cyclonic '
                        
                    group1Name += str(dataType)+' '
                    group2Name += str(dataType)+' '
                    
                    if includeNonTorInTDS:
                        group1Name += 'NON TOR and '
                    group1Name += ' NO TDS '+str(dataType)+' '+str(tilt)+' '+str(bin)+' pot. clusters '+str(potentialClusters)
                    group2Name += 'TDS '+str(dataType)+' '+str(tilt)+' '+str(bin)+' pot. clusters '+str(potentialClusters)
                    
                    tssData = stats2.calculateVrotTSS(otherData, tdsData, adjustRanges=[40], rangeAdjustValues=[-5], writeMode = 'a',\
                                                    writeFile=label.replace(' ', '_')+str(dataType)+'_'+str(tilt)+'_tdsEFtss.csv', 
                                                    group1Name=group1Name,
                                                    group2Name=group2Name)
                                                    
                    tssValues, farValues, podValues, csiValues, thresholds = unpackTSS(tssData)
                    bestTSS, bestTSSIndex = stats2.getMaximumTSS(tssValues)
                    
                    if bestTSSIndex is None:
                        print('Warning! A None bestTSSIndex was found. Setting values to slightly negative.')
                        skills = {'far':-0.05, 'pod':-0.05, 'CSI':-0.05}
                        bestThreshold = None
                    else:
                        skills = {'far':farValues[bestTSSIndex], 'pod':podValues[bestTSSIndex], 'CSI':csiValues[bestTSSIndex]}
                        bestThreshold = thresholds[bestTSSIndex]
                        
                    m17tss = stats2.calculateTSSRange(otherData, tdsData, 20, adjustRanges=[40], rangeAdjustValues=[-5])
                    
                    stats2.writeTSS([(20, m17tss)], group1Name, group2Name, [40], [-5], 'a', os.path.join('stats', label.replace(' ', '_')+dataType+'_'+str(tilt)+'_m17tdsEFtss.csv'))
                    
                    createTSSPlot(tssData, title, 'Automated $V_{{rot}}$ Threshold (Knots)', 'kts', 'h5', cfg)
                    makeWarningStatsPlot(tssData, 'Warning Stats For '+title.replace(' TSS', ''), 'Automated $V_{{rot}}$ Threshold (Knots)', 'h5', cfg)
                    
                    title2 = "Warning Stats for Best Threshold "+title
                    makeWarningBarPlots(skills, bestThreshold, m17tss, realWarningStats, title2, 'h5', cfg)
                    
        return

        
    else:
        print("You didn't specify boundadries or to sort by TDS. Just use the hypothesis5 function")
        return None
        
        
    return
        

def getManualLikeStats(torObjects, nonTorObjects, tiltList, cfg, realWarningStats, realWarningEFStats, potentialClusters):

    """ This function allocates all TOR by maximum AzShear from the zero-minute bin onward and NON TOR maximum from the -10-minute to zero-minute
        bin to be more consistent with Nowotarski et al. (2021).
    """
    
    #First get the TDS cses
    tdsObjects, noTDSObjects, nTDS, nNoTDS, tdsCountByEF, totalCountByEF = sorting.sortTDS(torObjects, tiltList[0], minCount=25, startBin=0, potentialClusters=potentialClusters)
    
    print('Starting time shifting in the manual stats')
    shiftedNonTor = coord.timeShiftByBin(nonTorObjects, tiltList, 'max', -2, 0, cfg)
    shiftedTor = coord.timeShiftByBin(torObjects, tiltList, 'max', 0, 0, cfg)
    shiftedTDS = coord.timeShiftByBin(tdsObjects, tiltList, 'max', 0, 0, cfg)
    shiftedNoTDS = coord.timeShiftByBin(noTDSObjects, tiltList, 'max', 0, 0, cfg)
    
    print('Now sorting for manual stats')
    #Sort each of these object sets
    sortedNonTor = sorting.getObjectsByBin(shiftedNonTor, tiltList, cfg, maxPotentialClusters=potentialClusters)[0]
    sortedTor = sorting.getObjectsByBin(shiftedTor, tiltList, cfg, isTOR=True, maxPotentialClusters=math.inf)[0]
    sortedTDS = sorting.getObjectsByBin(shiftedTDS, tiltList, cfg, isTOR=True, isTDS=True, maxPotentialClusters=potentialClusters)[0]
    sortedNoTDS = sorting.getObjectsByBin(shiftedNoTDS, tiltList, cfg, isTOR=True, maxPotentialClusters=potentialClusters)[0]
    
    
    print('Now doing plots and tests for manual stats')
    #Run the data with the existing hypothesis function. We can only look at the zero-bins if we want
    key1 = 'AzShear Clusters by Tilt and Range'
    hypothesis5(sortedNonTor[key1], sortedTor[key1], sortedTDS[key1], sortedNoTDS[key1], key1, ['posvrot', 'posazshear', '90thvrot'], potentialClusters, cfg, realWarningStats, label='N21-Like', specificBins=[0])
    
    key1 = 'AzShear Clusters by Tilt and Range and EF'
    hypothesis5EF(sortedNonTor['AzShear Clusters by Tilt and Range'], sortedTor[key1], sortedTDS[key1], sortedNoTDS[key1], key1, ['posvrot', '90thvrot'], potentialClusters, cfg, realWarningStats, sortByTDS=True,\
                  includeNonTorInTDS=True, label='N21-Like', specificBins=[0])
                  
    hypothesis5EF(sortedNonTor['AzShear Clusters by Tilt and Range'], sortedTor[key1], sortedTDS[key1], sortedNoTDS[key1], key1, ['posvrot', '90thvrot'], potentialClusters, cfg, realWarningEFStats, \
                 lowerEFBoundaries=[-2, 0], higherEFBoundaries=[1, 5], label='N21-Like', specificBins=[0])
                 
    
    return
    