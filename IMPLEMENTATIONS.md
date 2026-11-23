# Implementations

Conformance claims live here. A claim names the **role**, the **level** and the
**spec release** it was verified against (CONF-1 – CONF-5). Partial claims are
legitimate; a silent gap is not.

## Server side

| Project                                           | Language | Role            | Level          | Against     | Notes                                                                                                                                                                                                                                                 |
| ------------------------------------------------- | -------- | --------------- | -------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [vireo](https://github.com/ground-creative/vireo) | Go       | daemon (server) | L2, partial L3 | `spec-v0.4` | Reference implementation. `manifest_version` 1.3, `links`, `tags`, `capabilities`, `limits`, stable `digest`. Passes the frame and manifest fixtures. Advertises `progress`/`cancel` but has no fixture proving them yet, so L3 is claimed partially. |
| ziwa.ai                                           | —        | deployment      | L2             | `spec-v0.4` | Live endpoint at `vireo.ziwa.ai:7778`, found via `_frontdoor._tcp.ziwa.ai`. Publicly trusted certificate covering `ziwa.ai`. Verified by `machine/conformance.py` on 2026-11-21: 16 pass, 1 skip (`session.prune`, not probed).                           |

## Client side

| Project                                                   | Language | Role         | Level | Against     | Notes                                                                                                                                                               |
| --------------------------------------------------------- | -------- | ------------ | ----- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `vireo-chat` (in vireo)                                   | Go       | client       | L2    | `spec-v0.4` | Verifies certificates by default against the domain queried, not the SRV target (SEC-6, PROTO-47). Validates the manifest on receipt (MAN-47). Passes the fixtures. |
| [vireo-mcp](https://github.com/ground-creative/vireo-mcp) | Go       | host adapter | L2    | `spec-v0.4` | Same protocol vocabulary and fixtures. **The published 0.6.0 binary predates `tags` and the verification default**; the source is current.                          |

## How these were checked

Two independent checks, one static and one live:

```bash
# 1. the specification's own documents and fixtures
python3 machine/check.py

# 2. a running endpoint, as a client in any language would see it
python3 machine/conformance.py --endpoint vireo.ziwa.ai:7778 --server-name ziwa.ai
```

The second is the one that matters here: it shares no code with `vireo`, so it
is evidence rather than self-assessment. `--server-name` is the domain the
client asked for; SRV resolves it to another host, and the certificate is checked
against the queried name (`PROTO-47`).

For the implementation's own tests:

```bash
# in the vireo checkout, with the specification next to it
./scripts/check-conformance.sh ../agent-front-door-spec
```

That runs the fixture tests: frame hex round-trips, manifest documents that must
be accepted and rejected, and a check that every requirement ID cited by a fixture
exists in the normative text.

## Manifest publishers (L0)

| Publisher | Manifest | Notes                                                                                                                      |
| --------- | -------- | -------------------------------------------------------------------------------------------------------------------------- |
| —         | —        | Be the first. One file, no daemon. See [`machine/examples/manifest.minimal.json`](machine/examples/manifest.minimal.json). |

## Adding yourself

Open a pull request with a row. Include:

- project name and link;
- language;
- role: `server`, `client`, or `host adapter`;
- level and the spec tag it was verified against;
- anything you do not satisfy (CONF-3) — partial claims are expected at this stage;
- how a third party reproduces the check (CONF-4), even if it is only "run
  `go test ./...`".

If you are unsure what level you reach, start at L0: a valid manifest you actually
publish. That is a real contribution, and it is the level that grows the ecosystem.
