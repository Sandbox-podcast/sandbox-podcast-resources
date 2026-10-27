export const ROLES = ['ADMIN', 'PRODUCER', 'HOST', 'EDITOR', 'VIEWER'] as const;
export type Role = (typeof ROLES)[number];

export type Action =
  | 'podcast:read'
  | 'podcast:manage-members'
  | 'episode:read'
  | 'episode:create'
  | 'episode:edit-rundown'
  | 'episode:invite'
  | 'studio:join'
  | 'studio:control'
  | 'recording:control';

const MATRIX: Record<Action, readonly Role[]> = {
  'podcast:read': ['ADMIN', 'PRODUCER', 'HOST', 'EDITOR', 'VIEWER'],
  'podcast:manage-members': ['ADMIN'],
  'episode:read': ['ADMIN', 'PRODUCER', 'HOST', 'EDITOR', 'VIEWER'],
  'episode:create': ['ADMIN', 'PRODUCER'],
  'episode:edit-rundown': ['ADMIN', 'PRODUCER', 'HOST', 'EDITOR'],
  'episode:invite': ['ADMIN', 'PRODUCER'],
  'studio:join': ['ADMIN', 'PRODUCER', 'HOST'],
  'studio:control': ['ADMIN', 'PRODUCER'],
  'recording:control': ['ADMIN', 'PRODUCER'],
};

/** Qui peut quoi dans un podcast. Fonction pure : vérifiée par le serveur à chaque requête. */
export function can(role: Role | null | undefined, action: Action): boolean {
  return role !== null && role !== undefined && MATRIX[action].includes(role);
}

export const isRole = (value: unknown): value is Role =>
  typeof value === 'string' && (ROLES as readonly string[]).includes(value);
