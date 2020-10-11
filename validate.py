"""
Author: Wilfried Mercier - IRAP
"""

import tkinter as tk

class Validate(tk.Toplevel):
    '''A window with text, Yes/No buttons and a checkbox.'''
    
    def __init__(self, parent, main, root, 
                 acceptFunction=lambda *args, **kwargs: None, cancelFunction=lambda *args, **kwargs: None,
                 text='', splitText='', textMcolor='red',
                 title='', winProperties={}, textFrameProperties={}, textProperties={}, buttonsProperties={}):
        
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
            splitText : str
                text used to split the global string between the left, middle and right parts. Default is empty string.
            text : str
                text to show. Default is empty.
            textFrameProperties : dict
                properties of the frame containing the text widgets to pass to the __init__ method. Default is empty.
            textMcolor : tkinter color name
                color of the middle part of the string. Default is 'red'.
            textProperties : dict
                properties of the text widgets to pass to the __init__ method. Default is empty.
            title : str
                window title. Default is empty.
            winProperties : dict
                window properties to pass to the __init__ method. Default is empty.
        '''
            
        
        self.main   = main
        self.parent = parent
        self.root   = root
        
        self.acceptFunction = acceptFunction
        self.cancelFunction = cancelFunction
        
        super().__init__(self.root, **winProperties)
        self.wm_attributes('-type', 'utility')
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.resizable(width=True, height=False)
        self.wm_attributes('-topmost', True)
        self.title(title)
        self.transient()
        
        # Main text
        textl, textm, textr = text.partition(splitText)
        self.tframe = tk.Frame(self, **textFrameProperties)
        self.textl  = tk.Label(self.tframe, text=textl, **textProperties)
        self.textm  = tk.Label(self.tframe, text=textm, fg=textMcolor, font=(self.main.font, 10, 'bold'), **textProperties)
        self.textr  = tk.Label(self.tframe, text=textr, **textProperties)
        
        # Buttons
        self.yes  = tk.Button(self, text='Yes', underline=0, command=self.accept, **buttonsProperties)
        self.no   = tk.Button(self, text='No',  underline=0, command=self.cancel, **buttonsProperties)
        
        # Checkbox on the bottom
        self.cFrame = tk.Frame(      self, bg='gray94', bd=0, highlightbackground='gray94', highlightthickness=2)
        self.check  = tk.Checkbutton(self.cFrame, text=' Do not ask again', bg='gray94', bd=0, highlightthickness=0, activebackground='gray84')
        
        # Griding things up
        self.textl.grid(row=0)
        self.textm.grid(row=1, sticky=tk.W)
        self.textr.grid(row=2, sticky=tk.W)
        self.tframe.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        
        self.yes.grid(row=1, column=0, padx=10, pady=10, sticky=tk.E)
        self.no.grid( row=1, column=1, padx=10, pady=10, sticky=tk.W)
        
        self.check.pack(side=tk.LEFT, padx=2)
        self.cFrame.grid(row=2, column=0, columnspan=2, sticky=tk.E+tk.W+tk.S)
        
        self.state('withdrawn')
        
        
    def accept(self, *args, **kwargs):
        '''Actions taken when the button accept is triggered.'''
        
        self.acceptFunction(*args, **kwargs)
        self.grab_release()
        self.destroy()
        return True
    
    def cancel(self, *args, **kwargs):
        '''Actions taken when the button cancel is triggered.'''
        
        self.cancelFunction(*args, **kwargs)
        self.grab_release()
        self.destroy()
        return True
        
        