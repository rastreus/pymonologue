"""
pymonologue_keyboard.py — PyMonologue custom keyboard for Pythonista.

When running inside the Pythonista keyboard, this installs the custom input
view immediately. When run as a normal script inside Pythonista, it presents a
preview harness that exercises the same workflow against a local text pane.
"""

from pathlib import Path
import sys
import tempfile

import keyboard
import ui


_THIS_DIR = Path(__file__).resolve().parent
_UI_DIR = _THIS_DIR / "ui"
if str(_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_UI_DIR))

import auto_dictionary
import context_tags
import keyboard_style
import sound
import speech_recognizer
from keyboard_shell import PhaseOneKeyboardView
from modes_menu import ModesMenuView
from slash_menu import SlashMenuView
from tag_selector import TagSelectorView
from voice_workflow import VoiceWorkflowController


def _documents_path(filename: str) -> str:
    candidate = Path.home() / "Documents" / filename
    if candidate.parent.exists():
        return str(candidate)
    return str(_THIS_DIR / filename)


class PythonistaRecorder:
    def __init__(self):
        self._recorder = None
        self._audio_path = ""

    def start(self, path: str):
        self._audio_path = path
        self._recorder = sound.Recorder(path)
        self._recorder.record()

    def stop(self):
        if self._recorder is None:
            return self._audio_path
        self._recorder.stop()
        self._recorder = None
        return self._audio_path


class KeyboardTextSink:
    def insert(self, text: str):
        if hasattr(keyboard, "play_input_click"):
            keyboard.play_input_click()
        keyboard.insert_text(text)

    def backspace(self):
        if hasattr(keyboard, "play_input_click"):
            keyboard.play_input_click()
        keyboard.backspace()


