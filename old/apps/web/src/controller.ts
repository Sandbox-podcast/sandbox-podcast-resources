import { ApiClient, ApiError, type RoomAccess } from './api.ts';
import { describeDeviceError, isDeviceError, summarizeDevices } from './devices.ts';
import { hrefs, parseRoute, type Route } from './router.ts';
import type { ProgramSource } from './program.ts';
import { initialState, type AppState, type Loadable, type RoomView } from './state.ts';

/** Connexion à la salle : l'implémentation réelle (LiveKit) est injectée, les tests utilisent une fausse salle. */
export interface RoomHandle {
  participants(): string[];
  disconnect(): Promise<void>;
  /** Appelé quand la liste des participants ou l'état de la connexion change. */
  onChange(callback: () => void): void;
  /** Personnes de la salle avec leur vidéo, pour le rendu du Program. */
  sources?(): ProgramSource[];
}
export interface RoomConnector {
  connect(access: RoomAccess): Promise<RoomHandle>;
}
export interface DeviceAccess {
  enumerate(): Promise<{ kind: string }[]>;
  /** Demande l'accès à la caméra et au micro (et les relâche aussitôt). Lève l'erreur du navigateur. */
  test(): Promise<void>;
}

export interface ControllerDeps {
  api: ApiClient;
  rooms: RoomConnector;
  devices: DeviceAccess;
  /** Adresse de base pour construire les liens d'invitation (`https://hôte/`). */
  origin: string;
  today: () => string;
  /** Change le fragment d'URL (navigation). */
  navigateTo: (hash: string) => void;
}

const errorText = (error: unknown): { message: string; correlationId: string | null } =>
  error instanceof ApiError
    ? { message: error.message, correlationId: error.correlationId }
    : { message: 'Une erreur est survenue. Réessayez.', correlationId: null };

const failed = <T>(error: unknown): Loadable<T> => ({ status: 'error', ...errorText(error) });

const STUDIO_MESSAGES: Record<string, string> = {
  CONSENT_REQUIRED: "Tous les participants doivent d'abord consentir à l'enregistrement.",
  ALREADY_RECORDING: "L'enregistrement est déjà en cours.",
  NOT_RECORDING: "Aucun enregistrement n'est en cours.",
  NOTHING_IN_PREVIEW: "Rien n'est en Preview.",
  PREVIEW_CHANGED: "La Preview a changé : rechargez avant de passer à l'antenne.",
  STALE_VERSION: "Le studio a changé : l'état a été rechargé, réessayez.",
  FORBIDDEN: 'Votre rôle ne permet pas cette action.',
};

/**
 * Logique de l'application, sans DOM : un état, des actions, des abonnés notifiés à chaque changement.
 * L'interface (main.ts) ne fait que dessiner l'état et relayer les clics et formulaires.
 */
export class Controller {
  state: AppState = initialState();
  private readonly deps: ControllerDeps;
  private readonly listeners = new Set<() => void>();
  /** Clé d'idempotence par demande de création d'épisode : un rejeu (double clic, réseau) ne crée qu'un épisode. */
  private readonly episodeKeys = new Map<string, string>();
  private studioRoom: RoomHandle | null = null;
  private guestRoom: RoomHandle | null = null;
  private studioVersion = 0;

  constructor(deps: ControllerDeps) {
    this.deps = deps;
  }

  subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private set(patch: Partial<AppState>): void {
    this.state = { ...this.state, ...patch };
    for (const listener of this.listeners) listener();
  }

  private setRoom(kind: 'studio' | 'guest', room: RoomView): void {
    if (kind === 'studio') this.set({ studio: { ...this.state.studio, room } });
    else this.set({ guest: { ...this.state.guest, room } });
  }

