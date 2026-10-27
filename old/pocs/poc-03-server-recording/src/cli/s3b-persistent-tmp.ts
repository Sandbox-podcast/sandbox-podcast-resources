/**
 * Scénario S3b : crash d'Egress avec un dossier de travail persistant sur l'hôte.
 * 1. Enregistrement de 4 pistes, puis kill d'Egress.
 * 2. On regarde si le conteneur redémarre seul (politique `unless-stopped`) et si Egress
 *    efface alors le dossier de travail avant qu'on ait pu récupérer les fichiers.
 * 3. On récupère ce qui reste, on l'envoie dans le stockage sous `<salle>/recovered/`,
 *    et on vérifie les fichiers.
 * Usage : node src/cli/s3b-persistent-tmp.ts [auto-restart|no-restart]
 */
import { readdir, readFile } from 'node:fs/promises';
import { basename, join } from 'node:path';
import { recoverEgressTmp } from '../lib/recovery.ts';
import { compose, localDir, putObject, sleep, startPublisher } from '../lib/stack.ts';
import {
  cleanup,
  collectResults,
  createHarness,
  observe,
  printCollected,
  saveReport,
  startTrackEgresses,
  waitForParticipants,
} from '../lib/harness.ts';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const run = promisify(execFile);
const mode = process.argv[2] === 'no-restart' ? 'no-restart' : 'auto-restart';
const tmpDir = join(localDir, 'egress-tmp');
const h = await createHarness(`s3b-${mode}`);

async function listTmp(): Promise<string[]> {
  const found: string[] = [];
  for (const dir of await readdir(tmpDir, { withFileTypes: true }).catch(() => [])) {
    if (!dir.isDirectory()) continue;
    for (const file of await readdir(join(tmpDir, dir.name))) found.push(`${dir.name}/${file}`);
  }
  return found;
}

try {
  // La politique de redémarrage du conteneur est celle du scénario.
  await run('docker', [
    'update',
    '--restart',
    mode === 'no-restart' ? 'no' : 'unless-stopped',
    'poc03-egress-1',
  ]);
  h.log(`politique de redémarrage d'Egress : ${mode === 'no-restart' ? 'no' : 'unless-stopped'}`);

  h.containers.push(
    await startPublisher('publisher-a', h.room),
    await startPublisher('publisher-b', h.room),
  );
  const participants = await waitForParticipants(h, { participants: 2, tracksEach: 2 });
  await startTrackEgresses(h, participants);
  await observe(h, 25);
  h.log(`fichiers de travail pendant l'enregistrement : ${(await listTmp()).join(', ')}`);

  h.log('>>> KILL (SIGKILL) du conteneur egress');
  await compose(['kill', 'egress']);
  await sleep(1500);
  const afterKill = await listTmp();
  h.log(`juste après le kill : ${String(afterKill.length)} fichier(s) de travail sur l'hôte`);

  await sleep(15_000);
  const state = (
    await run('docker', [
      'inspect',
      '-f',
      '{{.State.Status}} restarts={{.RestartCount}}',
      'poc03-egress-1',
    ])
  ).stdout.trim();
  const later = await listTmp();
  h.log(
    `15 s plus tard : conteneur ${state}, ${String(later.length)} fichier(s) de travail sur l'hôte`,
  );

  // Récupération avec ce qui reste.
  const outDir = join(h.resultsDir, 'recovered');
  const recovered = await recoverEgressTmp(tmpDir, outDir);
  for (const item of recovered) {
    h.log(
      `récupération : ${basename(item.source)} → ${item.method}, ${String(item.durationSec ?? '?')} s (${item.note})`,
    );
    if (item.output) {
      await putObject(
        h.s3,
        h.config.s3Bucket,
        `${h.room}/recovered/${basename(item.output)}`,
        new Uint8Array(await readFile(item.output)),
      );
    }
  }

  await compose(['start', 'egress']);
  const final = await collectResults(h, undefined);
  printCollected(final);
  await saveReport(h, `s3b-${mode}`, { afterKill, later, state, recovered, final });
  console.log(
    `\nS3b (${mode}) : ${String(afterKill.length)} fichier(s) de travail juste après le kill, ${String(later.length)} après 15 s, ${String(recovered.filter((r) => r.output).length)} récupéré(s) sur ${String(h.egressFiles.size)} pistes. Rapport : ${h.resultsDir}`,
  );
} finally {
  await run('docker', ['update', '--restart', 'unless-stopped', 'poc03-egress-1']).catch(
    () => undefined,
  );
  await compose(['start', 'egress']).catch(() => undefined);
  await cleanup(h);
}
