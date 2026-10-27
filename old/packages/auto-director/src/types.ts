export type ParticipantId = string;

/** Niveaux audio instantanés, en dBFS (0 = saturation, -100 = silence), à un instant donné. */
export interface LevelFrame {
  timeMs: number;
  levelsDb: Readonly<Record<ParticipantId, number>>;
}

export type ShotMode = 'GROUP' | 'SPEAKER_FOCUS' | 'DUO' | 'PRESENTATION' | 'REACTION' | 'MANUAL';

/** Les scènes de la régie que le réalisateur peut demander. */
export interface SceneCatalog {
  group: string;
  focus: (speaker: ParticipantId) => string;
  duo: (a: ParticipantId, b: ParticipantId) => string;
  presentation: string;
}

export interface Shot {
  mode: ShotMode;
  participants: readonly ParticipantId[];
  sceneId: string;
}

export type DecisionSource = 'AUTO' | 'MANUAL';

/** Entrée du journal de mise en scène (master prompt §11.2). */
export interface DirectorDecision {
  timestampMs: number;
  /** Le plan décidé : mode, participants cadrés et identifiant de scène. */
  shot: Shot;
  source: DecisionSource;
  /** Locuteur actif au moment de la décision, `null` s'il n'y en a pas. */
  speakerId: ParticipantId | null;
  reason: string;
  /** 0 à 1, une aide pour l'humain, pas une probabilité calibrée. */
  confidence: number;
}

export interface SpeakerSnapshot {
  speakers: readonly ParticipantId[];
  /** Locuteur dominant, stable (hystérésis), ou `null`. */
  active: ParticipantId | null;
  /** Depuis quand le locuteur actif l'est, en ms, ou `null`. */
  activeSinceMs: number | null;
  /** Écart, en dB, entre le locuteur actif et le plus fort des autres participants (0 à 30). */
  marginDb: number;
  /** Plusieurs personnes parlent en même temps depuis assez longtemps pour être une conversation croisée. */
  crosstalk: boolean;
  /** Ils sont deux à se répondre vivement. */
  duo: readonly [ParticipantId, ParticipantId] | null;
  /** Dernière fois que quelqu'un parlait, `null` si personne n'a parlé. */
  lastSpeechMs: number | null;
}
