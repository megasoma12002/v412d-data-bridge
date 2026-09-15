#!/usr/bin/env bash
# Local / CI smoke: build e21-ops image and run live QC against mounted workspace.
# Soft-Frozen / LIVE_* unchanged. No broker secrets in the image.
#
# Usage (from repo root):
#   bash scripts/ops_docker_qc_smoke.sh
#   bash scripts/ops_docker_qc_smoke.sh --skip-build   # reuse existing tag
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

IMAGE="${E21_OPS_IMAGE:-e21-ops:local}"
SKIP_BUILD=0
for arg in "$@"; do
  case "$arg" in
    --skip-build) SKIP_BUILD=1 ;;
    -h|--help)
      echo "Usage: $0 [--skip-build]"
      exit 0
      ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker not found on PATH. Install Docker Engine / Desktop, then retry."
  exit 127
fi

if [[ "$SKIP_BUILD" -eq 0 ]]; then
  echo "==> docker build -t ${IMAGE} ."
  docker build -t "${IMAGE}" .
fi

echo "==> import live_config smoke"
docker run --rm \
  -v "${ROOT}:/workspace" \
  -w /workspace \
  "${IMAGE}" \
  python3 -c "import live_config; print('e21-ops', live_config.LIVE.capital, live_config.LIVE.fill_port)"

echo "==> e21_qc --state-dir forward/e21"
docker run --rm \
  -v "${ROOT}:/workspace" \
  -w /workspace \
  "${IMAGE}" \
  python3 scripts/e21_qc.py --state-dir forward/e21

echo "EXIT:0 ops_docker_qc_smoke OK image=${IMAGE}"
