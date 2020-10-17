"""
Mercier Wilfried - IRAP

Setting up the program at startup.
"""

import os
import os.path as     opath
from   yaml    import load, dump
from   yaml    import Loader, Dumper

def default(outname):
   '''
   Utility function writing a default YAML setting file if none is found.

   Parameters
   ----------
      outname : str
         name of the output YAML file
   '''

   configuration = {'font'    : 'fixed',
                    'path'    : opath.expanduser('~'),
                    'iconPath': opath.join(opath.dirname(__file__), 'icons'),
                    'projects': []
                   }
   writeConfiguration(outname, configuration)
   return

def writeConfiguration(outname, configuration):
   '''
   Utility function to write the YAML configuration file with the given parameters.

   Parameters
   ----------
      configuration : dict
         dictionnary to be converted into a YAML file
      outname : str
         name of the output YAML file
   '''

   output         = dump(configuration, Dumper=Dumper)
   with open(outname, 'w') as f:
      f.write(output)
   return

def init():
   '''
   Initialise code parameters at startup.
   Return the settings dictionnary and an error code (0 is ok, -1 if error).
   '''

   file           = 'settings.yaml'

   if not opath.isfile(file):
      default(file)

   # Load configuration option from setting file
   with open(file, 'r') as f:
      settings    = load(f, Loader=Loader)

   # If a key is missing, the setting file is saved and a new one is created with default values
   errCode        = 0
   for i in ['font', 'path', 'iconPath', 'projects']:
      if i not in settings.keys():
         os.rename(r'%s' %file, r'~%s' %file)
         default(file)
         settings = load(file, Loader=Loader)
         errCode  = -1

   return settings, errCode
