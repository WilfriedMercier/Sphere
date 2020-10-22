#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 03/10/2020

@author: Wilfried - IRAP

Software to manipulate projections for the sphere orb.
"""

import matplotlib
matplotlib.use('TkAgg')
 
import tkinter      as     tk
from   tkinter      import ttk
from   signal       import signal, SIGINT

from   threading    import Thread
import os.path      as     opath

# Program imports
import setup
from   icons        import iconload
from   sigint       import sigintHandler   
from   widgets      import PlotWindow, ConfigWindow, Validate, Tab

class mainApplication:
    '''
    Main application where all the different layouts are defined.
    '''
    
    def __init__(self, parent):
        '''
        Inputs
        ------
            parent : tk.Tk instance
                root propagated throughout the different Frames and Canvas
        '''

        self.parent            = parent
        self.color             = 'white smoke'
        self.parent.config(cursor='arrow', bg=self.color)
        
        # Initial program setup
        self.settings, errCode = setup.init()
        self.font              = self.settings['font']
        self.loadPath          = self.settings['path']
        icons                  = iconload(self.settings['iconPath'])
        projects               = self.settings['projects']
        
        if errCode != 0:
            print('YAML configuration could not be read correctly. A new one with default values has been created instead.')
       
        
        ######################################################
        #               Check for old projects               #
        ######################################################
        
        # If project file still exists, add it to the list
        self.projects = []
        for proj in projects:
            if opath.isfile(proj):
                self.projects.append(proj)
                
        # It at least one project exist, show validation window at startup
        if len(self.projects) > 0:
            
            # Validation window
            window = Validate(self, self, parent, 
                              mainText='You have old projects saved in the setting file. Select the files you want to open.',
                              listNames=self.projects,
                              textProperties={'highlightthickness':0, 'bd':0, 'bg':self.color, 'font':(self.font, 10)},
                              buttonsProperties={'bg':'floral white', 'activebackground':'linen'},
                              winProperties={'bg':self.color},
                              acceptFunction=lambda *args, **kwargs: self.loadProjects(*args, **kwargs))
            
            self.parent.lift()
            
            # For MAC it seems we must set False and then True
            window.overrideredirect(False)
            window.overrideredirect(True)
            
            window.focus_force()
            window.grab_set()
            window.geometry('+%d+%d' %(self.parent.winfo_screenwidth()//2-2*window.winfo_reqwidth(), self.parent.winfo_screenheight()//2-window.winfo_reqheight()))
            window.state('normal')
        
        
        ###########################################################
        #                    Custom ttk styles                    #
        ###########################################################
        
        # Custom style for Notebook
        self.style  = ttk.Style()
        self.style.configure('main.TNotebook', background=self.color)
        
        self.style.configure('main.TNotebook.Tab', padding=[5, 2], font=('fixed', 10))
        self.style.map('main.TNotebook.Tab',
                       background=[("selected", 'lavender'), ('!selected', 'white smoke')],
                       foreground=[('selected', 'RoyalBlue2')])
        
        
        #############################################################
        #               Load icons into Image objects               #
        #############################################################
        self.iconDict               = {}
        self.iconDict['FOLDER']     = tk.BitmapImage(data=icons['FOLDER'],     maskdata=icons['FOLDER_MASK'],     background='goldenrod')
        self.iconDict['FOLDER_256'] = tk.BitmapImage(data=icons['FOLDER_256'], maskdata=icons['FOLDER_256_MASK'], background='goldenrod')
        self.iconDict['FOLDER_17']  = tk.BitmapImage(data=icons['FOLDER_17'],  maskdata=icons['FOLDER_17_MASK'],  background='goldenrod')
        self.iconDict['DELETE']     = tk.BitmapImage(data=icons['DELETE'],     maskdata=icons['DELETE_MASK'],     background='light cyan', foreground='black')
        self.iconDict['DUPPLICATE'] = tk.BitmapImage(data=icons['DUPPLICATE'], maskdata=icons['DUPPLICATE_MASK'], background='black',      foreground='black')
        self.iconDict['CONFIG']     = tk.BitmapImage(data=icons['CONFIG'],     maskdata=icons['CONFIG_MASK'],     background=self.color,   foreground='black') 
        
        
        #############################################
        #                 Buttons                   #
        #############################################
        
        # Top frame with buttons and sliders
        self.topframe    = tk.Frame( self.parent, bg=self.color, bd=0, relief=tk.GROOVE)
        
        self.confButton  = tk.Button(self.topframe, image=self.iconDict['CONFIG'],
                                     bd=0, bg=self.color, highlightbackground=self.color, relief=tk.FLAT, activebackground=self.color)
        
        self.loadButton  = tk.Button(self.topframe, image=self.iconDict['FOLDER'], 
                                     bd=0, bg=self.color, highlightbackground=self.color, relief=tk.FLAT, activebackground='black')
        
        self.delButton   = tk.Button(self.topframe, image=self.iconDict['DELETE'], 
                                     bd=0, bg=self.color, highlightbackground=self.color, relief=tk.FLAT, activebackground=self.color)
        
        self.duppButton  = tk.Button(self.topframe, image=self.iconDict['DUPPLICATE'],
                                     bd=0, bg=self.color, highlightbackground=self.color, relief=tk.FLAT, activebackground=self.color)
        
        ##############################################
        #                   Scales                   #
        ##############################################
        
        self.scaleframe  = tk.Frame( self.topframe,   bg=self.color, bd=0, highlightthickness=0)
        self.latframe    = tk.Frame( self.scaleframe, bg=self.color, bd=0, highlightthickness=0)
        self.longframe   = tk.Frame( self.scaleframe, bg=self.color, bd=0, highlightthickness=0)
        
        self.latLabel    = tk.Label( self.latframe,  text='Latitude',  bg=self.color)
        self.longLabel   = tk.Label( self.longframe, text='Longitude', bg=self.color)
        
        self.latScale    = tk.Scale( self.latframe, length=200, width=12, orient='horizontal', from_=-90, to=90,
                                     cursor='hand1', showvalue=False,
                                     bg=self.color, bd=1, highlightthickness=1, highlightbackground=self.color, troughcolor='lavender', activebackground='black', font=('fixed', 11),
                                     command=lambda value: self.updateScale('latitude', value))
        
        self.longScale   = tk.Scale( self.longframe, length=200, width=12, orient='horizontal', from_=-180, to=180,
                                     cursor='hand1', showvalue=False,
                                     bg=self.color, bd=1, highlightthickness=1, highlightbackground=self.color, troughcolor='lavender', activebackground='black', font=('fixed', 11),
                                     command=lambda value: self.updateScale('longitude', value))
        
        
        ###########################################################
        #                     Bottom notebook                     #
        ###########################################################
        
        self.notebook    = ttk.Notebook(self.parent, style='main.TNotebook')
        
        # Keep track of notebook tabs
        self.tabs        = {}
        self.addTab()
        
        
        #######################################################################
        #                               Bindings                              #
        #######################################################################
        
        self.parent.bind('<Control-o>',    lambda *args, **kwargs: self.tabs[self.notebook.select()].askLoad())
        self.parent.bind('<Control-p>',    lambda *args, **kwargs: self.showConfigWindow(*args, **kwargs))
        
        self.confButton.bind('<Enter>',    lambda *args, **kwargs: self.iconDict['CONFIG'].configure(foreground='RoyalBlue2'))
        self.confButton.bind('<Leave>',    lambda *args, **kwargs: self.iconDict['CONFIG'].configure(foreground='black'))
        self.confButton.bind('<Button-1>', lambda *args, **kwargs: self.showConfigWindow(*args, **kwargs))
        
        self.loadButton.bind('<Enter>',    lambda *args, **kwargs: self.tabs[self.notebook.select()].loadButton.configure(bg='black')    if not self.tabs[self.notebook.select()].loaded else None)
        self.loadButton.bind('<Leave>',    lambda *args, **kwargs: self.tabs[self.notebook.select()].loadButton.configure(bg='lavender') if not self.tabs[self.notebook.select()].loaded else None)
        self.loadButton.bind('<Button-1>', lambda *args, **kwargs: self.tabs[self.notebook.select()].askLoad())
        
        self.delButton.bind( '<Enter>',    lambda *args, **kwargs: self.iconDict['DELETE'].configure(foreground='red',   background=self.color))
        self.delButton.bind( '<Leave>',    lambda *args, **kwargs: self.iconDict['DELETE'].configure(foreground='black', background='light cyan'))
        self.delButton.bind( '<Button-1>', lambda *args, **kwargs: self.delTab(*args, **kwargs))
        
        self.plotWindow = None
        self.duppButton.bind('<Enter>',    lambda *args, **kwargs: self.iconDict['DUPPLICATE'].configure(background='RoyalBlue2'))
        self.duppButton.bind('<Leave>',    lambda *args, **kwargs: self.iconDict['DUPPLICATE'].configure(background='black'))
        self.duppButton.bind('<Button-1>', lambda *args, **kwargs: self.showPlotWindow())
        
        self.latScale.bind(  '<Enter>',    lambda *args, **kwargs: self.latScale.configure(highlightbackground='RoyalBlue2'))
        self.latScale.bind(  '<Leave>',    lambda *args, **kwargs: self.latScale.configure(highlightbackground=self.color))
        self.longScale.bind( '<Enter>',    lambda *args, **kwargs: self.longScale.configure(highlightbackground='RoyalBlue2'))
        self.longScale.bind( '<Leave>',    lambda *args, **kwargs: self.longScale.configure(highlightbackground=self.color))
        
        self.notebook.bind(  '<<NotebookTabChanged>>', lambda *args, **kwargs: self.tabCghanged(*args, **kwargs))
                  
                  
        ##########################################################
        #                     Drawing frames                     #
        ##########################################################
                  
        self.confButton.pack(side=tk.LEFT, pady=10)
        self.loadButton.pack(side=tk.LEFT, pady=10)
        self.delButton.pack( side=tk.LEFT, pady=10)
        
        self.latLabel.grid(  row=0, stick=tk.W)
        self.longLabel.grid( row=0, stick=tk.W)
        self.latScale.grid(  row=1)
        self.longScale.grid( row=1)
        
        self.latframe.pack(  side=tk.LEFT,  padx=10)
        self.longframe.pack( side=tk.LEFT,  padx=10)
        self.scaleframe.pack(side=tk.LEFT,  padx=10, fill='x', expand=True)
        
        self.duppButton.pack(side=tk.RIGHT)
        
        self.topframe.pack(fill='x', padx=10)
        self.notebook.pack(fill='both', expand=True)
        
        
    ##############################################
    #            Creating new windows            #
    ##############################################
        
    def showConfigWindow(self, *args, **kwargs):
        '''Create or show back a configuration window to generate projections.'''
        
        winProperties     = {'bg':'white smoke'}
        entryProperties   = {'bg':'lavender', 'fg':'SpringGreen4'}
        self.configWindow = ConfigWindow(self, self, self.parent, title='Projection facility',
                                         winProperties=winProperties, entryProperties=entryProperties)
        size              = 500
        self.configWindow.geometry('%dx%d+%d+%d' %(size, size, (self.parent.winfo_screenwidth()-size)//2, (self.parent.winfo_screenheight()-size)//2))
            
        
        return
       
        
    def showPlotWindow(self, *args, **kwargs):
       '''Create or show back the separate window for the plot.'''
       
       self.duppButton.pack_forget()
       self.tabs[self.notebook.select()].showExplanation()
       
       data  = self.tabs[self.notebook.select()].data
       title = self.tabs[self.notebook.select()].name
       
       if self.plotWindow is not None:
           self.plotWindow.setTitle(title)
           self.plotWindow.state('normal')
           self.plotWindow.update(data)
       else:
           winProperties   = {'bg':'lavender'}
           self.plotWindow = PlotWindow(self, self, self.parent, data=data, winProperties=winProperties, title=title)
           
       return
    
    ##########################################################
    #                    Tab interactions                    #
    ##########################################################
    
    def addTab(self, *args, **kwargs):
        '''Add a new tab in the tab list.'''
            
        tab                                 = Tab(self.notebook, self, self.notebook, properties={'bg':'lavender', 'bd':1, 'highlightthickness':0})
        self.tabs[self.notebook.tabs()[-1]] = tab
        
        if len(self.tabs) > 1:    
            self.notebook.tab(self.notebook.tabs()[-1], state='disabled')
        return
    
    def delTab(self, *args, **kwargs):
        '''Delete a tab if some conditions are met'''
     
        # Remove the tab from the notebook AND the tab dictionary
        idd = self.notebook.select()
        if self.tabs[idd].loaded:
            self.plotWindow.update([[0, 0], [0, 0]])
            self.notebook.forget(idd)
            self.tabs.pop(idd)
        return
    
    def loadProjects(self, files, *args, **kwargs):
        '''
        Load the projects listed in files at startup only.
        
        Parameters
        ----------
            files : list of str
                projects yaml configuration files to load
        '''
        
        for f in files:
            idd = self.notebook.select()
            self.tabs[idd].load(f)
            self.notebook.select(self.notebook.tabs()[-1])
        return
    
    def tabCghanged(self, event, *args, **kwargs):
        '''Actions taken when a tab is changed.'''
        
        tab = self.tabs[event.widget.select()]
        tab.updateSliders()
        
        if not tab.loaded:
            self.duppButton.pack_forget()
        else:
            self.duppButton.pack(side=tk.RIGHT, padx=10)
        return
    
    ########################################
    #            Scale commands            #
    ########################################
    
    def updateScale(self, which, value, *args, **kwargs):
        '''Action taken when the latitude or longitude scales are updated.'''
        
        idd = self.notebook.select()
        
        if self.tabs[idd].loaded:
            if which == 'longitude':
                self.tabs[idd].updateGraph(longitude=value, latitude=self.latScale.get())
            elif which == 'latitude':
                self.tabs[idd].updateGraph(latitude=value, longitude=self.longScale.get())
                
            # Because it is a callback called at the very end of the load data process, we update back to normal the last tab here to avoid doing it before the scale values are updated
            if self.notebook.tab(self.notebook.tabs()[-1])['state'] != 'normal':
                self.notebook.tab(self.notebook.tabs()[-1], state='normal')
        return
    
    
    
class runMainloop(Thread):
    '''Class inheriting from threading.Thread. Defined this way to ensure that SIGINT signal from the shell can be caught despite the mainloop.'''
    
    def run(self):
        '''Run method from Thread called when using start()'''
        
        self.root = tk.Tk()
        self.root.title('Sphere - projections at hand')
        self.root.geometry('800x800+%d+%d' %(self.root.winfo_screenwidth()//2-400, self.root.winfo_screenheight()//2-400))
        
        app  = mainApplication(self.root)
        
        self.root.protocol("WM_DELETE_WINDOW", lambda signal=SIGINT, frame=None, obj=self, skipUpdate=True: sigintHandler(signal, obj, None, skipUpdate))
        
        #imgicon = ImageTk.PhotoImage(PROGRAMICON)
        #self.root.tk.call('wm', 'iconphoto', self.root._w, imgicon)
        
        self.root.mainloop()


def main():
    
    mainLoop = runMainloop()
    
    # Link Ctrl+C keystroke in shell to terminating window
    signal(SIGINT, lambda signal, frame, obj=mainLoop, root=None, skipUpdate=False: sigintHandler(signal, obj, root, skipUpdate))

    mainLoop.start()

if __name__ == '__main__':
    main()