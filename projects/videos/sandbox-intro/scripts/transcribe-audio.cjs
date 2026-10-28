async function main() {
  const fs = await import('node:fs');
  const path = await import('node:path');
  const { execFileSync } = await import('node:child_process');
  const { createRequire } = await import('node:module');
  const loadNative = createRequire(__filename);
  const cache = process.env.HYPERFRAMES_CACHE || 'C:/Users/Lou/.cache/hyperframes';
  const { OfflineRecognizer } = loadNative(
    cache + '/optional/sherpa-onnx-node@1.13.8-win32-x64/node_modules/sherpa-onnx-node',
  );
  const model = cache + '/parakeet/parakeet-tdt-0.6b-v3-int8';
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
  for (const file of process.argv.slice(2)) {
    const raw = execFileSync(
      'ffmpeg',
      ['-v', 'error', '-i', file, '-ar', '16000', '-ac', '1', '-f', 'f32le', 'pipe:1'],
      { maxBuffer: 40e6 },
    );
    const samples = new Float32Array(
      raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.byteLength),
    );
    const stream = recognizer.createStream();
    stream.acceptWaveform({ samples, sampleRate: 16000 });
    recognizer.decode(stream);
    const result = recognizer.getResult(stream);
    const destination = path.resolve(
      __dirname,
      '../analysis/' + path.basename(file).replace(/\.[^.]+$/, '') + '-transcript.json',
    );
    fs.writeFileSync(destination, JSON.stringify(result, null, 2));
    console.log(
      JSON.stringify({ file, text: result.text, duration: samples.length / 16000, destination }),
    );
  }
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
