i2x Tool Developers
===================

Familiarity with ``git`` and Python is expected.  Experience with OpenDSS is also helpful.  The steps for working on the i2x Python code are: 

1. From your local directory of software projects: ``git clone https://github.com/pnnl/i2x.git``
2. ``cd i2x``
3. ``pip install -e .`` to install i2x from your local copy of the code.

The steps for deployment to PyPi are (Starting in the parent directory of `src`, where ``setup.py`` is located):

0. Make sure that the version number in ``version.py`` is new
1. ``rm -rf dist``: Removes the wheel folder (if exists. use ``rd /s /q dist`` in windows cmd.exe)
2. ``python -m build``: Builds the wheel (note: this can take a while. ``build`` may need to be installed ``conda install build`` or ``pip install build``)
3. ``twine check dist/*`` should not show any errors (This of the wheel. ``twine`` may need to be installed ``conda install twine`` or ``pip install twine``)
4. ``twine upload -r testpypi dist/*`` requires project credentials for i2x on test.pypi.org (Note: this will reject if version already exists, also note that testpypi is a separate register to pypi)
5. ``pip install -i https://test.pypi.org/simple/ i2x==0.0.8`` for local testing of the deployable package, example version 0.0.8 (Note: some might want to this in a separate test environment)
6. ``twine upload dist/*`` final deployment; requires project credentials for i2x on pypi.org (if 2-Factor-Authentication is enabled an `API token <https://pypi.org/help/#apitoken>`_ needs to be used.)

To run the documentation locally:

1. Make sure the required packages are installed. Go to the ``i2x/docs/`` directory and run ``pip install -r Requrirements.txt --upgrade-strategy only-if-needed``
2. From the ``i2x`` directory run: ``sphinx-autobuild docs docs/_build/html``. This will create a live updating webpage at http://127.0.0.1:8000 where the local documentation can be viewed. The server can be shutdown with :kbd:`ctrl+c`.
3. See the `sphinx-guide <https://sublime-and-sphinx-guide.readthedocs.io/en/latest/>`_ for syntax help.


