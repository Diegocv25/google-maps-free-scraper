#!/usr/bin/env python3
import json, os, subprocess, sys
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

FIELDS=['result','niche','estado','cidade','bairro','raw','valid','discarded','inserted','verified','destination','coverage_updated','error']
TABLES={'salao':'LEADS_NICHOS_MISTO','barbearia':'LEADS_NICHOS_MISTO','spa':'LEADS_NICHOS_MISTO','estetica':'LEADS_NICHOS_MISTO','oficina_mecanica':'LEADS_MINHA_OFICINA','restaurante':'LEADS_CARDAPIOJA','lanchonete':'LEADS_CARDAPIOJA','pizzaria':'LEADS_CARDAPIOJA','hamburgueria':'LEADS_CARDAPIOJA'}
QUERIES={'salao':['salão'],'barbearia':['barbearia'],'spa':['spa'],'estetica':['estética'],'oficina_mecanica':['oficina mecânica'],'restaurante':['restaurante'],'lanchonete':['lanchonete'],'pizzaria':['pizzaria'],'hamburgueria':['hamburgueria']}

def report(**values):
    out={k:values.get(k) for k in FIELDS}
    print(json.dumps(out,ensure_ascii=False,separators=(',',':')))

def call(method,url,key,payload=None):
    data=json.dumps(payload,ensure_ascii=False).encode() if payload is not None else None
    headers={'apikey':key,'Authorization':f'Bearer {key}','Content-Type':'application/json','Prefer':'return=representation'}
    try:
        with urlopen(Request(url,data=data,headers=headers,method=method),timeout=45) as response:
            raw=response.read()
            return json.loads(raw or b'null')
    except HTTPError as exc:
        body=exc.read().decode('utf-8','replace').strip()
        raise RuntimeError(f'Supabase HTTP {exc.code}: {body or exc.reason}') from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f'Supabase transport error: {exc}') from exc

def main():
    niche=sys.argv[1].strip().lower() if len(sys.argv)>1 else ''
    table=TABLES.get(niche)
    if not table: raise RuntimeError(f'nicho inválido: {niche}')
    base=os.environ.get('SUPABASE_URL','').rstrip('/')
    key=os.environ.get('SUPABASE_KEY') or os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    scraper=os.environ.get('SCRAPER_BASE_URL','http://localhost:18080').rstrip('/')
    if not base or not key: raise RuntimeError('credenciais Supabase ausentes')
    queue=call('GET',f'{base}/rest/v1/cidades_bairros_geo?select=*&cobertura=eq.false&limit=1',key)
    if not queue:
        report(result='success',niche=niche,estado=None,cidade=None,bairro=None,raw=0,valid=0,discarded=0,inserted=0,verified=True,destination=table,coverage_updated=False,error=None)
        return
    row=queue[0]; state=row.get('estado') or row.get('Estado'); city=row.get('cidade') or row.get('Cidade'); neighborhood=row.get('bairro') or row.get('Bairro')
    cmd=['python3','scripts/scrape_neighborhood.py',neighborhood,'--city',city,'--state',state,'--radius','4000','--grid','5','--depth','3','--out',f'/tmp/capture-{niche}']
    proc=subprocess.run(cmd,capture_output=True,text=True,timeout=360)
    if proc.returncode: raise RuntimeError((proc.stderr or proc.stdout).strip()[-2000:])
    summary=json.loads(open(f'/tmp/capture-{niche}-summary.json').read())
    leads=json.load(open(f'/tmp/capture-{niche}.json')) if os.path.exists(f'/tmp/capture-{niche}.json') else []
    inserted=0
    for lead in leads:
        payload=dict(lead); payload.setdefault('Estado',state); payload.setdefault('Cidade',city); payload.setdefault('Bairro',neighborhood)
        identity=urlencode({'Nome':f"eq.{payload.get('Nome','')}",'Estado':f'eq.{state}'})
        existing=call('GET',f'{base}/rest/v1/{table}?{urlencode({"select":"id","limit":"1"})}&{identity}',key)
        if not existing:
            call('POST',f'{base}/rest/v1/{table}',key,payload); inserted+=1
    verify_query=urlencode({'select':'id','limit':'1','Estado':f'eq.{state}','Cidade':f'eq.{city}','Bairro':f'eq.{neighborhood}'})
    verify=call('GET',f'{base}/rest/v1/{table}?{verify_query}',key)
    if not verify: raise RuntimeError('persistência não confirmada')
    report(result='success',niche=niche,estado=state,cidade=city,bairro=neighborhood,raw=summary.get('raw',len(leads)),valid=summary.get('valid',len(leads)),discarded=summary.get('discarded',0),inserted=inserted,verified=True,destination=table,coverage_updated=False,error=None)

if __name__=='__main__':
    try: main()
    except Exception as exc:
        report(result='technical_failure',niche=sys.argv[1] if len(sys.argv)>1 else None,raw=None,valid=None,discarded=None,inserted=0,verified=False,destination=TABLES.get(sys.argv[1]) if len(sys.argv)>1 else None,coverage_updated=False,error=str(exc))
        raise
