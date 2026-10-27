import { mkdir, mkdtemp, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { PAGE_CSP, readStatic, resolveStaticPath } from '../src/static.ts';

const root = join(tmpdir(), 'racine-web');

describe('chemins des pages', () => {
  it('« / » donne index.html et les extensions autorisées sont typées', () => {
    expect(resolveStaticPath(root, '/')?.file).toBe(join(root, 'index.html'));
    expect(resolveStaticPath(root, '/app.js')?.type).toBe('text/javascript; charset=utf-8');
    expect(resolveStaticPath(root, '/assets/style.css')?.type).toBe('text/css; charset=utf-8');
    expect(resolveStaticPath(root, '/icone.SVG')?.type).toBe('image/svg+xml');
    expect(resolveStaticPath(root, '/mp/modele.wasm')?.type).toBe('application/wasm');
    expect(resolveStaticPath(root, '/mp/selfie_segmentation.tflite')?.type).toBe(
      'application/octet-stream',
    );
  });

  it.each([
    '/../secret.js',
    '/%2e%2e/secret.js',
    '/a/../../secret.js',
    '/..%2f..%2fsecret.js',
    '/a\\..\\secret.js',
    '/app.js%00.html',
    '/.env.js',
    '/dossier/.cache/x.js',
    '/app.exe',
    '/app.map',
    '/app',
    '/%zz.js',
    '/config.json',
  ])('refuse %s', (url) => {
    expect(resolveStaticPath(root, url)).toBeNull();
  });

  it('lit un fichier, rend null un fichier absent ou un chemin refusé', async () => {
    const dir = await mkdtemp(join(tmpdir(), 'web-'));
    await mkdir(join(dir, 'assets'));
    await writeFile(join(dir, 'index.html'), '<h1>ok</h1>');
    await writeFile(join(dir, 'assets', 'a.js'), 'console.log(1)');
    expect((await readStatic(dir, '/'))?.body.toString()).toBe('<h1>ok</h1>');
    expect((await readStatic(dir, '/assets/a.js'))?.type).toContain('javascript');
    expect(await readStatic(dir, '/absent.js')).toBeNull();
    expect(await readStatic(dir, '/../x.js')).toBeNull();
  });

  it('la politique de contenu interdit scripts en ligne, objets et intégration', () => {
    expect(PAGE_CSP).toContain("script-src 'self'");
    expect(PAGE_CSP).not.toContain('unsafe-inline');
    // WebAssembly est permis (détourage), pas l'évaluation de code JavaScript.
    expect(PAGE_CSP).toContain("'wasm-unsafe-eval'");
    expect(PAGE_CSP.replace("'wasm-unsafe-eval'", '')).not.toContain('unsafe-eval');
    expect(PAGE_CSP).toContain("frame-ancestors 'none'");
    expect(PAGE_CSP).toContain("default-src 'none'");
  });
});
