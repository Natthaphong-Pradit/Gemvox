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
from typing import List

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
- Fix 400 INVALID_ARGUMENT (Unknown name "speechConfig" at 'generation_config'):
  Resolves the Google AI Studio REST rejection by forcing the v1beta endpoint
  and typed GenerateContentConfig across single-speaker and multi-speaker synthesis.
- Automatic Multi-Model Fallback & 404 Resilience:
  Defaults to Universal AI Studio model (gemini-2.5-flash-preview-tts) with
  automatic fallback across Gemini 2.5 Flash, 3.1 Flash, 2.5 Pro, 3.8 Flash,
  and 2.0 Flash models, with seamless raw PCM-to-WAV RIFF wrapping.
- Studio Audio Player & Transport Deck Redesign:
  Full non-blocking studio transport controls across Single-Speaker,
  Multi-Speaker, Voice Design, and Recent Generations History (Ctrl+H):
  * Play / Pause / Resume toggle (Alt+P) & dedicated Stop (Alt+Q)
  * Rewind 5 Seconds (-5s, F7) & Fast-Forward 5 Seconds (+5s, F8)
  * Interactive Seek / Timeline Scrub Slider & MM:SS / MM:SS readout
  * Volume Slider (0% - 100%, F9 Volume Down / F10 Volume Up)
  * Playback Speed Selector (0.75x, 1.0x, 1.25x, 1.5x, 2.0x, Ctrl+Shift+P)
  * Loop Playback toggle (Ctrl+L)
- Direct GitHub Auto-Updater (Ctrl+U): Check for updates, download,
  and automatically install/reinstall the latest version directly from
  https://github.com/Natthaphong-Pradit/Gemvox without manual extraction.

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
- Alt+P             : Play / Pause / Resume Audio immediately
- Alt+Q             : Stop Audio & Reset to 00:00
- F7 / F8           : Rewind 5s (-5s) / Fast-Forward 5s (+5s)
- F9 / F10          : Volume Down (-10%) / Volume Up (+10%)
- Ctrl+L            : Toggle Loop Playback
- Ctrl+Shift+P      : Cycle Playback Speed (0.75x - 2.0x)
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


def run_step(cmd: List[str], desc: str):
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
