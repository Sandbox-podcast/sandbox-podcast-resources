/**
 * Page cliente du POC 1 : se connecte à LiveKit, publie une caméra (factice) et un micro,
 * expose des statistiques WebRTC. Pilotée depuis Node par Playwright via `window.poc`.
 */
import {
  ConnectionState,
  Room,
  RoomEvent,
  Track,
  VideoPresets,
  createLocalAudioTrack,
  createLocalVideoTrack,
  LocalVideoTrack,
  type RoomConnectOptions,
} from 'livekit-client';

export interface PublishOptions {
  codec: 'h264' | 'vp8' | 'vp9' | 'av1';
  width: number;
  height: number;
  fps: number;
  maxBitrate: number;
  simulcast: boolean;
  degradation: 'default' | 'maintain-resolution' | 'maintain-framerate' | 'balanced';
  /**
   * `camera` : caméra factice de Chrome. `video` : vidéo animée jouée dans la page (contenu complexe).
   * `sync` : fichier à repères (éclair + bip toutes les 10 s, POC 4) dont l'image ET le son sont publiés.
   */
  source: 'camera' | 'video' | 'sync';
  sourceUrl: string;
  /** Nombre de couches simulcast (2 : 1080p et 360p ; 3 : couches par défaut). */
  layers: 2 | 3;
  /** Si > 0 : demande une image clé toutes les N secondes (RTCRtpSender.generateKeyFrame). */
  keyframeEverySec: number;
}

export interface VideoStats {
  encoderImplementation: string | undefined;
  codec: string | undefined;
  frameWidth: number | undefined;
  frameHeight: number | undefined;
  framesPerSecond: number | undefined;
  framesSent: number | undefined;
  bytesSent: number | undefined;
  targetBitrate: number | undefined;
  qualityLimitationReason: string | undefined;
  packetsSent: number | undefined;
  nackCount: number | undefined;
  keyFramesEncoded: number | undefined;
  totalEncodeTime: number | undefined;
  framesEncoded: number | undefined;
  rid: string | undefined;
}

export interface PocStats {
  at: number;
  video: VideoStats[];
  remoteInbound: {
    packetsLost: number | undefined;
    jitter: number | undefined;
    roundTripTime: number | undefined;
  }[];
  pair: {
    currentRoundTripTime: number | undefined;
    availableOutgoingBitrate: number | undefined;
    localCandidateType: string | undefined;
    protocol: string | undefined;
  };
}

const events: { t: number; event: string }[] = [];
const startedAt = performance.now();
const note = (event: string): void => {
  events.push({ t: Math.round(performance.now() - startedAt), event });
};

let room: Room | undefined;
let videoTrack: LocalVideoTrack | undefined;
/** Piste audio du fichier joué (source `sync`) : publiée à la place du micro. */
let capturedAudio: MediaStreamTrack | undefined;

const num = (value: unknown): number | undefined => (typeof value === 'number' ? value : undefined);
const str = (value: unknown): string | undefined => (typeof value === 'string' ? value : undefined);

async function connect(
  url: string,
  token: string,
  rtcConfig?: RTCConfiguration,
  forceRelay = false,
  adaptive = false,
): Promise<{ identity: string; state: string }> {
  // adaptive : abonnement adapté à la taille d'affichage et publication des seules couches utiles.
  const r = new Room({ adaptiveStream: adaptive, dynacast: adaptive });
  room = r;
  r.on(RoomEvent.ConnectionStateChanged, (s) => {
    note(`état de connexion : ${s}`);
  });
  r.on(RoomEvent.Reconnecting, () => {
    note('reconnexion en cours');
  });
  r.on(RoomEvent.SignalReconnecting, () => {
    note('reconnexion du signal en cours');
  });
  r.on(RoomEvent.Reconnected, () => {
    note('reconnecté');
  });
  r.on(RoomEvent.Disconnected, (reason) => {
    note(`déconnecté (${String(reason)})`);
  });
  r.on(RoomEvent.LocalTrackPublished, (pub) => {
    note(`piste publiée : ${pub.kind} ${pub.trackSid}`);
  });
  r.on(RoomEvent.TrackSubscribed, (track) => {
    // On rend les vidéos distantes pour que le décodage ait réellement lieu.
    if (track.kind === Track.Kind.Video) {
      const element = track.attach() as HTMLVideoElement;
      element.width = 320;
      element.height = 180;
      element.muted = true;
      document.body.appendChild(element);
    } else {
      track.attach();
    }
  });
  const options: RoomConnectOptions = {
    ...(rtcConfig ? { rtcConfig } : {}),
  };
  if (forceRelay) options.rtcConfig = { ...(options.rtcConfig ?? {}), iceTransportPolicy: 'relay' };
  await r.connect(url, token, options);
  return { identity: r.localParticipant.identity, state: r.state };
}

