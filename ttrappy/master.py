#Module that contains primary functions for running the ttrappy application


#Import Modules
from ttrapcfg import config
from ttrappy import case as caseMod
from ttrappy import ttrappy as ttr
from ttrappy import download
from ttrappy import visualize
from ttrappy import error as err

from datetime import datetime as dt
from datetime import timedelta as td
import multiprocessing as mp
import psutil
import queue

import numpy as np
import sys
import os, shutil
import time
import pytz
import tkinter as tk
import gc
from tkinter import ttk
from PIL import ImageTk, Image

#Required WDSII programs
#ldm2netcdf, w2makeindex.py, w2qcnndp, w2echotop, w2simulator, w2merger, dealiasVel,w2circ, w2localmax, w2smooth, w2segmotionll, w2table2csv

class Master():

    
    def __init__(self, cfg):
        
        self.cfg = cfg
        self.m = mp.Manager()
        self.q = self.m.Queue()
        return
        
    def createDirectories(self, case):

        self.cfg.log("Creating directories")
        baseDirElements = case.baseDir.split("/")
        dirString = ""

        for e in baseDirElements:
            try:
                dirString = dirString+str(e)+"/"
                os.mkdir(dirString)
            except FileExistsError:
                self.cfg.log(dirString+' exists')

        try:
        
            for dir in case.dirs:
                if not os.path.exists(dir):
                    os.mkdir(dir)
            if not os.path.exists(case.saveDir):
                os.mkdir(case.saveDir)
            if not os.path.exists(case.saveDir+'/figs'):
                os.mkdir(case.saveDir+'/figs')
            if not os.path.exists(case.saveDir+'/pdf'):
                os.mkdir(case.saveDir+'/pdf')
            if not os.path.exists('w2mergercache') and self.cfg.createCache:
                os.mkdir('w2mergercache')
           
                
        except FileExistsError:
            self.cfg.log(FileExistsError)
            
        return


     
    def printTemplate(filename):
        
        filename = filename+".csv"
        fi = open(filename, 'w')
        fi.write('id,strom,year,month,day,time,start_lat,start_lon,stop_lat,stop_lon,istor,F-EF-Rating,class\n')
        fi.close()
        
        return
        
    def processArchivedCases(self, gui=None):

        try:
        
            #This is here so it doesn't get overwritten with each case

            # if os.path.exists('./logs') and not self.cfg.ttrapOnly:
                # shutil.rmtree('./logs')
                # os.mkdir('./logs')
                
                
            #Clear out the skipped cases file before processing cases
            with open(self.cfg.logName+'_skippedcases.csv', 'w') as fi:
                fi.write('TC,case,istor,errorcode,error\n')

            #Clear out the file for events
            with open(self.cfg.logName+'_events.csv', 'w') as fi:
                fi.write('TC,case,istor,code,remaining,event\n')
                
            processedCases = []
            
            if gui:
                pass
            cases = caseMod.loadCases(self.cfg)
            
            #c for currentCase
            for cCase in cases:

                
                self.ttrap = ttr.Processor(self.cfg, cCase, self.q, self.m)
                self.cfg.log("-------------- Starting case "+cCase.ID+" ------------")
                self.cfg.error("-------------- Starting case "+cCase.ID+" ------------")
                if cCase.storm != self.cfg.storm:
                    self.cfg.storm = cCase.storm
                    cCase.updateDirs(self.cfg)
                    self.cfg.log("Changed cfg storm to "+self.cfg.storm)
                    
                #Create directoies for the case	
                self.createDirectories(cCase)
                
                #Create the "hail report" to associate with hour target cell
                cCase.createReport()
                
                try:
                    hasVarFile = cCase.checkVars(self.cfg, cCase.baseDir, 'vars.pkl')
                except EOFError as E:
                    self.cfg.log(str(E)+"\nAssuming no var file!")
                    hasVarFile = False
            
                try:
                    downloadAsync, downloadPool = download.downloadData(self.cfg, cCase)
                    downloadAsync.wait(20)
                    results = downloadAsync.get()
                except err.RadarNotFoundError as excep:
                    cfg.error("The closest radar was not found in "+cCase.ID+". Continuing to next case")
                    
                    with open(self.cfg.logName+'_skippedcases.csv', 'a') as fi2:
                        fi2.write(str(cCase.storm)+','+str(cCase.ID)+','+str(cCase.isTor)+',1,'+str(excep)+'\n')
                        

                    continue
                    
                #Update the case object with recent scans for each site
                for result in results:
                    cCase.updateSite(result)
                
                downloadPool.close()

                #Check to see if L2 data actually exists
                L2Files = os.listdir(cCase.radDir)
                if not L2Files:
                    self.cfg.error("No L2 files downloaded")
                    with open(self.cfg.logName+'_skippedcases.csv', 'a') as fi:
                        fi.write(str(cCase.storm)+','+str(cCase.ID)+','+str(cCase.isTor)+',6,No Level 2 Radar Data Downloaded\n')
                        continue
                        
                self.ttrap.updateCase(cCase)
                
                #Process radar data with WDSII
                if not self.cfg.ttrapOnly or not hasVarFile:
                    if not hasVarFile and self.cfg.ttrapOnly:
                        self.cfg.error("Var File not found for case "+cCase.ID+". Running WDSSII")
                    
                    #Remove old log files before creating new ones
                    if os.path.exists(cCase.logDir) and not self.cfg.ttrapOnly:
                        shutil.rmtree(cCase.logDir)
                        os.mkdir(cCase.logDir)
                        
                    cCase, finished = self.ttrap.wdssii()
                    
                    #Check to see if processing actually finished. Don't finish the loop if it didn't
                    if not finished:
                        self.cfg.error("WDSSII did not finish!!! in case "+str(cCase.ID))
                        continue
                    
                try:
                    #Run the TTRAP algorithm on the WDSII data
                    frames = self.ttrap.ttrap()
                except err.NoReferenceClusterFoundException as excep1:
                    self.cfg.log("Starting next case after no reference cluster found")
                    
                    with open(self.cfg.logName+'_skippedcases.csv', 'a') as fi:
                        fi.write(str(cCase.storm)+','+str(cCase.ID)+','+str(cCase.isTor)+',2,'+str(excep1)+'\n')
                        

                    continue
                except err.NoModelDataFound as excep2:
                    self.cfg.log("Starting next case after no model data was found for a key cluster")
                    
                    with open(self.cfg.logName+'_skippedcases.csv', 'a') as fi2:
                        fi2.write(str(cCase.storm)+','+str(cCase.ID)+','+str(cCase.isTor)+',3,'+str(excep2)+'\n')
                    
                    continue
                    
                    
                cCase.setStormGroups(frames)
                
                if self.cfg.makeFigures:
                    visualize.createPlots(self.cfg, cCase)
                else:
                    self.cfg.log("Skipping figure creation")
                
                processedCases.append(cCase)
                
                #Delete the ttrap object to free up memory 
                del self.ttrap
                gc.collect() #Actually frees up unferenced memory spaces
                
                
            self.cfg.log("Finished cases")
                
                
        except Exception as E:

            self.cfg.log("Excpetion occured. Terminating subprocesses.\n"+str(E))
            
            self.q.put(err.StopProcessingException("Exception in Archive"))

            #Clean out the remaining queue items to avoid broken pipe at shutdown after confirmation the listener has stopped
            emptyStart = dt.now()
            startEmptying = False
            while not startEmptying or not self.q.empty():
                #Give the listener 2 seconds to close. Assumed the listener is no longer running then
                if not self.q.empty():
                    qResult = self.q.get_nowait()
                    if qResult == 'listenerstopped':
                        startEmptying = True
                    if startEmptying:
                        self.cfg.log("Removed "+str(qResult))
                        time.sleep(0.1)
                        emptyStart = dt.now()
                    else:
                        self.cfg.log("Waiting for listenerstopped from listener")
                        self.q.put(qResult)
                     
                if (dt.now() - emptyStart).seconds > 2:
                    self.cfg.log("Empty Timeout")
                    break
                time.sleep(0.1)
            self.q.put('listenerstopped') #Replace the listener status since the listener should be stopped            
            raise
         
        except err.StopProcessingException:
            raise
            
        return processedCases
        
            
    def startGui(self):

        try:
            os.mkdir(self.cfg.baseDir)
        except FileExistsError:
            pass
            
        #Start the TTRAP GUI
        root = tk.Tk()
        gui = visualize.Visualizer(root)
        gui.master.rowconfigure([0, 1, 2], minsize=50, weight=1)
        gui.master.columnconfigure([0, 1, 2], minsize=50, weight=1)
        gui.master.title("TTRAPpy")
        gui.master.geometry("1600x900")
        
        oldConfig = self.cfg
        
            
        def destroyGui():
            self.cfg.log("Stopping children and destroying gui")
            
            self.q.put(err.StopProcessingException("Destroying GUI"))
            
            #Clean out the remaining queue items to avoid broken pipe at shutdown after confirmation the listener has stopped
            startEmptying = False
            emptyStart = dt.now()
            while not startEmptying or not self.q.empty():
                #Give the listener 15 secodns to close. Assumed the listener is no longer running then
                if not self.q.empty():
                    qResult = self.q.get_nowait()
                    if qResult == 'listenerstopped':
                        startEmptying = True
                    if startEmptying:
                        self.cfg.log("Removed "+str(qResult))
                        time.sleep(0.1)
                        emptyStart = dt.now()
                    else:
                        self.cfg.log("Waiting for listenerstopped from listener")
                        self.q.put(qResult)
                        
                    
                    
                if (dt.now() - emptyStart).seconds > 2:
                    self.cfg.log("Empty Timeout")
                    break
                time.sleep(0.1)
            
            children = mp.active_children()
            #Stop multiprocessing children
            if children:
                for child in children:
                    self.cfg.log("Stopping process "+str(child.name))
                    child.terminate()
                    child.join()
                    
            #Close all image objects in the Fig Manager
            for a in range(4):
                images = figManager.getImages(self.cfg, a)
                if images:
                    for img in images:
                        img.close()
            
            
            
            #Close the window
            gui.master.destroy()
                                        
            return
            
        def startArchived():
            try:
                self.cfg.setTTRAP(not bool(ttrap_var.get()))
                self.cfg.makeFigures = bool(fig_var.get())
                self.cfg.combine = bool(combine_var.get())
                arcProcess = mp.Process(target=self.processArchivedCases, name="archive")
                arcProcess.start()
            except Exception as E:
                self.cfg.error("Exception occured while running archived. Stopping children ")
                

                        
                children = mp.active_children()
                #Stop multiprocessing children
                if children:
                    for child in children:
                        self.cfg.log("Stopping process "+str(child.name))
                        child.terminate()
                
                raise
                
            return
            
        def changeCaseFile(event):
            self.cfg.caseFile = 'case_files/'+case_box.get()
            return
            
        def changeConfig(event):
            self.cfg.updateConfig('ttrapcfg/configs/'+cfg_box.get())
            changeCaseFile(event)
            self.cfg.log("Loaded new configuration!!")
            self.cfg.log("Checking new config")
            self.cfg.log(str(vars(self.cfg)))
            return
            
            
        #Create Button Frame
        
        btn_frm = tk.Frame(master=gui.master)
        btn_frm.rowconfigure([0, 1, 2, 3], minsize=10, weight=1)
        btn_frm.columnconfigure([0, 1, 2, 3], minsize=10, weight=1)
        
        archive_btn = tk.Button(btn_frm, text="Run Archive", command=startArchived)
        archive_btn.grid(row=1, column=1, sticky="ne")
        
        quit_btn = tk.Button(btn_frm, text="Quit", command=destroyGui)
        quit_btn.grid(row=1, column=0, sticky="nw")
        
        case_box = ttk.Combobox(btn_frm, values=sorted(os.listdir('case_files')), state="readonly")
        case_box.grid(row=1, column=2, padx=1)
        case_box.bind("<<ComboboxSelected>>", changeCaseFile)
        case_label = tk.Label(btn_frm, text="Select Case")
        case_label.grid(row=1, column=3, padx=1)
        
        cfg_box = ttk.Combobox(btn_frm, values=os.listdir('ttrapcfg/configs'), state="readonly")
        cfg_box.grid(row=2, column=2, padx=1)
        cfg_box.bind("<<ComboboxSelected>>", lambda event, cfg=self.cfg : changeConfig(event))
        cfg_label = tk.Label(btn_frm, text="Select Config .xml")
        cfg_label.grid(row=2, column=3, padx=1)
        
        ttrap_var = tk.IntVar()
        ttrap_check = tk.Checkbutton(btn_frm, text="Process Radar", variable=ttrap_var)
        ttrap_check.grid(row=0, column=1, padx=1, pady=1, sticky="nsew")
        ttrap_check.select()
        
        combine_var = tk.IntVar()
        combine_check = tk.Checkbutton(btn_frm, text="Combine Data", variable=combine_var)
        combine_check.grid(row=0, column=2, padx=1, pady=1, sticky="nsew")
        combine_check.select()
        
        fig_var = tk.IntVar()
        fig_check = tk.Checkbutton(btn_frm, text="Make Figures", variable=fig_var)
        fig_check.grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
        
        
        btn_frm.grid(row=0, column=0)
       
        #Create Image Frame
        
        img_frm = tk.Frame(master=gui.master)
        img_frm.rowconfigure([0], minsize=640, weight=1)
        img_frm.columnconfigure([0], minsize=640, weight=1)
        img_frm.grid(row=1, column=1)
        
        figManager = visualize.FigManager(self.cfg)
        optionBoxes = visualize.ComboBoxes()
        
        
        def drawCanvases(event):
            stormS = optionBoxes.getStorm()
            caseS = optionBoxes.getCase()
            figS = optionBoxes.getFig()
            
            if stormS.get() and caseS.get() and figS.get():
            
                if figManager.getStorm(stormS.get()).getCase(caseS.get()).hasFigures():
                
                    for a in range(len(figManager.getCanvases())):
                        canvas = figManager.getCanvas(self.cfg, a)
                        if canvas:
                            image = figManager.getActiveImage(self.cfg, a).resize((figManager.getCurrentWidth(), figManager.getCurrentHeight()), Image.BILINEAR)
                            canvas.image = ImageTk.PhotoImage(image, Image.BILINEAR)
                            canvas.create_image(figManager.getCurrentX(), figManager.getCurrentY(), image=canvas.image, anchor="nw")
            
            return
            
        def resetFig():
            canvas = figManager.getCanvas(self.cfg, 0)
            canvas.xview_moveto(0)
            canvas.yview_moveto(0)
            figManager.setDimensions(0, 0, figManager.getOriginalWidth(), figManager.getOriginalHeight())
            figManager.setCanvas(self.cfg, canvas, 0)
            drawCanvases(None)
            return
            
        def incrementTime(event):
            figManager.incrementTime([0])
            drawCanvases(event)
            return
            
        def decreaseTime(event):
            figManager.decreaseTime([0])
            drawCanvases(event)
            return
            
        def increaseType(event):
            figS = optionBoxes.getFig()
            values = figS["values"]
            figS.set(values[values.index(figS.get())+1])
            drawCanvases(event)
            return
            
        def decreaseType(event):
            figS = optionBoxes.getFig()
            values = figS["values"]
            figS.set(values[values.index(figS.get())-1])
            drawCanvases(event)
            return
        
        def drag(event):
            canvas = figManager.getCanvas(self.cfg, 0)
            canvas.scan_dragto(event.x, event.y, gain=1)
            figManager.setCanvas(self.cfg, canvas, 0)
            return
           
        def mark(event):
            canvas = figManager.getCanvas(self.cfg, 0)
            canvas.scan_mark(event.x, event.y)
            figManager.setCanvas(self.cfg, canvas, 0)
            return
            
        def zoomIn(event):
            canvas = figManager.getCanvas(self.cfg, 0)
            if canvas:
                trueX = figManager.getCurrentX()
                trueY = figManager.getCurrentY()
                #Delete the current isntance of the image and replace with a resized one
                canvas.delete(canvas.image)
                newImage = figManager.getActiveImage(self.cfg, 0)
                currentWidth = figManager.getCurrentWidth()
                currentHeight = figManager.getCurrentHeight()
                
                newWidth = int(currentWidth+200)
                newHeight = int(currentHeight+200)
                if newWidth > 2000:
                    newWidth = 2000
                if newHeight > 2000:
                    newHeight = 2000
                
               
                trueX = -canvas.canvasx(event.x)/2 #- figManager.getOriginalWidth()/2
                trueY = -canvas.canvasy(event.y)/2 #- figManager.getOriginalHeight()/2
                
                print("Zoom In: To width "+str(newWidth)+" height "+str(newHeight)+" trueX "+str(trueX)+" trueY "+str(trueY))
                canvas.image = ImageTk.PhotoImage(newImage.resize((newWidth, newHeight), Image.BILINEAR))
                canvas.create_image(trueX, trueY, image=canvas.image, anchor="nw")
                figManager.setDimensions(trueX, trueY, newWidth, newHeight)
                
            return
            
        def zoomOut(event):
            canvas = figManager.getCanvas(self.cfg, 0)
            if canvas:
                trueX = figManager.getCurrentX()
                trueY = figManager.getCurrentY()
                #Delete the current isntance of the image and replace with a resized one
                canvas.delete(canvas.image)
                newImage = figManager.getActiveImage(self.cfg, 0)
                currentWidth = figManager.getCurrentWidth()
                currentHeight = figManager.getCurrentHeight()
                newWidth = int(currentWidth-200)
                newHeight = int(currentHeight-200)
                if newWidth < 1:
                    newWidth = 1
                if newHeight < 1:
                    newHeight = 1
                trueX = -canvas.canvasx(event.x)/2 # figManager.getOriginalWidth()/2
                trueY = -canvas.canvasy(event.y)/2 #- figManager.getOriginalHeight()/2
                print("Zoom Out: To width "+str(newWidth)+" height "+str(newHeight)+" trueX "+str(trueX)+" trueY "+str(trueY))
                canvas.image = ImageTk.PhotoImage(newImage.resize((newWidth, newHeight), Image.BILINEAR))
                canvas.create_image(trueX, trueY, image=canvas.image, anchor="nw")
                figManager.setDimensions(trueX, trueY, newWidth, newHeight)
                
            return
            
        def createOptions():
           
            
            #Define functions for Options Menus
            def updateStorm(event):
                figManager.createStorms(self.cfg)
                newValues = list(figManager.getStorms().keys())
                newValues.sort()
                stormSelect.configure(values=newValues)
                return
            def updateCases(event):
                if stormSelect.get():
                    newValues = list(figManager.getStorm(stormSelect.get()).getCases().keys())
                    newValues.sort()
                    caseSelect.configure(values=newValues)
                return
            def selectedStorm(event):
                if stormSelect.get():
                    newValues = list(figManager.getStorm(stormSelect.get()).getCases().keys())
                    newValues.sort()
                    caseSelect.configure(values=newValues)
                    caseSelect.configure(state="readonly")
                return
            def selectedCase(event):
                if stormSelect.get() and caseSelect.get():
                    newValues = list(figManager.getStorm(stormSelect.get()).getCase(caseSelect.get()).getTypes())
                    newValues.sort()
                    typeSelect.configure(values=newValues)
                    typeSelect.configure(state="readonly")
                return
                
            def selectedType1(event):
                canvas1 = canvas_for_image = tk.Canvas(img_frm, height=640, width=640)
                canvas1.grid(row=0, column=0)
                canvas1.bind("<Button-4>", zoomIn)
                canvas1.bind("<Button-5>", zoomOut)
                canvas1.bind("<ButtonRelease-1>", drag)
                canvas1.bind("<ButtonPress-1>", mark)
                canvas1.bind("<Double-Button-1>", zoomIn)
                canvas1.bind("<Double-Button-3>", zoomOut)
                
                stormS = optionBoxes.getStorm()
                caseS = optionBoxes.getCase()
                figS = optionBoxes.getFig()
                
                figures = list(figManager.getStorm(stormS.get()).getCase(caseS.get()).getOrderedFigs()[figS.get()])
                figManager.setSlot(self.cfg, figures, 0)
                figManager.setCanvas(self.cfg, canvas1, 0)
                
                images = []
                for fig in figManager.getSlot(self.cfg, 0):
                    images.append(Image.open(fig.getFullPath()).resize((figManager.getCurrentWidth(), figManager.getCurrentHeight()), Image.BILINEAR))
                    
                figManager.setImages(self.cfg, images, 0)
                
                drawCanvases(event)
                
                return
                
                
            options_frm = tk.Frame(master=gui.master)
           
            options_frm.rowconfigure([0, 1, 2], minsize=50, weight=1)
            options_frm.columnconfigure([0, 1, 2], minsize=10, weight=1)
            
            figManager.createStorms(self.cfg)
            stormSelect = ttk.Combobox(options_frm, values=[''], state="readonly")
            stormSelect.grid(row=1, column=0, padx=1)
            stormSelect.bind("<<ComboboxSelected>>", selectedStorm)
            stormSelect.bind("<Motion>", updateStorm)
            storm_label = tk.Label(options_frm, text="Storm")
            storm_label.grid(row=0, column=0, padx=1, pady=1)
            
            caseSelect = ttk.Combobox(options_frm,  values=[''], state="disable")
            caseSelect.grid(row=1, column=1, padx=1)
            caseSelect.bind("<<ComboboxSelected>>", selectedCase)
            caseSelect.bind("<Motion>", updateCases)
            case_label = tk.Label(options_frm, text="Case")
            case_label.grid(row=0, column=1, padx=1, pady=1)
            
            typeSelect = ttk.Combobox(options_frm, values=[''], state="disable")
            typeSelect.grid(row=1, column=2, padx=1)
            typeSelect.bind("<<ComboboxSelected>>", selectedType1)
            type_label = tk.Label(options_frm, text="Figure")
            type_label.grid(row=0, column=2, padx=1, pady=1)
            
            reset_btn = tk.Button(options_frm, text="Reset", command=resetFig)
            reset_btn.grid(row=2, column=0, padx=1, pady=1, sticky="nsew")
            
            options_frm.grid(row=1, column=2, sticky="ne")
            
            #Set the option boxes in the option boxes class
            optionBoxes.setStorm(stormSelect)
            optionBoxes.setCase(caseSelect)
            optionBoxes.setFig(typeSelect)
         
      
        createOptions()
        
        #Bind Arrows Keys for incrementing
        gui.master.bind("<Left>", decreaseTime)
        gui.master.bind("<Right>", incrementTime)
        gui.master.bind("<Up>", increaseType)
        gui.master.bind("<Down>", decreaseType)
        
        root.protocol("WM_DELETE_WINDOW", destroyGui)
        
        root.mainloop()
        
        return