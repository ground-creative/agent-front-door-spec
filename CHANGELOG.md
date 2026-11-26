# Changelog

Spec releases are tagged `spec-vX.Y` and never move. This file records what
changed and which requirement IDs are affected.

## spec-v0.4 — draft

**The wire identifier is `portico/1`.** `frontdoor/1` becomes `portico/1`;
`_frontdoor._tcp` becomes `_portico._tcp`; the webhook headers become
`X-Portico-Protocol`, `X-Portico-Agent` and `X-Portico-Session`.

Two problems with the previous name. `frontdoor` is the title of the proposal,
not an identifier — a wire token should not read as a slogan. And it still said
`vireo` in the webhook headers, which `spec-v0.4` renamed for the ALPN string and
the SRV record but not for the backend contract, so the protocol carried two
naming schemes at once and the implementation's name stayed inside the standard's
own contract.

- ALPN and the `protocol` member are `portico/1` (`PROTO-1`).
- Discovery is `_portico._tcp`. `_frontdoor._tcp` and `_vireo._tcp` remain legal
  fallbacks for one release (`PROTO-44`, `PROTO-48`).
- Webhook headers are `X-Portico-*` (`WH-3`).
- Clients offer every name the draft has used (`PROTO-1`), and a daemon accepts
  them all for the deprecation window, so a rename is not a flag day.
- `machine/check.py` now fails when a retired identifier appears outside a record
  of history, which is the failure the previous rename demonstrated.

**Withdrew the static-document on-ramp.** The manifest-publisher level (`L0`) and
its requirements `CONF-6` – `CONF-10` are removed. `CONF-8` required a publisher
to document where its manifest could be found, and no document ever defined that
location, so the level could not be checked by the specification's own probe or
found by any client. The identifiers are retired in place and never reused, as
`MAN-24` – `MAN-27` were in `spec-v0.2`. Levels are cumulative from the bottom,
so no claim at L1 or above changes. See `D-11`.

- `CONF-6` – `CONF-10` retired; the surviving obligations are `MAN-52` and
  `MAN-53`, which apply to every publisher regardless of level.
- `normative/CONFORMANCE.md`: four levels now, L1 – L4.
- Fixed a pre-existing error in the level table: L2 and L3 named the previous
  level's requirements, so the table and the requirement index disagreed.

**Documented every manifest member in the schema.** `machine/schema/manifest.schema.json`
described each property only by requirement number, which meant an implementer
had to read a second document to learn what a member was for. Every property now
carries a plain-language description, examples, and the requirement IDs that
govern it. `machine/check.py` fails if a property's description is only a
requirement reference, so this cannot regress.

**Added `MAN-59`.** A host adapter that connects an agent host to an endpoint must
make the manifest available to the model unmodified, rather than substituting a
prose summary. Without it, the artifact this document defines is read by the
adapter and never reaches the party it was written for.

**Fixed the digest to be reproducible across implementations.** `MAN-40` defines
the digest over RFC 8785 canonical JSON. The probe used Python's
`json.dumps(sort_keys=True)`, which escapes non-ASCII as `\uXXXX` and formats
floats differently, so it reported a failure on a correct endpoint whose
manifest carried an accented or non-Latin description. The reference daemon used
a third form again, and hashed a re-serialisation of its own struct rather than
the document it published, which inserted members the business never wrote.
Both now canonicalise per RFC 8785 and hash the bytes the endpoint sent.
`machine/fixtures/digest.json` pins the expected digests for four documents and
is checked from both languages.

