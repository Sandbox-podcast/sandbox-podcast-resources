import {
  initialState,
  type CommandResult,
  type CommitOutcome,
  type StudioEvent,
  type StudioState,
  type StudioStore,
} from '@podcast/studio-control';
import { withTransaction, type Pool } from '../db/db.ts';

/**
 * Stockage PostgreSQL de la régie d'un épisode (l'identifiant de studio est l'identifiant de l'épisode).
 * L'écriture est atomique : état, événements et résultat de la commande sont enregistrés ensemble,
 * seulement si la version n'a pas changé ; le résultat d'une commande déjà vue est renvoyé tel quel.
 */
export class PgStudioStore implements StudioStore {
  private readonly pool: Pool;

  constructor(pool: Pool) {
    this.pool = pool;
  }

  async load(studioId: string): Promise<StudioState> {
    const { rows } = await this.pool.query<{ state: StudioState; version: number }>(
      'select state, version from studios where episode_id = $1',
      [studioId],
    );
    const row = rows[0];
    return row ? { ...row.state, version: row.version } : initialState(studioId);
  }

  async getResult(
    studioId: string,
    commandId: string,
  ): Promise<{ result: CommandResult; events: StudioEvent[] } | undefined> {
    const { rows } = await this.pool.query<{ result: CommandResult; events: StudioEvent[] }>(
      'select result, events from studio_commands where episode_id = $1 and command_id = $2',
      [studioId, commandId],
    );
    return rows[0];
  }

  async commit(
    studioId: string,
    expectedVersion: number,
    commandId: string,
    result: CommandResult,
  ): Promise<CommitOutcome> {
    return withTransaction(this.pool, async (client): Promise<CommitOutcome> => {
      // Une seule écriture à la fois par studio.
      await client.query('select pg_advisory_xact_lock(hashtext($1))', [`studio:${studioId}`]);
      const known = await client.query<{ result: CommandResult; events: StudioEvent[] }>(
        'select result, events from studio_commands where episode_id = $1 and command_id = $2',
        [studioId, commandId],
      );
      const prior = known.rows[0];
      if (prior) return { kind: 'DUPLICATE', ...prior };

      const current = await client.query<{ version: number }>(
        'select version from studios where episode_id = $1',
        [studioId],
      );
      const currentVersion = current.rows[0]?.version ?? 0;
      if (currentVersion !== expectedVersion) return { kind: 'CONFLICT' };

      const last = await client.query<{ seq: number | null }>(
        'select max(seq) as seq from studio_events where episode_id = $1',
        [studioId],
      );
      const base = last.rows[0]?.seq ?? 0;
      const events = result.events.map((e, i): StudioEvent => ({ ...e, seq: base + i + 1 }));
      for (const event of events)
        await client.query(
          'insert into studio_events (episode_id, seq, event) values ($1, $2, $3)',
          [studioId, event.seq, JSON.stringify(event)],
        );
      if (result.ok) {
        await client.query(
          `insert into studios (episode_id, state, version) values ($1, $2, $3)
           on conflict (episode_id) do update set state = excluded.state, version = excluded.version`,
          [studioId, JSON.stringify(result.state), result.state.version],
        );
      }
      await client.query(
        'insert into studio_commands (episode_id, command_id, result, events) values ($1, $2, $3, $4)',
        [studioId, commandId, JSON.stringify(result), JSON.stringify(events)],
      );
      return { kind: 'OK', events };
    });
  }

  async events(studioId: string): Promise<StudioEvent[]> {
    const { rows } = await this.pool.query<{ event: StudioEvent }>(
      'select event from studio_events where episode_id = $1 order by seq',
      [studioId],
    );
    return rows.map((r) => r.event);
  }
}
