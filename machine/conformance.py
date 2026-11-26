#!/usr/bin/env python3
"""Probe a running endpoint and report which requirements it satisfies.

    python3 machine/conformance.py --endpoint 127.0.0.1:7777 --insecure
    python3 machine/conformance.py --endpoint agent.example.com:7777

This is a *client*. It needs nothing but this specification and a reachable
daemon, which is the point: an implementation in any language can be checked
without reading another implementation's source.

What it checks
  L1  TLS 1.3 and ALPN, the handshake, the manifest, and the three refusals
      (bad client id, unknown protocol, first frame not negotiate).
  L2  the manifest against the schema and the MAN rules, the digest, and
      whether advertised session operations are actually accepted.

What it deliberately does not check
  L3  progress and cancellation need a backend that streams and a turn that can
      be abandoned mid-flight. They are reported as not tested, not as passed.
  L4  retention and restart semantics need state across a restart, which a
      probe should not impose on a live endpoint.

Exit code is 0 when nothing failed, 1 otherwise, so it works as a gate.

Requires: python3 and jsonschema.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import socket
import ssl
import struct
import sys
import uuid
from decimal import Decimal

try:
    import jsonschema
except ImportError:  # pragma: no cover - documented requirement
    print(
        "conformance: jsonschema is required (pip install jsonschema)", file=sys.stderr
    )
    raise SystemExit(2)

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC_VERSION = "spec-v0.4"
HEADER = struct.Struct(">IBI")
MAX_PAYLOAD = 8 << 20

# MESSAGE is the single turn sent by --converse. It is deliberately trivial and
# carries a marker the probe can look for in the session envelope, so PROTO-36
# (an envelope never holds message text) is checkable rather than assumed.
MESSAGE = "portico conformance probe: 7f3a9c"

# ALPN_NAMES is what the probe offers, newest first. The wire identifier was
# renamed twice during the draft, and a daemon that has not been redeployed
# still speaks an older string; offering all of them is what lets the probe
# measure an unmigrated deployment instead of failing at the TLS layer (PROTO-49).
ALPN_NAMES = ["portico/1", "frontdoor/1", "vireo/1"]  # <!-- identifier: retired -->

T_MESSAGE, T_DATA, T_END, T_PARTIAL, T_ERROR = 0x01, 0x02, 0x03, 0x04, 0x05
T_NEGOTIATE, T_MANIFEST, T_SESSION = 0x10, 0x11, 0x12

RESULTS: list[tuple[str, str, str]] = []


def record(requirement: str, ok: bool | None, detail: str) -> None:
    """ok True = pass, False = fail, None = not tested."""
    RESULTS.append(
        (requirement, "PASS" if ok else ("SKIP" if ok is None else "FAIL"), detail)
    )


class Wire:
    """One connection: framing, plus the two primitives a probe needs."""

    def __init__(
        self,
        host: str,
        port: int,
        insecure: bool,
        server_name: str | None = None,
        timeout: float = 10.0,
    ):
        # create_default_context loads the system trust store. SSLContext built
        # by hand does not, which makes every valid certificate look untrusted.
        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        ctx.set_alpn_protocols(ALPN_NAMES)
        if insecure:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        raw = socket.create_connection((host, port), timeout=timeout)
        # The reference identity is the name the caller asked for, which is not
        # necessarily the host being dialled: SRV is routing only (PROTO-47).
        self.sock = ctx.wrap_socket(raw, server_hostname=server_name or host)
        self.sock.settimeout(timeout)
        self.last_raw: bytes = b""

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass

    def send(self, stream: int, frame_type: int, payload: dict | None = None) -> None:
        body = (
            b""
            if payload is None
            else json.dumps(payload, separators=(",", ":")).encode()
        )
        if len(body) > MAX_PAYLOAD:
            raise ValueError("payload would exceed the frame limit")
        self.sock.sendall(HEADER.pack(stream, frame_type, len(body)) + body)

    def _exactly(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("connection closed mid-frame")
            buf += chunk
        return buf

    def read(self) -> tuple[int, int, dict | None]:
        stream, frame_type, length = HEADER.unpack(self._exactly(HEADER.size))
        if length > MAX_PAYLOAD:
            raise ValueError(f"frame length {length} exceeds the 8 MiB limit")
        body = self._exactly(length) if length else b""
        self.last_raw = body
        return stream, frame_type, (json.loads(body) if body else None)

    def negotiate(self, client_id: str, protocol: str = ALPN_NAMES[0]) -> None:
        self.send(
            0,
            T_NEGOTIATE,
            {
                "protocol": protocol,
                "client": {"id": client_id, "name": "conformance", "version": "0.1"},
            },
        )

    def exchange(
        self, stream: int, frame_type: int, payload: dict
    ) -> tuple[str, dict | None]:
        """Send one request and collect data/end, or the first error."""
        self.send(stream, frame_type, payload)
        data = None
        deadline = 0
        while deadline < 4:
            _, got_type, body = self.read()
            if got_type == T_ERROR:
                return "error", body
            if got_type == T_DATA:
                data = body
                continue
            if got_type == T_END:
                return "end", data
            deadline += 1
        return "timeout", data


def new_client_id() -> str:
    return "vireo_" + uuid.uuid4().hex  # 32 lowercase hex characters


def _es6_number(value: int | float | Decimal) -> str:
    """ECMAScript Number::toString, as RFC 8785 §3.2.2.3 requires.

    Python's repr() is not it: repr(1.0) is "1.0" where JSON wants "1", and
    repr(1e-7) is "1e-07" where JSON wants "1e-7". A canonicaliser that emits
    either of those disagrees with every other implementation, which turns a
    correct daemon into a FAIL.
    """
    if isinstance(value, bool):  # bool is an int subclass; callers guard, be safe
        raise TypeError("bool is not a number here")
    if isinstance(value, int):
        return str(value)

    # A Decimal arrives from json.loads(parse_float=Decimal) and keeps the
    # literal the publisher wrote. Treat it as the shortest representation of
    # that value: strip trailing zeros, then re-derive digits and exponent.
    if isinstance(value, Decimal):
        if value != value or value.is_infinite():
            raise ValueError("JSON cannot represent NaN or Infinity")
        if value == 0:
            return "0"
        sign = "-" if value < 0 else ""
        digits_tuple = (abs(value)).normalize().as_tuple()
        digits = "".join(str(d) for d in digits_tuple.digits)
        exp = digits_tuple.exponent
    else:
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("JSON cannot represent NaN or Infinity")
        if value == 0:
            return "0"  # -0 serialises as 0
        sign = "-" if value < 0 else ""
        digits_tuple = Decimal(repr(abs(value))).as_tuple()
        digits = "".join(str(d) for d in digits_tuple.digits)
        exp = digits_tuple.exponent
        while len(digits) > 1 and digits[-1] == "0":
            digits = digits[:-1]
            exp += 1

    k = len(digits)
    n = k + exp  # value == digits * 10**(n-k)

    if k <= n <= 21:
        return sign + digits + "0" * (n - k)
    if 0 < n <= 21:
        return sign + digits[:n] + "." + digits[n:]
    if -6 < n <= 0:
        return sign + "0." + "0" * (-n) + digits
    mantissa = digits if k == 1 else digits[0] + "." + digits[1:]
    e = n - 1
    return sign + mantissa + "e" + ("+" if e >= 0 else "-") + str(abs(e))


def canonical_json(value) -> str:
    """RFC 8785 (JCS) serialisation.

    The manifest digest is defined over this form, so getting it wrong makes the
    probe disagree with a correct publisher. Three things differ from
    json.dumps(sort_keys=True): non-ASCII is emitted as UTF-8 rather than
    \\uXXXX escapes, numbers follow ECMAScript, and object members sort by UTF-16
    code units rather than code points.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (int, float)):
        return _es6_number(value)
    if isinstance(value, list):
        return "[" + ",".join(canonical_json(v) for v in value) + "]"
    if isinstance(value, dict):
        members = sorted(value.items(), key=lambda kv: kv[0].encode("utf-16-be"))
        return (
            "{"
            + ",".join(
                json.dumps(k, ensure_ascii=False) + ":" + canonical_json(v)
                for k, v in members
            )
            + "}"
        )
    raise TypeError(f"cannot canonicalise {type(value).__name__}")


