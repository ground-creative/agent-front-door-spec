# Contributing

Thanks for reading. There are four useful things to do here, in order of how much
they help.

## 1. Implement something and report where it hurt

The most valuable contribution is a client, a daemon, or a manifest publisher
written without reading the reference implementation's source. When something is
unclear, that is a defect in the specification, and it is worth an issue.

Open an issue titled `spec: <requirement ID> <what is unclear>` and include:

- the requirement ID (e.g. `PROTO-17`);
- what you expected, what the text says, and what you had to guess;
- the smallest example that shows the ambiguity.

Please do not patch the implementation instead. A workaround in your codebase is
invisible here; a note in an issue is not.

## 2. Publish a manifest

L0 conformance costs one file. Start from
[`machine/examples/manifest.minimal.json`](machine/examples/manifest.minimal.json),
validate against [`machine/schema/manifest.schema.json`](machine/schema/manifest.schema.json),
publish it, and add yourself to [`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md).

If the object cannot express something your business actually does, that is the
most useful finding you can give us.

## 3. Review a proposal

Read [`proposals/`](proposals/). Objections with a requirement ID, a concrete
case, and a suggested alternative are worth more than agreement.

## 4. Improve the fixtures

`machine/fixtures/` is the part that makes conformance checkable. A fixture that
pins down an edge case — a truncated frame, an oversize length, a manifest with an
unknown field, a cancelled turn — is a permanent gift.

## Ground rules

- **Cite requirement IDs** in issues and pull requests. If a change alters
  behaviour, say which `MAN-`, `PROTO-`, `WH-`, `SEC-` or `CONF-` requirement it
  touches.
- **Separate argument from text.** A proposal pull request argues; a follow-up
  pull request edits normative text.
- **No secrets, ever** — not in examples, not in fixtures, not in issue bodies.
- **Be specific about compatibility.** "Additive" and "breaking" are the only two
  categories that matter; say which one you are proposing.
- **Plain text in normative documents.** Tables, requirement IDs, MUST/SHOULD/MAY.
  No marketing.

## Before you push

```bash
pip install jsonschema
python3 machine/check.py
```

That validates every example against the schema, checks the fixture lists against
it, verifies that every requirement ID a fixture cites exists in a normative
index, and that every relative link resolves. CI runs the same script.

## Where things go

| You have | It goes in |
| --- | --- |
| a change to what implementations must do | `normative/` via a proposal |
| reasoning, comparison, explanation | `informative/` |
| a schema change, example, or fixture | `machine/` |
| a published post | `articles/` |
| a new implementation | a row in `IMPLEMENTATIONS.md` |

## Commit hygiene

One change per commit. The subject line says what changed, the body says which
requirement it touches and why. Spec tags are cut by maintainers, not by pull
requests.

## License

By contributing you agree your contribution is licensed under Apache-2.0, as
described in [`LICENSE`](LICENSE).
