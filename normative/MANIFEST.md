# The manifest

**Normative.** Requirement identifiers (`MAN-n`) are stable; cite them in issues
and proposals. `MUST`, `MUST NOT`, `SHOULD`, `MAY` are used as in RFC 2119.

- Spec release: `spec-v0.4`
- Document version described here: `manifest_version` `1.3`
- See also: [`PROTOCOL.md`](PROTOCOL.md) (how the manifest is delivered),
  [`CONFORMANCE.md`](CONFORMANCE.md) (what a valid implementation must do).

---

## 1. Purpose

A manifest answers one question for a caller that has just reached an endpoint:

> What does this endpoint expose, what can each exposed agent do, where should I
> look for more, and what must I obey?

It is a **data document**, not a web page. It carries no layout, no script, no
navigation and no marketing copy beyond a one-line description per agent. A
client must be able to act on it without guessing.

The manifest is **transport-independent**. This document defines the object. How
it arrives — inside a protocol handshake, or from a document a deployment
publishes — is specified elsewhere. What matters here is the object: a caller
that has just reached an endpoint must be able to read it and act on it without
guessing.

- **MAN-59.** An adapter that connects an agent host to an endpoint MUST make the
  manifest available to the model it serves, and MUST NOT substitute a prose
  summary for it.

  This is the requirement that makes the rest of this document real. A host
  adapter sits between a model and a business: it receives the manifest, and in
  many deployments nothing else ever reads it. If the adapter renders the document
  into a description of its own, the model acts on the adapter's reading rather
  than on the business's declaration, and no requirement here can be relied on by
  the party the manifest was written for.

  "Available" means the document itself, byte-for-byte as the endpoint published
  it, including members the adapter does not model. An adapter MAY present a
  summary in addition — a summary is useful, because a model needs orientation
  before it reads a schema — but the summary MUST NOT be the only form. An adapter
  SHOULD verify the digest (MAN-40) over the bytes it received and report a
  mismatch rather than passing an altered document on.

## 2. Scope and non-goals

In scope: endpoint identity, the agent list, what each agent claims to do, links
to published material, protocol capabilities, advertised limits, session
defaults, freshness and integrity metadata.

Out of scope, deliberately: models, prompts, prices, authentication schemes,
payment, authorization policy, backend implementation. A manifest MAY describe
that something is required; it MUST NOT be the mechanism that grants it.

## 3. Terminology

- **Endpoint** — the service a caller connected to. One party MAY run several
  endpoints.
- **Agent** — one thing a caller can talk to at that endpoint. An agent is named,
  described, and either conversational or stateless.
- **Manifest** — the document in this specification.
- **Caller / client** — anything that reads a manifest.
- **Publisher / server** — the party, or the deployment acting for it.

## 4. Versioning and compatibility

- **MAN-1.** A manifest MUST carry `manifest_version` as a string of the form
  `MAJOR.MINOR`.
- **MAN-2.** A change that only adds optional fields, or adds values to an
  extensible list, MUST increment MINOR and MUST NOT increment MAJOR.
- **MAN-3.** A client MUST ignore object members it does not recognise, and MUST
  NOT fail because of them.
- **MAN-4.** A client that encounters an unrecognised value in a field with a
  closed value set MUST treat it as the field's documented fallback (normally
  "absent").
- **MAN-5.** A change that removes a field, renames a field, changes a field's
  type, or changes the meaning of an existing value MUST increment MAJOR, and
  MUST be specified in a superseding document.
- **MAN-6.** A publisher MUST NOT omit a field marked required in this document,
  and MUST NOT rely on a client inferring it.

`manifest_version` is independent of the wire protocol identifier and of the
spec release tag. A single `portico/1` connection may carry a `1.0`, `1.1` or `1.2`
manifest.

