# DER Bootcamp
This folder contains materials for the the DER Bootcamp on October 23rd, 2023 taking place as part of GridTech Connect in Newport Rhode Island.

## Installation/Setup Instructions
> **Note:** Due to some of the software tools we'll be using, chiefly OpenDSS via the [py-dss-interface](https://py-dss-interface.readthedocs.io/en/latest/) only the Windows operating system is full supported.

To make sure and avoid any conflicts, it is **strongly** recommended that a dedicated environment be created for the purposes of this bootcamp and its exercises.
### Step 1: Environment Manager
We recommend using [Miniconda](https://docs.conda.io/projects/miniconda/en/latest/) as an environment manager.
If Miniconda (or Anaconda) is not already installed on your machine:
1. Go to https://docs.conda.io/projects/miniconda/en/latest/
2. Select the latest version
3. Run the installer

It is _not_ recommended to add miniconda to your PATH.

### Step 2: Setup the environment
1. Start either the "Anaconda Prompt (miniconda3)" or "Anaconda Powershell Prompt (miniconda3)", based on terminal preference.
2. create a new environment via `conda create --name der-bootcamp python=3.10`
3. Activate the new environment: `conda activate der-bootcamp`
4. Install the i2x package via [pip](https://pypi.org/project/pip/) `pip install i2x`
5. We'll need a few other packages for running the [jupyter notebooks](https://jupyter.org/) with the exercises. Run the command `conda install jupyter notebook nbformat chardet cchardet`

### Step 3: Run the excersizes
1. (TEMPORARY SOLUTION) Download i2x repository by:
    * Going to https://github.com/pnnl/i2x/tree/develop
    * Click on the "<> Code" button and select "Download ZIP"
    * Extract the downloaded ZIP file
    * The folder we'll be working in is called `der-bootcamp`. You can keep it where it is or move it elsewhere if you'd like.
2. Start either the "Anaconda Prompt (miniconda3)" or "Anaconda Powershell Prompt (miniconda3)", based on terminal preference.
3. Activate the der-bootcamp environment: `conda activate der-bootcamp`
4. Navigate to the location of the der-bootcamp folder using the `cd` command.
5. Start the jupyter notebook via `jupyter notebook`

The last step will open a web browser tab showing the file tree of the der-bootcamp folder.
All activities and materials are in this folder.
The activities are jupyter notebooks and end with `.ipynb`.

To start an activity simply click on the jupyter notebook in the file tree.
