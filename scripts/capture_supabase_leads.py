#!/usr/bin/env python3
"""Capture one pending niche neighborhood with the focused scraper."""
from __future__ import annotations
import argparse,json,os,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen

ENV_FILE=Path('/home/ubuntu/supabases.env')
SCRAPER=Path('/home/ubuntu/workspaces/google-maps-free-scraper/scripts/scrape_neighborhood.py')
BASE=os.environ.get('SCRAPER_BASE_URL','http://localhost:18080')
OUT=Path('/home/ubuntu/workspaces/google-maps-free-scraper/runtime-results')
NICHES={
'salao':('enviado_salao','enviado_em_salao','LEADS_NICHOS_MISTO',['salão']),
'barbearia':('enviado_barbearia','enviado_em_barbearia','LEADS_NICHOS_MISTO',['barbearia']),
'spa':('enviado_spa','enviado_em_spa','LEADS_NICHOS_MISTO',['spa']),
'estetica':('enviado_estetica','enviado_em_estetica','LEADS_NICHOS_MISTO',['estética']),
'oficina_mecanica':('enviado_oficina_mecanica','enviado_em_oficina_mecanica','LEADS_MINHA_OFICINA',['oficina mecânica']),
'restaurante':('enviado_restaurante','enviado_em_restaurante','LEADS_CARDAPIOJA',['restaurante']),
'lanchonete':('enviado_lanchonete','enviado_em_lanchonete','LEADS_CARDAPIOJA',['lanchonete']),
'pizzaria':('enviado_pizzaria','enviado_em_pizzaria','LEADS_CARDAPIOJA',['pizzaria']),
'hamburgueria':('enviado_hamburgueria','enviado_em_hamburgueria','LEADS_CARDAPIOJA',['hamburgueria']),
}
def env():
 d={}
 for line in ENV_FILE.read_text().splitlines():
  if line.strip() and not line.lstrip().startswith('#') and '=' in line:
   k,v=line.split('=',1); d[k.strip()]=v.strip().strip('"').strip("'")
 return d
def call(method,url,key,body=None):
 headers={'apikey':key,'Authorization':'Bearer '+key,'Accept':'application/json'}; data=None
 if body is not None: headers['Content-Type']='application/json'; data=json.dumps(body,ensure_ascii=False).encode()
 with urlopen(Request(url,data=data,headers=headers,method=method),timeout=45) as response:
  raw=response.read(); return json.loads(raw) if raw else None
def main():
 p=argparse.ArgumentParser(); p.add_argument('niche',choices=NICHES); p.add_argument('--dry-run',action='store_true'); a=p.parse_args()
 cfg=env(); base=cfg['SUPABASE_FUNIL_URL'].rstrip('/')+'/rest/v1'; key=cfg['SUPABASE_FUNIL_SERVICE_ROLE_KEY']; flag,stamp,table,queries=NICHES[a.niche]
 rows=call('GET',f'{base}/cidades_bairros_geo?select=*&{flag}=eq.false&order=id.asc&limit=1',key)
 if not rows: print(json.dumps({'result':'no_pending','niche':a.niche})); return 0
 geo=rows[0]; out=OUT/f"{a.niche}-{geo['id']}"; out.mkdir(parents=True,exist_ok=True)
 cmd=[sys.executable,str(SCRAPER),geo['bairro'],'--city',geo['cidade'],'--state',geo['estado'],'--radius','4000','--grid','5','--depth','3','--max-time','360','--out',str(out)]
 proc=subprocess.run(cmd,text=True,capture_output=True,timeout=3600,env={**os.environ,'SCRAPER_BASE_URL':BASE})
 summary=out/f"{re.sub(r'[^a-z0-9]+','-',geo['bairro'].lower()).strip('-')}-summary.json"
 if proc.returncode: raise RuntimeError((proc.stderr or proc.stdout)[-2000:])
 report=json.loads(summary.read_text())
 now=datetime.now(timezone.utc).isoformat(); csv_path=Path(report['file'])
 with csv_path.open(encoding='utf-8-sig',newline='') as fh:
  import csv
  leads=list(csv.DictReader(fh))
 inserted=0; verified=0
 if not a.dry_run:
  for lead in leads:
   name=(lead.get('title') or '').strip(); phone=(lead.get('phone') or '').strip(); address=(lead.get('address') or '').strip(); website=(lead.get('website') or '').strip()
   if not name: continue
   payload={'Nome':name,'Telefone':phone,'Endereço':address,'Website':website,'Estado':geo['estado'],'Status':'Aguardando','nicho':a.niche,'source':'google_maps_free_scraper','extracted_at':now,'created_at':now,'updated_at':now,'bairro':geo['bairro'],'cidade':geo['cidade']}
   identity=f'Nome=eq.{name}&Estado=eq.{geo["estado"]}'
   if not call('GET',f'{base}/{table}?select=id&limit=1&{identity}',key):
    call('POST',f'{base}/{table}',key,payload); inserted+=1
   if call('GET',f'{base}/{table}?select=id&limit=1&{identity}',key): verified+=1
  if len(leads)==0 or verified>=inserted:
   call('PATCH',f'{base}/cidades_bairros_geo?id=eq.{geo["id"]}',key,{flag:True,stamp:now})
 print(json.dumps({'result':'dry_run' if a.dry_run else 'success','niche':a.niche,'estado':geo['estado'],'cidade':geo['cidade'],'bairro':geo['bairro'],'raw':report['unique_raw'],'valid':report['confirmed'],'discarded':report['excluded'],'inserted':inserted,'verified':verified,'destination':table,'coverage_updated':not a.dry_run},ensure_ascii=False))
if __name__=='__main__': main()
