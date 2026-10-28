import { isUniqueViolation, type Pool } from '../db/db.ts';
import {
  DEFAULT_COST,
  hashPassword,
  passwordProblems,
  verifyPassword,
  type ScryptCost,
} from '../auth/password.ts';
import { hashToken, newToken } from '../auth/tokens.ts';

export interface AuthOptions {
  cost: ScryptCost;
  sessionTtlHours: number;
  maxFailures: number;
  lockMinutes: number;
}

export const DEFAULT_AUTH: AuthOptions = {
  cost: DEFAULT_COST,
  sessionTtlHours: 24 * 7,
  maxFailures: 5,
  lockMinutes: 15,
};

export interface User {
  id: string;
  email: string;
  displayName: string;
}

export const normalizeEmail = (email: string): string => email.trim().toLowerCase();

export type CreateUserResult =
  | { ok: true; user: User }
  | { ok: false; reason: 'WEAK_PASSWORD'; problems: string[] }
  | { ok: false; reason: 'INVALID_EMAIL' | 'EMAIL_TAKEN' };

export async function createUser(
  pool: Pool,
  input: { email: string; displayName: string; password: string },
  options: AuthOptions = DEFAULT_AUTH,
): Promise<CreateUserResult> {
  const email = normalizeEmail(input.email);
  if (!/^[^@\s]+@[^@\s]+$/.test(email) || email.length > 254)
    return { ok: false, reason: 'INVALID_EMAIL' };
  const problems = passwordProblems(input.password, email);
  if (problems.length > 0) return { ok: false, reason: 'WEAK_PASSWORD', problems };
  const hash = await hashPassword(input.password, options.cost);
  try {
    const { rows } = await pool.query<{ id: string }>(
      'insert into users (email, display_name, password_hash) values ($1, $2, $3) returning id',
      [email, input.displayName.trim(), hash],
    );
    const id = rows[0]?.id;
    if (!id) throw new Error('insertion sans identifiant');
    return { ok: true, user: { id, email, displayName: input.displayName.trim() } };
  } catch (error) {
    if (isUniqueViolation(error)) return { ok: false, reason: 'EMAIL_TAKEN' };
    throw error;
  }
}

export type LoginResult =
  | { ok: true; user: User; token: string; expiresAt: Date }
  | { ok: false; reason: 'INVALID_CREDENTIALS' }
  | { ok: false; reason: 'LOCKED'; until: Date };

// Hachage factice : un compte inconnu coûte le même temps de calcul qu'un compte connu.
let dummyHash: Promise<string> | null = null;
const getDummyHash = (cost: ScryptCost): Promise<string> =>
  (dummyHash ??= hashPassword('mot-de-passe-factice', cost));

/**
 * Connexion. Un compte inconnu, désactivé ou un mauvais mot de passe donnent la même réponse. Les échecs sont
 * comptés par adresse e-mail (même inconnue, pour ne rien révéler) ; après `maxFailures`, le compte est verrouillé
 * `lockMinutes` minutes, doublé à chaque nouvel échec pendant le verrouillage, plafonné à 24 h.
 */
export async function login(
  pool: Pool,
  input: { email: string; password: string },
  now: Date,
  options: AuthOptions = DEFAULT_AUTH,
): Promise<LoginResult> {
  const email = normalizeEmail(input.email);
  const failureRow = await pool.query<{ failures: number; locked_until: Date | null }>(
    'select failures, locked_until from login_failures where email = $1',
    [email],
  );
  const lockedUntil = failureRow.rows[0]?.locked_until;
  if (lockedUntil && lockedUntil > now) return { ok: false, reason: 'LOCKED', until: lockedUntil };

  const userRow = await pool.query<{
    id: string;
    display_name: string;
    password_hash: string;
    disabled: boolean;
  }>('select id, display_name, password_hash, disabled from users where email = $1', [email]);
  const user = userRow.rows[0];
  const valid = await verifyPassword(
    input.password,
    user && !user.disabled ? user.password_hash : await getDummyHash(options.cost),
  );
  if (!user || user.disabled || !valid) {
    const previous = failureRow.rows[0]?.failures ?? 0;
    const failures = previous + 1;
    const lock =
      failures >= options.maxFailures
        ? new Date(
            now.getTime() +
              Math.min(24 * 60, options.lockMinutes * 2 ** (failures - options.maxFailures)) *
                60_000,
          )
        : null;
    await pool.query(
      `insert into login_failures (email, failures, locked_until) values ($1, $2, $3)
       on conflict (email) do update set failures = excluded.failures, locked_until = excluded.locked_until`,
      [email, failures, lock],
    );
    return { ok: false, reason: 'INVALID_CREDENTIALS' };
  }

  await pool.query('delete from login_failures where email = $1', [email]);
  const token = newToken();
  const expiresAt = new Date(now.getTime() + options.sessionTtlHours * 3_600_000);
  await pool.query('insert into sessions (user_id, token_hash, expires_at) values ($1, $2, $3)', [
    user.id,
    hashToken(token),
    expiresAt,
  ]);
  return {
    ok: true,
    user: { id: user.id, email, displayName: user.display_name },
    token,
    expiresAt,
  };
}

/** L'utilisateur d'une session valide (non révoquée, non expirée, compte actif), sinon `null`. */
export async function authenticate(pool: Pool, token: string, now: Date): Promise<User | null> {
  const { rows } = await pool.query<{ id: string; email: string; display_name: string }>(
    `select u.id, u.email, u.display_name from sessions s join users u on u.id = s.user_id
     where s.token_hash = $1 and s.revoked_at is null and s.expires_at > $2 and not u.disabled`,
    [hashToken(token), now],
  );
  const row = rows[0];
  return row ? { id: row.id, email: row.email, displayName: row.display_name } : null;
}

export async function logout(pool: Pool, token: string, now: Date): Promise<void> {
  await pool.query(
    'update sessions set revoked_at = $2 where token_hash = $1 and revoked_at is null',
    [hashToken(token), now],
  );
}

/** Révoque toutes les sessions d'un utilisateur (compte désactivé, mot de passe changé). */
export async function revokeAllSessions(pool: Pool, userId: string, now: Date): Promise<number> {
  const result = await pool.query(
    'update sessions set revoked_at = $2 where user_id = $1 and revoked_at is null',
    [userId, now],
  );
  return result.rowCount ?? 0;
}
