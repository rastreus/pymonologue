import ui

import keyboard_style


class ModesMenuView(ui.View):
    def __init__(self, on_select, on_dismiss=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_select = on_select
        self.on_dismiss = on_dismiss
        self.flex = "WH"
        self.background_color = keyboard_style.OVERLAY_BG

        self.panel = ui.View()
        self.panel.background_color = keyboard_style.PANEL_BG
        self.panel.corner_radius = 16
        self.panel.border_width = 1
        self.panel.border_color = keyboard_style.FG_DARK_GRAY
        self.add_subview(self.panel)

        self.buttons = []
        for title, key in (
            ("Tag Context", "tags"),
            ("Slash Commands", "slash"),
            ("Clear Tags", "clear_tags"),
            ("Close", "close"),
        ):
            button = ui.Button(title=title)
            button.name = key
            button.background_color = keyboard_style.DARK_BG_3
            button.tint_color = keyboard_style.FG_WHITE
            button.corner_radius = 10
            button.font = (keyboard_style.FONT_BOLD, keyboard_style.FONT_SIZE_MEDIUM)
            button.action = self._did_tap
            self.buttons.append(button)
            self.panel.add_subview(button)

    def layout(self):
        width = min(max(self.width - 32, 220), 260)
        height = 18 + len(self.buttons) * 42
        self.panel.frame = (12, 12, width, height)
        y = 10
        for button in self.buttons:
            button.frame = (10, y, self.panel.width - 20, 32)
            y += 42

    def touch_began(self, touch):
        x, y = touch.location
        inside_panel = (
            self.panel.x <= x <= self.panel.x + self.panel.width and
            self.panel.y <= y <= self.panel.y + self.panel.height
        )
        if not inside_panel:
            self.dismiss()

    def dismiss(self):
        self.remove_from_superview()
        if callable(self.on_dismiss):
            self.on_dismiss()

    def _did_tap(self, sender):
        if sender.name == "close":
            self.dismiss()
            return
        if callable(self.on_select):
            self.on_select(sender.name)
        self.dismiss()
