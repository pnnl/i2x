import matplotlib.pyplot as plt 
import numpy as np
from scipy import interpolate
import os

dss_y = [0.6770,0.6256,0.6087,0.5833,0.58028,0.6025,0.657,
        0.7477,0.832,0.88,0.94,0.989,0.985,0.98,0.9898,
        0.999,1.000,0.958,0.936,0.913,0.876,0.876,0.828,0.756]

hticks = [0,4,8,12,16,20,24]
pathname = '../src/i2x/models/support/'

if __name__ == "__main__":
  dss_y.append(dss_y[0])
  dss_x = np.linspace(0.0,24.0,25)
  fzero = interpolate.interp1d (dss_x, dss_y, kind='zero')
  flinear = interpolate.interp1d (dss_x, dss_y, kind='slinear')
  fquad = interpolate.interp1d (dss_x, dss_y, kind='quadratic')
  fcube = interpolate.interp1d (dss_x, dss_y, kind='cubic')
  t = np.linspace(0.0,24.0,86401)
  zero = fzero(t)
  linear = flinear(t)
  quad = fquad(t)
  cube = fcube(t)
  hrs = t

  print ('Default   Min/Max = [{:6.4f},{:6.4f}]'.format(min(zero), max(zero)))
  print ('Linear    Min/Max = [{:6.4f},{:6.4f}]'.format(min(linear), max(linear)))
  print ('Quadratic Min/Max = [{:6.4f},{:6.4f}]'.format(min(quad), max(quad)))
  print ('Cubic     Min/Max = [{:6.4f},{:6.4f}]'.format(min(cube), max(cube)))

  fig, ax = plt.subplots (1, 1, sharex = 'col', figsize=(12,8), constrained_layout=True)
  fig.suptitle ('Interpolated Loadshapes to {:s}'.format(pathname))
  ax.plot (hrs, zero, label='Default', color='black', linestyle='dotted')
  ax.plot (hrs, linear, label='Linear (ldaily.dat)', color='red')
  ax.plot (hrs, quad, label='Quadratic (qdaily.dat)', color='blue')
  ax.plot (hrs, cube, label='Cubic (cdaily.dat)', color='green')
  ax.legend()
  ax.grid()
  ax.set_xticks (hticks)
  ax.set_xlim (hticks[0], hticks[-1])
  ax.set_xlabel('t [hrs]')
  plt.show()
  plt.close()

  np.savetxt (os.path.join(pathname, 'ldaily.dat'), linear, fmt='%.4f')
  np.savetxt (os.path.join(pathname, 'qdaily.dat'), quad, fmt='%.4f')
  np.savetxt (os.path.join(pathname, 'cdaily.dat'), cube, fmt='%.4f')


