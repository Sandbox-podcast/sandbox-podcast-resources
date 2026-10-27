/**
 * Scénario S4 : redémarrage du SFU (LiveKit) au milieu d'un enregistrement.
 * On observe la fin des egress et ce qui reste dans le stockage.
 */
import { compose, startPublisher } from '../lib/stack.ts';
import {
  cleanup,
  collectResults,
  createHarness,
  observe,
  printCollected,
  saveReport,
  startTrackEgresses,
  stopActiveEgresses,
  statusNames,
  waitForEgressEnd,
  waitForParticipants,
} from '../lib/harness.ts';

const h = await createHarness('s4');

try {
  h.containers.push(
    await startPublisher('publisher-a', h.room),
    await startPublisher('publisher-b', h.room),
  );
  const participants = await waitForParticipants(h, { participants: 2, tracksEach: 2 });
  await startTrackEgresses(h, participants);
  await observe(h, 25);

  h.log('>>> redémarrage du conteneur livekit');
  await compose(['restart', 'livekit']);
  await observe(h, 25);

  // Après un redémarrage, la salle a disparu : on demande l'état directement aux egress.
  const infos = await h.egress.listEgress({});
  const ours = infos.filter((i) => h.egressFiles.has(i.egressId));
  h.log(`statuts de nos egress après redémarrage : ${statusNames(ours)}`);
  // Constaté le 2026-10-05 : après un redémarrage du SFU, les egress vidéo se terminent et
  // envoient leur fichier, mais les egress audio restent « ACTIVE » sans rien envoyer
  // tant qu'on ne les arrête pas. On les arrête donc explicitement, comme le ferait le Control plane.
  await waitForEgressEnd(h, 20_000);
  await stopActiveEgresses(h);
  await waitForEgressEnd(h, 60_000);

  const collected = await collectResults(h, undefined);
  printCollected(collected);
  await saveReport(h, 's4', { ...collected, egressStatuses: statusNames(ours) });
  console.log(
    `\nS4 : ${String(collected.files.length)} fichier(s) de piste sur ${String(h.egressFiles.size)} pistes. Rapport : ${h.resultsDir}`,
  );
} finally {
  await cleanup(h);
}
