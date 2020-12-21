from __future__ import (absolute_import, division, print_function)

"""
Module for plotting data on maps with matplotlib.

Contains the :class:`Basemap` class (which does most of the
heavy lifting), and the following functions:

:func:`interp`:  bilinear interpolation between rectilinear grids.

:func:`maskoceans`:  mask 'wet' points of an input array.

:func:`shiftgrid`:  shifts global lat/lon grids east or west.

:func:`addcyclic`: Add cyclic (wraparound) point in longitude.
"""
from distutils.version import LooseVersion

from matplotlib import __version__ as _matplotlib_version

# check to make sure matplotlib is not too old.
_matplotlib_version = LooseVersion(_matplotlib_version)
_mpl_required_version = LooseVersion('0.98')
if _matplotlib_version < _mpl_required_version:
    msg = 'your matplotlib is too old - basemap requires version %s or higher, you have version %s' %(_mpl_required_version,_matplotlib_version)
    raise ImportError(msg)
    
import pyproj
import sys, os, math
from .proj import Proj
import numpy as np
import numpy.ma as ma
import functools

# basemap data files now installed in lib/matplotlib/toolkits/basemap/data
# check to see if environment variable BASEMAPDATA set to a directory,
# and if so look for the data there.
if 'BASEMAPDATA' in os.environ:
    basemap_datadir = os.environ['BASEMAPDATA']
    if not os.path.isdir(basemap_datadir):
        raise RuntimeError('Path in environment BASEMAPDATA not a directory')
else:
  if os.name == 'nt':
    basemap_datadir = os.path.join(sys.prefix, 'Library', 'share', 'basemap')
  else:
    basemap_datadir = os.path.join(sys.prefix, 'share', 'basemap')

__version__ = '1.1.0'

# module variable that sets the default value for the 'latlon' kwarg.
# can be set to True by user so plotting functions can take lons,lats
# in degrees by default, instead of x,y (map projection coords in meters).
latlon_default = False

# supported map projections.
_projnames = {'cyl'      : 'Cylindrical Equidistant',
             'merc'     : 'Mercator',
             'tmerc'    : 'Transverse Mercator',
             'omerc'    : 'Oblique Mercator',
             'mill'     : 'Miller Cylindrical',
             'gall'     : 'Gall Stereographic Cylindrical',
             'cea'      : 'Cylindrical Equal Area',
             'lcc'      : 'Lambert Conformal',
             'laea'     : 'Lambert Azimuthal Equal Area',
             'nplaea'   : 'North-Polar Lambert Azimuthal',
             'splaea'   : 'South-Polar Lambert Azimuthal',
             'eqdc'     : 'Equidistant Conic',
             'aeqd'     : 'Azimuthal Equidistant',
             'npaeqd'   : 'North-Polar Azimuthal Equidistant',
             'spaeqd'   : 'South-Polar Azimuthal Equidistant',
             'aea'      : 'Albers Equal Area',
             'stere'    : 'Stereographic',
             'npstere'  : 'North-Polar Stereographic',
             'spstere'  : 'South-Polar Stereographic',
             'cass'     : 'Cassini-Soldner',
             'poly'     : 'Polyconic',
             'ortho'    : 'Orthographic',
             'geos'     : 'Geostationary',
             'nsper'    : 'Near-Sided Perspective',
             'sinu'     : 'Sinusoidal',
             'moll'     : 'Mollweide',
             'hammer'   : 'Hammer',
             'robin'    : 'Robinson',
             'kav7'     : 'Kavrayskiy VII',
             'eck4'     : 'Eckert IV',
             'vandg'    : 'van der Grinten',
             'mbtfpq'   : 'McBryde-Thomas Flat-Polar Quartic',
             'gnom'     : 'Gnomonic',
             'rotpole'  : 'Rotated Pole',
             }
supported_projections = []
for _items in _projnames.items():
    supported_projections.append(" %-17s%-40s\n" % (_items))
supported_projections = ''.join(supported_projections)

_cylproj = ['cyl','merc','mill','gall','cea']
_pseudocyl = ['moll','robin','eck4','kav7','sinu','mbtfpq','vandg','hammer']
_dg2rad = math.radians(1.)
_rad2dg = math.degrees(1.)

# projection specific parameters.
projection_params = {'cyl'      : 'corners only (no width/height)',
             'merc'     : 'corners plus lat_ts (no width/height)',
             'tmerc'    : 'lon_0,lat_0,k_0',
             'omerc'    : 'lon_0,lat_0,lat_1,lat_2,lon_1,lon_2,no_rot,k_0',
             'mill'     : 'corners only (no width/height)',
             'gall'     : 'corners only (no width/height)',
             'cea'      : 'corners only plus lat_ts (no width/height)',
             'lcc'      : 'lon_0,lat_0,lat_1,lat_2,k_0',
             'laea'     : 'lon_0,lat_0',
             'nplaea'   : 'bounding_lat,lon_0,lat_0,no corners or width/height',
             'splaea'   : 'bounding_lat,lon_0,lat_0,no corners or width/height',
             'eqdc'     : 'lon_0,lat_0,lat_1,lat_2',
             'aeqd'     : 'lon_0,lat_0',
             'npaeqd'   : 'bounding_lat,lon_0,lat_0,no corners or width/height',
             'spaeqd'   : 'bounding_lat,lon_0,lat_0,no corners or width/height',
             'aea'      : 'lon_0,lat_0,lat_1',
             'stere'    : 'lon_0,lat_0,lat_ts,k_0',
             'npstere'  : 'bounding_lat,lon_0,lat_0,no corners or width/height',
             'spstere'  : 'bounding_lat,lon_0,lat_0,no corners or width/height',
             'cass'     : 'lon_0,lat_0',
             'poly'     : 'lon_0,lat_0',
             'ortho'    : 'lon_0,lat_0,llcrnrx,llcrnry,urcrnrx,urcrnry,no width/height',
             'geos'     : 'lon_0,satellite_height,llcrnrx,llcrnry,urcrnrx,urcrnry,no width/height',
             'nsper'    : 'lon_0,satellite_height,llcrnrx,llcrnry,urcrnrx,urcrnry,no width/height',
             'sinu'     : 'lon_0,lat_0,no corners or width/height',
             'moll'     : 'lon_0,lat_0,no corners or width/height',
             'hammer'   : 'lon_0,lat_0,no corners or width/height',
             'robin'    : 'lon_0,lat_0,no corners or width/height',
             'eck4'    : 'lon_0,lat_0,no corners or width/height',
             'kav7'    : 'lon_0,lat_0,no corners or width/height',
             'vandg'    : 'lon_0,lat_0,no corners or width/height',
             'mbtfpq'   : 'lon_0,lat_0,no corners or width/height',
             'gnom'     : 'lon_0,lat_0',
             'rotpole'  : 'lon_0,o_lat_p,o_lon_p,corner lat/lon or corner x,y (no width/height)'
             }

# create dictionary that maps epsg codes to Basemap kwargs.
pyproj_datadir = os.environ['PROJ_LIB']
epsgf = open(os.path.join(pyproj_datadir,'epsg'))
epsg_dict={}
for line in epsgf:
    if line.startswith("#"):
        continue
    l = line.split()
    code = l[0].strip("<>")
    parms = ' '.join(l[1:-1])
    _kw_args={}
    for s in l[1:-1]:
        try:
            k,v = s.split('=')
        except:
            pass
        k = k.strip("+")
        if k=='proj':
            if v == 'longlat': v = 'cyl'
            if v not in _projnames:
                continue
            k='projection'
        if k=='k':
            k='k_0'
        if k in ['projection','lat_1','lat_2','lon_0','lat_0',\
                 'a','b','k_0','lat_ts','ellps','datum']:
            if k not in ['projection','ellps','datum']:
                v = float(v)
            _kw_args[k]=v
    if 'projection' in _kw_args:
        if 'a' in _kw_args:
            if 'b' in _kw_args:
                _kw_args['rsphere']=(_kw_args['a'],_kw_args['b'])
                del _kw_args['b']
            else:
                _kw_args['rsphere']=_kw_args['a']
            del _kw_args['a']
        if 'datum' in _kw_args:
            if _kw_args['datum'] == 'NAD83':
                _kw_args['ellps'] = 'GRS80'
            elif _kw_args['datum'] == 'NAD27':
                _kw_args['ellps'] = 'clrk66'
            elif _kw_args['datum'] == 'WGS84':
                _kw_args['ellps'] = 'WGS84'
            del _kw_args['datum']
        # supported epsg projections.
        # omerc not supported yet, since we can't handle
        # alpha,gamma and lonc keywords.
        if _kw_args['projection'] != 'omerc':
            epsg_dict[code]=_kw_args
