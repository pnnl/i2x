# Copyright (C) 2023 Battelle Memorial Institute
# file: report.py
"""Generating a sample geospatial data report for i2X.
"""

import sys
import os
import requests
import urllib.parse
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt 

plt.rcParams['savefig.directory'] = os.getcwd()

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

# Block groups:
# NW = WA, OR, ID, WY, MT
# SW = CO, OK, TX, NM, AZ, UT
# W = CA, NV
# SE = AR, LA, MS, AL, GA, FL, SC, NC, TN
# NE = ME, NH, VT, MA, CT, RI
# MW = OH, IN, IL, MO, MI, WI, MN, KS, IA, NE, SD, ND, KY
# HI = HI
# MA = VA, WV, PA, MD, DE, NJ, NY
# AK = AK
nwbg_url_base = r'https://services7.arcgis.com/F8VN7MYN9lP1oiiV/ArcGIS/rest/services/North_West_Block_Groups_V3/FeatureServer/0/query?'
swbg_url_base = r'https://services7.arcgis.com/F8VN7MYN9lP1oiiV/arcgis/rest/services/South_West_Block_Groups_V3/FeatureServer/0/query?'
wbg_url_base = r'https://services7.arcgis.com/F8VN7MYN9lP1oiiV/arcgis/rest/services/West_Block_Groups_V3/FeatureServer/0/query?'
sebg_url_base = r'https://services7.arcgis.com/F8VN7MYN9lP1oiiV/arcgis/rest/services/South_East_Block_Groups_V3/FeatureServer/0/query?'
nebg_url_base = r'https://services7.arcgis.com/F8VN7MYN9lP1oiiV/arcgis/rest/services/North_East_Block_Groups_V3/FeatureServer/0/query?'
mwbg_url_base = r'https://services7.arcgis.com/F8VN7MYN9lP1oiiV/arcgis/rest/services/Mid_West_Block_Groups_V3/FeatureServer/0/query?'
hibg_url_base = r'https://services7.arcgis.com/F8VN7MYN9lP1oiiV/arcgis/rest/services/Hawaii_Block_Groups_V3/FeatureServer/0/query?'
mabg_url_base = r'https://services7.arcgis.com/F8VN7MYN9lP1oiiV/arcgis/rest/services/Mid_Atlantic_Block_Groups_V3/FeatureServer/0/query?'
akbg_url_base = r'https://services7.arcgis.com/F8VN7MYN9lP1oiiV/arcgis/rest/services/Alaska_Block_Groups_V3/FeatureServer/0/query?'

# Wetlands inventory data layers:
wet_url_base = r'https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest/services/Wetlands/MapServer/0/query?'
# Critical habitat data layers (polygons and lines):
hab_poly_url_base = r'https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/USFWS_Critical_Habitat/FeatureServer/0/query?'
hab_line_url_base = r'https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/USFWS_Critical_Habitat/FeatureServer/1/query?'

metro_areas = {
  'Seattle':      {'lon':-122.33,  'lat':47.610, 'url_base': nwbg_url_base},
  'Tucson':       {'lon':-110.974, 'lat':32.254, 'url_base': swbg_url_base},
  'Dallas':       {'lon': -96.797, 'lat':32.777, 'url_base': swbg_url_base},
  'Houston':      {'lon': -95.367, 'lat':29.760, 'url_base': swbg_url_base},
  'Denver':       {'lon':-104.990, 'lat':39.739, 'url_base': swbg_url_base},
  'Phoenix':      {'lon':-112.074, 'lat':33.448, 'url_base': swbg_url_base},
  'Los Angeles':  {'lon':-118.243, 'lat':34.055, 'url_base': wbg_url_base},
  'Las Vegas':    {'lon':-115.139, 'lat':36.172, 'url_base': wbg_url_base},
  'Chicago':      {'lon': -87.630, 'lat':41.878, 'url_base': mwbg_url_base},
  'Minneapolis':  {'lon': -93.265, 'lat':44.978, 'url_base': mwbg_url_base},
  'St Louis':     {'lon': -90.199, 'lat':38.627, 'url_base': mwbg_url_base},
  'New York':     {'lon': -74.006, 'lat':40.173, 'url_base': mabg_url_base},
  'Boston':       {'lon': -71.059, 'lat':42.360, 'url_base': nebg_url_base},
  'Philadelphia': {'lon': -75.165, 'lat':39.953, 'url_base': mabg_url_base},
  'Miami':        {'lon': -80.192, 'lat':25.762, 'url_base': sebg_url_base},
  'Charlotte':    {'lon': -80.843, 'lat':35.227, 'url_base': sebg_url_base},
  'Honolulu':     {'lon':-157.858, 'lat':21.310, 'url_base': hibg_url_base},
  'Anchorage':    {'lon':-149.900, 'lat':61.218, 'url_base': akbg_url_base}
}

