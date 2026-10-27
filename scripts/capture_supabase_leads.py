#!/usr/bin/env python3
"""Captura um bairro pendente, insere leads e emite um relatório JSON determinístico."""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ENV_FILE = Path("/home/ubuntu/supabases.env")
SCRAPER = Path("/home/ubuntu/workspaces/google-maps-free-scraper/scripts/scrape_neighborhood.py")
OUT = Path("/home/ubuntu/workspaces/google-maps-free-scraper/runtime-results")
FIELDS = ["result", "niche", "estado", "cidade", "bairro", "raw", "valid", "discarded", "inserted", "verified", "destination", "coverage_updated", "error"]
NICHES = {
    "salao": ("enviado_salao", "enviado_em_salao", "LEADS_NICHOS_MISTO"),
    "barbearia": ("enviado_barbearia", "enviado_em_barbearia", "LEADS_NICHOS_MISTO"),
    "spa": ("enviado_spa", "enviado_em_spa", "LEADS_NICHOS_MISTO"),
    "estetica": ("enviado_estetica", "enviado_em_estetica", "LEADS_NICHOS_MISTO"),
    "oficina_mecanica": ("enviado_oficina_mecanica", "enviado_em_oficina_mecanica", "LEADS_MINHA_OFICINA"),
    "restaurante": ("enviado_restaurante", "enviado_em_restaurante", "LEADS_CARDAPIOJA"),
    "lanchonete": ("enviado_lanchonete", "enviado_em_lanchonete", "LEADS_CARDAPIOJA"),
    "pizzaria": ("enviado_pizzaria", "enviado_em_pizzaria", "LEADS_CARDAPIOJA"),
    "hamburgueria": ("enviado_hamburgueria", "enviado_em_hamburgueria", "LEADS_CARDAPIOJA"),
}


def report(**values: object) -> None:
    print(json.dumps({field: values.get(field) for field in FIELDS}, ensure_ascii=False, separators=(",", ":")))


def load_env() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def call(method: str, url: str, key: str, payload: object | None = None) -> object:
    data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
        headers["Prefer"] = "return=representation"
    try:
        with urlopen(Request(url, data=data, headers=headers, method=method), timeout=45) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    except HTTPError as exc:
        body = exc.read().decode("utf-8", "replace").strip()
        raise RuntimeError(f"Supabase HTTP {exc.code}: {body or exc.reason}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Supabase transport error: {exc}") from exc


def main(niche: str, dry_run: bool = False) -> None:
    flag, stamp, table = NICHES[niche]
    cfg = load_env()
    base = cfg.get("SUPABASE_FUNIL_URL", "").rstrip("/") + "/rest/v1"
    key = cfg.get("SUPABASE_FUNIL_SERVICE_ROLE_KEY", "")
    if not base.strip("/rest/v1") or not key:
        raise RuntimeError("credenciais Supabase ausentes em /home/ubuntu/supabases.env")

    queue_url = f"{base}/cidades_bairros_geo?{urlencode({'select': '*', flag: 'eq.false', 'order': 'id.asc', 'limit': '1'})}"
    rows = call("GET", queue_url, key)
    if not rows:
        report(result="no_pending", niche=niche, estado=None, cidade=None, bairro=None, raw=0, valid=0, discarded=0, inserted=0, verified=True, destination=table, coverage_updated=False, error=None)
        return

    geo = rows[0]
    state, city, neighborhood = geo["estado"], geo["cidade"], geo["bairro"]
    out = OUT / f"{niche}-{geo['id']}"
    out.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(SCRAPER), neighborhood, "--city", city, "--state", state, "--radius", "4000", "--grid", "5", "--depth", "3", "--max-time", "360", "--out", str(out)]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=3600, env={**os.environ, "SCRAPER_BASE_URL": os.environ.get("SCRAPER_BASE_URL", "http://localhost:18080")})
    summary = out / f"{re.sub(r'[^a-z0-9]+', '-', neighborhood.lower()).strip('-')}-summary.json"
    if proc.returncode:
        raise RuntimeError((proc.stderr or proc.stdout)[-2000:])
    scraper_report = json.loads(summary.read_text(encoding="utf-8"))
    with Path(scraper_report["file"]).open(encoding="utf-8-sig", newline="") as handle:
        leads = list(csv.DictReader(handle))

    inserted = 0
    verified = 0
    now = datetime.now(timezone.utc).isoformat()
    if not dry_run:
        for lead in leads:
            name = (lead.get("title") or "").strip()
            if not name:
                continue
            payload = {"Nome": name, "Telefone": (lead.get("phone") or "").strip(), "Endereço": (lead.get("address") or "").strip(), "Website": (lead.get("website") or "").strip(), "Estado": state, "Status": "Aguardando", "nicho": niche, "source": "google_maps_free_scraper", "extracted_at": now, "created_at": now, "updated_at": now, "bairro": neighborhood, "cidade": city}
            identity = urlencode({"Nome": f"eq.{name}", "Estado": f"eq.{state}"})
            exists = call("GET", f"{base}/{table}?{urlencode({'select': 'id', 'limit': '1'})}&{identity}", key)
            if not exists:
                call("POST", f"{base}/{table}", key, payload)
                inserted += 1
            if call("GET", f"{base}/{table}?{urlencode({'select': 'id', 'limit': '1'})}&{identity}", key):
                verified += 1
        if len(leads) == 0 or verified >= inserted:
            coverage_query = urlencode({'id': f'eq.{geo["id"]}'})
            call("PATCH", f"{base}/cidades_bairros_geo?{coverage_query}", key, {flag: True, stamp: now})

    report(result="dry_run" if dry_run else "success", niche=niche, estado=state, cidade=city, bairro=neighborhood, raw=scraper_report["unique_raw"], valid=scraper_report["confirmed"], discarded=scraper_report["excluded"], inserted=inserted, verified=verified, destination=table, coverage_updated=bool(not dry_run and (len(leads) == 0 or verified >= inserted)), error=None)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("niche", choices=NICHES)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        main(args.niche, args.dry_run)
    except Exception as exc:
        table = NICHES[args.niche][2]
        report(result="technical_failure", niche=args.niche, estado=None, cidade=None, bairro=None, raw=None, valid=None, discarded=None, inserted=0, verified=False, destination=table, coverage_updated=False, error=str(exc))
        sys.exit(1)
