/**
 * POC 10 : de bout en bout, à partir de vrais fichiers enregistrés (POC 4, 3 participants Chrome) :
 *   sources → reconstruction (alignement par repères) → transcription (faux fournisseur) →
 *   suggestion de clips (validées) → export d'un clip 9:16 avec ffmpeg → vérification.
 * Le témoin : le même export sans alignement. L'alignement est vérifié sur le fichier produit :
 * largeur des bips (3 bips alignés = 1 bip de 100 ms) et écart entre l'éclair et le bip.
 *
 *   node src/run-e2e.ts [dossier-des-enregistrements]
 */
import { execFile, spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createReadStream } from 'node:fs';
import { mkdir, readdir, rm, stat, writeFile } from 'node:fs/promises';
import { join, resolve, sep } from 'node:path';
import { promisify } from 'node:util';
import {
  audioLevelSeries,
  beepOnsets,
  flashOnsets,
} from '@podcast/poc-04-multitrack-sync/extract.ts';
import { markerExtents } from '@podcast/poc-04-multitrack-sync/markers.ts';
import {
  IDENTITY,
  ScriptedProvider,
  alignToReference,
  attemptTranscription,
  buildClipArgs,
  exportRecord,
  newExportJob,
  newTranscriptionJob,
  runExport,
  validateSuggestions,
  verticalCrop,
  type EditDecisionList,
  type ExportExecutors,
  type ExportJob,
} from '@podcast/post-production';

const run = promisify(execFile);
const here = import.meta.dirname;
const defaultDir = join(
  here,
  '..',
  '..',
  'poc-03-server-recording',
  '.local',
  'egress-out',
  '_envoyes',
);
const exportsRoot = resolve(here, '..', '.local', 'exports');

async function findRecordingDir(): Promise<string> {
  const arg = process.argv[2];
  if (arg) return resolve(arg);
  const names = (await readdir(defaultDir)).filter((n) => n.startsWith('p1-sync-chrome-20min-'));
  const last = names.sort().at(-1);
  if (!last) throw new Error('aucun enregistrement Chrome de 20 minutes trouvé');
  return join(defaultDir, last);
}

const dir = await findRecordingDir();
const files = await readdir(dir);
const identities = [
  ...new Set(
    files.map((f) => /^(chrome-\d+)-(?:audio|video)-/.exec(f)?.[1]).filter((x): x is string => !!x),
  ),
].sort();
const fileOf = (id: string, kind: 'audio' | 'video'): string => {
  const name = files.find((f) => f.startsWith(`${id}-${kind}-`) && /\.(mp4|ogg)$/.test(f));
  if (!name) throw new Error(`fichier ${kind} introuvable pour ${id}`);
  return join(dir, name);
};
console.log(`Enregistrements : ${dir}\nParticipants : ${identities.join(', ')}`);

// 1. Reconstruction : la ligne de temps commune est celle de la vidéo du premier participant.
console.log('\n[1] Repères dans les 6 fichiers…');
const onsets = new Map<string, number[]>();
await Promise.all(
  identities.flatMap((id) => [
    flashOnsets(fileOf(id, 'video')).then((o) => onsets.set(`${id}:video`, o)),
    beepOnsets(fileOf(id, 'audio')).then((o) => onsets.set(`${id}:audio`, o)),
  ]),
);
const reference = onsets.get(`${identities[0] ?? ''}:video`) ?? [];
const tracks: EditDecisionList['tracks'] = identities.flatMap((id) =>
  (['video', 'audio'] as const).map((kind) => {
    const trackId = `${id}:${kind}`;
    const alignment = alignToReference(trackId, reference, onsets.get(trackId) ?? [], {
      maxGapSec: 4,
      minMarkers: 50,
    });
    return { ...alignment, kind, participantId: id, sourcePath: fileOf(id, kind) };
  }),
);
for (const t of tracks) {
  console.log(
    `  ${t.trackId.padEnd(16)} départ ${t.offsetSec.toFixed(3).padStart(7)} s, dérive ${t.driftPpm.toFixed(1).padStart(6)} ppm, ${String(t.markers)} repères, résidu ${t.residualRmsMs.toFixed(1)} ms`,
  );
}
const edl: EditDecisionList = { version: 1, episodeId: 'ep-poc10', tracks };
const unaligned: EditDecisionList = {
  ...edl,
  tracks: tracks.map((t) => ({ ...t, ...IDENTITY })),
};

