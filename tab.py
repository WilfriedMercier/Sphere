#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct  3 18:50:47 2020

@author: wilfried

Utility class to create new tabs.
"""

import yaml
import os.path                           as     opath
import numpy                             as     np 
import tkinter                           as     tk
from   tkinter.filedialog                import askopenfilename
from   matplotlib.figure                 import Figure
from   matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
            self.fname = askopenfilename(initialdir=self.main.loadPath, title='Select YAML connfiguration file...', filetypes=(('YAML files', '*.yaml'), ('All files', '*.*')))
        except:
            print('Failed to open file...')
            return
        
        if self.fnames != '':
            self.load(self.fname)
        return
        
    def load(self, file, *args, **kwargs):
        '''
        Effects applied when data is loaded.
        
        Parameters
        ----------
            files : str
                project yaml configuration file to load
        '''
        
        try:
            # First load YAML parameters
            self.yaml       = file
            self.loadYAML(file)
            
            # Do not create a new tab if data is already loaded
            if not self.loaded:
            
                # Create new tab
                self.main.addTab(*args, **kwargs)
                self.loaded = True
            
                # Destroy default layout and load matplotlib frame and canvas
                self.main.notebook.tab(self.main.notebook.select(), text=file.split('.yaml')[0])
                self.loadButton.destroy()
                self.label.destroy()
                self.bindFrame.destroy()
                self.main.loadButton.configure(bg=self.main.color)
                self.makeGraph()
        except:
            pass

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
        if 'y0' not in self.confParams:
            self.confParams['y0']   = 0
        if 'unit' not in self.confParams:
            self.confParams['unit'] = '°'
            
        # Setup additional attributes
        self.dataDir                = opath.dirname(file)
        
        
            
        return
    
    
    ###################################################
    #                  Graph methods                  #
    ###################################################
    
    def makeGraph(self):
        '''Generate an empty matplotlib graph.'''
        
        self.figure   = Figure(figsize=(10, 10), constrained_layout=True, facecolor=self.properties['bg'])
        
        # Creating an axis
        self.ax       = self.figure.add_subplot(111)
        
        self.ax.yaxis.set_ticks_position('none')
        self.ax.yaxis.set_ticks([])
        
        self.ax.xaxis.set_ticks_position('none')
        self.ax.xaxis.set_ticks([])
        
        # Default empty image
        self.im       = self.ax.imshow(np.zeros((2, 2)), cmap='Greys')
        
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
    
    def fillGraph(self):
        '''Fill the graph with new data.'''

