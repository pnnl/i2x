import sys
import numpy as np
import mpow_utilities as mpow

fuel_list = ['hca', 'wind', 'solar', 'nuclear', 'hydro', 'coal', 'ng', 'dl']

if __name__ == '__main__':
  upgrade_grid = False
  sys_name = 'hca'
  load_scale = 2.75
  if len(sys.argv) > 1:
    load_scale = float(sys.argv[1])

  # nominal quantities for the base case, hca generation at zero
  d = mpow.read_matpower_casefile ('{:s}_case.m'.format (sys_name))
  gen = np.array (d['gen'], dtype=float)
  bus = np.array (d['bus'], dtype=float)
  branch = np.array (d['branch'], dtype=float)
  nominalPd = np.sum (bus[:,mpow.PD])
  scaledPd = load_scale * nominalPd
  nominalPmax = np.sum (gen[:,mpow.PMAX])

  chgtab_name = None
  if upgrade_grid:
    chgtab_name = 'upgrades'
    #  br_scales = {4:3.0, 6:2.0, 11:1.5}
    br_scales = {4:1.5, 11:1.5}
    mpow.write_contab (chgtab_name, d, br_scales)

  hca_gen_idx = 0
  nb = len(d['bus'])
  ng = len(d['gen'])
  nl = len(d['branch'])
  muFtotal = np.zeros (nl)
  for i in range(ng):
    if d['genfuel'][i] == 'hca':
      hca_gen_idx = i + 1
  print ('HCA generator index = {:d}'.format(hca_gen_idx))

  print ('Bus Generation by Fuel[GW]')
  print ('   ', ' '.join(['{:>7s}'.format(x) for x in fuel_list]))
  for i in range(nb):
    hca_bus = i+1
    cmd = 'mpc.gen({:d},1)={:d};'.format(hca_gen_idx, hca_bus) # move the HCA injection to each bus in turn
    fscript, fsummary = mpow.write_hca_solve_file ('hca', load_scale=load_scale, cmd=cmd, quiet=True)

    mpow.run_matpower_and_wait (fscript, quiet=True)

    f, nb, ng, nl, ns, nt, nj_max, nc_max, psi, Pg, Pd, Rup, Rdn, SoC, Pf, u, lamP, muF = mpow.read_most_solution(fsummary)
    meanPg = np.mean(Pg[:,0,0,:], axis=1)
    meanPd = np.mean(Pd[:,0,0,:], axis=1)
    meanPf = np.mean(Pf[:,0,0,:], axis=1)
    meanlamP = np.mean(lamP[:,0,0,:], axis=1)
    meanmuF = np.mean(muF[:,0,0,:], axis=1)
    baselamP = lamP[:,0,0,0]
    basemuF = muF[:,0,0,0]
    actualPd = np.sum(np.mean(Pd[:,0,0,:], axis=1))
    meanPgen = np.mean(Pg[:,0,0,:], axis=1)
    actualPgen = np.sum(meanPgen)

    fuel_Pg = {}
    for fuel in fuel_list:
      fuel_Pg[fuel] = 0.0
    for i in range(ng):
      fuel = d['genfuel'][i]
      fuel_Pg[fuel] += meanPgen[i]
    for fuel in fuel_list:
      fuel_Pg[fuel] *= 0.001
    fuel_str = ' '.join(['{:7.3f}'.format(fuel_Pg[x]) for x in fuel_list])
    print ('{:3d} {:s}'.format(hca_bus, fuel_str))

    muFtotal += meanmuF

  muFtotal /= nb
  print ('Branches Overloaded:')
  print (' idx     muF     MVA     kV1     kV2')
  for i in range(nl):
    if muFtotal[i] > 0.0:
      rating = branch[i][mpow.RATE_A]
      fbus = int(branch[i][mpow.F_BUS])
      tbus = int(branch[i][mpow.T_BUS])
      kv1 = bus[fbus-1][mpow.BASE_KV]
      kv2 = bus[tbus-1][mpow.BASE_KV]
      print ('{:4d} {:7.4f} {:7.2f} {:7.2f} {:7.2f}'.format(i, muFtotal[i], rating, kv1, kv2))

