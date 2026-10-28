/**
 * Scénario de synchronisation : trois participants publient la même source à repères (voir
 * make-sync-media.ts), un egress par piste (6 fichiers) écrit sur le disque local pendant
 * `--seconds` secondes (1800 par défaut), puis analyse des repères dans les fichiers.
 *   node src/cli/run-sync.ts [--seconds 1800] [--participants 3]
 * Rapport : pocs/poc-03-server-recording/.local/results/<salle>/sync.json
 */
import { join } from 'node:path';
import { sleep, startPublisher } from '@podcast/poc-03-server-recording/stack.ts';
import {
  cleanup,
  createHarness,
  observe,
  saveReport,
  startTrackEgresses,
  stopActiveEgresses,
  waitForEgressEnd,
  waitForParticipants,
} from '@podcast/poc-03-server-recording/harness.ts';
import { localDir } from '@podcast/poc-03-server-recording/stack.ts';
import { readdir } from 'node:fs/promises';

const args = process.argv.slice(2);
const flag = (name: string, fallback: number): number => {
  const index = args.indexOf(name);
  return index === -1 ? fallback : Number(args[index + 1]);
};
const RECORD_SECONDS = flag('--seconds', 1800);
const PARTICIPANTS = flag('--participants', 3);
const SERVICES = ['publisher-s1', 'publisher-s2', 'publisher-s3'] as const;

const h = await createHarness('sync');
try {
  h.log(
    `salle ${h.room} : ${String(PARTICIPANTS)} publieurs, enregistrement de ${String(RECORD_SECONDS)} s`,
  );
  for (const service of SERVICES.slice(0, PARTICIPANTS)) {
    h.containers.push(await startPublisher(service, h.room));
    await sleep(300);
  }
  const participants = await waitForParticipants(h, { participants: PARTICIPANTS, tracksEach: 2 });
  h.log('participants connectés, pistes publiées');

  await startTrackEgresses(h, participants, '', 'local');
  await observe(h, RECORD_SECONDS, 60_000);

  await stopActiveEgresses(h);
  await waitForEgressEnd(h, 180_000);

  const dir = join(localDir, 'egress-out', h.room);
  const files = await readdir(dir);
  h.log(`${String(files.length)} fichiers dans ${dir}`);
  await saveReport(h, 'sync', {
    recordSeconds: RECORD_SECONDS,
    participants: PARTICIPANTS,
    files,
    dir,
  });
  console.log(
    `\nAnalyse : node src/cli/analyze-sync.ts --dir "${dir}" --out "${join(h.resultsDir, 'sync-analysis.json')}"`,
  );
} finally {
  await cleanup(h);
}
