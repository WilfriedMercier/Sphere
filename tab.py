#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct  3 18:50:47 2020

@author: wilfried

Utility class to create new tabs.
"""

import yaml
import matplotlib.pyplot                 as     plt
import os.path                           as     opath
import numpy                             as     np 
import tkinter                           as     tk
from   tkinter.filedialog                import askopenfilename
from   matplotlib.figure                 import Figure
from   matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from   glob                              import glob

class Tab(tk.Frame):
    def __init__(self, parent, main, notebook, properties={}):
        '''
        Initialise the tab object.
        
        Mandatory parameters
        --------------------
            notebook : ttk notebook object
                notebook the tab belongs to
            parent : tk object
                object to draw the frame within
            main : tk object
                object where the tab is created
        
        Optional parameters
        -------------------
            properties : dict
                properties passed to the frame instance
        '''
        
        self.parent     = parent
        self.main       = main
        self.notebook   = notebook
        self.properties = properties
        
        # Default properties before they are updated at loading
        self.data       = None     # Array containing the RGB values
        self.dataDir    = './'     # Directory where to find the YAML and the files
        self.name       = 'None'   # Name of the tab
        self.yaml       = ''       # YAML configuration file full path
        self.longitude  = []       # List or array of longitudes corresponding to each pixel column in the RGB array
        self.latitude   = []       # List or array of latitudes corresponding to each pixel column in the RGB array
        
        # Setup default properties if not given
        if 'bg' not in properties:
            self.properties['bg'] = 'lavender'
        
        # Flag to know whether data is already loaded or not
        self.loaded     = False
        
        super().__init__(self.parent, **properties)
        
        # Setup initial page
        self.bindFrame  = tk.Frame( self, **self.properties)
        self.loadButton = tk.Button(self.bindFrame, image=self.main.iconDict['FOLDER_256'],   
                                     bd=0, highlightthickness=0, bg=self.properties['bg'], highlightbackground=self.properties['bg'], relief=tk.FLAT, activebackground='black',
                                     command=self.askLoad)
        
        self.label      = tk.Label( self.bindFrame, text='Click on the folder icon to load a YAML projection file', 
                                    font=('fixed', 16), bg=self.properties['bg'], highlightbackground=self.properties['bg']) 
        
        # Binding
        self.loadButton.bind('<Enter>', lambda *args, **kwargs: self.main.loadButton.configure(bg='black'))
        self.loadButton.bind('<Leave>', lambda *args, **kwargs: self.main.loadButton.configure(bg=self.main.color))
        
        self.loadButton.pack()
        self.label.pack     (pady=10)
        self.bindFrame.pack( expand=True)
        
        # Add to notebook
        self.notebook.add(self, text='+')
        
    
    ##########################################
    #               IO methods               #
    ##########################################
        
    def askLoad(self, *args, **kwargs):
        '''Asking which file to open.'''
        
        try:
            # Load YAML file
            fname = askopenfilename(initialdir=self.main.loadPath, title='Select YAML connfiguration file...', filetypes=(('YAML files', '*.yaml'), ('All files', '*.*')))
        except:
            print('Failed to open file...')
            return
        
        if fname != () and fname != '':
            self.load(fname)
        else:
            print('No file selected...')
        return
    
    def getData(self, *args, **kwargs):
        '''Get data from the correct image after YAML has been loaded.'''
        
        name     = opath.splitext(self.yaml)[0] + '_%d,%d' %(self.confParams['x0'], self.confParams['y0']) + '*'
        file     = glob(name)
        if len(file) > 0:
            file = file[0]
        else:
            print('No file %s was found.' %name, self.yaml)
            raise IOError
            
        # Get RGB data
        self.data = plt.imread(file, format=opath.splitext(file)[-1])
        return
        
    def load(self, file, *args, **kwargs):
        '''
        Effects applied when data is loaded.
        
        Parameters
        ----------
            file : str
                project yaml configuration file to load
        '''
        
        # First load YAML parameters
        self.yaml       = file
        self.loadYAML(file)
        
        # Load data
        self.getData()
        
        # Update sliders
        self.updateSliders()
        
        # Do not create a new tab if data is already loaded
        if not self.loaded:
        
            # Create new tab
            self.main.addTab(*args, **kwargs)
            self.loaded = True
        
            # Destroy default layout and load matplotlib frame and canvas
            self.main.notebook.tab(self.main.notebook.select(), text=self.name)
            self.loadButton.destroy()
            self.label.destroy()
            self.bindFrame.destroy()
            self.main.loadButton.configure(bg=self.main.color)
            self.makeGraph(self.data)
        return
    
    def loadYAML(self, file):
        '''
        Load parameters when a YAML file is selected.
        
        Parameters
        ----------
            file : str
                project yaml configuration file to load
        '''
        
        if not isinstance(file, str):
            raise TypeError('yaml file name must be of type string.')
        
        # Load data parameters
        with open(file, 'r') as f:
            self.confParams         = yaml.load(f, Loader=yaml.Loader)
            
        # Perform some checks
        for i in ['lat min', 'lat max', 'long min', 'long max', 'step']:
            if i not in self.confParams:
                self.confParams = {}
                raise IOError('Data cannot be loaded because parameter %s is missing in the YAML file %s.' %(i, file))
                
        if self.confParams['lat min'] >= self.confParams['lat max']:
            self.confParams = {}
            raise ValueError('Minimum latitude (%s) >= Maximum latitude (%s).' %(self.confParams['lat min'], self.confParams['lat max']))

        if self.confParams['long min'] >= self.confParams['long max']:
            self.confParams = {}
            raise ValueError('Minimum longitude (%s) >= Maximum longitude (%s).' %(self.confParams['long min'], self.confParams['long max']))
            
        if self.confParams['step'] <= 0:
            self.confParams = {}
            raise ValueError('Given latitude and longitude increment is < 0, which is not allowed.')
        
        if 'x0' not in self.confParams:
            self.confParams['x0']   = 0
        else:
            self.confParams['x0']   = int(self.confParams['x0'])
            
        if 'y0' not in self.confParams:
            self.confParams['y0']   = 0
        else:
            self.confParams['y0']   = int(self.confParams['y0'])
        
        if 'unit' not in self.confParams:
            self.confParams['unit'] = '°'
            
        # Setup additional attributes
        self.dataDir, self.name     = opath.split(file)
        self.name                   = opath.splitext(self.name)[0]
        self.longitude              = np.arange(self.confParams['long min'], self.confParams['long max']+self.confParams['step'], self.confParams['step'])
        self.latitude               = np.arange(self.confParams['lat min'],  self.confParams['lat max'] +self.confParams['step'], self.confParams['step'])
        
        return
    
    
    ###################################################
    #                  Graph methods                  #
    ###################################################
    
    def makeGraph(self, data):
        '''Generate an empty matplotlib graph.'''
        
        self.figure   = Figure(figsize=(10, 10), constrained_layout=True, facecolor=self.properties['bg'])
        
        # Creating an axis
        self.ax       = self.figure.add_subplot(111)
        
        self.ax.yaxis.set_ticks_position('none')
        self.ax.yaxis.set_ticks([])
        
        self.ax.xaxis.set_ticks_position('none')
        self.ax.xaxis.set_ticks([])
        
        # Default empty image
        self.im       = self.ax.imshow(data, cmap='Greys')
        
        # Canvas holding figure
        self.figframe = tk.Frame( self, **self.properties)
        self.canvas   = FigureCanvasTkAgg(self.figure, master=self.figframe)
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.canvas.draw()
        
        # Draw frame containing the figure
        self.figframe.pack(expand=True)
        
        # Linking to events
        self.canvas.mpl_connect('button_press_event',  lambda *args, **kwargs: None)
        self.canvas.mpl_connect('motion_notify_event', lambda *args, **kwargs: None)
        self.canvas.mpl_connect('figure_enter_event',  lambda *args, **kwargs: None)
        self.canvas.mpl_connect('figure_leave_event',  lambda *args, **kwargs: None)
        return
    
    def updateGraph(self):
        '''Fill the graph with new data.'''

        return
    
    
    ###############################################
    #                Miscellaneous                #
    ###############################################
    
    def updateSliders(self):
        '''Update the latitude and longitude sliders limits and current value.'''
        
        self.main.latScale.configure( **{'from':self.latitude[0],  'to':self.latitude[-1],  'resolution':self.confParams['step']})
        self.main.longScale.configure(**{'from':self.longitude[0], 'to':self.longitude[-1], 'resolution':self.confParams['step']})
        
        self.main.latScale.set( self.latitude[ self.confParams['y0']])
        self.main.longScale.set(self.longitude[self.confParams['x0']])
        return
        
        
        
        
        
        
        
        