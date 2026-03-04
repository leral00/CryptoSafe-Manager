import time

class StateManager:

    def __init__(self):
        self._is_locked = True
        self._current_user = None
        self._clipboard_content = None
        self._clipboard_timestamp = 0
        self._last_activity_time = time.time()

    def lock(self):
        self._is_locked = True
        self._current_user = None
        self._clipboard_content = None

    def unlock(self, username: str):
        self._is_locked = False
        self._current_user = username
        self.reset_inactivity_timer()

    @property
    def is_locked(self) -> bool:
        return self._is_locked

    @property
    def current_user(self) -> str:
        return self._current_user

    def set_clipboard(self, content: str):

        self._clipboard_content = content
        self._clipboard_timestamp = time.time()

    def get_clipboard(self) -> str:
        return self._clipboard_content

    def get_clipboard_age(self) -> float:
        if not self._clipboard_content:
            return 0
        return time.time() - self._clipboard_timestamp

    def reset_inactivity_timer(self):
        self._last_activity_time = time.time()

    def get_inactive_seconds(self) -> float:
        return time.time() - self._last_activity_time
