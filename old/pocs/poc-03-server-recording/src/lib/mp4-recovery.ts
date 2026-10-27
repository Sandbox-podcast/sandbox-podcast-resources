export interface RecoveredStream {
  /** Flux H.264 en Annex B (codes de début 00 00 00 01), prêt pour `ffmpeg -f h264`. */
  annexB: Uint8Array<ArrayBuffer>;
  nalCount: number;
  /** Octets de fin de fichier ignorés car incomplets (dernier NAL coupé par le crash). */
  droppedTailBytes: number;
}

const START_CODE = [0, 0, 0, 1];

/**
 * Récupère le flux H.264 d'un MP4 dont l'index (`moov`) n'a jamais été écrit parce que
 * l'enregistrement a été interrompu. Constaté sur les fichiers de travail d'Egress : `ftyp`,
 * `free`, puis un `mdat` de taille 0 (jusqu'à la fin du fichier) dont les échantillons sont des
 * NAL à longueur de 4 octets, SPS et PPS compris.
 */
export function extractAnnexB(file: Uint8Array): RecoveredStream {
  const view = new DataView(file.buffer, file.byteOffset, file.byteLength);

  // 1. Trouver le début des données (`mdat`) en parcourant les boîtes de premier niveau.
  let position = 0;
  let payloadStart = -1;
  let payloadEnd = file.length;
  while (position + 8 <= file.length) {
    let size = view.getUint32(position);
    const type = String.fromCharCode(...file.subarray(position + 4, position + 8));
    let headerSize = 8;
    if (size === 1) {
      if (position + 16 > file.length) break;
      size = Number(view.getBigUint64(position + 8));
      headerSize = 16;
    }
    if (type === 'mdat') {
      payloadStart = position + headerSize;
      if (size !== 0 && position + size <= file.length) payloadEnd = position + size;
      break;
    }
    if (size < headerSize) break;
    position += size;
  }
  if (payloadStart < 0) throw new Error('Aucune boîte mdat dans le fichier');

  // 2. Lire les NAL (longueur sur 4 octets) jusqu'au premier NAL incomplet.
  const nals: Uint8Array[] = [];
  position = payloadStart;
  while (position + 4 <= payloadEnd) {
    const length = view.getUint32(position);
    if (length === 0 || position + 4 + length > payloadEnd) break;
    nals.push(file.subarray(position + 4, position + 4 + length));
    position += 4 + length;
  }

  // 3. Réécrire en Annex B.
  const annexB = new Uint8Array(nals.reduce((sum, nal) => sum + START_CODE.length + nal.length, 0));
  let offset = 0;
  for (const nal of nals) {
    annexB.set(START_CODE, offset);
    annexB.set(nal, offset + START_CODE.length);
    offset += START_CODE.length + nal.length;
  }
  return { annexB, nalCount: nals.length, droppedTailBytes: payloadEnd - position };
}
