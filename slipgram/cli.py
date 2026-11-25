"""Command-line interface for the morphology transform and the lossless codec."""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .codec import decode, encode
from .core import transform


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="slipgram")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    transform_parser = subparsers.add_parser("transform", help="canonicalize stdin with the lossy morphology rules")
    transform_parser.add_argument("--json", action="store_true", help="emit the full JSON result")
    transform_parser.add_argument("--show-log", action="store_true", help="print the transform log after the slipped text")
    transform_parser.add_argument(
        "--strict-protect",
        action="store_true",
        help="error if protected text is not preserved",
    )

    subparsers.add_parser("encode", help="losslessly compress stdin; decode restores it exactly")
    subparsers.add_parser("decode", help="invert an encode stream from stdin")
    subparsers.add_parser("benchmark", help="report compression ratios for the public-domain excerpts")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = args.command
    if command == "transform":
        return _transform(
            json_output=bool(args.json),
            show_log=bool(args.show_log),
            strict_protect=bool(args.strict_protect),
        )
    if command == "encode":
        sys.stdout.write(encode(sys.stdin.read()))
        return 0
    if command == "decode":
        try:
            sys.stdout.write(decode(sys.stdin.read()))
        except ValueError as exc:
            print(f"slipgram: {exc}", file=sys.stderr)
            return 1
        return 0
    if command == "benchmark":
        from .benchmark import main as benchmark_main

        return benchmark_main()
    return 2


def _transform(*, json_output: bool, show_log: bool, strict_protect: bool) -> int:
    source = sys.stdin.read()
    result = transform(source, strict_protect=strict_protect)
    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
        return 0

    sys.stdout.write(result.slipped_text)
    if show_log:
        if not result.slipped_text.endswith("\n"):
            sys.stdout.write("\n")
        sys.stdout.write("\n# transform_log\n")
        for entry in result.transform_log:
            sys.stdout.write(f"{entry.start}:{entry.end} {entry.original} -> {entry.canonical} [{entry.rule}]\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