**Extended the probe.** `machine/conformance.py` gained `--payload` (check a
captured document), `--converse` (send one real turn, off by default because it
spends the business's backend), oversize-length and truncated-frame checks
(`PROTO-4`, `PROTO-5`), documented-error-code checking (`PROTO-41`), and
cross-client session scoping (`PROTO-33`). It no longer reports a conformance
level that includes requirements it did not exercise, and it no longer records a
pass for `MAN-51` without checking it.

**Renamed the wire protocol and the discovery record.** `vireo/1` becomes
`frontdoor/1`; `_vireo._tcp` becomes `_frontdoor._tcp`.

The specification invites independent implementations, and then named the protocol
on the wire after the first one. Every ALPN negotiation and every SRV lookup would
have carried a product name, which tells a reader that implementing the specification
means being Vireo. A standard named after its implementation is a product with a
document attached.

- ALPN is now `frontdoor/1` (`PROTO-1`).
- Discovery is now `_frontdoor._tcp`; the previous record is retired but a client
  MAY fall back to it (`PROTO-44`, `PROTO-48`).
- The HTTP trace header `X-Vireo-Protocol` becomes `X-Frontdoor-Protocol`.

`manifest_version` stays **1.3**. The `protocol` field is a wire identifier and an
open string, not a document shape; a manifest that changes only its value is the same
manifest. A client that validated the old string byte for byte was reading a value set
that this document never closed (MAN-4).

Earlier drafts are untouched: `CHANGELOG` and `DECISIONS` record what was true then.

## spec-v0.3 — draft

**Added `tags`.** `manifest_version` goes to **1.3**.

`tags` is an array of lowercase labels on each agent, for a caller that wants to
filter agents without parsing prose:

```json
{
  "name": "sales-representative",
  "tags": ["sales", "consultation", "services"]
}
```

It is the answer to the question `actions` was trying to answer. One array of
strings, no implied callable operation, no unspecified input hints, no ambiguity
about whether it is a whitelist — because a tag never claims to be one (MAN-56).

Additive: `MAN-55` – `MAN-58`; a 1.2 client ignores the member (MAN-3).

## spec-v0.2 — draft

**Removed `actions`.** `manifest_version` goes to **1.2**.

`actions` was an array of named things an agent claimed it could do. It is gone
because nothing consumed it:

- no client routed on it — both reference clients only printed it;
- there is no `invoke` frame, so an action name could not select anything;
- `MAN-26` said it was not a whitelist and `MAN-25` said its fields were hints,
  which makes it non-binding by its own definition;
- two independent readers read it as quick replies and as an exclusive list of
  capabilities, neither of which it meant. A field whose name reliably misleads
  is a defect (PROPOSAL.md, "explicit over inferred").

`MAN-24` – `MAN-27` are retired, not reused (MANIFEST.md §18). A client built
against 1.1 that reads `actions` simply finds it absent, which `MAN-49` already
requires it to tolerate. A publisher MUST NOT emit it; a client MUST ignore one it
receives.

Considered and rejected: replacing `actions` with `tags: []string`. Tags would
cover the only real use (deterministic filtering) in one line, but adding a field
with no consumer repeats the same mistake in a better costume. The option is
recorded in `DECISIONS.md` D-8 so a future proposal can pick it up when a host
actually needs it.

Also in this release: `machine/check.py` validates inline JSON in fenced blocks,
so a formatter cannot leave a broken example behind; `manifests.json` fixtures are
split by obligation (client-rejectable, publisher-only, client-acceptable).

## spec-v0.1 — draft

First published draft. Establishes:

**Normative**

- `normative/MANIFEST.md` — the manifest object at `manifest_version` **1.1**.
  Adds `manifest_version`, `links`, `actions`, `capabilities`, `limits`,
  `agents[].id`, `generated_at`, `expires_at`, `digest`, `signature` (reserved).
  Deprecates `refs` (MAN-44) and `commands` (MAN-45). 54 requirements.
- `normative/PROTOCOL.md` — the `vireo/1` wire protocol, with requirement IDs
  assigned to every rule. 47 protocol requirements, 13 webhook requirements.
- `normative/CONFORMANCE.md` — levels L0–L4, 25 requirements.
- `normative/SECURITY.md` — threat model, TLS rules, client identity, manifest
  restrictions, 30 requirements.

**Machine**

- `machine/schema/manifest.schema.json` — JSON Schema for `manifest_version` 1.1.
- `machine/examples/` — minimal, full, and a deployed manifest.
- `machine/fixtures/` — frame encodings, a handshake, valid and invalid
  manifests, webhook pairs.

**Informative**

- `informative/PROPOSAL.md` — the front-door argument.
- `informative/RATIONALE.md`, `informative/COMPARISON.md`, `informative/FAQ.md`.

### Compatibility notes

- `manifest_version` **1.0** (a manifest with no `manifest_version`) remains valid.
  A client MUST treat its absence as `1.0` (MAN-53) and fall back to `refs` and
  `commands`.
- No wire incompatibility with the pre-release `vireo/1` implementations. The
  added frames (`partial`, `cancel`) are ignored by readers that do not know them
  (PROTO-6).

### Known gaps in this draft

- `signature` is reserved, not specified (SEC-29, open question 1 in SECURITY §8).
- `actions[].input`/`output` are free-form hints, not schemas (MAN-25).
- Client authentication is out of scope (SEC-14).
- Transport discovery publishes one `_tcp` record (PROTO-44 note).
