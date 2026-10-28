/* global process, console, Buffer, URL */
import http from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { dirname, extname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { z } from 'zod';
import { episode } from './content.js';
import { initialState, normalizeState, transition, scenes, stepCount } from './model.js';
import { sourceMedia } from './media.js';

const root = dirname(fileURLToPath(import.meta.url));
const port = Number(process.env.SANDBOX_BIS_PORT || 4324);
const prefix = '/episode-002-bis/';
const sessions = new Map();
const epoch = Date.now();
const maxStepDelta = Math.max(...scenes.map((scene) => stepCount(scene, episode))) - 1;
const actionSchema = z.discriminatedUnion('type', [
  z.object({ type: z.literal('media'), id: z.enum(['', 'creator', 'studio']) }).strict(),
  z.object({ type: z.literal('scene'), index: z.number().int().min(0).max(22) }).strict(),
  z
    .object({
      type: z.literal('step'),
      delta: z.number().int().min(-maxStepDelta).max(maxStepDelta),
    })
    .strict(),
  z.object({ type: z.literal('toggle'), key: z.enum(['frozen', 'blackout']) }).strict(),
  z.object({ type: z.literal('view'), view: z.enum(['visual', 'fact', 'zoom']) }).strict(),
  z.object({ type: z.literal('speaker'), host: z.enum(['', 'Lou', 'Loïc', 'Nico']) }).strict(),
  z
    .object({
      type: z.literal('position'),
      host: z.enum(['Lou', 'Loïc', 'Nico']),
      value: z.enum(['', 'Oui', 'Non', 'Ça dépend']),
    })
    .strict(),
  z.object({ type: z.literal('timer'), until: z.number().finite().min(0) }).strict(),
]);
const types = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.woff2': 'font/woff2',
};
const allowed = new Set([
  'index.html',
  'show.js',
  'show.css',
  'model.js',
  'visuals.js',
  'content.js',
  'media.js',
  ...Object.keys(sourceMedia).map((id) => `assets/sources/${id}.jpg`),
  'assets/sources/persuasion-zoom.jpg',
  'assets/logo.png',
  'assets/radar-hero.png',
  'assets/build-hero.png',
  'assets/clash-hero.png',
  'assets/beta-hero.png',
  'assets/archivo.woff2',
]);
const send = (res, status, value) => {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(value));
};

export const server = http.createServer(async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Referrer-Policy', 'no-referrer');
  const expectedHosts = new Set([`127.0.0.1:${port}`, `localhost:${port}`]);
  if (!expectedHosts.has(req.headers.host)) {
    send(res, 403, { error: 'Hôte refusé' });
    return;
  }
  try {
    const url = new URL(req.url, `http://${req.headers.host}`);
    if (url.pathname === '/episode-002-bis' || url.pathname === '/') {
      res.writeHead(302, { Location: prefix });
      res.end();
      return;
    }
    if (url.pathname === `${prefix}api/state`) {
      const session = url.searchParams.get('session') || 'rehearsal';
      if (!/^[a-zA-Z0-9_-]{1,50}$/.test(session)) {
        send(res, 400, { error: 'Session invalide' });
        return;
      }
      if (!sessions.has(session)) {
        if (sessions.size >= 100) {
          send(res, 429, { error: 'Trop de sessions' });
          return;
        }
        sessions.set(session, {
          state: normalizeState(initialState(), episode),
          revision: 0,
          epoch,
        });
      }
      if (req.method === 'GET') {
        send(res, 200, sessions.get(session));
        return;
      }
      if (req.method !== 'POST') {
        send(res, 405, { error: 'Méthode refusée' });
        return;
      }
      if (
        req.headers.origin !== `http://${req.headers.host}` ||
        req.headers['content-type'] !== 'application/json'
      ) {
        send(res, 403, { error: 'Origine refusée' });
        return;
      }
      let length = 0;
      const chunks = [];
      for await (const chunk of req) {
        length += chunk.length;
        if (length > 65536) {
          send(res, 413, { error: 'Corps trop volumineux' });
          return;
        }
        chunks.push(chunk);
      }
      let parsed;
      try {
        parsed = JSON.parse(Buffer.concat(chunks).toString('utf8'));
      } catch {
        send(res, 400, { error: 'JSON invalide' });
        return;
      }
      const result = actionSchema.safeParse(parsed);
      if (!result.success) {
        send(res, 400, { error: 'Commande invalide' });
        return;
      }
      const current = sessions.get(session);
      const next = {
        state: transition(current.state, result.data, episode),
        revision: current.revision + 1,
        epoch,
      };
      sessions.set(session, next);
      send(res, 200, next);
      return;
    }
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      send(res, 405, { error: 'Méthode refusée' });
      return;
    }
    if (!url.pathname.startsWith(prefix)) {
      send(res, 404, { error: 'Route absente' });
      return;
    }
    const relative = decodeURIComponent(url.pathname.slice(prefix.length)) || 'index.html';
    if (!allowed.has(relative)) {
      send(res, 404, { error: 'Fichier absent' });
      return;
    }
    const file = resolve(root, relative);
    if (!file.startsWith(root + sep) || (await stat(file)).isDirectory()) {
      send(res, 404, { error: 'Fichier absent' });
      return;
    }
    res.setHeader('Content-Type', types[extname(file)] || 'application/octet-stream');
    if (req.method === 'HEAD') {
      res.end();
      return;
    }
    res.end(await readFile(file));
  } catch (error) {
    console.error('Requête locale impossible :', error.message);
    if (!res.headersSent) send(res, 500, { error: 'Erreur du serveur local' });
    else res.end();
  }
});
server.listen(port, '127.0.0.1', () =>
  console.log(
    `Épisode 002 BIS : http://127.0.0.1:${port}${prefix}\nRégie : http://127.0.0.1:${port}${prefix}?view=director\nOBS : http://127.0.0.1:${port}${prefix}?obs`,
  ),
);
