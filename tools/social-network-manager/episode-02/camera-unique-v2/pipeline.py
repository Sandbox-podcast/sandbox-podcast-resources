"""Reproduction locale des trente Shorts E02. Aucun accès aux réseaux sociaux."""

import argparse
import hashlib
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REVISION = 'camera-unique-v2'


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def run(command, cwd=None, binary=False):
    result = subprocess.run(command, cwd=cwd, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', errors='replace')[-3000:])
    return result.stdout if binary else result.stdout.decode('utf-8', errors='replace')


def child(base, relative):
    """Une référence de manifeste ne peut sortir de son espace de travail."""
    base = Path(base).resolve()
    target = (base / relative).resolve()
    if target == base or not target.is_relative_to(base):
        raise ValueError(f'Chemin hors du dossier autorisé : {relative}')
    return target


def new_directory(path):
    path = Path(path).resolve()
    if path == HERE or path.is_relative_to(HERE):
        raise ValueError('Les sorties doivent rester hors des sources versionnées.')
    if path.exists():
        raise ValueError(f'Le dossier de destination existe déjà : {path}')
    path.mkdir(parents=True)
    return path


def existing_workspace(path):
    path = Path(path).resolve(strict=True)
    if path == HERE or path.is_relative_to(HERE):
        raise ValueError('Les sorties doivent rester hors des sources versionnées.')
    if not path.is_dir():
        raise ValueError('L’espace de travail doit être un dossier.')
    return path


class Composition(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.videos = []
        self.roots = []
        self.ids = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'video':
            self.videos.append(values)
        if 'data-composition-id' in values:
            self.roots.append(values)
        if values.get('id'):
            self.ids.append(values['id'])


def project_slug(clip):
    return clip['id'].lower() + '-' + clip['slug']


def validate_manifest(manifest, sources=HERE):
    clips = manifest['clips']
    if manifest['revision'] != REVISION or len(clips) != 30:
        raise ValueError('Le manifeste doit contenir les trente compositions caméra unique V2.')
    ids = [clip['id'] for clip in clips]
    if len(set(ids)) != 30:
        raise ValueError('Identifiant de clip dupliqué.')
    for clip in clips:
        numbers = [clip[key] for key in ('start', 'end', 'duration')]
        if not all(isinstance(value, (float, int)) and math.isfinite(value) for value in numbers):
            raise ValueError('Timecode non numérique ou non fini.')
        if clip['start'] < 0 or clip['duration'] <= 0 or abs(clip['end'] - clip['start'] - clip['duration']) > .001:
            raise ValueError('Bornes de passage incohérentes.')
        project = child(sources, 'projects/' + project_slug(clip))
        html = (project / 'index.html').read_text(encoding='utf-8')
        composition = Composition(html)
        if len(composition.videos) != 1 or len(composition.roots) != 1:
            raise ValueError(f'{clip["id"]} doit avoir une seule vidéo et une seule composition.')
        if len(set(composition.ids)) != len(composition.ids):
            raise ValueError(f'{clip["id"]} contient des identifiants DOM dupliqués.')
        root = composition.roots[0]
        if (root.get('data-width'), root.get('data-height'), root.get('data-fps')) != ('720', '1280', '30'):
            raise ValueError('Canvas différent de la version vérifiée.')
        if abs(float(root['data-duration']) - clip['duration']) > .001:
            raise ValueError('Durée HTML différente du manifeste.')
        video = composition.videos[0]
        if video.get('data-has-audio') != 'true' or 'muted' in video:
            raise ValueError('La source vidéo doit conserver son audio.')
        child(project, video['src'])
    return clips


def prepare(manifest, workspace, episode, gsap, font, logo):
    """Régénère les mezzanines dans un dossier neuf ; ne modifie jamais l'épisode."""
    clips = validate_manifest(manifest)
    inputs = [Path(path).resolve(strict=True) for path in (episode, gsap, font, logo)]
    if not all(path.is_file() for path in inputs):
        raise ValueError('L’épisode, GSAP, la police et le logo doivent être des fichiers.')
    episode, gsap, font, logo = inputs
    info = json.loads(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,width,height', '-of', 'json', str(episode)]))
    if not any(stream.get('width') == 1280 and stream.get('height') == 720 for stream in info['streams']):
        raise ValueError('Ces cadrages nécessitent la source 1280 × 720 vérifiée.')
    if float(info['format']['duration']) < max(clip['end'] for clip in clips):
        raise ValueError('La source ne couvre pas tous les passages sélectionnés.')
    target = new_directory(workspace)
    write_json(target / 'manifest.json', manifest)
    provenance = {'source_sha256': digest(episode), 'gsap_sha256': digest(gsap), 'clips': []}
    for clip in clips:
        project = target / 'projects' / project_slug(clip)
        shutil.copytree(HERE / 'projects' / project_slug(clip), project)
        assets = project / 'assets'
        assets.mkdir()
        for source, filename in [(gsap, 'gsap.min.js'), (font, 'archivo.woff2'), (logo, 'logo.png')]:
            shutil.copyfile(source, assets / filename)
        composition = Composition((project / 'index.html').read_text(encoding='utf-8'))
        media = child(project, composition.videos[0]['src'])
        run(['ffmpeg', '-nostdin', '-v', 'error', '-n', '-ss', str(clip['start']), '-i', str(episode), '-t', str(clip['duration']), '-map', '0:v:0', '-map', '0:a:0', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(media)])
        provenance['clips'].append({'id': clip['id'], 'source_range': [clip['start'], clip['end']], 'mezzanine_sha256': digest(media)})
        write_json(target / 'provenance.json', provenance)
    return {'prepared': len(clips), 'workspace': str(target)}


def inspect_output(path, expected_duration):
    info = json.loads(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,width,height,r_frame_rate', '-of', 'json', str(path)]))
    videos = [stream for stream in info['streams'] if stream['codec_type'] == 'video']
    audios = [stream for stream in info['streams'] if stream['codec_type'] == 'audio']
    if len(videos) != 1 or len(audios) != 1:
        raise ValueError('Une piste vidéo et une piste audio sont requises.')
    video = videos[0]
    if (video.get('width'), video.get('height'), video.get('r_frame_rate')) != (720, 1280, '30/1'):
        raise ValueError('Le rendu doit être en 720 × 1280 à 30 images/s.')
    if abs(float(info['format']['duration']) - expected_duration) > .15:
        raise ValueError('Durée du rendu incohérente.')
    run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(path), '-f', 'null', '-'])
    return info


def selected_clips(manifest, requested):
    ids = set(requested or [])
    known = {clip['id'] for clip in manifest['clips']}
    if ids - known:
        raise ValueError('Identifiants inconnus : ' + ', '.join(sorted(ids - known)))
    return [clip for clip in manifest['clips'] if not ids or clip['id'] in ids]


def render(manifest, workspace, cli, requested):
    """Un check HyperFrames précède chaque nouveau rendu ; sorties jamais écrasées."""
    executable = Path(cli).resolve() if Path(cli).is_file() else shutil.which(cli)
    if not executable:
        raise ValueError('Exécutable HyperFrames local absent.')
    cli = str(executable)
    workspace = existing_workspace(workspace)
    validate_manifest(manifest, sources=workspace)
    outputs = child(workspace, 'shorts')
    outputs.mkdir(exist_ok=True)
    logs = child(workspace, 'render-logs')
    logs.mkdir(exist_ok=True)
    status_path = child(workspace, 'render-status.json')
    records = read_json(status_path) if status_path.exists() else []
    for clip in selected_clips(manifest, requested):
        slug = project_slug(clip)
        project = child(workspace, 'projects/' + slug)
        output = child(workspace, 'shorts/' + slug + '.mp4')
        check_log = child(workspace, 'render-logs/' + slug + '-check.log')
        render_log = child(workspace, 'render-logs/' + slug + '-render.log')
        if output.exists():
            raise ValueError(f'Sortie existante : {output}. Utiliser qa pour la contrôler.')
        check_log.write_text(run([cli, 'check', '--json'], cwd=project), encoding='utf-8')
        render_log.write_text(run([cli, 'render', '--quality', 'delivery', '--fps', '30', '--workers', '4', '--frames-cache-dir', 'off', '--output', str(output)], cwd=project), encoding='utf-8')
        record = video_qa(workspace, clip)
        records = [row for row in records if row['id'] != clip['id']] + [record]
        write_json(status_path, records)
    return {'rendered': len(selected_clips(manifest, requested))}


def video_qa(workspace, clip):
    output = child(workspace, 'shorts/' + project_slug(clip) + '.mp4')
    info = inspect_output(output, clip['duration'])
    for label, seconds in [('start', .5), ('middle', clip['duration'] / 2), ('end', clip['duration'] - .5)]:
        picture = output.with_name(output.stem + '-' + label + '.jpg')
        picture = child(workspace, picture.relative_to(workspace))
        run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-ss', str(seconds), '-i', str(output), '-frames:v', '1', '-vf', 'scale=360:640', str(picture)])
    return {'id': clip['id'], 'status': 'rendered_verified', 'file': output.relative_to(workspace).as_posix(), 'sha256': digest(output), 'bytes': output.stat().st_size, 'streams': info['streams'], 'visual_qa': 'pending'}


def audio_correlation(reference, output, sample_rate=8000):
    import numpy as np
    a = np.asarray(reference, dtype=np.float64)
    b = np.asarray(output, dtype=np.float64)
    count = min(len(a), len(b))
    if count < sample_rate * 3:
        raise ValueError('Au moins trois secondes sont nécessaires à la comparaison audio.')
    if abs(len(a) - len(b)) > sample_rate * .15:
        return {'status': 'review_required', 'reason': 'duration_mismatch', 'checks': []}
    checks = []
    for ratio in (.15, .5, .85):
        start = max(800, min(count - 16800, int(count * ratio) - 8000))
        end = start + 16000
        x = a[start:end].copy()
        x -= x.mean()
        scores = []
        for lag in range(-800, 801, 8):
            y = b[start + lag:end + lag].copy()
            y -= y.mean()
            scores.append((float(np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y) + 1e-15)), lag))
        correlation, lag = max(scores)
        checks.append({'position': ratio, 'correlation': round(correlation, 6), 'lag_ms': lag / 8})
    passed = all(row['correlation'] > .97 and abs(row['lag_ms']) <= 10 for row in checks)
    return {'status': 'audio_matches_source' if passed else 'review_required', 'checks': checks, 'source_duration': len(a) / sample_rate, 'output_duration': len(b) / sample_rate, 'full_listening': False}


