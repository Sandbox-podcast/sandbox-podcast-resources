const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try {
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8765/');
 await page.waitForSelector('#initial',{state:'hidden'});
 await page.waitForFunction(()=>document.querySelector('#workspace').textContent.includes('Recette'));
 await page.screenshot({path:'.local/factory-rework-desktop.png',fullPage:true});
 for(const view of ['publications','media','thumbnails','operations','results','overview']){
  await page.locator('[data-view="'+view+'"]').click();
  assert(await page.locator('#view-'+view).isVisible());
 }
 await page.locator('[data-view="media"]').click();
 const video=page.locator('video').first();
 await video.evaluate(async v=>{v.muted=true;await v.play();v.dataset.testIdentity='preserved';});
 await page.locator('#refresh').click();
 await page.waitForFunction(()=>!document.querySelector('#refresh').disabled);
 assert.equal(await video.getAttribute('data-test-identity'),'preserved');
 assert.equal(await video.evaluate(v=>v.paused),false);
 await video.evaluate(v=>v.pause());
 await page.locator('#assets details summary').first().click();
 await page.locator('#refresh').click();
 await page.waitForFunction(()=>!document.querySelector('#refresh').disabled);
 assert(await page.locator('#assets details').first().evaluate(d=>d.open));
 await page.locator('[data-view="thumbnails"]').click();
 await page.locator('#thumbnails img').first().waitFor();
 await page.waitForFunction(()=>[...document.querySelectorAll('#thumbnails .thumb')].every(i=>i.complete&&i.naturalWidth>0));
 await page.screenshot({path:'.local/factory-rework-thumbnails.png',fullPage:true});
 await page.locator('[data-view="publications"]').click();
 await page.locator('#platform').selectOption('youtube');
 await page.waitForFunction(()=>document.querySelector('#publication-count').textContent.startsWith('2 '));
 await page.reload();await page.waitForSelector('#initial',{state:'hidden'});
 assert.equal(await page.locator('#platform').inputValue(),'youtube');
 assert(await page.locator('#view-publications').isVisible());
 await page.locator('#search').fill('DOES NOT EXIST');
 assert(await page.getByText('Aucun contenu ne correspond').isVisible());
 await page.locator('#search').fill('');
 const download=page.waitForEvent('download');await page.locator('#export').click();
 assert.equal((await download).suggestedFilename(),'factory-diagnostic.json');
 await page.locator('#platform').selectOption('');
 await page.locator('[data-view="overview"]').click();
 await page.setViewportSize({width:375,height:812});
 await page.screenshot({path:'.local/factory-rework-mobile.png',fullPage:true});
 for(const view of ['overview','publications','media','thumbnails','operations','results']){
  await page.locator('[data-view="'+view+'"]').click();
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'overflow '+view);
 }
 await page.route('**/api/state?*',r=>r.abort());
 await page.locator('#refresh').click();
 await page.waitForSelector('#error',{state:'visible'});
 assert((await page.locator('#error').textContent()).includes('dernières données'));
 assert.deepEqual(errors,[]);
 console.log('PASS: six views, actual video playback preserved, open details, thumbnails, URL filters, empty state, export, 375px overflow, network error; no JS errors.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