While the specification itself is a `0.x` draft, `manifest_version` MAY change in
ways that MAN-5 would forbid after a stable release. Each such change MUST be
recorded in `CHANGELOG.md` with its reason, and MUST NOT be made once an
independent implementation depends on the affected behaviour. From `spec-v1.0`
the rules above apply without exception. `1.2` removed `actions`, which `1.1`
introduced and no implementation consumed (§18). `1.3` adds `tags`, the cheaper
shape for the one job `actions` was reaching for (§7.1).

## 5. Top-level object

```json
{
  "manifest_version": "1.3",
  "protocol": "portico/1",
  "endpoint": {},
  "agents": [],
  "links": [],
  "capabilities": {},
  "limits": {},
  "session": {},
  "generated_at": "2026-11-21T09:14:00Z",
  "expires_at": "2026-11-22T09:14:00Z",
  "digest": "sha256:0f1c...",
  "signature": null
}
```

| Field              | Type              | Req.       | Since | Meaning                                      |
| ------------------ | ----------------- | ---------- | ----- | -------------------------------------------- |
| `manifest_version` | string            | MUST       | 1.1   | Document compatibility level (MAN-1)         |
| `protocol`         | string            | MUST       | 1.0   | Wire protocol identifier, e.g. `portico/1` |
| `endpoint`         | object            | MUST       | 1.0   | The service itself (§6)                      |
| `agents`           | array             | MUST       | 1.0   | The agents exposed; MAY be empty (§7)        |
| `links`            | array             | MAY        | 1.1   | Endpoint-level published references (§8)     |
| `capabilities`     | object            | MAY        | 1.1   | Protocol features the endpoint supports (§9) |
| `limits`           | object            | MAY        | 1.1   | Operational limits, advisory (§10)           |
| `session`          | object            | MAY        | 1.0   | Endpoint session defaults (§11)              |
| `generated_at`     | string (RFC 3339) | MAY        | 1.1   | When this document was produced (§12)        |
| `expires_at`       | string (RFC 3339) | MAY        | 1.1   | When a cached copy should be re-read (§12)   |
| `digest`           | string            | MAY        | 1.1   | `sha256:<hex>` over the canonical body (§12) |
| `signature`        | object \| null    | MAY        | 1.1   | Reserved; signing is not specified (§12)     |
| `refs`             | object            | deprecated | 1.0   | Superseded by `links` (§13)                  |
| `commands`         | array             | deprecated | 1.0   | Superseded by `capabilities.session` (§13)   |

- **MAN-7.** A manifest for an endpoint with no exposed agent MUST still be valid:
  `agents` MUST be present and MAY be empty. A client MUST treat that as "this
  endpoint answers, but offers nothing right now", not as an error.
- **MAN-8.** A publisher MUST NOT include sensitive material — credentials,
  internal hostnames, customer data — anywhere in a manifest. It is public.

## 6. `endpoint`

```json
{
  "id": "restaurant-prod",
  "name": "restaurant",
  "description": "Fresh pizza and table bookings"
}
```

| Field         | Type   | Req. | Meaning                                               |
| ------------- | ------ | ---- | ----------------------------------------------------- |
| `id`          | string | MAY  | Stable identifier of this endpoint; opaque to clients |
| `name`        | string | MUST | Display name of the endpoint                          |
| `description` | string | MAY  | One sentence, plain text                              |

- **MAN-9.** `endpoint.id`, when present, MUST be stable across restarts and MUST
  be treated as opaque. It is not a hostname and carries no structure.
- **MAN-10.** `endpoint.name` is display text. A client MUST NOT use it to address
  the endpoint; addressing is discovery's job.
- **MAN-11.** Descriptions are plain text. Markup MUST NOT be assumed renderable
  and MUST be escaped if it appears.

The endpoint is not an agent. Talking to an endpoint means talking to one of its
agents.

## 7. `agents`

An array of agent objects. Order is not significant.

