# IEEE C57.91 Edit

This code was modified to investigate inadvertent export events at the seconds timescale. The original, IEEE C57.91 Thermal Models repository that was modified for this work is found here: [link](https://opensource.ieee.org/inslife/ieee-c57.91-thermal-models).

Time scale modifications have been made to the following under
`transformer_thermal_models`:  
- `ageing.py`
- `data_classes.py`
- `plotting.py`

In addition, `Thermal_Modeling_UI_Example_Voila_EDIT.ipynb` was created based on the original `Thermal_Modeling_UI_Example.Voila.ipynb` to be the main notebook to explore these effects. 

## IEEE C57.91-202X
This code was developed to implement the hotspot in windings model for powers transformers as described in _IEEE C57.91 Guide for Loading Mineral-Oil-Immersed Transformers and Step-Voltage Regulators_.

The code is based in Python and additional package requirements are listed in `requirements.txt`

## Disclaimer

This open source repository contains material that may be included-in or referenced by an unapproved draft of a proposed IEEE Standard. All material in this repository is subject to change. The material in this repository is presented "as is" and with all faults. Use of the material is at the sole risk of the user. IEEE specifically disclaims all warranties and representations with respect to all material contained in this repository and shall not be liable, under any theory, for any use of the material. Unapproved drafts of proposed IEEE standards must not be utilized for any conformance/compliance purposes.

## New to Python

### Windows Executable

Download the code as a zip file and put in a directory. Once you install Python on a windows machine [link](https://learn.microsoft.com/en-us/windows/python/beginners), you can double click the 'Executable.bat' file. That file will install the python packages required and open a web browser with a UI that can run the code.

### JupyterLab

For more advanced interaction, it is recommended that you use [JupyterLab](https://github.com/jupyterlab/jupyterlab-desktop#installation).  This IDE will allow novice users to open and run jupyter notebooks (*.ipynb files) and execute the python code locally on thier computer.

Download the files from this repository to a local folder and open one of the *.ipynb files in the Notebooks folder using JupyterLab.  Refer to JupyterLab documentation for executing notebook files. For example, click on a cell of code and press Shift+Enter to execute the code.  Or use the top double right arrow to run and execute all code cells.

## Python users

`git clone` or download a zip file of the contents to a local folder and run `pip install <path_to_folder>`.

### Voila

You can load a basic UI for running the thermal models by executing via command line:

`voila Thermal_Modeling_UI_Example_Voila.ipynb` 

from within the Notebooks folder.

### As a module

You can also execute the code like a module using:

`import transformer_thermal_models`

An example is shown in the jupyter Notebook directory `Notebooks/Thermal_Modeling_Example.ipynb`.

## Code

The code has two primary classes `Transformer` and `LoadConditions`.  

The `Transformer` class contains static thermal properties associated with the transformer required to execute the models. 

The `LoadConditions` class contains the time varrying input data required for the modeling.  At a minimum, time, ambient temperature, and load are required.

Models for solving the hotspot temperatures are functions that will operate on the two classes as inputs.  Currently the module supports 3 methods for solving temperatures. The purpose of including them is for experimentation purposes. The guide itself would recommend the Main Clause 7 method from the latest editition of C57.91.  However, if there were insuffecient information (like an unknown bottom rated temperature), then the Alternative Clause 7 method could be used. The Old Clause 7 from C57.91-2011 is included for reference.

1.   C57.91-202X Main Clause 7 using differential equations with Runge-Kutta solver. 
1.   C57.91-202X Alternative Clause 7 using differential equations with Runge-Kutta solver. 
1.   C57.91-2011 Old Clause 7 using a simplified anlytical solution to the old clause 7 differential equations. 

Because the model uses differnetial equations, how you actaully solve thoose equations can matter under certain circumstances. Subtle differences have been noted between methods.  First, the differential equations method with a Runge-Kutta solver generally respond more quickly to changing load conditions compared to solving ODE equations using a finite difference method, potentially making it more accurate for rapid changes in loading conditions.  Furthermore, the maximum acheived hostpot temperature may vary depending on how long overloading conditions last.  

It was found that the Clause 7 of the 2011 version of C57.91 was effectively identical to Annex G mathematically, except that a series of assumptions are made that may not always be true.  However, the simplified assumptions in the old Clause 7 make it possible to attempt to model the hotspot temperature for older transformers that may not have all of the required nameplate properties (like the bottom oil rise temperature).  In that case, there is also the Alternative Clause 7 in the current revision of C57.91.

Optimizing the static thermal properties of the transformer by using real data is not covered here.  Therefore certain transformer designs may not be well modeled. Using temperature data from heat run tests could be used to optimize the nameplate properties in order to better model the hotspot temperature while in the field.  For that to be done, this model could be run iteratively to converge on the best parameters. Furthermore, the locations of temperature probes may not accurately reflect the location of the temperatures that are being modeled, so care should be taken when trying to optimize static thermal properties to better predict the modeled hotspot and top oil temperatures.

## Load Conditions Data Format

Accepted file format is a CSV file with the following column headers:

- "Time" in ISO datetime format (YYYY-mm-dd HH:MM:SS), _required_
    - or "Minutes" [minutes],
    - or "Hours" [decimal hours]
- "Ambient" as ambient temperature [C], _required_
- "Load" as fraction of rated load [0-10], _required_

## Known Issues

1. During low load conditions (<0.1) and cases where the ambient temperature exceeds the internal temperature of the transformer, the solution to the set of equations can become unstable. There are NaN values and instances where the root of a negative number is taken resulting in imaginary numbers.  To get around this, temporary exceptions are made to the eqations to continue the calculations.  For imaginary numbers the absolute value of the negative is taken and the heat is modified by the sign of the offending quantity.  The result is that peculiar step functions or spikes can occur in the temperature values before returning to "normal" values based on the model equations. Theese features are almost surely inaccurate compared to reality.

2. Not all external sources of heat transfer are modeled here.  For example, solar irradiance and wind may also influence the transformers temperature, particularly for smaller transformers.


## License 

Copyright 2022 C57.91 Open Source Authors (see AUTHORS.md)
Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:


1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.


2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.


3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.


THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

SPDX-License-Identifier: BSD-3-Clause
