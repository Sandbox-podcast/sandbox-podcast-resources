import { filePosition, type TrackAlignment } from './alignment.ts';
import type { ClipFormat, Rect } from './clips.ts';

/**
 * Liste de décisions de montage : référence les sources et décrit comment les assembler. Les fichiers
 * sources ne sont jamais modifiés (AC-EXPORT-002) ; l'export est un calcul à partir de cette liste.
 */
export interface EditDecisionList {
  version: number;
  episodeId: string;
  tracks: (TrackAlignment & {
    kind: 'audio' | 'video';
    participantId: string;
    sourcePath: string;
  })[];
}

export interface ClipExportPlan {
  edl: EditDecisionList;
  startSec: number;
  endSec: number;
  videoTrackId: string;
  audioTrackIds: readonly string[];
  format: ClipFormat;
  /** Fenêtre de recadrage dans l'image source (obligatoire pour 9:16 et 1:1). */
  crop?: Rect;
  outputPath: string;
  /** Loudness cible (LUFS intégrés) ; absent : pas de normalisation. */
  targetLufs?: number;
}

const OUTPUT_SIZE: Record<ClipFormat, { width: number; height: number }> = {
  '16:9': { width: 1920, height: 1080 },
  '9:16': { width: 1080, height: 1920 },
  '1:1': { width: 1080, height: 1080 },
};

const fixed = (value: number): string => value.toFixed(3);

export class ExportPlanError extends Error {}

/**
 * Arguments ffmpeg d'un export de clip (tableau d'arguments, jamais une chaîne passée à un shell).
 * Chaque entrée est positionnée à l'endroit du fichier qui correspond à l'instant de départ de la ligne
 * de temps commune. Un fichier audio qui commence après le départ du clip est retardé (`adelay`) ; la
 * dérive d'une piste audio par rapport à la référence est corrigée par `atempo`. La vidéo sert de référence.
 */
export function buildClipArgs(plan: ClipExportPlan): string[] {
  const duration = plan.endSec - plan.startSec;
  if (!(duration > 0)) throw new ExportPlanError('durée du clip nulle ou négative');
  const find = (id: string) => {
    const track = plan.edl.tracks.find((t) => t.trackId === id);
    if (!track) throw new ExportPlanError(`piste inconnue : ${id}`);
    return track;
  };
  const video = find(plan.videoTrackId);
  if (video.kind !== 'video')
    throw new ExportPlanError(`${video.trackId} n'est pas une piste vidéo`);
  if (plan.audioTrackIds.length === 0) throw new ExportPlanError('aucune piste audio');
  const videoStart = filePosition(video, plan.startSec);
  if (videoStart < 0) throw new ExportPlanError('le clip commence avant le début de la vidéo');

  const args = ['-y', '-hide_banner', '-loglevel', 'error'];
  args.push('-ss', fixed(videoStart), '-t', fixed(duration), '-i', video.sourcePath);

  const filters: string[] = [];
  const size = OUTPUT_SIZE[plan.format];
  const cropFilter =
    plan.format === '16:9'
      ? ''
      : plan.crop
        ? `crop=${String(plan.crop.width)}:${String(plan.crop.height)}:${String(plan.crop.x)}:${String(plan.crop.y)},`
        : (() => {
            throw new ExportPlanError('un recadrage est obligatoire hors 16:9');
          })();
  filters.push(
    `[0:v]${cropFilter}scale=${String(size.width)}:${String(size.height)}:flags=lanczos,setsar=1,format=yuv420p[v]`,
  );

  const labels: string[] = [];
  plan.audioTrackIds.forEach((id, i) => {
    const track = find(id);
    if (track.kind !== 'audio') throw new ExportPlanError(`${id} n'est pas une piste audio`);
    const position = filePosition(track, plan.startSec);
    // Position négative : le fichier commence après le départ du clip, on retarde d'autant.
    const delayMs = position < 0 ? Math.round((-position / (1 + track.driftPpm * 1e-6)) * 1000) : 0;
    const seek = Math.max(0, position);
    args.push(
      '-ss',
      fixed(seek),
      '-t',
      fixed(duration * (1 + track.driftPpm * 1e-6)),
      '-i',
      track.sourcePath,
    );
    const chain = [
      `[${String(i + 1)}:a]aresample=48000`,
      ...(Math.abs(track.driftPpm) > 0
        ? [`atempo=${(1 / (1 + track.driftPpm * 1e-6)).toFixed(9)}`]
        : []),
      ...(delayMs > 0 ? [`adelay=${String(delayMs)}:all=1`] : []),
      'apad',
    ].join(',');
    filters.push(`${chain}[a${String(i)}]`);
    labels.push(`[a${String(i)}]`);
  });
  const mix = `${labels.join('')}amix=inputs=${String(labels.length)}:duration=longest:normalize=0`;
  const loud =
    plan.targetLufs === undefined ? '' : `,loudnorm=I=${String(plan.targetLufs)}:TP=-1.5:LRA=11`;
  filters.push(`${mix}${loud},atrim=0:${fixed(duration)},asetpts=PTS-STARTPTS[a]`);

  args.push(
    '-filter_complex',
    filters.join(';'),
    '-map',
    '[v]',
    '-map',
    '[a]',
    '-t',
    fixed(duration),
    '-c:v',
    'libx264',
    '-preset',
    'veryfast',
    '-crf',
    '20',
    '-c:a',
    'aac',
    '-b:a',
    '160k',
    '-ar',
    '48000',
    '-movflags',
    '+faststart',
    plan.outputPath,
  );
  return args;
}

