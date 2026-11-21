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

try:
    import jsonschema
except ImportError:  # pragma: no cover - documented requirement
    print(
        "conformance: jsonschema is required (pip install jsonschema)", file=sys.stderr
    )
    raise SystemExit(2)

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC_VERSION = "spec-v0.3"
HEADER = struct.Struct(">IBI")
MAX_PAYLOAD = 8 << 20

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
        ctx.set_alpn_protocols(["vireo/1"])
        if insecure:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        raw = socket.create_connection((host, port), timeout=timeout)
        # The reference identity is the name the caller asked for, which is not
        # necessarily the host being dialled: SRV is routing only (PROTO-47).
        self.sock = ctx.wrap_socket(raw, server_hostname=server_name or host)
        self.sock.settimeout(timeout)

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
        return stream, frame_type, (json.loads(body) if body else None)

    def negotiate(self, client_id: str, protocol: str = "vireo/1") -> None:
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


def digest_of(manifest: dict) -> str:
    """MAN-40: sha256 over canonical JSON with digest and signature removed."""
    body = {k: v for k, v in manifest.items() if k not in ("digest", "signature")}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()


def load_schema() -> dict:
    path = ROOT / "machine" / "schema" / "manifest.schema.json"
    return json.loads(path.read_text())


# --------------------------------------------------------------------------
# L1 — transport, handshake, refusals
# --------------------------------------------------------------------------


def check_transport(host: str, port: int, insecure: bool, server_name: str | None) -> Wire | None:
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
    ok = version == "TLSv1.3" and alpn == "vireo/1"
    record("PROTO-1", ok, f"{version}, ALPN {alpn}")
    return wire


def check_refusals(host: str, port: int, insecure: bool, server_name: str | None) -> None:
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
        except (OSError, ConnectionError, ValueError) as exc:
            record(requirement, False, f"connection: {exc}")
        finally:
            wire.close()


def check_handshake(wire: Wire) -> dict | None:
    try:
        wire.negotiate(new_client_id())
        stream, frame_type, manifest = wire.read()
    except (OSError, ConnectionError, ValueError) as exc:
        record("PROTO-13", False, f"handshake: {exc}")
        return None

    if frame_type != T_MANIFEST:
        record(
            "PROTO-13", False, f"first answer is type 0x{frame_type:02x}, want manifest"
        )
        return None
    record("PROTO-13", True, f"manifest on stream {stream}")

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


def check_manifest(manifest: dict) -> None:
    schema = load_schema()
    try:
        jsonschema.validate(manifest, schema)
        record("MAN-47", True, "manifest validates against the schema")
    except jsonschema.ValidationError as exc:
        record("MAN-47", False, str(exc.message))
        return

    version = manifest.get("manifest_version", "1.0")
    record("MAN-1", True, f"manifest_version {version}")

    digest = manifest.get("digest")
    if not digest:
        record("MAN-40", None, "no digest published")
    else:
        want = digest_of(manifest)
        record(
            "MAN-40",
            digest == want,
            "digest matches" if digest == want else f"got {digest}, want {want}",
        )

    agents = manifest.get("agents") or []
    record("MAN-51", True, f"{len(agents)} agent(s) advertised")

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


def check_sessions(wire: Wire, manifest: dict) -> None:
    ops = (manifest.get("capabilities") or {}).get("session") or {}
    conversational = [a for a in (manifest.get("agents") or []) if a.get("sessions")]
    if not conversational:
        for req in ("MAN-28", "MAN-29", "PROTO-37"):
            record(req, None, "no conversational agent to exercise")
        return

    agent = conversational[0]["name"]

    # MAN-29: if an agent declares sessions, session.new must be available.
    if ops.get("new") is False:
        record(
            "MAN-29",
            False,
            "an agent declares sessions but capabilities.session.new is false",
        )
        return

    status, body = wire.exchange(2, T_SESSION, {"op": "session.new", "agent": agent})
    if status != "end" or not body:
        detail = (body or {}).get("code", status) if isinstance(body, dict) else status
        record("MAN-29", False, f"session.new for {agent} failed: {detail}")
        return
    record("MAN-29", True, f"session.new for {agent}")
    session_id = (body.get("session") or {}).get("id")
    if not session_id:
        record("PROTO-35", False, "session.new returned no id")
        return
    record("PROTO-35", True, "server minted a session id")

    # MAN-28 / PROTO-37: an operation advertised as true must be accepted; one
    # advertised as false must be refused with a documented error. Closing comes
    # last, because it ends the session the earlier probes use.
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


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------


def report(endpoint: str) -> int:
    width = max(len(r) for r, _, _ in RESULTS)
    for requirement, status, detail in RESULTS:
        print(f"{status:4s}  {requirement:{width}s}  {detail}")

    failures = [r for r, s, _ in RESULTS if s == "FAIL"]
    tested = [r for r, s, _ in RESULTS if s in ("PASS", "FAIL")]

    l1 = {"PROTO-1", "PROTO-8", "PROTO-11", "PROTO-12", "PROTO-13", "PROTO-14"}
    l2 = {"MAN-1", "MAN-28", "MAN-29", "MAN-40", "MAN-47", "PROTO-35"}
    l1_ok = l1 <= set(tested)
    l2_ok = l2 <= set(tested)

    if l1_ok and l2_ok and not failures:
        level = "L2"
    elif l1_ok and not failures:
        level = "L1"
    else:
        level = "below L1"

    print()
    print(f"claim: {endpoint} — {level}, {len(failures)} failure(s), {SPEC_VERSION}")
    print("not tested: L3 (progress, cancellation), L4 (retention, restart)")
    return 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe a vireo/1 endpoint against the specification."
    )
    parser.add_argument("--endpoint", required=True, help="host:port of the daemon")
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
    args = parser.parse_args()

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
        manifest = check_handshake(wire)
        if manifest is not None:
            check_manifest(manifest)
            check_sessions(wire, manifest)
    finally:
        wire.close()

    return report(args.endpoint)


if __name__ == "__main__":
    raise SystemExit(main())
