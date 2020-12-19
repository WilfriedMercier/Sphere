#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This code and its docstrings were adapted from the mpl_toolkit.basemap project (https://matplotlib.org/basemap/) which is now deprecated in favor of the Cartopy project (https://scitools.org.uk/cartopy/docs/latest/).
Only the code necessary to perform the aeqd projection was kept and everything else was removed.
For different projections or more options, please refer to the web sites above.

Adapted by : Wilfried Mercier - IRAP
"""

import math
import numpy    as     np
from   .proj    import Proj

###################################################
#            Utility public functions             #
###################################################

def interp(datain, xin, yin, xout, yout, order=1):
    """
    Interpolate data (``datain``) on a rectilinear grid (with x = ``xin`` and y = ``yin``) to a grid with x = ``xout``, y= ``yout``.

    .. tabularcolumns:: |l|L|

    ==============   ====================================================
    Arguments        Description
    ==============   ====================================================
    datain           a rank-2 array with 1st dimension corresponding to y, 2nd dimension x.
    xin, yin         rank-1 arrays containing x and y of datain grid in increasing order.
    xout, yout       rank-2 arrays containing x and y of desired output grid.
    order            0 for nearest-neighbor interpolation, 1 for bilinear interpolation, 3 for cublic spline (default 1). order=3 requires scipy.ndimage.
    ==============   ====================================================

    .. note::
     If datain is a masked array and order=1 (bilinear interpolation) is used, elements of dataout will be masked if any of the four surrounding points in datain are masked.  
     To avoid this, do the interpolation in two passes, first with order=1 (producing dataout1), then with order=0 (producing dataout2).  
     Then replace all the masked values in dataout1 with the corresponding elements in dataout2 (using numpy.where).
     This effectively uses nearest neighbor interpolation if any of the four surrounding points in datain are masked, and bilinear interpolation otherwise.

    Returns ``dataout``, the interpolated data on the grid ``xout, yout``.
    """
    
    # xin and yin must be monotonically increasing
    if xin[-1]-xin[0] < 0 or yin[-1]-yin[0] < 0:
        raise ValueError('xin and yin must be increasing!')
        
    if xout.shape != yout.shape:
        raise ValueError('xout and yout must have same shape!')
        
    # Check that xout, yout are within region defined by xin, yin
    if xout.min() < xin.min() or xout.max() > xin.max() or yout.min() < yin.min() or yout.max() > yin.max():
        raise ValueError('yout or xout outside range of yin or xin')
        
    # Compute grid coordinates of output grid.
    delx        = xin[1:]-xin[0:-1]
    dely        = yin[1:]-yin[0:-1]
    
    if max(delx)-min(delx) < 1.e-4 and max(dely)-min(dely) < 1.e-4:
        xcoords = (len(xin)-1)*(xout-xin[0])/(xin[-1]-xin[0])
        ycoords = (len(yin)-1)*(yout-yin[0])/(yin[-1]-yin[0])
    else:
        xoutflat = xout.flatten()
        youtflat = yout.flatten()
        
        ix = (np.searchsorted(xin, xoutflat)-1).tolist()
        iy = (np.searchsorted(yin, youtflat)-1).tolist()
        
        xoutflat = xoutflat.tolist()
        xin      = xin.tolist()
        youtflat = youtflat.tolist()
        yin      = yin.tolist()
        
        xcoords  = []
        ycoords  = []
        for n, i in enumerate(ix):
            
            # Outside of range on xin (lower end)
            if i < 0:
                xcoords.append(-1)
                
            # outside range on upper end
            elif i >= len(xin)-1:
                xcoords.append(len(xin))
                
            else:
                xcoords.append(float(i) + (xoutflat[n] - xin[i])/(xin[i+1] - xin[i]))
                
        for m, j in enumerate(iy):
            
            # Outside of range of yin (on lower end)
            if j < 0:
                ycoords.append(-1)
                
            # Outside range on upper end
            elif j >= len(yin)-1:
                ycoords.append(len(yin))
                
            else:
                ycoords.append(float(j) + (youtflat[m] - yin[j])/(yin[j+1] - yin[j]))
                
        xcoords  = np.reshape(xcoords, xout.shape)
        ycoords  = np.reshape(ycoords, yout.shape)
        
    # Data outside range xin, yin will be clipped to values on boundary
    xcoords      = np.clip(xcoords, 0, len(xin)-1)
    ycoords      = np.clip(ycoords, 0, len(yin)-1)
    
    # Interpolate to output grid using bilinear interpolation
    if order == 1:
        xi       = xcoords.astype(np.int32)
        yi       = ycoords.astype(np.int32)
        xip1     = xi+1
        yip1     = yi+1
        xip1     = np.clip(xip1,0,len(xin)-1)
        yip1     = np.clip(yip1,0,len(yin)-1)
        delx     = xcoords-xi.astype(np.float32)
        dely     = ycoords-yi.astype(np.float32)
        dataout = (1. - delx)*(1. - dely)*datain[yi, xi] + delx*dely*datain[yip1, xip1] + (1. - delx)*dely*datain[yip1, xi] + delx*(1. - dely)*datain[yi, xip1]
    elif order == 0:
        xcoordsi = np.around(xcoords).astype(np.int32)
        ycoordsi = np.around(ycoords).astype(np.int32)
        dataout  = datain[ycoordsi,xcoordsi]
    elif order == 3:
        try:
            from scipy.ndimage import map_coordinates
        except ImportError:
            raise ValueError('scipy.ndimage must be installed if order=3')
            
        coords   = [ycoords,xcoords]
        dataout  = map_coordinates(datain, coords, order=3, mode='nearest')
    else:
        raise ValueError('order keyword must be 0, 1 or 3')
        
    return dataout

###################################################
#            Utility private functions            #
###################################################

def _insert_validated(d, param, name, minval, maxval):
    '''
    Insert into a dictionary the given parameter after checking it.

    Parameters
    ----------
        maxval : int/float
            maximum value
        minval : int/float
            minimum value
        name : str
            name of the parameter
        param : int/float
            parameter to check
    '''
    
    if param is not None:
        d[name] = _validated_ll(param, name, minval, maxval)
    else:
        raise ValueError('One of the values to be inserted into the projection dictionary is None.')


def _validated_ll(param, name, minval, maxval):
    '''
    Validate or not the value of a parameters between given bounds.

    Parameters
    ----------
        maxval : int/float
            maximum value
        minval : int/float
            minimum value
        name : str
            name of the parameter
        param : int/float
            parameter to check
        
    Return parameter value if ok and raise a ValueError otherwise.
    '''
    
    param = float(param)
    if param > maxval or param < minval:
        raise ValueError('%s must be between %f and %f degrees' %(name, minval, maxval))
    return param


#############################
#           Class           #
#############################

class Basemap(object):

    def __init__(self, lat_0, lon_0, *args, **kwargs):

        """
        Sets up a basemap with aeqd map projection.
           
        Calling a Basemap class instance with the arguments lon, lat will convert lon/lat (in degrees) to x/y map projection coordinates (in meters). 
        The inverse transformation is done if the optional keyword ``inverse`` is set to True.
        
        Parameters
        ----------
            lat_0 : int/float
                central latitude
            lon_0 : int/float
                central longitude
        """

        # Set up projection parameter dict
        projparams          = {'R':6370997.0, 'units':'m'}

        # Add to projparams the parameters after having checked them
        _insert_validated(projparams, lat_0,  'lat_0',  -90,  90)
        _insert_validated(projparams, lon_0,  'lon_0',  -180, 180)
            
        self.llcrnrlon      = -180.
        self.llcrnrlat      = -90.
        self.urcrnrlon      =  180
        self.urcrnrlat      =  90.

        self.projtran       = Proj(projparams, self.llcrnrlon, self.llcrnrlat, self.urcrnrlon, self.urcrnrlat)

    def __call__(self, x, y, inverse=False):
        """
        Calling a Basemap class instance with the arguments lon, lat will convert lon/lat (in degrees) to x/y map projection coordinates (in meters).
        If optional keyword ``inverse`` is True (default is False), the inverse transformation from x/y to lon/lat is performed.

        The inverse transformation always returns longitudes between -180 and 180 degrees.
        Input arguments lon, lat can be either scalar floats, sequences, or numpy arrays.
        """
        
        return self.projtran(x, y, inverse=inverse)

    def makegrid(self, nx, ny):
        """Return arrays of shape (ny, nx) containing lon, lat coordinates of an equally spaced native projection grid."""
        
        return self.projtran.makegrid(nx, ny)

    def transform_scalar(self, datin, lons, lats, nx, ny, order=1):
        """
        Interpolate a scalar field (``datin``) from a lat/lon grid with longitudes = ``lons`` and latitudes = ``lats`` to a ``ny`` by ``nx`` map projection grid.  

        .. tabularcolumns:: |l|L|

        ==============   ====================================================
        Argument         Description
        ==============   ====================================================
        datin            input data on a lat/lon grid.
        lons, lats       rank-1 arrays containing longitudes and latitudes (in degrees) of input data in increasing order
        nx, ny           The size of the output regular grid in map projection coordinates
        order            0 for nearest-neighbor interpolation, 1 for bilinear, 3 for cubic spline (Default 1).
                         Cubic spline interpolation requires scipy.ndimage.
        ==============   ====================================================

        Returns ``datout`` (data on map projection grid).
        """
        
        # Check that lons, lats increasing
        delon            = lons[1:]-lons[0:-1]
        delat            = lats[1:]-lats[0:-1]
        
        if min(delon) < 0. or min(delat) < 0.:
            raise ValueError('lons and lats must be increasing!')
            
        # Check that lons in -180, 180
        lonsa            = np.array(lons)
        count            = np.sum(lonsa < -180.00001) + np.sum(lonsa > 180.00001)
        
        if count > 1:
            raise ValueError('grid must be shifted so that lons are monotonically increasing and fit in range -180, +180')
        elif count == 1 and math.fabs(lons[-1]-lons[0]-360.) > 1.e-4:
            raise ValueError('grid must be shifted so that lons are monotonically increasing and fit in range -180,+180')
   
        lonsout, latsout = self.makegrid(nx, ny)
        datout           = interp(datin, lons, lats, lonsout, latsout, order=order)
        
        return datout