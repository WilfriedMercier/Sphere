#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 18 12:56:36 2020

@author: Wilfried Mercier - IRAP

Configuration window to generate new projections.
"""

import tkinter as     tk
from   .entry  import Entry

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
        
        self.winProperties   = winProperties
        self.entryProperties = entryProperties
        self.textProperties  = textProperties
        
        ################################################
        #              Default properties              #
        ################################################
            
        if 'bg' not in self.winProperties:
            self.winProperties['bg']    = self.main.bg
            
        if 'font' not in self.textProperties:
            self.textProperties['font'] = (self.main.font, 11)
            
        super().__init__(self.root, **winProperties)
        
        # Need to handle MAC and Windows cases
        try:
            self.wm_attributes('-type', ['dialog'])
        except:
            pass
        
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.title(self.name)
        
        
        ####################################
        #           Project name           #
        ####################################
        
        self.nameFrame = tk.Frame(self,           bg='red', bd=0, highlightthickness=0)
        self.nameLabel = tk.Label(self.nameFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0, text='Project name', 
                                  anchor=tk.W, font=textProperties['font'])
        self.nameEntry = Entry(self.nameFrame, self, self.root, dtype=str, defaultValue='', **entryProperties)
        
        ###################################################
        #           Open rectangular input file           #
        ###################################################
        
        self.inputFrame  = tk.Frame(self,            bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.inputFrame1 = tk.Frame(self.inputFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.inputFrame2 = tk.Frame(self.inputFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        
        self.inputLabel  = tk.Label(self.inputFrame1, bg=self.winProperties['bg'], bd=0, highlightthickness=0, text='Input file (equirectangular projection)', 
                                    anchor=tk.W, font=textProperties['font'])
        
        self.inputEntry  = Entry(    self.inputFrame2, self, self.root, dtype=str, defaultValue='', **entryProperties)
        self.inputButton = tk.Button(self.inputFrame2, image=self.main.iconDict['FOLDER_17'], 
                                     bd=0, bg=self.winProperties['bg'], highlightbackground=self.winProperties['bg'], relief=tk.FLAT, activebackground='black')
        
        
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