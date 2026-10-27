import { describe, expect, it } from 'vitest';
import {
  LevelHistory,
  MAX_PARTICIPANTS,
  coverRect,
  cropForSlot,
  initials,
  programLayout,
} from '../src/layout.ts';

const W = 1920;
const H = 1080;

describe('mise en page du Program', () => {
  it.each([1, 2, 3, 4, 5])(
    '%i participant(s) : zones dans le canevas, ordonnées, bandeau par-dessus le bas des silhouettes',
    (n) => {
      const layout = programLayout(n, W, H);
      expect(layout.slots).toHaveLength(n);
      expect(layout.captions).toHaveLength(n);
      for (const slot of layout.slots) {
        expect(slot.x).toBeGreaterThanOrEqual(0);
        expect(slot.x + slot.width).toBeLessThanOrEqual(W);
        expect(slot.y).toBeGreaterThanOrEqual(0);
        // Le bas de la silhouette passe sous le bandeau, qui est dessiné après.
        expect(slot.y + slot.height).toBeGreaterThan(layout.panel.y);
        expect(slot.y + slot.height).toBeLessThan(layout.panel.y + layout.panel.height);
      }
      for (let i = 1; i < n; i += 1)
        expect(layout.slots[i]?.x ?? 0).toBeGreaterThan(layout.slots[i - 1]?.x ?? 0);
      expect(layout.panel.x + layout.panel.width).toBeLessThanOrEqual(W);
      expect(layout.panel.y + layout.panel.height).toBeLessThanOrEqual(H);
    },
  );

  it('trois participants : silhouettes qui se chevauchent un peu, centrées sur leur colonne', () => {
    const { slots } = programLayout(3, W, H);
    const [a, b, c] = slots;
    if (!a || !b || !c) throw new Error('zones manquantes');
    expect(a.x + a.width).toBeGreaterThan(b.x);
    expect(b.x + b.width).toBeGreaterThan(c.x);
    expect(b.x + b.width / 2).toBeCloseTo(W / 2, 6);
  });

  it('un seul participant : centré, pas plus large que sa caméra naturelle', () => {
    const [slot] = programLayout(1, W, H).slots;
    if (!slot) throw new Error('zone manquante');
    expect(slot.width / slot.height).toBeCloseTo(16 / 9, 6);
    expect(slot.x + slot.width / 2).toBeCloseTo(W / 2, 6);
  });

  it('borne le nombre de participants entre 1 et le maximum', () => {
    expect(programLayout(0, W, H).slots).toHaveLength(1);
    expect(programLayout(-4, W, H).slots).toHaveLength(1);
    expect(programLayout(99, W, H).slots).toHaveLength(MAX_PARTICIPANTS);
    expect(programLayout(2.9, W, H).slots).toHaveLength(2);
  });

  it('les légendes restent dans le bandeau, au-dessus des barres de niveau', () => {
    const layout = programLayout(3, W, H);
    for (const caption of layout.captions) {
      expect(caption.name.y).toBeGreaterThanOrEqual(layout.panel.y);
      expect(caption.name.y + caption.name.height).toBeLessThanOrEqual(caption.levels.y);
      expect(caption.levels.y + caption.levels.height).toBeLessThanOrEqual(
        layout.panel.y + layout.panel.height,
      );
    }
  });

  it('s’adapte à une autre taille de canevas', () => {
    const small = programLayout(3, 960, 540);
    const big = programLayout(3, 1920, 1080);
    expect(small.panel.width * 2).toBeCloseTo(big.panel.width, 6);
    expect(small.slots[0]?.width ?? 0).toBeCloseTo((big.slots[0]?.width ?? 0) / 2, 6);
  });
});

describe('recadrage d’une caméra dans sa zone', () => {
  const camera = { width: 1920, height: 1080 };

  it('garde les proportions de la zone et centre sur le sujet', () => {
    const slot = { x: 0, y: 0, width: 704, height: 540 };
    const crop = cropForSlot(camera, slot);
    expect(crop.width / crop.height).toBeCloseTo(704 / 540, 6);
    expect(crop.height).toBe(1080);
    expect(crop.x + crop.width / 2).toBeCloseTo(960, 6);
  });

  it('un zoom agrandit le sujet (zone source plus petite) sans sortir de l’image', () => {
    const slot = { x: 0, y: 0, width: 704, height: 540 };
    const normal = cropForSlot(camera, slot, 1);
    const zoomed = cropForSlot(camera, slot, 1.5);
    expect(zoomed.width).toBeCloseTo(normal.width / 1.5, 6);
    expect(zoomed.y).toBeGreaterThan(0);
    expect(zoomed.y + zoomed.height).toBeLessThanOrEqual(1080 + 1e-6);
  });

  it('suit le sujet décalé mais reste dans l’image', () => {
    const slot = { x: 0, y: 0, width: 704, height: 540 };
    expect(cropForSlot(camera, slot, 1, 0).x).toBe(0);
    const right = cropForSlot(camera, slot, 1, 1);
    expect(right.x + right.width).toBeCloseTo(1920, 6);
    expect(cropForSlot(camera, slot, 1, 0.7).x).toBeGreaterThan(
      cropForSlot(camera, slot, 1, 0.4).x,
    );
  });

  it('une zone plus large que la caméra est rognée en hauteur plutôt que de dépasser', () => {
    const wide = { x: 0, y: 0, width: 2000, height: 500 };
    const crop = cropForSlot(camera, wide);
    expect(crop.width).toBe(1920);
    expect(crop.height).toBeCloseTo(480, 6);
    expect(crop.y).toBeGreaterThan(0);
  });

  it('un zoom inférieur à 1 est ramené à 1', () => {
    const slot = { x: 0, y: 0, width: 704, height: 540 };
    expect(cropForSlot(camera, slot, 0.2)).toEqual(cropForSlot(camera, slot, 1));
  });
});

describe('décor', () => {
  it('couvre le canevas sans déformer l’image et la centre', () => {
    const tall = coverRect({ width: 1000, height: 2000 }, { width: 1920, height: 1080 });
    expect(tall.width).toBeCloseTo(1920, 6);
    expect(tall.width / tall.height).toBeCloseTo(0.5, 6);
    expect(tall.y).toBeLessThan(0);
    const wide = coverRect({ width: 4000, height: 1000 }, { width: 1920, height: 1080 });
    expect(wide.height).toBeCloseTo(1080, 6);
    expect(wide.x).toBeLessThan(0);
    const same = coverRect({ width: 1920, height: 1080 }, { width: 1920, height: 1080 });
    expect(same).toEqual({ x: 0, y: 0, width: 1920, height: 1080 });
  });
});

describe('initiales et historique de niveau', () => {
  it.each([
    ['Lou Husson', 'LH'],
    ['camille', 'C'],
    ['  Jean   Pierre  Martin ', 'JM'],
    ['', '?'],
    ['   ', '?'],
    ['Éloïse Ünal', 'ÉÜ'],
  ])('%j donne %j', (name, expected) => {
    expect(initials(name)).toBe(expected);
  });

  it('garde les N derniers niveaux, bornés entre 0 et 1, sans valeur absurde', () => {
    const history = new LevelHistory(4);
    expect(history.bars).toEqual([0, 0, 0, 0]);
    for (const level of [0.2, 0.5, 2, -1, Number.NaN, 0.7]) history.push(level);
    expect(history.bars).toEqual([1, 0, 0, 0.7]);
    expect(history.bars).toHaveLength(4);
  });
});