def audio_qa(workspace, clip):
    import numpy as np
    project = child(workspace, 'projects/' + project_slug(clip))
    composition = Composition((project / 'index.html').read_text(encoding='utf-8'))
    source = child(project, composition.videos[0]['src'])
    output = child(workspace, 'shorts/' + project_slug(clip) + '.mp4')
    def pcm(path):
        raw = run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(path), '-vn', '-ac', '1', '-ar', '8000', '-f', 'f32le', '-'], binary=True)
        return np.frombuffer(raw, dtype='<f4')
    return {'id': clip['id'], 'sha256': digest(output), 'source_sha256': digest(source), **audio_correlation(pcm(source), pcm(output))}


def contact_sheets(manifest, workspace):
    from PIL import Image, ImageDraw
    output = child(workspace, 'visual-review')
    output.mkdir(exist_ok=True)
    for start in range(0, len(manifest['clips']), 3):
        sheet = Image.new('RGB', (720, 1350), '#15222d')
        draw = ImageDraw.Draw(sheet)
        for row, clip in enumerate(manifest['clips'][start:start + 3]):
            draw.text((8, row * 450 + 3), clip['id'] + ' ' + clip['title'][:77], fill='white')
            for column, label in enumerate(['start', 'middle', 'end']):
                picture = child(workspace, 'shorts/' + project_slug(clip) + '-' + label + '.jpg')
                with Image.open(picture) as image:
                    sheet.paste(image.resize((240, 426)), (column * 240, row * 450 + 24))
        page = child(workspace, f'visual-review/page-{start // 3 + 1:02d}.jpg')
        sheet.save(page, quality=94)


