# Copyright (C) 2023 Battelle Memorial Institute
# file: bes_report.py
"""Generating a sample geospatial data report (wetlands, habitate, BES) for i2X.
"""

import sys
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

def protected_get_gdf (url_base, params, bLog=False, label=None):
  if bLog:
    print ('Requesting {:s} data ...'.format (label))
  url_final = url_base + urllib.parse.urlencode(params)
  response = requests.get(url=url_final)
  if bLog:
    print ('  returned from data request.')
  data = response.text
  try:
    # print ('\n\nJSON result:\n\n', data)
    gdf = gpd.read_file(data)
  except:
    gdf = gpd.GeoDataFrame(columns=['test', 'geometry'], crs='EPSG:4326')
  if bLog:
    print ('\n\n{:s} GeoDataFrame result:\n\n'.format (label), gdf)
  return gdf

def get_wetlands (lat, lon, bLog=True):
  url_base = r'https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest/services/Wetlands/MapServer/0/query?'
  params = {
    'geometry': '{:.3f}, {:.3f}'.format (lon, lat),  
    'geometryType': 'esriGeometryPoint',
    'inSR': '4326',
    'outSR': '4326',
    'distance': '100000',
    'units': 'esriSRUnit_Meter', 
    'returnGeometry': 'true', 
    'outFields': 'ACRES', #,WETLAND_TYPE', 
    'f': 'pjson'
    }
  return protected_get_gdf (url_base, params, bLog, 'Wetlands')

def get_habitat_polygons (lat, lon, bLog=True):
  url_base = r'https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/USFWS_Critical_Habitat/FeatureServer/0/query?'
  params = {
    'geometry': '{:.3f}, {:.3f}'.format (lon, lat),  
    'geometryType': 'esriGeometryPoint',
    'inSR': '4326',
    'outSR': '4326',
    'distance': '100000',
    'units': 'esriSRUnit_Meter', 
    'returnGeometry': 'true', 
    'outFields': 'comname', 
    'f': 'pjson'
    }
  return protected_get_gdf (url_base, params, bLog, 'Habitat polygon')

def get_habitat_lines (lat, lon, bLog=True):
  url_base = r'https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/USFWS_Critical_Habitat/FeatureServer/1/query?'
  params = {
    'geometry': '{:.3f}, {:.3f}'.format (lon, lat),  
    'geometryType': 'esriGeometryPoint',
    'inSR': '4326',
    'outSR': '4326',
    'distance': '100000',
    'units': 'esriSRUnit_Meter', 
    'returnGeometry': 'true', 
    'outFields': 'comname', 
    'f': 'pjson'
    }
  return protected_get_gdf (url_base, params, bLog, 'Habitat lines')

def overlay_plot (gdf_wet, gdf_hab_poly, gdf_hab_line, gdf_qu, lon, lat):
  f, ax = plt.subplots()
  plt.title('i2x Centroids in the Habitat/Wetlands Footprint Around {:.3f},{:.3f}'.format (lon, lat))
  if len(gdf_wet) > 0:
    gdf_wet.plot(ax=ax, color='blue', label='Wetland')
  if len(gdf_hab_poly) > 0:
    gdf_hab_poly.plot(ax=ax, color='yellow', label='Hab Polygons')
  if len(gdf_hab_line) > 0:
    gdf_hab_line.plot(ax=ax, color='red', label='Hab Lines')
  if len(gdf_qu) > 0:
    gdf_qu.plot(ax=ax, color='green', label='Queued Up')
  plt.ylabel('Latitude [deg]')
  plt.xlabel('Longitude [deg]')
  plt.show()
  plt.close()

def usage ():
  print ('usage: python bes_report.py [lon] [lat] [box_side]')
  print ('  units of lon, lat, and box are degrees')
  print ('  1-degree box width is about 60 miles')
  print ('  A precondition is that gdf_qu.shp and gdf_st.shp exist,')
  print ('     run "python make_i2x_gdfs.py" if necessary')

