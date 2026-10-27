import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory.js';
import { CollabClient, CollabServer, InMemoryDocumentStore } from '@podcast/collab';
import { InMemoryCatalog, InMemoryEpisodeRepository } from '@podcast/episode-factory';
import {
  ConfirmationService,
  InMemoryAuditSink,
  InMemoryCredentialStore,
  Platform,
  RateLimiter,
  createPlatformMcpServer,
  type Credential,
  type Envelope,
  type Scope,
} from '../src/index.ts';

export const ALL_SCOPES: Scope[] = [
  'episode:read',
  'episode:write',
  'asset:read',
  'presentation:read',
  'presentation:write',
];

export const GOOD_HTML = '<h1>Bienvenue</h1><p>Notre invité du jour.</p>';

export const until = async (
  condition: () => boolean | Promise<boolean>,
  timeoutMs = 5000,
): Promise<void> => {
  const startedAt = Date.now();
  while (!(await condition())) {
    if (Date.now() - startedAt > timeoutMs) throw new Error('Condition non remplie dans le délai');
    await new Promise((resolve) => setTimeout(resolve, 10));
  }
};

export interface Harness {
  platform: Platform;
  credentials: InMemoryCredentialStore;
  audit: InMemoryAuditSink;
  episodes: InMemoryEpisodeRepository;
  confirmations: ConfirmationService;
  collab: CollabServer;
  store: InMemoryDocumentStore;
  catalogs: Map<string, InMemoryCatalog>;
  port: number;
  clock: { now: number };
  issue(overrides?: Partial<Credential>): Credential;
  /** Client MCP relié en mémoire à un serveur lié au credential. */
  connect(credentialId: string): Promise<Client>;
  humanClient(docId: string, user?: string): CollabClient;
  close(): Promise<void>;
}

export async function createHarness(
  options: { limiter?: RateLimiter; confirmationTtlMs?: number } = {},
): Promise<Harness> {
  const credentials = new InMemoryCredentialStore();
  const audit = new InMemoryAuditSink();
  const episodes = new InMemoryEpisodeRepository();
  const confirmations = new ConfirmationService(options.confirmationTtlMs ?? 10 * 60_000);
  const store = new InMemoryDocumentStore();
  const collab = new CollabServer({
    // Dans ces tests, seuls des humains se connectent : « jeton-<utilisateur> » donne l'écriture.
    authorize: (token) =>
      token.startsWith('jeton-') ? { userId: token.slice(6), access: 'write' } : null,
    store,
    pingIntervalMs: 500,
    autosaveMs: 20,
  });
  const port = await collab.listen();
  const catalogs = new Map<string, InMemoryCatalog>([
    ['podcast-a', InMemoryCatalog.withStandardContent()],
    ['podcast-b', InMemoryCatalog.withStandardContent()],
  ]);
  const clock = { now: 1_700_000_000_000 };
  const platform = new Platform({
    credentials,
    episodes,
    catalogs: (podcastId) => {
      const catalog = catalogs.get(podcastId);
      if (!catalog) throw new Error(`podcast inconnu : ${podcastId}`);
      return { templates: catalog, assets: catalog, themes: catalog };
    },
    collab,
    audit,
    limiter: options.limiter ?? new RateLimiter(10_000, 1000),
    confirmations,
    now: () => clock.now,
  });

  const mcpClients: Client[] = [];
  const humans: CollabClient[] = [];
  let counter = 0;

  return {
    platform,
    credentials,
    audit,
    episodes,
    confirmations,
    collab,
    store,
    catalogs,
    port,
    clock,
    issue(overrides = {}) {
      counter += 1;
      const credential: Credential = {
        id: `cred-${String(counter)}`,
        actorId: 'lou',
        podcastId: 'podcast-a',
        scopes: ALL_SCOPES,
        expiresAtMs: null,
        revoked: false,
        ...overrides,
      };
      credentials.issue(credential);
      return credential;
    },
    async connect(credentialId) {
      const [clientSide, serverSide] = InMemoryTransport.createLinkedPair();
      const server = createPlatformMcpServer(platform, credentialId);
      const client = new Client({ name: 'agent-de-test', version: '0.0.0' });
      await Promise.all([server.connect(serverSide), client.connect(clientSide)]);
      mcpClients.push(client);
      return client;
    },
    humanClient(docId, user = 'lou') {
      const client = new CollabClient({
        url: `ws://127.0.0.1:${String(port)}/collab/${encodeURIComponent(docId)}?token=jeton-${user}`,
        reconnectDelayMs: 50,
      });
      humans.push(client);
      return client;
    },
    async close() {
      for (const human of humans) human.destroy();
      for (const client of mcpClients) await client.close();
      await collab.close();
    },
  };
}

/** Appelle un tool via MCP et retourne l'enveloppe structurée. */
export async function call(
  client: Client,
  name: string,
  args: Record<string, unknown>,
): Promise<Envelope> {
  const result = await client.callTool({ name, arguments: args });
  return result.structuredContent as Envelope;
}

export function expectOk(envelope: Envelope): Extract<Envelope, { ok: true }> {
  if (!envelope.ok) throw new Error(`échec inattendu : ${JSON.stringify(envelope.error)}`);
  return envelope;
}

export function expectError(
  envelope: Envelope,
  code: string,
): Extract<Envelope, { ok: false }>['error'] {
  if (envelope.ok) throw new Error(`succès inattendu : ${JSON.stringify(envelope.data)}`);
  if (envelope.error.code !== code)
    throw new Error(
      `code attendu ${code}, reçu ${envelope.error.code} : ${envelope.error.message}`,
    );
  return envelope.error;
}

export const createEpisodeArgs = (
  extra: Record<string, unknown> = {},
): Record<string, unknown> => ({
  templateId: 'standard',
  title: 'Les agents IA',
  date: '2026-10-05',
  idempotencyKey: 'cle-demande-0001',
  ...extra,
});

/** Crée un épisode et retourne ses identifiants. */
export async function createEpisode(
  client: Client,
  extra: Record<string, unknown> = {},
): Promise<{ episodeId: string; segmentId: string; revision: number }> {
  const envelope = expectOk(
    await call(client, 'create_episode_from_template', createEpisodeArgs(extra)),
  );
  const data = envelope.data as {
    episodeId: string;
    revision: number;
    segments: { id: string }[];
  };
  const segmentId = data.segments[0]?.id;
  if (!segmentId) throw new Error('aucune séquence');
  return { episodeId: data.episodeId, segmentId, revision: data.revision };
}

/** Identifiant de la première présentation d'un épisode. */
export async function firstPresentation(
  harness: Harness,
  podcastId: string,
  episodeId: string,
): Promise<{ presentationId: string; documentId: string }> {
  const episode = await harness.episodes.get(podcastId, episodeId);
  const slot = episode?.presentations[0];
  if (!slot) throw new Error('aucune présentation');
  return { presentationId: slot.id, documentId: slot.documentId };
}
