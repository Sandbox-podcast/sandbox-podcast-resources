/** Affiche les capacités d'accélération vidéo vues par Chrome (protocole CDP, SystemInfo). */
import { launchChrome } from '../lib/browser-runner.ts';

const headed = process.argv.includes('--headed');
const browser = await launchChrome({ headed });
try {
  const cdp = await browser.newBrowserCDPSession();
  const info = (await cdp.send('SystemInfo.getInfo' as never)) as unknown as {
    gpu: {
      devices: { vendorString: string; deviceString: string; driverVersion: string }[];
      featureStatus: Record<string, string>;
      videoEncoding?: {
        profile: string;
        maxResolution: { width: number; height: number };
        maxFramerateNumerator: number;
      }[];
      videoDecoding?: { profile: string }[];
    };
  };
  console.log(
    'Appareils :',
    info.gpu.devices
      .map((d) => `${d.vendorString} ${d.deviceString} ${d.driverVersion}`)
      .join(' ; '),
  );
  console.log('Fonctions :', JSON.stringify(info.gpu.featureStatus));
  console.log('Encodage vidéo matériel :', JSON.stringify(info.gpu.videoEncoding ?? []));
  console.log(
    'Décodage vidéo matériel (profils) :',
    (info.gpu.videoDecoding ?? []).map((d) => d.profile).join(', '),
  );
} finally {
  await browser.close();
}