// 2. Transcription : faux fournisseur déterministe (aucun modèle de parole n'est disponible ici).
const mediaDurationSec = 1200;
const job = newTranscriptionJob({ id: 'poc10', mediaRef: 'ep-poc10', mediaDurationSec });
const transcription = await attemptTranscription(
  job,
  new ScriptedProvider({ speakers: identities, turnSec: 20 }),
  0,
);
if (transcription.kind !== 'RAN' || transcription.job.document === null)
  throw new Error('transcription refusée');
const transcript = transcription.job.document;
console.log(
  `\n[2] Transcription (faux fournisseur) : ${String(transcript.segments.length)} segments, version ${String(transcript.version)}`,
);

// 3. Suggestions de clips : la « sortie de modèle » est écrite à la main, avec des pièges.
const modelOutput: unknown[] = [
  {
    startSec: 60,
    endSec: 120,
    title: 'Le passage clé',
    hook: 'Ce qu’on ne vous dit pas',
    reason: 'Trois tours de parole complets, sujet unique',
    score: 0.92,
  },
  {
    startSec: 60,
    endSec: 100,
    title: 'Même passage, plus court',
    hook: 'Doublon',
    reason: 'Recouvre la première suggestion',
    score: 0.7,
  },
  {
    startSec: 333,
    endSec: 391,
    title: 'Timecode inventé',
    hook: 'x',
    reason: 'Ne correspond à aucun segment',
    score: 0.99,
  },
  {
    startSec: 400,
    endSec: 1300,
    title: 'Après la fin du média',
    hook: 'x',
    reason: 'Dépasse la durée',
    score: 0.8,
  },
  { startSec: 200, endSec: 260, title: 'Sans raison', hook: 'x', score: 0.5 },
  {
    startSec: 800,
    endSec: 860,
    title: 'Un autre bon passage',
    hook: 'La suite',
    reason: 'Réponse longue et conclusive',
    score: 0.6,
  },
];
const { accepted, rejected } = validateSuggestions(
  modelOutput,
  transcript.segments,
  mediaDurationSec,
);
console.log(
  `[3] Suggestions : ${String(accepted.length)} acceptées, ${String(rejected.length)} rejetées`,
);
for (const r of rejected) console.log(`    rejetée #${String(r.index)} : ${r.reasons.join(' ; ')}`);
const clip = accepted.reduce((best, c) => (c.score > best.score ? c : best));
console.log(
  `    retenue : « ${clip.title} » ${String(clip.startSec)}–${String(clip.endSec)} s (segments ${clip.firstSegmentId} à ${clip.lastSegmentId})`,
);

// 4. Export d'un clip 9:16 : caméra du premier locuteur du clip, mix des trois micros.
const firstSegment = transcript.segments.find((s) => s.id === clip.firstSegmentId);
const speaker = firstSegment?.speakerId ?? identities[0] ?? '';
const crop = verticalCrop(
  { width: 1920, height: 1080 },
  { x: 800, y: 200, width: 320, height: 520 },
);

interface Exported {
  label: string;
  job: ExportJob;
  seconds: number;
}

async function ffprobeJson(path: string): Promise<{
  streams: { codec_type: string; width?: number; height?: number }[];
  format: { duration: string };
}> {
  const { stdout } = await run(
    'ffprobe',
    ['-v', 'error', '-show_streams', '-show_format', '-of', 'json', path],
    { maxBuffer: 1 << 24 },
  );
  return JSON.parse(stdout) as never;
}

const sha256 = (path: string): Promise<string> =>
  new Promise((resolveHash, reject) => {
    const hash = createHash('sha256');
    createReadStream(path)
      .on('data', (c) => hash.update(c))
      .on('error', reject)
      .on('end', () => {
        resolveHash(hash.digest('hex'));
      });
  });

