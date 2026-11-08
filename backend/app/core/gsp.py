"""
RECCORD DB — Guru Separation Protocol (Wizard grid).

Grid: 54 columns × 64 rows (rows numbered 1..64).

Two different placements — do not mix:
  1) User signup  → user's fullname + user phone uID
  2) Object commit → object name + account phone uID
       regular account_uid = user phone
       org/worker account_uid = organisation phone (org grid is fixed)

Language / alphabet: only to resolve column modulus (c / alphabet length).
Never use SQL UUID for Startrow or placement identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.core.identity import require_phone_uid

AccountType = Literal["regular", "organisation"]

GRID_COLS = 54
GRID_ROWS = 64
RACK_JUMP = 1
NUM_SPLITS = 6  # k = 0 primary + 5 replicas

DEFAULT_ALPHABET = "abcdefghijklmnopqrstuvwxyz"


@dataclass(frozen=True)
class GSPPlacement:
    kind: str  # "user_signup" | "object" | "vote"
    account_type: AccountType
    account_uid: str
    label: str  # fullname or object_name used for L/c
    L: int
    S: int
    c: int
    alphabet_len: int
    language: str
    start_row: int
    start_col: int
    key: str
    splits: tuple[tuple[int, int, int], ...]  # (k, row_k, col_k)
    cell_index: int


def normalize_label(name: str) -> str:
    normalized = "".join((name or "").split())
    if not normalized:
        raise ValueError("name must not be empty")
    return normalized


def sum_uid(phone_uid: str) -> int:
    phone = require_phone_uid(phone_uid, field="phone_uid")
    return sum(int(ch) for ch in phone if ch.isdigit())


def alphabet_for_language(language: str | None) -> str:
    lang = (language or "en").lower().split("-")[0]
    tables = {
        "en": DEFAULT_ALPHABET,
        "fr": DEFAULT_ALPHABET,
        "es": DEFAULT_ALPHABET,
        "pt": DEFAULT_ALPHABET,
        "de": DEFAULT_ALPHABET,
        "yo": "abdeẹefghiíjklmnoóọprsṣtuúwy",
        "ha": "abcdefghiƙjklmnoɓprstuwyzɗ",
        "ig": DEFAULT_ALPHABET,
    }
    return tables.get(lang, DEFAULT_ALPHABET)


def fold_char(ch: str) -> str:
    table = str.maketrans(
        "áàâäãåāéèêëēíìîïīóòôöõōúùûüūñçşṣẹọ"
        "ÁÀÂÄÃÅĀÉÈÊËĒÍÌÎÏĪÓÒÔÖÕŌÚÙÛÜŪÑÇŞṢẸỌ",
        "aaaaaaeeeeeeiiiiioooooouuuuunessẹọ"
        "aaaaaaeeeeeeiiiiioooooouuuuunessẹọ",
    )
    return ch.translate(table)


def first_letter_index(text: str, alphabet: str) -> int:
    alpha = alphabet.lower()
    for raw in text:
        if not raw.isalpha():
            continue
        ch = fold_char(raw).lower()
        if ch in alpha:
            return alpha.index(ch)
        if len(ch) >= 1 and ch[0] in alpha:
            return alpha.index(ch[0])
        if "a" <= ch[:1] <= "z":
            return DEFAULT_ALPHABET.index(ch[0]) % len(alpha)
    return 0


def compute_start_row(L: int, S: int) -> int:
    """start_row = ((L + S - 1) mod 64) + 1"""
    return ((L + S - 1) % GRID_ROWS) + 1


def split_cell(
    *,
    start_row_1: int,
    c: int,
    k: int,
    alphabet_len: int,
    D: int = RACK_JUMP,
) -> tuple[int, int]:
    """
    col_k = (c + k) mod alphabet_len  (then kept in 0 .. GRID_COLS-1)
    row_k = ((start_row - 1 + k * D) mod 64) + 1
    """
    mod = max(1, alphabet_len)
    col_k = (c + k) % mod
    col_k = col_k % GRID_COLS
    row_k = ((start_row_1 - 1 + k * D) % GRID_ROWS) + 1
    return row_k, col_k


def cell_index_0(row_1: int, col_0: int) -> int:
    return (row_1 - 1) * GRID_COLS + col_0


def _place(
    *,
    kind: str,
    account_type: AccountType,
    account_uid: str,
    label: str,
    language: str | None,
    D: int,
) -> GSPPlacement:
    phone = require_phone_uid(account_uid, field="account_uid")
    label_norm = normalize_label(label)

    L = len(label_norm)
    S = sum_uid(phone)
    alphabet = alphabet_for_language(language)
    alphabet_len = len(alphabet)
    c = first_letter_index(label_norm, alphabet)
    srow = compute_start_row(L, S)

    splits: list[tuple[int, int, int]] = []
    for k in range(NUM_SPLITS):
        row_k, col_k = split_cell(
            start_row_1=srow, c=c, k=k, alphabet_len=alphabet_len, D=D
        )
        splits.append((k, row_k, col_k))

    primary_row, primary_col = splits[0][1], splits[0][2]
    key = f"{label_norm}:{phone}"

    return GSPPlacement(
        kind=kind,
        account_type=account_type,
        account_uid=phone,
        label=label_norm,
        L=L,
        S=S,
        c=c,
        alphabet_len=alphabet_len,
        language=(language or "en"),
        start_row=srow,
        start_col=primary_col,
        key=key,
        splits=tuple(splits),
        cell_index=cell_index_0(primary_row, primary_col),
    )


def place_user_signup(
    *,
    account_type: AccountType,
    phone_uid: str,
    full_name: str,
    language: str | None = "en",
    D: int = RACK_JUMP,
) -> GSPPlacement:
    """Signup only: L/c from user's fullname, S from user phone."""
    return _place(
        kind="user_signup",
        account_type=account_type,
        account_uid=phone_uid,
        label=full_name,
        language=language,
        D=D,
    )


def place_object(
    *,
    account_type: AccountType,
    account_phone_uid: str,
    object_name: str,
    language: str | None = "en",
    D: int = RACK_JUMP,
) -> GSPPlacement:
    """
    Object commit only: L/c from object name, S from account phone uID.
    Org/worker must pass organisation phone (org grid is fixed).
    """
    return _place(
        kind="object",
        account_type=account_type,
        account_uid=account_phone_uid,
        label=object_name,
        language=language,
        D=D,
    )


def place_vote(
    *,
    voter_name: str,
    voter_phone: str,
    language: str | None = "en",
    D: int = RACK_JUMP,
) -> GSPPlacement:
    """Vote: voter name + voter phone uID (same object-style name+uid rule)."""
    return _place(
        kind="vote",
        account_type="regular",
        account_uid=voter_phone,
        label=voter_name,
        language=language,
        D=D,
    )
