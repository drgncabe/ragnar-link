from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class StateSource:
    def read(self) -> dict[str, Any]:
        raise NotImplementedError


class JsonFileStateSource(StateSource):
    def __init__(self, path: Path):
        self.path = path

    def read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"ragnar": "unknown", "message": f"missing {self.path}"}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{self.path} must contain a JSON object")
        return data


class CommandStateSource(StateSource):
    def __init__(self, command: list[str], timeout_s: float = 3.0):
        self.command = command
        self.timeout_s = timeout_s

    def read(self) -> dict[str, Any]:
        result = subprocess.run(
            self.command,
            check=True,
            capture_output=True,
            text=True,
            timeout=self.timeout_s,
        )
        data = json.loads(result.stdout)
        if not isinstance(data, dict):
            raise ValueError("state command must emit a JSON object")
        return data


class StaticStateSource(StateSource):
    def __init__(self, state: dict[str, Any]):
        self.state = state

    def read(self) -> dict[str, Any]:
        return dict(self.state)

