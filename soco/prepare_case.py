import tesp_support.api as tesp

tmy_file = '../../tesp/support/weather/TX-Houston_Bush_Intercontinental.tmy3'
tesp.weathercsv(tmy_file, 'weather.dat', '2013-08-04 00:00:00', '2013-08-11 00:00:00', 2013)
tesp.glm_dict('soco_test')
