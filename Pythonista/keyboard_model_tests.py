"""
keyboard_model_tests.py — unit tests for the phase-1 keyboard model.
"""

from keyboard_model import build_keyboard_view_model


def test_recording_model_uses_stop_label_and_keeps_monologue_shell():
    model = build_keyboard_view_model(workflow_state="recording")

    assert model.mode_button_title == "MODES"
    assert model.voice_button_title == "STOP"
    assert model.is_recording is True
    assert model.punctuation_titles == (".", ",", "?", "!", "'", "⌫")
    assert model.bottom_row_titles == ("ABC", "M", "return")


def test_transcribing_model_exposes_status_copy():
    model = build_keyboard_view_model(workflow_state="transcribing", status_text="Transcribing...")

    assert model.voice_button_title == "TRANSCRIBING..."
    assert model.is_busy is True
    assert model.status_text == "Transcribing..."
