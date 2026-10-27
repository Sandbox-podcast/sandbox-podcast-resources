import type { Episode, Segment } from './api.ts';
import { esc, html, raw, SafeHtml } from './html.ts';
import { hrefs } from './router.ts';
import type { AppState, Loadable, RoomView } from './state.ts';

const STATUS_LABELS: Record<Segment['status'], string> = {
  TODO: 'À faire',
  IN_PROGRESS: 'En cours',
  READY: 'Prête',
};

const ROLE_LABELS: Record<string, string> = {
  ADMIN: 'Administrateur',
  PRODUCER: 'Producteur',
  HOST: 'Animateur',
  EDITOR: 'Éditeur',
  VIEWER: 'Lecteur',
};

const formatDuration = (seconds: number): string => {
  const minutes = Math.round(seconds / 60);
  return `${String(minutes)} min`;
};

/** Rend un état de chargement, d'erreur ou le contenu : les trois états sont toujours traités. */
function loadable<T>(
  state: Loadable<T>,
  content: (data: T) => SafeHtml,
  emptyText?: (data: T) => string | null,
): SafeHtml {
  switch (state.status) {
    case 'idle':
    case 'loading':
      return html`<p class="muted" role="status">Chargement…</p>`;
    case 'error':
      return html`<p class="error" role="alert">
        ${state.message}${
          state.correlationId
            ? html` <span class="muted">(référence ${state.correlationId})</span>`
            : ''
        }
      </p>`;
    case 'ready': {
      const empty = emptyText?.(state.data);
      return empty ? html`<p class="muted">${empty}</p>` : content(state.data);
    }
  }
}

function flash(state: AppState): SafeHtml {
  if (!state.flash) return raw('');
  return state.flash.kind === 'error'
    ? html`<p class="flash error" role="alert">${state.flash.text}</p>`
    : html`<p class="flash ok" role="status">${state.flash.text}</p>`;
}

function header(state: AppState): SafeHtml {
  return html`<header class="top">
    <a class="brand" href="${hrefs.home()}">Plateforme podcast</a>
    ${
      state.user
        ? html`<span class="who">${state.user.displayName}</span>
            <button type="button" data-action="logout">Se déconnecter</button>`
        : ''
    }
  </header>`;
}

function loginPage(state: AppState): SafeHtml {
  return html`<section aria-labelledby="t">
    <h1 id="t">Connexion</h1>
    ${flash(state)}
    <form data-form="login" autocomplete="on">
      <label for="email">Adresse e-mail</label>
      <input id="email" name="email" type="email" required autocomplete="username" />
      <label for="password">Mot de passe</label>
      <input
        id="password"
        name="password"
        type="password"
        required
        autocomplete="current-password"
      />
      <button type="submit" ${state.busy ? raw('disabled') : ''}>Se connecter</button>
    </form>
  </section>`;
}

function homePage(state: AppState): SafeHtml {
  return html`<section aria-labelledby="t">
    <h1 id="t">Mes podcasts</h1>
    ${flash(state)}
    ${loadable(
      state.podcasts,
      (podcasts) =>
        html`<ul class="cards">
          ${podcasts.map(
            (p) =>
              html`<li>
                <a href="${hrefs.podcast(p.id)}">${p.name}</a>
                <span class="badge">${ROLE_LABELS[p.role] ?? p.role}</span>
              </li>`,
          )}
        </ul>`,
      (podcasts) =>
        podcasts.length === 0
          ? "Vous n'avez encore aucun podcast. Créez le premier ci-dessous."
          : null,
    )}
    <h2>Nouveau podcast</h2>
    <form data-form="create-podcast">
      <label for="name">Nom du podcast</label>
      <input id="name" name="name" type="text" required maxlength="200" />
      <button type="submit" ${state.busy ? raw('disabled') : ''}>Créer</button>
    </form>
  </section>`;
}

function podcastPage(state: AppState): SafeHtml {
  const route = state.route;
  const podcastId = route.name === 'podcast' ? route.podcastId : '';
  const role =
    state.podcasts.status === 'ready'
      ? state.podcasts.data.find((p) => p.id === podcastId)?.role
      : undefined;
  const canCreate = role === 'ADMIN' || role === 'PRODUCER';
  return html`<section aria-labelledby="t">
    <p><a href="${hrefs.home()}">← Mes podcasts</a></p>
    <h1 id="t">Épisodes</h1>
    ${flash(state)}
    ${loadable(
      state.episodes,
      (episodes) =>
        html`<ul class="cards">
          ${episodes.map(
            (e) =>
              html`<li>
                <a href="${hrefs.episode(podcastId, e.id)}">${e.title}</a>
                <span class="muted">${e.date}</span>
              </li>`,
          )}
        </ul>`,
      (episodes) => (episodes.length === 0 ? "Aucun épisode pour l'instant." : null),
    )}
    ${
      canCreate
        ? html`<h2>Nouvel épisode</h2>
            <p class="muted">
              Créé depuis le modèle standard : introduction, séquences A et B, conclusion.
            </p>
            <form data-form="create-episode">
              <label for="title">Titre</label>
              <input id="title" name="title" type="text" required maxlength="200" />
              <label for="date">Date d'enregistrement</label>
              <input id="date" name="date" type="date" required />
              <button type="submit" ${state.busy ? raw('disabled') : ''}>Créer l'épisode</button>
            </form>`
        : html`<p class="muted">Votre rôle ne permet pas de créer un épisode.</p>`
    }
  </section>`;
}

