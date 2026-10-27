/** Trois origines locales : l'application, les présentations, et un serveur « attaquant ». */
import { createServer, type IncomingMessage, type Server, type ServerResponse } from 'node:http';
import type { AddressInfo } from 'node:net';
import { join } from 'node:path';
import { presentationHeaders } from '@podcast/presentation-sandbox';
import { build } from 'esbuild';
import { payloadHtml } from './payload.ts';

export type Mode = 'secure' | 'vulnerable';

export interface Hits {
  /** Requêtes reçues par le serveur de l'application, hors chargement de la page. */
  app: string[];
  /** Requêtes reçues par le serveur « attaquant ». */
  evil: string[];
  /** Requêtes d'upgrade WebSocket reçues par le serveur « attaquant ». */
  evilUpgrades: string[];
}

export interface Harness {
  mode: Mode;
  appUrl: string;
  sandboxUrl: string;
  evilUrl: string;
  hits: Hits;
  close: () => Promise<void>;
}

const listen = async (server: Server, host: string): Promise<number> => {
  await new Promise<void>((resolve) => server.listen(0, host, resolve));
  return (server.address() as AddressInfo).port;
};

const closeServer = (server: Server): Promise<void> =>
  new Promise((resolve) => {
    server.closeAllConnections();
    server.close(() => {
      resolve();
    });
  });

async function appBundle(): Promise<string> {
  const result = await build({
    entryPoints: [join(import.meta.dirname, 'app-client.ts')],
    bundle: true,
    write: false,
    format: 'iife',
    platform: 'browser',
    target: 'chrome120',
  });
  const file = result.outputFiles[0];
  if (!file) throw new Error('bundle vide');
  return file.text;
}

export async function startHarness(mode: Mode): Promise<Harness> {
  const bundle = await appBundle();
  const hits: Hits = { app: [], evil: [], evilUpgrades: [] };
  // Les ports ne sont connus qu'après l'écoute : les gestionnaires lisent ces variables au moment d'une requête.
  const urls = { app: '', sandbox: '', evil: '' };

  const appServer = createServer((request: IncomingMessage, response: ServerResponse) => {
    const path = request.url ?? '/';
    if (path === '/') {
      const presentationUrl =
        mode === 'secure' ? `${urls.sandbox}/p/attack` : `${urls.app}/p/attack`;
      const config = JSON.stringify({ mode, presentationUrl, sandboxOrigin: urls.sandbox });
      response.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
      response.end(
        `<!doctype html><html><head><meta charset="utf-8"><title>application</title></head><body><script type="application/json" id="config">${config}</script><script>${bundle}</script></body></html>`,
      );
      return;
    }
    if (path === '/p/attack' && mode === 'vulnerable') {
      // Contrôle négatif : présentation servie par l'origine de l'application, sans CSP.
      response.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
      response.end(payloadHtml(urls.app, urls.evil, false));
      return;
    }
    if (path !== '/favicon.ico') hits.app.push(path);
    response.writeHead(200, { 'content-type': 'application/json' });
    response.end('{"secret":"APP_SECRET_API"}');
  });

  const sandboxServer = createServer((request, response) => {
    if (request.url === '/p/attack') {
      response.writeHead(200, {
        'content-type': 'text/html; charset=utf-8',
        ...presentationHeaders({ frameAncestors: [urls.app] }),
      });
      response.end(payloadHtml(urls.app, urls.evil));
      return;
    }
    if (request.url === '/p/direct') {
      response.writeHead(200, {
        'content-type': 'text/html; charset=utf-8',
        ...presentationHeaders({ frameAncestors: [urls.app] }),
      });
      response.end(
        '<!doctype html><script>window.__o = window.origin; try { document.cookie = "x=1"; window.__cookie = "ecrit"; } catch (e) { window.__cookie = e.name; } try { localStorage.setItem("a", "b"); window.__ls = "ecrit"; } catch (e) { window.__ls = e.name; }</script>',
      );
      return;
    }
    response.writeHead(404).end();
  });

  const evilServer = createServer((request, response) => {
    hits.evil.push(request.url ?? '/');
    response.writeHead(200, {
      'content-type': 'application/javascript',
      'access-control-allow-origin': '*',
    });
    response.end('window.__evilScriptRan = true;');
  });
  evilServer.on('upgrade', (request, socket) => {
    hits.evilUpgrades.push(request.url ?? '/');
    socket.destroy();
  });

  const [appPort, sandboxPort, evilPort] = await Promise.all([
    listen(appServer, '127.0.0.1'),
    listen(sandboxServer, '127.0.0.1'),
    listen(evilServer, '127.0.0.1'),
  ]);
  // « localhost » et « 127.0.0.1 » sont deux sites distincts : l'iframe est isolée dans son propre processus.
  urls.app = `http://localhost:${String(appPort)}`;
  urls.sandbox = `http://127.0.0.1:${String(sandboxPort)}`;
  urls.evil = `http://127.0.0.1:${String(evilPort)}`;

  return {
    mode,
    appUrl: urls.app,
    sandboxUrl: urls.sandbox,
    evilUrl: urls.evil,
    hits,
    close: async () => {
      await Promise.all([
        closeServer(appServer),
        closeServer(sandboxServer),
        closeServer(evilServer),
      ]);
    },
  };
}
