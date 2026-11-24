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
