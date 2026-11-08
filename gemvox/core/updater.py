import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, Tuple

from gemvox import VERSION

REPO_OWNER = "Natthaphong-Pradit"
REPO_NAME = "Gemvox"
REPO_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}"
RELEASES_LATEST_API = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
RELEASES_LIST_API = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"
MAIN_INIT_API = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/gemvox/__init__.py?ref=main"
MAIN_COMMITS_API = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits/main"
MAIN_ZIP_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/archive/refs/heads/main.zip"

USER_AGENT = f"Gemvox-Updater/{VERSION} (+{REPO_URL})"


@dataclass
class UpdateInfo:
    current_version: str
    latest_version: str
    is_newer: bool
    install_mode: str  # "standalone_exe", "portable_dir", or "source"
    download_url: str
    asset_name: str
    asset_size_bytes: int
    release_title: str
    release_notes: str
    html_url: str
    published_at: str = ""
    error: str = ""


def parse_version(ver_str: str) -> Tuple[int, ...]:
    """Parse a semantic version string like 'v1.1.6' into a tuple of ints (1, 1, 6)."""
    cleaned = str(ver_str or "").strip().lstrip("vV")
    nums = re.findall(r"\d+", cleaned)
    if not nums:
        return (0, 0, 0)
    return tuple(int(n) for n in nums)


def detect_install_mode() -> str:
    """
    Detect how Gemvox is currently running:
    - 'standalone_exe': Single-file PyInstaller EXE (Gemvox_Standalone.exe)
    - 'portable_dir': Folder-based PyInstaller build (Gemvox.exe + _internal/)
    - 'source': Running from Python source (gemvox.py / Gemvox.bat)
    """
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        if (exe_dir / "_internal").is_dir():
            return "portable_dir"
        return "standalone_exe"
    return "source"