epsgf.close()

# The __init__ docstring is pulled out here because it is so long;
# Having it in the usual place makes it hard to get from the
# __init__ argument list to the code that uses the arguments.
_Basemap_init_doc = """

 Sets up a basemap with specified map projection.
 and creates the coastline data structures in map projection
 coordinates.

 Calling a Basemap class instance with the arguments lon, lat will
 convert lon/lat (in degrees) to x/y map projection coordinates
 (in meters). The inverse transformation is done if the optional keyword
 ``inverse`` is set to True.

 The desired projection is set with the projection keyword. Default is ``cyl``.
 Supported values for the projection keyword are:

 ==============   ====================================================
 Value            Description
 ==============   ====================================================
%(supported_projections)s
 ==============   ====================================================

 For most map projections, the map projection region can either be
 specified by setting these keywords:

 .. tabularcolumns:: |l|L|

 ==============   ====================================================
 Keyword          Description
 ==============   ====================================================
 llcrnrlon        longitude of lower left hand corner of the desired map
                  domain (degrees).
 llcrnrlat        latitude of lower left hand corner of the desired map
                  domain (degrees).
 urcrnrlon        longitude of upper right hand corner of the desired map
                  domain (degrees).
 urcrnrlat        latitude of upper right hand corner of the desired map
                  domain (degrees).
 ==============   ====================================================

 or these

 .. tabularcolumns:: |l|L|

 ==============   ====================================================
 Keyword          Description
 ==============   ====================================================
 width            width of desired map domain in projection coordinates
                  (meters).
 height           height of desired map domain in projection coordinates
                  (meters).
 lon_0            center of desired map domain (in degrees).
 lat_0            center of desired map domain (in degrees).
 ==============   ====================================================

 For ``sinu``, ``moll``, ``hammer``, ``npstere``, ``spstere``, ``nplaea``, ``splaea``,
 ``npaeqd``, ``spaeqd``, ``robin``, ``eck4``, ``kav7``, or ``mbtfpq``, the values of
 llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat, width and height are ignored
 (because either they are computed internally, or entire globe is
 always plotted).

 For the cylindrical projections (``cyl``, ``merc``, ``mill``, ``cea``  and ``gall``),
 the default is to use
 llcrnrlon=-180,llcrnrlat=-90, urcrnrlon=180 and urcrnrlat=90). For all other
 projections except ``ortho``, ``geos`` and ``nsper``, either the lat/lon values of the
 corners or width and height must be specified by the user.

 For ``ortho``, ``geos`` and ``nsper``, the lat/lon values of the corners may be specified,
 or the x/y values of the corners (llcrnrx,llcrnry,urcrnrx,urcrnry) in the
 coordinate system of the global projection (with x=0,y=0 at the center
 of the global projection).  If the corners are not specified,
 the entire globe is plotted.

 For ``rotpole``, the lat/lon values of the corners on the unrotated sphere
 may be provided as llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat, or the lat/lon
 values of the corners on the rotated sphere can be given as
 llcrnrx,llcrnry,urcrnrx,urcrnry.

 Other keyword arguments:

 .. tabularcolumns:: |l|L|

 ==============   ====================================================
 Keyword          Description
 ==============   ====================================================
 resolution       resolution of boundary database to use. Can be ``c``
                  (crude), ``l`` (low), ``i`` (intermediate), ``h``
                  (high), ``f`` (full) or None.
                  If None, no boundary data will be read in (and
                  class methods such as drawcoastlines will raise an
                  if invoked).
                  Resolution drops off by roughly 80%% between datasets.
                  Higher res datasets are much slower to draw.
                  Default ``c``. Coastline data is from the GSHHS
                  (http://www.soest.hawaii.edu/wessel/gshhs/gshhs.html).
                  State, country and river datasets from the Generic
                  Mapping Tools (http://gmt.soest.hawaii.edu).
 area_thresh      coastline or lake with an area smaller than
                  area_thresh in km^2 will not be plotted.
                  Default 10000,1000,100,10,1 for resolution
                  ``c``, ``l``, ``i``, ``h``, ``f``.
 rsphere          radius of the sphere used to define map projection
                  (default 6370997 meters, close to the arithmetic mean
                  radius of the earth). If given as a sequence, the
                  first two elements are interpreted as the radii
                  of the major and minor axes of an ellipsoid.
                  Note: sometimes an ellipsoid is specified by the
                  major axis and an inverse flattening parameter (if).
                  The minor axis (b) can be computed from the major
                  axis (a) and the inverse flattening parameter using
                  the formula if = a/(a-b).
 ellps            string describing ellipsoid ('GRS80' or 'WGS84',
                  for example). If both rsphere and ellps are given,
                  rsphere is ignored. Default None. See pyproj.pj_ellps
                  for allowed values.
 suppress_ticks   suppress automatic drawing of axis ticks and labels
                  in map projection coordinates.  Default True,
                  so parallels and meridians can be labelled instead.
                  If parallel or meridian labelling is requested
                  (using drawparallels and drawmeridians methods),
                  automatic tick labelling will be supressed even if
                  suppress_ticks=False.  suppress_ticks=False
                  is useful if you want to use your own custom tick
                  formatter, or  if you want to let matplotlib label
                  the axes in meters using map projection
                  coordinates.
 fix_aspect       fix aspect ratio of plot to match aspect ratio
                  of map projection region (default True).
 anchor           determines how map is placed in axes rectangle
                  (passed to axes.set_aspect). Default is ``C``,
                  which means map is centered.
                  Allowed values are
                  ``C``, ``SW``, ``S``, ``SE``, ``E``, ``NE``,
                  ``N``, ``NW``, and ``W``.
 celestial        use astronomical conventions for longitude (i.e.
                  negative longitudes to the east of 0). Default False.
                  Implies resolution=None.
 ax               set default axes instance
                  (default None - matplotlib.pyplot.gca() may be used
                  to get the current axes instance).
                  If you do not want matplotlib.pyplot to be imported,
                  you can either set this to a pre-defined axes
                  instance, or use the ``ax`` keyword in each Basemap
                  method call that does drawing. In the first case,
                  all Basemap method calls will draw to the same axes
                  instance.  In the second case, you can draw to
                  different axes with the same Basemap instance.
                  You can also use the ``ax`` keyword in individual
                  method calls to selectively override the default
                  axes instance.
 ==============   ====================================================

 The following keywords are map projection parameters which all default to
 None.  Not all parameters are used by all projections, some are ignored.
 The module variable ``projection_params`` is a dictionary which
 lists which parameters apply to which projections.

 .. tabularcolumns:: |l|L|

 ================ ====================================================
 Keyword          Description
 ================ ====================================================
 lat_ts           latitude of true scale. Optional for stereographic,
                  cylindrical equal area and mercator projections.
                  default is lat_0 for stereographic projection.
                  default is 0 for mercator and cylindrical equal area
                  projections.
 lat_1            first standard parallel for lambert conformal,
                  albers equal area and equidistant conic.
                  Latitude of one of the two points on the projection
                  centerline for oblique mercator. If lat_1 is not given, but
                  lat_0 is, lat_1 is set to lat_0 for lambert
                  conformal, albers equal area and equidistant conic.
 lat_2            second standard parallel for lambert conformal,
                  albers equal area and equidistant conic.
                  Latitude of one of the two points on the projection
                  centerline for oblique mercator. If lat_2 is not
                  given it is set to lat_1 for lambert conformal,
                  albers equal area and equidistant conic.
 lon_1            Longitude of one of the two points on the projection
                  centerline for oblique mercator.
 lon_2            Longitude of one of the two points on the projection
                  centerline for oblique mercator.
 k_0              Scale factor at natural origin (used
                  by 'tmerc', 'omerc', 'stere' and 'lcc').
 no_rot           only used by oblique mercator.
                  If set to True, the map projection coordinates will
                  not be rotated to true North.  Default is False
                  (projection coordinates are automatically rotated).
 lat_0            central latitude (y-axis origin) - used by all
                  projections.
 lon_0            central meridian (x-axis origin) - used by all
                  projections.
 o_lat_p          latitude of rotated pole (only used by 'rotpole')
 o_lon_p          longitude of rotated pole (only used by 'rotpole')
 boundinglat      bounding latitude for pole-centered projections
                  (npstere,spstere,nplaea,splaea,npaeqd,spaeqd).
                  These projections are square regions centered
                  on the north or south pole.
                  The longitude lon_0 is at 6-o'clock, and the
                  latitude circle boundinglat is tangent to the edge
                  of the map at lon_0.
 round            cut off pole-centered projection at boundinglat
                  (so plot is a circle instead of a square). Only
                  relevant for npstere,spstere,nplaea,splaea,npaeqd
                  or spaeqd projections. Default False.
 satellite_height height of satellite (in m) above equator -
                  only relevant for geostationary
                  and near-sided perspective (``geos`` or ``nsper``)
                  projections. Default 35,786 km.
 ================ ====================================================

 Useful instance variables:

 .. tabularcolumns:: |l|L|

 ================ ====================================================
 Variable Name    Description
 ================ ====================================================
 projection       map projection. Print the module variable
                  ``supported_projections`` to see a list of allowed
                  values.
 epsg             EPSG code defining projection (see
                  http://spatialreference.org for a list of
                  EPSG codes and their definitions).
 aspect           map aspect ratio
                  (size of y dimension / size of x dimension).
 llcrnrlon        longitude of lower left hand corner of the
                  selected map domain.
 llcrnrlat        latitude of lower left hand corner of the
                  selected map domain.
 urcrnrlon        longitude of upper right hand corner of the
                  selected map domain.
 urcrnrlat        latitude of upper right hand corner of the
                  selected map domain.
 llcrnrx          x value of lower left hand corner of the
                  selected map domain in map projection coordinates.
 llcrnry          y value of lower left hand corner of the
                  selected map domain in map projection coordinates.
 urcrnrx          x value of upper right hand corner of the
                  selected map domain in map projection coordinates.
 urcrnry          y value of upper right hand corner of the
                  selected map domain in map projection coordinates.
 rmajor           equatorial radius of ellipsoid used (in meters).
 rminor           polar radius of ellipsoid used (in meters).
 resolution       resolution of boundary dataset being used (``c``
                  for crude, ``l`` for low, etc.).
                  If None, no boundary dataset is associated with the
                  Basemap instance.
 proj4string      the string describing the map projection that is
                  used by PROJ.4.
 ================ ====================================================

 **Converting from Geographic (lon/lat) to Map Projection (x/y) Coordinates**

 Calling a Basemap class instance with the arguments lon, lat will
 convert lon/lat (in degrees) to x/y map projection
 coordinates (in meters).  If optional keyword ``inverse`` is
 True (default is False), the inverse transformation from x/y
 to lon/lat is performed.

 For cylindrical equidistant projection (``cyl``), this
 does nothing (i.e. x,y == lon,lat).

 For non-cylindrical projections, the inverse transformation
 always returns longitudes between -180 and 180 degrees. For
 cylindrical projections (self.projection == ``cyl``, ``mill``,
 ``cea``, ``gall`` or ``merc``)
 the inverse transformation will return longitudes between
 self.llcrnrlon and self.llcrnrlat.

 Input arguments lon, lat can be either scalar floats, sequences
 or numpy arrays.

 **Example Usage:**

 >>> from mpl_toolkits.basemap import Basemap
 >>> import numpy as np
 >>> import matplotlib.pyplot as plt
 >>> # read in topo data (on a regular lat/lon grid)
 >>> etopo = np.loadtxt('etopo20data.gz')
 >>> lons  = np.loadtxt('etopo20lons.gz')
 >>> lats  = np.loadtxt('etopo20lats.gz')
 >>> # create Basemap instance for Robinson projection.
 >>> m = Basemap(projection='robin',lon_0=0.5*(lons[0]+lons[-1]))
 >>> # compute map projection coordinates for lat/lon grid.
 >>> x, y = m(*np.meshgrid(lons,lats))
 >>> # make filled contour plot.
 >>> cs = m.contourf(x,y,etopo,30,cmap=plt.cm.jet)
 >>> m.drawcoastlines() # draw coastlines
 >>> m.drawmapboundary() # draw a line around the map region
 >>> m.drawparallels(np.arange(-90.,120.,30.),labels=[1,0,0,0]) # draw parallels
 >>> m.drawmeridians(np.arange(0.,420.,60.),labels=[0,0,0,1]) # draw meridians
 >>> plt.title('Robinson Projection') # add a title
 >>> plt.show()

 [this example (simpletest.py) plus many others can be found in the
 examples directory of source distribution.  The "OO" version of this
 example (which does not use matplotlib.pyplot) is called "simpletest_oo.py".]
""" % locals()