function executorsFor(plan: EditDecisionList, clipLength: number): ExportExecutors {
  return {
    render: (exportJob, signal) =>
      new Promise((resolveRender, reject) => {
        const args = buildClipArgs({
          edl: plan,
          startSec: clip.startSec,
          endSec: clip.endSec,
          videoTrackId: `${speaker}:video`,
          audioTrackIds: identities.map((id) => `${id}:audio`),
          format: '9:16',
          crop,
          outputPath: exportJob.outputPath,
          targetLufs: -16,
        });
        const child = spawn('ffmpeg', args, { signal, stdio: ['ignore', 'ignore', 'pipe'] });
        let err = '';
        child.stderr.on('data', (c: Buffer) => {
          err += c.toString();
        });
        child.on('error', reject);
        child.on('close', (code) => {
          if (code === 0) resolveRender();
          else reject(new Error(`ffmpeg ${String(code)} : ${err.slice(0, 300)}`));
        });
      }),
    verify: async (exportJob) => {
      const probe = await ffprobeJson(exportJob.outputPath);
      const video = probe.streams.find((s) => s.codec_type === 'video');
      const duration = Number(probe.format.duration);
      if (video?.width !== 1080 || video.height !== 1920)
        throw new Error('format de sortie inattendu');
      if (!probe.streams.some((s) => s.codec_type === 'audio'))
        throw new Error('pas de piste audio');
      if (Math.abs(duration - clipLength) > 0.25)
        throw new Error(`durée ${String(duration)} s au lieu de ${String(clipLength)} s`);
    },
    checksum: (exportJob) => sha256(exportJob.outputPath),
    remove: async (paths) => {
      for (const p of paths) {
        // Garde-fou : seul le dossier des exports est effaçable, jamais une source.
        if (!resolve(p).startsWith(exportsRoot + sep)) throw new Error(`chemin refusé : ${p}`);
        await rm(p, { recursive: true, force: true });
      }
    },
  };
}

async function exportClip(label: string, plan: EditDecisionList): Promise<Exported> {
  const id = `${label}-${String(Date.now())}`;
  const tempDir = join(exportsRoot, id);
  await mkdir(tempDir, { recursive: true });
  const exportJob = newExportJob({
    id,
    episodeId: edl.episodeId,
    presetVersion: 1,
    editDecisionVersion: plan.version,
    sourceTrackIds: plan.tracks.map((t) => t.trackId),
    createdAt: Date.now(),
    createdBy: 'poc10',
    tempDir,
    outputPath: join(tempDir, 'clip.mp4'),
  });
  const startedAt = Date.now();
  const done = await runExport(exportJob, executorsFor(plan, clip.endSec - clip.startSec));
  const seconds = (Date.now() - startedAt) / 1000;
  console.log(
    `    ${label} : ${done.status} en ${seconds.toFixed(1)} s${done.status === 'SUCCEEDED' ? '' : ` (${JSON.stringify(done.steps)})`}`,
  );
  return { label, job: done, seconds };
}

console.log(
  `\n[4] Export 9:16 (caméra de ${speaker}, mix des ${String(identities.length)} micros, −16 LUFS)`,
);
const aligned = await exportClip('aligne', edl);
const control = await exportClip('temoin-sans-alignement', unaligned);

// 5. Mesure sur les fichiers produits.
console.log('\n[5] Mesure sur les fichiers produits');
const results: Record<string, unknown> = {};
for (const e of [aligned, control]) {
  if (e.job.status !== 'SUCCEEDED') {
    results[e.label] = { status: e.job.status };
    continue;
  }
  const [series, flashes, beeps] = await Promise.all([
    audioLevelSeries(e.job.outputPath),
    flashOnsets(e.job.outputPath),
    beepOnsets(e.job.outputPath),
  ]);
  // La normalisation change le niveau : seuil relatif au maximum du signal.
  const peak = Math.max(...series.map((s) => s.value));
  const extents = markerExtents(series, beeps, {
    threshold: peak - 20,
    beforeSec: 0.2,
    afterSec: 1,
  }).map((w) => w * 1000);
  const meanWidth = extents.reduce((a, b) => a + b, 0) / extents.length;
  const pairs = flashes
    .map((f) => beeps.find((b) => Math.abs(b - f) < 2))
    .map((b, i) => (b === undefined ? undefined : (b - (flashes[i] ?? 0)) * 1000));
  const offsets = pairs.filter((x): x is number => x !== undefined);
  const meanOffset = offsets.reduce((a, b) => a + b, 0) / offsets.length;
  const record = exportRecord(e.job);
  results[e.label] = {
    status: e.job.status,
    markers: flashes.length,
    beepExtentMs: Number(meanWidth.toFixed(1)),
    audioMinusFlashMs: Number(meanOffset.toFixed(1)),
    sizeBytes: (await stat(e.job.outputPath)).size,
    record,
    renderSeconds: e.seconds,
  };
  console.log(
    `    ${e.label.padEnd(24)} ${String(flashes.length)} repères, étendue des bips ${meanWidth.toFixed(0)} ms, bip − éclair ${meanOffset.toFixed(0)} ms, empreinte ${record?.checksum.slice(0, 12) ?? '?'}…`,
  );
}

const outFile = join(here, '..', '.local', 'e2e-result.json');
await mkdir(join(here, '..', '.local'), { recursive: true });
await writeFile(
  outFile,
  JSON.stringify({ dir, tracks, clip, rejected, results, speaker, crop }, null, 2),
);
console.log(`\nRésultat : ${outFile}`);
