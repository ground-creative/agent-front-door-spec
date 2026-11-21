# Conformance

**Normative.** This document defines what it means to claim a conformance level.
Requirement identifiers (`CONF-n`) are stable.

- Spec release: `spec-v0.1`

---

## 1. Levels

A claim names a level and a spec release, for example:

> `vireo 1.4` — daemon — **L3**, `spec-v0.1`

| Level | Name               | Requirements           |
| ----- | ------------------ | ---------------------- |
| L0    | Manifest publisher | CONF-1 – CONF-5        |
| L1    | Discovery          | L0 + CONF-6 – CONF-10  |
| L2    | Conversations      | L1 + CONF-11 – CONF-15 |
| L3    | Live               | L2 + CONF-16 – CONF-18 |
| L4    | Operational        | L3 + CONF-19 – CONF-21 |

Levels are cumulative. A client and a server claim the same ladder, with the
role-specific rows below.

- **CONF-1.** An implementation MUST state its role: `client`, `server`, or
  `host adapter`.
- **CONF-2.** A claim MUST name the spec release tag it was verified against.
- **CONF-3.** A claim MUST list any requirement it does not satisfy. A partial
  claim is legitimate; a silent failure is not.
- **CONF-4.** A claim MUST be reproducible: the implementation MUST publish how a
  third party runs the check.
- **CONF-5.** A claim that has not been re-verified against a newer spec release
  MUST be marked as such rather than silently carried forward.

## 2. L0 — manifest publisher

- **CONF-6.** Emits a document that validates against
  `machine/schema/manifest.schema.json`.
- **CONF-7.** Satisfies every `MUST` in `MANIFEST.md` that applies to publishing.
- **CONF-8.** Publishes where a caller can find it, and documents that location.
- **CONF-9.** Keeps `capabilities` truthful (MAN-52) even when it implements no
  protocol: an L0 publisher advertises only document-level facts.
- **CONF-10.** Declares `manifest_version` (MAN-1, MAN-53).

L0 is the on-ramp: no daemon, no TLS, no sessions. A business can be here today.

## 3. L1 — discovery

- **CONF-11.** Satisfies `PROTO-1` – `PROTO-14` and `PROTO-44` – `PROTO-47`.
- **CONF-12.** A server: publishes the SRV record and answers `negotiate` with a
  manifest. A client: resolves SRV, completes the handshake, and keeps the
  manifest.
- **CONF-13.** Rejects a malformed manifest rather than half-accepting it
  (MAN-47, MAN-48).
- **CONF-14.** Verifies the peer certificate by default (SEC-6). A development
  mode that disables verification MUST be explicit and MUST warn.
- **CONF-15.** Survives a peer that sends an unknown frame type (PROTO-6).

## 4. L2 — conversations

- **CONF-16.** Satisfies `PROTO-15` – `PROTO-22`, `PROTO-32` – `PROTO-39`, and
  `WH-1` – `WH-8`.
- **CONF-17.** A server: mints sessions, scopes them by client, and routes turns to
  one backend. A client: creates or resumes a session and sends turns.
- **CONF-18.** Keeps session envelopes content-free (PROTO-36).

## 5. L3 — live

- **CONF-19.** Satisfies `PROTO-23` – `PROTO-31` and `WH-9` – `WH-13`.
- **CONF-20.** A server: streams `partial` and accepts `cancel`, with turns running
  concurrently. A client: renders partials and can abandon a turn.
- **CONF-21.** Advertises `capabilities.progress` and `capabilities.cancel`
  only when it implements them (MAN-28, MAN-52).

## 6. L4 — operational

- **CONF-22.** Advertises the limits it enforces (MAN-31 – MAN-34) and enforces
  them.
- **CONF-23.** Emits `rate_limited` with a retry delay (PROTO-43).
- **CONF-24.** Bounds session lifetime and documents retention.
- **CONF-25.** Can restart without silently invalidating the ids it advertised in
  the manifest's terms. If a restart invalidates sessions, that MUST be documented
  and MUST surface as `unknown_session`, never as a crash.

## 7. Running the check

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
PASS  PROTO-1   TLSv1.3, ALPN vireo/1
PASS  PROTO-8   code=bad_client_id
PASS  PROTO-13  manifest on stream 0
PASS  MAN-47    manifest validates against the schema
PASS  MAN-40    digest matches
PASS  MAN-29    session.new for orders
FAIL  MAN-28    session.list advertised true but refused

claim: 127.0.0.1:7777 — L2, 1 failure(s), spec-v0.2
not tested: L3 (progress, cancellation), L4 (retention, restart)
```

It exits non-zero on any failure, so it works as a gate in an implementation's CI.
It deliberately does not probe `session.prune` (destructive), and it reports L3
and L4 as *not tested* rather than passed: progress, cancellation, retention and
restart semantics need a backend and state that a probe should not impose on a
live endpoint.

The fixture tests are the other half: `machine/fixtures/frames.json` etc. are
language-neutral, so an implementation can consume them directly without the
runner.

## 8. Requirement index

| ID      | Section | Subject                                  |
| ------- | ------- | ---------------------------------------- |
| CONF-1  | 1       | state the role                           |
| CONF-2  | 1       | name the spec release                    |
| CONF-3  | 1       | list unmet requirements                  |
| CONF-4  | 1       | reproducible check                       |
| CONF-5  | 1       | stale claims marked                      |
| CONF-6  | 2       | schema-valid document                    |
| CONF-7  | 2       | publishing MUSTs                         |
| CONF-8  | 2       | documented location                      |
| CONF-9  | 2       | truthful capabilities                    |
| CONF-10 | 2       | declared manifest_version                |
| CONF-11 | 3       | L1 protocol requirements                 |
| CONF-12 | 3       | discovery, both roles                    |
| CONF-13 | 3       | reject malformed manifest                |
| CONF-14 | 3       | verify by default                        |
| CONF-15 | 3       | unknown frame tolerated                  |
| CONF-16 | 4       | L2 protocol requirements                 |
| CONF-17 | 4       | sessions and routing, both roles         |
| CONF-18 | 4       | content-free envelopes                   |
| CONF-19 | 5       | L3 protocol requirements                 |
| CONF-20 | 5       | partial and cancel, both roles           |
| CONF-21 | 5       | advertises only implemented capabilities |
| CONF-22 | 6       | advertises enforced limits               |
| CONF-23 | 6       | rate limit error                         |
| CONF-24 | 6       | bounded sessions and retention           |
| CONF-25 | 6       | restart semantics documented             |
