/**
 * POC 1 : N participants Chrome publient une caméra factice et un micro vers LiveKit,
 * pendant que le serveur enregistre chaque piste. On mesure le CPU de Chrome, l'encodeur
 * réellement utilisé, les statistiques WebRTC, le CPU de LiveKit et d'Egress, puis la qualité
 * des fichiers enregistrés.
 *
 * Options : --codec h264|vp8|vp9  --participants N  --seconds S  --record true|false
 *           --width W --height H --fps F --bitrate Kbps --simulcast true|false
 *           --relay true  --simulate <scénario LiveKit>  --headed true  --name <étiquette>
 */
import { Supervisor } from '@podcast/poc-03-server-recording/supervisor.ts';
import {
  cleanup,
  collectResults,
  createHarness,
  printCollected,
  saveReport,
  waitForParticipants,
} from '@podcast/poc-03-server-recording/harness.ts';
import { sampleStats, sleep } from '@podcast/poc-03-server-recording/stack.ts';
import { summarizeStats } from '@podcast/poc-03-server-recording/docker-stats.ts';
import type { ContainerStats } from '@podcast/poc-03-server-recording/docker-stats.ts';
import type { Browser, CDPSession } from 'playwright-core';
import type { PocApi, PocStats, PublishOptions } from '../browser/client.ts';
import {
  chromeCpuSeconds,
  createToken,
  launchChrome,
  launchChromeRaw,
  sampleGpu,
  serveClient,
  type GpuSample,
} from '../lib/browser-runner.ts';
import {
  cpuPercentOfCore,
  summarizeVideo,
  timeToResolution,
  timeline,
  type VideoSample,
} from '../lib/summary.ts';

function arg(name: string, fallback: string): string {
  const index = process.argv.indexOf(`--${name}`);
  return index >= 0 ? (process.argv[index + 1] ?? fallback) : fallback;
}

const codec = arg('codec', 'h264') as 'h264' | 'vp8' | 'vp9' | 'av1';
const participantCount = Number(arg('participants', '1'));
const seconds = Number(arg('seconds', '60'));
const record = arg('record', 'true') === 'true';
const width = Number(arg('width', '1920'));
const height = Number(arg('height', '1080'));
const fps = Number(arg('fps', '30'));
const maxBitrate = Number(arg('bitrate', '4000')) * 1000;
const simulcast = arg('simulcast', 'false') === 'true';
const relay = arg('relay', 'false') === 'true';
const adaptive = arg('adaptive', 'false') === 'true';
const layers = Number(arg('layers', '3')) as 2 | 3;
const keyframeEverySec = Number(arg('keyframe', '0'));
const simulate = arg('simulate', '');
const headed = arg('headed', 'false') === 'true';
const fakeVideo = arg('fake-video', '');
const source = arg('source', 'camera') as PublishOptions['source'];
const degradation = arg('degradation', 'default') as PublishOptions['degradation'];
const label = arg('name', `${codec}-${String(participantCount)}p`);

const h = await createHarness(`p1-${label}`);
const server = await serveClient();
// --isolate true : un Chrome par participant, comme en vrai (un PC par participant).
// Sinon toutes les pages partagent un Chrome, donc un seul processus GPU.
const isolate = arg('isolate', 'false') === 'true';
const launcher = arg('raw', 'false') === 'true' ? launchChromeRaw : launchChrome;
const browsers: Browser[] = [];
const cdps: CDPSession[] = [];
for (let i = 0; i < (isolate ? participantCount : 1); i++) {
  const instance = await launcher({ headed, ...(fakeVideo ? { fakeVideoFile: fakeVideo } : {}) });
  browsers.push(instance);
  cdps.push(await instance.newBrowserCDPSession());
}
const totalCpuSeconds = async (): Promise<number> =>
  (await Promise.all(cdps.map((c) => chromeCpuSeconds(c)))).reduce((a, b) => a + b, 0);

const pages = [];
const videoSamples: VideoSample[][] = [];
const lastNetwork: {
  lost?: number;
  sent?: number;
  nack?: number;
  keyFrames?: number;
  rtt?: number;
  jitter?: number;
  pair?: string;
}[] = [];
const cpuSamples: { atMs: number; cpuSeconds: number }[] = [];
const gpuSamples: GpuSample[] = [];
const dockerSamples: ContainerStats[] = [];
let info: Awaited<ReturnType<PocApi['info']>> | undefined;
let events: { t: number; event: string }[][];

