# Test Directory

This repository contains command-line test scripts, and an auxiliarly 
script that creates smooth daily loadshapes for hosting capacity analysis.  
OpenDSS uses zero-order interpolation, also known as piecewise-constant.  
For analysis of solar fluctuations at sub-hourly time steps, we prefer to 
smooth aggregate load variations to more realistic behavior.  We are using 
the *quadratic* option by default, noting that GridLAB-D also uses 
quadratic interpolation.  As shown in the following table, both 
*quadratic* and *cubic* interpolants have slightly different minima and 
maxima from the original values.  
 
    Default   Min/Max = [0.5803,1.0000]
    Linear    Min/Max = [0.5803,1.0000]
    Quadratic Min/Max = [0.5784,1.0041]
    Cubic     Min/Max = [0.5781,1.0042]
 
[Interpolated Loadshapes](loadshapes.png). 
*Interpolated loadshapes from OpenDSS default hourly shape*

## Files in this Repository

- **dss.py**; testing focused on py\_dss\_interface
- **i2xDER.py**; testing focused on i2x functionality
- **interface\_functions.txt**; brief listing of py\_dss\_interface methods
- **make\_loadshape.py**; interpolate the default OpenDSS piecewise hourly loadshape to smoothed 1-second intervals

Copyright 2022-2023, Battelle Memorial Institute

