# Why DNS SRV, and why not a well-known URL

_Informative._

Both approaches answer "given a domain, where is the thing". They answer different
questions, and the difference matters for how a protocol grows.

## A well-known path answers "where is the document"

Given `example.com`, a client knows to fetch `https://example.com/.well-known/…`.
That is a document-retrieval convention. The document it gets back is authoritative
about the rest: it can point at another host, another port, another protocol, as A2A
Agent Cards do.

This works well when a document is what you need, and it has a real advantage:
it needs nothing but a web server.

## SRV answers "where is the service"

An SRV record names the target host and port for a service at that domain, **before
any HTTP request exists**. That is a routing fact, not a pointer discovered after
fetching something.

```dns
_portico._tcp.example.com. 300 IN SRV 10 5 7777 agent.example.com.
```

It matters because the agent endpoint usually is not the website. Another host,
another port, another transport is a normal deployment, and SRV expresses it
directly. SIP (RFC 3263), XMPP, LDAP and Matrix all use SRV for exactly this.

It also keeps the layers honest:

- DNS routes.
- TLS authenticates the peer.
- The manifest describes what is offered.

A client that follows an SRV target sends the **queried domain** as `ServerName`,
so the certificate at the target has to cover the name the business owns. That is
what binds the endpoint to the business, and it is why the certificate rule in
[`SECURITY.md`](../normative/SECURITY.md) is about the queried name, not the SRV
target.

## What SRV costs

- Operators are less familiar with SRV than with a path.
- Some DNS providers make SRV records awkward to create.
- An SRV record cannot carry the manifest; it only names where to ask.
- It is not registered with IANA under this name, so it is a convention, not a
  standard.

## Why we still chose it

The manifest has to arrive inside an authenticated connection for its claims to be
worth anything, so a document-fetch path would eventually need a second step
anyway. Starting with the routing record means there is one way to find the
endpoint and one way to talk to it, and no second host to keep consistent.

Because the manifest itself is transport-independent
([D-6](../DECISIONS.md)), a deployment that wants a document path can publish the
same object without changing this decision. Discovery is the only thing SRV owns.
