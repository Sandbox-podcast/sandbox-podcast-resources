import { z } from 'zod';

/**
 * Messages qu'une présentation a le droit d'envoyer à l'application, par `postMessage`.
 * Tout le reste est ignoré. Les messages sont validés par un schéma : on ne fait jamais
 * confiance à leur contenu.
 */
export const sandboxMessageSchema = z.discriminatedUnion('type', [
  z.strictObject({ type: z.literal('presentation:ready') }),
  z.strictObject({
    type: z.literal('presentation:slide'),
    index: z.number().int().min(0).max(10_000),
    total: z.number().int().min(1).max(10_000),
  }),
  z.strictObject({
    type: z.literal('presentation:resize'),
    height: z.number().int().min(0).max(20_000),
  }),
]);

export type SandboxMessage = z.infer<typeof sandboxMessageSchema>;

/** Retourne le message s'il est autorisé et bien formé, sinon `null`. */
export function parseSandboxMessage(data: unknown): SandboxMessage | null {
  const parsed = sandboxMessageSchema.safeParse(data);
  return parsed.success ? parsed.data : null;
}

export interface MessageOrigin {
  origin: string;
  source: unknown;
}

/**
 * Un message vient-il bien de l'iframe de la présentation ?
 * - la source est exactement la fenêtre de cette iframe ;
 * - l'origine est celle d'un document en bac à sable sans `allow-same-origin` (« null »),
 *   ou l'origine dédiée aux présentations.
 */
export function isTrustedMessage(
  event: MessageOrigin,
  iframeWindow: unknown,
  sandboxOrigin?: string,
): boolean {
  if (event.source === null || event.source !== iframeWindow) return false;
  return event.origin === 'null' || (sandboxOrigin !== undefined && event.origin === sandboxOrigin);
}
