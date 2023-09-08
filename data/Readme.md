# How to run
#### Run script directly from cmd:
python script.py (considering requirements are installed)

# improvements to be applied:
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
