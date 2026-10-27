/**
 * Médias de test à repères : un éclair blanc de 3 images (100 ms) et un bip de 1 kHz de 100 ms,
 * tous les 10 s à partir de t = 10 s, exactement au même instant dans la vidéo et dans l'audio.
 * Le décalage audio/vidéo de la source est donc nul par construction : tout décalage relevé dans
 * un enregistrement vient de la chaîne de publication, du SFU ou d'Egress.
 * La vidéo est un fond noir avec un léger bruit temporel (pour que les images diffèrent).
 */
import { execFile } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { promisify } from 'node:util';

const run = promisify(execFile);
const outDir = join(
  import.meta.dirname,
  '..',
  '..',
  '..',
  'poc-03-server-recording',
  '.local',
  'media',
);
const durationSec = Number(process.argv[2] ?? 2100);
const t = String(durationSec);

await mkdir(outDir, { recursive: true });

console.log(`vidéo : sync.h264 (${t} s, 1080p30)`);
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
    '-t',
    t,
    '-c:v',
    'libx264',
    '-profile:v',
    'baseline',
    '-level',
    '4.1',
    '-pix_fmt',
    'yuv420p',
    '-preset',
    'veryfast',
    '-b:v',
    '1500k',
    '-maxrate',
    '1500k',
    '-bufsize',
    '3000k',
    '-g',
    '60',
    '-f',
    'h264',
    'sync.h264',
  ],
  { cwd: outDir, maxBuffer: 1 << 26 },
);

console.log(`audio : sync.ogg (${t} s)`);
await run(
  'ffmpeg',
  [
    '-y',
    '-loglevel',
    'error',
    '-f',
    'lavfi',
    '-i',
    `aevalsrc='if(gte(t,10)*lt(mod(t,10),0.1),0.5*sin(2*PI*1000*t),0)':s=48000:c=mono:d=${t}`,
    '-c:a',
    'libopus',
    '-b:a',
    '64k',
    '-ar',
    '48000',
    '-ac',
    '2',
    'sync.ogg',
  ],
  { cwd: outDir, maxBuffer: 1 << 26 },
);

console.log('Médias à repères créés dans', outDir);
