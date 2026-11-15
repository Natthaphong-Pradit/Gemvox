# Gemvox v1.2.1: Multi-Document Support & Screen Reader Focus Enhancement

Maintenance and feature release building on Gemvox's Universal Design PySide6 architecture, adding rich document and Google Docs import alongside smoother `QAccessible` screen reader focus recovery on Windows.

---

## What's New in v1.2.1

### 1. More Document File Type Support (`Ctrl+O`)
- **Expanded File Formats**: `File -> Open Document / Script File...` (`Ctrl+O`) now extracts clean text directly into the active tab (**Single-Speaker** or **Multi-Speaker**) from:
  - **Word Documents (`.docx`)**: Extracts paragraphs and table contents via `python-docx` (with pure-stdlib `zipfile`/XML fallback).
  - **PDF Documents (`.pdf`)**: Extracts multi-page text via `pypdf` (with `PySide6.QtPdf.QPdfDocument` fallback and clear warnings for password-protected PDFs).
  - **HTML / Web Files (`.html`, `.htm`, `.xhtml`)**: Strips `<script>`, `<style>`, and non-content tags using `BeautifulSoup` (`beautifulsoup4`).
  - **Plain Text & Scripts (`.txt`, `.md`, `.script`, `.csv`, `.log`, `.srt`, `.vtt`)**: Supports automatic encoding fallback (`UTF-8`, `CP874`/`TIS-620`, `CP1252`).

---

### 2. Google Docs & Web URL Import (`Ctrl+G`)
- **Direct Link Fetching**: Added `File -> Open Google Docs / Web URL...` (`Ctrl+G`) and `OpenGoogleDocsDialog` (`gemvox/ui/dialogs.py`) powered by `urllib.request` and `BeautifulSoup` in `gemvox/core/document_loader.py`.
- **Google Docs Formats Supported**: Supports both standard share links (`/document/d/<ID>/...`) and published-to-web links (`/document/d/e/<ID>/pub`).
- **Smart Permission Detection & Guidance**: Detects restricted/private Google Docs (HTTP `401`/`403` or redirects to `accounts.google.com` sign-in) and displays an accessible warning dialog with step-by-step instructions (in English and Thai) to set sharing to **"Anyone with the link -> Viewer"**.
- **Non-Blocking Fetch**: Downloads and parses URLs in a background thread so the UI and screen reader remain responsive.

---

### 3. Screen Reader & `QAccessible` Focus Recovery Enhancement
- **Automatic Window-Switch Recovery**: Added `WindowActivate` focus tracking (`_last_focus_ref` and `_restore_accessibility_focus` in `gemvox/ui/main_window.py`) so switching away from Gemvox (`Alt+Tab`) and returning—or closing a modal dialog—gently re-syncs `QAccessible` / Win32 focus without focus ping-pong.
- **Lightweight `refresh_accessible_focus()` Helper**: Added `refresh_accessible_focus()` in `gemvox/ui/theme.py` and `refresh_win32_focus()` in `gemvox/ui/accessible_text.py` to keep `RICHEDIT50W` and Qt widgets synchronized smoothly without stuttering or disrupting caret position.

---

### 4. Updated Documentation, Guides & Diagnostics
- **Updated Help Guide (`F1`) & Welcome Tour**: Added `Ctrl+O` document formats, `Ctrl+G` Google Docs/URL workflow, and v1.2.1 `QAccessible` focus recovery notes in both English and Thai (`gemvox/ui/help_content.py`).
- **Updated `README.md`**: Reflected PySide6 Universal Design architecture, v1.2.1 features, dependencies, and keyboard shortcuts with clean plain-text formatting.
- **Expanded `test_gemvox.py`**: Added automated verification for `TXT`, `HTML`, `DOCX`, and `PDF` extraction, Google Docs URL parsing and restricted-access detection, `OpenGoogleDocsDialog` accessibility auditing (8 dialogs total), and `refresh_accessible_focus()` stability.
