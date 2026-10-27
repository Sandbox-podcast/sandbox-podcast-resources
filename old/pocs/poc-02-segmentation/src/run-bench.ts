/**
 * Lance un essai du banc dans Chrome (fenêtre hors écran, GPU actif) et relève le CPU de Chrome et
 * l'utilisation du GPU. Exemples :
 *   node src/run-bench.ts --participants 3 --seconds 30 --mode mediapipe
 *   node src/run-bench.ts --participants 3 --seconds 60 --mode mediapipe --controller true --stress 30
 * Résultat : .local/results/<nom>.json
 */
import { createServer } from 'node:http';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { createRequire } from 'node:module';
import {
  chromeCpuSeconds,
  launchChrome,
  sampleGpu,
  type GpuSample,
} from '@podcast/poc-01-media-plane/browser-runner.ts';
import type { BenchConfig } from './page/bench.ts';

const args = process.argv.slice(2);
const arg = (name: string, fallback: string): string => {
  const index = args.indexOf(`--${name}`);
  return index >= 0 ? (args[index + 1] ?? fallback) : fallback;
};
const config: BenchConfig = {
  participants: Number(arg('participants', '3')),
  seconds: Number(arg('seconds', '30')),
  mode: arg('mode', 'mediapipe') as BenchConfig['mode'],
  controller: arg('controller', 'false') === 'true',
  stressMs: Number(arg('stress', '0')),
  stressPerSegmentationMs: Number(arg('stress-seg', '0')),
  lockLevel: arg('lock', '') === '' ? null : Number(arg('lock', '0')),
  modelSelection: Number(arg('model', '1')) as 0 | 1,
};
const name = arg('name', `${config.mode}-${String(config.participants)}p`);

const root = join(import.meta.dirname, '..');
const require = createRequire(import.meta.url);
const mpDir = dirname(require.resolve('@mediapipe/selfie_segmentation/package.json'));
const sourcePath = resolve(root, '..', 'poc-01-media-plane', '.local', 'source-1080p30.mp4');

const types: Record<string, string> = {
  '.js': 'text/javascript',
  '.html': 'text/html',
  '.wasm': 'application/wasm',
  '.mp4': 'video/mp4',
};
const server = createServer((request, response) => {
  const url = new URL(request.url ?? '/', 'http://localhost').pathname;
  const file =
    url === '/'
      ? join(root, 'dist', 'index.html')
      : url === '/source.mp4'
        ? sourcePath
        : url.startsWith('/mp/')
          ? join(mpDir, url.slice(4).replace(/[/\\]/g, ''))
          : join(root, 'dist', url.slice(1).replace(/[/\\]/g, ''));
  const ext = file.slice(file.lastIndexOf('.'));
  readFile(file).then(
    (body) => {
      response
        .writeHead(200, { 'content-type': types[ext] ?? 'application/octet-stream' })
        .end(body);
    },
    () => {
      response.writeHead(404).end();
    },
  );
});
await new Promise<void>((resolveListen) => server.listen(0, '127.0.0.1', resolveListen));
const address = server.address();
if (address === null || typeof address === 'string') throw new Error('adresse inconnue');
const url = `http://127.0.0.1:${String(address.port)}/`;

const browser = await launchChrome({ headed: true });
try {
  const cdp = await browser.newBrowserCDPSession();
  const page = await browser.newPage();
  page.on('console', (message) => {
    if (message.type() === 'error') console.log('[page]', message.text());
  });
  page.on('pageerror', (error) => {
    console.log('[erreur page]', error.message);
  });
  await page.goto(url);

  const gpuSamples: GpuSample[] = [];
  const sampling = { active: true };
  const sampler = (async () => {
    while (sampling.active) {
      await new Promise((r) => setTimeout(r, 2000));
      const sample = await sampleGpu();
      if (sample) gpuSamples.push(sample);
    }
  })();
  const cpuBefore = await chromeCpuSeconds(cdp);
  const wallBefore = Date.now();
  const result = (await page.evaluate(
    (c) =>
      (window as unknown as { bench: { run: (c: BenchConfig) => Promise<unknown> } }).bench.run(c),
    config,
  )) as Record<string, unknown>;
  const cpuSeconds = (await chromeCpuSeconds(cdp)) - cpuBefore;
  const wallSeconds = (Date.now() - wallBefore) / 1000;
  sampling.active = false;
  await sampler;

  const mean = (xs: number[]): number =>
    xs.length === 0 ? 0 : xs.reduce((a, b) => a + b, 0) / xs.length;
  const output = {
    name,
    ...result,
    chromeCpuPercentOfOneCore: Math.round((cpuSeconds / wallSeconds) * 1000) / 10,
    gpu: {
      samples: gpuSamples.length,
      meanPercent: Math.round(mean(gpuSamples.map((g) => g.gpuPercent)) * 10) / 10,
      maxPercent: Math.max(0, ...gpuSamples.map((g) => g.gpuPercent)),
    },
  };
  await mkdir(join(root, '.local', 'results'), { recursive: true });
  await writeFile(join(root, '.local', 'results', `${name}.json`), JSON.stringify(output, null, 2));
  console.log(JSON.stringify(output, null, 1));
} finally {
  await browser.close();
  server.close();
}
