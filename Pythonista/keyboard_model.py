"""
keyboard_model.py — testable phase-1 keyboard view model.

This module freezes the phase-1 UI contract independently from Pythonista's
`ui` module so layout and labels can be refactored without changing behavior.
"""

from dataclasses import dataclass


PUNCTUATION_TITLES = (".", ",", "?", "!", "'", "⌫")
BOTTOM_ROW_TITLES = ("ABC", "M", "return")


@dataclass(frozen=True)
class KeyboardViewModel:
    mode_button_title: str
    voice_button_title: str
    punctuation_titles: tuple[str, ...]
    bottom_row_titles: tuple[str, ...]
    is_recording: bool = False
    is_busy: bool = False
    status_text: str = ""


def build_keyboard_view_model(workflow_state: str, status_text: str = "") -> KeyboardViewModel:
    """
    Map workflow state to the compact Monologue-style keyboard shell.
    """
    if workflow_state == "recording":
        voice_button_title = "STOP"
        is_recording = True
        is_busy = False
    elif workflow_state == "transcribing":
        voice_button_title = "TRANSCRIBING..."
        is_recording = False
        is_busy = True
    else:
        voice_button_title = "START MONOLOGUE"
        is_recording = False
        is_busy = False

    return KeyboardViewModel(
        mode_button_title="MODES",
        voice_button_title=voice_button_title,
        punctuation_titles=PUNCTUATION_TITLES,
        bottom_row_titles=BOTTOM_ROW_TITLES,
        is_recording=is_recording,
        is_busy=is_busy,
        status_text=status_text,
    )
