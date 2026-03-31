import ui

import keyboard_style


class TagSelectorView(ui.View):
    def __init__(self, tag_context, on_dismiss=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tag_context = tag_context
        self.on_dismiss = on_dismiss
        self.flex = 'WH'
        self.background_color = keyboard_style.OVERLAY_BG

        self.panel = ui.View()
        self.panel.background_color = keyboard_style.PANEL_BG
        self.panel.corner_radius = 18
        self.panel.border_width = 1
        self.panel.border_color = keyboard_style.FG_DARK_GRAY
        self.add_subview(self.panel)

        self.scroll = ui.ScrollView()
        self.scroll.shows_vertical_scroll_indicator = True
        self.panel.add_subview(self.scroll)

        self.title_label = self._make_label('Tag Context', keyboard_style.FONT_SIZE_LARGE)
        self.projects_label = self._make_label('Recent Projects', keyboard_style.FONT_SIZE_SMALL)
        self.tasks_label = self._make_label('Recent Tasks', keyboard_style.FONT_SIZE_SMALL)
        self.priority_label = self._make_label('Priority', keyboard_style.FONT_SIZE_SMALL)
        self.note_label = self._make_label('Note Tag', keyboard_style.FONT_SIZE_SMALL)

        self.priority_control = ui.SegmentedControl()
        self.priority_control.segments = ['Urgent', 'Normal', 'Low']
        self.priority_control.tint_color = keyboard_style.TEAL
        self.priority_control.selected_index = {'urgent': 0, 'normal': 1, 'low': 2}.get(tag_context.current_priority, 1)
        self.priority_control.action = self._priority_changed

        self.note_field = ui.TextField()
        self.note_field.background_color = keyboard_style.DARK_BG_3
        self.note_field.text_color = keyboard_style.FG_WHITE
        self.note_field.tint_color = keyboard_style.TEAL
        self.note_field.corner_radius = 10
        self.note_field.placeholder = 'freeform tag'
        self.note_field.text = tag_context.current_note or ''

        self.clear_button = self._make_button('Clear', self._clear)
        self.done_button = self._make_button('Done', self._done, accent=True)

        self.project_buttons = []
        for name in tag_context.tags.get('recent_projects', []):
            button = self._make_button(name, self._select_project)
            self.project_buttons.append(button)

        self.task_buttons = []
        for name in tag_context.tags.get('recent_tasks', []):
            button = self._make_button(name, self._select_task)
            self.task_buttons.append(button)

        for subview in [
            self.title_label,
            self.projects_label,
            self.tasks_label,
            self.priority_label,
            self.note_label,
            self.priority_control,
            self.note_field,
            self.clear_button,
            self.done_button,
            *self.project_buttons,
            *self.task_buttons,
        ]:
            self.scroll.add_subview(subview)

        self._refresh_button_states()

    def layout(self):
        panel_width = min(max(self.width - 24, 240), 320)
        panel_height = min(max(self.height - 16, 160), 220)
        self.panel.frame = ((self.width - panel_width) / 2.0, (self.height - panel_height) / 2.0, panel_width, panel_height)
        self.scroll.frame = self.panel.bounds

        inset = 16
        width = self.panel.width - (inset * 2)
        y = 16

        self.title_label.frame = (inset, y, width, 28)
        y += 36

        self.projects_label.frame = (inset, y, width, 18)
        y += 22
        y = self._layout_pill_buttons(self.project_buttons, y)

        self.tasks_label.frame = (inset, y, width, 18)
        y += 22
        y = self._layout_pill_buttons(self.task_buttons, y)

        self.priority_label.frame = (inset, y, width, 18)
        y += 22
        self.priority_control.frame = (inset, y, width, 32)
        y += 42

        self.note_label.frame = (inset, y, width, 18)
        y += 22
        self.note_field.frame = (inset, y, width, 36)
        y += 48

        button_width = (width - 10) / 2.0
        self.clear_button.frame = (inset, y, button_width, 38)
        self.done_button.frame = (inset + button_width + 10, y, button_width, 38)
        self.scroll.content_size = (self.scroll.width, y + 52)

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

    def _layout_pill_buttons(self, buttons, start_y):
        inset = 16
        available_width = self.panel.width - (inset * 2)
        x = inset
        y = start_y
        height = 30
        gap = 8
        for button in buttons:
            button_width = max(72, min(available_width, len(button.title) * 8 + 24))
            if x + button_width > inset + available_width:
                x = inset
                y += height + gap
            button.frame = (x, y, button_width, height)
            x += button_width + gap
        return y + height + 12

    def _refresh_button_states(self):
        for button in self.project_buttons:
            selected = button.title == self.tag_context.current_project
            button.background_color = keyboard_style.TEAL if selected else keyboard_style.DARK_BG_3
        for button in self.task_buttons:
            selected = button.title == self.tag_context.current_task
            button.background_color = keyboard_style.TEAL if selected else keyboard_style.DARK_BG_3

    def _make_label(self, text, size):
        label = ui.Label()
        label.text = text
        label.text_color = keyboard_style.FG_WHITE
        label.font = (keyboard_style.FONT_BOLD, size)
        return label

    def _make_button(self, title, action, accent=False):
        button = ui.Button(title=title)
        button.background_color = keyboard_style.TEAL if accent else keyboard_style.DARK_BG_3
        button.tint_color = keyboard_style.FG_WHITE
        button.corner_radius = 10
        button.font = (keyboard_style.FONT_BOLD, keyboard_style.FONT_SIZE_SMALL)
        button.action = action
        return button

    def _select_project(self, sender):
        self.tag_context.set_project(sender.title)
        self._refresh_button_states()

    def _select_task(self, sender):
        self.tag_context.set_task(sender.title)
        self._refresh_button_states()

    def _priority_changed(self, sender):
        mapping = {0: 'urgent', 1: 'normal', 2: 'low'}
        self.tag_context.set_priority(mapping.get(sender.selected_index, 'normal'))

    def _clear(self, sender):
        self.tag_context.set_project(None)
        self.tag_context.set_task(None)
        self.tag_context.set_priority('normal')
        self.tag_context.set_note(None)
        self.note_field.text = ''
        self.priority_control.selected_index = 1
        self._refresh_button_states()

    def _done(self, sender):
        note = (self.note_field.text or '').strip()
        self.tag_context.set_note(note or None)
        self.dismiss()
