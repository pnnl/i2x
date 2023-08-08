import sys
import numpy as np
import mpow_utilities as mpow
import json

fuel_list = ['hca', 'wind', 'solar', 'nuclear', 'hydro', 'coal', 'ng', 'dl']

def cfg_assign (cfg, tag, val):
  if tag in cfg:
    val = cfg[tag]
  return val

if __name__ == '__main__':
  sys_name = 'hca'
  load_scale = 2.75
  hca_buses = None
  upgrades = None
  if len(sys.argv) > 1:
    fp = open (sys.argv[1], 'r')
    cfg = json.loads(fp.read())
    fp.close()
    sys_name = cfg_assign (cfg, 'sys_name', sys_name)
    hca_buses = cfg_assign (cfg, 'hca_buses', hca_buses)
    upgrades = cfg_assign (cfg, 'upgrades', upgrades)
    load_scale = cfg_assign (cfg, 'load_scale', load_scale)

  # nominal quantities for the base case, hca generation at zero
  d = mpow.read_matpower_casefile ('{:s}_case.m'.format (sys_name))
  nb = len(d['bus'])
  ng = len(d['gen'])
  nl = len(d['branch'])

  gen = np.array (d['gen'], dtype=float)
  bus = np.array (d['bus'], dtype=float)
  branch = np.array (d['branch'], dtype=float)
  nominalPd = np.sum (bus[:,mpow.PD])
  scaledPd = load_scale * nominalPd
  nominalPmax = np.sum (gen[:,mpow.PMAX])

  # make sure we have a bus list
  if not hca_buses:
    hca_buses = np.arange(1, nb+1, dtype=int)
  if hca_buses[0] < 1:
    hca_buses = np.arange(1, nb+1, dtype=int)

  chgtab_name = None
  nupgrades = 0
  if upgrades:
    chgtab_name = '{:s}_upgrades'.format(sys_name)
    nupgrades = len(upgrades)
    mpow.write_contab (chgtab_name, d, upgrades)

  hca_gen_idx = 0

  muFtotal = np.zeros (nl)
  for i in range(ng):
    if d['genfuel'][i] == 'hca':
      hca_gen_idx = i + 1
      nominalPmax -= gen[i,mpow.PMAX]
  nominalPmax *= 0.001
  nominalPd *= 0.001
  scaledPd *= 0.001
  print ('System: {:s} with nominal load={:.3f} GW, actual load={:.3f} GW, existing generation={:.3f} GW'.format(sys_name, nominalPd, scaledPd, nominalPmax))
  print ('HCA generator index = {:d}, load_scale={:.4f}, checking {:d} buses with {:d} grid upgrades'.format(hca_gen_idx, load_scale, len(hca_buses), nupgrades))

  print ('Bus Generation by Fuel[GW]')
  print ('   ', ' '.join(['{:>7s}'.format(x) for x in fuel_list]))
  for hca_bus in hca_buses:
    cmd = 'mpc.gen({:d},1)={:d};'.format(hca_gen_idx, hca_bus) # move the HCA injection to each bus in turn
    fscript, fsummary = mpow.write_hca_solve_file ('hca', load_scale=load_scale, upgrades=chgtab_name, cmd=cmd, quiet=True)

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
  print ('Branches At Limit:')
  print (' idx From   To     muF     MVA     kV1     kV2')
  for i in range(nl):
    if muFtotal[i] > 0.0:
      rating = branch[i][mpow.RATE_A]
      fbus = int(branch[i][mpow.F_BUS])
      tbus = int(branch[i][mpow.T_BUS])
      kv1 = bus[fbus-1][mpow.BASE_KV]
      kv2 = bus[tbus-1][mpow.BASE_KV]
      print ('{:4d} {:4d} {:4d} {:7.4f} {:7.2f} {:7.2f} {:7.2f}'.format(i+1, fbus, tbus, muFtotal[i], rating, kv1, kv2))

