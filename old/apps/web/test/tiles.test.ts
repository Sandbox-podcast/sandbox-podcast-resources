import { describe, expect, it } from 'vitest';
import { initialState } from '../src/state.ts';
import { TileGrid, type Doc, type El } from '../src/tiles.ts';
import { renderApp } from '../src/views.ts';

class FakeEl implements El {
  className = '';
  textContent: string | null = null;
  children: FakeEl[] = [];
  parent: FakeEl | null = null;
  readonly tag: string;

  constructor(tag: string) {
    this.tag = tag;
  }

  append(...children: El[]): void {
    for (const child of children as FakeEl[]) {
      child.remove();
      child.parent = this;
      this.children.push(child);
    }
  }

  remove(): void {
    if (!this.parent) return;
    this.parent.children = this.parent.children.filter((c) => c !== this);
    this.parent = null;
  }
}

const doc: Doc = { createElement: (tag) => new FakeEl(tag) };
const setup = () => {
  const root = new FakeEl('div');
  return { root, grid: new TileGrid(root, doc) };
};
const names = (root: FakeEl): (string | null)[] =>
  root.children.filter((c) => c.tag === 'figure').map((f) => f.children[0]?.textContent ?? null);

describe('grille des vidéos', () => {
  it('une vignette par participant, avec son nom en texte brut, la sienne marquée « vous »', () => {
    const { root, grid } = setup();
    grid.ensure('moi', 'Lou', true);
    grid.ensure('lui', '<b>Camille</b>', false);
    grid.ensure('lui', '<b>Camille</b>', false);
    expect(grid.size).toBe(2);
    expect(names(root)).toEqual(['Lou (vous)', '<b>Camille</b>']);
    expect(root.children[0]?.className).toBe('tile local');
    expect(root.children[1]?.className).toBe('tile');
  });

  it('affiche la vidéo dans la vignette, la remplace sans doublon, la retire sans retirer le participant', () => {
    const { root, grid } = setup();
    const first = new FakeEl('video');
    const second = new FakeEl('video');
    grid.setVideo('lui', 'Camille', first, false);
    expect(grid.size).toBe(1);
    expect(root.children[0]?.children).toContain(first);
    grid.setVideo('lui', 'Camille', second, false);
    expect(root.children[0]?.children).not.toContain(first);
    expect(root.children[0]?.children).toContain(second);
    expect(root.children[0]?.children.filter((c) => c.tag === 'video')).toHaveLength(1);
    grid.removeVideo('lui');
    expect(root.children[0]?.children.some((c) => c.tag === 'video')).toBe(false);
    expect(grid.size).toBe(1);
  });

  it('retirer la vidéo d’un participant inconnu ne fait rien', () => {
    const { grid } = setup();
    expect(() => {
      grid.removeVideo('inconnu');
      grid.removeParticipant('inconnu');
      grid.removeAudio('inconnue');
    }).not.toThrow();
  });

  it('les pistes audio sont attachées, remplacées par identifiant, et retirées', () => {
    const { root, grid } = setup();
    const a1 = new FakeEl('audio');
    const a2 = new FakeEl('audio');
    grid.addAudio('piste-1', a1);
    grid.addAudio('piste-1', a2);
    expect(root.children).not.toContain(a1);
    expect(root.children).toContain(a2);
    grid.removeAudio('piste-1');
    expect(root.children).not.toContain(a2);
  });

  it('retirer un participant enlève sa vignette ; tout effacer vide la grille', () => {
    const { root, grid } = setup();
    grid.ensure('a', 'A', false);
    grid.ensure('b', 'B', false);
    grid.addAudio('t', new FakeEl('audio'));
    grid.removeParticipant('a');
    expect(names(root)).toEqual(['B']);
    grid.clear();
    expect(root.children).toEqual([]);
    expect(grid.size).toBe(0);
  });
});

describe('emplacement des vidéos dans les pages', () => {
  const state = initialState();
  it('le studio et la page invité réservent l’emplacement, pas les autres pages', () => {
    const podcasts = { status: 'ready' as const, data: [{ id: 'p', name: 'P', role: 'PRODUCER' }] };
    const user = { id: 'u', email: 'u@x.fr', displayName: 'Lou' };
    const studio = renderApp({
      ...state,
      user,
      podcasts,
      route: { name: 'studio', podcastId: 'p', episodeId: 'e' },
    }).toString();
    expect(studio).toContain('id="media-slot"');
    const guest = renderApp({
      ...state,
      user: null,
      route: { name: 'guest', token: 'a'.repeat(43) },
      guest: {
        ...state.guest,
        info: {
          status: 'ready',
          data: {
            podcastName: 'P',
            episodeTitle: 'E',
            role: 'GUEST',
            displayName: null,
            expiresAt: 'x',
          },
        },
      },
    }).toString();
    expect(guest).toContain('id="media-slot"');
    expect(
      renderApp({ ...state, user, podcasts, route: { name: 'home' } }).toString(),
    ).not.toContain('media-slot');
  });
});
