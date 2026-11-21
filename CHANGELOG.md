# Changelog

Spec releases are tagged `spec-vX.Y` and never move. This file records what
changed and which requirement IDs are affected.

## spec-v0.2 — draft

**Removed `actions`.** `manifest_version` goes to **1.2**.

`actions` was an array of named things an agent claimed it could do. It is gone
because nothing consumed it:

- no client routed on it — both reference clients only printed it;
- there is no `invoke` frame, so an action name could not select anything;
- `MAN-26` said it was not a whitelist and `MAN-25` said its fields were hints,
  which makes it non-binding by its own definition;
- two independent readers read it as quick replies and as an exclusive list of
  capabilities, neither of which it meant. A field whose name reliably misleads
  is a defect (PROPOSAL.md, "explicit over inferred").

`MAN-24` – `MAN-27` are retired, not reused (MANIFEST.md §18). A client built
against 1.1 that reads `actions` simply finds it absent, which `MAN-49` already
requires it to tolerate. A publisher MUST NOT emit it; a client MUST ignore one it
receives.

Considered and rejected: replacing `actions` with `tags: []string`. Tags would
cover the only real use (deterministic filtering) in one line, but adding a field
with no consumer repeats the same mistake in a better costume. The option is
recorded in `DECISIONS.md` D-8 so a future proposal can pick it up when a host
actually needs it.

Also in this release: `machine/check.py` validates inline JSON in fenced blocks,
so a formatter cannot leave a broken example behind; `manifests.json` fixtures are
split by obligation (client-rejectable, publisher-only, client-acceptable).

## spec-v0.1 — draft

First published draft. Establishes:

**Normative**

- `normative/MANIFEST.md` — the manifest object at `manifest_version` **1.1**.
  Adds `manifest_version`, `links`, `actions`, `capabilities`, `limits`,
  `agents[].id`, `generated_at`, `expires_at`, `digest`, `signature` (reserved).
  Deprecates `refs` (MAN-44) and `commands` (MAN-45). 54 requirements.
- `normative/PROTOCOL.md` — the `vireo/1` wire protocol, with requirement IDs
  assigned to every rule. 47 protocol requirements, 13 webhook requirements.
- `normative/CONFORMANCE.md` — levels L0–L4, 25 requirements.
- `normative/SECURITY.md` — threat model, TLS rules, client identity, manifest
  restrictions, 30 requirements.

**Machine**

- `machine/schema/manifest.schema.json` — JSON Schema for `manifest_version` 1.1.
- `machine/examples/` — minimal, full, and a deployed manifest.
- `machine/fixtures/` — frame encodings, a handshake, valid and invalid
  manifests, webhook pairs.

**Informative**

- `informative/PROPOSAL.md` — the front-door argument.
- `informative/RATIONALE.md`, `informative/COMPARISON.md`, `informative/FAQ.md`.

### Compatibility notes

- `manifest_version` **1.0** (a manifest with no `manifest_version`) remains valid.
  A client MUST treat its absence as `1.0` (MAN-53) and fall back to `refs` and
  `commands`.
- No wire incompatibility with the pre-release `vireo/1` implementations. The
  added frames (`partial`, `cancel`) are ignored by readers that do not know them
  (PROTO-6).

### Known gaps in this draft

- `signature` is reserved, not specified (SEC-29, open question 1 in SECURITY §8).
- `actions[].input`/`output` are free-form hints, not schemas (MAN-25).
- Client authentication is out of scope (SEC-14).
- Transport discovery publishes one `_tcp` record (PROTO-44 note).