```json
{
  "id": "orders",
  "name": "orders",
  "description": "Take food orders: pizzas, sides, drinks, pickup or delivery",
  "tags": ["orders", "delivery"],
  "sessions": true,
  "start_message": "Hello! Ask me anything about the restaurant.",
  "links": [],
  "limits": {},
  "session": {}
}
```

| Field           | Type    | Req.       | Since | Meaning                                           |
| --------------- | ------- | ---------- | ----- | ------------------------------------------------- |
| `name`          | string  | MUST       | 1.0   | The name a caller addresses this agent by         |
| `id`            | string  | MAY        | 1.1   | Stable identity, default `name`                   |
| `description`   | string  | SHOULD     | 1.0   | What this agent handles, one sentence             |
| `tags`          | array   | MAY        | 1.3   | Free-form labels for selection (§7.1)             |
| `sessions`      | boolean | MUST       | 1.0   | Whether a conversation is required (§11)          |
| `start_message` | string  | MAY        | 1.0   | Greeting the agent says when a conversation opens |
| `links`         | array   | MAY        | 1.1   | References specific to this agent (§8)            |
| `limits`        | object  | MAY        | 1.1   | Per-agent overrides of §10                        |
| `session`       | object  | MAY        | 1.1   | Per-agent overrides of §11                        |
| `refs`          | object  | deprecated | 1.0   | Superseded by `links` (§13)                       |

- **MAN-12.** Agent `name` values MUST be unique within a manifest, MUST be
  non-empty, and MUST match `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`.
- **MAN-13.** `name` is the address. A publisher MUST NOT change it for a
  long-lived agent without publishing the old name alongside the new one for at
  least one release; otherwise callers lose the ability to reach it.
- **MAN-14.** `id`, when present, MUST be stable even if `name` changes, and MUST
  be unique within the manifest. Clients SHOULD prefer `id` for bookkeeping and
  `name` for addressing.
- **MAN-15.** `sessions: false` means the agent answers single messages and holds
  no conversation state. A caller MUST NOT send a session identifier to such an
  agent.
- **MAN-16.** `start_message`, when present, is a greeting the endpoint produces
  itself at conversation creation. It is not a backend answer and consumes no
  turn.
- **MAN-17.** `description` MUST be plain text, SHOULD be one sentence, and SHOULD
  describe capability, not marketing. A client MAY show it verbatim.
- **MAN-18.** A publisher SHOULD NOT expose two agents whose descriptions are
  indistinguishable; a caller choosing between them has no basis to choose.

### 7.1 `tags`

Free-form labels a caller can filter on without parsing prose.

```json
"tags": ["sales", "consultation", "services"]
```

- **MAN-55.** Each tag MUST match `^[a-z][a-z0-9._-]{0,63}$` and MUST be unique
  within its agent.
- **MAN-56.** A tag is a label about topic, not a promise about behaviour and not
  a whitelist. A client MUST tolerate an unknown tag, and MUST NOT infer from an
  absent tag that the agent cannot help.
- **MAN-57.** A publisher SHOULD keep tags few and stable. Renaming a tag breaks
  any caller that filters on it, which is the one cost this field has.
- **MAN-58.** `tags` and `description` are not alternatives. A description is read
  by a person or a model; tags are compared by a program. Publishing both is
  normal.

## 8. `links`

`links` replaces `refs`. It is an array, so order is significant and duplicates
with different `rel` values are meaningful.

```json
"links": [
  { "rel": "menu",   "href": "https://example.com/menu",  "label": "Menu",  "type": "text/html" },
  { "rel": "openapi","href": "https://example.com/api.json","type": "application/json" },
  { "rel": "status", "href": "https://status.example.com", "type": "text/html" }
]
```

| Field         | Type   | Req. | Meaning                               |
| ------------- | ------ | ---- | ------------------------------------- |
| `rel`         | string | MUST | Machine-readable key for what this is |
| `href`        | string | MUST | Absolute URI                          |
| `label`       | string | MAY  | Human-readable name                   |
| `type`        | string | MAY  | Media type, if known                  |
| `description` | string | MAY  | One sentence                          |

