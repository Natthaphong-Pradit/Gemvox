import ctypes
import os
import platform
import queue
import sys
import threading
import winsound
from pathlib import Path
from gemvox.config import config


def _get_candidate_dirs() -> list[Path]:
    """Return candidate directories where screen reader client DLLs may be located."""
    dirs = []
    # 1. Module's own lib directory and module directory
    mod_dir = Path(__file__).resolve().parent
    dirs.append(mod_dir / "lib")
    dirs.append(mod_dir)
    dirs.append(mod_dir.parent.parent)

    # 2. PyInstaller _MEIPASS and executable directory
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        dirs.append(exe_dir)
        dirs.append(exe_dir / "lib")
        dirs.append(exe_dir / "_internal")
        dirs.append(exe_dir / "_internal" / "gemvox" / "accessibility" / "lib")
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            mp = Path(meipass)
            dirs.append(mp)
            dirs.append(mp / "gemvox" / "accessibility" / "lib")
            dirs.append(mp / "lib")

    # 3. Current working directory
    dirs.append(Path.cwd())

    # 4. System NVDA installation directories
    prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    prog_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    dirs.append(Path(prog_files) / "NVDA")
    dirs.append(Path(prog_files_x86) / "NVDA")

    # Deduplicate while preserving order
    seen = set()
    unique_dirs = []
    for d in dirs:
        try:
            resolved = str(d)
            if resolved not in seen:
                seen.add(resolved)
                unique_dirs.append(d)
        except Exception:
            pass
    return unique_dirs


