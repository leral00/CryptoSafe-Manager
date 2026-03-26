from datetime import datetime

class StateManager:
    def __init__(self):
        self._state = {
            'session_user': None,
            'login_time': None,
            'last_activity': None,
            'failed_attempts': 0  
        }

    def start_session(self, username: str):
        self._state['session_user'] = username
        self._state['login_time'] = datetime.now()
        self._state['last_activity'] = datetime.now()

    def update_activity(self):
        self._state['last_activity'] = datetime.now()

    def record_failed_attempt(self):
        self._state['failed_attempts'] += 1

    def reset_failed_attempts(self):
        self._state['failed_attempts'] = 0

    def get_failed_attempts(self) -> int:
        return self._state['failed_attempts']

    def get_session_info(self) -> dict:
        return self._state
