import {
  Room,
  RoomEvent,
  Track,
  VideoPresets,
  type LocalTrackPublication,
  type Participant,
  type RemoteTrack,
  type RemoteTrackPublication,
} from 'livekit-client';
import type { RoomAccess } from './api.ts';
import type { RoomConnector, RoomHandle } from './controller.ts';
import type { ProgramSource } from './program.ts';
import { TileGrid, type El } from './tiles.ts';

const label = (p: Participant): string => p.name ?? p.identity;

/**
 * Connexion LiveKit avec les réglages de l'ADR-0006 : H.264, simulcast à deux couches (1080p et 360p), débit plafonné à
 * 6 Mb/s, abonnement adaptatif et dynacast. L'identité de salle est celle du jeton, attribuée par le serveur.
 * Les vidéos sont affichées dans `mediaRoot`, un conteneur qui survit aux redessins de la page.
 */
export class LiveKitConnector implements RoomConnector {
  private readonly mediaRoot: HTMLElement;

  constructor(mediaRoot: HTMLElement) {
    this.mediaRoot = mediaRoot;
  }

  async connect(access: RoomAccess): Promise<RoomHandle> {
    const grid = new TileGrid(this.mediaRoot as unknown as El, document);
    grid.clear();
    const videos = new Map<string, HTMLVideoElement>();
    const room = new Room({
      adaptiveStream: true,
      dynacast: true,
      videoCaptureDefaults: { resolution: VideoPresets.h1080.resolution },
      publishDefaults: {
        videoCodec: 'h264',
        simulcast: true,
        videoSimulcastLayers: [VideoPresets.h360],
        videoEncoding: { maxBitrate: 6_000_000, maxFramerate: 30 },
      },
    });

    const showVideo = (
      participant: Participant,
      attach: () => HTMLMediaElement,
      local: boolean,
    ): void => {
      const element = attach();
      element.setAttribute('playsinline', '');
      if (element instanceof HTMLVideoElement) videos.set(participant.identity, element);
      if (local) element.muted = true;
      grid.setVideo(participant.identity, label(participant), element as unknown as El, local);
    };

    room.on(
      RoomEvent.TrackSubscribed,
      (track: RemoteTrack, _pub: RemoteTrackPublication, participant) => {
        if (track.kind === Track.Kind.Video) showVideo(participant, () => track.attach(), false);
        else if (track.kind === Track.Kind.Audio)
          grid.addAudio(track.sid ?? participant.identity, track.attach() as unknown as El);
      },
    );
    room.on(RoomEvent.TrackUnsubscribed, (track: RemoteTrack, _pub, participant) => {
      track.detach();
      if (track.kind === Track.Kind.Video) {
        videos.delete(participant.identity);
        grid.removeVideo(participant.identity);
      } else if (track.kind === Track.Kind.Audio)
        grid.removeAudio(track.sid ?? participant.identity);
    });
    room.on(RoomEvent.LocalTrackPublished, (publication: LocalTrackPublication, participant) => {
      // Sa propre vidéo, sans son (sinon écho).
      if (publication.kind === Track.Kind.Video && publication.track)
        showVideo(
          participant,
          () => publication.track?.attach() ?? document.createElement('video'),
          true,
        );
    });
    room.on(RoomEvent.LocalTrackUnpublished, (publication: LocalTrackPublication, participant) => {
      publication.track?.detach();
      if (publication.kind === Track.Kind.Video) {
        videos.delete(participant.identity);
        grid.removeVideo(participant.identity);
      }
    });
    room.on(RoomEvent.ParticipantConnected, (participant) => {
      grid.ensure(participant.identity, label(participant), false);
    });
    room.on(RoomEvent.ParticipantDisconnected, (participant) => {
      videos.delete(participant.identity);
      grid.removeParticipant(participant.identity);
    });

    await room.connect(access.url, access.token);
    grid.ensure(room.localParticipant.identity, label(room.localParticipant), true);
    for (const remote of room.remoteParticipants.values())
      grid.ensure(remote.identity, label(remote), false);
    await room.localParticipant.setMicrophoneEnabled(true);
    await room.localParticipant.setCameraEnabled(true);

    const names = (): string[] => [
      `${label(room.localParticipant)} (vous)`,
      ...[...room.remoteParticipants.values()].map(label),
    ];
    const toSource = (p: Participant, local: boolean): ProgramSource => ({
      id: p.identity,
      name: label(p),
      local,
      video: videos.get(p.identity) ?? null,
      level: () => p.audioLevel,
    });
    return {
      participants: names,
      sources: () => [
        toSource(room.localParticipant, true),
        ...[...room.remoteParticipants.values()].map((p) => toSource(p, false)),
      ],
      disconnect: async () => {
        await room.disconnect();
        grid.clear();
      },
      onChange: (callback) => {
        for (const event of [
          RoomEvent.ParticipantConnected,
          RoomEvent.ParticipantDisconnected,
          RoomEvent.Reconnecting,
          RoomEvent.Reconnected,
          RoomEvent.Disconnected,
        ])
          room.on(event, callback);
      },
    };
  }
}
