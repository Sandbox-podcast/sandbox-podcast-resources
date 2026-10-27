/**
 * Banc de mesure du studio virtuel dans Chrome : N flux vidéo 1080p30 détourés (MediaPipe Selfie
 * Segmentation, WebGL) et composés dans un décor commun 1920×1080, avec ou sans régulation de qualité.
 * Tout tourne dans la page ; le résultat est un objet JSON lu par le script de lancement.
 */
import { QualityController, type QualityLevel } from '@podcast/scene-quality';

interface SelfieSegmentationLike {
  setOptions(options: { modelSelection: number; selfieMode?: boolean }): void;
  onResults(callback: (results: { segmentationMask: CanvasImageSource }) => void): void;
  initialize(): Promise<void>;
  send(input: { image: HTMLCanvasElement | HTMLVideoElement }): Promise<void>;
  close(): Promise<void>;
}
declare const SelfieSegmentation: new (config: {
  locateFile: (file: string) => string;
}) => SelfieSegmentationLike;

export interface BenchConfig {
  participants: number;
  seconds: number;
  /** `compose` : composition seule (masque elliptique, aucun modèle) ; `mediapipe` : détourage réel. */
  mode: 'compose' | 'mediapipe';
  /** Régulation de qualité active ? Sinon le niveau 0 est tenu. */
  controller: boolean;
  /** Coût artificiel ajouté à chaque image (ms), pour simuler une machine plus faible. */
  stressMs: number;
  /** Coût artificiel par détourage lancé (ms à 720 p, proportionnel à la hauteur d'entrée) : simule un modèle plus lent sur une machine plus faible. */
  stressPerSegmentationMs: number;
  /** Niveau imposé (verrou), sinon la régulation décide. */
  lockLevel: number | null;
  modelSelection: 0 | 1;
}

interface Stats {
  count: number;
  p50: number;
  p95: number;
  max: number;
  mean: number;
}

const percentile = (sorted: readonly number[], p: number): number =>
  sorted.length === 0
    ? 0
    : (sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * p))] ?? 0);

function stats(values: readonly number[]): Stats {
  const sorted = [...values].sort((a, b) => a - b);
  const mean = sorted.length === 0 ? 0 : sorted.reduce((a, b) => a + b, 0) / sorted.length;
  const round = (x: number): number => Math.round(x * 100) / 100;
  return {
    count: sorted.length,
    p50: round(percentile(sorted, 0.5)),
    p95: round(percentile(sorted, 0.95)),
    max: round(sorted[sorted.length - 1] ?? 0),
    mean: round(mean),
  };
}

const sleep = (ms: number): Promise<void> =>
  new Promise((resolve) => {
    setTimeout(resolve, ms);
  });

function canvas(width: number, height: number): HTMLCanvasElement {
  const c = document.createElement('canvas');
  c.width = width;
  c.height = height;
  return c;
}

function context(c: HTMLCanvasElement): CanvasRenderingContext2D {
  const ctx = c.getContext('2d');
  if (!ctx) throw new Error('contexte 2D indisponible');
  return ctx;
}

interface Participant {
  video: HTMLVideoElement;
  segmenter: SelfieSegmentationLike | null;
  mask: HTMLCanvasElement;
  hasMask: boolean;
  inFlight: boolean;
  sentAt: number;
  scaled: HTMLCanvasElement;
  cutout: HTMLCanvasElement;
  maskUpdates: number;
}

async function loadVideo(url: string, offsetSec: number): Promise<HTMLVideoElement> {
  const video = document.createElement('video');
  video.src = url;
  video.loop = true;
  video.muted = true;
  video.playsInline = true;
  await new Promise<void>((resolve, reject) => {
    video.onloadedmetadata = () => {
      resolve();
    };
    video.onerror = () => {
      reject(new Error('vidéo illisible'));
    };
  });
  video.currentTime = offsetSec;
  await video.play();
  return video;
}

