#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
TOPO="$ROOT/nst-clos.clab.yml"

if ! command -v containerlab >/dev/null 2>&1; then
  echo "containerlab not found. Install: https://containerlab.dev/install/" >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon not running — start Docker Desktop / dockerd first." >&2
  exit 1
fi
if [[ -z "${N9KV_IMAGE:-}" ]]; then
  echo "Set N9KV_IMAGE to your local vrnetlab/cisco_n9kv tag." >&2
  echo "Example: export N9KV_IMAGE=vrnetlab/cisco_n9kv:lite.10.5.2.F" >&2
  exit 1
fi

# Substitute image into a temp topology (containerlab env expansion varies by version)
TMP="$(mktemp -t nst-clos.XXXXXX.clab.yml)"
sed "s|\${N9KV_IMAGE:-vrnetlab/cisco_n9kv:latest}|${N9KV_IMAGE}|g" "$TOPO" >"$TMP"
echo "Deploying $TMP with image $N9KV_IMAGE ..."
containerlab deploy -t "$TMP"
echo
echo "Inventory for NST UI: $ROOT/inventory.nst.txt"
echo "SSH: admin / admin  (mgmt 172.28.28.11–22)"
echo "Destroy: containerlab destroy -t $TMP"
