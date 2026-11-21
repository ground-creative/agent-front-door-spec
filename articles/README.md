# Articles

Posts published about this specification live here, in the same repository as the
specification they describe.

## Why here

An article and the specification it explains must not drift apart. Pinning each
article to a spec tag (`spec-v0.3`) and citing requirement IDs means that when the
specification changes, the affected posts are findable:

```bash
grep -rl 'spec-v0.3' articles/
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

## Front matter

```yaml
---
title: A front door for agents
published: 2026-11-21
spec: spec-v0.1
requirements: [MAN-1, PROTO-13, PROTO-27, SEC-6]
canonical: https://example.com/blog/a-front-door-for-agents
---
```

`canonical` is where the post was originally published, if it was. Keeping a copy
here is what makes the drift check possible.

## Ideas worth writing

- _Why agents impersonate browsers_ — the cost of the wrong front door.
- _What a manifest is for_ — one file, and what it changes.
- _Cancellation is not rollback_ — what a protocol can and cannot promise.
- _Reading a spec you did not write_ — the conformance ladder in practice.
