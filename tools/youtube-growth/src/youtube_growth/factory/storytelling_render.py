"""Measured, editable storytelling timelines and local FFmpeg composition."""
from __future__ import annotations

import json
import math
from pathlib import Path
import shutil
import subprocess

from .contracts import ROOT, digest
from .media import fingerprint, _load_stage, _save_stage, _srt_time, _scan, probe
from .narrative import join_waves
from .narrative_visuals import PALETTE, font_file, wrap

VERSION = 3


def caption_rows(utterance, spoken):
    start=spoken["start_seconds"]
    base={"utterance_id":utterance["utterance_id"],"speaker_id":utterance["speaker_id"]}
    chunks=spoken.get("caption_segments")
    if chunks:
        return [{**base,"text":c["text"],"start_seconds":start+c["start_seconds"],"end_seconds":start+c["end_seconds"],"alignment":"measured_audio_chunks"} for c in chunks]
    alignments=spoken.get("alignment")
    if isinstance(alignments,list) and alignments and " ".join(spoken.get("spoken_text",utterance["text"]).split())==" ".join(utterance["text"].split()):
        result=[]
        for block in alignments:
            align=block["alignment"]
            chars=align["characters"];starts=align["character_start_times_seconds"];ends=align["character_end_times_seconds"]
            offset=start+block["offset_seconds"]
            begin=0
            while begin<len(chars):
                end=min(begin+100,len(chars))
                if end<len(chars):
                    spaces=[i for i in range(begin+35,end) if chars[i].isspace() or chars[i] in '.!?']
                    if spaces:end=spaces[-1]+1
                text="".join(chars[begin:end]).strip()
                if text:result.append({**base,"text":text,"start_seconds":offset+starts[begin],"end_seconds":offset+ends[end-1],"alignment":"provider_characters"})
                begin=end
        if result:return result
    return [{**base,"text":utterance["text"],"start_seconds":start,"end_seconds":spoken["end_seconds"],"alignment":"measured_utterance_boundaries"}]


def artifact(path):
    return {"path": str(Path(path).resolve()), "sha256": fingerprint(Path(path))}


def checked(rows):
    for row in rows:
        if fingerprint(Path(row["path"])) != row["sha256"]:
            raise ValueError("storytelling_artifact_changed")


def build_timeline(script, audio, sources):
    scenes = {s["scene_id"]: s for s in audio["scenes"]}
    source_map = {s["source_id"]: s for s in sources}
    shots, captions, chapters = [], [], []
    cursor = 0.
    for scene in script["scenes"]:
        speech = scenes[scene["scene_id"]]
        start, duration = speech["start_seconds"], speech["duration_seconds"]
        if abs(start-cursor) > .03 or duration <= 0:
            raise ValueError("storytelling_audio_timeline_gap")
        utterances = {u["utterance_id"]: u for u in speech["utterances"]}
        if set(utterances) != {u["utterance_id"] for u in scene["utterances"]}:
            raise ValueError("storytelling_audio_coverage_mismatch")
        for u in scene["utterances"]:
            row = utterances[u["utterance_id"]]
            a, b = row["start_seconds"], row["end_seconds"]
            if not start <= a < b <= start+duration+.03:
                raise ValueError("storytelling_utterance_out_of_bounds")
            captions.extend(caption_rows(u,row))
        chapters.append({"scene_id": scene["scene_id"], "title": scene["function"], "start_seconds": start})
        local_end = start
        for index, shot in enumerate(scene["shots"]):
            refs = shot["utterance_ids"]
            if any(ref not in utterances for ref in refs):
                raise ValueError("storytelling_shot_anchor_missing")
            a = min(utterances[k]["start_seconds"] for k in refs)
            b = max(utterances[k]["end_seconds"] for k in refs)
            # A shot holds through the pause following its last spoken line.
            if index == 0:
                a = start
            if index+1 < len(scene["shots"]):
                next_refs = scene["shots"][index+1]["utterance_ids"]
                b = min(utterances[k]["start_seconds"] for k in next_refs)
            else:
                b = start+duration
            if abs(a-local_end) > .03 or b <= a:
                raise ValueError("storytelling_shots_overlap_or_gap")
            if any(utterances[k]["start_seconds"]<a-.03 or utterances[k]["end_seconds"]>b+.03 for k in refs):
                raise ValueError("storytelling_shot_anchor_out_of_bounds")
            source = source_map.get(shot.get("source_id"))
            if shot["type"] in {"image", "video"} and not source:
                raise ValueError("storytelling_visual_source_missing")
            shots.append({**shot, "scene_id": scene["scene_id"], "factual_status": scene["factual_status"],
                          "start_seconds": a, "end_seconds": b, "duration_seconds": b-a,
                          "source": source, "heading": scene["function"]})
            local_end = b
        cursor = start+duration
    if abs(cursor-audio["duration_seconds"]) > .03:
        raise ValueError("storytelling_total_duration_mismatch")
    return {"version": VERSION, "story_id": script["story_id"], "duration_seconds": cursor,
            "clock": "measured_audio", "shots": shots, "captions": captions, "chapters": chapters,
            "sound_tracks": audio.get("sound_tracks", [])}