# unsupported projection error message.
_unsupported_projection = ["'%s' is an unsupported projection.\n"]
_unsupported_projection.append("The supported projections are:\n")
_unsupported_projection.append(supported_projections)
_unsupported_projection = ''.join(_unsupported_projection)

def _validated_ll(param, name, minval, maxval):
    param = float(param)
    if param > maxval or param < minval:
        raise ValueError('%s must be between %f and %f degrees' %
                                           (name, minval, maxval))
    return param


def _validated_or_none(param, name, minval, maxval):
    if param is None:
        return None
    return _validated_ll(param, name, minval, maxval)


def _insert_validated(d, param, name, minval, maxval):
    if param is not None:
        d[name] = _validated_ll(param, name, minval, maxval)

def _transform(plotfunc):
    # shift data and longitudes to map projection region, then compute
    # transformation to map projection coordinates.
    @functools.wraps(plotfunc)
    def with_transform(self,x,y,data,*args,**kwargs):
        # input coordinates are latitude/longitude, not map projection coords.
        if kwargs.pop('latlon', latlon_default):
            # shift data to map projection region for
            # cylindrical and pseudo-cylindrical projections.
            if self.projection in _cylproj or self.projection in _pseudocyl:
                x, data = self.shiftdata(x, data,
                                         fix_wrap_around=plotfunc.__name__ not in ["scatter"])
            # convert lat/lon coords to map projection coords.
            x, y = self(x,y)
        return plotfunc(self,x,y,data,*args,**kwargs)
    return with_transform

def _transform1d(plotfunc):
    # shift data and longitudes to map projection region, then compute
    # transformation to map projection coordinates.
    @functools.wraps(plotfunc)
    def with_transform(self,x,y,*args,**kwargs):
        x = np.asarray(x)
        # input coordinates are latitude/longitude, not map projection coords.
        if kwargs.pop('latlon', latlon_default):
            # shift data to map projection region for
            # cylindrical and pseudo-cylindrical projections.
            if self.projection in _cylproj or self.projection in _pseudocyl:
                if x.ndim == 1:
                    x = self.shiftdata(x, fix_wrap_around=plotfunc.__name__ not in ["scatter"])
                elif x.ndim == 0:
                    if x > 180:
                        x = x - 360.
            # convert lat/lon coords to map projection coords.
            x, y = self(x,y)
        return plotfunc(self,x,y,*args,**kwargs)
    return with_transform

