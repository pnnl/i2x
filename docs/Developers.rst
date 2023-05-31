i2x Tool Developers
===================

Familiarity with ``git`` and Python is expected.  Experience with OpenDSS is also helpful.  The steps for working on the i2x Python code are: 

1. From your local directory of software projects: ``git clone https://github.com/pnnl/i2x.git``
2. ``cd i2x``
3. ``pip install -e .`` to install i2x from your local copy of the code.

The steps for deployment to PyPi are:

1. ``rm -rf dist``
2. ``python -m build``
3. ``twine check dist/*`` should not show any errors
4. ``twine upload -r testpypi dist/*`` requires project credentials for i2x on test.pypi.org
5. ``pip install -i https://test.pypi.org/simple/ i2x==0.0.8`` for local testing of the deployable package, example version 0.0.8
6. ``twine upload dist/*`` final deployment; requires project credentials for i2x on pypi.org

To run the documentation locally:

1. Make sure the required packages are installed. Go to the ``i2x/docs/`` directory and run ``pip install -r Requrirements.txt --upgrade-strategy only-if-needed``
2. From the ``i2x`` directory run: ``sphinx-autobuild docs docs/_build/html``. This will create a live updating webpage at http://127.0.0.1:8000 where the local documentation can be viewed. The server can be shutdown with :kbd:`ctrl+c`.
3. See the `sphinx-guide <https://sublime-and-sphinx-guide.readthedocs.io/en/latest/>`_ for syntax help.


