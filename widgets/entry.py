#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Wilfried Mercier - IRAP

Own entry widget
"""

import tkinter        as     tk
from   .misc.validate import validateType

class Entry(tk.Entry):
    '''A custom entry widget with a buffer and custom key bindings.
    
        Key bindings
        ------------
            Ctrl + a     : Select all the text, keeping the cursor at the current location
            Esc          : Cancel selection if text is selected, otherwise remove focus from this widget
            Home         : Move cursor the the beginning of the text
            End          : Move cursor to the end of the text
            Shift + Home : Select text from current location to the beginning of the text and move cursor to the latter location
            Shift + End  : Select text from current location to the end of the text and move cursor to the latter location
    '''
    
    def __init__(self, parent, main, root, dtype=float, defaultValue='', traceCommand=lambda: None, **kwargs):
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
            defaultValue : str
                default value placed in the entry variable. Default is an empty string.
            dtype : python data type
                type of data that should be contained within the entry. Only this type of data will be allowed in the entry. Default is float.
            traceCommand : function
                function called once the entry value has been validated, but before the buffer has been updated
            
            **kwargs
                Common tkinter entry parameters. If validate option is not provided default value will be set to 'key'.
        '''
        
        self.parent            = parent
        self.main              = main
        self.root              = root
        self.traceCommand      = traceCommand
        self.dtype             = dtype
        
        # A flag which changes colors when equal to True
        self.error             = False              
        
        # Set default value of validate entry option
        if 'validate' not in kwargs:
            kwargs['validate']         = 'key'
            
        if 'validatecommand' in kwargs:
            kwargs.remove('validatecommand')
            
        if 'highligthcolor' not in kwargs:
            kwargs['highlightcolor']   = 'RoyalBlue2'
            
        if 'selectbackground' not in kwargs:
            kwargs['selectbackground'] = 'cornflower blue'
        
        self.var                 = tk.StringVar()
        self.var.set(defaultValue)
        
        vcmd                     =  (self.parent.register(self.validateEntry), '%P', '%d')
        super().__init__(self.parent, textvariable=self.var, validatecommand=vcmd, **kwargs)
        
        self.bind('<Enter>', self.onEntry)
        self.bind('<Leave>', self.outEntry)
        
        self.bgColor             = self['bg']
        self.highlightbackground = self['highlightbackground']
        self.errorhighlightcolor = self['errorhighlightcolor'] if 'errorhighlightcolor' in kwargs else 'firebrick1'
        self.buffer              = [self.value]
        
        # Binding trace command with buffer
        self.var.trace('w', self.trace)
        
        ######################################################
        #                    Key bindings                    #
        ######################################################
        
        # Plateform independent
        self.bind('<Control-z>',     self._pop)
        self.bind('<Control-a>',     lambda event: self.selectText(0, tk.END, self.index(tk.INSERT)))
        self.bind('<Escape>',        self._escapeBinding)
        
        # Linux-specific ?
        self.bind('<KP_Home>',       lambda event: self.icursor(0))
        self.bind('<KP_End>',        lambda event: self.icursor(tk.END))
        self.bind('<Shift-KP_Home>', lambda event: self.selectText(0, tk.INSERT, 0))
        self.bind('<Shift-KP_End>',  lambda event: self.selectText(tk.INSERT, tk.END, tk.END))
        
        # Other OS ?
        self.bind('<Home>',          lambda event: self.icursor(0))
        self.bind('<End>',           lambda event: self.icursor(tk.END))
        self.bind('<Shift-Home>',    lambda event: self.selectText(0, tk.INSERT, 0))
        self.bind('<Shift-End>',     lambda event: self.selectText(tk.INSERT, tk.END, tk.END))
        
    
    @property
    def value(self, *args, **kwargs):
        '''Tkinter StringVar value accessible as a property.'''
        return self.var.get()
        
        
    def _escapeBinding(self, *args, **kwargs):
        '''Binding related to trigerring escape key.'''
        
        if self.select_present():
            self.select_clear()
        else:
            self.root.focus()
        
        return "break"


    def selectText(self, beg=0, end=tk.END, cursor=0):
        '''
        Select the text in the entry from beg position to end and move cursor to the given position.
        
        Optional parameters
        -------------------
            beg : int or str
                starting point to select the text
            cursor : int
                where to place the cursor after the selection
            end : int or str
                end point of the selection
        '''

        if self.select_present():
            self.select_clear()
        else:
            self.select_range(beg, end)
        self.icursor(cursor)
        return "break"

    
    def trace(self, *args, **kwargs):
        '''Function called when tracing the variable change. This includes buffer update.'''
        
        # Check whether new value is not identical to the lastly stored buffer value (typically happen after a pop)
        if self.value != self.buffer[-1]:
            
            # Calling the given trace function first, then push new value
            self.traceCommand()
            self._push()
        return
    
    
    #######################################################
    #                Error state functions                #
    #######################################################
    
    def removeError(self, *args, **kwargs):
        '''Remove the error state.'''
        
        self.error                      = False 
        
        if self['state'] == 'normal':
            self['highlightbackground'] = self.highlightbackground
        if self['state']== 'focus':
            self['highlightbackground'] = 'black'
    
    def triggerError(self, *args, **kwargs):
        '''Modify the widget state to an error state.'''
        
        self.error                  = True
        self['highlightbackground'] = self.errorhighlightcolor
        return
    
    ################################################
    #                Mouse hovering                #
    ################################################
    
    def onEntry(self, *args, **kwargs):
        
        if not self.error:
            self['highlightbackground'] = 'black'
        return
    
    
    def outEntry(self, *args, **kwargs):
        
        if not self.error:
            self['highlightbackground'] = self.highlightbackground
        else:
            self['highlightbackground'] = self.errorhighlightcolor
        return
    
    
    ############################################
    #             Buffer functions             #
    ############################################
    
    @property
    def _peak(self, *args, **kwargs):
        '''Getting the top of the buffer value.'''
        
        return self.buffer[-1]
    
    def _pop(self, *args, **kwargs):
        '''
        Remove the lastly stored value within the buffer and update the variable.
        
        Return 'break' because function is binded to Key binding which may interfere with higher level key bindings, i.e. this break any loop which may trigger later key bindings.
        '''
        
        if len(self.buffer) > 1:
            self.buffer.pop(-1)
            self.var.set(self.buffer[-1])
            self.traceCommand()
            
        return "break"
    
    def _push(self, *args, **kwargs):
        '''Append to the buffer the value within the widget tkinter.StringVar.'''
        
        self.buffer.append(self.value)
        return


    ##################################################################
    #              Validate the content of some the entry            #
    ##################################################################
    
    def validateEntry(self, P, d):
        '''
        Validate the type of the entry widget.
        
        Note
        ----
            This function must be called through a tkinter register and not directly through a wiget command. Explanation for the two parameters is below.
        
        Parameter
        ---------
            %d = Type of action (1=insert, 0=delete, -1 for others)
            %P = value of the entry if the edit is allowed
            
        Return True if the data type is correct or False otherwise.
        '''
        
        # If the text is completely deleted we do not check its type
        if P == '':
            return True
        
        return validateType(P, self.dtype)