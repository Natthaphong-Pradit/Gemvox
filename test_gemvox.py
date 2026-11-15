#!/usr/bin/env python3
"""
Gemvox v1.2.1 Diagnostic, Universal Design & Accessibility Verification Test Script.
Validates Python runtime, required packages, PySide6 GUI widgets,
UIA/MSAA accessibility metadata, wx-compatible keyboard navigation,
document loaders (TXT/HTML/DOCX/PDF/Google Docs), Gemini TTS engine, and Audio Player.
"""

import sys
import os

# Ensure project root is in sys.path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


def print_result(label: str, ok: bool, details: str = ""):
    status = "[PASS]" if ok else "[FAIL]"
    extra = f" - {details}" if details else ""
    print(f"  {status:7s} {label}{extra}")


def _verify_accessibility(root_widget) -> tuple[bool, str]:
    """Audit interactive widgets for Universal Design & Screen Reader accessibility."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QLineEdit,
        QListWidget,
        QPlainTextEdit,
        QPushButton,
        QRadioButton,
        QSlider,
        QWidget,
    )
    from gemvox.ui.accessible_text import AccessibleTextArea

    interactive_types = (
        QPushButton,
        QLineEdit,
        QPlainTextEdit,
        AccessibleTextArea,
        QComboBox,
        QCheckBox,
        QRadioButton,
        QSlider,
        QListWidget,
    )
    checked = 0
    for w in root_widget.findChildren(QWidget):
        if not isinstance(w, interactive_types):
            continue
        checked += 1
        acc_name = w.accessibleName().strip()
        if not acc_name:
            return False, f"Missing accessibleName on {type(w).__name__} (objectName={w.objectName()!r})"
        if isinstance(w, (QPlainTextEdit, AccessibleTextArea)) and not w.tabChangesFocus():
            return False, f"Multiline editor '{acc_name}' must have tabChangesFocus=True"
    return True, f"Audited {checked} interactive controls"


def main():
    print("=" * 65)
    print(" GEMVOX v1.2.2 DIAGNOSTIC & UNIVERSAL DESIGN TEST")
    print("=" * 65)
    all_ok = True

    # 1. Python Version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 9)
    print_result(f"Python Runtime ({py_ver})", py_ok, "Requires Python 3.9+")
    if not py_ok:
        all_ok = False

    # 2. Dependency: PySide6
    qt_ok = False
    try:
        import PySide6
        qt_ver = getattr(PySide6, "__version__", "unknown")
        qt_ok = True
        print_result(f"PySide6 Library (v{qt_ver})", True)
    except Exception as e:
        print_result("PySide6 Library", False, str(e))
        all_ok = False

    # 3. Dependency: google-genai
    try:
        from google import genai  # noqa: F401
        print_result("google-genai SDK", True)
    except Exception as e:
        print_result("google-genai SDK", False, str(e))
        all_ok = False

    # 4. Dependency: sounddevice
    try:
        import sounddevice  # noqa: F401
        print_result("sounddevice Audio Driver", True)
    except Exception as e:
        print_result("sounddevice Audio Driver", False, str(e))
        all_ok = False

    # 5. Core modules
    try:
        from gemvox import VERSION
        from gemvox.config import config  # noqa: F401
        from gemvox.i18n import tr  # noqa: F401
        from gemvox.core.audio_player import audio_player  # noqa: F401
        from gemvox.core.client import client_manager  # noqa: F401
        from gemvox.core.tts_engine import tts_engine  # noqa: F401
        from gemvox.core.updater import check_for_updates  # noqa: F401
        print_result(f"Gemvox Core Modules (v{VERSION})", True)
    except Exception as e:
        print_result("Gemvox Core Modules", False, str(e))
        all_ok = False

    # 6. PySide6 Universal Design UI, Dialogs & Accessibility Audit
    if qt_ok:
        try:
            from PySide6.QtCore import Qt
            from PySide6.QtWidgets import QApplication
            from gemvox.ui.theme import build_studio_stylesheet, refresh_accessible_focus
            from gemvox.ui.main_window import MainWindow
            from gemvox.ui.dialogs import (
                HelpDialog,
                InlineTagDialog,
                StylePresetDialog,
                CreateCustomStyleDialog,
                WelcomeTourDialog,
                GenerationHistoryDialog,
                OpenGoogleDocsDialog,
                UpdateDialog,
            )

            app = QApplication.instance() or QApplication(sys.argv)
            app.setStyle("Fusion")
            app.setStyleSheet(build_studio_stylesheet())

            win = MainWindow()
            assert win.tabs.count() == 6, f"Expected 6 tabs, got {win.tabs.count()}"
            assert win.tabs.tabBar().focusPolicy() == Qt.StrongFocus, "TabBar must have StrongFocus"

            # Verify keyboard tab switching simulation
            win.switch_tab(1)
            assert win.tabs.currentIndex() == 1
            win.cycle_tab(forward=True)
            assert win.tabs.currentIndex() == 2
            win.cycle_tab(forward=False)
            assert win.tabs.currentIndex() == 1
            win.switch_tab(0)
            assert win.tabs.currentIndex() == 0

            # Verify text area clear/insert/read-only caret does not crash
            win.tab_single.on_clear()
            assert win.tab_single.text_ctrl.toPlainText() == ""
            win.tab_single.text_ctrl.setPlainText("Hello world")
            win.tab_single.text_ctrl.insert_text_at_selection("<sigh>")
            assert "<sigh>" in win.tab_single.text_ctrl.toPlainText()

            # Verify accessibility metadata across all 6 tabs
            acc_ok, acc_msg = _verify_accessibility(win)
            print_result("Universal Design Accessibility Audit (MainWindow)", acc_ok, acc_msg)
            if not acc_ok:
                all_ok = False

            # Instantiate & audit all 8 dialogs
            for Dlg in (
                HelpDialog,
                InlineTagDialog,
                StylePresetDialog,
                CreateCustomStyleDialog,
                WelcomeTourDialog,
                GenerationHistoryDialog,
                OpenGoogleDocsDialog,
                UpdateDialog,
            ):
                d = Dlg(win)
                d_ok, d_msg = _verify_accessibility(d)
                if not d_ok:
                    print_result(f"Dialog Accessibility ({Dlg.__name__})", False, d_msg)
                    all_ok = False
                d.close()
                d.deleteLater()

            # Verify focus refresh & recovery helpers do not raise
            refresh_accessible_focus(win.tabs.tabBar(), force_nudge=True)
            refresh_accessible_focus(win.tab_single.text_ctrl, force_nudge=True)
            win._restore_accessibility_focus()

            win.close()
            win.deleteLater()
            app.processEvents()
            print_result("PySide6 Universal Design UI & Dialogs Instantiation", True, "Zero errors")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print_result("PySide6 Universal Design UI & Dialogs Instantiation", False, str(e))
            all_ok = False

    # 7. Document Loader Verification (TXT, HTML, DOCX, PDF, Google Docs)
    try:
        import tempfile
        import urllib.request
        from pathlib import Path
        from unittest.mock import patch
        from gemvox.core.document_loader import (
            GoogleDocsAccessError,
            extract_google_doc_info,
            load_document_from_file,
            load_document_from_url,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            # TXT
            txt_p = tmp / "sample.txt"
            txt_p.write_text("Hello Gemvox 1.2.1", encoding="utf-8")
            assert load_document_from_file(txt_p) == "Hello Gemvox 1.2.1"

            # HTML
            html_p = tmp / "sample.html"
            html_p.write_text(
                "<html><head><style>p{color:red}</style></head>"
                "<body><script>alert(1)</script><h1>Title</h1><p>Body text</p></body></html>",
                encoding="utf-8",
            )
            html_out = load_document_from_file(html_p)
            assert "Title" in html_out and "Body text" in html_out and "alert(1)" not in html_out

            # DOCX
            import docx
            docx_p = tmp / "sample.docx"
            doc = docx.Document()
            doc.add_paragraph("DOCX Paragraph One")
            doc.save(str(docx_p))
            assert "DOCX Paragraph One" in load_document_from_file(docx_p)

            # PDF (via minimal valid PDF bytes)
            pdf_p = tmp / "sample.pdf"
            minimal_pdf = (
                b"%PDF-1.4\n"
                b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
                b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
                b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] "
                b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
                b"4 0 obj << /Length 44 >> stream\n"
                b"BT /F1 12 Tf 10 100 Td (Hello PDF) Tj ET\n"
                b"endstream endobj\n"
                b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
                b"xref\n0 6\n0000000000 65535 f \n"
                b"0000000009 00000 n \n0000000058 00000 n \n"
                b"0000000115 00000 n \n0000000241 00000 n \n"
                b"0000000335 00000 n \n"
                b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n405\n%%EOF\n"
            )
            pdf_p.write_bytes(minimal_pdf)
            assert "Hello PDF" in load_document_from_file(pdf_p)

        # Google Docs URL parsing & restricted-access detection
        doc_id, is_pub = extract_google_doc_info("https://docs.google.com/document/d/AbC123_xyz/edit?usp=sharing")
        assert doc_id == "AbC123_xyz" and not is_pub

        class _FakeResp:
            def __init__(self, url, ct, data):
                self._url = url
                self.headers = _FakeHeaders(ct)
                self._data = data
            def geturl(self):
                return self._url
            def read(self):
                return self._data
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False

        class _FakeHeaders:
            def __init__(self, ct):
                self._ct = ct
            def get(self, k, default=""):
                return self._ct if k.lower() == "content-type" else default
            def get_content_charset(self):
                return "utf-8"

        # Accessible Google Doc
        with patch.object(
            urllib.request,
            "urlopen",
            return_value=_FakeResp(
                "https://docs.google.com/document/d/AbC123_xyz/export?format=txt",
                "text/plain; charset=utf-8",
                b"\xef\xbb\xbfShared Google Doc Content",
            ),
        ):
            g_text, _ = load_document_from_url("https://docs.google.com/document/d/AbC123_xyz/edit")
            assert g_text == "Shared Google Doc Content"

        # Restricted Google Doc (redirected to accounts.google.com)
        restricted_raised = False
        with patch.object(
            urllib.request,
            "urlopen",
            return_value=_FakeResp(
                "https://accounts.google.com/v3/signin/identifier",
                "text/html; charset=utf-8",
                b"<html><body>Sign in</body></html>",
            ),
        ):
            try:
                load_document_from_url("https://docs.google.com/document/d/AbC123_xyz/edit")
            except GoogleDocsAccessError as exc:
                restricted_raised = exc.reason == "restricted"
        assert restricted_raised, "Expected GoogleDocsAccessError('restricted')"

        print_result("Document Loader (TXT, HTML, DOCX, PDF, Google Docs)", True)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print_result("Document Loader (TXT, HTML, DOCX, PDF, Google Docs)", False, str(e))
        all_ok = False

    # 9. Security (DPAPI + Migration + Honeypot + Env Priority) & Progress Tracker & UTF-8 0x92
    try:
        import json
        import tempfile
        from pathlib import Path
        from gemvox.security import (
            DECOY_API_KEY,
            decrypt_secret,
            encrypt_secret,
            is_decoy_api_key,
            load_encrypted_api_key,
            save_encrypted_api_key,
        )
        from gemvox.core.document_loader import read_text_with_fallback
        from gemvox.ui.progress_tracker import SynthesisProgressTracker, estimate_synthesis_seconds

        # 9a. DPAPI round-trip
        sample_key = "AIzaSyTestRoundTripKey1234567890"
        enc = encrypt_secret(sample_key)
        assert enc and enc != sample_key
        assert decrypt_secret(enc) == sample_key

        # 9b. Separate secrets.dat save/load + decoy check
        with tempfile.TemporaryDirectory() as tmpdir:
            sec_path = Path(tmpdir) / "secrets.dat"
            assert save_encrypted_api_key(sec_path, sample_key) is True
            assert load_encrypted_api_key(sec_path) == sample_key
            assert is_decoy_api_key(DECOY_API_KEY) is True
            assert is_decoy_api_key(sample_key) is False

            # 9c. UTF-8 0x92 (cp1252 smart apostrophe) fallback
            win1252_file = Path(tmpdir) / "smart_quote.txt"
            win1252_file.write_bytes(b"It\x92s a Gemvox test")
            decoded = read_text_with_fallback(win1252_file)
            assert "Gemvox test" in decoded and "\u2019" in decoded

        # 9d. Progress estimation formula
        assert abs(estimate_synthesis_seconds(0) - 1.5) < 1e-6
        assert abs(estimate_synthesis_seconds(250) - 6.5) < 1e-6
        tracker = SynthesisProgressTracker()
        tracker.start(250)
        assert tracker.is_running is True
        tracker.finish(success=True)
        assert tracker.is_running is False and tracker.percent == 100

        print_result("Security (DPAPI & Decoy), UTF-8 Fallback & Progress Tracker", True)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print_result("Security (DPAPI & Decoy), UTF-8 Fallback & Progress Tracker", False, str(e))
        all_ok = False

    print("=" * 65)
    if all_ok:
        print(" ALL DIAGNOSTIC TESTS PASSED! Gemvox v1.2.2 is ready to run.")
        print(" You can start Gemvox normally using 'Gemvox.bat' or 'python gemvox.py'.")
    else:
        print(" SOME CHECKS FAILED. Please review the missing dependencies above.")
        print(" To install missing packages, run: pip install -r requirements.txt")
    print("=" * 65)

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
