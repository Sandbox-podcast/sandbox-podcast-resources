import { QualityController } from '@podcast/scene-quality';
import {
  LevelHistory,
  coverRect,
  cropForSlot,
  initials,
  programLayout,
  type Rect,
} from './layout.ts';
import type { Mask, Segmenter, SegmenterFactory } from './segmenter.ts';

/** Une personne de la salle, vue par le rendu du Program. */
export interface ProgramSource {
  id: string;
  name: string;
  local: boolean;
  /** Vidéo reçue ; `null` tant que la caméra n'est pas arrivée. */
  video: HTMLVideoElement | null;
  /** Niveau audio courant (0 à 1). */
  level(): number;
}

export interface ProgramInfo {
  title: string;
  subtitle: string;
  recording: boolean;
}

export interface ProgramDeps {
  sources: () => ProgramSource[];
  info: () => ProgramInfo;
  /** Absent : pas de détourage du tout (cadre elliptique aux bords adoucis). */
  segmenter: SegmenterFactory | null;
}

const WIDTH = 1920;
const HEIGHT = 1080;
const ACCENTS = ['#f5a524', '#3b82f6', '#a855f7', '#14b8a6', '#ec4899'];
const BARS = 28;

interface SourceState {
  cutout: HTMLCanvasElement;
  scaled: HTMLCanvasElement;
  mask: { canvas: HTMLCanvasElement; width: number; height: number } | null;
  segmenter: Segmenter | null;
  creating: boolean;
  failed: string | null;
  inFlight: boolean;
  history: LevelHistory;
}

const canvas = (w: number, h: number): HTMLCanvasElement => {
  const c = document.createElement('canvas');
  c.width = Math.max(1, Math.round(w));
  c.height = Math.max(1, Math.round(h));
  return c;
};

function context(c: HTMLCanvasElement): CanvasRenderingContext2D {
  const ctx = c.getContext('2d');
  if (!ctx) throw new Error('contexte 2D indisponible');
  return ctx;
}

function roundedRect(ctx: CanvasRenderingContext2D, r: Rect, radius: number): void {
  ctx.beginPath();
  ctx.roundRect(r.x, r.y, r.width, r.height, radius);
}

/** Réduit la taille de police jusqu'à ce que le texte tienne dans la largeur donnée. */
function fitFont(
  ctx: CanvasRenderingContext2D,
  text: string,
  weight: string,
  maxPx: number,
  maxWidth: number,
): void {
  let size = maxPx;
  ctx.font = `${weight} ${String(size)}px system-ui, sans-serif`;
  while (size > 12 && ctx.measureText(text).width > maxWidth) {
    size -= 2;
    ctx.font = `${weight} ${String(size)}px system-ui, sans-serif`;
  }
}

/**
 * Rendu du Program : décor commun, participants détourés, bandeau des noms et des niveaux audio, titre, signal
 * « ON AIR ». Régulé par `@podcast/scene-quality` : sous charge, le détourage est dégradé avant la fluidité.
 */
export class ProgramRenderer {
  readonly canvas: HTMLCanvasElement;
  private readonly ctx: CanvasRenderingContext2D;
  private readonly deps: ProgramDeps;
  private readonly controller = new QualityController();
  private readonly states = new Map<string, SourceState>();
  private decor: HTMLImageElement | null = null;
  private proceduralDecor: HTMLCanvasElement | null = null;
  private running = false;
  private loopId = 0;
  private segmentationOn: boolean;
  private frame = 0;
  private statusListener: ((text: string) => void) | null = null;

  constructor(target: HTMLCanvasElement, deps: ProgramDeps) {
    this.canvas = target;
    this.canvas.width = WIDTH;
    this.canvas.height = HEIGHT;
    this.ctx = context(target);
    this.deps = deps;
    this.segmentationOn = deps.segmenter !== null;
  }

  onStatus(listener: (text: string) => void): void {
    this.statusListener = listener;
  }

  setDecor(image: HTMLImageElement | null): void {
    this.decor = image;
  }

  setSegmentation(on: boolean): void {
    this.segmentationOn = on && this.deps.segmenter !== null;
    // Sans détourage : niveau « sans détourage » verrouillé ; avec : la régulation reprend la main.
    if (this.segmentationOn) this.controller.unlock(performance.now());
    else this.controller.lock(3, performance.now());
  }

  start(): void {
    if (this.running) return;
    this.running = true;
    this.loopId += 1;
    void this.loop(this.loopId);
  }

  stop(): void {
    this.running = false;
    for (const state of this.states.values()) state.segmenter?.close();
    this.states.clear();
  }