def _transformuv(plotfunc):
    # shift data and longitudes to map projection region, then compute
    # transformation to map projection coordinates. Works when call
    # signature has two data arrays instead of one.
    @functools.wraps(plotfunc)
    def with_transform(self,x,y,u,v,*args,**kwargs):
        # input coordinates are latitude/longitude, not map projection coords.
        if kwargs.pop('latlon', latlon_default):
            # shift data to map projection region for
            # cylindrical and pseudo-cylindrical projections.
            if self.projection in _cylproj or self.projection in _pseudocyl:
                x1, u = self.shiftdata(x, u)
                x, v = self.shiftdata(x, v)
            # convert lat/lon coords to map projection coords.
            x, y = self(x,y)
        return plotfunc(self,x,y,u,v,*args,**kwargs)
    return with_transform

class Basemap(object):

    def __init__(self, llcrnrlon=None, llcrnrlat=None,
                       urcrnrlon=None, urcrnrlat=None,
                       llcrnrx=None, llcrnry=None,
                       urcrnrx=None, urcrnry=None,
                       width=None, height=None,
                       projection='aeqd', resolution='c',
                       area_thresh=None, rsphere=6370997.0,
                       ellps=None, lat_ts=None,
                       lat_1=None, lat_2=None,
                       lat_0=None, lon_0=None,
                       lon_1=None, lon_2=None,
                       o_lon_p=None, o_lat_p=None,
                       k_0=None,
                       no_rot=False,
                       suppress_ticks=True,
                       satellite_height=35786000,
                       boundinglat=None,
                       fix_aspect=True,
                       anchor='C',
                       celestial=False,
                       round=False,
                       epsg=None,
                       ax=None):
        # docstring is added after __init__ method definition

        # set epsg code if given, set to 4326 for projection='cyl':
        if epsg is not None:
            self.epsg = epsg
        elif projection == 'cyl':
            self.epsg = 4326
        # replace kwarg values with those implied by epsg code,
        # if given.
        if hasattr(self,'epsg'):
            if str(self.epsg) not in epsg_dict:
                raise ValueError('%s is not a supported EPSG code' %
                        self.epsg)
            epsg_params = epsg_dict[str(self.epsg)]
            for k in epsg_params:
                if k == 'projection':
                    projection = epsg_params[k]
                elif k == 'rsphere':
                    rsphere = epsg_params[k]
                elif k == 'ellps':
                    ellps = epsg_params[k]
                elif k == 'lat_1':
                    lat_1 = epsg_params[k]
                elif k == 'lat_2':
                    lat_2 = epsg_params[k]
                elif k == 'lon_0':
                    lon_0 = epsg_params[k]
                elif k == 'lat_0':
                    lat_0 = epsg_params[k]
                elif k == 'lat_ts':
                    lat_ts = epsg_params[k]
                elif k == 'k_0':
                    k_0 = epsg_params[k]

        # fix aspect to ratio to match aspect ratio of map projection
        # region
        self.fix_aspect = fix_aspect
        # where to put plot in figure (default is 'C' or center)
        self.anchor = anchor
        # geographic or celestial coords?
        self.celestial = celestial
        # map projection.
        self.projection = projection
        # bounding lat (for pole-centered plots)
        self.boundinglat = boundinglat
        # is a round pole-centered plot desired?
        self.round = round
        # full disk projection?
        self._fulldisk = False # default value

        # set up projection parameter dict.
        projparams = {}
        projparams['proj'] = projection
        # if ellps keyword specified, it over-rides rsphere.
        if ellps is not None:
            try:
                elldict = pyproj.pj_ellps[ellps]
            except KeyError:
                raise ValueError(
                'illegal ellps definition, allowed values are %s' %
                pyproj.pj_ellps.keys())
            projparams['a'] = elldict['a']
            if 'b' in elldict:
                projparams['b'] = elldict['b']
            else:
                projparams['b'] = projparams['a']*(1.0-(1.0/elldict['rf']))
        else:
            try:
                if rsphere[0] > rsphere[1]:
                    projparams['a'] = rsphere[0]
                    projparams['b'] = rsphere[1]
                else:
                    projparams['a'] = rsphere[1]
                    projparams['b'] = rsphere[0]
            except:
                if projection == 'tmerc':
                # use bR_a instead of R because of obscure bug
                # in proj4 for tmerc projection.
                    projparams['bR_a'] = rsphere
                else:
                    projparams['R'] = rsphere
        # set units to meters.
        projparams['units']='m'
        # check for sane values of lon_0, lat_0, lat_ts, lat_1, lat_2
        lat_0 = _validated_or_none(lat_0, 'lat_0', -90, 90)
        lat_1 = _validated_or_none(lat_1, 'lat_1', -90, 90)
        lat_2 = _validated_or_none(lat_2, 'lat_2', -90, 90)
        lat_ts = _validated_or_none(lat_ts, 'lat_ts', -90, 90)
        lon_0 = _validated_or_none(lon_0, 'lon_0', -360, 720)
        lon_1 = _validated_or_none(lon_1, 'lon_1', -360, 720)
        lon_2 = _validated_or_none(lon_2, 'lon_2', -360, 720)
        llcrnrlon = _validated_or_none(llcrnrlon, 'llcrnrlon', -360, 720)
        urcrnrlon = _validated_or_none(urcrnrlon, 'urcrnrlon', -360, 720)
        llcrnrlat = _validated_or_none(llcrnrlat, 'llcrnrlat', -90, 90)
        urcrnrlat = _validated_or_none(urcrnrlat, 'urcrnrlat', -90, 90)

        _insert_validated(projparams, lat_0, 'lat_0', -90, 90)
        _insert_validated(projparams, lat_1, 'lat_1', -90, 90)
        _insert_validated(projparams, lat_2, 'lat_2', -90, 90)
        _insert_validated(projparams, lat_ts, 'lat_ts', -90, 90)
        _insert_validated(projparams, lon_0, 'lon_0', -360, 720)
        _insert_validated(projparams, lon_1, 'lon_1', -360, 720)
        _insert_validated(projparams, lon_2, 'lon_2', -360, 720)
        if projection in ['geos','nsper']:
            projparams['h'] = satellite_height
        # check for sane values of projection corners.
        using_corners = (None not in [llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat])
        if using_corners:
            self.llcrnrlon = _validated_ll(llcrnrlon, 'llcrnrlon', -360, 720)
            self.urcrnrlon = _validated_ll(urcrnrlon, 'urcrnrlon', -360, 720)
            self.llcrnrlat = _validated_ll(llcrnrlat, 'llcrnrlat', -90, 90)
            self.urcrnrlat = _validated_ll(urcrnrlat, 'urcrnrlat', -90, 90)

        # for each of the supported projections,
        # compute lat/lon of domain corners
        # and set values in projparams dict as needed.

        if projection in ['lcc', 'eqdc', 'aea']:
            if projection == 'lcc' and k_0 is not None:
                projparams['k_0']=k_0
            # if lat_0 is given, but not lat_1,
            # set lat_1=lat_0
            if lat_1 is None and lat_0 is not None:
                lat_1 = lat_0
                projparams['lat_1'] = lat_1
            if lat_1 is None or lon_0 is None:
                raise ValueError('must specify lat_1 or lat_0 and lon_0 for %s basemap (lat_2 is optional)' % _projnames[projection])
            if lat_2 is None:
                projparams['lat_2'] = lat_1
            if not using_corners:
                using_cornersxy = (None not in [llcrnrx,llcrnry,urcrnrx,urcrnry])
                if using_cornersxy:
                    llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat = _choosecornersllur(llcrnrx,llcrnry,urcrnrx,urcrnry,**projparams)
                    self.llcrnrlon = llcrnrlon; self.llcrnrlat = llcrnrlat
                    self.urcrnrlon = urcrnrlon; self.urcrnrlat = urcrnrlat
                else:
                    if width is None or height is None:
                        raise ValueError('must either specify lat/lon values of corners (llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat) in degrees or width and height in meters')
                    if lon_0 is None or lat_0 is None:
                        raise ValueError('must specify lon_0 and lat_0 when using width, height to specify projection region')
                    llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat = _choosecorners(width,height,**projparams)
                    self.llcrnrlon = llcrnrlon; self.llcrnrlat = llcrnrlat
                    self.urcrnrlon = urcrnrlon; self.urcrnrlat = urcrnrlat
        elif projection == 'stere':
            if k_0 is not None:
                projparams['k_0']=k_0
            if lat_0 is None or lon_0 is None:
                raise ValueError('must specify lat_0 and lon_0 for Stereographic basemap (lat_ts is optional)')
            if not using_corners:
                if width is None or height is None:
                    raise ValueError('must either specify lat/lon values of corners (llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat) in degrees or width and height in meters')
                if lon_0 is None or lat_0 is None:
                    raise ValueError('must specify lon_0 and lat_0 when using width, height to specify projection region')
                llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat = _choosecorners(width,height,**projparams)
                self.llcrnrlon = llcrnrlon; self.llcrnrlat = llcrnrlat
                self.urcrnrlon = urcrnrlon; self.urcrnrlat = urcrnrlat
        elif projection in ['spstere', 'npstere',
                            'splaea', 'nplaea',
                            'spaeqd', 'npaeqd']:
            if (projection == 'splaea' and boundinglat >= 0) or\
               (projection == 'nplaea' and boundinglat <= 0):
                msg='boundinglat cannot extend into opposite hemisphere'
                raise ValueError(msg)
            if boundinglat is None or lon_0 is None:
                raise ValueError('must specify boundinglat and lon_0 for %s basemap' % _projnames[projection])
            if projection[0] == 's':
                sgn = -1
            else:
                sgn = 1
            rootproj = projection[2:]
            projparams['proj'] = rootproj
            if rootproj == 'stere':
                projparams['lat_ts'] = sgn * 90.
            projparams['lat_0'] = sgn * 90.
            self.llcrnrlon = lon_0 - sgn*45.
            self.urcrnrlon = lon_0 + sgn*135.
            proj = pyproj.Proj(projparams)
            x,y = proj(lon_0,boundinglat)
            lon,self.llcrnrlat = proj(math.sqrt(2.)*y,0.,inverse=True)
            self.urcrnrlat = self.llcrnrlat
            if width is not None or height is not None:
                sys.stdout.write('warning: width and height keywords ignored for %s projection' % _projnames[projection])
        elif projection == 'laea':
            if lat_0 is None or lon_0 is None:
                raise ValueError('must specify lat_0 and lon_0 for Lambert Azimuthal basemap')
            if not using_corners:
                if width is None or height is None:
                    raise ValueError('must either specify lat/lon values of corners (llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat) in degrees or width and height in meters')
                if lon_0 is None or lat_0 is None:
                    raise ValueError('must specify lon_0 and lat_0 when using width, height to specify projection region')
                llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat = _choosecorners(width,height,**projparams)
                self.llcrnrlon = llcrnrlon; self.llcrnrlat = llcrnrlat
                self.urcrnrlon = urcrnrlon; self.urcrnrlat = urcrnrlat
        elif projection in ['tmerc','gnom','cass','poly'] :
            if projection == 'tmerc' and k_0 is not None:
                projparams['k_0']=k_0
            if projection == 'gnom' and 'R' not in projparams:
                raise ValueError('gnomonic projection only works for perfect spheres - not ellipsoids')
            if lat_0 is None or lon_0 is None:
                raise ValueError('must specify lat_0 and lon_0 for Transverse Mercator, Gnomonic, Cassini-Soldnerr and Polyconic basemap')
            if not using_corners:
                if width is None or height is None:
                    raise ValueError('must either specify lat/lon values of corners (llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat) in degrees or width and height in meters')
                if lon_0 is None or lat_0 is None:
                    raise ValueError('must specify lon_0 and lat_0 when using width, height to specify projection region')
                llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat = _choosecorners(width,height,**projparams)
                self.llcrnrlon = llcrnrlon; self.llcrnrlat = llcrnrlat
                self.urcrnrlon = urcrnrlon; self.urcrnrlat = urcrnrlat
        elif projection == 'ortho':
            if 'R' not in projparams:
                raise ValueError('orthographic projection only works for perfect spheres - not ellipsoids')
            if lat_0 is None or lon_0 is None:
                raise ValueError('must specify lat_0 and lon_0 for Orthographic basemap')
            if (lat_0 == 90 or lat_0 == -90) and\
               None in [llcrnrx,llcrnry,urcrnrx,urcrnry]:
                # for ortho plot centered on pole, set boundinglat to equator.
                # (so meridian labels can be drawn in this special case).
                self.boundinglat = 0
                self.round = True
            if width is not None or height is not None:
                sys.stdout.write('warning: width and height keywords ignored for %s projection' % _projnames[self.projection])
            if not using_corners:
                llcrnrlon = -180.
                llcrnrlat = -90.
                urcrnrlon = 180
                urcrnrlat = 90.
                self._fulldisk = True
            else:
                self._fulldisk = False
            self.llcrnrlon = llcrnrlon; self.llcrnrlat = llcrnrlat
            self.urcrnrlon = urcrnrlon; self.urcrnrlat = urcrnrlat
            # FIXME: won't work for points exactly on equator??
            if np.abs(lat_0) < 1.e-2: lat_0 = 1.e-2
            projparams['lat_0'] = lat_0
        elif projection == 'geos':
            if lat_0 is not None and lat_0 != 0:
                raise ValueError('lat_0 must be zero for Geostationary basemap')
            if lon_0 is None:
                raise ValueError('must specify lon_0 for Geostationary basemap')
            if width is not None or height is not None:
                sys.stdout.write('warning: width and height keywords ignored for %s projection' % _projnames[self.projection])
            if not using_corners:
                llcrnrlon = -180.
                llcrnrlat = -90.
                urcrnrlon = 180
                urcrnrlat = 90.
                self._fulldisk = True
            else:
                self._fulldisk = False
            self.llcrnrlon = llcrnrlon; self.llcrnrlat = llcrnrlat
            self.urcrnrlon = urcrnrlon; self.urcrnrlat = urcrnrlat
        elif projection == 'nsper':
            if 'R' not in projparams:
                raise ValueError('near-sided perspective projection only works for perfect spheres - not ellipsoids')
            if lat_0 is None or lon_0 is None:
                msg='must specify lon_0 and lat_0 for near-sided perspective Basemap'
                raise ValueError(msg)
            if width is not None or height is not None:
                sys.stdout.write('warning: width and height keywords ignored for %s projection' % _projnames[self.projection])
            if not using_corners:
                llcrnrlon = -180.
                llcrnrlat = -90.
                urcrnrlon = 180
                urcrnrlat = 90.
                self._fulldisk = True
            else:
                self._fulldisk = False
            self.llcrnrlon = llcrnrlon; self.llcrnrlat = llcrnrlat
            self.urcrnrlon = urcrnrlon; self.urcrnrlat = urcrnrlat
        elif projection in _pseudocyl:
            if lon_0 is None:
                raise ValueError('must specify lon_0 for %s projection' % _projnames[self.projection])
            if width is not None or height is not None:
                sys.stdout.write('warning: width and height keywords ignored for %s projection' % _projnames[self.projection])
            llcrnrlon = lon_0-180.
            llcrnrlat = -90.
            urcrnrlon = lon_0+180
            urcrnrlat = 90.
            self.llcrnrlon = llcrnrlon; self.llcrnrlat = llcrnrlat
            self.urcrnrlon = urcrnrlon; self.urcrnrlat = urcrnrlat
        elif projection == 'omerc':
            if k_0 is not None:
                projparams['k_0']=k_0
            if lat_1 is None or lon_1 is None or lat_2 is None or lon_2 is None:
                raise ValueError('must specify lat_1,lon_1 and lat_2,lon_2 for Oblique Mercator basemap')
            projparams['lat_1'] = lat_1
            projparams['lon_1'] = lon_1
            projparams['lat_2'] = lat_2
            projparams['lon_2'] = lon_2
            projparams['lat_0'] = lat_0
            if no_rot:
                projparams['no_rot']=''
            #if not using_corners:
            #    raise ValueError, 'cannot specify map region with width and height keywords for this projection, please specify lat/lon values of corners'
            if not using_corners:
                if width is None or height is None:
                    raise ValueError('must either specify lat/lon values of corners (llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat) in degrees or width and height in meters')
                if lon_0 is None or lat_0 is None:
                    raise ValueError('must specify lon_0 and lat_0 when using width, height to specify projection region')
                llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat = _choosecorners(width,height,**projparams)
                self.llcrnrlon = llcrnrlon; self.llcrnrlat = llcrnrlat
                self.urcrnrlon = urcrnrlon; self.urcrnrlat = urcrnrlat
        elif projection == 'aeqd':
            if lat_0 is None or lon_0 is None:
                raise ValueError('must specify lat_0 and lon_0 for Azimuthal Equidistant basemap')
            if not using_corners:
                if width is None or height is None:
                    self._fulldisk = True
                    llcrnrlon = -180.
                    llcrnrlat = -90.
                    urcrnrlon = 180
                    urcrnrlat = 90.
                else:
                    self._fulldisk = False
                if lon_0 is None or lat_0 is None:
                    raise ValueError('must specify lon_0 and lat_0 when using width, height to specify projection region')
                if not self._fulldisk:
                    llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat = _choosecorners(width,height,**projparams)
                self.llcrnrlon = llcrnrlon; self.llcrnrlat = llcrnrlat
                self.urcrnrlon = urcrnrlon; self.urcrnrlat = urcrnrlat
        elif projection in _cylproj:
            if projection == 'merc' or projection == 'cea':
                if lat_ts is None:
                    lat_ts = 0.
                    projparams['lat_ts'] = lat_ts
            if not using_corners:
                llcrnrlat = -90.
                urcrnrlat = 90.
                if lon_0 is not None:
                    llcrnrlon = lon_0-180.
                    urcrnrlon = lon_0+180.
                else:
                    llcrnrlon = -180.
                    urcrnrlon = 180
                if projection == 'merc':
                    # clip plot region to be within -89.99S to 89.99N
                    # (mercator is singular at poles)
                    if llcrnrlat < -89.99: llcrnrlat = -89.99
                    if llcrnrlat > 89.99: llcrnrlat = 89.99
                    if urcrnrlat < -89.99: urcrnrlat = -89.99
                    if urcrnrlat > 89.99: urcrnrlat = 89.99
                self.llcrnrlon = llcrnrlon; self.llcrnrlat = llcrnrlat
                self.urcrnrlon = urcrnrlon; self.urcrnrlat = urcrnrlat
            if width is not None or height is not None:
                sys.stdout.write('warning: width and height keywords ignored for %s projection' % _projnames[self.projection])
            if lon_0 is not None:
                projparams['lon_0'] = lon_0
            else:
                projparams['lon_0']=0.5*(llcrnrlon+urcrnrlon)
        elif projection == 'rotpole':
            if lon_0 is None or o_lon_p is None or o_lat_p is None:
                msg='must specify lon_0,o_lat_p,o_lon_p for rotated pole Basemap'
                raise ValueError(msg)
            if width is not None or height is not None:
                sys.stdout.write('warning: width and height keywords ignored for %s projection' % _projnames[self.projection])
            projparams['lon_0']=lon_0
            projparams['o_lon_p']=o_lon_p
            projparams['o_lat_p']=o_lat_p
            projparams['o_proj']='longlat'
            projparams['proj']='ob_tran'
            if not using_corners and None in [llcrnrx,llcrnry,urcrnrx,urcrnry]:
                raise ValueError('must specify lat/lon values of corners in degrees')
            if None not in [llcrnrx,llcrnry,urcrnrx,urcrnry]:
                p = pyproj.Proj(projparams)
                llcrnrx = _dg2rad*llcrnrx; llcrnry = _dg2rad*llcrnry
                urcrnrx = _dg2rad*urcrnrx; urcrnry = _dg2rad*urcrnry
                llcrnrlon, llcrnrlat = p(llcrnrx,llcrnry,inverse=True)
                urcrnrlon, urcrnrlat = p(urcrnrx,urcrnry,inverse=True)
                self.llcrnrlon = llcrnrlon; self.llcrnrlat = llcrnrlat
                self.urcrnrlon = urcrnrlon; self.urcrnrlat = urcrnrlat
        else:
            raise ValueError(_unsupported_projection % projection)

        # initialize proj4
        proj = Proj(projparams,self.llcrnrlon,self.llcrnrlat,self.urcrnrlon,self.urcrnrlat)

        # make sure axis ticks are suppressed.
        self.noticks = suppress_ticks
        # map boundary not yet drawn.
        self._mapboundarydrawn = False

        # make Proj instance a Basemap instance variable.
        self.projtran = proj
        # copy some Proj attributes.
        atts = ['rmajor','rminor','esq','flattening','ellipsoid','projparams']
        for att in atts:
            self.__dict__[att] = proj.__dict__[att]
        # these only exist for geostationary projection.
        if hasattr(proj,'_width'):
            self.__dict__['_width'] = proj.__dict__['_width']
        if hasattr(proj,'_height'):
            self.__dict__['_height'] = proj.__dict__['_height']
        # spatial reference string (useful for georeferencing output
        # images with gdal_translate).
        if hasattr(self,'_proj4'):
            #self.srs = proj._proj4.srs
            self.srs = proj._proj4.pjinitstring
        else:
            pjargs = []
            for key,value in self.projparams.items():
                # 'cyl' projection translates to 'eqc' in PROJ.4
                if projection == 'cyl' and key == 'proj':
                    value = 'eqc'
                # ignore x_0 and y_0 settings for 'cyl' projection
                # (they are not consistent with what PROJ.4 uses)
                elif projection == 'cyl' and key in ['x_0','y_0']:
                    continue
                pjargs.append('+'+key+"="+str(value)+' ')
            self.srs = ''.join(pjargs)
        self.proj4string = self.srs
        # set instance variables defining map region.
        self.xmin = proj.xmin
        self.xmax = proj.xmax
        self.ymin = proj.ymin
        self.ymax = proj.ymax
        if projection == 'cyl':
            self.aspect = (self.urcrnrlat-self.llcrnrlat)/(self.urcrnrlon-self.llcrnrlon)
        else:
            self.aspect = (proj.ymax-proj.ymin)/(proj.xmax-proj.xmin)
        if projection in ['geos','ortho','nsper'] and \
           None not in [llcrnrx,llcrnry,urcrnrx,urcrnry]:
            self.llcrnrx = llcrnrx+0.5*proj.xmax
            self.llcrnry = llcrnry+0.5*proj.ymax
            self.urcrnrx = urcrnrx+0.5*proj.xmax
            self.urcrnry = urcrnry+0.5*proj.ymax
            self._fulldisk = False
        else:
            self.llcrnrx = proj.llcrnrx
            self.llcrnry = proj.llcrnry
            self.urcrnrx = proj.urcrnrx
            self.urcrnry = proj.urcrnry

        if self.projection == 'rotpole':
            lon0,lat0 = self(0.5*(self.llcrnrx + self.urcrnrx),\
                             0.5*(self.llcrnry + self.urcrnry),\
                             inverse=True)
            self.projparams['lat_0']=lat0

        # if ax == None, pyplot.gca may be used.
        self.ax = ax
        self.lsmask = None
        # This will record hashs of Axes instances.
        self._initialized_axes = set()

        # set defaults for area_thresh.
        self.resolution = resolution
        # celestial=True implies resolution=None (no coastlines).
        if self.celestial:
            self.resolution=None
        if area_thresh is None and self.resolution is not None:
            if resolution == 'c':
                area_thresh = 10000.
            elif resolution == 'l':
                area_thresh = 1000.
            elif resolution == 'i':
                area_thresh = 100.
            elif resolution == 'h':
                area_thresh = 10.
            elif resolution == 'f':
                area_thresh = 1.
            else:
                raise ValueError("boundary resolution must be one of 'c','l','i','h' or 'f'")
        self.area_thresh = area_thresh
        
        # set min/max lats for projection domain.
        if self.projection in _cylproj:
            self.latmin = self.llcrnrlat
            self.latmax = self.urcrnrlat
            self.lonmin = self.llcrnrlon
            self.lonmax = self.urcrnrlon
        elif self.projection in ['ortho','geos','nsper'] + _pseudocyl:
            self.latmin = -90.
            self.latmax = 90.
            self.lonmin = self.llcrnrlon
            self.lonmax = self.urcrnrlon
        else:
            lons, lats = self.makegrid(1001,1001)
            lats = ma.masked_where(lats > 1.e20,lats)
            lons = ma.masked_where(lons > 1.e20,lons)
            self.latmin = lats.min()
            self.latmax = lats.max()
            self.lonmin = lons.min()
            self.lonmax = lons.max()
            
            if lat_0 is None:
                lon_0, lat_0 =\
                self(0.5*(self.xmin+self.xmax),
                     0.5*(self.ymin+self.ymax),inverse=True)
        
    # set __init__'s docstring
    __init__.__doc__ = _Basemap_init_doc

    def __call__(self,x,y,inverse=False):
        """
        Calling a Basemap class instance with the arguments lon, lat will
        convert lon/lat (in degrees) to x/y map projection
        coordinates (in meters).  If optional keyword ``inverse`` is
        True (default is False), the inverse transformation from x/y
        to lon/lat is performed.

        For cylindrical equidistant projection (``cyl``), this
        does nothing (i.e. x,y == lon,lat).

        For non-cylindrical projections, the inverse transformation
        always returns longitudes between -180 and 180 degrees. For
        cylindrical projections (self.projection == ``cyl``,
        ``cea``, ``mill``, ``gall`` or ``merc``)
        the inverse transformation will return longitudes between
        self.llcrnrlon and self.llcrnrlat.

        Input arguments lon, lat can be either scalar floats,
        sequences, or numpy arrays.
        """
        if self.celestial:
            # don't assume center of map is at greenwich
            # (only relevant for cyl or pseudo-cyl projections)
            if self.projection in _pseudocyl or self.projection in _cylproj:
                lon_0=self.projparams['lon_0']
            else:
                lon_0 = 0.
        if self.celestial and not inverse:
            try:
                x = 2.*lon_0-x
            except TypeError:
                x = [2*lon_0-xx for xx in x]
        if self.projection == 'rotpole' and inverse:
            try:
                x = _dg2rad*x
            except TypeError:
                x = [_dg2rad*xx for xx in x]
            try:
                y = _dg2rad*y
            except TypeError:
                y = [_dg2rad*yy for yy in y]
        xout,yout = self.projtran(x,y,inverse=inverse)
        if self.celestial and inverse:
            try:
                xout = -2.*lon_0-xout
            except:
                xout = [-2.*lon_0-xx for xx in xout]
        if self.projection == 'rotpole' and not inverse:
            try:
                xout = _rad2dg*xout
                xout = np.where(xout < 0., xout+360, xout)
            except TypeError:
                xout = [_rad2dg*xx for xx in xout]
                xout = [xx+360. if xx < 0 else xx for xx in xout]
            try:
                yout = _rad2dg*yout
            except TypeError:
                yout = [_rad2dg*yy for yy in yout]
        return xout,yout

    def makegrid(self,nx,ny,returnxy=False):
        """
        return arrays of shape (ny,nx) containing lon,lat coordinates of
        an equally spaced native projection grid.

        If ``returnxy = True``, the x,y values of the grid are returned also.
        """
        return self.projtran.makegrid(nx,ny,returnxy=returnxy)

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

