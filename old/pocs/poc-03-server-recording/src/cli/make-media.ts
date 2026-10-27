import { execFile } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { promisify } from 'node:util';
import { mediaJobs } from '../lib/media-commands.ts';

const run = promisify(execFile);
const outDir = join(import.meta.dirname, '..', '..', '.local', 'media');
const durationSec = 180;

await mkdir(outDir, { recursive: true });

for (const job of mediaJobs(durationSec)) {
  console.log(`ffmpeg → ${job.output}`);
  await run('ffmpeg', ['-y', '-loglevel', 'error', ...job.args], { cwd: outDir });
}

console.log(`Médias de test (${String(durationSec)} s) créés dans`, outDir);