async function publish(options: PublishOptions): Promise<{ videoSid: string | undefined }> {
  if (!room) throw new Error('pas de salle');
  if (options.source === 'video' || options.source === 'sync') {
    const element = document.createElement('video');
    element.src = options.sourceUrl;
    element.loop = options.source === 'video';
    element.muted = options.source === 'video';
    element.playsInline = true;
    document.body.appendChild(element);
    await element.play();
    const stream = (
      element as HTMLVideoElement & { captureStream: (fps?: number) => MediaStream }
    ).captureStream(options.fps);
    const mediaTrack = stream.getVideoTracks()[0];
    if (!mediaTrack) throw new Error('aucune piste vidéo capturée');
    videoTrack = new LocalVideoTrack(mediaTrack, undefined, true);
    capturedAudio = stream.getAudioTracks()[0];
  } else {
    videoTrack = await createLocalVideoTrack({
      resolution: { width: options.width, height: options.height, frameRate: options.fps },
    });
  }
  const settings = videoTrack.mediaStreamTrack.getSettings();
  note(
    `caméra : ${String(settings.width)}x${String(settings.height)} à ${String(settings.frameRate)} images/s`,
  );
  const publication = await room.localParticipant.publishTrack(videoTrack, {
    videoCodec: options.codec,
    simulcast: options.simulcast,
    ...(options.simulcast && options.layers === 2
      ? { videoSimulcastLayers: [VideoPresets.h360] }
      : {}),
    ...(options.degradation === 'default' ? {} : { degradationPreference: options.degradation }),
    videoEncoding: { maxBitrate: options.maxBitrate, maxFramerate: options.fps },
    source: Track.Source.Camera,
  });
  if (options.keyframeEverySec > 0) {
    const sender = videoTrack.sender;
    const Transform = (
      globalThis as unknown as {
        RTCRtpScriptTransform?: new (worker: Worker, options: unknown) => unknown;
      }
    ).RTCRtpScriptTransform;
    if (sender && Transform) {
      // Le transformateur d'encodage tourne dans un Worker : c'est là que generateKeyFrame existe.
      const source = `onrtctransform = (event) => {
        const t = event.transformer;
        setInterval(() => { try { void t.generateKeyFrame().catch(() => {}); } catch (e) {} }, t.options.everyMs);
        t.readable.pipeTo(t.writable);
      };`;
      const worker = new Worker(
        URL.createObjectURL(new Blob([source], { type: 'text/javascript' })),
      );
      (sender as unknown as { transform: unknown }).transform = new Transform(worker, {
        everyMs: options.keyframeEverySec * 1000,
      });
      note(`images clés forcées toutes les ${String(options.keyframeEverySec)} s`);
    } else {
      note('RTCRtpScriptTransform indisponible');
    }
  }
  if (options.source === 'sync') {
    if (!capturedAudio) throw new Error('aucune piste audio capturée du fichier à repères');
    await room.localParticipant.publishTrack(capturedAudio, { source: Track.Source.Microphone });
    return { videoSid: publication.trackSid };
  }
  const audio = await createLocalAudioTrack({
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,
  });
  await room.localParticipant.publishTrack(audio.mediaStreamTrack, {
    source: Track.Source.Microphone,
  });
  return { videoSid: publication.trackSid };
}

