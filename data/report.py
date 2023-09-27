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

# From https://services7.arcgis.com/F8VN7MYN9lP1oiiV/ArcGIS/rest/services/North_West_Block_Groups_V3/FeatureServer/0
# Type: Feature Layer
# Geometry Type: esriGeometryPolygon
# Min. Scale: 18489298
# Max. Scale: 2256
# Default Visibility: true
# Max Record Count: 2000
# Supported query Formats: JSON
# Use Standardized Queries: True
# Extent:
#   XMin: -13889634.2777885
#   YMin: 5011571.30170265
#   XMax: -11581646.8758166
#   YMax: 6275276.54303364
#   Spatial Reference: 102100 (3857)
# Fields:
#   FID (type: esriFieldTypeOID, alias: FID, SQL Type: sqlTypeInteger, length: 0, nullable: false, editable: false)
#   GEOID (type: esriFieldTypeString, alias: GEOID, SQL Type: sqlTypeNVarchar, length: 80, nullable: true, editable: true)
#   POP (type: esriFieldTypeDouble, alias: POP, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   WHITE (type: esriFieldTypeDouble, alias: WHITE, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   BLACK (type: esriFieldTypeDouble, alias: BLACK, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   NATAM (type: esriFieldTypeDouble, alias: NATAM, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   ASIAN (type: esriFieldTypeDouble, alias: ASIAN, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   ISLANDER (type: esriFieldTypeDouble, alias: ISLANDER, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   OTHER (type: esriFieldTypeDouble, alias: OTHER, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   MULTI (type: esriFieldTypeDouble, alias: MULTI, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   LATINX (type: esriFieldTypeDouble, alias: LATINX, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   F_BLK (type: esriFieldTypeDouble, alias: F_BLK, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   F_IND (type: esriFieldTypeDouble, alias: F_IND, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   F_ASN (type: esriFieldTypeDouble, alias: F_ASN, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   F_ISL (type: esriFieldTypeDouble, alias: F_ISL, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   F_OTH (type: esriFieldTypeDouble, alias: F_OTH, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   F_MLT (type: esriFieldTypeDouble, alias: F_MLT, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   F_LAT (type: esriFieldTypeDouble, alias: F_LAT, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   F_POC (type: esriFieldTypeDouble, alias: F_POC, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   QPOC (type: esriFieldTypeDouble, alias: QPOC, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   LOWINC (type: esriFieldTypeDouble, alias: LOWINC, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   QPOV (type: esriFieldTypeDouble, alias: QPOV, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   F_LEP (type: esriFieldTypeDouble, alias: F_LEP, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   QLEP (type: esriFieldTypeDouble, alias: QLEP, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   FDIS (type: esriFieldTypeDouble, alias: FDIS, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   QDIS (type: esriFieldTypeDouble, alias: QDIS, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   FCHILD (type: esriFieldTypeDouble, alias: FCHILD, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   FELDER (type: esriFieldTypeDouble, alias: FELDER, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   QCHILD (type: esriFieldTypeDouble, alias: QCHILD, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   QELDER (type: esriFieldTypeDouble, alias: QELDER, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   F_SNAP (type: esriFieldTypeDouble, alias: F_SNAP, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   QSNAP (type: esriFieldTypeDouble, alias: QSNAP, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   F_COV (type: esriFieldTypeDouble, alias: F_COV, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   QCOV (type: esriFieldTypeDouble, alias: QCOV, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   F_WEB (type: esriFieldTypeDouble, alias: F_WEB, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   QWEB (type: esriFieldTypeDouble, alias: QWEB, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   FLAGS (type: esriFieldTypeDouble, alias: FLAGS, SQL Type: sqlTypeFloat, nullable: true, editable: true)
#   Shape__Area (type: esriFieldTypeDouble, alias: Shape__Area, SQL Type: sqlTypeFloat, nullable: true, editable: false)
#   Shape__Length (type: esriFieldTypeDouble, alias: Shape__Length, SQL Type: sqlTypeFloat, nullable: true, editable: false)

