import { describe, expect, it } from 'vitest';
import {
  generateConfig,
  parseEnvFile,
  renderEnvFile,
  renderS3Config,
} from '../src/lib/local-config.ts';
import { mediaJobs } from '../src/lib/media-commands.ts';

describe('generateConfig', () => {
  it('génère des secrets différents à chaque appel', () => {
    const first = generateConfig();
    const second = generateConfig();
    expect(first.livekitApiSecret).not.toBe(second.livekitApiSecret);
    expect(first.s3SecretKey).not.toBe(second.s3SecretKey);
  });

  it('génère des secrets d’au moins 32 caractères', () => {
    const config = generateConfig();
    expect(config.livekitApiSecret.length).toBeGreaterThanOrEqual(32);
    expect(config.s3SecretKey.length).toBeGreaterThanOrEqual(32);
  });
});

describe('renderEnvFile', () => {
  it('produit les variables attendues par compose.yaml', () => {
    const config = generateConfig();
    const lines = renderEnvFile(config).split('\n');
    expect(lines).toContain(`LIVEKIT_API_KEY=${config.livekitApiKey}`);
    expect(lines).toContain(`LIVEKIT_API_SECRET=${config.livekitApiSecret}`);
    expect(lines).toContain(`S3_ACCESS_KEY=${config.s3AccessKey}`);
    expect(lines).toContain(`S3_SECRET_KEY=${config.s3SecretKey}`);
    expect(lines).toContain('S3_BUCKET=recordings');
  });
});

describe('parseEnvFile', () => {
  it('relit ce que renderEnvFile a écrit', () => {
    const config = generateConfig();
    expect(parseEnvFile(renderEnvFile(config))).toEqual(config);
  });

  it('accepte les fins de ligne Windows', () => {
    const config = generateConfig();
    expect(parseEnvFile(renderEnvFile(config).replaceAll('\n', '\r\n'))).toEqual(config);
  });

  it('signale une variable manquante', () => {
    expect(() => parseEnvFile('LIVEKIT_API_KEY=abc\n')).toThrow(/LIVEKIT_API_SECRET/);
  });
});

describe('renderS3Config', () => {
  it('produit un JSON avec les identifiants générés', () => {
    const config = generateConfig();
    const parsed = JSON.parse(renderS3Config(config)) as {
      identities: { credentials: { accessKey: string; secretKey: string }[] }[];
    };
    expect(parsed.identities[0]?.credentials[0]).toEqual({
      accessKey: config.s3AccessKey,
      secretKey: config.s3SecretKey,
    });
  });
});

describe('mediaJobs', () => {
  const jobs = mediaJobs(90);

  it('prépare deux vidéos H.264 et deux audios Opus', () => {
    expect(jobs.map((job) => job.output)).toEqual(['a.h264', 'b.h264', 'a.ogg', 'b.ogg']);
  });

  it('demande du 1080p30 pour les vidéos', () => {
    for (const job of jobs.filter((j) => j.output.endsWith('.h264'))) {
      expect(job.args.join(' ')).toContain('size=1920x1080:rate=30');
    }
  });

  it('applique la durée demandée à chaque fichier', () => {
    for (const job of jobs) {
      const index = job.args.indexOf('-t');
      expect(job.args[index + 1]).toBe('90');
    }
  });
});
