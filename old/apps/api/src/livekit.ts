import { AccessToken } from 'livekit-server-sdk';
import type { Config } from './config.ts';

export type RoomRole = 'ADMIN' | 'PRODUCER' | 'HOST' | 'GUEST';

/** Nom de la salle d'un épisode : dérivé de l'identifiant (UUID), jamais de texte libre. */
export const roomName = (episodeId: string): string => `ep-${episodeId}`;

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

/** Retire tout caractère de contrôle et borne la longueur : un nom affiché ne sert jamais dans un chemin. */
export function cleanDisplayName(name: string): string {
  let kept = '';
  for (let i = 0; i < name.length; i += 1) {
    const code = name.charCodeAt(i);
    if (code > 31 && code !== 127) kept += name.charAt(i);
  }
  return kept.trim().slice(0, 120);
}

export interface RoomTokenInput {
  episodeId: string;
  /** Identifiant de la ligne `participants` : l'identité LiveKit est attribuée par le serveur. */
  participantId: string;
  displayName: string;
  role: RoomRole;
}

/**
 * Jeton de salle signé par le serveur : durée courte, une seule salle, droits selon le rôle. Les identités
 * doivent être des UUID (elles entrent dans le chemin des fichiers d'enregistrement).
 */
export async function issueRoomToken(
  config: Config,
  input: RoomTokenInput,
  ttlSeconds = 2 * 3600,
): Promise<string> {
  if (!config.LIVEKIT_API_KEY || !config.LIVEKIT_API_SECRET)
    throw new Error('LiveKit non configuré');
  if (!UUID.test(input.participantId) || !UUID.test(input.episodeId))
    throw new Error("identité de participant ou d'épisode invalide");
  const token = new AccessToken(config.LIVEKIT_API_KEY, config.LIVEKIT_API_SECRET, {
    identity: input.participantId,
    name: cleanDisplayName(input.displayName),
    ttl: ttlSeconds,
    metadata: JSON.stringify({ role: input.role }),
  });
  token.addGrant({
    room: roomName(input.episodeId),
    roomJoin: true,
    canPublish: true,
    canSubscribe: true,
    canPublishData: input.role !== 'GUEST',
    // Seuls les rôles de régie administrent la salle (hors enregistrement, géré par le serveur).
    roomAdmin: false,
    hidden: false,
  });
  return token.toJwt();
}
