#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 18 12:56:36 2020

@author: Wilfried Mercier - IRAP

Configuration window to generate new projections.
"""

import threading
import os
import os.path                           as     opath
import numpy                             as     np
import matplotlib.pyplot                 as     plt
import tkinter                           as     tk
from   tkinter.filedialog                import askopenfilename
from   matplotlib.figure                 import Figure
from   matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from   .entry                            import Entry
from   .scale                            import Scale
from   .errorMessage                     import ErrorMessage
from   backend.tools                     import RunProjection

class ConfigWindow(tk.Toplevel):
    '''Configuration window to generate new projections.'''

    def __init__(self, parent, main, root, *args, winProperties={}, entryProperties={}, textProperties={}, title='None', **kwargs):
        '''
        Init function.
        
        Mandatory parameters
        --------------------
            main : tkinter widget
                main parent window
            parent : tkinter widget
                parent widget
            root : tkinter widget
                root object

        Optional parameters
        -------------------
            entryProperties : dict
                properties to be passed to the entries Default is an empty dict.
            textProperties : dict
                properties to be passed to the Labels. Default is an empty dict.
            title : str
                window title. Default is 'None'.
            winProperties : dict
                properties to be passed to the Toplevel window. Default is an empty dict.
        '''
        
        # Setup attributes
        self.main            = main
        self.parent          = parent
        self.root            = root
        self.name            = title
        
        self.runState        = False
        
        self.xres            = 720
        self.yres            = 720
        
        # Dictionnary with flags to know when a value is incorrect before launching the projection routine
        self.error           = {'step'          : True,
                                'res'           : False,
                                'inputFile'     : True,
                                'projectName'   : True
                               }
        
        # Layout properties
        self.winProperties   = winProperties
        self.entryProperties = entryProperties
        self.textProperties  = textProperties
        
        # Attributes related to the matplotlib graph
        self.data            = None
        self.canvas          = None
        self.crosshair       = None
        
        # Allowed file types and file extensions when loading the image
        self.filetypes       = [('PNG', '*.png'), ('JEPG', '*.jpeg'), ('JPG', '*.jpg'), ('GIF', '*.gif')]
        self.extensions      = [i[1].strip('.*').lower() for i in self.filetypes]
        
        ################################################
        #              Default properties              #
        ################################################
            
        if 'bg' not in self.winProperties:
            self.winProperties['bg']    = self.main.bg
            
        if 'font' not in self.textProperties:
            self.textProperties['font'] = (self.main.font, 11, 'bold')
            
        if 'fg' not in self.entryProperties:
            self.entryProperties['fg']  = 'black'
            
        super().__init__(self.root, **winProperties)
        
        # Need to handle MAC and Windows cases
        try:
            self.wm_attributes('-type', ['dialog'])
        except:
            pass
        
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.title(self.name)
        
        # Setup window size
        size          = (850, 220)
        self.geometry('%dx%d+%d+%d' %(size[0], size[1], (self.root.winfo_screenwidth()-size[0])//2, (self.root.winfo_screenheight()-size[1])//2))
        
        ########################################
        #           Scale properties           #
        ########################################
        
        hoverParams   = {'highlightbackground':'RoyalBlue2',     'activebackground':'RoyalBlue2'}
        normalState   = {'troughcolor':'lavender',               'highlightbackground':self.winProperties['bg'], 'cursor':'hand1', 'activebackground':'RoyalBlue2'}
        errorState    = {'troughcolor':'lavender',               'highlightbackground':'firebrick1',             'cursor':'hand1', 'activebackground':'black'}
        disabledState = {'troughcolor':self.winProperties['bg'], 'highlightbackground':self.winProperties['bg'], 'cursor':'arrow', 'activebackground':'black'}
        
        ###################################
        #          Setup widgets          #
        ###################################
        
        '''
        Master frames
        -------------
            self.masterFrame : main frame containing all the others
            self.line1       : 1st line frame
            self.line2       : 2nd line frame
            self.dposFrame   : frame containing the default position widgets
            self.entryFrame  : frame containing the entry widgets on the second column
            self.line2col2   : frame for the second line of the second column
        '''
        
        self.masterFrame = tk.Frame(     self,             bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.line1       = tk.Frame(     self.masterFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.line2       = tk.Frame(     self.masterFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        
        self.entryFrame  = tk.LabelFrame(self.line1,       bg=self.winProperties['bg'], bd=0, highlightthickness=0, text='Project properties', font=self.textProperties['font'])
        
        self.line11      = tk.Frame(     self.entryFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        
        self.dposFrame   = tk.LabelFrame(self.line2,       bg=self.winProperties['bg'], bd=0, highlightthickness=0, text='Default position',   font=self.textProperties['font'])
        self.line2col2   = tk.Frame(     self.line2,       bg=self.winProperties['bg'], bd=1, highlightthickness=0)
        
        '''
        Project name
        ------------
            self.nameFrame : frame containing widgets relative to typing the project name
        '''
        
        self.nameFrame   = tk.Frame(self.line11,      bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.nameLabel   = tk.Label(self.nameFrame,   bg=self.winProperties['bg'], bd=0, highlightthickness=0, text='Project name', anchor=tk.W, font=(self.main.font, 10))
        self.nameEntry   = Entry(   self.nameFrame, self, self.root, dtype=str, defaultValue='', 
                                    traceCommand=self.checkName,
                                    **entryProperties)
        self.nameEntry.triggerError()
        
        '''
        Open rectangular input file  
        ---------------------------
            self.inputFame   : frame containing widgets relative to selecting an input file
            self.inputFrame1 : frame for the label widget
            self.inputFrame2 : frame for the entry + button widgets
        '''
        
        self.inputFrame  = tk.Frame(self.entryFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.inputFrame1 = tk.Frame(self.inputFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.inputFrame2 = tk.Frame(self.inputFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        
        self.inputLabel  = tk.Label(self.inputFrame1, bg=self.winProperties['bg'], bd=0, highlightthickness=0, text='Input file (equirectangular projection)', 
                                    anchor=tk.W, font=(self.main.font, 10))
        
        self.inputEntry  = Entry(   self.inputFrame2, self, self.root, dtype=str, defaultValue='',
                                    traceCommand=self.loadInput, **entryProperties)
        self.inputEntry.triggerError()
        
        self.inputButton = tk.Button(self.inputFrame2, image=self.main.iconDict['FOLDER_17'], 
                                     bd=0, bg=self.winProperties['bg'], highlightbackground=self.winProperties['bg'], relief=tk.FLAT, activebackground='black', 
                                     command=lambda *args, **kwargs: self.askLoad(title='Select a equirectangular surface image...', filetypes=self.filetypes))
        
        # Output resolution widgets
        self.resFrame     = tk.Frame(self.line11, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        
        self.resLabel     = tk.Label(self.resFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0, text='Output file resolution (widthxheight)', 
                             anchor=tk.W, font=(self.main.font, 10))
        
        self.resEntry     = Entry(self.resFrame, self, self.root, dtype=str, defaultValue='720x720',
                                  traceCommand=self.checkResolution, **entryProperties)
        
        
        '''
        Number of threads widgets
        -------------------------
            self.threadAll   : frame for all the thread widgets
            self.thLablFrame : frame for the label of the thread widgets
            self.threadFrame : frame for the buttons+entry of the thread widgets
        '''
        
        self.threadAll   = tk.Frame( self.line2col2,  bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        
        self.thLablFrame = tk.Frame( self.threadAll,  bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.threadLabel = tk.Label( self.thLablFrame, text='Number of threads', bg=self.winProperties['bg'], font=(self.main.font, 10), anchor=tk.W)
        
        self.threadFrame = tk.Frame( self.threadAll,  bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        
        self.minButton   = tk.Button(self.threadFrame, bd=0, bg=self.winProperties['bg'], highlightbackground=self.winProperties['bg'], activebackground='black', state='disabled',
                                     text='-', font=('fixed', 10, 'bold'), activeforeground='white',
                                     command=lambda *args, **kwargs: None)
        
        self.maxButton   = tk.Button(self.threadFrame, bd=0, bg=self.winProperties['bg'], highlightbackground=self.winProperties['bg'], activebackground='black',
                                     text='+', font=('fixed', 10, 'bold'), activeforeground='white',
                                     command=lambda *args, **kwargs: None)
        
        self.threadCount = tk.Label( self.threadFrame, width=3, justify=tk.CENTER, fg=self.entryProperties['fg'], bg=self.winProperties['bg'], text=1)
        
        '''
        Longitude and latitude steps widgets
        ------------------------------------
            self.stepAll      : frame for all the step widgets
            self.stepLblFrame : frame for the label of the step widgets
            self.stepFrame    : frame for the entry of the step widgets
        '''
        
        self.stepAll      = tk.Frame( self.line2col2,    bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        
        self.stepLblFrame = tk.Frame( self.stepAll,      bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.stepLabel    = tk.Label( self.stepLblFrame, bg=self.winProperties['bg'], text='Step (°)', font=(self.main.font, 10), anchor=tk.W)
        
        self.stepFrame    = tk.Frame( self.stepAll,      bg=self.winProperties['bg'],  bd=0, highlightthickness=0)
        self.stepEntry    = Entry(    self.stepFrame, self, self.root, dtype=float, defaultValue=0, width=3, justify=tk.CENTER, **entryProperties,
                                      traceCommand=lambda *args, **kwargs: self.updateStep(*args, **kwargs))
        self.stepEntry.triggerError()
        self.stepEntry.configure(fg='firebrick1')
        
        # Run widgets
        self.runButton    = tk.Button(self.line2col2,    bg=self.winProperties['bg'],  bd=0, image=self.parent.iconDict['RUN'],
                                      highlightthickness=0, highlightbackground=self.winProperties['bg'], relief=tk.FLAT, activebackground=self.winProperties['bg'],
                                      command=self.run)
        
        # Default position
        
        self.dposLatFrame = tk.Frame(self.dposFrame,    bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.dposLonFrame = tk.Frame(self.dposFrame,    bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        
        self.dposLatLabel = tk.Label(self.dposLatFrame, text='Latitude',  bg=self.winProperties['bg'], font=(self.main.font, 10), anchor=tk.W)
        self.dposLonLabel = tk.Label(self.dposLonFrame, text='Longitude', bg=self.winProperties['bg'], font=(self.main.font, 10), anchor=tk.W)
        
        self.dposLatScale = Scale(   self.dposLatFrame, self, self.root, disable=True, initValue=0,
                                     hoverParams=hoverParams, normalStateParams=normalState, errorStateParams=errorState, disabledStateParams=disabledState,
                                     length=200, width=12, orient='horizontal', from_=-90, to=90, resolution=0.1, showvalue=False, sliderrelief=tk.FLAT,
                                     bg=self.winProperties['bg'], bd=1, highlightthickness=1, highlightbackground=self.winProperties['bg'], troughcolor=self.winProperties['bg'],
                                     command=lambda *args, **kwargs: self.sliderUpdate(self.dposLatScale, *args, **kwargs))
        self.sliderUpdate(self.dposLatScale)
        
        self.dposLonScale = Scale(   self.dposLonFrame, self, self.root, disable=True, initValue=0,
                                     hoverParams=hoverParams, normalStateParams=normalState, errorStateParams=errorState, disabledStateParams=disabledState,
                                     length=200, width=12, orient='horizontal', from_=-180, to=180, resolution=0.1, showvalue=False, sliderrelief=tk.FLAT,
                                     bg=self.winProperties['bg'], bd=1, highlightthickness=1, highlightbackground=self.winProperties['bg'], troughcolor=self.winProperties['bg'],
                                     command=lambda *args, **kwargs: self.sliderUpdate(self.dposLonScale, *args, **kwargs))
        self.sliderUpdate(self.dposLonScale)
        
        #######################################################################
        #                               Bindings                              #
        #######################################################################

        # Buttons bindings
        self.minButton.bind('<Button-1>', lambda *args, **kwargs: self.decreaseThread(*args, **kwargs) if self.minButton['state'] != 'disabled' else None)
        self.maxButton.bind('<Button-1>', lambda *args, **kwargs: self.increaseThread(*args, **kwargs) if self.maxButton['state'] != 'disabled' else None)
        
        
        ##########################################################
        #                     Drawing frames                     #
        ##########################################################
        
        # Resolution widgets
        self.resLabel.pack(side=tk.TOP,       fill='x', expand=True)
        self.resEntry.pack(side=tk.BOTTOM,    fill='x', expand=True)
        self.resFrame.pack(side=tk.LEFT,      fill='x', padx=10, pady=12)
        
        # Project name widgets
        self.nameLabel.pack(side=tk.TOP,      fill='x', expand=True)
        self.nameEntry.pack(side=tk.BOTTOM,   fill='x', expand=True)
        self.nameFrame.pack(side=tk.TOP,      fill='x', expand=True, padx=10, pady=12)
        
        # Open file widgets
        self.inputLabel.pack( side=tk.LEFT,   fill='x', expand=True)
        self.inputFrame1.pack(side=tk.TOP,    fill='x', expand=True)
        
        self.inputEntry.pack( side=tk.LEFT,   fill='x', expand=True)
        self.inputButton.pack(side=tk.RIGHT,            padx=10)
        self.inputFrame2.pack(side=tk.BOTTOM, fill='x', expand=True)
        self.inputFrame.pack( side=tk.BOTTOM, fill='x', padx=10)
        
        # Thread widgets
        self.threadLabel.pack(side=tk.LEFT)
        
        self.minButton.pack(  side=tk.LEFT)
        self.threadCount.pack(side=tk.LEFT, padx=5)
        self.maxButton.pack(  side=tk.LEFT)
        
        self.thLablFrame.pack(side=tk.TOP)
        self.threadFrame.pack(side=tk.BOTTOM)
        self.threadAll.pack(  side=tk.LEFT, padx=10, anchor=tk.N+tk.W)
        
        # Step widgets
        self.stepLabel.pack(   side=tk.LEFT)
        self.stepEntry.pack(   side=tk.BOTTOM, pady=5)
        self.stepLblFrame.pack(side=tk.TOP)
        self.stepFrame.pack(   side=tk.BOTTOM)
        self.stepAll.pack(     side=tk.LEFT, padx=10, anchor=tk.N+tk.E)
        
        # Run widget
        self.runButton.pack(   side=tk.RIGHT, padx=10, anchor=tk.CENTER)
        self.runButton.config(state=tk.DISABLED)
        
        # Default position widgets
        self.dposLatLabel.pack(side=tk.TOP,    fill='x', expand=True)
        self.dposLatScale.pack(side=tk.BOTTOM, fill='x', expand=True)
        
        self.dposLonLabel.pack(side=tk.TOP,    fill='x', expand=True)
        self.dposLonScale.pack(side=tk.BOTTOM, fill='x', expand=True)
        
        self.dposLatFrame.pack(side=tk.LEFT,   fill='x', padx=15, pady=10, expand=True)
        self.dposLonFrame.pack(side=tk.LEFT,   fill='x',          pady=10, expand=True)
        
        # Master frames
        self.entryFrame.pack(  side=tk.LEFT,   fill='x', padx=3,           expand=True)
        self.line1.pack(       side=tk.TOP,    fill='x')
        self.line11.pack(      side=tk.LEFT,   fill='x',                   expand=True)
        
        self.dposFrame.pack(   side=tk.LEFT,   fill='x', padx=3, expand=True)
        self.line2col2.pack(   side=tk.LEFT ,  fill='x', padx=3,  pady=5,  anchor=tk.S)
        self.line2.pack(       side=tk.LEFT,   fill='x',          pady=10, expand=True)
        
        self.masterFrame.pack( side=tk.TOP,    fill='x',          pady=5)
        
        return
    
    ########################################################
    #            Resolution widgets interaction            #
    ########################################################
    
    def checkResolution(self, *args, **kwargs):
        '''Actions taken when the resolution is changed.'''
        
        resolution            = self.resEntry.value.split('x')
        
        # If syntax is not 'n1xn2' trigger error
        if len(resolution)!=2:
            self.resEntry.configure(fg='firebrick1')
            self.resEntry.triggerError()
            self.error['res'] = True
            return
            
        # If non numeric characters appear, trigger error
        try:
            xres              = int(resolution[0])
            yres              = int(resolution[1])
        except ValueError:
            self.resEntry.configure(fg='firebrick1')
            self.resEntry.triggerError()
            self.error['res'] = True
            return
        
        # If negative integers, trigger error
        if xres <= 0 or yres <=0:
            self.resEntry.configure(fg='firebrick1')
            self.resEntry.triggerError()
            self.error['res'] = True
            return
        else:
            self.resEntry.configure(fg=self.entryProperties['fg'])
            self.xres         = xres
            self.yres         = yres
            self.resEntry.removeError()
            self.error['res'] = True
        
        self.checkRun()
        return
    
    
    #######################################
    #          Name interactions          #
    #######################################
    
    def checkName(self, *args, **kwargs):
        '''Actions taken when the name is changed.'''
        
        if self.nameEntry.value != '':
            self.nameEntry.removeError()
            self.error['projectName'] = False
        else:
            self.nameEntry.triggerError()
            self.error['projectName'] = True
            
        self.checkRun()
        return
    
    
    #######################################
    #          Step interactions          #
    #######################################
    
    def updateStep(self, *args, **kwargs):
        '''Actions taken when the value of the step entry is updated.'''
        
        value   = self.stepEntry.value
        
        if value== '' or float(value)<=0 or float(value)>45:
            self.stepEntry.triggerError()
            self.stepEntry.configure(fg='firebrick1')
            self.error['step'] = True
        else:
            self.stepEntry.removeError()
            self.stepEntry.configure(fg=self.entryProperties['fg'])
            self.error['step'] = False
            
        self.checkRun()
        return
    
    
    ############################################
    #           Thread interactions            #
    ############################################
    
    def decreaseThread(self, *args, **kwargs):
        '''Decrease by 1 the number of threads.'''
        
        value     = int(self.threadCount.cget('text'))
        if value > 1:
            self.threadCount.configure(text=value-1)
            
        self.updateThreadButtons()
        return
    
    def increaseThread(self, *args, **kwargs):
        '''Decrease by 1 the number of threads.'''
        
        value     = int(self.threadCount.cget('text'))
        if value < self.main.cpuCount:
            self.threadCount.configure(text=value+1)
            
        self.updateThreadButtons()
        return
    
    def updateThreadButtons(self, *args, **kwargs):
        '''Update the state of the thread buttons.'''
        
        if   int(self.threadCount.cget('text')) == 1:
            self.minButton.config(state='disabled')
        elif int(self.threadCount.cget('text')) == self.main.cpuCount:
            self.maxButton.config(state='disabled')
        else:
            if self.minButton.cget('state') not in ['normal', 'active']:
                self.minButton.config(state='normal')
            if self.maxButton.cget('state') not in ['normal', 'active']:
                self.maxButton.config(state='normal')
            
        return
        
        
    ############################################
    #           Sliders interactions           #
    ############################################
    
    def sliderUpdate(self, slider, *args, **kwargs):
        '''Actions taken when the slider is updated.'''
        
        value = slider.get()
        
        if slider is self.dposLatScale:
            self.dposLatLabel.configure(text='Latitude: %.1f°' %value)        
            self.updateCrosshair('black')
                
        elif slider is self.dposLonScale:
            self.dposLonLabel.configure(text='Longitude: %.1f°' %value)
            self.updateCrosshair('black')
            
        self.checkRun()
        return
    
    #######################################
    #           Loading file(s)           #
    #######################################

    def askLoad(self, *args, title='', filetypes=('All files', '*.*'), **kwargs):
        '''Asking which file to open.'''
        
        try:
            # Load YAML file
            fname = askopenfilename(initialdir=self.main.loadPath, title=title, filetypes=tuple([['All files', '*.*']] + filetypes))
        except:
            print('Failed to open file...')
            return None
        
        if fname == () or fname == '':
            return None
        else:
            self.main.loadPath = opath.dirname(fname)
            self.inputEntry.var.set(fname)
            return fname

    def loadInput(self, *args, **kwargs):
        '''Load the input file into the matplotlib frame and write its name into the entry widget.'''
        
        def okFunction(*args, **kwargs):
            
            try:
                # Change entry text color to ok 
                self.inputEntry.configure(fg=self.entryProperties['fg'])
                
                # Change out to error state
                self.inputEntry.removeError()
                
                # Resize window
                size = (850, 650)
                self.geometry('%dx%d' %(size[0], size[1]))
                
                # Update sliders
                for widget in [self.dposLatScale, self.dposLonScale]:
                    widget.normalState()
                
                # Load graph onto the window
                self.makeGraph()
            except:
                print('An error occured while loading data.')
            
            return
        
        def errorFunction(*args, **kwargs):
            
            # Change entry text color to error
            self.inputEntry.configure(fg='firebrick1')
            
            # Change to error state
            self.inputEntry.triggerError()
            
            # Hide graph in the window
            self.hideGraph()
            
            # Resize window
            size = (850, 220)
            self.geometry('%dx%d' %(size[0], size[1]))
            
            # Update sliders
            for widget in [self.dposLatScale, self.dposLonScale]:
                widget.disabledState()
                
            self.checkRun()
            return

        # Retrieve name written in Entry
        fname = self.inputEntry.var.get()
        
        # If empty string, set back the default foreground color
        if fname == '':
            self.inputEntry.configure(fg=self.entryProperties['fg'])
            errorFunction()
            self.error['inputFile'] = True
            self.checkRun()
            return
        
        # If no file was selected or if an error occured, do nothing
        elif fname is None:
            return
        
        # Otherwise check whether the file exists and apply the correct function
        else:
            self.checkFile(fname, okFunction=okFunction, errorFunction=errorFunction)
            self.checkRun()
        return
        

    ###################################################
    #                  Axis methods                   #
    ###################################################
    
    def makeAxis(self, *args, **kwargs):
        '''Creating a new axis.'''
        
        self.ax       = self.figure.add_subplot(111)
        self.setAxis()
        return
    
    def updateAxis(self, *args, **kwargs):
        '''Update the data in the axis.'''
        
        self.setAxis()
        return
    
    def updateCrosshair(self, color, *args, **kwargs):
        '''Update the crosshair.'''
        
        if self.data is not None:

            xpos = self.xlim[0] + (float(self.dposLonScale.get()) + 180)/360 * (self.xlim[1] - self.xlim[0])
            ypos = self.ylim[1] - (float(self.dposLatScale.get()) + 90 )/180 * (self.ylim[1] - self.ylim[0])
            if self.crosshair is None:
                self.crosshair = self.ax.plot([xpos], [ypos], marker='x', markersize=15, color=color, markeredgewidth=5)[0]
            else:
                self.crosshair.set_xdata([xpos])
                self.crosshair.set_ydata([ypos])
                self.crosshair.set_color(color)
            
            self.canvas.draw_idle()
        return
        
    def setAxis(self, *args, **kwargs):
        '''Set the axis for a new figure.'''
        
        self.ax.autoscale_view(True,True,True)
        self.ax.clear()
        self.ax.yaxis.set_ticks_position('none')
        self.ax.yaxis.set_ticks([])
        
        self.ax.xaxis.set_ticks_position('none')
        self.ax.xaxis.set_ticks([])
        
        # Default empty image
        if self.data is None:
            print('No data loaded...')
            self.data = [[0]*4]*2
        
        self.im       = self.ax.imshow(self.data, cmap='Greys')
        self.xlim     = self.ax.get_xlim()
        self.ylim     = self.ax.get_ylim()[::-1]
        return

    
    ###################################################
    #                  Graph methods                  #
    ###################################################
    
    def hideGraph(self, *args, **kwargs):
        '''Hide the graph frame if no data is loaded.'''
        
        if self.canvas is not None:
            self.crosshair = None
            self.figframe.pack_forget()
        return
    
    def makeGraph(self, *args, **kwargs):
        '''Generate a matplotlib graph with the image loaded.'''
            
        # RGB array with image data
        self.data         = plt.imread(self.inputEntry.var.get(), format=opath.splitext(self.inputEntry.var.get())[-1])
        
        if self.canvas is None:
            # Get background color and convert in matplotlib RGB values
            color         = [i/255**2 for i in self.root.winfo_rgb(self.winProperties['bg'])]
            
            self.figure   = Figure(figsize=(20, 10), constrained_layout=True, facecolor=color)
            self.makeAxis()
            
            # Canvas holding figure
            self.figframe = tk.Frame( self, bg='lavender', bd=1, highlightthickness=0)
            self.canvas   = FigureCanvasTkAgg(self.figure, master=self.figframe)
            self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        else:
            self.updateAxis()
            
        # Draw frame containing the figure
        self.canvas.draw()
        self.figframe.pack(side=tk.BOTTOM, fill='x', expand=True)
        
        # Set crosshair
        self.updateCrosshair('black')

        return
        

    #################################################
    #            Miscellaneous functions            #
    #################################################
        
    def close(self, *args, **kwargs):
        '''Actions taken when the window is closed.'''
        
        self.main.confButton.configure(state=tk.NORMAL)
        self.withdraw()
        return True
    
    def checkFile(self, file, *args, okFunction=lambda *args, **kwargs: None, errorFunction=lambda *args, **kwargs: None, **kwargs):
        '''
        Check whether a file exists and has the correct type and apply the correct function depending on the result.

        # Arrays of latitude and longitude where to compute the projections
        Mandatory parameters
        --------------------
            file : str
                file to check the existence
                
        Optional parameters
        -------------------
            okFunction : function
                Function to apply when the file exists
            errorFunction : function
                Function to apply when the file does not exist
                
        Return the value returned by the correct function.
        '''
        
        if not isinstance(file, str):
            raise TypeError('File must be a string.')
        
        if opath.exists(file) and file.split('.')[-1].lower() in self.extensions:
            self.error['inputFile'] = False
            return okFunction()
        else:
            self.error['inputFile'] = True
            return errorFunction()
        return
    
    def checkRun(self, *args, **kwargs):
        '''Check whether the projection can be run or not.'''
        
        print('hey2')
        if not self.runState:            
            if any(self.error.values()):
                self.runButton.configure(state=tk.DISABLED)
                self.runButton.unbind('<Enter>')
                self.runButton.unbind('<Leave>')
            else:
                self.runButton.configure(state=tk.NORMAL)
                self.runButton.bind(  '<Enter>', lambda *args, **kwargs: self.parent.iconDict['RUN'].configure(foreground='black'))
                self.runButton.bind(  '<Leave>', lambda *args, **kwargs: self.parent.iconDict['RUN'].configure(foreground='white'))
        else:
            print("jey3")
            self.runButton.bind(      '<Enter>', lambda *args, **kwargs: self.parent.iconDict['CHECK'].configure(foreground='black'))
            self.runButton.bind(      '<Leave>', lambda *args, **kwargs: self.parent.iconDict['CHECK'].configure(foreground='firebrick1'))
        return

    def setTitle(self, title, *args, **kwargs):
        '''
        Set a new title for the window.

        Parameters
        ----------
            title : str
                the new title
        '''
        
        if self.name != title:
            self.name = title
            self.title(self.name)
        return
    
    
    #####################################
    #            Run method             #
    #####################################
        
    def run(self, *args, **kwargs):
        '''Run the projection.'''
        
        if self.runState:
            self.runState = False
            for i in self.thread.threads:
                i.ok = False
            self.runButton.config(cursor='arrow', image=self.main.iconDict['RUN'])
            self.checkRun()
            print('Threads stopped')
        else:
            # Setup the function parameters for the projection
            data         = self.data
            
            # Generate the file and directory names
            name         = self.nameEntry.value
            directory    = opath.join(opath.dirname(self.inputEntry.value), name)
            
            # Check that if directory exists, it only contain config files
            if opath.isdir(directory):
                files    = [f for f in os.listdir(directory) if opath.isfile(opath.join(directory, f))]
                if any(['.yaml' not in i for i in files]):
                    ErrorMessage(self, self.root, text='Directory %s is not empty.' %directory)
                    return
            
            step         = float(self.stepEntry.value)
            numThreads   = int(self.threadCount.cget('text'))
            
            # Init pos must be given in grid units, so we must convert the given values to the closest one
            latInit       = self.dposLatScale.get()
            longInit      = self.dposLonScale.get()
            
            allLong       = np.arange(-180, 180, step)
            allLat        = np.arange(-90,  90+step,  step)
            initPos       = [int(np.argmin((allLong-longInit)**2)), int(np.argmin((allLat-latInit)**2))]
            
            size          = (self.xres, self.yres)
            
            # Change button icon first 
            self.config(cursor='watch')
            self.runState = True
            self.runButton.config(cursor='arrow', image=self.main.iconDict['CHECK'])
            print('hey')
            self.checkRun()
            
            # Run thread
            self.thread   = RunProjection(data, directory, name, step, numThreads, initPos=initPos, allLat=allLat, allLong=allLong, size=size)
            self.thread.start()
            self.thread.join()
            
            # Set back the icon
            self.config(cursor='arrow')
            self.runState = False
            self.runButton.config(cursor='arrow', image=self.main.iconDict['RUN'])
            self.checkRun()
        return

