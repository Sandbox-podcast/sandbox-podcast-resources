/**
 * Superviseur de l'enregistrement : observe LiveKit, Docker et les disques, demande un plan à
 * `@podcast/recording-control`, puis l'exécute. Boucle simple, toutes les décisions viennent de
 * la fonction pure `planRecording`.
 */
import { execFile } from 'node:child_process';
import { copyFile, mkdir, readdir, rm } from 'node:fs/promises';
import { basename, join } from 'node:path';
import { promisify } from 'node:util';
import {
  planRecording,
  type EgressFiles,
  type EgressRecord,
  type EgressStatus as RecordedStatus,
  type ObservedRecordingState,
  type PublishedTrack,
  type RecordingAction,
} from '@podcast/recording-control';
import { DirectFileOutput, EgressStatus, TrackType } from 'livekit-server-sdk';
import type { Harness } from './harness.ts';
import { recoverEgressTmp } from './recovery.ts';
import { localDir, sleep } from './stack.ts';
import { uploadPending } from './uploader.ts';

const run = promisify(execFile);
const WORKER = 'poc03-egress-1';

interface KnownEgress {
  trackSid: string;
  /** Chemin demandé dans le stockage, sans extension : `<salle>/<identité>-<type>-<sid>`. */
  filepath: string;
  startedAtMs: number;
}

export class Supervisor {
  recordingActive = false;
  readonly log: string[] = [];
  private readonly known = new Map<string, KnownEgress>();
  private readonly verified = new Set<string>();
  private readonly stopAttempted = new Set<string>();
  private readonly lastSeenTracks = new Map<string, number>();
  private readonly unpublishedSince = new Map<string, number>();
  private participants = new Map<string, PublishedTrack & { identity: string }>();
  private stopRequested = false;
  private lastSummary = '';
  private activeAlerts = new Set<string>();

  readonly tmpDir = join(localDir, 'egress-tmp');
  readonly outRoot = join(localDir, 'egress-out');

  private readonly h: Harness;

  constructor(h: Harness) {
    this.h = h;
  }

  private note(message: string): void {
    this.log.push(message);
    this.h.log(`[superviseur] ${message}`);
  }

  get roomOutDir(): string {
    return join(this.outRoot, this.h.room);
  }

  get egressSegments(): ReadonlyMap<string, KnownEgress> {
    return this.known;
  }

  /** Boucle jusqu'à `stop()`. */
  async loop(intervalMs = 2000): Promise<void> {
    while (!this.stopRequested) {
      try {
        const observed = await this.observe();
        const plan = planRecording(observed);
        const summary = `${plan.segments.map((s) => s.state).join(',')} | ${plan.actions
          .filter((a) => a.type !== 'ALERT')
          .map((a) => a.type)
          .join(',')}`;
        if (summary !== this.lastSummary) {
          this.note(`segments=[${summary}]`);
          this.lastSummary = summary;
        }
        this.logNewAlerts(plan.actions);
        await this.execute(plan.actions.filter((a) => a.type !== 'ALERT'));
      } catch (error) {
        this.note(`erreur de cycle : ${error instanceof Error ? error.message : 'inconnue'}`);
      }
      await sleep(intervalMs);
    }
  }

  /** Journalise une alerte une seule fois tant qu'elle reste active. */
  private logNewAlerts(actions: readonly RecordingAction[]): void {
    const current = new Set<string>();
    for (const action of actions) {
      if (action.type !== 'ALERT') continue;
      const key = `${action.code}|${action.subject}`;
      current.add(key);
      if (!this.activeAlerts.has(key)) {
        this.note(`ALERTE ${action.code} (${action.subject}) : ${action.message}`);
      }
    }
    this.activeAlerts = current;
  }

  stop(): void {
    this.stopRequested = true;
  }

  /** Vrai quand tous les segments connus sont vérifiés dans le stockage. */
  allSafe(): boolean {
    return this.known.size > 0 && [...this.known.keys()].every((id) => this.verified.has(id));
  }

  async observe(): Promise<ObservedRecordingState> {
    const nowMs = Date.now();

    // Pistes publiées (participants visibles seulement : les egress sont cachés).
    const participants = (await this.h.rooms.listParticipants(this.h.room).catch(() => [])).filter(
      (p) => p.permission?.hidden !== true,
    );
    const current = new Map<string, PublishedTrack & { identity: string }>();
    for (const p of participants) {
      for (const t of p.tracks) {
        current.set(t.sid, {
          sid: t.sid,
          participantId: p.identity,
          identity: p.identity,
          kind: t.type === TrackType.VIDEO ? 'video' : 'audio',
        });
        this.lastSeenTracks.set(t.sid, nowMs);
        this.unpublishedSince.delete(t.sid);
      }
    }
    for (const sid of this.lastSeenTracks.keys()) {
      if (!current.has(sid) && !this.unpublishedSince.has(sid))
        this.unpublishedSince.set(sid, nowMs);
    }
    this.participants = current;

    // Egress vus par LiveKit.
    const infos = await this.h.egress.listEgress({ roomName: this.h.room });
    const egresses: EgressRecord[] = infos.flatMap((info) => {
      const known = this.known.get(info.egressId);
      if (!known) return [];
      return [
        {
          egressId: info.egressId,
          trackSid: known.trackSid,
          status: EgressStatus[info.status].replace('EGRESS_', '') as RecordedStatus,
          startedAtMs: known.startedAtMs,
        },
      ];
    });

    // État du worker, lu auprès de Docker (pas auprès de LiveKit).
    const inspect = await run('docker', [
      'inspect',
      '-f',
      '{{.State.Running}}|{{.State.StartedAt}}',
      WORKER,
    ]).catch(() => ({ stdout: 'false|' }));
    const [running, startedAt] = inspect.stdout.trim().split('|');
    const workerStartedAtMs = startedAt ? Date.parse(startedAt) : 0;

    return {
      nowMs,
      recordingActive: this.recordingActive,
      tracks: [...current.values()].map(({ sid, participantId, kind }) => ({
        sid,
        participantId,
        kind,
      })),
      egresses,
      files: await this.observeFiles(),
      workerHealthy: running === 'true',
      workerStartedAtMs: Number.isFinite(workerStartedAtMs) ? workerStartedAtMs : 0,
      unpublishedSince: Object.fromEntries(this.unpublishedSince),
    };
  }

