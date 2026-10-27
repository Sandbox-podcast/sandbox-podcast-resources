/**
 * Scénario S3c : le stockage objet est indisponible quand on arrête l'enregistrement.
 * On observe le statut des egress, ce qui reste dans le dossier de travail, et si une
 * récupération puis un envoi manuel après le retour du stockage rendent les fichiers.
 */
import { execFile } from 'node:child_process';
import { readdir, readFile } from 'node:fs/promises';
import { basename, join } from 'node:path';
import { promisify } from 'node:util';
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
  stopActiveEgresses,
  waitForEgressEnd,
  waitForParticipants,
} from '../lib/harness.ts';

const run = promisify(execFile);
const tmpDir = join(localDir, 'egress-tmp');
const h = await createHarness('s3c');

async function listTmp(): Promise<string[]> {
  const found: string[] = [];
  for (const dir of await readdir(tmpDir, { withFileTypes: true }).catch(() => [])) {
    if (!dir.isDirectory()) continue;
    for (const file of await readdir(join(tmpDir, dir.name))) {
      if (file.endsWith('.mp4') || file.endsWith('.ogg')) found.push(`${dir.name}/${file}`);
    }
  }
  return found;
}

try {
  h.containers.push(
    await startPublisher('publisher-a', h.room),
    await startPublisher('publisher-b', h.room),
  );
  const participants = await waitForParticipants(h, { participants: 2, tracksEach: 2 });
  await startTrackEgresses(h, participants);
  await observe(h, 20);

  h.log('>>> arrêt du stockage (conteneur s3)');
  await run('docker', ['stop', 'poc03-s3-1']);

  await stopActiveEgresses(h);
  const infos = await waitForEgressEnd(h, 60_000);
  for (const info of infos) h.log(`egress ${info.egressId} : ${info.error || 'sans erreur'}`);
  const kept = await listTmp();
  h.log(`fichiers de travail conservés après l'échec d'envoi : ${String(kept.length)}`);

  h.log('>>> retour du stockage');
  await compose(['start', 's3']);
  for (let i = 0; i < 40; i++) {
    const ready = await fetch('http://localhost:8333/').then(
      () => true,
      () => false,
    );
    if (ready) break;
    await sleep(2000);
  }
  const outDir = join(h.resultsDir, 'recovered');
  const recovered = await recoverEgressTmp(tmpDir, outDir);
  for (const item of recovered) {
    h.log(
      `récupération : ${basename(item.source)} → ${item.method}, ${String(item.durationSec ?? '?')} s`,
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
  const final = await collectResults(h, undefined);
  printCollected(final);
  await saveReport(h, 's3c', {
    infos: infos.map((i) => ({ id: i.egressId, error: i.error, status: i.status })),
    kept,
    recovered,
    final,
  });
  console.log(
    `\nS3c : ${String(kept.length)} fichier(s) conservés après l'échec, ${String(recovered.filter((r) => r.output).length)} récupéré(s), ${String(final.files.length)} fichier(s) dans le stockage au final. Rapport : ${h.resultsDir}`,
  );
} finally {
  await compose(['start', 's3']).catch(() => undefined);
  await cleanup(h);
}
