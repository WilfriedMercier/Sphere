# Mercier Wilfried - IRAP
# Tools used to generate the projection

# Since it is not used yet, no need to really import it
try:
   from   mpl_toolkits.basemap import Basemap
except:
   pass

from   threading            import Thread
import os.path              as     opath
import numpy                as     np
import matplotlib.pyplot    as     plt
import os
import yaml
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
              'step'    : step,
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

   def __init__(self, data, dataLong, dataLat, longitude, longIndices, latitude, 
                directory='out', name='out', size=(720, 720)):
      '''
      Initialisation
      
      Parameters
      ----------
         data : numpy 2D array or numpy RGB array
            data corresponding to the given matrix image loaded
         dataLat : numpy array
             latitude corresponding to each pixel line in the image
         dataLong : numpy array
             longitude corresponding to each pixel column in the image
         latitude : list of float/int
            latitudes where to compute the projection
         longitude : list of float/int
            full list of longitudes where to compute the projection
         longIndices : list of int
            indices int the longitude array/list where the thread must compute the projection
            
      Optional parameters
      -------------------
         directory : str
             name of the directory where to write the ouput files. Default is 'out'.
         name : str
            name of the outputfile. Default is 'out'.
         size : (int, int)
            size of the output images in x and y. Default is 720 pixels in both directions. 
      '''
      
      if not isinstance(name, str):
          raise TypeError('Output name must be of type string only.')
          
      if not isinstance(size, (list, tuple)) or len(size) != 2:
          raise TypeError('Size of images must be a tuple of length 2.')
          
      Thread.__init__(self)
      
      # Data and its longitude and latitude
      self.data    = data
      self.dataLong = dataLong
      self.dataLat  = dataLat 
      
      # Longitude and latitude where to compute the projections
      self.indices = longIndices
      self.long    = longitude
      self.lat     = latitude
      
      # General output name used to save the figures
      self.name    = name
      self.size    = size 

   def run(self):
      
      # Make directory if it does not exist yet
      shp = np.shape(self.data)[2]
       
      for index in self.indices:
         for pos, lat in enumerate(self.lat):

            print('Computing at (long, lat) = (%s, %s)' %(self.long[index], lat))
            m         = Basemap(projection='aeqd', lat_0=lat, lon_0=self.long[index])
            
            # Compute the projected data for each of the 3 RGB arrays in the image
            projData  = []
            for i in range(shp):
               projData.append(m.transform_scalar(self.data[:,:,i], self.dataLong, self.dataLat, int(self.size[0]), int(self.size[1])))

            # Use the indices rather than the values to name the files
            plt.imsave(opath.join(self.directory, self.name + '_%d,%d' %(self.long.index(self.long[index]), pos) + '.jpg'), \
                       np.asarray(np.moveaxis(projData, 0, -1), dtype='uint8'), origin='lower', format='.jpg')
      return

def projection(data, directory, name, limLatitude, limLongitude, step, numThreads, initPos=None):
    '''
    Perform the projections given the step, bounds and number of threads allowed to use.
    
    Parameters
    ----------
        directory : str
            name of the directory where to write the YAML and output files
       data : numpy 2D array or numpy RGB array
          data corresponding to the given matrix image loaded
       limLatitude : (int/float, int/float)
          lower and upper values of the latitude corresponding to the image horizontal borders
       limLongitude : (int/float, int/float)
          lower and upper values of the lnogitude corresponding to the image vertical borders
       numThreads : int
          number of threads to use for the computation
       name : str
          name used for the YAML and output files
       step : float/int
          step used when computed a new image with different coordinates. Units is assumed identical as latitude and longitude.
    
    Optional parameters
    -------------------
       initPos : (int, int)
          longitude and latitude initial position written in the YAML file. Must be given in grid units. If None, first longitude lower bound and latitude upper bound are used.
    '''
    
    if not isinstance(name, str):
        raise TypeError('Name should be of type string.')
    
    if not isinstance(directory, str):
        raise TypeError('Directory should be of type string')
    
    for dname, data in zip(['limLatitude', 'limLongitude'], [limLatitude, limLongitude]):
       checkPairs(data, dname)
    
    if not isinstance(step, (int, float)):
       raise TypeError('step must either be a float or an int.')
    
    if not isinstance(numThreads, int):
       raise TypeError('Number of threads must be an int.')
    if numThreads < 1:
       raise ValueError('Given number of threads is %s but accepted value must be >= 1.' %numThreads)
    
    # Create directory if it does not exist
    os.makedirs(directory, exist_ok=True)   
    
    # Shape of the image, longitude and latitude values for each pixel
    shp           = np.shape(data)
    longList      = np.linspace(limLongitude[0], limLongitude[-1], shp[1])
    latList       = np.linspace(limLatitude[0],  limLongitude[-1], shp[0])
    
    # Arrays of latitude and longitude where to compute the projections
    allLong       = np.arange(limLongitude[0], limLongitude[-1]+step, step)
    lenLong       = len(allLong)-1
    allLat        = np.arange(limLatitude[0],  limLatitude[-1]+step,  step)
    lenLat        = len(allLat)-1
    
    if initPos is None:
       initPos    = [0, lenLat]
    
    # Setup number of threads
    numThreads    = 8
    if numThreads > lenLong+1:
       numThreads = lenLong+1
    
    # Write YAML configuration file
    writeYAML(opath.join(directory, name), initPos, (allLat[0], allLat[-1]), (allLong[0], allLong[-1]), step)
    
    # We split the array into subarrays so that each thread is fed with independent data
    threads       = []
    long          = np.array_split(np.indices(allLong.shape)[0], numThreads)
    
    # Launch the run method for each thread to improve speed 
    print('Setting up the projection dictionnary...')
    for i in range(numThreads):
       threads.append(Projection(data, longList, latList, allLong, long[i], allLat, 
                                 directory=directory, name=name))
       threads[i].start()
    
     # Join threads once job is done
    for i in range(numThreads):
       threads[i].join()
       print('Thread %d done.' %i)
