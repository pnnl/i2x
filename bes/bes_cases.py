CASES = [
  {'id': '1783D2A8-1204-4781-A0B4-7A73A2FA6038', 
   'name': 'IEEE118', 
   'swingbus':'131',
   'load_scale':0.6748,
   'softlims': False,
   'glpk_opts': None,
   'min_kv_to_upgrade': 100.0,
   'min_contingency_mva': 400.0,
   'mva_upgrades': None},
  {'id': '2540AF5C-4F83-4C0F-9577-DEE8CC73BBB3', 
   'name': 'WECC240', 
   'swingbus':'2438',
   'load_scale':1.0425,
   'softlims': False,
   'glpk_opts': None, # {'glpk.opts.itlim': 5},
   'min_kv_to_upgrade': 10.0,
   'min_contingency_mva': 5000.0,
   'mva_upgrades': [
     {'branch_number': 50, 'new_mva':1200.0},
     {'branch_number': 52, 'new_mva':1700.0},
     {'branch_number': 53, 'new_mva':1200.0},
     {'branch_number': 54, 'new_mva':1200.0},
     {'branch_number': 55, 'new_mva':1200.0},
     {'branch_number': 56, 'new_mva':1800.0},
     {'branch_number':264, 'new_mva':7200.0},
     {'branch_number':307, 'new_mva':2168.0},
     {'branch_number':332, 'new_mva':1200.0},
     {'branch_number':333, 'new_mva':1200.0},
     {'branch_number':406, 'new_mva': 750.0},
     {'branch_number':422, 'new_mva':3300.0},
     {'branch_number':430, 'new_mva':1500.0},
     {'branch_number':442, 'new_mva':1000.0},
     {'branch_number':443, 'new_mva':1000.0},
     {'branch_number':449, 'new_mva':1500.0}]},
  {'id': None,
   'name': 'IEEE39',
   'swingbus':'31',
   'load_scale':1.0000,
   'softlims': False,
   'glpk_opts': None,
   'min_kv_to_upgrade': 500.0,
   'min_contingency_mva': 1000.0,
   'mva_upgrades': None}
  ]


