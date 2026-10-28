/* global document, window, location, history, URL, URLSearchParams, BroadcastChannel, localStorage, setTimeout, clearTimeout, setInterval, fetch, console */
import { episode } from './content.js';
import {
  chapters,
  scenes,
  initialState,
  normalizeState,
  transition,
  stepCount,
  indexFromHash,
  navigationActions,
} from './model.js';
import { renderScene, escapeText as e, useCases } from './visuals.js';
import { sourceMedia, videoMedia } from './media.js';

const $ = (selector) => document.querySelector(selector);
const params = new URLSearchParams(location.search);
const localApi = $('meta[name="sandbox-sync"]')?.content === 'local-server';
const program = params.get('view') === 'program' || params.has('obs');
const session =
  (params.get('session') || 'rehearsal').replace(/[^a-zA-Z0-9_-]/g, '').slice(0, 50) || 'rehearsal';
const storageKey = `sandbox-002-bis:${session}`;
const api = new URL(`./api/state?session=${session}`, location.href);
let state = normalizeState(initialState(), episode);
let channel;
let server = false;
let revision = -1;
let serverEpoch = null;
let queue = Promise.resolve();
let notificationTimer;
let lastScene = -1;
let localVersion = 0;
let touchStart;
let stopped = false;
let activeMedia = '';

function notify(text) {
  if (program) return;
  $('#notification').textContent = text;
  $('#notification').hidden = false;
  clearTimeout(notificationTimer);
  notificationTimer = setTimeout(() => {
    $('#notification').hidden = true;
  }, 5000);
}

function persist() {
  try {
    localStorage.setItem(storageKey, JSON.stringify(state));
  } catch {
    /* La synchronisation serveur reste disponible sans stockage navigateur. */
    $('#connection').textContent = 'Stockage navigateur indisponible';
  }
}

