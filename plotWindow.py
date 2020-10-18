#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 18 12:56:36 2020

@author: Wilfried Mercier - IRAP

Simplistic window which just shows the data if it is loaded.
"""

import tkinter                           as     tk
from   matplotlib.figure                 import Figure
from   matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class PlotWindow(tk.Toplevel):
    '''Simplistic window which just shows the data if it is loaded.'''

    def __init__(self, parent, main, root, *args, data=None, winProperties={}, title='None', **kwargs):
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
            winProperties : dict
                properties to be passed to the Toplevel window. Default is an empty dict.
        '''
        
        # Setup attributes
        self.main           = main
        self.parent         = parent
        self.root           = root
        self.name           = title
        
        self.winProperties  = winProperties
        
        ################################################
        #              Default properties              #
        ################################################
            
        if 'bg' not in self.winProperties:
            self.winProperties['bg'] = self.main.bg
            
        super().__init__(self.root, **winProperties)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.title(self.name)
        
        ##################################
        #         Generate graph         #
        ##################################
        
        self.figure   = Figure(figsize=(10, 10), constrained_layout=True, facecolor=self.winProperties['bg'])
        
        # Creating an axis
        self.ax       = self.figure.add_subplot(111)
        
        self.ax.yaxis.set_ticks_position('none')
        self.ax.yaxis.set_ticks([])
        
        self.ax.xaxis.set_ticks_position('none')
        self.ax.xaxis.set_ticks([])
        
        # Default empty image
        if data is None:
            data = [[0, 0], [0, 0]]
            
        self.im       = self.ax.imshow(data, cmap='Greys')
        
        # Canvas holding figure
        self.figframe = tk.Frame( self, **self.winProperties)
        self.canvas   = FigureCanvasTkAgg(self.figure, master=self.figframe)
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.canvas.draw()
        
        # Draw frame containing the figure
        self.figframe.pack(expand=True)
        
        return


    def update(self, data, *args, **kwargs):
        '''
        Update the graph with new data.
        
        Parameters
        ----------
            data : numpy 2D or RGB array
                new data to load into the Figure
        '''
        
        if data is not None:
            self.im.set_data(data)
            self.canvas.draw()
        return

    def setTitle(self, title):
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

    def close(self, *args, **kwargs):
        '''Actions taken when the window is closed.'''
        
        tab       = self.main.tabs[self.main.notebook.select()]
        tab.resetAxis()
        
        longitude = tab.longitude[tab.confParams['x0']]
        latitude  = tab.latitude[ tab.confParams['y0']]
        tab.updateGraph(longitude=longitude, latitude=latitude, forceUpdate=True)
        
        self.main.duppButton.pack(side=tk.RIGHT, padx=10)
        self.withdraw()
        return True