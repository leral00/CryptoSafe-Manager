import sys
import time

sys.path.insert(0, '.')
from src.core.events import EventBus, EventType

def test_event_subscribe_and_publish():
    bus = EventBus()
    received = []

    def callback(data):
        received.append(data)

    bus.subscribe(EventType.ENTRY_ADDED, callback)
    bus.publish(EventType.ENTRY_ADDED, "test_data")

    assert len(received) == 1
    assert received[0] == "test_data"

def test_event_async():
    bus = EventBus()
    received = []

    def callback(data):
        received.append(data)

    bus.subscribe(EventType.USER_LOGGED_IN, callback)
    bus.publish_async(EventType.USER_LOGGED_IN, "user_admin")

    time.sleep(0.1)

    assert len(received) == 1
