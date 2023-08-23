clear;
define_constants;
mpopt = mpoption('verbose', 0, 'out.all', 0);
mpopt = mpoption(mpopt, 'most.dc_model', 1);
mpopt = mpoption(mpopt, 'most.uc.run', 1);
mpopt = mpoption(mpopt, 'most.solver', 'GLPK');
mpopt = mpoption(mpopt, 'glpk.opts.msglev', 1);
mpc = loadcase ('hca_case.m');
% mpcbase = loadcase ('hca_case.m');
% chgtab = uc_contab;
% mpc = apply_changes (1, mpcbase, chgtab);
mpc = scale_load(4.0, mpc);
xgd = loadxgendata('hca_xgd.m', mpc);
mdi = loadmd(mpc, [], xgd, [], 'hca_contab');
mdo = most(mdi, mpopt);
ms = most_summary(mdo);
save('-text', 'hca_summary.txt', 'ms');
total_time = mdo.results.SolveTime + mdo.results.SetupTime
