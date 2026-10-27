import { loadConfig } from '../config.ts';
import { createPool } from '../db/db.ts';
import { migrate } from '../db/migrate.ts';

const pool = createPool(loadConfig().DATABASE_URL, 2);
try {
  const report = await migrate(pool);
  console.log('Appliquées :', report.applied.join(', ') || '(aucune)');
  console.log('Déjà appliquées :', report.alreadyApplied.join(', ') || '(aucune)');
} finally {
  await pool.end();
}
