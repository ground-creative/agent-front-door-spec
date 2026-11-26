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

import importlib.util
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


def check_digest_fixture() -> None:
    """The digest fixtures pin MAN-40's canonical form across implementations.

    A probe and a daemon that canonicalise differently report a failure on a
    correct publisher. These cases carry the digest both must compute, so the
    Python probe and the Go daemon are checked against the same bytes rather
    than against each other's assumptions.
    """
    path = ROOT / "machine" / "fixtures" / "digest.json"
    doc = json.loads(path.read_text())
    cases = doc.get("cases", [])
    if not cases:
        fail("fixtures/digest.json: no cases")
        return

    spec = importlib.util.spec_from_file_location(
        "conformance", ROOT / "machine" / "conformance.py"
    )
    if spec is None or spec.loader is None:
        fail("machine/conformance.py: cannot be imported")
        return
    conformance = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(conformance)

    for case in cases:
        expected = case.get("digest")
        if not expected or expected == "PENDING":
            fail(
                f"fixtures/digest.json: {case['name']} has no published digest; "
                "run the digest writer and commit the result"
            )
            continue
        got = conformance.digest_of(case["document"])
        if got != expected:
            fail(
                f"fixtures/digest.json: {case['name']} digest is {got}, "
                f"want {expected} (MAN-40)"
            )


def check_schema_documents_itself() -> None:
    """Every property in the schema must explain itself.

    The schema is the file an implementer builds against, so a property whose
    whole description is a requirement number ("MAN-1") documents nothing: the
    reader is sent to another document to learn what the member means. This was
    the state of the whole schema until the requirement was made explicit here.

    Two things are enforced:
      - every property carries a description long enough to be an explanation;
      - every requirement ID cited anywhere in the schema exists in a normative
        index table, so a renamed or retired requirement cannot linger.
    """
    path = ROOT / "machine" / "schema" / "manifest.schema.json"
    schema = json.loads(path.read_text())
    known = normative_requirement_ids()

    def walk(node: dict, where: str) -> None:
        for name, member in (node.get("properties") or {}).items():
            here = f"{where}.{name}" if where else name
            if not isinstance(member, dict):
                continue
            description = member.get("description") or ""
            # A bare requirement reference is not a description. Forty
            # characters is the floor below which nothing is explained.
            if "$ref" not in member and len(description.strip()) < 40:
                fail(
                    f"machine/schema: {here} has no real description; a member must "
                    "say what it means, not only which requirement defines it"
                )
            walk(member, here)
        for name, sub in (node.get("$defs") or {}).items():
            walk(sub, name)

    walk(schema, "")

    text = path.read_text()
    for match in REQUIREMENT.finditer(text):
        if match.group(0) not in known:
            fail(
                f"machine/schema: cites {match.group(0)}, which is not in any "
                "normative index table"
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


HISTORY_MARKER = "<!-- spec-version: history -->"
FENCED = re.compile(r"```.*?```", re.DOTALL)
ANY_VERSION = re.compile(r"spec-v[0-9]+\.[0-9]+")


def check_retired_identifiers() -> None:
    """No retired wire identifier may survive outside a record of history.

    The wire identifier was renamed twice during the draft, and the first rename
    landed only halfway: the ALPN string took the new name while the webhook
    headers kept the old one, so a protocol carried two naming schemes and the
    implementation's name stayed inside the standard's own contract.

    That happened because a rename is a search across prose, code and fixtures,
    and nothing failed when part of it was missed. This does.

    A line carrying ``<!-- identifier: retired -->`` is exempt, for the places
    where naming an old identifier is the point — a changelog, a decision record,
    a migration note, or the compatibility list itself.
    """
    # This list is the definition of what is retired, so it names the old
    # identifiers on purpose.
    retired = ("frontdoor/1", "_frontdoor._tcp", "X-Frontdoor-", "X-Vireo-", "vireo/1")  # <!-- identifier: retired -->
    exempt_files = {"CHANGELOG.md", "DECISIONS.md"}
    marker = "<!-- identifier: retired -->"
    # The files where an old name must appear, because they implement or
    # document the compatibility window itself.
    exempt_paths = {"machine/schema"}

    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix not in {".md", ".json", ".py"}:
            continue
        if any(part in {".git", "__pycache__"} for part in path.parts):
            continue
        if path.name in exempt_files:
            continue
        # Articles are not exempt. They publish commands a reader will run, so a
        # stale identifier there is a broken instruction, not a historical note.
        if any(str(path.relative_to(ROOT)).startswith(p) for p in exempt_paths):
            continue
        for number, line in enumerate(path.read_text().splitlines(), start=1):
            for name in retired:
                if name in line and marker not in line:
                    fail(
                        f"{path.relative_to(ROOT)}:{number}: retired identifier {name!r} "
                        f"survived the rename (mark the line {marker} if it is intentional)"
                    )


def check_spec_version_consistency() -> None:
    """Every document must name the newest release, outside history.

    A reader opening CONFORMANCE.md and seeing spec-v0.1 while the repository is
    at spec-v0.4 has no way to tell which is current. The drift is silent and
    reappears on every release, so it is checked rather than trusted.

    Prose may still mention an older tag when the line carries
    `<!-- spec-version: history -->`, which is what a list of past releases is.
    Fenced blocks are skipped: they hold illustrative transcripts. A tag with a
    major of 1 or more is a forward reference to the stable release a draft talks
    about, not a stale claim, so it is allowed without a marker.
    """
    changelog = (ROOT / "CHANGELOG.md").read_text()
    releases = CHANGELOG_HEADING.findall(changelog)
    if not releases:
        fail("CHANGELOG.md names no release")
        return
    newest = releases[0]

    # History belongs in these files by design.
    skip = {"CHANGELOG.md", "DECISIONS.md"}

    documents = [
        ROOT / "README.md",
        ROOT / "GOVERNANCE.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "IMPLEMENTATIONS.md",
    ]
    for folder in ("normative", "informative", "articles", "proposals"):
        documents.extend(sorted((ROOT / folder).glob("*.md")))
    documents.extend(sorted((ROOT / ".github").rglob("*.md")))

    for path in documents:
        if not path.exists() or path.name in skip:
            continue
        text = FENCED.sub("", path.read_text())
        for number, line in enumerate(text.splitlines(), start=1):
            for version in ANY_VERSION.findall(line):
                if version == newest or HISTORY_MARKER in line:
                    continue
                if int(version.split("v")[1].split(".")[0]) >= 1:
                    continue  # forward reference to the stable release
                relative = path.relative_to(ROOT)
                fail(
                    f"{relative}:{number}: says {version}, but the newest release is "
                    f"{newest} (mark the line {HISTORY_MARKER} if the older tag is intentional)"
                )

    probe = (ROOT / "machine" / "conformance.py").read_text()
    for version in re.findall(r'SPEC_VERSION = "(spec-v[0-9]+\.[0-9]+)"', probe):
        if version != newest:
            fail(
                f"machine/conformance.py: says {version}, but the newest release is {newest}"
            )


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
    check_digest_fixture()
    check_schema_documents_itself()
    check_retired_identifiers()
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
