# Copyright (C) 2023 Battelle Memorial Institute
# file: make_i2x_gdfs.py
"""Create SolarTRACE and Queued Up GeoDataFrames on disk.

Reads existing CSV files from ../hubdata/output
Output used by report.py and bes_report.py
"""

import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt 

plt.rcParams['savefig.directory'] = os.getcwd()

# load the processed DataHub data, column names limited to 10 characters for SHP file saving
def short_qu_column_name (tag, quant):
  short_tag = tag[0:2].upper()
  if quant == 'mw':
    short_quant = 'MW'
  else:
    short_quant = 'N'
  return '{:s}_RE_{:s}'.format (short_quant, short_tag)

def get_qu (bLog=False):
  fname = '../hubdata/output/queued_up.csv'
  df = pd.read_csv(fname)
  if bLog:
    df.info()
  retained_columns = ['lat', 'lon']
  for tag in ['withdrawn', 'operational', 'active', 'suspended']:
    for quant in ['mw', 'proj_count']:
      solar_col = '{:s}_Solar_{:s}'.format (quant, tag)
      wind_col = '{:s}_Wind_{:s}'.format (quant, tag)
      new_col = short_qu_column_name (tag, quant)
      retained_columns.append (new_col)
      df[new_col] = df[solar_col] + df[wind_col]
  df_new = df[retained_columns].copy()
  gdf = gpd.GeoDataFrame (data=df_new, geometry=gpd.points_from_xy(df.lon, df.lat))
  if bLog:
    print ('\n\nReduced-order QU GeoDataFrame Info:')
    gdf.info()
    print (gdf)
  return gdf

def get_st (bLog=False):
  fname = '../hubdata/output/solarTRACE.csv'
  df = pd.read_csv(fname)
  if bLog:
    df.info()
  retained_columns = ['lat', 'lon']
  aggregates = {
    'Tot10kW': [16, 17, 18, 19, 20], # column numbers from df.info(), 15 and 37 not included
    'Tot50kW': [21, 22, 23, 24, 25],
    'Wt10kW': [6, 7, 8, 9],
    'Wt50kW': [10, 11, 12, 13, 14],
    'Wt.1.10kW': [28, 29, 30, 31],
    'Wt.1.50kW': [32, 33, 34, 35, 36]
  }
  for key, row in aggregates.items():
    retained_columns.append (key)
    df[key] = df.iloc[:,row[0]]
    for i in range (1, len(row)):
      df[key] += df.iloc[:, row[i]]
  df_new = df[retained_columns].copy()
  gdf = gpd.GeoDataFrame (data=df_new, geometry=gpd.points_from_xy(df.lon, df.lat))
  if bLog:
    print ('\n\nReduced-order ST GeoDataFrame Info:')
    gdf.info()
    print (gdf)
  return gdf

def show_plot (gdf, title):
  gdf.plot()
  plt.title(title + ' ({:d} rows)'.format (len(gdf)))
  plt.ylabel('Latitude [deg]')
  plt.xlabel('Longitude [deg]')
  plt.show()
  plt.close()

if __name__ == '__main__':
  gdf_qu = get_qu (bLog=True)
  gdf_st = get_st (bLog=True)
  gdf_qu.to_file ('gdf_qu.shp')
  gdf_st.to_file ('gdf_st.shp')

  show_plot (gdf_st, 'SolarTRACE Coverage')
  show_plot (gdf_qu, 'Queued Up Coverage')

