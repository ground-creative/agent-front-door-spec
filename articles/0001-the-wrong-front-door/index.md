---
title: The wrong front door
published: 2026-11-21
spec: spec-v0.4
requirements: [MAN-1, MAN-47, PROTO-13, PROTO-27, SEC-6]
canonical:
---

# The wrong front door

_Draft. Pinned to `spec-v0.4`; requirement IDs refer to that release._

Ask an assistant whether a plumber covers the north side of your city. Watch what
it does.

It fetches a page. The page is mostly navigation, cookie banners, product copy,
scripts and styling. The answer is not on it, or not only on it, so the agent
fetches three more. It parses markup, guesses which link matters, and pays for all
of it in tokens — for a fact the business would happily have told it in one
sentence.

Then the site pushes back. Bot walls, captchas, fingerprinting. Those exist to stop
automation, and the agent is automation, so it ends up doing what a scraper has
always done: wearing a browser costume to read a page that is public.

And the business has no say in any of it. It does not know which agent asked, it
cannot answer differently for a machine, and it cannot tell the agent that the
thing it is looking for lives at `/services/coverage` rather than `/about`.

## The web's front door was built for readers

That is not a complaint about the web. HTML, HTTP, cookies and a page rendered for
a human are an excellent design for a human. The problem is that the web is the
_only_ door, so everything that is not a human has to squeeze through it.

When a machine squeezes through a door built for eyes, three costs follow:

**Tokens.** A page is mostly not the answer. You pay for navigation, styling and
scripts on every fetch, and one question often needs several pages.

**Fragility.** When the layout changes, the integration breaks quietly. Nobody
notices until an answer is wrong.

**No representation for the business.** The business published the page, but it
did not publish a contract. It cannot say "here is what I expose, here is what
each thing does, here is how to talk to it", so every agent guesses differently.

## What is missing is not another API

The obvious answer is "publish an API". That works, and it is what everyone does
— one custom integration per service, per assistant. A REST endpoint, a GraphQL
schema, an OpenAPI document, an MCP server: each can do discovery and multi-turn
conversation perfectly well, if somebody builds it for that service, for that
caller.

What does not exist is a common contract. Nothing about one integration carries
over to the next business or the next assistant, so the work is repeated forever,
by everyone, in private.

## A second door

The proposal behind this specification is a second door next to the website, built
for a different kind of caller:

- **the domain names it.** The business already owns and maintains that name. No
  directory, marketplace or vendor catalogue decides whether it exists.
- **a manifest describes it.** A small document saying which agents exist, what
  each one claims to do, and where to read more.
- **a session holds the conversation.** Multi-turn, with explicit progress and an
  explicit end.

Discovery is a DNS SRV record — `_portico._tcp.example.com` — because an agent
endpoint is usually not the website's host, port or protocol, and SRV expresses
that as a routing fact rather than as a pointer discovered after fetching a
document.

TLS then answers _who_. There is a detail worth being precise about here: the
client sends the **domain you asked for** as `ServerName`, not the host the SRV
record pointed at, and the certificate must cover the name you queried
(`PROTO-47`, `SEC-9`). SRV is routing; it must not be allowed to move which
certificate is acceptable. Verification is on by default (`SEC-6`), because a
connection that is encrypted but unauthenticated tells you nothing about who is
answering.

Inside that connection, the first thing a caller receives is the manifest
(`PROTO-13`) — the document that turns a routing fact into something a program can
act on:

```json
{
  "manifest_version": "1.3",
  "protocol": "portico/1",
  "endpoint": { "name": "acme-plumbing" },
  "links": [{ "rel": "site", "href": "https://acme-plumbing.example" }],
  "agents": [
    {
      "name": "support",
      "description": "Questions about service, coverage and pricing",
      "tags": ["coverage", "pricing"],
      "sessions": true
    }
  ]
}
```

That is the whole front door. It carries no model, no API key, no vendor, and no
layout to parse. A client validates it before acting on it (`MAN-47`), and a
business can publish it without writing a daemon — a manifest is a document, and
publishing one is the lowest rung of the conformance ladder.

## What a session gives you that HTTP does not

Asking a question and getting a document back is the easy half. The hard half is
knowing what is happening while it happens:

- **progress** — "still working" lines while the backend thinks, which never count
  as a turn;
- **completion** — one explicit end to a turn, so a caller never has to guess
  whether an answer is final;
- **cancellation** — the caller abandons the turn, and the daemon stops waiting
  and answers `{"ok": false, "cancelled": true}` without counting it (`PROTO-27`).

Cancellation is cooperative and best effort, and the specification says so
plainly: the daemon can abort the request the backend is still working on, but it
cannot undo what that backend already committed. A protocol that claimed rollback
would be lying, and a caller would plan around the lie.

## What this is not

It does not run a model. It does not hold an API key. It does not answer on the
business's behalf — the daemon routes, the business's backend replies. It does not
keep a registry: discovery is DNS and the manifest is served per endpoint. It does
not require MCP; the MCP bridge is one adapter for hosts that already speak MCP,
and a client that speaks the protocol natively never needs it.

## What is missing

Agreement, and evidence.

Today there is one implementation: a daemon, a terminal client, an MCP adapter, and
one live deployment. That is enough to prove the design works for its author. It
is not evidence that the contract is complete or understandable, and the
specification says so in its own words.

What would change that is boring and specific:

1. **Run an endpoint on a domain you control.** A daemon and a backend, which is
   more than one file and that is the point: participating means answering. The
   probe tells you requirement by requirement what you got right.
2. **Write a client in another language.** Not a port of the reference client — an
   implementation from the document. Every place you had to guess is a defect in
   the specification, and worth an issue that cites the requirement ID.
3. **Argue with the text.** A well-argued objection is more useful at this stage
   than an implementation that agrees.

Two implementations that interoperate are the only real measure of whether any of
this works. Everything else is a claim.

- Specification: [`agent-front-door-spec`](https://github.com/ground-creative/agent-front-door-spec) at `spec-v0.4`
- Reference implementation: [`vireo`](https://github.com/ground-creative/vireo)
- Live endpoint: `connect ziwa.ai`
