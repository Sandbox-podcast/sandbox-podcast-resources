import { z } from 'zod';

/** État de l'envoi d'un chunk vers le serveur. */
export const UPLOAD_STATUSES = [
  'NOT_UPLOADED',
  'UPLOADING',
  /** Octets reçus par le serveur, checksum pas encore confirmé. */
  'UPLOADED',
  /** Le serveur a recalculé le checksum et il correspond. */
  'VERIFIED',
  /** Le serveur a refusé le chunk (checksum différent, chunk invalide). */
  'REJECTED',
] as const;

/** Où se trouve la copie locale du chunk côté navigateur. */
export const LOCAL_COPIES = [
  'NONE',
  /** En mémoire seulement : perdu si l'onglet plante. */
  'MEMORY',
  /** Écrite dans un stockage persistant (ex. OPFS) et confirmée. */
  'DURABLE',
] as const;

export type UploadStatus = (typeof UPLOAD_STATUSES)[number];
export type LocalCopy = (typeof LOCAL_COPIES)[number];

/**
 * Métadonnées d'un chunk d'enregistrement (master prompt §17.2).
 * Les horodatages sont en millisecondes sur l'horloge de session.
 * `durationMs` est la durée média du chunk ; elle peut différer légèrement de
 * `endTimestampMs - startTimestampMs`.
 */
export const chunkMetadataSchema = z
  .strictObject({
    recordingSessionId: z.string().min(1),
    participantId: z.string().min(1),
    trackId: z.string().min(1),
    sequenceNumber: z.number().int().nonnegative(),
    startTimestampMs: z.number().int().nonnegative(),
    endTimestampMs: z.number().int().nonnegative(),
    durationMs: z.number().int().nonnegative(),
    codec: z.string().min(1),
    container: z.string().min(1),
    sizeBytes: z.number().int().nonnegative(),
    checksum: z.string().regex(/^[0-9a-f]{64}$/, 'SHA-256 hexadécimal minuscule attendu'),
    uploadStatus: z.enum(UPLOAD_STATUSES),
    localCopy: z.enum(LOCAL_COPIES),
  })
  .refine((chunk) => chunk.endTimestampMs >= chunk.startTimestampMs, {
    message: 'endTimestampMs doit être supérieur ou égal à startTimestampMs',
    path: ['endTimestampMs'],
  });

export type ChunkMetadata = z.infer<typeof chunkMetadataSchema>;
