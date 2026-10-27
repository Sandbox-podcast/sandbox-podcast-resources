/**
 * Modèle de coût d'un épisode : des QUANTITÉS (Go, heures-cœur, minutes), puis un prix seulement si
 * l'appelant fournit des prix unitaires. Aucun prix n'est inventé ici : l'hébergeur, les fournisseurs
 * IA et les tarifs sont des décisions du propriétaire. Les valeurs par défaut sont soit mesurées
 * (source indiquée), soit des hypothèses signalées comme telles.
 */

export interface EpisodeInput {
  /** Personnes qui publient audio et vidéo (invités, animateurs, Producer). */
  participants: number;
  hours: number;
  /** Débit vidéo publié par participant, Mb/s (couche haute). */
  videoMbps: number;
  /** Débit audio par participant, kb/s. */
  audioKbps: number;
  /** Débit de la couche basse reçue par les invités, Mb/s. */
  lowLayerMbps: number;
  /** Débit du replay exporté, Mb/s. */
  replayMbps: number;
  /** Nombre de clips et durée moyenne, secondes. */
  clips: number;
  clipSeconds: number;
  clipMbps: number;
  /** Mois de conservation des pistes brutes et des exports. */
  rawRetentionMonths: number;
  exportRetentionMonths: number;
  /** Transcrire chaque piste séparément (sinon seulement le mélange). */
  transcribePerTrack: boolean;
  /** Part du trafic de signalisation et de média qui passe par un relais TURN (0 à 1). */
  turnShare: number;
  /** Cœurs utilisés par piste enregistrée (Egress) et par participant (SFU). */
  egressCorePerTrack: number;
  sfuCorePerParticipant: number;
}

/**
 * Valeurs par défaut.
 * Mesurées (poste de développement, voir docs/pocs) : audio ≈ 22 kb/s (POC 4) ; Egress ≈ 3 % d'un cœur par
 * piste (12 à 13 % pour 4 pistes, 18 % pour 6) ; SFU ≈ 2 % d'un cœur par participant publiant, sans abonnés
 * réels (5 à 7 % pour 2 à 3).
 * Hypothèses, non mesurées : débits vidéo (2 à 6 Mb/s mesurés sur du contenu animé bruité, un visage parlant
 * est probablement plus léger) ; couche basse 0,6 Mb/s ; replay 8 Mb/s ; clips 6 Mb/s ; TURN 0 % ;
 * SFU avec abonnés réels : valeur de précaution double de la mesure.
 */
export const DEFAULTS: EpisodeInput = {
  participants: 4,
  hours: 1,
  videoMbps: 4,
  audioKbps: 24,
  lowLayerMbps: 0.6,
  replayMbps: 8,
  clips: 5,
  clipSeconds: 60,
  clipMbps: 6,
  rawRetentionMonths: 12,
  exportRetentionMonths: 12,
  transcribePerTrack: true,
  turnShare: 0,
  egressCorePerTrack: 0.03,
  sfuCorePerParticipant: 0.04,
};

export interface Quantities {
  /** Stockage en gigaoctets (10⁹ octets). */
  rawStorageGb: number;
  exportStorageGb: number;
  /** Gigaoctets-mois à facturer. */
  storageGbMonths: number;
  /** Trafic sortant du SFU vers les participants, Go. */
  sfuEgressGb: number;
  /** Dont celui relayé par TURN. */
  turnGb: number;
  /** Heures-cœur : enregistrement serveur (Egress) et SFU. */
  egressCoreHours: number;
  sfuCoreHours: number;
  /** Minutes d'audio à transcrire. */
  transcriptionMinutes: number;
}

const GB = 1e9;
const bytesPerSecond = (mbps: number): number => (mbps * 1e6) / 8;

export function episodeQuantities(overrides: Partial<EpisodeInput> = {}): Quantities {
  const e: EpisodeInput = { ...DEFAULTS, ...overrides };
  if (e.participants < 1 || e.hours <= 0)
    throw new Error('au moins 1 participant et une durée positive');
  const seconds = e.hours * 3600;
  const tracks = e.participants * 2;

  const perParticipantBytesPerSecond = bytesPerSecond(e.videoMbps) + (e.audioKbps * 1000) / 8;
  const rawStorageGb = (e.participants * perParticipantBytesPerSecond * seconds) / GB;
  const exportStorageGb =
    (bytesPerSecond(e.replayMbps) * seconds +
      e.clips * e.clipSeconds * bytesPerSecond(e.clipMbps)) /
    GB;

  // Le Producer reçoit les autres participants en couche haute ; chaque invité reçoit les autres en couche basse.
  const others = e.participants - 1;
  const audioMbps = (e.audioKbps / 1000) * others;
  const producerMbps = others * e.videoMbps + audioMbps;
  const guestMbps = others * e.lowLayerMbps + audioMbps;
  const guests = Math.max(0, e.participants - 1);
  const sfuEgressGb = ((producerMbps + guests * guestMbps) * 1e6 * seconds) / 8 / GB;

  return {
    rawStorageGb,
    exportStorageGb,
    storageGbMonths:
      rawStorageGb * e.rawRetentionMonths + exportStorageGb * e.exportRetentionMonths,
    sfuEgressGb,
    turnGb: sfuEgressGb * e.turnShare,
    egressCoreHours: tracks * e.egressCorePerTrack * e.hours,
    sfuCoreHours: e.participants * e.sfuCorePerParticipant * e.hours,
    transcriptionMinutes: (e.transcribePerTrack ? e.participants : 1) * e.hours * 60,
  };
}

/** Prix unitaires fournis par l'appelant. Les prix absents laissent le poste correspondant à `null`. */
export interface Prices {
  /** Par Go-mois de stockage. */
  storagePerGbMonth?: number;
  /** Par Go sortant (SFU et relais TURN confondus). */
  egressPerGb?: number;
  /** Par heure-cœur de calcul (serveurs média). */
  corePerHour?: number;
  /** Par minute d'audio transcrite. */
  transcriptionPerMinute?: number;
  /** Prix du trafic relayé par TURN en plus du trafic sortant. */
  turnPerGb?: number;
}

export interface PricedEpisode {
  quantities: Quantities;
  lines: Record<'storage' | 'network' | 'compute' | 'transcription' | 'turn', number | null>;
  /** Somme des postes chiffrés ; `null` si aucun prix n'a été fourni. */
  total: number | null;
  /** Postes sans prix : le total ne les compte pas. */
  missing: string[];
}

export function price(quantities: Quantities, prices: Prices): PricedEpisode {
  const line = (quantity: number, unit: number | undefined): number | null =>
    unit === undefined ? null : quantity * unit;
  const lines = {
    storage: line(quantities.storageGbMonths, prices.storagePerGbMonth),
    network: line(quantities.sfuEgressGb, prices.egressPerGb),
    compute: line(quantities.egressCoreHours + quantities.sfuCoreHours, prices.corePerHour),
    transcription: line(quantities.transcriptionMinutes, prices.transcriptionPerMinute),
    turn: line(quantities.turnGb, prices.turnPerGb),
  };
  const known = Object.values(lines).filter((v): v is number => v !== null);
  return {
    quantities,
    lines,
    total: known.length === 0 ? null : known.reduce((a, b) => a + b, 0),
    missing: Object.entries(lines)
      .filter(([, v]) => v === null)
      .map(([k]) => k),
  };
}
