/**
 * Scénario S3 : arrêt brutal (kill, par défaut) ou propre (stop) du conteneur Egress
 * au milieu d'un enregistrement. On observe ce qui reste dans le stockage et l'état
 * des egress vu par LiveKit, avant et après le redémarrage d'Egress.
 * Usage : node src/cli/s3-egress-crash.ts [kill|stop]
 */
import { readdir, stat } from 'node:fs/promises';
import { join } from 'node:path';
import { compose, copyFromContainer, probeFile, startPublisher } from '../lib/stack.ts';
import {
  cleanup,
  collectResults,
  createHarness,
  observe,
  printCollected,
  saveReport,
  startTrackEgresses,
  statusNames,
  waitForParticipants,
} from '../lib/harness.ts';

const mode = process.argv[2] === 'stop' ? 'stop' : 'kill';
const h = await createHarness(`s3-${mode}`);

try {
  h.containers.push(
    await startPublisher('publisher-a', h.room),
    await startPublisher('publisher-b', h.room),
  );
  const participants = await waitForParticipants(h, { participants: 2, tracksEach: 2 });
  await startTrackEgresses(h, participants);
  await observe(h, 25);

  h.log(`>>> ${mode === 'kill' ? 'KILL (SIGKILL)' : 'STOP (SIGTERM)'} du conteneur egress`);
  await compose([mode, 'egress']);
  await observe(h, 20);

  const afterCrash = await collectResults(h, undefined);
  h.log(`après ${mode} : ${String(afterCrash.files.length)} fichier(s) de piste dans le stockage`);

  // Les fichiers de travail d'Egress survivent-ils dans le conteneur arrêté ?
  const leftoverDir = join(h.resultsDir, 'egress-tmp-after-crash');
  await copyFromContainer('poc03-egress-1', '/home/egress/tmp', leftoverDir);
  const leftovers: { file: string; size: number; readable: boolean; detail: string }[] = [];
  for (const entry of await readdir(leftoverDir, { recursive: true })) {
    const path = join(leftoverDir, entry);
    const info = await stat(path);
    if (!info.isFile() || info.size < 100_000) continue;
    try {
      const summary = await probeFile(path);
      leftovers.push({
        file: entry,
        size: info.size,
        readable: true,
        detail: `${summary.kind} ${summary.codec ?? '?'} ${String(summary.durationSec ?? '?')} s`,
      });
    } catch (error) {
      leftovers.push({
        file: entry,
        size: info.size,
        readable: false,
        detail:
          error instanceof Error ? (error.message.split('\n')[1] ?? 'illisible') : 'illisible',
      });
    }
  }
  h.log(`fichiers de travail restants dans le conteneur arrêté : ${String(leftovers.length)}`);
  for (const leftover of leftovers) {
    h.log(
      `  ${leftover.file} (${String(leftover.size)} octets) lisible=${String(leftover.readable)} ${leftover.detail}`,
    );
  }

  h.log('>>> redémarrage du conteneur egress');
  await compose(['start', 'egress']);
  await observe(h, 20);
  h.log(
    `statuts finaux vus par LiveKit : ${statusNames(await h.egress.listEgress({ roomName: h.room }))}`,
  );

  const final = await collectResults(h, undefined);
  printCollected(final);
  await saveReport(h, `s3-${mode}`, { afterCrash, final, leftovers });
  console.log(
    `\nS3 (${mode}) : ${String(afterCrash.files.length)} fichier(s) juste après, ${String(final.files.length)} après redémarrage, sur ${String(h.egressFiles.size)} pistes. Rapport : ${h.resultsDir}`,
  );
} finally {
  await compose(['start', 'egress']).catch(() => undefined);
  await cleanup(h);
}
