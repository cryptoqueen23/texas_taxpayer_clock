import { chromium } from 'playwright';
import assert from 'node:assert/strict';
const base=process.env.TEST_BASE_URL||'http://127.0.0.1:4321';
const browser=await chromium.launch({headless:true});
try{
 for(const viewport of [{width:390,height:844},{width:1440,height:900}]){
  const page=await browser.newPage({viewport});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(const prefix of ['','es/']){
   const visit=async route=>{const response=await page.goto(base+'/'+prefix+route);assert(response?.ok(),route);assert.equal(await page.locator('html').getAttribute('lang'),prefix?'es':'en');};
   await visit('');
   assert(await page.locator('a[href="/'+prefix+'evidence/"]').count());
   await visit('unmatched-debt/');
   await page.waitForFunction(()=>document.querySelector('#count')?.textContent==='225 / 225');
   await page.locator('#filter').fill('014-000-19');
   await page.waitForFunction(()=>document.querySelector('#count')?.textContent==='1 / 225');
   assert.equal(await page.locator('tbody tr:visible').count(),1);
   await page.locator('#filter').fill('no-such-government-xyz');
   await page.waitForFunction(()=>document.querySelector('#count')?.textContent==='0 / 225');
   await visit('compare/');
   await page.locator('#search').fill('050-910-02');
   await page.locator('#results button').first().click();
   assert.equal(await page.locator('#chosen article').count(),1);
   assert(page.url().includes('ids='));
   await page.reload();
   await page.locator('#chosen article').waitFor();
   await page.locator('#chosen article button').click();
   assert.equal(await page.locator('#chosen article').count(),0);
   await visit('evidence/');
   assert((await page.locator('main').innerText()).includes('365,500,296,028'));
   assert.equal(await page.locator('tbody tr').count(),44);
   await visit('household-burden/');
   assert(await page.locator('input').count()>0);
   for(const route of ['household-burden/','unmatched-debt/','evidence/']){
    await visit(route);
    await page.keyboard.press('Tab');
    assert.equal(await page.locator(':focus').getAttribute('href'),'#main-content');
    await page.keyboard.press('Enter');
    assert.equal(await page.locator(':focus').getAttribute('id'),'main-content');
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),prefix+route+' horizontal page overflow');
    const metrics=await page.evaluate(()=>{const n=performance.getEntriesByType('navigation')[0];return {loadMs:n.loadEventEnd,transferBytes:n.transferSize,resourceBytes:performance.getEntriesByType('resource').reduce((s,r)=>s+r.transferSize,0)}});
    console.log(JSON.stringify({route:prefix+route,viewport:viewport.width,...metrics}));
   }
  }
  assert.deepEqual(errors,[]);
  await page.close();
 }
 console.log('Bilingual desktop and mobile browser smoke tests passed');
}finally{await browser.close();}
