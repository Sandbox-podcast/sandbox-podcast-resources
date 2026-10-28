// Run against the local factory. Read-only; browser fixtures never alter SQLite.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const base=process.env.FACTORY_UI_URL||'http://127.0.0.1:8765';
 const state=await (await page.request.get(base+'/api/state?episode_id=episode-003')).json();
 assert(state.candidates.length>0,'Requires the analysed episode-003');
 await page.goto(base+'/?episode=episode-003#publications');
 await page.waitForSelector('#initial',{state:'hidden'});
 assert((await page.locator('#next-step').textContent()).includes(state.candidates.length+' passages proposés'));
 assert((await page.locator('#publications').textContent()).includes('Aucune publication préparée'));
 await page.locator('#publications').getByRole('link',{name:'Examiner les passages proposés'}).click();
 assert(await page.locator('#view-media').isVisible());
 assert.equal(await page.locator('.candidate-card').count(),state.candidates.length);
 const card=page.locator('.candidate-card').first();
 assert(await card.locator('.timecode').isVisible());
 assert((await card.locator('.timecode').textContent()).includes('secondes'));
 assert((await card.getByRole('link',{name:'Voir ce passage sur YouTube'}).getAttribute('href')).includes('eEsaxtmDjR4&t='));
 assert.equal(await card.locator('pre').isVisible(),false);
 assert.equal(await page.locator('#platform').isVisible(),false);
 await page.screenshot({path:'.local/factory-novice-passages.png',fullPage:true});
 await page.locator('#search').fill('NOT PRESENT 123');
 assert(await page.getByText('Aucun passage ne correspond à ta recherche',{exact:true}).isVisible());
 await page.locator('#search').fill('');
 const first=page.locator('.candidate-card').first();await first.locator('details').first().locator('summary').click();
 await page.locator('#refresh').click();await page.waitForFunction(()=>!document.querySelector('#refresh').disabled);
 assert(await first.locator('details').first().evaluate(d=>d.open));
 for(const width of [375,768,1440]){
  await page.setViewportSize({width,height:900});
  for(const view of ['overview','media','publications','thumbnails','operations','results']){
   await page.locator('nav [data-view="'+view+'"]').click();
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Overflow '+width+' '+view);
  }
 }
 await page.setViewportSize({width:1440,height:1000});await page.locator('nav [data-view="publications"]').click();
 await page.screenshot({path:'.local/factory-novice-publications.png',fullPage:true});
 await page.setViewportSize({width:375,height:812});await page.locator('nav [data-view="overview"]').click();
 await page.screenshot({path:'.local/factory-novice-mobile.png',fullPage:true});
 // State presentation must adapt to no episode and to downstream work without
 // claiming that earlier reviews were completed.
 const empty={...state,episodes:[],analyses:[],candidates:[],assets:[],publications:[],attention:[],jobs:[],windows:[],thumbnail_bundles:[]};
 await page.route('**/api/state?*',r=>r.fulfill({json:empty}));await page.locator('#refresh').click();
 await page.waitForFunction(()=>document.querySelector('#next-step').textContent.includes('Commencer avec un épisode'));
 await page.unroute('**/api/state?*');
 await page.route('**/api/state?*',r=>r.fulfill({json:{...state,candidates:state.candidates.map(c=>({...c,decision:'retained'}))}}));
 await page.locator('#refresh').click();await page.waitForFunction(()=>document.querySelector('#next-step').textContent.includes('attendent leur montage'));
 assert.deepEqual(errors,[]);
 console.log('PASS: real episode, actionable empty publications, readable candidates/timecodes/source links, details preserved, 6 views at 375/768/1440px, no-episode and retained-only states; no JS errors.');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
