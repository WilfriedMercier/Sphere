import builtins

def sigintHandler(signal, obj=None, root=None, skipUpdate=False, *args, **kwargs):
    '''
    Handle SIGINT (Ctrl+C in shell) signal + tkinter WM_DELETE_WINDOW event.

    Mandatory parameters
    --------------------
        signal : int
            type of signal    
    
    Optional inputs
    ---------------
        obj : any type with a root attribute
            object with root attribute which is to be destroyed. If obj is None, root will be used unless it is also None.
        root : tkinter root object
            root object with quit method.
        skipUpdate : bool
            whether to skip the update method. Default is to not skip it.
    '''
    
    if obj is not None:
        obj.root.quit()
    elif root is not None:
        root.quit()
    else:
        raise ValueError('Neither tk.Tk object, nor root was provided. Exiting not possible.')
        return
    
    if not skipUpdate:
        obj.root.update()
    print('Thanks for using Sphere. See you another time !')
    return

builtins.sigintHandler = sigintHandler
