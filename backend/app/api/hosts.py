"""Election host register / login (password, cross-device)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.host_auth_service import login_host, register_host

router = APIRouter(prefix="/hosts", tags=["hosts"])


class HostRegisterRequest(BaseModel):
    host_phone: str = Field(min_length=7)
    host_name: str = Field(min_length=1)
    password: str = Field(min_length=6)
    identity_number: str | None = None


class HostLoginRequest(BaseModel):
    host_phone: str = Field(min_length=7)
    password: str = Field(min_length=6)


@router.post("/register")
def host_register(payload: HostRegisterRequest):
    try:
        return register_host(
            host_phone=payload.host_phone,
            host_name=payload.host_name,
            password=payload.password,
            identity_number=payload.identity_number,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login")
def host_login(payload: HostLoginRequest):
    try:
        return login_host(
            host_phone=payload.host_phone,
            password=payload.password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
