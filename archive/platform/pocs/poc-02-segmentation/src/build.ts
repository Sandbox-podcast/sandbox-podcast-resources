/** Assemble la page du banc (HTML + bundle) dans dist/. */
import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { build } from 'esbuild';

const root = join(import.meta.dirname, '..');
const dist = join(root, 'dist');
await mkdir(dist, { recursive: true });

await build({
  entryPoints: [join(root, 'src', 'page', 'bench.ts')],
  outfile: join(dist, 'bench.js'),
  bundle: true,
  format: 'iife',
  platform: 'browser',
  target: 'chrome120',
  logLevel: 'info',
});
await writeFile(
  join(dist, 'index.html'),
  '<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>POC 2</title></head><body><script src="/mp/selfie_segmentation.js"></script><script src="bench.js"></script></body></html>\n',
);
console.log('Page du banc construite dans', dist);
