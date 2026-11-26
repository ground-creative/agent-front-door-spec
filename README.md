# Agent Front Door

**An open specification for a channel built for AI agents, at the endpoint's own
domain, without a directory or marketplace in between.**

> **Status: draft (spec-v0.4), seeking implementers.** Nothing here is ratified.
> It is published to find where it is wrong before anyone runs production traffic
> on it. One implementation exists; that is evidence, not adoption.

---

## The problem

Every party that owns a domain already has a front door for humans: a website,
HTTP, HTML, cookies, forms. That door is built for a reader with eyes. It carries
navigation, styling and scripts, it assumes a session kept in a browser, and it
defends itself against automation with bot walls and captchas. Most often the
party is a business, and this document uses that case throughout because it is
the one everybody recognises — but it is not a boundary. The same design serves a
person, a studio, or an agent running on hardware someone owns.

An AI agent that needs one fact has to walk through that door wearing a human
costume: fetch pages, parse markup, guess which link matters, and hope the layout
does not change. One answer costs several pages and a parse. When the layout
changes the integration breaks quietly, and nobody notices until an answer is
wrong.

Custom APIs, GraphQL schemas, OpenAPI documents and MCP servers each solve this
for one service, built for one assistant, by somebody who decided it was worth the
work. Nothing carries over to the next business or the next assistant.

The gap is not capability. It is **a contract**: one way to name an endpoint, one
way to describe what it exposes, one way to hold a conversation with it, one way
to say _finished_, _still working_, or _gave up_.

## The proposal

A second door, next to the website, at the address the business already owns.

|                           | for humans                | for agents                                          |
| ------------------------- | ------------------------- | --------------------------------------------------- |
| how it is found           | a URL you type            | `_portico._tcp.<domain>` in the business's own DNS  |
| what arrives first        | an HTML page              | a **manifest**: what this endpoint exposes          |
| what carries the exchange | forms, cookies, redirects | a **session** with explicit turns, progress and end |

Nothing is registered anywhere. A domain is already owned, already delegated, and
already maintained by the business, and each zone is authoritative for its own
records. Discovery needs nobody's approval — which is the point.

**The business keeps everything that makes it a business**: its backend, models,
logic and data. The specification standardises the contract between the two sides,
not the software behind it, and implies no model, provider, language or agent
framework.

## What the agent receives

This is the artifact the whole specification exists to define. When a caller
opens a session, the first thing it learns is a manifest — a data document, not a
page, with no layout and no script:

```json
{
  "manifest_version": "1.3",
  "protocol": "portico/1",
  "endpoint": {
    "name": "acme-plumbing",
    "description": "Plumbing and heating"
  },
  "capabilities": {
    "session": { "new": true, "get": true, "close": true },
    "progress": true,
    "cancel": true
  },
  "agents": [
    {
      "name": "bookings",
      "description": "Book a visit, change or cancel an appointment",
      "sessions": true,
      "start_message": "Which day suits you?"
    },
    {
      "name": "support",
      "description": "Questions about service, coverage and pricing",
      "sessions": false
    }
  ],
  "digest": "sha256:…"
}
```

Every member is documented in
[`machine/schema/manifest.schema.json`](machine/schema/manifest.schema.json), in
plain language, with the requirement ID that states the obligation. That file is
enough to write a publisher; you do not need the normative text to produce a valid
document.

That is the shape. `machine/examples/manifest.full.json` is a complete one, with every
optional member present, and the probe checks it:

```bash
python3 machine/conformance.py --payload machine/examples/manifest.full.json
```

The manifest is not a web page and it is not a service description for
programmers. It answers four questions for a caller that has just arrived: _what
does this business expose, what can I do with each thing, where do I look for
more, and what must I obey._

## The four normative documents

| Document                                               | Defines                                                                              | Requirements           |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------ | ---------------------- |
| [`normative/MANIFEST.md`](normative/MANIFEST.md)       | the object above, member by member                                                   | `MAN-1` … `MAN-57`     |
| [`normative/PROTOCOL.md`](normative/PROTOCOL.md)       | framing, handshake, messages, progress, cancel, sessions, errors, webhook, discovery | `PROTO-1` … `PROTO-48` |
| [`normative/CONFORMANCE.md`](normative/CONFORMANCE.md) | what a conformance claim means and what each level requires                          | `CONF-1` … `CONF-21`   |
| [`normative/SECURITY.md`](normative/SECURITY.md)       | threat model, TLS rules, identity, what is not protected                             | `SEC-1` …              |

The argument for all of it is in [`informative/PROPOSAL.md`](informative/PROPOSAL.md).
Why DNS rather than a well-known URL is
[`informative/RATIONALE.md`](informative/RATIONALE.md). How it compares to MCP,
A2A, OpenAPI and `llms.txt` is
[`informative/COMPARISON.md`](informative/COMPARISON.md).

## Check a document or a running endpoint

`machine/conformance.py` is a client written against this specification alone. It
shares no code with any implementation, which is what makes it evidence rather
than self-assessment. It has two modes.

**A captured payload** — what an agent was actually shown when it connected:

```bash
python3 machine/conformance.py --payload payload.json
```