async function stats(): Promise<PocStats> {
  const sender = videoTrack?.sender;
  const result: PocStats = {
    at: Date.now(),
    video: [],
    remoteInbound: [],
    pair: {
      currentRoundTripTime: undefined,
      availableOutgoingBitrate: undefined,
      localCandidateType: undefined,
      protocol: undefined,
    },
  };
  if (!sender) return result;
  const report = await sender.getStats();
  const candidates = new Map<string, { candidateType?: string; protocol?: string }>();
  report.forEach((entry: Record<string, unknown>) => {
    if (entry['type'] === 'local-candidate') {
      const candidateType = str(entry['candidateType']);
      const protocol = str(entry['protocol']);
      candidates.set(String(entry['id']), {
        ...(candidateType ? { candidateType } : {}),
        ...(protocol ? { protocol } : {}),
      });
    }
  });
  const codecs = new Map<string, string>();
  report.forEach((entry: Record<string, unknown>) => {
    if (entry['type'] === 'codec') codecs.set(String(entry['id']), String(entry['mimeType']));
  });
  report.forEach((entry: Record<string, unknown>) => {
    const type = entry['type'];
    if (type === 'outbound-rtp' && entry['kind'] === 'video') {
      result.video.push({
        encoderImplementation: str(entry['encoderImplementation']),
        codec: codecs.get(String(entry['codecId'])),
        frameWidth: num(entry['frameWidth']),
        frameHeight: num(entry['frameHeight']),
        framesPerSecond: num(entry['framesPerSecond']),
        framesSent: num(entry['framesSent']),
        bytesSent: num(entry['bytesSent']),
        targetBitrate: num(entry['targetBitrate']),
        qualityLimitationReason: str(entry['qualityLimitationReason']),
        packetsSent: num(entry['packetsSent']),
        nackCount: num(entry['nackCount']),
        keyFramesEncoded: num(entry['keyFramesEncoded']),
        totalEncodeTime: num(entry['totalEncodeTime']),
        framesEncoded: num(entry['framesEncoded']),
        rid: str(entry['rid']),
      });
    } else if (type === 'remote-inbound-rtp' && entry['kind'] === 'video') {
      result.remoteInbound.push({
        packetsLost: num(entry['packetsLost']),
        jitter: num(entry['jitter']),
        roundTripTime: num(entry['roundTripTime']),
      });
    } else if (
      type === 'candidate-pair' &&
      entry['nominated'] === true &&
      entry['state'] === 'succeeded'
    ) {
      const local = candidates.get(String(entry['localCandidateId']));
      result.pair = {
        currentRoundTripTime: num(entry['currentRoundTripTime']),
        availableOutgoingBitrate: num(entry['availableOutgoingBitrate']),
        localCandidateType: local?.candidateType,
        protocol: local?.protocol,
      };
    }
  });
  return result;
}

async function simulate(
  scenario:
    | 'signal-reconnect'
    | 'full-reconnect'
    | 'resume-reconnect'
    | 'force-tcp'
    | 'force-tls'
    | 'speaker'
    | 'migration'
    | 'node-failure',
): Promise<void> {
  if (!room) throw new Error('pas de salle');
  note(`simulation : ${scenario}`);
  await room.simulateScenario(scenario);
}

function info(): {
  userAgent: string;
  state: string;
  videoCodecs: string[];
  remoteVideos: number;
  decodedFrames: number;
} {
  const capabilities = RTCRtpSender.getCapabilities('video')?.codecs ?? [];
  const videos = Array.from(document.querySelectorAll('video'));
  return {
    userAgent: navigator.userAgent,
    state: room?.state ?? ConnectionState.Disconnected,
    videoCodecs: [
      ...new Set(
        capabilities.map((c) => `${c.mimeType}${c.sdpFmtpLine ? ` (${c.sdpFmtpLine})` : ''}`),
      ),
    ],
    remoteVideos: videos.length,
    decodedFrames: videos.reduce(
      (sum, v) => sum + (v.getVideoPlaybackQuality().totalVideoFrames || 0),
      0,
    ),
  };
}

async function disconnect(): Promise<void> {
  await room?.disconnect();
}

const api = { connect, publish, stats, simulate, info, disconnect, events: () => events };
(window as unknown as { poc: typeof api }).poc = api;
export type PocApi = typeof api;
