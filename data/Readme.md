# Procedures

- ***pip install -r requirements.txt***
- ***python script.py*** generates post-processed CSV files from SolarTRACE and Queued Up data from NREL and LBNL, respectively. 
    - The source data is updated annually. The i2X post-processing may then be triggered with webhooks, or run manually.
    - This step involves many network accesses, and it may take an hour to run. If there has not been an update to the source data, the last archived data in this repository (*../hubdata/output)* could be used.
- ***python make\_i2x\_gdfs.py*** uses CSV files from the previous step to make local GeoDataFrames, and save them in ESRI format
- ***python report.py*** creates a sample SolarTRACE report for Denver block group demographics
    - Invoke ***python report.py /?*** to show other cities that may be chosen at the present time
- ***python bes\_report.py*** creates a sample Queued Up report for wetland and critical habitat data
    - Invoke ***python bes\_report.py /?*** to show how other longitude, latitude, and box size options may be chosen

At the present time, both kinds of reports are affected by limits on the GIS query return, i.e., either 1000 or 2000 rows depending on the data source.

# Suggested Improvements

1. In the initial_processing.py file,
 for the solar_trace data, years and sizes variables are hardcoded. These must be improved by reading all the years and sizes that are available from the original input file.
The current vesrion (filename: "pnnl_utility_timelines_summary.xlsx" as of 9-6-23) of the input file for SolarTRACE has the following columns:

	state	ahj	geo_id	utility	eia_id	All	2017	2018	2019	2020	2021	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX	Installs	Pre Ix	N	Final IX	N	Full IX	Total IX

Assuming numbered years start from column 7 (2017 in this case), This may be used as a starting point to extract the years present in the file. Another approach is to read the first row that has the following columns in the current vesrion (filename: "pnnl_utility_timelines_summary.xlsx" as of 9-6-23) of the input file for SolarTRACE: 
Total installs	2017 | 0-10kW	2018 | 0-10kW	2019 | 0-10kW	2020 | 0-10kW	2021 | 0-10kW   2017 | 11-50kW  2018 | 11-50kW  2019 | 11-50kW  2020 | 11-50kW  2021 | 11-50kW

NOTE: the read_input function reads the input files and year can be extracted in this module instead.											

2. In the main_processing.py file,
 for the solar_trace data, the indices ideally must be read from the file. After figuring out the ending year's index which is 11 with the year 2021 for the current vesrion (filename: "pnnl_utility_timelines_summary.xlsx" as of 9-6-23), every 14 columns (with first 7 for PV-only and second 7 PV+Storage).

In this same file, The while loops can be encapsulated and the duplicated code removed.

3. In the helper_methods.py file, 
 The get_api_results function may return a None which must be cleaned up in the output file. Currently these None values, result in 0 lat 0 lon entries within the output file that may look odd.

# Output Schemas

FDataframe info read from ```../hubdata/output/queued_up.csv```

```
RangeIndex: 2116 entries, 0 to 2115
Data columns (total 34 columns):
 #   Column                          Non-Null Count  Dtype
---  ------                          --------------  -----
 0   state_county                    2116 non-null   object
 1   utility_count                   2116 non-null   float64
 2   mw_max                          2116 non-null   float64
 3   project_count                   2116 non-null   float64
 4   days_max                        2116 non-null   float64
 5   type_clean                      2116 non-null   object
 6   mw_Solar_withdrawn              2116 non-null   float64
 7   mw_Solar_operational            2116 non-null   float64
 8   mw_Solar_active                 2116 non-null   float64
 9   mw_Solar_suspended              2116 non-null   float64
 10  mw_Wind_withdrawn               2116 non-null   float64
 11  mw_Wind_operational             2116 non-null   float64
 12  mw_Wind_active                  2116 non-null   float64
 13  mw_Wind_suspended               2116 non-null   float64
 14  mw_Neither_withdrawn            2116 non-null   float64
 15  mw_Neither_operational          2116 non-null   float64
 16  mw_Neither_active               2116 non-null   float64
 17  mw_Neither_suspended            2116 non-null   float64
 18  proj_count_Solar_withdrawn      2116 non-null   float64
 19  proj_count_Solar_operational    2116 non-null   float64
 20  proj_count_Solar_active         2116 non-null   float64
 21  proj_count_Solar_suspended      2116 non-null   float64
 22  proj_count_Wind_withdrawn       2116 non-null   float64
 23  proj_count_Wind_operational     2116 non-null   float64
 24  proj_count_Wind_active          2116 non-null   float64
 25  proj_count_Wind_suspended       2116 non-null   float64
 26  proj_count_Neither_withdrawn    2116 non-null   float64
 27  proj_count_Neither_operational  2116 non-null   float64
 28  proj_count_Neither_active       2116 non-null   float64
 29  proj_count_Neither_suspended    2116 non-null   float64
 30  STATE_NAME                      2116 non-null   object
 31  STATE_ABBR                      2116 non-null   object
 32  lat                             2116 non-null   float64
 33  lon                             2116 non-null   float64
dtypes: float64(30), object(4)
memory usage: 562.2+ KB
```

