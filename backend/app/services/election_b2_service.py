"""Mirror host election lists onto B2 partitions (cross-device durable index)."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

from app.core.tenant_paths import grid_meta_key  # unused; keep imports minimal
from app.services.b2_service import b2_service

logger = logging.getLogger(__name__)


def _norm_phone(phone: str) -> str:
    return re.sub(r"\s+", "", (phone or "").strip())


def host_prefix(host_phone: str) -> str:
    return f"tenants/election-host/{_norm_phone(host_phone)}"


def host_elections_meta_key(host_phone: str) -> str:
    return f"{host_prefix(host_phone)}/elections/meta.json"


def host_election_key(host_phone: str, election_uuid: str) -> str:
    return f"{host_prefix(host_phone)}/elections/{election_uuid}.json"


def upsert_host_election_on_b2(
    *,
    host_phone: str,
    election: dict[str, Any],
) -> None:
    """Write one election snapshot and update the host list index on B2."""
    if not host_phone:
        return
    phone = _norm_phone(host_phone)
    eid = str(election.get("id") or "")
    now = datetime.now(timezone.utc).isoformat()

    record = {
        **election,
        "updated_at": now,
    }
    b2_service.put_json(host_election_key(phone, eid), record)

    meta = b2_service.get_json(host_elections_meta_key(phone)) or {
        "host_phone": phone,
        "elections": [],
        "updated_at": None,
    }
    entries = [
        e
        for e in meta.get("elections", [])
        if str(e.get("id")) != eid
    ]
    entries.insert(
        0,
        {
            "id": eid,
            "election_id": election.get("election_id"),
            "title": election.get("title"),
            "status": election.get("status"),
            "total_candidates": election.get("total_candidates"),
            "updated_at": now,
        },
    )
    meta["elections"] = entries[:200]
    meta["updated_at"] = now
    b2_service.put_json(host_elections_meta_key(phone), meta)
