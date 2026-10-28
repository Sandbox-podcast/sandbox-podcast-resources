import { randomBytes } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import pg from 'pg';
import type { FastifyInstance } from 'fastify';
import { buildApp } from '../src/app.ts';
import { loadConfig, type Config } from '../src/config.ts';
import type { Pool } from '../src/db/db.ts';
import { migrate } from '../src/db/migrate.ts';
import { createUser, type AuthOptions } from '../src/services/auth-service.ts';

/** URL de la base de test : variable d'environnement, sinon `.local/.env` ; `null` si elle n'est pas joignable. */
export async function findDatabase(): Promise<string | null> {
  let url = process.env['DATABASE_URL'];
  if (!url) {
    try {
      const env = readFileSync(join(import.meta.dirname, '..', '.local', '.env'), 'utf8');
      url = /^DATABASE_URL=(.+)$/m.exec(env)?.[1];
    } catch {
      return null;
    }
  }
  if (!url) return null;
  const probe = new pg.Pool({ connectionString: url, max: 1, connectionTimeoutMillis: 2000 });
  try {
    await probe.query('select 1');
    return url;
  } catch {
    return null;
  } finally {
    await probe.end().catch(() => undefined);
  }
}

export const FAST_AUTH: AuthOptions = {
  cost: { N: 2 ** 10, r: 8, p: 1 },
  sessionTtlHours: 24,
  maxFailures: 3,
  lockMinutes: 15,
};

export const ORIGIN = 'http://localhost:3000';
export const PASSWORD = 'une phrase de passe correcte';

export interface Env {
  pool: Pool;
  app: FastifyInstance;
  config: Config;
  clock: { t: number };
  schema: string;
  close(): Promise<void>;
  /** Crée un utilisateur et retourne un jeton porteur. */
  user(email: string, name?: string): Promise<{ id: string; token: string; email: string }>;
  call(
    method: 'GET' | 'POST' | 'PATCH' | 'DELETE',
    url: string,
    options?: {
      token?: string;
      cookie?: string;
      body?: unknown;
      origin?: string | null;
      headers?: Record<string, string>;
    },
  ): Promise<{
    status: number;
    body: any;
    headers: Record<string, string | string[] | number | undefined>;
  }>;
}

export async function createEnv(
  databaseUrl: string,
  extra: Record<string, string> = {},
): Promise<Env> {
  const schema = `t_${randomBytes(6).toString('hex')}`;
  const admin = new pg.Pool({ connectionString: databaseUrl, max: 1 });
  await admin.query(`create schema ${schema}`);
  await admin.end();
  const pool = new pg.Pool({
    connectionString: databaseUrl,
    options: `-c search_path=${schema}`,
    max: 8,
  });
  await migrate(pool);
  const config = loadConfig({
    DATABASE_URL: databaseUrl,
    ALLOWED_ORIGINS: ORIGIN,
    ALLOW_REGISTRATION: 'true',
    LIVEKIT_URL: 'ws://livekit.test:7880',
    LIVEKIT_API_KEY: 'cle-de-test',
    LIVEKIT_API_SECRET: 'secret-de-test-assez-long-pour-hs256',
    ...extra,
  });
  const clock = { t: Date.UTC(2026, 9, 6, 12, 0, 0) };
  const app = buildApp({ config, pool, auth: FAST_AUTH, now: () => new Date(clock.t) });
  await app.ready();

  const call: Env['call'] = async (method, url, options = {}) => {
    const headers: Record<string, string> = { ...(options.headers ?? {}) };
    if (options.token) headers['authorization'] = `Bearer ${options.token}`;
    if (options.cookie) headers['cookie'] = options.cookie;
    if (options.origin !== null && options.origin !== undefined) headers['origin'] = options.origin;
    const response = await app.inject({
      method,
      url,
      headers,
      ...(options.body === undefined ? {} : { payload: options.body as object }),
    });
    let body: unknown;
    try {
      body = response.body.length > 0 ? JSON.parse(response.body) : null;
    } catch {
      body = response.body;
    }
    return { status: response.statusCode, body, headers: response.headers };
  };

  const user: Env['user'] = async (email, name = 'Utilisateur') => {
    const created = await createUser(
      pool,
      { email, displayName: name, password: PASSWORD },
      FAST_AUTH,
    );
    if (!created.ok) throw new Error(`création refusée : ${created.reason}`);
    const login = await call('POST', '/api/auth/login', { body: { email, password: PASSWORD } });
    if (login.status !== 200) throw new Error(`connexion refusée : ${JSON.stringify(login.body)}`);
    return { id: created.user.id, token: (login.body as { token: string }).token, email };
  };

  return {
    pool,
    app,
    config,
    clock,
    schema,
    call,
    user,
    async close() {
      await app.close();
      await pool.end();
      const cleanup = new pg.Pool({ connectionString: databaseUrl, max: 1 });
      await cleanup.query(`drop schema ${schema} cascade`);
      await cleanup.end();
    },
  };
}
