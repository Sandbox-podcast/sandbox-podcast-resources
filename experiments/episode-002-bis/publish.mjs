import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import process from 'node:process';
import { Buffer } from 'node:buffer';
import console from 'node:console';
import { sourceMedia } from './media.js';

const sourceRoot = dirname(fileURLToPath(import.meta.url));
const defaultSiteRoot = resolve(sourceRoot, '../../../sandbox-podcast-site/apps/site');
const siteRoot = process.env['SANDBOX_SITE_ROOT']
  ? resolve(process.env['SANDBOX_SITE_ROOT'])
  : defaultSiteRoot;
export const publicRoot = resolve(siteRoot, 'public/slides/episode-002-bis');
export const publicFiles = [
  'index.html',
  'show.js',
  'show.css',
  'model.js',
  'visuals.js',
  'content.js',
  'media.js',
  'assets/logo.png',
  'assets/archivo.woff2',
  'assets/font-license.txt',
  ...['radar', 'build', 'clash', 'beta'].map((name) => `assets/${name}-hero.png`),
  ...Object.keys(sourceMedia).map((name) => `assets/sources/${name}.jpg`),
  'assets/sources/persuasion-zoom.jpg',
];

export function publicHtml(html) {
  const marker = '<meta name="sandbox-sync" content="local-server" />';
  if (!html.includes(marker)) throw new Error('Mode de synchronisation absent du HTML BIS.');
  return html.replace(marker, '<meta name="sandbox-sync" content="browser" />');
}

export async function expectedPublicFile(file) {
  const bytes = await readFile(resolve(sourceRoot, file));
  return file === 'index.html' ? Buffer.from(publicHtml(bytes.toString('utf8'))) : bytes;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const check = process.argv.includes('--check');
  for (const file of publicFiles) {
    const expected = await expectedPublicFile(file);
    const destination = resolve(publicRoot, file);
    if (check) {
      const actual = await readFile(destination);
      if (!actual.equals(expected)) throw new Error(`Copie publique BIS différente : ${file}`);
    } else {
      await mkdir(dirname(destination), { recursive: true });
      await writeFile(destination, expected);
    }
  }
  console.log(
    `${publicFiles.length} fichiers BIS ${check ? 'vérifiés' : 'copiés'} dans public/slides/episode-002-bis.`,
  );
}
