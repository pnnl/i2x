t = cputime;
t0 = clock();

define_constants;

mpopt = mpoption('verbose', 0, 'out.all', 0, 'opf.dc.solver', 'GLPK');
mpopt = mpoption(mpopt, 'most.dc_model', 1);
mpopt = mpoption(mpopt, 'most.uc.run', 1);
mpopt = mpoption(mpopt, 'glpk.opts.msglev', 1);
%% mpopt = mpoption(mpopt, 'glpk.opts.itlim', 10);

%% see https://docs.octave.org/interpreter/Linear-Programming.html for GLPK options
%% these do not allow GLPK to solve a 72-day unit commitment problem on the ERCOT 8-bus network,
%%  so it will be solved in a sequence of 24-hour problems from uc_days.py
%% mpopt = mpoption(mpopt, 'glpk.opts.outfrq', 50);
%% mpopt = mpoption(mpopt, 'glpk.opts.lpsolver', 1);  %% default 1, range 1..2
%% mpopt = mpoption(mpopt, 'glpk.opts.btrack', 4);  %% default 4, range 1..4
%% mpopt = mpoption(mpopt, 'glpk.opts.branch', 4);  %% default 4, range 1..5
%% mpopt = mpoption(mpopt, 'glpk.opts.price', 34);  %% default 34, range 17, 34
%% mpopt = mpoption(mpopt, 'glpk.opts.dual', 1);  %% default 1, range 1..3
%% mpopt = mpoption(mpopt, 'glpk.opts.scale', 16);  %% default 16, range 1, 16, 32, 64, 128, bitor
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

elapsed_time = etime (clock(), t0);
cpu_time = cputime - t;
printf('Objective Function Value = %.5e\n', ms.f);
printf('  Elapsed Time=%.2f\n', elapsed_time);
printf('  CPU Time=    %.2f\n', cpu_time);
printf('  Setup Time=  %.2f\n', mdo.results.SetupTime);
printf('  Solve Time=  %.2f\n', mdo.results.SolveTime);
printf('  Total Time=  %.2f\n', mdo.results.SetupTime + mdo.results.SolveTime);

