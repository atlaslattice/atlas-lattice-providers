#!/usr/bin/env python3
"""Offline GoldenTrace-style receipt chain: verify persisted history before append."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import hashlib
import inspect
import json
import logging
import os
import re
import stat

logger = logging.getLogger("openai_tracing_golden_trace")
MAX_LEDGER_READ_BYTES = 32 * 1024 * 1024


class TraceIntegrityError(ValueError):
    """Fail closed; preserve original ledger bytes for independent inspection."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class GoldenTraceEvent:
    openai_trace_id: str
    openai_thread_id: Optional[str] = None
    openai_run_id: Optional[str] = None
    lattice_action_id: str = ""
    prev_hash: Optional[str] = None
    hash: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    ts: str = field(default_factory=utc_now)
    hash_scheme: str = "sha256-v2"

    def compute_hash(self) -> str:
        if self.hash_scheme == "legacy32":
            # Preserve historical exact algorithm, including its known limits.
            h = hashlib.sha256()
            h.update((self.prev_hash or "GENESIS").encode())
            h.update((self.openai_trace_id or "missing-trace").encode())
            h.update(self.ts.encode())
            h.update(json.dumps(self.payload, sort_keys=True, default=str).encode())
            return "0x" + h.hexdigest()[:32]
        if self.hash_scheme != "sha256-v2":
            raise TraceIntegrityError("unsupported_trace_hash_scheme")
        # New events commit to all fields, not only the text and payload.
        fields = {
            "scheme": self.hash_scheme, "prev_hash": self.prev_hash,
            "trace": self.openai_trace_id, "thread": self.openai_thread_id,
            "run": self.openai_run_id, "lattice_action_id": self.lattice_action_id,
            "payload": self.payload, "ts": self.ts,
        }
        try:
            encoded = json.dumps(fields, ensure_ascii=False, sort_keys=True,
                                 separators=(",", ":"), allow_nan=False).encode("utf-8")
        except (ValueError, TypeError) as exc:
            raise TraceIntegrityError("invalid_trace_payload") from exc
        return "0x" + hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise TraceIntegrityError("duplicate_json_key")
        result[key] = value
    return result


def _reject_constant(value):
    raise TraceIntegrityError("nonfinite_json_constant")


