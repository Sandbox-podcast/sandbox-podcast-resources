import { randomBytes } from 'node:crypto';
import { networkInterfaces } from 'node:os';

/** Secrets de développement local, générés au premier lancement et jamais commités. */
export interface LocalConfig {
  livekitApiKey: string;
  livekitApiSecret: string;
  s3AccessKey: string;
  s3SecretKey: string;
  s3Bucket: string;
  /** Adresse que LiveKit annonce aux clients : joignable depuis le poste et depuis les conteneurs. */
  nodeIp: string;
}

/**
 * Première adresse IPv4 privée du poste (réseau local), sinon 127.0.0.1.
 * Chrome (sur le poste) et Egress (dans Docker) doivent tous deux pouvoir la joindre.
 */
export function detectNodeIp(): string {
  for (const addresses of Object.values(networkInterfaces())) {
    for (const address of addresses ?? []) {
      if (
        address.family === 'IPv4' &&
        !address.internal &&
        /^(192\.168\.|10\.)/.test(address.address)
      ) {
        return address.address;
      }
    }
  }
  return '127.0.0.1';
}

const token = (bytes: number): string => randomBytes(bytes).toString('base64url');

export function generateConfig(): LocalConfig {
  return {
    livekitApiKey: `API${token(9)}`,
    livekitApiSecret: token(36),
    s3AccessKey: `AK${token(9)}`,
    s3SecretKey: token(36),
    s3Bucket: 'recordings',
    nodeIp: detectNodeIp(),
  };
}

/** Relit le contenu de `.local/.env` produit par `renderEnvFile`. */
export function parseEnvFile(text: string): LocalConfig {
  const values = new Map<string, string>();
  for (const line of text.split(/\r?\n/)) {
    const match = /^([A-Z0-9_]+)=(.*)$/.exec(line);
    if (match?.[1] !== undefined && match[2] !== undefined) values.set(match[1], match[2]);
  }
  const need = (key: string): string => {
    const value = values.get(key);
    if (!value) throw new Error(`Variable manquante dans .local/.env : ${key}`);
    return value;
  };
  return {
    livekitApiKey: need('LIVEKIT_API_KEY'),
    livekitApiSecret: need('LIVEKIT_API_SECRET'),
    s3AccessKey: need('S3_ACCESS_KEY'),
    s3SecretKey: need('S3_SECRET_KEY'),
    s3Bucket: need('S3_BUCKET'),
    nodeIp: values.get('NODE_IP') ?? '127.0.0.1',
  };
}

/** Fichier lu par `docker compose --env-file`. */
export function renderEnvFile(config: LocalConfig): string {
  return [
    `LIVEKIT_API_KEY=${config.livekitApiKey}`,
    `LIVEKIT_API_SECRET=${config.livekitApiSecret}`,
    `S3_ACCESS_KEY=${config.s3AccessKey}`,
    `S3_SECRET_KEY=${config.s3SecretKey}`,
    `S3_BUCKET=${config.s3Bucket}`,
    `NODE_IP=${config.nodeIp}`,
    '',
  ].join('\n');
}

/** Identité unique reconnue par la passerelle S3 de SeaweedFS. */
export function renderS3Config(config: LocalConfig): string {
  return JSON.stringify(
    {
      identities: [
        {
          name: 'poc',
          credentials: [{ accessKey: config.s3AccessKey, secretKey: config.s3SecretKey }],
          actions: ['Admin', 'Read', 'Write', 'List', 'Tagging'],
        },
      ],
    },
    null,
    2,
  );
}
