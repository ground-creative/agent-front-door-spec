---
title: The fragmentation tax
published: 2026-11-21
spec: spec-v0.3
requirements: [MAN-2, MAN-3, MAN-4, MAN-44, MAN-45, MAN-46, PROTO-6, PROTO-39]
canonical:
---

# The fragmentation tax

_Draft. Pinned to `spec-v0.3`; requirement IDs refer to that release._

## Premises

- A caller pays for every integration it does not share with another caller.
- A business will not adopt a contract that costs more than the integrations it
  replaces.
- Part of the cost is irreducible: two systems can agree on a shape without
  agreeing on what a word means.

---

## Count it

Suppose `N` callers and `M` businesses. Every pair that wants to talk needs an
agreement: how to find each other, what a request looks like, what an error looks
like, how a conversation continues, when it is over.

Without a shared contract that is up to `N × M` agreements. With one, it is `N`
implementations of the contract plus `M` publications of it — and each new
participant is one more, not one more multiplied.

The reason this feels like a tax rather than a design choice is that the caller —
the one with the least leverage over any single service — is the party that pays
it. Every business can reasonably say "our API is our API". Nobody can reasonably
say "my integrator is everyone's integrator".

## Why per-integration work does not compound

Two businesses can both answer "do you cover my area?" and share nothing. The
question is the same; the shape is not. One returns a boolean, one returns a
polygon, one returns a PDF, one returns an HTML page with the answer in the third
paragraph.

A caller that has absorbed four integrations has four clients, four retry
policies, four error vocabularies, and no reusable knowledge about the fifth
business. That is the tax: work that produces capability but no leverage.

## What a shared contract actually buys

Not agreement about meaning. A contract buys:

- **one discovery path** — a name resolves to an endpoint, with no per-vendor
  registry;
- **one framing** — a message and its answer have a shape, whatever the payload
  says;
- **one error vocabulary** — `session_required` means the same thing at every
  endpoint (`PROTO-39`);
- **one session model** — the same rules for continuing, closing and abandoning a
  conversation.

That is a smaller promise than "interoperability", and it is the one that
compounds. Everything above it — auth, pricing, idempotency, what an answer
actually guarantees — stays with the business, and pretending otherwise would
have made the contract unadoptable.

## The transitional price, paid in public

Standards are expensive before they are cheap. This one makes that visible rather
than hiding it.

`manifest_version` 1.0 carried `refs` (a map of key to URL) and `commands` (a list
of operation names). 1.1 replaced them with `links` (label, media type, and room to
grow) and `capabilities` (per-operation availability). Neither replacement can be
made in one step without breaking the callers already in the field — so both
shapes are emitted together (`MAN-44`, `MAN-45`), and the deprecated members are
frozen so nobody invents a third meaning for them (`MAN-46`).

That duplication is the tax, paid once, in public. A specification that quietly
renames a field and calls it a minor version has not avoided the tax; it has
moved it to every implementation, at a worse exchange rate.

## How the contract bounds the next bill

Every rule below exists to stop a future change from charging callers twice:

- a change that only adds optional fields is a MINOR bump (`MAN-2`);
- a client must ignore members it does not recognise (`MAN-3`);
- an unknown value in a closed set degrades to its documented fallback (`MAN-4`);
- a reader must ignore unknown frame types rather than treat them as a protocol
  violation (`PROTO-6`).

Together they mean a caller written against an older revision keeps working when
an endpoint is newer, which is the only version negotiation that scales.

## The honest limit

What is standardised here is discovery, framing, sessions and completion
semantics. What is not: authentication, versioning of a business's own data,
idempotency of a side effect, and the meaning of the words inside a reply.

So the tax does not go to zero. It moves: from _finding_ the business and
_guessing_ the shape of the exchange, to _understanding_ what this particular
business means. That is a real improvement, because understanding is work that a
caller can do once per question, while finding-and-guessing is work it repeats for
every business it ever meets.

Anyone claiming a protocol removes the rest is selling something. The measure of
this one is smaller and checkable: a caller implements the contract once, and each
new business is a manifest and a session instead of a project.

## Why the specification is deliberately small

Every field added to a shared contract is a promise kept by every implementation
forever. That is why this document refuses to standardise things it cannot hold
implementations to — why `actions` arrived in one draft and was removed in the
next before anyone depended on it, and why a client is required to ignore what it
does not know rather than to understand everything.

A contract earns adoption by being small enough to keep.
