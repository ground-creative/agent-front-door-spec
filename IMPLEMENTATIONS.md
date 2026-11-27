# Implementations

Conformance claims live here. A claim names the **role**, the **level** and the
**spec release** it was verified against (CONF-1 – CONF-5). Partial claims are
legitimate; a silent gap is not.

## Server side

| Project                                           | Language | Role            | Level          | Against     | Notes                                                                                                                                                                                                                                                 |
| ------------------------------------------------- | -------- | --------------- | -------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [vireo](https://github.com/ground-creative/vireo) | Go       | daemon (server) | L2, partial L3 | `spec-v0.4` | Reference implementation. `manifest_version` 1.3, `links`, `tags`, `capabilities`, `limits`, stable `digest`. Passes the frame and manifest fixtures. Advertises `progress`/`cancel` but has no fixture proving them yet, so L3 is claimed partially. |
| ziwa.ai                                           | —        | deployment      | L2             | `spec-v0.4` | Live endpoint at `vireo.ziwa.ai:7778`, found via `_portico._tcp.ziwa.ai`. Publicly trusted certificate covering `ziwa.ai`. `machine/conformance.py` reports 0 failures against it: ALPN `portico/1`, digest matches.                                  |

## Client side

| Project                                                   | Language | Role         | Level | Against     | Notes                                                                                                                                                               |
| --------------------------------------------------------- | -------- | ------------ | ----- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `vireo-chat` (in vireo)                                   | Go       | client       | L2    | `spec-v0.4` | Verifies certificates by default against the domain queried, not the SRV target (SEC-6, PROTO-47). Validates the manifest on receipt (MAN-47). Passes the fixtures. |
| [vireo-mcp](https://github.com/ground-creative/vireo-mcp) | Go       | host adapter | L2    | `spec-v0.4` | Same protocol vocabulary and fixtures. **The published 0.6.0 binary predates `tags` and the verification default**; the source is current.                          |

## Backend adapters

Not implementations of `portico/1`. A backend adapter sits on the *other* side of
a daemon and speaks the daemon's own HTTP webhook — it never sees a client, never
parses a frame, and never publishes a manifest. It has no conformance level to
claim, because the specification does not reach it.

They are listed because a daemon is only as useful as what answers behind it, and
because an adapter is evidence of something else: that the split between "the
endpoint" and "the thing behind it" holds up in practice.

| Project | Language | Role | Against | Notes |
| --- | --- | --- | --- | --- |
| [openclaw-bridge](https://github.com/ground-creative/vireo/tree/main/bridges/openclaw-bridge) | Go | backend adapter for vireo | vireo's webhook contract | Answers `POST /vireo/message` through an [OpenClaw](https://openclaw.ai) gateway's OpenAI-compatible Chat Completions endpoint. Maps vireo's minted session id onto the gateway's session key, so the gateway holds conversation history and nothing is resent between turns. |

A daemon written against this specification can have any number of these, and
several at once: vireo's `transport` is a per-agent default, so one endpoint can
front a stub, an adapter, and a service in another language together. Nothing in
the specification requires the backend to be written in Go or to be a program at
all.

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

## What to build next

The empty column is the point. Each row below is independently useful, needs
nobody's permission, and is most valuable when built without reading our source.

| Artifact                                             | Difficulty | What it proves                                               | Start at                                  |
| ---------------------------------------------------- | ---------- | ------------------------------------------------------------ | ----------------------------------------- |
| A client in another language                         | small      | the wire is implementable from the text alone                | `normative/PROTOCOL.md` §1–§4             |
| A daemon for one real backend                        | medium     | the manifest can describe an endpoint nobody designed it for | `normative/MANIFEST.md`, `PROTOCOL.md` §9 |
| A host adapter for a host that is not MCP            | medium     | the session model is not an MCP artefact                     | `normative/PROTOCOL.md` §3–§7             |
| A host adapter that surfaces the manifest unmodified | trivial    | an agent actually sees the contract (`MAN-59`)               | `normative/MANIFEST.md` §1                |
| A fixture for an edge case                           | trivial    | an ambiguity is a spec defect                                | `machine/fixtures/`                       |

## Adding yourself

Open a pull request with a row. Include:

- project name and link;
- language;
- role: `server`, `client`, or `host adapter`;
- level and the spec tag it was verified against;
- anything you do not satisfy (CONF-3) — partial claims are expected at this stage;
- how a third party reproduces the check (CONF-4), even if it is only "run
  `go test ./...`".

If you are unsure what level you reach, run the probe and believe its output. It
reports what it exercised, per level, and never claims a level it did not test:

```bash
python3 machine/conformance.py --endpoint your.host:7777
```
