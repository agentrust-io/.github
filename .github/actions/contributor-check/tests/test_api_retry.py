"""Regression tests for the bounded retry in vendor/agt/contributor_check.py `_api`.

Covers agentrust-io/.github#27 item 1. The rule under test: retry transient
failures within a bound, and report everything else as itself. A 404 is an
answer. A rate limit that outlasts the bound is still a rate limit.
"""
from __future__ import annotations

import importlib.util
import io
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

VENDOR = Path(__file__).resolve().parents[1] / "vendor" / "agt"


def _load():
    spec = importlib.util.spec_from_file_location(
        "agt_contributor_check", VENDOR / "contributor_check.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def cc(monkeypatch):
    mod = _load()
    monkeypatch.setattr(mod, "_get_token", lambda: "t")
    monkeypatch.setattr(mod.time, "sleep", lambda _s: None)
    return mod


class _Resp:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _http(code: int, headers: dict | None = None) -> HTTPError:
    return HTTPError("https://api.github.com/x", code, "err", headers or {}, None)


def _seq(monkeypatch, cc, outcomes):
    """urlopen that yields each outcome in turn; raises if an exception."""
    calls = {"n": 0}

    def fake(_req, timeout=None):
        i = calls["n"]
        calls["n"] += 1
        out = outcomes[min(i, len(outcomes) - 1)]
        if isinstance(out, Exception):
            raise out
        return _Resp(out)

    monkeypatch.setattr(cc, "urlopen", fake)
    return calls


def test_5xx_retries_then_succeeds(cc, monkeypatch):
    calls = _seq(monkeypatch, cc, [_http(502), _http(502), b'{"ok":1}'])
    assert cc._api("/x") == {"ok": 1}
    assert calls["n"] == 3


def test_urlerror_retries_then_succeeds(cc, monkeypatch):
    calls = _seq(monkeypatch, cc, [URLError("timed out"), b'{"ok":1}'])
    assert cc._api("/x") == {"ok": 1}
    assert calls["n"] == 2


def test_404_returns_none_without_retrying(cc, monkeypatch):
    calls = _seq(monkeypatch, cc, [_http(404)])
    assert cc._api("/x") is None
    assert calls["n"] == 1, "a 404 is an answer and must not be retried"


def test_rate_limit_exhausted_reports_as_a_rate_limit(cc, monkeypatch, capsys):
    calls = _seq(monkeypatch, cc, [_http(403, {"Retry-After": "7"})])
    with pytest.raises(HTTPError):
        cc._api("/x")
    assert calls["n"] == cc._RETRY_MAX_ATTEMPTS
    last = capsys.readouterr().err.strip().splitlines()[-1]
    # Must be the final cause line, not one of the "waiting Ns..." lines that
    # also contain "Rate limited". contributor_check_action.py reports the last
    # stderr line, so that line is what a maintainer sees.
    assert "still limited after" in last, (
        f"last stderr line must name the exhausted rate limit, got {last!r}"
    )


def test_server_error_exhausted_reports_as_a_server_error(cc, monkeypatch, capsys):
    calls = _seq(monkeypatch, cc, [_http(503)])
    with pytest.raises(HTTPError):
        cc._api("/x")
    assert calls["n"] == cc._RETRY_MAX_ATTEMPTS
    last = capsys.readouterr().err.strip().splitlines()[-1]
    assert "503" in last and "attempts" in last


def test_network_error_exhausted_reports_as_a_network_error(cc, monkeypatch, capsys):
    calls = _seq(monkeypatch, cc, [URLError("dns failure")])
    with pytest.raises(URLError):
        cc._api("/x")
    assert calls["n"] == cc._RETRY_MAX_ATTEMPTS
    last = capsys.readouterr().err.strip().splitlines()[-1]
    # Not just "Network error": the per-attempt "retrying in Xs..." lines say
    # that too, so a bare substring check passes even with the final line gone.
    assert "on all" in last and str(cc._RETRY_MAX_ATTEMPTS) in last, (
        f"last stderr line must name the exhausted network error, got {last!r}"
    )


def test_other_http_status_raises_on_first_attempt(cc, monkeypatch):
    calls = _seq(monkeypatch, cc, [_http(422)])
    with pytest.raises(HTTPError):
        cc._api("/x")
    assert calls["n"] == 1, "a 422 is the API answering and must not be retried"


def test_backoff_is_bounded_and_jittered(cc):
    for attempt in range(cc._RETRY_MAX_ATTEMPTS):
        for _ in range(50):
            s = cc._retry_sleep_seconds(attempt)
            assert 0 <= s <= cc._RETRY_MAX_SLEEP_SECONDS


def test_backoff_cap_binds_above_the_curve(cc):
    # Across the attempts the loop actually uses, the raw curve stays under the
    # cap, so those attempts cannot show whether the cap is applied at all.
    # Exercise it at an attempt where it has to bite.
    attempt = 30
    assert cc._RETRY_BASE_SECONDS * (2 ** attempt) > cc._RETRY_MAX_SLEEP_SECONDS
    for _ in range(200):
        assert cc._retry_sleep_seconds(attempt) <= cc._RETRY_MAX_SLEEP_SECONDS


def test_backoff_is_not_a_constant(cc):
    # Full jitter, so a fleet of runners hitting the same limit does not retry
    # in lockstep. A fixed attempt must not return one value.
    assert len({cc._retry_sleep_seconds(2) for _ in range(50)}) > 1
