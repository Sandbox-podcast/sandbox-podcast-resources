/**
 * Scénario S3e : crash d'Egress pendant un enregistrement, géré par le superviseur seul.
 * Attendu : détection du worker arrêté, récupération des fichiers de travail, envoi vérifié,
 * redémarrage du worker, nouveaux egress pour les pistes encore publiées, puis arrêt normal.
 */
import { basename, join } from 'node:path';
import { Supervisor } from '../lib/supervisor.ts';
import { compose, sleep, startPublisher } from '../lib/stack.ts';
import {
  cleanup,
  collectResults,
  createHarness,
  printCollected,
  saveReport,
  waitForParticipants,
} from '../lib/harness.ts';

const h = await createHarness('s3e');
const supervisor = new Supervisor(h);

try {
  await compose(['up', '-d', 'egress']);
  h.containers.push(
    await startPublisher('publisher-a', h.room),
    await startPublisher('publisher-b', h.room),
  );
  await waitForParticipants(h, { participants: 2, tracksEach: 2 });
  supervisor.recordingActive = true;
  const loop = supervisor.loop(2000);
  h.log('enregistrement demandé, superviseur en marche');

  await sleep(25_000);
  const crashAt = Date.now();
  h.log('>>> KILL du conteneur egress');
  await compose(['kill', 'egress']);

  await sleep(45_000);
  h.log('enregistrement arrêté par l’utilisateur');
  supervisor.recordingActive = false;

  const deadline = Date.now() + 120_000;
  while (Date.now() < deadline && !supervisor.allSafe()) await sleep(2000);
  h.log(`tous les segments vérifiés : ${String(supervisor.allSafe())}`);
  supervisor.stop();
  await loop;

  const final = await collectResults(h, undefined);
  printCollected(final);
  await saveReport(h, 's3e', {
    crashAtMs: crashAt,
    segments: [...supervisor.egressSegments].map(([id, k]) => ({ id, ...k })),
    supervisorLog: supervisor.log,
    final,
  });
  const names = final.files.map((f) => basename(f.key));
  console.log(
    `\nS3e : ${String(supervisor.egressSegments.size)} segment(s) d'egress, ${String(final.files.length)} fichier(s) dans le stockage, tous vérifiés : ${String(supervisor.allSafe())}. Rapport : ${join(h.resultsDir)}\n${names.join('\n')}`,
  );
} finally {
  supervisor.stop();
  await compose(['start', 'egress']).catch(() => undefined);
  await cleanup(h);
}