function segmentForm(segment: Segment, canEdit: boolean): SafeHtml {
  return html`<li class="segment">
    <h3>${segment.title} <span class="badge">${STATUS_LABELS[segment.status]}</span></h3>
    <p class="muted">
      ${segment.objective} · durée visée ${formatDuration(segment.targetDurationSec)}
    </p>
    <form data-form="segment">
      <input type="hidden" name="segmentId" value="${segment.id}" />
      <label for="notes-${segment.id}">Notes</label>
      <textarea
        id="notes-${segment.id}"
        name="notes"
        rows="3"
        maxlength="20000"
        ${canEdit ? '' : raw('readonly')}
      >
${segment.notes}</textarea>
      <label for="status-${segment.id}">Statut</label>
      <select id="status-${segment.id}" name="status" ${canEdit ? '' : raw('disabled')}>
        ${(Object.keys(STATUS_LABELS) as Segment['status'][]).map(
          (key) =>
            html`<option value="${key}" ${key === segment.status ? raw('selected') : ''}>
              ${STATUS_LABELS[key]}
            </option>`,
        )}
      </select>
      ${canEdit ? html`<button type="submit">Enregistrer</button>` : ''}
    </form>
  </li>`;
}

function episodePage(state: AppState): SafeHtml {
  const route = state.route;
  if (route.name !== 'episode') return raw('');
  const role =
    state.podcasts.status === 'ready'
      ? state.podcasts.data.find((p) => p.id === route.podcastId)?.role
      : undefined;
  const canEdit = role === 'ADMIN' || role === 'PRODUCER' || role === 'HOST' || role === 'EDITOR';
  const canInvite = role === 'ADMIN' || role === 'PRODUCER';
  const canStudio = canInvite || role === 'HOST';
  const body = (episode: Episode): SafeHtml => {
    const order = new Map(episode.rundown.map((r) => [r.segmentId, r.order]));
    const segments = [...episode.segments].sort(
      (a, b) => (order.get(a.id) ?? 0) - (order.get(b.id) ?? 0),
    );
    return html`<h1 id="t">${episode.title}</h1>
      <p class="muted">${episode.date} · révision ${episode.revision}</p>
      ${canStudio ? html`<p><a class="button" href="${hrefs.studio(route.podcastId, episode.id)}">Ouvrir le studio</a></p>` : ''}
      <h2>Conducteur</h2>
      <ol class="segments">
        ${segments.map((s) => segmentForm(s, canEdit))}
      </ol>
      ${
        canInvite
          ? html`<h2>Inviter un participant</h2>
              <form data-form="invite">
                <label for="guest-name">Nom de l'invité (facultatif)</label>
                <input id="guest-name" name="displayName" type="text" maxlength="120" />
                <button type="submit">Créer un lien d'invitation</button>
              </form>
              ${
                state.invitationLinks.length > 0
                  ? html`<p class="muted">
                        Ces liens ne sont affichés qu'une fois. Transmettez-les par un canal sûr.
                      </p>
                      <ul>
                        ${state.invitationLinks.map((link) => html`<li><code>${link}</code></li>`)}
                      </ul>`
                  : ''
              }`
          : ''
      }`;
  };
  return html`<section aria-labelledby="t">
    <p><a href="${hrefs.podcast(route.podcastId)}">← Épisodes</a></p>
    ${flash(state)} ${loadable(state.episode, body)}
  </section>`;
}

