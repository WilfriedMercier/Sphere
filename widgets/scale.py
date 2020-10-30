#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 08:30:28 2020

@author: wilfried

A modified version of the tkinter Scale widget
"""

import tkinter as tk

class Scale(tk.Scale):
    '''A modified version of the tkinter Scale widget.'''
    
    def __init__(self, parent, main, root, *args, 
                 enterFunc=lambda *args, **kwargs: None, leaveFunc=lambda *args, **kwargs: None,
                 disable = False, initValue=0,
                 hoverParams={},
                 normalStateParams={},
                 errorStateParams={},
                 disabledStateParams={}, **kwargs):
        '''
        Init function for the entry widget.
    
        Mandatory parameters
        --------------------
            main : tk object
                object where the tab is created
            parent : tkinter widget
                parent widget
            root : tkinter main window
                root object
                
        Optional parameters
        -------------------
            disable : bool
                whether to disable the widget at creation or not. Default is to enable it.
            disabledStateParams : dict
                parameters to be passed to the Scale widget when the disabled state is trigerred
            errorStateParams : dict
                parameters to be passed to the Scale widget when the error state is trigerred
            hoverParams : dict
                parameters to be passed to the Scale widget when the cursor is hovering over it
            normalStateParams : dict
                parameters to be passed to the Scale widget when the normal state is trigerred
            **kwargs : other optional parameters
                default parameter values to be passed to the Scale. Beware that the normalStateParams value will override these if present in **kwargs.
        '''
        
        # Attributes
        self.parent              = parent
        self.root                = root
        self.main                = main
        self.error               = False
        
        self.enterFunc           = enterFunc
        self.leaveFunc           = leaveFunc 
        
        self.hoverParams         = hoverParams
        self.normalStateParams   = normalStateParams
        self.errorStateParams    = errorStateParams
        self.disabledStateParams = disabledStateParams
        
        # Deal with parameters
        for key, value in normalStateParams.items():
            if key in kwargs:
                kwargs[key]      = value
                
        # 'state' keyword must be removed because we control the state of the widget with state parameter
        for dictionary in [kwargs, self.normalStateParams, self.disabledStateParams, self.errorStateParams]:
            if 'state' in dictionary:
                dictionary.pop('state')
                
        if not isinstance(initValue, (float, int)):
            initValue = 0
        
        # Generate scale
        super().__init__(self.parent, *args, **kwargs)
        self.set(initValue)
        
        if disable:
            self.disabledState()
        
    
    ##########################################
    #            Bindinds methods            #
    ##########################################
        
    def enterBinding(self, *args, **kwargs):
        '''Actions taken when the cursor enters the widget.'''
        
        self.configure(**self.hoverParams)
        return self.enterFunc(*args, **kwargs)
    
    def leaveBinding(self, *args, **kwargs):
        '''Actions taken when the cursor leaves the widget.'''
        
        self.configure(**self.normalStateParams)
        return self.leaveFunc(*args, **kwargs)
        
    
    ###########################################
    #              State methods              #
    ###########################################
    
    def disabledState(self, *args, **kwargs):
        '''Change the widget into a disabled state.'''
        
        self.configure(state='disabled', **self.disabledStateParams)
        self.unbind('<Enter>')
        self.unbind('<Leave>')
        return
    
    def errorState(self, *args, **kwargs):
        '''Change the widget into an error state.'''
        
        # Enable the widget and change its appearance
        self.configure(state='normal', **self.errorStateParams)

        # Replace old bindings with just the user function
        self.bind('<Enter>',    lambda *args, **kwargs: self.enterFunc(*args, **kwargs))
        self.bind('<Leave>',    lambda *args, **kwargs: self.leaveFunc(*args, **kwargs))
        return
        
    def normalState(self, *args, **kwargs):
        '''Change the widget into normal (activated) state.'''

        # Enable the widget and change its appearance
        self.configure(state='normal', **self.normalStateParams)
        
        # Enable the default bindings
        self.bind('<Enter>',    lambda *args, **kwargs: self.enterBinding(*args, **kwargs))
        self.bind('<Leave>',    lambda *args, **kwargs: self.leaveBinding(*args, **kwargs))
        return



