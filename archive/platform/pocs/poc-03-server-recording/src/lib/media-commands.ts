export interface FfmpegJob {
  /** Nom du fichier produit, relatif au dossier de sortie. */
  output: string;
  args: string[];
}

const VIDEO_ARGS = [
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
  '4M',
  '-maxrate',
  '4M',
  '-bufsize',
  '8M',
  '-g',
  '60',
  '-f',
  'h264',
];

const AUDIO_ARGS = ['-c:a', 'libopus', '-b:a', '64k', '-ar', '48000', '-ac', '2'];

/**
 * Médias de test déterministes pour le publieur `lk room join --publish` :
 * vidéo H.264 1080p30 à 4 Mb/s (image clé toutes les 2 s) et audio Opus.
 * Deux sources distinctes (A et B) pour reconnaître les pistes à l'écoute et à l'image.
 */
export function mediaJobs(durationSec: number): FfmpegJob[] {
  const t = String(durationSec);
  return [
    {
      output: 'a.h264',
      args: [
        '-f',
        'lavfi',
        '-i',
        'testsrc2=size=1920x1080:rate=30',
        '-t',
        t,
        ...VIDEO_ARGS,
        'a.h264',
      ],
    },
    {
      output: 'b.h264',
      args: [
        '-f',
        'lavfi',
        '-i',
        'testsrc2=size=1920x1080:rate=30,hue=h=120,hflip',
        '-t',
        t,
        ...VIDEO_ARGS,
        'b.h264',
      ],
    },
    {
      output: 'a.ogg',
      args: [
        '-f',
        'lavfi',
        '-i',
        'sine=frequency=440:sample_rate=48000',
        '-t',
        t,
        ...AUDIO_ARGS,
        'a.ogg',
      ],
    },
    {
      output: 'b.ogg',
      args: [
        '-f',
        'lavfi',
        '-i',
        'sine=frequency=660:sample_rate=48000',
        '-t',
        t,
        ...AUDIO_ARGS,
        'b.ogg',
      ],
    },
  ];
}
