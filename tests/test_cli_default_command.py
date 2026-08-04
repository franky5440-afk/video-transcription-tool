#!/usr/bin/env python3
"""
Test default command resolution in cli.py without starting a server.

Covers the D1 / D3 / D4 contract on argument parsing only:
  1. no arguments                -> parsed command is "serve"
  2. `mp4 <path>`                -> command stays "mp4" (not defaulted to serve)
  3. unknown subcommand          -> parsing fails via SystemExit with code != 0
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cli


def parse(argv):
    """Parse argv through the real parser. No defaulting happens here."""
    return cli.build_parser().parse_args(argv)


def test_no_args_defaults_to_serve():
    """Drive cli.main() itself.

    Reimplementing the defaulting here would make this pass even with the
    defaulting deleted from cli.main(), so the empty argv goes through the real
    entry point with cmd_serve stubbed out to keep a server from starting.
    """
    print("\n=== Case 1: no arguments defaults to serve ===")

    original_serve = cli.cmd_serve
    original_argv = sys.argv
    seen = {}

    def fake_serve(args):
        seen["command"] = args.command
        return 0

    cli.cmd_serve = fake_serve
    sys.argv = ["video-transcription-tool.AppImage"]
    try:
        cli.main()
    except SystemExit as exc:
        seen["exit"] = exc.code
    finally:
        cli.cmd_serve = original_serve
        sys.argv = original_argv

    print(f"reached serve = {'command' in seen}, exit = {seen.get('exit')!r}")
    if seen.get("command") != "serve":
        print("FAIL: main() did not dispatch to serve on an empty argv")
        return False
    if seen.get("exit") != 0:
        print(f"FAIL: expected exit 0, got {seen.get('exit')!r}")
        return False
    print("PASS: main() dispatches to serve when given no arguments")
    return True


def test_mp4_not_defaulted_to_serve():
    print("\n=== Case 2: 'mp4 <path>' keeps command 'mp4' ===")
    args = parse(["mp4", "some/file.mp4"])
    print(f"parsed command = {args.command!r}, input = {args.input!r}")
    if args.command != "mp4":
        print("FAIL: expected command 'mp4', got altered by defaulting")
        return False
    if args.input != "some/file.mp4":
        print("FAIL: expected input position preserved")
        return False
    print("PASS: mp4 subcommand preserved")
    return True


def test_unknown_subcommand_rejects():
    print("\n=== Case 3: unknown subcommand raises SystemExit with code != 0 ===")
    try:
        parse(["bogus"])
    except SystemExit as e:
        print(f"caught SystemExit, code = {e.code!r}")
        if e.code == 0:
            print("FAIL: SystemExit code must be non-zero")
            return False
        print("PASS: unknown subcommand rejected with non-zero exit")
        return True
    print("FAIL: expected SystemExit for unknown subcommand")
    return False


def main():
    print("Testing cli default-command resolution (no server, no network)...")

    tests = [
        test_no_args_defaults_to_serve,
        test_mp4_not_defaulted_to_serve,
        test_unknown_subcommand_rejects,
    ]

    passed = []
    failed = []
    not_tested = []

    for test in tests:
        try:
            result = test()
            if result == "NOT_TESTED":
                not_tested.append(test.__name__)
            elif result:
                passed.append(test.__name__)
            else:
                failed.append(test.__name__)
        except Exception as e:
            print(f"Exception in {test.__name__}: {e}")
            failed.append(test.__name__)

    print(f"\n=== Test Results ===")
    print(f"PASSED: {len(passed)}/{len(tests)}")
    for name in passed:
        print(f"  PASS {name}")
    print(f"FAILED: {len(failed)}/{len(tests)}")
    for name in failed:
        print(f"  FAIL {name}")
    print(f"NOT TESTED: {len(not_tested)}/{len(tests)}")
    for name in not_tested:
        print(f"  NOT TESTED {name}")

    if failed:
        print("FAIL: some tests failed")
        return 1
    print("PASS: all executed tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())