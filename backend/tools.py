# Mercier Wilfried - IRAP
# Tools used to generate the projection

from   mpl_toolkits.basemap import Basemap
from   threading            import Thread
import os.path              as     opath
import numpy                as     np
import matplotlib.pyplot    as     plt
import matplotlib
import yaml
import PIL
import warnings
warnings.filterwarnings("ignore")

def checkPairs(data, name):
   '''
   Check whether given data is an iterable with length=2.

   Parameters
   ----------
      data : any type
         data to check
      name : str
         name used in the error messageO
   '''

   if not isinstance(data, (list, tuple)):
      raise TypeError('%s must either be a list or a tuple.' %name)

   if len(data) != 2:
      raise ValueError('%s must be a list or tuple of length 2 but current length is %d' %len(data))
   return

#################################################################
#                YAML project file manipulation                 #
#################################################################

def writeYAML(name, coordsInit, limLatitude, limLongitude, step, unit='°'):
   '''
   Write a YAML configuration file

   Parameters
   ----------
      coordsInit : (int, int)
         coordinates of the first frame to be drawn when data is loaded. Must be given in grid coordinates, not in angle unit.
      limLatitude : (int/float, int/float)
         minimum and maximum latitude used to generate the grid of images.
      limLongitude : (int/float, int/float)
         minimum and maximum longitude used to generate the grid of images.
      name : str
         output YAML file name
      step : float/int
         increment in longitude and latitude. Assumed to be of the same unit as latitude and longitude.

   Optional parameters
   -------------------
      unit : str
         unit shown in Sphere manipulation window for the latitude and longitude. Default is degrees (°).
   '''

   # Check a few things first
   if not isinstance(name, str):
      raise TypeError('Output name should be a string.')

   if name.split('.')[-1].lower() != 'yaml':
      raise ValueError('A .yaml output name is required.')

   for name, data in zip(['coordsInit', 'limLatitude', 'limLongitude'], [coordsInit, limLatitude, limLongitude]):
      checkPairs(data, name)

   print(limLatitude, limLongitude)
   outDict = {'x0'      : float(coordsInit[0]),
              'y0'      : float(coordsInit[1]),
              'lat min' : float(limLatitude[0]),
              'lat max' : float(limLatitude[1]),
              'long min': float(limLongitude[0]),
              'long max': float(limLongitude[1]),
              'step'    : step
              'unit'    : unit
             }

   outYAML  = yaml.dump(outDict, Dumper=yaml.Dumper)
   with open(name, 'w') as f:
      f.write(outYAML)
   return


######################################
#             Projection             #
######################################

class Projection(Thread):
   '''A class to project some data with speed improvement from threading.'''

   def __init__(self, outname, data, longitude, longIndices, latitude):
      '''
      Initialisation
      --------------
         data : numpy 2D array or numpy RGB array
            data corresponding to the given matrix image loaded
         latitude : list of float/int
            latitudes where to compute the projection
         longitude : list of float/int
            full list of longitudes
         longIndices : list of int
            indices int the longitude array/list where the thread must compute the projection
         outname : str
            name of the outputfile
      '''

      Thread.__init__(self)
      self.data    = data
      self.indices = longIndices
      self.long    = longitude
      self.lat     = latitude
      self.outname = outname

   def run(self):
      for index in self.indices:
         for pos, lat in enumerate(self.lat):

            print('Computing at (long, lat) = (%s, %s)' %(long, lat))
            m         = Basemap(projection='aeqd', lat_0=lat, lon_0=self.long[index])
            projData  = []
            for i in range(shp[2]):
               projData.append(m.transform_scalar(data[:,:,i], longList, latList, 720, 720))

#            plt.imsave(opath.join(outpath, outpath + '_%d,%d' %(long, lapos) + '.' + file.split('.')[-1])>
      return

def projection(data, outName, limLatitude, limLongitude, step, numThreads, initPos=None):
   '''
   Perform the projections given the step, bounds and number of threads allowed to use.

   Parameters
   ----------
      data : numpy 2D array or numpy RGB array
         data corresponding to the given matrix image loaded
      limLatitude : (int/float, int/float)
         lower and upper values of the latitude corresponding to the image horizontal borders
      limLongitude : (int/float, int/float)
         lower and upper values of the lnogitude corresponding to the image vertical borders
      numThreads : int
         number of threads to use for the computation
      outName : str
         output YAML file name
      step : float/int
         step used when computed a new image with different coordinates. Units is assumed identical as latitude and longitude.

   Optional parameters
   -------------------
      initPos : (int, int)
         longitude and latitude initial position written in the YAML file. Must be given in grid units. If None, first longitude lower bound and latitude upper bound are used.
   '''

   for name, data in zip(['limLatitude', 'limLongitude'], [limLatitude, limLongitude]):
      checkPairs(data, name)

   if not isinstance(step, (int, float)):
      raise TypeError('step must either be a float or an int.')

   if not isinstance(numThreads, int):
      raise TypeError('Number of threads must be an int.')
   if numThreads < 1:
      raise ValueError('Given number of threads is %s but accepted value must be >= 1.' %numThreads)

   # Shape of the image, longitude and latitude values for each pixel
   shape         = np.shape(data)
   longList      = np.linspace(limLongitude[0], limLongitude[-1], shp[1])
   latList       = np.linspace(limLatitude[0],  limLongitude[-1], shp[0])

   # Arrays of latitude and longitude where to compute the projections
   allLong       = np.arange(limLongitude[0], limLongitude[-1]+step, step)
   lenLong       = len(allLong)-1
   allLat        = np.arange(limLatitude[0],  limLatitude[-1]+step,  step)
   lenLat        = len(allLat)-1

   if initPos is None:
      initPos    = [0, lenLat]

   # Dictionnary of projections: keys are labelled with the following convention 'longPos,latPos'
   allProj       = {}

   # Setup number of threads
   numThreads    = 8
   if numThreads > lenLong+1:
      numThreads = lenLong+1

   # Write YAML configuration file
   writeYAML(outname, initPos, (allLat[0], allLat[-1]), (allLong[0], allLong[-1]), step)

   # We split the array into subarrays so that each thread is fed with independent data
   threads       = []
   long          = np.array_split(np.indices(allLong.shape)[0], numThreads)

   print('Setting up the projection dictionnary...')
   for i in range(numThreads):
      threads.append(dictProj(long[i], allLat))
      threads[i].start()

   for i in range(numThreads):
      threads[i].join()
      dic     = threads[i].dict
      allProj = {**allProj, **dic}
      print('Thread %d done.' %i)
