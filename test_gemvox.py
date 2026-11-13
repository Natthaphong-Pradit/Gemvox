#!/usr/bin/env python3
"""
Gemvox Diagnostic & Environment Verification Test Script.
Validates Python runtime, required packages, wxPython GUI widgets,
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

def main():
    print("=" * 65)
    print(" GEMVOX v1.1.9 DIAGNOSTIC & ENVIRONMENT TEST")
    print("=" * 65)
    all_ok = True

    # 1. Python Version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 9)
    print_result(f"Python Runtime ({py_ver})", py_ok, "Requires Python 3.9+")
    if not py_ok:
        all_ok = False

    # 2. Dependency: wxPython
    wx_ok = False
    try:
        import wx
        wx_ver = getattr(wx, "__version__", "unknown")
        wx_ok = True
        print_result(f"wxPython Library (v{wx_ver})", True)
    except Exception as e:
        print_result("wxPython Library", False, str(e))
        all_ok = False

    # 3. Dependency: google-genai
    try:
        from google import genai
        print_result("google-genai SDK", True)
    except Exception as e:
        print_result("google-genai SDK", False, str(e))
        all_ok = False

    # 4. Dependency: sounddevice
    try:
        import sounddevice
        print_result("sounddevice Audio Driver", True)
    except Exception as e:
        print_result("sounddevice Audio Driver", False, str(e))
        all_ok = False

    # 5. Core modules
    try:
        from gemvox.config import config
        from gemvox.i18n import tr
        from gemvox.core.audio_player import audio_player
        from gemvox.core.client import client_manager
        from gemvox.core.tts_engine import tts_engine
        from gemvox.core.updater import check_for_updates
        print_result("Gemvox Core Modules (config, i18n, client, player, engine, updater)", True)
    except Exception as e:
        print_result("Gemvox Core Modules", False, str(e))
        all_ok = False

    # 6. GUI Subsystems (Instantiate wx.App and MainWindow)
    if wx_ok:
        try:
            app = wx.App(False)
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
            frame = MainWindow()
            for Dlg in (HelpDialog, InlineTagDialog, StylePresetDialog, CreateCustomStyleDialog, WelcomeTourDialog, GenerationHistoryDialog):
                d = Dlg(frame)
                d.Destroy()
            frame.Destroy()
            print_result("wxPython Accessible UI & Dialogs Instantiation", True, "Zero errors")
        except Exception as e:
            print_result("wxPython Accessible UI & Dialogs Instantiation", False, str(e))
            all_ok = False

    print("=" * 65)
    if all_ok:
        print(" ALL DIAGNOSTIC TESTS PASSED! Gemvox is ready to run.")
        print(" You can start Gemvox normally using 'Gemvox.bat' or 'python gemvox.py'.")
    else:
        print(" SOME CHECKS FAILED. Please review the missing dependencies above.")
        print(" To install missing packages, run: pip install -r requirements.txt")
    print("=" * 65)

    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()
