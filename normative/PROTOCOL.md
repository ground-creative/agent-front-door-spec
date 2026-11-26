# The wire protocol

**Normative.** Requirement identifiers (`PROTO-n`, `WH-n`) are stable; cite them
in issues and proposals.

- Spec release: `spec-v0.4`
- Protocol identifier: `portico/1`
- See also: [`MANIFEST.md`](MANIFEST.md) (the document delivered at handshake),
  [`CONFORMANCE.md`](CONFORMANCE.md), [`SECURITY.md`](SECURITY.md).

---

## 1. Shape

One port serves both transports:

- **TCP + TLS 1.3**, and **UDP + QUIC**, on the same port;
- ALPN `portico/1` selects the protocol;
- every message is a **frame**: a 9-byte header, then a JSON payload.

- **PROTO-1.** A server MUST offer TLS 1.3 or later, and MUST select `portico/1`
  via ALPN. There is no plaintext mode.
- **PROTO-49.** A client SHOULD offer every wire identifier the draft has used,
  newest first, so that a server which has not been redeployed still completes
  the handshake. A server SHOULD accept those identifiers for a deprecation
  window and MUST NOT require the newest one from a peer during it. This is the
  ALPN equivalent of `PROTO-48`: a rename is a change of token, not a flag day.
  The identifiers that must be accepted are `portico/1`, `frontdoor/1` and <!-- identifier: retired -->
  `vireo/1`; the last two are retired and a server MAY stop honouring them at the <!-- identifier: retired -->
  release after next.
- **PROTO-2.** A server SHOULD serve TCP/TLS and UDP/QUIC on the same port
  number. A client MUST be able to use either; it MAY prefer one.
- **PROTO-3.** Frames are self-delimiting. A reader MUST consume exactly one
  frame per read, regardless of how the transport splits or coalesces bytes.

## 2. Frames

| Byte | Field                | Meaning                            |
| ---- | -------------------- | ---------------------------------- |
| 0–3  | `stream_id` (uint32) | correlates request/response stream |
| 4    | `type` (uint8)       | frame type                         |
| 5–8  | `length` (uint32)    | payload length                     |
| 9–   | payload              | UTF-8 JSON                         |

All integers are big-endian.

| Type        | Code   | Payload            | Since |
| ----------- | ------ | ------------------ | ----- |
| `message`   | `0x01` | `MessageRequest`   | 1.0   |
| `data`      | `0x02` | `MessageResponse`  | 1.0   |
| `end`       | `0x03` | `EndPayload`       | 1.0   |
| `partial`   | `0x04` | `PartialPayload`   | 1.1   |
| `error`     | `0x05` | `ErrorPayload`     | 1.0   |
| `negotiate` | `0x10` | `NegotiateRequest` | 1.0   |
| `manifest`  | `0x11` | manifest           | 1.0   |
| `session`   | `0x12` | `SessionRequest`   | 1.0   |
| `cancel`    | `0x13` | empty              | 1.1   |

- **PROTO-4.** A payload MUST NOT exceed 8 388 608 bytes (8 MiB). A reader MUST
  reject a larger advertised length without buffering it.
- **PROTO-5.** A payload cut short mid-frame is an error, not end-of-stream.
- **PROTO-6.** A reader MUST ignore unknown frame types on a stream it did not
  originate, and MUST NOT treat them as a protocol violation. Unknown frames are
  how additive features arrive.
- **PROTO-7.** A writer MUST NOT send a frame type the peer has not advertised a
  capability for, except where this document says otherwise.

Frame types are reserved by `type` code, not by name. Codes `0x06`–`0x0F` and
`0x14`–`0x1F` are unassigned; a future revision may allocate them.

## 3. Handshake

The first frame on a connection MUST be `negotiate`:

```json
{
  "protocol": "portico/1",
  "client": {
    "id": "vireo_4f1c8a2e9b7d4c0fa1e2d3b4c5a6f7e8",
    "name": "example-client",
    "version": "0.4"
  }
}
```

