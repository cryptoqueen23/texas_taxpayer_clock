import urllib.request, re, json, io
from urllib.parse import urljoin
from html.parser import HTMLParser
from openpyxl import load_workbook
from pathlib import Path
base='https://comptroller.texas.gov/taxes/property-tax/rates/index.php'
class Links(HTMLParser):
 def __init__(self): super().__init__(); self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag=='a': self.links.extend(v for k,v in attrs if k=='href')
def fetch(url):
 return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Texas Taxpayer Clock public data importer'}),timeout=90).read()
p=Links();p.feed(fetch(base).decode())
units={}
for year in range(2021,2026):
 links={urljoin(base,x) for x in p.links if f'{year}-total-rates-levies.xlsx' in x}
 if len(links)!=1: raise ValueError((year,links))
 w=load_workbook(io.BytesIO(fetch(links.pop())),read_only=True,data_only=True)
 seen={}
 for row in list(w.active.values)[3:]:
  name,id,rate=(row[0],row[1],row[2]) if year==2025 else (row[3],row[2],row[5])
  if not id or not isinstance(rate,(int,float)): continue
  id=str(id)[:10]; name=str(name).strip()
  if not re.fullmatch(r'\d{3}-\d{3}-\d{2}',id): continue
  rate=None if '*' in name else rate
  if id in seen and seen[id]!=rate: raise ValueError((year,id,'conflicting rates'))
  seen[id]=rate
  u=units.setdefault(id,{'id':id,'name':name.rstrip(' *'),'rates':{}})
  u['name']=name.rstrip(' *');u['rates'][str(year)]=rate
 if len(seen)<4000: raise ValueError('Incomplete source')
Path('public/data').mkdir(parents=True,exist_ok=True)
Path('public/data/tax-units.json').write_text(json.dumps(list(units.values()),ensure_ascii=False,separators=(',',':')))
print(len(units),'taxing units')
