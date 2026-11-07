from google import genai
from gemvox.config import config
from gemvox.accessibility import announcer

class GeminiClientManager:
    """Manages the Google GenAI SDK client instance."""
    def __init__(self):
        self._client = None
        self._current_key = None

    def get_client(self) -> genai.Client:
        key = config.api_key.strip()
        if not key:
            raise ValueError("Gemini API key is not set. Please configure your API key in Settings or set GEMINI_API_KEY environment variable.")
        
        if self._client is None or self._current_key != key:
            self._client = genai.Client(api_key=key)
            self._current_key = key
        
        return self._client

    def validate_key(self, api_key: str = None) -> tuple[bool, str]:
        """Validate if the provided API key or configured API key works."""
        test_key = (api_key or config.api_key).strip()
        if not test_key:
            return False, "API key is empty."
        try:
            temp_client = genai.Client(api_key=test_key)
            # Perform a lightweight call to test authorization
            # Listing 1 model or checking interaction status
            models = temp_client.models.list(page_size=1)
            # If successful:
            return True, "API key is valid and connected to Gemini API successfully."
        except Exception as e:
            err_msg = str(e)
            if "API_KEY_INVALID" in err_msg or "403" in err_msg or "400" in err_msg:
                return False, f"Invalid API Key: {err_msg}"
            return False, f"Connection error: {err_msg}"

client_manager = GeminiClientManager()
