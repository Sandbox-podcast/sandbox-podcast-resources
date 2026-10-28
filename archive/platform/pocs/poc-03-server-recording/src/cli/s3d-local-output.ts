/**
 * Scénario S3d : Egress écrit sur un disque local persistant (/out) et notre envoyeur pousse
 * les fichiers vers le stockage avec vérification. On arrête le stockage avant l'arrêt de
 * l'enregistrement, puis on le rallume : rien ne doit être perdu.
 */
import { execFile } from 'node:child_process';
import { join } from 'node:path';
import { promisify } from 'node:util';
import { uploadPending } from '../lib/uploader.ts';
import { compose, localDir, sleep, startPublisher } from '../lib/stack.ts';
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
const outDir = join(localDir, 'egress-out');
const h = await createHarness('s3d');

try {
  h.containers.push(
    await startPublisher('publisher-a', h.room),
    await startPublisher('publisher-b', h.room),
  );
  const participants = await waitForParticipants(h, { participants: 2, tracksEach: 2 });
  await startTrackEgresses(h, participants, '', 'local');
  await observe(h, 20);

  h.log('>>> arrêt du stockage (conteneur s3)');
  await run('docker', ['stop', 'poc03-s3-1']);
  await stopActiveEgresses(h);
  const infos = await waitForEgressEnd(h, 60_000);
  for (const info of infos) h.log(`egress ${info.egressId} : ${info.error || 'sans erreur'}`);

  h.log('>>> envoi avec le stockage éteint (2 tentatives)');
  const whileDown = await uploadPending({
    s3: h.s3,
    bucket: h.config.s3Bucket,
    localDir: join(outDir, h.room),
    keyPrefix: h.room,
    doneDir: join(outDir, '_envoyes', h.room),
    maxAttempts: 2,
    retryDelayMs: 500,
  });
  h.log(
    `envoi stockage éteint : ${whileDown.map((r) => r.outcome).join(',') || '(aucun fichier)'}`,
  );

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
  await sleep(3000);
  const afterReturn = await uploadPending({
    s3: h.s3,
    bucket: h.config.s3Bucket,
    localDir: join(outDir, h.room),
    keyPrefix: h.room,
    doneDir: join(outDir, '_envoyes', h.room),
  });
  for (const r of afterReturn)
    h.log(`${r.outcome} (${String(r.attempts)} tentative(s)) : ${r.file}`);

  const final = await collectResults(h, 20, 8);
  printCollected(final);
  await saveReport(h, 's3d', {
    infos: infos.map((i) => ({ id: i.egressId, error: i.error, status: i.status })),
    whileDown,
    afterReturn,
    final,
  });
  const ok = final.files.filter((f) => f.issues.length === 0).length;
  console.log(
    `\nS3d : ${String(whileDown.length)} fichier(s) vus stockage éteint (${String(whileDown.filter((r) => r.outcome === 'verified').length)} envoyés), ${String(afterReturn.filter((r) => r.outcome === 'verified').length)} envoyés et vérifiés après le retour, ${String(ok)}/${String(h.egressFiles.size)} conformes dans le stockage. Rapport : ${h.resultsDir}`,
  );
} finally {
  await compose(['start', 's3']).catch(() => undefined);
  await cleanup(h);
}
