# Fixtures

Language-neutral test vectors. An implementation in any language should be able to
consume these without reading another implementation's source.

| File | What it pins down |
| --- | --- |
| `frames.json` | frame encoding and decoding, including error cases |
| `handshake.json` | the frames of a `negotiate` → `manifest` exchange |
| `manifests.invalid.json` | documents that must be rejected, and why |
| `webhook.json` | backend request/response pairs, plain and NDJSON |

## Reading a fixture

Frame fixtures give the header fields explicitly and the payload as JSON. The `hex`
field is the complete frame, so a test can compare bytes rather than parse.

```json
{
  "name": "negotiate-on-stream-0",
  "stream_id": 0,
  "type": "negotiate",
  "type_code": 16,
  "payload": "{\"protocol\":\"vireo/1\"}",
  "hex": "0000000010000000167b2270726f746f636f6c223a22766972656f2f31227d"
}
```

`hex` is authoritative. If `payload` and `hex` ever disagree, `hex` wins and the
fixture is buggy — report it.

## Expected outcomes

- `frames.json` entries with `"expect"` are tests: `"accept"` means decode then
  re-encode to the same bytes; `"reject"` means a conforming reader must refuse the
  frame, and `"error"` names the documented reason.
- `manifests.invalid.json` entries name the requirement that is violated.
- `webhook.json` entries have `request` and `response` halves; NDJSON fixtures carry
  the expected sequence of `partial` frames.

## Adding a fixture

Prefer the smallest case that fails without the rule. A fixture that only restates
the happy path is less useful than one that isolates a boundary: zero-length payload,
exactly 8 MiB, 8 MiB + 1, a payload cut mid-frame, an unknown frame type, an unknown
manifest member.

Any fixture added here is consumed by every implementation's conformance test. That
is the point: the same bytes, checked by different code.
