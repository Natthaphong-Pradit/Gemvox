# Gemvox: Accessible Gemini Speech Synthesis Studio

**Gemvox** is a lightweight, accessible Windows desktop application and CLI studio designed specifically for **blind and visually impaired creators**. It brings the full expressive power of Google's state-of-the-art **Gemini TTS models** (Gemini 2.5 Flash, 3.1 Flash, 2.5 Pro, and 3.8 Flash TTS) into a clean, distraction-free, 100% keyboard-navigable environment.

---

## ⚡ Quick Start: Download Ready-to-Use Windows Executables

> [!TIP]
> **No Python installation or command-line setup is required!** Pre-compiled, self-contained Windows packages are readily available on our GitHub Releases page.

👉 **[Download Latest Gemvox Release (v1.1.8)](https://github.com/Natthaphong-Pradit/Gemvox/releases/latest)**

You can choose between two convenient download formats:

### 1. Standalone Single-File Executable (`Gemvox_Standalone.exe`)
- **Zero installation or extraction required**: Download the single `.exe` file to your Desktop or Downloads folder and run it immediately.
- Ideal for users who want a quick, clean, and portable setup.
- Stores user preferences and API keys persistently in `%APPDATA%\Gemvox`.

### 2. Complete Portable Folder Edition (`Gemvox_v1.1.8_Portable.zip`)
- **100% Self-Contained**: Extract the ZIP file to any folder or USB flash drive and run `Gemvox.exe`.
- **True Portable Mode**: Contains a `portable.txt` flag so that your `config.json` settings, custom vocal personas, and generated `.wav` audio files (`output/` folder) stay inside the application directory without touching your system registry or AppData.
- **Pre-bundled Screen Reader DLLs**: Includes high-performance 32-bit and 64-bit client libraries for NVDA (`nvdaControllerClient`), JAWS, and ZDSR out of the box.

### 🔄 In-App Auto-Updater (`Ctrl+U`)
Gemvox features a built-in direct GitHub updater. Whenever a new version is released, simply press **`Ctrl+U`** inside Gemvox. The program will check `https://github.com/Natthaphong-Pradit/Gemvox`, download the latest update, and reinstall it in place automatically without losing your settings or audio files.

---

## 💻 Running from Source (For Developers & Power Users)

If you prefer running Gemvox directly from the Python source code or contributing to development:

### 1. Clone the Repository
```powershell
git clone https://github.com/Natthaphong-Pradit/Gemvox.git
cd Gemvox
```

### 2. Automated One-Click Setup & Launch (Recommended)
Double-click (or press Enter on) the provided batch launchers in File Explorer:
- **`Gemvox.bat`**: Automatically detects or creates the virtual environment (`venv`), installs missing dependencies from `requirements.txt`, and launches the Accessible GUI.
- **`Test.bat`**: Runs the comprehensive diagnostic test suite verifying Python runtime, wxPython, google-genai SDK, sounddevice drivers, and UI dialogs.
- **`Gemvox_CLI.bat`**: Launches the accessible, linear interactive terminal menu.

### 3. Manual Virtual Environment Setup
On Windows PowerShell:
```powershell
# Create isolated virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt

# Run diagnostic verification
python test_gemvox.py

# Launch Gemvox GUI
python gemvox.py
```

Or on Command Prompt (CMD):
```cmd
python -m venv venv
.\venv\Scripts\activate.bat
pip install -r requirements.txt
python test_gemvox.py
python gemvox.py
```

---

## 🔑 Configuring Your Gemini API Key

Gemvox requires a Google Gemini API key (free or paid tier from [Google AI Studio](https://aistudio.google.com/)).

You can configure your key in any of three easy ways:
1. **Inside Gemvox Settings Tab (`Ctrl+6`)**: Paste your key into the API Key field, press **`Alt+C`** to test the connection, and press **`Alt+S`** to save.
2. **Via `.env` file**: Create a `.env` file in the application directory:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```
3. **Via Environment Variable**:
   ```powershell
   $env:GEMINI_API_KEY="your_actual_api_key_here"
   ```

---

## 🌟 Why Gemvox?

The official Google AI Studio web interface is feature-rich, but its deeply nested visual components, dynamic ARIA regions, unannounced sliders, and visual voice cards make it difficult and exhausting for screen reader users (NVDA, JAWS, Windows Narrator).

**Gemvox** solves this with a screen reader first-class design:
- **Native Accessible Controls**: Built with native Win32 controls via `wxPython`, offering full UI Automation (UIA) and MSAA support with zero unlabeled buttons.
- **Direct Screen Reader Speech Announcements**: Announces synthesis status and progress directly through your active screen reader (NVDA, JAWS, ZDSR, PC Talker) without causing SAPI 5 speech collisions.
- **Auditory Sound Cues**: Distinct, subtle earcons for generation start, completion, stop, and error events.
- **100% Keyboard-Driven Workflow**: High-contrast mnemonic shortcuts (`Alt+...`) and standard global keys (`Ctrl+Enter`, `Alt+P`, `Alt+Q`, `Ctrl+S`).
- **Resilient Multi-Model Fallback**: Automatically connects to the Universal AI Studio TTS endpoint (`v1beta`) with intelligent fallback across Gemini 2.5 Flash, 3.1 Flash, 2.5 Pro, 3.8 Flash, and 2.0 Flash models.
- **Dual Interface**: Use the accessible graphical studio or the linear interactive command-line interface (`--cli`).
- **Bilingual Localization (English & Thai)**: Complete interface and spoken screen reader announcements in both English and Thai (ภาษาไทย).

---

## 🎛️ Key Features & Capabilities

### 1. Single-Speaker Text-to-Speech (`Ctrl+1`)
- Recite verbatim text transcripts with natural phrasing and pacing.
- **Sustained Delivery Styles (`Alt+Y`)**: Direct vocal performance using natural-language styles (e.g., *"cheerful and friendly"*, *"whispered urgently"*, *"calm and relaxed"*).
- **Custom Style Presets**: Save and manage reusable style presets (`Alt+B` to browse, `Alt+C` to create).
- **Inline Vocal Tags Dialog (`Alt+I`)**: Insert momentary expressive tags such as `<sigh>`, `<laugh>`, `<whisper>`, `<yawn>`, `<cough>`, and `<short pause>`.
- **Text & Script Statistics (`Ctrl+I`)**: Instantly check character count, word count, line count, and estimated speech duration.
- **Voice Audition (`Alt+U`)**: Audition any voice with a quick sample phrase before synthesizing long transcripts.

### 2. Multi-Speaker Conversational Dialogue (`Ctrl+2`)
- Write natural scripts using standard format:
  ```text
  Alice: Welcome back to our podcast! [cheerful and friendly]
  Bob: Thanks Alice! Excited to be here today. [warm and relaxed]
  ```
- **Automatic Speaker Detection**: Detects all unique speaker names and automatically assigns voice mappings.
- **Seamless Multi-Turn Audio**: Synthesizes multi-turn dialogue into a single, cohesive audio file.

### 3. Studio Audio Player & Transport Deck
Integrated into every major tab (**Single-Speaker**, **Multi-Speaker**, **Voice Design**, and **History Dialog `Ctrl+H`**):
- **Play / Pause / Resume (`Alt+P`)**: Non-blocking audio playback with dynamic button status.
- **Stop (`Alt+Q`)**: Halts playback immediately and resets timeline to `00:00`.
- **Rewind & Fast-Forward 5s (`F7` / `F8`)**: Jump backward or forward by 5 seconds.
- **Timeline Scrub Slider**: Navigate and inspect exact positions with an accessible `MM:SS / MM:SS` time readout.
- **Volume Slider (`F9` / `F10`)**: Adjust output volume from 0% to 100%.
- **Playback Speed Selector (`Ctrl+Shift+P`)**: Cycle between `0.75x`, `1.0x (Normal)`, `1.25x`, `1.5x`, and `2.0x`.
- **Loop Playback (`Ctrl+L`)**: Continuous looping for acoustic review and prompt tuning.

### 4. Voice Design Studio (`Ctrl+3`)
- Create persistent vocal personas from natural-language descriptions.
- Customize character age, vocal timbre, accent, and delivery (e.g., *"A warm astronomer in his 60s with a gentle British accent speaking with quiet wonder"*).
- **Real-Time Voice Sync**: Newly created voices appear instantly across all voice dropdowns without restarting.

### 5. Voice Replication (`Ctrl+4`)
- Replicate an adult speaker's voice using a 10–30 second clean reference WAV clip.
- Built-in consent phrase helper with one-click clipboard copying.
- Supports both stateful project storage (`voice_...`) and stateless keys (`voicekey_...`).

### 6. Voice Library & Extended Catalog (`Ctrl+5`)
- Browse all **30 Curated Studio Voices** (Zephyr, Puck, Charon, Kore, Fenrir, Leda, Orus, Aoede, Callirrhoe, Autonoe, Enceladus, Iapetus, Umbriel, Algieba, Despina, Erinome, Algenib, Rasalgethi, Laomedeia, Achernar, Alnilam, Schedar, Gacrux, Pulcherrima, Achird, Zubenelgenubi, Vindemiatrix, Sadachbia, Sadaltager, Sulafat) alongside your custom voices.
- **Send to TTS (`Alt+Y`)**: Send any selected voice directly to the Single-Speaker synthesizer.
- Query hundreds of voices from the online Gemini Extended Voice Library by language, gender, and domain.

### 7. Recent Generations History (`Ctrl+H`)
- Review all generated `.wav` takes in your output folder.
- Replay takes, export copies (`Alt+S`), delete takes (`Alt+D`), or open the output folder in File Explorer (`Ctrl+Shift+O`).

---

## ⌨️ Complete Keyboard Shortcuts Guide

| Shortcut | Description |
|---|---|
| **`Ctrl+Enter`** / **`Alt+G`** | Synthesize Speech / Multi-Speaker Dialogue / Voice Design |
| **`Alt+P`** | Play / Pause / Resume Audio |
| **`Alt+Q`** | Stop Audio & Reset Timeline to `00:00` |
| **`F7`** / **`F8`** | Rewind 5 seconds (-5s) / Fast-Forward 5 seconds (+5s) |
| **`F9`** / **`F10`** | Volume Down (-10%) / Volume Up (+10%) |
| **`Ctrl+L`** | Toggle Loop Playback Mode |
| **`Ctrl+Shift+P`** | Cycle Playback Speed (0.75x, 1.0x, 1.25x, 1.5x, 2.0x) |
| **`Ctrl+S`** | Save current audio as WAV |
| **`Ctrl+O`** | Open `.txt` text or dialogue script file |
| **`Ctrl+Shift+S`** | Save current text or dialogue script as `.txt` file |
| **`Ctrl+H`** | Open Recent Generations History dialog |
| **`Ctrl+Shift+O`** | Open Output Audio Folder in File Explorer |
| **`Ctrl+I`** | Announce Text & Script Statistics (words, characters, lines, duration) |
| **`Ctrl+U`** | Check for Updates & Direct Auto-Installer from GitHub |
| **`Ctrl+1` .. `Ctrl+6`** | Switch directly between Tabs 1 to 6 |
| **`F1`** | Open Comprehensive Help & Accessibility Guide (6 Chapters) |
| **`Alt+X`** | Focus Text Input field (Single-Speaker tab) |
| **`Alt+M`** | Focus Model Selector dropdown |
| **`Alt+V`** | Focus Voice Selector dropdown |
| **`Alt+Y`** | Focus Style field (Tab 1) / Send Selected Voice to TTS (Tab 5) |
| **`Alt+B`** | Open Style Presets dialog (Tab 1) / Show Built-in Voices (Tab 5) |
| **`Alt+C`** | Create Style Preset (Tab 1) / Copy Voice ID (Tab 5) / Test Connection (Tab 6) |
| **`Alt+R`** | Remove Selected Custom Voice (Tab 5) |
| **`Alt+I`** | Open Inline Vocal Tags dialog |
| **`Alt+U`** | Audition currently selected voice |

---

## 💻 CLI Commands (Command-Line Mode)

You can also use Gemvox as a powerful command-line tool:

```powershell
# Interactive accessible terminal menu
python gemvox.py --cli

# Quick speech generation
python gemvox.py speak "Welcome to Gemvox!" --voice Kore --style "cheerful and friendly" --play

# Multi-speaker dialogue script synthesis
python gemvox.py dialogue script.txt --speakers Alice:Puck Bob:Kore --out dialogue.wav --play

# List available voices
python gemvox.py voices --search "warm"

# Design a custom voice persona
python gemvox.py design "Warm British Historian" --prompt "A knowledgeable British historian in his 60s" --gender male --lang en-GB

# Check for updates directly from GitHub
python gemvox.py update
```

---

## 🔧 Technical Specifications

- **SDK**: `google-genai` (Targeting `v1beta` endpoint for speech synthesis)
- **Supported Models**: `gemini-2.5-flash-preview-tts` (Default), `gemini-3.1-flash-tts-preview`, `gemini-2.5-pro-preview-tts`, `gemini-3.8-flash-tts`, `gemini-3.8-flash-lite-tts`, `gemini-2.0-flash`
- **Audio Output**: 24kHz 16-bit Mono Linear PCM WAV
- **Screen Reader Support**: NVDA, JAWS, Windows Narrator, ZDSR, PC Talker, SuperNova
- **Accessibility Libraries**: Bundled NVDA Controller Client (`nvdaControllerClient32.dll` / `nvdaControllerClient64.dll`), JAWS COM API, ZDSR API, Win32 UIA/MSAA

---

## 📄 License & Attribution

Copyright (c) 2026 Natthaphong Pradit. Released under the MIT License.
Gemini is a trademark of Google LLC.
