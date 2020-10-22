#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 18 12:56:36 2020

@author: Wilfried Mercier - IRAP

Configuration window to generate new projections.
"""

import os.path            as     opath
import tkinter            as     tk
from   tkinter.filedialog import askopenfilename
from   .entry             import Entry

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
        
        #           Project name
        
        self.nameFrame = tk.Frame(self,           bg='red', bd=0, highlightthickness=0)
        self.nameLabel = tk.Label(self.nameFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0, text='Project name', 
                                  anchor=tk.W, font=textProperties['font'])
        self.nameEntry = Entry(self.nameFrame, self, self.root, dtype=str, defaultValue='', **entryProperties)
        
        #           Open rectangular input file           
        
        self.inputFrame  = tk.Frame(self,            bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.inputFrame1 = tk.Frame(self.inputFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        self.inputFrame2 = tk.Frame(self.inputFrame, bg=self.winProperties['bg'], bd=0, highlightthickness=0)
        
        self.inputLabel  = tk.Label(self.inputFrame1, bg=self.winProperties['bg'], bd=0, highlightthickness=0, text='Input file (equirectangular projection)', 
                                    anchor=tk.W, font=textProperties['font'])
        
        self.inputEntry  = Entry(    self.inputFrame2, self, self.root, dtype=str, defaultValue='',
                                     traceCommand=self.loadInput, **entryProperties)
        
        self.inputButton = tk.Button(self.inputFrame2, image=self.main.iconDict['FOLDER_17'], 
                                     bd=0, bg=self.winProperties['bg'], highlightbackground=self.winProperties['bg'], relief=tk.FLAT, activebackground='black', 
                                     command=lambda *args, **kwargs: self.loadInput(askload=True))
        

        #######################################################################
        #                               Bindings                              #
        #######################################################################
        
        self.inputButton.bind('<Button-1>', lambda *args, **kwargs: self.loadInput(*args, **kwargs))
        
        
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
    
    
    #######################################
    #           Loading file(s)           #
    #######################################

    def askLoad(self, *args, title='', filetypes=('All files', '*.*'), **kwargs):
        '''Asking which file to open.'''
        
        try:
            # Load YAML file
            fname = askopenfilename(initialdir=self.main.loadPath, title=title, filetypes=tuple(filetypes + [['All files', '*.*']]))
        except:
            print('Failed to open file...')
            return None
        
        if fname != () and fname != '':
            return fname
        
        return None

    def loadInput(self, askload=False, *args, **kwargs):
        '''Load the input file into the matplotlib frame and write its name into the entry widget.'''

        if askload:
            fname = self.askLoad(title='Select a equirectangular surface image...', 
                                 filetypes=self.filetypes)
        else:
            fname = self.inputEntry.var.get()
        
        # If empty string, set back the default foreground color
        if fname == '':
            self.inputEntry.configure(fg=self.entryProperties['fg'])
            return
        
        # If no file was selected or if an error occured, do nothing
        elif fname is None:
            return
        
        else:
            self.inputEntry.var.set(fname)
            okFunction    = lambda *args, **kwargs: self.inputEntry.configure(fg=self.entryProperties['fg'])
            errorFunction = lambda *args, **kwargs: self.inputEntry.configure(fg='firebrick1')
            return self.checkFile(fname, okFunction=okFunction, errorFunction=errorFunction)
        


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

