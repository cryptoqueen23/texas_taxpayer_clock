import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
const raw=fs.readFileSync('public/data/tax-units.json');
const rows=JSON.parse(raw);
assert(rows.length>=4862);
assert.equal(new Set(rows.map(r=>r.id)).size,rows.length);
assert.equal(rows.filter(r=>r.id.endsWith('-000-00')).length,254);
const aliases=JSON.parse(fs.readFileSync('src/data/profile-aliases.json','utf8'));
for(const r of rows){
 assert.match(r.id,/^\d{3}-\d{3}-\d{2}$/);
 assert(typeof r.name==='string'&&r.name.trim());
 for(const [year,v] of Object.entries(r.rates)){
  assert(['2021','2022','2023','2024','2025'].includes(year));
  assert(v===null||(typeof v==='number'&&Number.isFinite(v)&&v>=0));
 }
 for(const prefix of ['','es/']){
  const path='dist/'+prefix+'government/'+(aliases[r.id]??r.id)+'/index.html';
  assert(fs.existsSync(path),path);
 }
}
for(const id of ['copperas-cove','copperas-cove-isd','austin','coryell-county']){
 const html=fs.readFileSync('dist/government/'+id+'/index.html','utf8');
 assert.equal((html.match(/<\/html>/g)||[]).length,1);
 assert(html.includes(id==='copperas-cove-isd'?'School district calculated property tax levies':'Historical property tax rates'));
 if(id==='copperas-cove-isd'){assert(html.includes('Pending verification'));assert(html.indexOf('First reported 2026 bond issuance')<html.indexOf('FY 2025 outstanding principal'));assert(!html.includes('Local sales tax allocations'));}
}
console.log('Verified '+rows.length*2+' bilingual profile routes; SHA256 '+crypto.createHash('sha256').update(raw).digest('hex'));

const debt=JSON.parse(fs.readFileSync('public/data/local-debt-2025.json','utf8'));
assert.equal(debt.fiscalYear,2025);
assert.equal(debt.records.length,3319);
assert.equal(new Set(debt.records.map(r=>r.id)).size,3319);
for(const r of debt.records) for(const k of ['count','principal','interest','repayment']) assert(Number.isSafeInteger(r[k])&&r[k]>=0);
for(const [k,v] of Object.entries({count:17718,principal:365500296028,interest:195978007362,repayment:561478303383})) assert.equal(debt.records.reduce((s,r)=>s+r[k],0),v);
const ids=new Set(rows.map(r=>r.id));
const matched=debt.records.filter(r=>ids.has(r.id));
assert.equal(matched.length,3094);
for(const r of matched) for(const prefix of ['','es/']){
 const html=fs.readFileSync('dist/'+prefix+'government/'+(aliases[r.id]??r.id)+'/index.html','utf8');
 assert(html.includes(new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(r.principal)),r.id);
}
console.log('Verified 3094 matched debt profiles in both languages; 225 unmatched debt records retained.');

for(const prefix of ['','es/']) for(const route of ['debt','tax-rates']) assert(fs.existsSync('dist/'+prefix+route+'/index.html'));

for(const prefix of ['','es/']) assert(fs.existsSync('dist/'+prefix+'calculator/index.html'));

const hist=JSON.parse(fs.readFileSync('public/data/local-debt-history.json','utf8'));
assert.deepEqual(hist.years,[2016,2017,2018,2019,2020,2021,2022,2023,2024,2025]);
for(const r of debt.records) assert.deepEqual(hist.records[r.id]['2025'],[r.principal,r.interest,r.repayment,r.count],r.id);
for(const years of Object.values(hist.records)) for(const [y,v] of Object.entries(years)){assert(hist.years.includes(Number(y)));assert.equal(v.length,4);assert(v.every(n=>Number.isSafeInteger(n)&&n>=0));}
console.log('Historical dataset reconciled with FY2025 debt records');

const denominators=JSON.parse(fs.readFileSync('public/data/local-debt-denominators-2025.json','utf8'));
assert.equal(denominators.fiscalYear,2025);assert.equal(denominators.sourceSha256,debt.sourceSha256);assert.deepEqual(denominators.fields,['Population','StudentHeadcount','TaxableValue','BudgetedTotalExpenditures','ADA']);assert.equal(Object.keys(denominators.records).length,debt.records.length);for(const r of debt.records){const v=denominators.records[r.id];assert.equal(v.length,5);assert(v.every(n=>n===null||(Number.isFinite(n)&&n>=0)));}

