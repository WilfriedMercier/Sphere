"""
Author: Wilfried Mercier - IRAP
"""

import sys
sys.path.append("..")

from   setup   import writeConfiguration
import tkinter as     tk
from   tkinter import ttk

class Validate(tk.Toplevel):
    '''A window with text, Yes/No buttons and a checkbox.'''
    
    def __init__(self, parent, main, root, 
                 acceptFunction=lambda *args, **kwargs: None, cancelFunction=lambda *args, **kwargs: None,
                 mainText='', listNames=[''],
                 title='', winProperties={}, textProperties={}, buttonsProperties={}):
        
        '''
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
            buttonsProperties : dict
                properties of the buttons to pass to the __init__ method. Default is empty.
            listNames : list of str
                names to be shown. Default is [''].
            mainText : str
                text to show. Default is empty.
            textProperties : dict
                properties of the text widgets to pass to the __init__ method. Default is empty.
            title : str
                window title. Default is empty.
            winProperties : dict
                window properties to pass to the __init__ method. Default is empty.
        '''
            
        # Setup attributes
        self.main           = main
        self.parent         = parent
        self.root           = root
        
        self.winProperties  = winProperties
        self.names          = listNames
        
        
        ################################################
        #              Default properties              #
        ################################################
        
        if 'font' not in textProperties:
            textProperties['font']   = (self.main.font, 10)
            
        if 'bg' not in self.winProperties:
            self.winProperties['bg'] = self.main.bg
        
        
        ###################################################
        #              Custom treeview style              #
        ###################################################
            
        self.style    = ttk.Style()
        self.style.configure("mystyle.Treeview", highlightthickness=10, background=self.winProperties['bg'], foreground='red', font=textProperties['font']) # Modify the font of the body
        self.style.map('mystyle.Treeview', background=[('selected', self.winProperties['bg'])], foreground=[('selected', 'red')])
        self.style.configure("mystyle.Treeview.Heading", background=self.winProperties['bg'], font=tuple(list(textProperties['font']) + ['bold'])) # Modify the font of the headings
        
        self.acceptFunction = acceptFunction
        self.cancelFunction = cancelFunction
        
        super().__init__(self.root, **self.winProperties)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.resizable(width=True, height=False)
        self.wm_attributes('-topmost', True)
        self.title(title)
        self.transient()
        
        # Main text
        self.textl  = tk.Label(self, text=mainText, **textProperties)
        
        
        ###############################################################################
        #                      Treeview to show and select files                      #
        ###############################################################################
        
        self.treeview = ttk.Treeview(self, style='mystyle.Treeview', height=len(self.names))
        self.treeview.heading('#0', text='Files', anchor=tk.W)
        
        for pos, name in enumerate(self.names):
            self.treeview.insert('', pos, text=name)
            
        # Bind event(s)
        self.treeview.bind('<Button-1>', lambda *args, **kwargs: self.onClick(*args, **kwargs))
        
        # List of selected items
        self.selection = []
        
        # Define tags
        self.treeview.tag_configure('selected',   foreground='white', background='RoyalBlue2')
        self.treeview.tag_configure('unselected', foreground='red',   background=winProperties['bg'])
        

        #####################################################
        #                      Buttons                      #
        #####################################################
        
        self.yes  = tk.Button(self, text='Ok',      underline=0, command=self.accept, **buttonsProperties, state=tk.DISABLED)
        self.no   = tk.Button(self, text='Cancel',  underline=0, command=self.cancel, **buttonsProperties)
        
        ############################################################
        #                  Checkbox on the bottom                  #
        ############################################################
        
        self.cFrame = tk.Frame(      self, bg='gray94', bd=0, highlightbackground='gray94', highlightthickness=2)
        self.checkV = tk.IntVar()
        self.check  = tk.Checkbutton(self.cFrame, text=' Do not ask again', bg='gray94', bd=0, highlightthickness=0, activebackground='gray84', variable=self.checkV)
        
        
        ##################################################
        #                     Binding                    #
        ##################################################
        
        self.bind('<Return>', lambda *args, **kwargs: self.accept(*args, **kwargs))
        self.bind('<Escape>', lambda *args, **kwargs: self.cancel(*args, **kwargs))
        
        
        ###########################################################
        #                    Griding things up                    #
        ###########################################################
        
        self.textl.grid(   row=0, pady=5, padx=5)
        self.treeview.grid(row=1, columnspan=3, sticky=tk.E+tk.W, padx=5, pady=10)
        
        self.yes.grid(row=2, column=1, padx=10, pady=5, sticky=tk.E)
        self.no.grid( row=2, column=2, padx=10, pady=5, sticky=tk.W)
        
        self.check.pack(side=tk.LEFT, padx=2)
        self.cFrame.grid(row=2, column=0, columnspan=1, sticky=tk.W)
        
        self.state('withdrawn')
        
        
    def accept(self, *args, **kwargs):
        '''Actions taken when the button accept is triggered.'''
        
        try:
            files = [self.names[self.treeview.index(i)] for i in self.selection]
            self.acceptFunction(files, *args, **kwargs)
        except:
            pass
        
        # Not very fancy but otherwise tk throws an error when closing this window before the main one...
        del self.checkV
        
        self.grab_release()
        self.destroy()
        return True
    
    def cancel(self, *args, **kwargs):
        '''Actions taken when the button cancel is triggered.'''
        
        try:
            # Remove from setting file the YAML file names if asked for
            if self.checkV.get():
                self.main.settings['projects'] = []
                writeConfiguration('settings.yaml', self.main.settings)
            
            self.cancelFunction(*args, **kwargs)
        except:
            pass
        
        # Not very fancy but otherwise tk throws an error when closing this window before the main one...
        del self.checkV
        
        self.grab_release()
        self.destroy()
        return True
        
    
    def onClick(self, event, *args, **kwargs):
        '''Action taken when a row is clicked.'''
        
        item = self.treeview.identify('item', event.x, event.y)
        
        if item not in self.selection:
            self.selection.append(item)
            self.treeview.item(item, tags='selected')
            self.style.map('mystyle.Treeview', background=[('selected', 'RoyalBlue2')], foreground=[('selected', 'white')])
        else:
            self.selection.remove(item)
            self.treeview.item(item, tags='unselected')
            self.style.map('mystyle.Treeview', background=[('selected', self.winProperties['bg'])], foreground=[('selected', 'red')])
            
        # Enable back the yes button if at least one element is selected
        if len(self.selection)>0 and self.yes.cget('state') == 'disabled':
            self.yes.configure(state='normal')
        elif len(self.selection)==0 and self.yes.cget('state') in ['normal', 'active']:
            self.yes.configure(state=tk.DISABLED)
        return
        
        
