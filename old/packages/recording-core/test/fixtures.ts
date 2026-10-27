import type { ChunkMetadata } from '../src';

export const CHECKSUM = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad';

export function makeChunk(overrides: Partial<ChunkMetadata> = {}): ChunkMetadata {
  const sequenceNumber = overrides.sequenceNumber ?? 0;
  return {
    recordingSessionId: 'session-1',
    participantId: 'participant-a',
    trackId: 'track-video-a',
    sequenceNumber,
    startTimestampMs: sequenceNumber * 2000,
    endTimestampMs: (sequenceNumber + 1) * 2000,
    durationMs: 2000,
    codec: 'vp9',
    container: 'webm',
    sizeBytes: 1_000_000,
    checksum: CHECKSUM,
    uploadStatus: 'VERIFIED',
    localCopy: 'DURABLE',
    ...overrides,
  };
}
