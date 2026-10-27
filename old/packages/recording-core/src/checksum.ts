/** SHA-256 en hexadécimal minuscule (Web Crypto, disponible dans Chrome et Node). */
export async function sha256Hex(data: Uint8Array<ArrayBuffer>): Promise<string> {
  const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', data));
  return Array.from(digest, (byte) => byte.toString(16).padStart(2, '0')).join('');
}

export async function matchesChecksum(
  data: Uint8Array<ArrayBuffer>,
  expectedHex: string,
): Promise<boolean> {
  return (await sha256Hex(data)) === expectedHex.toLowerCase();
}
