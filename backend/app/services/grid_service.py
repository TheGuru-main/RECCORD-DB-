"""Per-tenant grid placement on B2 — cell = GSP Startrow from name + phone."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from app.core.gsp import GRID_COLS, GRID_ROWS
from app.core.tenant_paths import (
    grid_meta_key,
    organisation_prefix,
    placement_key,
    regular_prefix,
    replica_key,
)
from app.services.b2_service import b2_service
from app.services.placement_service import (
    place_organisation_commit,
    place_regular_commit,
)

TenantKind = Literal["regular", "organisation"]


def _tenant_prefix(kind: TenantKind, tenant_id: str) -> str:
    if kind == "regular":
        return regular_prefix(tenant_id)
    return organisation_prefix(tenant_id)


def write_object_placement(
    *,
    kind: TenantKind,
    tenant_id: str,
    account_uid: str,
    object_id: str,
    object_name: str,
    description: str | None = None,
) -> dict[str, Any]:
    """account_uid must be the user's phone uID."""
    if kind == "regular":
        gsp = place_regular_commit(account_uid=account_uid, object_name=object_name)
    else:
        gsp = place_organisation_commit(account_uid=account_uid, object_name=object_name)

    placement_id = str(object_id)
    prefix = _tenant_prefix(kind, tenant_id)
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "placement_id": placement_id,
        "object_id": str(object_id),
        "object_name": object_name,
        "description": description or "",
        "gsp_key": gsp.key,
        "start_row": gsp.start_row,
        "col": gsp.col,
        "cell_index": gsp.cell_index,
        "account_type": gsp.account_type,
        "account_uid": gsp.account_uid,
        "normalized_name": gsp.normalized_name,
        "replicas": [f"{gsp.key}:r{i}" for i in range(1, 6)],
        "created_at": now,
    }

    b2_service.put_json(placement_key(prefix, placement_id), record)
    for i in range(1, 6):
        b2_service.put_json(
            replica_key(prefix, placement_id, i),
            {**record, "replica": i},
        )

    meta = b2_service.get_json(grid_meta_key(prefix)) or {
        "tenant_kind": kind,
        "tenant_id": tenant_id,
        "rows": GRID_ROWS,
        "cols": GRID_COLS,
        "cells": {},
        "placements": [],
        "updated_at": None,
    }
    meta["rows"] = GRID_ROWS
    meta["cols"] = GRID_COLS

    cells = meta.get("cells") or {}
    cells[str(gsp.cell_index)] = {
        "object_id": str(object_id),
        "object_name": object_name,
        "description": description or "",
        "created_at": now,
        "placement_id": placement_id,
    }
    meta["cells"] = cells

    entries = [
        e for e in meta.get("placements", []) if e.get("placement_id") != placement_id
    ]
    entries.insert(
        0,
        {
            "placement_id": placement_id,
            "object_id": str(object_id),
            "object_name": object_name,
            "description": description or "",
            "cell_index": gsp.cell_index,
            "created_at": now,
        },
    )
    meta["placements"] = entries[:500]
    meta["updated_at"] = now
    b2_service.put_json(grid_meta_key(prefix), meta)
    return record


def get_tenant_grid_meta(*, kind: TenantKind, tenant_id: str) -> dict[str, Any]:
    prefix = _tenant_prefix(kind, tenant_id)
    meta = b2_service.get_json(grid_meta_key(prefix))
    if meta is None:
        return {
            "tenant_kind": kind,
            "tenant_id": tenant_id,
            "rows": GRID_ROWS,
            "cols": GRID_COLS,
            "cells": {},
            "placements": [],
            "updated_at": None,
            "storage": "b2" if b2_service.enabled else "disabled",
        }
    meta.setdefault("rows", GRID_ROWS)
    meta.setdefault("cols", GRID_COLS)
    meta.setdefault("cells", {})
    meta["storage"] = "b2" if b2_service.enabled else "disabled"
    return meta
