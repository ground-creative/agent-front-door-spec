# Articles

Posts published about this specification live here, in the same repository as the
specification they describe.

## Why here

An article and the specification it explains must not drift apart. Pinning each
article to a spec tag (`spec-v0.4`) and citing requirement IDs means that when the
specification changes, the affected posts are findable:

```bash
grep -rl 'spec-v0.4' articles/
grep -rl 'PROTO-27'   articles/
```

A post that lives on a blog and links to a moving document teaches the reader
something that may no longer be true.

## Conventions

- One directory per post: `articles/NNNN-short-slug/`.
- `index.md` is the post. Assets sit beside it.
- The front matter names the spec tag and the requirement IDs it relies on.
- If the post describes behaviour the spec has since changed, do not rewrite
  history: add a note at the top saying what changed and when.

## Claims versus premises

The repository is a reference. Anything it asserts should be checkable against it,
or clearly marked as an assumption. That distinction is what keeps an argument
alive when the world moves.

**A claim** is something a reader can verify: a requirement, a frame layout, a
behaviour of the reference implementation, a `dig` answer. These must be true, and
they cite the artefact that makes them true.

**A premise** is a starting point the argument needs, which this repository cannot
prove: that intermediaries optimise for their own revenue, that buyers prefer one
contract over twenty, that a business would rather own its access than rent it.
Premises are legitimate — an argument without them is just a list — but they must
be **stated**, not smuggled in as fact.

```markdown
## Premises

- An intermediary's revenue depends on the traffic it directs, so a layer that
  removes the traffic competes with the intermediary's income. This is a claim
  about incentives, not about any one company's decisions.
- A business that already owns a domain would rather expose its own agents than
  depend on a directory it does not control.
```

Three rules that follow:

1. **State incentives, not events.** "An AI layer that answers inside the search
   box removes the click" is an incentive you can reason about. "Company X removed
   feature Y because of revenue" is a news claim, and this repository cannot hold
   it — it may be wrong tomorrow, and a wrong fact in a durable article costs more
   than the point it scored.
2. **Write so the argument survives its premise.** If the premise fails, the
   conclusion should weaken, not collapse. "If access is rented, it can be
   revoked" stays true whether or not any specific company revokes anything.
3. **No numbers you cannot regenerate.** Statistics from elsewhere are undated the
   moment they are copied. Cite a source and a date, or leave the number out.

A premise section is not a disclaimer. It is the honest boundary of the argument,
and it lets a reader disagree with one assumption without discarding the piece.

## Front matter

```yaml
---
title: A front door for agents
published: 2026-11-21
spec: spec-v0.4
requirements: [MAN-1, PROTO-13, PROTO-27, SEC-6]
canonical: https://example.com/blog/a-front-door-for-agents
---
```

`canonical` is where the post was originally published, if it was. Keeping a copy
here is what makes the drift check possible.

## Ideas worth writing

Ordered by what a reader needs first, not by what is easiest.

**1. The wrong front door** — _written, `0001`_. HTTP and HTML are a door built for
a reader; a caller without eyes pays for it in tokens and impersonates a browser.
Cites `PROTO-13`, `MAN-47`, `SEC-6`.

**2. Rented access and owned access** — _written, `0002`_. The strongest framing from
the field discussions. Access granted by an intermediary is permission that can be withdrawn
without notice; a domain is an asset the business already holds. Premise: an
intermediary's revenue depends on the traffic it directs. Cite `PROTO-44`,
`PROTO-47`.

**3. The fragmentation tax** — _written, `0003`_. Why per-integration contracts do
not compound: each new business is a new client, a new error contract, a new retry
policy. A shared contract is the only thing that amortises. Cite `MAN-43`, `MAN-44`, `PROTO-39`.

**4. What a session buys you** — _written, `0004`_. Explicit completion, progress
that never counts as a turn, and cancellation that admits it is not rollback
(`PROTO-19`, `PROTO-20`, `PROTO-23`, `PROTO-27`). This is the article only this protocol can write, and it
answers the strongest objection: discovery moves the cost from _finding_ to
_understanding_.

**5. The banner is not the service** — why "AI-ready" badges, `llms.txt` files and
marketing pages are not a contract, and what would be: a schema, a version, a
conformance level. Cite `MAN-1`, `MAN-28`, `CONF-1`–`CONF-5`.

**6. You are verifying the wrong name** — a real bug from this project's history.
The client checked the certificate of the host DNS sent it to, not the domain the
caller asked for, so a DNS answer decided which certificate was acceptable. Short,
concrete, and it teaches `SEC-9` better than any normative sentence.

**7. Reading a specification you did not write** — the conformance ladder in
practice: what a level claim is worth, why a partial claim beats a compliance
claim, and how to file an ambiguity.

**8. The artifact an agent actually sees** — the manifest arrives inside the
session, at the moment of use, which is why it cannot go stale the way a published
file does. Cite `MAN-59`, `MAN-42`.

The first four are drafted (`0001`–`0004`). They carry the argument a reader needs
to decide whether to implement anything, and each states its premises instead of
asserting a claim the repository cannot verify.

Next, when a second implementation exists: **5** and **6**, which are about
trusting a contract rather than wanting one.
