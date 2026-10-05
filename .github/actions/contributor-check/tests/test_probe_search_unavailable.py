"""The credential and cluster probes on an account GitHub search refuses.

Both probes read ``author:`` searches. Their ``_api`` turned every 422 into
``None``, so a refused search read as an empty history and scored NONE, the one
reading that looks clean. A refusal now reports UNKNOWN; any other 422 keeps
its old meaning. Follow-up to agentrust-io/.github#56, raised on #57.
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path
from urllib.error import HTTPError

import pytest

VENDOR = Path(__file__).resolve().parents[1] / "vendor" / "agt"

REFUSED = (
    b'{"message":"Validation Failed","errors":[{"message":"The listed users cannot be '
    b'searched either because the users do not exist or you do not have permission to '
    b'view the users.","resource":"Search","field":"q","code":"invalid"}]}'
)
OTHER_422 = b'{"message":"Validation Failed"}'


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"agt_{name}", VENDOR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class _Resp:
    def __init__(self, payload):
        self._payload = json.dumps(payload).encode()

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _fake_urlopen(search_body: bytes):
    def fake(req, timeout=None):
        url = req.full_url
        if "/search/" in url:
            raise HTTPError(url, 422, "err", {}, io.BytesIO(search_body))
        if url.rstrip("/").endswith("/users/someone"):
            return _Resp({"login": "someone", "created_at": "2014-05-17T06:30:28Z",
                          "public_repos": 0, "followers": 0, "following": 0})
        return _Resp([])
    return fake


@pytest.fixture(params=["credential_audit", "cluster_detect"])
def probe(request, monkeypatch):
    mod = _load(request.param)
    monkeypatch.setattr(mod, "_get_token", lambda: "t")
    return request.param, mod


def _risk(name, mod):
    if name == "credential_audit":
        return mod.audit_credentials("someone", "agentrust-io/.github").risk
    return mod.detect_cluster("someone").risk_level()


def test_refused_search_is_unknown_not_clean(probe, monkeypatch):
    name, mod = probe
    monkeypatch.setattr(mod, "urlopen", _fake_urlopen(REFUSED))
    assert _risk(name, mod) == "UNKNOWN"


def test_other_422_keeps_its_old_reading(probe, monkeypatch):
    name, mod = probe
    monkeypatch.setattr(mod, "urlopen", _fake_urlopen(OTHER_422))
    assert _risk(name, mod) == "NONE"