  private stateFor(id: string): SourceState {
    let state = this.states.get(id);
    if (!state) {
      state = {
        cutout: canvas(2, 2),
        scaled: canvas(2, 2),
        mask: null,
        segmenter: null,
        creating: false,
        failed: null,
        inFlight: false,
        history: new LevelHistory(BARS),
      };
      this.states.set(id, state);
    }
    return state;
  }

  /** Crée le détoureur d'une personne, une seule fois ; en cas d'échec, on retombe sur le cadre adouci. */
  private ensureSegmenter(state: SourceState): void {
    const factory = this.deps.segmenter;
    if (!factory || state.segmenter || state.creating || state.failed) return;
    state.creating = true;
    void factory()
      .then((segmenter) => {
        segmenter.onMask((mask: Mask) => {
          const target = state.mask?.canvas ?? canvas(mask.width, mask.height);
          if (target.width !== mask.width || target.height !== mask.height) {
            target.width = mask.width;
            target.height = mask.height;
          }
          const mctx = context(target);
          mctx.clearRect(0, 0, target.width, target.height);
          mctx.drawImage(mask.image, 0, 0);
          state.mask = { canvas: target, width: mask.width, height: mask.height };
        });
        state.segmenter = segmenter;
      })
      .catch((error: unknown) => {
        state.failed = error instanceof Error ? error.message : 'détourage indisponible';
      })
      .finally(() => {
        state.creating = false;
      });
  }

  private async loop(id: number): Promise<void> {
    let next = performance.now();
    let lastStatus = 0;
    let frames = 0;
    let costSum = 0;
    while (this.running && id === this.loopId) {
      const started = performance.now();
      const lateness = Math.max(0, started - next);
      this.drawFrame();
      const cost = performance.now() - started;
      costSum += cost;
      frames += 1;
      this.controller.onFrame(cost + lateness, performance.now());
      if (performance.now() - lastStatus > 1000) {
        this.statusListener?.(this.statusText(frames, costSum));
        lastStatus = performance.now();
        frames = 0;
        costSum = 0;
      }
      next += 1000 / this.controller.currentSettings.compositionFps;
      const wait = next - performance.now();
      if (wait > 0) await new Promise<void>((resolve) => setTimeout(resolve, wait));
      else next = performance.now();
    }
  }

  private statusText(frames: number, costSum: number): string {
    const failures = [...this.states.values()].map((s) => s.failed).find((f) => f !== null);
    const parts = [
      `${String(frames)} images/s`,
      `${(frames > 0 ? costSum / frames : 0).toFixed(1)} ms par image`,
      this.segmentationOn
        ? `détourage : niveau ${this.controller.currentSettings.name}`
        : 'détourage désactivé',
    ];
    if (failures) parts.push(`détourage indisponible (${failures}), cadre adouci à la place`);
    return parts.join(' · ');
  }

  private drawFrame(): void {
    const sources = this.deps.sources().slice(0, 5);
    const layout = programLayout(sources.length, WIDTH, HEIGHT);
    const level = this.controller.currentSettings;
    this.frame += 1;
    this.drawDecor();

    sources.forEach((source, i) => {
      const slot = layout.slots[i];
      if (!slot) return;
      const state = this.stateFor(source.id);
      state.history.push(source.level());
      if (this.segmentationOn) this.ensureSegmenter(state);
      this.drawPerson(source, state, slot, level.segmentEvery, level.segmentInputHeight);
    });
    // Les identifiants qui ont disparu libèrent leur détoureur.
    for (const [id, state] of this.states) {
      if (!sources.some((s) => s.id === id)) {
        state.segmenter?.close();
        this.states.delete(id);
      }
    }

    this.drawPanel(sources, layout);
    this.drawTitle(layout.title);
    this.drawOnAir(layout.onAir);
  }

  private drawDecor(): void {
    const ctx = this.ctx;
    ctx.globalCompositeOperation = 'source-over';
    if (this.decor && this.decor.naturalWidth > 0) {
      const r = coverRect(
        { width: this.decor.naturalWidth, height: this.decor.naturalHeight },
        { width: WIDTH, height: HEIGHT },
      );
      ctx.drawImage(this.decor, r.x, r.y, r.width, r.height);
      return;
    }
    this.proceduralDecor ??= this.buildProceduralDecor();
    ctx.drawImage(this.proceduralDecor, 0, 0);
  }

