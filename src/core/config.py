import json
class ConfigManager:

    def save(self, data):
        with open("config.json", "w") as f:
            json.dump(data, f)

    def load(self):
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except:
            return {}
