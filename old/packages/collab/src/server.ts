import type { IncomingMessage } from 'node:http';
import * as decoding from 'lib0/decoding';
import * as encoding from 'lib0/encoding';
import { WebSocketServer, type RawData, type WebSocket } from 'ws';
import * as awarenessProtocol from 'y-protocols/awareness';
import * as syncProtocol from 'y-protocols/sync';
import * as Y from 'yjs';
import {
  MESSAGE_AWARENESS,
  MESSAGE_ERROR,
  MESSAGE_SYNC,
  isWriteMessage,
  peekMessage,
} from './protocol.ts';
import type { DocumentStore } from './store.ts';

export type Access = 'read' | 'write';

export interface Authorization {
  userId: string;
  access: Access;
}

/**
 * Décide si un jeton donne accès à un document. Appelé à chaque connexion, et le serveur
 * revérifie les droits à chaque message : le client n'est jamais une frontière de sécurité.
 */
export type Authorize = (
  token: string,
  docId: string,
) => Authorization | null | Promise<Authorization | null>;

/** Codes de fermeture WebSocket propres à ce serveur. */
export const CLOSE_UNAUTHORIZED = 4401;
export const CLOSE_REVOKED = 4403;

export interface CollabServerOptions {
  authorize: Authorize;
  store: DocumentStore;
  /** Intervalle du test de vie des connexions. Une connexion muette est coupée au bout de deux intervalles. */
  pingIntervalMs?: number;
  /** Délai d'attente après la dernière modification avant la sauvegarde automatique. */
  autosaveMs?: number;
  /** Taille maximale d'un message WebSocket, en octets (1 Mio par défaut ; la bibliothèque autorise 100 Mio). */
  maxPayloadBytes?: number;
  /**
   * Origines autorisées. Un navigateur envoie toujours `Origin` : s'il est présent et absent de la liste, la connexion est
   * refusée (détournement de WebSocket depuis une autre page). Un client sans `Origin` (serveur, test) n'est pas concerné.
   * Absent : aucun contrôle d'origine.
   */
  allowedOrigins?: readonly string[];
}

interface Connection {
  docId: string;
  socket: WebSocket;
  userId: string;
  access: Access;
  alive: boolean;
  awarenessIds: Set<number>;
}

interface Room {
  doc: Y.Doc;
  awareness: awarenessProtocol.Awareness;
  connections: Set<Connection>;
  saveTimer: ReturnType<typeof setTimeout> | null;
  dirty: boolean;
}

const bytes = (data: RawData): Uint8Array => {
  if (Array.isArray(data)) return new Uint8Array(Buffer.concat(data));
  return new Uint8Array(data instanceof ArrayBuffer ? data : data);
};

export class CollabServer {
  private readonly options: Required<CollabServerOptions>;
  private readonly rooms = new Map<string, Promise<Room>>();
  private readonly originCheck: boolean;
  private wss: WebSocketServer | null = null;
  private heartbeat: ReturnType<typeof setInterval> | null = null;
  /** Écritures refusées faute de droit, par document, pour l'audit. */
  readonly rejectedWrites = new Map<string, number>();
  /** Connexions refusées pour cause d'origine non autorisée, pour l'audit. */
  rejectedOrigins = 0;
  readonly errors: Error[] = [];

  constructor(options: CollabServerOptions) {
    this.options = {
      pingIntervalMs: 10_000,
      autosaveMs: 2000,
      maxPayloadBytes: 1024 * 1024,
      allowedOrigins: [],
      ...options,
    };
    this.originCheck = options.allowedOrigins !== undefined;
  }

  /** Démarre l'écoute (port 0 : port libre) et retourne le port. */
  async listen(port = 0): Promise<number> {
    const wss = new WebSocketServer({
      host: '127.0.0.1',
      port,
      maxPayload: this.options.maxPayloadBytes,
    });
    this.wss = wss;
    wss.on('connection', (socket, request) => {
      void this.accept(socket, request);
    });
    await new Promise<void>((resolve) => wss.once('listening', resolve));
    this.heartbeat = setInterval(() => {
      this.pingAll();
    }, this.options.pingIntervalMs);
    const address = wss.address();
    return typeof address === 'object' && address !== null ? address.port : port;
  }

