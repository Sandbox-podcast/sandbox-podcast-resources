/** Lancement de Chrome (installé sur le poste), serveur de la page cliente, mesures du poste. */
import { execFile, spawn } from 'node:child_process';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { createServer, type Server } from 'node:http';
import { join } from 'node:path';
import { promisify } from 'node:util';
import { AccessToken } from 'livekit-server-sdk';
import { chromium, type Browser, type CDPSession } from 'playwright-core';

const run = promisify(execFile);
const distDir = join(import.meta.dirname, '..', '..', 'dist');

export interface StaticServer {
  url: string;
  close: () => Promise<void>;
}

/** Sert dist/ sur un port libre de localhost. */
export async function serveClient(): Promise<StaticServer> {
  const server: Server = createServer((request, response) => {
    const name =
      request.url === '/' || request.url === undefined ? 'index.html' : request.url.slice(1);
    if (
      name !== 'index.html' &&
      name !== 'client.js' &&
      name !== 'source.mp4' &&
      name !== 'source-sync.mp4'
    ) {
      response.writeHead(404).end();
      return;
    }
    readFile(
      name === 'source.mp4'
        ? join(distDir, '..', '.local', 'source-1080p30.mp4')
        : name === 'source-sync.mp4'
          ? join(distDir, '..', '.local', 'source-sync.mp4')
          : join(distDir, name),
    ).then(
      (body) => {
        response
          .writeHead(200, {
            'content-type': name.endsWith('.js')
              ? 'text/javascript'
              : name.endsWith('.mp4')
                ? 'video/mp4'
                : 'text/html',
          })
          .end(body);
      },
      () => {
        response.writeHead(500).end();
      },
    );
  });
  await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
  const address = server.address();
  if (address === null || typeof address === 'string')
    throw new Error('adresse du serveur inconnue');
  return {
    url: `http://127.0.0.1:${String(address.port)}`,
    close: () =>
      new Promise<void>((resolve) => {
        server.close(() => {
          resolve();
        });
      }),
  };
}

export async function createToken(
  apiKey: string,
  apiSecret: string,
  room: string,
  identity: string,
): Promise<string> {
  const token = new AccessToken(apiKey, apiSecret, { identity });
  token.addGrant({ roomJoin: true, room, canPublish: true, canSubscribe: true });
  return token.toJwt();
}

/** Chrome lancé directement (sans les options d'automatisation de Playwright), puis relié par CDP. */
export async function launchChromeRaw(options: LaunchOptions): Promise<Browser> {
  const port = 9333 + Math.floor(Math.random() * 500);
  const userDataDir = await mkdtemp(join(tmpdir(), 'poc1-chrome-'));
  const child = spawn(
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    [
      `--remote-debugging-port=${String(port)}`,
      `--user-data-dir=${userDataDir}`,
      '--no-first-run',
      '--no-default-browser-check',
      '--use-fake-device-for-media-stream',
      '--use-fake-ui-for-media-stream',
      '--autoplay-policy=no-user-gesture-required',
      '--disable-background-timer-throttling',
      '--disable-renderer-backgrounding',
      '--disable-backgrounding-occluded-windows',
      '--window-position=-3000,100',
      '--window-size=900,600',
      ...(options.headed ? [] : ['--headless=new']),
      'about:blank',
    ],
    { stdio: 'ignore' },
  );
  for (let i = 0; i < 40; i++) {
    const up = await fetch(`http://127.0.0.1:${String(port)}/json/version`).then(
      () => true,
      () => false,
    );
    if (up) break;
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  const browser = await chromium.connectOverCDP(`http://127.0.0.1:${String(port)}`);
  browser.on('disconnected', () => {
    child.kill();
  });
  return browser;
}

export interface LaunchOptions {
  headed: boolean;
  /** Fichier vidéo pour la caméra factice (.mjpeg ou .y4m), sinon le motif intégré de Chrome. */
  fakeVideoFile?: string;
}

export async function launchChrome(options: LaunchOptions): Promise<Browser> {
  return chromium.launch({
    channel: 'chrome',
    headless: !options.headed,
    args: [
      '--use-fake-device-for-media-stream',
      '--use-fake-ui-for-media-stream',
      '--autoplay-policy=no-user-gesture-required',
      '--disable-background-timer-throttling',
      '--disable-renderer-backgrounding',
      '--disable-backgrounding-occluded-windows',
      // Fenêtre hors écran pour ne pas gêner l'utilisateur pendant les essais avec fenêtre.
      ...(options.headed ? ['--window-position=-3000,100', '--window-size=900,600'] : []),
      ...(options.fakeVideoFile
        ? [`--use-file-for-fake-video-capture=${options.fakeVideoFile}`]
        : []),
    ],
  });
}

interface ProcessInfo {
  type: string;
  id: number;
  cpuTime: number;
}

/** Temps CPU cumulé de tous les processus de Chrome, en secondes. */
export async function chromeCpuSeconds(cdp: CDPSession): Promise<number> {
  const { processInfo } = (await cdp.send('SystemInfo.getProcessInfo' as never)) as unknown as {
    processInfo: ProcessInfo[];
  };
  return processInfo.reduce((sum, p) => sum + p.cpuTime, 0);
}

export interface GpuSample {
  gpuPercent: number;
  encoderPercent: number;
  decoderPercent: number;
}

/** Utilisation du GPU NVIDIA (moteurs vidéo compris), `undefined` si nvidia-smi est absent. */
export async function sampleGpu(): Promise<GpuSample | undefined> {
  try {
    const { stdout } = await run('nvidia-smi', [
      '--query-gpu=utilization.gpu,utilization.encoder,utilization.decoder',
      '--format=csv,noheader,nounits',
    ]);
    const [gpu, encoder, decoder] = stdout
      .trim()
      .split(',')
      .map((v) => Number(v.trim()));
    if (gpu === undefined || encoder === undefined || decoder === undefined) return undefined;
    return { gpuPercent: gpu, encoderPercent: encoder, decoderPercent: decoder };
  } catch {
    return undefined;
  }
}
