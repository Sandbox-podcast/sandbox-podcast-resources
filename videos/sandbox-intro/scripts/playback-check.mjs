import { createRequire } from 'node:module';
import { writeFile } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const require = createRequire(import.meta.url);
const {
  chromium,
} = require('C:/Users/Lou/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root = path.resolve(import.meta.dirname, '..');
const browser = await chromium.launch({
  executablePath:
    process.env.CHROME_PATH ?? 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  headless: true,
});
const page = await browser.newPage();
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));
const results = [];
try {
  await page.goto(pathToFileURL(path.resolve(root, '../../output/preview.html')).href);
  for (const variant of ['final', 'preview']) {
    await page.locator('video').evaluate((video, name) => {
      video.src = `sandbox-intro-${name}.mp4`;
      video.muted = true;
      video.load();
    }, variant);
    await page.waitForFunction(() => document.querySelector('video').readyState >= 2);
    await page.locator('video').evaluate((video) => video.play());
    await page.waitForTimeout(1200);
    const playback = await page.locator('video').evaluate((video) => ({
      duration: video.duration,
      width: video.videoWidth,
      height: video.videoHeight,
      time: video.currentTime,
      frames: video.getVideoPlaybackQuality().totalVideoFrames,
      error: video.error?.message ?? null,
    }));
    if (playback.time < 0.5 || playback.frames < 10 || playback.error)
      throw new Error(JSON.stringify(playback));
    await page.locator('video').evaluate((video) => video.pause());
    for (const time of [5.8, 13.8, 19.6, 27.7, 35.5, 41.5, 44.4, 49.7, 53.7, 60.5, 63.4]) {
      await page.locator('video').evaluate(
        (video, t) =>
          new Promise((resolve) => {
            video.addEventListener('seeked', resolve, { once: true });
            video.currentTime = t;
          }),
        time,
      );
      const state = await page.locator('video').evaluate((video) => ({
        time: video.currentTime,
        ready: video.readyState,
        error: video.error?.message ?? null,
      }));
      if (Math.abs(state.time - time) > 0.05 || state.ready < 2 || state.error)
        throw new Error(JSON.stringify(state));
    }
    results.push({ variant, playback, seeks: 11 });
  }
  if (errors.length) throw new Error(errors.join('\n'));
  await writeFile(
    root + '/analysis/playback.json',
    JSON.stringify({ browser: 'Chrome', results, errors }, null, 2),
  );
  console.log(JSON.stringify(results));
} finally {
  await browser.close();
}
