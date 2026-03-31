import ui

import keyboard_style

try:
    import keyboard
except ImportError:
    keyboard = None


class PunctuationRow(ui.View):
    def __init__(self, symbols=None, on_insert=None, on_backspace=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.symbols = list(symbols or (".", ",", "?", "!", "'", "⌫"))
        self.on_insert = on_insert
        self.on_backspace = on_backspace
        self.flex = "W"
        self.background_color = "clear"
        self.buttons = []
        self.set_symbols(self.symbols)

    def set_symbols(self, symbols):
        self.symbols = list(symbols)
        for button in self.buttons:
            button.remove_from_superview()
        self.buttons = []
        for symbol in self.symbols:
            button = ui.Button(title=symbol)
            button.background_color = keyboard_style.DARK_BG_3
            button.tint_color = keyboard_style.FG_WHITE
            button.corner_radius = keyboard_style.BUTTON_RADIUS
            button.font = (keyboard_style.FONT_BOLD, keyboard_style.FONT_SIZE_MEDIUM)
            button.action = self._insert_symbol
            self.buttons.append(button)
            self.add_subview(button)
        self.set_needs_layout()

    def layout(self):
        if not self.buttons:
            return

        gap = 6
        width = max(0, self.width - (gap * (len(self.buttons) - 1))) / len(self.buttons)
        for index, button in enumerate(self.buttons):
            x = index * (width + gap)
            button.frame = (x, 0, width, self.height)

    def _insert_symbol(self, sender):
        if keyboard is not None and hasattr(keyboard, 'play_input_click'):
            keyboard.play_input_click()

        title = sender.title
        if title == "⌫":
            if callable(self.on_backspace):
                self.on_backspace()
            elif keyboard is not None:
                keyboard.backspace()
            return

        if callable(self.on_insert):
            self.on_insert(title)
        elif keyboard is not None:
            keyboard.insert_text(title)
