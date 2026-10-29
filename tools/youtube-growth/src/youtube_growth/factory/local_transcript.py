"""Conservative French surface corrections; raw ASR and timings remain evidence."""
from __future__ import annotations

import copy
import re

from .local_models import LocalModelError
from .local_quality import TEXT, object_schema


def same_spoken_words(before: str, after: str) -> bool:
    """Allow case/punctuation and narrowly bounded, normally silent plural endings.

    This is a surface check, not a phonetic recognizer. A separate reviewer
    still must approve meaning preservation; no noun/number substitution is allowed.
    """
    old, new = (re.findall(r"[^\W_]+", value.casefold(), re.UNICODE) for value in (before, after))
    if len(old) != len(new) or before.count("?") != after.count("?") or before.count("!") != after.count("!"):
        return False
    protected = {"le", "ce", "de", "ne", "que", "je", "te", "se", "pas", "plus", "sans", "moins"}
    for a, b in zip(old, new):
        if a == b:
            continue
        if {a, b} == {"au", "aux"}:
            continue
        short, long = sorted((a, b), key=len)
        if (short in protected or not short.isalpha() or len(short) < 4 or not short.endswith(("e", "é"))
                or long != short+"s"):
            return False
    return True


def _surface_choices(index: int, text: str) -> tuple[dict, dict]:
    choices, originals = {}, {}
    tokens = list(re.finditer(r"[^\W_]+", text, re.UNICODE))
    for word_index, match in enumerate(tokens):
        original = match.group()
        lower = original.casefold()
        # Request a correction only around an agreement clue. Listing
        # every reversible word encouraged gratuitous plural changes
        # on already-correct speech in the real episode.
        previous = [m.group().casefold() for m in tokens[max(0, word_index-3):word_index]]
        plural = {"les", "des", "ces", "ses", "mes", "tes", "nos", "vos", "leurs", "plusieurs", "quelques", "au", "aux"}
        singular = {"un", "une", "ce", "cet", "cette"}
        clue = next((w for w in reversed(previous) if w in plural | singular), None)
        replacement = None
        if lower in {"au", "aux"}:
            replacement = "aux" if lower == "au" else "au"
            if original[0].isupper():
                replacement = replacement.capitalize()
        elif clue in plural and original.isalpha() and len(original) >= 4 and lower.endswith(("e", "é")):
            replacement = original+"s"
        elif clue in singular and original.isalpha() and len(original) >= 5 and lower.endswith(("es", "és")):
            replacement = original[:-1]
        if replacement and same_spoken_words(original, replacement):
            choices[(index, word_index)] = replacement
            originals[(index, word_index)] = original
    return choices, originals


def proofread(raw: dict, model) -> dict:
    result = copy.deepcopy(raw)
    receipts, changes, rejected = [], [], []
    rows = raw["segments"]
    available = {i: _surface_choices(i, row["text"]) for i, row in enumerate(rows)}
    eligible = [i for i, (options, _) in available.items() if options]
    for start in range(0, len(eligible), 12):
        indices = eligible[start:start+12]
        batch = [{"index": i, "text": rows[i]["text"],
                  "context_before": rows[i-1]["text"] if i else "",
                  "context_after": rows[i+1]["text"] if i+1 < len(rows) else ""} for i in indices]
        choices, originals, alternatives = {}, {}, []
        for index in indices:
            options, words = available[index]
            choices.update(options)
            originals.update(words)
        alternatives = [object_schema({"index": {"const": i}, "word_index": {"const": w},
                                       "replacement": {"const": value}}) for (i, w), value in choices.items()]
        if not alternatives:
            continue
        schema = object_schema({"edits": {"type": "array", "maxItems": min(80, len(alternatives)),
                                          "uniqueItems": True, "items": {"anyOf": alternatives}}})
        def validate_edits(value):
            seen = set()
            for edit in value["edits"]:
                position = (edit["index"], edit["word_index"])
                if position in seen or choices.get(position) != edit["replacement"]:
                    raise ValueError("Une opération par mot, uniquement la substitution autorisée, sans ajout ni répétition.")
                seen.add(position)
        response, proof = model.complete("transcript_orthography_tokens",
            "Relis seulement les accords silencieux français. Propose uniquement des opérations sur les mots indexés, "
            "avec les valeurs autorisées par le contrat. Les mots commencent à word_index=0 dans chaque unité. "
            "Un mot avec apostrophe peut former plusieurs mots selon ces index, fournis dans word_choices. "
            "Ne corrige pas les noms propres, le lexique, les faits, les nombres ou les négations. "
            "Une unité peut finir au milieu d'une phrase : ne la complète jamais. "
            "Une liste vide est valide si aucun accord n'est clairement fautif. Ne supprime pas un pluriel déjà correct.",
            {"units": batch, "word_choices": [{"index": i, "word_index": w, "original": originals[(i, w)], "replacement": v}
                                              for (i, w), v in choices.items()]},
            schema, validator=validate_edits)
        validate_edits(response)
        receipts.append({k: v for k, v in proof.items() if k != "cache"})
        edits = []
        for index in sorted({op["index"] for op in response["edits"]}):
            original = rows[index]["text"]
            matches = list(re.finditer(r"[^\W_]+", original, re.UNICODE))
            corrected = original
            operations = sorted((op for op in response["edits"] if op["index"] == index),
                                key=lambda op: op["word_index"], reverse=True)
            for op in operations:
                span = matches[op["word_index"]].span()
                corrected = corrected[:span[0]]+op["replacement"]+corrected[span[1]:]
            if not same_spoken_words(original, corrected):
                raise LocalModelError("local_transcript_rewrite_refused")
            edits.append({"index": index, "original": original, "corrected": corrected,
                          "reason": "Accord silencieux par opérations bornées.", "operations": operations})
        response = {"edits": edits}
        if response["edits"]:
            review, evidence = model.complete("transcript_orthography_review", "Tu es un relecteur distinct du correcteur. "
                "Vérifie chaque correction : elle ne doit modifier ni mots prononcés, ni fait, nombre, nom, négation, "
                "attribution ou nuance. Seuls des accords orthographiques normalement silencieux et une ponctuation neutre sont permis. "
                "Ne prétends pas avoir écouté l'audio. En cas de changement de sens ou d'incertitude, approved=false.",
                {"units": batch, "proposed_edits": response["edits"]}, object_schema({"approved": {"type": "boolean"}, "reason": TEXT}), reviewer=True)
            receipts.append({k: v for k, v in evidence.items() if k != "cache"})
            if not review["approved"]:
                # A veto rejects the proposed edit, not the unchanged source.
                # Keep both the raw words and the refusal as explicit evidence.
                rejected.append({"proposed_edits": response["edits"], "review": review, "evidence": evidence})
                continue
            for edit in response["edits"]:
                result["segments"][edit["index"]]["text"] = edit["corrected"]
                changes.append(edit)
    result["orthography"] = {"scope": "bounded_surface_corrections", "raw_segments": rows,
                            "changes": changes, "candidate_unit_indices": eligible, "rejected_corrections": rejected,
                            "receipts": receipts, "human_listening": False}
    return result