- **PROTO-8.** `client.id` MUST be present and MUST match
  `^vireo_[0-9a-f]{32}$` — the prefix, then 32 lowercase hex characters (128
  random bits). Anything else MUST be refused with `bad_client_id`.
- **PROTO-9.** A client SHOULD generate its id once and reuse it across sessions
  and hosts. The id is the identity sessions are scoped by.
- **PROTO-10.** `client.name` and `client.version` are informational and MAY be
  omitted. A server MUST NOT make authorization decisions from them.
- **PROTO-11.** A protocol identifier other than the one the server implements
  MUST be refused with `bad_protocol`.
- **PROTO-12.** Any first frame of another type MUST be refused with
  `invalid_frame`.
- **PROTO-13.** The server MUST answer `negotiate` on the same stream with a
  `manifest` frame containing a valid manifest per `MANIFEST.md`.
- **PROTO-14.** A `negotiate` frame arriving later on an established connection
  MUST be answered with the manifest again. It MUST NOT close the connection.

The manifest is the _first_ thing a caller learns. Everything after it is
conversation.

## 4. Messages

A `message` frame carries one turn:

```json
{
  "agent": "orders",
  "session_id": "y113YjxvfPQzaE6ZWhmabl-wnxthBAFJ",
  "message": "I'd like 2 margherita pizzas for pickup"
}
```

| Field        | Type   | Req.        | Meaning                                     |
| ------------ | ------ | ----------- | ------------------------------------------- |
| `agent`      | string | MUST        | An agent `name` from the manifest           |
| `session_id` | string | conditional | Present when the agent has `sessions: true` |
| `message`    | string | MUST        | The turn's text                             |

- **PROTO-15.** `agent` MUST name an agent present in the manifest the client
  received. An unknown name MUST fail with `agent_not_found`.
- **PROTO-16.** A conversational agent (`sessions: true`) MUST be addressed with a
  session id; omitting it MUST fail with `session_required`.
- **PROTO-17.** A stateless agent (`sessions: false`) MUST be addressed without one;
  supplying it MUST fail with `invalid_frame`.
- **PROTO-18.** `message` MAY be empty only if the agent's `start_message` makes an
  empty turn meaningful. Otherwise a server SHOULD reject it as `invalid_frame`.

The server answers with a `data` frame, then an `end` frame:

```json
{
  "reply": "Sure — margherita, marinara and tiramisu are on the menu today.",
  "session": { "summary": "took an order request" }
}
```

```json
{
  "ok": true,
  "session": {
    "id": "y113Y...",
    "agent": "orders",
    "turns": 1,
    "summary": "took an order request",
    "status": "open"
  }
}
```

- **PROTO-19.** Exactly one `data` frame MAY precede `end` for a turn. A turn that
  produces no answer MUST close with `end` carrying `ok: false`.
- **PROTO-20.** `end` MUST be the last frame on the stream for that turn. It is the
  only frame that completes a turn.
- **PROTO-21.** `session.summary` in a reply, when non-empty, MUST replace the
  envelope's summary.
- **PROTO-22.** `session.status: "closed"` MUST close the conversation after the
  turn and MUST be reflected in the `end` envelope.

## 5. Progress

A `partial` frame is progress inside a turn:

```json
{ "kind": "status", "seq": 2, "text": "fetching the menu…" }
```

- **PROTO-23.** A `partial` frame MUST NOT end a turn and MUST NOT increment the
  turn count.
- **PROTO-24.** `seq` MUST increase monotonically within a turn. A client MUST
  tolerate gaps and duplicates.
- **PROTO-25.** `kind` is `status` for an ephemeral line. Other values are reserved;
  a client MUST ignore a kind it does not know.
- **PROTO-26.** A server MUST NOT emit `partial` if `capabilities.progress` is
  absent or false.

## 6. Cancellation

A caller abandons a turn by sending `cancel` on the stream the `message` was sent
on, with an empty payload.

