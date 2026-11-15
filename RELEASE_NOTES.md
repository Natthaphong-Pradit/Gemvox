# Gemvox v1.2.2: Security Enhancements & Accessible Synthesis Progress

## What's New in This Release

### Security & Storage Enhancements
* **Encrypted API Key Storage:** Implemented machine-bound API key encryption, protecting credentials from unauthorized copying across devices or user accounts.
* **Separated Configuration & Secrets:** Decoupled general application settings (`config.json`) from encrypted API key storage, allowing users to safely share configuration presets without exposing sensitive credentials.
* **Automatic Key Migration:** Added seamless migration to automatically encrypt legacy plain-text API keys from older configurations upon startup.
* **CLI & Environment Variable Priority:** Prioritized `GEMINI_API_KEY` from `.env` or system environment variables before falling back to DPAPI-encrypted storage.
* **API Key Visibility Toggle:** Added an accessible show/hide toggle in the Settings panel with screen reader announcements and automatic 10-second re-masking for added privacy.

### Progress Tracking & Accessibility
* **Estimated Processing Progress:** Introduced real-time progress estimation (`1.5 + len(text) / 50.0` seconds) during audio generation with a smooth Qt progress bar.
* **Accessible Progress Announcements:** Added milestone-based screen reader announcements (start, 50%, complete) and on-demand status updates (`Ctrl+I`) without interrupting active speech navigation. Text Statistics moved to `Ctrl+T`.

### Bug Fixes & Stability
* **UTF-8 Decoding Fix:** Resolved a status bar error (`'utf-8' codec can't decode byte 0x92`) by enforcing UTF-8 encoding with fallback error handling across file-reading operations.

---

