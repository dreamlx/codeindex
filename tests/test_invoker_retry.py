"""GH #97: in-run retry/backoff for transient AI CLI failures.

`scan-all --ai` is a serial loop; a transient haiku timeout / rate-limit
previously lost that directory for the whole run (recovered only on a manual
re-run). invoke_ai_cli now retries transient failures with exponential backoff,
while permanent failures (config errors, unlabeled non-zero exits) fail fast so
a misconfigured ai_command does not get hammered N× across every directory.

Refusal/punt is NOT in scope here — that is a *successful* invocation with bad
content, classified downstream by enricher.looks_like_refusal.
"""

import subprocess
from unittest.mock import MagicMock, patch

from codeindex.invoker import _is_transient, invoke_ai_cli


def _ok(stdout="# ok"):
    return MagicMock(returncode=0, stdout=stdout, stderr="")


def _fail(returncode=1, stderr="boom"):
    return MagicMock(returncode=returncode, stdout="", stderr=stderr)


class TestIsTransient:
    def test_timeout_is_transient(self):
        assert _is_transient("Command timed out after 120 seconds")

    def test_rate_limit_and_5xx_are_transient(self):
        assert _is_transient("Error: 429 rate limit exceeded")
        assert _is_transient("API error: 529 overloaded_error")
        assert _is_transient("upstream returned 503 Service Unavailable")
        assert _is_transient("connection reset by peer")

    def test_config_and_unlabeled_errors_are_not_transient(self):
        assert not _is_transient("Exit code: 127")          # command not found
        assert not _is_transient("Exit code: 1")            # unlabeled — conservative
        assert not _is_transient("command not found: claude")
        assert not _is_transient("")


class TestRetry:
    def test_retries_transient_timeout_then_succeeds(self):
        with patch("subprocess.run") as run, patch("time.sleep") as sleep:
            run.side_effect = [
                subprocess.TimeoutExpired(cmd="claude", timeout=120),
                subprocess.TimeoutExpired(cmd="claude", timeout=120),
                _ok(),
            ]
            r = invoke_ai_cli('claude -p "{prompt}"', "hi", max_attempts=3, retry_backoff=0)
            assert r.success
            assert run.call_count == 3
            assert sleep.call_count == 2  # slept between the 3 attempts

    def test_retries_transient_5xx_then_succeeds(self):
        with patch("subprocess.run") as run, patch("time.sleep"):
            run.side_effect = [_fail(stderr="529 overloaded_error"), _ok()]
            r = invoke_ai_cli('claude -p "{prompt}"', "hi", max_attempts=3, retry_backoff=0)
            assert r.success
            assert run.call_count == 2

    def test_does_not_retry_config_error(self):
        with patch("subprocess.run") as run, patch("time.sleep"):
            run.return_value = _fail(returncode=127, stderr="command not found: claude")
            r = invoke_ai_cli('claude -p "{prompt}"', "hi", max_attempts=3, retry_backoff=0)
            assert not r.success
            assert run.call_count == 1  # fail fast — don't hammer a misconfig

    def test_does_not_retry_unlabeled_exit(self):
        with patch("subprocess.run") as run, patch("time.sleep"):
            run.return_value = _fail(returncode=1, stderr="")  # error="Exit code: 1"
            r = invoke_ai_cli('claude -p "{prompt}"', "hi", max_attempts=3, retry_backoff=0)
            assert not r.success
            assert run.call_count == 1

    def test_exhausts_retries_on_persistent_transient(self):
        with patch("subprocess.run") as run, patch("time.sleep"):
            run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=120)
            r = invoke_ai_cli('claude -p "{prompt}"', "hi", max_attempts=3, retry_backoff=0)
            assert not r.success
            assert run.call_count == 3

    def test_default_is_single_attempt(self):
        """Default max_attempts=1 preserves existing behavior for all callers."""
        with patch("subprocess.run") as run, patch("time.sleep"):
            run.return_value = _fail(stderr="529 overloaded_error")  # transient
            r = invoke_ai_cli('claude -p "{prompt}"', "hi")  # no max_attempts
            assert not r.success
            assert run.call_count == 1  # no retry unless opted in