**A running endpoint** — the full protocol, requirement by requirement:

```bash
python3 machine/conformance.py --endpoint 127.0.0.1:7777 --insecure
```

It prints `PASS`, `FAIL` or `SKIP` per requirement and exits non-zero on any
failure, so it gates CI. It reports what it exercised and does not claim a level
it did not test:

```text
claim: 127.0.0.1:7777 — spec-v0.4, 0 failure(s)
  L1 discovery: verified
  L2 conversations: PARTIAL (2 not exercised)
  L3 live: not tested
```

Add `--converse` to send one real message and verify the turn itself
(`PROTO-19` … `PROTO-22`). It is off by default: a turn reaches the business's
backend and may cost it a model call, so spending somebody else's money is opt-in.

The probe caught a genuine interop defect in the reference implementation the
first time it ran with the digest fixture: the daemon hashed a re-serialisation of
its own struct rather than the document it published, so no client could ever
reproduce the digest. That is the failure mode this tool exists to find.

## What to build

Everything below is independently useful. None of it requires permission, and the
specification is at its most valuable when somebody builds one of these without
reading our source.

| Build                                                   | Difficulty | What it proves                                                    | Start at                        |
| ------------------------------------------------------- | ---------- | ----------------------------------------------------------------- | ------------------------------- |
| A client in another language (Python, TypeScript, Rust) | small      | the wire is implementable from the text alone                     | `PROTOCOL.md` §1–§4             |
| A daemon for one real backend                           | medium     | the manifest can describe a business you did not design for       | `MANIFEST.md`, `PROTOCOL.md` §9 |
| A host adapter for a host that is not MCP               | medium     | the session model is not an MCP artefact                          | `PROTOCOL.md` §3–§7             |
| A fixture for an edge case                              | trivial    | an ambiguity is a specification defect, not an implementation bug | `machine/fixtures/`             |
| A host adapter that surfaces the manifest unmodified    | trivial    | an agent actually sees the contract                               | `MAN-59`                        |

If the manifest cannot express something your business really does, **that is the
most useful thing you can report**. Open an issue with the requirement ID.

## Conformance levels

Levels are cumulative and a claim names the release it was verified against, for
example `vireo 1.x — L2, spec-v0.4`. Partial claims are legitimate; silent gaps
are not — a claim must list every requirement it does not satisfy.

| Level | Name          | Requires                                                 |
| ----- | ------------- | -------------------------------------------------------- |
| L1    | Discovery     | DNS SRV, TLS 1.3, ALPN, `negotiate` → manifest           |
| L2    | Conversations | L1 + sessions + `message`/`data`/`end` + backend webhook |
| L3    | Live          | L2 + progress + cancellation                             |
| L4    | Operational   | L3 + advertised limits + persistence + retention         |

See [`normative/CONFORMANCE.md`](normative/CONFORMANCE.md) for the requirement
matrix.

## Repository map

```
normative/      the contract. changes require a proposal.
  MANIFEST.md     the manifest object, member by member, with requirement IDs
  PROTOCOL.md     framing, handshake, sessions, webhook, errors
  CONFORMANCE.md  levels, requirement matrix, how to claim one
  SECURITY.md     threat model, TLS rules, identity, what is not protected

informative/    reasoning and interpretation. may be rewritten freely.
  PROPOSAL.md     the problem, the principles, the front-door argument
  RATIONALE.md    why DNS SRV, why the manifest rides inside the connection
  COMPARISON.md   versus MCP, A2A Agent Cards, OpenAPI, llms.txt, scraping
  FAQ.md          the questions the first reviewers ask

machine/        the checkable parts, versioned with the prose.
  schema/         JSON Schema, every member documented in plain language
  examples/       a minimal manifest and a full one
  fixtures/       frame hex, handshakes, valid/invalid manifests, digest cases
  conformance.py  the independent probe: a payload, or a running endpoint
  check.py        validates this repository's own documents and fixtures

proposals/      numbered change proposals (see 0001-template.md)
articles/       published posts, each pinned to a spec tag
```

## Versioning

Two independent version numbers, deliberately:

- **Spec tag** — `spec-v0.1`, `spec-v0.2`, `spec-v0.4`.<!-- spec-version: history -->
  A release of this repository. Cited by articles and conformance claims. A tag
  never moves.
- **`manifest_version`** — a value inside the manifest, e.g. `1.3`. The
  compatibility contract of the document itself. Minor bumps are additive and
  backwards compatible; a client that sees a newer minor ignores what it does not
  know.

The wire protocol identifier (`portico/1`) is separate again and changes only
for incompatible framing or semantic changes.

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) and
[`GOVERNANCE.md`](GOVERNANCE.md). The short version: implement something, then say
where the text made you guess. A well-argued objection with a requirement ID is
worth more at this stage than an implementation that agrees with us.

## Implementations

[`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md) lists what exists and what level it
claims. Today: one daemon, one terminal client, one MCP adapter, one deployment.
Independent implementations are the only real measure of whether any of this
works — that column is deliberately almost empty, and filling it is the work.

## License

Apache-2.0. See [`LICENSE`](LICENSE).