### End of Basemap class

def _searchlist(a,x):
    """
    like bisect, but works for lists that are not sorted,
    and are not in increasing order.
    returns -1 if x does not fall between any two elements"""
    # make sure x is a float (and not an array scalar)
    x = float(x)
    itemprev = a[0]
    nslot = -1
    eps = 180.
    for n,item in enumerate(a[1:]):
        if item < itemprev:
            if itemprev-item>eps:
                if ((x>itemprev and x<=360.) or (x<item and x>=0.)):
                    nslot = n+1
                    break
            elif x <= itemprev and x > item and itemprev:
                nslot = n+1
                break
        else:
            if item-itemprev>eps:
                if ((x<itemprev and x>=0.) or (x>item and x<=360.)):
                    nslot = n+1
                    break
            elif x >= itemprev and x < item:
                nslot = n+1
                break
        itemprev = item
    return nslot

def interp(datain,xin,yin,xout,yout,checkbounds=False,masked=False,order=1):
    """
    Interpolate data (``datain``) on a rectilinear grid (with x = ``xin``
    y = ``yin``) to a grid with x = ``xout``, y= ``yout``.

    .. tabularcolumns:: |l|L|

    ==============   ====================================================
    Arguments        Description
    ==============   ====================================================
    datain           a rank-2 array with 1st dimension corresponding to
                     y, 2nd dimension x.
    xin, yin         rank-1 arrays containing x and y of
                     datain grid in increasing order.
    xout, yout       rank-2 arrays containing x and y of desired output grid.
    ==============   ====================================================

    .. tabularcolumns:: |l|L|

    ==============   ====================================================
    Keywords         Description
    ==============   ====================================================
    checkbounds      If True, values of xout and yout are checked to see
                     that they lie within the range specified by xin
                     and xin.
                     If False, and xout,yout are outside xin,yin,
                     interpolated values will be clipped to values on
                     boundary of input grid (xin,yin)
                     Default is False.
    masked           If True, points outside the range of xin and yin
                     are masked (in a masked array).
                     If masked is set to a number, then
                     points outside the range of xin and yin will be
                     set to that number. Default False.
    order            0 for nearest-neighbor interpolation, 1 for
                     bilinear interpolation, 3 for cublic spline
                     (default 1). order=3 requires scipy.ndimage.
    ==============   ====================================================

    .. note::
     If datain is a masked array and order=1 (bilinear interpolation) is
     used, elements of dataout will be masked if any of the four surrounding
     points in datain are masked.  To avoid this, do the interpolation in two
     passes, first with order=1 (producing dataout1), then with order=0
     (producing dataout2).  Then replace all the masked values in dataout1
     with the corresponding elements in dataout2 (using numpy.where).
     This effectively uses nearest neighbor interpolation if any of the
     four surrounding points in datain are masked, and bilinear interpolation
     otherwise.

    Returns ``dataout``, the interpolated data on the grid ``xout, yout``.
    """
    # xin and yin must be monotonically increasing.
    if xin[-1]-xin[0] < 0 or yin[-1]-yin[0] < 0:
        raise ValueError('xin and yin must be increasing!')
    if xout.shape != yout.shape:
        raise ValueError('xout and yout must have same shape!')
    # check that xout,yout are
    # within region defined by xin,yin.
    if checkbounds:
        if xout.min() < xin.min() or \
           xout.max() > xin.max() or \
           yout.min() < yin.min() or \
           yout.max() > yin.max():
            raise ValueError('yout or xout outside range of yin or xin')
    # compute grid coordinates of output grid.
    delx = xin[1:]-xin[0:-1]
    dely = yin[1:]-yin[0:-1]
    if max(delx)-min(delx) < 1.e-4 and max(dely)-min(dely) < 1.e-4:
        # regular input grid.
        xcoords = (len(xin)-1)*(xout-xin[0])/(xin[-1]-xin[0])
        ycoords = (len(yin)-1)*(yout-yin[0])/(yin[-1]-yin[0])
    else:
        # irregular (but still rectilinear) input grid.
        xoutflat = xout.flatten(); youtflat = yout.flatten()
        ix = (np.searchsorted(xin,xoutflat)-1).tolist()
        iy = (np.searchsorted(yin,youtflat)-1).tolist()
        xoutflat = xoutflat.tolist(); xin = xin.tolist()
        youtflat = youtflat.tolist(); yin = yin.tolist()
        xcoords = []; ycoords = []
        for n,i in enumerate(ix):
            if i < 0:
                xcoords.append(-1) # outside of range on xin (lower end)
            elif i >= len(xin)-1:
                xcoords.append(len(xin)) # outside range on upper end.
            else:
                xcoords.append(float(i)+(xoutflat[n]-xin[i])/(xin[i+1]-xin[i]))
        for m,j in enumerate(iy):
            if j < 0:
                ycoords.append(-1) # outside of range of yin (on lower end)
            elif j >= len(yin)-1:
                ycoords.append(len(yin)) # outside range on upper end
            else:
                ycoords.append(float(j)+(youtflat[m]-yin[j])/(yin[j+1]-yin[j]))
        xcoords = np.reshape(xcoords,xout.shape)
        ycoords = np.reshape(ycoords,yout.shape)
    # data outside range xin,yin will be clipped to
    # values on boundary.
    if masked:
        xmask = np.logical_or(np.less(xcoords,0),np.greater(xcoords,len(xin)-1))
        ymask = np.logical_or(np.less(ycoords,0),np.greater(ycoords,len(yin)-1))
        xymask = np.logical_or(xmask,ymask)
    xcoords = np.clip(xcoords,0,len(xin)-1)
    ycoords = np.clip(ycoords,0,len(yin)-1)
    # interpolate to output grid using bilinear interpolation.
    if order == 1:
        xi = xcoords.astype(np.int32)
        yi = ycoords.astype(np.int32)
        xip1 = xi+1
        yip1 = yi+1
        xip1 = np.clip(xip1,0,len(xin)-1)
        yip1 = np.clip(yip1,0,len(yin)-1)
        delx = xcoords-xi.astype(np.float32)
        dely = ycoords-yi.astype(np.float32)
        dataout = (1.-delx)*(1.-dely)*datain[yi,xi] + \
                  delx*dely*datain[yip1,xip1] + \
                  (1.-delx)*dely*datain[yip1,xi] + \
                  delx*(1.-dely)*datain[yi,xip1]
    elif order == 0:
        xcoordsi = np.around(xcoords).astype(np.int32)
        ycoordsi = np.around(ycoords).astype(np.int32)
        dataout = datain[ycoordsi,xcoordsi]
    elif order == 3:
        try:
            from scipy.ndimage import map_coordinates
        except ImportError:
            raise ValueError('scipy.ndimage must be installed if order=3')
        coords = [ycoords,xcoords]
        dataout = map_coordinates(datain,coords,order=3,mode='nearest')
    else:
        raise ValueError('order keyword must be 0, 1 or 3')
    if masked:
        newmask = ma.mask_or(ma.getmask(dataout), xymask)
        dataout = ma.masked_array(dataout, mask=newmask)
        if not isinstance(masked, bool):
            dataout = dataout.filled(masked)
    return dataout

