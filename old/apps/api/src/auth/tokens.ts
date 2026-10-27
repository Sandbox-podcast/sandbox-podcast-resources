import { createHash, randomBytes } from 'node:crypto';

/** Jeton opaque de 256 bits. Seule son empreinte est stockée : une fuite de la base ne donne pas de sessions. */
export const newToken = (): string => randomBytes(32).toString('base64url');
export const hashToken = (token: string): string =>
  createHash('sha256').update(token).digest('hex');

/** Forme attendue d'un jeton : on refuse tout le reste avant d'interroger la base. */
export const isTokenShape = (value: unknown): value is string =>
  typeof value === 'string' && /^[A-Za-z0-9_-]{43}$/.test(value);