def qa(manifest, workspace, audio=False, contact=False):
    workspace = existing_workspace(workspace)
    validate_manifest(manifest, sources=workspace)
    video_status = child(workspace, 'render-status.json')
    audio_status = child(workspace, 'audio-qa.json')
    video = [video_qa(workspace, clip) for clip in manifest['clips']]
    write_json(video_status, video)
    if audio:
        write_json(audio_status, [audio_qa(workspace, clip) for clip in manifest['clips']])
    if contact:
        contact_sheets(manifest, workspace)
    return {'checked': len(video), 'visual_review': 'required', 'full_listening': False}


def install(manifest, workspace, destination):
    """Prépare un nouveau bundle local ; n'écrit jamais dans la file de publication."""
    workspace = existing_workspace(workspace)
    validate_manifest(manifest, sources=workspace)
    clips = manifest['clips']
    ids = {clip['id'] for clip in clips}
    video = read_json(child(workspace, 'render-status.json'))
    audio = read_json(child(workspace, 'audio-qa.json'))
    visual = read_json(child(workspace, 'visual-review.json'))
    provenance = read_json(child(workspace, 'provenance.json'))
    source_records = provenance.get('clips', [])
    if len(source_records) != len(ids) or {row['id'] for row in source_records} != ids:
        raise ValueError('La provenance doit couvrir exactement les trente mezzanines.')
    for rows, status in [(video, 'rendered_verified'), (audio, 'audio_matches_source'), (visual, 'reviewed')]:
        if len(rows) != len(ids) or {row['id'] for row in rows} != ids or any(row['status'] != status for row in rows):
            raise ValueError('Les contrôles vidéo, audio et visuels doivent couvrir exactement les trente fichiers.')
    for clip in clips:
        project = child(workspace, 'projects/' + project_slug(clip))
        composition = Composition((project / 'index.html').read_text(encoding='utf-8'))
        source_checksum = digest(child(project, composition.videos[0]['src']))
        source_record = next(row for row in source_records if row['id'] == clip['id'])
        audio_record = next(row for row in audio if row['id'] == clip['id'])
        if source_record.get('mezzanine_sha256') != source_checksum or audio_record.get('source_sha256') != source_checksum:
            raise ValueError('Une preuve audio porte sur une autre version de la mezzanine source.')
        checksum = digest(child(workspace, 'shorts/' + project_slug(clip) + '.mp4'))
        for rows in (video, audio, visual):
            record = next(row for row in rows if row['id'] == clip['id'])
            if record.get('sha256') != checksum:
                raise ValueError('Une preuve de contrôle porte sur une autre version du média.')
        review = next(row for row in visual if row['id'] == clip['id'])
        if not isinstance(review.get('reviewed_by'), str) or not review['reviewed_by'].strip():
            raise ValueError('La revue visuelle doit être attribuée à son auteur.')
    target = new_directory(destination)
    for clip in clips:
        filename = project_slug(clip) + '.mp4'
        shutil.copyfile(child(workspace, 'shorts/' + filename), target / filename)
    for name in ('manifest.json', 'provenance.json', 'render-status.json', 'audio-qa.json', 'visual-review.json'):
        shutil.copyfile(child(workspace, name), target / name)
    return {'installed': len(clips), 'destination': str(target), 'publication': 'not_uploaded'}


