# Brief: for agents that research, write or answer about this

**Informative.** A one-page orientation for an agent working on this project's behalf.

It is not the specification. Where this brief and the normative text disagree, the normative
text wins — and this brief is wrong and should be fixed.

## The problem

An agent that wants one fact from a business goes through a front door built for a human
reader: fetch a page of markup, parse it, guess. One answer costs several pages and a parse.
Bot walls then stop it, so the agent impersonates a browser to read what the business
published publicly. Every integration is written per business and per assistant, so nothing
carries over; when a layout changes it breaks quietly. The business has no say in any of it.

This is not a capability gap. An API, a GraphQL schema or an MCP server can do discovery and
multi-turn conversation perfectly well — for one service, built by someone, for someone.
What is missing is a **common discovery and communication contract**, so the work does not
restart at every business and reachability is not decided by whoever runs the directory.

## The shape of the answer

- The business's own **domain** is the discovery point. It is already public, renewable, and
  under the business's operational control.
- A **DNS SRV record** answers "where is the service" before any HTTP request exists. A
  well-known path answers "where is the document", after one. DNS routes, TLS authenticates,
  the **manifest** describes what is offered.
- The business runs a small **daemon** on its own infrastructure. On connection it presents
  the manifest: what it exposes, its links, its limits, its session rules.
- Each turn is routed to the business's **own endpoint**. The business keeps its
  capabilities, data, models and execution.
- A **session** is an envelope — id, owner, agent, timestamps, expiry, summary, turn count,
  status. It does not hold the conversation. Resuming means the same session id from the
  same client and restores nothing on the caller's side.

## What the standard defines

`agent-front-door-spec`, currently **`spec-v0.3`**:

| Document        | Settles                                                        |
| --------------- | -------------------------------------------------------------- |
| `MANIFEST.md`   | what a business publishes, and what each field means            |
| `PROTOCOL.md`   | how a caller and the daemon talk, and what each must do         |
| `CONFORMANCE.md`| what a claim of conformance means, and what it does not         |
| `SECURITY.md`   | how the peer is authenticated, what a client must not accept    |

Conformance is a ladder, cumulative, and both roles climb it:

| Level | Name               | Proves                                                  |
| ----- | ------------------ | ------------------------------------------------------- |
| L0    | Manifest publisher | a document exists and validates — one file, no daemon    |
| L1    | Discovery          | the domain resolves to the service                       |
| L2    | Conversations      | a session with turns works                               |
| L3    | Live               | advertised operations are proven, not merely listed      |
| L4    | Operational        | it holds under operational conditions                    |

A claim names its **role**, its **level** and the **spec release**, and lists any
requirement it does not satisfy. A partial claim is legitimate; a silent gap is not.

`machine/` holds the schema, examples, fixtures, and a probe that shares no code with any
implementation — which is what makes its result evidence rather than self-assessment.

## What exists today

| Thing | State |
| --- | --- |
| [vireo](https://github.com/ground-creative/vireo) — reference daemon, Go | **L2, partial L3** against `spec-v0.3` |
| `ziwa.ai` — a live deployment | L2, verified by the specification's probe |
| `vireo-chat`, `vireo-mcp` — clients | L2 against `spec-v0.3` |
| Manifest publishers | none yet |

The partial is specific: `progress` and `cancel` are advertised without a fixture proving
them. Nothing here is proven at scale.

## What may be claimed

**About the standard:** what the four documents define, what a level means, that the
specification is open and versioned and has an independent probe.

**About the implementation:** only what its own claim supports — a daemon at the business's
domain found by a DNS lookup; each turn routed to the business's own endpoint; a session
envelope that does not hold the conversation; and the removal of the third-party directory,
and only that.

**Never:** that it holds the conversation, keeps context, remembers history, recovers the
caller's sockets or state, guarantees delivery or execution, or authorises anyone. Never
that it removes the caller's adapters, parsers or schema drift. Never that publishing
stopped being work. Never that the implementation *is* the standard, or that a business must
choose it.

Never a transitive verb that promises an outcome — lets, enables, allows, solves, addresses,
eliminates, replaces, removes the need for. The honest tense is "we are working on", "we are
testing", "we have not proven".

Never pose the open question as a cost comparison where our side is obviously heavier. A
daemon is more work than a form field. The honest question is which work moved.

## How to judge whether something is relevant

Judge against the problem, not against whether the thing resembles an implementation.

| Score | The item                                                              |
| ----- | --------------------------------------------------------------------- |
| 1–3   | has little to do with it                                              |
| 4–6   | adjacent: agent infrastructure, protocols, integration pain, adoption |
| 7–8   | direct work on discovery, capability descriptions, sessions, identity  |
| 9–10  | ships something that works, or seriously challenges the approach       |

A competing architecture or an independent implementation is as relevant as this one —
sometimes more. Popularity is not relevance; an endorsement is not relevance.

## The adoption asymmetry

This is not blocked by protocol design. It is blocked by adoption. Closed networks did not
win on their wire; they won because the participants were already inside.

A business cannot adopt a protocol — it needs budget, a vendor, a meeting, a reason. An
agent can adopt one in an afternoon. So the first adopters are agents and the people who
build them.

## Vocabulary

manifest, discovery, capability, session, caller, business, directory, conformance, level.
"Front door" names the arrangement; "daemon" names a process, not the standard. Use one
word per idea so a reader can connect one piece of writing to the next.

## Where the source is

- The standard: this repository — `normative/` for the rules, `informative/` for the
  argument, `machine/` for the schema, fixtures and probe.
- The reference implementation: <https://github.com/ground-creative/vireo>.
