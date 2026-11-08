"""
Per-tenant object placement on B2 — GSP object Startrow only.

Does not place users at signup. Signup placement is separate.
Org/worker objects always use organisation phone uID (org grid fixed).
"""

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
    place_organisation_object,
    place_regular_object,
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
    account_phone_uid: str,
    object_id: str,
    object_name: str,
    description: str | None = None,
    language: str | None = "en",
) -> dict[str, Any]:
    """
    Object placement only.
    account_phone_uid:
      regular → user phone
      organisation → organisation phone (never worker personal phone for grid uID)
    """
    if kind == "regular":
        gsp = place_regular_object(
            user_phone_uid=account_phone_uid,
            object_name=object_name,
            language=language,
        )
    else:
        gsp = place_organisation_object(
            organisation_phone_uid=account_phone_uid,
            object_name=object_name,
            language=language,
        )

    placement_id = str(object_id)
    prefix = _tenant_prefix(kind, tenant_id)
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "placement_id": placement_id,
        "object_id": str(object_id),
        "object_name": object_name,
        "description": description or "",
        "placement_kind": "object",
        "gsp_key": gsp.key,
        "L": gsp.L,
        "S": gsp.S,
        "c": gsp.c,
        "alphabet_len": gsp.alphabet_len,
        "language": gsp.language,
        "start_row": gsp.start_row,
        "start_col": gsp.start_col,
        "cell_index": gsp.cell_index,
        "splits": [
            {"k": k, "row": row, "col": col} for k, row, col in gsp.splits
        ],
        "account_type": gsp.account_type,
        "account_uid": gsp.account_uid,
        "created_at": now,
    }

    b2_service.put_json(placement_key(prefix, placement_id), record)
    for k, row, col in gsp.splits[1:]:
        b2_service.put_json(
            replica_key(prefix, placement_id, k),
            {**record, "replica_k": k, "row": row, "col": col},
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
        "start_row": gsp.start_row,
        "start_col": gsp.start_col,
        "created_at": now,
        "placement_id": placement_id,
    }
    for k, row, col in gsp.splits[1:]:
        idx = (row - 1) * GRID_COLS + col
        cells[str(idx)] = {
            "object_id": str(object_id),
            "object_name": object_name,
            "description": description or "",
            "replica_k": k,
            "start_row": row,
            "start_col": col,
            "placement_id": placement_id,
            "created_at": now,
        }
    meta["cells"] = cells

    entries = [
        e
        for e in meta.get("placements", [])
        if e.get("placement_id") != placement_id
    ]
    entries.insert(
        0,
        {
            "placement_id": placement_id,
            "object_id": str(object_id),
            "object_name": object_name,
            "description": description or "",
            "start_row": gsp.start_row,
            "start_col": gsp.start_col,
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
    meta["rows"] = GRID_ROWS
    meta["cols"] = GRID_COLS
    meta.setdefault("cells", {})
    meta["storage"] = "b2" if b2_service.enabled else "disabled"
    return meta
