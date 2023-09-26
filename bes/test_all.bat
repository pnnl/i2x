rem Matpower and MOST
python mpow.py
python most.py

rem IEEE 118-bus hca
python hca_prep.py 0
python hca.py test_118.json
rem python hca.py IEEE118_prep.json
python grid_upgrades.py 0

rem WECC 240-bus hca
python hca_prep.py 1
python hca.py test_240.json
rem python hca.py WECC240_prep.json
python grid_upgrades.py 1

rem IEEE 39-bus hca
python hca_prep.py 2
python hca.py IEEE39_prep.json
python grid_upgrades.py 2


