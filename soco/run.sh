declare -r TESP_SUPPORT=$TESP_INSTALL/share/support
declare -r SCHED_PATH=$TESP_SUPPORT/schedules

# start a HELICS federation for GridLAB-D, weather and SOCO agent
(exec helics_broker -f 3 --loglevel=1 --name=mainbroker &> broker.log &)
(exec gridlabd -D USE_HELICS -D SCHED_PATH=$SCHED_PATH -D METRICS_FILE=soco_hub_metrics.json soco_test.glm &> gridlabd.log &)
(export WEATHER_CONFIG=weatherConfig.json && exec python3 -c "import tesp_support.api as tesp;tesp.startWeatherAgent('weather.dat')" &> weather.log &)
(export SOCO_CONFIG=socoConfig.json && exec python3 soco.py &> soco.log &)

