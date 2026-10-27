import { createHash } from 'node:crypto';
import { readdir, readFile } from 'node:fs/promises';
import { join } from 'node:path';
import type { Pool } from 'pg';

export const MIGRATIONS_DIR = join(import.meta.dirname, 'migrations');

/** Une migration déjà appliquée a changé de contenu : on refuse de continuer. */
export class MigrationTamperedError extends Error {}

const checksum = (sql: string): string => createHash('sha256').update(sql).digest('hex');

/** Verrou consultatif : deux instances qui démarrent en même temps ne migrent pas en parallèle. */
const LOCK_KEY = 7_410_001;

export interface MigrationReport {
  applied: string[];
  alreadyApplied: string[];
}

/**
 * Applique les fichiers `NNNN_nom.sql` dans l'ordre, chacun dans une transaction. L'empreinte de chaque
 * fichier est conservée : si un fichier appliqué change, la fonction lève `MigrationTamperedError`
 * avant d'appliquer quoi que ce soit.
 */
export async function migrate(pool: Pool, dir: string = MIGRATIONS_DIR): Promise<MigrationReport> {
  const client = await pool.connect();
  try {
    await client.query('select pg_advisory_lock($1)', [LOCK_KEY]);
    await client.query(`create table if not exists schema_migrations (
      version text primary key,
      checksum text not null,
      applied_at timestamptz not null default now()
    )`);
    const files = (await readdir(dir)).filter((f) => /^\d{4}_.+\.sql$/.test(f)).sort();
    const { rows } = await client.query<{ version: string; checksum: string }>(
      'select version, checksum from schema_migrations',
    );
    const known = new Map(rows.map((r) => [r.version, r.checksum]));

    const contents = new Map<string, string>();
    for (const file of files) contents.set(file, await readFile(join(dir, file), 'utf8'));
    for (const [file, sql] of contents) {
      const previous = known.get(file);
      if (previous !== undefined && previous !== checksum(sql))
        throw new MigrationTamperedError(
          `La migration ${file} a été modifiée après son application`,
        );
    }

    const report: MigrationReport = { applied: [], alreadyApplied: [] };
    for (const [file, sql] of contents) {
      if (known.has(file)) {
        report.alreadyApplied.push(file);
        continue;
      }
      try {
        await client.query('begin');
        await client.query(sql);
        await client.query('insert into schema_migrations (version, checksum) values ($1, $2)', [
          file,
          checksum(sql),
        ]);
        await client.query('commit');
      } catch (error) {
        await client.query('rollback');
        throw error;
      }
      report.applied.push(file);
    }
    return report;
  } finally {
    await client.query('select pg_advisory_unlock($1)', [LOCK_KEY]).catch(() => undefined);
    client.release();
  }
}
