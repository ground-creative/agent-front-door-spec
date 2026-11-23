---
title: Rented access and owned access
published: 2026-11-21
spec: spec-v0.4
requirements: [PROTO-44, PROTO-47, MAN-7, MAN-33, SEC-6]
canonical:
---

# Rented access and owned access

_Draft. Pinned to `spec-v0.4`; requirement IDs refer to that release._

## Premises

- An intermediary's revenue depends on the traffic it directs. A layer that
  removes the traffic competes with the intermediary's income. This is an
  observation about incentives, not about any one company's decisions.
- A business that already registers and renews a domain would rather expose its
  own agents than depend on a directory it does not control.
- Access a caller has to request per provider is different in kind from access a
  caller can discover.

If any of those is wrong, the argument below weakens — it does not disappear.

---

## What renting looks like

Every agent that reaches a business today is either scraping, or has been granted
permission by someone. The permission comes in ordinary shapes: an API key, an
allowlist entry, a partner integration, a connector somebody wrote for that
vendor.

None of that is malicious. It is how a party that owns a gateway stays in
business, and it works — until it doesn't.

## Revocation does not need intent

The fragile part is not that someone might decide to cut you off. It is that the
permission was never yours. It was lent.

Lending ends for reasons that have nothing to do with you: a layer stops
converting, so it is deprioritised; a price changes; a policy is reworded; a
provider decides which callers are "accountable" and which are not. Each of those
is a business decision made by someone whose interests are not your access.

So the honest description of rented access is not "they can take it away". It is:
**the default state of your access is decided elsewhere.** You can influence it.
You cannot hold it.

## What ownership means here, concretely

A business already owns three things, and does them without asking anyone:

- **a name** it renews, which resolves in DNS;
- **a certificate** it installs for that name;
- **a service** it runs on infrastructure it controls.

This specification adds one publication to that list: a manifest describing what
the business exposes.

There is no approval step for any of it. A DNS record needs the zone's operator,
not a registry. A certificate needs a CA, not a platform. A manifest is a document
the business serves. Nothing in the path decides whether the business is
interesting enough to be listed.

That is what "owned" means in this context — not that the business is safe, but
that nobody else is holding the pen.

## The part that is easy to get wrong

The domain is the identity, and the specification is specific about it: the client
resolves `_frontdoor._tcp.<domain>`, connects to whatever host and port the record
names, and verifies the certificate against **the domain that was queried**, not
the host DNS sent it to (`PROTO-47`, `SEC-9`).

That detail is the whole point. If the certificate were checked against the SRV
target instead, a DNS answer would decide which certificate is acceptable — which
is renting your identity from the routing layer. This project shipped that bug
once, and the fix is what makes the name on the door the name you can trust.

## What this does not buy

A door is not an invitation.

Discovery gives a caller an address. It does not give it permission, and the
specification says so in ways that matter:

- an endpoint may expose **no agents at all** (`MAN-7`), and that is a valid
  answer, not an error;
- an endpoint may rate limit, and is expected to say so (`MAN-33`);
- an agent may hold a conversation, and require a session before the first word;
- a business may simply not run a daemon, in which case the domain has no record
  and the caller is told so.

Ownership of discovery is not ownership of the business. What changes is that the
answer — yes, no, not now, not for you — comes from the business itself, on
infrastructure it controls, in a form a program can read.

## What you can check

Three commands, no trust required:

```bash
dig +short SRV _frontdoor._tcp.ziwa.ai
openssl s_client -connect vireo.ziwa.ai:7778 -servername ziwa.ai -alpn frontdoor/1 1 \
  | grep "Verify return code"
```

The record either exists or it does not. The certificate either covers the name
you asked for or it does not. That is a lower bar than "the platform promised",
and a much higher one than "the platform's incentives are aligned with mine".

Rented access is permission that can be withdrawn without notice. Owned access is
a name, a certificate and a document — three things the business already knows how
to keep alive.