- **MAN-19.** `href` MUST be an absolute URI with a scheme.
- **MAN-20.** `rel` MUST be a lowercase token matching `^[a-z][a-z0-9._-]{0,63}$`.
  Registries of conventional values are informative, not closed; a client MUST
  tolerate unknown `rel` values.
- **MAN-21.** Conventional `rel` values, informative: `site`, `docs`, `api`,
  `openapi`, `menu`, `pricing`, `status`, `terms`, `privacy`, `support`, `careers`.
- **MAN-22.** Agent-level `links` are additive to endpoint-level `links`. A client
  MUST consider both; it MUST NOT assume one replaces the other.
- **MAN-23.** A link is a promise that the URI existed when the manifest was
  generated. Clients MUST NOT treat an unreachable link as a manifest error.

### 8.2 Reserved

`manifest_version` 1.1 described an `actions` array here: a list of named things
an agent claimed it could do. It was removed in 1.2 before any implementation
consumed it, because it implied callable operations the protocol cannot provide
and a client could not act on it. See §18 and `DECISIONS.md` D-8.

A client MUST ignore an `actions` member if it receives one (MAN-3). A publisher
MUST NOT emit it.

## 9. `capabilities`

Which protocol features this endpoint implements. Absent means "assume the
minimum in `PROTO`".

```json
"capabilities": {
  "session": { "new": true, "get": true, "list": false, "close": true, "prune": false },
  "progress": true,
  "cancel": true
}
```

| Field              | Type    | Req. | Meaning                               |
| ------------------ | ------- | ---- | ------------------------------------- |
| `session.new`      | boolean | MAY  | Callers may create sessions           |
| `session.get`      | boolean | MAY  | Callers may read a session envelope   |
| `session.list`     | boolean | MAY  | Callers may browse previous sessions  |
| `session.close`    | boolean | MAY  | Callers may close a session           |
| `session.prune`    | boolean | MAY  | Callers may request retention pruning |
| `progress`         | boolean | MAY  | The endpoint emits `partial` frames   |
| `cancel`           | boolean | MAY  | The endpoint accepts `cancel`         |
| `max_turn_seconds` | integer | MAY  | Advisory ceiling for one turn         |

- **MAN-28.** A capability advertised as `true` MUST be accepted by the endpoint.
  A capability advertised as `false` or omitted MUST be rejected with the
  documented error rather than silently ignored.
- **MAN-29.** `session.new` MUST be `true` if any agent has `sessions: true`.
  Disabling history browsing (`session.list`) MUST NOT disable creation.
- **MAN-30.** A client MUST NOT call an operation whose capability is absent;
  if it does, it MUST handle the resulting error without treating the endpoint as
  broken.

## 10. `limits`

Advertised operational limits. **Advisory**: they describe intent, not a
guarantee.

```json
"limits": {
  "max_message_bytes": 8388608,
  "requests_per_minute": 60,
  "burst": 10
}
```

| Field                 | Type    | Req. | Meaning                                     |
| --------------------- | ------- | ---- | ------------------------------------------- |
| `max_message_bytes`   | integer | MAY  | Largest accepted message payload            |
| `requests_per_minute` | integer | MAY  | Sustained request rate per caller per agent |
| `burst`               | integer | MAY  | Token-bucket depth                          |
| `max_turns`           | integer | MAY  | Turns after which a session ends            |

- **MAN-31.** `max_message_bytes` MUST NOT exceed the protocol's own frame limit.
  A publisher MAY advertise a smaller ceiling.
- **MAN-32.** Limits are advisory. A client MUST still handle the `rate_limited`
  error and its retry delay; it MUST NOT rely on pacing alone to avoid it.
- **MAN-33.** A publisher SHOULD advertise limits when it enforces them. Silence
  is legal and means "unknown", not "unlimited".
