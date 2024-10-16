function mpc = uc_case
mpc.version = '2';
mpc.baseMVA = 100;
%% bus_i  type  Pd   Qd   Gs   Bs area   Vm   Va baseKV zone Vmax Vmin
mpc.bus = [
 1.0  3.0  7182.65  0.0  0.0  0.0  1.0  1.0  0.0  345.0  1  1.1  0.9;
 2.0  2.0  7726.69  0.0  0.0  0.0  1.0  1.0  0.0  345.0  1  1.1  0.9;
 3.0  2.0   162.23  0.0  0.0  0.0  1.0  1.0  0.0  345.0  1  1.1  0.9;
 4.0  2.0  2097.83  0.0  0.0  0.0  1.0  1.0  0.0  345.0  1  1.1  0.9;
 5.0  2.0  3922.54  0.0  0.0  0.0  1.0  1.0  0.0  345.0  1  1.1  0.9;
 6.0  2.0   232.03  0.0  0.0  0.0  1.0  1.0  0.0  345.0  1  1.1  0.9;
 7.0  2.0  2650.16  0.0  0.0  0.0  1.0  1.0  0.0  345.0  1  1.1  0.9;
 8.0  1.0    56.55  0.0  0.0  0.0  1.0  1.0  0.0  345.0  1  1.1  0.9
];
%% bus  Pg     Qg    Qmax     Qmin   Vg  mBase status     Pmax   Pmin  Pc1 Pc2 Qc1min  Qc1max  Qc2min  Qc2max  ramp_agc  ramp_10 ramp_30 ramp_q  apf
mpc.gen = [
 1.0 10000.0  0.0  6567.0  -6567.0  1.0   1000.0  1.0  19978.8     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 1.0  3000.0  0.0  3834.0  -3834.0  1.0   1000.0  1.0  11664.8     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 1.0  2000.0  0.0  798.7  -798.7    1.0   1000.0  1.0   2430.0     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 2.0  6000.0  0.0  6824.0  -6824.0  1.0   1000.0  1.0  20761.7     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 2.0  2000.0  0.0  1048.6  -1048.6  1.0   1000.0  1.0   3190.3     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 2.0  2000.0  0.0  890.3  -890.3    1.0   1000.0  1.0   2708.6     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 3.0   40.92  0.0  26.3  -26.3      1.0     80.0  1.0     80.0     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 3.0   330.0  0.0  236.7  -236.7    1.0    720.0  1.0    720.0     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 4.0   340.0  0.0  1130.1  -1130.1  1.0   1000.0  1.0   3438.2     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 5.0  2000.0  0.0  3480.7  -3480.7  1.0   1000.0  1.0  10589.7     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 5.0  2000.0  0.0  1882.7  -1882.7  1.0   1000.0  1.0   5728.1     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 7.0  2000.0  0.0  2427.3  -2427.3  1.0   1000.0  1.0   7385.0     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 7.0   330.0  0.0  204.6  -204.6    1.0    622.4  1.0    622.4     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 1.0     0.0  0.0  550.6  -550.6    1.0   1674.8  0.0   1674.8     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 3.0     0.0  0.0  737.0  -737.0    1.0   2242.2  0.0   2242.2     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 4.0     0.0  0.0  2869.5  -2869.5  1.0   8730.3  0.0   8730.3     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 6.0     0.0  0.0  32.8  -32.8      1.0     99.8  0.0     99.8     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 7.0     0.0  0.0  1170.8  -1170.8  1.0   3562.2  0.0   3562.2     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 1.0  -2394.22   0.0     0.0  0.0      1.0   1000.0  1.0   0.0 -2394.22  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 2.0  -2575.57   0.0     0.0  0.0      1.0   1000.0  1.0   0.0 -2575.57  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 3.0    -54.08   0.0     0.0  0.0      1.0   1000.0  1.0   0.0   -54.08  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 4.0   -699.28   0.0     0.0  0.0      1.0   1000.0  1.0   0.0  -699.28  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 5.0  -1307.51   0.0     0.0  0.0      1.0   1000.0  1.0   0.0 -1307.51  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 6.0    -77.34   0.0     0.0  0.0      1.0   1000.0  1.0   0.0   -77.34  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 7.0   -883.39   0.0     0.0  0.0      1.0   1000.0  1.0   0.0  -883.39  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
 8.0    -18.85   0.0     0.0  0.0      1.0   1000.0  1.0   0.0   -18.85  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0
];
%% bus  tbus       r         x        b   rateA   rateB   rateC ratio angle status angmin angmax
mpc.branch = [
 5.0  6.0  0.0042376 0.0358982  2.48325  2168.0  2168.0  2168.0  0.0  0.0  1.0  -360.0  360.0;
 4.0  5.0  0.0024809 0.0210167 13.08450  6504.0  6504.0  6504.0  0.0  0.0  1.0  -360.0  360.0;
 4.0  6.0  0.0059792 0.0506525  3.50388  2168.0  2168.0  2168.0  0.0  0.0  1.0  -360.0  360.0;
 1.0  2.0  0.0061586 0.0521727  3.60905  2168.0  2168.0  2168.0  0.0  0.0  1.0  -360.0  360.0;
 2.0  7.0  0.0062152 0.0526516  3.64217  2168.0  2168.0  2168.0  0.0  0.0  1.0  -360.0  360.0;
 1.0  5.0  0.0058505 0.0495622  3.42847  2168.0  2168.0  2168.0  0.0  0.0  1.0  -360.0  360.0;
 4.0  8.0  0.0063891 0.0541249  3.74409  2168.0  2168.0  2168.0  0.0  0.0  1.0  -360.0  360.0;
 6.0  7.0  0.0059465 0.0503755  3.48473  2168.0  2168.0  2168.0  0.0  0.0  1.0  -360.0  360.0;
 2.0  5.0  0.0014728 0.0124769  7.76783  6504.0  6504.0  6504.0  0.0  0.0  1.0  -360.0  360.0;
 1.0  4.0  0.0078791 0.0667473  4.61724  2168.0  2168.0  2168.0  0.0  0.0  1.0  -360.0  360.0;
 3.0  4.0  0.0043923 0.0372097  2.57398  2168.0  2168.0  2168.0  0.0  0.0  1.0  -360.0  360.0;
 5.0  7.0  0.0049678 0.0420845  2.91120  2168.0  2168.0  2168.0  0.0  0.0  1.0  -360.0  360.0;
 1.0  3.0  0.0042162 0.0357173  5.55918  3252.0  3252.0  3252.0  0.0  0.0  1.0  -360.0  360.0
];
%% either 1 startup shutdown n x1 y1  ... xn  yn
%%   or 2 startup shutdown n c(n-1) ... c0
%% resp_c1 = 40.0;
mpc.gencost = [
 2.0 20.0 10.0  2.0   36.0  2230.0;
 2.0 20.0 10.0  2.0   19.3  2128.0;
 2.0 20.0 10.0  2.0    8.2  1250.0;
 2.0 20.0 10.0  2.0   56.5  2230.0;
 2.0 20.0 10.0  2.0   19.1  2128.0;
 2.0 20.0 10.0  2.0    8.0  1250.0;
 2.0 20.0 10.0  2.0   57.04   10.0;
 2.0 20.0 10.0  2.0   19.0  2128.0;
 2.0 20.0 10.0  2.0   57.03   10.0;
 2.0 20.0 10.0  2.0   45.0  2230.0;
 2.0 20.0 10.0  2.0   19.2  2128.0;
 2.0 20.0 10.0  2.0   50.3  2230.0;
 2.0 20.0 10.0  2.0   19.5  2128.0;
 2.0 10.0 10.0  2.0   1.01  10.0;
 2.0 10.0 10.0  2.0   1.01  10.0;
 2.0 10.0 10.0  2.0   1.01  10.0;
 2.0 10.0 10.0  2.0   1.01  10.0;
 2.0 10.0 10.0  2.0   1.01  10.0;
 2.0  0.0  0.0  2.0   40  90.0;
 2.0  0.0  0.0  2.0   41  90.0;
 2.0  0.0  0.0  2.0   42  90.0;
 2.0  0.0  0.0  2.0   43  90.0;
 2.0  0.0  0.0  2.0   44  90.0;
 2.0  0.0  0.0  2.0   45  90.0;
 2.0  0.0  0.0  2.0   46  90.0;
 2.0  0.0  0.0  2.0   47  90.0
];

mpc.gentype = {
  'GT';
  'ST';
  'ST';
  'GT';
  'ST';
  'ST';
  'GT';
  'ST';
  'GT';
  'GT';
  'ST';
  'GT';
  'ST';
  'WT';
  'WT';
  'WT';
  'WT';
  'WT';
  'DL';
  'DL';
  'DL';
  'DL';
  'DL';
  'DL';
  'DL';
  'DL';
};

%% generator fuel type (see GENFUELS); use wind, solar, hydro, nuclear, ng, coal, dl
mpc.genfuel = {
  'ng';
  'coal';
  'nuclear';
  'ng';
  'coal';
  'nuclear';
  'ng';
  'coal';
  'ng';
  'ng';
  'coal';
  'ng';
  'coal';
  'wind';
  'wind';
  'wind';
  'wind';
  'wind';
  'dl';
  'dl';
  'dl';
  'dl';
  'dl';
  'dl';
  'dl';
  'dl';
};

