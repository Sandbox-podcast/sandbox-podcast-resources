/**
 * Détourage du fond avec MediaPipe Selfie Segmentation (Apache-2.0, modèle fourni par le paquet npm
 * `@mediapipe/selfie_segmentation`, copié dans `/mp/` au moment de la construction). Un détoureur par flux.
 * Voir l'ADR-0012 : le détourage tourne chez le Producer, sur les flux reçus.
 */
export interface Mask {
  /** Image dont la transparence indique la personne (opaque) et le fond (transparent). */
  image: CanvasImageSource;
  width: number;
  height: number;
}

export interface Segmenter {
  /** Lance un détourage ; le résultat arrive par `onMask`. Se termine quand le calcul est fini. */
  send(frame: HTMLCanvasElement): Promise<void>;
  onMask(callback: (mask: Mask) => void): void;
  close(): void;
}

export type SegmenterFactory = () => Promise<Segmenter>;

interface MediaPipeResults {
  segmentationMask: CanvasImageSource & { width: number; height: number };
}
interface MediaPipeSegmenter {
  setOptions(options: { modelSelection: number }): void;
  onResults(callback: (results: MediaPipeResults) => void): void;
  initialize(): Promise<void>;
  send(input: { image: CanvasImageSource }): Promise<void>;
  close(): Promise<void>;
}
type MediaPipeConstructor = new (config: {
  locateFile: (file: string) => string;
}) => MediaPipeSegmenter;

let loading: Promise<MediaPipeConstructor> | null = null;

/** Charge le script de MediaPipe une seule fois (même origine, voir la politique de contenu). */
function loadMediaPipe(): Promise<MediaPipeConstructor> {
  loading ??= new Promise<MediaPipeConstructor>((resolve, reject) => {
    const existing = (window as unknown as { SelfieSegmentation?: MediaPipeConstructor })
      .SelfieSegmentation;
    if (existing) {
      resolve(existing);
      return;
    }
    const script = document.createElement('script');
    script.src = '/mp/selfie_segmentation.js';
    script.onload = () => {
      const ctor = (window as unknown as { SelfieSegmentation?: MediaPipeConstructor })
        .SelfieSegmentation;
      if (ctor) resolve(ctor);
      else reject(new Error('MediaPipe chargé mais introuvable'));
    };
    script.onerror = () => {
      loading = null;
      reject(new Error('Script de détourage introuvable (/mp/selfie_segmentation.js)'));
    };
    document.head.append(script);
  });
  return loading;
}

/** Détoureur MediaPipe. Lève une erreur claire si le script, le modèle ou WebGL sont indisponibles. */
export const mediaPipeSegmenterFactory: SegmenterFactory = async () => {
  const Ctor = await loadMediaPipe();
  const inner = new Ctor({ locateFile: (file) => `/mp/${file}` });
  // Modèle « paysage » (256×144), adapté aux cadrages de caméra.
  inner.setOptions({ modelSelection: 1 });
  await inner.initialize();
  let listener: ((mask: Mask) => void) | null = null;
  inner.onResults((results) => {
    listener?.({
      image: results.segmentationMask,
      width: results.segmentationMask.width,
      height: results.segmentationMask.height,
    });
  });
  return {
    send: (frame) => inner.send({ image: frame }),
    onMask: (callback) => {
      listener = callback;
    },
    close: () => {
      void inner.close();
    },
  };
};