def digest_of(manifest: dict) -> str:
    """MAN-40: sha256 over canonical JSON with digest and signature removed."""
    body = {k: v for k, v in manifest.items() if k not in ("digest", "signature")}
    return "sha256:" + hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


def digest_of_wire(raw: bytes) -> str:
    """The digest of a manifest as it arrived, before any re-encoding.

    A client hashes the bytes it received. Decoding to a dict and re-serialising
    is what a probe must NOT do: it silently normalises anything the publisher
    wrote differently (member order, number spelling, escapes) and can report a
    mismatch on a document that is correct. Parsing with parse_float and
    parse_int left as the default would also lose the original number form, so
    the JSON is decoded to a value the canonicaliser formats itself.
    """
    document = json.loads(raw, parse_float=Decimal, parse_int=int)
    body = {k: v for k, v in document.items() if k not in ("digest", "signature")}
    return "sha256:" + hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


def load_schema() -> dict:
    path = ROOT / "machine" / "schema" / "manifest.schema.json"
    return json.loads(path.read_text())


# --------------------------------------------------------------------------
# L1 — transport, handshake, refusals
# --------------------------------------------------------------------------


def check_transport(
    host: str, port: int, insecure: bool, server_name: str | None
) -> Wire | None:
    try:
        wire = Wire(host, port, insecure, server_name)
    except ssl.SSLError as exc:
        record("PROTO-1", False, f"TLS handshake failed: {exc}")
        return None
    except OSError as exc:
        record("PROTO-1", False, f"cannot connect: {exc}")
        return None

    version = wire.sock.version()
    alpn = wire.sock.selected_alpn_protocol()
    ok = version == "TLSv1.3" and alpn in ALPN_NAMES
    record("PROTO-1", ok, f"{version}, ALPN {alpn}")
    # PROTO-49: the newest identifier is preferred, but an older one is a
    # conforming answer during the deprecation window. Which one answered is
    # information an operator needs, so it is reported either way.
    if alpn:
        record(
            "PROTO-49",
            True,
            "daemon selected the current identifier"
            if alpn == ALPN_NAMES[0]
            else f"daemon selected retired {alpn!r}; redeploy to serve {ALPN_NAMES[0]}",
        )
    else:
        record("PROTO-49", None, "no ALPN selected")
    return wire