def shiftgrid(lon0,datain,lonsin,start=True,cyclic=360.0):
    """
    Shift global lat/lon grid east or west.

    .. tabularcolumns:: |l|L|

    ==============   ====================================================
    Arguments        Description
    ==============   ====================================================
    lon0             starting longitude for shifted grid
                     (ending longitude if start=False). lon0 must be on
                     input grid (within the range of lonsin).
    datain           original data with longitude the right-most
                     dimension.
    lonsin           original longitudes.
    ==============   ====================================================

    .. tabularcolumns:: |l|L|

    ==============   ====================================================
    Keywords         Description
    ==============   ====================================================
    start            if True, lon0 represents the starting longitude
                     of the new grid. if False, lon0 is the ending
                     longitude. Default True.
    cyclic           width of periodic domain (default 360)
    ==============   ====================================================

    returns ``dataout,lonsout`` (data and longitudes on shifted grid).
    """
    if np.fabs(lonsin[-1]-lonsin[0]-cyclic) > 1.e-4:
        # Use all data instead of raise ValueError, 'cyclic point not included'
        start_idx = 0
    else:
        # If cyclic, remove the duplicate point
        start_idx = 1
    if lon0 < lonsin[0] or lon0 > lonsin[-1]:
        raise ValueError('lon0 outside of range of lonsin')
    i0 = np.argmin(np.fabs(lonsin-lon0))
    i0_shift = len(lonsin)-i0
    if ma.isMA(datain):
        dataout  = ma.zeros(datain.shape,datain.dtype)
    else:
        dataout  = np.zeros(datain.shape,datain.dtype)
    if ma.isMA(lonsin):
        lonsout = ma.zeros(lonsin.shape,lonsin.dtype)
    else:
        lonsout = np.zeros(lonsin.shape,lonsin.dtype)
    if start:
        lonsout[0:i0_shift] = lonsin[i0:]
    else:
        lonsout[0:i0_shift] = lonsin[i0:]-cyclic
    dataout[...,0:i0_shift] = datain[...,i0:]
    if start:
        lonsout[i0_shift:] = lonsin[start_idx:i0+start_idx]+cyclic
    else:
        lonsout[i0_shift:] = lonsin[start_idx:i0+start_idx]
    dataout[...,i0_shift:] = datain[...,start_idx:i0+start_idx]
    return dataout,lonsout

