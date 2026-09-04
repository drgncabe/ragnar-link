from __future__ import annotations

import argparse
import json
import sys

from .protocol import status_frame


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a Ragnar Link status frame")
    parser.add_argument("state_json", help="Ragnar state JSON object")
    parser.add_argument("--seq", type=int, default=1)
    args = parser.parse_args(argv)

    state = json.loads(args.state_json)
    sys.stdout.buffer.write(status_frame(args.seq, state).to_json_line())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

