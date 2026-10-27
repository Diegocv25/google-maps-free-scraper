#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/workspaces/google-maps-free-scraper
: "${SCRAPER_BASE_URL:=http://localhost:18080}"
export SCRAPER_BASE_URL
exec python3 scripts/capture_supabase_leads.py "$@"
