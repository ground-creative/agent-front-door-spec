# Proposal: a front door for agents

**Informative.** This document argues for a direction. It is not a wire
specification; the normative text is in [`../normative/`](../normative/).

Status: draft, seeking implementers and objections.

---

## The argument

The web has a front door. You type a name, you get a page, you read it. It was
built for a reader with eyes and a browser: HTTP carries the document, HTML
carries the layout, cookies carry the session, and the whole thing assumes a
human is looking at it.

That door works. It is also the wrong door for an agent, and the cost is paid
every time an agent wants to know something simple.

### What an agent does today

Ask an assistant whether a business covers the north side. It fetches a page.
The page is mostly navigation, product copy, scripts and styling. One answer needs
several pages. The agent pays for all of it in tokens, and what it gets back is
markup that must be parsed and guessed at.

Then the site pushes back. Bot walls, captchas and fingerprinting exist to stop
exactly this, so the agent ends up impersonating a human browser to read a page
the business published publicly. When the layout changes, the integration breaks
quietly and nobody notices until an answer is wrong.

And the business has no say: no idea which agent is asking, no control over what
it sees, no way to answer differently for a machine that just wants one fact.

### What is missing is not another API

It would be easy to say "publish an API". But an API is a contract between a
developer and a service, negotiated per integration. A custom endpoint, a GraphQL
schema, an OpenAPI document, an MCP server — each can do discovery and multi-turn
conversation perfectly well, if somebody builds it for that service, for that
assistant. Nothing carries over to the next business or the next assistant.

The missing piece is not capability. It is **a common contract**: one way to name
an endpoint, one way to describe what it exposes, one way to hold a conversation
with it, one way to say "finished", "still working" or "gave up".

### The second door

A second door, next to the website, built for a different kind of caller:

- **the domain names it** — the business already owns and maintains that name; no
  directory, marketplace or vendor catalogue decides whether it exists;
- **a manifest describes it** — a small document saying which agents exist, what
  each claims to do, and where to read more;
- **a session holds the conversation** — multi-turn, with explicit progress and an
  explicit end, so an agent never has to guess whether an answer is complete.

The business keeps everything that makes it a business: its backend, its models,
its logic, its data. The protocol standardizes the contract between the two
sides, not the software behind it.

Nothing about this requires a particular AI provider, model, language or agent
framework. It requires agreement on a small number of rules.

### Why not just publish JSON somewhere?

Because a document is half of it. Retrieving a description is a document problem,
and HTTP is fine for that — this specification allows a business to start there
(L0) with a static file.

Conversation is not a document problem. Asking a question, being told "still
working", cancelling, and knowing that a turn has definitively ended are things a
document cannot express and a page cannot carry. That is what the session channel
is for, and it is why the protocol exists alongside the manifest.

So the honest split is:

- **metadata** may travel as a document, over whatever transport is convenient;
- **conversation** travels over this protocol, because it has state.

## Principles

1. **The business stays in control.** It decides which agents exist, what they say,
   and which backend answers. No model is implied anywhere.
2. **Discovery is delegated, not centralized.** DNS already expresses "where is the
   service for this name", with each zone authoritative for its own records. No
   registry has to approve a new participant.
3. **Layers stay separate.** DNS routes, TLS authenticates the peer, the manifest
   describes what is offered. Asking one to do another's job is how a protocol
   becomes insecure.
4. **Explicit over inferred.** A completed turn, a failed turn and an abandoned turn
   are distinct and say so. Anything a client has to guess is a defect in the
   specification, not a detail to be discovered by reading somebody's source.
5. **Additive by default.** New optional fields, unknown frames ignored, unknown
   values degrading to documented fallbacks. A protocol that needs a flag day will
   not be adopted.
6. **The spec is not the product.** One implementation is evidence that a design
   works for its author. Two that interoperate are evidence that it is a
   specification.

## What is deliberately not here

- No model, prompt, embedding or provider. The protocol does not know what answers.
- No payment, pricing or fulfillment semantics.
- No authentication scheme. Identity of a _client_ is a random id used for scoping;
  anything stronger belongs above this layer and is the deployment's choice.
- No registry, directory or marketplace. Discovery is DNS; a manifest is served per
  endpoint.
- No requirement that the endpoint is a website's host, port or protocol.

## What exists today

One implementation, in three parts: a daemon that serves a manifest and routes
turns, a terminal client that speaks the protocol directly, and an MCP adapter so
an MCP-speaking host can reach a daemon. Plus one live deployment.

That is one implementation. The interesting column is the empty one.

## Open questions

These are unsettled, and listed so they can be argued with:

- **Manifest signing.** Who signs, with what key, bound to the domain how?
- **Delegation.** A domain may serve its agents from another host. What must that
  host prove?
- **Durable client identity.** A random id is cheap and anonymous. What should a
  caller do when it needs to prove it is the same caller as yesterday?
- **Authorization.** A manifest can say sessions exist. It does not say who may open
  one. Where does that live?
- **Transport discovery.** One `_tcp` record today, serving TLS and QUIC on the same
  port. Should discovery publish each transport separately?
- **Manifest scope.** Is a manifest one document for an endpoint, or a set of
  documents negotiated per agent as a business grows?
- **Execution semantics.** What must a backend commit before a turn is
  acknowledged? Can an abandoned turn ever be resumed?

## How to take part

The most useful contributions right now are not more software:

- **Implement a client in another language** and report where the specification is
  ambiguous. That is a bug report against the spec, not against your code.
- **Publish a manifest for a real business** at L0. It costs a file and it tells us
  whether the object is expressive enough.
- **Argue with this document.** A well-argued objection is more useful at this stage
  than an implementation that agrees with us.

Read [`../CONTRIBUTING.md`](../CONTRIBUTING.md) and
[`../GOVERNANCE.md`](../GOVERNANCE.md).
