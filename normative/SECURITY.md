# Security considerations

**Normative where it says MUST.** Requirement identifiers (`SEC-n`) are stable.

- Spec release: `spec-v0.4`

---

## 1. Three questions, three layers

Most security mistakes in a design like this come from asking one layer to answer
a question that belongs to another.

| Layer    | Answers                                         | Does not answer                                |
| -------- | ----------------------------------------------- | ---------------------------------------------- |
| DNS      | _where_ — the host and port serving this domain | who is there, or what they offer               |
| TLS      | _how_ — a private, integrity-protected channel  | that you reached the business, unless verified |
| Manifest | _what_ — the agents and their claims            | that the claims are true                       |

- **SEC-1.** A protocol implementation MUST NOT treat a DNS answer as evidence of
  endpoint identity. SRV records can be stale, wrong, or manipulated on the
  resolution path.
- **SEC-2.** A protocol implementation MUST NOT treat the manifest as evidence of
  endpoint identity. It is content from whichever peer completed the handshake.
- **SEC-3.** Endpoint identity MUST come from certificate verification against the
  queried domain, and from nothing else.

## 2. Transport

- **SEC-4.** TLS 1.3 or later MUST be used. There MUST be no plaintext mode and no
  downgrade path.
- **SEC-5.** ALPN MUST be `portico/1` for this revision. A server MUST refuse a
  connection that negotiates anything else.
- **SEC-6.** A client MUST verify the server certificate and MUST send the queried
  domain as `ServerName`. Verification MUST be on by default.
- **SEC-7.** A client MAY provide a development mode that disables verification.
  Such a mode MUST be explicit, MUST be named as unsafe in its own help text, MUST
  warn at runtime, and MUST NOT be reachable by configuration default. Silent
  disabling is forbidden.
- **SEC-8.** A deployment that needs an exception MUST implement custom
  verification or certificate pinning. Falling back to accepting arbitrary
  certificates is not an exception, it is the absence of the control.

With verification off, the connection is encrypted but the business's identity is
not established: an active attacker on the path can present its own certificate
and the client cannot tell. Encryption and integrity hold for **whichever peer
completed the handshake**; they do not say who that peer was.

Certificate identity rules for this revision: the certificate MUST be valid for
the domain that was queried, and SHOULD be valid for the SRV target host as well.
A deployment whose SRV target differs from the queried domain MUST obtain a
certificate covering the queried domain, because that is the name the client
sends.

- **SEC-9.** A client that follows an SRV target MUST NOT silently accept a
  certificate valid only for a different name than the one it queried.
- **SEC-10.** A server SHOULD refuse connections whose SNI does not match a name it
  is configured to serve.

## 3. Client identity

`client.id` is an identifier, not a credential.

- **SEC-11.** A server MUST treat `client.id` as a scoping key for sessions, and
  MUST NOT treat possession of an id as proof of anything else.
- **SEC-12.** A server MUST NOT use `client.name` or `client.version` for
  authorization (PROTO-10).
- **SEC-13.** A client id MUST NOT be derived from a user identifier, an email
  address, a hardware id, or anything that identifies a person.
- **SEC-14.** Implementations that need authenticated callers MUST do so above this
  protocol — a bearer token in a host-side adapter, mutual TLS, or an application
  authorization step — and MUST document where that boundary sits. This
  specification does not define authentication, and claiming otherwise is a
  security defect in a description, not a gap in the protocol.

## 4. What a manifest may and may not contain

- **SEC-15.** A manifest MUST NOT contain credentials, tokens, internal hostnames,
  customer data, or anything that would be harmful if mirrored by a third party
  (MAN-8).
- **SEC-16.** A manifest MUST NOT be the mechanism by which a caller obtains
  access. It may describe that access is required; it must not grant it.
- **SEC-17.** Descriptive text in a manifest is untrusted input. A client MUST
  escape it before rendering and MUST NOT execute or interpret it.
- **SEC-18.** A link in a manifest is a URI, not an instruction. A client MUST NOT
  dereference a link automatically as part of discovery.

## 5. Content the caller sends and receives

- **SEC-19.** A server MUST bound the size of any frame before buffering it
  (PROTO-4), and MUST bound the backend response body (WH-6).
