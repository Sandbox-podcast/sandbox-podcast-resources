/**
 * Analyse de synchronisation.
 *   node src/cli/analyze-sync.ts --dir <dossier-egress-de-la-salle> [--period 10] [--out rapport.json]
 *   node src/cli/analyze-sync.ts --pair <video> <audio> [--period 10]
 * Le premier mode retrouve les participants à partir des noms de fichiers « <identité>-video-… »
 * et « <identité>-audio-… », avec les manifestes `EG_*.json` pour les débuts d'egress.
 */
import { readdir, readFile, writeFile } from 'node:fs/promises';
import { basename, join } from 'node:path';
import { beepOnsets, flashOnsets } from '../lib/extract.ts';
import { buildSyncReport, evaluateReport, type TrackOnsets } from '../lib/sync-report.ts';

const args = process.argv.slice(2);
const flag = (name: string): string | undefined => {
  const index = args.indexOf(name);
  return index === -1 ? undefined : args[index + 1];
};
const periodSec = Number(flag('--period') ?? 10);
const fmt = (values: readonly number[]): string =>
  values
    .slice(0, 6)
    .map((v) => v.toFixed(3))
    .join(', ');

if (flag('--pair')) {
  const video = flag('--pair') ?? '';
  const audio = args[args.indexOf('--pair') + 2] ?? '';
  const [flashes, beeps] = await Promise.all([flashOnsets(video), beepOnsets(audio)]);
  console.log(`éclairs : ${String(flashes.length)} (${fmt(flashes)} …)`);
  console.log(`bips    : ${String(beeps.length)} (${fmt(beeps)} …)`);
  const report = buildSyncReport([{ participant: 'paire', video: flashes, audio: beeps }], {
    periodSec,
  });
  console.log(JSON.stringify(report.participants[0], null, 2));
  process.exit(0);
}

const dir = flag('--dir');
if (!dir) {
  console.error('Usage : --dir <dossier> | --pair <vidéo> <audio>');
  process.exit(2);
}

const names = await readdir(dir);
const manifests = new Map<string, number>();
for (const name of names.filter((n) => /^EG_.*\.json$/.test(n))) {
  const manifest = JSON.parse(await readFile(join(dir, name), 'utf8')) as {
    started_at: number;
    files: { filename: string }[];
  };
  for (const file of manifest.files) manifests.set(basename(file.filename), manifest.started_at);
}

const identities = [
  ...new Set(
    names
      .map((n) => /^(.+?)-(?:audio|video)-/.exec(n)?.[1])
      .filter((id): id is string => id !== undefined),
  ),
].sort();

const tracks: TrackOnsets[] = [];
await Promise.all(
  identities.map(async (identity) => {
    const video = names.find((n) => n.startsWith(`${identity}-video-`) && n.endsWith('.mp4'));
    const audio = names.find((n) => n.startsWith(`${identity}-audio-`) && n.endsWith('.ogg'));
    if (!video || !audio) {
      console.error(`${identity} : fichier audio ou vidéo manquant`);
      return;
    }
    const [flashes, beeps] = await Promise.all([
      flashOnsets(join(dir, video)),
      beepOnsets(join(dir, audio)),
    ]);
    console.log(`${identity} : ${String(flashes.length)} éclairs, ${String(beeps.length)} bips`);
    const videoStart = manifests.get(video);
    const audioStart = manifests.get(audio);
    tracks.push({
      participant: identity,
      video: flashes,
      audio: beeps,
      ...(videoStart === undefined ? {} : { videoStartedAtNs: videoStart }),
      ...(audioStart === undefined ? {} : { audioStartedAtNs: audioStart }),
    });
  }),
);
tracks.sort((a, b) => a.participant.localeCompare(b.participant));

const report = buildSyncReport(tracks, { periodSec });
const issues = evaluateReport(report);
console.log(JSON.stringify(report, null, 2));
console.log(
  issues.length === 0
    ? '\nTous les seuils sont respectés.'
    : `\nÉcarts aux seuils :\n- ${issues.join('\n- ')}`,
);

const out = flag('--out');
if (out) await writeFile(out, JSON.stringify({ report, issues }, null, 2));
