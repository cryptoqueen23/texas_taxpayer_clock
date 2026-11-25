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
 assert(html.includes('Historical property tax rates'));
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
