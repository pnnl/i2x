declare -r TESP_SUPPORT=$TESP_INSTALL/share/support
declare -r SCHED_PATH=$TESP_SUPPORT/schedules

gridlabd -D WANT_VI_DUMP -D SCHED_PATH=$SCHED_PATH -D METRICS_FILE=soco_test_metrics.json soco_test.glm

