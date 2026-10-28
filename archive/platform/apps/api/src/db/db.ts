import pg from 'pg';
import type { Pool, PoolClient, QueryResultRow } from 'pg';

export type { Pool, PoolClient } from 'pg';

/** Ce que les services acceptent : le pool (une requête isolée) ou un client (dans une transaction). */
export interface Queryable {
  // R est le type de ligne attendu par l'appelant : il n'apparaît qu'une fois dans la signature, par construction.
  // eslint-disable-next-line @typescript-eslint/no-unnecessary-type-parameters
  query<R extends QueryResultRow = QueryResultRow>(
    text: string,
    values?: readonly unknown[],
  ): Promise<{ rows: R[]; rowCount: number | null }>;
}

export function createPool(connectionString: string, max = 10): Pool {
  return new pg.Pool({ connectionString, max });
}

/** Exécute `work` dans une transaction ; annule en cas d'erreur. */
export async function withTransaction<T>(
  pool: Pool,
  work: (client: PoolClient) => Promise<T>,
): Promise<T> {
  const client = await pool.connect();
  try {
    await client.query('begin');
    const result = await work(client);
    await client.query('commit');
    return result;
  } catch (error) {
    await client.query('rollback').catch(() => undefined);
    throw error;
  } finally {
    client.release();
  }
}

/** Code d'erreur PostgreSQL de violation d'unicité. */
export const isUniqueViolation = (error: unknown): boolean =>
  typeof error === 'object' && error !== null && 'code' in error && error.code === '23505';
