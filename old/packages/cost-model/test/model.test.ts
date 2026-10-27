import { describe, expect, it } from 'vitest';
import { DEFAULTS, episodeQuantities, price } from '../src/index.ts';

describe('quantités', () => {
  it('stockage brut : participants × (vidéo + audio) × durée', () => {
    // 1 participant, 1 h, 8 Mb/s + 0 audio = 1 Mo/s × 3600 s = 3,6 Go.
    const q = episodeQuantities({ participants: 1, hours: 1, videoMbps: 8, audioKbps: 0 });
    expect(q.rawStorageGb).toBeCloseTo(3.6, 9);
    expect(
      episodeQuantities({ participants: 4, hours: 2, videoMbps: 8, audioKbps: 0 }).rawStorageGb,
    ).toBeCloseTo(3.6 * 4 * 2, 9);
  });

  it('compte l’audio : 24 kb/s pendant 1 h = 10,8 Mo par participant', () => {
    const withAudio = episodeQuantities({ participants: 1, videoMbps: 0, audioKbps: 24 });
    expect(withAudio.rawStorageGb).toBeCloseTo(0.0108, 9);
  });

  it('exports : un replay plus des clips', () => {
    // Replay 8 Mb/s sur 1 h = 3,6 Go ; 5 clips de 60 s à 6 Mb/s = 5 × 60 × 0,75 Mo = 0,225 Go.
    const q = episodeQuantities({
      hours: 1,
      replayMbps: 8,
      clips: 5,
      clipSeconds: 60,
      clipMbps: 6,
    });
    expect(q.exportStorageGb).toBeCloseTo(3.6 + 0.225, 9);
  });

  it('Go-mois : chaque catégorie avec sa durée de conservation', () => {
    const q = episodeQuantities({ rawRetentionMonths: 12, exportRetentionMonths: 3 });
    expect(q.storageGbMonths).toBeCloseTo(q.rawStorageGb * 12 + q.exportStorageGb * 3, 9);
    expect(
      episodeQuantities({ rawRetentionMonths: 0, exportRetentionMonths: 0 }).storageGbMonths,
    ).toBe(0);
  });

  it('trafic sortant : le Producer reçoit la couche haute, chaque invité la couche basse', () => {
    // 3 participants, 1 h, audio nul : Producer 2 × 4 Mb/s ; 2 invités × (2 × 0,6 Mb/s) = 8 + 2,4 = 10,4 Mb/s.
    const q = episodeQuantities({
      participants: 3,
      hours: 1,
      videoMbps: 4,
      lowLayerMbps: 0.6,
      audioKbps: 0,
    });
    expect(q.sfuEgressGb).toBeCloseTo((10.4 * 1e6 * 3600) / 8 / 1e9, 9);
  });

  it('un seul participant ne génère aucun trafic sortant', () => {
    expect(episodeQuantities({ participants: 1 }).sfuEgressGb).toBe(0);
  });

  it('TURN : part du trafic sortant', () => {
    const none = episodeQuantities({ turnShare: 0 });
    const some = episodeQuantities({ turnShare: 0.25 });
    expect(none.turnGb).toBe(0);
    expect(some.turnGb).toBeCloseTo(some.sfuEgressGb * 0.25, 9);
  });

  it('calcul : Egress par piste (2 par participant), SFU par participant', () => {
    const q = episodeQuantities({
      participants: 4,
      hours: 2,
      egressCorePerTrack: 0.03,
      sfuCorePerParticipant: 0.04,
    });
    expect(q.egressCoreHours).toBeCloseTo(8 * 0.03 * 2, 9);
    expect(q.sfuCoreHours).toBeCloseTo(4 * 0.04 * 2, 9);
  });

  it('transcription : par piste ou sur le mélange seulement', () => {
    expect(
      episodeQuantities({ participants: 4, hours: 1.5, transcribePerTrack: true })
        .transcriptionMinutes,
    ).toBe(360);
    expect(
      episodeQuantities({ participants: 4, hours: 1.5, transcribePerTrack: false })
        .transcriptionMinutes,
    ).toBe(90);
  });

  it('refuse des entrées absurdes', () => {
    expect(() => episodeQuantities({ participants: 0 })).toThrow(/au moins 1 participant/);
    expect(() => episodeQuantities({ hours: 0 })).toThrow(/durée positive/);
    expect(() => episodeQuantities({ hours: -1 })).toThrow(/durée positive/);
  });

  it('les valeurs par défaut sont celles documentées', () => {
    expect(DEFAULTS).toMatchObject({
      participants: 4,
      hours: 1,
      videoMbps: 4,
      audioKbps: 24,
      turnShare: 0,
    });
  });
});

describe('prix', () => {
  const q = episodeQuantities({ participants: 2, hours: 1, turnShare: 0.5 });

  it('sans aucun prix, rien n’est chiffré et tout est signalé manquant', () => {
    const priced = price(q, {});
    expect(priced.total).toBeNull();
    expect(priced.missing).toEqual(['storage', 'network', 'compute', 'transcription', 'turn']);
  });

  it('chiffre seulement les postes dont le prix est fourni et signale les autres', () => {
    const priced = price(q, { storagePerGbMonth: 0.02, transcriptionPerMinute: 0.01 });
    expect(priced.lines.storage).toBeCloseTo(q.storageGbMonths * 0.02, 9);
    expect(priced.lines.transcription).toBeCloseTo(q.transcriptionMinutes * 0.01, 9);
    expect(priced.lines.network).toBeNull();
    expect(priced.total).toBeCloseTo(q.storageGbMonths * 0.02 + q.transcriptionMinutes * 0.01, 9);
    expect(priced.missing).toEqual(['network', 'compute', 'turn']);
  });

  it('un prix nul est un prix : le poste vaut 0 et n’est pas manquant', () => {
    const priced = price(q, { corePerHour: 0 });
    expect(priced.lines.compute).toBe(0);
    expect(priced.missing).not.toContain('compute');
    expect(priced.total).toBe(0);
  });

  it('additionne tous les postes', () => {
    const priced = price(q, {
      storagePerGbMonth: 1,
      egressPerGb: 1,
      corePerHour: 1,
      transcriptionPerMinute: 1,
      turnPerGb: 1,
    });
    const expected =
      q.storageGbMonths +
      q.sfuEgressGb +
      q.egressCoreHours +
      q.sfuCoreHours +
      q.transcriptionMinutes +
      q.turnGb;
    expect(priced.total).toBeCloseTo(expected, 9);
    expect(priced.missing).toEqual([]);
  });
});
