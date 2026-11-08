#!/usr/bin/env python3
"""
Automated Release Builder & Packager for Gemvox.
Builds both:
1. dist/Gemvox_Standalone.exe (Single-file executable)
2. dist/Gemvox_v{VERSION}_Portable.zip (Portable folder package with portable.txt & README.txt)

Optionally uploads the built assets to the corresponding GitHub Release if --upload is passed.
"""

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from gemvox import VERSION

ROOT_DIR = Path(__file__).resolve().parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"

PORTABLE_TXT = f"""Portable mode enabled for Gemvox v{VERSION}.
Configuration and output files are stored inside this folder.
"""

README_TXT = f"""====================================================================
Gemvox v{VERSION} - Portable Edition (Obsidian & Royal Gold Edition)
Accessible Multi-Speaker AI Voice Studio powered by Google Gemini
====================================================================

WHAT'S NEW IN v{VERSION}:
- Direct GitHub Auto-Updater (Ctrl+U): Check for updates, download,
  and automatically install/reinstall the latest version directly from
  https://github.com/Natthaphong-Pradit/Gemvox without manual extraction.
- Real-Time Custom Voice Synchronization & Management: Newly created or
  replicated voices sync across all tabs immediately without restarting.
  Added "Use Selected Voice in TTS (Alt+Y)" and "Remove Custom Voice (Alt+R)".
- 100% Bilingual Screen Reader Localization (English & Thai): All spoken
  screen reader announcements, status bar messages, and dialogs are fully
  localized in both English and Thai.
- Recent Generations History Dialog (Ctrl+H): Browse, replay/stop (Enter /
  Alt+P), export copies (Alt+S), or delete (Alt+D) generated WAV files,
  plus open the output folder directly (Ctrl+Shift+O).
- Script & Text Productivity Tools: Open .txt scripts (Ctrl+O), save
  scripts (Ctrl+Shift+S), and announce Text & Script Statistics (Ctrl+I:
  word count, character count, line count, and estimated speech duration).
- 100% Shortcut & Mnemonic Consistency: Every button and control's '&'
  mnemonic matches its (Alt+Key) label 100% with zero collisions.

HOW TO RUN:
1. Run "Gemvox.exe" inside this folder.
2. Because "portable.txt" is present in this directory, Gemvox runs in
   Portable Mode:
   - Your settings and API keys are saved locally in "config.json".
   - Generated audio files are saved in the "output" folder by default.
3. Screen Reader Support:
   - NVDA (32-bit & 64-bit DLLs included), JAWS, ZDSR, PC Talker,
     Window-Eyes, System Access, and Dolphin are supported natively
     without SAPI 5 interference.

KEYBOARD SHORTCUTS:
- F1                : Open User Guide & Keyboard Shortcuts (6 Chapters)
- Ctrl+Enter / Alt+G: Generate Speech / Dialogue / Voice Design
- Alt+P             : Play / Stop Audio immediately
- Ctrl+S / Alt+S    : Save Audio File as WAV
- Ctrl+O            : Open .txt Text / Script File
- Ctrl+Shift+S      : Save Text / Script File As .txt
- Ctrl+H            : Recent Generations History Dialog
- Ctrl+Shift+O      : Open Output Folder in File Explorer
- Ctrl+I            : Announce Text & Script Statistics
- Ctrl+U            : Check for Updates & Direct Auto-Installer
- Ctrl+1 .. Ctrl+6  : Switch directly to Tab 1 through Tab 6 (also Alt+1..6)
====================================================================
"""


def run_step(cmd: list[str], desc: str):
    print(f"\n=== {desc} ===")
    print("Running:", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, cwd=str(ROOT_DIR), check=True)


def build_all(upload: bool = False):
    if sys.platform != "win32":
        print("Error: Windows (.exe) PyInstaller builds must be run on Windows (or via GitHub Actions windows-latest).")
        sys.exit(1)

    # Clean previous build artifacts
    for d in (BUILD_DIR, DIST_DIR):
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)

    # Ensure PyInstaller is installed
    run_step([sys.executable, "-m", "PyInstaller", "--version"], "Checking PyInstaller")

    # 1. Build Portable Folder Edition (dist/Gemvox)
    run_step(
        [sys.executable, "-m", "PyInstaller", "Gemvox.spec", "--noconfirm", "--clean"],
        f"Building Gemvox v{VERSION} Portable Folder Edition",
    )

    portable_folder = DIST_DIR / "Gemvox"
    if not portable_folder.is_dir():
        raise RuntimeError(f"Expected portable folder at {portable_folder} was not created.")

    (portable_folder / "portable.txt").write_text(PORTABLE_TXT, encoding="utf-8")
    (portable_folder / "README.txt").write_text(README_TXT, encoding="utf-8")

    zip_name = f"Gemvox_v{VERSION}_Portable.zip"
    zip_path = DIST_DIR / zip_name
    print(f"\n=== Packaging {zip_name} ===")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for file_path in portable_folder.rglob("*"):
            arcname = Path("Gemvox") / file_path.relative_to(portable_folder)
            zf.write(file_path, str(arcname))
    print(f"Created: {zip_path} ({zip_path.stat().st_size / (1024 * 1024):.2f} MB)")

    # 2. Build Standalone Single-File EXE (dist/Gemvox_Standalone.exe)
    run_step(
        [sys.executable, "-m", "PyInstaller", "Gemvox_Standalone.spec", "--noconfirm", "--clean"],
        f"Building Gemvox v{VERSION} Standalone EXE Edition",
    )

    standalone_exe = DIST_DIR / "Gemvox_Standalone.exe"
    if not standalone_exe.is_file():
        raise RuntimeError(f"Expected standalone EXE at {standalone_exe} was not created.")
    print(f"Created: {standalone_exe} ({standalone_exe.stat().st_size / (1024 * 1024):.2f} MB)")

    if upload:
        tag = f"v{VERSION}"
        run_step(
            ["gh", "release", "upload", tag, str(standalone_exe), str(zip_path), "--clobber"],
            f"Uploading release assets to GitHub Release {tag}",
        )

    print("\n====================================================================")
    print(f"BUILD COMPLETE FOR GEMVOX v{VERSION}")
    print(f"  1. {standalone_exe}")
    print(f"  2. {zip_path}")
    print("====================================================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Gemvox Windows Release Packages")
    parser.add_argument("--upload", action="store_true", help="Upload built assets to GitHub Release via gh CLI")
    args = parser.parse_args()
    build_all(upload=args.upload)
