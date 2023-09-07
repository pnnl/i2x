# PSCAD Materials for EMT Bootcamps 

This repository contains presentations and examples for the PSCAD track of 
the NERC/i2X bootcamps in electromagnetic transient (EMT) modeling of 
inverter-based resources (IBR).
 
You may obtain PSCAD models by downloading a zip file, one directory
above this one:
 
- [Plant-Level Session](../Plant-Level.zip) 

## Directory of PSCAD Files

The PSCAD **Version 5** models and scripts located here include:

- **EMT\_Boot\_Camp\_WS.pswx**; a workspace for the examples
- **Solar\_SMIB\_S?\*.pscx**; a series of 6 example cases, where **?** numbers them sequentially from 0 to 5. These contain a switching-model of a 100-MW solar plant.
- **Solar\_Lib.pslx**; components and subsystems to support the IBR plant models.
- **Backup/**; baseline copies of the 6 example cases, used to restore from your local changes if needed.
- **Machine2.pscx**; a project with rotating machine in the plant model test circuit.
- **Solar2.pscx**; a project with IBR in the plant model test circuit.
- **Solar3avm.pscx**; an IBR with average model, for comparison to switching model.
- **Solar3dm.pscx**; an IBR with switching model, for comparison to average model.
- **Solar4.pscx**; a plant model test circuit, set up for automated fault simulations.
- **FaultScript.py**; a Python script that applies 12 faults to *Solar4.pscx*
 
The PSCAD **Version 4.6** models are at:

- **PSCAD\_V4/EMT\_Boot\_Camp\_WS\_V4.pswx**; a workspace for the examples
- **PSCAD\_V4/Solar\_SMIB\_S?\*\_V4.pscx**; a series of 6 example cases, where **?** numbers them sequentially from 0 to 5. These contain a switching-model of a 100-MW solar plant.
- **PSCAD\_V4/Solar\_Lib\_V4.pslx**; components and subsystems to support the IBR plant models.
- **PSCAD\_V4/Backup/**; baseline copies of the 6 example cases, used to restore from your local changes if needed.

In addition, data located here includes:

- **COMTRADEtest/**; a directory of saved COMTRADE output for post-processing exercises

Copyright 2022-2023, Battelle Memorial Institute

