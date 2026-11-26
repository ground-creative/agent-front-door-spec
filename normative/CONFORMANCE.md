# Conformance

**Normative.** This document defines what it means to claim a conformance level.
Requirement identifiers (`CONF-n`) are stable.

- Spec release: `spec-v0.4`

---

## 1. Levels

A claim names a level and a spec release, for example:

> `vireo 1.4` — daemon — **L2**, `spec-v0.4`

| Level | Name               | Requirements                  |
| ----- | ------------------ | ----------------------------- |
| L1    | Discovery          | CONF-1 – CONF-5, CONF-11 – CONF-15 |
| L2    | Conversations      | L1 + CONF-16 – CONF-18        |
| L3    | Live               | L2 + CONF-19 – CONF-21        |
| L4    | Operational        | L3 + CONF-22 – CONF-25        |

Levels are cumulative. A client and a server claim the same ladder, with the
role-specific rows below. `CONF-1` – `CONF-5` apply to every claim at every
level: they say how a claim is stated, not what is implemented.

> **Removed at spec-v0.4: the manifest-publisher level.** An earlier draft
> defined `L0` as "publish a valid manifest document, no daemon required", and
> `CONF-6` – `CONF-10` as its requirements. The level is withdrawn and the
> identifiers are retired in place, never reused.
>
> The reason is `CONF-8`, which required a publisher to "publish where a caller
> can find it, and document that location". No document ever defined that
> location: no path, no media type, no filename. No client in this repository
> could fetch it, and `machine/conformance.py` has never had a mode that could
> check it. A conformance level that nothing can locate and nothing can verify is
> not a claim about an implementation, and keeping it made the specification
> argue against its own thesis — that what a caller receives is defined by the
> session handshake, at the moment of use, rather than by a file of unknown age.
>
> A business that wants to participate runs an endpoint, or is reachable through
> one. That is a real narrowing of the on-ramp compared with the withdrawn level,
> and it is stated here rather than glossed.

- **CONF-1.** An implementation MUST state its role: `client`, `server`, or
  `host adapter`.
- **CONF-2.** A claim MUST name the spec release tag it was verified against.
- **CONF-3.** A claim MUST list any requirement it does not satisfy. A partial
  claim is legitimate; a silent failure is not.
- **CONF-4.** A claim MUST be reproducible: the implementation MUST publish how a
  third party runs the check.
- **CONF-5.** A claim that has not been re-verified against a newer spec release
  MUST be marked as such rather than silently carried forward.

## 2. L1 — discovery

