"""GitHub search refusing an account's ``author:`` queries (agentrust-io/.github#56).

The search API answers 422 "The listed users cannot be searched" for some
accounts with public profiles. That is the API declining to answer, so the
check reports the account as undetermined instead of crashing on it.
"""
from __future__ import annotations

import io
from urllib.error import HTTPError

import pytest

from test_api_retry import _http, _load, _seq

REFUSED = (
    b'{"message":"Validation Failed","errors":[{"message":"The listed users cannot be '
    b'searched either because the users do not exist or you do not have permission to '
    b'view the users.","resource":"Search","field":"q","code":"invalid"}]}'
)


def _http_body(code: int, body: bytes) -> HTTPError:
    return HTTPError("https://api.github.com/search/issues", code, "err", {}, io.BytesIO(body))


@pytest.fixture()
def cc(monkeypatch):
    mod = _load()
    monkeypatch.setattr(mod, "_get_token", lambda: "t")
    monkeypatch.setattr(mod.time, "sleep", lambda _s: None)
    return mod


def test_refused_author_search_raises_search_unavailable(cc, monkeypatch):
    _seq(monkeypatch, cc, [_http_body(422, REFUSED)])
    with pytest.raises(cc.SearchUnavailable):
        cc._search_issues("author:someone is:issue")


def test_other_422_is_still_reported_as_itself(cc, monkeypatch):
    _seq(monkeypatch, cc, [_http_body(422, b'{"message":"Validation Failed"}')])
    with pytest.raises(HTTPError) as info:
        cc._search_issues("author:someone is:issue")
    assert not isinstance(info.value, cc.SearchUnavailable)


def test_unretried_status_names_the_request_path(cc, monkeypatch, capsys):
    _seq(monkeypatch, cc, [_http(422)])
    with pytest.raises(HTTPError):
        cc._api("/search/issues", {"q": "author:someone"})
    last = capsys.readouterr().err.strip().splitlines()[-1]
    assert "422" in last and "/search/issues" in last, last


def test_exhausted_server_error_names_the_request_path(cc, monkeypatch, capsys):
    _seq(monkeypatch, cc, [_http(503)])
    with pytest.raises(HTTPError):
        cc._api("/users/someone/repos")
    assert "/users/someone/repos" in capsys.readouterr().err.strip().splitlines()[-1]


def test_account_hidden_from_search_is_unknown_not_scored(cc, monkeypatch):
    def fake_api(path, params=None):
        if path == "/users/someone":
            return {"login": "someone", "created_at": "2014-05-17T06:30:28Z",
                    "public_repos": 3, "followers": 0, "following": 0}
        if path == "/search/issues":
            raise _http_body(422, REFUSED)
        return []

    monkeypatch.setattr(cc, "_api", fake_api)
    report = cc.check_contributor("someone", "agentrust-io/.github")
    assert report.risk == "UNKNOWN"
    assert [s.name for s in report.signals if s.name == "search_unavailable"] == ["search_unavailable"]
