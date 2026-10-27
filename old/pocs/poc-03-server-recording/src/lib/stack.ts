import { execFile } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { promisify } from 'node:util';
import {
  CreateBucketCommand,
  GetObjectCommand,
  HeadBucketCommand,
  ListObjectsV2Command,
  PutObjectCommand,
  S3Client,
} from '@aws-sdk/client-s3';
import { DirectFileOutput, EgressClient, RoomServiceClient, S3Upload } from 'livekit-server-sdk';
import { parseFfprobe, type MediaSummary } from './analyze.ts';
import { parseDockerStatsLine, type ContainerStats } from './docker-stats.ts';
import { parseEnvFile, type LocalConfig } from './local-config.ts';

const run = promisify(execFile);

export const stackDir = join(import.meta.dirname, '..', '..');
export const localDir = join(stackDir, '.local');

/** Adresses vues depuis la machine hôte (ports publiés par compose.yaml). */
export const LIVEKIT_HTTP_URL = 'http://localhost:7880';
export const S3_ENDPOINT = 'http://localhost:8333';

/** Adresse du stockage vue depuis le conteneur Egress (réseau Docker). */
const S3_ENDPOINT_FROM_EGRESS = 'http://s3:8333';

/**
 * Destination d'un fichier de piste, passée explicitement dans la requête Egress.
 * Constaté le 2026-10-05 : sans elle, Egress écrit sur son disque local (« Local upload failed »)
 * au lieu d'utiliser le bloc `s3` de sa configuration.
 */
export function trackFileOutput(config: LocalConfig, filepath: string): DirectFileOutput {
  return new DirectFileOutput({
    filepath,
    output: {
      case: 's3',
      value: new S3Upload({
        accessKey: config.s3AccessKey,
        secret: config.s3SecretKey,
        region: 'us-east-1',
        endpoint: S3_ENDPOINT_FROM_EGRESS,
        bucket: config.s3Bucket,
        forcePathStyle: true,
      }),
    },
  });
}

export async function loadConfig(): Promise<LocalConfig> {
  return parseEnvFile(await readFile(join(localDir, '.env'), 'utf8'));
}

export function createClients(config: LocalConfig) {
  return {
    rooms: new RoomServiceClient(LIVEKIT_HTTP_URL, config.livekitApiKey, config.livekitApiSecret),
    egress: new EgressClient(LIVEKIT_HTTP_URL, config.livekitApiKey, config.livekitApiSecret),
    s3: new S3Client({
      endpoint: S3_ENDPOINT,
      region: 'us-east-1',
      forcePathStyle: true,
      credentials: { accessKeyId: config.s3AccessKey, secretAccessKey: config.s3SecretKey },
    }),
  };
}

export async function ensureBucket(s3: S3Client, bucket: string): Promise<void> {
  try {
    await s3.send(new HeadBucketCommand({ Bucket: bucket }));
  } catch {
    await s3.send(new CreateBucketCommand({ Bucket: bucket }));
  }
}

export interface StoredObject {
  key: string;
  size: number;
  lastModified: Date | undefined;
}

export async function listObjects(
  s3: S3Client,
  bucket: string,
  prefix: string,
): Promise<StoredObject[]> {
  const response = await s3.send(new ListObjectsV2Command({ Bucket: bucket, Prefix: prefix }));
  return (response.Contents ?? []).flatMap((object) =>
    object.Key === undefined
      ? []
      : [{ key: object.Key, size: object.Size ?? 0, lastModified: object.LastModified }],
  );
}

export async function downloadObject(
  s3: S3Client,
  bucket: string,
  key: string,
): Promise<Uint8Array> {
  const response = await s3.send(new GetObjectCommand({ Bucket: bucket, Key: key }));
  if (!response.Body) throw new Error(`Objet vide : ${key}`);
  return response.Body.transformToByteArray();
}

export async function putObject(
  s3: S3Client,
  bucket: string,
  key: string,
  body: Uint8Array,
): Promise<void> {
  await s3.send(new PutObjectCommand({ Bucket: bucket, Key: key, Body: body }));
}

/** Analyse un fichier local avec ffprobe (arguments fixes, aucun argument utilisateur). */
export async function probeFile(path: string): Promise<MediaSummary> {
  const { stdout } = await run('ffprobe', [
    '-v',
    'error',
    '-show_format',
    '-show_streams',
    '-of',
    'json',
    path,
  ]);
  return parseFfprobe(JSON.parse(stdout) as unknown);
}

/** Lance un publieur de test en arrière-plan et retourne le nom de son conteneur. */
export async function startPublisher(
  service: 'publisher-a' | 'publisher-b' | 'publisher-s1' | 'publisher-s2' | 'publisher-s3',
  room: string,
): Promise<string> {
  const { stdout } = await run(
    'docker',
    ['compose', '--env-file', '.local/.env', '--profile', 'publisher', 'run', '-d', service],
    { cwd: stackDir, env: { ...process.env, ROOM: room } },
  );
  return stdout.trim().split(/\r?\n/).at(-1) ?? '';
}

/** Commande `docker compose` dans le dossier de la pile (arguments fixes écrits dans les scénarios). */
export async function compose(args: string[]): Promise<string> {
  const { stdout } = await run('docker', ['compose', '--env-file', '.local/.env', ...args], {
    cwd: stackDir,
  });
  return stdout;
}

const STATS_CONTAINERS = ['poc03-egress-1', 'poc03-livekit-1', 'poc03-s3-1'];

/** Relevé instantané du CPU et de la mémoire des conteneurs de la pile. */
export async function sampleStats(): Promise<ContainerStats[]> {
  try {
    const { stdout } = await run('docker', [
      'stats',
      '--no-stream',
      '--format',
      '{{.Name}};{{.CPUPerc}};{{.MemUsage}}',
      ...STATS_CONTAINERS,
    ]);
    return stdout.split(/\r?\n/).flatMap((line) => parseDockerStatsLine(line) ?? []);
  } catch {
    return [];
  }
}

/** Copie un dossier d'un conteneur (même arrêté) vers la machine hôte. */
export async function copyFromContainer(
  container: string,
  containerPath: string,
  destination: string,
): Promise<void> {
  await run('docker', ['cp', `${container}:${containerPath}`, destination]);
}

export async function removeContainer(name: string): Promise<void> {
  await run('docker', ['rm', '-f', name]);
}

/** Sérialise des objets protobuf (qui contiennent des bigint) pour les journaux. */
export function jsonSafe(value: unknown): string {
  return JSON.stringify(value, (_key, item: unknown) =>
    typeof item === 'bigint' ? item.toString() : item,
  );
}

export const sleep = (ms: number): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, ms));