- **CONF-6.** *(retired at spec-v0.4 — was "emits a document that validates
  against the manifest schema", part of the withdrawn manifest-publisher level)*
- **CONF-7.** *(retired at spec-v0.4 — was "satisfies every MUST in MANIFEST.md
  that applies to publishing")*
- **CONF-8.** *(retired at spec-v0.4 — was "publishes where a caller can find it,
  and documents that location"; no location was ever defined)*
- **CONF-9.** *(retired at spec-v0.4 — was "keeps capabilities truthful even when
  it implements no protocol"; the requirement survives as MAN-52, which every
  publisher must satisfy regardless of level)*
- **CONF-10.** *(retired at spec-v0.4 — was "declares manifest_version"; the
  requirement survives as MAN-53)*

- **CONF-11.** Satisfies `PROTO-1` – `PROTO-14` and `PROTO-44` – `PROTO-47`.
- **CONF-12.** A server: publishes the SRV record and answers `negotiate` with a
  manifest. A client: resolves SRV, completes the handshake, and keeps the
  manifest.
- **CONF-13.** Rejects a malformed manifest rather than half-accepting it
  (MAN-47, MAN-48).
- **CONF-14.** Verifies the peer certificate by default (SEC-6). A development
  mode that disables verification MUST be explicit and MUST warn.
- **CONF-15.** Survives a peer that sends an unknown frame type (PROTO-6).

## 3. L2 — conversations

- **CONF-16.** Satisfies `PROTO-15` – `PROTO-22`, `PROTO-32` – `PROTO-39`, and
  `WH-1` – `WH-8`.
- **CONF-17.** A server: mints sessions, scopes them by client, and routes turns to
  one backend. A client: creates or resumes a session and sends turns.
- **CONF-18.** Keeps session envelopes content-free (PROTO-36).

## 4. L3 — live

- **CONF-19.** Satisfies `PROTO-23` – `PROTO-31` and `WH-9` – `WH-13`.
- **CONF-20.** A server: streams `partial` and accepts `cancel`, with turns running
  concurrently. A client: renders partials and can abandon a turn.
- **CONF-21.** Advertises `capabilities.progress` and `capabilities.cancel`
  only when it implements them (MAN-28, MAN-52).

## 5. L4 — operational

- **CONF-22.** Advertises the limits it enforces (MAN-31 – MAN-34) and enforces
  them.
- **CONF-23.** Emits `rate_limited` with a retry delay (PROTO-43).
- **CONF-24.** Bounds session lifetime and documents retention.
- **CONF-25.** Can restart without silently invalidating the ids it advertised in
  the manifest's terms. If a restart invalidates sessions, that MUST be documented
  and MUST surface as `unknown_session`, never as a crash.

## 6. Running the check

The checkable artefacts are `machine/fixtures/`,
`machine/schema/manifest.schema.json`, and `machine/conformance.py`.

`conformance.py` is a **client**: it connects to a running endpoint, performs the
handshake, validates the manifest, and probes the session operations the manifest
advertises. It needs the specification and a reachable daemon, nothing else — an
implementation in any language can be checked without reading another
implementation's source.

```bash
python3 machine/conformance.py --endpoint 127.0.0.1:7777 --insecure
python3 machine/conformance.py --endpoint agent.example.com:7777
```

```text
PASS  PROTO-1   TLSv1.3, ALPN frontdoor/1
PASS  PROTO-8   code=bad_client_id
PASS  PROTO-13  manifest on stream 0
PASS  MAN-47    manifest validates against the schema
PASS  MAN-40    digest matches
PASS  MAN-29    session.new for orders
FAIL  MAN-28    session.list advertised true but refused

claim: 127.0.0.1:7777 — L2, 1 failure(s), spec-v0.4
not tested: L3 (progress, cancellation), L4 (retention, restart)
```

It exits non-zero on any failure, so it works as a gate in an implementation's CI.
It deliberately does not probe `session.prune` (destructive), and it reports L3
and L4 as _not tested_ rather than passed: progress, cancellation, retention and
restart semantics need a backend and state that a probe should not impose on a
live endpoint.

The fixture tests are the other half: `machine/fixtures/frames.json` etc. are
language-neutral, so an implementation can consume them directly without the
runner.

## 7. Requirement index

| ID      | Section | Subject                                  |
| ------- | ------- | ---------------------------------------- |
| CONF-1  | 1       | state the role                           |
| CONF-2  | 1       | name the spec release                    |
| CONF-3  | 1       | list unmet requirements                  |
| CONF-4  | 1       | reproducible check                       |
| CONF-5  | 1       | stale claims marked                      |
| CONF-6  | —       | retired at spec-v0.4 (manifest publisher) |
| CONF-7  | —       | retired at spec-v0.4 (manifest publisher) |
| CONF-8  | —       | retired at spec-v0.4 (manifest publisher) |
| CONF-9  | —       | retired at spec-v0.4; see MAN-52         |
| CONF-10 | —       | retired at spec-v0.4; see MAN-53         |
| CONF-11 | 2       | L1 protocol requirements                 |
| CONF-12 | 2       | discovery, both roles                    |
| CONF-13 | 2       | reject malformed manifest                |
| CONF-14 | 2       | verify by default                        |
| CONF-15 | 2       | unknown frame tolerated                  |
| CONF-16 | 3       | L2 protocol requirements                 |
| CONF-17 | 3       | sessions and routing, both roles         |
| CONF-18 | 3       | content-free envelopes                   |
| CONF-19 | 4       | L3 protocol requirements                 |
| CONF-20 | 4       | partial and cancel, both roles           |
| CONF-21 | 4       | advertises only implemented capabilities |
| CONF-22 | 5       | advertises enforced limits               |
| CONF-23 | 5       | rate limit error                         |
| CONF-24 | 5       | bounded sessions and retention           |
| CONF-25 | 5       | restart semantics documented             |
