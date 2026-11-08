from typing import Optional, Tuple, Any

try:
    from google import genai
except ImportError:
    genai = None

from gemvox.config import config
from gemvox.accessibility import announcer


class GeminiClientManager:
    """Manages the Google GenAI SDK client instance."""

    def __init__(self):
        self._client: Any = None
        self._current_key: Optional[str] = None

    def get_client(self) -> Any:
        if genai is None:
            raise RuntimeError(
                "The google-genai SDK is not installed in this Python environment. "
                "Please run: pip install google-genai"
            )
        key = config.api_key.strip()
        if not key:
            raise ValueError(
                "Gemini API key is not set. Please configure your API key in Settings "
                "or set the GEMINI_API_KEY environment variable."
            )

        if self._client is None or self._current_key != key:
            self._client = genai.Client(api_key=key)
            self._current_key = key

        return self._client

    def validate_key(self, api_key: Optional[str] = None) -> Tuple[bool, str]:
        """Validate if the provided API key or configured API key works."""
        if genai is None:
            return False, "The google-genai SDK is not installed. Please run: pip install google-genai"

        test_key = (api_key or config.api_key).strip()
        if not test_key:
            return False, "API key is empty."
        try:
            temp_client = genai.Client(api_key=test_key)
            # Perform a lightweight call to test authorization
            temp_client.models.list(page_size=1)
            return True, "API key is valid and connected to Gemini API successfully."
        except Exception as e:
            err_msg = str(e)
            if "API_KEY_INVALID" in err_msg or "403" in err_msg or "400" in err_msg:
                return False, f"Invalid API Key: {err_msg}"
            return False, f"Connection error: {err_msg}"


client_manager = GeminiClientManager()

