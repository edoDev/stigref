"""Stable identifier helpers for STIGs and rules."""

from __future__ import annotations

import hashlib
import re
import unicodedata


_SLUG_RE = re.compile(r"[^a-z0-9]+")
RULE_ID_RE = re.compile(r"^(?P<base>.+?)r(?P<rev>\d+)_rule$", re.IGNORECASE)


def slugify(text: str, max_len: int = 80) -> str:
    """ASCII slug suitable for path segments."""
    normalized = (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    slug = _SLUG_RE.sub("-", normalized.lower()).strip("-")
    if not slug:
        slug = "item"
    return slug[:max_len].rstrip("-")


def stig_id(name: str, version: str | int, release: str | int) -> str:
    """
    Deterministic STIG id stable across rebuilds.

    Format: {slug}-v{version}r{release}
    Plus a short content hash of the canonical triple so renames that only
    change punctuation still collide safely when name/version/release match.
    """
    v = str(version).strip()
    r = str(release).strip()
    base = slugify(name)
    digest = hashlib.sha1(f"{name}|{v}|{r}".encode("utf-8")).hexdigest()[:8]
    return f"{base}-v{v}r{r}-{digest}"


def parse_rule_id(full_rule_id: str) -> tuple[str, str, str]:
    """
    Split DISA-style rule ids.

    Returns (full_rule_id, rule_base, revision).
    If the pattern does not match, base is the full id and revision is "".
    """
    full = full_rule_id.strip()
    m = RULE_ID_RE.match(full)
    if not m:
        return full, full, ""
    return full, m.group("base"), m.group("rev")


def rule_path_id(full_rule_id: str) -> str:
    """
    Path segment for a rule. Prefer the published full id; encode only
    characters that are illegal in a single path segment when writing files.
    """
    # Windows-illegal: <>:"/\|?*
    safe = re.sub(r'[<>:"/\\\\|?*]', "_", full_rule_id.strip())
    return safe
