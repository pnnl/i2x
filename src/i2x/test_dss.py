import py_dss_interface # .DSS as dss
import pkg_resources as pkg

def test_opendss_interface():

  dss = py_dss_interface.DSSDLL()

  print (pkg.get_default_cache())

  fdr_path = pkg.resource_filename (__name__, 'models/ieee_lvn')
  print (fdr_path)

  pkg.resource_listdir (__name__, 'models/ieee_lvn')


#dss.text('compile c:/src/i2x/src/i2x/models/ieee_lvn/secpar.dss')
  dss.text ('compile {:s}/secpar.dss'.format (fdr_path))
  dss.text('show voltages')

#dss = py_dss_interface.DSS()
#print (dss.DLL_NAME_WIN)

#for row in dir(dss):
#  print (row)

#for row in vars(dss):
#  print (row)

#print (dss.DSSDLL().started)
#print (dss.vsources_count())
#dss.DSSDLL()

#dss.Text('compile c:/src/i2x/src/i2x/models/ieee_lvn/secpar.dss')
#print (dss.DSSDLL().started)
#print (dss.Circuit().CircuitS(0, ''))

#dss.Text('show voltages')

