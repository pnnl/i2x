import sys
import numpy as np
import mpow_utilities as mpow

if __name__ == '__main__':
  sys_name = 'hca_case'
  d = mpow.read_matpower_casefile ('{:s}.m'.format (sys_name))

  chgtab_name = 'hca_contab'
  contingencies = [{'branch':1, 'scale':0.5},
                   {'branch':2, 'scale':0.8333},
                   {'branch':3, 'scale':0.5},
                   {'branch':4, 'scale':0.5},
                   {'branch':5, 'scale':0.5},
                   {'branch':6, 'scale':0.5},
                   {'branch':7, 'scale':0.5},
                   {'branch':8, 'scale':0.5},
                   {'branch':9, 'scale':0.8333},
                   {'branch':10, 'scale':0.5},
                   {'branch':11, 'scale':0.5},
                   {'branch':12, 'scale':0.5},
                   {'branch':13, 'scale':0.6667}
                   ]
  mpow.write_contab_list (chgtab_name, d, contingencies)