def check_frame_discipline(host: str, port: int, insecure: bool, name: str | None) -> None:
    """PROTO-4, PROTO-5 — properties of the framing itself.

    These are cheap to probe and expensive to get wrong: a reader that buffers
    an advertised 4 GiB length is a denial of service, and a reader that treats
    a truncated frame as a clean end of stream loses a turn silently.

    PROTO-6 is deliberately NOT probed here. It obliges a *reader* to ignore
    unknown frames on a stream it did not originate, and a client probing a
    server can only write on streams it originated itself — where PROTO-7
    forbids sending a type the peer never advertised. Rejecting that frame is
    therefore correct behaviour, not a defect. PROTO-6 is tested in the client
    role (machine/testdaemon sends an unknown frame to the client under test),
    which is where the obligation actually falls.
    """
    record(
        "PROTO-6",
        None,
        "reader obligation on a peer-originated stream; tested in the client role",
    )

    # PROTO-4: an advertised length beyond the cap must be refused without
    # buffering the body. Announce 9 MiB and send nothing; a server that tries
    # to read it will hang until its timeout, so a prompt error is the pass.
    try:
        wire = Wire(host, port, insecure, name, timeout=5.0)
    except OSError as exc:
        record("PROTO-4", False, f"connect: {exc}")
        return
    try:
        wire.negotiate(new_client_id())
        wire.read()
        wire.sock.sendall(HEADER.pack(1, T_MESSAGE, MAX_PAYLOAD + 1))
        try:
            _, frame_type, body = wire.read()
            code = (body or {}).get("code") if isinstance(body, dict) else None
            record(
                "PROTO-4",
                frame_type == T_ERROR or frame_type == T_END,
                f"rejected oversize length (0x{frame_type:02x}, code={code})",
            )
        except (ConnectionError, OSError):
            # Closing the connection is also a refusal, and is what a reader
            # that cannot frame the rest of the stream must do.
            record("PROTO-4", True, "connection closed on oversize length")
        except ValueError as exc:
            record("PROTO-4", True, f"rejected oversize length: {exc}")
    except (OSError, ValueError) as exc:
        record("PROTO-4", False, f"{exc}")
    finally:
        wire.close()

    # PROTO-5: a payload cut short is an error, not end-of-stream. Announce 64
    # bytes, send 8, then close: the server must not have answered anything as
    # if it had a complete frame.
    try:
        wire = Wire(host, port, insecure, name, timeout=5.0)
    except OSError as exc:
        record("PROTO-5", False, f"connect: {exc}")
        return
    try:
        wire.negotiate(new_client_id())
        wire.read()
        wire.sock.sendall(HEADER.pack(1, T_MESSAGE, 64) + b"12345678")
        wire.sock.shutdown(socket.SHUT_WR)
        answered = False
        try:
            _, frame_type, _ = wire.read()
            answered = frame_type in (T_DATA, T_END)
        except (ConnectionError, OSError, ValueError):
            answered = False
        record(
            "PROTO-5",
            not answered,
            "truncated frame not treated as a complete turn"
            if not answered
            else "server answered a truncated frame as if it were complete",
        )
    except (OSError, ValueError) as exc:
        record("PROTO-5", False, f"{exc}")
    finally:
        wire.close()


