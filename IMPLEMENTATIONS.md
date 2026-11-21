# Implementations

Conformance claims live here. A claim names the **role**, the **level** and the
**spec release** it was verified against (CONF-1 – CONF-5). Partial claims are
legitimate; a silent gap is not.

## Server side

| Project | Language | Role | Level | Against | Notes |
| --- | --- | --- | --- | --- | --- |
| [vireo](https://github.com/ground-creative/vireo) | Go | daemon (server) | in progress | `spec-v0.1` | Reference implementation. Emits `manifest_version` 1.1; `links`/`actions` derived from `refs`/config. |
| ziwa.ai | — | deployment | L2 (partial) | pre-`spec-v0.1` | Live endpoint used for testing. Verification and L3 features pending. |

## Client side

| Project | Language | Role | Level | Against | Notes |
| --- | --- | --- | --- | --- | --- |
| `vireo-chat` (in vireo) | Go | client | in progress | `spec-v0.1` | Direct `vireo/1` client, no MCP in the path. |
| [vireo-mcp](https://github.com/ground-creative/vireo-mcp) | Go | host adapter | in progress | `spec-v0.1` | Maps the protocol onto MCP tools for MCP-speaking hosts. |

## Manifest publishers (L0)

| Publisher | Manifest | Notes |
| --- | --- | --- |
| — | — | Be the first. One file, no daemon. See [`machine/examples/manifest.minimal.json`](machine/examples/manifest.minimal.json). |

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
