---
title: What a session buys you
published: 2026-11-21
spec: spec-v0.3
requirements: [PROTO-19, PROTO-20, PROTO-23, PROTO-24, PROTO-26, PROTO-27, PROTO-28, PROTO-30, PROTO-31, PROTO-36]
canonical:
---

# What a session buys you

*Draft. Pinned to `spec-v0.3`; requirement IDs refer to that release.*

## Premises

- A caller that cannot distinguish "still working" from "finished" from "gave up"
  will guess, and will guess wrong.
- Most request/response shapes encode none of those three.
- A business would rather expose what a caller needs to know than explain its
  internal state.

---

## The 200 that means nothing

Every agent that talks to a service today eventually receives a `200 OK` and a
body. It has no way to know whether that body is an answer, a partial answer, an
acknowledgement, or a formatted apology. The status code is about the transport;
the meaning is invented per service.

So the caller guesses. It guesses that a timeout means failure when the work
succeeded. It guesses that a long gap means a hang when it means thinking. Those
guesses are the expensive part, and they are structurally unavoidable in a shape
that only has "request sent" and "bytes received".

A session is an attempt to remove exactly three guesses.

## One turn, one end

A turn is one message in, and at most one answer out, closed by one explicit
terminator (`PROTO-19`, `PROTO-20`):

```json
{ "ok": true, "session": { "turns": 3, "summary": "answered coverage question" } }
```

`end` is the last frame on that stream and the only frame that completes a turn.
A turn that produces no answer still closes with `end`, carrying `ok: false`. There
is no shape in which a caller waits forever on a well-behaved endpoint, and no
shape in which a missing answer is silently the same as a successful one.

## Progress that is not a turn

A backend that knows it will be slow can emit `partial` frames while it works
(`PROTO-23`). The rules that make this safe are the interesting ones:

- a `partial` never ends a turn and never increments the turn count;
- `seq` is monotonic within a turn, and a client must tolerate gaps and duplicates
  (`PROTO-24`);
- a server must not emit one unless it advertised `capabilities.progress`
  (`PROTO-26`).

The last rule is what keeps this honest. Progress is a promise the endpoint makes
about itself before the first turn; a caller can decide what UI to build based on
the manifest, not on watching what happens.

## Cancellation that admits what it is

A caller that no longer wants an answer sends `cancel` on the stream the message
was sent on (`PROTO-27`). The daemon stops waiting, cancels the backend's request
context, and answers that stream with `{"ok": false, "cancelled": true}` — no
`data` frame.

Two details make this more than a nicety:

**The session is not touched** (`PROTO-28`). A cancelled turn is not a turn:
`turns` and `summary` are exactly what they were. That means a caller can abandon
work without corrupting the record of what happened.

**It is explicitly not rollback** (`PROTO-30`). The daemon can stop waiting and can
abort the request; it cannot undo what the backend already committed. A
specification that implied otherwise would be worse than silence, because callers
would build around a promise the protocol cannot keep.

And it only works because of a structural choice: turns run concurrently with the
read loop (`PROTO-31`). If a turn blocked the connection, a cancel frame would sit
unread behind the very call it was meant to abandon.

## The envelope is a receipt, not a transcript

A session carries identity and metadata — id, agent, timestamps, summary, turn
count, status — and **no message content** (`PROTO-36`). That is a deliberate
boundary, not an oversight:

- the daemon is not a party to the conversation, so it should not hold one;
- a business can be audited about what it received without a third party keeping
  a copy;
- a caller can recognise a conversation later from a one-line summary, which is
  all most callers need.

What it does not carry is just as deliberate: there is no delivery guarantee, no
idempotency key, no transaction across turns. Two turns are two events, and the
effects belong to the business's backend. The specification says so instead of
letting a caller assume otherwise.

## Why this is the half that matters

Discovery is the part everyone can agree with — it is routing, and routing is
easy to describe. The session is where a protocol has to make promises it can keep:
that a turn has an end, that progress is not an answer, that abandoning a turn is
not a lie about rolling back the world.

Every system that talks to a business today hands you a response and leaves the
meaning to you. A session hands you the smallest set of facts that removes the
guessing: this turn ended, here is what it changed, and here is whether you are
still talking to the same conversation.

That is not glamorous. It is the difference between a caller that can plan and one
that can only hope.