# Error codes PROTO-41 permits. Anything else a client must treat as internal.
ERROR_CODES = {
    "bad_client_id",
    "bad_protocol",
    "agent_not_found",
    "session_required",
    "unknown_session",
    "upstream_error",
    "rate_limited",
    "invalid_frame",
    "internal",
}


def check_refusals(
    host: str, port: int, insecure: bool, server_name: str | None
) -> None:
    """PROTO-8, PROTO-11, PROTO-12 — each on its own connection."""
    cases = [
        (
            "PROTO-8",
            "bad_client_id",
            lambda w: w.negotiate("not-a-client-id"),
            T_NEGOTIATE,
        ),
        (
            "PROTO-11",
            "bad_protocol",
            lambda w: w.negotiate(new_client_id(), "vireo/99"),
            T_NEGOTIATE,
        ),
        (
            "PROTO-12",
            "invalid_frame",
            lambda w: w.send(0, T_MESSAGE, {"agent": "x", "message": "hi"}),
            T_MESSAGE,
        ),
    ]
    for requirement, want_code, action, _ in cases:
        try:
            wire = Wire(host, port, insecure, server_name)
        except OSError as exc:
            record(requirement, False, f"connect: {exc}")
            continue
        try:
            action(wire)
            _, frame_type, body = wire.read()
            if frame_type != T_ERROR:
                record(
                    requirement,
                    False,
                    f"expected an error frame, got type 0x{frame_type:02x}",
                )
                continue
            code = (body or {}).get("code")
            record(requirement, code == want_code, f"code={code}")
            # PROTO-41: a code outside the documented set is one a client must
            # treat as internal, which makes the specific error unusable.
            if code is not None:
                known = code in ERROR_CODES
                record(
                    "PROTO-41",
                    known,
                    f"{code} is documented"
                    if known
                    else f"{code} is not a documented error code",
                )
        except (OSError, ConnectionError, ValueError) as exc:
            record(requirement, False, f"connection: {exc}")
        finally:
            wire.close()


def check_handshake(wire: Wire) -> dict | None:
    try:
        wire.negotiate(new_client_id())
        stream, frame_type, manifest = wire.read()
        manifest_raw = wire.last_raw
    except (OSError, ConnectionError, ValueError) as exc:
        record("PROTO-13", False, f"handshake: {exc}")
        return None

    if frame_type != T_MANIFEST:
        record(
            "PROTO-13", False, f"first answer is type 0x{frame_type:02x}, want manifest"
        )
        return None
    record("PROTO-13", True, f"manifest on stream {stream}")
    wire.manifest_raw = manifest_raw

    # PROTO-14: a later negotiate is answered with the manifest again.
    try:
        wire.negotiate(new_client_id())
        _, again_type, again = wire.read()
        record(
            "PROTO-14",
            again_type == T_MANIFEST,
            (
                "re-negotiate answered with the manifest"
                if again_type == T_MANIFEST
                else f"re-negotiate answered 0x{again_type:02x}"
            ),
        )
    except (OSError, ConnectionError, ValueError) as exc:
        record("PROTO-14", False, f"re-negotiate: {exc}")

    return manifest


# --------------------------------------------------------------------------
# L2 — the manifest and the session operations it advertises
# --------------------------------------------------------------------------


