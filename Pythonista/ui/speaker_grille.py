import ui

import keyboard_style


class SpeakerGrilleView(ui.View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.background_color = "clear"
        self.touch_enabled = False

    def draw(self):
        dot_size = 6
        gap = 8
        columns = 7
        rows = 3
        total_width = columns * dot_size + (columns - 1) * gap
        total_height = rows * dot_size + (rows - 1) * gap
        start_x = (self.width - total_width) / 2.0
        start_y = (self.height - total_height) / 2.0

        ui.set_color(keyboard_style.FG_DARK_GRAY)
        for row in range(rows):
            for column in range(columns):
                x = start_x + column * (dot_size + gap)
                y = start_y + row * (dot_size + gap)
                ui.Path.oval(x, y, dot_size, dot_size).fill()
