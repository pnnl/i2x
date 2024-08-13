## HCA Statisicts
```
HC profile statistics:
        length  8760
        min     23260.1
        avg     23953.1
        max     25468.9
        q[10,25,50,75,90]       [23490.6 23732.2 23894.5 24127.6 24415.9]
PV profile profile statistics:
        length  8760
        min     0.0
        avg     0.2
        max     1.0
        q[10,25,50,75,90]       [0.  0.  0.  0.4 0.7]
```
### LGP statistics
#### Daily profile:
```
HC profile statistics:
        length  8760
        min     23260.1
        avg     23472.6
        max     23708.8
        q[10,25,50,75,90]       [23264.1 23285.6 23480.3 23608.9 23705.3]
```
## Short Circuit
```
Active bus is regxfmr_hvmv11sub1_lsb
Testing Zsc * Ysc = I:
[[1.-0.j 0.-0.j 0.-0.j]
 [0.-0.j 1.-0.j 0.+0.j]
 [0.-0.j 0.-0.j 1.-0.j]]
Testing zsc1:
        zsc1 (DSS) = 0.142900+0.938667j zsc1 (calc) = 0.142900+0.938667j        Success
Testing zsc0:
        zsc0 (DSS) = 0.138147+0.763369j zsc1 (calc) = 0.138147+0.763369j        Success

Delta P (kw) leading to ~3% voltage change: 32645.35

========= HCA Round 1 dss time: [0, 0] (pv)=================
Setting bus regxfmr_hvmv11sub1_lsb as active bus
Specified capacity: {'kw': 32645.347632657504, 'kva': 40806.68454082188}
Creating new pv resource pv_regxfmr_hvmv11sub1_lsb_cnt1 with S = {'kw': 32645.347632657504, 'kva': 40806.68454082188}
c:\users\schw197\onedrive - pnnl\documents\02projects\i2x\i2x\src\i2x\der_hca\hca.py:1934: FutureWarning: The behavior of array concatenation with empty 
entries is deprecated. In a future version, this will no longer exclude empty items when determining the result dtype. To retain the old behavior, exclude the empty entries before the concat operation.
  return pd.concat([test1, test2]), pd.concat([margin1[~test1], margin2[~test2]])
Violations with capacity {'kw': 32645.347632657504, 'kva': 40806.68454082188} (allow_violations is True).
        thermal_emerg,thermal_norm_hrs
*******Results for bus regxfmr_hvmv11sub1_lsb (pv) in 0.710 sec
Sij = {'kw': 32645.347632657504, 'kva': 40806.68454082188}
hc = not calculated

Active bus is regxfmr_hvmv11sub1_lsb
Voltage before is 7303.0 V (1.014 pu)
Voltage after  is 7381.8 V (1.025 pu)
Voltage change (w.r.t nominal voltage) due to addition of 32645.35 kW is 1.10%
```

Note that since this is a stronger part of the system the formula for calculating the max delta is conservative and the actual voltage change is only ~1% rather than 3%.

## RVC Limit
```
Max DER Rating - HC = 32645.4 kW
Min HC = 23260.1 kW
Max DER (Option 1): 55905.5 kW
Max DER (Option 2): 56524.3 kW
Option 2 verification:  32645.4 kW
```