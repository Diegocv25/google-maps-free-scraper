#!/usr/bin/env python3
"""Focused neighborhood search for the local Google Maps scraper API.
Runs one neighborhood at a time, uses five controlled centers, three query variants,
and exports only rows whose returned address/title names the requested neighborhood.
"""
import argparse,csv,io,json,os,re,subprocess,time,urllib.parse,urllib.request,unicodedata
from pathlib import Path
BASE=os.environ.get('SCRAPER_BASE_URL','http://localhost:18080').rstrip('/')
UA='google-maps-free-scraper-neighborhood/1.0'
def norm(s): return re.sub(r'[^a-z0-9]+',' ',unicodedata.normalize('NFKD',str(s or '')).encode('ascii','ignore').decode().lower()).strip()
def api(method,path,body=None):
 data=json.dumps(body).encode() if body is not None else None
 r=urllib.request.Request(BASE+path,data=data,method=method,headers={'Content-Type':'application/json','User-Agent':UA})
 with urllib.request.urlopen(r,timeout=60) as x: return x.read()
def geocode(place):
 q=urllib.parse.urlencode({'format':'json','limit':5,'addressdetails':1,'countrycodes':'br','accept-language':'pt-BR','q':place})
 r=urllib.request.Request('https://nominatim.openstreetmap.org/search?'+q,headers={'User-Agent':UA})
 with urllib.request.urlopen(r,timeout=30) as x: hits=json.loads(x.read())
 target=norm(place.split(',')[0])
 def score(h):
  a=h.get('address',{}); s=0
  if target and target in norm(h.get('display_name')): s+=4
  if any(k in a for k in ('neighbourhood','suburb','quarter')): s+=3
  if h.get('type') in ('neighbourhood','suburb','quarter','district'): s+=3
  if a.get('city') or a.get('town') or a.get('municipality'): s+=2
  if a.get('state'): s+=1
  return s
 if not hits:
  parts=[part.strip() for part in place.split(',')]
  fallback=', '.join(parts[1:]) if len(parts)>1 else ''
  if fallback:
   q2=urllib.parse.urlencode({'format':'json','limit':5,'addressdetails':1,'countrycodes':'br','accept-language':'pt-BR','q':fallback})
   r2=urllib.request.Request('https://nominatim.openstreetmap.org/search?'+q2,headers={'User-Agent':UA})
   with urllib.request.urlopen(r2,timeout=30) as x: hits=json.loads(x.read())
  if not hits: raise RuntimeError('geocoding returned no candidates')
 return max(hits,key=score),hits
def restart_worker_if_idle():
 # The API can remain healthy after its internal scrapemate worker exits.
 # Restart only when no other job is actively working, so recovery does not
 # interrupt a different neighborhood capture.
 jobs=json.loads(api('GET','/api/v1/jobs'))
 active=[x for x in jobs if (x.get('Status') or x.get('status')) == 'working']
 if active: return False
 p=subprocess.run(['sudo','-n','docker','restart','gmaps-scraper'],capture_output=True,text=True,timeout=60)
 if p.returncode: raise RuntimeError(f'worker restart failed: {(p.stderr or p.stdout).strip()}')
 return True

def job(queries,lat,lon,a):
 body={'name':'focused-neighborhood','keywords':queries,'lang':'pt','zoom':15,'lat':str(lat),'lon':str(lon),'fast_mode':False,'radius':a.radius,'depth':a.depth,'email':False,'max_time':a.max_time}
 created=json.loads(api('POST','/api/v1/jobs',body)); jid=created.get('id') or created.get('ID')
 if not jid: raise RuntimeError('job id missing')
 deadline=time.time()+a.max_time; pending_since=None; recovered=False
 while time.time()<deadline:
  info=json.loads(api('GET','/api/v1/jobs/'+jid)); status=info.get('Status') or info.get('status')
  if status=='ok': return list(csv.DictReader(io.StringIO(api('GET','/api/v1/jobs/'+jid+'/download').decode('utf-8','replace')))),body,jid
  if status=='failed': raise RuntimeError('job failed '+jid)
  if status=='pending':
   pending_since=pending_since or time.time()
   if not recovered and time.time()-pending_since >= 45:
    recovered=restart_worker_if_idle(); pending_since=time.time() if recovered else pending_since
  else: pending_since=None
  time.sleep(5)
 info=json.loads(api('GET','/api/v1/jobs/'+jid))
 raise RuntimeError(f'job timeout {jid} (status={info.get("Status") or info.get("status")})')
def row_key(r):
 for k in ('place_id','placeid','phone'):
  if r.get(k): return k+':'+norm(r[k])
 return 'nameaddr:'+norm(r.get('title','')+' '+r.get('address',''))
def main():
 p=argparse.ArgumentParser(); p.add_argument('neighborhood'); p.add_argument('--query',default='restaurante'); p.add_argument('--city',default='Palhoça'); p.add_argument('--state',default='SC'); p.add_argument('--out',required=True); p.add_argument('--radius',type=int,default=4000); p.add_argument('--depth',type=int,default=3,help='scraper depth per job; 3 is the bounded default for 15 focused jobs'); p.add_argument('--max-time',type=int,default=240); p.add_argument('--grid',type=int,default=5); p.add_argument('--min-confirmed',type=int,default=0,help='stop after this many confirmed rows; 0 runs all requested cells'); a=p.parse_args()
 chosen,candidates=geocode(f'{a.neighborhood}, {a.city}, {a.state}, Brasil'); lat,lon=float(chosen['lat']),float(chosen['lon']); d=0.012
 centers=[(lat,lon,'center'),(lat+d,lon,'north'),(lat-d,lon,'south'),(lat,lon+d,'east'),(lat,lon-d,'west')][:max(1,min(5,a.grid))]
 queries=[f'{a.query} em {a.neighborhood}, {a.city}, {a.state}',f'{a.query} {a.neighborhood}, {a.city}, {a.state}',f'{a.query}s {a.neighborhood}, {a.city}, {a.state}']
 allrows={}; jobs=[]
 for clat,clon,cell in centers:
  rows,body,jid=job(queries,clat,clon,a); jobs.append({'id':jid,'cell':cell,'query':queries,'count':len(rows),'payload':body})
  for r in rows: allrows.setdefault(row_key(r),r)
  if a.min_confirmed and sum(1 for r in allrows.values() if norm(a.neighborhood) in norm(r.get('address','')+' '+r.get('title',''))) >= a.min_confirmed:
   break
 confirmed=[r for r in allrows.values() if norm(a.neighborhood) in norm(r.get('address','')+' '+r.get('title',''))]; excluded=[r for r in allrows.values() if r not in confirmed]
 out=Path(a.out); out.mkdir(parents=True,exist_ok=True); stem=re.sub(r'[^a-z0-9]+','-',a.neighborhood.lower()).strip('-')
 def save(name,rows):
  f=out/name; fields=sorted({k for r in rows for k in r}) or ['title','address'];
  with f.open('w',newline='',encoding='utf-8-sig') as x: w=csv.DictWriter(x,fieldnames=fields); w.writeheader(); w.writerows(rows)
  return str(f)
 report={'neighborhood':a.neighborhood,'geocode':chosen,'candidate_count':len(candidates),'grid_requested':a.grid,'grid_used':len(centers),'queries':queries,'radius':a.radius,'depth':a.depth,'jobs':jobs,'unique_raw':len(allrows),'confirmed':len(confirmed),'excluded':len(excluded),'file':save(stem+'.csv',confirmed),'excluded_file':save(stem+'-excluded.csv',excluded)}; (out/(stem+'-summary.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