def get_block_groups (area, bLog=False):
  if bLog:
    print ('Entered block groups function, requesting data for {:s} ...'.format (area))
  if area in metro_areas:
    lat = metro_areas[area]['lat']
    lon = metro_areas[area]['lon']
    url_base = metro_areas[area]['url_base']
  else:
    print ('ERROR: {:s} is not defined for reporting. Choose from:'.format (area))
    for key in metro_areas:
      print ('  ', key)
    quit()
    return None

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

def overlay_plot (gdf_bg, gdf_st, gdf_qu, area):
  f, ax = plt.subplots()
  plt.title('i2x Centroids in the {:s} Block Group Footprint'.format (area))
  gdf_bg.plot(ax=ax)
  gdf_st.plot(ax=ax, color='red')
  gdf_qu.plot(ax=ax, color='yellow')
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

def usage ():
  print ('usage: python report.py [area]')
  print ('  area is one of', sorted(list(metro_areas.keys())))
  print ('  A precondition is that gdf_qu.shp and gdf_st.shp exist,')
  print ('     run "python make_i2x_gdfs.py" if necessary')

if __name__ == '__main__':
  area = 'Denver'
  if len(sys.argv) > 1:
    if sys.argv[1] in ['-h', '/h', '--h', '/?']:
      usage()
      quit()
    area = str(sys.argv[1])

  #test()
  if True: # build and save Block Group dataframes
    gdf_bg = get_block_groups (area, bLog=True)
    gdf_bg.to_file ('gdf_bg.shp')
  else: # read from disk
    gdf_bg = gpd.read_file ('gdf_bg.shp')
    print ('\n\nLoaded Block Group GeoDataFrame: crs={:s}, items={:d}\n'.format (str(gdf_bg.crs), len(gdf_bg)))

  gdf_qu = gpd.read_file ('gdf_qu.shp')
  print ('\n\nLoaded QU GeoDataFrame: crs={:s}, items={:d}\n'.format (str(gdf_qu.crs), len(gdf_qu)))
  gdf_st = gpd.read_file ('gdf_st.shp')
  print ('\n\nLoaded ST GeoDataFrame: crs={:s}, items={:d}\n'.format (str(gdf_st.crs), len(gdf_st)))

  if False:
    show_plot (gdf_bg, 'Block Group Coverage')
    show_plot (gdf_st, 'SolarTRACE Coverage')
    show_plot (gdf_qu, 'Queued Up Coverage')

  gdf_st = gdf_st.clip (gdf_bg)
  gdf_qu = gdf_qu.clip (gdf_bg)
  print ('{:d} block groups include {:d} SolarTRACE and {:d} Queued Up Centroids'.format (len(gdf_bg), len(gdf_st), len(gdf_qu)))
  overlay_plot (gdf_bg, gdf_st, gdf_qu, area)

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
  if len(d_der) < 1:
    print ('No DER data to analyze.')
    quit()
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

