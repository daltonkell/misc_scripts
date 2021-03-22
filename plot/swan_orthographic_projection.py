# -*- coding: utf-8 -*-
#!/usr/bin/env python

import matplotlib
matplotlib.use('Agg')

import cartopy
from cartopy.feature import NaturalEarthFeature
import matplotlib.cm
import matplotlib.pyplot as plt
import netCDF4
import numpy as np
import pyproj
import sys

LON_0 = 54.
LAT_0 = 25.

# warning colormap
from matplotlib.colors import ListedColormap
matplotlib.cm.register_cmap(name='warning', cmap=ListedColormap(['#67ff53', '#ffd752', '#ed373c']))

with netCDF4.Dataset(sys.argv[1]) as nc:

    lon = nc.variables['lon'][:]
    lat = nc.variables['lat'][:]
    ele = nc.variables['ele'][:]

    coastline = NaturalEarthFeature(category='physical', name='coastline',               scale='10m', facecolor='none',    edgecolor='lightslategrey', linewidth=0.3)
    states    = NaturalEarthFeature(category='cultural', name='admin_0_countries_lakes', scale='10m', facecolor='#dcdcdc', edgecolor='dimgrey',        linewidth=0.2)

    for t in range(nc.variables['time'].size):

        LON_0 = -24+t

        pORTHO = pyproj.Proj('+proj=ortho +lon_0={} +lat_0={} +ellps=WGS84'.format(LON_0, LAT_0))
        lo,la  = pORTHO(lon, lat)
        cORTHO = cartopy.crs.Orthographic(central_longitude=LON_0, central_latitude=LAT_0)

        hs = np.ma.masked_equal(nc.variables['HSIGN'][t,:], -9.)

        # image size/resolution
        height = 512
        width = 512
        dpi = 256

        ax = plt.axes(projection=cORTHO)
        fig = plt.gcf()

        ax.outline_patch.set_linewidth(0.2)

        # coastline/states
        ax.add_feature(coastline)
        ax.add_feature(states)

        # color scale
        cmin = 0.5
        cmax = 1.5
        nlvls = 200
        lvls = np.linspace(cmin, cmax, nlvls)

        # -- pcolor
        pcolor = ax.tripcolor(lo, la, ele, hs, vmin=cmin, vmax=cmax, cmap='warning', edgecolor='#999999', lw=0.02)

        ax.set_global()

        # remove some plot stuff
        ax.set_axis_off()
        ax.set_frame_on(False)
        ax.set_clip_on(False)
        ax.set_position([0, 0, 1, 1])

        filename = 'orthographic_%03d.png' % t
        fig.savefig(filename, dpi=dpi, transparent=False)

        plt.close(fig)
