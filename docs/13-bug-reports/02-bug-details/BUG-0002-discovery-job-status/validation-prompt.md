# Validation prompt — BUG-0002

1. `python -m unittest tests.test_network_discovery -v`
2. Manual: start `vlan_checker_web.py`, POST `/api/discovery/run` with `demo_mode: false` and empty `seed_hosts` if API allows, or mock plugin error — confirm status JSON has `"status": "error"`.
3. Discovery tab: force a failure path → UI shows red error, not green Complete.
4. `python _prebuild.py` must pass.
