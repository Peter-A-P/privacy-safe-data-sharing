"""The website reads only what the report wrote, and every element its script fills exists.

The page is static: `facsimile site` writes `site/data.json` from the committed results, and
`site/app.js` draws it. If the committed file falls behind the results, or the script looks for an
element the page no longer has, the published page is wrong without anything failing; these tests
are what fails instead.
"""

from __future__ import annotations

import json
import re

from facsimile import report
from facsimile.paths import REPO

SITE = REPO / "site"
TYPOGRAPHIC = {chr(c) for c in (0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D)}


def test_the_committed_data_is_what_the_report_builds_now() -> None:
    committed = json.loads((SITE / "data.json").read_text(encoding="utf-8"))
    built = json.loads(json.dumps(report.build()))
    for key in ("cells", "surface", "leaks", "agreement", "groundhog_reference", "gate"):
        assert committed[key] == built[key], (
            f"site/data.json is stale in {key!r}: run facsimile site"
        )
    assert set(committed["dcr_null"]) == set(report.DATASETS)


def test_every_element_the_script_fills_is_on_the_page() -> None:
    script = (SITE / "app.js").read_text(encoding="utf-8")
    page = (SITE / "index.html").read_text(encoding="utf-8")
    wanted = set(re.findall(r'\$\("([a-z0-9-]+)"\)', script))
    present = set(re.findall(r'id="([a-z0-9-]+)"', page))
    assert wanted and wanted <= present, sorted(wanted - present)


def test_the_site_uses_plain_punctuation_and_no_off_origin_script() -> None:
    for path in SITE.glob("*.*"):
        if path.suffix not in {".html", ".js", ".css"}:
            continue
        text = path.read_text(encoding="utf-8")
        # Typographic dashes and curly quotes, named by code point so this file has none.
        assert not set(text) & TYPOGRAPHIC, path.name
        assert not re.search(r"<script[^>]+src=\"https?:", text), path.name


def test_the_architecture_page_links_back() -> None:
    page = (SITE / "architecture.html").read_text(encoding="utf-8")
    assert page.count('href="index.html"') >= 2
    for svg in re.findall(r'src="(architecture/[a-z-]+\.svg)"', page):
        assert (SITE / svg).exists(), svg
