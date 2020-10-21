#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 18 12:56:36 2020

@author: Wilfried Mercier - IRAP

Configuration window to generate new projections.
"""

import tkinter                           as     tk

class ConfigWindow(tk.Toplevel):
    '''Configuration window to generate new projections.'''

    def __init__(self, parent, main, root, *args, winProperties={}, entryProperties={}, title='None', **kwargs):
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
        
        self.winProperties   = winProperties
        self.entryProperties = entryProperties
        
        ################################################
        #              Default properties              #
        ################################################
            
        if 'bg' not in self.winProperties:
            self.winProperties['bg'] = self.main.bg
            
        super().__init__(self.root, **winProperties)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.title(self.name)
        
        self.nameFrame = tk.Frame(self,           bg='red', bd=0, highlightthickness=0)
        self.nameLabel = tk.Label(self.nameFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0, text='Project name', anchor=tk.W)
        self.nameEntry = tk.Entry(self.nameFrame, **entryProperties)
        
        self.nameLabel.pack(side=tk.TOP,    fill='x', expand=True)
        self.nameEntry.pack(side=tk.BOTTOM, fill='x', expand=True)
        
        self.nameFrame.pack(side=tk.TOP, padx=10, expand=True, fill='x')
        
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
        
        self.withdraw()
        return True