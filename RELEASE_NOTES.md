# Gemvox v1.2.0: Universal Design Architecture (wxPython → PySide6)

Major architectural upgrade under **Universal Design**, migrating Gemvox's desktop GUI from `wxPython` to `PySide6` (Qt6) to deliver a modern dark studio interface for sighted users while preserving 100% keyboard navigation and native Windows screen reader accessibility.

---

## 🌟 What's New in v1.2.0

### 1. 🏗️ Architecture Migration: wxPython → PySide6 (Qt6)
- **Modern Qt6 GUI Foundation**: Replaced `wxPython` with `PySide6>=6.7.0` using the cross-platform Fusion style (`requirements.txt`, `gemvox.py`, `version_info.txt`).
- **Complete UI & Dialog Rebuild**: Migrated all 6 studio tabs (`Single-Speaker`, `Multi-Speaker`, `Voice Design`, `Voice Replication`, `Voice Library`, `Settings`), the `AudioTransportBar`, and all 7 dialogs (`InlineTagDialog`, `CreateCustomStyleDialog`, `StylePresetDialog`, `GenerationHistoryDialog`, `UpdateDialog`, `WelcomeTourDialog`, `HelpDialog`) to PySide6.
- **Thread-Safe UI Dispatching**: Replaced `wx.CallAfter` with a queued Qt signal dispatcher (`call_after`) for background TTS generation, audio playback transport updates, and update checks.

---

### 2. 🎨 Universal Design: "Obsidian & Royal Gold 2.0" Theme
- **High-Contrast Dark Studio UI**: Styled with deep obsidian surfaces (`#161A26`) and high-visibility `#E6B85C` Royal Gold `2px` focus rings so keyboard focus is always unmistakable for sighted and low-vision users alike.
- **Clean Accessible Metadata**: Built `apply_accessible()`, `QLabel.setBuddy()`, and `clean_mnemonic()` in `gemvox/ui/theme.py` so `&` shortcut markers are stripped from screen reader names while preserving `Alt+<Key>` keyboard accelerators.
- **Non-Focusable Custom Header**: Added `StudioHeaderBanner` (`QPainter`) for clean visual branding without adding clutter to keyboard `Tab` order.

---

### 3. ♿ Native Screen Reader Multiline Text (`RICHEDIT50W` Hybrid)
- **Solves Qt6 Blank-Line Repetition**: Native Qt6 `QPlainTextEdit` / `QTextEdit` Windows UIA providers repeat the previous line when navigating blank lines. Gemvox's `AccessibleTextArea` (`gemvox/ui/accessible_text.py`) embeds Windows' native `RICHEDIT50W` (`msftedit.dll`) via `QWindow.fromWinId` + `QWidget.createWindowContainer`, ensuring NVDA and Windows screen readers announce `"blank"` accurately on empty lines and end-of-line.
- **Read-Only Caret Navigation**: Enables full keyboard arrow navigation in read-only multiline areas including Help Guide (`F1`), Welcome Tour, Update Notes, and Consent Phrase.
- **Dynamic MSAA/UIA Annotations & Focus Sync**: Uses `IAccPropServices::SetHwndPropStr` (`PROPID_ACC_NAME`, `PROPID_ACC_DESCRIPTION`) and plain-text paste mode (`TM_PLAINTEXT`), and synchronizes Win32/Qt focus on `Tab` / `Shift+Tab` transitions so leaving and returning to any text area always restores screen reader speech and caret tracking.

---

### 4. ⌨️ Complete Keyboard Navigation & Shortcut Parity
- **wx-Compatible `eventFilter` & `WndProc` Forwarding**: Preserves all existing studio shortcuts across both Qt widgets and `RICHEDIT50W` text areas:
  - **Tab Switching**: `Ctrl+1..6`, `Alt+1..6`, `Ctrl+Tab`, `Ctrl+Shift+Tab`, `Ctrl+PageUp`, `Ctrl+PageDown`, plus `Left`/`Right` arrow navigation when focused on the tab bar.
  - **Studio Actions**: `Ctrl+Enter` (Generate), `Alt+P` / `Alt+Q` (Playback), `F1` (Help Guide), `F7..F10`, `Ctrl+O/S/H/I/U/L`, `Ctrl+Shift+S/O/P`, `Alt+Shift+L`, and all per-tab `Alt+<Key>` mnemonics.
- **Expanded Diagnostic Audit**: Updated `test_gemvox.py` to audit 92 interactive controls, tab switching, text editing operations, and all 7 dialogs under PySide6.
