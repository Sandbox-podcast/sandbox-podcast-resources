import * as decoding from 'lib0/decoding';

/** Types de messages du protocole y-websocket. */
export const MESSAGE_SYNC = 0;
export const MESSAGE_AWARENESS = 1;
/** Message propre à ce serveur : notification d'erreur à un client. */
export const MESSAGE_ERROR = 100;

/** Sous-types des messages de synchronisation (y-protocols/sync). */
export const SYNC_STEP1 = 0;
export const SYNC_STEP2 = 1;
export const SYNC_UPDATE = 2;

export interface PeekedMessage {
  type: number;
  /** Pour un message de synchronisation, son sous-type. */
  syncType: number | null;
}

/** Lit le type d'un message sans le consommer, pour décider s'il est autorisé. */
export function peekMessage(data: Uint8Array): PeekedMessage | null {
  try {
    const decoder = decoding.createDecoder(data);
    const type = decoding.readVarUint(decoder);
    const syncType = type === MESSAGE_SYNC ? decoding.readVarUint(decoder) : null;
    return { type, syncType };
  } catch {
    return null;
  }
}

/** Un message de synchronisation qui modifie le document (et pas une simple demande d'état). */
export function isWriteMessage(message: PeekedMessage): boolean {
  return (
    message.type === MESSAGE_SYNC &&
    (message.syncType === SYNC_STEP2 || message.syncType === SYNC_UPDATE)
  );
}
