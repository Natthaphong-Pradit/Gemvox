# Gemvox: Accessible Gemini 3.8 Flash TTS Client

**Gemvox** is a Python desktop application and accessible CLI tool designed specifically for **blind and visually impaired creators**. It brings the full power of Google's state-of-the-art **Gemini 3.8 Flash TTS** (`gemini-3.8-flash-tts` and `gemini-3.8-flash-lite-tts`) into a clean, distraction-free, 100% keyboard-navigable environment.

---

## Why Gemvox?

The official Google AI Studio web interface is powerful, but its nested web components, dynamic ARIA regions, unannounced sliders, and visual-heavy voice selector grids make it steep and fatiguing for screen reader users (NVDA, JAWS, Windows Narrator). 

**Gemvox** solves this by providing:
- **Native Win32 Accessible Controls** (powered by `wxPython`) with full UI Automation (UIA) and MSAA support.
- **Spoken Status Announcements**: Automatically speaks progress ("Synthesizing with voice Kore...", "Audio ready in 1.2s", "Playing audio...") directly through the active screen reader (NVDA, JAWS, etc.) without SAPI 5 voice collisions.
- **Auditory Sound Cues**: Distinct, pleasant tones for generation start, completion, stop, and errors.
- **100% Keyboard-Driven Workflow**: Fast mnemonic access keys (`Alt+X`, `Alt+V`, `Alt+M`, etc.) and global shortcuts (`Ctrl+Enter`, `Alt+P`, `Ctrl+S`).
- **Complete Feature Parity**: Covers every feature of Gemini 3.8 Flash TTS.
- **Dual Mode**: Choose between the accessible GUI or the linear interactive terminal CLI (`--cli`).
- **Bilingual Localization (English & Thai)**: Full English and Thai (ภาษาไทย) interface with instant language switching and a guided First-Run Setup Wizard.

---

## Features

1. **Single-Speaker Text-to-Speech (Ctrl+1)**
   - Verbatim transcript recitation.
   - Sustained turn-level delivery styles (`speech_metadata.style`: e.g. "cheerful and friendly", "whispered urgently", "calm and relaxed"), including custom user-defined style presets (create with `Alt+C`, delete custom styles with `Alt+D`).
   - Inline vocal tags picker dialog (`<short pause>`, `<sigh>`, `<cough>`, `<whisper>`, `<yawn>`, `<laugh>`, `<throat-clearing>`, etc.).
   - Open `.txt` text files (`Ctrl+O`), save `.txt` scripts (`Ctrl+Shift+S`), and check Text & Script Statistics (`Ctrl+I` — word count, character count, line count, and estimated speech duration).
   - Model switching between `gemini-3.8-flash-tts` (studio fidelity) and `gemini-3.8-flash-lite-tts` (high-throughput, ultra-low latency).
   - Audition voice preview button (`Alt+U`).

2. **Multi-Speaker Conversational Dialogue (Ctrl+2)**
   - Accessible script format: `SpeakerName: Text [optional style]`
   - Built-in templates for podcasts and interviews (`Alt+L`, `Alt+N`), plus `.txt` script loading (`Ctrl+O`) and saving (`Ctrl+Shift+S`).
   - Automatic speaker detection with voice mapping dropdowns that preserve assigned voices across edits.
   - Generates natural multi-turn conversations in a single audio file.

3. **Voice Design Studio (Ctrl+3)**
   - Create brand-new, persistent vocal personas from natural language descriptions.
   - Specify name, gender, language code, and persona description (e.g., *"A warm astronomer in his 60s with a gentle British accent speaking with quiet wonder"*).
   - Instant playback of returned sample audio preview and persistent `voice_...` ID.
   - **Real-Time Voice Synchronization**: Newly created voices are automatically saved and appear immediately across all voice selectors (Single-Speaker, Multi-Speaker, Voice Library, and Settings) without restarting the application.

4. **Voice Replication (Ctrl+4)**
   - Replicate an adult speaker's voice from a 10–30s clean reference WAV clip.
   - Mandatory consent phrase helper with one-click clipboard copying:
     > *"I am the owner of this voice and I consent to Google using this voice to create a synthetic voice model."*
   - Choice between Stateful project storage (`voice_...`) and Stateless keys (`voicekey_...`), with real-time voice list updates across all tabs.

5. **Voice Library, Custom Voice Management & Extended Search (Ctrl+5)**
   - Complete built-in catalog of all **30 Featured Studio Voices** (Zephyr, Puck, Charon, Kore, Fenrir, Leda, Orus, Aoede, Callirrhoe, Autonoe, Enceladus, Iapetus, Umbriel, Algieba, Despina, Erinome, Algenib, Rasalgethi, Laomedeia, Achernar, Alnilam, Schedar, Gacrux, Pulcherrima, Achird, Zubenelgenubi, Vindemiatrix, Sadachbia, Sadaltager, Sulafat) alongside your saved **Custom Voices**.
   - **Use Selected Voice in TTS (`Alt+Y`)**: Send any studio, custom, or online Extended Library voice directly into the Single-Speaker TTS voice selector.
   - **Remove Custom Voice (`Alt+R`)**: Cleanly delete custom voices with real-time synchronization across all tabs.
   - Live querying of the Gemini Extended Voice Library by language, gender, domain (Audiobook, Conversational, News), and keywords.

