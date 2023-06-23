t = cputime;
t0 = clock();

define_constants;

% mpopt = mpoption('verbose', 3, 'out.all', 1, 'most.dc_model', 0, 'opf.dc.solver', 'GLPK');
mpopt = mpoption('verbose', 0, 'out.all', 0, 'most.dc_model', 0, 'opf.dc.solver', 'GLPK');
mpopt = mpoption(mpopt, 'most.uc.run', 1);
mpopt = mpoption(mpopt, 'glpk.opts.msglev', 1);
mpopt = mpoption(mpopt, 'glpk.opts.outfrq', 50);
mpopt = mpoption(mpopt, 'glpk.opts.itlim', 1000);
%% mipgap is either not passed to GLPK or does not affect this example
%% tmlim will stop the solution in GLPK, but not return usable output                                               
%% mpopt = mpoption(mpopt, 'glpk.opts.tmlim', 60000);
%% mpopt = mpoption(mpopt, 'glpk.opts.mipgap', 0.1);
%% mpopt = mpoption(mpopt, 'glpk.opts.tolint', 1e-10);
%% mpopt = mpoption(mpopt, 'glpk.opts.tolobj', 1e-10);
%% mpopt = mpoption(mpopt, 'glpk.opts.tolint', 1e-5);
%% mpopt = mpoption(mpopt, 'glpk.opts.tolobj', 1e-7);

mpc = loadcase ('test_case.m');
% turn on the wind turbines
mpc.gen([14,15,16,17,18],GEN_STATUS)=1;

xgd = loadxgendata('test_xgd.m', mpc);
profiles = getprofiles('test_unresp.m');
profiles = getprofiles('test_resp.m', profiles);
profiles = getprofiles('test_wind.m', profiles);

nt = size(profiles(1).values, 1);

mdi = loadmd(mpc, nt, xgd, [], [], profiles);
mdo = most(mdi, mpopt);

ms = most_summary(mdo);
save('-text', 'msout.txt', 'ms');

elapsed_time = etime (clock(), t0)
cpu_time = cputime - t
ms.f