async function run(config: BenchConfig): Promise<unknown> {
  const OUT_W = 1920;
  const OUT_H = 1080;
  const TILE_W = 640;
  const TILE_H = 360;
  const out = canvas(OUT_W, OUT_H);
  const outCtx = context(out);

  const probeCanvas = canvas(1, 1);
  const probeCtx = probeCanvas.getContext('2d', { willReadFrequently: true });
  if (!probeCtx) throw new Error('contexte 2D indisponible');

  // Décor commun, dessiné une fois.
  const decor = canvas(OUT_W, OUT_H);
  const decorCtx = context(decor);
  const gradient = decorCtx.createLinearGradient(0, 0, OUT_W, OUT_H);
  gradient.addColorStop(0, '#16324f');
  gradient.addColorStop(1, '#6b2b5e');
  decorCtx.fillStyle = gradient;
  decorCtx.fillRect(0, 0, OUT_W, OUT_H);
  decorCtx.fillStyle = 'rgba(255,255,255,0.08)';
  for (let i = 0; i < 12; i += 1) decorCtx.fillRect(i * 160, 0, 6, OUT_H);

  // Masque de repli (niveau sans détourage) : ellipse aux bords adoucis.
  const fallbackMask = canvas(TILE_W, TILE_H);
  const fmCtx = context(fallbackMask);
  const radial = fmCtx.createRadialGradient(
    TILE_W / 2,
    TILE_H / 2,
    TILE_H * 0.25,
    TILE_W / 2,
    TILE_H / 2,
    TILE_H * 0.5,
  );
  radial.addColorStop(0, 'rgba(0,0,0,1)');
  radial.addColorStop(1, 'rgba(0,0,0,0)');
  fmCtx.fillStyle = radial;
  fmCtx.fillRect(0, 0, TILE_W, TILE_H);

  const initStart = performance.now();
  const participants: Participant[] = [];
  for (let i = 0; i < config.participants; i += 1) {
    const video = await loadVideo('/source.mp4', i * 2.5);
    const p: Participant = {
      video,
      segmenter: null,
      mask: canvas(TILE_W, TILE_H),
      hasMask: false,
      inFlight: false,
      sentAt: 0,
      scaled: canvas(1280, 720),
      cutout: canvas(TILE_W, TILE_H),
      maskUpdates: 0,
    };
    if (config.mode === 'mediapipe') {
      const segmenter = new SelfieSegmentation({ locateFile: (f) => `/mp/${f}` });
      segmenter.setOptions({ modelSelection: config.modelSelection });
      await segmenter.initialize();
      p.segmenter = segmenter;
    }
    participants.push(p);
  }
  const initMs = performance.now() - initStart;

  const latencies: number[] = [];
  for (const p of participants) {
    p.segmenter?.onResults((results) => {
      const maskCtx = context(p.mask);
      maskCtx.clearRect(0, 0, TILE_W, TILE_H);
      maskCtx.drawImage(results.segmentationMask, 0, 0, TILE_W, TILE_H);
      p.hasMask = true;
      p.maskUpdates += 1;
      latencies.push(performance.now() - p.sentAt);
    });
  }

  const controller = new QualityController();
  if (config.lockLevel !== null) controller.lock(config.lockLevel, 0);
  const levelFrames = new Map<number, number>();
  const syncCosts: number[] = [];
  const fullCosts: number[] = [];
  const intervals: number[] = [];
  const perSecond: {
    t: number;
    level: number;
    fps: number;
    meanSyncMs: number;
    meanLateMs: number;
    maxLateMs: number;
    load: number;
  }[] = [];
  let sec = { ticks: 0, sync: 0, late: 0, maxLate: 0 };
  let secStart = performance.now();
  let lastLoad = 0;
  const timeline: { tSec: number; level: number; name: string; load: number }[] = [];

  const startedAt = performance.now();
  let frame = 0;
  let nextTick = startedAt;
  let lastDone = startedAt;
  timeline.push({ tSec: 0, level: 0, name: controller.currentSettings.name, load: 0 });

  while (performance.now() - startedAt < config.seconds * 1000) {
    const level: QualityLevel = controller.currentSettings;
    const tickStart = performance.now();
    const lateness = Math.max(0, tickStart - nextTick);

    for (const [index, p] of participants.entries()) {
      // Détourage : une image sur N, sans attendre le résultat (le masque précédent est réutilisé).
      if (
        config.mode === 'mediapipe' &&
        level.segmentEvery > 0 &&
        frame % level.segmentEvery === 0 &&
        !p.inFlight &&
        p.segmenter
      ) {
        const h = level.segmentInputHeight;
        const w = Math.round((h * 16) / 9);
        if (p.scaled.width !== w) {
          p.scaled.width = w;
          p.scaled.height = h;
        }
        context(p.scaled).drawImage(p.video, 0, 0, w, h);
        if (config.stressPerSegmentationMs > 0) {
          const until = performance.now() + (config.stressPerSegmentationMs * h) / 720;
          while (performance.now() < until) {
            /* coût artificiel */
          }
        }
        p.inFlight = true;
        p.sentAt = performance.now();
        const segmenter = p.segmenter;
        void segmenter.send({ image: p.scaled }).finally(() => {
          p.inFlight = false;
        });
      }
      const cut = context(p.cutout);
      cut.globalCompositeOperation = 'source-over';
      cut.clearRect(0, 0, TILE_W, TILE_H);
      cut.drawImage(p.video, 0, 0, TILE_W, TILE_H);
      cut.globalCompositeOperation = 'destination-in';
      const useModelMask = config.mode === 'mediapipe' && level.segmentEvery > 0 && p.hasMask;
      cut.drawImage(useModelMask ? p.mask : fallbackMask, 0, 0, TILE_W, TILE_H);
      cut.globalCompositeOperation = 'source-over';
      outCtx.drawImage(index === 0 ? decor : out, 0, 0);
      outCtx.drawImage(p.cutout, index * TILE_W, (OUT_H - TILE_H) / 2);
    }
    if (config.stressMs > 0) {
      const until = performance.now() + config.stressMs;
      while (performance.now() < until) {
        /* coût artificiel */
      }
    }
    const syncCost = performance.now() - tickStart;
    // Toutes les 10 images, on force l'exécution côté GPU pour mesurer le coût réel de bout en bout.
    if (frame % 10 === 0) {
      // Lecture sur un petit canvas annexe : lire `out` directement ferait basculer Chrome vers un canvas logiciel
      // (heuristique `willReadFrequently`) au milieu de l'essai, ce qui a faussé une première série de mesures.
      probeCtx.drawImage(out, 0, 0, 1, 1);
      probeCtx.getImageData(0, 0, 1, 1);
      fullCosts.push(performance.now() - tickStart);
    }
    syncCosts.push(syncCost);
    sec = {
      ticks: sec.ticks + 1,
      sync: sec.sync + syncCost,
      late: sec.late + lateness,
      maxLate: Math.max(sec.maxLate, lateness),
    };
    const decision = config.controller
      ? controller.onFrame(syncCost + lateness, performance.now())
      : null;
    if (decision?.changed) {
      timeline.push({
        tSec: Math.round((performance.now() - startedAt) / 10) / 100,
        level: decision.level,
        name: controller.currentSettings.name,
        load: Math.round(decision.load * 100) / 100,
      });
    }
    lastLoad = decision?.load ?? lastLoad;
    if (performance.now() - secStart >= 1000) {
      perSecond.push({
        t: Math.round((performance.now() - startedAt) / 1000),
        level: controller.currentLevel,
        fps: sec.ticks,
        meanSyncMs: Math.round((sec.sync / sec.ticks) * 10) / 10,
        meanLateMs: Math.round((sec.late / sec.ticks) * 10) / 10,
        maxLateMs: Math.round(sec.maxLate),
        load: Math.round(lastLoad * 100) / 100,
      });
      sec = { ticks: 0, sync: 0, late: 0, maxLate: 0 };
      secStart = performance.now();
    }
    levelFrames.set(controller.currentLevel, (levelFrames.get(controller.currentLevel) ?? 0) + 1);

    const done = performance.now();
    intervals.push(done - lastDone);
    lastDone = done;
    frame += 1;
    nextTick += 1000 / controller.currentSettings.compositionFps;
    const wait = nextTick - performance.now();
    if (wait > 0) await sleep(wait);
    else nextTick = performance.now(); // en retard : on repart de maintenant, sans rattraper
  }

  const elapsedSec = (performance.now() - startedAt) / 1000;
  const gl = canvas(1, 1).getContext('webgl');
  const debug = gl?.getExtension('WEBGL_debug_renderer_info');
  const renderer = gl && debug ? String(gl.getParameter(debug.UNMASKED_RENDERER_WEBGL)) : 'inconnu';
  const result = {
    config,
    renderer,
    initMs: Math.round(initMs),
    elapsedSec: Math.round(elapsedSec * 10) / 10,
    ticks: frame,
    achievedFps: Math.round((frame / elapsedSec) * 10) / 10,
    intervalMs: stats(intervals),
    syncCostMs: stats(syncCosts),
    fullCostMs: stats(fullCosts),
    segmentationLatencyMs: stats(latencies),
    maskUpdatesPerSecPerParticipant: participants.map(
      (p) => Math.round((p.maskUpdates / elapsedSec) * 10) / 10,
    ),
    framesPerLevel: Object.fromEntries([...levelFrames.entries()].map(([k, v]) => [k, v])),
    timeline,
    perSecond,
    finalLevel: controller.currentSettings.name,
  };
  for (const p of participants) {
    p.video.pause();
    void p.segmenter?.close();
  }
  return result;
}

(window as unknown as { bench: { run: typeof run } }).bench = { run };