  private async observeFiles(): Promise<EgressFiles[]> {
    const outFiles = await readdir(this.roomOutDir).catch(() => [] as string[]);
    const result: EgressFiles[] = [];
    for (const [egressId, known] of this.known) {
      const prefix = basename(known.filepath);
      const workingFiles = await readdir(join(this.tmpDir, egressId)).catch(() => [] as string[]);
      result.push({
        egressId,
        workingFile: workingFiles.some((f) => f.startsWith(prefix)),
        localOutput: outFiles.some((f) => f.startsWith(prefix)),
        verifiedInStorage: this.verified.has(egressId),
      });
    }
    return result;
  }

  async execute(actions: readonly RecordingAction[]): Promise<void> {
    for (const action of actions) {
      switch (action.type) {
        case 'ALERT':
          this.note(`ALERTE ${action.code} (${action.subject}) : ${action.message}`);
          break;
        case 'START_EGRESS':
          await this.startEgress(action.trackSid);
          break;
        case 'STOP_EGRESS':
          await this.stopEgress(action.egressId, action.reason);
          break;
        case 'RUN_RECOVERY':
          await this.recover(action.egressIds);
          break;
        case 'RESTART_WORKER':
          this.note('redémarrage du worker Egress (fichiers déjà récupérés)');
          await run('docker', ['start', WORKER]);
          await sleep(3000);
          break;
        case 'UPLOAD':
          await this.upload();
          break;
      }
    }
  }

  private async startEgress(trackSid: string): Promise<void> {
    const track = this.participants.get(trackSid);
    if (!track) return;
    const attempt = this.known.size;
    const filepath = `${this.h.room}/${track.identity}-${track.kind}-${trackSid}-s${String(attempt)}`;
    try {
      const info = await this.h.egress.startTrackEgress(
        this.h.room,
        new DirectFileOutput({ filepath: `/out/${filepath}` }),
        trackSid,
      );
      this.known.set(info.egressId, { trackSid, filepath, startedAtMs: Date.now() });
      this.h.egressFiles.set(info.egressId, filepath);
      this.note(`egress ${info.egressId} démarré pour ${track.identity}/${track.kind}`);
    } catch (error) {
      this.note(
        `démarrage impossible pour ${trackSid} : ${error instanceof Error ? error.message.slice(0, 80) : 'erreur'}`,
      );
    }
  }

  private async stopEgress(egressId: string, reason: string): Promise<void> {
    if (this.stopAttempted.has(egressId)) return;
    this.stopAttempted.add(egressId);
    this.note(`arrêt de ${egressId} (${reason})`);
    const timeout = new Promise<never>((_, reject) => {
      setTimeout(() => {
        reject(new Error('délai dépassé'));
      }, 8000);
    });
    await Promise.race([this.h.egress.stopEgress(egressId), timeout]).catch((error: unknown) => {
      this.note(
        `arrêt de ${egressId} sans effet : ${error instanceof Error ? error.message.slice(0, 80) : 'erreur'}`,
      );
    });
  }

  private async recover(egressIds: readonly string[]): Promise<void> {
    this.note(`récupération des fichiers de travail de ${egressIds.join(', ')}`);
    await mkdir(this.roomOutDir, { recursive: true });
    const scratch = join(this.h.resultsDir, 'recovery-scratch');
    const recovered = await recoverEgressTmp(this.tmpDir, scratch);
    for (const item of recovered) {
      if (!egressIds.includes(item.egressId) || !item.output) continue;
      await copyFile(item.output, join(this.roomOutDir, basename(item.output)));
      await rm(join(this.tmpDir, item.egressId), { recursive: true, force: true });
      this.note(
        `récupéré : ${basename(item.output)} (${item.method}, ${String(item.durationSec ?? '?')} s)`,
      );
    }
  }

  private async upload(): Promise<void> {
    const results = await uploadPending({
      s3: this.h.s3,
      bucket: this.h.config.s3Bucket,
      localDir: this.roomOutDir,
      keyPrefix: this.h.room,
      doneDir: join(this.outRoot, '_envoyes', this.h.room),
      maxAttempts: 2,
      retryDelayMs: 500,
    });
    for (const [egressId, known] of this.known) {
      const prefix = basename(known.filepath);
      if (
        results.some(
          (r) =>
            r.outcome === 'verified' &&
            basename(r.file).startsWith(prefix) &&
            !r.file.endsWith('.json'),
        )
      ) {
        if (!this.verified.has(egressId)) this.note(`vérifié dans le stockage : ${prefix}`);
        this.verified.add(egressId);
      }
    }
  }
}
