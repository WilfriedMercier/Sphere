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
        
        # Figure interaction properties
        self.clicked    = False
        
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
        
    @property
    def tabID(self, *args, **kwargs):
        
        values = list(self.main.tabs.values())
        where  = values.index(self)
        return self.main.tabs.keys()[where]
    
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
        
        # Steps in x and y used to update image when moving figure with mouse
        shp        = np.shape(self.data)
        self.xstep = (shp[1]-1)//self.lenLong
        self.ystep = (shp[0]-1)//self.lenLat
        
        return file
        
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
        
        # Do not create a new tab if data is already loaded
        if not self.loaded:
        
            # Create new tab
            self.loaded = True
            self.main.addTab(*args, **kwargs)
        
            # Destroy default layout and load matplotlib frame and canvas
            self.main.notebook.tab(self.main.notebook.select(), text=self.name)
            self.loadButton.destroy()
            self.label.destroy()
            self.bindFrame.destroy()
            self.main.loadButton.configure(bg=self.main.color)
            self.makeGraph()
            
        # Update sliders will also load data into the image through the callback command
        self.updateSliders()
        self.main.duppButton.pack(side=tk.RIGHT, padx=10)
        
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
        self.lenLong                = len(self.longitude) 
        self.lenLat                 = len(self.latitude)
        return
    

    ###################################################
    #                  Axis methods                   #
    ###################################################
    
    def makeAxis(self):
        '''Creating a new axis.'''
        
        self.ax       = self.figure.add_subplot(111)
        self.resetAxis()
        return
    
    def resetAxis(self):
        '''Reset to default the axis.'''
        
        self.ax.clear()
        self.ax.yaxis.set_ticks_position('none')
        self.ax.yaxis.set_ticks([])
        
        self.ax.xaxis.set_ticks_position('none')
        self.ax.xaxis.set_ticks([])
        
        # Default empty image
        self.im       = self.ax.imshow([[0, 0], [0, 0]], cmap='Greys')
        return
    
    ###################################################
    #                  Graph methods                  #
    ###################################################
    
    def makeGraph(self):
        '''Generate an empty matplotlib graph.'''
        
        self.figure   = Figure(figsize=(10, 10), constrained_layout=True, facecolor=self.properties['bg'])
        
        self.makeAxis()
        
        # Canvas holding figure
        self.figframe = tk.Frame( self, **self.properties)
        self.canvas   = FigureCanvasTkAgg(self.figure, master=self.figframe)
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.canvas.draw()
        
        # Draw frame containing the figure
        self.figframe.pack(expand=True)
        
        # Linking to events
        self.canvas.mpl_connect('button_press_event',   lambda *args, **kwargs: self.onClick(  *args, **kwargs))
        self.canvas.mpl_connect('button_release_event', lambda *args, **kwargs: self.outClick( *args, **kwargs))
        self.canvas.mpl_connect('motion_notify_event',  lambda *args, **kwargs: self.onMove(   *args, **kwargs))
        self.canvas.mpl_connect('figure_enter_event',   lambda *args, **kwargs: self.onFigure( *args, **kwargs))
        self.canvas.mpl_connect('figure_leave_event',   lambda *args, **kwargs: self.outFigure(*args, **kwargs))
        return
    
    def onFigure(self, *args, **kwargs):
        '''Actions taken when cursor enters figure.'''
        
        self.main.parent.config(cursor='hand1')
        return
    
    def outFigure(self, *args, **kwargs):
        '''Actions taken when cursor leaves figure.'''
        
        self.main.parent.config(cursor='arrow')
        return
    
    def onClick(self, event, *args, **kwargs):
        '''Actions taken when mouse button is pressed on figure.'''
        
        self.clicked  = True
        self.clickPos = [event.x, event.y]
        return
    
    def outClick(self, *args, **kwargs):
        '''Actions taken when mouse button is released on figure.'''
        
        self.clicked  = False
        self.clickPos = []
        return
    
    def onMove(self, event, *args, **kwargs):
        '''Actions taken when mouse is moved on figure.'''
        
        if self.clicked:
            
            # Load new image with different longitude if condition is met
            if abs(self.clickPos[0] - event.x) >= self.xstep:
                
                sign                       = (self.clickPos[0] - event.x)//abs(self.clickPos[0] - event.x)
                
                if self.confParams['x0'] == self.lenLong-1 and sign>0:
                    self.confParams['x0']  = 0
                elif self.confParams['x0'] == 0 and sign<0:
                    self.confParams['x0']  = self.lenLong-1
                else:
                    self.confParams['x0'] += sign
                    
                self.clickPos[0]       = event.x
                
            # Load new image with different latitude if condition is met
            if abs(self.clickPos[1] - event.y) >= self.ystep:
               
                sign                       = (self.clickPos[1] - event.y)//abs(self.clickPos[1] - event.y)
                
                if self.confParams['y0'] == self.lenLat-1 and sign>0:
                    self.confParams['y0']  = 0
                elif self.confParams['y0'] == 0 and sign<0:
                    self.confParams['y0']  = self.lenLat-1
                else:
                    self.confParams['y0'] += sign
                    
                self.clickPos[1]           = event.y
                
            self.updateSliders()
        return
    
    def updateGraph(self, latitude=None, longitude=None, forceUpdate=False):
        '''
        Fill the graph with new data.
        
        Parameters
        ----------
            forceUpdate : bool
                whether to force the image update even if the plot window still exists or not Default is False.
            latitude : int/float
                latitude value used to load the new data
            longitude : int/float
                longitude value used to load the new data
        '''
        
        if latitude is None and longitude is None:
            return
        
        try:
            y0 = np.where(self.latitude==float(latitude))[0][0]
        except:
            print('No image with latitude %s found. Using default value instead.' %latitude)
            print('Acceptable values are %s' %self.latitude)
            y0 = self.confParams['y0']
            
        try:
            x0 = np.where(self.longitude==float(longitude))[0][0]
        except:
            print('No image found with longitude %s found. Using default value instead.' %longitude)
            print('Acceptable values are %s' %self.longitude)
            x0 = self.confParams['x0']
        
        self.confParams['y0'] = y0
        self.confParams['x0'] = x0
        
        # Update slider labels
        self.main.longLabel.configure(text='Longitude: %s°' %self.longitude[x0])
        self.main.latLabel.configure (text='Latitude: %s°' %self.latitude[y0])
        
        self.getData()
        
        # Either update the plot window or the main one
        if self.main.plotWindow is not None and self.main.plotWindow.state() != 'withdrawn' and not forceUpdate:
            self.main.plotWindow.update(self.data)
        else:
            self.im.set_data(self.data)
            self.canvas.draw()
        return
    
    def showExplanation(self, *args, **kwargs):
        '''Show a figure with explanations when the plot window is shown.'''
        
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()[::-1]
        
        self.im.set_data([[0, 0], [0, 0]])
        
        midy = (ylim[0]+ylim[1])/2
        midx = (xlim[0]+xlim[1])/2
        
        # Horizontal arrow
        self.arrows = []
        self.arrows.append(self.ax.arrow(xlim[0]+0.1, midy,   xlim[1]-xlim[0]-0.2,  0, width=0.02, overhang=0.1, facecolor='black'))
        self.arrows.append(self.ax.arrow(xlim[1]-0.1, midy, -(xlim[1]-xlim[0]-0.2), 0, width=0.02, overhang=0.1, facecolor='black'))
    
        # Vertical arrow
        self.arrows.append(self.ax.arrow(midx, ylim[0]+0.1, 0,   ylim[1]-ylim[0]-0.2,  width=0.02, overhang=0.1, facecolor='black'))
        self.arrows.append(self.ax.arrow(midx, ylim[1]-0.1, 0, -(ylim[1]-ylim[0]-0.2), width=0.02, overhang=0.1, facecolor='black'))
        
        self.texts = []
        self.texts.append(self.ax.text(midx+0.3, midy-0.05, 'Longitude', fontsize='xx-large', fontweight='bold'))
        self.ax.text(midx-0.1, midy-0.3, 'Latitude',  fontsize='xx-large', fontweight='bold', rotation='vertical')
        self.ax.text(-midx+0.1, midy*2.8, 'Click and drag to move along\nthe longitude and latitude\ndirections', fontsize='large', fontstyle='oblique')
        
        self.canvas.draw()
        
        
        return
    
    
    ###############################################
    #                Miscellaneous                #
    ###############################################
    
    def updateSliders(self):
        '''Update the latitude and longitude sliders limits and current value.'''
        
        # If data has been loaded, we activate the sliders and update their values
        if self.loaded:
            self.main.latScale.configure( state='normal', cursor='hand1', troughcolor='lavender')
            self.main.longScale.configure(state='normal', cursor='hand1', troughcolor='lavender')
            
            self.main.latScale.bind(  '<Enter>',    lambda *args, **kwargs:self.main.latScale.configure(highlightbackground='RoyalBlue2'))
            self.main.latScale.bind(  '<Leave>',    lambda *args, **kwargs:self.main.latScale.configure(highlightbackground=self.main.color))
            self.main.longScale.bind( '<Enter>',    lambda *args, **kwargs:self.main.longScale.configure(highlightbackground='RoyalBlue2'))
            self.main.longScale.bind( '<Leave>',    lambda *args, **kwargs:self.main.longScale.configure(highlightbackground=self.main.color))
            
            self.main.latScale.configure( **{'from':self.latitude[0],  'to':self.latitude[-1],  'resolution':self.confParams['step']})
            self.main.longScale.configure(**{'from':self.longitude[0], 'to':self.longitude[-1], 'resolution':self.confParams['step']})
            
            self.main.latScale.set( self.latitude[ self.confParams['y0']])
            self.main.longScale.set(self.longitude[self.confParams['x0']])
        else:
            self.main.latScale.configure( state='disabled', cursor='arrow', troughcolor=self.main.color, sliderrelief=tk.FLAT)
            self.main.longScale.configure(state='disabled', cursor='arrow', troughcolor=self.main.color, sliderrelief=tk.FLAT)
            
            self.main.latScale.unbind( '<Enter>')
            self.main.latScale.unbind( '<Leave>')
            self.main.longScale.unbind('<Enter>')
            self.main.longScale.unbind('<Leave>')
        return
        
        
        
        
        
        
        
        