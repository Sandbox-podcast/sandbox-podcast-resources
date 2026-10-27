"""Contrôle indépendant des MP4 et de leur bande-son avec FFmpeg/FFprobe."""
import hashlib
import json
import pathlib
import subprocess
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT = ROOT.parents[1] / 'output'
TIMELINE = json.loads((ROOT / 'timeline.json').read_text(encoding='utf-8'))

def probe(file):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(file)]))

def pcm(file):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(file), '-vn', '-ac', '1', '-ar', '16000', '-f', 'f32le', 'pipe:1'])
    return np.frombuffer(raw, dtype=np.float32)

original = ROOT / TIMELINE['audio']
source = pcm(original)
report = {'source': probe(original), 'sourceSha256': hashlib.sha256(original.read_bytes()).hexdigest(), 'files': []}
for name in ['final', 'preview']:
    file = OUTPUT / f'sandbox-intro-{name}.mp4'
    meta = probe(file)
    video = next(s for s in meta['streams'] if s['codec_type'] == 'video')
    audio = next(s for s in meta['streams'] if s['codec_type'] == 'audio')
    assert video['codec_name'] == 'h264'
    assert audio['codec_name'] == 'aac'
    assert audio['channels'] == 2
    assert video['r_frame_rate'] == '50/1'
    assert int(video['nb_frames']) == TIMELINE['durationInFrames']
    assert abs(float(meta['format']['duration']) - TIMELINE['duration']) < 0.001
    if name == 'final':
        assert (video['width'], video['height']) == (1920, 1080)
    decoded = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(file), '-f', 'null', '-'], capture_output=True, text=True)
    assert decoded.returncode == 0, decoded.stderr
    assert decoded.stderr == '', decoded.stderr
    rendered = pcm(file)
    length = min(len(source), len(rendered), int(TIMELINE['duration'] * 16000))
    # AAC est avec pertes : l'identité binaire n'est pas attendue.
    correlation = float(np.corrcoef(source[:length], rendered[:length])[0, 1])
    assert correlation > .98, f'Audio décalé ou différent : {correlation}'
    block_correlations = []
    for start in range(0, length - 16000, 16000 * 5):
        end = min(start + 16000 * 5, length)
        block_correlations.append({'start': start / 16000, 'correlation': float(np.corrcoef(source[start:end], rendered[start:end])[0, 1])})
    assert all(p['correlation'] > .97 for p in block_correlations)
    entry = {'file': str(file), 'bytes': file.stat().st_size, 'duration': float(meta['format']['duration']), 'width': video['width'], 'height': video['height'], 'fps': video['r_frame_rate'], 'frames': int(video['nb_frames']), 'videoCodec': video['codec_name'], 'audioCodec': audio['codec_name'], 'audioChannels': audio['channels'], 'decodeErrors': [], 'audioCorrelation': correlation, 'audioBlocks': block_correlations}
    report['files'].append(entry)
    print(json.dumps(entry, ensure_ascii=False))

report['limitations'] = ['Repères des paroles issus de Parakeet, résolution native 80 ms, sans validation phonétique manuelle.']
(ROOT / 'analysis' / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