const geo=JSON.parse(fs.readFileSync('public/data/texas-county-boundaries-2025.json','utf8'));assert.equal(geo.counties.length,254);assert.equal(new Set(geo.counties.map(c=>c.taxId)).size,254);for(const c of geo.counties){assert(ids.has(c.taxId));assert.match(c.fips,/^48\d{3}$/);assert(c.path.startsWith('M'));}for(const prefix of ['','es/'])assert(fs.existsSync('dist/'+prefix+'county-map/index.html'));

for(const prefix of ['','es/'])assert(fs.existsSync('dist/'+prefix+'revenue/index.html'));

const finances=JSON.parse(fs.readFileSync('public/data/texas-state-finances-2026.json','utf8'));assert.equal(finances.fiscalYear,2026);assert.equal(Object.keys(finances.historical).length,24);for(const rows of Object.values(finances.historical))for(const r of rows){assert.equal(r.monthly.length,12);assert(r.annual===null||Number.isFinite(r.annual));assert(r.monthly.every(v=>v===null||Number.isFinite(v)));}for(const prefix of ['','es/'])assert(fs.readFileSync('dist/'+prefix+'revenue/index.html','utf8').includes('213,724,395,531'));

const sales=JSON.parse(fs.readFileSync('public/data/local-sales-tax-2026-11.json','utf8'));assert.equal(sales.latestPeriod,'2026-11');assert.equal(sales.records.length,1827);assert.equal(new Set(sales.records.map(r=>JSON.stringify(r.slice(0,3)))).size,1827);for(const r of sales.records){assert.equal(r.length,8);assert(r.slice(3).every(Number.isFinite));assert(r.slice(4).every(Number.isSafeInteger));}for(const prefix of ['','es/'])assert(fs.existsSync('dist/'+prefix+'local-sales-tax/index.html'));

const salesHistory=JSON.parse(fs.readFileSync('public/data/local-sales-tax-history.json','utf8'));const historyByKey=new Map(salesHistory.records.map(r=>[JSON.stringify(r.slice(0,3)),r[3]]));assert.equal(historyByKey.size,salesHistory.records.length);for(const r of salesHistory.records)for(const [p,v] of Object.entries(r[3])){assert(/^20(1[3-9]|2[0-6])-(11|12)$/.test(p));assert(p!=='2026-12');assert(Number.isSafeInteger(v));}for(const r of sales.records)assert.equal(historyByKey.get(JSON.stringify([r[0],r[1],r[2]??'']))?.['2026-11'],r[6]);for(const prefix of ['','es/'])assert(fs.existsSync('dist/'+prefix+'local-sales-tax-history/index.html'));

const salesCrosswalk=JSON.parse(fs.readFileSync('src/data/sales-tax-crosswalk.json','utf8'));const salesKeys=new Set(sales.records.map(r=>JSON.stringify(r.slice(0,3))));for(const [id,k] of Object.entries(salesCrosswalk)){assert(ids.has(id));assert(salesKeys.has(JSON.stringify(k)));}assert.equal(salesCrosswalk['050-101-03'][1],'Copperas Cove');

const schoolLevies=JSON.parse(fs.readFileSync('public/data/school-levies-2021-2025.json','utf8'));
assert.deepEqual(Object.keys(schoolLevies.years).sort(),['2021','2022','2023','2024','2025']);
for(const [year,rows] of Object.entries(schoolLevies.years)){assert.equal(Object.keys(rows).length,({'2021':1015,'2022':1014,'2023':1014,'2024':1013,'2025':1013})[year]);for(const [id,r] of Object.entries(rows)){assert(/^\d{3}-\d{3}-02$/.test(id));assert.equal(r.length,5);assert(typeof r[0]==='string');assert(r.slice(1).every(v=>v===null||Number.isFinite(v)));}}
assert.equal(schoolLevies.years['2025']['050-910-02'][4],14511511);

for(const prefix of ['','es/']) assert(fs.existsSync('dist/'+prefix+'school-rankings/index.html'));
