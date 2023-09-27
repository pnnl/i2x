# Copyright (C) 2023 Battelle Memorial Institute
# file: report.py
"""Generating a sample geospatial data report for i2X.
"""

import os
import requests
import urllib.parse
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt 

plt.rcParams['savefig.directory'] = os.getcwd()

# load the processed DataHub data
def get_qu ():
  fname = '../hubdata/output/queued_up.csv'
  df = pd.read_csv(fname)
  # df.info()
  retained_columns = ['lat', 'lon']
  for tag in ['withdrawn', 'operational', 'active', 'suspended']:
    for quant in ['mw', 'proj_count']:
      solar_col = '{:s}_Solar_{:s}'.format (quant, tag)
      wind_col = '{:s}_Wind_{:s}'.format (quant, tag)
      new_col = '{:s}_RE_{:s}'.format (quant, tag)
      retained_columns.append (new_col)
      df[new_col] = df[solar_col] + df[wind_col]
  df_new = df[retained_columns].copy()
  print ('\n\nReduced-order QU GeoDataFrame Info:')
  gdf = gpd.GeoDataFrame (data=df_new, geometry=gpd.points_from_xy(df.lon, df.lat))
  gdf.info()
  print (gdf)
  return gdf

def get_st ():
  fname = '../hubdata/output/solarTRACE.csv'
  df = pd.read_csv(fname)
  # df.info()
  retained_columns = ['lat', 'lon']
  aggregates = {
    'Total10kW': [16, 17, 18, 19, 20], # column numbers from df.info(), 15 and 37 not included
    'Total50kW': [21, 22, 23, 24, 25],
    'Weight10kW': [6, 7, 8, 9],
    'Weight50kW': [10, 11, 12, 13, 14],
    'Weight.1.10kW': [28, 29, 30, 31],
    'Weight.1.50kW': [32, 33, 34, 35, 36]
  }
  for key, row in aggregates.items():
    retained_columns.append (key)
    df[key] = df.iloc[:,row[0]]
    for i in range (1, len(row)):
      df[key] += df.iloc[:, row[i]]
  df_new = df[retained_columns].copy()
  print ('\n\nReduced-order ST GeoDataFrame Info:')
  gdf = gpd.GeoDataFrame (data=df_new, geometry=gpd.points_from_xy(df.lon, df.lat))
  gdf.info()
  print (gdf)
  return gdf

# example from https://gis.stackexchange.com/questions/427434/query-feature-service-on-esri-arcgis-rest-api-with-python-requests
def test ():
  print ('Entered test function, rquesting data...')
  url_base = r'https://dpw.gis.lacounty.gov/dpw/rest/services/PW_Open_Data/MapServer/22/query?'
  params = {
    'geometry': '-118.21637221791077, 34.094916196179504',
    'geometryType': 'esriGeometryPoint',
    'inSR': '4326',
    'distance': '10000', 
    'units': 'esriSRUnit_Meter', 
    'returnGeometry': 'true', 
    'outFields': 'OBJECTID,DIVISION,FACILITY_N,ADDRESS,CITY', 
    'f': 'pjson'
    }
  url_final = url_base + urllib.parse.urlencode(params)
  response = requests.get(url=url_final)
  print ('  returned from data request.')
  data = response.text
  # print ('\n\nJSON result:\n\n', data)
  gdf_temp = gpd.read_file(data)
  print ('\n\nGEOPANDAS result:\n\n', gdf_temp)

if __name__ == '__main__':
  #test()
  df_qu = get_qu()
  df_st = get_st()
