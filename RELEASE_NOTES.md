# Gemvox v1.1.8: Fix 400 INVALID_ARGUMENT speechConfig & Enhanced TTS Endpoint Resilience

Accessible Desktop Studio for Google Gemini Speech Synthesis (Single-Speaker, Multi-Speaker Conversational Dialogue, Voice Design, Replication & Extended Library) with First-Class Screen Reader Support (NVDA, JAWS, Narrator).

---

## 🌟 What's New in v1.1.8

### 1. 🛠️ Fix 400 INVALID_ARGUMENT (`Unknown name "speechConfig" at 'generation_config'`)
- **Root Cause**: When initialized without an explicit API version, the `google-genai` SDK defaults to Google AI Studio's `/v1/` endpoint. The `v1` endpoint schema only supports standard Text/Vision models and rejects `speechConfig` and `responseModalities: ["AUDIO"]` inside `generation_config`, resulting in HTTP 400 rejection upon prompt submission.
- **Enforced `v1beta` Endpoint**:
  - Configured `genai.Client` with `http_options={"api_version": "v1beta"}` and exported `GOOGLE_GENAI_API_VERSION="v1beta"`.
  - Upgraded payload generation to use strongly-typed `google.genai.types.GenerateContentConfig` and `types.SpeechConfig` for both single-speaker and multi-speaker synthesis.
- **Interactions API Compliance for Dialogue**:
  - Removed deprecated `mode: "conversational"` parameter from `speech_config` to prevent recent 400 parameter rejection from Google backend servers.

---

### 2. 🛡️ Intelligent Model Fallback & Error Classification
- **Automatic Fallback on Model Rejection**: The engine automatically detects `404 Not Found`, `Unknown name speechConfig`, `cannot find field`, and `is not supported` errors, immediately falling back to the next candidate model in sequence without interrupting the user.
- **Accurate Authentication & Quota Reporting**: Legitimate API key errors (`API_KEY_INVALID`) or quota limits (`RESOURCE_EXHAUSTED`) are preserved and reported directly to the user rather than erroneously triggering fallbacks.
- **Candidate Fallback Priority**:
  1. `gemini-2.5-flash-preview-tts` (Maximum stability across all Google AI Studio API key tiers)
  2. `gemini-3.1-flash-tts-preview` (Rich vocal acting & inline vocal tag support)
  3. `gemini-2.5-pro-preview-tts` (Studio-grade long-form narration)
  4. `gemini-3.8-flash-lite-tts` (Low-latency throughput)
  5. `gemini-3.8-flash-tts` (Flagship next-gen synthesis)
  6. `gemini-2.0-flash` (Universal audio modality fallback)
- **Seamless PCM-to-WAV RIFF Wrapping**: Automatically encapsulates 24kHz 16-bit Mono raw PCM (`audio/L16`) into standardized RIFF WAV headers.

---

### 3. 🎛️ Studio Audio Player Transport Deck Redesign
Integrated a non-blocking, professional audio transport bar across all primary studio views (**Single-Speaker**, **Multi-Speaker Dialogue**, **Voice Design**, and **Recent Generations History Ctrl+H**):
- **Play / Pause / Resume Toggle (`Alt+P`)**: Seamlessly toggles playback state with dynamic label and button styling.
- **Dedicated Stop Button (`Alt+Q`)**: Instantly halts playback and resets position to `00:00`.
- **Rewind & Fast-Forward 5s (`F7` / `F8`)**: Skips backwards or forwards by 5 seconds with precision.
- **Interactive Seek Timeline Slider**: Real-time position scrubbing with high-contrast accessible `MM:SS / MM:SS` time display.
- **Volume Control (`F9` Volume Down / `F10` Volume Up)**: Granular volume control from 0% to 100% saved automatically to user settings.
- **Playback Speed Selector (`Ctrl+Shift+P`)**: Choose between 5 speed presets: `0.75x`, `1.0x (Normal)`, `1.25x`, `1.5x`, and `2.0x`.
- **Loop Playback Mode (`Ctrl+L`)**: Continuous looping for acoustic review and prompt tuning.

---

### 4. 🚀 Startup Resilience & Diagnostic Environment Checker
- **Cross-Platform Accessibility Safety**: Fully guarded `ctypes.windll` and `winsound` calls in `announcer.py` for safe execution across all environments.
- **`wx.App` Initialization Lifecycle Fix**: Guaranteed wx application lifecycle initialization before window construction.
- **Integrated Health Check (`Test.bat` / `test_gemvox.py`)**: One-click environment diagnostic verifying Python, wxPython, google-genai, sounddevice, and accessible dialogs.
- **Direct GitHub Auto-Updater (`Ctrl+U`)**: Checks for updates, downloads, and reinstalls new releases directly from GitHub.

---

## ⌨️ Essential Keyboard Shortcuts
- **`Ctrl+Enter` / `Alt+G`**: Synthesize Speech / Multi-Speaker Dialogue / Voice Design
- **`Alt+P`**: Play / Pause / Resume
- **`Alt+Q`**: Stop and reset to 00:00
- **`F7` / `F8`**: Rewind 5s (-5s) / Fast-Forward 5s (+5s)
- **`F9` / `F10`**: Decrease Volume (-10%) / Increase Volume (+10%)
- **`Ctrl+L`**: Toggle Loop Playback
- **`Ctrl+Shift+P`**: Cycle Playback Speed (0.75x - 2.0x)
- **`Ctrl+S`**: Save current audio file as WAV
- **`Ctrl+H`**: Open Generation History Dialog
- **`Ctrl+U`**: Check for Updates directly from GitHub
- **`Ctrl+1 .. 6`**: Switch studio tabs
- **`F1`**: Open Comprehensive User Guide

---

## 📦 Download Assets:
- **`Gemvox_Standalone.exe`**: Single-file portable executable (No installation required)
- **`Gemvox_v1.1.8_Portable.zip`**: Complete portable directory including Screen Reader client DLLs (NVDA 32/64-bit) and portable configuration
