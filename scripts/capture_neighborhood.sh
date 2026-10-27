#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${SCRAPER_BASE_URL:=http://localhost:8080}"
exec python3 scripts/scrape_neighborhood.py "$@"
