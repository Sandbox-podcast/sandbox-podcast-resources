import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import { detectOnsets, type Sample } from './markers.ts';

/**
 * Lance ffmpeg avec le filtre `metadata=print` et rend la suite (heure, valeur) d'une clé.
 * Le format de sortie est : « frame:N pts:P pts_time:T » puis « <clé>=<valeur> ».
 */
async function metadataSeries(args: string[], key: string): Promise<Sample[]> {
  const child = spawn('ffmpeg', ['-hide_banner', '-loglevel', 'error', ...args], {
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  let stderr = '';
  child.stderr.on('data', (chunk: Buffer) => {
    stderr += chunk.toString();
  });
  const done = new Promise<void>((resolve, reject) => {
    child.on('error', reject);
    child.on('close', (code) => {
      if (code === 0) resolve();
      else
        reject(
          new Error(`ffmpeg a échoué (code ${String(code)}) : ${stderr.split('\n')[0] ?? ''}`),
        );
    });
  });

  const series: Sample[] = [];
  let currentTime: number | undefined;
  for await (const line of createInterface({ input: child.stdout })) {
    const time = /pts_time:(-?[\d.]+)/.exec(line);
    if (time?.[1] !== undefined) {
      currentTime = Number(time[1]);
      continue;
    }
    if (line.startsWith(`${key}=`) && currentTime !== undefined) {
      const raw = line.slice(key.length + 1).trim();
      const value = raw === '-inf' ? -200 : Number(raw);
      if (Number.isFinite(value)) series.push({ t: currentTime, value });
    }
  }
  await done;
  return series;
}

/** Luminance moyenne de chaque image, dans la ligne de temps du conteneur. */
export function videoLumaSeries(file: string): Promise<Sample[]> {
  return metadataSeries(
    [
      '-i',
      file,
      '-an',
      '-fps_mode',
      'passthrough',
      '-vf',
      'scale=32:18:flags=area,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-',
      '-f',
      'null',
      '-',
    ],
    'lavfi.signalstats.YAVG',
  );
}

/** Niveau efficace (dB) de fenêtres de 2,5 ms (120 échantillons à 48 kHz). */
export function audioLevelSeries(file: string): Promise<Sample[]> {
  return metadataSeries(
    [
      '-i',
      file,
      '-vn',
      '-ac',
      '1',
      '-ar',
      '48000',
      '-af',
      'asetnsamples=n=120:p=0,astats=metadata=1:reset=1:measure_perchannel=none:measure_overall=RMS_level,ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-',
      '-f',
      'null',
      '-',
    ],
    'lavfi.astats.Overall.RMS_level',
  );
}

/** Heures des éclairs (luminance au-dessus de 128) et des bips (au-dessus de −30 dB). */
export async function flashOnsets(file: string): Promise<number[]> {
  return detectOnsets(await videoLumaSeries(file), { threshold: 128, minGapSec: 1 });
}

export async function beepOnsets(file: string): Promise<number[]> {
  return detectOnsets(await audioLevelSeries(file), { threshold: -30, minGapSec: 1 });
}
