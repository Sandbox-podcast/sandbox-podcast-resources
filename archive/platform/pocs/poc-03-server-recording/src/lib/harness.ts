/**
 * Briques communes aux scénarios du POC 3 : salle de test, publieurs, un egress par piste,
 * observation du stockage, collecte et vérification des fichiers.
 */
import { mkdir, writeFile } from 'node:fs/promises';
import { basename, join } from 'node:path';
import type { S3Client } from '@aws-sdk/client-s3';
import {
  DirectFileOutput,
  EgressStatus,
  TrackType,
  type EgressClient,
  type EgressInfo,
  type ParticipantInfo,
  type RoomServiceClient,
} from 'livekit-server-sdk';
import { checkAgainst, type MediaSummary } from './analyze.ts';
import { summarizeStats, type ContainerStats } from './docker-stats.ts';
import type { LocalConfig } from './local-config.ts';
import {
  createClients,
  downloadObject,
  ensureBucket,
  jsonSafe,
  listObjects,
  loadConfig,
  localDir,
  probeFile,
  removeContainer,
  sampleStats,
  sleep,
  trackFileOutput,
} from './stack.ts';

export interface Harness {
  room: string;
  config: LocalConfig;
  rooms: RoomServiceClient;
  egress: EgressClient;
  s3: S3Client;
  resultsDir: string;
  timeline: { tSec: number; event: string }[];
  log: (event: string) => void;
  containers: string[];
  /** egressId → chemin du fichier demandé dans le stockage. */
  egressFiles: Map<string, string>;
  stats: ContainerStats[];
}

export async function createHarness(name: string): Promise<Harness> {
  const room = `${name}-${String(Date.now())}`;
  const config = await loadConfig();
  const { rooms, egress, s3 } = createClients(config);
  await ensureBucket(s3, config.s3Bucket);
  const resultsDir = join(localDir, 'results', room);
  await mkdir(resultsDir, { recursive: true });

  const startedAtMs = Date.now();
  const timeline: Harness['timeline'] = [];
  const log = (event: string): void => {
    const tSec = Number(((Date.now() - startedAtMs) / 1000).toFixed(1));
    timeline.push({ tSec, event });
    console.log(`[t=${String(tSec).padStart(5)} s] ${event}`);
  };
  return {
    room,
    config,
    rooms,
    egress,
    s3,
    resultsDir,
    timeline,
    log,
    containers: [],
    egressFiles: new Map(),
    stats: [],
  };
}

export async function cleanup(h: Harness): Promise<void> {
  for (const name of h.containers) await removeContainer(name).catch(() => undefined);
  await h.rooms.deleteRoom(h.room).catch(() => undefined);
}

export async function waitForParticipants(
  h: Harness,
  expected: { participants: number; tracksEach: number },
  timeoutMs = 90_000,
): Promise<ParticipantInfo[]> {
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    // Chaque egress rejoint la salle comme participant caché (type EGRESS, identité « EG_… »,
    // constaté le 2026-10-05) : on ne compte que les participants visibles.
    const participants = (await h.rooms.listParticipants(h.room).catch(() => [])).filter(
      (p) => p.permission?.hidden !== true,
    );
    const ready =
      participants.length === expected.participants &&
      participants.every((p) => p.tracks.length === expected.tracksEach);
    if (ready) return participants;
    if (Date.now() > deadline) {
      throw new Error(
        `Délai dépassé : ${String(participants.length)} participant(s) dans la salle ${h.room}`,
      );
    }
    await sleep(500);
  }
}

/** Démarre un egress pour chaque piste des participants donnés. `suffix` distingue les reprises. */
export async function startTrackEgresses(
  h: Harness,
  participants: readonly ParticipantInfo[],
  suffix = '',
  destination: 's3' | 'local' = 's3',
): Promise<void> {
  for (const participant of participants) {
    for (const track of participant.tracks) {
      const kind = track.type === TrackType.VIDEO ? 'video' : 'audio';
      const filepath = `${h.room}/${participant.identity}${suffix}-${kind}-${track.sid}`;
      // « local » : Egress écrit dans /out (dossier monté sur l'hôte), notre envoyeur fait le reste.
      const output =
        destination === 'local'
          ? new DirectFileOutput({ filepath: `/out/${filepath}` })
          : trackFileOutput(h.config, filepath);
      const info = await h.egress.startTrackEgress(h.room, output, track.sid);
      h.egressFiles.set(info.egressId, filepath);
      h.log(
        `egress ${info.egressId} démarré : ${participant.identity}/${kind} sid=${track.sid} (${EgressStatus[info.status]})`,
      );
    }
  }
}

const TERMINAL = new Set<EgressStatus>([
  EgressStatus.EGRESS_COMPLETE,
  EgressStatus.EGRESS_FAILED,
  EgressStatus.EGRESS_ABORTED,
  EgressStatus.EGRESS_LIMIT_REACHED,
]);

export const statusNames = (infos: readonly EgressInfo[]): string =>
  infos.map((i) => EgressStatus[i.status]).join(',');

/**
 * Observe pendant `seconds` : apparition des objets dans le stockage, changements de statuts
 * des egress, et relevé périodique du CPU et de la mémoire des conteneurs.
 */
