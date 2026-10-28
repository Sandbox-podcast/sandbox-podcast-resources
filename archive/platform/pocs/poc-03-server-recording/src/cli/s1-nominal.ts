/**
 * Scénarios S1 et S2 : 2 participants (audio + vidéo 1080p30), un egress par piste pendant
 * RECORD_SECONDS, arrêt normal, vérification des fichiers, relevé du CPU et de la mémoire.
 * Rapport : .local/results/<salle>/s1.json
 */
import { startPublisher } from '../lib/stack.ts';
import {
  cleanup,
  collectResults,
  createHarness,
  observe,
  printCollected,
  printStats,
  saveReport,
  startTrackEgresses,
  stopActiveEgresses,
  waitForEgressEnd,
  waitForParticipants,
} from '../lib/harness.ts';

const RECORD_SECONDS = 60;
const h = await createHarness('s1');

try {
  h.log(`salle ${h.room} : démarrage des deux publieurs`);
  h.containers.push(
    await startPublisher('publisher-a', h.room),
    await startPublisher('publisher-b', h.room),
  );
  const participants = await waitForParticipants(h, { participants: 2, tracksEach: 2 });
  h.log('2 participants connectés, pistes publiées');

  await startTrackEgresses(h, participants);
  await observe(h, RECORD_SECONDS);

  await stopActiveEgresses(h);
  await waitForEgressEnd(h);

  const collected = await collectResults(h, RECORD_SECONDS);
  printCollected(collected);
  printStats(h);
  await saveReport(h, 's1', { recordSeconds: RECORD_SECONDS, ...collected });
  const ok = collected.files.filter((f) => f.issues.length === 0).length;
  console.log(
    `\nS1 : ${String(collected.files.length)}/${String(h.egressFiles.size)} fichiers de piste, ${String(ok)} conformes. Rapport : ${h.resultsDir}`,
  );
} finally {
  await cleanup(h);
}
