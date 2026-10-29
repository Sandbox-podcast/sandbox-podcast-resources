"""Optional local structured-model adapter; no shell, network client or paid API."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

from .contracts import digest
from .media import _load_stage, _save_stage


def generate(request, config, output: Path):
    provider = config.get("generation", {})
    command = provider.get("local_command")
    identity = {"version": 1, "request": request, "command": command, "model_revision": provider.get("model_revision")}
    output.mkdir(parents=True, exist_ok=True)
    request_path = output / (digest(identity)+".request.json")
    request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")
    if not command:
        return {"status": "blocked", "blocker": "local_editorial_model_not_configured", "request_path": str(request_path)}
    if provider.get("network") is not False or provider.get("cost_per_call") != 0:
        raise ValueError("Seul un modèle local déclaré sans réseau et sans coût est admis.")
    if not isinstance(command, list) or not command or any(not isinstance(s, str) or not s for s in command):
        raise ValueError("Commande locale sous forme de liste argv requise.")
    if not provider.get("model_revision"):
        raise ValueError("Révision du modèle local requise pour le cache.")
    receipt = output / (digest(identity)+".response.json")
    previous = _load_stage(receipt, identity)
    if previous is not None:
        return previous
    result = subprocess.run(command, input=json.dumps(request, ensure_ascii=False), capture_output=True,
                            text=True, encoding="utf-8", timeout=provider.get("timeout_seconds", 300), shell=False)
    if result.returncode:
        raise RuntimeError("Le modèle local a échoué ; consulter son diagnostic local sans publier de credentials.")
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise ValueError("Réponse JSON objet du modèle requise.")
    _save_stage(receipt, identity, value)
    return value
