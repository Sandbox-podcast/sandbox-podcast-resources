import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const cache = 'C:/Users/Lou/.cache/hyperframes';
const { OfflineRecognizer } = require(
  cache + '/optional/sherpa-onnx-node@1.13.8-win32-x64/node_modules/sherpa-onnx-node',
);
const model = cache + '/parakeet/parakeet-tdt-0.6b-v3-int8';
const root = path.resolve(import.meta.dirname, '..');
const raw = execFileSync(
  'ffmpeg',
  [
    '-v',
    'error',
    '-i',
    root + '/public/original.m4a',
    '-ar',
    '16000',
    '-ac',
    '1',
    '-f',
    'f32le',
    'pipe:1',
  ],
  { maxBuffer: 20e6 },
);
const samples = new Float32Array(raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.byteLength));
const recognizer = new OfflineRecognizer({
  featConfig: { sampleRate: 16000, featureDim: 80 },
  modelConfig: {
    transducer: {
      encoder: model + '/encoder.int8.onnx',
      decoder: model + '/decoder.int8.onnx',
      joiner: model + '/joiner.int8.onnx',
    },
    tokens: model + '/tokens.txt',
    numThreads: 4,
    provider: 'cpu',
    modelType: 'nemo_transducer',
  },
  decodingMethod: 'greedy_search',
});
const stream = recognizer.createStream();
stream.acceptWaveform({ samples, sampleRate: 16000 });
recognizer.decode(stream);
const result = recognizer.getResult(stream);
fs.writeFileSync(root + '/analysis/transcript-raw.json', JSON.stringify(result, null, 2));
console.log(JSON.stringify(result));
const envelope = [];
for (let i = 0; i < samples.length; i += 160) {
  let sum = 0;
  for (let j = i; j < Math.min(i + 160, samples.length); j++) sum += samples[j] ** 2;
  envelope.push({ t: i / 16000, rms: Math.sqrt(sum / 160) });
}
const impacts = envelope.filter(
  (v, i) =>
    i > 5 &&
    i < envelope.length - 5 &&
    v.rms > 0.13 &&
    envelope.slice(i - 5, i + 6).every((p) => p.rms <= v.rms),
);
fs.writeFileSync(
  root + '/analysis/audio-analysis.json',
  JSON.stringify(
    { duration: samples.length / 16000, sampleRate: 16000, envelope, impacts },
    null,
    2,
  ),
);
