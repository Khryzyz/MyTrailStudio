from __future__ import annotations

import argparse
import sys

from ui_app import APP_NAME, APP_VERSION


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=".\\mts_ui.ps1")
    parser.add_argument("--version", action="store_true", help="Show the UI version and exit.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        print(f"{APP_NAME} UI {APP_VERSION}")
        return 0

    try:
        from ui_app.app import run
    except ModuleNotFoundError as exc:
        if exc.name == "PySide6":
            print("ERROR: PySide6 is not installed. Run: python -m pip install -r requirements-ui.txt", file=sys.stderr)
            return 1
        raise

    return run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