def addcyclic(*arr,**kwargs):
    """
    Adds cyclic (wraparound) points in longitude to one or several arrays,
    the last array being longitudes in degrees. e.g.

   ``data1out, data2out, lonsout = addcyclic(data1,data2,lons)``

    ==============   ====================================================
    Keywords         Description
    ==============   ====================================================
    axis             the dimension representing longitude (default -1,
                     or right-most)
    cyclic           width of periodic domain (default 360)
    ==============   ====================================================
    """
    # get (default) keyword arguments
    axis = kwargs.get('axis',-1)
    cyclic = kwargs.get('cyclic',360)
    # define functions
    def _addcyclic(a):
        """addcyclic function for a single data array"""
        npsel = np.ma if np.ma.is_masked(a) else np
        slicer = [slice(None)] * np.ndim(a)
        try:
            slicer[axis] = slice(0, 1)
        except IndexError:
            raise ValueError('The specified axis does not correspond to an '
                    'array dimension.')
        return npsel.concatenate((a,a[slicer]),axis=axis)
    def _addcyclic_lon(a):
        """addcyclic function for a single longitude array"""
        # select the right numpy functions
        npsel = np.ma if np.ma.is_masked(a) else np
        # get cyclic longitudes
        clon = (np.take(a,[0],axis=axis)
                + cyclic * np.sign(np.diff(np.take(a,[0,-1],axis=axis),axis=axis)))
        # ensure the values do not exceed cyclic
        clonmod = npsel.where(clon<=cyclic,clon,np.mod(clon,cyclic))
        return npsel.concatenate((a,clonmod),axis=axis)
    # process array(s)
    if len(arr) == 1:
        return _addcyclic_lon(arr[-1])
    else:
        return list(map(_addcyclic,arr[:-1]) + [_addcyclic_lon(arr[-1])])

