"""Upload and list binary media under tenant B2 partition."""

from __future__ import annotations

import base64
import logging
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.authentication import AuthenticatedPrincipal, get_current_principal
from app.core.database import get_db
from app.core.tenant_paths import media_key, organisation_prefix, regular_prefix
from app.services.b2_service import b2_service
from app.services.object_service import get_object

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/media", tags=["media"])


class MediaUploadRequest(BaseModel):
    object_id: str
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(default="application/octet-stream")
    data_base64: str = Field(min_length=1)


def _tenant(principal: AuthenticatedPrincipal) -> tuple[str, str]:
    if principal.account_type == "regular" and principal.user is not None:
        return "regular", str(principal.user.id)
    if principal.account_type == "organisation" and principal.organisation is not None:
        return "organisation", str(principal.organisation.id)
    raise HTTPException(status_code=403, detail="Media not enabled for this role")


def _prefix(kind: str, tenant_id: str) -> str:
    return regular_prefix(tenant_id) if kind == "regular" else organisation_prefix(tenant_id)


def _manifest_key(prefix: str, object_id: str) -> str:
    return f"{prefix}/media/{object_id}/manifest.json"


@router.post("/upload")
def upload_media(
    payload: MediaUploadRequest,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
):
    kind, tenant_id = _tenant(principal)
    owner_user_id = principal.user.id if principal.account_type == "regular" else None
    organisation_id = (
        principal.organisation.id if principal.account_type == "organisation" else None
    )

    obj = get_object(
        db,
        object_id=uuid.UUID(payload.object_id),
        owner_user_id=owner_user_id,
        organisation_id=organisation_id,
    )
    if obj is None:
        raise HTTPException(status_code=404, detail="Object not found")

    # strip data-url prefix if present
    raw_b64 = payload.data_base64
    if "," in raw_b64 and raw_b64.strip().startswith("data:"):
        raw_b64 = raw_b64.split(",", 1)[1]
    try:
        body = base64.b64decode(raw_b64)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid base64") from exc

    if len(body) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="file too large (max 8MB for this endpoint)")

    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", payload.filename)[:180]
    file_id = str(uuid.uuid4())[:8]
    stored_name = f"{file_id}_{safe_name}"
    prefix = _prefix(kind, tenant_id)
    key = media_key(prefix, str(obj.id), stored_name)

    ok = b2_service.put_bytes(key, body, content_type=payload.content_type or "application/octet-stream")
    if not ok and b2_service.enabled:
        raise HTTPException(status_code=502, detail="storage upload failed")

    entry = {
        "id": file_id,
        "filename": safe_name,
        "content_type": payload.content_type,
        "key": key,
        "size": len(body),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    manifest = b2_service.get_json(_manifest_key(prefix, str(obj.id))) or {
        "object_id": str(obj.id),
        "files": [],
    }
    files = [f for f in manifest.get("files", []) if f.get("id") != file_id]
    files.insert(0, entry)
    manifest["files"] = files[:50]
    b2_service.put_json(_manifest_key(prefix, str(obj.id)), manifest)

    return {"file": entry, "storage": "b2" if b2_service.enabled else "disabled"}


@router.get("/object/{object_id}")
def list_media(
    object_id: str,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
):
    kind, tenant_id = _tenant(principal)
    owner_user_id = principal.user.id if principal.account_type == "regular" else None
    organisation_id = (
        principal.organisation.id if principal.account_type == "organisation" else None
    )
    obj = get_object(
        db,
        object_id=uuid.UUID(object_id),
        owner_user_id=owner_user_id,
        organisation_id=organisation_id,
    )
    if obj is None:
        raise HTTPException(status_code=404, detail="Object not found")

    prefix = _prefix(kind, tenant_id)
    manifest = b2_service.get_json(_manifest_key(prefix, str(obj.id))) or {
        "object_id": object_id,
        "files": [],
    }
    return manifest
