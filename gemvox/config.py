import json
import os
import shutil
import sys
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

CONFIG_SCHEMA_VERSION = 2


def _get_app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _get_user_appdata_dir() -> Path:
    """Return persistent OS user configuration directory (%APPDATA%\\Gemvox or ~/.gemvox)."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Gemvox"
    return Path.home() / ".gemvox"


def _resolve_paths():
    base_dir = _get_app_base_dir()
    portable_marker = base_dir / "portable.txt"
    portable_config = base_dir / "config.json"

    user_appdata_dir = _get_user_appdata_dir()
    user_appdata_config = user_appdata_dir / "config.json"

    legacy_home_dir = Path.home() / ".gemvox"
    legacy_home_config = legacy_home_dir / "config.json"

    # 1. Explicit Portable Mode (when portable.txt or local config.json already exists in app folder)
    if portable_marker.exists() or portable_config.exists():
        return base_dir, portable_config, base_dir / "output", True

    # 2. Persistent Standard Mode (%APPDATA%\Gemvox) so updates / new EXE replacements
    #    never wipe out the user's saved settings, custom voices, or custom styles.
    return user_appdata_dir, user_appdata_config, base_dir / "output", False


CONFIG_DIR, CONFIG_FILE, DEFAULT_OUTPUT_DIR, IS_PORTABLE_MODE = _resolve_paths()

DEFAULT_CONFIG = {
    "config_version": CONFIG_SCHEMA_VERSION,
    "language": "en",
    "first_run_completed": False,
    "api_key": "",
    "default_model": "gemini-2.5-flash-preview-tts",
    "default_voice": "Kore",
    "default_style": "cheerful and friendly",
    "output_dir": "",
    "speech_announcements": True,
    "sound_cues": True,
    "autoplay": True,
    "streaming": False,
    "player_volume": 100,
    "player_speed": 1.0,
    "player_loop": False,
    "custom_voices": [],
    "custom_styles": []
}


class Config:
    """
    Systematic, version-safe configuration manager for Gemvox.
    Automatically migrates legacy configurations across updates without losing
    API keys, custom voices, or custom style presets.
    """

    def __init__(self):
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        load_dotenv()
        self.data = DEFAULT_CONFIG.copy()
        self.data["custom_voices"] = []
        self.data["custom_styles"] = []
        self._voices_listeners = []
        self._existed_before_load = False
        self.load()

    def _find_legacy_config_files(self) -> list[Path]:
        """Discover any previous config.json files from older versions or locations."""
        base_dir = _get_app_base_dir()
        candidates = [
            base_dir / "config.json",
            Path.home() / ".gemvox" / "config.json",
            _get_user_appdata_dir() / "config.json",
        ]
        found = []
        seen = set()
        for p in candidates:
            try:
                resolved = str(p.resolve())
                if resolved not in seen and p.is_file():
                    seen.add(resolved)
                    found.append(p)
            except Exception:
                pass
        return found

    def _merge_and_migrate(self, loaded_dict: dict):
        """Non-destructively merge loaded settings into current schema."""
        if not isinstance(loaded_dict, dict):
            return

        # Preserve all known and custom fields while ensuring new defaults exist
        for k, default_val in DEFAULT_CONFIG.items():
            if k in loaded_dict and loaded_dict[k] is not None:
                self.data[k] = loaded_dict[k]
            elif k not in self.data:
                self.data[k] = default_val

        # Also keep any forward-compatible extra keys
        for k, val in loaded_dict.items():
            if k not in self.data:
                self.data[k] = val

        # Normalize language code
        lang = str(self.data.get("language", "en")).lower().strip()
        if lang not in ("en", "th"):
            lang = "en"
        self.data["language"] = lang

        # Normalize lists
        if not isinstance(self.data.get("custom_voices"), list):
            self.data["custom_voices"] = []
        if not isinstance(self.data.get("custom_styles"), list):
            self.data["custom_styles"] = []

        # If a user upgrading from v1.1.0-v1.1.4 already had an API key or custom items saved,
        # mark first_run_completed as True if it wasn't explicitly set in the old schema.
        if "first_run_completed" not in loaded_dict:
            has_existing_setup = bool(
                str(loaded_dict.get("api_key", "")).strip()
                or loaded_dict.get("custom_voices")
                or loaded_dict.get("custom_styles")
            )
            if has_existing_setup:
                self.data["first_run_completed"] = True

        self.data["config_version"] = CONFIG_SCHEMA_VERSION

    def load(self):
        loaded_any = False

        # 1. Try primary config file first
        if CONFIG_FILE.is_file():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._merge_and_migrate(saved)
                loaded_any = True
                self._existed_before_load = True
            except Exception:
                pass

        # 2. If primary config didn't exist yet, check legacy locations to auto-migrate seamlessly
        if not loaded_any:
            for legacy_path in self._find_legacy_config_files():
                if legacy_path == CONFIG_FILE:
                    continue
                try:
                    with open(legacy_path, "r", encoding="utf-8") as f:
                        saved = json.load(f)
                    self._merge_and_migrate(saved)
                    loaded_any = True
                    self._existed_before_load = True
                    # Save migrated config to primary path immediately
                    self.save()
                    break
                except Exception:
                    pass

        # 3. Check environment variable for API key fallback
        env_key = os.getenv("GEMINI_API_KEY", "").strip()
        if env_key and not self.data.get("api_key"):
            self.data["api_key"] = env_key

    def save(self):
        """Atomically save configuration with automatic backup (.bak) for safety."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            self.data["config_version"] = CONFIG_SCHEMA_VERSION
            tmp_file = CONFIG_FILE.with_suffix(".json.tmp")
            bak_file = CONFIG_FILE.with_suffix(".json.bak")

            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)

            if CONFIG_FILE.is_file():
                try:
                    shutil.copy2(CONFIG_FILE, bak_file)
                except Exception:
                    pass

            os.replace(tmp_file, CONFIG_FILE)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value, auto_save: bool = True):
        self.data[key] = value
        if auto_save:
            self.save()

    @property
    def language(self) -> str:
        lang = str(self.data.get("language", "en")).lower().strip()
        return lang if lang in ("en", "th") else "en"

    @language.setter
    def language(self, value: str):
        lang = str(value).lower().strip()
        self.data["language"] = lang if lang in ("en", "th") else "en"
        self.save()

    @property
    def is_first_run(self) -> bool:
        """Return True if this is the very first time the user launches Gemvox."""
        if not self.data.get("first_run_completed", False) and not self.api_key:
            return True
        return False

    @property
    def api_key(self) -> str:
        return (self.data.get("api_key") or os.getenv("GEMINI_API_KEY", "")).strip()

    @api_key.setter
    def api_key(self, value: str):
        self.data["api_key"] = value.strip()
        self.save()

    @property
    def output_dir(self) -> Path:
        custom = self.data.get("output_dir")
        if custom:
            out = Path(custom)
        else:
            out = DEFAULT_OUTPUT_DIR
        try:
            out.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return out

    def add_voices_listener(self, callback):
        """Register a callback invoked whenever custom voices are added or removed."""
        if callback not in self._voices_listeners:
            self._voices_listeners.append(callback)

    def remove_voices_listener(self, callback):
        """Unregister a custom voices listener callback."""
        if callback in self._voices_listeners:
            self._voices_listeners.remove(callback)

    def _notify_voices_changed(self):
        for cb in list(self._voices_listeners):
            try:
                cb()
            except Exception:
                pass

    def add_custom_voice(self, voice_id: str, display_name: str, voice_type: str = "prompted", description: str = ""):
        custom_voices = self.data.get("custom_voices", [])
        filtered = [v for v in custom_voices if v.get("id") != voice_id]
        filtered.append({
            "id": voice_id,
            "display_name": display_name,
            "type": voice_type,
            "description": description
        })
        self.data["custom_voices"] = filtered
        self.save()
        self._notify_voices_changed()

    def remove_custom_voice(self, voice_id: str):
        custom_voices = self.data.get("custom_voices", [])
        self.data["custom_voices"] = [v for v in custom_voices if v.get("id") != voice_id]
        self.save()
        self._notify_voices_changed()

    def add_custom_style(self, name: str, style: str):
        custom_styles = self.data.get("custom_styles", [])
        filtered = [s for s in custom_styles if s.get("name", "").lower() != name.lower()]
        filtered.append({
            "name": name,
            "style": style,
            "is_custom": True
        })
        self.data["custom_styles"] = filtered
        self.save()

    def remove_custom_style(self, name: str):
        custom_styles = self.data.get("custom_styles", [])
        self.data["custom_styles"] = [s for s in custom_styles if s.get("name", "").lower() != name.lower()]
        self.save()


# Singleton configuration
config = Config()