Dataframe info read from ```../hubdata/output/solarTRACE.csv```

```
RangeIndex: 7005 entries, 0 to 7004
Data columns (total 38 columns):
 #   Column                                               Non-Null Count  Dtype
---  ------                                               --------------  -----
 0   geo_id                                               7005 non-null   float64
 1   state                                                7005 non-null   object
 2   state_full                                           7005 non-null   object
 3   ahj                                                  7005 non-null   object
 4   utility                                              7005 non-null   object
 5   eia_id                                               7005 non-null   float64
 6   Weighted_Installs.2_Pre Ix.2_0-10kW_2018             7005 non-null   float64
 7   Weighted_Installs.4_Pre Ix.4_0-10kW_2019             7005 non-null   float64
 8   Weighted_Installs.6_Pre Ix.6_0-10kW_2020             7005 non-null   float64
 9   Weighted_Installs.8_Pre Ix.8_0-10kW_2021             7005 non-null   float64
 10  Weighted_Installs.10_Pre Ix.10_11-50kW_2017          7005 non-null   float64
 11  Weighted_Installs.12_Pre Ix.12_11-50kW_2018          7005 non-null   float64
 12  Weighted_Installs.14_Pre Ix.14_11-50kW_2019          7005 non-null   float64
 13  Weighted_Installs.16_Pre Ix.16_11-50kW_2020          7005 non-null   float64
 14  Weighted_Installs.18_Pre Ix.18_11-50kW_2021          7005 non-null   float64
 15  Weighted_Installs_Installs_Installs.2_0-10kW_2018    7005 non-null   float64
 16  Add_Full IX_Total IX_0-10kW_2017                     7005 non-null   float64
 17  Add_Full IX.2_Total IX.2_0-10kW_2018                 7005 non-null   float64
 18  Add_Full IX.4_Total IX.4_0-10kW_2019                 7005 non-null   float64
 19  Add_Full IX.6_Total IX.6_0-10kW_2020                 7005 non-null   float64
 20  Add_Full IX.8_Total IX.8_0-10kW_2021                 7005 non-null   float64
 21  Add_Full IX.10_Total IX.10_11-50kW_2017              7005 non-null   float64
 22  Add_Full IX.12_Total IX.12_11-50kW_2018              7005 non-null   float64
 23  Add_Full IX.14_Total IX.14_11-50kW_2019              7005 non-null   float64
 24  Add_Full IX.16_Total IX.16_11-50kW_2020              7005 non-null   float64
 25  Add_Full IX.18_Total IX.18_11-50kW_2021              7005 non-null   float64
 26  lat                                                  7005 non-null   float64
 27  lon                                                  7005 non-null   float64
 28  Weighted_Installs.2_Pre Ix.2_0-10kW_2018.1           7005 non-null   float64
 29  Weighted_Installs.4_Pre Ix.4_0-10kW_2019.1           7005 non-null   float64
 30  Weighted_Installs.6_Pre Ix.6_0-10kW_2020.1           7005 non-null   float64
 31  Weighted_Installs.8_Pre Ix.8_0-10kW_2021.1           7005 non-null   float64
 32  Weighted_Installs.10_Pre Ix.10_11-50kW_2017.1        7005 non-null   float64
 33  Weighted_Installs.12_Pre Ix.12_11-50kW_2018.1        7005 non-null   float64
 34  Weighted_Installs.14_Pre Ix.14_11-50kW_2019.1        7005 non-null   float64
 35  Weighted_Installs.16_Pre Ix.16_11-50kW_2020.1        7005 non-null   float64
 36  Weighted_Installs.18_Pre Ix.18_11-50kW_2021.1        7005 non-null   float64
 37  Weighted_Installs_Installs_Installs.2_0-10kW_2018.1  7005 non-null   float64
dtypes: float64(34), object(4)
memory usage: 2.0+ MB
```
