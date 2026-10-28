/**
 * Grille des vidéos de la salle. Gère uniquement la structure (une vignette par participant, une piste audio par
 * abonnement) ; les éléments média eux-mêmes viennent de LiveKit. Indépendant du DOM réel pour être testable :
 * `Doc` et `El` ne décrivent que ce dont on a besoin.
 */
export interface El {
  className: string;
  textContent: string | null;
  append(...children: El[]): void;
  remove(): void;
}
export interface Doc {
  createElement(tag: 'figure' | 'figcaption'): El;
}

interface Tile {
  figure: El;
  video: El | null;
}

export class TileGrid {
  private readonly root: El;
  private readonly doc: Doc;
  private readonly tiles = new Map<string, Tile>();
  private readonly audios = new Map<string, El>();

  constructor(root: El, doc: Doc) {
    this.root = root;
    this.doc = doc;
  }

  /** Nombre de vignettes (un participant sans vidéo a quand même une vignette avec son nom). */
  get size(): number {
    return this.tiles.size;
  }

  private tile(participantId: string, name: string, local: boolean): Tile {
    const existing = this.tiles.get(participantId);
    if (existing) return existing;
    const figure = this.doc.createElement('figure');
    figure.className = local ? 'tile local' : 'tile';
    const caption = this.doc.createElement('figcaption');
    // Le nom vient du serveur : texte brut, jamais du balisage.
    caption.textContent = local ? `${name} (vous)` : name;
    figure.append(caption);
    this.root.append(figure);
    const created: Tile = { figure, video: null };
    this.tiles.set(participantId, created);
    return created;
  }

  /** Affiche (ou remplace) la vidéo d'un participant. */
  setVideo(participantId: string, name: string, video: El, local: boolean): void {
    const tile = this.tile(participantId, name, local);
    tile.video?.remove();
    tile.figure.append(video);
    tile.video = video;
  }

  /** Retire la vidéo d'un participant (caméra coupée) mais garde sa vignette. */
  removeVideo(participantId: string): void {
    const tile = this.tiles.get(participantId);
    tile?.video?.remove();
    if (tile) tile.video = null;
  }

  /** Vignette sans vidéo (participant connecté, caméra pas encore reçue). */
  ensure(participantId: string, name: string, local: boolean): void {
    this.tile(participantId, name, local);
  }

  /** Piste audio d'un participant distant : attachée pour être entendue, jamais pour soi-même (écho). */
  addAudio(trackId: string, audio: El): void {
    this.audios.get(trackId)?.remove();
    this.audios.set(trackId, audio);
    this.root.append(audio);
  }

  removeAudio(trackId: string): void {
    this.audios.get(trackId)?.remove();
    this.audios.delete(trackId);
  }

  removeParticipant(participantId: string): void {
    const tile = this.tiles.get(participantId);
    tile?.figure.remove();
    this.tiles.delete(participantId);
  }

  clear(): void {
    for (const tile of this.tiles.values()) tile.figure.remove();
    for (const audio of this.audios.values()) audio.remove();
    this.tiles.clear();
    this.audios.clear();
  }
}
