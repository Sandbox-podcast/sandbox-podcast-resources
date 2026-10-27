import { readFile } from 'node:fs/promises';
import { join, resolve, sep } from 'node:path';

const TYPES: Record<string, string> = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  // Détourage (MediaPipe) : WebAssembly et modèles, servis depuis la même origine.
  '.wasm': 'application/wasm',
  '.tflite': 'application/octet-stream',
  '.binarypb': 'application/octet-stream',
  '.data': 'application/octet-stream',
};

/**
 * Politique de contenu des pages de l'application : uniquement des ressources de la même origine, aucun script
 * ni style en ligne, pas d'intégration dans une autre page. Les connexions WebSocket (LiveKit) sont permises.
 */
export const PAGE_CSP =
  "default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self'; connect-src 'self' ws: wss:; img-src 'self' data: blob:; media-src 'self' blob:; base-uri 'none'; form-action 'self'; frame-ancestors 'none'";

/**
 * Chemin de fichier correspondant à une URL, ou `null` si l'URL est refusée : segments `..`, antislash, octet nul,
 * extension non autorisée, ou sortie du dossier racine. `/` donne `index.html`.
 */
export function resolveStaticPath(
  root: string,
  urlPath: string,
): { file: string; type: string } | null {
  let decoded: string;
  try {
    decoded = decodeURIComponent(urlPath);
  } catch {
    return null;
  }
  if (decoded.includes('\0') || decoded.includes('\\')) return null;
  const relative = decoded === '/' ? '/index.html' : decoded;
  const segments = relative.split('/').filter((s) => s.length > 0);
  if (segments.some((s) => s === '..' || s === '.' || s.startsWith('.'))) return null;
  const last = segments[segments.length - 1] ?? '';
  const dot = last.lastIndexOf('.');
  const type = dot > 0 ? TYPES[last.slice(dot).toLowerCase()] : undefined;
  if (type === undefined) return null;
  const base = resolve(root);
  const file = resolve(join(base, ...segments));
  return file.startsWith(base + sep) ? { file, type } : null;
}

export async function readStatic(
  root: string,
  urlPath: string,
): Promise<{ body: Buffer; type: string } | null> {
  const found = resolveStaticPath(root, urlPath);
  if (!found) return null;
  try {
    return { body: await readFile(found.file), type: found.type };
  } catch {
    return null;
  }
}
