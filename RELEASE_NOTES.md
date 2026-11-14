# Gemvox v1.1.9: Long-Form Audio Quality Fix, Long-Play Stability & Startup Auto-Updater

More enhancement to audio player model and updating function.

---

## 🌟 What's New in v1.1.9

### 1. 🎙️ Long-Form TTS Chunking & Seamless PCM Stitching (Fixes 5+ Minute Audio Distortion)
- **Root Cause**: Sending very long paragraphs (5+ minutes of speech) to Gemini TTS models in a single request caused autoregressive audio degradation toward the end of the generation, resulting in distorted, crackly, or muffled audio.
- **Intelligent Text Chunking**: Texts exceeding `1,800` characters (~2 minutes of speech per segment) are now automatically split at natural paragraph, sentence, or whitespace boundaries without breaking inline vocal tags (`<...>`), supporting both English and Thai scripts. Short and medium texts still run in a single request with zero added latency.
- **Model Consistency Locking**: Locks onto the first working TTS model across all chunks in a generation so vocal timbre and style remain consistent from start to finish.
- **Click-Free PCM Stitching**: Applies 5ms micro fade-in/fade-out edges on each 16-bit PCM segment and inserts natural conversational pauses (`0.16s` for single-speaker, `0.14s` for multi-speaker) before wrapping into a single RIFF WAV file.
- **Multi-Speaker Long Dialogue Support**: Extended automatic batching and sub-chunking to 1-speaker, 2-speaker, and 3+ speaker dialogues.

---

### 2. 🔊 Studio Audio Player Optimization for Extended Playback (10+ Minutes)
- **Glitch-Free PortAudio Buffering**: Increased streaming chunk size from `1024` to `4096` frames (~170ms at 24kHz) and enabled high-latency output buffering (`blocksize=2048, latency="high"` with automatic fallback) to prevent buffer underruns during 10+ minute playback.
- **Continuous-Phase Linear Interpolation**: Upgraded playback speed resampling (`0.75x` – `2.0x`) from per-chunk nearest-neighbor to continuous-phase linear interpolation with lookahead frame smoothing, eliminating boundary clicks and metallic artifacts.
- **Zero UI / Accessibility Event Storm**: Throttled playback transport updates to `0.25s` and added state-diffing in the Audio Transport Bar so buttons, sliders, and labels only update when their values actually change—eliminating redundant Win32/UIA screen reader events and GDI repaints during long playback.

---

### 3. 🔄 Automatic Startup Update Checker
- **Silent Background Check on Launch**: Gemvox now checks GitHub for newer releases automatically in the background when launched (or right after completing the first-run Welcome Tour).
- **Zero-Interruption Behavior**: If a newer version is found, the Auto-Updater dialog opens immediately with pre-loaded release notes ready to install; if you are already up to date (or offline), it stays silent and does nothing.
- **Manual Check Preserved**: Press `Ctrl+U` (or use **Help → Check for Updates...** / Settings) anytime to check manually. Controlled by `auto_check_updates` (enabled by default).
