"""Adaptateurs locaux sans transport social et barrière des écritures historiques.

Une réponse simulée ne certifie aucun accès à un compte réel. Le module ne charge
ni credentials, ni client HTTP, ni bibliothèque des API sociales.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta, timezone
import hashlib
import json
from typing import Any


PLATFORMS = frozenset({"youtube", "tiktok", "instagram", "x", "linkedin"})


class ConnectorError(RuntimeError):
    """Erreur dont la politique de reprise est explicite et indépendante du texte."""

    def __init__(self, code: str, *, retryable: bool = False, uncertain: bool = False,
                 retry_after_seconds: int | None = None) -> None:
        self.code = code
        self.retryable = retryable
        self.uncertain = uncertain
        self.retry_after_seconds = retry_after_seconds
        super().__init__(code)


class SimulationOnlyError(ConnectorError):
    def __init__(self, code: str = "real_social_mutation_disabled") -> None:
        super().__init__(code)


def guard_legacy_write(action: str, **_: Any) -> None:
    """Bloque aussi les anciens points d'entrée, même hors du worker factory.

    Aucun drapeau d'environnement ou token ne constitue une activation. Une
    future livraison devra implémenter une autorisation par compte et périmètre,
    puis réconcilier les anciens journaux avant de remplacer cette barrière.
    """
    raise SimulationOnlyError("legacy_social_write_disabled:" + action)


def _identifier(publication: dict[str, Any], platform: str, account_id: str) -> str:
    publication_id = publication.get("publication_id")
    if not isinstance(publication_id, str) or not publication_id.strip():
        raise ValueError("publication_id stable requis.")
    for field, expected in (("platform", platform), ("account_id", account_id)):
        if publication.get(field, expected) != expected:
            raise ConnectorError("publication_destination_mismatch")
    value = json.dumps([platform, account_id, publication_id], separators=(",", ":"))
    return f"sim:{platform}:{hashlib.sha256(value.encode()).hexdigest()[:24]}"


def _instant(value: str | datetime | None) -> datetime:
    result = (datetime.now(timezone.utc) if value is None else value if isinstance(value, datetime)
              else datetime.fromisoformat(value.replace("Z", "+00:00")))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Instant avec fuseau requis.")
    return result.astimezone(timezone.utc)


class SimulationConnector:
    """Faux fournisseur déterministe, avec scénarios de panne injectés.

    Les réservations et tentatives persistantes appartiennent au worker. Cet
    objet ne garantit pas la persistance de son registre de réponses simulées.
    Après redémarrage, un résultat inconnu reste inconnu sans preuve importée.
    """

    capability_status = "simulation_only"
    has_remote_transport = False

    def __init__(self, platform: str, account_id: str, *, scenarios: list[str] | None = None) -> None:
        if platform not in PLATFORMS:
            raise ValueError("Plateforme inconnue.")
        if not isinstance(account_id, str) or not account_id.strip():
            raise ValueError("Compte explicite requis.")
        valid = {"success", "transient", "quota", "expired_token", "unknown", "unknown_after_accept", "rejected"}
        if scenarios is not None and (not isinstance(scenarios, list) or any(item not in valid for item in scenarios)):
            raise ValueError("Scénario de simulation inconnu.")
        self.platform = platform
        self.account_id = account_id
        self._scenarios = deque(scenarios or [])
        self._receipts: dict[str, dict[str, Any]] = {}

    def dispatch(self, publication: dict[str, Any]) -> dict[str, Any]:
        if self.platform == "linkedin":
            raise ConnectorError("linkedin_manual_only")
        remote_id = _identifier(publication, self.platform, self.account_id)
        if remote_id in self._receipts:
            return {**self._receipts[remote_id], "deduplicated": True}
        scenario = self._scenarios.popleft() if self._scenarios else "success"
        if scenario == "transient":
            raise ConnectorError("simulated_service_unavailable", retryable=True, retry_after_seconds=60)
        if scenario == "quota":
            raise ConnectorError("simulated_quota", retryable=True, retry_after_seconds=3600)
        if scenario == "expired_token":
            raise ConnectorError("simulated_expired_token")
        if scenario == "rejected":
            raise ConnectorError("simulated_content_rejected")
        if scenario == "unknown":
            raise ConnectorError("simulated_unknown_result", uncertain=True)
        receipt = {"remote_id": remote_id, "status": "simulated", "visibility": "simulated",
                   "media_status": "simulated_processed", "post_status": "simulated",
                   "publication_id": publication["publication_id"], "platform": self.platform,
                   "account_id": self.account_id, "simulation": True,
                   "capability_status": self.capability_status, "deduplicated": False}
        self._receipts[remote_id] = receipt
        if scenario == "unknown_after_accept":
            raise ConnectorError("simulated_response_lost_after_accept", uncertain=True)
        return dict(receipt)

    def reconcile(self, publication: dict[str, Any]) -> dict[str, Any]:
        remote_id = _identifier(publication, self.platform, self.account_id)
        if remote_id in self._receipts:
            return {**self._receipts[remote_id], "reconciled": True}
        # A known persistent receipt can be inspected without creating a new post.
        if publication.get("remote_id") == remote_id and publication.get("status") == "simulated":
            return {"remote_id": remote_id, "status": "simulated", "visibility": "simulated",
                    "simulation": True, "reconciled": True, "evidence": "persistent_simulation_receipt"}
        return {"status": "unknown", "remote_id": publication.get("remote_id"),
                "visibility": "unknown", "simulation": True, "reconciled": False,
                "requires_evidence": True}

    def collect(self, publication: dict[str, Any], *, fixture: bool = False,
                collected_at: str | datetime | None = None) -> list[dict[str, Any]]:
        """Aucune performance inventée par défaut ; fixture seulement sur demande."""
        if not fixture:
            return []
        remote_id = _identifier(publication, self.platform, self.account_id)
        if not (publication.get("simulation") is True or publication.get("status") == "simulated"):
            raise ConnectorError("fixture_metrics_require_simulated_publication")
        collected = _instant(collected_at)
        start = _instant(publication["published_at"]) if publication.get("published_at") else collected - timedelta(hours=48)
        if start > collected:
            raise ValueError("La période des métriques précède leur collecte.")
        return [{"observation_id": f"{remote_id}:fixture-views:{collected.isoformat()}",
                 "platform": self.platform, "account_id": self.account_id,
                 "publication_id": publication["publication_id"], "scope": "post",
                 "entity_id": remote_id, "metric": "views", "value": 12, "unit": "count",
                 "statistic": "cumulative", "denominator": None,
                 "source": "local_simulation_fixture", "data_class": "synthetic_fixture",
                 "period_start": start.isoformat(), "period_end": collected.isoformat(),
                 "collected_at": collected.isoformat(), "aggregation_timezone": "Europe/Paris",
                 "definition": "Compteur inventé pour tester la collecte ; aucune performance SANDBOX.",
                 "definition_version": "fixture-v1"}]


def build_connector(platform: str, account_id: str, config: dict[str, Any]) -> SimulationConnector:
    """Sélectionne uniquement un adaptateur local pour un compte configuré."""
    if config.get("mode", "simulation") != "simulation" or config.get("live_enabled", False) is not False:
        raise SimulationOnlyError()
    accounts = config.get("authorized_accounts", {})
    allowed = accounts.get(platform, []) if isinstance(accounts, dict) else []
    if not isinstance(allowed, list) or account_id not in allowed:
        raise ConnectorError("account_not_authorized")
    return SimulationConnector(platform, account_id)
