import io
import os
import tempfile
import threading
import time
import wave
from typing import Callable, List, Optional
from gemvox.i18n import tr
from gemvox.accessibility import announcer

try:
    import sounddevice as sd
except ImportError:
    sd = None

try:
    import winsound
except ImportError:
    winsound = None


class AudioPlayer:
    """
    Non-blocking, thread-safe audio player for WAV speech synthesis.
    Optimized for Windows accessibility with zero UI lag on stop/interrupt.
    """
    def __init__(self):
        self._current_thread: Optional[threading.Thread] = None
        self._stop_requested = threading.Event()
        self._is_playing = False
        self._active_stream = None
        self._temp_fallback_file: Optional[str] = None
        self._lock = threading.Lock()
        self._listeners: List[Callable[[bool], None]] = []

    @property
    def is_playing(self) -> bool:
        with self._lock:
            return self._is_playing

    def add_state_listener(self, callback: Callable[[bool], None]):
        """Register a callback invoked when playback starts (True) or finishes/stops (False)."""
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def remove_state_listener(self, callback: Callable[[bool], None]):
        """Unregister a state listener callback."""
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)

    def set_state_listener(self, callback: Callable[[bool], None]):
        """Backwards compatibility alias for add_state_listener."""
        self.add_state_listener(callback)

    def _notify_state_change(self, is_playing: bool):
        with self._lock:
            callbacks = list(self._listeners)
        for cb in callbacks:
            try:
                cb(is_playing)
            except Exception:
                pass

    def play_wav_bytes(self, wav_bytes: bytes, announce_on_start: bool = True):
        """Play WAV audio directly from bytes in memory without blocking the UI thread."""
        self.stop()

        if not wav_bytes:
            return

        self._stop_requested.clear()

        def _play_worker():
            with self._lock:
                self._is_playing = True
            self._notify_state_change(True)

            if announce_on_start:
                announcer.announce(tr("announce_playing_audio"), interrupt=False)

            played_via_sd = False

            # 1. Primary method: sounddevice streaming (instant stop, zero UI blocking)
            if sd is not None:
                try:
                    with wave.open(io.BytesIO(wav_bytes), 'rb') as wf:
                        rate = wf.getframerate()
                        channels = wf.getnchannels()
                        width = wf.getsampwidth()
                        raw_data = wf.readframes(wf.getnframes())

                    dtype_map = {1: 'int8', 2: 'int16', 4: 'int32'}
                    dtype = dtype_map.get(width, 'int16')

                    with sd.RawOutputStream(samplerate=rate, channels=channels, dtype=dtype) as stream:
                        with self._lock:
                            self._active_stream = stream
                        chunk_size = 4096
                        for i in range(0, len(raw_data), chunk_size):
                            if self._stop_requested.is_set():
                                break
                            chunk = raw_data[i:i + chunk_size]
                            stream.write(chunk)
                    played_via_sd = True
                except Exception:
                    played_via_sd = False

            # 2. Fallback method: asynchronous file playback via winsound (SND_ASYNC)
            if not played_via_sd and not self._stop_requested.is_set() and winsound is not None:
                temp_path = None
                try:
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tf:
                        temp_path = tf.name
                        tf.write(wav_bytes)
                    with self._lock:
                        self._temp_fallback_file = temp_path

                    duration = 3.0
                    try:
                        with wave.open(io.BytesIO(wav_bytes), 'rb') as wf:
                            duration = wf.getnframes() / float(wf.getframerate())
                    except Exception:
                        pass

                    # SND_ASYNC returns immediately and can be cleanly stopped
                    winsound.PlaySound(temp_path, winsound.SND_FILENAME | winsound.SND_ASYNC)

                    start_t = time.time()
                    while time.time() - start_t < duration and not self._stop_requested.is_set():
                        time.sleep(0.05)

                    if not self._stop_requested.is_set():
                        winsound.PlaySound(None, 0)
                except Exception as ex:
                    announcer.announce(tr("announce_playback_error", error=ex))
                finally:
                    if temp_path:
                        try:
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                        except Exception:
                            pass
                    with self._lock:
                        if self._temp_fallback_file == temp_path:
                            self._temp_fallback_file = None

            # Reset playing state and notify listeners
            with self._lock:
                self._is_playing = False
                self._active_stream = None
            self._notify_state_change(False)

        self._current_thread = threading.Thread(target=_play_worker, daemon=True)
        self._current_thread.start()

    def play_file(self, filepath: str, announce_on_start: bool = True):
        """Play WAV audio from a file path."""
        if not os.path.exists(filepath):
            announcer.announce(tr("announce_file_not_found", path=filepath))
            return
        try:
            with open(filepath, "rb") as f:
                self.play_wav_bytes(f.read(), announce_on_start=announce_on_start)
        except Exception as e:
            announcer.announce(tr("announce_read_audio_error", error=e))

    def stop(self):
        """Immediately and non-blockingly stop any playing audio."""
        with self._lock:
            if not self._is_playing:
                return
            self._stop_requested.set()
            stream = self._active_stream
            fallback_file = self._temp_fallback_file
            self._is_playing = False
            self._active_stream = None
            self._temp_fallback_file = None

        # Instantly abort sounddevice stream
        if stream is not None:
            try:
                stream.abort()
            except Exception:
                pass

        # Instantly stop winsound async sound
        if fallback_file is not None and winsound is not None:
            try:
                winsound.PlaySound(None, 0)
            except Exception:
                pass
            try:
                if os.path.exists(fallback_file):
                    os.remove(fallback_file)
            except Exception:
                pass

        self._notify_state_change(False)
        announcer.announce(tr("announce_audio_stopped"), interrupt=True)
        announcer.play_sound("stop")


# Global AudioPlayer instance
audio_player = AudioPlayer()
