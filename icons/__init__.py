# Loading layout icons
from   glob    import glob
from   PIL     import Image
import os.path as     opath
import builtins

def iconload(path):
   '''Load all the icons located in this directory'''

   ICONS          = {}
   icons          = glob(opath.join(path, '*.xbm'))

   for icon in icons:
      path, name  =  opath.split(icon)
      with open(icon) as f:
         ICONS[name.rsplit('.', 1)[0].upper()] = f.read()
   return ICONS
