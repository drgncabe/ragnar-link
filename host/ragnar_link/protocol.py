from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

PROTOCOL_VERSION = 1

STATUS_FIELDS = {
    "ragnar",
    "camera_count",
    "wifi_count",
    "ble_count",
    "gps",
    "capture",
    "uptime_s",
    "message",
}


@dataclass(frozen=True)
class HostFrame:
    type: str
    sequence: int
    payload: dict[str, Any]
    version: int = PROTOCOL_VERSION

    def to_json_line(self) -> bytes:
        body = {
            "v": self.version,
            "type": self.type,
            "seq": self.sequence,
            **self.payload,
        }
        return (json.dumps(body, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")


def parse_json_line(line: bytes | str) -> dict[str, Any]:
    if isinstance(line, bytes):
        line = line.decode("utf-8", errors="replace")
    data = json.loads(line)
    if not isinstance(data, dict):
        raise ValueError("frame must be a JSON object")
    if data.get("v") != PROTOCOL_VERSION:
        raise ValueError(f"unsupported protocol version: {data.get('v')!r}")
    if not isinstance(data.get("type"), str):
        raise ValueError("frame missing string type")
    return data


def hello_frame(sequence: int, node_name: str, channel: int | None = None) -> HostFrame:
    payload: dict[str, Any] = {
        "node": node_name,
        "host_time_ms": int(time.time() * 1000),
    }
    if channel is not None:
        payload["channel"] = channel
    return HostFrame("hello", sequence, payload)


def status_frame(sequence: int, state: dict[str, Any]) -> HostFrame:
    payload = normalize_state(state)
    return HostFrame("status", sequence, payload)


def command_frame(sequence: int, command: str, **kwargs: Any) -> HostFrame:
    payload = {"command": command}
    payload.update(kwargs)
    return HostFrame("command", sequence, payload)


def normalize_state(state: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key in STATUS_FIELDS:
        if key in state:
            normalized[key] = state[key]

    normalized.setdefault("ragnar", "unknown")
    normalized.setdefault("camera_count", 0)
    normalized.setdefault("wifi_count", 0)
    normalized.setdefault("ble_count", 0)
    normalized.setdefault("gps", "unknown")
    normalized.setdefault("capture", "idle")
    normalized.setdefault("uptime_s", 0)

    normalized["camera_count"] = _clamp_u16(normalized["camera_count"])
    normalized["wifi_count"] = _clamp_u16(normalized["wifi_count"])
    normalized["ble_count"] = _clamp_u16(normalized["ble_count"])
    normalized["uptime_s"] = _clamp_u32(normalized["uptime_s"])

    for key in ("ragnar", "gps", "capture"):
        normalized[key] = str(normalized[key]).lower()

    if "message" in normalized:
        normalized["message"] = str(normalized["message"])[:80]

    return normalized


def _clamp_u16(value: Any) -> int:
    return max(0, min(65535, int(value)))


def _clamp_u32(value: Any) -> int:
    return max(0, min(4294967295, int(value)))

