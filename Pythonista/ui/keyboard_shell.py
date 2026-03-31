import ui

import keyboard_style
from punctuation_row import PunctuationRow
from speaker_grille import SpeakerGrilleView
from voice_button import VoiceButton


class PhaseOneKeyboardView(ui.View):
    def __init__(
        self,
        on_mode_tap,
        on_voice_tap,
        on_space_tap,
        on_return_tap,
        on_backspace_tap,
        on_punctuation_tap,
        on_abc_tap,
        preview_output_view=None,
        initial_model=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.flex = "WH"
        self.background_color = keyboard_style.DARK_BG
        self.corner_radius = keyboard_style.SHELL_CORNER_RADIUS
        self.preview_output_view = preview_output_view
        self.active_overlay = None

        if self.preview_output_view is not None:
            self.add_subview(self.preview_output_view)

        self.mode_button = self._make_button("MODES", on_mode_tap)
        self.mode_button.font = (keyboard_style.FONT_BOLD, keyboard_style.FONT_SIZE_SMALL)

        self.speaker_grille = SpeakerGrilleView()

        self.voice_button = VoiceButton(action=on_voice_tap)

        self.punctuation_row = PunctuationRow(
            symbols=(".", ",", "?", "!", "'", "⌫"),
            on_insert=on_punctuation_tap,
            on_backspace=on_backspace_tap,
        )

        self.abc_button = self._make_button("ABC", on_abc_tap)
        self.space_button = self._make_button("M", on_space_tap)
        self.return_button = self._make_button("return", on_return_tap, accent=True)

        self.status_label = ui.Label()
        self.status_label.text_color = keyboard_style.FG_GRAY
        self.status_label.alignment = ui.ALIGN_CENTER
        self.status_label.font = (keyboard_style.FONT_REGULAR, keyboard_style.FONT_SIZE_SMALL)

        for subview in [
            self.mode_button,
            self.speaker_grille,
            self.voice_button,
            self.punctuation_row,
            self.abc_button,
            self.space_button,
            self.return_button,
            self.status_label,
        ]:
            self.add_subview(subview)

        if initial_model is not None:
            self.apply_view_model(initial_model)

    def layout(self):
        w = self.width or 320
        h = self.height or keyboard_style.KEYBOARD_HEIGHT
        pad = keyboard_style.SHELL_PADDING

        if self.preview_output_view is not None:
            self.preview_output_view.frame = (0, 0, w, max(96, h * 0.32))
            shell_top = self.preview_output_view.height + 12
            shell_height = h - shell_top
            shell_bounds = (0, shell_top, w, shell_height)
        else:
            shell_top = 0
            shell_height = h
            shell_bounds = (0, 0, w, h)

        shell_x, shell_y, shell_w, shell_h = shell_bounds

        self.mode_button.frame = (shell_x + pad, shell_y + 12, 68, 32)
        self.speaker_grille.frame = (shell_x + (shell_w - 96) / 2.0, shell_y + 12, 96, 32)

        voice_x = shell_x + pad
        voice_y = shell_y + 52
        voice_w = shell_w - (pad * 2)
        voice_h = min(72, max(58, shell_h * 0.24))
        self.voice_button.frame = (voice_x, voice_y, voice_w, voice_h)

        punct_y = voice_y + voice_h + 12
        punct_h = 38
        self.punctuation_row.frame = (voice_x, punct_y, voice_w, punct_h)

        row_y = punct_y + punct_h + 8
        row_h = 38
        abc_w = 54
        return_w = 80
        gap = 8
        self.abc_button.frame = (voice_x, row_y, abc_w, row_h)
        self.return_button.frame = (shell_x + shell_w - pad - return_w, row_y, return_w, row_h)
        space_x = voice_x + abc_w + gap
        space_w = self.return_button.x - gap - space_x
        self.space_button.frame = (space_x, row_y, space_w, row_h)

        self.status_label.frame = (voice_x, row_y + row_h + 2, voice_w, 16)

        if self.active_overlay is not None:
            self.active_overlay.frame = self.bounds

    def apply_view_model(self, model):
        self.mode_button.title = model.mode_button_title
        self.voice_button.apply_view_model(model)
        self.punctuation_row.set_symbols(model.punctuation_titles)
        self.abc_button.title, self.space_button.title, self.return_button.title = model.bottom_row_titles
        self.status_label.text = model.status_text

    def show_overlay(self, overlay):
        if self.active_overlay is not None:
            self.active_overlay.remove_from_superview()
        self.active_overlay = overlay
        overlay.frame = self.bounds
        overlay.flex = "WH"
        self.add_subview(overlay)
        self.bring_to_front(overlay)

    def clear_overlay(self):
        self.active_overlay = None

    def _make_button(self, title, action, accent=False):
        button = ui.Button(title=title)
        button.background_color = keyboard_style.RETURN_BG if accent else keyboard_style.DARK_BG_3
        button.tint_color = keyboard_style.FG_WHITE
        button.corner_radius = keyboard_style.BUTTON_RADIUS
        button.font = (keyboard_style.FONT_BOLD, keyboard_style.FONT_SIZE_MEDIUM)
        button.action = action
        return button
