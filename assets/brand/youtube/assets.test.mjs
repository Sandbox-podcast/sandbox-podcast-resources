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
  test(`${name} conserve ses dimensions et une taille exploitable`, {skip: process.env.SANDBOX_MEDIA_INTEGRATION !== '1'}, async () => {
    const bytes = await readFile(resolve(root, name));
    assert.equal(bytes.subarray(1, 4).toString(), 'PNG');
    assert.equal(bytes.readUInt32BE(16), width);
    assert.equal(bytes.readUInt32BE(20), height);
    assert.ok(bytes.byteLength < maxBytes);
  });
}

for (const [name, width, height] of [
  ['channel-banner-v2.svg', 2560, 1440],
  ['channel-avatar-v2.svg', 800, 800],
  ['video-watermark-v2.svg', 150, 150],
  ['episode-thumbnail-template-v2.svg', 1280, 720],
]) {
  test(`${name} garde un gabarit éditable aux dimensions prévues`, async () => {
    const source = await readFile(resolve(root, name), 'utf8');
    assert.ok(source.includes(`viewBox="0 0 ${width} ${height}"`));
    assert.ok(!source.includes('logov2.png'), 'Utiliser le logo commun assets/brand/logo.png.');
  });
}
