/**
 * Page « application » du banc d'essai : affiche une présentation dans une iframe et applique
 * la politique de messages du module `@podcast/presentation-sandbox`.
 */
import {
  iframeAttributes,
  isTrustedMessage,
  parseSandboxMessage,
  type SandboxMessage,
} from '@podcast/presentation-sandbox';

interface Config {
  mode: 'secure' | 'vulnerable';
  presentationUrl: string;
  sandboxOrigin: string;
}

interface Raw {
  origin: string;
  data: unknown;
}

interface Probe {
  raw: Raw[];
  accepted: SandboxMessage[];
  rejected: number;
  ticks: number;
  report: unknown;
  xss: boolean;
}

declare global {
  interface Window {
    probe: Probe;
  }
}

const configElement = document.getElementById('config');
const config = JSON.parse(configElement?.textContent ?? '{}') as Config;

// Secrets de l'application : une présentation ne doit jamais y avoir accès.
document.cookie = 'session=APP_SECRET_COOKIE; path=/';
localStorage.setItem('token', 'APP_SECRET_TOKEN');

const probe: Probe = {
  raw: [],
  accepted: [],
  rejected: 0,
  ticks: 0,
  report: undefined,
  xss: false,
};
window.probe = probe;
setInterval(() => {
  probe.ticks += 1;
}, 100);

// Un titre de présentation contenant du HTML s'affiche en texte, jamais comme du HTML.
const title = document.createElement('div');
title.textContent = '<img src=x onerror="window.probe.xss=true">';
document.body.appendChild(title);

const frame = document.createElement('iframe');
if (config.mode === 'secure') {
  for (const [name, value] of Object.entries(iframeAttributes(config.presentationUrl))) {
    frame.setAttribute(name, value);
  }
} else {
  // Contrôle négatif : configuration volontairement dangereuse.
  frame.setAttribute('sandbox', 'allow-scripts allow-same-origin');
  frame.setAttribute('src', config.presentationUrl);
}
document.body.appendChild(frame);

window.addEventListener('message', (event: MessageEvent) => {
  const raw: unknown = event.data;
  probe.raw.push({ origin: event.origin, data: raw });
  const data = raw as { type?: string; results?: unknown } | null;
  if (data?.type === '__report') {
    probe.report = data.results;
    return;
  }
  if (
    !isTrustedMessage(
      { origin: event.origin, source: event.source },
      frame.contentWindow,
      config.sandboxOrigin,
    )
  ) {
    probe.rejected += 1;
    return;
  }
  const message = parseSandboxMessage(raw);
  if (message) probe.accepted.push(message);
  else probe.rejected += 1;
});
