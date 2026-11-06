"""Per-tenant B2 key prefixes."""

from __future__ import annotations


def regular_prefix(user_id: str) -> str:
    return f"tenants/regular/{user_id}"


def organisation_prefix(organisation_id: str) -> str:
    return f"tenants/organisation/{organisation_id}"


def grid_meta_key(tenant_prefix: str) -> str:
    return f"{tenant_prefix}/grid/meta.json"


def placement_key(tenant_prefix: str, placement_id: str) -> str:
    return f"{tenant_prefix}/grid/placements/{placement_id}.json"


def replica_key(tenant_prefix: str, placement_id: str, replica: int) -> str:
    return f"{tenant_prefix}/grid/replicas/{placement_id}/r{replica}.json"


def media_key(tenant_prefix: str, object_id: str, filename: str) -> str:
    return f"{tenant_prefix}/media/{object_id}/{filename}"
