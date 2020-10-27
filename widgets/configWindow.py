#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 18 12:56:36 2020

@author: Wilfried Mercier - IRAP

Configuration window to generate new projections.
"""

import os.path                           as     opath
import matplotlib.pyplot                 as     plt
import tkinter                           as     tk
from   tkinter.filedialog                import askopenfilename
from   matplotlib.figure                 import Figure
from   matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from   .entry                            import Entry

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
        
        # Dictionnary with flags to know when a value is incorrect before launching the projection routine
        self.error           = {'thread':False}
        
        # Layout properties
        self.winProperties   = winProperties
        self.entryProperties = entryProperties
        self.textProperties  = textProperties
        
        # Attributes related to the matplotlib graph
        self.data            = None
        self.canvas          = None
        
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
        size             = (850, 220)
        self.geometry('%dx%d+%d+%d' %(size[0], size[1], (self.root.winfo_screenwidth()-size[0])//2, (self.root.winfo_screenheight()-size[1])//2))
        
        ###################################
        #          Setup widgets          #
        ###################################
        
        '''
        Master frames
        -------------
            self.masterFrame : main frame containing all the others
            self.line1       : 1st line frame
            self.line2       : 2nd line frame
            self.boundFrame  : frame containing the latitude and longitude bounds widgets
            self.dposFrame   : frame containing the default position widgets
            self.entryFrame  : frame containing the entry widgets on the second column
            self.line2col2   : frame for the second line of the second column
        '''
        
        self.masterFrame = tk.Frame(     self,             bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.line1       = tk.Frame(     self.masterFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.line2       = tk.Frame(     self.masterFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        
        self.boundFrame  = tk.LabelFrame(self.line1,       bg=self.winProperties['bg'], bd=0, highlightthickness=0, text='Setup bounds',       font=self.textProperties['font'])
        self.entryFrame  = tk.LabelFrame(self.line1,       bg=self.winProperties['bg'], bd=0, highlightthickness=0, text='Project properties', font=self.textProperties['font'])
        
        self.dposFrame   = tk.LabelFrame(self.line2,       bg=self.winProperties['bg'], bd=0, highlightthickness=0, text='Default position',   font=self.textProperties['font'])
        self.line2col2   = tk.Frame(     self.line2,       bg=self.winProperties['bg'], bd=1, highlightthickness=0)
        
        '''
        Project name
        ------------
            self.nameFrame : frame containing widgets relative to typing the project name
        '''
        
        self.nameFrame   = tk.Frame(self.entryFrame,  bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.nameLabel   = tk.Label(self.nameFrame,   bg=self.winProperties['bg'], bd=0, highlightthickness=0, text='Project name', anchor=tk.W, font=(self.main.font, 10))
        self.nameEntry   = Entry(   self.nameFrame, self, self.root, dtype=str, defaultValue='', **entryProperties)
        
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
        
        self.inputButton = tk.Button(self.inputFrame2, image=self.main.iconDict['FOLDER_17'], 
                                     bd=0, bg=self.winProperties['bg'], highlightbackground=self.winProperties['bg'], relief=tk.FLAT, activebackground='black', 
                                     command=lambda *args, **kwargs: self.askLoad(title='Select a equirectangular surface image...', filetypes=self.filetypes))
        
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
        
        self.threadEntry = Entry(    self.threadFrame, self, self.root, dtype=int, defaultValue=1, width=3, justify=tk.CENTER, **entryProperties,
                                     traceCommand=lambda *args, **kwargs: self.updateThreadValue(*args, **kwargs))
        self.threadEntry.configure(fg='black')
        
        # Latitude and longitude limits widgets
        
        self.latMinframe  = tk.Frame( self.boundFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.latMaxframe  = tk.Frame( self.boundFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        
        self.longMinframe = tk.Frame( self.boundFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.longMaxframe = tk.Frame( self.boundFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        
        self.latMinLabel  = tk.Label( self.latMinframe,  text='Minimum latitude',  bg=self.winProperties['bg'], font=(self.main.font, 10), anchor=tk.W)
        self.latMaxLabel  = tk.Label( self.latMaxframe,  text='Maximum latitude',  bg=self.winProperties['bg'], font=(self.main.font, 10), anchor=tk.W)
        
        self.longMinLabel = tk.Label( self.longMinframe, text='Minimum longitude', bg=self.winProperties['bg'], font=(self.main.font, 10), anchor=tk.W)
        self.longMaxLabel = tk.Label( self.longMaxframe, text='Maximum longitude', bg=self.winProperties['bg'], font=(self.main.font, 10), anchor=tk.W)
        
        self.latMinScale  = tk.Scale( self.latMinframe, length=200, width=12, orient='horizontal', from_=-90, to=90, resolution=0.1,
                                     cursor='arrow', showvalue=False, sliderrelief=tk.FLAT,
                                     bg=self.winProperties['bg'], bd=1, highlightthickness=1, highlightbackground=self.winProperties['bg'], troughcolor=self.winProperties['bg'], activebackground='black',
                                     state=tk.DISABLED,
                                     command=lambda *args, **kwargs: self.sliderUpdate(self.latMinScale, *args, **kwargs))
        
        self.latMaxScale  = tk.Scale( self.latMaxframe, length=200, width=12, orient='horizontal', from_=-90, to=90, resolution=0.1,
                                     cursor='arrow', showvalue=False, sliderrelief=tk.FLAT,
                                     bg=self.winProperties['bg'], bd=1, highlightthickness=1, highlightbackground=self.winProperties['bg'], troughcolor=self.winProperties['bg'], activebackground='black',
                                     state=tk.DISABLED,
                                     command=lambda *args, **kwargs: self.sliderUpdate(self.latMaxScale, *args, **kwargs))
        
        
        self.longMinScale = tk.Scale( self.longMinframe, length=200, width=12, orient='horizontal', from_=-180, to=180, resolution=0.1,
                                     cursor='arrow', showvalue=False, sliderrelief=tk.FLAT,
                                     bg=self.winProperties['bg'], bd=1, highlightthickness=1, highlightbackground=self.winProperties['bg'], troughcolor=self.winProperties['bg'], activebackground='black',
                                     state=tk.DISABLED,
                                     command=lambda *args, **kwargs: self.sliderUpdate(self.longMinScale, *args, **kwargs))
        
        self.longMaxScale = tk.Scale( self.longMaxframe, length=200, width=12, orient='horizontal', from_=-180, to=180, resolution=0.1,
                                     cursor='arrow', showvalue=False, sliderrelief=tk.FLAT,
                                     bg=self.winProperties['bg'], bd=1, highlightthickness=1, highlightbackground=self.winProperties['bg'], troughcolor=self.winProperties['bg'], activebackground='black',
                                     state=tk.DISABLED,
                                     command=lambda *args, **kwargs: self.sliderUpdate(self.longMaxScale, *args, **kwargs))
        
        # Default position
        
        self.dposLatFrame = tk.Frame(     self.dposFrame,    bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.dposLonFrame = tk.Frame(     self.dposFrame,    bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        
        self.dposLatLabel = tk.Label(self.dposLatFrame, text='Latitude',  bg=self.winProperties['bg'], font=(self.main.font, 10), anchor=tk.W)
        self.dposLonLabel = tk.Label(self.dposLonFrame, text='Longitude', bg=self.winProperties['bg'], font=(self.main.font, 10), anchor=tk.W)
        
        self.dposLatScale = tk.Scale(self.dposLatFrame, length=200, width=12, orient='horizontal', from_=-90, to=90, resolution=0.1,
                                     cursor='arrow', showvalue=False, sliderrelief=tk.FLAT,
                                     bg=self.winProperties['bg'], bd=1, highlightthickness=1, highlightbackground=self.winProperties['bg'], troughcolor=self.winProperties['bg'], activebackground='black',
                                     state=tk.DISABLED,
                                     command=lambda *args, **kwargs: None)
        
        self.dposLonScale = tk.Scale(self.dposLonFrame, length=200, width=12, orient='horizontal', from_=-90, to=90, resolution=0.1,
                                     cursor='arrow', showvalue=False, sliderrelief=tk.FLAT,
                                     bg=self.winProperties['bg'], bd=1, highlightthickness=1, highlightbackground=self.winProperties['bg'], troughcolor=self.winProperties['bg'], activebackground='black',
                                     state=tk.DISABLED,
                                     command=lambda *args, **kwargs: None)
        
        
        #######################################################################
        #                               Bindings                              #
        #######################################################################

        # Buttons bindings
        self.minButton.bind('   <Button-1>', lambda *args, **kwargs: self.decreaseThread(*args, **kwargs))
        self.maxButton.bind('   <Button-1>', lambda *args, **kwargs: self.increaseThread(*args, **kwargs))
        
        
        ##########################################################
        #                     Drawing frames                     #
        ##########################################################
        
        # Project name widgets
        self.nameLabel.pack(side=tk.TOP,      fill='x', expand=True)
        self.nameEntry.pack(side=tk.BOTTOM,   fill='x', expand=True)
        self.nameFrame.pack(side=tk.TOP,      fill='x', padx=10, pady=12)
        
        # Open file widgets
        self.inputLabel.pack( side=tk.LEFT,   fill='x', expand=True)
        self.inputFrame1.pack(side=tk.TOP,    fill='x', expand=True)
        
        self.inputEntry.pack( side=tk.LEFT,   fill='x', expand=True)
        self.inputButton.pack(side=tk.RIGHT,            padx=10)
        self.inputFrame2.pack(side=tk.BOTTOM, fill='x', expand=True)
        self.inputFrame.pack( side=tk.TOP,    fill='x', padx=10, )
        
        # Thread widgets
        self.threadLabel.pack(side=tk.LEFT)
        
        self.minButton.pack(  side=tk.LEFT)
        self.threadEntry.pack(side=tk.LEFT, padx=5)
        self.maxButton.pack(  side=tk.LEFT)
        
        self.thLablFrame.pack(side=tk.TOP)
        self.threadFrame.pack(side=tk.BOTTOM)
        self.threadAll.pack(  side=tk.LEFT, padx=10, anchor=tk.S+tk.W)
        
        # Lat and long bounds widgets
        self.latMinLabel.pack( side=tk.TOP,    fill='x', expand=True)
        self.latMinScale.pack( side=tk.BOTTOM, fill='x', expand=True)
        
        self.latMaxLabel.pack( side=tk.TOP,    fill='x', expand=True)
        self.latMaxScale.pack( side=tk.BOTTOM, fill='x', expand=True)
        
        self.longMinLabel.pack(side=tk.TOP,    fill='x', expand=True)
        self.longMinScale.pack(side=tk.BOTTOM, fill='x', expand=True)
        
        self.longMaxLabel.pack(side=tk.TOP,    fill='x', expand=True)
        self.longMaxScale.pack(side=tk.BOTTOM, fill='x', expand=True)
        
        self.latMinframe.grid( row=0, column=0, pady=10, padx=15)
        self.latMaxframe.grid( row=0, column=1, pady=10)
        self.longMinframe.grid(row=1, column=0, padx=15)
        self.longMaxframe.grid(row=1, column=1)
        
        # Default position widgets
        self.dposLatLabel.pack(side=tk.TOP,    fill='x', expand=True)
        self.dposLatScale.pack(side=tk.BOTTOM, fill='x', expand=True)
        
        self.dposLonLabel.pack(side=tk.TOP,    fill='x', expand=True)
        self.dposLonScale.pack(side=tk.BOTTOM, fill='x', expand=True)
        
        self.dposLatFrame.pack(side=tk.LEFT,   fill='x', padx=15, pady=10)
        self.dposLonFrame.pack(side=tk.LEFT,   fill='x',          pady=10)
        
        # Master frames
        self.boundFrame.pack(  side=tk.LEFT,   fill='x', padx=3)
        self.entryFrame.pack(  side=tk.LEFT,   fill='x', padx=3,           expand=True)
        self.line1.pack(       side=tk.TOP,    fill='x')
        
        self.dposFrame.pack(   side=tk.LEFT,   fill='x', padx=3)
        self.line2col2.pack(   side=tk.LEFT ,  fill='x', padx=3,  pady=5,  expand=True, anchor=tk.S)
        self.line2.pack(       side=tk.LEFT,   fill='x',          pady=10, expand=True)
        
        self.masterFrame.pack( side=tk.TOP,    fill='x',          pady=5)
        
        return
    
    
    ############################################
    #           Thread interactions            #
    ############################################
    
    def decreaseThread(self, *args, **kwargs):
        '''Decrease by 1 the number of threads.'''
        
        value     = self.threadEntry.var.get()
        
        if value == '' or value =='1':
            self.threadEntry.var.set(1)
        else:
            self.threadEntry.var.set(int(value)-1)
            
        return
    
    def increaseThread(self, *args, **kwargs):
        '''Decrease by 1 the number of threads.'''
        
        value     = self.threadEntry.var.get()
        
        if value == '':
            self.threadEntry.var.set(1)
        elif value == self.main.cpuCount:
            self.threadEntry.var.set(self.main.cpuCount)
        else:
            self.threadEntry.var.set(int(value)+1)
            
        return
    
    def updateThreadValue(self, *args, **kwargs):
        '''Actions taken when the thread value is modified.'''
        
        value = self.threadEntry.var.get()
        
        # If entry is empty we only change to 1 when the widget loses focus
        if value == '':
            self.error['thread']   = True
            self.threadEntry.triggerError()
            return
        else:
           value = int(value) 
           self.error['thread']  = False 
           self.threadEntry.removeError()
            
        # Deal with cases where number of threads goes beyond the max value or the min (1)
        if value > self.main.cpuCount:
            self.threadEntry.var.set(self.main.cpuCount)
        elif value < 1:
            self.threadEntry.var.set('1')
            
        value = int(self.threadEntry.var.get())
        
        if value == self.main.cpuCount:
            self.maxButton.config(state='disabled')
        elif value == 1:
            self.minButton.config(state='disabled')
        else:
            if self.maxButton['state'] == 'disabled':
                self.maxButton.config(state='normal')
            if self.minButton['state'] == 'disabled':
                self.minButton.config(state='normal')
        return
        
        
    ############################################
    #           Sliders interactions           #
    ############################################
    
    def activateSliders(self, *args, **kwargs):
        '''Active all the scales in the window.'''
        
        # (Re)activate
        self.latMinScale.configure(state=tk.NORMAL)
        self.latMaxScale.configure(state=tk.NORMAL)
        self.lonMinScale.configure(state=tk.NORMAL)
        self.lonMaxScale.configure(state=tk.NORMAL)
        self.dposLatScale.configure(state=tk.NORMAL)
        self.dposLonScale.configure(state=tk.NORMAL)
        
        # Set (back) bindings
        self.latMinScale.bind( '<Enter>',    lambda *args, **kwargs: self.latMinScale.configure(highlightbackground='RoyalBlue2'))
        self.latMinScale.bind( '<Leave>',    lambda *args, **kwargs: self.latMinScale.configure(highlightbackground=self.winProperties['bg']))
        
        self.latMaxScale.bind( '<Enter>',    lambda *args, **kwargs: self.latMaxScale.configure(highlightbackground='RoyalBlue2'))
        self.latMaxScale.bind( '<Leave>',    lambda *args, **kwargs: self.latMaxScale.configure(highlightbackground=self.winProperties['bg']))
        
        self.longMinScale.bind('<Enter>',    lambda *args, **kwargs: self.longMinScale.configure(highlightbackground='RoyalBlue2'))
        self.longMinScale.bind('<Leave>',    lambda *args, **kwargs: self.longMinScale.configure(highlightbackground=self.winProperties['bg']))
        
        self.longMaxScale.bind('<Enter>',    lambda *args, **kwargs: self.longMaxScale.configure(highlightbackground='RoyalBlue2'))
        self.longMaxScale.bind('<Leave>',    lambda *args, **kwargs: self.longMaxScale.configure(highlightbackground=self.winProperties['bg']))
        
        self.dposLatScale.bind('<Enter>',    lambda *args, **kwargs: self.dposLatScale.configure(highlightbackground='RoyalBlue2'))
        self.dposLatScale.bind('<Leave>',    lambda *args, **kwargs: self.dposLatScale.configure(highlightbackground=self.winProperties['bg']))
        
        self.dposLonScale.bind('<Enter>',    lambda *args, **kwargs: self.dposLonScale.configure(highlightbackground='RoyalBlue2'))
        self.dposLonScale.bind('<Leave>',    lambda *args, **kwargs: self.dposLonScale.configure(highlightbackground=self.winProperties['bg']))
        
    
    def sliderUpdate(self, slider, *args, **kwargs):
        '''Actions taken when the slider is updated.'''
        
        value = slider.get()
        
        if slider is self.latMinScale:
            self.latMinLabel.configure(text='Minimum latitude: %.1f°' %value)
        elif slider is self.latMaxScale:
            self.latMaxLabel.configure(text='Maximum latitude: %.1f°' %value)
        elif slider is self.longMinScale:
            self.longMinLabel.configure(text='Minimum longitude: %.1f°' %value)
        elif slider is self.longMaxScale:
            self.longMaxLabel.configure(text='Maximum longitude: %.1f°' %value)
            
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
            
            # Change entry text color to ok 
            self.inputEntry.configure(fg=self.entryProperties['fg'])
            
            # Resize window
            size = (850, 650)
            self.geometry('%dx%d+%d+%d' %(size[0], size[1], (self.root.winfo_screenwidth()-size[0])//2, (self.root.winfo_screenheight()-size[1])//2))
            
            # Update sliders
            for widget in [self.latMinScale, self.latMaxScale, self.longMinScale, self.longMaxScale, self.dposLatScale, self.dposLonFrame]:
                widget.configure(state='normal', cursor='hand1', troughcolor='lavender')
                
            self.latMinScale.set( -90)
            self.latMaxScale.set(  90)
            self.longMinScale.set(-180)
            self.longMaxScale.set( 180)
            self.dposLatScale.set( 0)
            self.dposLonScale.set( 0)
            
            # Load graph onto the window
            self.makeGraph()
            return
        
        def errorFunction(*args, **kwargs):
            
            # Change entry text color to error
            self.inputEntry.configure(fg='firebrick1')
            
            # Hide graph in the windoq
            self.hideGraph()
            
            # Resize window
            size = (850, 220)
            self.geometry('%dx%d+%d+%d' %(size[0], size[1], (self.root.winfo_screenwidth()-size[0])//2, (self.root.winfo_screenheight()-size[1])//2))
            
            # Update sliders
            for widget in [self.latMinScale, self.latMaxScale, self.longMinScale, self.longMaxScale, self.dposLatScale, self.dposLonFrame]:
                widget.configure(state='disabled', cursor='arrow', troughcolor=self.winProperties['bg'])
                
            return

        # Retrieve name written in Entry
        fname = self.inputEntry.var.get()
        
        # If empty string, set back the default foreground color
        if fname == '':
            self.inputEntry.configure(fg=self.entryProperties['fg'])
            errorFunction()
            return
        
        # If no file was selected or if an error occured, do nothing
        elif fname is None:
            return
        
        # Otherwise check whether the file exists and apply the correct function
        else:
            self.checkFile(fname, okFunction=okFunction, errorFunction=errorFunction)
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
            return okFunction()
        else:
            return errorFunction()
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

