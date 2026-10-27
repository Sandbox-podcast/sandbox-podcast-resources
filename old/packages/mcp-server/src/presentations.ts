import type * as Y from 'yjs';
import { sha256 } from './security.ts';

/**
 * Convention d'un document de présentation collaboratif :
 * - `html` (Y.Text) : le contenu HTML complet ;
 * - `meta` (Y.Map) : `title`.
 * Le même document est édité par les humains (CollabClient) et par les agents (côté serveur).
 */
export const PRESENTATION_SCHEMA = { html: 'text', meta: 'map' } as const;

export const readHtml = (doc: Y.Doc): string => doc.getText('html').toJSON();
export const readTitle = (doc: Y.Doc): string => {
  const title = doc.getMap<unknown>('meta').get('title');
  return typeof title === 'string' ? title : '';
};
export const contentHash = (html: string): string => sha256(html);

/** Remplace le contenu en une seule transaction : les collaborateurs reçoivent un seul changement cohérent. */
export function writePresentation(
  doc: Y.Doc,
  content: { html: string; title?: string },
  origin: string,
): void {
  doc.transact(() => {
    const text = doc.getText('html');
    text.delete(0, text.length);
    text.insert(0, content.html);
    if (content.title !== undefined) doc.getMap<unknown>('meta').set('title', content.title);
  }, origin);
}