  /** Décor par défaut, dessiné une fois : dégradé sombre, lumières floues, fines lignes. Remplaçable par une image. */
  private buildProceduralDecor(): HTMLCanvasElement {
    const c = canvas(WIDTH, HEIGHT);
    const ctx = context(c);
    const base = ctx.createLinearGradient(0, 0, WIDTH, HEIGHT);
    base.addColorStop(0, '#10131c');
    base.addColorStop(0.5, '#1a1530');
    base.addColorStop(1, '#0d1620');
    ctx.fillStyle = base;
    ctx.fillRect(0, 0, WIDTH, HEIGHT);
    const lights: [number, number, number, string][] = [
      [300, 220, 360, 'rgba(245,165,36,0.22)'],
      [1500, 180, 420, 'rgba(59,130,246,0.2)'],
      [980, 380, 520, 'rgba(168,85,247,0.12)'],
      [1700, 760, 300, 'rgba(236,72,153,0.14)'],
    ];
    for (const [x, y, r, color] of lights) {
      const g = ctx.createRadialGradient(x, y, 0, x, y, r);
      g.addColorStop(0, color);
      g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, WIDTH, HEIGHT);
    }
    ctx.strokeStyle = 'rgba(255,255,255,0.05)';
    ctx.lineWidth = 2;
    for (let x = 0; x <= WIDTH; x += 160) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, HEIGHT);
      ctx.stroke();
    }
    for (let y = 0; y <= HEIGHT; y += 160) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(WIDTH, y);
      ctx.stroke();
    }
    const vignette = ctx.createRadialGradient(
      WIDTH / 2,
      HEIGHT / 2,
      HEIGHT * 0.4,
      WIDTH / 2,
      HEIGHT / 2,
      HEIGHT * 0.95,
    );
    vignette.addColorStop(0, 'rgba(0,0,0,0)');
    vignette.addColorStop(1, 'rgba(0,0,0,0.55)');
    ctx.fillStyle = vignette;
    ctx.fillRect(0, 0, WIDTH, HEIGHT);
    return c;
  }

  private drawPerson(
    source: ProgramSource,
    state: SourceState,
    slot: Rect,
    segmentEvery: number,
    segmentHeight: number,
  ): void {
    const ctx = this.ctx;
    const video = source.video;
    if (!video || video.videoWidth === 0 || video.readyState < 2) {
      // Pas encore d'image : pastille avec les initiales.
      const cx = slot.x + slot.width / 2;
      const cy = slot.y + slot.height * 0.6;
      ctx.fillStyle = 'rgba(255,255,255,0.12)';
      ctx.beginPath();
      ctx.arc(cx, cy, slot.height * 0.22, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#fff';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.font = `700 ${String(Math.round(slot.height * 0.16))}px system-ui, sans-serif`;
      ctx.fillText(initials(source.name), cx, cy);
      return;
    }

    // Lance un détourage sur une image sur N, sans attendre : le dernier masque reste utilisé entre-temps.
    if (
      this.segmentationOn &&
      state.segmenter &&
      segmentEvery > 0 &&
      this.frame % segmentEvery === 0 &&
      !state.inFlight
    ) {
      const h = segmentHeight;
      const w = Math.round((h * video.videoWidth) / video.videoHeight);
      if (state.scaled.width !== w || state.scaled.height !== h) {
        state.scaled.width = w;
        state.scaled.height = h;
      }
      context(state.scaled).drawImage(video, 0, 0, w, h);
      state.inFlight = true;
      void state.segmenter.send(state.scaled).finally(() => {
        state.inFlight = false;
      });
    }

    const cutW = Math.round(slot.width);
    const cutH = Math.round(slot.height);
    if (state.cutout.width !== cutW || state.cutout.height !== cutH) {
      state.cutout.width = cutW;
      state.cutout.height = cutH;
    }
    const cut = context(state.cutout);
    cut.globalCompositeOperation = 'source-over';
    cut.clearRect(0, 0, cutW, cutH);
    const crop = cropForSlot(
      { width: video.videoWidth, height: video.videoHeight },
      { x: 0, y: 0, width: cutW, height: cutH },
    );

    const useModel = this.segmentationOn && state.mask !== null && segmentEvery > 0;
    if (useModel && state.mask) {
      // Le masque couvre toute l'image de la caméra : même rognage que la vidéo, converti à sa taille.
      const k = state.mask.width / video.videoWidth;
      cut.filter = 'blur(1.5px)';
      cut.drawImage(
        state.mask.canvas,
        crop.x * k,
        crop.y * k,
        crop.width * k,
        crop.height * k,
        0,
        0,
        cutW,
        cutH,
      );
      cut.filter = 'none';
    } else {
      // Sans modèle : ellipse aux bords adoucis.
      const g = cut.createRadialGradient(
        cutW / 2,
        cutH * 0.55,
        cutH * 0.2,
        cutW / 2,
        cutH * 0.55,
        cutH * 0.62,
      );
      g.addColorStop(0, 'rgba(0,0,0,1)');
      g.addColorStop(1, 'rgba(0,0,0,0)');
      cut.fillStyle = g;
      cut.fillRect(0, 0, cutW, cutH);
    }
    cut.globalCompositeOperation = 'source-in';
    cut.drawImage(video, crop.x, crop.y, crop.width, crop.height, 0, 0, cutW, cutH);
    cut.globalCompositeOperation = 'source-over';
    ctx.drawImage(state.cutout, slot.x, slot.y);
  }

  private drawPanel(sources: ProgramSource[], layout: ReturnType<typeof programLayout>): void {
    const ctx = this.ctx;
    const panel = layout.panel;
    ctx.save();
    roundedRect(ctx, panel, 18);
    ctx.fillStyle = 'rgba(8,10,18,0.82)';
    ctx.fill();
    ctx.lineWidth = 3;
    const edge = ctx.createLinearGradient(panel.x, 0, panel.x + panel.width, 0);
    edge.addColorStop(0, ACCENTS[0] ?? '#fff');
    edge.addColorStop(0.5, ACCENTS[1] ?? '#fff');
    edge.addColorStop(1, ACCENTS[2] ?? '#fff');
    ctx.strokeStyle = edge;
    ctx.stroke();
    ctx.restore();

    sources.forEach((source, i) => {
      const caption = layout.captions[i];
      const state = this.states.get(source.id);
      if (!caption || !state) return;
      const accent = ACCENTS[i % ACCENTS.length] ?? '#fff';
      const speaking = source.level() > 0.05;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = '#fff';
      fitFont(ctx, source.name, '700', Math.round(caption.name.height * 0.8), caption.name.width);
      ctx.fillText(
        source.name,
        caption.name.x + caption.name.width / 2,
        caption.name.y + caption.name.height / 2,
      );
      ctx.fillStyle = accent;
      ctx.fillRect(
        caption.name.x,
        caption.name.y + caption.name.height + 4,
        caption.name.width,
        speaking ? 6 : 3,
      );

      const bars = state.history.bars;
      const barWidth = caption.levels.width / bars.length;
      ctx.fillStyle = accent;
      ctx.globalAlpha = speaking ? 1 : 0.55;
      bars.forEach((value, k) => {
        // Une barre minimale reste visible : une piste silencieuse n'est pas une piste absente.
        const h = Math.max(3, value * caption.levels.height * 2.2);
        const clamped = Math.min(h, caption.levels.height);
        ctx.fillRect(
          caption.levels.x + k * barWidth + barWidth * 0.2,
          caption.levels.y + (caption.levels.height - clamped) / 2,
          barWidth * 0.6,
          clamped,
        );
      });
      ctx.globalAlpha = 1;
    });
  }

  private drawTitle(rect: Rect): void {
    const ctx = this.ctx;
    const info = this.deps.info();
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.shadowColor = 'rgba(0,0,0,0.6)';
    ctx.shadowBlur = 12;
    ctx.fillStyle = '#fff';
    fitFont(ctx, info.title.toUpperCase(), '800', Math.round(rect.height * 0.6), rect.width);
    ctx.fillText(info.title.toUpperCase(), rect.x, rect.y);
    ctx.fillStyle = 'rgba(255,255,255,0.85)';
    fitFont(ctx, info.subtitle, '500', Math.round(rect.height * 0.28), rect.width);
    ctx.fillText(info.subtitle, rect.x, rect.y + rect.height * 0.65);
    ctx.shadowBlur = 0;
  }

  private drawOnAir(rect: Rect): void {
    const ctx = this.ctx;
    const on = this.deps.info().recording;
    ctx.save();
    roundedRect(ctx, rect, 12);
    ctx.fillStyle = on ? 'rgba(220,38,38,0.92)' : 'rgba(60,60,70,0.7)';
    if (on) {
      ctx.shadowColor = 'rgba(248,113,113,0.9)';
      ctx.shadowBlur = 28;
    }
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.lineWidth = 3;
    ctx.strokeStyle = on ? '#fecaca' : 'rgba(255,255,255,0.25)';
    ctx.stroke();
    ctx.fillStyle = on ? '#fff' : 'rgba(255,255,255,0.45)';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.font = `800 ${String(Math.round(rect.height * 0.55))}px system-ui, sans-serif`;
    ctx.fillText('ON AIR', rect.x + rect.width / 2, rect.y + rect.height / 2);
    ctx.restore();
  }
}