try {
  for (let i = 0; i < participantCount; i++) {
    const owner = browsers[isolate ? i : 0];
    if (!owner) throw new Error('navigateur manquant');
    const page = await owner.newPage();
    await page.goto(server.url);
    pages.push(page);
    videoSamples.push([]);
    lastNetwork.push({});
  }

  const wsUrl = 'ws://localhost:7880';
  for (const [index, page] of pages.entries()) {
    const token = await createToken(
      h.config.livekitApiKey,
      h.config.livekitApiSecret,
      h.room,
      `chrome-${String(index)}`,
    );
    await page.evaluate(
      ([url, jwt, forceRelay, adaptiveStream]) =>
        (window as unknown as { poc: PocApi }).poc.connect(
          url,
          jwt,
          undefined,
          forceRelay,
          adaptiveStream,
        ),
      [wsUrl, token, relay, adaptive] as [string, string, boolean, boolean],
    );
  }
  for (const page of pages) {
    await page.evaluate((options) => (window as unknown as { poc: PocApi }).poc.publish(options), {
      codec,
      width,
      height,
      fps,
      maxBitrate,
      simulcast,
      degradation,
      source,
      layers,
      keyframeEverySec,
      sourceUrl: `${server.url}/${source === 'sync' ? 'source-sync.mp4' : 'source.mp4'}`,
    });
  }
  h.log(`${String(participantCount)} participant(s) Chrome connecté(s) et publiant en ${codec}`);

  await waitForParticipants(h, {
    participants: participantCount,
    tracksEach: 2,
  });
  info = await pages[0]?.evaluate(() => (window as unknown as { poc: PocApi }).poc.info());
  // Le superviseur démarre un egress par piste publiée et le relance si besoin (reconnexion, crash).
  const supervisor = record ? new Supervisor(h) : undefined;
  let supervisorLoop: Promise<void> | undefined;
  if (supervisor) {
    supervisor.recordingActive = true;
    supervisorLoop = supervisor.loop(2000);
  }

  // Observation : relevés toutes les 5 s.
  const t0 = Date.now();
  let simulated = false;
  cpuSamples.push({ atMs: Date.now(), cpuSeconds: await totalCpuSeconds() });
  while (Date.now() - t0 < seconds * 1000) {
    await sleep(5000);
    if (simulate && !simulated && Date.now() - t0 > (seconds * 1000) / 3) {
      simulated = true;
      h.log(`>>> simulation LiveKit : ${simulate}`);
      await pages[0]?.evaluate(
        (scenario) => (window as unknown as { poc: PocApi }).poc.simulate(scenario as never),
        simulate,
      );
    }
    cpuSamples.push({ atMs: Date.now(), cpuSeconds: await totalCpuSeconds() });
    const gpu = await sampleGpu();
    if (gpu) gpuSamples.push(gpu);
    dockerSamples.push(...(await sampleStats()));
    for (const [index, page] of pages.entries()) {
      const stats: PocStats = await page.evaluate(() =>
        (window as unknown as { poc: PocApi }).poc.stats(),
      );
      const remote = stats.remoteInbound.reduce((sum, r) => sum + (r.packetsLost ?? 0), 0);
      lastNetwork[index] = {
        lost: remote,
        sent: stats.video.reduce((sum, v) => sum + (v.packetsSent ?? 0), 0),
        nack: stats.video.reduce((sum, v) => sum + (v.nackCount ?? 0), 0),
        keyFrames: stats.video.reduce((sum, v) => sum + (v.keyFramesEncoded ?? 0), 0),
        ...(stats.pair.currentRoundTripTime !== undefined
          ? { rtt: stats.pair.currentRoundTripTime }
          : {}),
        pair: `${stats.pair.localCandidateType ?? '?'}/${stats.pair.protocol ?? '?'}`,
      };
      // Avec le simulcast, on ne suit que la couche la plus haute.
      const top = stats.video.reduce<PocStats['video'][number] | undefined>(
        (best, v) => ((v.frameWidth ?? 0) > (best?.frameWidth ?? -1) ? v : best),
        undefined,
      );
      for (const v of top ? [top] : []) {
        videoSamples[index]?.push({
          at: stats.at,
          bytesSent: v.bytesSent,
          framesEncoded: v.framesEncoded,
          totalEncodeTime: v.totalEncodeTime,
          frameWidth: v.frameWidth,
          frameHeight: v.frameHeight,
          framesPerSecond: v.framesPerSecond,
          qualityLimitationReason: v.qualityLimitationReason,
          encoderImplementation: v.encoderImplementation,
          codec: v.codec,
        });
      }
    }
  }
  info = await pages[0]?.evaluate(() => (window as unknown as { poc: PocApi }).poc.info());
  events = await Promise.all(
    pages.map((page) => page.evaluate(() => (window as unknown as { poc: PocApi }).poc.events())),
  );

  // Synthèse.
  const perParticipant = videoSamples.map((samples) => summarizeVideo(samples));
  const chromeCpu = cpuPercentOfCore(cpuSamples);
  const gpuEncoder = gpuSamples.length
    ? gpuSamples.reduce((s, g) => s + g.encoderPercent, 0) / gpuSamples.length
    : undefined;
  const gpuDecoder = gpuSamples.length
    ? gpuSamples.reduce((s, g) => s + g.decoderPercent, 0) / gpuSamples.length
    : undefined;
  const gpuTotal = gpuSamples.length
    ? gpuSamples.reduce((s, g) => s + g.gpuPercent, 0) / gpuSamples.length
    : undefined;
  console.log(
    `\n=== ${label} : ${String(participantCount)} participant(s), ${codec}, ${String(width)}x${String(height)} à ${String(fps)} images/s demandées ===`,
  );
  console.log(`Navigateur : ${info?.userAgent ?? '?'}`);
  console.log(
    `Chrome (tous processus) : ${String(chromeCpu)} % d'un cœur au total, soit ${chromeCpu === undefined ? '?' : (chromeCpu / participantCount).toFixed(1)} % par participant`,
  );
  console.log(
    `GPU : encodeur ${gpuEncoder?.toFixed(1) ?? '?'} %, décodeur ${gpuDecoder?.toFixed(1) ?? '?'} %, global ${gpuTotal?.toFixed(1) ?? '?'} %`,
  );
  perParticipant.forEach((s, i) => {
    console.log(
      `  chrome-${String(i)} : ${s.codec ?? '?'} via ${s.encoder ?? '?'}, ${s.resolution ?? '?'}, ${String(s.avgFps)} images/s, ${String(s.avgBitrateKbps)} kb/s, encodage ${String(s.avgEncodeMsPerFrame)} ms/image, limitation ${JSON.stringify(s.limitationReasons)}`,
    );
  });
  lastNetwork.forEach((n, i) => {
    console.log(
      `  réseau chrome-${String(i)} : paquets perdus ${String(n.lost)} sur ${String(n.sent)} envoyés, NACK ${String(n.nack)}, images clés encodées ${String(n.keyFrames)}, RTT ${String(n.rtt !== undefined ? Math.round(n.rtt * 1000) : '?')} ms, chemin ${n.pair ?? '?'}`,
    );
  });
  const firstTimeline = timeline(videoSamples[0] ?? []);
  console.log(
    `Chronologie de chrome-0 : ${firstTimeline.map((p) => `${String(p.tSec)}s ${p.resolution} ${String(p.fps?.toFixed(0))}i/s ${String(p.kbps)}kb/s ${p.limitation}`).join(' | ')}`,
  );
  console.log(
    `Temps pour atteindre ${String(width)}x${String(height)} : ${String(timeToResolution(firstTimeline, `${String(width)}x${String(height)}`) ?? 'jamais')} s`,
  );
  for (const s of summarizeStats(dockerSamples)) {
    console.log(
      `  ${s.name} : CPU moyen ${String(s.cpuAvgPercent)} %, max ${String(s.cpuMaxPercent)} %, mémoire max ${String(s.memMaxMiB)} MiB`,
    );
  }
  console.log(
    `Vidéos distantes rendues par la page 0 : ${String(info?.remoteVideos ?? 0)}, images décodées : ${String(info?.decodedFrames ?? 0)}`,
  );
  events.forEach((e, i) => {
    const important = e.filter((x) =>
      /reconnect|déconnect|simulation|état de connexion/i.test(x.event),
    );
    if (important.length)
      console.log(
        `  événements chrome-${String(i)} : ${important.map((x) => `${String(x.t)} ms ${x.event}`).join(' ; ')}`,
      );
  });

  let collected;
  if (supervisor && supervisorLoop) {
    supervisor.recordingActive = false;
    const deadline = Date.now() + 120_000;
    while (Date.now() < deadline && !supervisor.allSafe()) await sleep(2000);
    h.log(`tous les segments vérifiés dans le stockage : ${String(supervisor.allSafe())}`);
    supervisor.stop();
    await supervisorLoop;
    console.log(`Segments d'enregistrement : ${String(supervisor.egressSegments.size)}`);
    collected = await collectResults(h, undefined);
    printCollected(collected);
  }

  await saveReport(h, `p1-${label}`, {
    options: {
      isolate,
      adaptive,
      layers,
      keyframeEverySec,
      codec,
      participantCount,
      seconds,
      width,
      height,
      fps,
      maxBitrate,
      simulcast,
      relay,
      simulate,
      headed,
    },
    userAgent: info?.userAgent,
    videoCodecs: info?.videoCodecs,
    chromeCpuPercentOfCore: chromeCpu,
    gpu: { encoder: gpuEncoder, decoder: gpuDecoder, total: gpuTotal },
    perParticipant,
    network: lastNetwork,
    events,
    collected,
  });
} finally {
  for (const instance of browsers) await instance.close().catch(() => undefined);
  await server.close();
  await cleanup(h);
}
