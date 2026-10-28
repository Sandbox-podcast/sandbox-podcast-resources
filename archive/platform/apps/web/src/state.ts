import type {
  Episode,
  EpisodeSummary,
  InvitationInfo,
  PodcastSummary,
  StudioState,
  User,
} from './api.ts';
import type { DeviceReport } from './devices.ts';
import type { Route } from './router.ts';

export type Loadable<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'ready'; data: T }
  | { status: 'error'; message: string; correlationId: string | null };

export const idle = <T>(): Loadable<T> => ({ status: 'idle' });

export interface Flash {
  kind: 'error' | 'ok';
  text: string;
}

export type RoomStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export interface RoomView {
  status: RoomStatus;
  participants: string[];
  message: string | null;
}

export interface StudioPage {
  info: Loadable<StudioState>;
  room: RoomView;
  /** Participant (identité de salle) de l'utilisateur, une fois le jeton obtenu. */
  participantId: string | null;
}

export interface GuestPage {
  info: Loadable<InvitationInfo>;
  displayName: string;
  devices: DeviceReport | null;
  deviceMessage: string | null;
  consent: boolean;
  room: RoomView;
}

export interface AppState {
  route: Route;
  /** `null` : pas connecté ; `undefined` : on ne sait pas encore. */
  user: User | null | undefined;
  podcasts: Loadable<PodcastSummary[]>;
  episodes: Loadable<EpisodeSummary[]>;
  episode: Loadable<Episode>;
  studio: StudioPage;
  guest: GuestPage;
  flash: Flash | null;
  /** Liens d'invitation créés pendant cette visite (le jeton n'est montré qu'une fois). */
  invitationLinks: string[];
  busy: boolean;
}

const emptyRoom = (): RoomView => ({ status: 'disconnected', participants: [], message: null });

export function initialState(): AppState {
  return {
    route: { name: 'home' },
    user: undefined,
    podcasts: idle(),
    episodes: idle(),
    episode: idle(),
    studio: { info: idle(), room: emptyRoom(), participantId: null },
    guest: {
      info: idle(),
      displayName: '',
      devices: null,
      deviceMessage: null,
      consent: false,
      room: emptyRoom(),
    },
    flash: null,
    invitationLinks: [],
    busy: false,
  };
}