- **PROTO-27.** A server that receives `cancel` MUST stop waiting for the turn,
  MUST cancel the upstream request's context, and MUST answer that stream with
  `end` carrying `ok: false, cancelled: true` and no `data` frame.
- **PROTO-28.** A cancelled turn MUST NOT modify the session envelope. `turns` and
  `summary` MUST be unchanged.
- **PROTO-29.** Cancelling a stream that is not in flight MUST be ignored, not
  reported as an error.
- **PROTO-30.** Cancellation is cooperative and best effort. A server MUST NOT
  claim rollback semantics it cannot provide, and a client MUST NOT assume work
  the backend already committed has been undone.
- **PROTO-31.** Turns MUST run concurrently with the read loop, so that a `cancel`
  frame is readable while a turn is in flight.

## 7. Sessions

A session is an **envelope**: identity and metadata, never conversation content.

```json
{
  "id": "y113YjxvfPQzaE6ZWhmabl-wnxthBAFJ",
  "agent": "orders",
  "created_at": "2026-11-13T16:04:31Z",
  "updated_at": "2026-11-13T16:04:31Z",
  "expires_at": "2026-11-13T17:04:31Z",
  "summary": "took an order request",
  "turns": 1,
  "status": "open"
}
```

- **PROTO-32.** `status` MUST be `open`, `closed` or `expired`.
- **PROTO-33.** Envelopes MUST be scoped by `(client id, agent, session id)`. An id
  belonging to another client MUST behave exactly as an unknown id.
- **PROTO-34.** Only `open` sessions MAY be resumed. Others MUST fail with
  `unknown_session`.
- **PROTO-35.** The server MUST mint ids. A client MUST treat them as opaque and
  MUST NOT parse them.
- **PROTO-36.** A server MUST NOT store message content in a session envelope.

Session operations ride the `session` frame:

| Op              | Fields                       | Answer                                |
| --------------- | ---------------------------- | ------------------------------------- |
| `session.new`   | `agent`, `summary?`          | `{session, start_message?}`           |
| `session.list`  | `agent`, `limit?`, `cursor?` | `{sessions, next_cursor}`             |
| `session.get`   | `agent`, `id`                | the envelope                          |
| `session.close` | `agent`, `id`, `reason?`     | the closed envelope                   |
| `session.prune` | `retention?`                 | `{retention, removed, before, after}` |

- **PROTO-37.** A server MUST accept only operations advertised as `true` in
  `capabilities.session`, and MUST reject the rest with `invalid_frame`.
- **PROTO-38.** `session.new` MUST be available for every agent with
  `sessions: true`. Disabling `session.list` MUST NOT disable it.
- **PROTO-39.** `session.new` on a stateless agent MUST fail with
  `invalid_frame`.

## 8. Errors

```json
{
  "code": "session_required",
  "message": "agent \"orders\" holds conversations: start one first"
}
```

| Code               | When                                                    |
| ------------------ | ------------------------------------------------------- |
| `bad_client_id`    | the client id is missing or malformed                   |
| `bad_protocol`     | the negotiated protocol is not implemented              |
| `agent_not_found`  | no agent with that name                                 |
| `session_required` | a conversational agent was addressed without a session  |
| `unknown_session`  | the id is unknown, closed, expired, or another client's |
| `upstream_error`   | the backend failed, timed out, or returned non-2xx      |
| `rate_limited`     | the caller exceeded an advertised or enforced limit     |
| `invalid_frame`    | malformed frame, payload, or a disabled operation       |
| `internal`         | anything unexpected                                     |

- **PROTO-40.** An error MUST arrive as an `error` frame on the caller's stream.
- **PROTO-41.** `code` MUST be one of the values above. A client MUST treat an
  unknown code as `internal`.
- **PROTO-42.** `message` is diagnostic text for humans and MAY change.
- **PROTO-43.** `rate_limited` MUST carry a message stating the retry delay. A
  client SHOULD honour it.