- **MAN-34.** Per-agent `limits` override endpoint `limits` field by field. A field
  absent at both levels is unknown, not zero.

## 11. `session`

Session defaults for agents with `sessions: true`.

```json
"session": { "ttl_seconds": 3600 }
```

| Field         | Type    | Req. | Meaning                                       |
| ------------- | ------- | ---- | --------------------------------------------- |
| `ttl_seconds` | integer | MAY  | Lifetime of an idle session before it expires |

- **MAN-35.** `session` at endpoint level is a default. An agent-level `session`
  block overrides it field by field.
- **MAN-36.** Session identifiers are minted by the endpoint. A manifest MUST NOT
  specify the id format, length or charset; callers receive ids and echo them.
- **MAN-37.** `ttl_seconds` MUST be a positive integer when present. A caller MUST
  NOT assume a session outlives it.
- **MAN-38.** Whether a conversation is required at all is `agents[].sessions`, not
  this object. `session` never overrides `sessions`.

## 12. Freshness and integrity

```json
{
  "generated_at": "2026-11-21T09:14:00Z",
  "expires_at": "2026-11-22T09:14:00Z",
  "digest": "sha256:6b1e...",
  "signature": null
}
```

| Field          | Type           | Req. | Meaning                                           |
| -------------- | -------------- | ---- | ------------------------------------------------- |
| `generated_at` | string         | MAY  | RFC 3339 timestamp of production                  |
| `expires_at`   | string         | MAY  | RFC 3339 timestamp after which to re-read         |
| `digest`       | string         | MAY  | `sha256:` + lowercase hex over the canonical body |
| `signature`    | object \| null | MAY  | Reserved; MUST be `null` in 1.1                   |

- **MAN-39.** Timestamps MUST be RFC 3339 with an explicit offset or `Z`.
- **MAN-40.** When `digest` is present, it MUST be computed over the manifest
  serialised as canonical JSON (RFC 8785) **with `digest` and `signature`
  removed**. A client MAY verify it; failure means the document is not the one
  the publisher produced.
- **MAN-41.** `signature` is reserved. In `manifest_version` 1.1 a publisher MUST
  emit `null` or omit the field, and a client MUST ignore any object it does not
  understand.
- **MAN-42.** A client MUST NOT treat a missing `generated_at` or `digest` as an
  error. A manifest delivered inside an authenticated connection does not need
  them.
- **MAN-43.** A caller MAY cache a manifest until `expires_at`, and MUST treat a
  manifest obtained over a connection as fresh at the moment of the handshake.

## 13. Deprecated members

Both remain legal and MUST be accepted; both MUST be emitted by an
implementation that also emits their replacement, for one minor release.

| Deprecated                    | Replacement            | Rule   |
| ----------------------------- | ---------------------- | ------ |
| `refs` (`map[string]string`)  | `links` (array)        | MAN-44 |
| `commands` (array of strings) | `capabilities.session` | MAN-45 |

- **MAN-44.** When `refs` is present, a client MUST read it as if each key/value
  were a link with `rel` = key, `href` = value, and no `label` or `type`.
  A publisher SHOULD emit both `refs` and the equivalent `links` while `refs`
  remains in use.
- **MAN-45.** When `commands` is present, a client MUST read each entry as a
  session operation name (`session.new`, `session.get`, `session.list`,
  `session.close`, `session.prune`). A publisher SHOULD emit only operations it
  actually accepts — the defect this replacement exists to fix.
- **MAN-46.** A publisher MUST NOT invent new values for `commands` or new keys
  with special meaning in `refs`. Deprecated members are frozen.

## 14. Client obligations, summarised

