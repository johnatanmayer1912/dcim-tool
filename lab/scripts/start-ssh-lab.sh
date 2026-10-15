#!/usr/bin/env bash
# Start the Docker offline SSH fabric (IOS + NX-OS CLI sims).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT/lab/docker"

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon not running."
  if [[ "$(uname -s)" == "Darwin" ]]; then
    echo "Starting Docker Desktop…"
    open -a Docker || true
    echo "Wait until Docker is green, then re-run: ./lab/scripts/start-ssh-lab.sh"
  fi
  exit 1
fi

docker compose up -d --build
echo
echo "SSH sims up on 127.0.0.1:2201–2204"
echo "Commit inventory: lab/docker/inventory.nst.txt"
echo "Test:  ssh -p 2203 admin@127.0.0.1   (any password)"
docker compose ps
