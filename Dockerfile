# Ops / research image for E21 live + month-end paper (no broker secrets).
# Soft-Frozen / LIVE_* knobs stay in repo SSOT — this image only packages tooling.
#
# Build:  docker build -t e21-ops:local .
# Run:    docker run --rm -v "$PWD:/workspace" -w /workspace e21-ops:local \
#           python3 scripts/e21_qc.py --state-dir forward/e21

FROM python:3.12-slim-bookworm

WORKDIR /workspace

# System deps kept minimal (pandas wheels; no compiler toolchain by default).
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml setup.py README.md ./
COPY scripts ./scripts

RUN pip install --no-cache-dir --disable-pip-version-check .

# Default: show help; CI / cron override the command.
CMD ["python3", "-c", "import live_config; print('e21-ops', live_config.LIVE.capital)"]
