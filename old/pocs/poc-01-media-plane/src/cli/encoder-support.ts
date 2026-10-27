/** Teste quels encodeurs vidéo (matériels ou logiciels) Chrome expose via WebCodecs. */
import { launchChromeRaw, serveClient } from '../lib/browser-runner.ts';

const server = await serveClient();
const browser = await launchChromeRaw({ headed: process.argv.includes('--headed') });
try {
  const page = await browser.newPage();
  await page.goto(server.url); // contexte sécurisé requis par WebCodecs
  const results = await page.evaluate(async () => {
    const configs = [
      {
        name: 'H.264 1080p30 matériel',
        codec: 'avc1.640028',
        hardwareAcceleration: 'prefer-hardware',
      },
      {
        name: 'H.264 1080p30 logiciel',
        codec: 'avc1.640028',
        hardwareAcceleration: 'prefer-software',
      },
      {
        name: 'VP9 1080p30 matériel',
        codec: 'vp09.00.40.08',
        hardwareAcceleration: 'prefer-hardware',
      },
      {
        name: 'AV1 1080p30 matériel',
        codec: 'av01.0.08M.08',
        hardwareAcceleration: 'prefer-hardware',
      },
      { name: 'VP8 1080p30 matériel', codec: 'vp8', hardwareAcceleration: 'prefer-hardware' },
    ] as const;
    const out: { name: string; supported: boolean; accelerationReported?: string }[] = [];
    for (const c of configs) {
      try {
        const r = await VideoEncoder.isConfigSupported({
          codec: c.codec,
          width: 1920,
          height: 1080,
          bitrate: 8_000_000,
          framerate: 30,
          hardwareAcceleration: c.hardwareAcceleration,
        });
        out.push({
          name: c.name,
          supported: Boolean(r.supported),
          accelerationReported: String(r.config?.hardwareAcceleration),
        });
      } catch (e) {
        out.push({ name: c.name, supported: false, accelerationReported: String(e) });
      }
    }
    return out;
  });
  for (const r of results)
    console.log(`${r.name} : ${r.supported ? 'oui' : 'non'} (${r.accelerationReported ?? ''})`);
} finally {
  await browser.close();
  await server.close();
}
