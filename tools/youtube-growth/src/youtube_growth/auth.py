from __future__ import annotations

import argparse
import json
from pathlib import Path


READ_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly", "https://www.googleapis.com/auth/yt-analytics.readonly"]
WRITE_SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl", "https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/yt-analytics.readonly"]


def authorize(client_secrets: Path, token_path: Path, allow_writes: bool = False) -> None:
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as error:
        raise RuntimeError("Installez requirements.txt avant de lancer l'autorisation OAuth.") from error

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), WRITE_SCOPES if allow_writes else READ_SCOPES)
    credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    from googleapiclient.discovery import build
    from .identity import verify_channel
    service = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    verify_channel(service)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    token_path.chmod(0o600)
    print(f"Jeton écrit dans {token_path}. Ne l'ajoutez jamais à Git.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Autoriser SANDBOX à utiliser l'API YouTube.")
    parser.add_argument("client_secrets", type=Path, help="JSON OAuth Desktop téléchargé depuis Google Cloud")
    parser.add_argument("--token", type=Path, default=Path(".local/youtube-token.json"))
    parser.add_argument("--allow-writes", action="store_true", help="Demande les droits d'édition après le contrôle initial du pipeline")
    args = parser.parse_args()
    authorize(args.client_secrets, args.token, args.allow_writes)


if __name__ == "__main__":
    main()
