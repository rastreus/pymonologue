"""
speech_recognizer_tests.py — unit tests for the speech bridge's Python logic.
"""

import pytest

import speech_recognizer


def test_request_authorization_skips_block_when_status_is_already_authorized(monkeypatch):
    calls = []

    monkeypatch.setattr(
        speech_recognizer,
        "authorization_status",
        lambda: speech_recognizer.AUTH_STATUS_AUTHORIZED,
    )

    def _should_not_run(timeout):
        calls.append(timeout)
        raise AssertionError("block-based authorization path should not run")

    monkeypatch.setattr(
        speech_recognizer,
        "_request_authorization_via_block",
        _should_not_run,
    )

    status = speech_recognizer.request_authorization()

    assert status == speech_recognizer.AUTH_STATUS_AUTHORIZED
    assert calls == []


def test_request_authorization_uses_block_when_status_is_not_determined(monkeypatch):
    monkeypatch.setattr(
        speech_recognizer,
        "authorization_status",
        lambda: speech_recognizer.AUTH_STATUS_NOT_DETERMINED,
    )
    monkeypatch.setattr(
        speech_recognizer,
        "_request_authorization_via_block",
        lambda timeout: speech_recognizer.AUTH_STATUS_DENIED,
    )

    status = speech_recognizer.request_authorization()

    assert status == speech_recognizer.AUTH_STATUS_DENIED


def test_result_collector_returns_latest_transcription_on_success():
    collector = speech_recognizer._RecognitionResultCollector()

    collector.record_transcription("hello")
    collector.record_transcription("hello world")
    collector.finish(success=True)

    assert collector.wait_for_result(0.01) == "hello world"


def test_result_collector_raises_speech_error_on_failure():
    collector = speech_recognizer._RecognitionResultCollector()

    collector.finish(success=False, error_message="delegate failed")

    with pytest.raises(speech_recognizer.SpeechRecognitionError):
        collector.wait_for_result(0.01)
