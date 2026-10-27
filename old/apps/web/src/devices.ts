const DEVICE_ERRORS = new Set([
  'NotAllowedError',
  'SecurityError',
  'NotFoundError',
  'DevicesNotFoundError',
  'NotReadableError',
  'TrackStartError',
  'OverconstrainedError',
  'AbortError',
]);

/** L'erreur vient-elle de l'accès à la caméra ou au micro (et non du réseau) ? */
export const isDeviceError = (error: unknown): boolean =>
  typeof error === 'object' &&
  error !== null &&
  'name' in error &&
  DEVICE_ERRORS.has(String(error.name));

/** Message pour l'utilisateur à partir de l'erreur d'accès à la caméra ou au micro (device check). */
export function describeDeviceError(error: unknown): string {
  const name =
    typeof error === 'object' && error !== null && 'name' in error ? String(error.name) : '';
  switch (name) {
    case 'NotAllowedError':
    case 'SecurityError':
      return "L'accès à la caméra ou au micro est bloqué : autorisez-le dans la barre d'adresse du navigateur, puis réessayez.";
    case 'NotFoundError':
    case 'DevicesNotFoundError':
      return 'Aucune caméra ou aucun micro détecté : branchez un appareil, puis réessayez.';
    case 'NotReadableError':
    case 'TrackStartError':
      return 'La caméra ou le micro est utilisé par une autre application : fermez-la, puis réessayez.';
    case 'OverconstrainedError':
      return 'La caméra ne sait pas fournir la qualité demandée : essayez une autre caméra.';
    case 'AbortError':
      return "L'accès à l'appareil a été interrompu : réessayez.";
    default:
      return "Impossible d'accéder à la caméra ou au micro.";
  }
}

export interface DeviceReport {
  cameras: number;
  microphones: number;
  ok: boolean;
  problems: string[];
}

/** Bilan d'un device check à partir de la liste des appareils connus du navigateur. */
export function summarizeDevices(devices: readonly { kind: string }[]): DeviceReport {
  const cameras = devices.filter((d) => d.kind === 'videoinput').length;
  const microphones = devices.filter((d) => d.kind === 'audioinput').length;
  const problems = [
    ...(cameras === 0 ? ['Aucune caméra détectée.'] : []),
    ...(microphones === 0 ? ['Aucun micro détecté.'] : []),
  ];
  return { cameras, microphones, ok: problems.length === 0, problems };
}
