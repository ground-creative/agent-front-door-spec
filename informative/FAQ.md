# FAQ

_Informative._ Answers to what reviewers ask first.

## Is this a standard?

No. It is a draft specification, published so that people can implement it and find
what is wrong. Nothing here has been ratified by a standards body, and the
governance section says plainly who decides today — one maintainer, with the stated
intent to hand that over to implementers.

## Why not just use MCP?

MCP connects a host to a tool server that someone already configured. It does not
answer which businesses exist for a domain, how to reach one that is not the
website, or how a conversation with turns is held and ended.

If your host speaks MCP, this specification reaches it through an adapter. If your
runtime can speak this protocol natively, you do not need MCP anywhere in the path.

## Why not an OpenAPI document?

OpenAPI describes operations on an HTTP API. It is not a discovery mechanism, it has
no session, and it cannot say "still working" or "this turn is abandoned". Point a
manifest's `link` at one if you have it — that is what the `openapi` rel is for.

## Why DNS and not a directory?

A directory decides who exists. A domain is already owned, already delegated, and
already maintained by the business, with each zone authoritative for its own
records. Discovery through SRV needs nobody's approval, which is the point.

## Do I need to run a daemon to participate?

No. A manifest is the document a caller receives when it connects, so publishing
one means running something that answers. There is no static-file on-ramp: an
earlier draft defined one and withdrew it, because no document ever defined where
such a file would live and no client could find it. If you want to participate
today you run an endpoint, or you point an existing implementation at a backend
you already have.

What you can do without a daemon is validate the document itself. Capture a
manifest from any endpoint and check it:

```bash
python3 machine/conformance.py --payload captured.json
```

## Does the daemon see my conversations?

No. The daemon routes a turn and keeps an envelope: id, agent, timestamps, summary,
turn count, status. Message text is not stored (D-1, PROTO-36). Whatever answers is
your backend, and the daemon does not know what it is.

## Is the manifest signed?

Not yet. `signature` is reserved and must be `null` in `manifest_version` 1.1, and
signing is listed as an open question with a stated reason. A `digest` is present
and is an integrity check, not authentication — anyone can compute one.

## Do clients verify certificates?

The specification requires it (SEC-6). Earlier reference clients defaulted to
skipping verification for local development, which is exactly the defect this draft
fixes: with verification off the traffic is encrypted but the business is not
identified, and an attacker on the path can impersonate the endpoint.

## What about authentication and authorization?

Out of scope, deliberately. `client.id` is a random identifier used to scope
sessions — it is not a credential, and the spec says so (SEC-11). Anything stronger
belongs above this layer, in the host adapter or the deployment, and the spec
requires that boundary to be documented (SEC-14).

## What if two agents have the same name?

They cannot: `MAN-12` requires unique names within a manifest. Two agents at
different endpoints may share a name, and that is expected — names are scoped to the
endpoint you connected to.

## What happens if a deployment sets `session.list: false`?

Only browsing history is disabled. Creating, reading and closing a session keep
working, because a conversational agent is unusable without them (`MAN-29`,
`PROTO-38`). A manifest that advertised otherwise would be a defect.

## Can an endpoint expose nothing?

Yes. `agents` may be empty (`MAN-7`). A caller must treat that as "this endpoint
answers, but offers nothing right now", not as an error.

## Where do I ask a question?

Open an issue citing the requirement ID. If you are unsure which one, cite the file
and quote the sentence. Ambiguity in the text is a defect and worth reporting even
when you worked around it.