class ScreenReaderAnnouncer:
    """
    Handles direct active screen reader announcements and accessible audio feedback.
    Outputs exclusively through the active screen reader (no SAPI 5 speech synthesis,
    preventing overlapping voices with the user's screen reader).

    Supported Active Screen Readers:
    1. NVDA (via bundled nvdaControllerClient64.dll / nvdaControllerClient32.dll)
    2. JAWS (via FreedomSci.JawsApi COM interface)
    3. ZDSR / Zhengdu Screen Reader (via ZDSRAPI_x64.dll / ZDSRAPI.dll)
    4. Window-Eyes (via GWSpeak.Speak COM interface)
    5. PC Talker (via PCTKUSR64.dll / PCTKUSR.dll)
    6. System Access (via SAAPI32.dll)
    7. Dolphin SuperNova (via dolapi.dll)
    """

    def __init__(self):
        self._is_64bit = platform.architecture()[0] == "64bit"
        self._nvda_dll = None
        self._zdsr_dll = None
        self._zdsr_initialized = False
        self._pctalker_dll = None
        self._sa_dll = None
        self._dolphin_dll = None

        self._speech_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._worker_thread = None

        self._load_client_dlls()
        self._start_worker()

    def _find_and_load_dll(self, dll_names: list[str], use_cdll: bool = False):
        """Search candidate directories and load the first matching DLL for the current architecture."""
        loader = ctypes.cdll if use_cdll else ctypes.windll
        candidate_dirs = _get_candidate_dirs()

        for dll_name in dll_names:
            for d in candidate_dirs:
                full_path = d / dll_name
                if full_path.is_file():
                    try:
                        return loader.LoadLibrary(str(full_path))
                    except Exception:
                        pass
            # Also try direct load via Windows DLL search path
            try:
                return loader.LoadLibrary(dll_name)
            except Exception:
                pass
        return None

    def _load_client_dlls(self):
        # 1. NVDA Controller Client (64-bit / 32-bit)
        nvda_candidates = (
            ["nvdaControllerClient64.dll", "nvdaControllerClient.dll", "nvdaControllerClient32.dll"]
            if self._is_64bit
            else ["nvdaControllerClient32.dll", "nvdaControllerClient.dll", "nvdaControllerClient64.dll"]
        )
        self._nvda_dll = self._find_and_load_dll(nvda_candidates)
        if self._nvda_dll is not None:
            try:
                self._nvda_dll.nvdaController_speakText.argtypes = [ctypes.c_wchar_p]
                self._nvda_dll.nvdaController_brailleMessage.argtypes = [ctypes.c_wchar_p]
            except Exception:
                pass

        # 2. ZDSR Client (64-bit / 32-bit)
        zdsr_candidates = (
            ["ZDSRAPI_x64.dll", "ZDSRAPI.dll"]
            if self._is_64bit
            else ["ZDSRAPI.dll", "ZDSRAPI_x64.dll"]
        )
        self._zdsr_dll = self._find_and_load_dll(zdsr_candidates)

        # 3. PC Talker Client (64-bit / 32-bit)
        pct_candidates = (
            ["PCTKUSR64.dll", "PCTKUSR.dll"]
            if self._is_64bit
            else ["PCTKUSR.dll", "PCTKUSR64.dll"]
        )
        self._pctalker_dll = self._find_and_load_dll(pct_candidates, use_cdll=True)
        if self._pctalker_dll is not None:
            try:
                self._pctalker_dll.PCTKPRead.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
            except Exception:
                pass

        # 4. System Access (32-bit) & Dolphin (32-bit)
        if not self._is_64bit:
            self._sa_dll = self._find_and_load_dll(["SAAPI32.dll"])
            if self._sa_dll is not None:
                try:
                    self._sa_dll.SA_SayW.argtypes = [ctypes.c_wchar_p]
                    self._sa_dll.SA_BrlShowTextW.argtypes = [ctypes.c_wchar_p]
                except Exception:
                    pass
            self._dolphin_dll = self._find_and_load_dll(["dolapi.dll"])
            if self._dolphin_dll is not None:
                try:
                    self._dolphin_dll.DolAccess_Command.argtypes = [ctypes.c_wchar_p, ctypes.c_int, ctypes.c_int]
                    self._dolphin_dll.DolAccess_Action.argtypes = [ctypes.c_int]
                except Exception:
                    pass

    def _start_worker(self):
        self._worker_thread = threading.Thread(target=self._speech_loop, daemon=True)
        self._worker_thread.start()

    def _try_speak_nvda(self, text: str, interrupt: bool) -> bool:
        """Speak and braille via NVDA if NVDA is currently running."""
        if self._nvda_dll is None:
            # Retry loading in case DLL became available
            self._load_client_dlls()
        if self._nvda_dll is None:
            return False

        try:
            if hasattr(self._nvda_dll, "nvdaController_testIfRunning"):
                if self._nvda_dll.nvdaController_testIfRunning() != 0:
                    return False
            if interrupt and hasattr(self._nvda_dll, "nvdaController_cancelSpeech"):
                self._nvda_dll.nvdaController_cancelSpeech()
            res = self._nvda_dll.nvdaController_speakText(ctypes.c_wchar_p(text))
            if hasattr(self._nvda_dll, "nvdaController_brailleMessage"):
                try:
                    self._nvda_dll.nvdaController_brailleMessage(ctypes.c_wchar_p(text))
                except Exception:
                    pass
            return res == 0
        except Exception:
            return False

    def _try_speak_jaws(self, text: str, interrupt: bool, jaws_com) -> bool:
        """Speak and braille via JAWS if JAWS is currently running."""
        if jaws_com is None:
            return False
        try:
            jaws_running = False
            try:
                if ctypes.windll.user32.FindWindowW("JFWUI2", None) != 0:
                    jaws_running = True
            except Exception:
                pass

            if not jaws_running:
                return False

            res = jaws_com.SayString(text, bool(interrupt))
            try:
                safe_text = text.replace('"', "'")
                jaws_com.RunFunction(f'BrailleString("{safe_text}")')
            except Exception:
                pass
            return bool(res) or jaws_running
        except Exception:
            return False

    def _try_speak_zdsr(self, text: str, interrupt: bool) -> bool:
        """Speak via ZDSR screen reader if running."""
        if self._zdsr_dll is None:
            return False
        try:
            if not self._zdsr_initialized:
                self._zdsr_dll.InitTTS(0, ctypes.c_wchar_p(""))
                self._zdsr_initialized = True
            if self._zdsr_dll.GetSpeakState() == 2:
                return False
            self._zdsr_dll.Speak(ctypes.c_wchar_p(text), ctypes.c_bool(interrupt))
            return True
        except Exception:
            return False

    def _try_speak_window_eyes(self, text: str, interrupt: bool, we_com) -> bool:
        """Speak via Window-Eyes if running."""
        if we_com is None:
            return False
        try:
            if ctypes.windll.user32.FindWindowW("GWMExternalControl", "External Control") == 0:
                return False
            if interrupt:
                we_com.Silence()
            we_com.SpeakString(text)
            return True
        except Exception:
            return False

    def _try_speak_other_dlls(self, text: str, interrupt: bool) -> bool:
        """Speak via PC Talker, System Access, or Dolphin if active."""
        # PC Talker
        if self._pctalker_dll is not None:
            try:
                if self._pctalker_dll.PCTKStatus() != 0:
                    if interrupt:
                        self._pctalker_dll.PCTKVReset()
                    self._pctalker_dll.PCTKPRead(text.encode("cp932", "replace"), 0, 1)
                    return True
            except Exception:
                pass

        # System Access
        if self._sa_dll is not None:
            try:
                if self._sa_dll.SA_IsRunning():
                    self._sa_dll.SA_SayW(ctypes.c_wchar_p(text))
                    return True
            except Exception:
                pass

        # Dolphin
        if self._dolphin_dll is not None:
            try:
                if self._dolphin_dll.DolAccess_GetSystem() in (1, 4, 8):
                    if interrupt:
                        self._dolphin_dll.DolAccess_Action(141)
                    self._dolphin_dll.DolAccess_Command(ctypes.c_wchar_p(text), (len(text) * 2) + 2, 1)
                    return True
            except Exception:
                pass

        return False

    def _speech_loop(self):
        # Background thread for non-blocking screen reader output
        jaws_com = None
        we_com = None
        com_initialized = False

        try:
            import pythoncom
            pythoncom.CoInitialize()
            com_initialized = True
        except Exception:
            pass

        while not self._stop_event.is_set():
            try:
                item = self._speech_queue.get(timeout=0.2)
                if item is None:
                    break
                text, interrupt = item

                # Check config setting
                if not config.get("speech_announcements", True):
                    self._speech_queue.task_done()
                    continue

                # If interrupt is requested, drain any older pending announcements in queue
                # so only the latest announcement is spoken without lag
                if interrupt:
                    while True:
                        try:
                            next_item = self._speech_queue.get_nowait()
                            if next_item is None:
                                self._speech_queue.put(None)
                                break
                            self._speech_queue.task_done()
                            text, interrupt = next_item
                        except queue.Empty:
                            break

                spoken = False

                # 1. Try NVDA first (via nvdaControllerClient64.dll / nvdaControllerClient32.dll)
                if self._try_speak_nvda(text, interrupt):
                    spoken = True

                # 2. Try JAWS (if NVDA did not handle it)
                if not spoken and com_initialized:
                    try:
                        if ctypes.windll.user32.FindWindowW("JFWUI2", None) != 0:
                            if jaws_com is None:
                                import win32com.client
                                jaws_com = win32com.client.Dispatch("FreedomSci.JawsApi")
                            spoken = self._try_speak_jaws(text, interrupt, jaws_com)
                    except Exception:
                        jaws_com = None

                # 3. Try ZDSR
                if not spoken:
                    spoken = self._try_speak_zdsr(text, interrupt)

                # 4. Try Window-Eyes
                if not spoken and com_initialized:
                    try:
                        if ctypes.windll.user32.FindWindowW("GWMExternalControl", "External Control") != 0:
                            if we_com is None:
                                import win32com.client
                                we_com = win32com.client.Dispatch("GWSpeak.Speak")
                            spoken = self._try_speak_window_eyes(text, interrupt, we_com)
                    except Exception:
                        we_com = None

                # 5. Try PC Talker / System Access / Dolphin
                if not spoken:
                    self._try_speak_other_dlls(text, interrupt)

                # NOTE: SAPI 5 fallback is intentionally removed so it never clashes
                # or overlaps with the user's active screen reader.

                self._speech_queue.task_done()
            except queue.Empty:
                continue
            except Exception:
                pass

        if com_initialized:
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except Exception:
                pass

    def announce(self, text: str, interrupt: bool = True):
        """Queue text to be spoken directly by the active screen reader."""
        if not text:
            return
        if config.get("speech_announcements", True):
            self._speech_queue.put((text, interrupt))

    def silence(self):
        """Immediately silence the active screen reader speech if supported."""
        if self._nvda_dll is not None:
            try:
                if (
                    hasattr(self._nvda_dll, "nvdaController_testIfRunning")
                    and self._nvda_dll.nvdaController_testIfRunning() == 0
                    and hasattr(self._nvda_dll, "nvdaController_cancelSpeech")
                ):
                    self._nvda_dll.nvdaController_cancelSpeech()
            except Exception:
                pass

    def play_sound(self, sound_type: str = "success"):
        """Plays accessible audio cues asynchronously without blocking UI."""
        if not config.get("sound_cues", True):
            return

        def _beep_worker():
            try:
                if sound_type == "success":
                    winsound.Beep(880, 100)
                    winsound.Beep(1174, 150)
                elif sound_type == "start":
                    winsound.Beep(587, 80)
                    winsound.Beep(784, 100)
                elif sound_type == "stop":
                    winsound.Beep(440, 120)
                elif sound_type == "error":
                    winsound.Beep(260, 250)
                elif sound_type == "click":
                    winsound.Beep(1200, 30)
                else:
                    winsound.MessageBeep(winsound.MB_OK)
            except Exception:
                pass

        threading.Thread(target=_beep_worker, daemon=True).start()

    def stop(self):
        self._stop_event.set()
        self._speech_queue.put(None)


# Global announcer instance
announcer = ScreenReaderAnnouncer()
