# Copyright (C) 2021-22 Battelle Memorial Institute
import json
import os
import sys
import numpy as np
import helics

if sys.platform != 'win32':
  import resource

def refresh_double (sub, val=0.0, scale=1.0):
  if (sub is not None) and helics.helicsInputIsUpdated(sub):
    return scale * helics.helicsInputGetDouble(sub)
  return val

def helics_loop(arg_cfg_filename):
  lp = open(arg_cfg_filename)
  cfg_dict = json.loads(lp.read())
  lp.close()

  app_cfg = cfg_dict['application']
  tmax = app_cfg['Tmax']
  logperiod = app_cfg['LogInterval']
  event_time = app_cfg['EventTime']
  start_date_time = app_cfg['StartTime']
  bess_max_charging = app_cfg['BESS_Max_Charging']
  bess_max_discharging = app_cfg['BESS_Max_Discharging']
  pswing_cap = app_cfg['Pswing_Cap']
  bess_hub_logic = app_cfg['BESSHubLogic']

  h_fed = None
  h_fed = helics.helicsCreateValueFederateFromConfig(arg_cfg_filename)
  fed_name = helics.helicsFederateGetName(h_fed)
  pub_count = helics.helicsFederateGetPublicationCount(h_fed)
  sub_count = helics.helicsFederateGetInputCount(h_fed)
  period = int(helics.helicsFederateGetTimeProperty(h_fed, helics.helics_property_time_period))

  print('Federate {:s} has {:d} pub and {:d} sub, {:d} period'.format(fed_name, pub_count, sub_count, period), flush=True)

  sub_fdr_kw = None
  sub_bess_kw = None
  sub_bess_soc = None
  sub_pv_kw = None
  sub_dg_kw = None
  sub_hub_kw = None
  sub_homesA_kw = None
  sub_homesB_kw = None
  sub_homesC_kw = None
  sub_temp = None
  pub_sw = None
  pub_bess_power = None
  pub_bess_price = None
  pub_lightsA = None
  pub_lightsB = None
  pub_lightsC = None
  pub_plugsA = None
  pub_plugsB = None
  pub_plugsC = None
  pub_refrigeratorsA = None
  pub_refrigeratorsB = None
  pub_refrigeratorsC = None
  pub_microwavesA = None
  pub_microwavesB = None
  pub_microwavesC = None
  pub_dg_pA = None
  pub_dg_pB = None
  pub_dg_pC = None
  pub_dg_qA = None
  pub_dg_qB = None
  pub_dg_qC = None

  for i in range(pub_count):
    pub = helics.helicsFederateGetPublicationByIndex(h_fed, i)
    key = helics.helicsPublicationGetKey(pub)
#    print ('HELICS publication key', i, key)
    if 'dg/pA' in key:
      pub_dg_pA = pub
    if 'dg/pB' in key:
      pub_dg_pB = pub
    if 'dg/pC' in key:
      pub_dg_pC = pub
    if 'dg/qA' in key:
      pub_dg_qA = pub
    if 'dg/qB' in key:
      pub_dg_qB = pub
    if 'dg/qC' in key:
      pub_dg_qC = pub
    if 'sw_utility' in key:
      pub_sw = pub
    if 'bess/power' in key:
      pub_bess_power = pub
    if 'bess/price' in key:
      pub_bess_price = pub
    if 'lightsA' in key:
      pub_lightsA = pub
    if 'lightsB' in key:
      pub_lightsB = pub
    if 'lightsC' in key:
      pub_lightsC = pub
    if 'plugsA' in key:
      pub_plugsA = pub
    if 'plugsB' in key:
      pub_plugsB = pub
    if 'plugsC' in key:
      pub_plugsC = pub
    if 'refrigeratorsA' in key:
      pub_refrigeratorsA = pub
    if 'refrigeratorsB' in key:
      pub_refrigeratorsB = pub
    if 'refrigeratorsC' in key:
      pub_refrigeratorsC = pub
    if 'microwavesA' in key:
      pub_microwavesA = pub
    if 'microwavesB' in key:
      pub_microwavesB = pub
    if 'microwavesC' in key:
      pub_microwavesC = pub
  for i in range(sub_count):
    sub = helics.helicsFederateGetInputByIndex(h_fed, i)
    key = helics.helicsInputGetKey(sub)
    target = helics.helicsSubscriptionGetKey(sub)
