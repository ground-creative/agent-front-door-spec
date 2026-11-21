# Implementations

Conformance claims live here. A claim names the **role**, the **level** and the
**spec release** it was verified against (CONF-1 – CONF-5). Partial claims are
legitimate; a silent gap is not.

## Server side

| Project                                           | Language | Role            | Level          | Against             | Notes                                                                                                                                                                                               |
| ------------------------------------------------- | -------- | --------------- | -------------- | ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [vireo](https://github.com/ground-creative/vireo) | Go       | daemon (server) | L3, partial L4 | `spec-v0.1` (draft) | Reference implementation. Emits `manifest_version` 1.1. Passes the frame and manifest fixtures. Does not yet advertise/verify every L4 item (restart semantics documented, retention configurable). |
| ziwa.ai                                           | —        | deployment      | L2             | pre-`spec-v0.1`     | Live endpoint used for testing. Runs an older build: no `manifest_version`, no `links`, verification not enforced.                                                                                  |

## Client side

| Project                                                   | Language | Role         | Level | Against             | Notes                                                                                                                         |
| --------------------------------------------------------- | -------- | ------------ | ----- | ------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `vireo-chat` (in vireo)                                   | Go       | client       | L3    | `spec-v0.1` (draft) | Verifies certificates by default (SEC-6). Validates the manifest on receipt (MAN-47). Passes the frame and manifest fixtures. |
| [vireo-mcp](https://github.com/ground-creative/vireo-mcp) | Go       | host adapter | L3    | `spec-v0.1` (draft) | Same protocol vocabulary, same fixtures, same verification default. Mirrored structs must stay identical.                     |

## How these were checked

```bash
# in the vireo checkout, with the specification next to it
./scripts/check-conformance.sh ../agent-front-door-spec
```

That runs the fixture tests: frame hex round-trips, manifest documents that must
be accepted and rejected, and a check that every requirement ID cited by a fixture
exists in the normative text. The L4 items are the ones with no fixture yet, which
is why the claim is partial.

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