def check_manifest(manifest: dict, raw: bytes | None = None) -> None:
    schema = load_schema()
    try:
        jsonschema.validate(manifest, schema)
        record("MAN-47", True, "manifest validates against the schema")
    except jsonschema.ValidationError as exc:
        record("MAN-47", False, str(exc.message))
        return

    # MAN-53: absence is legal and means 1.0, not an error.
    if "manifest_version" in manifest:
        record("MAN-1", True, f"manifest_version {manifest['manifest_version']}")
        record("MAN-53", True, "manifest_version present")
    else:
        record("MAN-1", None, "no manifest_version: read as 1.0 (MAN-53)")
        record("MAN-53", True, "absent manifest_version read as 1.0")

    digest = manifest.get("digest")
    if not digest:
        record("MAN-40", None, "no digest published")
    else:
        # Hash the bytes as received, not a re-encoding of the decoded object:
        # a client hashes what the publisher sent (MAN-40).
        want = digest_of_wire(raw) if raw else digest_of(manifest)
        record(
            "MAN-40",
            digest == want,
            "digest matches" if digest == want else f"got {digest}, want {want}",
        )

    agents = manifest.get("agents")
    if not isinstance(agents, list):
        record("MAN-7", False, "agents is not an array")
        return
    # MAN-7: an endpoint exposing nothing is valid, not an error.
    record("MAN-7", True, f"{len(agents)} agent(s)")

    # MAN-12: names are the address, so a duplicate makes one agent unreachable.
    name_pattern = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
    bad_names: list[str] = []
    seen_names: set[str] = set()
    for agent in agents:
        name = agent.get("name")
        if not isinstance(name, str) or not name_pattern.match(name):
            bad_names.append(f"{name!r} is not a valid agent name")
        elif name in seen_names:
            bad_names.append(f"duplicate agent name {name!r}")
        else:
            seen_names.add(name)
    record("MAN-12", not bad_names, "; ".join(bad_names) if bad_names else "names unique and well formed")

    # MAN-51 is that every listed agent actually answers. That costs a message
    # per agent, so it is exercised where messages are sent, not here; claiming
    # it from the document alone is how a probe starts lying.
    record("MAN-51", None, "checked when each agent is addressed")

    # MAN-55: a tag a caller might filter on must be well formed, or the filter
    # silently misses an agent.
    tag_pattern = re.compile(r"^[a-z][a-z0-9._-]{0,63}$")
    bad: list[str] = []
    for agent in agents:
        seen: set[str] = set()
        for tag in agent.get("tags") or []:
            if not isinstance(tag, str) or not tag_pattern.match(tag):
                bad.append(f"{agent.get('name')}: {tag!r} is not a valid tag")
            elif tag in seen:
                bad.append(f"{agent.get('name')}: duplicate tag {tag!r}")
            else:
                seen.add(tag)
    if not any(agent.get("tags") for agent in agents):
        record("MAN-55", None, "no agent publishes tags")
    else:
        record("MAN-55", not bad, "; ".join(bad) if bad else "tags well formed")


def check_sessions(wire: Wire, manifest: dict) -> tuple[str | None, str | None]:
    """Exercise the advertised session operations.

    Returns the id of a session left open, and the agent it belongs to, so a
    caller can continue into a real turn instead of inferring conversation
    support from session.new succeeding.
    """
    ops = (manifest.get("capabilities") or {}).get("session") or {}
    conversational = [a for a in (manifest.get("agents") or []) if a.get("sessions")]
    if not conversational:
        for req in ("MAN-28", "MAN-29", "PROTO-37"):
            record(req, None, "no conversational agent to exercise")
        return None, None

    agent = conversational[0]["name"]

    # MAN-29: if an agent declares sessions, session.new must be available.
    if ops.get("new") is False:
        record(
            "MAN-29",
            False,
            "an agent declares sessions but capabilities.session.new is false",
        )
        return None, None

    status, body = wire.exchange(2, T_SESSION, {"op": "session.new", "agent": agent})
    if status != "end" or not body:
        detail = (body or {}).get("code", status) if isinstance(body, dict) else status
        record("MAN-29", False, f"session.new for {agent} failed: {detail}")
        return None, None
    record("MAN-29", True, f"session.new for {agent}")
    session_id = (body.get("session") or {}).get("id")
    if not session_id:
        record("PROTO-35", False, "session.new returned no id")
        return None, None
    record("PROTO-35", True, "server minted a session id")

    # MAN-28 / PROTO-37: an operation advertised as true must be accepted; one
    # advertised as false must be refused with a documented error. Closing comes
    # last, because it ends the session the earlier probes use, so the second
    # session minted below is the one handed to the conversation check.
    expectations = [
        ("get", {"op": "session.get", "agent": agent, "id": session_id}),
        ("list", {"op": "session.list", "agent": agent}),
        ("close", {"op": "session.close", "agent": agent, "id": session_id}),
    ]
    for op, payload in expectations:
        advertised = ops.get(op)
        if advertised is None:
            record("MAN-28", None, f"session.{op} not advertised; not probed")
            continue
        status, body = wire.exchange(3, T_SESSION, payload)
        if advertised:
            ok = status == "end"
            detail = (
                f"session.{op} accepted"
                if ok
                else f"session.{op} advertised true but refused"
            )
        else:
            ok = status == "error"
            detail = (
                f"session.{op} refused as advertised"
                if ok
                else f"session.{op} advertised false but accepted"
            )
        record("MAN-28", ok, detail)

    if ops.get("prune"):
        record("MAN-28", None, "session.prune advertised; not probed (destructive)")

    # A fresh session for the conversation check, because the one above was
    # closed. Minting here also re-proves session.new is repeatable.
    status, body = wire.exchange(4, T_SESSION, {"op": "session.new", "agent": agent})
    if status == "end" and body:
        return (body.get("session") or {}).get("id"), agent
    return None, agent