function roomPanel(room: RoomView): SafeHtml {
  const labels = {
    disconnected: 'Non connecté',
    connecting: 'Connexion…',
    connected: 'Connecté',
    error: 'Erreur',
  } as const;
  return html`<div class="panel" aria-live="polite">
    <p>Salle : <strong>${labels[room.status]}</strong></p>
    ${room.message ? html`<p class="${room.status === 'error' ? 'error' : 'muted'}">${room.message}</p>` : ''}
    ${
      room.participants.length > 0
        ? html`<ul>
            ${room.participants.map((p) => html`<li>${p}</li>`)}
          </ul>`
        : room.status === 'connected'
          ? html`<p class="muted">Personne d'autre dans la salle.</p>`
          : ''
    }
  </div>`;
}

function studioPage(state: AppState): SafeHtml {
  const route = state.route;
  if (route.name !== 'studio') return raw('');
  const role =
    state.podcasts.status === 'ready'
      ? state.podcasts.data.find((p) => p.id === route.podcastId)?.role
      : undefined;
  const canControl = role === 'ADMIN' || role === 'PRODUCER';
  const recording = (s: { recording: { status: string } }): boolean =>
    s.recording.status === 'RECORDING';
  return html`<section aria-labelledby="t">
    <p><a href="${hrefs.episode(route.podcastId, route.episodeId)}">← Épisode</a></p>
    <h1 id="t">Studio</h1>
    ${flash(state)} ${roomPanel(state.studio.room)}
    <div class="studio-grid">
      <div id="program-slot"></div>
      <aside aria-label="Caméras brutes">
        <h2>Sur le réseau</h2>
        <div id="media-slot"></div>
      </aside>
    </div>
    <p>
      <button
        type="button"
        data-action="studio-connect"
        ${state.studio.room.status === 'connecting' || state.studio.room.status === 'connected' ? raw('disabled') : ''}
      >
        Rejoindre la salle
      </button>
      <button type="button" data-action="consent">Je consens à l'enregistrement</button>
    </p>
    ${loadable(
      state.studio.info,
      (studio) =>
        html`<h2>Régie</h2>
          <dl>
            <dt>Preview</dt>
            <dd>${studio.preview ? studio.preview.id : 'vide'}</dd>
            <dt>Program</dt>
            <dd>${studio.program ? studio.program.id : 'vide'}</dd>
            <dt>Enregistrement</dt>
            <dd>${recording(studio) ? 'en cours' : 'arrêté'}</dd>
          </dl>
          ${
            canControl
              ? html`<p>
                    <button type="button" data-action="preview" data-scene="groupe">
                      Preview : groupe
                    </button>
                    <button type="button" data-action="preview" data-scene="presentation">
                      Preview : présentation
                    </button>
                    <button type="button" data-action="take">Passer à l'antenne</button>
                  </p>
                  <p>
                    ${
                      recording(studio)
                        ? html`<button type="button" data-action="rec-stop">
                            Arrêter l'enregistrement
                          </button>`
                        : html`<button type="button" data-action="rec-start">
                            Démarrer l'enregistrement
                          </button>`
                    }
                  </p>`
              : html`<p class="muted">Seul un producteur pilote la régie.</p>`
          }`,
    )}
  </section>`;
}

function guestPage(state: AppState): SafeHtml {
  const guest = state.guest;
  return html`<section aria-labelledby="t">
    <h1 id="t">Rejoindre l'enregistrement</h1>
    ${flash(state)}
    ${loadable(
      guest.info,
      (info) =>
        html`<p>
            Podcast <strong>${info.podcastName}</strong> · épisode
            <strong>${info.episodeTitle}</strong>
          </p>
          <h2>1. Vérifier ma caméra et mon micro</h2>
          <p><button type="button" data-action="device-check">Tester</button></p>
          ${guest.deviceMessage ? html`<p class="${guest.devices?.ok ? 'ok' : 'error'}" role="status">${guest.deviceMessage}</p>` : ''}
          <h2>2. Mon nom</h2>
          <form data-form="guest-join">
            <label for="display-name">Nom affiché</label>
            <input
              id="display-name"
              name="displayName"
              type="text"
              maxlength="120"
              value="${info.displayName ?? guest.displayName}"
              ${info.displayName ? raw('readonly') : ''}
              required
            />
            <h2>3. Enregistrement</h2>
            <p>
              Cet épisode est enregistré : votre image et votre voix seront conservées par l'équipe
              du podcast.
            </p>
            <label
              ><input type="checkbox" name="consent" ${guest.consent ? raw('checked') : ''} /> Je
              consens à cet enregistrement</label
            >
            <button type="submit" ${state.busy ? raw('disabled') : ''}>Rejoindre</button>
          </form>
          ${roomPanel(guest.room)}
          <div id="media-slot"></div>`,
    )}
  </section>`;
}

export function renderApp(state: AppState): SafeHtml {
  const route = state.route;
  let page: SafeHtml;
  if (state.user === undefined && route.name !== 'guest')
    page = html`<p class="muted" role="status">Chargement…</p>`;
  else if (route.name === 'guest') page = guestPage(state);
  else if (state.user === null || route.name === 'login') page = loginPage(state);
  else if (route.name === 'home') page = homePage(state);
  else if (route.name === 'podcast') page = podcastPage(state);
  else if (route.name === 'episode') page = episodePage(state);
  else if (route.name === 'studio') page = studioPage(state);
  else
    page = html`<h1>Page introuvable</h1>
      <p><a href="${hrefs.home()}">Retour à l'accueil</a></p>`;
  return html`${header(state)}
    <main>${page}</main>`;
}

export { esc };