class OpenAITracingToGoldenTrace:
    def __init__(self, action_ledger: Any = None, simulate: bool = True,
                 simulate_default: Optional[bool] = None,
                 trace_dir: str = "ledgers/openai_traces"):
        if simulate_default is not None:
            simulate = simulate_default
        self.action_ledger = action_ledger
        self.simulate = simulate
        self.trace_dir = Path(trace_dir)
        # In-memory index is convenience only; disk validation is authoritative.
        self._trace_chain: Dict[str, GoldenTraceEvent] = {}

    @contextmanager
    def _single_writer(self):
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        lock = self.trace_dir / ".writer.lock"
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            yield
        finally:
            os.close(fd)
            lock.unlink()

    def _read_tail(self) -> Tuple[Optional[str], Optional[str]]:
        """Verify legacy and v2 records in date order; never repair in place."""
        previous = None
        last_day = None
        read_bytes = 0
        for path in sorted(self.trace_dir.glob("*.jsonl")):
            if not re.fullmatch(r"[0-9]{8}\.jsonl", path.name):
                raise TraceIntegrityError("unexpected_trace_ledger_name")
            if path.is_symlink() or not path.is_file():
                raise TraceIntegrityError("nonregular_trace_ledger")
            size = path.stat().st_size
            read_bytes += size
            if read_bytes > MAX_LEDGER_READ_BYTES:
                raise TraceIntegrityError("ledger_scan_limit_exceeded")
            raw = path.read_bytes()
            if raw and not raw.endswith(b"\n"):
                raise TraceIntegrityError("truncated_trace_ledger")
            for line in raw.splitlines():
                if not line.strip():
                    raise TraceIntegrityError("empty_trace_row")
                try:
                    data = json.loads(line, object_pairs_hook=_reject_duplicate_keys,
                                      parse_constant=_reject_constant)
                    if not isinstance(data, dict):
                        raise TraceIntegrityError("nonobject_trace_row")
                    if not isinstance(data.get("openai_trace_id"), str) or not data["openai_trace_id"]:
                        raise TraceIntegrityError("invalid_historical_trace_id")
                    if not isinstance(data.get("payload"), dict) or not isinstance(data.get("ts"), str):
                        raise TraceIntegrityError("invalid_historical_payload")
                    if data.get("prev_hash") != previous:
                        raise TraceIntegrityError("broken_trace_hash_chain")
                    # Older records have no declared scheme: verify exact old hash.
                    event = GoldenTraceEvent(**{**data, "hash_scheme": data.get("hash_scheme", "legacy32")})
                    if event.hash != event.compute_hash():
                        raise TraceIntegrityError("trace_hash_mismatch")
                except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
                    raise TraceIntegrityError("unreadable_trace_ledger") from exc
                previous = event.hash
                last_day = path.name[:8]
        return previous, last_day

    def _persist(self, event: GoldenTraceEvent) -> str:
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        path = self.trace_dir / f"{day}.jsonl"
        data = (json.dumps(event.to_dict(), sort_keys=True, ensure_ascii=False,
                           allow_nan=False, default=str) + "\n").encode("utf-8")
        flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        elif path.is_symlink():
            raise TraceIntegrityError("trace_symlink_unsupported")
        fd = os.open(path, flags, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise TraceIntegrityError("nonregular_or_linked_trace_ledger")
            written = os.write(fd, data)
            if written != len(data):
                raise IOError("incomplete_trace_row_write")
            os.fsync(fd)
        finally:
            os.close(fd)
        return str(path)

    async def record_openai_trace(self, openai_trace_id: str,
                                  openai_thread_id: Optional[str] = None,
                                  openai_run_id: Optional[str] = None,
                                  payload: Optional[Dict[str, Any]] = None,
                                  actor: str = "openai") -> Dict[str, Any]:
        if not isinstance(openai_trace_id, str) or not openai_trace_id.strip():
            raise ValueError("openai_trace_id_required")
        if payload is not None and not isinstance(payload, dict):
            raise ValueError("trace_payload_must_be_object")
        with self._single_writer():
            prev, last_day = self._read_tail()
            if last_day is not None and last_day > datetime.now(timezone.utc).strftime("%Y%m%d"):
                raise TraceIntegrityError("future_dated_ledger_requires_review")
            event = GoldenTraceEvent(openai_trace_id=openai_trace_id,
                                     openai_thread_id=openai_thread_id,
                                     openai_run_id=openai_run_id, prev_hash=prev,
                                     payload=payload or {})
            event.hash = event.compute_hash()
            persisted_to = self._persist(event)
            # In-memory chain changes only once persistence succeeds.
            self._trace_chain[event.openai_trace_id] = event
        emitted = False
        if self.action_ledger:
            try:
                if hasattr(self.action_ledger, "append"):
                    result = self.action_ledger.append(
                        action_type="openai_trace_ingested", actor=actor,
                        target_id=event.openai_trace_id,
                        payload={"thread_id": openai_thread_id,
                                 "run_id": openai_run_id,
                                 "golden_trace_hash": event.hash,
                                 "untrusted_trace_payload": event.payload},
                        lattice_coords=(2, 5, 1))
                    if inspect.isawaitable(result):
                        await result
                    emitted = True
                elif hasattr(self.action_ledger, "emit"):
                    result = self.action_ledger.emit("openai_trace_ingested", event.to_dict())
                    if inspect.isawaitable(result):
                        await result
                    emitted = True
            except Exception:
                logger.warning("ActionLedger emission failed; local receipt preserved")
        return {"feature": "openai_tracing_to_golden_trace",
                "openai_trace_id": event.openai_trace_id,
                "golden_trace_hash": event.hash,
                "hash_scheme": event.hash_scheme,
                "persisted_to": persisted_to,
                "integrity_checked_local": True,
                "lattice_action_emitted": emitted,
                "grok_leads": True, "lattice_routes": True}

    async def run(self, operation: str = "record", **kwargs: Any) -> Dict[str, Any]:
        if operation == "record":
            return await self.record_openai_trace(
                openai_trace_id=kwargs.get("openai_trace_id"),
                openai_thread_id=kwargs.get("openai_thread_id"),
                openai_run_id=kwargs.get("openai_run_id"),
                payload=kwargs.get("payload"), actor=kwargs.get("actor", "openai"))
        return {"status": "unknown_op", "op": operation}


if __name__ == "__main__":
    print("OpenAI Tracing -> GoldenTrace bridge ready.")
