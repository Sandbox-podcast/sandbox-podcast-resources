import { existsSync } from 'node:fs';
import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { generateConfig, renderEnvFile, renderS3Config } from '../lib/local-config.ts';

const localDir = join(import.meta.dirname, '..', '..', '.local');
const envPath = join(localDir, '.env');
const s3Path = join(localDir, 's3.json');

await mkdir(localDir, { recursive: true });

if (existsSync(envPath) && existsSync(s3Path)) {
  console.log('Configuration locale déjà présente, rien à faire :', localDir);
} else {
  const config = generateConfig();
  await writeFile(envPath, renderEnvFile(config), { flag: 'wx' });
  await writeFile(s3Path, renderS3Config(config), { flag: 'wx' });
  console.log('Configuration locale créée (secrets aléatoires, ignorés par git) :', localDir);
}
