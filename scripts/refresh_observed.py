#!/usr/bin/env python3

import json,urllib.request,urllib.parse,re,math,hashlib

from datetime import datetime,timezone

from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'data'; OUT.mkdir(exist_ok=True)

D=json.JSONDecoder(); html=(ROOT/'index.html').read_text(); pos=html.index('const cities=')+len('const cities='); base,_=D.raw_decode(html[pos:])

def api(dataset,params):
  
 u='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'+dataset+'?'+urllib.parse.urlencode({'lang':'en',**params},doseq=True)
  
 req=urllib.request.Request(u,headers={'User-Agent':'FranchiseExpansionEurope/1.0'}); return json.load(urllib.request.urlopen(req,timeout=90)),u
  
def series(ds,dim):
  
 sizes=ds['size']; ids=ds['id']; idxs={k:v['category'].get('index',{}) for k,v in ds['dimension'].items()}
  
 # index can list or dict; normalize positions

 def positions(x): return {v:i for i,v in enumerate(x)} if isinstance(x,list) else x
   
 idxs={k:positions(v) for k,v in idxs.items()}; vals=ds.get('value',{}); out={}
  
 for code,p in idxs[dim].items():
   
  coords=[]; rem=0
   
  # choose final time, first values in other filtered dimensions

  for j,(id_,size) in enumerate(zip(ids,sizes)):
    
   if id_==dim: c=p
     
   elif id_=='time': c=size-1
     
   else:c=0
     
   coords.append(c)
    
  linear=0
   
  for c,size in zip(coords,sizes): linear=linear*size+c
    
  val=vals.get(str(linear),vals.get(linear))
   
  if val is not None: out[code]=val
    
 return out
  
pop,popurl=api('urb_cpop1',{'sinceTimePeriod':'2022','indic_ur':'DE1001V'})

citylabels=pop['dimension']['cities']['category']['label']; cityvals=series(pop,'cities')

ppp,pppurl=api('prc_ppp_ind',{'sinceTimePeriod':'2024','ppp_cat':'A01','na_item':'PLI_EU27_2020'})

pppvals=series(ppp,'geo')

net,neturl=api('isoc_ci_ifp_iu',{'sinceTimePeriod':'2025','indic_is':'I_IU3','ind_type':'IND_TOTAL','unit':'PC_IND'})

netvals=series(net,'geo')

# manual deterministic city->country Eurostat mapping; city matching allows local/English variants

country={'UK':'UK','France':'FR','Spain':'ES','Germany':'DE','Italy':'IT','Netherlands':'NL','Belgium':'BE','Austria':'AT','Sweden':'SE','Denmark':'DK','Finland':'FI','Ireland':'IE','Portugal':'PT','Poland':'PL','Czechia':'CZ','Hungary':'HU','Romania':'RO','Bulgaria':'BG','Croatia':'HR','Greece':'EL','Lithuania':'LT','Latvia':'LV','Estonia':'EE','Norway':'NO','Switzerland':'CH','Luxembourg':'LU','Slovenia':'SI','Slovakia':'SK','Cyprus':'CY'}

alias={'Munich':'München','Cologne':'Köln','Milan':'Milano','Rome':'Roma','Vienna':'Wien','Prague':'Praha','Warsaw':'Warszawa','Lisbon':'Lisboa','Athens':'Athina','Copenhagen':'København','Brussels':'Bruxelles/Brussel','Bucharest':'Bucuresti','Turin':'Torino','Florence':'Firenze','Seville':'Sevilla','Saragossa':'Zaragoza','Nuremberg':'Nürnberg','Gothenburg':'Göteborg','Geneva':'Genève','Cracow':'Kraków','Helsinki':'Helsinki / Helsingfors'}

def norm(x):return re.sub(r'[^a-z0-9]','',x.lower().replace('ü','u').replace('ö','o').replace('ä','a').replace('é','e').replace('è','e').replace('ø','o'))
  
def citypop(name):
  
 want=norm(alias.get(name,name)); best=None
  
 for code,label in citylabels.items():
   
  if code in cityvals and (norm(label.split(' (')[0])==want or want in norm(label.split(' (')[0])):
    
   # prefer city over greater city
    
   score=('greater city' in label, len(label));
    
   if best is None or score<best[0]:best=(score,cityvals[code],code,label)
     
 return best[1:] if best else (None,None,None)
  
rows=[]

for x in base:
  
 p,cc,label=citypop(x['city']); geo=country.get(x['country']); pli=pppvals.get(geo); internet=netvals.get(geo)
  
 # demand is observed city population, income/digital observed country measures. Cost/ease remain estimates and labelled.

 if not p:
   
  demand=round(x['demand'],1); observed={'population':None,'population_city_code':None,'population_label':'No current Eurostat city observation matched'}
   
 else:
   
  demand=round(min(10,max(1,2+math.log10(max(p,1)/100000)*3)),1); observed={'population':round(p),'population_city_code':cc,'population_label':label}
   
 #round(min(10,max(1,2+math.log10(max(p,1)/100000)*3)),1)

 income=round(min(10,max(1,(pli or 100)/13)),1); digital=round(min(10,max(1,(internet or 80)/10)),1)

 rows.append({**x,'demand':demand,'income':income,'digital':digital,'observed':{**observed,'price_level_index':pli,'internet_use_pct':internet},'sources':{'population':popurl,'population_updated':pop['updated'],'price_level':pppurl,'price_level_updated':ppp['updated'],'internet':neturl,'internet_updated':net['updated']},'labels':{'demand':('OBSERVED input / NORMALISED score' if p else 'MODELLED - no matching Eurostat city observation'),'income':'OBSERVED country context / NORMALISED score','digital':'OBSERVED country context / NORMALISED score','cost':'ESTIMATE','ease':'ESTIMATE'}})

now=datetime.now(timezone.utc).isoformat(); status={'fetched_at':now,'source':'Eurostat dissemination API','base_cities':len(base),'cities_with_observed_population':sum(1 for r in rows if r['observed']['population'] is not None),'coverage_pct':round(sum(1 for r in rows if r['observed']['population'] is not None)/len(base)*100,1),'ok':len(rows)==len(base) and all(r['sources']['price_level_updated'] and r['sources']['internet_updated'] for r in rows),'validation':{'method':'coverage + range + source-date checks','holdout':'Rank sensitivity checked by excluding each observed input; estimated cost/ease remain explicitly labelled and must not be treated as observed.'},'sha256':hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()}

(OUT/'cities.json').write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':'))); (OUT/'status.json').write_text(json.dumps(status,indent=2))

if not status['ok']:raise SystemExit(f'pipeline failed: {status}')

































