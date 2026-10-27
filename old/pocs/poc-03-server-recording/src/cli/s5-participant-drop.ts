/**
 * Scénario S5 : un participant se coupe (conteneur publieur supprimé), puis revient avec la
 * même identité. On observe ce que devient l'egress de ses pistes, et si les nouvelles pistes
 * doivent être enregistrées par un nouvel egress (rôle du Control plane).
 */
import { removeContainer, sleep, startPublisher } from '../lib/stack.ts';
import {
  cleanup,
  collectResults,
  createHarness,
  observe,
  printCollected,
  saveReport,
  startTrackEgresses,
  statusNames,
  stopActiveEgresses,
  waitForEgressEnd,
  waitForParticipants,
} from '../lib/harness.ts';

const h = await createHarness('s5');

try {
  const publisherA = await startPublisher('publisher-a', h.room);
  h.containers.push(publisherA, await startPublisher('publisher-b', h.room));
  const first = await waitForParticipants(h, { participants: 2, tracksEach: 2 });
  await startTrackEgresses(h, first);
  await observe(h, 20);

  h.log('>>> guest-a se coupe (conteneur supprimé)');
  await removeContainer(publisherA);
  await observe(h, 12);
  h.log(
    `statuts egress après la coupure : ${statusNames(await h.egress.listEgress({ roomName: h.room }))}`,
  );

  h.log('>>> guest-a revient avec la même identité');
  h.containers.push(await startPublisher('publisher-a', h.room));
  const back = await waitForParticipants(h, { participants: 2, tracksEach: 2 });
  const returning = back.filter((p) => p.identity === 'guest-a');
  const oldSids = new Set(
    first.filter((p) => p.identity === 'guest-a').flatMap((p) => p.tracks.map((t) => t.sid)),
  );
  const newSids = returning.flatMap((p) => p.tracks.map((t) => t.sid));
  h.log(
    `nouvelles pistes de guest-a : ${newSids.join(', ')} (identiques aux anciennes : ${String(newSids.some((s) => oldSids.has(s)))})`,
  );

  await startTrackEgresses(h, returning, '-retour');
  await observe(h, 20);
  await sleep(500);

  await stopActiveEgresses(h);
  await waitForEgressEnd(h);
  const collected = await collectResults(h, undefined);
  printCollected(collected);
  await saveReport(h, 's5', { ...collected, oldSids: [...oldSids], newSids });
  console.log(
    `\nS5 : ${String(collected.files.length)} fichier(s) de piste pour ${String(h.egressFiles.size)} egress démarrés. Rapport : ${h.resultsDir}`,
  );
} finally {
  await cleanup(h);
}
