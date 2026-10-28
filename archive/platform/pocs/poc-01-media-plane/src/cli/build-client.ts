/** Assemble la page cliente (HTML + bundle) dans dist/. */
import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { build } from 'esbuild';

const root = join(import.meta.dirname, '..', '..');
const dist = join(root, 'dist');
await mkdir(dist, { recursive: true });

await build({
  entryPoints: [join(root, 'src', 'browser', 'client.ts')],
  outfile: join(dist, 'client.js'),
  bundle: true,
  format: 'iife',
  platform: 'browser',
  target: 'chrome120',
  sourcemap: false,
  logLevel: 'info',
});
await writeFile(
  join(dist, 'index.html'),
  '<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>POC 1</title></head><body><script src="client.js"></script></body></html>\n',
);
console.log('Page cliente construite dans', dist);
