import { ApiClient } from './api.ts';
import { browserDevices } from './browser-devices.ts';
import { Controller } from './controller.ts';
import { LiveKitConnector } from './livekit-room.ts';
import { ProgramRenderer } from './program.ts';
import { mediaPipeSegmenterFactory } from './segmenter.ts';
import { renderApp } from './views.ts';

const root = document.getElementById('app');
if (!root) throw new Error('élément #app introuvable');
const app: HTMLElement = root;

/**
 * Conteneurs qui vivent en dehors du HTML redessiné : à chaque rendu on les replace dans leur emplacement
 * (`#media-slot`, `#program-slot`), ce qui garde les flux vidéo et le canevas du Program en marche au lieu de les recréer.
 */
const media = document.createElement('div');
media.id = 'media';
media.className = 'media';

const program = document.createElement('div');
program.className = 'program';
const programCanvas = document.createElement('canvas');
const programStatus = document.createElement('p');
programStatus.className = 'muted';
programStatus.setAttribute('role', 'status');
const tools = document.createElement('div');
tools.className = 'tools';
const decorLabel = document.createElement('label');
decorLabel.textContent = 'Décor (image) : ';
const decorInput = document.createElement('input');
decorInput.type = 'file';
decorInput.accept = 'image/png,image/jpeg,image/webp';
decorInput.id = 'decor-file';
decorLabel.htmlFor = decorInput.id;
const segLabel = document.createElement('label');
const segInput = document.createElement('input');
segInput.type = 'checkbox';
segInput.checked = true;
segInput.id = 'decor-seg';
segLabel.htmlFor = segInput.id;
segLabel.append(segInput, ' Détourer le fond');
tools.append(decorLabel, decorInput, segLabel);
program.append(programCanvas, programStatus, tools);

const controller = new Controller({
  api: new ApiClient({ fetch: window.fetch.bind(window), newId: () => crypto.randomUUID() }),
  rooms: new LiveKitConnector(media),
  devices: browserDevices,
  origin: window.location.origin,
  today: () => new Date().toISOString().slice(0, 10),
  navigateTo: (hash) => {
    window.location.hash = hash;
  },
});

const renderer = new ProgramRenderer(programCanvas, {
  sources: () => controller.studioSources,
  info: () => {
    const s = controller.state;
    const route = s.route;
    const podcast =
      s.podcasts.status === 'ready' && route.name === 'studio'
        ? s.podcasts.data.find((p) => p.id === route.podcastId)?.name
        : undefined;
    return {
      title: podcast ?? 'Podcast',
      subtitle: s.episode.status === 'ready' ? s.episode.data.title : '',
      recording:
        s.studio.info.status === 'ready' && s.studio.info.data.recording.status === 'RECORDING',
    };
  },
  segmenter: mediaPipeSegmenterFactory,
});
renderer.onStatus((text) => {
  programStatus.textContent = text;
});

segInput.addEventListener('change', () => {
  renderer.setSegmentation(segInput.checked);
});
decorInput.addEventListener('change', () => {
  const file = decorInput.files?.[0];
  if (!file) {
    renderer.setDecor(null);
    return;
  }
  // Le fichier reste dans le navigateur : il n'est envoyé nulle part.
  const url = URL.createObjectURL(file);
  const image = new Image();
  image.onload = () => {
    renderer.setDecor(image);
  };
  image.src = url;
});

type Field = HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;

/**
 * Redessine la page. Les valeurs saisies sont conservées d'un rendu à l'autre (sauf mots de passe) : un message d'erreur
 * ne doit pas effacer ce que la personne vient de taper.
 */
function render(): void {
  const saved = new Map<string, string | boolean>();
  for (const el of app.querySelectorAll<Field>('input, textarea, select')) {
    const skipped =
      el instanceof HTMLInputElement &&
      (el.type === 'password' || el.type === 'hidden' || el.type === 'file');
    if (!el.id || skipped) continue;
    saved.set(
      el.id,
      el instanceof HTMLInputElement && el.type === 'checkbox' ? el.checked : el.value,
    );
  }
  const focused = document.activeElement?.id ?? '';
  app.innerHTML = renderApp(controller.state).toString();
  const slot = document.getElementById('media-slot');
  if (slot) slot.append(media);
  else media.remove();
  const programSlot = document.getElementById('program-slot');
  if (programSlot) {
    programSlot.append(program);
    renderer.start();
  } else {
    program.remove();
    renderer.stop();
  }
  for (const el of app.querySelectorAll<Field>('input, textarea, select')) {
    const value = saved.get(el.id);
    if (value === undefined) continue;
    if (el instanceof HTMLInputElement && el.type === 'checkbox') el.checked = value === true;
    else if (typeof value === 'string' && !(el instanceof HTMLInputElement && el.readOnly))
      el.value = value;
  }
  if (focused) document.getElementById(focused)?.focus();
}

controller.subscribe(render);

app.addEventListener('click', (event) => {
  const target =
    event.target instanceof Element ? event.target.closest<HTMLElement>('[data-action]') : null;
  if (!target?.dataset['action']) return;
  const data: Record<string, string> = {};
  for (const [key, value] of Object.entries(target.dataset))
    if (value !== undefined) data[key] = value;
  void controller.act(target.dataset['action'], data);
});

app.addEventListener('submit', (event) => {
  event.preventDefault();
  const form = event.target instanceof HTMLFormElement ? event.target : null;
  const name = form?.dataset['form'];
  if (!form || !name) return;
  const values: Record<string, string> = {};
  for (const [key, value] of new FormData(form)) if (typeof value === 'string') values[key] = value;
  void controller.submit(name, values);
});

window.addEventListener('hashchange', () => {
  void controller.navigate(window.location.hash);
});
window.addEventListener('pagehide', () => {
  renderer.stop();
  void controller.leaveRooms();
});

render();
void controller.start(window.location.hash);
