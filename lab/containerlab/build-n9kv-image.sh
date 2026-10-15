#!/usr/bin/env bash
# Build a Docker-wrapped Cisco Nexus 9000v image via vrnetlab.
# You must download the qcow2 from Cisco Software Download (account required).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
VRNETLAB_DIR="${VRNETLAB_DIR:-$ROOT/.vrnetlab}"
QCOW2="${1:-}"

if [[ -z "$QCOW2" || ! -f "$QCOW2" ]]; then
  cat <<'EOF'
Usage:
  ./lab/containerlab/build-n9kv-image.sh /path/to/nexus9300v*.qcow2

Steps:
  1) Download Nexus 9000v (or Lite) qcow2 from Cisco (licensed).
  2) Run this script — clones hellt/vrnetlab and builds vrnetlab/cisco_n9kv:<tag>
  3) Export N9KV_IMAGE=vrnetlab/cisco_n9kv:<tag>
  4) ./lab/containerlab/deploy.sh

Docs: https://containerlab.dev/manual/kinds/vr-n9kv/
EOF
  exit 1
fi

if ! command -v docker >/dev/null; then
  echo "docker required" >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon not running — start Docker Desktop first." >&2
  exit 1
fi

if [[ ! -d "$VRNETLAB_DIR/.git" ]]; then
  git clone --depth 1 https://github.com/hellt/vrnetlab.git "$VRNETLAB_DIR"
fi

N9KV_DIR="$VRNETLAB_DIR/n9kv"
mkdir -p "$N9KV_DIR"
cp -f "$QCOW2" "$N9KV_DIR/"
BASE="$(basename "$QCOW2")"
echo "Building image from $BASE in $N9KV_DIR ..."
(
  cd "$N9KV_DIR"
  make docker-image
)
echo
echo "Done. List images:"
docker images | grep -i n9kv || docker images | head -20
echo
echo "Then: export N9KV_IMAGE=<repo:tag> && ./lab/containerlab/deploy.sh"