def _choosecorners(width,height,**kwargs):
    """
    private function to determine lat/lon values of projection region corners,
    given width and height of projection region in meters.
    """
    p = pyproj.Proj(kwargs)
    urcrnrlon, urcrnrlat = p(0.5*width,0.5*height, inverse=True)
    llcrnrlon, llcrnrlat = p(-0.5*width,-0.5*height, inverse=True)
    corners = llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat
    # test for invalid projection points on output
    if llcrnrlon > 1.e20 or urcrnrlon > 1.e20:
        raise ValueError('width and/or height too large for this projection, try smaller values')
    else:
        return corners

def _choosecornersllur(llcrnrx, llcrnry, urcrnrx, urcrnry,**kwargs):
    """
    private function to determine lat/lon values of projection region corners,
    given width and height of projection region in meters.
    """
    p = pyproj.Proj(kwargs)
    urcrnrlon, urcrnrlat = p(urcrnrx, urcrnry, inverse=True)
    llcrnrlon, llcrnrlat = p(llcrnrx, llcrnry, inverse=True)
    corners = llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat
    # test for invalid projection points on output
    if llcrnrlon > 1.e20 or urcrnrlon > 1.e20:
        raise ValueError('width and/or height too large for this projection, try smaller values')
    else:
        return corners


class _dict(dict):
    # override __delitem__ to first call remove method on values.
    def __delitem__(self,key):
        self[key].remove()
        super(_dict, self).__delitem__(key)