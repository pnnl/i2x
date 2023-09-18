# Materials for EMT Bootcamps 

This repository contains presentations and examples for the NERC/i2X
bootcamps in electromagnetic transient (EMT) modeling of inverter-based
resources (IBR).

| Topic | Materials |
| ----- | ----------|
| Pre-session (7/27/2023) | [Intro Slides](EMT_Bootcamp_July_27.pdf)<br>[EMTP Slides](EMTP/EMTP_training_session_1.pdf)<br>[PSCAD Slides](PSCAD/EMT-largescale-simulations.pdf) |
| Plant-Level Session (8/3/2023) | [Slides](EMT_Bootcamp_Aug_3.pdf)<br>[Models](Plant-Level.zip) |
| Comparing rotating machine and IBR behaviors in EMT | [Slides](MachineIBR.pdf)<br>[Models](MachineIBR.zip)<br>[Intro Video](https://youtu.be/xEy14ngf5S8)<br>[EMTP Video](https://youtu.be/hL52Ou9pnms)<br>[PSCAD Video](https://youtu.be/_fqEFi1c2RE) |
| Comparing switching and average models | [Slides](AVMvsSwitching.pdf)<br>[Intro Video](https://youtu.be/I_r8cAxrhbI)<br>[EMTP Video]()<br>[PSCAD Video](https://www.youtube.com/watch?v=puneEQfquRQ) |
| Automation of faults | [Slides](FaultTests.pdf)<br>[Intro Video](https://youtu.be/AfuLv0IZJmg)<br>[EMTP Video]()<br>[PSCAD Video](https://www.youtube.com/watch?v=COSS0iXmNU4) |
| Automation of IEEE P2800.2 type tests | [Slides](PlantTests.pdf)<br>[Intro Video](https://youtu.be/nfA5zHqVcfE)<br>[SCR Test Video](https://youtu.be/c95BJ9WOk04)<br>[EMTP Video]()<br>[PSCAD Video](https://www.youtube.com/watch?v=9WVdVTPErD8)<br>[PSCAD SCR](https://www.youtube.com/watch?v=ExsLqhpGrH0) |
| Automation of system study | [Slides](SystemStudy.pdf)<br>[Intro Video](https://youtu.be/99ZjOcmDR3o)<br>[EMTP Video]()<br>[PSCAD Video](https://www.youtube.com/watch?v=9ci4Qkclt1c) |
| Automation of waveform evaluations | TBD |
| System-Level Session (9/14/2023)<br>Updated 9/18/2023 | [Slides](EMT_Bootcamp_Sep_14.pdf)<br>[Models](System-Level.zip)<br>[PDH Request Form](PDH_Hours.xlsx) |

## Obtaining the Sample Models and Scripts

There are two options available:

1. Download a zip file just before you need it:
   - For example, the [Plant-Level Session Models](Plant-Level.zip)
   - Extract the contents into a local directory. You may use the same local directory each time, i.e., only "safe" updates will be made to earlier files.
   - Because the material is brand new, there may be last-minute updates. We will announce the time of last update as each session begins.
   - You may download individual updated files through the web browser, but make sure they go to the correct relative directory.
2. If you're comfortable using [git](https://git-scm.com/download/win), feel free to clone [the i2X repository](https://github.com/pnnl/i2x/tree/develop). We don't suggest installing git just for this bootcamp.

## Python and Jupyter Notebook Support

We'll be using Python for most of the automation and post-processing
examples in this bootcamp. To prepare your computer for these examples:

1. Install Python 3 if necessary. This is available from [Python Site](https://python.org), 
   [Anaconda/Miniconda](https://www.anaconda.com/), or the 
   [Microsoft Store](https://apps.microsoft.com/store/detail/python-310/9PJPW5LDXLZ5).
   - On the second panel of Python 3's installer, **select the option** that adds Python variables to your system environment, which includes the **path**.
2. Install the Python support packages as necessary:
   - Open a **Command Prompt** from the Start / Windows System menu.
   - Enter **pip install matplotlib scipy plotly** for plotting and numerical support, see [Matplotlib](https://matplotlib.org/), [numpy](https://numpy.org/doc/stable/user/index.html),[scipy](https://scipy.org/), and [plotly](https://plotly.com/python/getting-started/).
   - Enter **pip install jupyter ipympl ipywidgets** for a browser-based interface to Python, see [Jupyter Notebook](https://jupyter.org).

To test these installations:

1. Make sure you have extracted the [Plant-Level Session Models](Plant-Level.zip) to your computer.
2. In Windows Explorer, double-click on the batch script **notebook.bat**, which you'll find in the **python** subdirectory of your local copy of this repository. This will open a command prompt in the background, which starts the notebook server.
   - Alternatively, you may open a Command Prompt from the Start / Windows System menu, change to the python subdirectory in your local copy of this repository, and enter **jupyter notebook cplot.ipynb** from the command prompt.
3. Your browser should start display some code from the notebook, and possibly some saved text results, but no plot.
4. Click the **run** button on the notebook's toolbar **4 times**.  A plot should appear at the bottom of the browser.
5. When finished, close the browser's notebook tab.
6. To shut down the notebook server, enter **Ctrl-C** in the **Command Prompt** window, or just close that window.

Some hints in case of trouble:

1. When installing packages without admin privilege, pip tries to install them in user directories. Users can encounter SSL certificate errors, which may be resolved following [these instructions](https://jhooq.com/pip-install-connection-error/).
2. Python directories may be added to the PATH, without admin privileges, using [Rapid Environment Editor](https://www.rapidee.com/en/about).

Copyright 2022-2023, Battelle Memorial Institute

