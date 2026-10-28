/**
 * Crée `.local/.env` (ignoré par git) avec un mot de passe de base aléatoire. Si la pile LiveKit du POC 3
 * existe déjà, ses clés sont reprises pour émettre des jetons de salle en développement.
 */
import { randomBytes } from 'node:crypto';
import { existsSync } from 'node:fs';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const localDir = join(import.meta.dirname, '..', '..', '.local');
const envPath = join(localDir, '.env');
await mkdir(localDir, { recursive: true });

if (existsSync(envPath)) {
  console.log('Configuration locale déjà présente, rien à faire :', envPath);
} else {
  const password = randomBytes(24).toString('base64url');
  const port = 54329;
  const lines = [
    `POSTGRES_PASSWORD=${password}`,
    `POSTGRES_PORT=${String(port)}`,
    `DATABASE_URL=postgres://podcast:${password}@127.0.0.1:${String(port)}/podcast`,
    'ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000',
    'ALLOW_REGISTRATION=false',
    'LIVEKIT_URL=ws://localhost:7880',
  ];
  const poc3 = join(
    import.meta.dirname,
    '..',
    '..',
    '..',
    '..',
    'pocs',
    'poc-03-server-recording',
    '.local',
    '.env',
  );
  if (existsSync(poc3)) {
    for (const line of (await readFile(poc3, 'utf8')).split(/\r?\n/)) {
      if (/^LIVEKIT_API_(KEY|SECRET)=/.test(line)) lines.push(line);
    }
  }
  await writeFile(envPath, `${lines.join('\n')}\n`, { flag: 'wx' });
  console.log('Configuration locale créée (secrets aléatoires, ignorés par git) :', envPath);
}
