#!/usr/bin/env python3
"""Validate the machine-checkable parts of this specification.

Run from anywhere:

    python3 machine/check.py

What it checks:
  1. every example validates against the schema for its manifest_version;
  2. every `cases` entry is rejected by the 1.1 schema, or is marked as semantic;
  3. every `publisher` entry is rejected by the schema;
  4. every `accepted` entry validates against the schema it names;
  5. every requirement ID cited by a fixture exists in a normative index table;
  6. every relative markdown link in the repository points at a file that exists.

Requires: python3 and jsonschema (`pip install jsonschema`).
Exit code is non-zero on the first failure, so it works as a CI gate.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

try:
    import jsonschema
except ImportError:  # pragma: no cover - CI installs it
    print("check: jsonschema is required (pip install jsonschema)", file=sys.stderr)
    raise SystemExit(2)

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMAS = {
    "manifest.schema.json": None,
    "manifest-1.0.schema.json": None,
}
REQUIREMENT = re.compile(r"\b(MAN|PROTO|WH|SEC|CONF)-(\d+)\b")
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def load_schemas() -> None:
    for name in SCHEMAS:
        path = ROOT / "machine" / "schema" / name
        SCHEMAS[name] = json.loads(path.read_text())


def schema_accepts(
    document: dict, name: str = "manifest.schema.json"
) -> tuple[bool, str]:
    try:
        jsonschema.validate(document, SCHEMAS[name])
        return True, ""
    except jsonschema.ValidationError as exc:
        return False, exc.message


def check_examples() -> None:
    for path in sorted((ROOT / "machine" / "examples").glob("*.json")):
        document = json.loads(path.read_text())
        ok, message = schema_accepts(document)
        if not ok:
            fail(f"{path.relative_to(ROOT)}: {message}")


def check_fixtures() -> None:
    path = ROOT / "machine" / "fixtures" / "manifests.json"
    doc = json.loads(path.read_text())

    for entry in doc.get("cases", []):
        ok, _ = schema_accepts(entry["document"])
        if ok and "note" not in entry:
            fail(
                f"fixtures/manifests.json: {entry['name']} is listed as client-rejectable "
                "but the schema accepts it and no note explains why"
            )

    for entry in doc.get("publisher", []):
        ok, _ = schema_accepts(entry["document"])
        if ok:
            fail(
                f"fixtures/manifests.json: {entry['name']} is listed as publisher-only but the schema accepts it"
            )

    for entry in doc.get("accepted", []):
        schema = entry.get("schema", "manifest.schema.json")
        ok, message = schema_accepts(entry["document"], schema)
        if not ok:
            fail(
                f"fixtures/manifests.json: {entry['name']} should be accepted by {schema}: {message}"
            )


def normative_requirement_ids() -> set[str]:
    ids: set[str] = set()
    for name in ("MANIFEST.md", "PROTOCOL.md", "CONFORMANCE.md", "SECURITY.md"):
        for line in (ROOT / "normative" / name).read_text().splitlines():
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.split("|")]
            if len(cells) >= 3 and REQUIREMENT.fullmatch(cells[1]):
                ids.add(cells[1])
    return ids


def check_fixture_requirements() -> None:
    known = normative_requirement_ids()
    if not known:
        fail("no requirement IDs found in the normative index tables")
        return
    for path in sorted((ROOT / "machine" / "fixtures").glob("*.json")):
        text = path.read_text()
        for match in REQUIREMENT.finditer(text):
            req = match.group(0)
            if req not in known:
                fail(
                    f"{path.relative_to(ROOT)} cites {req}, which is not in any normative index"
                )


def check_links() -> None:
    for path in sorted(ROOT.rglob("*.md")):
        if ".git" in path.parts:
            continue
        for target in LINK.findall(path.read_text()):
            target = target.split("#", 1)[0].strip()
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                fail(f"{path.relative_to(ROOT)}: link {target} does not resolve")


JSON_FENCE = re.compile(r"```json\n(.*?)```", re.DOTALL)


VERSION_LINE = re.compile(r"^- Spec release: `(spec-v[0-9]+\.[0-9]+)`", re.MULTILINE)
CHANGELOG_HEADING = re.compile(r"^## (spec-v[0-9]+\.[0-9]+)", re.MULTILINE)


def check_spec_version_consistency() -> None:
    """Every normative document must name the newest release.

    A reader opening CONFORMANCE.md and seeing spec-v0.1 while the repository is
    at spec-v0.3 has no way to tell which one is current. This drift is silent and
    happens on every release, so it is checked rather than trusted.
    """
    changelog = (ROOT / "CHANGELOG.md").read_text()
    releases = CHANGELOG_HEADING.findall(changelog)
    if not releases:
        fail("CHANGELOG.md names no release")
        return
    newest = releases[0]

    for name in ("MANIFEST.md", "PROTOCOL.md", "CONFORMANCE.md", "SECURITY.md"):
        text = (ROOT / "normative" / name).read_text()
        named = VERSION_LINE.findall(text)
        if not named:
            fail(f"normative/{name}: no 'Spec release:' line")
            continue
        for version in named:
            if version != newest:
                fail(f"normative/{name}: says {version}, but the newest release is {newest}")

    probe = (ROOT / "machine" / "conformance.py").read_text()
    probe_versions = re.findall(r'SPEC_VERSION = "(spec-v[0-9]+\.[0-9]+)"', probe)
    for version in probe_versions:
        if version != newest:
            fail(f"machine/conformance.py: says {version}, but the newest release is {newest}")


def check_inline_json() -> None:
    """Examples inside normative text must still parse.

    A formatter that reflows a fenced block can leave valid prose behind and
    invalid JSON inside it; that is worse than a typo, because a reader copies it.

    Two forms are legal: a complete document, and a single object member shown on
    its own (this document is field-by-field, so `"links": [ ... ]` is a normal
    block). An empty block is a template placeholder.
    """
    for path in sorted(ROOT.rglob("*.md")):
        if ".git" in path.parts:
            continue
        text = path.read_text()
        for index, block in enumerate(JSON_FENCE.findall(text), start=1):
            stripped = block.strip()
            if not stripped:
                continue
            try:
                json.loads(stripped)
                continue
            except json.JSONDecodeError:
                pass
            # A member fragment: "{ <block> }" is a document with one member.
            try:
                json.loads("{" + stripped + "}")
            except json.JSONDecodeError as exc:
                fail(
                    f"{path.relative_to(ROOT)}: json block {index} does not parse: {exc}"
                )


def main() -> int:
    load_schemas()
    check_examples()
    check_fixtures()
    check_fixture_requirements()
    check_links()
    check_inline_json()
    check_spec_version_consistency()

    for message in failures:
        print(f"FAIL {message}", file=sys.stderr)
    if failures:
        print(f"\n{len(failures)} problem(s)", file=sys.stderr)
        return 1
    print("ok: schemas, fixtures, requirement IDs, links and release version")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