  async close(): Promise<void> {
    if (this.heartbeat) clearInterval(this.heartbeat);
    await this.flush();
    for (const socket of this.wss?.clients ?? []) socket.terminate();
    for (const promise of this.rooms.values()) this.destroy(await promise);
    this.rooms.clear();
    await new Promise<void>((resolve) => {
      if (this.wss)
        this.wss.close(() => {
          resolve();
        });
      else resolve();
    });
  }

  /** Le document, chargé depuis le stockage au besoin. Pour les lectures côté serveur et les tests. */
  async document(docId: string): Promise<Y.Doc> {
    return (await this.room(docId)).doc;
  }

  connectionCount(docId: string): Promise<number> {
    return this.room(docId).then((room) => room.connections.size);
  }

  /** Utilisateurs présents (connexion ouverte) sur un document. */
  async presentUsers(docId: string): Promise<string[]> {
    const room = await this.room(docId);
    return [...new Set([...room.connections].map((c) => c.userId))].sort();
  }

  /**
   * Change ou retire les droits d'un utilisateur sur un document, sans qu'il ait à se reconnecter.
   * `null` retire l'accès : ses connexions sont fermées.
   */
  async setAccess(docId: string, userId: string, access: Access | null): Promise<void> {
    const room = await this.room(docId);
    for (const connection of room.connections) {
      if (connection.userId !== userId) continue;
      if (access === null) connection.socket.close(CLOSE_REVOKED, 'accès retiré');
      else connection.access = access;
    }
  }

  /** Sauvegarde immédiatement tous les documents modifiés. */
  async flush(): Promise<void> {
    const rooms = await Promise.all(this.rooms.values());
    await Promise.all(rooms.filter((room) => room.dirty).map((room) => this.save(room)));
  }

  /** Enregistre un instantané nommé, sans toucher à l'historique existant. */
  async createVersion(docId: string, label: string, userId: string): Promise<string> {
    const room = await this.room(docId);
    const id = `v${String((await this.options.store.versions(docId)).length + 1)}`;
    await this.options.store.addVersion(docId, {
      id,
      label,
      createdAtMs: Date.now(),
      createdBy: userId,
      state: Y.encodeStateAsUpdate(room.doc),
    });
    return id;
  }

  /**
   * Restaure une version : le contenu actuel est remplacé par celui de la version, comme une
   * nouvelle modification. L'historique n'est jamais effacé : on enregistre en plus une version
   * « avant restauration » et une version « restauration ».
   * `schema` indique le type des éléments partagés à restaurer.
   */
  async restoreVersion(
    docId: string,
    versionId: string,
    userId: string,
    schema: Readonly<Record<string, 'text' | 'map' | 'array'>>,
  ): Promise<string> {
    const version = (await this.options.store.versions(docId)).find((v) => v.id === versionId);
    if (!version) throw new Error(`Version inconnue : ${versionId}`);
    const room = await this.room(docId);
    await this.createVersion(docId, `avant restauration de ${version.label}`, userId);

    const old = new Y.Doc();
    Y.applyUpdate(old, version.state);
    room.doc.transact(() => {
      for (const [name, kind] of Object.entries(schema)) {
        if (kind === 'text') {
          const live = room.doc.getText(name);
          live.delete(0, live.length);
          live.insert(0, old.getText(name).toJSON());
        } else if (kind === 'map') {
          const live = room.doc.getMap<unknown>(name);
          for (const key of [...live.keys()]) live.delete(key);
          for (const [key, value] of old.getMap<unknown>(name).entries()) live.set(key, value);
        } else {
          const live = room.doc.getArray<unknown>(name);
          live.delete(0, live.length);
          live.push(old.getArray<unknown>(name).toArray());
        }
      }
    }, `restore:${userId}`);
    return this.createVersion(docId, `restauration de ${version.label}`, userId);
  }

  private room(docId: string): Promise<Room> {
    let promise = this.rooms.get(docId);
    if (!promise) {
      promise = this.loadRoom(docId);
      this.rooms.set(docId, promise);
    }
    return promise;
  }

