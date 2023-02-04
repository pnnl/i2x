# Interconnection Innovation e-Xchange (i2x) Open Test Systems 

This repository contains open grid network models and modeling scripts to 
test and compare different factors/measures (e.g., technoeconomic, social, 
equity, and engineering) that examine practices and policies for 
interconnection queue management and cost allocation.  This repository is 
used for engineering training bootcamps, interconnection study guides, and 
an interconnection roadmap for the [i2x project](https://energy.gov/i2x).  

## Users

The i2x DER package has been tested on Windows only, with Python 3.10. It
should work on Mac OS X and Linux as well, but this has not been tested yet.
During the installation process, a version of OpenDSS will be installed
to work with the Python interface, i.e., you do not have to install OpenDSS
separately. The steps are:

1. Install Python 3 if necessary. This is available from [Python Site](https://python.org), [Anaconda/Miniconda](https://www.anaconda.com/), or the [Microsoft Store](https://apps.microsoft.com/store/detail/python-310/9PJPW5LDXLZ5).
2. From a command prompt, `pip install i2x --upgrade`

Once installed, invoke the GUI from a command prompt: `i2x-der`

## Developers

The steps for deployment to PyPi are:

1. `rm -rf dist`
2. `python -m build`
3. `twine check dist/*` should not show any errors
4. `twine upload -r testpypi dist/*` requires project credentials for i2x on test.pypi.org
5. `pip install -i https://test.pypi.org/simple/ i2x==0.0.2` for local testing of the deployable package, example version 0.0.2
6. `twine upload dist/*` final deployment; requires project credentials for i2x on pypi.org

## License

See [License](license.txt)

## Notice

This material was prepared as an account of work sponsored by an agency of the United States Government.  Neither the United States Government nor the United States Department of Energy, nor Battelle, nor any of their employees, nor any jurisdiction or organization that has cooperated in the development of these materials, makes any warranty, express or implied, or assumes any legal liability or responsibility for the accuracy, completeness, or usefulness or any information, apparatus, product, software, or process disclosed, or represents that its use would not infringe privately owned rights.
Reference herein to any specific commercial product, process, or service by trade name, trademark, manufacturer, or otherwise does not necessarily constitute or imply its endorsement, recommendation, or favoring by the United States Government or any agency thereof, or Battelle Memorial Institute. The views and opinions of authors expressed herein do not necessarily state or reflect those of the United States Government or any agency thereof.

    PACIFIC NORTHWEST NATIONAL LABORATORY
                operated by
                 BATTELLE
                 for the
     UNITED STATES DEPARTMENT OF ENERGY
      under Contract DE-AC05-76RL01830

Copyright 2022-2023, Battelle Memorial Institute
