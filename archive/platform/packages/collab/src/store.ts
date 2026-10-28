/** Version nommée d'un document : un instantané complet de l'état Yjs. */
export interface DocumentVersion {
  id: string;
  label: string;
  createdAtMs: number;
  createdBy: string;
  /** État Yjs complet (`Y.encodeStateAsUpdate`). */
  state: Uint8Array;
}

/**
 * Persistance des documents collaboratifs. En production : PostgreSQL (état courant, historique).
 * L'état courant est sauvegardé automatiquement ; les versions sont des instantanés nommés.
 */
export interface DocumentStore {
  load(docId: string): Promise<Uint8Array | null>;
  save(docId: string, state: Uint8Array): Promise<void>;
  addVersion(docId: string, version: DocumentVersion): Promise<void>;
  versions(docId: string): Promise<DocumentVersion[]>;
}

export class InMemoryDocumentStore implements DocumentStore {
  private readonly states = new Map<string, Uint8Array>();
  private readonly history = new Map<string, DocumentVersion[]>();
  /** Nombre d'écritures de l'état courant, utile aux tests d'autosave. */
  saves = 0;

  load(docId: string): Promise<Uint8Array | null> {
    return Promise.resolve(this.states.get(docId) ?? null);
  }

  save(docId: string, state: Uint8Array): Promise<void> {
    this.saves += 1;
    this.states.set(docId, state);
    return Promise.resolve();
  }

  addVersion(docId: string, version: DocumentVersion): Promise<void> {
    this.history.set(docId, [...(this.history.get(docId) ?? []), version]);
    return Promise.resolve();
  }

  versions(docId: string): Promise<DocumentVersion[]> {
    return Promise.resolve(this.history.get(docId) ?? []);
  }
}
