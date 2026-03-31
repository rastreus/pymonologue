"""
voice_workflow.py — pure-python voice workflow controller.

The goal is to keep the Pythonista-specific keyboard code as thin as possible.
This controller owns the Phase 1 state machine so it can be tested on Mac.
"""

from dataclasses import dataclass
from typing import Callable, Optional

import text_normalizer
from keyboard_model import KeyboardViewModel, build_keyboard_view_model


@dataclass(frozen=True)
class VoiceWorkflowAction:
    kind: str
    audio_path: str = ""
    text: str = ""


class VoiceWorkflowController:
    """
    State machine for the tap-to-talk workflow.

    `recorder`, `transcriber`, and `insert_text` are adapter seams that keep the
    orchestration logic testable outside Pythonista.
    """

    def __init__(
        self,
        recorder,
        transcriber,
        insert_text: Callable[[str], None],
        audio_path_factory: Callable[[], str],
        *,
        normalize_text: Callable[[str], str] = text_normalizer.normalize,
        tag_text: Optional[Callable[[str], str]] = None,
        process_dictionary: Optional[Callable[[str, Optional[dict]], tuple[dict, list[str]]]] = None,
        on_dictionary_processed: Optional[Callable[[str], None]] = None,
    ):
        self.recorder = recorder
        self.transcriber = transcriber
        self.insert_text = insert_text
        self.audio_path_factory = audio_path_factory
        self.normalize_text = normalize_text
        self.tag_text = tag_text or (lambda text: text)
        self.process_dictionary = process_dictionary or (lambda text, dictionary: (dictionary or {}, []))
        self.on_dictionary_processed = on_dictionary_processed

        self.state = "idle"
        self.last_audio_path = ""
        self.last_error = ""
        self.last_inserted_text = ""
        self.pending_dictionary: Optional[dict] = None
        self.last_suggestions: list[str] = []

    def tap_voice_button(self) -> VoiceWorkflowAction:
        if self.state == "idle":
            return self.start_recording()
        if self.state == "recording":
            audio_path = self.stop_recording()
            return self.complete_transcription(audio_path)
        raise RuntimeError(f"voice workflow is busy: {self.state}")

    def build_view_model(self) -> KeyboardViewModel:
        return build_keyboard_view_model(self.state, status_text=self._status_text())

    def _status_text(self) -> str:
        if self.state == "recording":
            return "Listening..."
        if self.state == "transcribing":
            return "Transcribing..."
        return self.last_error

    def start_recording(self) -> VoiceWorkflowAction:
        audio_path = self.audio_path_factory()
        self.recorder.start(audio_path)
        self.last_audio_path = audio_path
        self.last_error = ""
        self.state = "recording"
        return VoiceWorkflowAction(kind="started_recording", audio_path=audio_path)

    def stop_recording(self) -> str:
        if self.state != "recording":
            raise RuntimeError(f"cannot stop recording from state: {self.state}")

        self.state = "transcribing"
        stopped_path = self.recorder.stop()
        return stopped_path or self.last_audio_path

    def complete_transcription(self, audio_path: str) -> VoiceWorkflowAction:
        if self.state != "transcribing":
            raise RuntimeError(f"cannot complete transcription from state: {self.state}")

        try:
            raw_text = self.transcriber.transcribe(audio_path)
            if not raw_text:
                raw_text = "(no speech detected)"

            cleaned_text = self.normalize_text(raw_text)
            if self.on_dictionary_processed is not None:
                self.on_dictionary_processed(cleaned_text)

            self.pending_dictionary, self.last_suggestions = self.process_dictionary(
                cleaned_text,
                self.pending_dictionary,
            )
            final_text = self.tag_text(cleaned_text)
            self.insert_text(final_text)

            self.last_inserted_text = final_text
            self.last_error = ""
            self.state = "idle"
            return VoiceWorkflowAction(kind="inserted_text", audio_path=audio_path, text=final_text)
        except Exception as exc:
            self.last_error = str(exc)
            self.state = "idle"
            raise