def get_block_groups (lon=-122.33, lat=47.61, bLog=False): # default is Seattle
  if bLog:
    print ('Entered block groups function, requesting data...')
  #url_base = r'https://services7.arcgis.com/F8VN7MYN9lP1oiiV/ArcGIS/rest/services/North_West_Block_Groups_V3/FeatureServer/0/query?'
  # Denver
  lat = 39.739
  lon = -104.990
  # Dallas
# lat = 32.777
# lon = -96.797
# # Houston
# lat = 29.7604
# lon = -95.3698
# # Phoenix
# lat = 33.4484
# lon = -112.0740
  url_base = r'https://services7.arcgis.com/F8VN7MYN9lP1oiiV/arcgis/rest/services/South_West_Block_Groups_V3/FeatureServer/0/query?'
  params = {
    'geometry': '{:.3f}, {:.3f}'.format (lon, lat),  
    'geometryType': 'esriGeometryPoint',
    'inSR': '4326',
    'outSR': '4326',
    'distance': '100000', # about 60 miles?
    'units': 'esriSRUnit_Meter', 
    'returnGeometry': 'true', 
    'outFields': 'POP,WHITE,BLACK,NATAM,ASIAN,ISLANDER,OTHER,MULTI,LATINX,LOWINC', 
    'f': 'pjson'
    }
  url_final = url_base + urllib.parse.urlencode(params)
  response = requests.get(url=url_final)
  if bLog:
    print ('  returned from data request.')
  data = response.text
  # print ('\n\nJSON result:\n\n', data)
  gdf = gpd.read_file(data)
  if bLog:
    print ('\n\nBlock Group GeoDataFrame result:\n\n', gdf)
  return gdf

def show_plot (gdf, title):
  gdf.plot()
  plt.title(title)
  plt.ylabel('Latitude [deg]')
  plt.xlabel('Longitude [deg]')
  plt.show()
  plt.close()

def overlay_plot (gdf_bg, gdf_st, gdf_qu):
  f, ax = plt.subplots()
  plt.title('SolarTrace Centroids in the Block Group Footprint')
  gdf_bg.plot(ax=ax)
  gdf_st.plot(ax=ax, color='red')
  gdf_qu.plot(ax=ax, color='yellow') # there are none for Denver
  plt.ylabel('Latitude [deg]')
  plt.xlabel('Longitude [deg]')
  plt.show()
  plt.close()

def plot_der_results (df):
  f, ax = plt.subplots()
  plt.title('SolarTrace Correlations')
  plt.xlabel('White Population [%]')
  plt.ylabel('Total Projects')
  x = 100.0 * df['p_white']
  ax.scatter (x, df['Tot10kW'], c='red', label='0-10 kW')
  ax.scatter (x, df['Tot50kW'], c='blue', label='11-50 kW')
  ax.legend()
  ax.grid()
  plt.show()
  plt.close()

