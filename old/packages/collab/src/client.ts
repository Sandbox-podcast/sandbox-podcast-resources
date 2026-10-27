import * as decoding from 'lib0/decoding';
import * as encoding from 'lib0/encoding';
import { WebSocket } from 'ws';
import * as awarenessProtocol from 'y-protocols/awareness';
import * as syncProtocol from 'y-protocols/sync';
import * as Y from 'yjs';
import { MESSAGE_AWARENESS, MESSAGE_ERROR, MESSAGE_SYNC } from './protocol.ts';
import { CLOSE_REVOKED, CLOSE_UNAUTHORIZED } from './server.ts';

export type ClientStatus = 'connecting' | 'connected' | 'disconnected';

export interface CollabClientOptions {
  /** Adresse complète : `ws://hôte:port/collab/<document>?token=<jeton>`. */
  url: string;
  /** Délai avant une nouvelle tentative de connexion. */
  reconnectDelayMs?: number;
  /** Si faux, le client ne répond pas aux tests de vie du serveur (simule un réseau coupé en silence). */
  autoPong?: boolean;
}

/**
 * Client du serveur collaboratif. Les modifications faites hors ligne s'accumulent dans le
 * document local et sont envoyées à la reconnexion : le CRDT les fusionne sans perte.
 * Dans un navigateur, le même protocole fonctionne avec l'API WebSocket native.
 */
export class CollabClient {
  readonly doc = new Y.Doc();
  readonly awareness = new awarenessProtocol.Awareness(this.doc);
  status: ClientStatus = 'disconnected';
  /** Erreurs signalées par le serveur (par exemple READ_ONLY). */
  readonly serverErrors: string[] = [];
  /** Octets de modifications faites pendant la déconnexion, pas encore envoyées. */
  pendingOfflineBytes = 0;
  /** Dernier code de fermeture reçu du serveur. */
  closeCode: number | null = null;
  /** Nombre de synchronisations complètes (connexion initiale et reconnexions). */
  syncCount = 0;

  private readonly options: Required<CollabClientOptions>;
  private socket: WebSocket | null = null;
  private wanted = false;
  private retry: ReturnType<typeof setTimeout> | null = null;

  constructor(options: CollabClientOptions) {
    this.options = { reconnectDelayMs: 200, autoPong: true, ...options };
    this.doc.on('update', (update: Uint8Array, origin: unknown) => {
      if (origin === this) return;
      if (this.status === 'connected') this.sendUpdate(update);
      else this.pendingOfflineBytes += update.length;
    });
    this.awareness.on(
      'update',
      (
        { added, updated, removed }: { added: number[]; updated: number[]; removed: number[] },
        origin: unknown,
      ) => {
        if (origin === this || this.status !== 'connected') return;
        const encoder = encoding.createEncoder();
        encoding.writeVarUint(encoder, MESSAGE_AWARENESS);
        encoding.writeVarUint8Array(
          encoder,
          awarenessProtocol.encodeAwarenessUpdate(this.awareness, [
            ...added,
            ...updated,
            ...removed,
          ]),
        );
        this.send(encoding.toUint8Array(encoder));
      },
    );
  }

  connect(): void {
    this.wanted = true;
    this.open();
  }

  /** Ferme la connexion et ne la rétablit pas. */
  close(): void {
    this.wanted = false;
    if (this.retry) clearTimeout(this.retry);
    this.socket?.close();
    this.socket = null;
    this.clearRemotePresence();
    this.status = 'disconnected';
  }

  /** Ferme et libère le document et la présence (leur minuteur interne garderait le processus en vie). */
  destroy(): void {
    this.close();
    this.awareness.destroy();
    this.doc.destroy();
  }

  /** Simule une perte réseau : la connexion est coupée sans préavis, le client tente de se reconnecter. */
  dropConnection(): void {
    this.socket?.terminate();
  }

  /** Résout quand le client est connecté et synchronisé. */
  async whenSynced(timeoutMs = 5000): Promise<void> {
    const startedAt = Date.now();
    const target = this.syncCount + (this.status === 'connected' && this.syncCount > 0 ? 0 : 1);
    while (this.syncCount < target || this.status !== 'connected') {
      if (Date.now() - startedAt > timeoutMs) throw new Error('Délai de synchronisation dépassé');
      await new Promise((resolve) => setTimeout(resolve, 10));
    }
  }

  private open(): void {
    if (this.socket) return;
    this.status = 'connecting';
    const socket = new WebSocket(this.options.url, { autoPong: this.options.autoPong });
    socket.binaryType = 'nodebuffer';
    this.socket = socket;

    socket.on('open', () => {
      this.status = 'connected';
      const encoder = encoding.createEncoder();
      encoding.writeVarUint(encoder, MESSAGE_SYNC);
      syncProtocol.writeSyncStep1(encoder, this.doc);
      this.send(encoding.toUint8Array(encoder));
      if (this.awareness.getLocalState() !== null) {
        const awarenessEncoder = encoding.createEncoder();
        encoding.writeVarUint(awarenessEncoder, MESSAGE_AWARENESS);
        encoding.writeVarUint8Array(
          awarenessEncoder,
          awarenessProtocol.encodeAwarenessUpdate(this.awareness, [this.doc.clientID]),
        );
        this.send(encoding.toUint8Array(awarenessEncoder));
      }
    });
    socket.on('message', (data: Buffer) => {
      this.onMessage(new Uint8Array(data));
    });
    socket.on('close', (code: number) => {
      this.closeCode = code;
      this.socket = null;
      this.status = 'disconnected';
      this.clearRemotePresence();
      const fatal = code === CLOSE_UNAUTHORIZED || code === CLOSE_REVOKED;
      if (this.wanted && !fatal) {
        this.retry = setTimeout(() => {
          this.open();
        }, this.options.reconnectDelayMs);
      }
    });
    socket.on('error', () => {
      // La fermeture qui suit déclenche la reconnexion.
    });
  }

  private onMessage(data: Uint8Array): void {
    const decoder = decoding.createDecoder(data);
    const type = decoding.readVarUint(decoder);
    if (type === MESSAGE_SYNC) {
      const encoder = encoding.createEncoder();
      encoding.writeVarUint(encoder, MESSAGE_SYNC);
      const syncType = syncProtocol.readSyncMessage(decoder, encoder, this.doc, this);
      if (encoding.length(encoder) > 1) this.send(encoding.toUint8Array(encoder));
      if (syncType === syncProtocol.messageYjsSyncStep2) {
        this.pendingOfflineBytes = 0;
        this.syncCount += 1;
      }
    } else if (type === MESSAGE_AWARENESS) {
      awarenessProtocol.applyAwarenessUpdate(
        this.awareness,
        decoding.readVarUint8Array(decoder),
        this,
      );
    } else if (type === MESSAGE_ERROR) {
      this.serverErrors.push(decoding.readVarString(decoder));
    }
  }

  private sendUpdate(update: Uint8Array): void {
    const encoder = encoding.createEncoder();
    encoding.writeVarUint(encoder, MESSAGE_SYNC);
    syncProtocol.writeUpdate(encoder, update);
    this.send(encoding.toUint8Array(encoder));
  }

  private send(message: Uint8Array): void {
    if (this.socket?.readyState === WebSocket.OPEN) this.socket.send(message);
  }

  /** Efface les présences des autres : sans connexion, on ne sait plus qui est là. */
  private clearRemotePresence(): void {
    const others = [...this.awareness.getStates().keys()].filter((id) => id !== this.doc.clientID);
    if (others.length > 0) awarenessProtocol.removeAwarenessStates(this.awareness, others, this);
  }
}