- **MAN-47.** A client MUST validate that the document is a JSON object, that
  `manifest_version`, `protocol`, `endpoint` and `agents` are present and of the
  documented types, and that every agent has `name` and `sessions`.

  Presence of a _zero-valued_ member is not observable in most encodings: after
  decoding, `"sessions": false` and an absent `sessions` are the same value, and
  so are `0` and an absent integer. A client MUST NOT treat that as an error, and
  MUST fall back to the documented meaning of the zero value (`sessions: false`,
  TTL unknown). The publisher obligation to emit those members is enforced by the
  schema, not by the client.

- **MAN-48.** On a document that fails MAN-47, a client MUST report a manifest
  error and MUST NOT proceed as if it had received a smaller valid manifest.
- **MAN-49.** A client MUST NOT require any optional field, or any particular
  `rel` value in `links`.
- **MAN-50.** A client MUST NOT present `endpoint.description` or agent
  `description` as if it were an answer from the business.

## 15. Server obligations, summarised

- **MAN-51.** A publisher MUST produce a manifest whose `agents` entries
  correspond to agents that actually answer, and MUST NOT list an agent that
  would fail every message with `agent_not_found`.
- **MAN-52.** A publisher MUST keep `capabilities` truthful: advertised `true`
  means accepted, omitted or `false` means rejected with a documented error.
- **MAN-53.** A publisher MUST emit `manifest_version`. Emitting `1.0` (no
  `manifest_version`) remains legal for older deployments; clients MUST treat its
  absence as `1.0` and fall back to `refs` and `commands`.
- **MAN-54.** A publisher SHOULD produce a stable manifest for unchanged state, so
  that `digest` is meaningful and clients can skip re-reading.

## 16. Examples

A minimal valid manifest (`manifest_version` `1.3`, one stateless agent):

```json
{
  "manifest_version": "1.3",
  "protocol": "portico/1",
  "endpoint": { "name": "acme-plumbing" },
  "agents": [
    {
      "name": "support",
      "description": "Questions about service and coverage",
      "sessions": false
    }
  ]
}
```

A full manifest:

```json
{
  "manifest_version": "1.3",
  "protocol": "portico/1",
  "endpoint": {
    "id": "restaurant-prod",
    "name": "restaurant",
    "description": "Fresh pizza and table bookings"
  },
  "links": [
    { "rel": "site", "href": "https://restaurant.example", "type": "text/html" }
  ],
  "capabilities": {
    "session": {
      "new": true,
      "get": true,
      "list": true,
      "close": true,
      "prune": true
    },
    "progress": true,
    "cancel": true,
    "max_turn_seconds": 300
  },
  "limits": {
    "max_message_bytes": 8388608,
    "requests_per_minute": 60,
    "burst": 10
  },
  "session": { "ttl_seconds": 3600 },
  "agents": [
    {
      "id": "orders",
      "name": "orders",
      "description": "Take food orders: pizzas, sides, drinks, pickup or delivery",
      "tags": ["orders", "delivery", "pickup"],
      "sessions": true,
      "start_message": "Hello! Ask me anything about the restaurant.",
      "links": [
        {
          "rel": "menu",
          "href": "https://restaurant.example/menu",
          "label": "Menu",
          "type": "text/html"
        }
      ],
      "session": { "ttl_seconds": 86400 }
    },
    {
      "name": "status",
      "description": "Opening hours and current waiting time",
      "sessions": false
    }
  ],
  "generated_at": "2026-11-21T09:14:00Z",
  "digest": "sha256:0f1c9c1e8a6d4b2f5e7a0c3d9b8f6a4e2d1c0b9a8f7e6d5c4b3a2918f7e6d5c4",
  "signature": null
}
```

## 17. Requirement index