#    print ('HELICS subscription key', i, key, 'target', target)
    if 'fdr/power' in target:
      sub_fdr_kw = sub
    if 'bess/power' in target:
      sub_bess_kw = sub
    if 'pv/power' in target:
      sub_pv_kw = sub
    if 'dg/power' in target:
      sub_dg_kw = sub
    if 'hub/power' in target:
      sub_hub_kw = sub
    if 'homesA/power' in target:
      sub_homesA_kw = sub
    if 'homesB/power' in target:
      sub_homesB_kw = sub
    if 'homesC/power' in target:
      sub_homeC_kw = sub
    if 'bess/soc' in target:
      sub_bess_soc = sub
    if 'temperature' in target:
      sub_temp = sub

  helics.helicsFederateEnterExecutingMode(h_fed)
  print('### Entering Execution Mode ###')
  print('hello')

  ts = 0
  fdr_kw = 0.0
  bess_kw = 0.0
  pv_kw = 0.0
  dg_kw = 0.0
  hub_kw = 0.0
  homesA_kw = 0.0
  homesB_kw = 0.0
  homesC_kw = 0.0
  bess_soc = 0.0
  degF = 0.0
  event_triggered = False

  while ts < tmax:
    # some notes on helicsInput timing
    #  1) initial values are garbage until the other federate actually publishes
    #  2) helicsInputIsValid checks the subscription pipeline for validity, but not the value
    #  3) helicsInputIsUpdated resets to False immediately after you read the value,
    #  will become True if value changes later
    #  4) helicsInputLastUpdateTime is > 0 only after the other federate published its first value
    fdr_kw = refresh_double (sub_fdr_kw, fdr_kw, 0.001)
    bess_kw = refresh_double (sub_bess_kw, bess_kw, 0.001)
    pv_kw = refresh_double (sub_pv_kw, pv_kw, 0.001)
    dg_kw = refresh_double (sub_dg_kw, dg_kw, 0.001)
    hub_kw = refresh_double (sub_hub_kw, hub_kw, 0.001)
    homesA_kw = refresh_double (sub_homesA_kw, homesA_kw, 0.001)
    homesB_kw = refresh_double (sub_homesB_kw, homesB_kw, 0.001)
    homesC_kw = refresh_double (sub_homesC_kw, homesC_kw, 0.001)
    bess_soc = refresh_double (sub_bess_soc, bess_soc)
    degF = refresh_double (sub_temp, degF)

    if ts >= event_time and not event_triggered:
      event_triggered = True
      print ('****** Triggering Event at {:6.2f} hours'.format(float(ts)/3600.0))
      helics.helicsPublicationPublishString (pub_sw, '0')

    if event_triggered: # whack-a-mole on the schedule
      for pub in [pub_plugsA, pub_plugsB, pub_plugsC]:
        helics.helicsPublicationPublishDouble (pub, 1.0)
      for pub in [pub_lightsA, pub_lightsB, pub_lightsC]:
        helics.helicsPublicationPublishDouble (pub, 1.0)
      for pub in [pub_refrigeratorsA, pub_refrigeratorsB, pub_refrigeratorsC]:
        helics.helicsPublicationPublishDouble (pub, 1.0)
      for pub in [pub_microwavesA, pub_microwavesB, pub_microwavesC]:
        helics.helicsPublicationPublishDouble (pub, 1.0)

      # charge battery during day, discharge at night
      pv_watts = 1000.0 * abs(pv_kw)
      pbess = 0.0
      if bess_hub_logic:
        phub = 1000.0 * hub_kw
        if pv_watts > phub and bess_soc < 1.0:
          pbess = -1.0 * min (pv_watts-phub, bess_max_charging)
        elif bess_soc > 0.01:
          pbess = min (phub-pv_watts, bess_max_discharging)
      else:
        if pv_watts > 1000.0 and bess_soc < 1.0:
          pbess = -1.0 * min (pv_watts, bess_max_charging)
        elif pv_watts <= 1000.0 and bess_soc > 0.01:
          pbess = bess_max_discharging
      helics.helicsPublicationPublishDouble (pub_bess_power, pbess)

      # dispatch DG to be the swing bus
      pLoad = hub_kw + homesA_kw + homesB_kw + homesC_kw
      pSource = fdr_kw - pv_kw - bess_kw
      pSwing = min(pswing_cap, 1000.0 * (pLoad - pSource) / 3.0)
      if pSwing < 1.0:
        pSwing = 1.0
      for pub in [pub_dg_pA, pub_dg_pB, pub_dg_pC]:
        helics.helicsPublicationPublishDouble (pub, pSwing)
      for pub in [pub_dg_qA, pub_dg_qB, pub_dg_qC]:
        helics.helicsPublicationPublishDouble (pub, 0.4 * pSwing)
#      print ('  Dispatch soc={:.2f} pv_watts={:.2f} pbess={:.2f} pSwing={:.2f} pLoad={:.2f} kW pSource={:.2f} kW'.format (bess_soc,
#        pv_watts, pbess, pSwing, pLoad, pSource))

    if ts % logperiod == 0:
      print ('Hr={:6.2f}  FdrKW={:7.2f}  HubKW={:7.2f}  HomesKW={:7.2f}  DGKW={:7.2f}  BESSKW={:7.2f}  PVKW={:7.2f} SoC={:6.3f} degF={:6.2f}'.format(float(ts)/3600.0, fdr_kw,
        hub_kw, homesA_kw + homesB_kw + homesC_kw, dg_kw, bess_kw, pv_kw, bess_soc, degF))

    ts = int(helics.helicsFederateRequestTime(h_fed, tmax))

  helics.helicsFederateDestroy(h_fed)

if __name__ == '__main__':
  cfg_filename = os.environ['SOCO_CONFIG']
  helics_loop(cfg_filename)

  if sys.platform != 'win32':
    usage = resource.getrusage(resource.RUSAGE_SELF)
    RESOURCES = [
      ('ru_utime', 'User time'),
      ('ru_stime', 'System time'),
      ('ru_maxrss', 'Max. Resident Set Size'),
      ('ru_ixrss', 'Shared Memory Size'),
      ('ru_idrss', 'Unshared Memory Size'),
      ('ru_isrss', 'Stack Size'),
      ('ru_inblock', 'Block inputs'),
      ('ru_oublock', 'Block outputs')]
    print('Resource usage:')
    for name, desc in RESOURCES:
      print('  {:<25} ({:<10}) = {}'.format(desc, name, getattr(usage, name)))
