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

def nw_block_groups (bLog=False):
  if bLog:
    print ('Entered block groups function, rquesting data...')
  url_base = r'https://services7.arcgis.com/F8VN7MYN9lP1oiiV/ArcGIS/rest/services/North_West_Block_Groups_V3/FeatureServer/0/query?'
  params = {
    'geometry': '-122.33, 47.61',  # Seattle
    'geometryType': 'esriGeometryPoint',
    'inSR': '4326',
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

if __name__ == '__main__':
  #test()
  if False: # build and save GeoDataFrames
    gdf_qu = get_qu (bLog=True)
    gdf_st = get_st (bLog=True)
    gdf_nw = nw_block_groups (bLog=True)
    
    gdf_qu.to_file ('gdf_qu.shp')
    gdf_st.to_file ('gdf_st.shp')
    gdf_nw.to_file ('gdf_nw.shp')
  else: # read the local GeoDataFrames
    gdf_qu = gpd.read_file ('gdf_qu.shp')
    print ('\n\nLoaded QU GeoDataFrame:\n', gdf_qu)
    gdf_st = gpd.read_file ('gdf_st.shp')
    print ('\n\nLoaded ST GeoDataFrame:\n', gdf_st)
    gdf_nw = gpd.read_file ('gdf_nw.shp')
    print ('\n\nLoaded Block Group GeoDataFrame:\n', gdf_nw)

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

