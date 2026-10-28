/**
 * Répare un MP4 sans index laissé par un crash d'Egress.
 * Usage : node src/cli/recover-mp4.ts <entree.mp4> <sortie.mp4> [fps=30]
 * Limite : la cadence est supposée constante, les horodatages d'origine sont perdus.
 */
import { execFile } from 'node:child_process';
import { readFile, writeFile } from 'node:fs/promises';
import { promisify } from 'node:util';
import { extractAnnexB } from '../lib/mp4-recovery.ts';
import { probeFile } from '../lib/stack.ts';

const run = promisify(execFile);
const [input, output, fpsArg] = process.argv.slice(2);
if (!input || !output) throw new Error('Usage : recover-mp4.ts <entree.mp4> <sortie.mp4> [fps]');
const fps = fpsArg ?? '30';

const recovered = extractAnnexB(new Uint8Array(await readFile(input)));
console.log(
  `${String(recovered.nalCount)} NAL récupérés, ${String(recovered.droppedTailBytes)} octets de fin ignorés`,
);
const rawPath = `${output}.h264`;
await writeFile(rawPath, recovered.annexB);
await run('ffmpeg', [
  '-y',
  '-loglevel',
  'error',
  '-f',
  'h264',
  '-framerate',
  fps,
  '-i',
  rawPath,
  '-c',
  'copy',
  output,
]);

const summary = await probeFile(output);
console.log(
  `Fichier réparé : ${summary.codec ?? '?'} ${String(summary.width)}x${String(summary.height)} ${summary.fps?.toFixed(2) ?? '?'} images/s, ${summary.durationSec?.toFixed(2) ?? '?'} s`,
);
