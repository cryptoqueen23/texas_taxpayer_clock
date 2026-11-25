import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve('dist');
const routes=['','revenue','debt','tax-rates','calculator','county-map','local-sales-tax','local-sales-tax-history','government/copperas-cove','government/copperas-cove-isd','government/coryell-county','school-rankings','school-spending','appraisal-districts','economic-development','edc-history','local-finances','pensions','household-burden','methodology','support','watchlist','compare'];
let checked=0;const errors=[];
for(const lang of ['en','es'])for(const route of routes){
 const relative=[lang==='es'?'es':'',route].filter(Boolean).join('/');
 const file=path.join(root,relative,'index.html');
 const html=fs.readFileSync(file,'utf8');
 if(!new RegExp('<html[^>]*lang=["\\\']?'+lang+'(?:["\\\'\\s>])','i').test(html))errors.push(relative+': missing language');
 if(!/<title[^>]*>[^<]+<\/title>/i.test(html))errors.push(relative+': missing title');
 if(!/<meta[^>]*name=["']?viewport/i.test(html))errors.push(relative+': missing viewport');
 if(!/<h1(?:\s|>)/i.test(html))errors.push(relative+': missing h1');
 for(const m of html.matchAll(/<a\b[^>]*\bhref="(\/(?!\/)[^"]*)"/gi)){
 const url=m[1].split(/[?#]/)[0];const dest=path.resolve(root,'.'+url);
 if(!dest.startsWith(root+path.sep)&&dest!==root){errors.push(relative+': invalid path '+url);continue;}
 if(!fs.existsSync(dest)||fs.statSync(dest).isDirectory()&&!fs.existsSync(path.join(dest,'index.html')))errors.push(relative+': broken link '+url);
 }
 checked++;
}
console.log(JSON.stringify({checked,errors},null,2));assert.equal(errors.length,0,'Static route quality checks failed');

// Comparison regression checks: both locale pages, accessible controls, mobile layout and honest missing-data labels.
for(const lang of ['en','es']){
 const p=path.join(root,lang==='es'?'es/compare/index.html':'compare/index.html');
 const html=fs.readFileSync(p,'utf8');
 for(const [label,pattern] of Object.entries({
  searchLabel:/<label[^>]*for="search"/,
  searchInput:/<input[^>]*id="search"/,
  resultsRegion:/id="results"[^>]*role="region"/,
  selectedRegion:/id="chosen"[^>]*aria-live="polite"/,
  responsiveCards:/grid-template-columns:repeat\(auto-fit/,
  missingData:/Not reported|No reportado/,
  perResident:/Debt principal per resident|Principal de deuda por residente/,
  historicalTrend:/Reported debt principal trend|Tendencia del principal/,
  profileLinks:/government\//,
  noCheckout:/<form[^>]*action=["'][^"']*(?:paypal|stripe|zelle)/i
 })){
  if(label==='noCheckout'){if(pattern.test(html))throw new Error(lang+' compare contains payment form');}
  else if(!pattern.test(html))throw new Error(lang+' compare missing '+label);
 }
}
console.log('Bilingual comparison regression checks passed');
