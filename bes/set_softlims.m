mpc.softlims.RATE_A = struct('hl_mod', 'remove', 'hl_val', 1.5);
for lim = {'VMIN', 'VMAX', 'ANGMIN', 'ANGMAX', 'PMIN', 'PMAX', 'QMIN', 'QMAX'}
    mpc.softlims.(lim{:}).hl_mod = 'none';
end
mpc = toggle_softlims (mpc, 'on');

