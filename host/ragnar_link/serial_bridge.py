from __future__ import annotations

import logging
import os
from pathlib import Path
import select
import threading
import time
from typing import Callable

from .protocol import HostFrame, parse_json_line

try:
    import termios
    import tty
except ImportError:
    termios = None
    tty = None

LOGGER = logging.getLogger(__name__)


class SerialBridge:
    def __init__(self, port: str, baud: int, timeout_s: float = 0.2, write_timeout_s: float = 2.0):
        self.port = port
        self.baud = baud
        self.timeout_s = timeout_s
        self.write_timeout_s = write_timeout_s
        self._fd: int | None = None
        self._buffer = bytearray()
        self._lock = threading.Lock()

    def open(self) -> None:
        if termios is None or tty is None:
            raise RuntimeError("serial bridge requires Linux/POSIX termios support")
        resolved_port = resolve_serial_port(self.port)
        self._fd = os.open(resolved_port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        attrs = termios.tcgetattr(self._fd)
        tty.setraw(self._fd)
        speed = _termios_speed(self.baud)
        attrs[4] = speed
        attrs[5] = speed
        attrs[2] |= termios.CLOCAL | termios.CREAD
        attrs[2] &= ~termios.CRTSCTS
        termios.tcsetattr(self._fd, termios.TCSANOW, attrs)
        LOGGER.info("opened serial gateway on %s at %s baud", resolved_port, self.baud)

    def close(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

    def send(self, frame: HostFrame) -> None:
        if self._fd is None:
            raise RuntimeError("serial bridge is not open")
        data = frame.to_json_line()
        with self._lock:
            write_all(self._fd, data, self.write_timeout_s)
        LOGGER.debug("host->gateway %s", data.decode("utf-8").rstrip())

    def read_available(self, on_frame: Callable[[dict], None]) -> None:
        if self._fd is None:
            raise RuntimeError("serial bridge is not open")
        ready, _, _ = select.select([self._fd], [], [], 0)
        if not ready:
            return
        try:
            chunk = os.read(self._fd, 4096)
        except BlockingIOError:
            return
        self._buffer.extend(chunk)
        while b"\n" in self._buffer:
            line, _, rest = self._buffer.partition(b"\n")
            self._buffer = bytearray(rest)
            if not line:
                continue
            try:
                frame = parse_json_line(line)
            except Exception as exc:
                LOGGER.warning("discarding invalid gateway frame %r: %s", line, exc)
                continue
            LOGGER.debug("gateway->host %s", line.decode("utf-8", errors="replace").rstrip())
            on_frame(frame)


def _termios_speed(baud: int) -> int:
    speed_name = f"B{baud}"
    if not hasattr(termios, speed_name):
        raise ValueError(f"unsupported baud rate: {baud}")
    return getattr(termios, speed_name)


def write_all(fd: int, data: bytes, timeout_s: float) -> None:
    deadline = time.monotonic() + timeout_s
    view = memoryview(data)
    offset = 0

    while offset < len(data):
        try:
            written = os.write(fd, view[offset:])
            if written == 0:
                raise BlockingIOError("serial write accepted zero bytes")
            offset += written
            continue
        except InterruptedError:
            continue
        except BlockingIOError:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"timed out writing {len(data)} bytes to serial gateway")
            _, writable, _ = select.select([], [fd], [], min(remaining, 0.25))
            if not writable and time.monotonic() >= deadline:
                raise TimeoutError(f"timed out writing {len(data)} bytes to serial gateway")


def resolve_serial_port(port: str) -> str:
    if port != "auto":
        return port

    candidates = []
    candidates.extend(sorted(Path("/dev/serial/by-id").glob("*Espressif*")))
    candidates.extend(sorted(Path("/dev/serial/by-id").glob("*USB_JTAG*")))
    candidates.extend(sorted(Path("/dev").glob("ttyACM*")))
    candidates.extend(sorted(Path("/dev").glob("ttyUSB*")))
    if not candidates:
        raise FileNotFoundError("no ESP32 USB serial device found; set serial_port in /etc/ragnar-link/config.yaml")
    return str(candidates[0])