6. **Audio Player, Recent Generations History & WAV Export**
   - In-app non-blocking playback (`Alt+P` or `Space`).
   - **Recent Generations History (`Ctrl+H`)**: Browse all generated `.wav` audio takes in your output folder, replay/stop takes, export copies (`Alt+S`), delete old takes (`Alt+D`), or open the output folder directly (`Ctrl+Shift+O`).
   - One-click WAV export (`Ctrl+S`) and automatic timestamped audio saving in the output directory.
   - **100% Bilingual Localization (English & Thai)**: Both the visual interface and all spoken Screen Reader announcements / status bar messages are localized in English and Thai.

---

## Installation & Setup

Gemvox uses an isolated Python virtual environment (`python -m venv`):

### 1. Clone the Repository
```powershell
git clone https://github.com/Natthaphong-Pradit/Gemvox.git
cd Gemvox
```

### 2. Create & Activate the Virtual Environment
On Windows PowerShell:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
Or on Command Prompt (cmd):
```cmd
python -m venv venv
.\venv\Scripts\activate.bat
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Your Gemini API Key
You can configure your key in any of three ways:
1. **Inside Gemvox Settings Tab (Ctrl+6)**: Enter key and click **Test Connection** (`Alt+C`) then **Save Settings** (`Alt+S`).
2. **In `.env` file**: Create a `.env` file from `.env.example`:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```
3. **In environment variables**:
   ```powershell
   $env:GEMINI_API_KEY="your_actual_api_key_here"
   ```

---

## How to Run

### Easiest Way (Double-Click Batch Files)
- **`Gemvox.bat`**: Double-click (or press Enter in File Explorer) to launch the Accessible GUI immediately without needing PowerShell or a black console window.
- **`Gemvox_CLI.bat`**: Double-click to launch the Accessible Interactive Terminal Menu.

---

### Via Command Line or PowerShell
#### Graphical User Interface (Default)
```powershell
.\venv\Scripts\python.exe gemvox.py
```
Or via CMD:
```cmd
Gemvox.bat
```

#### Interactive Screen Reader CLI Mode
For users who prefer operating directly in the terminal:
```powershell
.\venv\Scripts\python.exe gemvox.py --cli
```
Or via CMD:
```cmd
Gemvox_CLI.bat
```

### Direct Command-Line Automation
Synthesize single-speaker text:
```powershell
.\venv\Scripts\python.exe gemvox.py speak "Welcome to Gemvox!" --voice Kore --style "cheerful and friendly" --play
```

Synthesize multi-speaker dialogue script:
```powershell
.\venv\Scripts\python.exe gemvox.py dialogue script.txt --speakers Joe:Puck Jane:Kore --out podcast.wav --play
```

Browse voices:
```powershell
.\venv\Scripts\python.exe gemvox.py voices
.\venv\Scripts\python.exe gemvox.py voices --search "warm"
```

Design custom voice:
```powershell
.\venv\Scripts\python.exe gemvox.py design "Warm British Astronomer" --prompt "A warm astronomer in his late 60s" --gender male --lang en-GB
```

---

## Keyboard Shortcuts Guide

| Shortcut | Action |
|---|---|
| `Ctrl+Enter` or `Alt+G` | Generate Speech / Dialogue |
| `Alt+P` | Play / Stop audio |
| `Ctrl+S` or `Alt+S` | Save current audio as WAV |
| `Ctrl+O` | Open `.txt` Text or Dialogue Script file |
| `Ctrl+Shift+S` | Save current Text or Dialogue Script as `.txt` file |
| `Ctrl+H` | Open Recent Generations History dialog |
| `Ctrl+Shift+O` | Open Output Folder in File Explorer |
| `Ctrl+I` | Announce Text & Script Statistics (words, characters, lines, duration) |
| `Ctrl+1` .. `Ctrl+6` | Switch directly to Tabs 1 through 6 |
| `Alt+T` | Open Tabs menu |
| `F1` | Open Help & Accessibility Guide dialog |
| `Alt+X` | Jump to Text input area (Single-Speaker tab) |
| `Alt+M` | Focus Model selector |
| `Alt+V` | Focus Voice selector |
| `Alt+Y` | Focus Style / Emotion field (Tab 1) / Use Selected Voice in TTS (Tab 5) |
| `Alt+B` | Open Style Presets dialog (Tab 1) / Show Built-in & Custom Voices (Tab 5) |
| `Alt+C` | Create Custom Style Preset (Tab 1) / Copy Voice ID (Tab 5) / Test Connection (Tab 6) |
| `Alt+R` | Remove Selected Custom Voice (Tab 5) |
| `Alt+I` | Open Inline Vocal Tag dialog |
| `Alt+L` | Clear Text in Single-Speaker tab |
| `Alt+U` | Audition currently selected voice |

---

## Technical Specifications

- **SDK**: `google-genai >= 2.25.0` (using latest Interactions API)
- **Primary Model**: `gemini-3.8-flash-tts`
- **Secondary Model**: `gemini-3.8-flash-lite-tts`
- **Audio Output**: 24kHz 16-bit Mono Linear PCM WAV
- **Screen Reader Support**: NVDA, JAWS, Windows Narrator, SuperNova
- **Accessibility Layer**: Bundled NVDA Controller Client (`nvdaControllerClient32.dll` / `nvdaControllerClient64.dll`), JAWS API, ZDSR, and Win32 UIA/MSAA
