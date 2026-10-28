"""Montage local des sources propriétaires et contrôle technique des exports."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import textwrap

SOURCES = Path(__file__).resolve().parent
ROOT = SOURCES.parents[3]
KIT = ROOT / '.local/relay-kits/2026-10-18'
HERE = KIT / 'production'


def command(args):
    result = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode:
        raise RuntimeError(result.stderr[-3500:])
    return result.stdout


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def timestamp(value):
    millis = round(value * 1000)
    hours, millis = divmod(millis, 3600000)
    minutes, millis = divmod(millis, 60000)
    seconds, millis = divmod(millis, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{millis:03}'


def transcript(episode, explicit=None):
    if episode == 2:
        path = Path(explicit) if explicit else ROOT / '.local/legacy/exports/reseaux-sociaux/episode-02/source/transcript-fr.jsonl'
        return [json.loads(row) for row in path.read_text(encoding='utf-8-sig').splitlines() if row.strip()]
    path = Path(explicit) if explicit else ROOT / '.local/youtube-growth/GgSiPkADCz4/transcript-youtube.txt'
    pattern = re.compile(r'^\[(?:(\d+):)?(\d+):(\d+)\]\s*(.*)$')
    rows = []
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        match = pattern.match(line)
        if match:
            hour, minute, second, text = match.groups()
            rows.append({'start': int(hour or 0)*3600+int(minute)*60+int(second), 'text': text})
    for index, row in enumerate(rows):
        row['end'] = rows[index+1]['start'] if index+1 < len(rows) else row['start']+2
    return rows


def captions(rows, start, end, target):
    cues = []
    for row in rows:
        lower, upper = max(start,row['start']), min(end,row['end'])
        text = row['text'].strip()
        if upper-lower < .1 or not text:
            continue
        text = re.sub(r'\bChat\s*GPT\b', 'ChatGPT', text, flags=re.I)
        text = re.sub(r'\bcloud code\b', 'Claude Code', text, flags=re.I)
        text = re.sub(r'\bopen code\b', 'OpenCode', text, flags=re.I)
        text = re.sub(r'\b(?:harnet|harnets|arnet)\b', 'harnais', text, flags=re.I)
        text = re.sub(r'\bLia\b', "l'IA", text)
        text = text.replace("l'HGPT", 'ChatGPT')
        text = text.replace('prépément', 'prépaiement')
        if text == "s'y être vu":
            # Fausse reconnaissance isolée, sans information intelligible.
            continue
        cues.append(f'{len(cues)+1}\n{timestamp(lower-start)} --> {timestamp(upper-start)}\n'+ '\n'.join(textwrap.wrap(text, width=55)))
    target.write_text('\n\n'.join(cues)+'\n',encoding='utf-8')


def encode(source, start, end, target, srt=None, endcard=None):
    if source.resolve() == target.resolve():
        raise ValueError('La source ne peut pas être la destination du montage')
    target.parent.mkdir(parents=True,exist_ok=True)
    temporary = target.with_name(target.stem+'.tmp.mp4')
    args = ['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-ss',str(start),'-t',str(end-start),'-i',str(source)]
    if endcard:
        args += ['-i',str(endcard)]
        filters = '[0:v]scale=1280:720,fps=25,setsar=1,setpts=PTS-STARTPTS[v0];[0:a]aresample=48000,asetpts=PTS-STARTPTS[a0];[1:v]fps=25,setsar=1,setpts=PTS-STARTPTS[v1];[1:a]aresample=48000,asetpts=PTS-STARTPTS[a1];[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]'
        args += ['-filter_complex',filters,'-map','[v]','-map','[a]']
    else:
        video_filter = 'scale=1280:720,fps=25,setsar=1'
        if srt:
            relative = srt.relative_to(ROOT).as_posix()
            video_filter += f",subtitles=filename='{relative}':force_style='FontName=Arial,FontSize=20,Outline=2,Shadow=0,MarginV=22,Alignment=2'"
        args += ['-vf',video_filter,'-map','0:v:0','-map','0:a:0']
    args += ['-c:v','libx264','-preset','fast','-crf','25','-maxrate','1100k','-bufsize','2200k','-pix_fmt','yuv420p','-c:a','aac','-b:a','112k','-ar','48000','-ac','2','-movflags','+faststart',str(temporary)]
    command(args)
    temporary.replace(target)


def verify(path, expected=None):
    info=json.loads(command(['ffprobe','-v','error','-show_entries','format=duration,size:stream=codec_type,width,height,codec_name,r_frame_rate','-of','json',str(path)]))
    command(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-i',str(path),'-f','null','-'])
    video=next(s for s in info['streams'] if s['codec_type']=='video')
    if (video['width'],video['height']) != (1280,720):
        raise RuntimeError('Dimensions inattendues')
    if not any(s['codec_type']=='audio' for s in info['streams']):
        raise RuntimeError('Audio absent')
    if expected is not None and abs(float(info['format']['duration'])-expected) > .3:
        raise RuntimeError('Durée inattendue')
    return {'sha256':digest(path),'duration':float(info['format']['duration']),'bytes':path.stat().st_size,'width':1280,'height':720,'audio':True,'fullDecode':'passed'}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--episode',required=True,type=int,choices=[1,2])
    parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--transcript',type=Path)
    parser.add_argument('--clips-only',action='store_true')
    parser.add_argument('--video',help='Identifiant du seul montage long à exporter')
    args=parser.parse_args()
    source=args.source.resolve()
    if not source.is_file():
        parser.error('Source vidéo absente')
    rows=transcript(args.episode,args.transcript)
    source_hash=digest(source)
    endcard=HERE/'assets/fin-avec-audio.mp4'
    if not args.clips_only and not endcard.is_file():
        parser.error('Rendre la fin HyperFrames puis ajouter sa piste audio silencieuse ; voir README.md')
    selection = HERE/'selection.json' if (HERE/'selection.json').is_file() else SOURCES/'selection.json'
    selected=json.loads(selection.read_text(encoding='utf-8'))['videos']
    if not args.clips_only:
        for video in selected:
            if video['episode'] != args.episode:
                continue
            if args.video and video['id'] != args.video:
                continue
            folder=KIT/'videos'/video['id']
            folder.mkdir(parents=True, exist_ok=True)
            output=folder/'video.mp4'
            captions(rows,video['start'],video['end'],folder/'sous-titres.srt')
            encode(source,video['start'],video['end'],output,endcard=endcard)
            report=verify(output,video['end']-video['start']+3)
            report.update({'id':video['id'],'sourceVideoId':video['sourceVideoId'],'sourceSha256':source_hash,'sourceStart':video['start'],'sourceEnd':video['end'],'endcardSeconds':3,'captionsReview':'automatic-transcript-to-review','publication':'not-uploaded'})
            (folder/'montage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            print(video['id'],json.dumps(report),flush=True)
    if args.episode == 2 and not args.video:
        promos=[('lou',3369.95,3399.6),('loic',5182.3,5195.8),('nico',4591.0,4622.1)]
        for name,start,end in promos:
            folder=KIT/name/'assets'
            # Le MP4 est déjà sous-titré : un SRT voisin peut être chargé
            # automatiquement par le lecteur et afficher le texte en double.
            sidecar=HERE/'captions'/f'{name}.srt'
            sidecar.parent.mkdir(parents=True,exist_ok=True)
            captions(rows,start,end,sidecar)
            encode(source,start,end,folder/'extrait.mp4',srt=sidecar)
            report=verify(folder/'extrait.mp4',end-start)
            report.update({'sourceVideoId':'7KVqydbGow0','sourceSha256':source_hash,'sourceStart':start,'sourceEnd':end,'captionsReview':'automatic-transcript-to-review','publication':'not-uploaded','context':'Extrait de discussion du trio, pas une citation attribuée au titulaire du kit.'})
            (folder/'extrait.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            print('kit-'+name,json.dumps(report),flush=True)


if __name__=='__main__':
    main()