if __name__ == '__main__':
  #test()
  if False: # build and save GeoDataFrames
    gdf_qu = get_qu (bLog=True)
    gdf_st = get_st (bLog=True)
    gdf_bg = get_block_groups (bLog=True)
    gdf_qu.to_file ('gdf_qu.shp')
    gdf_st.to_file ('gdf_st.shp')
    gdf_bg.to_file ('gdf_bg.shp')
  else: # read the local GeoDataFrames
    gdf_qu = gpd.read_file ('gdf_qu.shp')
    print ('\n\nLoaded QU GeoDataFrame: crs={:s}\n'.format (str(gdf_qu.crs)), gdf_qu)
    gdf_st = gpd.read_file ('gdf_st.shp')
    print ('\n\nLoaded ST GeoDataFrame: crs={:s}\n'.format (str(gdf_st.crs)), gdf_st)
    gdf_bg = gpd.read_file ('gdf_bg.shp')
    print ('\n\nLoaded Block Group GeoDataFrame: crs={:s}\n'.format (str(gdf_bg.crs)), gdf_bg)
  if False:
    show_plot (gdf_bg, 'Block Group Coverage')
    show_plot (gdf_st, 'SolarTRACE Coverage')
    show_plot (gdf_qu, 'Queued Up Coverage')

  gdf_st = gdf_st.clip (gdf_bg)
  gdf_qu = gdf_qu.clip (gdf_bg)
  print ('{:d} block groups include {:d} SolarTRACE and {:d} Queued Up Centroids'.format (len(gdf_bg), len(gdf_st), len(gdf_qu)))
  #overlay_plot (gdf_bg, gdf_st, gdf_qu)

  d_der = {}
  der_fields = ['Tot10kW', 'Tot50kW', 'Wt10kW', 'Wt50kW', 'Wt.1.10kW', 'Wt.1.50kW']
  d_bes = {}
  bes_fields = ['MW_RE_WI', 'N_RE_WI', 'MW_RE_OP', 'N_RE_OP', 'MW_RE_AC', 'N_RE_AC', 'MW_RE_SU', 'N_RE_SU']
  min_p_white = 2.0
  max_p_lowinc = 0.0
  for idx, bg in gdf_bg.iterrows():
    if idx % 200 == 0:
      print ('processing block group {:d}'.format (idx))
    pop = bg['POP']
    p_white = bg['WHITE'] / pop
    p_lowinc = bg['LOWINC'] / pop
    if p_white < min_p_white:
      min_p_white = p_white
    if p_lowinc > max_p_lowinc:
      max_p_lowinc = p_lowinc
    for j, st in gdf_st.iterrows():
      if bg['geometry'].contains (st['geometry']):
        if idx not in d_der:
          d_der[idx] = {'p_white':p_white, 'p_lowinc': p_lowinc, 'n':0}
          for field in der_fields:
            d_der[idx][field] = 0.0
        d_der[idx]['n'] += 1
        for field in der_fields:
          d_der[idx][field] += st[field]
    for j, qu in gdf_qu.iterrows():
      if bg['geometry'].contains (qu['geometry']):
        if idx not in d_bes:
          d_bes[idx] = {'p_white':p_white, 'p_lowinc': p_lowinc, 'n':0}
          for field in bes_fields:
            d_bes[idx][field] = 0.0
        d_bes[idx]['n'] += 1
        for field in bes_fields:
          d_bes[idx][field] += qu[field]

  print ('Minimum white population = {:.2f}%, Maximum low-income population = {:.2f}%'.format (100.0*min_p_white, 100.0*max_p_lowinc))
  print ('{:d} block groups have SolarTRACE Data'.format (len(d_der)))
# for key, row in d_der.items():
#   print ('  ', key, row)
  print ('{:d} block groups with Queued Up Data'.format (len(d_bes)))
# for key, row in d_bes.items():
#   print ('  ', key, row)

  df = pd.DataFrame.from_dict (d_der, orient='index')
  print (df)
  print (df.corr())
  plot_der_results (df)

  # For a DER report, loop through each block group and build a dataframe for analysis
  #   1) find the ST centroids within this block group
  #   2) sum the contained ST columns, i.e., Tot10kW, Wt10kW, Wt.1.10kW, Tot50kW, Wt50kW, Wt.1.50kW
  #   3) scatter plot the ST quantities vs proportion of WHITE population, and/or proportion of LOWINC population
  #   4) where correlation is evident, calculate rho

  # For a QU report, loop through each block group and build a dataframe for analysis
  #   1) find all QU centroids within 25 miles
  #   2) sum the contained QU size and count columns, i.e., MW_RE_WI, etc.
  #   3) scatter plot the QU quantities
  #   4) where correlation is evident, calculate rho

