# Comparison

_Informative._ One page, because it is the first question every reviewer asks.

|                                | What it solves                                         | What it does not                                                          | Relationship to this spec                                                       |
| ------------------------------ | ------------------------------------------------------ | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **Scraping a website**         | nothing structural — it reads what is already public   | token cost, bot walls, silent breakage, no business control               | the thing this replaces                                                         |
| **Custom API per integration** | one service, one caller                                | carries over to nobody; every integration is new work                     | compatible: the backend behind a webhook can be any API                         |
| **OpenAPI**                    | describing an HTTP API's operations and schemas        | discovery of the business, sessions, progress, cancellation, who may call | a `link` with `rel: "openapi"` may point at one                                 |
| **MCP**                        | exposing tools to a host over stdio or HTTP            | a business naming itself, discovery by domain, a conversation with turns  | `vireo-mcp` is an adapter; a host that speaks this protocol natively needs none |
| **A2A Agent Cards**            | a well-known document describing an agent's interfaces | routing to a non-HTTP endpoint; sessions with explicit turn semantics     | overlapping intent; different discovery and session model (see below)           |
| **`llms.txt`**                 | a curated list of pages for a model to read            | anything enforceable; no conversation, no state, no identity              | a link could point at one                                                       |
| **A registry / directory**     | a place to be listed                                   | independence from the operator of the registry                            | explicitly rejected (`D-3`)                                                     |

## Versus MCP

MCP is a way for a host to call tools. It assumes both sides are already connected
and that someone configured the server. It does not answer "which businesses exist
for this domain" or "how do I resume yesterday's conversation with the bookings
agent".

This specification is the other half: discovery by domain, a manifest of exposed
agents, and a conversation with explicit turns. An MCP-speaking host reaches it
through an adapter, which is a mapping problem, not a protocol requirement —
`vireo-chat` connects with no MCP in the path at all.

## Versus A2A Agent Cards

Both publish a description of what an agent offers, and both are intended to be
implemented independently. The differences are deliberate:

- **Discovery.** A2A looks for a well-known document over HTTPS. This spec resolves
  an SRV record, because the endpoint is usually not the website.
- **Session semantics.** This spec makes "turn", "progress", "completed", "failed",
  and "abandoned" distinct, normative things. That distinction is the reason the
  session channel is separate from the description.
- **Scope.** A2A is a broader effort with a different governance story. This is a
  small contract with a written rationale and a conformance ladder.

They can coexist: a manifest can carry a link to an A2A Agent Card, and a business
can publish both.

## Versus OpenAPI

OpenAPI describes operations on an HTTP API: paths, methods, schemas, status codes.
It is excellent at that, and it is not a discovery mechanism. It has no notion of a
business naming itself, of a conversation across turns, of progress inside a turn,
or of who is allowed to call.

A useful pairing: a manifest's `links` say where the published material is, and a
`link` with `rel: "openapi"` says where the machine-readable description of a
specific integration lives.

## Versus `llms.txt` and similar conventions

They are a polite list of pages. They carry no state, no session, no completion
signal, and no way for a business to answer differently to a machine. They reduce
token cost at the margin; they do not make an integration.

## What makes this different in one sentence

The website is a door for a reader; this is a door for a caller — a named endpoint, a
declarative manifest, and a conversation with an explicit end.
