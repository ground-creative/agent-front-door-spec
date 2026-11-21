# Decisions

A short log of decisions that shaped this specification, with the reasoning that
produced them. If you want to change one, open a proposal and reference the entry
number.

Newest first.

---

## D-7 — Clients verify certificates by default

**Decision.** `SEC-6` requires verification on by default. A development mode that
disables it must be explicit, named unsafe, and warned about at runtime.

**Why.** The reference clients shipped with verification off for convenience. That
made `localhost` work and made every real deployment impersonable: encryption held,
identity did not. A specification that ships that default cannot be reviewed
seriously, and the fix is cheapest before anyone depends on the old behaviour.

**Cost.** Local development needs an explicit flag or a locally trusted certificate.
Accepted.

## D-6 — The manifest is transport-independent

**Decision.** `MANIFEST.md` defines the object. `PROTOCOL.md` defines how it arrives
inside a session. A deployment may publish the same object as a document for L0
use.

**Why.** Adoption is staged. A business that publishes a valid manifest has joined
the ecosystem without writing TLS code. It also keeps the "retrieve a document" and
"hold a conversation" concerns separate, which is the difference between this and a
page-scraping integration.

**Cost.** Two delivery paths to keep consistent. Accepted: they share one schema.

## D-5 — `links` replaces `refs`; `commands` is replaced by `capabilities`

**Decision.** `refs` (a map of string to string) is deprecated in favour of `links`
(an array of objects). `commands` (a list of strings) is deprecated in favour of
`capabilities.session`. Both remain legal and must be emitted alongside their
replacement for one minor release.

**Why.** `refs` cannot say what a link _is_: an agent cannot tell a menu PDF from an
OpenAPI document from a status page, and there is no label. `commands` was a list of
operations the server might not accept — the exact failure mode `MAN-28` exists to
forbid. An array of objects is also the only shape that can grow additively.

**Cost.** Two ways to say the same thing for one release. Accepted.

## D-4 — Additive versioning, not a protocol bump

**Decision.** New optional fields arrive under `manifest_version` minor bumps. The
wire identifier stays `vireo/1`. Breaking changes require a MAJOR and a superseding
document.

**Why.** There is a live deployment. A flag day would break it and would prove the
opposite of the interoperability claim. Clients that ignore unknown members — which
`MAN-3` requires — keep working while capabilities grow.

## D-3 — Discovery is DNS SRV, not a well-known URI

**Decision.** A bare domain resolves through `_vireo._tcp.<domain>`.

**Why.** A well-known path answers "where is the document". SRV answers "where is
the service", before any HTTP request exists, and can name another host, port or
transport. That matters when the agent endpoint is not the website, which is the
normal case. SIP, XMPP, LDAP and Matrix use SRV for the same reason.

**Cost.** SRV is unfamiliar to some operators and cannot carry the manifest itself.
Accepted: the manifest arrives inside the connection.

## D-2 — The manifest arrives inside the connection

**Decision.** The manifest is the answer to `negotiate`, not a separate fetch.

**Why.** One connection, one authenticated peer, one document: there is no window in
which a caller has a manifest from one host and a session with another. It also
makes the manifest's freshness implicit — it is read at the moment of use.

**Cost.** No manifest without a handshake, which is why D-6 allows a document path
for L0.

## D-1 — Sessions are envelopes, never content

**Decision.** A stored session holds id, agent, timestamps, summary, turn count and
status. No message text.

**Why.** The daemon is not the business. Storing conversation content would make it
a party to the conversation, with everything that implies for retention, privacy
and liability. Summaries are enough for a caller to recognise a conversation.

**Cost.** A daemon cannot replay a conversation. Accepted, and documented as a
non-goal rather than a limitation.
