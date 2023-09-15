.. role:: math(raw)
   :format: html latex
..
=======
DataHub
=======

The goal of the data hub is to process solarTRACE and queued up (Berkeley lab) data. The solarTRACE data cosists of interconnection timelines for Authority Having Jurisdictions.

1. How the data hub src code is arranged
-----------------------------------

The data hub consists of two modules [solarTRACE (st) and queued up(qu)] run sequentially. The data/main.py file calls the two module drivers (qu first and st second).
The drivers then reach the queued_up and the solarTRACE directories respectively and run the scripts through the input files.

2. How to run the data hub source code
-----------------------------------
.. note:: Running the data hub will take approximately 1hr-1hr:30mins. This is because of the NOMINATIM API used for the solarTRACE module.

From the i2x/data directory on the command line or terminal:

.. code-block:: console

   python main.py
   or
   pytest test_data.py

.. warning:: pytest test_data.py may fail while there are no problems with the code but there is a server or connection error.

3. Triggering the workflow from GitHub actions:
--------------------------------------------
To trigger the workflow to do the calculations using the three input files under i2x\\hubdata\\input directory and putting the output files
in the i2x\\hubdata\\input directory, simply make a change to one of the input files and do:

.. code-block:: console

   git add .
   git commit -m "YOUR MESSAGE HERE"
   git push

Any changes made within the i2x\\hubdata\\input directory will trigger the workflow. You can view the progress within the i2x github repo under the actions tab.
To make changes to how the workflow is run, refer to the python-package.yml under i2x\\.github\\workflows.

.. note:: For suggested improvements refer to the readme.md within the i2x\\data directory.



