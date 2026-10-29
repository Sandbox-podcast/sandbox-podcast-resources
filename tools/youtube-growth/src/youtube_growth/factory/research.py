"""Frozen source snapshots and claim-level verification, separate from opinion."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
from html.parser import HTMLParser
import ipaddress
import json
import socket

from .contracts import digest, instant, iso, utcnow
from .editorial import text
from .media import fingerprint


def _public_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("URL documentaire HTTPS publique requise.")
    addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError("Une source documentaire ne peut viser un réseau privé.")
    return url


class _PublicRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class _DocumentText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.hidden = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden-1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def fetch_sources(manifest, output, *, now=None):
    """Read explicitly supplied source URLs; preserve each retrieved revision."""
    from hashlib import sha256
    current = iso(now or utcnow())
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    result = []
    for source in manifest.get("sources", []):
        for name in ("source_id", "title", "url", "kind", "rights"):
            text(source.get(name), name)
        url = _public_url(source["url"])
        request = Request(url, headers={"User-Agent": "Sandbox-Factory-Research/1", "Accept": "text/html,text/plain"})
        with build_opener(_PublicRedirect()).open(request, timeout=30) as response:
            kind = response.headers.get_content_type()
            if kind not in {"text/html", "text/plain", "text/markdown"}:
                raise ValueError("Source texte ou HTML requise ; importer séparément les autres formats.")
            body = response.read(2_000_001)
            if len(body) > 2_000_000:
                raise ValueError("Source documentaire trop volumineuse.")
            content = body.decode(response.headers.get_content_charset() or "utf-8")
            final_url = response.geturl()
        if kind == "text/html":
            parser = _DocumentText()
            parser.feed(content)
            content = " ".join(" ".join(parser.parts).split())
        raw = content.encode("utf-8")
        key = sha256(raw).hexdigest()
        snapshot = output/(key+".txt")
        if snapshot.exists():
            if fingerprint(snapshot) != key:
                raise ValueError("Copie documentaire existante modifiée.")
        else:
            with snapshot.open("xb") as stream:
                stream.write(raw)
        result.append({**source, "resolved_url": final_url, "snapshot": str(snapshot), "sha256": key, "retrieved_at": current})
    record = {"version": 1, "sources": result, "claims": [], "notice": "Documents archivés ; affirmations et vérification restent à établir."}
    receipt = output/("sources-"+digest(record)+".json")
    if not receipt.exists():
        receipt.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "sources_frozen", "dossier_path": str(receipt), "source_count": len(result), "claims_verified": False}


def verify(dossier, *, base=Path('.'), now=None):
    current = instant(now or utcnow())
    if dossier.get("version") != 1:
        raise ValueError("Dossier de recherche version 1 requis.")
    sources, claims, blockers = {}, {}, []
    if dossier.get("expires_at") and instant(dossier["expires_at"]) <= current:
        blockers.append("research_expired")
    for raw in dossier.get("sources", []):
        source = dict(raw)
        key = text(source.get("source_id"), "source_id")
        if key in sources:
            raise ValueError("Source dupliquée.")
        text(source.get("title"), "source title")
        url = urlparse(text(source.get("url"), "url"))
        if url.scheme != "https" or not url.hostname or url.username or url.password or url.query and "token" in url.query.lower():
            raise ValueError("URL source HTTPS publique sans credential requise.")
        if source.get("kind") not in {"primary", "secondary", "episode"}:
            raise ValueError("Nature de source inconnue.")
        fetched = instant(source.get("retrieved_at", ""))
        if fetched > current:
            raise ValueError("Source collectée dans le futur.")
        if source.get("published_at"):
            if instant(source["published_at"]) > current:
                raise ValueError("Date de source dans le futur.")
        path = (base / text(source.get("snapshot"), "snapshot")).resolve(strict=True)
        if fingerprint(path) != source.get("sha256"):
            raise ValueError("L'empreinte d'une source documentaire a changé.")
        content = path.read_text(encoding="utf-8-sig")
        if len(content) > 2_000_000:
            raise ValueError("Source documentaire trop volumineuse.")
        text(source.get("rights"), "rights")
        sources[key] = {**source, "snapshot": str(path), "content": content}
    for raw in dossier.get("claims", []):
        claim = dict(raw)
        key = text(claim.get("claim_id"), "claim_id")
        if key in claims:
            raise ValueError("Affirmation dupliquée.")
        text(claim.get("text"), "claim text")
        if claim.get("kind") not in {"fact", "analysis", "hypothesis", "testimony"}:
            raise ValueError("Fait, analyse, hypothèse ou témoignage requis.")
        refs = claim.get("references", [])
        primary = False
        for ref in refs:
            source = sources.get(ref.get("source_id"))
            if not source or text(ref.get("quote"), "citation") not in source["content"]:
                raise ValueError("Citation absente de la source archivée.")
            primary |= source["kind"] == "primary"
        verification = claim.get("verification", {})
        verified = verification.get("status") == "confirmed" and bool(refs)
        draft_supported = claim["kind"] == "testimony" and verification.get("status") == "transcript_supported" and bool(refs)
        if verified or draft_supported:
            text(verification.get("reviewer"), "reviewer")
            text(verification.get("reason"), "verification reason")
            if instant(verification.get("checked_at", "")) > current:
                raise ValueError("Vérification future.")
        if claim["kind"] == "fact" and (not verified or not primary):
            blockers.append("unverified_fact:"+key)
        if claim.get("cross_check_required") and len({r["source_id"] for r in refs}) < 2:
            blockers.append("cross_check_missing:"+key)
        if claim["kind"] == "testimony" and not (verified or draft_supported):
            blockers.append("unverified_testimony:"+key)
        claims[key] = {**claim, "verified": verified, "draft_supported": draft_supported}
    if not sources:
        blockers.append("sources_missing")
    if not claims:
        blockers.append("claims_missing")
    return {"version": 1, "research_id": digest(dossier), "verified_at": iso(current),
            "sources": [{k: v for k, v in s.items() if k != "content"} for s in sources.values()],
            "claims": list(claims.values()), "blockers": blockers,
            "oral_verification_pending": [key for key, c in claims.items() if c["draft_supported"]],
            "status": "blocked" if blockers else "ready_for_script", "verification": "documented_review_not_automated_truth"}
