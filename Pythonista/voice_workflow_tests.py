"""
voice_workflow_tests.py — unit tests for the voice workflow controller.
"""

from keyboard_model import build_keyboard_view_model
from voice_workflow import VoiceWorkflowController


class FakeRecorder:
    def __init__(self):
        self.events = []
        self.stop_result = None

    def start(self, path):
        self.events.append(("start", path))

    def stop(self):
        self.events.append(("stop",))
        return self.stop_result


class FakeTranscriber:
    def __init__(self, transcript=""):
        self.transcript = transcript
        self.calls = []

    def transcribe(self, path):
        self.calls.append(path)
        return self.transcript


def test_idle_tap_starts_recording():
    recorder = FakeRecorder()
    transcriber = FakeTranscriber("ignored")
    inserted = []

    controller = VoiceWorkflowController(
        recorder=recorder,
        transcriber=transcriber,
        insert_text=inserted.append,
        audio_path_factory=lambda: "/tmp/test-audio.m4a",
    )

    action = controller.tap_voice_button()

    assert action.kind == "started_recording"
    assert action.audio_path == "/tmp/test-audio.m4a"
    assert controller.state == "recording"
    assert recorder.events == [("start", "/tmp/test-audio.m4a")]
    assert transcriber.calls == []
    assert inserted == []


def test_second_tap_stops_before_transcribing_and_inserts_text():
    recorder = FakeRecorder()
    transcriber = FakeTranscriber("hello world")
    inserted = []
    dictionary_inputs = []

    controller = VoiceWorkflowController(
        recorder=recorder,
        transcriber=transcriber,
        insert_text=inserted.append,
        audio_path_factory=lambda: "/tmp/test-audio.m4a",
        tag_text=lambda text: f"[project:demo] {text}",
        process_dictionary=lambda text, dictionary: (
            {"approved": [], "pending": ["Demo"]},
            ["Demo"],
        ),
        on_dictionary_processed=dictionary_inputs.append,
    )

    controller.tap_voice_button()
    action = controller.tap_voice_button()

    assert action.kind == "inserted_text"
    assert recorder.events == [
        ("start", "/tmp/test-audio.m4a"),
        ("stop",),
    ]
    assert transcriber.calls == ["/tmp/test-audio.m4a"]
    assert inserted == ["[project:demo] Hello world."]
    assert dictionary_inputs == ["Hello world."]
    assert controller.state == "idle"
    assert controller.last_inserted_text == "[project:demo] Hello world."
    assert controller.pending_dictionary == {"approved": [], "pending": ["Demo"]}


def test_stop_uses_returned_audio_path_when_recorder_provides_one():
    recorder = FakeRecorder()
    recorder.stop_result = "/tmp/final-path.m4a"
    transcriber = FakeTranscriber("hello")
    inserted = []

    controller = VoiceWorkflowController(
        recorder=recorder,
        transcriber=transcriber,
        insert_text=inserted.append,
        audio_path_factory=lambda: "/tmp/initial-path.m4a",
    )

    controller.tap_voice_button()
    controller.tap_voice_button()

    assert transcriber.calls == ["/tmp/final-path.m4a"]
    assert inserted == ["Hello."]


def test_empty_transcript_falls_back_to_no_speech_message():
    recorder = FakeRecorder()
    transcriber = FakeTranscriber("")
    inserted = []

    controller = VoiceWorkflowController(
        recorder=recorder,
        transcriber=transcriber,
        insert_text=inserted.append,
        audio_path_factory=lambda: "/tmp/test-audio.m4a",
    )

    controller.tap_voice_button()
    controller.tap_voice_button()

    assert inserted == ["(no speech detected)."]


def test_workflow_view_model_tracks_recording_state():
    controller = VoiceWorkflowController(
        recorder=FakeRecorder(),
        transcriber=FakeTranscriber("hello"),
        insert_text=lambda text: None,
        audio_path_factory=lambda: "/tmp/test-audio.m4a",
    )

    idle_model = controller.build_view_model()
    assert idle_model.voice_button_title == "START MONOLOGUE"
    assert idle_model.mode_button_title == "MODES"

    controller.tap_voice_button()

    recording_model = controller.build_view_model()
    assert recording_model.voice_button_title == "STOP"
    assert recording_model.is_recording is True
    assert recording_model.punctuation_titles == (".", ",", "?", "!", "'", "⌫")


def test_phase_one_keyboard_model_matches_monologue_voice_mode():
    model = build_keyboard_view_model(workflow_state="idle")

    assert model.mode_button_title == "MODES"
    assert model.voice_button_title == "START MONOLOGUE"
    assert model.punctuation_titles == (".", ",", "?", "!", "'", "⌫")
    assert model.bottom_row_titles == ("ABC", "M", "return")
