import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    CLIENT_SECRETS_FILE = os.getenv("CLIENT_SECRETS_FILE", "docs/client_secret.json")
    TOKEN_FILE = os.getenv("TOKEN_FILE", "token.json")

config = Config()

class SettingsManager:
    def __init__(self, settings_file="settings.json"):
        self.settings_file = settings_file
        self.settings = {
            "shortcuts": {
                "play_pause": "<ctrl>+<shift>+<space>",
                "next_track": "<ctrl>+<shift>+<right>",
                "prev_track": "<ctrl>+<shift>+<left>"
            },
            "local_music_dir": ""
        }
        self.load()

    def load(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    data = json.load(f)
                    self._update_dict(self.settings, data)
            except Exception as e:
                print(f"Error loading settings: {e}")
        else:
            self.save()

    def save(self):
        try:
            with open(self.settings_file, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def _update_dict(self, target, source):
        for k, v in source.items():
            if isinstance(v, dict):
                target[k] = self._update_dict(target.get(k, {}), v)
            else:
                target[k] = v
        return target

    def get_shortcut(self, action):
        return self.settings["shortcuts"].get(action, "")

    def set_shortcut(self, action, hotkey):
        self.settings["shortcuts"][action] = hotkey

settings_manager = SettingsManager()
