/**
 * Fichier MP4 (H.264 1080p30 + AAC) à repères, pour les publieurs Chrome (banc du POC 1,
 * `--source sync`) : éclair blanc de 100 ms et bip de 1 kHz de 100 ms toutes les 10 s à partir de
 * t = 10 s, au même instant. Même contenu que make-sync-media.ts, dans un seul fichier que la page
 * joue avec son image et son son. Durée par défaut : 1 500 s, à ne pas boucler pendant la mesure.
 */
import { execFile } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { promisify } from 'node:util';

const run = promisify(execFile);
const outDir = join(import.meta.dirname, '..', '..', '..', 'poc-01-media-plane', '.local');
const t = String(Number(process.argv[2] ?? 1500));

await mkdir(outDir, { recursive: true });
await run(
  'ffmpeg',
  [
    '-y',
    '-loglevel',
    'error',
    '-f',
    'lavfi',
    '-i',
    "color=c=black:s=1920x1080:r=30,noise=alls=4:allf=t+u,drawbox=x=0:y=0:w=iw:h=ih:color=white:t=fill:enable='gte(t,10)*lt(mod(t,10),0.1)'",
    '-f',
    'lavfi',
    '-i',
    `aevalsrc='if(gte(t,10)*lt(mod(t,10),0.1),0.5*sin(2*PI*1000*t),0)':s=48000:c=stereo:d=${t}`,
    '-t',
    t,
    '-c:v',
    'libx264',
    '-profile:v',
    'high',
    '-pix_fmt',
    'yuv420p',
    '-preset',
    'veryfast',
    '-b:v',
    '800k',
    '-maxrate',
    '800k',
    '-bufsize',
    '1600k',
    '-g',
    '60',
    '-c:a',
    'aac',
    '-b:a',
    '128k',
    '-ar',
    '48000',
    '-movflags',
    '+faststart',
    'source-sync.mp4',
  ],
  { cwd: outDir, maxBuffer: 1 << 26 },
);
console.log(`source-sync.mp4 (${t} s) créé dans ${outDir}`);