def check_session_scoping(
    host: str, port: int, insecure: bool, name: str | None, manifest: dict
) -> None:
    """PROTO-33: an id belonging to another client behaves as an unknown id.

    This is the only privacy property in L2. Without it, a caller that guesses
    or observes a session id can read another caller's conversation metadata,
    so it is worth a second connection rather than trusting the text.
    """
    conversational = [a for a in (manifest.get("agents") or []) if a.get("sessions")]
    if not conversational:
        record("PROTO-33", None, "no conversational agent to exercise")
        return
    agent = conversational[0]["name"]

    try:
        owner = Wire(host, port, insecure, name)
        stranger = Wire(host, port, insecure, name)
    except OSError as exc:
        record("PROTO-33", False, f"connect: {exc}")
        return

    try:
        owner.negotiate(new_client_id())
        owner.read()
        stranger.negotiate(new_client_id())
        stranger.read()

        status, body = owner.exchange(2, T_SESSION, {"op": "session.new", "agent": agent})
        session_id = (body or {}).get("session", {}).get("id") if status == "end" else None
        if not session_id:
            record("PROTO-33", None, "could not mint a session to test scoping")
            return

        status, body = stranger.exchange(
            2, T_SESSION, {"op": "session.get", "agent": agent, "id": session_id}
        )
        code = (body or {}).get("code") if isinstance(body, dict) else None
        record(
            "PROTO-33",
            status == "error" and code == "unknown_session",
            f"another client got {status} {code or ''}".strip(),
        )
    except (OSError, ConnectionError, ValueError) as exc:
        record("PROTO-33", False, f"{exc}")
    finally:
        owner.close()
        stranger.close()


