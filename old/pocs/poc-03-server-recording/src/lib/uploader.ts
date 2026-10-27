/**
 * Envoyeur des fichiers d'Egress vers le stockage objet : checksum SHA-256, vérification
 * par relecture, nouvelles tentatives. Le fichier local n'est supprimé qu'après vérification.
 */
import { createHash } from 'node:crypto';
import { mkdir, readFile, readdir, rename, stat } from 'node:fs/promises';
import { dirname, join, relative } from 'node:path';
import type { S3Client } from '@aws-sdk/client-s3';
import { downloadObject, putObject, sleep } from './stack.ts';

export type UploadOutcome = 'verified' | 'failed';

export interface UploadResult {
  file: string;
  key: string;
  sizeBytes: number;
  sha256: string;
  attempts: number;
  outcome: UploadOutcome;
  error: string | undefined;
}

const sha256 = (bytes: Uint8Array): string => createHash('sha256').update(bytes).digest('hex');

/** Liste récursivement les fichiers d'un dossier, chemins relatifs. */
async function listFiles(dir: string): Promise<string[]> {
  const entries = await readdir(dir, { recursive: true, withFileTypes: true }).catch(() => []);
  return entries.filter((e) => e.isFile()).map((e) => relative(dir, join(e.parentPath, e.name)));
}

export interface UploadOptions {
  s3: S3Client;
  bucket: string;
  /** Dossier local qui contient `<salle>/<fichier>`. */
  localDir: string;
  /** Préfixe des clés dans le stockage, par exemple le nom de la salle. */
  keyPrefix: string;
  /** Dossier où déplacer les fichiers une fois vérifiés. */
  doneDir: string;
  maxAttempts?: number;
  retryDelayMs?: number;
}

/**
 * Envoie tous les fichiers présents dans `localDir`. Chaque fichier est relu depuis le
 * stockage et comparé par SHA-256 avant d'être déplacé dans `doneDir`.
 */
export async function uploadPending(options: UploadOptions): Promise<UploadResult[]> {
  const { s3, bucket, localDir, doneDir, keyPrefix } = options;
  const maxAttempts = options.maxAttempts ?? 5;
  const retryDelayMs = options.retryDelayMs ?? 2000;
  const results: UploadResult[] = [];

  for (const file of await listFiles(localDir)) {
    const path = join(localDir, file);
    const key = `${keyPrefix}/${file.split('\\').join('/')}`;
    const bytes = new Uint8Array(await readFile(path));
    const digest = sha256(bytes);
    let attempts = 0;
    let error: string | undefined;
    let outcome: UploadOutcome = 'failed';

    while (attempts < maxAttempts && outcome === 'failed') {
      attempts += 1;
      try {
        await putObject(s3, bucket, key, bytes);
        const stored = await downloadObject(s3, bucket, key);
        if (stored.length !== bytes.length || sha256(stored) !== digest) {
          throw new Error('checksum différent après envoi');
        }
        outcome = 'verified';
        error = undefined;
      } catch (e) {
        error = e instanceof Error ? e.message.split('\n')[0] : 'erreur';
        if (attempts < maxAttempts) await sleep(retryDelayMs * attempts);
      }
    }

    if (outcome === 'verified') {
      const target = join(doneDir, file);
      await mkdir(dirname(target), { recursive: true });
      await rename(path, target);
    }
    results.push({
      file,
      key,
      sizeBytes: (await stat(outcome === 'verified' ? join(doneDir, file) : path)).size,
      sha256: digest,
      attempts,
      outcome,
      error,
    });
  }
  return results;
}