function renderNotes(scene) {
  if (scene.kind === 'uses') {
    const item = useCases[state.step];
    return `<div class="notes-body"><p class="eyebrow">${e(item.sector)}</p><h2>${e(item.title)}</h2><p>${e(item.action)}</p><h3>Gain visé</h3><p>${e(item.gain)}</p><h3>Pour en parler</h3><p>${e(item.note)}</p><p>Idées de produits à construire avec l'IA. Ces exemples ne sont pas des applications déjà développées ni des gains mesurés par SANDBOX.</p><h3>Les cas d'usage</h3><ol>${useCases.map((it) => `<li>${e(it.sector)} : ${e(it.title)}</li>`).join('')}</ol><h3>Références techniques</h3><a href="https://modelviewer.dev/" target="_blank" rel="noopener noreferrer">model-viewer : afficher des modèles 3D sur le Web et en réalité augmentée</a><a href="https://www.cnil.fr/fr/la-prospection-commerciale-par-courrier-electronique-sms-mms-et-automate-dappel" target="_blank" rel="noopener noreferrer">CNIL : prospection commerciale par SMS</a><details><summary>Conserver la sélection et les notes du support original</summary>${renderNotes({ ...scene, kind: 'archive' })}</details></div>`;
  }
  const source = episode.original.slides.find((s) => s.n === scene.originalNumber);
  const archive = episode.archive.find((s) => s.originalNumber === scene.originalNumber);
  if (!source)
    return `<div class="notes-body"><h2>${e(scene.title)}</h2><p>Les prochains essais et les questions du public. Les outils et cas d'usage sont présentés dans le Build.</p></div>`;
  const sources = source.sources.map((key) => episode.original.sources[key]).filter(Boolean);
  const capture = sourceMedia[scene.id];
  if (capture)
    sources.unshift({ title: `Capture à l'antenne : ${capture.publisher}`, url: capture.url });
  for (const video of Object.values(videoMedia).filter((v) => v.scene === scene.id))
    sources.push({ title: `${video.author} : ${video.title}. ${video.note}`, url: video.url });
  const links = sources
    .map(
      (source) =>
        `<a href="${e(source.url)}" target="_blank" rel="noopener noreferrer">${e(source.title)}</a>`,
    )
    .join('');
  return `<div class="notes-body"><h2>${e(source.title)}</h2>${source.sub ? `<p>${e(source.sub)}</p>` : ''}${scene.caution ? `<p class="operator-warning">${e(scene.caution)}</p>` : ''}${source.items.length ? `<h3>Les points du sujet</h3><ul>${source.items.map((item) => `<li>${item.map(e).join(' : ')}</li>`).join('')}</ul>` : ''}${source.action ? `<h3>Relance</h3><p>${e(source.action)}</p>` : ''}<h3>Notes complètes</h3>${
    source.note
      ? source.note
          .split('\n\n')
          .map((p) => `<p>${e(p)}</p>`)
          .join('')
      : '<p>Intertitre sans notes dans le support original.</p>'
  }${source.transition ? `<details><summary>Transition du support original</summary><p>${e(source.transition)}</p><p>L'ordre BIS est Radar, Build, Clash, Bêta.</p></details>` : ''}${links ? `<h3>Sources et références</h3>${links}` : ''}<details><summary>Texte intégral de l'écran original ${source.n}</summary><p class="source-copy">${e(archive?.text)}</p>${archive?.links.map((link) => `<a href="${e(link.url)}" target="_blank" rel="noopener noreferrer">${e(link.title)}</a>`).join('') || ''}</details></div>`;
}

function render() {
  const scene = scenes[state.scene];
  const chapter = chapters.find((c) => c.id === scene.chapter);
  $('#screen').style.setProperty('--accent', chapter.color);
  $('#screen').classList.toggle('frozen', state.frozen);
  $('#chapter-bug').textContent = chapter.label;
  $('#scene').innerHTML = renderScene(scene, state, episode, chapter);
  if (lastScene !== state.scene) {
    $('#scene').classList.remove('scene-enter');
    // L'animation ne redémarre qu'au changement de sujet.
    void $('#scene').offsetWidth;
    $('#scene').classList.add('scene-enter');
  }
  $('#blackout').hidden = !state.blackout;
  const media = videoMedia[state.media];
  $('#video-layer').hidden = !media;
  if (state.media !== activeMedia) {
    $('#video-slot').replaceChildren();
    if (media) {
      const frame = document.createElement('iframe');
      frame.title = `${media.author} : ${media.title}`;
      frame.allow = 'autoplay; fullscreen';
      frame.referrerPolicy = 'strict-origin-when-cross-origin';
      frame.src = `https://www.youtube-nocookie.com/embed/${media.id}?autoplay=1&mute=1&rel=0&start=${media.start}${media.end ? `&end=${media.end}` : ''}`;
      $('#video-slot').append(frame);
      $('#video-credit').textContent = `${media.label} / ${media.author} / ${media.title}`;
    }
    activeMedia = state.media;
  }
  if (!program) {
    const count = stepCount(scene, episode);
    const unit = scene.kind === 'uses' ? 'Cas' : scene.kind === 'tools' ? 'Outil' : 'Point';
    $('#counter').textContent = count > 1 ? `${unit} ${state.step + 1} / ${count}` : chapter.label;
    $('#current-title').textContent = scene.title;
    $('[data-action="previous"]').disabled = state.scene === 0 && state.step === 0;
    $('[data-action="next"]').disabled =
      state.scene === scenes.length - 1 && state.step === count - 1;
    $('#zoom-button').hidden = !scene.figure;
    $('#fact-button').hidden = !scene.figure;
    $('#zoom-button').textContent =
      state.view === 'zoom' ? 'Revenir à la source entière' : 'Agrandir la source';
    $('#fact-button').textContent =
      state.view === 'fact' ? 'Masquer le chiffre clé' : 'Afficher le chiffre clé';
    $('#media-controls').hidden = !Object.values(videoMedia).some((v) => v.scene === scene.id);
    $('#stop-video').hidden = !state.media;
    $('#zoom-button').setAttribute('aria-pressed', String(state.view === 'zoom'));
    $('#fact-button').setAttribute('aria-pressed', String(state.view === 'fact'));
    $('#overview-content').innerHTML = chapters
      .map(
        (c) =>
          `<section class="overview-section" style="--chapter:${c.color}"><h3>${c.label}</h3><div class="overview-grid">${scenes
            .map((s, i) => ({ s, i }))
            .filter(({ s }) => s.chapter === c.id)
            .map(
              ({ s, i }) =>
                `<button data-scene="${i}" class="${i === state.scene ? 'active' : ''}"><span>${String(i + 1).padStart(2, '0')}</span>${e(s.title)}</button>`,
            )
            .join('')}</div></section>`,
      )
      .join('');
    $('#notes-content').innerHTML = renderNotes(scene);
  }
  lastScene = state.scene;
  updateTimer();
}

function updateTimer() {
  const timer = $('#debate-timer');
  if (!timer) return;
  if (!state.timerUntil) {
    timer.textContent = '';
    return;
  }
  const remaining = Math.max(0, Math.ceil((state.timerUntil - Date.now()) / 1000));
  timer.textContent =
    remaining === 0
      ? 'Temps écoulé'
      : `${Math.floor(remaining / 60)}:${String(remaining % 60).padStart(2, '0')}`;
}

function receive(next, nextRevision) {
  state = normalizeState(next, episode);
  if (typeof nextRevision === 'number') revision = nextRevision;
  persist();
  render();
}

