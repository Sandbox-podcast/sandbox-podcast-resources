export type Route =
  | { name: 'home' }
  | { name: 'login' }
  | { name: 'podcast'; podcastId: string }
  | { name: 'episode'; podcastId: string; episodeId: string }
  | { name: 'studio'; podcastId: string; episodeId: string }
  | { name: 'guest'; token: string }
  | { name: 'not-found' };

const UUID = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}';
const TOKEN = '[A-Za-z0-9_-]{43}';

/** Route d'un fragment d'URL (`#/p/<uuid>/e/<uuid>`). Les identifiants mal formés ne sont jamais envoyés au serveur. */
export function parseRoute(hash: string): Route {
  const path = hash.replace(/^#/, '').split('?')[0] ?? '';
  if (path === '' || path === '/') return { name: 'home' };
  if (path === '/login') return { name: 'login' };
  const podcast = new RegExp(`^/p/(${UUID})$`).exec(path);
  if (podcast?.[1]) return { name: 'podcast', podcastId: podcast[1] };
  const episode = new RegExp(`^/p/(${UUID})/e/(${UUID})$`).exec(path);
  if (episode?.[1] && episode[2])
    return { name: 'episode', podcastId: episode[1], episodeId: episode[2] };
  const studio = new RegExp(`^/p/(${UUID})/e/(${UUID})/studio$`).exec(path);
  if (studio?.[1] && studio[2])
    return { name: 'studio', podcastId: studio[1], episodeId: studio[2] };
  const guest = new RegExp(`^/join/(${TOKEN})$`).exec(path);
  if (guest?.[1]) return { name: 'guest', token: guest[1] };
  return { name: 'not-found' };
}

export const hrefs = {
  home: (): string => '#/',
  login: (): string => '#/login',
  podcast: (podcastId: string): string => `#/p/${podcastId}`,
  episode: (podcastId: string, episodeId: string): string => `#/p/${podcastId}/e/${episodeId}`,
  studio: (podcastId: string, episodeId: string): string =>
    `#/p/${podcastId}/e/${episodeId}/studio`,
  guest: (token: string): string => `#/join/${token}`,
};
