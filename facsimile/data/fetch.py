"""Downloads and checksums.

The first fetch of a file records its SHA-256 and size in `facsimile/data/checksums.json`, which
is committed; every later fetch or read verifies against it, so a truncated, substituted or
silently revised file is an error rather than a strange result. SPARCS says on its own page
that "Data is subject to change", which is exactly the case this exists for.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
import urllib.request
from pathlib import Path
from typing import Any, Final

from facsimile import __version__

CHECKSUMS: Final = Path(__file__).with_name("checksums.json")

USER_AGENT: Final = (
    f"facsimile/{__version__} (+https://github.com/Peter-A-P/privacy-safe-data-sharing)"
)
"""Names the project and where it lives. Not a disguise: health.ny.gov refuses curl's default."""


class ChecksumError(ValueError):
    """A file on disk does not match the checksum recorded at its first fetch."""


def sha256_of(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def _load() -> dict[str, dict[str, dict[str, Any]]]:
    if not CHECKSUMS.exists():
        return {}
    data: dict[str, dict[str, dict[str, Any]]] = json.loads(CHECKSUMS.read_text(encoding="utf-8"))
    return data


def recorded(dataset: str, name: str) -> dict[str, Any] | None:
    return _load().get(dataset, {}).get(name)


def verify_or_record(dataset: str, path: Path, *, source: str) -> dict[str, Any]:
    """Verify `path` against its recorded checksum, or record it if this is the first fetch."""
    digest, size = sha256_of(path), path.stat().st_size
    entry = recorded(dataset, path.name)
    if entry is not None:
        if entry["sha256"] != digest or entry["bytes"] != size:
            raise ChecksumError(
                f"{dataset}/{path.name}: sha256 {digest[:16]} and {size} bytes, recorded "
                f"{entry['sha256'][:16]} and {entry['bytes']} bytes on {entry['fetched']}"
            )
        return entry
    data = _load()
    entry = {
        "sha256": digest,
        "bytes": size,
        "fetched": dt.date.today().isoformat(),
        "source": source,
    }
    data.setdefault(dataset, {})[path.name] = entry
    CHECKSUMS.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"recorded first-fetch checksum for {dataset}/{path.name}: {digest}")
    return entry


def verify(dataset: str, path: Path) -> dict[str, Any]:
    """Verify only: a file with no recorded checksum is an error, not a first fetch."""
    entry = recorded(dataset, path.name)
    if entry is None:
        raise ChecksumError(f"{dataset}/{path.name}: no recorded checksum")
    return verify_or_record(dataset, path, source=str(entry.get("source", "")))


def download(url: str, dest: Path, *, timeout: float = 600.0) -> Path:
    """Fetch `url` to `dest` through a temporary file, so a broken transfer leaves nothing."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response, tmp.open("wb") as out:
        shutil.copyfileobj(response, out, length=1 << 22)
    tmp.replace(dest)
    return dest
