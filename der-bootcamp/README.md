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
3. Run the installer (sticking with the default options is just fine.)

It is _not_ recommended to add miniconda to your PATH.

### Step 2: Setup the environment
> **VPN and Proxy** if you are connecting to the internet via a company VPN or Proxy, you may run into some issues with the `conda` and `pip` installation commands.
> If you can, try turning the VPM off.
> If you can't, or that doesn't work, go to the [Dealing with Proxy Issues Section](#dealing-with-proxy-issues) for some suggested solutions.

1. Start either the "Anaconda Prompt (miniconda3)" or "Anaconda Powershell Prompt (miniconda3)", based on terminal preference.
    * Click on the Windows-Start menu and search for one of these
2. Create a new environment via `conda create --name der-bootcamp python=3.10`
    * When asked to proceed, entry `y` and click `Enter`
3. Activate the new environment: `conda activate der-bootcamp`
    * After this you should see `(der-bootcamp)` at the start of the command line. 
4. Install the i2x package via [pip] by entering (https://pypi.org/project/pip/) `pip install i2x` in the command line.
    * _Note_: This might take a couple minutes. When it's done the `(der-bootcamp) >` at the start of the line will reappear.
5. We'll need a few other packages for running the [jupyter notebooks](https://jupyter.org/) with the exercises. Run the command `conda install jupyter notebook nbformat chardet cchardet`
    * When asked to proceed, enter `y` and click `Enter` 
### Step 3: Run the excersizes
1. Download the [der-bootcamp.zip](./der-bootcamp.zip) file and unpack it.
    * To download click the link above and then click on the download arrow on the right side of the screen:
    ![](./figs/download_zip_file_1.png)
    * To unzip the folder _right-click_ and select "Extract All..."
2. Start either the "Anaconda Prompt (miniconda3)" or "Anaconda Powershell Prompt (miniconda3)", based on terminal preference.
3. Activate the der-bootcamp environment: `conda activate der-bootcamp`
4. Navigate to the location of the unpacked der-bootcamp folder using the `cd` command.
    * For example, if the extracted folder is located at "C:\Users\myuser\Desktop\der-bootcamp\" then enter the command `cd C:\Users\myuser\Desktop\der-bootcamp`
    * To get the path to the folder you can open it in the file explorer and copy the path out of the folder path bar:<br>
    ![](./figs/get_derbootcamp_path.png)
5. Start the jupyter notebook via `jupyter notebook`

The last step will open a web browser tab showing the file tree of the der-bootcamp folder.
All activities and materials are in this folder.
The activities are jupyter notebooks and end with `.ipynb`.

To start an activity simply click on the jupyter notebook in the file tree (see the [Running Jupyter Notebooks Section](#running-jupyter-notebooks)).

Try out the [getting_started](./getting_started.ipynb) notebook to see that everything is running properly.

## Running Jupyter Notebooks
Jupyter notebooks are comprized of _cells_.
To move through a jupyter notebook simply run each cell.
This can be done either by:
* Clicking the _Run_ button at the top of the page, or
* Press _Shift+Enter_ on the keyboard.

## Current status of .zip file to download
This table links to the most recent zip file with the bootcamp materials, along with latest update and status note.

| zip file link| last updated | status |
|:------------ | :---------- | :----- |
|[der-bootcamp.zip](./der-bootcamp.zip) | Oct. 18, 2023 | In development, good for environment testing, not final|

## Dealing with Proxy Issues
### Conda
To resolve proxy issues with conda try disabling ssl verification:
```
>conda config --set ssl_verify false 
```

Note, it is probably best to turn ssl verification back on when you're done via:
```
>conda config --set ssl_verify true 
```

### Pip
The following seems to work to resolve ssl issues with pip:
```
>pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org <package>
```
So to install the `i2x` package try:
```
>pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org i2x
```