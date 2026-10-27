import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

const root = fileURLToPath(new URL('.', import.meta.url));
for (const [name, width, height, maxBytes] of [
  ['channel-banner-v2.png', 2560, 1440, 6 * 1024 * 1024],
  ['channel-avatar-v2.png', 800, 800, 4 * 1024 * 1024],
  ['video-watermark-v2.png', 150, 150, 1024 * 1024],
  ['episode-thumbnail-template-v2.png', 1280, 720, 6 * 1024 * 1024],
]) {
  test(`${name} conserve ses dimensions et une taille exploitable`, async () => {
    const bytes = await readFile(resolve(root, name));
    assert.equal(bytes.subarray(1, 4).toString(), 'PNG');
    assert.equal(bytes.readUInt32BE(16), width);
    assert.equal(bytes.readUInt32BE(20), height);
    assert.ok(bytes.byteLength < maxBytes);
  });
}