async function postAction(action, version = localVersion) {
  try {
    const response = await fetch(api, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(action),
    });
    if (!response.ok) throw new Error(`Synchronisation HTTP ${response.status}`);
    const body = await response.json();
    if (body.epoch !== serverEpoch) {
      serverEpoch = body.epoch;
      revision = -1;
    }
    // Une action locale plus récente ne doit pas être remplacée par une réponse retardée.
    if (body.revision >= revision && version === localVersion) receive(body.state, body.revision);
    $('#connection').textContent = 'Sortie reliée';
    $('#sync-status').textContent = 'Sortie synchronisée';
  } catch (error) {
    console.warn('Synchronisation locale indisponible', error.message);
    $('#connection').textContent = 'Connexion interrompue';
    $('#sync-status').textContent = 'Sortie distante non confirmée';
    notify('Connexion locale interrompue. La sortie conserve son dernier état.');
  }
}

function dispatch(action) {
  if (program) return;
  state = transition(state, action, episode);
  localVersion++;
  persist();
  if (!server) channel?.postMessage({ type: 'state', state });
  render();
  history.replaceState(null, '', `#${scenes[state.scene].id}`);
  const version = localVersion;
  if (server) queue = queue.then(() => postAction(action, version));
}

async function poll() {
  if (stopped || !localApi) return;
  const before = localVersion;
  try {
    await queue;
    const response = await fetch(api, {
      cache: 'no-store',
      signal: window.AbortSignal.timeout(2500),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const body = await response.json();
    if (body.epoch !== serverEpoch) {
      serverEpoch = body.epoch;
      revision = -1;
    }
    server = true;
    if (
      before === localVersion &&
      body.revision >= revision &&
      JSON.stringify(body.state) !== JSON.stringify(state)
    )
      receive(body.state, body.revision);
    $('#connection').textContent = 'Sortie reliée';
    $('#sync-status').textContent = 'Sortie synchronisée';
  } catch {
    if (server) {
      $('#connection').textContent = 'Connexion interrompue';
      $('#sync-status').textContent = 'Sortie distante non confirmée';
    }
  } finally {
    if (!stopped) setTimeout(poll, 500);
  }
}

function openView(view) {
  const url = new URL(location.href);
  url.hash = '';
  url.search = `?view=${view}&session=${session}`;
  const opened = window.open(
    url.href,
    `sandbox-002-bis-${view}-${session}`,
    'popup,width=1280,height=720',
  );
  if (!opened) notify('Fenêtre bloquée. Autorisez les fenêtres pour ouvrir la sortie OBS.');
}

function openDialog(id) {
  closeDialogs();
  if (!program) $(`#${id}`).showModal();
}
function closeDialogs() {
  document.querySelectorAll('dialog[open]').forEach((dialog) => dialog.close());
}
async function fullscreen() {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await $('#app').requestFullscreen();
  } catch {
    notify('Le plein écran est indisponible. Utilisez le plein écran du navigateur.');
  }
}
function action(name) {
  if (name === 'fullscreen') {
    closeDialogs();
    void fullscreen();
    return;
  }
  if (program) return;
  if (['zoom', 'fact', 'program'].includes(name)) closeDialogs();
  if (name === 'next' || name === 'previous') {
    for (const command of navigationActions(state, name === 'next' ? 1 : -1, episode))
      dispatch(command);
  }
  if (name === 'fact' && scenes[state.scene].figure)
    dispatch({ type: 'view', view: state.view === 'fact' ? 'visual' : 'fact' });
  if (name === 'freeze') dispatch({ type: 'toggle', key: 'frozen' });
  if (name === 'blackout') dispatch({ type: 'toggle', key: 'blackout' });
  if (name === 'zoom' && scenes[state.scene].chapter === 'radar')
    dispatch({ type: 'view', view: state.view === 'zoom' ? 'visual' : 'zoom' });
  if (name === 'stop-video') dispatch({ type: 'media', id: '' });
  if (['overview', 'notes', 'options'].includes(name)) openDialog(name);
  if (name === 'program') openView('program');
}

document.addEventListener('click', (event) => {
  const target = event.target.closest('button');
  if (!target || target.disabled || program) return;
  if (target.dataset.close) {
    $(`#${target.dataset.close}`).close();
    return;
  }
  if (target.dataset.scene !== undefined) {
    dispatch({ type: 'scene', index: Number(target.dataset.scene) });
    closeDialogs();
    return;
  }
  if (target.dataset.step !== undefined) {
    dispatch({ type: 'step', delta: Number(target.dataset.step) - state.step });
    return;
  }
  if (target.dataset.speaker !== undefined) {
    dispatch({ type: 'speaker', host: target.dataset.speaker });
    return;
  }
  if (target.dataset.timer !== undefined) {
    const seconds = Number(target.dataset.timer);
    dispatch({ type: 'timer', until: seconds ? Date.now() + seconds * 1000 : 0 });
    return;
  }
  if (target.dataset.action) action(target.dataset.action);
  if (target.dataset.video) {
    closeDialogs();
    dispatch({ type: 'media', id: target.dataset.video });
  }
});
document.addEventListener('change', (event) => {
  if (event.target.dataset.position)
    dispatch({ type: 'position', host: event.target.dataset.position, value: event.target.value });
});
window.addEventListener('keydown', (event) => {
  if (
    event.altKey ||
    event.ctrlKey ||
    event.metaKey ||
    event.target.closest('input,select,textarea,[contenteditable=true]')
  )
    return;
  const key = event.key.toLowerCase();
  if (key === 'escape') {
    if (!program && state.media) dispatch({ type: 'media', id: '' });
    if (!program && state.view !== 'visual') dispatch({ type: 'view', view: 'visual' });
    closeDialogs();
    return;
  }
  if (document.querySelector('dialog[open]') || program) return;
  if (key === ' ' && event.target.closest('button,a')) return;
  const mapping = {
    arrowright: 'next',
    pagedown: 'next',
    arrowleft: 'previous',
    pageup: 'previous',
    ' ': event.shiftKey ? 'previous' : 'next',
    o: 'overview',
    n: 'notes',
    z: 'zoom',
    c: 'fact',
    f: 'fullscreen',
  };
  if (mapping[key]) {
    event.preventDefault();
    action(mapping[key]);
  }
  if (['1', '2', '3', '4'].includes(key))
    dispatch({ type: 'scene', index: chapters[Number(key) - 1].start });
  if (key === 'home') dispatch({ type: 'scene', index: 0 });
  if (key === 'end') dispatch({ type: 'scene', index: scenes.length - 1 });
});
$('#screen').addEventListener(
  'touchstart',
  (event) => {
    if (program || event.target.closest('button,iframe')) return;
    touchStart = { x: event.changedTouches[0].clientX, y: event.changedTouches[0].clientY };
  },
  { passive: true },
);
$('#screen').addEventListener(
  'touchend',
  (event) => {
    if (!touchStart) return;
    const dx = event.changedTouches[0].clientX - touchStart.x;
    const dy = event.changedTouches[0].clientY - touchStart.y;
    touchStart = null;
    if (Math.abs(dx) > 75 && Math.abs(dx) > Math.abs(dy)) action(dx < 0 ? 'next' : 'previous');
  },
  { passive: true },
);
window.addEventListener('hashchange', () => {
  if (!program) dispatch({ type: 'scene', index: indexFromHash(location.hash) });
});
window.addEventListener('pagehide', () => {
  stopped = true;
  channel?.close();
});

async function start() {
  document.body.classList.toggle('program-mode', program);
  try {
    const saved = localStorage.getItem(storageKey);
    if (saved) state = normalizeState(JSON.parse(saved), episode);
  } catch {
    notify('Stockage navigateur indisponible. La navigation fonctionne en mémoire.');
  }
  try {
    channel = new BroadcastChannel(storageKey);
    channel.onmessage = (event) => {
      if (!server && event.data?.type === 'state') receive(event.data.state);
    };
  } catch {
    notify('Synchronisation entre fenêtres indisponible. Le serveur local prend le relais.');
  }
  if (localApi) {
    try {
      const response = await fetch(api, {
        cache: 'no-store',
        signal: window.AbortSignal.timeout(2500),
      });
      if (response.ok) {
        const body = await response.json();
        server = true;
        state = normalizeState(body.state, episode);
        revision = body.revision;
      }
    } catch {
      /* Hébergement statique : synchronisation limitée au même navigateur. */
      server = false;
    }
  }
  if (location.hash && !program) {
    state = transition(state, { type: 'scene', index: indexFromHash(location.hash) }, episode);
    if (server) await postAction({ type: 'scene', index: state.scene });
  }
  render();
  $('#boot').hidden = true;
  $('#app').hidden = false;
  $('#connection').textContent = server ? 'Sortie reliée' : 'Même navigateur uniquement';
  $('#sync-status').textContent = server
    ? 'Sortie synchronisée'
    : 'Dans OBS, capturez la fenêtre de ce navigateur. Une source navigateur OBS séparée ne reçoit pas les commandes.';
  setInterval(updateTimer, 250);
  void poll();
}
start().catch((error) => {
  console.error(error);
  $('#boot').textContent =
    "Le conducteur n'a pas pu démarrer. Rechargez la page ou consultez le journal du navigateur.";
});
