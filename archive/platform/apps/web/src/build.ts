/** Assemble l'application web dans dist/ (servie par l'API : WEB_DIR). */
import { copyFile, mkdir, readdir } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { build } from 'esbuild';

const root = join(import.meta.dirname, '..');
const dist = join(root, 'dist');
await mkdir(dist, { recursive: true });
await build({
  entryPoints: [join(root, 'src', 'main.ts')],
  outfile: join(dist, 'app.js'),
  bundle: true,
  format: 'iife',
  platform: 'browser',
  target: 'chrome120',
  minify: true,
  logLevel: 'info',
});
for (const file of ['index.html', 'styles.css'])
  await copyFile(join(root, 'public', file), join(dist, file));
// Détourage : scripts, modèles et WebAssembly de MediaPipe, servis depuis la même origine (/mp/).
const require = createRequire(import.meta.url);
const mediaPipe = dirname(require.resolve('@mediapipe/selfie_segmentation/package.json'));
await mkdir(join(dist, 'mp'), { recursive: true });
for (const file of await readdir(mediaPipe)) {
  if (/\.(js|wasm|tflite|binarypb|data)$/.test(file))
    await copyFile(join(mediaPipe, file), join(dist, 'mp', file));
}
console.log('Application web construite dans', dist);
