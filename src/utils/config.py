import os
import sys
import json
from dotenv import load_dotenv

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # For development, assume we are in src/utils/
        # base_path = project root
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    return os.path.join(base_path, relative_path)

def get_user_data_path(filename):
    """Get path to a writable user data directory (AppData on Windows)."""
    # Use AppData/Roaming for settings/tokens
    if os.name == 'nt':
        base_path = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'jYT Music')
    else:
        base_path = os.path.expanduser('~/.jyt-music')
    
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    
    return os.path.join(base_path, filename)

# Load environment variables from .env file
load_dotenv()

class Config:
    # client_secret.json is a bundled resource
    CLIENT_SECRETS_FILE = os.getenv("CLIENT_SECRETS_FILE", get_resource_path("docs/client_secret.json"))
    # token.json contains sensitive user data, must be in writable AppData
    TOKEN_FILE = os.getenv("TOKEN_FILE", get_user_data_path("token.json"))

config = Config()

class SettingsManager:
    def __init__(self, settings_file=None):
        if settings_file is None:
            self.settings_file = get_user_data_path("settings.json")
        else:
            self.settings_file = settings_file
        self.settings = {
            "shortcuts": {
                "play_pause": "<ctrl>+<shift>+<space>",
                "next_track": "<ctrl>+<shift>+<right>",
                "prev_track": "<ctrl>+<shift>+<left>"
            },
            "local_music_dir": "",
            "download_dir": ""
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
