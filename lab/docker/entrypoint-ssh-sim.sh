#!/bin/sh
set -eu
export PYTHONPATH=/app
python -m lab.ssh_sim.server --host 0.0.0.0 --port 2201 --device ios_access &
python -m lab.ssh_sim.server --host 0.0.0.0 --port 2202 --device nxos_leaf1 &
python -m lab.ssh_sim.server --host 0.0.0.0 --port 2203 --device nxos_leaf2 &
wait
