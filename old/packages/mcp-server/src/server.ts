import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import type { Envelope, Platform, Tool } from './platform.ts';

const errorShape = z.looseObject({
  code: z.string(),
  message: z.string(),
  details: z.array(z.string()).optional(),
  requiredScopes: z.array(z.string()).optional(),
  retryAfterMs: z.number().optional(),
  confirmationId: z.string().optional(),
});

/** Enveloppe de sortie de tous les tools : `ok`, la corrélation, puis `data` ou `error`. */
const outputSchema = (tool: Tool) =>
  z.looseObject({
    ok: z.boolean(),
    correlationId: z.string(),
    result: z.enum(['OK', 'UNCHANGED']).optional(),
    data: tool.data.optional(),
    error: errorShape.optional(),
  });

const toCallToolResult = (envelope: Envelope) => ({
  content: [{ type: 'text' as const, text: JSON.stringify(envelope) }],
  structuredContent: envelope as unknown as Record<string, unknown>,
  isError: !envelope.ok,
});

/**
 * Un serveur MCP lié à un credential. Le transport (stdio, HTTP) authentifie l'agent et choisit
 * le credential ; ensuite chaque appel repasse par `Platform.execute`, qui réapplique l'authentification,
 * la limite de débit, les scopes, la validation, l'isolation par podcast et l'audit.
 */
export function createPlatformMcpServer(platform: Platform, credentialId: string): McpServer {
  const server = new McpServer({ name: 'podcast-platform', version: '0.0.0' });
  for (const tool of platform.tools) {
    server.registerTool(
      tool.name,
      {
        description: tool.description,
        inputSchema: tool.input as z.ZodObject,
        outputSchema: outputSchema(tool),
        annotations: {
          readOnlyHint: tool.kind === 'read',
          destructiveHint: false,
          openWorldHint: false,
        },
      },
      async (args: unknown) =>
        toCallToolResult(await platform.execute(credentialId, tool.name, args)),
    );
  }
  return server;
}