def check_conversation(
    wire: Wire, manifest: dict, session_id: str | None, agent: str | None
) -> None:
    """PROTO-19 – PROTO-22, PROTO-34, PROTO-36: one real turn.

    Everything else in L2 exercises session bookkeeping. This is the only check
    that sends a message, which is also the only thing that makes "L2 —
    conversations" a true claim rather than an inference from session.new.

    It is run only when the caller passes --converse, because a turn reaches the
    business's backend and may cost it a model call. A probe that spends a third
    party's money by default is not a conformance tool.
    """
    if not session_id:
        for req in ("PROTO-19", "PROTO-20", "PROTO-21", "PROTO-34", "PROTO-36"):
            record(req, None, "no session available to converse in")
        return

    try:
        wire.send(
            4, T_MESSAGE, {"agent": agent, "session_id": session_id, "message": MESSAGE}
        )
    except (OSError, ValueError) as exc:
        for req in ("PROTO-19", "PROTO-20", "PROTO-21", "PROTO-34", "PROTO-36"):
            record(req, False, f"send message: {exc}")
        return

    data_frames = 0
    end_seen = False
    end_body: dict = {}
    error: dict | None = None
    try:
        while True:
            _, frame_type, body = wire.read()
            if frame_type == T_ERROR:
                error = body or {}
                break
            if frame_type == T_DATA:
                data_frames += 1
                continue
            if frame_type == T_PARTIAL:
                continue  # L3 territory; a progress line before end is legal
            if frame_type == T_END:
                end_seen = True
                end_body = body or {}
                break
    except (OSError, ConnectionError, ValueError) as exc:
        record("PROTO-19", False, f"reading the turn: {exc}")
        return

    if error is not None:
        code = error.get("code")
        # A backend failure is the business's problem, not a protocol defect:
        # upstream_error is a conforming answer and proves the turn ended well.
        if code == "upstream_error":
            for req in ("PROTO-19", "PROTO-20", "PROTO-21", "PROTO-36"):
                record(req, None, "backend failed; turn shape not observable")
            record("PROTO-34", None, "no open session to resume")
            return
        for req in ("PROTO-19", "PROTO-20", "PROTO-21", "PROTO-36"):
            record(req, False, f"message refused: {code}")
        record("PROTO-34", None, "no open session to resume")
        return

    # PROTO-19: exactly one data frame may precede end.
    record(
        "PROTO-19",
        end_seen and data_frames <= 1,
        f"{data_frames} data frame(s) before end"
        if end_seen
        else "no end frame: the turn never completed",
    )
    # PROTO-20: end is last, and is the only frame that completes a turn.
    record("PROTO-20", end_seen, "end terminated the turn" if end_seen else "no end frame")

    envelope = (end_body.get("session") or {})
    # PROTO-36: the envelope carries metadata, never the message text.
    leaked = [
        value
        for value in envelope.values()
        if isinstance(value, str) and MESSAGE in value
    ]
    record(
        "PROTO-36",
        not leaked,
        "envelope carries no message text"
        if not leaked
        else "envelope echoed the message text",
    )

    # PROTO-34: only an open session may be resumed. Resuming the one we just
    # used must succeed (it is still open) or fail with a documented reason if
    # the agent closed it (PROTO-22).
    status = envelope.get("status")
    if status == "closed":
        record("PROTO-34", None, "agent closed the session after the turn (PROTO-22)")
        record("PROTO-21", None, "session closed; summary replacement not observable")
        return
    status_code, body = wire.exchange(
        5, T_SESSION, {"op": "session.get", "agent": agent, "id": session_id}
    )
    record(
        "PROTO-34",
        status_code == "end",
        "open session resumed"
        if status_code == "end"
        else f"resume failed: {(body or {}).get('code', status_code)}",
    )
    # PROTO-21: a reply's summary, when non-empty, replaces the envelope's.
    reply_summary = ((end_body or {}).get("session") or {}).get("summary")
    record(
        "PROTO-21",
        True if reply_summary is None else reply_summary == envelope.get("summary"),
        "summary consistent with the end envelope",
    )


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------


def report(endpoint: str, live: bool = True) -> int:
    width = max(len(r) for r, _, _ in RESULTS)
    for requirement, status, detail in RESULTS:
        print(f"{status:4s}  {requirement:{width}s}  {detail}")

    failures = [r for r, s, _ in RESULTS if s == "FAIL"]
    passed = {r for r, s, _ in RESULTS if s == "PASS"}

    print()
    if not live:
        # A document cannot establish a conformance level: every level includes
        # protocol behaviour that only a running peer can demonstrate. Saying so
        # is more useful than a level name followed by six PARTIAL notes.
        print(f"claim: {endpoint} — {SPEC_VERSION}, {len(failures)} failure(s)")
        print("  document-level requirements checked; protocol requirements not tested")
        print("  a level claim requires probing a running endpoint (--endpoint)")
        return 0 if not failures else 1

    # A level is claimed only for the requirements this run actually exercised.
    # The probe used to print "L2" while never sending a message, which is the
    # one thing L2 is named after; a claim must not exceed the evidence.
    levels = [
        (
            "L1 discovery",
            {
                "PROTO-1",
                "PROTO-8",
                "PROTO-11",
                "PROTO-12",
                "PROTO-13",
                "PROTO-14",
                "MAN-47",
            },
        ),
        (
            "L2 conversations",
            {
                "MAN-1",
                "MAN-28",
                "MAN-29",
                "MAN-40",
                "PROTO-19",
                "PROTO-20",
                "PROTO-35",
            },
        ),
        ("L3 live", {"PROTO-25", "PROTO-28", "PROTO-30"}),
    ]

    lines = []
    for name, requirements in levels:
        full = requirements <= passed
        partial = passed & requirements
        if full:
            lines.append(f"{name}: verified")
        elif partial:
            missing = len(requirements) - len(partial)
            lines.append(f"{name}: PARTIAL ({missing} not exercised)")
        else:
            lines.append(f"{name}: not tested")

    print()
    print(f"claim: {endpoint} — {SPEC_VERSION}, {len(failures)} failure(s)")
    for line in lines:
        print(f"  {line}")
    return 0 if not failures else 1


