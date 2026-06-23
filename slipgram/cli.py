from __future__ import annotations

import argparse
import json
import sys

from .core import transform


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="slipgram")
    subparsers = parser.add_subparsers(dest="command", required=True)

    transform_parser = subparsers.add_parser("transform", help="transform stdin using Slip Grammar")
    transform_parser.add_argument("--json", action="store_true", help="emit full JSON result")
    transform_parser.add_argument("--show-log", action="store_true", help="print transform log after slipped text")
    transform_parser.add_argument("--strict-protect", action="store_true", help="error if protected text is not preserved")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "transform":
        source = sys.stdin.read()
        result = transform(source, strict_protect=args.strict_protect)
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
            return 0

        sys.stdout.write(result.slipped_text)
        if args.show_log:
            if not result.slipped_text.endswith("\n"):
                sys.stdout.write("\n")
            sys.stdout.write("\n# transform_log\n")
            for entry in result.transform_log:
                sys.stdout.write(f"{entry.start}:{entry.end} {entry.original} -> {entry.canonical} [{entry.rule}]\n")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