  private async loadRoom(docId: string): Promise<Room> {
    const doc = new Y.Doc();
    const stored = await this.options.store.load(docId);
    if (stored) Y.applyUpdate(doc, stored);
    const awareness = new awarenessProtocol.Awareness(doc);
    awareness.setLocalState(null);
    const room: Room = { doc, awareness, connections: new Set(), saveTimer: null, dirty: false };

    doc.on('update', (update: Uint8Array, origin: unknown) => {
      room.dirty = true;
      this.scheduleSave(room, docId);
      const encoder = encoding.createEncoder();
      encoding.writeVarUint(encoder, MESSAGE_SYNC);
      syncProtocol.writeUpdate(encoder, update);
      const message = encoding.toUint8Array(encoder);
      for (const connection of room.connections) {
        if (connection !== origin) this.send(connection.socket, message);
      }
    });

    awareness.on(
      'update',
      (
        { added, updated, removed }: { added: number[]; updated: number[]; removed: number[] },
        origin: unknown,
      ) => {
        const changed = [...added, ...updated, ...removed];
        if (origin instanceof Object && 'awarenessIds' in origin) {
          const owner = origin as Connection;
          for (const id of added) owner.awarenessIds.add(id);
          for (const id of removed) owner.awarenessIds.delete(id);
        }
        const encoder = encoding.createEncoder();
        encoding.writeVarUint(encoder, MESSAGE_AWARENESS);
        encoding.writeVarUint8Array(
          encoder,
          awarenessProtocol.encodeAwarenessUpdate(awareness, changed),
        );
        const message = encoding.toUint8Array(encoder);
        for (const connection of room.connections) this.send(connection.socket, message);
      },
    );
    return room;
  }

