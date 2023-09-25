rem Wind Plant Data

python wind_plants.py 150
python test_wind.py 150

rem 3-day unit commitment with variable wind

python prep_most_profiles.py 0 72
python most_mday.py
python plot_mday.py

rem BES hosting capacity

python hca_prep.py
python hca.py hca_all.json
python hca.py hca_one.json
python plot_hca.py
python grid_upgrades.py

rem auction and queue simulation

python impact.py

