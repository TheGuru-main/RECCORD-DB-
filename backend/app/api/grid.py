"""Per-tenant grid read API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.authentication import AuthenticatedPrincipal, get_current_principal
from app.services.grid_service import get_tenant_grid_meta

router = APIRouter(prefix="/grid", tags=["grid"])


@router.get("")
def get_my_grid(
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
):
    if principal.account_type == "regular" and principal.user is not None:
        return get_tenant_grid_meta(
            kind="regular",
            tenant_id=str(principal.user.id),
        )

    if principal.account_type == "organisation" and principal.organisation is not None:
        return get_tenant_grid_meta(
            kind="organisation",
            tenant_id=str(principal.organisation.id),
        )

    if principal.account_type == "worker" and principal.organisation is not None:
        return get_tenant_grid_meta(
            kind="organisation",
            tenant_id=str(principal.organisation.id),
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tenant grid for this account",
    )
