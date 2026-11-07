#!/usr/bin/env python3
"""
Gemvox: Accessible Gemini 3.8 Flash TTS Client.
Empowering blind and visually impaired creators with direct, accessible speech synthesis.
Developed by Natthaphong Pradit, with agentic AI companion.
"""

import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

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

from gemvox.cli import parse_cli_args, run_interactive_cli, handle_speak, handle_dialogue, handle_voices, handle_design

def main():
    _attach_console_if_needed()
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

    # Check CLI flag
    if args.cli:
        run_interactive_cli()
        return

    # Default: launch Accessible wxPython GUI
    try:
        from gemvox.ui.theme import enable_high_dpi
        enable_high_dpi()
        import wx
        from gemvox.ui.main_window import MainWindow

        app = wx.App(False)
        frame = MainWindow()
        frame.Show()
        app.MainLoop()
    except Exception as e:
        print(f"Could not launch graphical interface: {e}")
        print("Falling back to accessible interactive console mode...\n")
        run_interactive_cli()

if __name__ == "__main__":
    main()
