function unresp = test_unresp
  [PQ, PV, REF, NONE, BUS_I, BUS_TYPE, PD, QD, GS, BS, BUS_AREA, VM, ...
    VA, BASE_KV, ZONE, VMAX, VMIN, LAM_P, LAM_Q, MU_VMAX, MU_VMIN] = idx_bus;
  [F_BUS, T_BUS, BR_R, BR_X, BR_B, RATE_A, RATE_B, RATE_C, TAP, SHIFT, ...
    BR_STATUS, ANGMIN, ANGMAX, PF, QF, PT, QT, MU_SF, MU_ST, MU_ANGMIN, ...
    MU_ANGMAX] = idx_brch;
  [CT_LABEL, CT_PROB, CT_TABLE, CT_TBUS, CT_TGEN, CT_TBRCH, CT_TAREABUS, ...
    CT_TAREAGEN, CT_TAREABRCH, CT_ROW, CT_COL, CT_CHGTYPE, CT_REP, ...
    CT_REL, CT_ADD, CT_NEWVAL, CT_TLOAD, CT_TAREALOAD, CT_LOAD_ALL_PQ, ...
    CT_LOAD_FIX_PQ, CT_LOAD_DIS_PQ, CT_LOAD_ALL_P, CT_LOAD_FIX_P, ...
    CT_LOAD_DIS_P, CT_TGENCOST, CT_TAREAGENCOST, CT_MODCOST_F, ...
    CT_MODCOST_X] = idx_ct;
  [GEN_BUS, PG, QG, QMAX, QMIN, VG, MBASE, GEN_STATUS, PMAX, PMIN, ...
    MU_PMAX, MU_PMIN, MU_QMAX, MU_QMIN, PC1, PC2, QC1MIN, QC1MAX, ...
    QC2MIN, QC2MAX, RAMP_AGC, RAMP_10, RAMP_30, RAMP_Q, APF] = idx_gen;
  [PW_LINEAR, POLYNOMIAL, MODEL, STARTUP, SHUTDOWN, NCOST, COST] = idx_cost;
  unresp = struct( ...
    'type', 'mpcData', ...
    'table', CT_TBUS, ...
    'rows', [1, 2, 3, 4, 5, 6, 7, 8], ...
    'col', PD, ...
    'chgtype', CT_REP, ...
    'values', [] );
  scale = 1.000;
  unresp.values(:, 1, 1) = scale * [7182.65; 6831.0; 6728.83; 6781.1; 6985.44; 7291.94; 7650.72; 8104.54; 8522.71; 8874.36; 9173.74; 9446.98; 9736.85; 10078.99; 10466.28; 10855.94; 11179.08; 11319.26; 11200.46; 10893.96; 10630.22; 10326.1; 9781.99; 8810.21];
  unresp.values(:, 1, 2) = scale * [7726.69; 6840.09; 6637.09; 6603.94; 6719.95; 6972.67; 7295.82; 7693.55; 8140.99; 8518.01; 8837.02; 9114.6; 9383.9; 9686.33; 10046.77; 10436.22; 10800.8; 11053.52; 11078.38; 10862.95; 10560.51; 10311.93; 9930.77; 9255.46];
  unresp.values(:, 1, 3) = scale * [162.23; 150.74; 147.38; 147.58; 151.14; 157.34; 164.74; 174.24; 183.88; 191.86; 198.73; 204.8; 210.94; 218.0; 226.31; 234.89; 242.62; 247.1; 246.18; 240.24; 233.97; 228.03; 218.06; 200.84];
  unresp.values(:, 1, 4) = scale * [2097.83; 1715.67; 1634.79; 1612.55; 1625.69; 1676.24; 1750.04; 1836.99; 1946.17; 2045.25; 2129.17; 2200.95; 2265.65; 2335.41; 2418.31; 2511.32; 2604.34; 2680.16; 2712.51; 2681.17; 2608.38; 2544.69; 2470.88; 2337.43];
  unresp.values(:, 1, 5) = scale * [3922.54; 3492.58; 3390.92; 3376.09; 3437.51; 3568.83; 3731.92; 3937.36; 4163.99; 4356.73; 4519.81; 4661.72; 4801.51; 4956.12; 5140.39; 5337.36; 5523.74; 5650.82; 5663.53; 5549.16; 5396.66; 5267.47; 5070.49; 4723.14];
  unresp.values(:, 1, 6) = scale * [232.03; 198.01; 191.14; 189.66; 192.44; 199.23; 208.37; 219.33; 232.2; 243.34; 252.82; 260.91; 268.66; 277.18; 287.27; 298.32; 309.02; 316.94; 318.77; 313.37; 304.59; 297.45; 287.36; 269.27];
  unresp.values(:, 1, 7) = scale * [2650.16; 2535.62; 2503.87; 2529.95; 2610.47; 2727.27; 2864.48; 3034.58; 3187.67; 3315.82; 3425.81; 3527.87; 3636.74; 3766.01; 3911.17; 4055.18; 4170.85; 4212.81; 4159.51; 4043.84; 3947.45; 3827.25; 3612.92; 3213.76];
  unresp.values(:, 1, 8) = scale * [56.55; 51.95; 50.65; 50.57; 51.68; 53.72; 56.25; 59.4; 62.76; 65.57; 67.97; 70.06; 72.15; 74.53; 77.34; 80.29; 83.0; 84.73; 84.61; 82.72; 80.5; 78.53; 75.32; 69.74];
end