| ID     | Section | Subject                                      |
| ------ | ------- | -------------------------------------------- |
| MAN-1  | 4       | `manifest_version` shape                     |
| MAN-2  | 4       | additive change = MINOR                      |
| MAN-3  | 4       | ignore unknown members                       |
| MAN-4  | 4       | unknown enum value → fallback                |
| MAN-5  | 4       | breaking change = MAJOR                      |
| MAN-6  | 4       | required fields present                      |
| MAN-7  | 5       | empty `agents` is valid                      |
| MAN-8  | 5       | no sensitive material                        |
| MAN-9  | 6       | `endpoint.id` opaque and stable              |
| MAN-10 | 6       | `endpoint.name` is display only              |
| MAN-11 | 6       | descriptions are plain text                  |
| MAN-12 | 7       | agent `name` uniqueness and charset          |
| MAN-13 | 7       | renaming an agent                            |
| MAN-14 | 7       | agent `id` stability                         |
| MAN-15 | 7       | `sessions: false` semantics                  |
| MAN-16 | 7       | `start_message` is endpoint-produced         |
| MAN-17 | 7       | description style                            |
| MAN-18 | 7       | no indistinguishable agents                  |
| MAN-19 | 8       | link `href` absolute                         |
| MAN-20 | 8       | link `rel` charset                           |
| MAN-21 | 8       | conventional `rel` values                    |
| MAN-22 | 8       | agent + endpoint links are additive          |
| MAN-23 | 8       | links may rot                                |
| MAN-28 | 9       | advertised capability is honoured            |
| MAN-29 | 9       | `session.new` whenever sessions exist        |
| MAN-30 | 9       | client honours missing capability            |
| MAN-31 | 10      | `max_message_bytes` bound                    |
| MAN-32 | 10      | limits advisory, handle `rate_limited`       |
| MAN-33 | 10      | advertise enforced limits                    |
| MAN-34 | 10      | per-agent limits override                    |
| MAN-35 | 11      | agent `session` overrides endpoint           |
| MAN-36 | 11      | ids are minted, not described                |
| MAN-37 | 11      | `ttl_seconds` positive                       |
| MAN-38 | 11      | `sessions` is authoritative                  |
| MAN-39 | 12      | RFC 3339 timestamps                          |
| MAN-40 | 12      | digest over canonical JSON                   |
| MAN-41 | 12      | `signature` reserved                         |
| MAN-42 | 12      | freshness fields optional                    |
| MAN-43 | 12      | caching bounded by `expires_at`              |
| MAN-44 | 13      | `refs` read as links                         |
| MAN-45 | 13      | `commands` read as session ops               |
| MAN-46 | 13      | deprecated members frozen                    |
| MAN-47 | 14      | client validation                            |
| MAN-48 | 14      | reject, do not half-accept                   |
| MAN-49 | 14      | no optional field is required                |
| MAN-50 | 14      | descriptions are not answers                 |
| MAN-51 | 15      | listed agents answer                         |
| MAN-52 | 15      | capabilities truthful                        |
| MAN-53 | 15      | absent `manifest_version` = 1.0              |
| MAN-54 | 15      | stable output for stable state               |
| MAN-55 | 7.1     | tag charset and uniqueness                   |
| MAN-56 | 7.1     | tags are labels, not promises                |
| MAN-57 | 7.1     | keep tags few and stable                     |
| MAN-58 | 7.1     | tags and description are not either/or       |
| MAN-59 | 1       | adapters surface the document, not a summary |

## 18. Retired requirements

Identifiers are never reused: a citation in an article or an issue keeps naming
the rule it named when it was written. These were removed, and the numbers stay
retired.

| ID     | Retired in | Was                                  | Why                      |
| ------ | ---------- | ------------------------------------ | ------------------------ |
| MAN-24 | 1.2        | `action.name` charset and uniqueness | `actions` removed (§8.2) |
| MAN-25 | 1.2        | `input`/`output` are hints           | `actions` removed (§8.2) |
| MAN-26 | 1.2        | `actions` is not a whitelist         | `actions` removed (§8.2) |
| MAN-27 | 1.2        | no unhonourable action               | `actions` removed (§8.2) |

A client built against `manifest_version` 1.1 that reads `actions` will simply
find it absent, which MAN-49 already requires it to tolerate.
