/**
 * Récupération des fichiers de travail d'Egress laissés par un crash.
 * Constaté (POC 3) : audio Ogg lisible tel quel, vidéo MP4 sans index à réparer.
 */
import { execFile } from 'node:child_process';
import { copyFile, mkdir, readdir, readFile, stat, writeFile } from 'node:fs/promises';
import { basename, extname, join } from 'node:path';
import { promisify } from 'node:util';
import { extractAnnexB } from './mp4-recovery.ts';
import { probeFile } from './stack.ts';

const run = promisify(execFile);

export type RecoveryMethod = 'copy' | 'repair-mp4' | 'remux-webm' | 'unreadable';

export interface RecoveredFile {
  egressId: string;
  source: string;
  output: string | undefined;
  method: RecoveryMethod;
  durationSec: number | undefined;
  note: string;
}

const MEDIA_EXTENSIONS = new Set(['.ogg', '.mp4', '.webm']);
const MIN_BYTES = 4096;

/**
 * Parcourt `<tmpDir>/<egressId>/<fichier>` et produit, dans `outDir`, des fichiers lisibles.
 * La cadence d'une vidéo réparée est supposée constante (`fps`).
 */
export async function recoverEgressTmp(
  tmpDir: string,
  outDir: string,
  fps = 30,
): Promise<RecoveredFile[]> {
  await mkdir(outDir, { recursive: true });
  const results: RecoveredFile[] = [];

  for (const entry of await readdir(tmpDir, { withFileTypes: true })) {
    if (!entry.isDirectory() || !entry.name.startsWith('EG_')) continue;
    const egressId = entry.name;
    for (const file of await readdir(join(tmpDir, egressId))) {
      const source = join(tmpDir, egressId, file);
      if (!MEDIA_EXTENSIONS.has(extname(file)) || (await stat(source)).size < MIN_BYTES) continue;
      results.push(await recoverOne(egressId, source, join(outDir, basename(file)), fps));
    }
  }
  return results;
}

async function recoverOne(
  egressId: string,
  source: string,
  output: string,
  fps: number,
): Promise<RecoveredFile> {
  const base = { egressId, source };
  const extension = extname(source);

  // 1. Déjà lisible : on copie.
  try {
    const summary = await probeFile(source);
    if (extension !== '.webm' || summary.durationSec !== undefined) {
      await copyFile(source, output);
      return {
        ...base,
        output,
        method: 'copy',
        durationSec: summary.durationSec,
        note: 'lisible tel quel',
      };
    }
  } catch {
    // Illisible : on tente une réparation selon le conteneur.
  }

  try {
    if (extension === '.mp4') {
      const recovered = extractAnnexB(new Uint8Array(await readFile(source)));
      if (recovered.nalCount === 0) throw new Error('aucun NAL dans le mdat');
      const raw = `${output}.h264`;
      await writeFile(raw, recovered.annexB);
      await run('ffmpeg', [
        '-y',
        '-loglevel',
        'error',
        '-f',
        'h264',
        '-framerate',
        String(fps),
        '-i',
        raw,
        '-c',
        'copy',
        output,
      ]);
      const summary = await probeFile(output);
      return {
        ...base,
        output,
        method: 'repair-mp4',
        durationSec: summary.durationSec,
        note: `${String(recovered.nalCount)} NAL récupérés, cadence supposée constante à ${String(fps)} images/s`,
      };
    }
    if (extension === '.webm') {
      await run('ffmpeg', ['-y', '-loglevel', 'error', '-i', source, '-c', 'copy', output]);
      const summary = await probeFile(output);
      return {
        ...base,
        output,
        method: 'remux-webm',
        durationSec: summary.durationSec,
        note: 'remux pour reconstruire la durée',
      };
    }
  } catch (error) {
    return {
      ...base,
      output: undefined,
      method: 'unreadable',
      durationSec: undefined,
      note: error instanceof Error ? (error.message.split('\n')[0] ?? 'erreur') : 'erreur',
    };
  }
  return {
    ...base,
    output: undefined,
    method: 'unreadable',
    durationSec: undefined,
    note: 'format non pris en charge',
  };
}
