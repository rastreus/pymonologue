import ui

import keyboard_style


class VoiceButton(ui.View):
    def __init__(self, action=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.action = action
        self.is_recording = False
        self.is_busy = False
        self.flex = "WH"
        self.background_color = keyboard_style.DARK_BG_2
        self.corner_radius = keyboard_style.VOICE_BUTTON_RADIUS
        self.tint_color = keyboard_style.TEAL

        self.button = ui.Button()
        self.button.flex = "WH"
        self.button.background_color = keyboard_style.TEAL
        self.button.tint_color = keyboard_style.FG_WHITE
        self.button.corner_radius = keyboard_style.VOICE_BUTTON_RADIUS
        self.button.action = self._did_tap
        self.add_subview(self.button)

        self.icon_label = ui.Label()
        self.icon_label.text = "🎤"
        self.icon_label.text_color = keyboard_style.FG_WHITE
        self.icon_label.alignment = ui.ALIGN_CENTER
        self.icon_label.font = (keyboard_style.FONT_REGULAR, keyboard_style.FONT_SIZE_LARGE)
        self.icon_label.touch_enabled = False
        self.add_subview(self.icon_label)

        self.title_label = ui.Label()
        self.title_label.text_color = keyboard_style.VOICE_TEXT
        self.title_label.alignment = ui.ALIGN_CENTER
        self.title_label.font = (keyboard_style.FONT_BOLD, keyboard_style.FONT_SIZE_VOICE)
        self.title_label.touch_enabled = False
        self.add_subview(self.title_label)

        self.apply_view_model(type("ViewModel", (), {
            "voice_button_title": "START MONOLOGUE",
            "is_recording": False,
            "is_busy": False,
        })())

    def layout(self):
        self.button.frame = self.bounds.inset(2, 2)
        self.icon_label.frame = (12, 0, 32, self.height)
        self.title_label.frame = (36, 0, self.width - 48, self.height)

    def apply_view_model(self, model):
        self.is_recording = model.is_recording
        self.is_busy = model.is_busy
        self.tint_color = keyboard_style.RECORDING_RED if model.is_recording else keyboard_style.TEAL
        self.button.background_color = keyboard_style.BUSY_BG if model.is_busy else self.tint_color
        self.title_label.text = model.voice_button_title
        self.title_label.text_color = keyboard_style.FG_WHITE if model.is_busy else keyboard_style.VOICE_TEXT
        self.icon_label.alpha = 0.0 if model.is_busy else 1.0
        self.button.enabled = not model.is_busy
        if model.is_recording:
            self._pulse_out()
        else:
            self.button.transform = ui.Transform.identity()

    def _did_tap(self, sender):
        if callable(self.action):
            self.action(self)

    def _pulse_out(self):
        if not self.is_recording:
            self.button.transform = ui.Transform.identity()
            return

        ui.animate(
            lambda: setattr(self.button, 'transform', ui.Transform.scale(1.03, 1.03)),
            duration=keyboard_style.PULSE_INTERVAL / 2.0,
            completion=self._pulse_in,
        )

    def _pulse_in(self):
        if not self.is_recording:
            self.button.transform = ui.Transform.identity()
            return

        ui.animate(
            lambda: setattr(self.button, 'transform', ui.Transform.identity()),
            duration=keyboard_style.PULSE_INTERVAL / 2.0,
            completion=self._pulse_out,
        )
