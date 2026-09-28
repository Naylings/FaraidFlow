import flet as ft


class FakeStorage:
    """In-memory stand-in for ft.SharedPreferences (async get/set)."""

    def __init__(self):
        self.data = {}

    async def get(self, key, default=None):
        return self.data.get(key, default)

    async def set(self, key, value):
        self.data[key] = value


class FakePage:
    """Minimal stand-in for ft.Page — only the parts HomePage uses."""

    def __init__(self):
        self.controls = []
        self.appbar = None
        self.dialogs = []
        # Below TWO_PANE_MIN_WIDTH (992), so the default in tests is stacked mode.
        self.width = 800

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self, *controls):
        pass

    def clean(self):
        self.controls.clear()

    def show_dialog(self, dialog):
        if dialog in self.dialogs:
            raise RuntimeError("Dialog is already opened")
        self.dialogs.append(dialog)

    def pop_dialog(self):
        if self.dialogs:
            self.dialogs.pop()