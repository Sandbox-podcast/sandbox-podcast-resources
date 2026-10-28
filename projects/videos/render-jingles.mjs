import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { mkdir, readFile, stat, writeFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';

const root = path.dirname(fileURLToPath(import.meta.url));
const manifest = JSON.parse(await readFile(path.join(root, 'jingles.json'), 'utf8'));
const require = createRequire(import.meta.url);
let playwright;
try {
  playwright = require('playwright');
} catch {
  const bundledModules =
    process.env.CODEX_NODE_MODULES ??
    'C:\\Users\\Lou\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\node\\node_modules';
  playwright = require(path.join(bundledModules, 'playwright'));
}

const args = new Set(process.argv.slice(2));
const requested = [...args].find((arg) => arg.startsWith('--only='))?.slice('--only='.length);
const selected = requested
  ? manifest.projects.filter((project) => project.id === requested)
  : manifest.projects;
if (!selected.length) throw new Error(`Unknown jingle: ${requested}`);

const fps = manifest.fps;
const frameCountFor = (duration) => Math.ceil(duration * fps);
const chromePath =
  process.env.CHROME_PATH ?? 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const ffmpegPath = process.env.FFMPEG_PATH ?? 'ffmpeg';
const browser = await playwright.chromium.launch({
  executablePath: chromePath,
  headless: true,
  args: ['--disable-gpu', '--disable-dev-shm-usage'],
});

const waitForDrain = (stream) =>
  new Promise((resolve, reject) => {
    const onError = (error) => reject(error);
    stream.once('error', onError);
    stream.once('drain', () => {
      stream.off('error', onError);
      resolve();
    });
  });

try {
  for (const project of selected) {
    const projectDir = path.join(root, project.folder);
    const outputDir = path.join(projectDir, 'renders');
    const proofDir = path.join(outputDir, 'proof');
    await mkdir(proofDir, { recursive: true });
    const outputPath = path.join(outputDir, project.outputFile);
    const requiredAssets = [
      path.join(projectDir, 'assets', project.heroFile ?? 'hero.png'),
      path.join(projectDir, 'assets', 'sandbox-logov2.png'),
      path.join(projectDir, 'assets', 'music.mp3'),
    ];
    for (const asset of requiredAssets) {
      try {
        await stat(asset);
      } catch {
        throw new Error(
          `${project.id} is missing a required asset: ${path.relative(projectDir, asset)}`,
        );
      }
    }
    const htmlUrl = `${pathToFileURL(path.join(projectDir, 'production.html')).href}?render=1`;
    const page = await browser.newPage({
      viewport: { width: manifest.width, height: manifest.height },
      deviceScaleFactor: 1,
    });
    const pageErrors = [];
    page.on('pageerror', (error) => pageErrors.push(error.message));
    await page.goto(htmlUrl, { waitUntil: 'load', timeout: 30000 });
    await page.waitForFunction(() => window.__JINGLE_READY__ === true, { timeout: 30000 });
    await page.waitForFunction(
      () => {
        const image = document.querySelector('#hero-image');
        const logo = document.querySelector('#brand-logo');
        return image?.complete && image.naturalWidth > 0 && logo?.complete && logo.naturalWidth > 0;
      },
      { timeout: 30000 },
    );
    if (pageErrors.length) throw new Error(`${project.id} browser error: ${pageErrors.join('; ')}`);

    const ffmpeg = spawn(
      ffmpegPath,
      [
        '-hide_banner',
        '-loglevel',
        'error',
        '-y',
        '-f',
        'image2pipe',
        '-vcodec',
        'mjpeg',
        '-framerate',
        String(fps),
        '-i',
        'pipe:0',
        '-i',
        path.join(projectDir, 'assets', 'music.mp3'),
        '-map',
        '0:v:0',
        '-map',
        '1:a:0',
        '-frames:v',
        String(frameCountFor(project.duration)),
        '-c:v',
        'libx264',
        '-preset',
        'slow',
        '-crf',
        '16',
        '-profile:v',
        'high',
        '-level:v',
        '4.2',
        '-pix_fmt',
        'yuv420p',
        '-c:a',
        'aac',
        '-b:a',
        '256k',
        '-ar',
        '48000',
        '-movflags',
        '+faststart',
        '-metadata',
        `title=${project.title} · Jingle Sandbox`,
        '-metadata',
        'artist=Sandbox TalkShow',
        '-metadata',
        'comment=Motion design original · 1920x1080 · 30 fps',
        outputPath,
      ],
      { stdio: ['pipe', 'ignore', 'pipe'] },
    );
    let ffmpegError = '';
    ffmpeg.stderr.setEncoding('utf8');
    ffmpeg.stderr.on('data', (chunk) => {
      ffmpegError += chunk;
    });
    const ffmpegExit = new Promise((resolve, reject) => {
      ffmpeg.once('error', reject);
      ffmpeg.once('close', (code) =>
        code === 0 ? resolve() : reject(new Error(`ffmpeg exited ${code}: ${ffmpegError}`)),
      );
    });

    const frameCount = frameCountFor(project.duration);
    const proofTimes = [
      1.1,
      Math.min(project.duration - 2.3, project.finaleStart),
      project.duration - 1.1,
    ];
    const proofFrames = new Map(proofTimes.map((time) => [Math.round(time * fps), time]));
    console.log(`Rendering ${project.title}: ${frameCount} frames at ${fps} fps`);
    for (let frame = 0; frame < frameCount; frame += 1) {
      const time = Math.min(project.duration, frame / fps);
      await page.evaluate((value) => window.renderAt(value), time);
      const screenshot = await page.screenshot({ type: 'jpeg', quality: 98, timeout: 30000 });
      if (proofFrames.has(frame)) {
        const label = proofFrames.get(frame).toFixed(2).replace('.', '-');
        await writeFile(path.join(proofDir, `frame-${label}s.jpg`), screenshot);
      }
      if (!ffmpeg.stdin.write(screenshot)) await waitForDrain(ffmpeg.stdin);
      if ((frame + 1) % 240 === 0 || frame === frameCount - 1) {
        console.log(`  ${project.id}: ${Math.round(((frame + 1) / frameCount) * 100)}%`);
      }
    }
    ffmpeg.stdin.end();
    await ffmpegExit;
    await page.close();
    console.log(`Created ${path.relative(root, outputPath)}`);
  }
} finally {
  await browser.close();
}
