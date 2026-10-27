import { bundle } from '@remotion/bundler';
import { selectComposition, renderMedia, renderStill, openBrowser } from '@remotion/renderer';
import { readFile, mkdir } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
const root = path.resolve(import.meta.dirname, '..');
const output = path.resolve(root, '../../output');
const timeline = JSON.parse(await readFile(root + '/timeline.json', 'utf8'));
const mode = process.argv[2] ?? 'preview';
await mkdir(output, { recursive: true });
await mkdir(root + '/analysis/proof', { recursive: true });
const browserExecutable =
  process.env.CHROME_PATH ?? 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const serveUrl = await bundle({
  entryPoint: root + '/src/index.tsx',
  publicDir: root + '/public',
  outDir: root + '/dist',
});
const browser = await openBrowser('chrome', { browserExecutable });
try {
  const composition = await selectComposition({
    serveUrl,
    id: 'SandboxIntro',
    puppeteerInstance: browser,
  });
  if (mode === 'stills') {
    const moments = [
      1.5, 5.8, 9.6, 13.8, 15.8, 19.6, 21.5, 25.5, 27.7, 29.1, 31.5, 35.5, 36.9, 39.7, 41.5, 44.4,
      45.8, 49.7, 51.1, 53.7, 57.5, 60.5,
    ];
    for (const time of moments) {
      await renderStill({
        composition,
        serveUrl,
        puppeteerInstance: browser,
        output: root + '/analysis/proof/' + time.toFixed(2) + '.png',
        frame: Math.round(time * timeline.fps),
        scale: 0.5,
      });
      console.log('Capture ' + time + 's');
    }
  } else {
    const final = mode === 'final';
    const silent = output + `/sandbox-intro-${mode}-silent.mp4`;
    let progress = -1;
    await renderMedia({
      composition,
      serveUrl,
      puppeteerInstance: browser,
      codec: 'h264',
      outputLocation: silent,
      muted: true,
      scale: final ? 1 : 2 / 3,
      crf: final ? 17 : 23,
      x264Preset: final ? 'medium' : 'veryfast',
      concurrency: Number(process.env.RENDER_CONCURRENCY ?? 6),
      imageFormat: 'jpeg',
      jpegQuality: final ? 98 : 90,
      onProgress: ({ progress: p }) => {
        const n = Math.floor(p * 10);
        if (n !== progress) {
          progress = n;
          console.log(`${mode}: ${n * 10}%`);
        }
      },
    });
    execFileSync(
      process.env.FFMPEG_PATH ?? 'ffmpeg',
      [
        '-v',
        'error',
        '-y',
        '-i',
        silent,
        '-i',
        root + '/' + timeline.audio,
        '-map',
        '0:v:0',
        '-map',
        '1:a:0',
        '-c:v',
        'copy',
        '-c:a',
        'aac',
        '-b:a',
        '320k',
        '-ar',
        '48000',
        '-t',
        String(timeline.duration),
        '-movflags',
        '+faststart',
        '-metadata',
        'title=SANDBOX - Générique officiel',
        output + `/sandbox-intro-${mode}.mp4`,
      ],
      { stdio: 'inherit' },
    );
    console.log(output + `/sandbox-intro-${mode}.mp4`);
  }
} finally {
  await browser.close({ silent: true });
}
