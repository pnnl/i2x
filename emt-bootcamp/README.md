# Materials for EMT Bootcamps 

This repository contains presentations and examples for the NERC/i2X
bootcamps in electromagnetic transient (EMT) modeling of inverter-based
resources (IBR).

## Pre-session Slides

- [Introductory slides](EMT_Bootcamp_July_27.pdf)
- [EMTP slides](EMTP/EMTP_training_session_1.pdf)
- PSCAD slides will be posted later

## Obtaining Models and Data Files

There are two options available:

1. Download a zip file just before each session:
   - [Plant-Level Session](Plant-Level.zip)
   - Extract the contents into a local directory.
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
   - Enter **pip install matplotlib scipy plotly** for plotting and numerical support, see [Matplotlib](https://matplotlib.org/), [numpy](https://numpy.org/doc/stable/user/index.html), and [scipy](https://scipy.org/), [plotly](https://plotly.com/python/getting-started/).
   - Enter **pip install jupyter ipympl** for a browser-based interface to Python, see [Jupyter Notebook](https://jupyter.org).

To test these installations:

1. In Windows Explorer, double-click on the batch script **notebook.bat**, which you'll find in the **python** subdirectory of your local copy of this repository. This will open a command prompt in the background, which starts the notebook server.
   - Alternatively, you may open a Command Prompt from the Start / Windows System menu, change to the python subdirectory in your local copy of this repository, and enter **jupyter notebook cplot.ipynb** from the command prompt.
2. Your browser should start display some code from the notebook, and possibly some saved text results, but no plot.
3. Click the **run** button on the notebook's toolbar **4 times**.  A plot should appear at the bottom of the browser.
4. When finished, close the browser's notebook tab.
5. To shut down the notebook server, enter **Ctrl-C** in the **Command Prompt** window, or just close that window.

Some hints in case of trouble:

1. When installing packages without admin privilege, pip tries to install them in user directories. Users can encounter SSL certificate errors, which may be resolved following [these instructions](https://jhooq.com/pip-install-connection-error/).
2. Python directories may be added to the PATH, without admin privileges, using [Rapid Environment Editor](https://www.rapidee.com/en/about).

Copyright 2022-2023, Battelle Memorial Institute

