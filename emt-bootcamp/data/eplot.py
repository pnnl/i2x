# copyright 2023 Battelle Memorial Institute

import sys
import matplotlib.pyplot as plt
import numpy as np
import os

plt.rcParams['savefig.directory'] = os.getcwd()

if __name__ == '__main__':
  fname = 'SM_SCRX9m.m'
  if len(sys.argv) > 1:
    fname = sys.argv[1]

  # create a dictionary of the scope channels
  n_scopes = 0
  filn = None
  t_max = None
  output_type = None
  scope_dict = {}
  fp = open (fname, 'r')
  ln = fp.readline()
  while ln:
    toks = ln.strip(""";\n\r\t """).split('=')
    if 'filn' == toks[0]:
      filn = toks[1].strip("""'""")
    elif 't' == toks[0]:
      output_type = 'time'
    elif 'f' == toks[0]:
      output_type = 'frequency scan (UNSUPPORTED)'
    elif 'statistical' == toks[0]:
      output_type = 'statistical (UNSUPPORTED)'
    elif 't_max' == toks[0]:
      t_max = float(toks[1])
    elif 'n_scopes' == toks[0]:
      n_scopes = int(toks[1])
    elif 'n_' in toks[0] and '_scopes' in toks[0]:
      group_type = toks[0].split('_')[1]
      group_count = int(toks[1])
      scope_dict[group_type] = {}
      channels = []
      for i in range(group_count):
        cname = fp.readline().split("""'""")[1]
        channels.append (cname)
        scope_dict[group_type][cname] = 0
      # assuming the column indices are consecutive within each scope group,
      #  converting 1-based MATLAB indexing to 0-based Python indexing
      toks = fp.readline().strip(""";\n\r\t """).split('=')[1]
      cols = toks.split(':')
      col_start = int(cols[0])
      col_step = int(cols[1]) # should be 1
      col_end = int(cols[2])
      for idx in range (col_end - col_start + 1):
        scope_dict[group_type][channels[idx]] = idx + col_start - 1

    ln = fp.readline()

  fp.close()
  print ('filn', filn, 'has', output_type, 'output data in', n_scopes, 'columns')
  print ('t_max', t_max)
  print ('Scope groups with channel names and 0-based column indices:')
  print (scope_dict)

  # now read the binary data into a structured Numpy array
  fields = [0] * n_scopes
  for group in scope_dict:
    for cname, col in scope_dict[group].items():
      fields[col] = cname
  print ('fields in order:', fields)
  dt = [('_prefix', np.int32)]
  for fld in fields:
    dt.append ((fld, np.float64))
  dt.append (('_suffix', np.int32))
  data = np.fromfile (filn, dtype=np.dtype(dt))
  print ('read', data.shape, 'rows from', filn)
  print ('time', data['time'])

  # now plot everything that fits on a page
  nrows = 3
  ncols = 4
  idx = 1
  t = data['time']
  fig, ax = plt.subplots(nrows, ncols, sharex = 'col', figsize=(15,6), constrained_layout=True)
  fig.suptitle ('Data: ' + filn)
  for i in range(nrows):
    for j in range(ncols):
      if idx >= len(fields):
        break
      fld = fields[idx]
      ax[i,j].plot (t, data[fld])
      ax[i,j].set_title (fld)
      ax[i,j].grid()
      idx += 1
  plt.show()
  plt.close()