  /** Démarrage : session existante ? puis route de l'URL. */
  async start(hash: string): Promise<void> {
    const route = parseRoute(hash);
    if (route.name === 'guest') {
      this.set({ user: null });
      await this.navigate(hash);
      return;
    }
    try {
      const me = await this.deps.api.me();
      this.set({ user: me.user, podcasts: { status: 'ready', data: me.podcasts } });
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) this.set({ user: null });
      else this.set({ user: null, flash: { kind: 'error', text: errorText(error).message } });
    }
    await this.navigate(hash);
  }

  async navigate(hash: string): Promise<void> {
    const route: Route = parseRoute(hash);
    this.set({ route, flash: null });
    if (route.name === 'guest') {
      this.set({ guest: { ...this.state.guest, info: { status: 'loading' } } });
      try {
        const { invitation } = await this.deps.api.invitationInfo(route.token);
        this.set({ guest: { ...this.state.guest, info: { status: 'ready', data: invitation } } });
      } catch (error) {
        this.set({ guest: { ...this.state.guest, info: failed(error) } });
      }
      return;
    }
    if (!this.state.user) return;
    try {
      if (route.name === 'home') {
        const me = await this.deps.api.me();
        this.set({ podcasts: { status: 'ready', data: me.podcasts } });
      } else if (route.name === 'podcast') {
        this.set({ episodes: { status: 'loading' } });
        const { episodes } = await this.deps.api.listEpisodes(route.podcastId);
        this.set({ episodes: { status: 'ready', data: episodes } });
      } else if (route.name === 'episode') {
        this.set({ episode: { status: 'loading' } });
        const { episode } = await this.deps.api.getEpisode(route.podcastId, route.episodeId);
        this.set({ episode: { status: 'ready', data: episode } });
      } else if (route.name === 'studio') {
        this.set({ studio: { ...this.state.studio, info: { status: 'loading' } } });
        const { state } = await this.deps.api.studioState(route.podcastId, route.episodeId);
        this.studioVersion = state.version;
        this.set({ studio: { ...this.state.studio, info: { status: 'ready', data: state } } });
        // Le titre de l'épisode sert au rendu du Program ; son absence n'empêche pas d'ouvrir le studio.
        try {
          const { episode } = await this.deps.api.getEpisode(route.podcastId, route.episodeId);
          this.set({ episode: { status: 'ready', data: episode } });
        } catch {
          // titre indisponible : le rendu affichera seulement le nom du podcast
        }
      }
    } catch (error) {
      this.handleLoadError(route, error);
    }
  }

  private handleLoadError(route: Route, error: unknown): void {
    if (error instanceof ApiError && error.code === 'UNAUTHENTICATED') {
      this.set({
        user: null,
        flash: { kind: 'error', text: 'Votre session a expiré, reconnectez-vous.' },
      });
      return;
    }
    const failure = failed<never>(error);
    if (route.name === 'podcast') this.set({ episodes: failure });
    else if (route.name === 'episode') this.set({ episode: failure });
    else if (route.name === 'studio') this.set({ studio: { ...this.state.studio, info: failure } });
    else this.set({ flash: { kind: 'error', text: errorText(error).message } });
  }

  /** Exécute une action qui modifie quelque chose : une seule à la fois, erreurs affichées, jamais lancées. */
  private async mutate(work: () => Promise<void>): Promise<void> {
    if (this.state.busy) return;
    this.set({ busy: true, flash: null });
    try {
      await work();
    } catch (error) {
      if (error instanceof ApiError && error.code === 'UNAUTHENTICATED')
        this.set({
          user: null,
          flash: { kind: 'error', text: 'Votre session a expiré, reconnectez-vous.' },
        });
      else {
        const known = error instanceof ApiError ? STUDIO_MESSAGES[error.code] : undefined;
        const failure = errorText(error);
        this.set({
          flash: {
            kind: 'error',
            text:
              known ??
              (failure.correlationId
                ? `${failure.message} (référence ${failure.correlationId})`
                : failure.message),
          },
        });
      }
    } finally {
      this.set({ busy: false });
    }
  }

  async submit(form: string, values: Record<string, string>): Promise<void> {
    const route = this.state.route;
    switch (form) {
      case 'login':
        return this.mutate(async () => {
          const { user } = await this.deps.api.login(
            values['email'] ?? '',
            values['password'] ?? '',
          );
          this.set({ user });
          this.deps.navigateTo(hrefs.home());
          await this.navigate(hrefs.home());
        });
      case 'create-podcast':
        return this.mutate(async () => {
          const { podcast } = await this.deps.api.createPodcast(values['name'] ?? '');
          const current = this.state.podcasts.status === 'ready' ? this.state.podcasts.data : [];
          this.set({
            podcasts: { status: 'ready', data: [...current, podcast] },
            flash: { kind: 'ok', text: 'Podcast créé.' },
          });
        });
      case 'create-episode':
        if (route.name !== 'podcast') return;
        return this.mutate(async () => {
          const date = values['date'];
          const input = {
            title: values['title'] ?? '',
            date: date !== undefined && date !== '' ? date : this.deps.today(),
          };
          const signature = JSON.stringify([route.podcastId, input.title, input.date]);
          const key = this.episodeKeys.get(signature) ?? this.deps.api.newId();
          this.episodeKeys.set(signature, key);
          const { episode, created } = await this.deps.api.createEpisode(
            route.podcastId,
            input,
            key,
          );
          const { episodes } = await this.deps.api.listEpisodes(route.podcastId);
          this.set({
            episodes: { status: 'ready', data: episodes },
            flash: {
              kind: 'ok',
              text: created ? `Épisode « ${episode.title} » créé.` : 'Cet épisode existait déjà.',
            },
          });
        });
      case 'segment':
        if (route.name !== 'episode' || this.state.episode.status !== 'ready') return;
        return this.mutate(async () => {
          const current = this.state.episode;
          if (current.status !== 'ready') return;
          const status = values['status'];
          const { episode } = await this.deps.api.patchSegment(
            route.podcastId,
            route.episodeId,
            values['segmentId'] ?? '',
            current.data.revision,
            {
              notes: values['notes'] ?? '',
              ...(status === 'TODO' || status === 'IN_PROGRESS' || status === 'READY'
                ? { status }
                : {}),
            },
          );
          this.set({
            episode: { status: 'ready', data: episode },
            flash: { kind: 'ok', text: 'Séquence enregistrée.' },
          });
        });
      case 'invite':
        if (route.name !== 'episode') return;
        return this.mutate(async () => {
          const name = values['displayName']?.trim();
          const created = await this.deps.api.createInvitation(
            route.podcastId,
            route.episodeId,
            name ? { displayName: name } : {},
          );
          const link = `${this.deps.origin}${hrefs.guest(created.token)}`;
          this.set({
            invitationLinks: [...this.state.invitationLinks, link],
            flash: { kind: 'ok', text: "Lien d'invitation créé." },
          });
        });
      case 'guest-join':
        if (route.name !== 'guest') return;
        return this.mutate(async () => {
          if (values['consent'] !== 'on') {
            this.set({
              flash: {
                kind: 'error',
                text: "Cochez la case de consentement pour rejoindre l'enregistrement.",
              },
            });
            return;
          }
          const joined = await this.deps.api.invitationJoin(route.token, values['displayName']);
          await this.deps.api.invitationConsent(route.token);
          this.set({
            guest: {
              ...this.state.guest,
              consent: true,
              displayName: joined.participant.displayName,
            },
          });
          await this.connectRoom('guest', joined.livekit);
        });
      default:
        return;
    }
  }

  async act(action: string, data: Record<string, string> = {}): Promise<void> {
    const route = this.state.route;
    switch (action) {
      case 'logout':
        return this.mutate(async () => {
          await this.deps.api.logout();
          await this.leaveRooms();
          this.set({
            user: null,
            podcasts: { status: 'idle' },
            episodes: { status: 'idle' },
            episode: { status: 'idle' },
            invitationLinks: [],
          });
        });
      case 'device-check':
        return this.mutate(async () => {
          try {
            await this.deps.devices.test();
            const report = summarizeDevices(await this.deps.devices.enumerate());
            this.set({
              guest: {
                ...this.state.guest,
                devices: report,
                deviceMessage: report.ok
                  ? `Caméra et micro détectés (${String(report.cameras)} caméra, ${String(report.microphones)} micro).`
                  : report.problems.join(' '),
              },
            });
          } catch (error) {
            this.set({
              guest: {
                ...this.state.guest,
                devices: null,
                deviceMessage: describeDeviceError(error),
              },
            });
          }
        });
      case 'studio-connect':
        if (route.name !== 'studio') return;
        return this.mutate(async () => {
          const access = await this.deps.api.studioToken(route.podcastId, route.episodeId);
          this.set({ studio: { ...this.state.studio, participantId: access.participantId } });
          await this.connectRoom('studio', access.livekit);
        });
      case 'consent':
        if (route.name !== 'studio') return;
        return this.mutate(async () => {
          if (!this.state.studio.participantId) {
            const access = await this.deps.api.studioToken(route.podcastId, route.episodeId);
            this.set({ studio: { ...this.state.studio, participantId: access.participantId } });
          }
          await this.deps.api.studioConsent(route.podcastId, route.episodeId);
          this.set({ flash: { kind: 'ok', text: 'Votre consentement est enregistré.' } });
        });
      case 'preview':
        return this.studioCommand({
          type: 'SET_PREVIEW',
          source: { kind: 'scene', id: data['scene'] ?? 'groupe' },
        });
      case 'take': {
        const info = this.state.studio.info;
        const previewId = info.status === 'ready' ? info.data.preview?.id : undefined;
        if (!previewId) {
          this.set({ flash: { kind: 'error', text: STUDIO_MESSAGES['NOTHING_IN_PREVIEW'] ?? '' } });
          return;
        }
        return this.studioCommand({ type: 'TAKE', expectPreviewId: previewId });
      }
      case 'rec-start':
        return this.studioCommand({
          type: 'START_RECORDING',
          sessionId: `rec-${this.deps.api.newId()}`,
        });
      case 'rec-stop':
        return this.studioCommand({ type: 'STOP_RECORDING' });
      default:
        return;
    }
  }

  private async studioCommand(command: Record<string, unknown>): Promise<void> {
    const route = this.state.route;
    if (route.name !== 'studio') return;
    return this.mutate(async () => {
      try {
        const result = await this.deps.api.studioCommand(route.podcastId, route.episodeId, command);
        if (result.state) {
          this.studioVersion = result.state.version;
          this.set({
            studio: { ...this.state.studio, info: { status: 'ready', data: result.state } },
          });
        }
      } catch (error) {
        // Version périmée : on recharge l'état avant de montrer l'erreur, pour que le prochain essai parte de l'état réel.
        if (error instanceof ApiError && error.code === 'STALE_VERSION') {
          const { state } = await this.deps.api.studioState(route.podcastId, route.episodeId);
          this.studioVersion = state.version;
          this.set({ studio: { ...this.state.studio, info: { status: 'ready', data: state } } });
        }
        throw error;
      }
    });
  }

  private async connectRoom(kind: 'studio' | 'guest', access: RoomAccess): Promise<void> {
    this.setRoom(kind, { status: 'connecting', participants: [], message: null });
    try {
      const handle = await this.deps.rooms.connect(access);
      handle.onChange(() => {
        this.setRoom(kind, {
          status: 'connected',
          participants: handle.participants(),
          message: null,
        });
      });
      if (kind === 'studio') this.studioRoom = handle;
      else this.guestRoom = handle;
      this.setRoom(kind, {
        status: 'connected',
        participants: handle.participants(),
        message: null,
      });
    } catch (error) {
      const message = isDeviceError(error)
        ? describeDeviceError(error)
        : 'Connexion à la salle impossible : vérifiez votre réseau, puis réessayez.';
      this.setRoom(kind, { status: 'error', participants: [], message });
    }
  }

  async leaveRooms(): Promise<void> {
    const rooms = [this.studioRoom, this.guestRoom];
    this.studioRoom = null;
    this.guestRoom = null;
    for (const room of rooms) await room?.disconnect().catch(() => undefined);
  }

  /** Personnes de la salle du studio (vide tant qu'on n'a pas rejoint). */
  get studioSources(): ProgramSource[] {
    return this.studioRoom?.sources?.() ?? [];
  }

  /** Version du studio connue, pour les tests et l'affichage. */
  get knownStudioVersion(): number {
    return this.studioVersion;
  }
}