- **SEC-20.** A server MUST NOT log message content by default. Session envelopes
  are metadata; message text is not the daemon's business.
- **SEC-21.** A server SHOULD enforce the limits it advertises and MUST return
  `rate_limited` rather than degrading silently.
- **SEC-22.** A client MUST treat replies, partials and descriptions as untrusted
  text and MUST NOT feed them into a shell, a template with execution, or an
  instruction-following path without its own review.

## 6. Denial of service

- **SEC-23.** A server MUST cap concurrent turns per connection and per client id.
- **SEC-24.** A server MUST impose a per-turn deadline (WH-7) and MUST release the
  resources of an abandoned turn after `cancel` (PROTO-27).
- **SEC-25.** A server MUST NOT hold a lock across a backend call; a slow backend
  must not block reads from other callers on the same connection.
- **SEC-26.** A deployment SHOULD rate limit per `(client id, agent)` rather than
  per connection, because a client can reconnect cheaply.

## 7. Freshness and integrity

- **SEC-27.** A client MUST verify `digest` when present and MUST report a mismatch
  (MAN-40).
- **SEC-28.** A `digest` is an integrity check against accidental corruption or a
  truncated document. It is **not** authentication: anyone can compute a digest of
  their own document.
- **SEC-29.** `signature` is reserved and MUST be `null` in `manifest_version` 1.1
  (MAN-41). Signing is an open question, and a client MUST NOT accept an unsigned
  manifest as signed merely because the field is absent.
- **SEC-30.** A manifest cached until `expires_at` MUST be re-read afterwards; a
  stale manifest is not evidence about the present.

## 8. Known open questions

Deliberately unresolved, and listed so implementations can be honest about them:

1. **Signing.** Who signs a manifest, with what key, and how is the key bound to the
   domain? A DNSSEC-anchored key or a certificate-bound key are both plausible, and
   neither is specified here.
2. **Durable client identity.** `client.id` is a random string a host stores. What
   happens when it is lost, or when a caller wants the same identity on two hosts?
3. **Delegation.** A domain may delegate its agent endpoint to a third party. What
   must that third party prove, and what does the business's certificate say?
4. **Authorization semantics.** What does a capability grant look like, and how is
   it revoked? Today a manifest can say "sessions exist"; it says nothing about who
   may open one.
5. **Repudiation.** A cancelled turn may still have committed work. The protocol is
   explicit that cancellation is not rollback (PROTO-30); it does not say who bears
   the cost.

## 9. Requirement index

| ID     | Section | Subject                                 |
| ------ | ------- | --------------------------------------- |
| SEC-1  | 1       | DNS is routing, not identity            |
| SEC-2  | 1       | manifest is not identity                |
| SEC-3  | 1       | certificate verification is identity    |
| SEC-4  | 2       | TLS 1.3, no plaintext                   |
| SEC-5  | 2       | ALPN enforced                           |
| SEC-6  | 2       | verify by default, send ServerName      |
| SEC-7  | 2       | development mode rules                  |
| SEC-8  | 2       | exceptions are custom verification      |
| SEC-9  | 2       | SRV target name coverage                |
| SEC-10 | 2       | SNI matching                            |
| SEC-11 | 3       | client id is not a credential           |
| SEC-12 | 3       | no authorization from name/version      |
| SEC-13 | 3       | no personal identifiers                 |
| SEC-14 | 3       | authentication lives above the protocol |
| SEC-15 | 4       | no secrets in a manifest                |
| SEC-16 | 4       | manifest does not grant access          |
| SEC-17 | 4       | descriptions are untrusted text         |
| SEC-18 | 4       | links are not auto-dereferenced         |
| SEC-19 | 5       | size bounds                             |
| SEC-20 | 5       | no message content in logs              |
| SEC-21 | 5       | enforce advertised limits               |
| SEC-22 | 5       | replies are untrusted text              |
| SEC-23 | 6       | cap concurrent turns                    |
| SEC-24 | 6       | per-turn deadline, release after cancel |
| SEC-25 | 6       | no lock across a backend call           |
| SEC-26 | 6       | rate limit per client and agent         |
| SEC-27 | 7       | verify digest                           |
| SEC-28 | 7       | digest is not authentication            |
| SEC-29 | 7       | signature reserved                      |
| SEC-30 | 7       | cached manifests expire                 |
