from collections import defaultdict
import threading
class EventType:
    ENTRY_ADDED = "EntryAdded"
    ENTRY_UPDATED = "EntryUpdated"
    ENTRY_DELETED = "EntryDeleted"

    USER_LOGGED_IN = "UserLoggedIn"
    USER_LOGGED_OUT = "UserLoggedOut"

    CLIPBOARD_COPIED = "ClipboardCopied"
    CLIPBOARD_CLEARED = "ClipboardCleared"

class EventBus:
    def __init__(self):
        self.listeners = defaultdict(list)

    def subscribe(self, event_type: str, callback):
        self.listeners[event_type].append(callback)

    def publish(self, event_type: str, data=None):
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"[EventBus Error] {e}")

    def publish_async(self, event_type: str, data=None):
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                try:
                    thread = threading.Thread(target=callback, args=(data,), daemon=True)
                    thread.start()
                except Exception as e:
                    print(f"[EventBus Async Error] {e}")


class AuditManager:

    def __init__(self, bus: EventBus, db_helper):
        self.bus = bus
        self.db = db_helper
        self._setup_listeners()

    def _setup_listeners(self):
        self.bus.subscribe(EventType.ENTRY_ADDED, self._log_event)
        self.bus.subscribe(EventType.ENTRY_DELETED, self._log_event)
        self.bus.subscribe(EventType.ENTRY_UPDATED, self._log_event)
        self.bus.subscribe(EventType.USER_LOGGED_IN, self._log_event)
        self.bus.subscribe(EventType.CLIPBOARD_COPIED, self._log_event)

    def _log_event(self, data):
        if not self.db:
            print(f"[Audit Stub] DB not ready. Event data: {data}")
            return

        try:
            action = data.get('action', 'UNKNOWN') if isinstance(data, dict) else 'UNKNOWN'
            details = str(data)

            print(f"[Audit] Writing to DB: {action}")
            self.db.execute(
                "INSERT INTO audit_log (action, details) VALUES (?, ?)",
                (action, details)
            )
        except Exception as e:
            print(f"[Audit Error] Failed to write log: {e}")
