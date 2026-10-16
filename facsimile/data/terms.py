"""The terms gate: no loader fetches or reads a dataset whose terms are not recorded as permitting it.

CLAUDE.md: terms are quoted in `docs/data.md` before the first fetch, and a dataset whose terms
do not permit the use is dropped, not bent. Written down, that rule decays into a document
nobody checks; wired into the loader it costs nothing. `docs/data.md` carries a register table
under the heading `## Terms register`, and every loader calls `require()` first. A row that does
not say `Yes` in the Permitted column, with a date in the Read column, stops the loader.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from facsimile.paths import DOCS

REGISTER_HEADING = "## Terms register"
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


class TermsError(PermissionError):
    """The register does not record terms that permit this use."""


@dataclass(frozen=True, slots=True)
class Entry:
    dataset: str
    read: str
    permitted: str

    @property
    def allowed(self) -> bool:
        return self.permitted.strip().lower().startswith("yes") and bool(DATE.search(self.read))


def register(path: Path | None = None) -> dict[str, Entry]:
    text = (path or DOCS / "data.md").read_text(encoding="utf-8")
    if REGISTER_HEADING not in text:
        raise TermsError(f"no '{REGISTER_HEADING}' section in {path or 'docs/data.md'}")
    section = text.split(REGISTER_HEADING, 1)[1].split("\n## ", 1)[0]
    rows = [line for line in section.splitlines() if line.startswith("|")]
    if len(rows) < 3:
        raise TermsError("the terms register has no rows")
    header = [c.strip().lower() for c in rows[0].strip("|").split("|")]
    try:
        i_key, i_read, i_ok = header.index("key"), header.index("read"), header.index("permitted")
    except ValueError as exc:
        raise TermsError(
            f"the register needs Key, Read and Permitted columns, has {header}"
        ) from exc
    entries: dict[str, Entry] = {}
    for line in rows[2:]:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        key = cells[i_key].strip("`")
        entries[key] = Entry(key, cells[i_read], cells[i_ok])
    return entries


def require(dataset: str, path: Path | None = None) -> Entry:
    entry = register(path).get(dataset)
    if entry is None:
        raise TermsError(f"{dataset}: no row in the terms register; read and quote the terms first")
    if not entry.allowed:
        raise TermsError(
            f"{dataset}: the register says Read={entry.read!r}, Permitted={entry.permitted!r}; "
            "nothing is fetched or read until it says Yes with a date"
        )
    return entry
