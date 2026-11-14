#!/usr/bin/env python3
"""
Gemvox v1.2.0 Diagnostic, Universal Design & Accessibility Verification Test Script.
Validates Python runtime, required packages, PySide6 GUI widgets,
UIA/MSAA accessibility metadata, wx-compatible keyboard navigation,
Gemini TTS engine, and Studio Audio Player deck.
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
    print(" GEMVOX v1.2.0 DIAGNOSTIC & UNIVERSAL DESIGN TEST")
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
            from gemvox.ui.theme import build_studio_stylesheet
            from gemvox.ui.main_window import MainWindow
            from gemvox.ui.dialogs import (
                HelpDialog,
                InlineTagDialog,
                StylePresetDialog,
                CreateCustomStyleDialog,
                WelcomeTourDialog,
                GenerationHistoryDialog,
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

            # Instantiate & audit all 7 dialogs
            for Dlg in (
                HelpDialog,
                InlineTagDialog,
                StylePresetDialog,
                CreateCustomStyleDialog,
                WelcomeTourDialog,
                GenerationHistoryDialog,
                UpdateDialog,
            ):
                d = Dlg(win)
                d_ok, d_msg = _verify_accessibility(d)
                if not d_ok:
                    print_result(f"Dialog Accessibility ({Dlg.__name__})", False, d_msg)
                    all_ok = False
                d.close()
                d.deleteLater()

            win.close()
            win.deleteLater()
            app.processEvents()
            print_result("PySide6 Universal Design UI & Dialogs Instantiation", True, "Zero errors")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print_result("PySide6 Universal Design UI & Dialogs Instantiation", False, str(e))
            all_ok = False

    print("=" * 65)
    if all_ok:
        print(" ALL DIAGNOSTIC TESTS PASSED! Gemvox v1.2.0 is ready to run.")
        print(" You can start Gemvox normally using 'Gemvox.bat' or 'python gemvox.py'.")
    else:
        print(" SOME CHECKS FAILED. Please review the missing dependencies above.")
        print(" To install missing packages, run: pip install -r requirements.txt")
    print("=" * 65)

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
