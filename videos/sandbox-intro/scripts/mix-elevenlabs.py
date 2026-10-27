"""Reconstitue le mix ElevenLabs sans modifier les médias source."""
import json
import pathlib
import subprocess
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
config = json.loads((ROOT / 'voice-edit.json').read_text(encoding='utf-8'))
RATE = config['sampleRate']
LENGTH = round(config['duration'] * RATE)

def decode(file, filters=None):
    args = ['ffmpeg', '-v', 'error', '-i', str(file)]
    if filters:
        args += ['-af', filters]
    raw = subprocess.check_output(args + ['-ar',str(RATE),'-ac','2','-f','f32le','pipe:1'])
    return np.frombuffer(raw, dtype=np.float32).reshape(-1,2).copy()

def fit_length(data):
    return np.pad(data[:LENGTH], ((0,max(0,LENGTH-len(data))),(0,0)))

def envelope(start, end, fade):
    result = np.zeros(LENGTH,dtype=np.float32)
    a,b = round(start*RATE), min(LENGTH,round(end*RATE))
    n = min(round(fade*RATE),(b-a)//2)
    result[a:b] = 1
    result[a:a+n] = np.linspace(0,1,n)
    result[b-n:b] = np.linspace(1,0,n)
    return result

original = fit_length(decode(ROOT/config['original']))
instrumental = fit_length(decode(ROOT/config['instrumental']))
replacement = np.zeros(LENGTH,dtype=np.float32)
for start,end in config['replaceWindows']:
    replacement = np.maximum(replacement,envelope(start,end,.08))
bed = original*(1-replacement[:,None]) + instrumental*replacement[:,None]
dialogue = np.zeros_like(bed)
duck = np.zeros(LENGTH,dtype=np.float32)
report=[]
clips_dir=ROOT/'public/voices/aligned'
clips_dir.mkdir(parents=True,exist_ok=True)
for item in config['segments']:
    duration = item['out']-item['in']
    available = item['end']-item['start']
    speed = max(1,duration/available)
    if speed>1.3:
        raise ValueError(f"Réplique trop accélérée : {item['id']} ({speed})")
    filters = f"atrim=start={item['in']}:end={item['out']},asetpts=PTS-STARTPTS,atempo={speed},loudnorm=I=-17:TP=-2:LRA=7"
    source = item.get('sourceFile', f"public/voices/{item['voice']}-elevenlabs.mp3")
    samples = decode(ROOT/source,filters)
    # L'excédent de padding de l'étirement ne doit pas chevaucher la phrase suivante.
    samples = samples[:round(available*RATE)]
    fade = min(round(.006*RATE),len(samples)//2)
    samples[:fade] *= np.linspace(0,1,fade)[:,None]
    samples[-fade:] *= np.linspace(1,0,fade)[:,None]
    a = round(item['start']*RATE)
    dialogue[a:a+len(samples)] += samples
    duck = np.maximum(duck,envelope(max(0,item['start']-.06),item['start']+len(samples)/RATE+.15,.08))
    clip = clips_dir/(item['id']+'.wav')
    subprocess.run(['ffmpeg','-v','error','-y','-f','f32le','-ar',str(RATE),'-ac','2','-i','pipe:0','-c:a','pcm_s24le',str(clip)],input=samples.astype(np.float32).tobytes(),check=True)
    report.append({**item,'speed':speed,'renderedDuration':len(samples)/RATE,'file':clip.relative_to(ROOT).as_posix()})

mix = bed*(1-.55*duck[:,None]) + dialogue
peak = float(np.max(np.abs(mix)))
gain = min(1,10**(-1.5/20)/peak)
mix *= gain
subprocess.run(['ffmpeg','-v','error','-y','-f','f32le','-ar',str(RATE),'-ac','2','-i','pipe:0','-c:a','pcm_s24le',str(ROOT/config['output'])],input=mix.astype(np.float32).tobytes(),check=True)
result={'provider':config['provider'],'model':config['model'],'catalogVoices':config['catalogVoices'],'duration':len(mix)/RATE,'peakDbFS':float(20*np.log10(np.max(np.abs(mix)))),'masterGain':gain,'segments':report}
(ROOT/'analysis/voice-mix-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='segments'},ensure_ascii=False))
