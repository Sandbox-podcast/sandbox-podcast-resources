import type { DeviceAccess } from './controller.ts';

export const browserDevices: DeviceAccess = {
  enumerate: async () => navigator.mediaDevices.enumerateDevices(),
  test: async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
    // On relâche aussitôt : le test ne doit pas laisser la caméra allumée.
    for (const track of stream.getTracks()) track.stop();
  },
};