## 9. Backend webhook

The daemon is not the business. Every turn becomes one HTTP request to the
agent's backend.

```
POST /vireo/message
Content-Type: application/json
X-Portico-Protocol: portico/1
X-Portico-Agent: orders
X-Portico-Session: y113YjxvfPQzaE6ZWhmabl-wnxthBAFJ

{ "agent": "orders",
  "session_id": "y113YjxvfPQzaE6ZWhmabl-wnxthBAFJ",
  "message": "I'd like 2 margherita pizzas for pickup" }
```

- **WH-1.** A server MUST deliver a turn to exactly one backend endpoint (the
  agent's configured transport).
- **WH-2.** The request body MUST contain `agent`, `session_id` (when present) and
  `message`.
- **WH-3.** `X-Portico-Agent` and `X-Portico-Session` MUST match the body.
- **WH-4.** A 2xx response MUST be read as JSON
  `{reply, session?}`; a bare JSON string MUST be accepted as `reply`.
- **WH-5.** A non-2xx response MUST surface to the caller as `upstream_error`.
- **WH-6.** A response body MUST be capped at 8 MiB.
- **WH-7.** A turn MUST be bounded by the agent's timeout (default 30 s), and a
  timeout MUST surface as `upstream_error`.
- **WH-8.** When cancellation occurs, the backend request's context MUST be
  cancelled. A backend observes it as `Context().Done()`.

### 9.1 Streaming progress

If the request carries `Accept: application/x-ndjson` and the backend answers
`Content-Type: application/x-ndjson`, the body is newline-delimited JSON:

```
{"partial": "fetching your menu…"}
{"partial": "composing the answer…"}
{"reply": "Done — margherita is available.", "session": {"summary": "answered"}}
```

- **WH-9.** Each `{"partial": "…"}` line MUST be forwarded immediately as a
  `partial` frame with `kind: "status"`.
- **WH-10.** The last line MUST be the usual `{reply, session}` object, and the
  turn MUST still end with `end`.
- **WH-11.** A backend that does not answer with that content type MUST be read
  as a single JSON body (WH-4).

### 9.2 First turn

When an agent declares `start_message`, the server returns it at
`session.new` without calling the backend, and tells the backend on the first
turn:

```json
{
  "agent": "orders",
  "session_id": "…",
  "message": "…",
  "initial_assistant_message": "Welcome to the orders desk."
}
```

- **WH-12.** `initial_assistant_message` MUST be present only on the first turn of
  a session created with a `start_message`, and MUST be the exact text the caller
  saw.
- **WH-13.** A later turn MUST omit the field.

## 10. Discovery

A client given a bare domain resolves a service record:

```
_portico._tcp.example.com. 300 IN SRV 10 5 7777 agent.example.com.
```

- **PROTO-44.** A client MUST treat the SRV target and port as the endpoint
  address. There is no default port and no fallback.
- **PROTO-45.** A hostname without an SRV record MUST be refused; the caller may
  address the endpoint as `host:port` explicitly.
- **PROTO-46.** When several records exist, a client MUST honour `priority`, then
  `weight`, as DNS defines them.
- **PROTO-47.** The TLS `ServerName` MUST be the queried domain, and the presented
  certificate MUST be valid for it. See [`SECURITY.md`](SECURITY.md).
- **PROTO-48.** A client MAY fall back to the retired records `_frontdoor._tcp` <!-- identifier: retired -->
  and `_vireo._tcp` when `_portico._tcp` does not resolve, and MUST treat all of <!-- identifier: retired -->
  them as the same service. It SHOULD report which record answered, so that an
  operator can see an unmigrated deployment rather than a silent fallback.

`_portico._tcp` is the identifier this revision publishes. It is not registered with
IANA. Earlier drafts of this document published `_vireo._tcp`, named after the reference
implementation; that was a defect in an open specification and is retired here (D-10).
A future revision may publish separate `_tcp` and `_udp` records; a client MUST tolerate
their absence.

## 11. Requirement index

| ID       | Section | Subject                                      |
| -------- | ------- | -------------------------------------------- |
| PROTO-1  | 1       | TLS 1.3 minimum, ALPN                        |
| PROTO-2  | 1       | both transports on one port                  |
| PROTO-3  | 1       | one frame per read                           |
| PROTO-4  | 2       | 8 MiB cap, reject before buffering           |
| PROTO-5  | 2       | truncated payload is an error                |
| PROTO-6  | 2       | ignore unknown frame types                   |
| PROTO-7  | 2       | do not send unsupported frames               |
| PROTO-8  | 3       | client id shape                              |
| PROTO-9  | 3       | client id reused                             |
| PROTO-10 | 3       | name/version are informational               |
| PROTO-11 | 3       | unknown protocol refused                     |
| PROTO-12 | 3       | first frame must be negotiate                |
| PROTO-13 | 3       | manifest answers negotiate                   |
| PROTO-14 | 3       | re-negotiate returns manifest                |
| PROTO-15 | 4       | agent must exist                             |
| PROTO-16 | 4       | session required for conversational agents   |
| PROTO-17 | 4       | no session for stateless agents              |
| PROTO-18 | 4       | empty message                                |
| PROTO-19 | 4       | one data frame per turn                      |
| PROTO-20 | 4       | end terminates a turn                        |
| PROTO-21 | 4       | reply summary replaces envelope              |
| PROTO-22 | 4       | closed status ends the conversation          |
| PROTO-23 | 5       | partial never ends a turn                    |
| PROTO-24 | 5       | partial seq ordering                         |
| PROTO-25 | 5       | unknown partial kind ignored                 |
| PROTO-26 | 5       | no partial without capability                |
| PROTO-27 | 6       | cancel behaviour                             |
| PROTO-28 | 6       | cancelled turn does not touch the envelope   |
| PROTO-29 | 6       | late cancel ignored                          |
| PROTO-30 | 6       | no rollback claims                           |
| PROTO-31 | 6       | concurrent turns                             |
| PROTO-32 | 7       | session status values                        |
| PROTO-33 | 7       | session scoping                              |
| PROTO-34 | 7       | only open sessions resume                    |
| PROTO-35 | 7       | server mints ids                             |
| PROTO-36 | 7       | envelope holds no content                    |
| PROTO-37 | 7       | only advertised ops accepted                 |
| PROTO-38 | 7       | session.new always for conversational agents |
| PROTO-39 | 7       | session.new on stateless agent fails         |
| PROTO-40 | 8       | errors arrive as error frames                |
| PROTO-41 | 8       | known error codes                            |
| PROTO-42 | 8       | message is diagnostic                        |
| PROTO-43 | 8       | rate limit states retry delay                |
| PROTO-44 | 10      | SRV target and port are the address          |
| PROTO-45 | 10      | no SRV means no resolution                   |
| PROTO-46 | 10      | priority and weight honoured                 |
| PROTO-47 | 10      | ServerName and certificate                   |
| PROTO-48 | 10      | retired SRV record fallback                  |
| PROTO-49 | 1       | ALPN identifier compatibility                |
| WH-1     | 9       | one backend per turn                         |
| WH-2     | 9       | request body fields                          |
| WH-3     | 9       | headers match body                           |
| WH-4     | 9       | 2xx semantics                                |
| WH-5     | 9       | non-2xx is upstream_error                    |
| WH-6     | 9       | 8 MiB body cap                               |
| WH-7     | 9       | turn timeout                                 |
| WH-8     | 9       | cancellation reaches the backend             |
| WH-9     | 9.1     | partial lines forwarded                      |
| WH-10    | 9.1     | last NDJSON line is the answer               |
| WH-11    | 9.1     | non-NDJSON is a single body                  |
| WH-12    | 9.2     | first-turn greeting field                    |
| WH-13    | 9.2     | later turns omit it                          |
