// Read-only browser acceptance of a prepared local cycle. No social transport.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const base=process.env.FACTORY_UI_URL||'http://127.0.0.1:8790';
 const episode=process.env.FACTORY_EPISODE_ID||'recette-locale';
 const expectedStatus=process.env.FACTORY_EXPECTED_CALENDAR_STATUS||'completed';
 const output=process.env.FACTORY_UI_REPORT_DIRECTORY||'.local';
 require('node:fs').mkdirSync(output,{recursive:true});
 const browser=await chromium.launch({channel:process.env.FACTORY_BROWSER_CHANNEL||'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  const errors=[],mutations=[],external=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(r.method()!=='GET')mutations.push(r.url());if(!r.url().startsWith(base)&&!r.url().startsWith('data:')&&!r.url().startsWith('blob:'))external.push(r.url())});
  const state=await(await page.request.get(base+'/api/state?episode_id='+encodeURIComponent(episode))).json();
  const calendar=state.local_calendars.find(c=>c.episode_id===episode);
  assert(calendar&&calendar.status===expectedStatus,'Requires the explicitly expected local calendar status');
  for(const field of ['missing','blocked','stage_errors','selection_needs_review'])assert.equal((calendar[field]||[]).length,0,'Unresolved calendar check: '+field);
  if(expectedStatus==='partial')assert(calendar.surplus.length>0,'Partial is accepted only for documented capacity surplus');
  assert.equal(calendar.valid_for_publication,false);
  assert(!state.jobs.some(j=>j.kind==='dispatch'),'No dispatch jobs');
  await page.goto(base+'/?episode='+encodeURIComponent(episode)+'#overview');
  await page.waitForSelector('#initial',{state:'hidden'});
  assert((await page.locator('#next-step').textContent()).includes('Préparation locale terminée'));
  assert((await page.locator('.local-calendar').textContent()).includes('Aucun envoi ni programmation'));
  assert((await page.locator('.local-calendar').textContent()).includes('Calendrier prévisionnel'));
  const localStat=page.locator('#stats .stat').nth(2);
  assert((await localStat.textContent()).includes('Dates proposées'));
  assert.equal(Number(await localStat.locator('strong').textContent()),calendar.planned.length);
  await page.locator('nav [data-view="media"]').click();
  const videos=[];
  for(const asset of state.assets.filter(a=>a.qa_status==='local_passed')){
   const proof=await page.locator('video[aria-label="Rendu '+asset.asset_id+'"]').evaluate(async(v,expected)=>{
    v.muted=true;
    const wait=(name,action)=>new Promise((resolve,reject)=>{
     const timer=setTimeout(()=>reject(new Error('Video '+name+' timeout')),15000);
     v.addEventListener(name,()=>{clearTimeout(timer);resolve()},{once:true});
     v.addEventListener('error',()=>{clearTimeout(timer);reject(new Error('Video decoder error'))},{once:true});
     action();
    });
    await wait('loadedmetadata',()=>v.load());
    if(Math.abs(v.duration-expected)>.3)throw new Error('Video duration differs from asset');
    const samples=[];
    for(const at of [.2,Math.max(.3,v.duration-1)]){
     await wait('seeked',()=>{v.currentTime=at});
     const frame=new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>reject(new Error('No decoded video frame')),15000);
      v.requestVideoFrameCallback((_,m)=>{clearTimeout(timer);resolve({mediaTime:m.mediaTime,presentedFrames:m.presentedFrames})});
     });
     await v.play();samples.push(await frame);v.pause();
    }
    return {duration:v.duration,width:v.videoWidth,height:v.videoHeight,samples};
   },asset.duration_seconds);
   assert.equal(proof.width,asset.width);assert.equal(proof.height,asset.height);
   videos.push({asset_id:asset.asset_id,...proof});
  }
  await page.locator('nav [data-view="thumbnails"]').click();
  await page.waitForFunction(()=>Array.from(document.querySelectorAll('#view-thumbnails img')).filter(i=>i.complete&&i.naturalWidth>0).length>=3);
  assert(/Contrôles automatiques réussis|Contrôle enregistré/.test(await page.locator('#view-thumbnails').textContent()));
  const previews=page.locator('#view-thumbnails summary').filter({hasText:'Examiner à 160 px'});
  for(let i=0;i<await previews.count();i++)await previews.nth(i).click();
  const images=page.locator('#view-thumbnails img');
  for(let i=0;i<await images.count();i++){
   await images.nth(i).scrollIntoViewIfNeeded();
   await images.nth(i).evaluate(img=>new Promise((resolve,reject)=>{
    if(img.complete&&img.naturalWidth>0)return resolve();
    img.addEventListener('load',()=>resolve(),{once:true});img.addEventListener('error',()=>reject(new Error('Thumbnail decode failed')),{once:true});
   }));
  }
  const imageCount=await images.count();
  const currentBundles=state.thumbnail_bundles.filter(b=>b.review_status!=='superseded');
  assert(currentBundles.length>0,'Requires current thumbnail bundles');
  assert(currentBundles.every(b=>b.review_status==='local_passed'||b.review_status==='passed'&&b.independent_local_review),'All displayed thumbnail bundles must pass an identified review');
  assert.equal(imageCount,currentBundles.reduce((n,b)=>n+b.variants.length*2,0),'Every current concept must display its 320 px and 160 px previews');
  await page.evaluate(()=>scrollTo(0,0));
  await page.screenshot({path:output+'/autonomy-thumbnails-desktop.png',fullPage:true});
  for(const width of [375,768,1440]){
   await page.setViewportSize({width,height:900});
   for(const view of ['overview','media','publications','thumbnails','operations','results']){
    await page.locator('nav [data-view="'+view+'"]').click();
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Overflow '+width+' '+view);
   }
  }
  await page.setViewportSize({width:375,height:812});
  await page.locator('nav [data-view="overview"]').click();
  await page.screenshot({path:output+'/autonomy-calendar-mobile.png',fullPage:true});
  assert.deepEqual(errors,[]);assert.deepEqual(mutations,[]);assert.deepEqual(external,[]);
  require('node:fs').writeFileSync(output+'/browser-evidence.json',JSON.stringify({calendar_status:calendar.status,videos,thumbnail_previews_decoded:imageCount,errors,mutations,external},null,2));
  console.log('PASS: '+videos.length+' real videos decoded at both ends, '+imageCount+' thumbnail previews decoded, local calendar, automatic-review labels, six views at 375/768/1440 px, zero JS error, no mutation or external request.');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
