"""Acoustic timing of supplied words; no recognition or lexical rewriting."""
from __future__ import annotations

import gc
from pathlib import Path
import subprocess

from .contracts import digest
from .media import fingerprint, _load_stage, _save_stage
from .local_lock import local_lock
from ..shorts import _require_media_tools


def word_captions(words: list[dict], source_row: dict) -> list[dict]:
    if ''.join(w['word'] for w in words).strip() != source_row['text'].strip():
        raise ValueError("L'alignement a changé les mots ; aucun remplacement autorisé.")
    duration=source_row['end']-source_row['start']
    previous=0.0; result=[]; pending=[]
    def flush():
        if not pending:return
        text=''.join(w['word'] for w in pending).strip()
        start=source_row['start']+pending[0]['start'];end=source_row['start']+pending[-1]['end']
        if end<=start:
            if result:result[-1]['text']+=text
            else:raise ValueError('Alignement sans durée acoustique.')
        else:result.append({'start':start,'end':end,'text':text})
        pending.clear()
    for word in words:
        start,end=word['start'],word['end']
        if not 0 <= start <= end <= duration+.05 or start < previous-.02:
            raise ValueError("Horaires d'alignement invalides.")
        row={**word,'start':max(previous,min(duration,start)),'end':min(duration,max(end,previous))}
        text=''.join(w['word'] for w in pending)
        if pending and word['word'].startswith(' ') and (len(text)+len(word['word'])>72 or row['end']-pending[0]['start']>3.5):flush()
        pending.append(row);previous=row['end']
    flush()
    if not result or not ''.join(r['text'] for r in result).strip():raise ValueError('Alignement vide.')
    if ' '.join(' '.join(r['text'] for r in result).split()) != ' '.join(source_row['text'].split()):
        raise ValueError('Les sous-titres alignés ne conservent pas le texte source.')
    return result


def align_rows(source: Path, source_sha: str, rows: list[dict], options: dict, directory: Path):
    from faster_whisper import WhisperModel
    from faster_whisper.tokenizer import Tokenizer
    from faster_whisper.audio import pad_or_trim
    from huggingface_hub import hf_hub_download
    import numpy as np
    model_path=Path(options['transcription_model'])
    if not model_path.is_dir():
        name=options['transcription_model'];repository=name if '/' in name else 'Systran/faster-whisper-'+name
        model_path=Path(hf_hub_download(repository,'model.bin',local_files_only=True,token=False)).parent
    model_hashes={name:fingerprint(model_path/name) for name in ('model.bin','config.json','tokenizer.json')}
    model=None;results=[];evidence=[]
    try:
        for row in rows:
            identity={'version':1,'method':'forced_supplied_tokens_no_lexical_rewrite','source_sha256':source_sha,'row':row,
                      'model':model_hashes,'device':options['transcription_device'],'compute_type':options['transcription_compute_type'],
                      'language':options['language'],'median_filter_width':7}
            path=directory/(digest(identity)+'.json')
            with local_lock(directory / digest(identity)):
                cached=_load_stage(path,identity)
                if cached is None:
                    duration=row['end']-row['start']
                    if not 0<duration<=30:raise ValueError("Un bloc de plus de30secondes requiert un alignement plus fin.")
                    ffmpeg,_=_require_media_tools()
                    decoded=subprocess.run([ffmpeg,'-nostdin','-v','error','-ss',str(row['start']),'-t',str(duration),'-i',str(source),
                        '-vn','-ac','1','-ar','16000','-f','f32le','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    if decoded.returncode or not decoded.stdout:raise ValueError('Décodage pour alignement impossible.')
                    audio=np.frombuffer(decoded.stdout,dtype='<f4')
                    if model is None:
                        model=WhisperModel(str(model_path),device=options['transcription_device'],compute_type=options['transcription_compute_type'],local_files_only=True)
                    tokenizer=Tokenizer(model.hf_tokenizer,model.model.is_multilingual,task='transcribe',language=options['language'])
                    features=model.feature_extractor(audio);encoded=model.encode(pad_or_trim(features))
                    aligned=model.find_alignment(tokenizer,[tokenizer.encode(' '+row['text'])],encoded,min(features.shape[-1],3000))[0]
                    words=[{'word':w['word'],'start':float(w['start']),'end':float(w['end']),'probability':float(w['probability'])} for w in aligned]
                    captions=word_captions(words,row)
                    cached={'captions':captions,'words':words,'scope':'estimated_acoustic_alignment_not_verified_word_accuracy','human_listening':False}
                    if fingerprint(source)!=source_sha:raise ValueError("Master modifié pendant l'alignement.")
                    _save_stage(path,identity,cached)
                # Revalidate cached token/timing contracts as well as the receipt hash.
                if word_captions(cached['words'],row)!=cached['captions']:raise ValueError("Reçu d'alignement incohérent.")
                results.append({'source_row':row,'captions':cached['captions']});evidence.append({'path':str(path),'sha256':fingerprint(path)})
    finally:
        if model is not None:
            del model
            gc.collect()
    return results,evidence
