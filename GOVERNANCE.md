# Governance

_Informative, but binding on this repository's process._

## Who decides

Right now: whoever maintains this repository. That is a starting point, not a
governance model, and it is written down here so nobody has to guess.

The stated goal is to hand decision-making to the people who implement the
specification. When there are two or more independent implementations, the
intent is:

1. a maintainer per active implementation;
2. a simple majority on whether a proposal is accepted;
3. a published list of who those maintainers are, in this file.

Until then, treat every decision here as provisional and every objection as
welcome.

## How a change happens

1. **Open a proposal.** Copy [`proposals/0001-template.md`](proposals/0001-template.md),
   number it, open it as a pull request. Do not edit normative text in the same
   pull request as the argument — the argument has to be reviewable on its own.
2. **Review.** The discussion lives on the proposal pull request. Objections must
   cite a requirement ID or a fixture; "I do not like it" is a valid vote but not
   a defect report.
3. **Decide.** Accepted, rejected, or deferred. Every outcome is recorded in the
   proposal file, including the reasons for rejection — rejections are how future
   readers learn what was already considered.
4. **Apply.** Normative edits land after the proposal, with requirement IDs updated
   and the changelog bumped.
5. **Release.** A spec tag (`spec-v0.1`, `spec-v0.2`, `spec-v0.4`) is cut.<!-- spec-version: history -->
   Tags never move.

## What needs a proposal

- any change to a requirement (`MAN-`, `PROTO-`, `WH-`, `SEC-`, `CONF-`);
- any new field, frame type, error code, or conventional value;
- any change to a compatibility rule;
- any change to a conformance level.

## What does not

- typo fixes, link fixes, formatting;
- new examples, new fixtures, new implementation entries;
- new articles under `articles/`;
- clarifying a sentence without changing what it requires.

## Compatibility policy

Additive changes are cheap and expected. Breaking changes are expensive and need
a MAJOR bump with a migration note. The rules are normative in
[`normative/MANIFEST.md`](normative/MANIFEST.md) §4 and
[`normative/PROTOCOL.md`](normative/PROTOCOL.md) §2 — this section only says
that the process enforces them.

## Conflict of interest

An implementation's maintainer voting on a change that benefits only that
implementation should say so in the proposal. Not a veto, just a disclosure.

## Amending this document

Same as any other change: proposal, review, decision. Governance changes are
recorded separately in `DECISIONS.md` so the trail is visible.
