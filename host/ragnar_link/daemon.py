from __future__ import annotations

import argparse
import json
import logging
import signal
import sys
import time
from pathlib import Path

from .config import Config, load_config
from .protocol import command_frame, hello_frame, status_frame
from .serial_bridge import SerialBridge
from .state import CommandStateSource, JsonFileStateSource, StateSource, StaticStateSource

LOGGER = logging.getLogger("ragnar-linkd")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ragnar Link ESP-NOW USB bridge daemon")
    parser.add_argument("--config", type=Path, default=Path("/etc/ragnar-link/config.yaml"))
    parser.add_argument("--once", action="store_true", help="send one status frame and exit")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = load_config(args.config)
    stop = StopFlag()
    signal.signal(signal.SIGTERM, stop.set)
    signal.signal(signal.SIGINT, stop.set)

    source = build_state_source(config)
    bridge = SerialBridge(config.serial_port, config.baud)

    sequence = 1
    last_state_json = ""
    last_heartbeat = 0.0

    try:
        bridge.open()
        bridge.send(hello_frame(sequence, config.node_name, config.espnow_channel))
        sequence += 1
        bridge.send(command_frame(sequence, "set_channel", channel=config.espnow_channel))
        sequence += 1

        while not stop.requested:
            bridge.read_available(handle_gateway_frame)
            try:
                state = source.read()
                frame = status_frame(sequence, state)
                state_json = json.dumps(frame.payload, sort_keys=True, separators=(",", ":"))
                now = time.monotonic()
                if state_json != last_state_json or now - last_heartbeat >= config.heartbeat_interval_s:
                    bridge.send(frame)
                    sequence += 1
                    last_state_json = state_json
                    last_heartbeat = now
            except Exception:
                LOGGER.exception("failed to publish Ragnar state")

            if args.once:
                return 0
            time.sleep(config.poll_interval_s)
    finally:
        bridge.close()

    return 0


class StopFlag:
    requested = False

    def set(self, *_args: object) -> None:
        self.requested = True


def build_state_source(config: Config) -> StateSource:
    if config.state_command:
        return CommandStateSource(config.state_command)
    if config.state_file:
        return JsonFileStateSource(config.state_file)
    return StaticStateSource({"ragnar": "unknown"})


def handle_gateway_frame(frame: dict) -> None:
    frame_type = frame.get("type")
    if frame_type == "ack":
        LOGGER.debug("gateway ack seq=%s status=%s", frame.get("seq"), frame.get("status"))
    elif frame_type == "event":
        LOGGER.info("gateway event: %s", frame)
    elif frame_type == "hello":
        LOGGER.info("gateway hello: %s", frame)
    else:
        LOGGER.info("gateway frame: %s", frame)


if __name__ == "__main__":
    sys.exit(main())

