#!/usr/bin/env python3
"""
Gemvox: Accessible Gemini 3.8 Flash TTS Client.
Empowering blind and visually impaired creators with direct, accessible speech synthesis.
Developed by Natthaphong Pradit, with agentic AI companion.
"""

import os
import sys
import traceback

# Ensure project root is in sys.path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


def _attach_console_if_needed():
    if getattr(sys, "frozen", False):
        try:
            import ctypes
            # ATTACH_PARENT_PROCESS = -1
            if ctypes.windll.kernel32.AttachConsole(-1):
                sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
                sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
                sys.stdin = open("CONIN$", "r", encoding="utf-8", errors="replace")
        except Exception:
            pass


def _enable_windows_high_dpi():
    """Enable crisp Per-Monitor High-DPI scaling on Windows before wx.App creation."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def _has_interactive_stdin() -> bool:
    """Return True if sys.stdin is available and usable for interactive CLI input()."""
    if sys.stdin is None:
        return False
    try:
        if getattr(sys.stdin, "closed", False):
            return False
        # Under pythonw.exe on Windows, fileno() raises ValueError/io.UnsupportedOperation
        sys.stdin.fileno()
        return True
    except Exception:
        return False


def _report_startup_error(title: str, exc: BaseException):
    """Write traceback to gemvox_startup_error.log and show a native Windows dialog if needed."""
    tb_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    log_path = os.path.join(ROOT_DIR, "gemvox_startup_error.log")
    try:
        with open(log_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(tb_text)
    except Exception:
        pass

    msg = f"{title}:\n{exc}\n\nDetails written to:\n{log_path}"
    try:
        if sys.stderr is not None:
            print(msg, file=sys.stderr)
            print(tb_text, file=sys.stderr)
    except Exception:
        pass

    if sys.platform == "win32" and not _has_interactive_stdin():
        try:
            import ctypes
            # MB_OK | MB_ICONERROR = 0x00000010
            ctypes.windll.user32.MessageBoxW(0, msg, "Gemvox Startup Error", 0x00000010)
        except Exception:
            pass


def main():
    _attach_console_if_needed()

    try:
        from gemvox.cli import (
            parse_cli_args,
            run_interactive_cli,
            handle_speak,
            handle_dialogue,
            handle_voices,
            handle_design,
            handle_update,
        )
    except Exception as e:
        _report_startup_error("Failed to initialize Gemvox core dependencies", e)
        sys.exit(1)

    parser, args = parse_cli_args()

    # Route subcommands if provided
    if args.command == "speak":
        handle_speak(args)
        return
    elif args.command == "dialogue":
        handle_dialogue(args)
        return
    elif args.command == "voices":
        handle_voices(args)
        return
    elif args.command == "design":
        handle_design(args)
        return
    elif args.command == "update":
        handle_update(args)
        return

    # Check CLI flag
    if args.cli:
        run_interactive_cli()
        return

    # Default: launch Accessible wxPython GUI
    # IMPORTANT: Create wx.App(False) BEFORE importing MainWindow / theme so wx stock GDI
    # objects (wx.Colour, wx.Font) are always initialized after wx.App exists.
    try:
        _enable_windows_high_dpi()
        import wx
        app = wx.App(False)
        from gemvox.ui.main_window import MainWindow

        frame = MainWindow()
        frame.Show()
        app.MainLoop()
    except Exception as e:
        _report_startup_error("Could not launch Gemvox graphical interface", e)
        if _has_interactive_stdin():
            print("Falling back to accessible interactive console mode...\n")
            run_interactive_cli()
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