export async function observe(h: Harness, seconds: number, statsEveryMs = 10_000): Promise<void> {
  const seen = new Map<string, number>();
  const until = Date.now() + seconds * 1000;
  let lastStatuses = '';
  let lastStatsAt = 0;
  while (Date.now() < until) {
    await sleep(2000);
    for (const object of await listObjects(h.s3, h.config.s3Bucket, `${h.room}/`)) {
      if (!seen.has(object.key)) {
        h.log(
          `objet visible dans le stockage : ${basename(object.key)} (${String(object.size)} octets)`,
        );
      }
      seen.set(object.key, object.size);
    }
    const statuses = statusNames(await h.egress.listEgress({ roomName: h.room }));
    if (statuses !== lastStatuses) {
      h.log(`statuts egress : ${statuses || '(aucun)'}`);
      lastStatuses = statuses;
    }
    if (Date.now() - lastStatsAt >= statsEveryMs) {
      h.stats.push(...(await sampleStats()));
      lastStatsAt = Date.now();
    }
  }
}

export async function stopActiveEgresses(h: Harness): Promise<void> {
  const active = await h.egress.listEgress({ roomName: h.room, active: true });
  h.log(`arrêt de ${String(active.length)} egress actifs`);
  for (const info of active) await h.egress.stopEgress(info.egressId);
}

export async function waitForEgressEnd(h: Harness, timeoutMs = 120_000): Promise<EgressInfo[]> {
  const deadline = Date.now() + timeoutMs;
  let infos = await h.egress.listEgress({ roomName: h.room });
  while (Date.now() < deadline && infos.some((i) => !TERMINAL.has(i.status))) {
    await sleep(1000);
    infos = await h.egress.listEgress({ roomName: h.room });
  }
  h.log(`egress dans leur état final : ${statusNames(infos)}`);
  await writeFile(join(h.resultsDir, 'egress-info.json'), jsonSafe(infos));
  return infos;
}

export interface FileReport {
  key: string;
  size: number;
  lastModified: string | undefined;
  summary: MediaSummary | undefined;
  probeError: string | undefined;
  issues: string[];
}

export interface Collected {
  files: FileReport[];
  manifests: { file: string; startedAtNs: number; endedAtNs: number }[];
}

/** Télécharge ce qui est dans le stockage pour la salle, analyse chaque fichier de piste. */
export async function collectResults(
  h: Harness,
  expectedDurationSec: number | undefined,
  durationToleranceSec = 6,
): Promise<Collected> {
  const files: FileReport[] = [];
  const manifests: Collected['manifests'] = [];
  for (const object of await listObjects(h.s3, h.config.s3Bucket, `${h.room}/`)) {
    const localPath = join(h.resultsDir, basename(object.key));
    const bytes = await downloadObject(h.s3, h.config.s3Bucket, object.key);
    await writeFile(localPath, bytes);

    if (object.key.endsWith('.json')) {
      const manifest = JSON.parse(new TextDecoder().decode(bytes)) as {
        started_at: number;
        ended_at: number;
        files: { filename: string }[];
      };
      manifests.push({
        file: basename(manifest.files[0]?.filename ?? object.key),
        startedAtNs: manifest.started_at,
        endedAtNs: manifest.ended_at,
      });
      continue;
    }

    const base = {
      key: object.key,
      size: object.size,
      lastModified: object.lastModified?.toISOString(),
    };
    try {
      const summary = await probeFile(localPath);
      const issues =
        expectedDurationSec === undefined
          ? []
          : checkAgainst(summary, {
              kind: object.key.includes('-video-') ? 'video' : 'audio',
              expectedDurationSec,
              durationToleranceSec,
              ...(object.key.includes('-video-')
                ? { minWidth: 1920, minHeight: 1080, minFps: 29 }
                : {}),
            });
      files.push({ ...base, summary, probeError: undefined, issues });
    } catch (error) {
      files.push({
        ...base,
        summary: undefined,
        probeError: error instanceof Error ? (error.message.split('\n')[0] ?? 'erreur') : 'erreur',
        issues: ['fichier illisible par ffprobe'],
      });
    }
  }
  return { files, manifests };
}

export function printCollected(collected: Collected): void {
  for (const file of collected.files) {
    console.log(
      `${basename(file.key)}\n  ${file.summary ? jsonSafe(file.summary) : `illisible : ${file.probeError ?? ''}`}\n  écarts : ${file.issues.length ? file.issues.join(' ; ') : 'aucun'}`,
    );
  }
  const earliest = Math.min(...collected.manifests.map((m) => m.startedAtNs));
  console.log('\nDébut et durée murale d’après les manifestes :');
  for (const m of collected.manifests) {
    console.log(
      `  ${m.file} : début +${((m.startedAtNs - earliest) / 1e6).toFixed(1)} ms, durée ${((m.endedAtNs - m.startedAtNs) / 1e9).toFixed(2)} s`,
    );
  }
}

export function printStats(h: Harness): void {
  const summary = summarizeStats(h.stats);
  if (summary.length === 0) return;
  console.log('\nCPU et mémoire des conteneurs pendant l’enregistrement (100 % = 1 cœur) :');
  for (const s of summary) {
    console.log(
      `  ${s.name} : CPU moyen ${String(s.cpuAvgPercent)} %, max ${String(s.cpuMaxPercent)} %, mémoire max ${String(s.memMaxMiB)} MiB (${String(s.samples)} relevés)`,
    );
  }
}

export async function saveReport(h: Harness, scenario: string, extra: object): Promise<void> {
  await writeFile(
    join(h.resultsDir, `${scenario}.json`),
    JSON.stringify(
      { room: h.room, timeline: h.timeline, statsSummary: summarizeStats(h.stats), ...extra },
      null,
      2,
    ),
  );
}
