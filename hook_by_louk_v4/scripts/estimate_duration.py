"""Estimate a French hook's reading time, with explicit spoken-form assumptions."""
import argparse
import json
import math
import re
from pathlib import Path

PRONUNCIATIONS = {
    'ChatGPT': 'tchat gé pé té',
    'HTML': 'ache té ème elle',
    'CSV': 'cé esse vé',
    'PDF': 'pé dé effe',
    'API': 'a pé i',
    'GPT': 'gé pé té',
    'SEO': 'esse e o',
    'URL': 'u erre elle',
    'IA': 'i a',
}
WORD = re.compile(r"[^\W_]+(?:['-][^\W_]+)*", re.UNICODE)


def spoken_form(text, explicit=False):
    prepared = text.replace('\u2019', "'").replace('\u2018', "'")
    replacements = []
    if not explicit:
        for written, spoken in PRONUNCIATIONS.items():
            prepared, count = re.subn(r'\b' + re.escape(written) + r'\b', spoken, prepared)
            if count:
                replacements.append({'written': written, 'spoken': spoken, 'occurrences': count})
    unresolved = []
    for token in re.findall(r'\b\S*\d\S*', prepared):
        unresolved.append({'token': token, 'reason': 'number_or_model_name_needs_spoken_form'})
    for token in re.findall(r'\b[A-Z]{2,}\b', prepared):
        unresolved.append({'token': token, 'reason': 'acronym_pronunciation_needs_confirmation'})
    for token in re.findall(r'[%\u20ac$&+/@]', prepared):
        unresolved.append({'token': token, 'reason': 'symbol_needs_spoken_form_or_removal'})
    return prepared, replacements, unresolved


def estimate(text, wpm=165, pause_seconds=1, spoken_text=None):
    if not math.isfinite(wpm) or wpm <= 0:
        raise ValueError('wpm must be finite and positive')
    if not math.isfinite(pause_seconds) or pause_seconds < 0:
        raise ValueError('pause_seconds must be finite and nonnegative')
    prepared, replacements, unresolved = spoken_form(spoken_text if spoken_text is not None else text,
                                                     explicit=spoken_text is not None)
    count = len(WORD.findall(prepared))
    if not count:
        raise ValueError('text must contain spoken words')
    seconds = count * 60 / wpm + pause_seconds
    return {
        'written_word_count': len(WORD.findall(text)),
        'spoken_unit_count_estimated': count,
        'spoken_form_used': prepared,
        'automatic_pronunciations': replacements,
        'unresolved_spoken_items': unresolved,
        'spoken_form_ready': not unresolved,
        'words_per_minute_assumed': wpm,
        'pause_seconds_assumed': pause_seconds,
        'estimated_seconds': round(seconds, 1),
        'within_target_at_reference_pace': 15 <= seconds <= 20,
        'estimate_usable': not unresolved,
        'sensitivity_seconds': {str(pace): round(count * 60 / pace + pause_seconds, 1)
                                for pace in (150, 165, 180)},
        'actual_duration_measured': False,
        'note': 'Estimation de lecture. Les prononciations automatiques sont des hypothèses ; seul un audio ou un chronométrage mesure la durée réelle.',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--text')
    source.add_argument('--file', type=Path)
    spoken = parser.add_mutually_exclusive_group()
    spoken.add_argument('--spoken-text')
    spoken.add_argument('--spoken-file', type=Path)
    parser.add_argument('--wpm', type=float, default=165)
    parser.add_argument('--pauses', type=float, default=1)
    args = parser.parse_args()
    text = args.text if args.text is not None else args.file.read_text(encoding='utf-8-sig')
    prepared = args.spoken_text
    if args.spoken_file is not None:
        prepared = args.spoken_file.read_text(encoding='utf-8-sig')
    try:
        result = estimate(text, args.wpm, args.pauses, prepared)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))
