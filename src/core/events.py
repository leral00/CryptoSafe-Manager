class EventBus:
    def __init__(self):
        self.events = {}

    def subscribe(self, name, func):
        if name not in self.events:
            self.events[name] = []
        self.events[name].append(func)

    def publish(self, name, data=None):
        if name in self.events:
            for func in self.events[name]:
                func(data)