def get_app_root_dir() -> Path:
    """Return the root installation directory of Gemvox."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


def _http_get_json(url: str, timeout: int = 12) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _fetch_latest_release_data() -> Optional[dict]:
    try:
        data = _http_get_json(RELEASES_LATEST_API)
        if isinstance(data, dict) and data.get("tag_name"):
            return data
    except Exception:
        pass

    try:
        releases = _http_get_json(RELEASES_LIST_API)
        if isinstance(releases, list) and releases:
            for rel in releases:
                if isinstance(rel, dict) and not rel.get("draft"):
                    return rel
    except Exception:
        pass
    return None


def _fetch_main_branch_version() -> Tuple[Optional[str], str, str]:
    """Check gemvox/__init__.py on the main branch for the latest version string, commit notes, and date."""
    ver = None
    notes = ""
    pub_date = ""
    try:
        data = _http_get_json(MAIN_INIT_API)
        if isinstance(data, dict) and data.get("content"):
            raw_code = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            m = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', raw_code)
            if not m:
                m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', raw_code)
            if m:
                ver = m.group(1).strip()
    except Exception:
        pass

    if ver:
        try:
            commit_data = _http_get_json(MAIN_COMMITS_API)
            if isinstance(commit_data, dict):
                commit_obj = commit_data.get("commit", {})
                msg = commit_obj.get("message", "").strip()
                pub_date = commit_obj.get("committer", {}).get("date", "")
                sha = str(commit_data.get("sha", ""))[:7]
                notes = f"Latest main branch commit ({sha} - {pub_date}):\n\n{msg}"
        except Exception:
            notes = f"Direct update from {REPO_URL} (main branch)."

    return ver, notes, pub_date


def check_for_updates(
    current_version: Optional[str] = None,
    install_mode: Optional[str] = None,
) -> UpdateInfo:
    """
    Query the official GitHub repository (https://github.com/Natthaphong-Pradit/Gemvox)
    for the latest version and select the appropriate package for automatic installation.
    """
    mode = install_mode or detect_install_mode()
    curr_ver = current_version or VERSION
    curr_tuple = parse_version(curr_ver)

    try:
        release_data = _fetch_latest_release_data()
        rel_ver = None
        rel_tuple = (0, 0, 0)
        if release_data:
            rel_ver = str(release_data.get("tag_name", "")).lstrip("vV").strip()
            rel_tuple = parse_version(rel_ver)

        # Also check main branch version (especially useful for source mode or if main is ahead of releases)
        main_ver, main_notes, main_date = _fetch_main_branch_version()
        main_tuple = parse_version(main_ver) if main_ver else (0, 0, 0)

        # If running from source and main branch is >= release version, use main branch archive
        if mode == "source" and main_ver and main_tuple >= rel_tuple:
            is_newer = main_tuple > curr_tuple
            return UpdateInfo(
                current_version=curr_ver,
                latest_version=main_ver,
                is_newer=is_newer,
                install_mode=mode,
                download_url=MAIN_ZIP_URL,
                asset_name=f"{REPO_NAME}-main.zip",
                asset_size_bytes=0,
                release_title=f"Gemvox v{main_ver} (GitHub Main Repository)",
                release_notes=main_notes or f"Latest source code from {REPO_URL}",
                html_url=REPO_URL,
                published_at=main_date,
            )

        if release_data and rel_ver:
            assets = release_data.get("assets", []) or []
            exe_asset = None
            zip_asset = None
            for a in assets:
                name_lower = str(a.get("name", "")).lower()
                if name_lower.endswith(".exe"):
                    exe_asset = a
                elif name_lower.endswith(".zip"):
                    zip_asset = a

            chosen_url = ""
            chosen_name = ""
            chosen_size = 0

            if mode == "standalone_exe" and exe_asset:
                chosen_url = exe_asset.get("browser_download_url", "")
                chosen_name = exe_asset.get("name", "Gemvox_Standalone.exe")
                chosen_size = int(exe_asset.get("size", 0) or 0)
            elif mode == "portable_dir" and zip_asset:
                chosen_url = zip_asset.get("browser_download_url", "")
                chosen_name = zip_asset.get("name", f"Gemvox_v{rel_ver}_Portable.zip")
                chosen_size = int(zip_asset.get("size", 0) or 0)
            elif zip_asset and mode != "source":
                chosen_url = zip_asset.get("browser_download_url", "")
                chosen_name = zip_asset.get("name", f"Gemvox_v{rel_ver}_Portable.zip")
                chosen_size = int(zip_asset.get("size", 0) or 0)
            elif exe_asset and mode != "source":
                chosen_url = exe_asset.get("browser_download_url", "")
                chosen_name = exe_asset.get("name", "Gemvox_Standalone.exe")
                chosen_size = int(exe_asset.get("size", 0) or 0)
            else:
                chosen_url = release_data.get("zipball_url") or MAIN_ZIP_URL
                chosen_name = f"Gemvox-v{rel_ver}-source.zip"
                chosen_size = 0

            is_newer = rel_tuple > curr_tuple
            notes = str(release_data.get("body") or "").strip() or f"Official release Gemvox v{rel_ver}"
            title = str(release_data.get("name") or f"Gemvox v{rel_ver}").strip()
            html_url = str(release_data.get("html_url") or REPO_URL)
            pub_at = str(release_data.get("published_at") or "")

            return UpdateInfo(
                current_version=curr_ver,
                latest_version=rel_ver,
                is_newer=is_newer,
                install_mode=mode,
                download_url=chosen_url,
                asset_name=chosen_name,
                asset_size_bytes=chosen_size,
                release_title=title,
                release_notes=notes,
                html_url=html_url,
                published_at=pub_at,
            )

        if main_ver:
            is_newer = main_tuple > curr_tuple
            return UpdateInfo(
                current_version=curr_ver,
                latest_version=main_ver,
                is_newer=is_newer,
                install_mode=mode,
                download_url=MAIN_ZIP_URL,
                asset_name=f"{REPO_NAME}-main.zip",
                asset_size_bytes=0,
                release_title=f"Gemvox v{main_ver}",
                release_notes=main_notes or f"Direct repository update from {REPO_URL}",
                html_url=REPO_URL,
                published_at=main_date,
            )

        return UpdateInfo(
            current_version=curr_ver,
            latest_version=curr_ver,
            is_newer=False,
            install_mode=mode,
            download_url="",
            asset_name="",
            asset_size_bytes=0,
            release_title="",
            release_notes="",
            html_url=REPO_URL,
            error=f"Unable to reach GitHub repository at {REPO_URL}",
        )
    except Exception as e:
        return UpdateInfo(
            current_version=curr_ver,
            latest_version=curr_ver,
            is_newer=False,
            install_mode=mode,
            download_url="",
            asset_name="",
            asset_size_bytes=0,
            release_title="",
            release_notes="",
            html_url=REPO_URL,
            error=str(e),
        )


def _find_extracted_root(extract_dir: Path) -> Path:
    """If a zip archive contains a single top-level directory, return that directory."""
    entries = [p for p in extract_dir.iterdir() if not p.name.startswith("__MACOSX")]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return extract_dir


def download_and_install_update(
    update_info: UpdateInfo,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    relaunch: bool = True,
) -> Tuple[bool, str]:
    """
    Download the update package from GitHub and automatically install/reinstall it.
    Returns (ok, status_message).
    """
    staging_dir = Path(tempfile.mkdtemp(prefix="gemvox_update_"))
    try:
        download_path = staging_dir / (update_info.asset_name or "gemvox_update.zip")

        if progress_callback:
            progress_callback(5, f"Connecting to GitHub ({update_info.asset_name})")

        req = urllib.request.Request(
            update_info.download_url,
            headers={"User-Agent": USER_AGENT},
        )

        with urllib.request.urlopen(req, timeout=60) as resp:
            total_size = int(resp.headers.get("Content-Length", 0) or update_info.asset_size_bytes or 0)
            downloaded = 0
            chunk_size = 65536
            with open(download_path, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        if total_size > 0:
                            pct = min(85, max(5, int((downloaded * 85) / total_size)))
                            mb_done = downloaded / (1024 * 1024)
                            mb_total = total_size / (1024 * 1024)
                            stage = f"Downloading {update_info.asset_name} ({mb_done:.1f} / {mb_total:.1f} MB)"
                        else:
                            pct = 50
                            mb_done = downloaded / (1024 * 1024)
                            stage = f"Downloading {update_info.asset_name} ({mb_done:.1f} MB)"
                        progress_callback(pct, stage)

        if progress_callback:
            progress_callback(90, "Extracting and applying update files")

        mode = update_info.install_mode
        app_root = get_app_root_dir()

        # =========================================================================
        # CASE 1: Standalone Single-File EXE (Gemvox_Standalone.exe)
        # =========================================================================
        if mode == "standalone_exe" and download_path.suffix.lower() == ".exe":
            with open(download_path, "rb") as f:
                magic = f.read(2)
            if magic != b"MZ":
                shutil.rmtree(staging_dir, ignore_errors=True)
                return False, "Downloaded executable file is invalid or corrupted."

            target_exe = Path(sys.executable).resolve()
            bat_path = staging_dir / "gemvox_apply_update.bat"
            relaunch_line = f'start "" "{target_exe}"\r\n' if relaunch else ""
            bat_content = (
                "@echo off\r\n"
                "chcp 65001 >nul\r\n"
                "ping 127.0.0.1 -n 3 >nul\r\n"
                "set /a retries=0\r\n"
                ":retry\r\n"
                f'move /y "{download_path}" "{target_exe}" >nul 2>&1\r\n'
                "if errorlevel 1 (\r\n"
                "    set /a retries+=1\r\n"
                "    if %retries% lss 15 (\r\n"
                "        ping 127.0.0.1 -n 2 >nul\r\n"
                "        goto retry\r\n"
                "    )\r\n"
                ")\r\n"
                f"{relaunch_line}"
                f'rmdir /s /q "{staging_dir}" >nul 2>&1\r\n'
            )
            bat_path.write_text(bat_content, encoding="utf-8")
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            subprocess.Popen(["cmd.exe", "/c", str(bat_path)], creationflags=creationflags)
            if progress_callback:
                progress_callback(100, "Update ready. Restarting Gemvox")
            return True, f"Updated executable to v{update_info.latest_version}. Restarting..."

        # =========================================================================
        # CASE 2: Portable Folder Build (Gemvox.exe + _internal/)
        # =========================================================================
        if mode in ("portable_dir", "standalone_exe") and download_path.suffix.lower() == ".zip":
            extract_dir = staging_dir / "extracted"
            extract_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(download_path, "r") as zf:
                zf.extractall(extract_dir)
            inner_root = _find_extracted_root(extract_dir)

            # Protect user's output folder, .env, and portable config.json
            for protected in ("output", ".env", "config.json", "config.json.bak"):
                prot_path = inner_root / protected
                if prot_path.is_dir():
                    shutil.rmtree(prot_path, ignore_errors=True)
                elif prot_path.is_file():
                    prot_path.unlink(missing_ok=True)

            target_exe = Path(sys.executable).resolve()
            bat_path = Path(tempfile.gettempdir()) / f"gemvox_folder_update_{os.getpid()}.bat"
            relaunch_line = f'start "" "{target_exe}"\r\n' if relaunch else ""
            bat_content = (
                "@echo off\r\n"
                "chcp 65001 >nul\r\n"
                "ping 127.0.0.1 -n 3 >nul\r\n"
                f'xcopy "{inner_root}\\*" "{app_root}\\" /E /I /H /Y /Q >nul 2>&1\r\n'
                f"{relaunch_line}"
                f'rmdir /s /q "{staging_dir}" >nul 2>&1\r\n'
                'del "%~f0" >nul 2>&1\r\n'
            )
            bat_path.write_text(bat_content, encoding="utf-8")
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            subprocess.Popen(["cmd.exe", "/c", str(bat_path)], creationflags=creationflags)
            if progress_callback:
                progress_callback(100, "Update ready. Restarting Gemvox")
            return True, f"Updated portable package to v{update_info.latest_version}. Restarting..."

        # =========================================================================
        # CASE 3: Source Code Mode (python gemvox.py / Gemvox.bat)
        # =========================================================================
        extract_dir = staging_dir / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(download_path, "r") as zf:
            zf.extractall(extract_dir)
        inner_root = _find_extracted_root(extract_dir)

        # Clear stale bytecode caches before copying updated source files
        for pycache in app_root.rglob("__pycache__"):
            if "venv" not in pycache.parts and ".venv" not in pycache.parts:
                shutil.rmtree(pycache, ignore_errors=True)

        protected_names = {"venv", ".venv", ".env", "output", ".git", "__pycache__", "build", "dist", "config.json", "config.json.bak"}
        for item in inner_root.iterdir():
            if item.name in protected_names:
                continue
            dest = app_root / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

        # If .git exists, softly sync git metadata in background so future git status/pull stays clean
        if (app_root / ".git").is_dir():
            try:
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                subprocess.run(
                    ["git", "fetch", "origin", "main"],
                    cwd=str(app_root),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10,
                    creationflags=creationflags,
                )
                subprocess.run(
                    ["git", "reset", "--soft", "origin/main"],
                    cwd=str(app_root),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                    creationflags=creationflags,
                )
            except Exception:
                pass

        shutil.rmtree(staging_dir, ignore_errors=True)
        if progress_callback:
            progress_callback(100, "Update complete")
        if relaunch:
            relaunch_current_app()
        return True, f"Updated source files to v{update_info.latest_version}."
    except Exception as e:
        shutil.rmtree(staging_dir, ignore_errors=True)
        return False, str(e)


def relaunch_current_app():
    """Relaunch Gemvox when running from Python source mode."""
    if not getattr(sys, "frozen", False):
        app_root = get_app_root_dir()
        entry_script = app_root / "gemvox.py"
        exe_path = Path(sys.executable)
        pythonw_candidate = exe_path.with_name("pythonw.exe")
        launcher = str(pythonw_candidate) if pythonw_candidate.is_file() else str(exe_path)
        subprocess.Popen(
            [launcher, "-B", str(entry_script)],
            cwd=str(app_root),
        )