  private async accept(socket: WebSocket, request: IncomingMessage): Promise<void> {
    // Les messages qui arrivent pendant l'autorisation sont mis en file : rien n'est perdu ni traité trop tôt.
    const queued: Uint8Array[] = [];
    let connection: Connection | null = null;
    let room: Room | null = null;
    socket.on('message', (data: RawData) => {
      const payload = bytes(data);
      if (connection && room) this.onMessage(room, connection, payload);
      else queued.push(payload);
    });

    const origin = request.headers.origin;
    if (this.originCheck && origin !== undefined && !this.options.allowedOrigins.includes(origin)) {
      this.rejectedOrigins += 1;
      socket.close(CLOSE_UNAUTHORIZED, 'origine non autorisée');
      return;
    }
    const url = new URL(request.url ?? '/', 'http://localhost');
    const docId = decodeURIComponent(url.pathname.replace(/^\/collab\//, ''));
    const token = url.searchParams.get('token') ?? '';
    let authorization: Authorization | null = null;
    try {
      authorization = docId.length > 0 ? await this.options.authorize(token, docId) : null;
    } catch (error) {
      this.errors.push(error instanceof Error ? error : new Error(String(error)));
    }
    if (!authorization) {
      socket.close(CLOSE_UNAUTHORIZED, 'non autorisé');
      return;
    }

    const joined = await this.room(docId);
    const mine: Connection = {
      docId,
      socket,
      userId: authorization.userId,
      access: authorization.access,
      alive: true,
      awarenessIds: new Set(),
    };
    connection = mine;
    room = joined;
    joined.connections.add(mine);

    socket.on('pong', () => {
      mine.alive = true;
    });
    socket.on('close', () => {
      this.onClose(joined, mine, docId);
    });
    socket.on('error', (error: Error) => {
      this.errors.push(error);
    });

    // Poignée de main : l'état du serveur, puis la présence des autres.
    const hello = encoding.createEncoder();
    encoding.writeVarUint(hello, MESSAGE_SYNC);
    syncProtocol.writeSyncStep1(hello, joined.doc);
    this.send(socket, encoding.toUint8Array(hello));
    const states = joined.awareness.getStates();
    if (states.size > 0) {
      const encoder = encoding.createEncoder();
      encoding.writeVarUint(encoder, MESSAGE_AWARENESS);
      encoding.writeVarUint8Array(
        encoder,
        awarenessProtocol.encodeAwarenessUpdate(joined.awareness, [...states.keys()]),
      );
      this.send(socket, encoding.toUint8Array(encoder));
    }
    for (const payload of queued) this.onMessage(joined, mine, payload);
  }

  private onMessage(room: Room, connection: Connection, data: Uint8Array): void {
    const peeked = peekMessage(data);
    if (!peeked) return;

    // Les droits sont revérifiés à chaque message : une révocation s'applique immédiatement.
    if (isWriteMessage(peeked) && connection.access !== 'write') {
      this.reject(connection, 'READ_ONLY');
      return;
    }

    const decoder = decoding.createDecoder(data);
    const type = decoding.readVarUint(decoder);
    if (type === MESSAGE_SYNC) {
      const encoder = encoding.createEncoder();
      encoding.writeVarUint(encoder, MESSAGE_SYNC);
      syncProtocol.readSyncMessage(decoder, encoder, room.doc, connection);
      if (encoding.length(encoder) > 1)
        this.send(connection.socket, encoding.toUint8Array(encoder));
    } else if (type === MESSAGE_AWARENESS) {
      awarenessProtocol.applyAwarenessUpdate(
        room.awareness,
        decoding.readVarUint8Array(decoder),
        connection,
      );
    }
  }

  private reject(connection: Connection, code: string): void {
    this.rejectedWrites.set(connection.docId, (this.rejectedWrites.get(connection.docId) ?? 0) + 1);
    const encoder = encoding.createEncoder();
    encoding.writeVarUint(encoder, MESSAGE_ERROR);
    encoding.writeVarString(encoder, code);
    this.send(connection.socket, encoding.toUint8Array(encoder));
  }

  private onClose(room: Room, connection: Connection, docId: string): void {
    room.connections.delete(connection);
    if (connection.awarenessIds.size > 0) {
      awarenessProtocol.removeAwarenessStates(room.awareness, [...connection.awarenessIds], null);
    }
    if (room.connections.size === 0) void this.unloadIfEmpty(docId, room).catch(this.recordError);
  }

  /**
   * Décharge un document que plus personne n'édite : sauvegarde, puis libère la mémoire et le
   * minuteur interne de la présence. Sans cela, chaque document ouvert resterait en mémoire.
   */
  private async unloadIfEmpty(docId: string, room: Room): Promise<void> {
    if (room.saveTimer) clearTimeout(room.saveTimer);
    room.saveTimer = null;
    if (room.dirty) await this.save(room, docId);
    if (room.connections.size > 0 || this.rooms.get(docId) === undefined) return;
    this.rooms.delete(docId);
    this.destroy(room);
  }

  private destroy(room: Room): void {
    if (room.saveTimer) clearTimeout(room.saveTimer);
    room.awareness.destroy();
    room.doc.destroy();
  }

  private send(socket: WebSocket, message: Uint8Array): void {
    if (socket.readyState === 1) socket.send(message);
  }

  private scheduleSave(room: Room, docId: string): void {
    if (room.saveTimer) clearTimeout(room.saveTimer);
    room.saveTimer = setTimeout(() => {
      room.saveTimer = null;
      void this.save(room, docId).catch(this.recordError);
    }, this.options.autosaveMs);
  }

  private async save(room: Room, docId?: string): Promise<void> {
    const id = docId ?? (await this.idOf(room));
    room.dirty = false;
    await this.options.store.save(id, Y.encodeStateAsUpdate(room.doc));
  }

  private async idOf(room: Room): Promise<string> {
    for (const [id, promise] of this.rooms) if ((await promise) === room) return id;
    throw new Error('Document inconnu');
  }

  private readonly recordError = (error: unknown): void => {
    this.errors.push(error instanceof Error ? error : new Error(String(error)));
  };

  private pingAll(): void {
    for (const promise of this.rooms.values()) {
      void promise.then((room) => {
        for (const connection of room.connections) {
          if (!connection.alive) {
            connection.socket.terminate();
            continue;
          }
          connection.alive = false;
          connection.socket.ping();
        }
      });
    }
  }
}
