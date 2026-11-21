# Agent Front Door

**An open specification for a communication channel built for AI agents, not for
browsers.**

> **Status: draft (spec-v0.1), seeking implementers.** Nothing here has been
> ratified. The point of publishing it is to find the places where it is wrong
> before anyone builds production traffic on it. See
> [`informative/PROPOSAL.md`](informative/PROPOSAL.md).

## The idea in one paragraph

Every business already has a front door for humans: a domain name, a website,
HTTP, HTML, cookies, forms. That door is built for a reader with eyes — it
carries navigation, styling and scripts, it assumes a session kept in a browser,
and it defends itself against automation with bot walls and captchas. An AI agent
that needs to know whether a business covers the north side has to walk through
that door wearing a human costume: fetch pages, parse markup, guess which link
matters, and hope the layout does not change. What is missing is a second door,
built for a different kind of caller — one that names the business by its own
domain, publishes a declarative description of what it offers, and then holds an
actual conversation with explicit beginning, progress and end.

This repository is that second door, written down.

## What is here

| Layer  | Artifact                                                            | Who adopts it              |
| ------ | ------------------------------------------------------------------- | -------------------------- |
| L0     | DNS SRV record naming the endpoint                                  | a business with DNS access |
| **L1** | **the manifest** — a declarative description of endpoint and agents | anyone, no daemon required |
| L2     | session protocol — framing, handshake, messages, progress, cancel   | daemon authors             |
| L3     | backend contract — the webhook a business answers on                | backend authors            |

The manifest is the adoption hook. A business can publish one before it owns a
daemon, before it has TLS, before it writes a line of protocol code. The
conversation channel is what the manifest describes.

## Conformance levels

Implementations claim a level; they do not have to implement everything.

| Level  | Name               | Requires                                                 | Typical implementer                    |
| ------ | ------------------ | -------------------------------------------------------- | -------------------------------------- |
| **L0** | Manifest publisher | publishes a valid manifest document                      | a business, a marketing site           |
| **L1** | Discovery          | L0 + DNS SRV + TLS 1.3 + ALPN + `negotiate` → `manifest` | a read-only client or a minimal daemon |
| **L2** | Conversations      | L1 + sessions + `message`/`data`/`end` + webhook         | a business daemon                      |
| **L3** | Live               | L2 + `partial` progress + `cancel`                       | a production daemon                    |
| **L4** | Operational        | L3 + advertised limits + persistence + retention         | a hosted deployment                    |

Conformance is claimed against a **spec tag**, not against a branch:
`vireo 1.x — L3, spec-v0.1`. See [`normative/CONFORMANCE.md`](normative/CONFORMANCE.md).

## The 20-minute path

You do not need any of this repository's machinery to start.

1. Write a manifest. Start from
   [`machine/examples/manifest.minimal.json`](machine/examples/manifest.minimal.json).
2. Check it against [`machine/schema/manifest.schema.json`](machine/schema/manifest.schema.json).
3. Publish it wherever you publish documents, and say so in your docs.

That is L0. It costs one file, and it already tells any agent what you expose
and what each agent claims to do. Discovery and conversation are additive: when
a daemon exists, the same manifest arrives inside the connection instead.

## Repository map

```
normative/      the contract. changes require a proposal.
  MANIFEST.md     the manifest object, field by field, with requirement IDs
  PROTOCOL.md     framing, handshake, sessions, webhook, errors
  CONFORMANCE.md  levels, requirement matrix, how to claim one
  SECURITY.md     threat model, TLS rules, identity, what is not protected

informative/    reasoning and interpretation. may be rewritten freely.
  PROPOSAL.md     the problem, the principles, the front-door argument
  RATIONALE.md    why DNS SRV, why the manifest rides inside the connection
  COMPARISON.md   versus MCP, A2A Agent Cards, OpenAPI, llms.txt, scraping
  FAQ.md          the questions the first reviewers ask

machine/        the checkable parts, versioned with the prose.
  schema/         JSON Schema for a manifest
  examples/       a minimal manifest, a full one, a deployed one
  fixtures/       frame hex, handshakes, valid/invalid manifests, webhook pairs

proposals/      numbered change proposals (see 0001-template.md)
articles/       published posts, each pinned to a spec tag
```

## Versioning

Two independent version numbers, deliberately:

- **Spec tag** — `spec-v0.1`, `spec-v0.2`. A release of this repository. Cited by
  articles and conformance claims. A tag never moves.
- **`manifest_version`** — a value inside the manifest, e.g. `1.1`. The
  compatibility contract of the document itself. Minor bumps are additive and
  backwards compatible; a client that sees a newer minor ignores what it does not
  know.

The wire protocol identifier (`vireo/1`) is separate again and changes only for
incompatible framing or semantic changes.

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) and
[`GOVERNANCE.md`](GOVERNANCE.md). The short version: open a numbered proposal,
cite the requirement ID you want to change, say what an implementation must do
differently, and say whether it is additive. A well-argued objection is more
useful at this stage than an implementation that agrees with us.

## Implementations

[`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md) lists what exists and what level it
claims. Today: one daemon, one terminal client, one MCP adapter, one deployment.
Independent implementations are the only real measure of whether any of this
works — that column is deliberately almost empty.

## License

Apache-2.0. See [`LICENSE`](LICENSE).
