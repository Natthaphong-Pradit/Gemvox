import array
import io
import os
import tempfile
import threading
import time
import wave
from typing import Callable, List, Optional
from gemvox.config import config
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

SPEED_PRESETS: List[float] = [0.75, 1.0, 1.25, 1.5, 2.0]


def format_mm_ss(seconds: float) -> str:
    """Format seconds as MM:SS."""
    sec = max(0, int(round(seconds)))
    mins = sec // 60
    rem = sec % 60
    return f"{mins:02d}:{rem:02d}"


class AudioPlayer:
    """
    Studio-grade, non-blocking, thread-safe audio player for WAV speech synthesis.
    Supports Play, Pause/Resume, Stop, Seek/Scrub (-5s/+5s & slider), Volume (0-100%),
    Playback Speed (0.75x - 2.0x), and Loop playback with zero UI lag.
    """

    def __init__(self):
        self._current_thread: Optional[threading.Thread] = None
        self._stop_requested = threading.Event()
        self._is_playing = False
        self._is_paused = False
        self._active_stream = None
        self._temp_fallback_file: Optional[str] = None
        self._lock = threading.RLock()

        # Loaded audio buffer & transport position
        self._wav_bytes: Optional[bytes] = None
        self._raw_pcm: bytes = b""
        self._sample_rate: int = 24000
        self._channels: int = 1
        self._sampwidth: int = 2
        self._total_frames: int = 0
        self._current_frame: int = 0

        # Studio playback parameters
        self._volume: int = max(0, min(100, int(config.get("player_volume", 100))))
        raw_speed = float(config.get("player_speed", 1.0))
        self._speed: float = raw_speed if raw_speed in SPEED_PRESETS else 1.0
        self._loop: bool = bool(config.get("player_loop", False))

        # Listeners
        self._listeners: List[Callable[[bool], None]] = []
        # Transport listeners receive: (state: str, current_sec: float, total_sec: float)
        # where state is "playing", "paused", or "stopped"
        self._transport_listeners: List[Callable[[str, float, float], None]] = []

    @property
    def is_playing(self) -> bool:
        with self._lock:
            return self._is_playing and not self._is_paused

    @property
    def is_paused(self) -> bool:
        with self._lock:
            return self._is_paused

    @property
    def is_active(self) -> bool:
        with self._lock:
            return self._is_playing or self._is_paused

    @property
    def has_audio(self) -> bool:
        with self._lock:
            return self._total_frames > 0 and bool(self._raw_pcm)

    @property
    def current_time(self) -> float:
        with self._lock:
            if self._sample_rate <= 0 or self._total_frames <= 0:
                return 0.0
            tot = self._total_frames / float(self._sample_rate)
            return min(tot, self._current_frame / float(self._sample_rate))

    @property
    def duration(self) -> float:
        with self._lock:
            if self._sample_rate <= 0 or self._total_frames <= 0:
                return 0.0
            return self._total_frames / float(self._sample_rate)

    @property
    def volume(self) -> int:
        with self._lock:
            return self._volume

    @property
    def speed(self) -> float:
        with self._lock:
            return self._speed

    @property
    def loop(self) -> bool:
        with self._lock:
            return self._loop

    @property
    def state_name(self) -> str:
        with self._lock:
            if self._is_paused:
                return "paused"
            if self._is_playing:
                return "playing"
            return "stopped"

    def add_state_listener(self, callback: Callable[[bool], None]):
        """Register a callback invoked when active playback starts (True) or pauses/stops (False)."""
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

    def add_transport_listener(self, callback: Callable[[str, float, float], None]):
        """Register a callback receiving (state, current_sec, total_sec)."""
        with self._lock:
            if callback not in self._transport_listeners:
                self._transport_listeners.append(callback)

    def remove_transport_listener(self, callback: Callable[[str, float, float], None]):
        with self._lock:
            if callback in self._transport_listeners:
                self._transport_listeners.remove(callback)

    def _notify_state_change(self, is_playing: bool):
        with self._lock:
            callbacks = list(self._listeners)
        for cb in callbacks:
            try:
                cb(is_playing)
            except Exception:
                pass
        self._notify_transport()

    def _notify_transport(self):
        with self._lock:
            t_callbacks = list(self._transport_listeners)
            state = "paused" if self._is_paused else ("playing" if self._is_playing else "stopped")
            cur = (self._current_frame / float(self._sample_rate)) if self._sample_rate > 0 else 0.0
            tot = (self._total_frames / float(self._sample_rate)) if self._sample_rate > 0 else 0.0
            cur = max(0.0, min(tot, cur))
        for cb in t_callbacks:
            try:
                cb(state, cur, tot)
            except Exception:
                pass

    def _parse_wav(self, wav_bytes: bytes) -> bool:
        """Parse WAV bytes into PCM buffer and metadata under lock."""
        if not wav_bytes:
            return False
        try:
            with wave.open(io.BytesIO(wav_bytes), 'rb') as wf:
                rate = wf.getframerate() or 24000
                channels = wf.getnchannels() or 1
                width = wf.getsampwidth() or 2
                nframes = wf.getnframes()
                raw_data = wf.readframes(nframes)
            with self._lock:
                self._wav_bytes = wav_bytes
                self._raw_pcm = raw_data
                self._sample_rate = rate
                self._channels = channels
                self._sampwidth = width
                frame_bytes = max(1, channels * width)
                self._total_frames = len(raw_data) // frame_bytes
                self._current_frame = 0
            return True
        except Exception:
            return False

    def load_wav_bytes(self, wav_bytes: bytes) -> bool:
        """Load WAV bytes into the player without starting playback so transport UI shows duration."""
        if not wav_bytes:
            return False
        if not self.is_active:
            if self._parse_wav(wav_bytes):
                self._notify_transport()
                return True
        return False

    def _transform_pcm_chunk(self, chunk: bytes, width: int, channels: int, volume: int, speed: float) -> bytes:
        """Apply real-time digital volume scaling and playback speed resampling to a 16-bit PCM chunk."""
        if not chunk:
            return chunk
        if width != 2:
            return chunk

        vol_scale = volume / 100.0
        if abs(vol_scale - 1.0) < 1e-3 and abs(speed - 1.0) < 1e-3:
            return chunk

        samples = array.array('h')
        samples.frombytes(chunk)
        n_samples = len(samples)
        if n_samples == 0:
            return chunk

        # 1. Speed resampling (preserving channel alignment)
        if abs(speed - 1.0) >= 1e-3:
            in_frames = n_samples // max(1, channels)
            out_frames = max(1, int(in_frames / speed))
            if channels == 1:
                resampled = array.array(
                    'h',
                    (samples[min(in_frames - 1, int(i * speed))] for i in range(out_frames))
                )
            else:
                resampled = array.array('h')
                for i in range(out_frames):
                    src_f = min(in_frames - 1, int(i * speed))
                    base = src_f * channels
                    for c in range(channels):
                        resampled.append(samples[base + c])
            samples = resampled

        # 2. Volume scaling
        if volume == 0:
            return b"\x00" * (len(samples) * 2)
        if abs(vol_scale - 1.0) >= 1e-3:
            scaled = array.array(
                'h',
                (max(-32768, min(32767, int(s * vol_scale))) for s in samples)
            )
            samples = scaled

        return samples.tobytes()

    def play_wav_bytes(self, wav_bytes: bytes, announce_on_start: bool = True, start_sec: float = 0.0):
        """Play WAV audio directly from bytes in memory without blocking the UI thread."""
        self.stop(announce=False)

        if not wav_bytes:
            return

        if not self._parse_wav(wav_bytes):
            return

        if start_sec > 0.0:
            with self._lock:
                target_frame = int(start_sec * self._sample_rate)
                self._current_frame = max(0, min(self._total_frames, target_frame))

        self._start_playback_thread(announce_on_start=announce_on_start)

    def _start_playback_thread(self, announce_on_start: bool = True):
        self._stop_requested.clear()

        def _play_worker():
            with self._lock:
                self._is_playing = True
                self._is_paused = False
                rate = self._sample_rate
                channels = self._channels
                width = self._sampwidth
                raw_data = self._raw_pcm
                total_frames = self._total_frames

            self._notify_state_change(True)

            if announce_on_start:
                announcer.announce(tr("announce_playing_audio"), interrupt=False)

            played_via_sd = False
            frame_bytes = max(1, channels * width)

            # 1. Primary method: sounddevice streaming with real-time pause, seek, volume, and speed
            if sd is not None and total_frames > 0:
                try:
                    dtype_map = {1: 'int8', 2: 'int16', 4: 'int32'}
                    dtype = dtype_map.get(width, 'int16')
                    frames_per_chunk = 1024  # ~42ms per chunk at 24kHz for instant responsiveness
                    last_ui_notify = 0.0

                    with sd.RawOutputStream(samplerate=rate, channels=channels, dtype=dtype) as stream:
                        with self._lock:
                            self._active_stream = stream

                        while not self._stop_requested.is_set():
                            with self._lock:
                                paused = self._is_paused
                                cur_frame = self._current_frame
                                vol = self._volume
                                spd = self._speed
                                loop_en = self._loop

                            if paused:
                                time.sleep(0.025)
                                continue

                            if cur_frame >= total_frames:
                                if loop_en and total_frames > 0:
                                    with self._lock:
                                        self._current_frame = 0
                                    self._notify_transport()
                                    continue
                                else:
                                    break

                            end_frame = min(total_frames, cur_frame + frames_per_chunk)
                            byte_start = cur_frame * frame_bytes
                            byte_end = end_frame * frame_bytes
                            chunk = raw_data[byte_start:byte_end]

                            out_chunk = self._transform_pcm_chunk(chunk, width, channels, vol, spd)
                            stream.write(out_chunk)

                            with self._lock:
                                # Only advance if seek() didn't jump _current_frame during write
                                if self._current_frame == cur_frame:
                                    self._current_frame = end_frame

                            now = time.time()
                            if now - last_ui_notify >= 0.08:
                                last_ui_notify = now
                                self._notify_transport()

                    played_via_sd = True
                except Exception:
                    played_via_sd = False

            # 2. Fallback method: asynchronous file playback via winsound (SND_ASYNC)
            if not played_via_sd and not self._stop_requested.is_set() and winsound is not None:
                temp_path = None
                try:
                    with self._lock:
                        wav_bytes = self._wav_bytes or b""
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tf:
                        temp_path = tf.name
                        tf.write(wav_bytes)
                    with self._lock:
                        self._temp_fallback_file = temp_path

                    duration = max(0.1, self.duration)
                    winsound.PlaySound(temp_path, winsound.SND_FILENAME | winsound.SND_ASYNC)

                    start_t = time.time()
                    while time.time() - start_t < duration and not self._stop_requested.is_set():
                        elapsed = time.time() - start_t
                        with self._lock:
                            self._current_frame = min(self._total_frames, int(elapsed * self._sample_rate))
                        self._notify_transport()
                        time.sleep(0.08)

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

            # Reset playing state on natural completion
            with self._lock:
                was_stopped = self._stop_requested.is_set()
                self._is_playing = False
                self._is_paused = False
                self._active_stream = None
                if not was_stopped:
                    self._current_frame = 0
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

    def pause(self, announce: bool = True):
        """Pause playback at the current frame without losing position."""
        with self._lock:
            if not self._is_playing or self._is_paused:
                return
            self._is_paused = True
        self._notify_state_change(False)
        if announce:
            announcer.announce(
                tr("announce_audio_paused", pos=format_mm_ss(self.current_time), dur=format_mm_ss(self.duration)),
                interrupt=True
            )

    def resume(self, announce: bool = True):
        """Resume paused playback from the current frame."""
        with self._lock:
            if self._is_playing and self._is_paused:
                self._is_paused = False
                need_new_thread = False
            elif not self._is_playing and self._raw_pcm:
                need_new_thread = True
            else:
                return

        if need_new_thread:
            self._start_playback_thread(announce_on_start=False)
        else:
            self._notify_state_change(True)

        if announce:
            announcer.announce(
                tr("announce_audio_resumed", pos=format_mm_ss(self.current_time)),
                interrupt=False
            )

    def toggle_play_pause(self, fallback_wav_bytes: Optional[bytes] = None, announce: bool = True):
        """
        Toggle between Play, Pause, and Resume:
        - If playing: pause at current position.
        - If paused (and same audio buffer): resume from current position.
        - If stopped (or new audio buffer provided): start playing.
        """
        with self._lock:
            playing = self._is_playing
            paused = self._is_paused
            same_buffer = (fallback_wav_bytes is None) or (fallback_wav_bytes == self._wav_bytes)

        if playing and not paused:
            self.pause(announce=announce)
        elif paused and same_buffer:
            self.resume(announce=announce)
        elif fallback_wav_bytes:
            if same_buffer and self.current_time > 0.0 and self.current_time < self.duration:
                self.resume(announce=announce)
            else:
                self.play_wav_bytes(fallback_wav_bytes, announce_on_start=announce)
        elif self._wav_bytes:
            if self.current_time > 0.0 and self.current_time < self.duration:
                self.resume(announce=announce)
            else:
                self.play_wav_bytes(self._wav_bytes, announce_on_start=announce)

    def seek(self, target_seconds: float, announce: bool = False):
        """Seek to a specific position in seconds."""
        with self._lock:
            if self._total_frames <= 0 or self._sample_rate <= 0:
                return
            dur = self._total_frames / float(self._sample_rate)
            clamped_sec = max(0.0, min(dur, float(target_seconds)))
            self._current_frame = max(0, min(self._total_frames, int(clamped_sec * self._sample_rate)))
        self._notify_transport()
        if announce:
            announcer.announce(
                tr("announce_audio_seek", pos=format_mm_ss(self.current_time), dur=format_mm_ss(self.duration)),
                interrupt=True
            )

    def skip(self, delta_seconds: float, announce: bool = True):
        """Skip forward or backward by delta_seconds (e.g. -5.0 or +5.0)."""
        if not self.has_audio:
            return
        self.seek(self.current_time + delta_seconds, announce=announce)

    def set_volume(self, percent: int, announce: bool = False):
        """Set playback volume percentage (0 to 100)."""
        vol = max(0, min(100, int(percent)))
        with self._lock:
            self._volume = vol
        config.set("player_volume", vol)
        self._notify_transport()
        if announce:
            announcer.announce(tr("announce_volume_changed", volume=vol), interrupt=True)

    def change_volume(self, delta: int, announce: bool = True):
        """Adjust playback volume by delta percent (e.g. -10 or +10)."""
        self.set_volume(self.volume + delta, announce=announce)

    def set_speed(self, speed: float, announce: bool = False):
        """Set playback speed multiplier (0.75, 1.0, 1.25, 1.5, 2.0)."""
        spd = float(speed)
        if spd not in SPEED_PRESETS:
            spd = min(SPEED_PRESETS, key=lambda x: abs(x - spd))
        with self._lock:
            self._speed = spd
        config.set("player_speed", spd)
        self._notify_transport()
        if announce:
            announcer.announce(tr("announce_speed_changed", speed=f"{spd:g}x"), interrupt=True)

    def cycle_speed(self, announce: bool = True) -> float:
        """Cycle through available playback speeds."""
        cur = self.speed
        try:
            idx = SPEED_PRESETS.index(cur)
            nxt = SPEED_PRESETS[(idx + 1) % len(SPEED_PRESETS)]
        except ValueError:
            nxt = 1.0
        self.set_speed(nxt, announce=announce)
        return nxt

    def set_loop(self, enabled: bool, announce: bool = False):
        """Enable or disable loop playback."""
        val = bool(enabled)
        with self._lock:
            self._loop = val
        config.set("player_loop", val)
        self._notify_transport()
        if announce:
            key = "announce_loop_on" if val else "announce_loop_off"
            announcer.announce(tr(key), interrupt=True)

    def toggle_loop(self, announce: bool = True) -> bool:
        """Toggle loop playback on or off."""
        new_val = not self.loop
        self.set_loop(new_val, announce=announce)
        return new_val

    def stop(self, announce: bool = True):
        """Immediately and non-blockingly stop any playing or paused audio and reset position to 00:00."""
        with self._lock:
            was_active = self._is_playing or self._is_paused
            self._stop_requested.set()
            stream = self._active_stream
            fallback_file = self._temp_fallback_file
            self._is_playing = False
            self._is_paused = False
            self._active_stream = None
            self._temp_fallback_file = None
            self._current_frame = 0

        if not was_active:
            self._notify_transport()
            return

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
        if announce:
            announcer.announce(tr("announce_audio_stopped"), interrupt=True)
            announcer.play_sound("stop")


# Global AudioPlayer instance
audio_player = AudioPlayer()
