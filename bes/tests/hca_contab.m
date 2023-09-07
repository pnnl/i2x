function chgtab = hca_contab
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
  %	label	prob	table	row	col	chgtype	newval
  chgtab = [
     1 0.0714286 CT_TBRCH   1 BR_R      CT_REP   0.0084752;
     1 0.0714286 CT_TBRCH   1 BR_X      CT_REP   0.0717964;
     1 0.0714286 CT_TBRCH   1 BR_B      CT_REP     1.24162;
     1 0.0714286 CT_TBRCH   1 RATE_A    CT_REP    1084.000;
     1 0.0714286 CT_TBRCH   1 RATE_B    CT_REP    1084.000;
     1 0.0714286 CT_TBRCH   1 RATE_C    CT_REP    1084.000;
     2 0.0714286 CT_TBRCH   2 BR_R      CT_REP   0.0029771;
     2 0.0714286 CT_TBRCH   2 BR_X      CT_REP   0.0252200;
     2 0.0714286 CT_TBRCH   2 BR_B      CT_REP    10.90375;
     2 0.0714286 CT_TBRCH   2 RATE_A    CT_REP    5420.000;
     2 0.0714286 CT_TBRCH   2 RATE_B    CT_REP    5420.000;
     2 0.0714286 CT_TBRCH   2 RATE_C    CT_REP    5420.000;
     3 0.0714286 CT_TBRCH   3 BR_R      CT_REP   0.0119584;
     3 0.0714286 CT_TBRCH   3 BR_X      CT_REP   0.1013050;
     3 0.0714286 CT_TBRCH   3 BR_B      CT_REP     1.75194;
     3 0.0714286 CT_TBRCH   3 RATE_A    CT_REP    1084.000;
     3 0.0714286 CT_TBRCH   3 RATE_B    CT_REP    1084.000;
     3 0.0714286 CT_TBRCH   3 RATE_C    CT_REP    1084.000;
     4 0.0714286 CT_TBRCH   4 BR_R      CT_REP   0.0123172;
     4 0.0714286 CT_TBRCH   4 BR_X      CT_REP   0.1043454;
     4 0.0714286 CT_TBRCH   4 BR_B      CT_REP     1.80452;
     4 0.0714286 CT_TBRCH   4 RATE_A    CT_REP    1084.000;
     4 0.0714286 CT_TBRCH   4 RATE_B    CT_REP    1084.000;
     4 0.0714286 CT_TBRCH   4 RATE_C    CT_REP    1084.000;
     5 0.0714286 CT_TBRCH   5 BR_R      CT_REP   0.0124304;
     5 0.0714286 CT_TBRCH   5 BR_X      CT_REP   0.1053032;
     5 0.0714286 CT_TBRCH   5 BR_B      CT_REP     1.82109;
     5 0.0714286 CT_TBRCH   5 RATE_A    CT_REP    1084.000;
     5 0.0714286 CT_TBRCH   5 RATE_B    CT_REP    1084.000;
     5 0.0714286 CT_TBRCH   5 RATE_C    CT_REP    1084.000;
     6 0.0714286 CT_TBRCH   6 BR_R      CT_REP   0.0117010;
     6 0.0714286 CT_TBRCH   6 BR_X      CT_REP   0.0991244;
     6 0.0714286 CT_TBRCH   6 BR_B      CT_REP     1.71423;
     6 0.0714286 CT_TBRCH   6 RATE_A    CT_REP    1084.000;
     6 0.0714286 CT_TBRCH   6 RATE_B    CT_REP    1084.000;
     6 0.0714286 CT_TBRCH   6 RATE_C    CT_REP    1084.000;
     7 0.0714286 CT_TBRCH   7 BR_R      CT_REP   0.0127782;
     7 0.0714286 CT_TBRCH   7 BR_X      CT_REP   0.1082498;
     7 0.0714286 CT_TBRCH   7 BR_B      CT_REP     1.87204;
     7 0.0714286 CT_TBRCH   7 RATE_A    CT_REP    1084.000;
     7 0.0714286 CT_TBRCH   7 RATE_B    CT_REP    1084.000;
     7 0.0714286 CT_TBRCH   7 RATE_C    CT_REP    1084.000;
     8 0.0714286 CT_TBRCH   8 BR_R      CT_REP   0.0118930;
     8 0.0714286 CT_TBRCH   8 BR_X      CT_REP   0.1007510;
     8 0.0714286 CT_TBRCH   8 BR_B      CT_REP     1.74236;
     8 0.0714286 CT_TBRCH   8 RATE_A    CT_REP    1084.000;
     8 0.0714286 CT_TBRCH   8 RATE_B    CT_REP    1084.000;
     8 0.0714286 CT_TBRCH   8 RATE_C    CT_REP    1084.000;
     9 0.0714286 CT_TBRCH   9 BR_R      CT_REP   0.0017674;
     9 0.0714286 CT_TBRCH   9 BR_X      CT_REP   0.0149723;
     9 0.0714286 CT_TBRCH   9 BR_B      CT_REP     6.47319;
     9 0.0714286 CT_TBRCH   9 RATE_A    CT_REP    5420.000;
     9 0.0714286 CT_TBRCH   9 RATE_B    CT_REP    5420.000;
     9 0.0714286 CT_TBRCH   9 RATE_C    CT_REP    5420.000;
    10 0.0714286 CT_TBRCH  10 BR_R      CT_REP   0.0157582;
    10 0.0714286 CT_TBRCH  10 BR_X      CT_REP   0.1334946;
    10 0.0714286 CT_TBRCH  10 BR_B      CT_REP     2.30862;
    10 0.0714286 CT_TBRCH  10 RATE_A    CT_REP    1084.000;
    10 0.0714286 CT_TBRCH  10 RATE_B    CT_REP    1084.000;
    10 0.0714286 CT_TBRCH  10 RATE_C    CT_REP    1084.000;
    11 0.0714286 CT_TBRCH  11 BR_R      CT_REP   0.0087846;
    11 0.0714286 CT_TBRCH  11 BR_X      CT_REP   0.0744194;
    11 0.0714286 CT_TBRCH  11 BR_B      CT_REP     1.28699;
    11 0.0714286 CT_TBRCH  11 RATE_A    CT_REP    1084.000;
    11 0.0714286 CT_TBRCH  11 RATE_B    CT_REP    1084.000;
    11 0.0714286 CT_TBRCH  11 RATE_C    CT_REP    1084.000;
    12 0.0714286 CT_TBRCH  12 BR_R      CT_REP   0.0099356;
    12 0.0714286 CT_TBRCH  12 BR_X      CT_REP   0.0841690;
    12 0.0714286 CT_TBRCH  12 BR_B      CT_REP     1.45560;
    12 0.0714286 CT_TBRCH  12 RATE_A    CT_REP    1084.000;
    12 0.0714286 CT_TBRCH  12 RATE_B    CT_REP    1084.000;
    12 0.0714286 CT_TBRCH  12 RATE_C    CT_REP    1084.000;
    13 0.0714286 CT_TBRCH  13 BR_R      CT_REP   0.0063243;
    13 0.0714286 CT_TBRCH  13 BR_X      CT_REP   0.0535759;
    13 0.0714286 CT_TBRCH  13 BR_B      CT_REP     3.70612;
    13 0.0714286 CT_TBRCH  13 RATE_A    CT_REP    2168.000;
    13 0.0714286 CT_TBRCH  13 RATE_B    CT_REP    2168.000;
    13 0.0714286 CT_TBRCH  13 RATE_C    CT_REP    2168.000;
  ];
end
