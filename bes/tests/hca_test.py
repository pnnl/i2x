import sys
import numpy as np
import i2x.mpow_utilities as mpow

fuel_list = ['ng', 'wind', 'solar', 'coal', 'nuclear', 'hydro', 'dl', 'hca']

if __name__ == '__main__':
  write_daily_output = False
  upgrade_grid = False
  sys_name = 'hca'
  load_scale = 2.75
  if len(sys.argv) > 1:
    load_scale = float(sys.argv[1])
  d = mpow.read_matpower_casefile ('{:s}_case.m'.format (sys_name))
#  mpow.summarize_casefile (d, 'Input')
  fscript, fsummary = mpow.write_hca_solve_file ('hca', load_scale=load_scale)

  chgtab_name = None
  if upgrade_grid:
    chgtab_name = 'upgrades'
    #  br_scales = {4:3.0, 6:2.0, 11:1.5}
    br_scales = {4:1.5, 11:1.5}
    mpow.write_contab (chgtab_name, d, br_scales)

  mpow.run_matpower_and_wait (fscript)

  f, nb, ng, nl, ns, nt, nj_max, nc_max, psi, Pg, Pd, Rup, Rdn, SoC, Pf, u, lamP, muF = mpow.read_most_solution(fsummary)
  print ('read HCA solution from {:s}, cost={:.2f}'.format (fsummary, f))
  print ('  nb={:d}, ng={:d}, nl={:d}, ns={:d}, nt={:d}, nj_max={:d}, nc_max={:d}'.format(nb, ng, nl, ns, nt, nj_max, nc_max))
# print ('  psi', np.shape(psi), psi.dtype)
# print ('  Pg', np.shape(Pg), Pg.dtype)
# print ('  Pd', np.shape(Pd), Pd.dtype)
# print ('  Rup', np.shape(Rup), Rup.dtype)
# print ('  Rdn', np.shape(Rdn), Rdn.dtype)
# print ('  SoC', np.shape(SoC), SoC.dtype)
# print ('  Pf', np.shape(Pf), Pf.dtype)
# print ('  u', np.shape(u), u.dtype)
# print ('  lamP', np.shape(lamP), lamP.dtype)
# print ('  muF', np.shape(muF), muF.dtype)

  meanPg = np.mean(Pg[:,0,0,:], axis=1)
  meanPd = np.mean(Pd[:,0,0,:], axis=1)
  meanPf = np.mean(Pf[:,0,0,:], axis=1)
  meanlamP = np.mean(lamP[:,0,0,:], axis=1)
  meanmuF = np.mean(muF[:,0,0,:], axis=1)
  baselamP = lamP[:,0,0,0]
  basemuF = muF[:,0,0,0]

# print ('Mean Pg over contingencies\n', meanPg)
# print ('Mean Pd over contingencies\n', meanPd)
# print ('Mean Pf over contingencies\n', meanPf)
# print ('Base lamP\n', baselamP)
# print ('Mean lamP over contingencies\n', meanlamP)
# print ('Base muF\n', basemuF)
# print ('Mean muF over contingencies\n', meanmuF)
# print ('Worst muF\n', muF[3,0,0,:])

  gen = d['gen']
  bus = d['bus']
  branch = d['branch']
  nominalPd = np.sum (bus[:,mpow.PD])
  scaledPd = load_scale * nominalPd
  actualPd = np.sum(np.mean(Pd[:,0,0,:], axis=1))
  nominalPmax = np.sum (gen[:,mpow.PMAX])
  meanPgen = np.mean(Pg[:,0,0,:], axis=1)
  actualPgen = np.sum(meanPgen)
# print ('Nominal Generation = {:.2f} MW'.format (nominalPmax))
# print (' Actual Generation = {:.2f} MW'.format (actualPgen))
# print ('Nominal Bus Load = {:.2f} MW'.format (nominalPd))
# print (' Scaled Bus Load = {:.2f} MW'.format (scaledPd))
# print (' Actual Bus Load = {:.2f} MW'.format (actualPd))

  fuel_Pg = {}
  for fuel in fuel_list:
    fuel_Pg[fuel] = 0.0
  for i in range(ng):
    fuel = d['genfuel'][i]
    fuel_Pg[fuel] += meanPgen[i]
  print ('Generation Usage:')
  print (' Fuel      Mean MW       %')
  for fuel in fuel_list:
    print (' {:8s} {:8.2f} {:7.3f}'.format (fuel, fuel_Pg[fuel], 100.0 * fuel_Pg[fuel] / actualPgen))

  print ('Branches At Limit:')
  print (' idx From   To     muF     MVA     kV1     kV2')
  for i in range(nl):
    if meanmuF[i] > 0.0:
      rating = branch[i][mpow.RATE_A]
      fbus = int(branch[i][mpow.F_BUS])
      tbus = int(branch[i][mpow.T_BUS])
      kv1 = bus[fbus-1][mpow.BASE_KV]
      kv2 = bus[tbus-1][mpow.BASE_KV]
      print ('{:4d} {:4d} {:4d} {:7.4f} {:7.2f} {:7.2f} {:7.2f}'.format(i, fbus, tbus, meanmuF[i], rating, kv1, kv2))


