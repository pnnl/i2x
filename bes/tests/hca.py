import sys
import numpy as np
import mpow_utilities as mpow

if __name__ == '__main__':
  write_daily_output = False
  upgrade_grid = False
  sys_name = 'hca'
  load_scale = 1.0
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

  print ('Mean Pg over contingencies\n', np.mean(Pg[:,0,0,:], axis=1))
  print ('Mean Pd over contingencies\n', np.mean(Pd[:,0,0,:], axis=1))
  print ('Mean Pf over contingencies\n', np.mean(Pf[:,0,0,:], axis=1))
  print ('Mean lamP over contingencies\n', np.mean(lamP[:,0,0,:], axis=1))
  print ('Mean muF over contingencies\n', np.mean(muF[:,0,0,:], axis=1))

  gen = np.array (d['gen'], dtype=float)
  bus = np.array (d['bus'], dtype=float)
  nominalPd = np.sum (bus[:,mpow.PD])
  scaledPd = load_scale * nominalPd
  actualPd = np.sum(np.mean(Pd[:,0,0,:], axis=1))
  nominalPmax = np.sum (gen[:,mpow.PMAX])
  actualPgen = np.sum(np.mean(Pg[:,0,0,:], axis=1))
  print ('Nominal Generation = {:.2f} MW'.format (nominalPmax))
  print (' Actual Generation = {:.2f} MW'.format (actualPgen))
  print ('Nominal Bus Load = {:.2f} MW'.format (nominalPd))
  print (' Scaled Bus Load = {:.2f} MW'.format (scaledPd))
  print (' Actual Bus Load = {:.2f} MW'.format (actualPd))