class PreviewOutputView(ui.View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.background_color = keyboard_style.PANEL_BG
        self.corner_radius = 14

        self.title_label = ui.Label()
        self.title_label.text = "Preview Output"
        self.title_label.text_color = keyboard_style.FG_GRAY
        self.title_label.font = (keyboard_style.FONT_BOLD, keyboard_style.FONT_SIZE_SMALL)
        self.title_label.alignment = ui.ALIGN_CENTER

        self.text_view = ui.TextView()
        self.text_view.background_color = keyboard_style.DARK_BG_2
        self.text_view.text_color = keyboard_style.FG_WHITE
        self.text_view.font = (keyboard_style.FONT_REGULAR, keyboard_style.FONT_SIZE_MEDIUM)
        self.text_view.editable = False

        self.placeholder_label = ui.Label()
        self.placeholder_label.text = "Run the keyboard here without switching apps."
        self.placeholder_label.text_color = keyboard_style.FG_DARK_GRAY
        self.placeholder_label.font = (keyboard_style.FONT_REGULAR, keyboard_style.FONT_SIZE_SMALL)
        self.placeholder_label.alignment = ui.ALIGN_CENTER
        self.placeholder_label.number_of_lines = 0
        self.placeholder_label.touch_enabled = False

        for subview in [self.title_label, self.text_view, self.placeholder_label]:
            self.add_subview(subview)

    def layout(self):
        pad = 10
        self.title_label.frame = (pad, 8, self.width - pad * 2, 16)
        self.text_view.frame = (pad, 30, self.width - pad * 2, self.height - 40)
        self.placeholder_label.frame = (
            self.text_view.x + 8,
            self.text_view.y + 24,
            self.text_view.width - 16,
            40,
        )

    def insert_text(self, text: str):
        self.text_view.text = (self.text_view.text or "") + text
        self._sync_placeholder()

    def backspace(self):
        current = self.text_view.text or ""
        self.text_view.text = current[:-1]
        self._sync_placeholder()

    def clear(self):
        self.text_view.text = ""
        self._sync_placeholder()

    def _sync_placeholder(self):
        self.placeholder_label.hidden = bool(self.text_view.text)


class PreviewTextSink:
    def __init__(self, preview_output: PreviewOutputView):
        self.preview_output = preview_output

    def insert(self, text: str):
        self.preview_output.insert_text(text)

    def backspace(self):
        self.preview_output.backspace()


class DictionaryStore:
    def __init__(self, path: str):
        self.path = path
        self.dictionary = auto_dictionary.load_dictionary(path)

    def process(self, text: str, current_dictionary):
        dictionary = current_dictionary or self.dictionary
        dictionary, suggestions = auto_dictionary.process_transcription(text, dictionary)
        self.dictionary = dictionary
        auto_dictionary.save_dictionary(dictionary, self.path)
        return dictionary, suggestions


class PyMonologueCoordinator:
    def __init__(self, is_keyboard_context: bool):
        self.is_keyboard_context = is_keyboard_context
        self.tag_storage_path = _documents_path(context_tags.DEFAULT_STORAGE_PATH)
        self.dictionary_store = DictionaryStore(_documents_path(auto_dictionary.DEFAULT_DICT_PATH))
        self.tag_context = context_tags.TagContext(
            tags=context_tags.load_tags(self.tag_storage_path)
        )
        self.preview_output = None if is_keyboard_context else PreviewOutputView()
        self.text_sink = KeyboardTextSink() if is_keyboard_context else PreviewTextSink(self.preview_output)
        self.recorder = PythonistaRecorder()
        self.transcriber = speech_recognizer.SpeechRecognizer()
        self.controller = VoiceWorkflowController(
            recorder=self.recorder,
            transcriber=self.transcriber,
            insert_text=self.text_sink.insert,
            audio_path_factory=self._audio_path,
            tag_text=self._prepend_tags,
            process_dictionary=self.dictionary_store.process,
        )
        self.view = PhaseOneKeyboardView(
            self._handle_mode_tap,
            self._handle_voice_tap,
            self._handle_space_tap,
            self._handle_return_tap,
            self._handle_backspace_tap,
            self._handle_punctuation_tap,
            self._handle_abc_tap,
            preview_output_view=self.preview_output,
            initial_model=self.controller.build_view_model(),
            frame=(0, 0, 320, self._view_height()),
        )
        self.view.name = "PyMonologue"

    def install(self):
        if self.is_keyboard_context:
            keyboard.set_view(self.view, mode="expanded")
        else:
            self.view.present("sheet", hide_title_bar=True)

    def _view_height(self):
        if self.is_keyboard_context:
            return keyboard_style.KEYBOARD_HEIGHT
        return keyboard_style.KEYBOARD_HEIGHT + 132

    def _audio_path(self):
        return tempfile.gettempdir() + "/pymonologue_rec.m4a"

    def _prepend_tags(self, text: str) -> str:
        return context_tags.prepend_tags(text, self.tag_context.get_current_tags())

    def _save_tags(self):
        context_tags.save_tags(self.tag_context.tags, self.tag_storage_path)

    def _refresh_view(self):
        self.view.apply_view_model(self.controller.build_view_model())

    def _show_overlay(self, overlay):
        self.view.show_overlay(overlay)

    def _handle_mode_tap(self, sender):
        menu = ModesMenuView(on_select=self._handle_mode_selection, on_dismiss=self.view.clear_overlay)
        self._show_overlay(menu)

    def _handle_mode_selection(self, selection: str):
        if selection == "tags":
            selector = TagSelectorView(self.tag_context, on_dismiss=self._dismiss_tag_selector)
            self._show_overlay(selector)
            return

        if selection == "slash":
            menu = SlashMenuView(on_dismiss=self.view.clear_overlay)
            self._show_overlay(menu)
            return

        if selection == "clear_tags":
            self.tag_context.set_project(None)
            self.tag_context.set_task(None)
            self.tag_context.set_priority("normal")
            self.tag_context.set_note(None)
            self._save_tags()

    def _dismiss_tag_selector(self):
        self._save_tags()
        self.view.clear_overlay()

    @ui.in_background
    def _handle_voice_tap(self, sender):
        if self.controller.state == "idle":
            self.controller.start_recording()
            self._refresh_view()
            return

        if self.controller.state != "recording":
            return

        audio_path = self.controller.stop_recording()
        self._refresh_view()
        try:
            self.controller.complete_transcription(audio_path)
        except Exception as exc:
            self.controller.last_error = str(exc)
        self._refresh_view()

    def _handle_space_tap(self, sender):
        self.text_sink.insert(" ")

    def _handle_return_tap(self, sender):
        self.text_sink.insert("\n")

    def _handle_backspace_tap(self):
        self.text_sink.backspace()

    def _handle_punctuation_tap(self, text: str):
        self.text_sink.insert(text)

    def _handle_abc_tap(self, sender):
        if self.is_keyboard_context:
            keyboard.set_view(None, mode="expanded")
        elif self.preview_output is not None:
            self.preview_output.clear()
            self.controller.last_error = ""
            self._refresh_view()


_is_keyboard_context = keyboard.is_keyboard()
_coordinator = PyMonologueCoordinator(_is_keyboard_context)
_coordinator.install()
