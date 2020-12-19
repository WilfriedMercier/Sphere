#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
This code and its docstrings were adapted from the mpl_toolkit.basemap project (https://matplotlib.org/basemap/) which is now deprecated in favor of the Cartopy project (https://scitools.org.uk/cartopy/docs/latest/).
Only the code necessary to perform the aeqd projection was kept and everything else was removed.
For different projections or more options, please refer to the web sites above.

Adapted by : Wilfried Mercier - IRAP
'''

from   __future__ import absolute_import, division, print_function
import numpy      as     np
import pyproj

__version__                = '1.2.2'

class Proj(object):
    """
    Peform a cartographic transformations (converts from longitude,latitude to native map projection x,y coordinates and vice versa) using proj (http://proj.maptools.org/).
    Uses a pyrex generated C-interface to libproj.

    __init__ method sets up projection information.
    __call__ method compute transformations.
    See docstrings for __init__ and __call__ for details.

    Contact: Jeff Whitaker <jeffrey.s.whitaker@noaa.gov>
    """

    def __init__(self, projparams, llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat, urcrnrislatlon=True):
        """
        Initialize a Proj class instance.

        Parameters
        ----------
            projparams : dict
                dictionary containing proj map projection control parameter key/value pairs. See the proj documentation (http://www.remotesensing.org/proj/) for details.
            llcrnrlon, llcrnrlat : int/float
                lon and lat (in degrees) of lower left hand corner of projection region.
            urcrnrlon, urcrnrlat : int/float
                lon and lat (in degrees) of upper right hand corner of projection region if urcrnrislatlon=True. Otherwise, urcrnrlon and urcrnrlat are x,y in projection coordinates (units meters), assuming the lower left corner is x=0,y=0.
        """
        
        self.projparams = projparams
        self.projection = 'aeqd'
        
        # rmajor is the semi-major axis, rminor the semi-minor axis and esq is eccentricity squared
        self.rmajor = projparams['R']
        self.rminor = self.rmajor
        
        self.ellipsoid  = False
        self.flattening = 0
        self.esq        = 0
        
        self.llcrnrlon = llcrnrlon
        self.llcrnrlat = llcrnrlat
    
        self._fulldisk = True
        self._proj4    = pyproj.Proj(projparams)
            
        llcrnrx        = -np.pi*self.rmajor
        llcrnry        = -np.pi*self.rmajor
        self._width    = -llcrnrx
        self._height   = -llcrnry
        urcrnrx        = -llcrnrx
        urcrnry        = -llcrnry
            
        # Compute x_0, y_0 so ll corner of domain is x=0, y=0
        self.projparams['x_0'] = -llcrnrx
        self.projparams['y_0'] = -llcrnry
        llcrnrx                = llcrnrlon
        llcrnry                = llcrnrlat
        
        if urcrnrislatlon:
            self.urcrnrlon     = urcrnrlon
            self.urcrnrlat     = urcrnrlat
            urcrnrx            = 2.*self._width
            urcrnry            = 2.*self._height
        else:
            urcrnrx              = urcrnrlon
            urcrnry              = urcrnrlat
            urcrnrlon, urcrnrlat = self(urcrnrx, urcrnry, inverse=True)
            self.urcrnrlon       = urcrnrlon
            self.urcrnrlat       = urcrnrlat

        # Corners of domain
        self.llcrnrx             = llcrnrx
        self.llcrnry             = llcrnry
        self.urcrnrx             = urcrnrx
        self.urcrnry             = urcrnry
        
        if urcrnrx > llcrnrx:
            self.xmin            = llcrnrx
            self.xmax            = urcrnrx
        else:
            self.xmax            = llcrnrx
            self.xmin            = urcrnrx
            
        if urcrnry > llcrnry:
            self.ymin            = llcrnry
            self.ymax            = urcrnry
        else:
            self.ymax            = llcrnry
            self.ymin            = urcrnry

    def __call__(self, *args, **kw):
        """
        Calling a Proj class instance with the arguments lon, lat will  convert lon/lat (in degrees) to x/y native map projection coordinates (in meters).  
        If optional keyword 'inverse' is True (default is False), the inverse transformation from x/y to lon/lat is performed.

        lon,lat can be either scalar floats or N arrays.
        """
        
        if len(args) == 1:
            xy       = args[0]
            onearray = True
        else:
            x,y      = args
            onearray = False
            
        inverse        = kw.get('inverse', False)
        
        if onearray:
            outxy      = self._proj4(xy, inverse=inverse)
        else:
            outx, outy = self._proj4(x, y, inverse=inverse)
            
        if onearray:
            return outxy
        else:
            return outx, outy

    def makegrid(self, nx, ny, returnxy=False):
        """
        Return arrays of shape (ny, nx) containing lon, lat coordinates of an equally spaced native projection grid.
        If returnxy=True, the x,y values of the grid are returned also.
        """
        
        dx         = (self.urcrnrx - self.llcrnrx)/(nx-1)
        dy         = (self.urcrnry - self.llcrnry)/(ny-1)
        x          = self.llcrnrx + dx*np.indices((ny, nx), np.float32)[1, :, :]
        y          = self.llcrnry + dy*np.indices((ny, nx), np.float32)[0, :, :]
        lons, lats = self(x, y, inverse=True)
        
        if returnxy:
            return lons, lats, x, y
        else:
            return lons, lats