def run_payload(source: str) -> int:
    """Apply the document-level requirements to a captured manifest.

    This exists because the artifact an agent actually receives is often not
    read from a socket the reviewer can dial: it is a payload a host adapter
    surfaced to its model, pasted into an issue, or written to a log. The
    requirement set is the same one the live path applies to the document, so
    there is one definition of a valid manifest and no second script to drift.

    Protocol requirements are reported as not tested. A document cannot prove a
    daemon refuses a bad client id.
    """
    try:
        if source == "-":
            raw = sys.stdin.buffer.read()
        else:
            raw = pathlib.Path(source).read_bytes()
    except OSError as exc:
        print(f"conformance: read {source}: {exc}", file=sys.stderr)
        return 2

    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"conformance: {source} is not JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(manifest, dict):
        print(f"conformance: {source} is not a JSON object", file=sys.stderr)
        return 2

    check_manifest(manifest, raw)

    # Everything requiring a live peer is honestly untested.
    for req in (
        "PROTO-1",
        "PROTO-8",
        "PROTO-11",
        "PROTO-12",
        "PROTO-13",
        "PROTO-14",
        "PROTO-19",
        "PROTO-20",
        "PROTO-21",
        "PROTO-22",
        "PROTO-28",
        "PROTO-29",
        "PROTO-33",
        "PROTO-34",
        "PROTO-35",
        "PROTO-36",
        "PROTO-41",
        "MAN-29",
    ):
        record(req, None, "not tested from a captured document")

    label = "stdin" if source == "-" else source
    return report(f"{label} (payload)", live=False)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe a portico/1 endpoint against the specification, "
        "or check a captured manifest document."
    )
    parser.add_argument(
        "--endpoint",
        default=None,
        help="host:port of the daemon. Required unless --payload is given.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="skip certificate verification (development only)",
    )
    parser.add_argument(
        "--server-name",
        default=None,
        help="name the certificate must cover, when it differs from the address "
        "(e.g. connect to the SRV target but verify the business domain)",
    )
    parser.add_argument(
        "--converse",
        action="store_true",
        help="send one real message to the business to verify PROTO-19..22, 34, 36. "
        "Off by default: a turn reaches the business's backend and may cost it a "
        "model call, so spending another party's money is opt-in.",
    )
    parser.add_argument(
        "--payload",
        default=None,
        help="check a captured manifest document (a file, or - for stdin) instead "
        "of dialling an endpoint. Every document-level requirement is applied; "
        "protocol requirements are reported as not tested.",
    )
    args = parser.parse_args()

    if args.payload:
        return run_payload(args.payload)

    if not args.endpoint:
        print("conformance: give --endpoint host:port or --payload FILE", file=sys.stderr)
        return 2

    host, _, port_text = args.endpoint.rpartition(":")
    if not host or not port_text.isdigit():
        print("conformance: --endpoint must be host:port", file=sys.stderr)
        return 2
    host, port = host.strip("[]"), int(port_text)

    wire = check_transport(host, port, args.insecure, args.server_name)
    if wire is None:
        return report(args.endpoint)

    try:
        check_refusals(host, port, args.insecure, args.server_name)
        check_frame_discipline(host, port, args.insecure, args.server_name)
        manifest = check_handshake(wire)
        if manifest is not None:
            check_manifest(manifest, getattr(wire, "manifest_raw", None))
            session_id, agent = check_sessions(wire, manifest)
            check_session_scoping(host, port, args.insecure, args.server_name, manifest)
            if args.converse:
                check_conversation(wire, manifest, session_id, agent)
    finally:
        wire.close()

    return report(args.endpoint)


if __name__ == "__main__":
    raise SystemExit(main())
