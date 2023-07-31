# PSCAD Materials for EMT Bootcamps 

This repository contains presentations and examples for the NERC/i2X
bootcamps in electromagnetic transient (EMT) modeling of inverter-based
resources (IBR).

- use py test.py or python test.py after taking the following two steps
- C:\Users\Public\Documents\Manitoba Hydro International\Python\Packages>pip install  mhi\_common-2.3.9-py3-none-any.whl
- C:\Users\Public\Documents\Manitoba Hydro International\Python\Packages>pip install mhi\_pscad-2.9.0-py3-none-any.whl

## Pre-session Slides

- [Introductory slides](EMT_Bootcamp_July_27.pdf)
- [EMTP slides](EMTP/EMTP_training_session_1.pdf)
- [PSCAD slides](PSCAD)

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
   - Enter **pip install jupyter** for a browser-based interface to Python, see [Jupyter Notebook](https://jupyter.org).
   - Enter **pip install matplotlib** for plotting and numerical support, see [Matplotlib](https://matplotlib.org/) and [numpy](https://numpy.org/doc/stable/user/index.html).

To test these installations:

1. Open a **Command Prompt** from the Start / Windows System menu.
2. Change to the **python** subdirectory of your local copy of this repository.
3. Enter the command **jupyter notebook cplot.ipynb** from the command prompt. Your browser should start display some code and saved text results, but no plot.
4. Click the **run** button on the notebook's toolbar **3 times**.  A plot should appear at the bottom of the browser.
5. When finished, enter **Ctrl-C** in the **Command Prompt** window, which shuts down the notebook server.

Copyright 2022-2023, Battelle Memorial Institute