def poster(shot, path, size):
    from PIL import Image, ImageDraw, ImageFont
    width, height = size
    scale = width/960
    im = Image.new("RGBA", size, (0,0,0,0)) if shot["type"]=="video" else Image.new("RGB", size, PALETTE["background"])
    draw = ImageDraw.Draw(im)
    font = str(font_file())
    title = ImageFont.truetype(font, round(34*scale))
    label = ImageFont.truetype(font, round(25*scale))
    small = ImageFont.truetype(font, round(17*scale))
    margin = round(48*scale)
    draw.text((margin, round(24*scale)), "SANDBOX / STORYTELLING", font=small, fill=PALETTE["cyan"])
    heading = shot.get("on_screen_text") or shot["heading"]
    lines = wrap(draw, heading, title, width-2*margin)
    if len(lines) > 3:
        raise ValueError("storytelling_screen_title_too_long")
    y = round(72*scale)
    for line in lines:
        draw.text((margin,y), line, font=title, fill=PALETTE["white"])
        y += round(42*scale)
    top, bottom = max(y+round(25*scale), round(190*scale)), height-round(80*scale)
    if shot["type"] == "image":
        src = Path(shot["source"]["path"])
        with Image.open(src) as source:
            picture = source.convert("RGB")
            picture.thumbnail((width-2*margin, bottom-top))
            im.paste(picture, ((width-picture.width)//2, top+(bottom-top-picture.height)//2))
    elif shot["type"] == "diagram":
        labels = shot.get("labels") or [shot["description"]]
        gap = round(16*scale)
        card_h = (bottom-top-gap*(len(labels)-1))/len(labels)
        for i, text in enumerate(labels):
            a = top+i*(card_h+gap)
            draw.rounded_rectangle((margin,a,width-margin,a+card_h),radius=round(9*scale),fill=PALETTE["panel"],outline=PALETTE["cyan"])
            rows = wrap(draw,text,label,width-2*margin-round(32*scale))
            if len(rows)*round(30*scale) > card_h-round(8*scale):
                raise ValueError("storytelling_diagram_text_overflow")
            for j,line in enumerate(rows):
                draw.text((margin+round(16*scale),a+(card_h-len(rows)*round(30*scale))/2+j*round(30*scale)),line,font=label,fill=PALETTE["white"])
    nature = {"fiction":"FICTION", "reconstruction":"RECONSTITUTION", "fact":"SOURCES DU DOSSIER"}[shot["factual_status"]]
    draw.text((margin,height-round(45*scale)),nature,font=small,fill=PALETTE["orange"])
    im.save(path)


def _run(args):
    result = subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=1800)
    if result.returncode:
        raise RuntimeError("storytelling_ffmpeg_failed")


def render(script, timeline, audio, directory, *, draft=False, portrait=False):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    size = ((540,960) if portrait else (960,540)) if draft else ((1080,1920) if portrait else (1920,1080))
    fps = 12 if draft else 24
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise ValueError("ffmpeg_required")
    checked(audio.get("artifacts", []))
    checked([s["source"] for s in timeline["shots"] if s.get("source")])
    identity = {"version":VERSION,"timeline":timeline,"audio":audio,"size":size,"fps":fps,"font":fingerprint(font_file())}
    receipt = directory/"render.json"
    cached = _load_stage(receipt,identity)
    if cached:
        checked(cached["artifacts"])
        return cached
    segments, artifacts = [], []
    for shot in timeline["shots"]:
        # Artwork is independent of the recorded duration and survives a voice edit.
        art_key = digest({k:v for k,v in shot.items() if k not in {"start_seconds","end_seconds","duration_seconds"}})
        art_dir = directory.parent.parent/"visual-cache"/digest({"art":art_key,"size":size})
        art_dir.mkdir(parents=True,exist_ok=True)
        picture = art_dir/"frame.png"
        if not picture.exists():
            poster(shot,picture,size)
        image_receipt = art_dir/"image.json"
        if image_receipt.exists():
            saved = json.loads(image_receipt.read_text(encoding="utf-8"))
            checked([saved])
        else:
            image_receipt.write_text(json.dumps(artifact(picture)),encoding="utf-8")
        frame_count=round(shot["end_seconds"]*fps)-round(shot["start_seconds"]*fps)
        if frame_count<1:
            raise ValueError("storytelling_shot_shorter_than_frame")
        key = digest({"version":VERSION,"art":artifact(picture),"frame_count":frame_count,"fps":fps,"type":shot["type"]})
        part = directory/(key+".mp4")
        part_receipt = directory/(key+".json")
        if part_receipt.exists():
            checked([json.loads(part_receipt.read_text(encoding="utf-8"))])
        else:
            temp = directory/(key+".partial.mp4")
            args = [ffmpeg,"-nostdin","-hide_banner","-v","error","-y"]
            if shot["type"] == "video":
                args += ["-stream_loop","-1","-i",shot["source"]["path"],"-loop","1","-i",str(picture)]
            else:
                args += ["-loop","1","-framerate",str(fps),"-i",str(picture)]
            w,h=size
            duration=frame_count/fps
            vf=f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fade=t=in:d=0.15,fade=t=out:st={max(0,duration-.15):.5f}:d=0.15"
            if shot["type"]=="video":
                vf=f"[0:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1[base];[base][1:v]overlay=0:0:shortest=1,fade=t=in:d=0.15,fade=t=out:st={max(0,duration-.15):.5f}:d=0.15[out]"
                args += ["-filter_complex",vf,"-map","[out]"]
            else:
                args += ["-vf",vf]
            args += ["-an","-frames:v",str(frame_count),"-r",str(fps),"-c:v","libx264","-preset","veryfast","-crf","23","-pix_fmt","yuv420p",str(temp)]
            _run(args)
            temp.replace(part)
            part_receipt.write_text(json.dumps(artifact(part)),encoding="utf-8")
        segments.append(part)
        artifacts.extend([artifact(part),artifact(picture)])
    # concat demuxer paths use generated hexadecimal names in this directory.
    concat = directory/"shots.txt"
    concat.write_text("\n".join("file '"+p.name+"'" for p in segments)+"\n",encoding="utf-8")
    voice = directory/"voice.wav"
    join_waves([Path(s["path"]) for s in audio["scenes"]],voice,pause=0)
    duration = timeline["duration_seconds"]
    srt=directory/"subtitles.srt"
    vtt=directory/"subtitles.vtt"
    cues=timeline["captions"]
    srt.write_text("\n\n".join(f"{i+1}\n{_srt_time(c['start_seconds'])} --> {_srt_time(c['end_seconds'])}\n{c['text']}" for i,c in enumerate(cues))+"\n",encoding="utf-8")
    vtt.write_text("WEBVTT\n\n"+"\n\n".join(f"{_srt_time(c['start_seconds']).replace(',','.')} --> {_srt_time(c['end_seconds']).replace(',','.')}\n{c['text']}" for c in cues)+"\n",encoding="utf-8")
    args=[ffmpeg,"-nostdin","-hide_banner","-v","error","-y","-f","concat","-safe","1","-i",str(concat),"-i",str(voice)]
    tracks=timeline.get("sound_tracks",[])
    if len(tracks)>64:
        raise ValueError("storytelling_too_many_sound_tracks")
    for track in tracks:
        args += ["-i",track["path"]]
    args += ["-i",str(srt)]
    filters=["[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,asplit=2[voice][duck]"] if tracks else []
    if tracks:
        for i,track in enumerate(tracks):
            seconds=float(track["duration_seconds"])
            gain=float(track.get("gain_db",-24 if track["kind"]=="music" else -14))
            delay=round(1000*float(track.get("start_seconds",0)))
            filters.append(f"[{i+2}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=duration={seconds},afade=t=in:d=0.1,afade=t=out:st={max(0,seconds-.3)}:d=0.3,volume={gain}dB,adelay={delay}|{delay}[s{i}]")
        labels="".join(f"[s{i}]" for i in range(len(tracks)))
        filters += [labels+f"amix=inputs={len(tracks)}:normalize=0[bed]", "[bed][duck]sidechaincompress=threshold=0.025:ratio=8:attack=20:release=300[quiet]", "[voice][quiet]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,alimiter=limit=0.89[mix]"]
        args += ["-filter_complex",";".join(filters),"-map","0:v:0","-map","[mix]"]
    else:
        args += ["-map","0:v:0","-map","1:a:0","-af","loudnorm=I=-16:TP=-1.5:LRA=11"]
    final=directory/"video.mp4"
    temp=directory/"video.partial.mp4"
    args += ["-map",str(len(tracks)+2)+":s:0","-c:s","mov_text","-metadata:s:s:0","language=fra","-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000","-t",str(duration),"-movflags","+faststart",str(temp)]
    _run(args)
    temp.replace(final)
    info=probe(final)
    if abs(info["duration_seconds"]-duration)>max(.15,2/fps):
        raise ValueError("storytelling_render_duration_mismatch")
    technical=_scan(final)
    artifacts.extend(artifact(p) for p in (final,voice,srt,vtt))
    result={"path":str(final),"sha256":fingerprint(final),"srt":str(srt),"vtt":str(vtt),"duration_seconds":duration,"size":size,"draft":draft,"technical":technical,"artifacts":artifacts,"human_review":"pending"}
    _save_stage(receipt,identity,result)
    return result
