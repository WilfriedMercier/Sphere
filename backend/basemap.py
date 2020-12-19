#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This code and its docstrings were adapted from the mpl_toolkit.basemap project (https://matplotlib.org/basemap/) which is now deprecated in favor of the Cartopy project (https://scitools.org.uk/cartopy/docs/latest/).
Only the code necessary to perform the aeqd projection was kept and everything else was removed.
For different projections or more options, please refer to the web sites above.

Adapted by : Wilfried Mercier - IRAP
"""

import _geoslib
import numpy    as     np
import numpy.ma as     ma
from   .proj    import Proj

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


def _validated_or_none(param, name, minval, maxval):
    '''
    Validate or not the value of a parameter between given bounds if the parameter is not None.

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
        
    Return parameter value if ok and raise a ValueError otherwise, except if the parameter is None in which case None is returned.
    '''
    
    if param is None:
        return None
    return _validated_ll(param, name, minval, maxval)


class Basemap(object):

    def __init__(self,
                 llcrnrx=None, llcrnry=None, urcrnrx=None, urcrnry=None,
                 width=None, height=None,
                 area_thresh=None,
                 lat_ts=None,
                 lat_0=None, lat_1=None, lat_2=None, 
                 lon_0=None, lon_1=None, lon_2=None, 
                 o_lon_p=None, o_lat_p=None,  k_0=None,
                 no_rot=False,
                 ax=None):

        self.fix_aspect     = True
        self.boundinglat    = None
        self._fulldisk      = False

        # Set up projection parameter dict
        projparams          = {}
        projparams['R']     = 6370997.0
            
        # Set units to meters
        projparams['units'] = 'm'
        
        # Check for bounds
        lat_0               = _validated_or_none(lat_0,  'lat_0',  -90,  90)
        lat_1               = _validated_or_none(lat_1,  'lat_1',  -90,  90)
        lat_2               = _validated_or_none(lat_2,  'lat_2',  -90,  90)
        lat_ts              = _validated_or_none(lat_ts, 'lat_ts', -90,  90)
        lon_0               = _validated_or_none(lon_0,  'lon_0',  -360, 720)
        lon_1               = _validated_or_none(lon_1,  'lon_1',  -360, 720)
        lon_2               = _validated_or_none(lon_2,  'lon_2',  -360, 720)

        # Add to projparams the parameters after having checked them
        _insert_validated(projparams, lat_0,  'lat_0',  -90,  90)
        _insert_validated(projparams, lat_1,  'lat_1',  -90,  90)
        _insert_validated(projparams, lat_2,  'lat_2',  -90,  90)
        _insert_validated(projparams, lat_ts, 'lat_ts', -90,  90)
        _insert_validated(projparams, lon_0,  'lon_0',  -360, 720)
        _insert_validated(projparams, lon_1,  'lon_1',  -360, 720)
        _insert_validated(projparams, lon_2,  'lon_2',  -360, 720)

        # Compute lat/lon of domain corners and set values in projparams dict as needed
        if lat_0 is None or lon_0 is None:
            raise ValueError('must specify lat_0 and lon_0 for Azimuthal Equidistant basemap')
        
        self._fulldisk = True
        llcrnrlon      = -180.
        llcrnrlat      = -90.
        urcrnrlon      = 180
        urcrnrlat      = 90.
            
        self.llcrnrlon = llcrnrlon
        self.llcrnrlat = llcrnrlat
        self.urcrnrlon = urcrnrlon
        self.urcrnrlat = urcrnrlat

        # Initialize proj4
        proj           = Proj(projparams, self.llcrnrlon, self.llcrnrlat, self.urcrnrlon, self.urcrnrlat)
        self.projtran  = proj
        
        # Copy some Proj attributes
        atts = ['rmajor', 'rminor', 'esq', 'flattening', 'ellipsoid', 'projparams', '_width', '_height']
        for att in atts:
            self.__dict__[att] = proj.__dict__[att]
            
        # Set instance variables defining map region.
        self.xmin      = proj.xmin
        self.xmax      = proj.xmax
        self.ymin      = proj.ymin
        self.ymax      = proj.ymax
        self.aspect    = (proj.ymax - proj.ymin)/(proj.xmax - proj.xmin)
        
        self.llcrnrx   = proj.llcrnrx
        self.llcrnry   = proj.llcrnry
        self.urcrnrx   = proj.urcrnrx
        self.urcrnry   = proj.urcrnry

        self.ax        = ax
        self.lsmask    = None
        self._initialized_axes = set()

        self.resolution = 'c'
        self.area_thresh = 10000.
        
        # Define map boundary polygon (in lat/lon coordinates)
        blons, blats, self._boundarypolyll, self._boundarypolyxy = self._getmapboundary()
        self.boundarylats = blats
        self.boundarylons = blons
        
        # Set min/max lats for projection domain.
        lons, lats        = self.makegrid(1001, 1001)
        lats              = ma.masked_where(lats > 1.e20, lats)
        lons              = ma.masked_where(lons > 1.e20, lons)
        self.latmin       = lats.min()
        self.latmax       = lats.max()
        self.lonmin       = lons.min()
        self.lonmax       = lons.max()
        
        NPole             = _geoslib.Point(  self(0., 90.))
        SPole             = _geoslib.Point(  self(0., -90.))
        Dateline          = _geoslib.Point(  self(180., lat_0))
        Greenwich         = _geoslib.Point(  self(0.,   lat_0))
        hasNP             = NPole.within(    self._boundarypolyxy)
        hasSP             = SPole.within(    self._boundarypolyxy)
        hasPole           = hasNP or hasSP
        hasDateline       = Dateline.within( self._boundarypolyxy)
        hasGreenwich      = Greenwich.within(self._boundarypolyxy)
        
        # Projection crosses dateline (and not Greenwich or pole).
        if not hasPole and hasDateline and not hasGreenwich:
            if self.lonmin < 0 and self.lonmax > 0.:
                lons        = np.where(lons < 0, lons+360, lons)
                self.lonmin = lons.min()
                self.lonmax = lons.max()
                
        # Read in coastline polygons, only keeping those that intersect map boundary polygon
        self.coastsegs, self.coastpolygontypes = self._readboundarydata('gshhs', as_polygons=True)
        
        # Reformat for use in matplotlib.patches.Polygon
        self.coastpolygons = []
        for seg in self.coastsegs:
            x, y = list(zip(*seg))
            self.coastpolygons.append((x, y))
            
        # Replace coastsegs with line segments (instead of polygons)
        self.coastsegs, types = self._readboundarydata('gshhs', as_polygons=False)
            
        # Create geos Polygon structures for land areas (currently only used in is_land method)
        self.landpolygons=[]
        self.lakepolygons=[]
        if len(self.coastpolygons) > 0:
            
            x, y = list(zip(*self.coastpolygons))
            for x, y, typ in zip(x ,y, self.coastpolygontypes):
                b = np.asarray([x, y]).T
                if typ == 1: 
                    self.landpolygons.append(_geoslib.Polygon(b))
                    
                if typ == 2: 
                    self.lakepolygons.append(_geoslib.Polygon(b))


    def __call__(self, x, y, inverse=False):
        """
        Calling a Basemap class instance with the arguments lon, lat will convert lon/lat (in degrees) to x/y map projection coordinates (in meters).
        If optional keyword ``inverse`` is True (default is False), the inverse transformation from x/y to lon/lat is performed.

        The inverse transformation always returns longitudes between -180 and 180 degrees.
        Input arguments lon, lat can be either scalar floats, sequences, or numpy arrays.
        """
        
        return self.projtran(x,y,inverse=inverse)

    def makegrid(self,nx,ny,returnxy=False):
        """
        return arrays of shape (ny,nx) containing lon,lat coordinates of
        an equally spaced native projection grid.

        If ``returnxy = True``, the x,y values of the grid are returned also.
        """
        return self.projtran.makegrid(nx,ny,returnxy=returnxy)

    def _readboundarydata(self,name,as_polygons=False):
        """
        read boundary data, clip to map projection region.
        """
        msg = dedent("""
        Unable to open boundary dataset file. Only the 'crude' and  'low',
        resolution datasets are installed by default.
        If you are requesting an, 'intermediate', 'high' or 'full'
        resolution dataset, you may need to download and install those
        files separately with
        `conda install basemap-data-hires`.""")
        # only gshhs coastlines can be polygons.
        if name != 'gshhs': as_polygons=False
        try:
            bdatfile = open(os.path.join(basemap_datadir,name+'_'+self.resolution+'.dat'),'rb')
            bdatmetafile = open(os.path.join(basemap_datadir,name+'meta_'+self.resolution+'.dat'),'r')
        except:
            raise IOError(msg)
        polygons = []
        polygon_types = []
        # coastlines are polygons, other boundaries are line segments.
        if name == 'gshhs':
            Shape = _geoslib.Polygon
        else:
            Shape = _geoslib.LineString
        # see if map projection region polygon contains a pole.
        NPole = _geoslib.Point(self(0.,90.))
        SPole = _geoslib.Point(self(0.,-90.))
        boundarypolyxy = self._boundarypolyxy
        boundarypolyll = self._boundarypolyll
        hasNP = NPole.within(boundarypolyxy)
        hasSP = SPole.within(boundarypolyxy)
        containsPole = hasNP or hasSP
        # these projections cannot cross pole.
        if containsPole and\
            self.projection in _cylproj + _pseudocyl + ['geos']:
            raise ValueError('%s projection cannot cross pole'%(self.projection))
        # make sure some projections have has containsPole=True
        # we will compute the intersections in stereographic
        # coordinates, then transform back. This is
        # because these projections are only defined on a hemisphere, and
        # some boundary features (like Eurasia) would be undefined otherwise.
        tostere =\
        ['omerc','ortho','gnom','nsper','nplaea','npaeqd','splaea','spaeqd']
        if self.projection in tostere and name == 'gshhs':
            containsPole = True
            lon_0=self.projparams['lon_0']
            lat_0=self.projparams['lat_0']
            re = self.projparams['R']
            # center of stereographic projection restricted to be
            # nearest one of 6 points on the sphere (every 90 deg lat/lon).
            lon0 = 90.*(np.around(lon_0/90.))
            lat0 = 90.*(np.around(lat_0/90.))
            if np.abs(int(lat0)) == 90: lon0=0.
            maptran = pyproj.Proj(proj='stere',lon_0=lon0,lat_0=lat0,R=re)
            # boundary polygon for ortho/gnom/nsper projection
            # in stereographic coordinates.
            b = self._boundarypolyll.boundary
            blons = b[:,0]; blats = b[:,1]
            b[:,0], b[:,1] = maptran(blons, blats)
            boundarypolyxy = _geoslib.Polygon(b)
        for line in bdatmetafile:
            linesplit = line.split()
            area = float(linesplit[1])
            south = float(linesplit[3])
            north = float(linesplit[4])
            crossdatelineE=False; crossdatelineW=False
            if name == 'gshhs':
                id = linesplit[7]
                if id.endswith('E'):
                    crossdatelineE = True
                elif id.endswith('W'):
                    crossdatelineW = True
            # make sure south/north limits of dateline crossing polygons
            # (Eurasia) are the same, since they will be merged into one.
            # (this avoids having one filtered out and not the other).
            if crossdatelineE:
                south_save=south
                north_save=north
            if crossdatelineW:
                south=south_save
                north=north_save
            if area < 0.: area = 1.e30
            useit = self.latmax>=south and self.latmin<=north and area>self.area_thresh
            if useit:
                typ = int(linesplit[0])
                npts = int(linesplit[2])
                offsetbytes = int(linesplit[5])
                bytecount = int(linesplit[6])
                bdatfile.seek(offsetbytes,0)
                # read in binary string convert into an npts by 2
                # numpy array (first column is lons, second is lats).
                polystring = bdatfile.read(bytecount)
                # binary data is little endian.
                b = np.array(np.frombuffer(polystring,dtype='<f4'),'f8')
                b.shape = (npts,2)
                b2 = b.copy()
                # merge polygons that cross dateline.
                poly = Shape(b)
                # hack to try to avoid having Antartica filled polygon
                # covering entire map (if skipAnart = False, this happens
                # for ortho lon_0=-120, lat_0=60, for example).
                skipAntart = self.projection in tostere and south < -89 and \
                 not hasSP
                if crossdatelineE and not skipAntart:
                    if not poly.is_valid(): poly=poly.fix()
                    polyE = poly
                    continue
                elif crossdatelineW and not skipAntart:
                    if not poly.is_valid(): poly=poly.fix()
                    b = poly.boundary
                    b[:,0] = b[:,0]+360.
                    poly = Shape(b)
                    poly = poly.union(polyE)
                    if not poly.is_valid(): poly=poly.fix()
                    b = poly.boundary
                    b2 = b.copy()
                    # fix Antartica.
                    if name == 'gshhs' and south < -89:
                        b = b[4:,:]
                        b2 = b.copy()
                        poly = Shape(b)
                # if map boundary polygon is a valid one in lat/lon
                # coordinates (i.e. it does not contain either pole),
                # the intersections of the boundary geometries
                # and the map projection region can be computed before
                # transforming the boundary geometry to map projection
                # coordinates (this saves time, especially for small map
                # regions and high-resolution boundary geometries).
                if not containsPole:
                    # close Antarctica.
                    if name == 'gshhs' and south < -89:
                        lons2 = b[:,0]
                        lats = b[:,1]
                        lons1 = lons2 - 360.
                        lons3 = lons2 + 360.
                        lons = lons1.tolist()+lons2.tolist()+lons3.tolist()
                        lats = lats.tolist()+lats.tolist()+lats.tolist()
                        lonstart,latstart = lons[0], lats[0]
                        lonend,latend = lons[-1], lats[-1]
                        lons.insert(0,lonstart)
                        lats.insert(0,-90.)
                        lons.append(lonend)
                        lats.append(-90.)
                        b = np.empty((len(lons),2),np.float64)
                        b[:,0] = lons; b[:,1] = lats
                        poly = Shape(b)
                        if not poly.is_valid(): poly=poly.fix()
                        # if polygon instersects map projection
                        # region, process it.
                        if poly.intersects(boundarypolyll):
                            if name != 'gshhs' or as_polygons:
                                geoms = poly.intersection(boundarypolyll)
                            else:
                                # convert polygons to line segments
                                poly = _geoslib.LineString(poly.boundary)
                                geoms = poly.intersection(boundarypolyll)
                            # iterate over geometries in intersection.
                            for psub in geoms:
                                b = psub.boundary
                                blons = b[:,0]; blats = b[:,1]
                                bx, by = self(blons, blats)
                                polygons.append(list(zip(bx,by)))
                                polygon_types.append(typ)
                    else:
                        # create duplicate polygons shifted by -360 and +360
                        # (so as to properly treat polygons that cross
                        # Greenwich meridian).
                        b2[:,0] = b[:,0]-360
                        poly1 = Shape(b2)
                        b2[:,0] = b[:,0]+360
                        poly2 = Shape(b2)
                        polys = [poly1,poly,poly2]
                        for poly in polys:
                            # try to fix "non-noded intersection" errors.
                            if not poly.is_valid(): poly=poly.fix()
                            # if polygon instersects map projection
                            # region, process it.
                            if poly.intersects(boundarypolyll):
                                if name != 'gshhs' or as_polygons:
                                    geoms = poly.intersection(boundarypolyll)
                                else:
                                    # convert polygons to line segments
                                    # note: use fix method here or Eurasia
                                    # line segments sometimes disappear.
                                    poly = _geoslib.LineString(poly.fix().boundary)
                                    geoms = poly.intersection(boundarypolyll)
                                # iterate over geometries in intersection.
                                for psub in geoms:
                                    b = psub.boundary
                                    blons = b[:,0]; blats = b[:,1]
                                    # transformation from lat/lon to
                                    # map projection coordinates.
                                    bx, by = self(blons, blats)
                                    if not as_polygons or len(bx) > 4:
                                        polygons.append(list(zip(bx,by)))
                                        polygon_types.append(typ)
                # if map boundary polygon is not valid in lat/lon
                # coordinates, compute intersection between map
                # projection region and boundary geometries in map
                # projection coordinates.
                else:
                    # transform coordinates from lat/lon
                    # to map projection coordinates.
                    # special case for ortho/gnom/nsper, compute coastline polygon
                    # vertices in stereographic coords.
                    if name == 'gshhs' and as_polygons and self.projection in tostere:
                        b[:,0], b[:,1] = maptran(b[:,0], b[:,1])
                    else:
                        b[:,0], b[:,1] = self(b[:,0], b[:,1])
                    goodmask = np.logical_and(b[:,0]<1.e20,b[:,1]<1.e20)
                    # if less than two points are valid in
                    # map proj coords, skip this geometry.
                    if np.sum(goodmask) <= 1: continue
                    if name != 'gshhs' or (name == 'gshhs' and not as_polygons):
                        # if not a polygon,
                        # just remove parts of geometry that are undefined
                        # in this map projection.
                        bx = np.compress(goodmask, b[:,0])
                        by = np.compress(goodmask, b[:,1])
                        # split coastline segments that jump across entire plot.
                        xd = (bx[1:]-bx[0:-1])**2
                        yd = (by[1:]-by[0:-1])**2
                        dist = np.sqrt(xd+yd)
                        split = dist > 0.1*(self.xmax-self.xmin)
                        if np.sum(split) and self.projection not in _cylproj:
                            ind = (np.compress(split,np.squeeze(split*np.indices(xd.shape)))+1).tolist()
                            iprev = 0
                            ind.append(len(xd))
                            for i in ind:
                                # don't add empty lists.
                                if len(list(range(iprev,i))):
                                    polygons.append(list(zip(bx[iprev:i],by[iprev:i])))
                                iprev = i
                        else:
                            polygons.append(list(zip(bx,by)))
                        polygon_types.append(typ)
                        continue
                    # create a GEOS geometry object.
                    if name == 'gshhs' and not as_polygons:
                        # convert polygons to line segments
                        poly = _geoslib.LineString(poly.boundary)
                    else:
                        poly = Shape(b)
                    # this is a workaround to avoid
                    # "GEOS_ERROR: TopologyException:
                    # found non-noded intersection between ..."
                    if not poly.is_valid(): poly=poly.fix()
                    # if geometry instersects map projection
                    # region, and doesn't have any invalid points, process it.
                    if goodmask.all() and poly.intersects(boundarypolyxy):
                        # if geometry intersection calculation fails,
                        # just move on.
                        try:
                            geoms = poly.intersection(boundarypolyxy)
                        except:
                            continue
                        # iterate over geometries in intersection.
                        for psub in geoms:
                            b = psub.boundary
                            # if projection in ['ortho','gnom','nsper'],
                            # transform polygon from stereographic
                            # to ortho/gnom/nsper coordinates.
                            if self.projection in tostere:
                                # if coastline polygon covers more than 99%
                                # of map region for fulldisk projection,
                                # it's probably bogus, so skip it.
                                #areafrac = psub.area()/boundarypolyxy.area()
                                #if self.projection == ['ortho','nsper']:
                                #    if name == 'gshhs' and\
                                #       self._fulldisk and\
                                #       areafrac > 0.99: continue
                                # inverse transform from stereographic
                                # to lat/lon.
                                b[:,0], b[:,1] = maptran(b[:,0], b[:,1], inverse=True)
                                # orthographic/gnomonic/nsper.
                                b[:,0], b[:,1]= self(b[:,0], b[:,1])
                            if not as_polygons or len(b) > 4:
                                polygons.append(list(zip(b[:,0],b[:,1])))
                                polygon_types.append(typ)
        bdatfile.close()
        bdatmetafile.close()
        return polygons, polygon_types

    def _getmapboundary(self):
        """
        create map boundary polygon (in lat/lon and x/y coordinates)
        """
        nx = 100; ny = 100
        maptran = self
        if self.projection in ['ortho','geos','nsper']:
            # circular region.
            thetas = np.linspace(0.,2.*np.pi,2*nx*ny)[:-1]
            rminor = self._height
            rmajor = self._width
            x = rmajor*np.cos(thetas) + rmajor
            y = rminor*np.sin(thetas) + rminor
            b = np.empty((len(x),2),np.float64)
            b[:,0]=x; b[:,1]=y
            boundaryxy = _geoslib.Polygon(b)
            # compute proj instance for full disk, if necessary.
            if not self._fulldisk:
                projparms = self.projparams.copy()
                del projparms['x_0']
                del projparms['y_0']
                if self.projection == 'ortho':
                    llcrnrx = -self.rmajor
                    llcrnry = -self.rmajor
                    urcrnrx = -llcrnrx
                    urcrnry = -llcrnry
                else:
                    llcrnrx = -self._width
                    llcrnry = -self._height
                    urcrnrx = -llcrnrx
                    urcrnry = -llcrnry
                projparms['x_0']=-llcrnrx
                projparms['y_0']=-llcrnry
                maptran = pyproj.Proj(projparms)
        elif self.projection == 'aeqd' and self._fulldisk:
            # circular region.
            thetas = np.linspace(0.,2.*np.pi,2*nx*ny)[:-1]
            rminor = self._height
            rmajor = self._width
            x = rmajor*np.cos(thetas) + rmajor
            y = rminor*np.sin(thetas) + rminor
            b = np.empty((len(x),2),np.float64)
            b[:,0]=x; b[:,1]=y
            boundaryxy = _geoslib.Polygon(b)
        elif self.projection in _pseudocyl:
            nx = 10*nx; ny = 10*ny
            # quasi-elliptical region.
            lon_0 = self.projparams['lon_0']
            # left side
            lats1 = np.linspace(-89.9999,89.9999,ny).tolist()
            lons1 = len(lats1)*[lon_0-179.9]
            # top.
            lons2 = np.linspace(lon_0-179.9,lon_0+179.9,nx).tolist()
            lats2 = len(lons2)*[89.9999]
            # right side
            lats3 = np.linspace(89.9999,-89.9999,ny).tolist()
            lons3 = len(lats3)*[lon_0+179.9]
            # bottom.
            lons4 = np.linspace(lon_0+179.9,lon_0-179.9,nx).tolist()
            lats4 = len(lons4)*[-89.9999]
            lons = np.array(lons1+lons2+lons3+lons4,np.float64)
            lats = np.array(lats1+lats2+lats3+lats4,np.float64)
            x, y = maptran(lons,lats)
            b = np.empty((len(x),2),np.float64)
            b[:,0]=x; b[:,1]=y
            boundaryxy = _geoslib.Polygon(b)
        else: # all other projections are rectangular.
            nx = 100*nx; ny = 100*ny
            # left side (x = xmin, ymin <= y <= ymax)
            yy = np.linspace(self.ymin, self.ymax, ny)[:-1]
            x = len(yy)*[self.xmin]; y = yy.tolist()
            # top (y = ymax, xmin <= x <= xmax)
            xx = np.linspace(self.xmin, self.xmax, nx)[:-1]
            x = x + xx.tolist()
            y = y + len(xx)*[self.ymax]
            # right side (x = xmax, ymin <= y <= ymax)
            yy = np.linspace(self.ymax, self.ymin, ny)[:-1]
            x = x + len(yy)*[self.xmax]; y = y + yy.tolist()
            # bottom (y = ymin, xmin <= x <= xmax)
            xx = np.linspace(self.xmax, self.xmin, nx)[:-1]
            x = x + xx.tolist()
            y = y + len(xx)*[self.ymin]
            x = np.array(x,np.float64)
            y = np.array(y,np.float64)
            b = np.empty((4,2),np.float64)
            b[:,0]=[self.xmin,self.xmin,self.xmax,self.xmax]
            b[:,1]=[self.ymin,self.ymax,self.ymax,self.ymin]
            boundaryxy = _geoslib.Polygon(b)
        if self.projection in _cylproj:
            # make sure map boundary doesn't quite include pole.
            if self.urcrnrlat > 89.9999:
                urcrnrlat = 89.9999
            else:
                urcrnrlat = self.urcrnrlat
            if self.llcrnrlat < -89.9999:
                llcrnrlat = -89.9999
            else:
                llcrnrlat = self.llcrnrlat
            lons = [self.llcrnrlon, self.llcrnrlon, self.urcrnrlon, self.urcrnrlon]
            lats = [llcrnrlat, urcrnrlat, urcrnrlat, llcrnrlat]
            self.boundarylonmin = min(lons)
            self.boundarylonmax = max(lons)
            x, y = self(lons, lats)
            b = np.empty((len(x),2),np.float64)
            b[:,0]=x; b[:,1]=y
            boundaryxy = _geoslib.Polygon(b)
        else:
            if self.projection not in _pseudocyl:
                lons, lats = maptran(x,y,inverse=True)
                # fix lons so there are no jumps.
                n = 1
                lonprev = lons[0]
                for lon,lat in zip(lons[1:],lats[1:]):
                    if np.abs(lon-lonprev) > 90.:
                        if lonprev < 0:
                            lon = lon - 360.
                        else:
                            lon = lon + 360
                        lons[n] = lon
                    lonprev = lon
                    n = n + 1
                self.boundarylonmin = lons.min()
                self.boundarylonmax = lons.max()
                # for circular full disk projections where boundary is
                # a latitude circle, set boundarylonmax and boundarylonmin
                # to cover entire world (so parallels will be drawn).
                if self._fulldisk and \
                   np.abs(self.boundarylonmax-self.boundarylonmin) < 1.:
                   self.boundarylonmin = -180.
                   self.boundarylonmax = 180.
        b = np.empty((len(lons),2),np.float64)
        b[:,0] = lons; b[:,1] = lats
        boundaryll = _geoslib.Polygon(b)
        return lons, lats, boundaryll, boundaryxy

    def gcpoints(self,lon1,lat1,lon2,lat2,npoints):
        """
        compute ``points`` points along a great circle with endpoints
        ``(lon1,lat1)`` and ``(lon2,lat2)``.

        Returns arrays x,y with map projection coordinates.
        """
        gc = pyproj.Geod(a=self.rmajor,b=self.rminor)
        lonlats = gc.npts(lon1,lat1,lon2,lat2,npoints-2)
        lons=[lon1];lats=[lat1]
        for lon,lat in lonlats:
            lons.append(lon); lats.append(lat)
        lons.append(lon2); lats.append(lat2)
        x, y = self(lons, lats)
        return x,y

    def transform_scalar(self,datin,lons,lats,nx,ny,returnxy=False,checkbounds=False,order=1,masked=False):
        """
        Interpolate a scalar field (``datin``) from a lat/lon grid with
        longitudes = ``lons`` and latitudes = ``lats`` to a ``ny`` by ``nx``
        map projection grid.  Typically used to transform data to
        map projection coordinates for plotting on a map with
        the :meth:`imshow`.

        .. tabularcolumns:: |l|L|

        ==============   ====================================================
        Argument         Description
        ==============   ====================================================
        datin            input data on a lat/lon grid.
        lons, lats       rank-1 arrays containing longitudes and latitudes
                         (in degrees) of input data in increasing order.
                         For non-cylindrical projections (those other than
                         ``cyl``, ``merc``, ``cea``, ``gall`` and ``mill``) lons
                         must fit within range -180 to 180.
        nx, ny           The size of the output regular grid in map
                         projection coordinates
        ==============   ====================================================

        .. tabularcolumns:: |l|L|

        ==============   ====================================================
        Keyword          Description
        ==============   ====================================================
        returnxy         If True, the x and y values of the map
                         projection grid are also returned (Default False).
        checkbounds      If True, values of lons and lats are checked to see
                         that they lie within the map projection region.
                         Default is False, and data outside map projection
                         region is clipped to values on boundary.
        masked           If True, interpolated data is returned as a masked
                         array with values outside map projection region
                         masked (Default False).
        order            0 for nearest-neighbor interpolation, 1 for
                         bilinear, 3 for cubic spline (Default 1).
                         Cubic spline interpolation requires scipy.ndimage.
        ==============   ====================================================

        Returns ``datout`` (data on map projection grid).
        If returnxy=True, returns ``data,x,y``.
        """
        # check that lons, lats increasing
        delon = lons[1:]-lons[0:-1]
        delat = lats[1:]-lats[0:-1]
        if min(delon) < 0. or min(delat) < 0.:
            raise ValueError('lons and lats must be increasing!')
        # check that lons in -180,180 for non-cylindrical projections.
        if self.projection not in _cylproj:
            lonsa = np.array(lons)
            count = np.sum(lonsa < -180.00001) + np.sum(lonsa > 180.00001)
            if count > 1:
                raise ValueError('grid must be shifted so that lons are monotonically increasing and fit in range -180,+180 (see shiftgrid function)')
            # allow for wraparound point to be outside.
            elif count == 1 and math.fabs(lons[-1]-lons[0]-360.) > 1.e-4:
                raise ValueError('grid must be shifted so that lons are monotonically increasing and fit in range -180,+180 (see shiftgrid function)')
        if returnxy:
            lonsout, latsout, x, y = self.makegrid(nx,ny,returnxy=True)
        else:
            lonsout, latsout = self.makegrid(nx,ny)
        datout = interp(datin,lons,lats,lonsout,latsout,checkbounds=checkbounds,order=order,masked=masked)
        if returnxy:
            return datout, x, y
        else:
            return datout

    def transform_vector(self,uin,vin,lons,lats,nx,ny,returnxy=False,checkbounds=False,order=1,masked=False):
        """
        Rotate and interpolate a vector field (``uin,vin``) from a
        lat/lon grid with longitudes = ``lons`` and latitudes = ``lats``
        to a ``ny`` by ``nx`` map projection grid.

        The input vector field is defined in spherical coordinates (it
        has eastward and northward components) while the output
        vector field is rotated to map projection coordinates (relative
        to x and y). The magnitude of the vector is preserved.

        .. tabularcolumns:: |l|L|

        ==============   ====================================================
        Arguments        Description
        ==============   ====================================================
        uin, vin         input vector field on a lat/lon grid.
        lons, lats       rank-1 arrays containing longitudes and latitudes
                         (in degrees) of input data in increasing order.
                         For non-cylindrical projections (those other than
                         ``cyl``, ``merc``, ``cea``, ``gall`` and ``mill``) lons
                         must fit within range -180 to 180.
        nx, ny           The size of the output regular grid in map
                         projection coordinates
        ==============   ====================================================

        .. tabularcolumns:: |l|L|

        ==============   ====================================================
        Keyword          Description
        ==============   ====================================================
        returnxy         If True, the x and y values of the map
                         projection grid are also returned (Default False).
        checkbounds      If True, values of lons and lats are checked to see
                         that they lie within the map projection region.
                         Default is False, and data outside map projection
                         region is clipped to values on boundary.
        masked           If True, interpolated data is returned as a masked
                         array with values outside map projection region
                         masked (Default False).
        order            0 for nearest-neighbor interpolation, 1 for
                         bilinear, 3 for cubic spline (Default 1).
                         Cubic spline interpolation requires scipy.ndimage.
        ==============   ====================================================

        Returns ``uout, vout`` (vector field on map projection grid).
        If returnxy=True, returns ``uout,vout,x,y``.
        """
        # check that lons, lats increasing
        delon = lons[1:]-lons[0:-1]
        delat = lats[1:]-lats[0:-1]
        if min(delon) < 0. or min(delat) < 0.:
            raise ValueError('lons and lats must be increasing!')
        # check that lons in -180,180 for non-cylindrical projections.
        if self.projection not in _cylproj:
            lonsa = np.array(lons)
            count = np.sum(lonsa < -180.00001) + np.sum(lonsa > 180.00001)
            if count > 1:
                raise ValueError('grid must be shifted so that lons are monotonically increasing and fit in range -180,+180 (see shiftgrid function)')
            # allow for wraparound point to be outside.
            elif count == 1 and math.fabs(lons[-1]-lons[0]-360.) > 1.e-4:
                raise ValueError('grid must be shifted so that lons are monotonically increasing and fit in range -180,+180 (see shiftgrid function)')
        lonsout, latsout, x, y = self.makegrid(nx,ny,returnxy=True)
        # interpolate to map projection coordinates.
        uin = interp(uin,lons,lats,lonsout,latsout,checkbounds=checkbounds,order=order,masked=masked)
        vin = interp(vin,lons,lats,lonsout,latsout,checkbounds=checkbounds,order=order,masked=masked)
        # rotate from geographic to map coordinates.
        return self.rotate_vector(uin,vin,lonsout,latsout,returnxy=returnxy)

    def rotate_vector(self,uin,vin,lons,lats,returnxy=False):
        """
        Rotate a vector field (``uin,vin``) on a rectilinear grid
        with longitudes = ``lons`` and latitudes = ``lats`` from
        geographical (lat/lon) into map projection (x/y) coordinates.

        Differs from transform_vector in that no interpolation is done.
        The vector is returned on the same grid, but rotated into
        x,y coordinates.

        The input vector field is defined in spherical coordinates (it
        has eastward and northward components) while the output
        vector field is rotated to map projection coordinates (relative
        to x and y). The magnitude of the vector is preserved.

        .. tabularcolumns:: |l|L|

        ==============   ====================================================
        Arguments        Description
        ==============   ====================================================
        uin, vin         input vector field on a lat/lon grid.
        lons, lats       Arrays containing longitudes and latitudes
                         (in degrees) of input data in increasing order.
                         For non-cylindrical projections (those other than
                         ``cyl``, ``merc``, ``cyl``, ``gall`` and ``mill``) lons
                         must fit within range -180 to 180.
        ==============   ====================================================

        Returns ``uout, vout`` (rotated vector field).
        If the optional keyword argument
        ``returnxy`` is True (default is False),
        returns ``uout,vout,x,y`` (where ``x,y`` are the map projection
        coordinates of the grid defined by ``lons,lats``).
        """
        # if lons,lats are 1d and uin,vin are 2d, and
        # lats describes 1st dim of uin,vin, and
        # lons describes 2nd dim of uin,vin, make lons,lats 2d
        # with meshgrid.
        if lons.ndim == lats.ndim == 1 and uin.ndim == vin.ndim == 2 and\
           uin.shape[1] == vin.shape[1] == lons.shape[0] and\
           uin.shape[0] == vin.shape[0] == lats.shape[0]:
            lons, lats = np.meshgrid(lons, lats)
        else:
            if not lons.shape == lats.shape == uin.shape == vin.shape:
                raise TypeError("shapes of lons,lats and uin,vin don't match")
        x, y = self(lons, lats)
        # rotate from geographic to map coordinates.
        if ma.isMaskedArray(uin):
            mask = ma.getmaskarray(uin)
            masked = True
            uin = uin.filled(1)
            vin = vin.filled(1)
        else:
            masked = False

        # Map the (lon, lat) vector in the complex plane.
        uvc = uin + 1j*vin
        uvmag = np.abs(uvc)
        theta = np.angle(uvc)

        # Define a displacement (dlon, dlat) that moves all
        # positions (lons, lats) a small distance in the
        # direction of the original vector.
        dc = 1E-5 * np.exp(theta*1j)
        dlat = dc.imag * np.cos(np.radians(lats))
        dlon = dc.real

        # Deal with displacements that overshoot the North or South Pole.
        farnorth = np.abs(lats+dlat) >= 90.0
        somenorth = farnorth.any()
        if somenorth:
            dlon[farnorth] *= -1.0
            dlat[farnorth] *= -1.0

        # Add displacement to original location and find the native coordinates.
        lon1 = lons + dlon
        lat1 = lats + dlat
        xn, yn = self(lon1, lat1)

        # Determine the angle of the displacement in the native coordinates.
        vecangle = np.arctan2(yn-y, xn-x)
        if somenorth:
            vecangle[farnorth] += np.pi

        # Compute the x-y components of the original vector.
        uvcout = uvmag * np.exp(1j*vecangle)
        uout = uvcout.real
        vout = uvcout.imag

        if masked:
            uout = ma.array(uout, mask=mask)
            vout = ma.array(vout, mask=mask)
        if returnxy:
            return uout,vout,x,y
        else:
            return uout,vout

    def _save_use_hold(self, ax, kwargs):
        h = kwargs.pop('hold', None)
        if hasattr(ax, '_hold'):
            self._tmp_hold = ax._hold
            if h is not None:
                ax._hold = h

    def _restore_hold(self, ax):
        if hasattr(ax, '_hold'):
            ax._hold = self._tmp_hold


    def shiftdata(self,lonsin,datain=None,lon_0=None,fix_wrap_around=True):
        """
        Shift longitudes (and optionally data) so that they match map projection region.
        Only valid for cylindrical/pseudo-cylindrical global projections and data
        on regular lat/lon grids. longitudes and data can be 1-d or 2-d, if 2-d
        it is assumed longitudes are 2nd (rightmost) dimension.

        .. tabularcolumns:: |l|L|

        ==============   ====================================================
        Arguments        Description
        ==============   ====================================================
        lonsin           original 1-d or 2-d longitudes.
        ==============   ====================================================

        .. tabularcolumns:: |l|L|

        ==============   ====================================================
        Keywords         Description
        ==============   ====================================================
        datain           original 1-d or 2-d data. Default None.
        lon_0            center of map projection region. Defaut None,
                         given by current map projection.
        fix_wrap_around  if True reindex (if required) longitudes (and data) to
                         avoid jumps caused by remapping of longitudes of
                         points from outside of the [lon_0-180, lon_0+180]
                         interval back into the interval.
                         If False do not reindex longitudes and data, but do
                         make sure that longitudes are in the
                         [lon_0-180, lon_0+180] range.
        ==============   ====================================================

        if datain given, returns ``dataout,lonsout`` (data and longitudes shifted to fit in interval
        [lon_0-180,lon_0+180]), otherwise just returns longitudes.  If
        transformed longitudes lie outside map projection region, data is
        masked and longitudes are set to 1.e30.
        """
        if lon_0 is None and 'lon_0' not in self.projparams:
            msg='lon_0 keyword must be provided'
            raise ValueError(msg)
        lonsin = np.asarray(lonsin)
        if lonsin.ndim not in [1,2]:
            raise ValueError('1-d or 2-d longitudes required')
        if datain is not None:
            # if it's a masked array, leave it alone.
            if not ma.isMA(datain): datain = np.asarray(datain)
            if datain.ndim not in [1,2]:
                raise ValueError('1-d or 2-d data required')
        if lon_0 is None:
            lon_0 = self.projparams['lon_0']
        # 2-d data.
        if lonsin.ndim == 2:
            nlats = lonsin.shape[0]
            nlons = lonsin.shape[1]
            lonsin1 = lonsin[0,:]
            lonsin1 = np.where(lonsin1 > lon_0+180, lonsin1-360 ,lonsin1)
            lonsin1 = np.where(lonsin1 < lon_0-180, lonsin1+360 ,lonsin1)
            if nlons > 1:
                londiff = np.abs(lonsin1[0:-1]-lonsin1[1:])
                londiff_sort = np.sort(londiff)
                thresh = 360.-londiff_sort[-2] if nlons > 2 else 360.-londiff_sort[-1]
                itemindex = nlons-np.where(londiff>=thresh)[0]
            else:
                lonsin[0, :] = lonsin1
                itemindex = 0

            # if no shift necessary, itemindex will be
            # empty, so don't do anything
            if fix_wrap_around and itemindex:
                # check to see if cyclic (wraparound) point included
                # if so, remove it.
                if np.abs(lonsin1[0]-lonsin1[-1]) < 1.e-4:
                    hascyclic = True
                    lonsin_save = lonsin.copy()
                    lonsin = lonsin[:,1:]
                    if datain is not None:
                       datain_save = datain.copy()
                       datain = datain[:,1:]
                else:
                    hascyclic = False
                lonsin = np.where(lonsin > lon_0+180, lonsin-360 ,lonsin)
                lonsin = np.where(lonsin < lon_0-180, lonsin+360 ,lonsin)
                lonsin = np.roll(lonsin,itemindex-1,axis=1)
                if datain is not None:
                    # np.roll works on ndarrays and on masked arrays
                    datain = np.roll(datain,itemindex-1,axis=1)
                # add cyclic point back at beginning.
                if hascyclic:
                    lonsin_save[:,1:] = lonsin
                    lonsin_save[:,0] = lonsin[:,-1]-360.
                    lonsin = lonsin_save
                    if datain is not None:
                        datain_save[:,1:] = datain
                        datain_save[:,0] = datain[:,-1]
                        datain = datain_save

        # 1-d data.
        elif lonsin.ndim == 1:
            nlons = len(lonsin)
            lonsin = np.where(lonsin > lon_0+180, lonsin-360 ,lonsin)
            lonsin = np.where(lonsin < lon_0-180, lonsin+360 ,lonsin)

            if nlons > 1:
                londiff = np.abs(lonsin[0:-1]-lonsin[1:])
                londiff_sort = np.sort(londiff)
                thresh = 360.-londiff_sort[-2] if nlons > 2 else 360.0 - londiff_sort[-1]
                itemindex = len(lonsin)-np.where(londiff>=thresh)[0]
            else:
                itemindex = 0

            if fix_wrap_around and itemindex:
                # check to see if cyclic (wraparound) point included
                # if so, remove it.
                if np.abs(lonsin[0]-lonsin[-1]) < 1.e-4:
                    hascyclic = True
                    lonsin_save = lonsin.copy()
                    lonsin = lonsin[1:]
                    if datain is not None:
                        datain_save = datain.copy()
                        datain = datain[1:]
                else:
                    hascyclic = False
                lonsin = np.roll(lonsin,itemindex-1)
                if datain is not None:
                    datain = np.roll(datain,itemindex-1)
                # add cyclic point back at beginning.
                if hascyclic:
                    lonsin_save[1:] = lonsin
                    lonsin_save[0] = lonsin[-1]-360.
                    lonsin = lonsin_save
                    if datain is not None:
                        datain_save[1:] = datain
                        datain_save[0] = datain[-1]
                        datain = datain_save

        # mask points outside
        # map region so they don't wrap back in the domain.
        mask = np.logical_or(lonsin<lon_0-180,lonsin>lon_0+180)
        lonsin = np.where(mask,1.e30,lonsin)
        if datain is not None and mask.any():
            datain = ma.masked_where(mask, datain)

        if datain is not None:
            return lonsin, datain
        else:
            return lonsin