export type StepName = 'RENDER' | 'VERIFY' | 'CHECKSUM';
export const STEPS: readonly StepName[] = ['RENDER', 'VERIFY', 'CHECKSUM'];
export type StepStatus = 'PENDING' | 'DONE' | 'FAILED';
export type ExportStatus = 'PENDING' | 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'CANCELLED';

export interface ExportJob {
  readonly id: string;
  readonly episodeId: string;
  readonly presetVersion: number;
  readonly editDecisionVersion: number;
  readonly sourceTrackIds: readonly string[];
  readonly createdAt: number;
  readonly createdBy: string;
  readonly status: ExportStatus;
  readonly steps: Readonly<
    Record<StepName, { status: StepStatus; attempts: number; error: string | null }>
  >;
  /** Dossier temporaire du job : seul endroit où le nettoyage peut supprimer. */
  readonly tempDir: string;
  readonly outputPath: string;
  readonly checksum: string | null;
}

export const newExportJob = (input: {
  id: string;
  episodeId: string;
  presetVersion: number;
  editDecisionVersion: number;
  sourceTrackIds: readonly string[];
  createdAt: number;
  createdBy: string;
  tempDir: string;
  outputPath: string;
}): ExportJob => ({
  ...input,
  status: 'PENDING',
  steps: {
    RENDER: { status: 'PENDING', attempts: 0, error: null },
    VERIFY: { status: 'PENDING', attempts: 0, error: null },
    CHECKSUM: { status: 'PENDING', attempts: 0, error: null },
  },
  checksum: null,
});

export interface ExportExecutors {
  /** Produit le fichier à `job.outputPath` ; doit s'arrêter quand le signal est levé. */
  render(job: ExportJob, signal: AbortSignal): Promise<void>;
  /** Lève une erreur si le fichier produit n'est pas conforme. */
  verify(job: ExportJob): Promise<void>;
  checksum(job: ExportJob): Promise<string>;
  /** Supprime des dossiers temporaires. Reçoit uniquement `job.tempDir` ; l'implémentation refuse tout chemin hors de la racine des exports. */
  remove(paths: readonly string[]): Promise<void>;
}

const message = (error: unknown): string =>
  error instanceof Error ? error.message : String(error);

/**
 * Exécute les étapes dans l'ordre, en sautant celles déjà faites (AC-EXPORT-003) : un export échoué à
 * la vérification n'est pas rendu à nouveau. Un signal levé arrête l'export proprement.
 */
export async function runExport(
  job: ExportJob,
  executors: ExportExecutors,
  signal: AbortSignal = new AbortController().signal,
): Promise<ExportJob> {
  if (job.status === 'SUCCEEDED' || job.status === 'CANCELLED') return job;
  // Le signal peut être levé pendant un `await` : on le relit à chaque fois (TypeScript le croirait figé).
  const isAborted = (): boolean => signal.aborted;
  let current: ExportJob = { ...job, status: 'RUNNING' };
  for (const step of STEPS) {
    if (current.steps[step].status === 'DONE') continue;
    if (isAborted()) return cancelExport(current, executors);
    const attempts = current.steps[step].attempts + 1;
    try {
      if (step === 'RENDER') await executors.render(current, signal);
      else if (step === 'VERIFY') await executors.verify(current);
      else current = { ...current, checksum: await executors.checksum(current) };
      current = {
        ...current,
        steps: { ...current.steps, [step]: { status: 'DONE', attempts, error: null } },
      };
    } catch (error) {
      if (isAborted()) return cancelExport(current, executors);
      return {
        ...current,
        status: 'FAILED',
        steps: { ...current.steps, [step]: { status: 'FAILED', attempts, error: message(error) } },
      };
    }
  }
  return { ...current, status: 'SUCCEEDED' };
}

/** Relance un export échoué : les étapes `DONE` sont conservées, l'étape échouée est rejouée. */
export const retryExport = (job: ExportJob): ExportJob =>
  job.status === 'FAILED' ? { ...job, status: 'PENDING' } : job;

/**
 * AC-EXPORT-005 : annule l'export et supprime le dossier temporaire du job (sortie partielle comprise).
 * Seul `job.tempDir` est transmis au nettoyage : jamais une source, jamais le dossier d'un autre job.
 */
export async function cancelExport(job: ExportJob, executors: ExportExecutors): Promise<ExportJob> {
  if (job.status === 'SUCCEEDED') return job;
  await executors.remove([job.tempDir]);
  return { ...job, status: 'CANCELLED' };
}

/** AC-EXPORT-004 : ce qu'un export réussi conserve pour la traçabilité. */
export interface ExportRecord {
  episodeId: string;
  presetVersion: number;
  editDecisionVersion: number;
  sourceTrackIds: readonly string[];
  createdAt: number;
  createdBy: string;
  checksum: string;
}

export function exportRecord(job: ExportJob): ExportRecord | null {
  if (job.status !== 'SUCCEEDED' || job.checksum === null) return null;
  return {
    episodeId: job.episodeId,
    presetVersion: job.presetVersion,
    editDecisionVersion: job.editDecisionVersion,
    sourceTrackIds: job.sourceTrackIds,
    createdAt: job.createdAt,
    createdBy: job.createdBy,
    checksum: job.checksum,
  };
}
