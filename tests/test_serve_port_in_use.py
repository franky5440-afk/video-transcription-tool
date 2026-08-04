#!/usr/bin/env python3
"""
Test the port-in-use handling in webui.server without starting a real server.

Covers contracts E1-E7 / T1-T6:
  T1 _is_our_server: 200 + body contains OUR_TITLE_MARKER        -> True
  T2 _is_our_server: 200 + body without marker                   -> False
  T3 _is_our_server: connection refused / timeout (stub raises)  -> False, never raises
  T4 serve(): _is_our_server True  -> no make_server, opens browser, returns
  T5 serve(): _is_our_server True  + open_browser=False -> no make_server, no browser
  T6 serve(): _is_our_server False -> make_server (stub) is called

Every HTTP/network/browser interaction is replaced by a stub, so nothing real
is started or opened.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import webui.server as server_mod


class FakeResp:
    """Stand-in for the urllib response used inside the `with urlopen(...)`."""

    def __init__(self, status, body):
        self.status = status
        self._body = body if isinstance(body, bytes) else body.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._body


class FakeBrowser:
    def __init__(self):
        self.opened = []

    def open(self, url, *args, **kwargs):
        self.opened.append(url)


class FakeServer:
    """Stand-in for the object make_server returns; serve_forever returns at once."""

    def serve_forever(self):
        return None

    def shutdown(self):
        return None


def stub(attr, value):
    """Swap a webui.server global for a test double and return the restore fn."""
    previous = getattr(server_mod, attr)
    setattr(server_mod, attr, value)
    return lambda: setattr(server_mod, attr, previous)


def test_t1_marker_present():
    print("\n=== T1: 200 + body contains OUR_TITLE_MARKER -> True ===")
    restore = stub("urlopen", lambda *a, **k: FakeResp(200, f"<html>{server_mod.OUR_TITLE_MARKER}</html>"))
    try:
        result = server_mod._is_our_server(8713)
    finally:
        restore()
    print(f"result = {result!r}")
    if result is not True:
        print("FAIL: expected True when the body contains the marker and status is 200")
        return False
    print("PASS: marker + 200 identified as our own server")
    return True


def test_t2_marker_absent():
    print("\n=== T2: 200 + body without marker -> False ===")
    restore = stub("urlopen", lambda *a, **k: FakeResp(200, "<html>something else</html>"))
    try:
        result = server_mod._is_our_server(8713)
    finally:
        restore()
    print(f"result = {result!r}")
    if result is not False:
        print("FAIL: expected False when another program answers 200 without the marker")
        return False
    print("PASS: 200 without marker treated as not our server")
    return True


def test_t3_connection_error_returns_false_without_raising():
    print("\n=== T3: connection refused/timeout -> False, no exception escapes ===")

    def raising_urlopen(*a, **k):
        raise ConnectionRefusedError("refused")

    restore = stub("urlopen", raising_urlopen)
    try:
        result = server_mod._is_our_server(8713)
        raised = False
    except Exception as exc:
        result = None
        raised = exc
    finally:
        restore()
    print(f"result = {result!r}, raised = {raised!r}")
    if raised is not False:
        print(f"FAIL: _is_our_server must not propagate exceptions (got {raised!r})")
        return False
    if result is not False:
        print("FAIL: expected False on a connection error")
        return False
    print("PASS: connection error swallowed, returns False")
    return True


def _run_serve(open_browser, is_ours):
    """Drive serve() with all side effects stubbed, return a record dict."""
    fake_browser = FakeBrowser()
    calls = {"make_server": 0}
    record = {"make_server_called": 0, "browser_opened": 0, "returned": False}

    def fake_make_server(*a, **k):
        calls["make_server"] += 1
        return FakeServer()

    restore_is = stub("_is_our_server", lambda port: is_ours)
    restore_ms = stub("make_server", fake_make_server)
    restore_browser = stub("webbrowser", fake_browser)
    try:
        server_mod.serve(8713, open_browser=open_browser, output="./output")
    finally:
        record["make_server_called"] = calls["make_server"]
        record["browser_opened"] = len(fake_browser.opened)
        record["returned"] = True
        restore_is()
        restore_ms()
        restore_browser()
    return record


def test_t4_serve_our_server_true():
    print("\n=== T4: serve() with _is_our_server True -> no make_server, browser opened ===")
    record = _run_serve(open_browser=True, is_ours=True)
    print(f"record = {record!r}")
    if record["make_server_called"] != 0:
        print("FAIL: make_server must not be called when our server is already running")
        return False
    if record["browser_opened"] != 1:
        print("FAIL: expected exactly one webbrowser.open call when open_browser=True")
        return False
    if not record["returned"]:
        print("FAIL: serve() should return normally (exit 0) instead of starting a server")
        return False
    print("PASS: already-running branch reopens the browser and returns without a server")
    return True


def test_t5_serve_our_server_true_no_browser():
    print("\n=== T5: serve() already-running + open_browser=False -> no make_server, no browser ===")
    record = _run_serve(open_browser=False, is_ours=True)
    print(f"record = {record!r}")
    if record["make_server_called"] != 0:
        print("FAIL: make_server must not be called when our server is already running")
        return False
    if record["browser_opened"] != 0:
        print("FAIL: expected no browser to open when open_browser=False")
        return False
    if not record["returned"]:
        print("FAIL: serve() should return normally in the already-running branch")
        return False
    print("PASS: already-running branch honours open_browser=False and starts nothing")
    return True


def test_t6_serve_normal_path():
    print("\n=== T6: serve() with _is_our_server False -> make_server is called ===")
    record = _run_serve(open_browser=False, is_ours=False)
    print(f"record = {record!r}")
    if record["make_server_called"] != 1:
        print("FAIL: make_server should be reached once on the normal start path")
        return False
    if record["browser_opened"] != 0:
        print("FAIL: no browser should open with open_browser=False")
        return False
    print("PASS: normal start path still calls make_server")
    return True


def main():
    print("Testing serve() port-in-use handling (no real server, no network, no browser)...")

    tests = [
        test_t1_marker_present,
        test_t2_marker_absent,
        test_t3_connection_error_returns_false_without_raising,
        test_t4_serve_our_server_true,
        test_t5_serve_our_server_true_no_browser,
        test_t6_serve_normal_path,
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