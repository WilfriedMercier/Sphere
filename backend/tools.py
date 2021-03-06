# Mercier Wilfried - IRAP
# Tools used to generate the projection

from   threading            import Thread
import os.path              as     opath
import numpy                as     np
import cartopy.crs          as     ccrs
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
         name used in the error message
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
      raise ValueError('Output file must have a .yaml file extension.')

   checkPairs(coordsInit, 'coordsInit')   

   outDict = {'x0'      : float(coordsInit[0]),
              'y0'      : float(coordsInit[1]),
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

   def __init__(self, data, longitude, longIndices, latitude, directory='out', name='out', size=(1080, 1080)):
      '''
      Initialisation
      
      Parameters
      ----------
         data : numpy 2D array or numpy RGB array
            data corresponding to the given matrix image loaded
         latitude : list of float/int
            latitudes where to compute the projection
         longitude : list of float/int
            full list of longitudes where to compute the projection
         longIndices : list of int
            indices in the longitude array/list where the thread must compute the projection
            
      Optional parameters
      -------------------
         directory : str
             name of the directory where to write the ouput files. Default is 'out'.
         name : str
            name of the outputfile. Default is 'out'.
      '''
      
      if not isinstance(name, str):
          raise TypeError('Output name must be of type string only.')
          
      Thread.__init__(self)
      
      # Data and its longitude and latitude
      self.data      = data
      self.size      = size
      
      # Longitude and latitude where to compute the projections
      self.indices   = longIndices
      self.long      = longitude
      self.lat       = latitude
      
      # General output name used to save the figures
      self.name      = name
      self.directory = directory
      
      # Keyword used to stop the thread if necessary
      self.ok        = True 

   def run(self):
       
      for index in self.indices:
         for pos, lat in enumerate(self.lat):
             
            if not self.ok:
                break

            print('Computing at (longitude, latitude) = (%s, %s)' %(self.long[index], lat))
            
            # Generate new figure
            if self.size[0] == self.size[1]:
                figsize = (1, 1)
                dpi     = self.size[0]
            elif self.size[0] > self.size[1]:
                figsize = (self.size[0]/self.size[1], 1)
                dpi     = self.size[1]
            else:
                figsize = (self.size[0], self.size[1]/self.size[0])
                dpi     = self.size[0]
            
            plt.figure(figsize=[i*1.3 for i in figsize], dpi=dpi, frameon=False)
            plt.axes(projection=ccrs.AzimuthalEquidistant(central_latitude=lat, central_longitude=self.long[index]))
            plt.imshow(self.data, transform=ccrs.PlateCarree())

            # Use the indices rather than the values to name the files
            plt.savefig(opath.join(self.directory, self.name + '_%d,%d' %(index, pos) + '.jpg'), format='jpg',
                        transparent=True, bbox_inches='tight', pad_inches=0)
            
         if not self.ok:
             break
         
      return

class RunProjection(Thread):

    def __init__(self, data, directory, name, step, numThreads, initPos=None, allLong=None, allLat=None, size=(1080, 1080)):
        '''
        Perform the projections given the step, bounds and number of threads.
        
        Parameters
        ----------
           data : numpy 2D array or numpy RGB array
              data corresponding to the given matrix image loaded
           directory : str
              name of the directory where to write the YAML and output files
           name : str
              name used for the YAML and output files
           numThreads : int
              number of threads to use for the computation
           step : float/int
              step used when computed a new image with different coordinates. Unit is assumed identical as latitude and longitude.
        
        Optional parameters
        -------------------
           allLat : numpy array
              the latitudes where to compute the projection. If not given, the array is computed.
           allLong : numpy array
              the longitudes where to compute the projection. If not given, the array is computed. 
           initPos : (int, int)
              longitude and latitude initial position written in the YAML file. Must be given in grid units. If None, first longitude lower bound and latitude upper bound are used.
        '''
        
        Thread.__init__(self)
        
        if not isinstance(name, str):
            raise TypeError('Name should be of type string.')
        
        if not isinstance(directory, str):
            raise TypeError('Directory should be of type string')
        
        if not isinstance(step, (int, float)):
           raise TypeError('step must either be a float or an int.')
        
        if not isinstance(numThreads, int):
           raise TypeError('Number of threads must be an int.')
           
        if numThreads < 1:
           raise ValueError('Given number of threads is %s but accepted value must be >= 1.' %numThreads)
           
        self.name          = name
        self.directory     = directory
        
        # Create directory if it does not exist
        os.makedirs(self.directory, exist_ok=True)   
        
        self.step          = step
        self.data          = data
        self.size          = size
        
        # Arrays of latitude and longitude where to compute the projections
        if allLong is None:
            self.allLong   = np.arange(-180, 180, self.step)
        else:
            self.allLong   = allLong
        
        if allLat is None:
            self.allLat    = np.arange(-90,  90+self.step,  self.step)
        else:
            self.allLat    = allLat    
            
        self.lenLong       = len(self.allLong)-1
        self.lenLat        = len(self.allLat)-1
        
        if initPos is None:
           self.initPos    = [0, self.lenLat]
        else:
           self.initPos    = initPos
        
        # Setup number of threads
        if numThreads > self.lenLong+1:
           self.numThreads = self.lenLong+1
        else:
           self.numThreads = numThreads 
        
        # Write YAML configuration file
        writeYAML(opath.join(directory, name + '.yaml'), self.initPos, (self.allLat[0], self.allLat[-1]), (self.allLong[0], self.allLong[-1]), self.step)
        
        # We split the array into subarrays so that each thread is fed with independent data
        self.threads       = []
        self.long          = np.array_split(np.indices(self.allLong.shape)[0], self.numThreads)
        
    def run(self, *args, **kwargs):
        
        # Launch the run method for each thread to improve speed 
        print('Setting up the projection dictionnary...')
        for i in range(self.numThreads):
           self.threads.append(Projection(self.data, self.allLong, self.long[i], self.allLat, directory=self.directory, name=self.name, size=self.size))
           self.threads[i].setDaemon(True)
           self.threads[i].start()
        
        # Join threads once job is done
        for i in range(self.numThreads):
           self.threads[i].join()
           print('Thread %d done.' %i)