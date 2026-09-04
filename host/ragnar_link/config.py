from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Config:
    serial_port: str
    baud: int
    node_name: str
    espnow_channel: int
    state_file: Path | None
    state_command: list[str] | None
    poll_interval_s: float
    heartbeat_interval_s: float


DEFAULT_CONFIG = Config(
    serial_port="auto",
    baud=115200,
    node_name="ragnar",
    espnow_channel=6,
    state_file=Path("/run/ragnar-link/state.json"),
    state_command=None,
    poll_interval_s=1.0,
    heartbeat_interval_s=10.0,
)


def load_config(path: Path) -> Config:
    if not path.exists():
        return DEFAULT_CONFIG

    raw = parse_simple_yaml(path.read_text(encoding="utf-8"))

    return Config(
        serial_port=str(raw.get("serial_port", DEFAULT_CONFIG.serial_port)),
        baud=int(raw.get("baud", DEFAULT_CONFIG.baud)),
        node_name=str(raw.get("node_name", DEFAULT_CONFIG.node_name)),
        espnow_channel=int(raw.get("espnow_channel", DEFAULT_CONFIG.espnow_channel)),
        state_file=_optional_path(raw.get("state_file", DEFAULT_CONFIG.state_file)),
        state_command=_optional_command(raw.get("state_command", DEFAULT_CONFIG.state_command)),
        poll_interval_s=float(raw.get("poll_interval_s", DEFAULT_CONFIG.poll_interval_s)),
        heartbeat_interval_s=float(raw.get("heartbeat_interval_s", DEFAULT_CONFIG.heartbeat_interval_s)),
    )


def _optional_path(value: Any) -> Path | None:
    if value in (None, ""):
        return None
    return Path(str(value))


def _optional_command(value: Any) -> list[str] | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(part) for part in value]
    raise ValueError("state_command must be a string or list")


def parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the small config shape used by Ragnar Link without external deps."""
    result: dict[str, Any] = {}
    current_list_key: str | None = None
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("  - "):
            if current_list_key is None:
                raise ValueError(f"list item without key on line {line_number}")
            result.setdefault(current_list_key, []).append(_parse_scalar(line[4:].strip()))
            continue
        if ":" not in line:
            raise ValueError(f"invalid config line {line_number}: {raw_line!r}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"missing config key on line {line_number}")
        if value == "":
            result[key] = None
            current_list_key = key
        else:
            result[key] = _parse_scalar(value)
            current_list_key = None
    return result


def _parse_scalar(value: str) -> Any:
    if value in ("null", "None", "~"):
        return None
    if value in ("true", "false"):
        return value == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value