def instagram_variants(manifest, workspace):
    workspace = existing_workspace(workspace)
    ranges = manifest['instagram_ranges']
    targets = new_directory(child(workspace, 'instagram'))
    records = []
    for clip_id, kept in ranges.items():
        clip = next(clip for clip in manifest['clips'] if clip['id'] == clip_id)
        last_frame_end = math.ceil(clip['duration'] * manifest['canvas']['fps']) / manifest['canvas']['fps']
        if any(start < 0 or end <= start or end > last_frame_end + .001 for start, end in kept):
            raise ValueError('Bornes Instagram hors de leur clip source.')
        duration = sum(end - start for start, end in kept)
        if duration >= 90:
            raise ValueError('La variante doit durer moins de 90 secondes.')
        source = child(workspace, 'shorts/' + project_slug(clip) + '.mp4')
        output = targets / source.name
        filters = []
        for index, (start, end) in enumerate(kept):
            filters.extend([f'[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{index}]', f'[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{index}]'])
        labels = ''.join(f'[v{index}][a{index}]' for index in range(len(kept)))
        filters.append(labels + f'concat=n={len(kept)}:v=1:a=1[v][a]')
        run(['ffmpeg', '-nostdin', '-n', '-v', 'error', '-i', str(source), '-filter_complex', ';'.join(filters), '-map', '[v]', '-map', '[a]', '-r', '30', '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', str(output)])
        inspect_output(output, duration)
        records.append({'id': clip_id, 'file': output.relative_to(workspace).as_posix(), 'source_sha256': digest(source), 'sha256': digest(output), 'kept_source_ranges': kept, 'duration': duration, 'visual_qa': 'pending', 'publication': 'not_uploaded'})
    write_json(child(workspace, 'instagram-variants.json'), records)
    return {'variants': len(records), 'visual_review': 'required'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check', 'prepare', 'render', 'qa', 'install', 'instagram'])
    parser.add_argument('--workspace', type=Path)
    parser.add_argument('--episode', type=Path)
    parser.add_argument('--gsap', type=Path)
    parser.add_argument('--font', type=Path)
    parser.add_argument('--logo', type=Path)
    parser.add_argument('--cli', help='Exécutable local HyperFrames 0.8.172, déjà installé.')
    parser.add_argument('--clip', action='append')
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--audio', action='store_true')
    parser.add_argument('--contact', action='store_true')
    parser.add_argument('--execute', action='store_true', help='Autorise cette opération locale ; sinon affiche seulement le plan.')
    args = parser.parse_args(argv)
    manifest = read_json(HERE / 'manifest.json')
    validate_manifest(manifest)
    if args.command == 'check':
        return {'valid_sources': len(manifest['clips']), 'revision': REVISION}
    required = {'prepare': ['workspace', 'episode', 'gsap', 'font', 'logo'], 'render': ['workspace', 'cli'], 'qa': ['workspace'], 'install': ['workspace', 'destination'], 'instagram': ['workspace']}
    for option in required[args.command]:
        if not getattr(args, option):
            parser.error('--' + option + ' requis')
    if not args.execute:
        return {'dry_run': True, 'command': args.command, 'workspace': str(args.workspace), 'clips': [clip['id'] for clip in selected_clips(manifest, args.clip)], 'publication': 'not_uploaded'}
    if args.command == 'prepare':
        return prepare(manifest, args.workspace, args.episode, args.gsap, args.font, args.logo)
    workspace_manifest = read_json(args.workspace / 'manifest.json')
    if workspace_manifest != manifest:
        raise ValueError('Le manifeste du workspace diffère des sources versionnées.')
    if args.command == 'render':
        return render(manifest, args.workspace, args.cli, args.clip)
    if args.command == 'qa':
        return qa(manifest, args.workspace, args.audio, args.contact)
    if args.command == 'install':
        return install(manifest, args.workspace, args.destination)
    return instagram_variants(manifest, args.workspace)


if __name__ == '__main__':
    try:
        print(json.dumps(main(), ensure_ascii=False))
    except (ValueError, RuntimeError, OSError, KeyError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
