import sys
import types

try:
    from .client import client_manager, GeminiClientManager
except ImportError:
    # Resilient fallback in case client.py was deleted or failed to pull
    from gemvox.config import config

    class GeminiClientManager:
        def __init__(self):
            self._client = None
            self._current_key = None

        def get_client(self):
            try:
                from google import genai
            except ImportError:
                raise RuntimeError("The google-genai library is not installed. Please run: pip install google-genai")
            key = config.api_key.strip()
            if not key:
                raise ValueError("Gemini API key is not set. Please configure your API key in Settings.")
            if self._client is None or self._current_key != key:
                import os
                os.environ["GOOGLE_GENAI_API_VERSION"] = "v1beta"
                try:
                    self._client = genai.Client(api_key=key, http_options={"api_version": "v1beta"})
                except Exception:
                    self._client = genai.Client(api_key=key)
                self._current_key = key
            return self._client

        def validate_key(self, api_key=None):
            try:
                from google import genai
            except ImportError:
                return False, "The google-genai library is not installed. Please run: pip install google-genai"
            test_key = (api_key or config.api_key).strip()
            if not test_key:
                return False, "API key is empty."
            try:
                import os
                os.environ["GOOGLE_GENAI_API_VERSION"] = "v1beta"
                try:
                    temp_client = genai.Client(api_key=test_key, http_options={"api_version": "v1beta"})
                except Exception:
                    temp_client = genai.Client(api_key=test_key)
                temp_client.models.list(page_size=1)
                return True, "API key is valid."
            except Exception as e:
                return False, f"Connection error: {e}"

    client_manager = GeminiClientManager()

    # Register virtual gemvox.core.client module so sub-imports never fail
    if "gemvox.core.client" not in sys.modules:
        _mod = types.ModuleType("gemvox.core.client")
        _mod.client_manager = client_manager
        _mod.GeminiClientManager = GeminiClientManager
        sys.modules["gemvox.core.client"] = _mod

from .voice_catalog import (
    PREBUILT_VOICES,
    STYLE_PRESETS,
    INLINE_VOCAL_TAGS,
    SUPPORTED_MODELS,
    VoiceInfo,
    get_all_voices,
    find_voice
)
from .audio_player import audio_player, AudioPlayer
from .tts_engine import tts_engine, TTSEngine

__all__ = [
    "client_manager",
    "GeminiClientManager",
    "PREBUILT_VOICES",
    "STYLE_PRESETS",
    "INLINE_VOCAL_TAGS",
    "SUPPORTED_MODELS",
    "VoiceInfo",
    "get_all_voices",
    "find_voice",
    "audio_player",
    "AudioPlayer",
    "tts_engine",
    "TTSEngine",
]
