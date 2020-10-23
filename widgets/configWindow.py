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
            self.textProperties['font'] = (self.main.font, 11)
            
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
        
        
        ###################################
        #          Setup widgets          #
        ###################################
        
        self.masterFrame = tk.Frame(     self,             bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.boundFrame  = tk.LabelFrame(self.masterFrame, bg=self.winProperties['bg'], bd=1, highlightthickness=0, text='Setup bounds',       font=self.textProperties['font'])
        self.entryFrame  = tk.LabelFrame(self.masterFrame, bg=self.winProperties['bg'], bd=1, highlightthickness=0, text='Project properties', font=self.textProperties['font'])
        
        # Project name
        
        self.nameFrame   = tk.Frame(self.entryFrame,  bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.nameLabel   = tk.Label(self.nameFrame,   bg=self.winProperties['bg'], bd=0, highlightthickness=0, text='Project name', 
                                    anchor=tk.W, font=textProperties['font'])
        self.nameEntry   = Entry(   self.nameFrame, self, self.root, dtype=str, defaultValue='', **entryProperties)
        
        # Open rectangular input file           
        
        self.inputFrame  = tk.Frame(self.entryFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.inputFrame1 = tk.Frame(self.inputFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.inputFrame2 = tk.Frame(self.inputFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        
        self.inputLabel  = tk.Label(self.inputFrame1, bg=self.winProperties['bg'], bd=0, highlightthickness=0, text='Input file (equirectangular projection)', 
                                    anchor=tk.W, font=textProperties['font'])
        
        self.inputEntry  = Entry(   self.inputFrame2, self, self.root, dtype=str, defaultValue='',
                                    traceCommand=self.loadInput, **entryProperties)
        
        self.inputButton = tk.Button(self.inputFrame2, image=self.main.iconDict['FOLDER_17'], 
                                     bd=0, bg=self.winProperties['bg'], highlightbackground=self.winProperties['bg'], relief=tk.FLAT, activebackground='black', 
                                     command=lambda *args, **kwargs: self.askLoad(title='Select a equirectangular surface image...', filetypes=self.filetypes))
        
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
                                     cursor='hand1', showvalue=False, sliderrelief=tk.FLAT,
                                     bg=self.winProperties['bg'], bd=1, highlightthickness=1, highlightbackground=self.winProperties['bg'], troughcolor='lavender', activebackground='black',
                                     command=lambda *args, **kwargs: self.sliderUpdate(self.latMinScale, *args, **kwargs))
        
        self.latMaxScale  = tk.Scale( self.latMaxframe, length=200, width=12, orient='horizontal', from_=-90, to=90, resolution=0.1,
                                     cursor='hand1', showvalue=False, sliderrelief=tk.FLAT,
                                     bg=self.winProperties['bg'], bd=1, highlightthickness=1, highlightbackground=self.winProperties['bg'], troughcolor='lavender', activebackground='black',
                                     command=lambda *args, **kwargs: self.sliderUpdate(self.latMaxScale, *args, **kwargs))
        
        
        self.longMinScale = tk.Scale( self.longMinframe, length=200, width=12, orient='horizontal', from_=-180, to=180, resolution=0.1,
                                     cursor='hand1', showvalue=False, sliderrelief=tk.FLAT,
                                     bg=self.winProperties['bg'], bd=1, highlightthickness=1, highlightbackground=self.winProperties['bg'], troughcolor='lavender', activebackground='black',
                                     command=lambda *args, **kwargs: self.sliderUpdate(self.longMinScale, *args, **kwargs))
        
        self.longMaxScale = tk.Scale( self.longMaxframe, length=200, width=12, orient='horizontal', from_=-180, to=180, resolution=0.1,
                                     cursor='hand1', showvalue=False, sliderrelief=tk.FLAT,
                                     bg=self.winProperties['bg'], bd=1, highlightthickness=1, highlightbackground=self.winProperties['bg'], troughcolor='lavender', activebackground='black',
                                     command=lambda *args, **kwargs: self.sliderUpdate(self.longMaxScale, *args, **kwargs))
        
        # Apply initial values for the scales
        self.latMinScale.set( -90)
        self.latMaxScale.set(  90)
        self.longMinScale.set(-180)
        self.longMaxScale.set( 180)
        
        
        #######################################################################
        #                               Bindings                              #
        #######################################################################

        self.latMinScale.bind(   '<Enter>',    lambda *args, **kwargs: self.latMinScale.configure(highlightbackground='RoyalBlue2'))
        self.latMinScale.bind(   '<Leave>',    lambda *args, **kwargs: self.latMinScale.configure(highlightbackground=self.winProperties['bg']))
        
        self.latMaxScale.bind(   '<Enter>',    lambda *args, **kwargs: self.latMaxScale.configure(highlightbackground='RoyalBlue2'))
        self.latMaxScale.bind(   '<Leave>',    lambda *args, **kwargs: self.latMaxScale.configure(highlightbackground=self.winProperties['bg']))
        
        self.longMinScale.bind(  '<Enter>',    lambda *args, **kwargs: self.longMinScale.configure(highlightbackground='RoyalBlue2'))
        self.longMinScale.bind(  '<Leave>',    lambda *args, **kwargs: self.longMinScale.configure(highlightbackground=self.winProperties['bg']))
        
        self.longMaxScale.bind(  '<Enter>',    lambda *args, **kwargs: self.longMaxScale.configure(highlightbackground='RoyalBlue2'))
        self.longMaxScale.bind(  '<Leave>',    lambda *args, **kwargs: self.longMaxScale.configure(highlightbackground=self.winProperties['bg']))
        
        
        ##########################################################
        #                     Drawing frames                     #
        ##########################################################
        
        # Project name widgets
        self.nameLabel.pack(side=tk.TOP,    fill='x', expand=True)
        self.nameEntry.pack(side=tk.BOTTOM, fill='x', expand=True)
        self.nameFrame.pack(side=tk.TOP,    fill='x', padx=10, pady=10)
        
        # Open file widgets
        self.inputLabel.pack( side=tk.LEFT, fill='x', expand=True)
        self.inputFrame1.pack(side=tk.TOP,  fill='x', expand=True)
        
        self.inputEntry.pack( side=tk.LEFT,   fill='x', expand=True)
        self.inputButton.pack(side=tk.RIGHT,  padx=10)
        self.inputFrame2.pack(side=tk.BOTTOM, fill='x', expand=True)
        
        self.inputFrame.pack( side=tk.TOP, padx=10, fill='x')
        
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
        
        # Master frames
        self.boundFrame.pack(side=tk.LEFT, padx=5)
        self.entryFrame.pack(side=tk.LEFT, fill='x', expand=True, padx=5)
        self.masterFrame.pack(side=tk.TOP, fill='x', pady=5)
        
        return
    
    
    ############################################
    #           Sliders interactions           #
    ############################################
    
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
            self.inputEntry.configure(fg=self.entryProperties['fg'])
            self.makeGraph()
            return
        
        def errorFunction(*args, **kwargs):
            self.inputEntry.configure(fg='firebrick1')
            self.hideGraph()
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
        
        #self.im.set_data(self.data)
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

