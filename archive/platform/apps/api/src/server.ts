import { buildApp } from './app.ts';
import { loadConfig } from './config.ts';
import { createPool } from './db/db.ts';
import { migrate } from './db/migrate.ts';

const config = loadConfig();
const pool = createPool(config.DATABASE_URL);
const report = await migrate(pool);
if (report.applied.length > 0) console.log('Migrations appliquées :', report.applied.join(', '));

const app = buildApp({ config, pool });
await app.listen({ host: '127.0.0.1', port: config.PORT });
console.log(`API à l'écoute sur http://127.0.0.1:${String(config.PORT)}`);

const stop = async (): Promise<void> => {
  await app.close();
  await pool.end();
};
process.on('SIGINT', () => void stop());
process.on('SIGTERM', () => void stop());
