import py_dss_interface # .DSS as dss
import pkg_resources as pkg
import inspect

def test_opendss_interface(doc_fp=None):

  choice = 'ieee9500'
#  choice = 'ieee_lvn'

  dss = py_dss_interface.DSSDLL()

  print (pkg.get_default_cache())

  fdr_path = pkg.resource_filename (__name__, 'models/{:s}'.format(choice))
  print (fdr_path)

  pkg.resource_listdir (__name__, 'models/{:s}'.format(choice))


  dss.text ('compile {:s}/HCABase.dss'.format (fdr_path))
  # dss.text('show voltages')
  print ('Circuit:', dss.circuit_name())
#  print (dss.circuit_all_bus_volts())

  if doc_fp is not None:
    print ('DSSDLL vars:', file=doc_fp)
    for row in vars(dss):
      print (' ', row, file=doc_fp)
    print ('DSSDLL dir:', file=doc_fp)
    for row in dir(dss):
      fn = getattr(dss, row)
      if inspect.ismethod(fn):
        print ('  {:40s} {:s}'.format (row, str(inspect.signature(fn))), file=doc_fp)