if __name__ == '__main__':
  lon = -104.990
  lat = 39.739
  box_side = 3.0 # degrees, which is about 60 miles

  if len(sys.argv) > 1:
    if sys.argv[1] in ['-h', '/h', '--h', '/?']:
      usage()
      quit()
    lon = float(sys.argv[1])
    if len(sys.argv) > 2:
      lat = float(sys.argv[2])
      if len(sys.argv) > 3:
        box_side = float(sys.argv[3])

  dbox = box_side / 2.0
  box = [lon-dbox, lat-dbox, lon+dbox, lat+dbox]
  gdf_qu = gpd.read_file ('gdf_qu.shp')
  print ('\n\nLoaded QU GeoDataFrame: crs={:s}, items={:d}\n'.format (str(gdf_qu.crs), len(gdf_qu)))
  gdf_box = gdf_qu.clip (box)
  print (box, 'contains {:d} Queued Up centroids'.format (len(gdf_box)))

  if True: # build and save wetland and habitat GeoDataFrames
    gdf_wet = get_wetlands (lon=lon, lat=lat, bLog=True)
    if len(gdf_wet) > 0:
      gdf_wet.to_file ('gdf_wet.shp')
    gdf_hab_poly = get_habitat_polygons (lon=lon, lat=lat, bLog=True)
    if len(gdf_hab_poly) > 0:
      gdf_hab_poly.to_file ('gdf_hab_poly.shp')
    gdf_hab_line = get_habitat_lines (lon=lon, lat=lat, bLog=True)
    if len(gdf_hab_poly) > 0:
      gdf_hab_line.to_file ('gdf_hab_line.shp')
  else: # read from disk
    gdf_wet = gpd.read_file ('gdf_wet.shp')
    print ('\n\nLoaded Wetlands GeoDataFrame: crs={:s}, items={:d}\n'.format (str(gdf_wet.crs), len(gdf_wet)))
    gdf_hab_poly = gpd.read_file ('gdf_hab_poly.shp')
    print ('\n\nLoaded Habitat polygon GeoDataFrame: crs={:s}, items={:d}\n'.format (str(gdf_hab_poly.crs), len(gdf_hab_poly)))
    gdf_hab_line = gpd.read_file ('gdf_hab_line.shp')
    print ('\n\nLoaded Habitat line GeoDataFrame: crs={:s}, items={:d}\n'.format (str(gdf_hab_line.crs), len(gdf_hab_line)))

  print ('Environmental bounding box includes {:d} Queued Up Centroids'.format (len(gdf_box)))
  overlay_plot (gdf_wet, gdf_hab_poly, gdf_hab_line, gdf_box, lon, lat)

  bes_tags = ['OP', 'AC', 'SU', 'WI']
  bes_desc = ['Operational', 'Active', 'Suspended', 'Withdrawn']
  all_projects = 0.0
  box_projects = 0.0
  for tag in bes_tags:
    col = 'N_RE_{:s}'.format(tag)
    all_projects += gdf_qu[col].sum()
    box_projects += gdf_box[col].sum()
  print ('Mean Values for Solar and Wind Projects')
  print ('Quantity         Nationwide      Boxed')
  print ('Total Projects   {:10d} {:10d}'.format (int(all_projects), int(box_projects)))
  if box_projects < 1:
    box_projects = 1.0
  for i in range(len(bes_tags)):
    col = 'MW_RE_{:s}'.format(bes_tags[i])
    desc = '{:s} [MW]'.format (bes_desc[i])
    mean_all = gdf_qu[col].mean()
    mean_box = gdf_box[col].mean()
    print ('{:16s} {:10.2f} {:10.2f}'.format (desc, mean_all, mean_box))
  for i in range(len(bes_tags)):
    col = 'N_RE_{:s}'.format(bes_tags[i])
    desc = '{:s} [%]'.format (bes_desc[i])
    pct_all = 100.0 * gdf_qu[col].sum() / all_projects
    pct_box = 100.0 * gdf_box[col].sum() / box_projects
    print ('{:16s} {:10.3f} {:10.3f}'.format (desc, pct_all, pct_box))

