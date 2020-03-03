#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Use this script to generate geospatial extent metadata and suggested keywords.

usage: get_geo_attrs.py [-h] [--k] dataset

positional arguments:
  dataset     dataset to get extents for; must be .nc or OPeNDAP

optional arguments:
  -h, --help  show this help message and exit
  --k         don't print auto-generated keywords

"""

import argparse
import json
import netCDF4
import numpy as np
import os
from compliance_checker.cf import util

def get_geo_extents(nc, possible_units, std_name, axis_name, short_name):
    """
    Get the geospatial extents for a NetCDF file, if available.

    Args:
        nc (netCDF4.Dataset)  : open Dataset
        possible_units (tuple): possible unit names for the extent
        std_name (str)        : standard name of the extent
        axis_name (str)       : name of the axis the extent maps to
        short_name (str)      : abbreviated name of the extent

    Returns:
        None
    """

    geo_extent_vars = {}
    geo_extent_units = []

    # variables must have units
    for var in nc.get_variables_by_attributes(units=lambda x: x is not None):
    
        geo_extent_vars[var.name] = 0
        # units in this set
        if var.units in possible_units:
            geo_extent_vars[var.name] += 1
            geo_extent_units.append(var.units)
    

        # standard name
        if hasattr(var, 'standard_name') and var.standard_name == std_name:
            geo_extent_vars[var.name] += 1
            geo_extent_units.append(var.units)
    
        # axis of "X"
        if hasattr(var, 'axis') and var.axis == axis_name:
            geo_extent_vars[var.name] += 1
            geo_extent_units.append(var.units)
    

        if var.name == std_name or var.name == short_name:
            geo_extent_vars[var.name] += 1
            geo_extent_units.append(var.units)

    if len(geo_extent_vars) == 0:
        return

    # filter out any zero scores
    geo_extent_vars = dict(filter(lambda x: x[1]>0, geo_extent_vars.items()))

    # sort by criteria passed
    final_geo_vars = sorted(geo_extent_vars, key=lambda x: geo_extent_vars[x], reverse=True)

    obs_mins = [np.nanmin(nc.variables[var]) for var in final_geo_vars if not np.isnan(nc.variables[var]).all()]
    obs_maxs = [np.nanmax(nc.variables[var]) for var in final_geo_vars if not np.isnan(nc.variables[var]).all()]

    # Let's just pick one
    geo_vals = nc.variables[final_geo_vars[0][:]]
    if geo_vals.size == 1:
        obs_res = [0.0]
    else:
        obs_res = [np.nanmean(np.diff(nc.variables[var])) for var in final_geo_vars if not np.isnan(nc.variables[var]).all()]

    geo_min = round(float(min(obs_mins)), 5)
    geo_max = round(float(max(obs_maxs)), 5)
    geo_extent_units = [nc.variables[k].units for k, v in geo_extent_vars.items()][0]
    geo_res = "{} {}".format(round(float(abs(np.mean(obs_res))), 5), geo_extent_units)

    print('<attribute name="geospatial_{}_min" value="{}" />'.format(short_name, geo_min))
    print('<attribute name="geospatial_{}_max" value="{}" />'.format(short_name, geo_max))
    print('<attribute name="geospatial_{}_resolution" value="{}" />'.format(short_name, geo_res))
    print('<attribute name="geospatial_{}_units" value="{}" />'.format(short_name, geo_extent_units))

def main(fpath, kwds=True):
    """
    Main function to get geospatial extent metadata.

    Args:
        fpath (str): path to NetCDF dataset (can be OPeNDAP)
        kwds (bool): print out suggested keywords; default True

    Returns:
        None
    """

    gcmd_keywords_path = os.path.join(os.path.dirname(__file__), 'gcmd_contents.json')
    suggested_keywords = {'suggested_keywords': []}

    with open(gcmd_keywords_path) as fp:
        gcmd_keywords = json.load(fp)
        fp.close()

    with netCDF4.Dataset(fpath) as nc:
        # Add GCMD keywords
        for cf_var in nc.variables:
            cf_var = nc.variables[cf_var]
            standard_name = getattr(cf_var, 'standard_name', None)
            if standard_name is None:
                continue
            if standard_name in gcmd_keywords:
                for keyword in gcmd_keywords[standard_name]:
                    if keyword:
                        suggested_keywords['suggested_keywords'].append(keyword)

        # Add cf standard names
        standard_name_table = util.StandardNameTable()
        for cf_var in nc.variables:
            cf_var = nc.variables[cf_var]
            standard_name = getattr(cf_var, 'standard_name', None)
            if standard_name is None:
                continue
            if standard_name in ['time', 'latitude', 'longitude']:
                continue
            if standard_name in standard_name_table:
                suggested_keywords['suggested_keywords'].append(standard_name)

        # make dict to unpack in the get_geo_extents() function
        geo_cfg = {
            "lat": {
                "possible_units": (
                    'degrees_east',
                    'degree_east',
                    'degrees_E',
                    'degree_E',
                    'degreesE',
                    'degreeE'
                ),
                "std_name": "latitude",
                "axis_name": "X",
                "short_name": "lat"
            },

            "lon": {
                "possible_units": (
                    'degrees_north',
                    'degree_north',
                    'degrees_N',
                    'degree_N',
                    'degreesN',
                    'degreeN'
                ),
                "std_name": "longitude",
                "axis_name": "Y",
                "short_name": "lon"

            }
        }

        # print
        for g in geo_cfg.values():
            get_geo_extents(nc, **g)

        if kwds:
            print(','.join(suggested_keywords['suggested_keywords']))

    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", help="dataset to get extents for; must be .nc or OPeNDAP")
    parser.add_argument("--k", help="don't print auto-generated keywords", action="store_false")
    args = parser.parse_args()
    main(args.dataset, args.k)
