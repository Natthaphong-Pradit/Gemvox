from typing import Callable, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from gemvox.i18n import tr
from gemvox.core.audio_player import audio_player, SPEED_PRESETS, format_mm_ss
from gemvox.ui.theme import (
    apply_accessible,
    call_after,
    clean_mnemonic,
    style_button,
    style_label,
)


class AudioTransportBar(QGroupBox):
    """
    Studio Audio Player & Transport Controller (PySide6 Universal Design).
    Provides Play/Pause (Alt+P), Stop (Alt+Q), Rewind -5s (F7), Fast-Forward +5s (F8),
    interactive Seek Slider, MM:SS / MM:SS time display, Volume Slider (F9/F10),
    Playback Speed selector (0.75x - 2.0x), and Loop toggle (Ctrl+L).
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        get_audio_bytes_cb: Optional[Callable[[], Optional[bytes]]] = None,
        on_play_custom_cb: Optional[Callable[[], None]] = None,
        play_label_key: str = "btn_play_audio",
        pause_label_key: str = "btn_pause_audio",
        resume_label_key: str = "btn_resume_audio",
    ):
        super().__init__(clean_mnemonic(tr("player_box_title")), parent)
        self.setAccessibleName(clean_mnemonic(tr("player_box_title")))
        self.get_audio_bytes_cb = get_audio_bytes_cb
        self.on_play_custom_cb = on_play_custom_cb
        self.play_label_key = play_label_key
        self.pause_label_key = pause_label_key
        self.resume_label_key = resume_label_key
        self._has_local_audio = False
        self._updating_ui = False
        self._alive = True

        self._last_state: Optional[str] = None
        self._last_play_enabled: Optional[bool] = None
        self._last_stop_enabled: Optional[bool] = None
        self._last_has_timeline: Optional[bool] = None
        self._last_pos_val: Optional[int] = None
        self._last_time_text: Optional[str] = None
        self._last_vol: Optional[int] = None
        self._last_loop: Optional[bool] = None

        self._init_ui()
        audio_player.add_transport_listener(self._on_transport_event)
        self.destroyed.connect(self._on_destroyed)

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(8)

        # Row 1: Transport Buttons + Seek Slider + Time Readout
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        self.btn_play = QPushButton(tr(self.play_label_key), self)
        self.btn_play.setEnabled(False)
        style_button(self.btn_play, "success")

        self.btn_stop = QPushButton(tr("btn_stop_audio_q"), self)
        self.btn_stop.setEnabled(False)
        style_button(self.btn_stop, "danger")

        self.btn_rew = QPushButton(tr("btn_rewind_5s"), self)
        self.btn_rew.setEnabled(False)
        style_button(self.btn_rew, "secondary")

        self.btn_ff = QPushButton(tr("btn_forward_5s"), self)
        self.btn_ff.setEnabled(False)
        style_button(self.btn_ff, "secondary")

        lbl_pos = QLabel(tr("lbl_player_pos"), self)
        style_label(lbl_pos, "muted")

        self.slider_seek = QSlider(Qt.Horizontal, self)
        self.slider_seek.setRange(0, 1000)
        self.slider_seek.setValue(0)
        self.slider_seek.setSingleStep(10)
        self.slider_seek.setPageStep(50)
        self.slider_seek.setEnabled(False)
        self.slider_seek.setFocusPolicy(Qt.StrongFocus)
        apply_accessible(
            self.slider_seek,
            name=tr("lbl_player_pos"),
            description="Audio playback position slider",
            label=lbl_pos,
        )

        self.lbl_time = QLabel("00:00 / 00:00", self)
        style_label(self.lbl_time, "mono")
        apply_accessible(self.lbl_time, name="Playback time", description="Current time and total duration")

        row1.addWidget(self.btn_play)
        row1.addWidget(self.btn_stop)
        row1.addWidget(self.btn_rew)
        row1.addWidget(self.btn_ff)
        row1.addSpacing(6)
        row1.addWidget(lbl_pos)
        row1.addWidget(self.slider_seek, 1)
        row1.addSpacing(4)
        row1.addWidget(self.lbl_time)

        # Row 2: Volume Slider + Playback Speed + Loop Checkbox
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        self.lbl_vol = QLabel(tr("lbl_player_volume", vol=audio_player.volume), self)
        style_label(self.lbl_vol, "muted")

        self.slider_vol = QSlider(Qt.Horizontal, self)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(audio_player.volume)
        self.slider_vol.setSingleStep(5)
        self.slider_vol.setPageStep(10)
        self.slider_vol.setFixedWidth(140)
        self.slider_vol.setFocusPolicy(Qt.StrongFocus)
        apply_accessible(
            self.slider_vol,
            name=tr("lbl_player_volume_name"),
            description=f"{audio_player.volume}%",
            label=self.lbl_vol,
        )

        lbl_speed = QLabel(tr("lbl_player_speed"), self)
        style_label(lbl_speed, "muted")

        self.combo_speed = QComboBox(self)
        self.combo_speed.addItems([f"{s:g}x" for s in SPEED_PRESETS])
        self.combo_speed.setFocusPolicy(Qt.StrongFocus)
        apply_accessible(
            self.combo_speed,
            name=tr("lbl_player_speed"),
            description="Playback speed multiplier (Ctrl+Shift+P to cycle)",
            label=lbl_speed,
        )
        self._sync_speed_selection(audio_player.speed)

        self.chk_loop = QCheckBox(tr("chk_player_loop"), self)
        self.chk_loop.setChecked(audio_player.loop)
        self.chk_loop.setFocusPolicy(Qt.StrongFocus)
        apply_accessible(
            self.chk_loop,
            name=clean_mnemonic(tr("chk_player_loop")),
            description="Toggle continuous loop playback (Ctrl+L)",
        )

        row2.addWidget(self.lbl_vol)
        row2.addWidget(self.slider_vol)
        row2.addSpacing(10)
        row2.addWidget(lbl_speed)
        row2.addWidget(self.combo_speed)
        row2.addSpacing(10)
        row2.addWidget(self.chk_loop)
        row2.addStretch(1)

        root_layout.addLayout(row1)
        root_layout.addLayout(row2)

        # Connections
        self.btn_play.clicked.connect(self.on_play_pause)
        self.btn_stop.clicked.connect(self.on_stop)
        self.btn_rew.clicked.connect(self.on_rewind)
        self.btn_ff.clicked.connect(self.on_forward)
        self.slider_seek.valueChanged.connect(self.on_seek_slider)
        self.slider_vol.valueChanged.connect(self.on_volume_slider)
        self.combo_speed.currentIndexChanged.connect(self.on_speed_combo)
        self.chk_loop.toggled.connect(self.on_loop_check)

    def _on_destroyed(self, *args):
        self._alive = False
        audio_player.remove_transport_listener(self._on_transport_event)

    def _sync_speed_selection(self, speed_val: float):
        try:
            idx = SPEED_PRESETS.index(speed_val)
        except ValueError:
            idx = 1
        if self.combo_speed.currentIndex() != idx:
            self.combo_speed.setCurrentIndex(idx)

    def set_audio_ready(self, ready: bool = True, wav_bytes: Optional[bytes] = None):
        """Enable Play/Transport controls once audio has been generated or selected."""
        self._has_local_audio = bool(ready)
        if wav_bytes and not audio_player.is_active:
            audio_player.load_wav_bytes(wav_bytes)
        self.btn_play.setEnabled(self._has_local_audio or audio_player.is_active)
        has_timeline = self._has_local_audio or audio_player.has_audio
        self.btn_rew.setEnabled(has_timeline)
        self.btn_ff.setEnabled(has_timeline)
        self.slider_seek.setEnabled(has_timeline)

    def on_play_pause(self, *args):
        if self.on_play_custom_cb is not None and not audio_player.is_active:
            self.on_play_custom_cb()
            return
        wav_bytes = self.get_audio_bytes_cb() if self.get_audio_bytes_cb else None
        audio_player.toggle_play_pause(fallback_wav_bytes=wav_bytes, announce=True)

    def on_stop(self, *args):
        audio_player.stop(announce=True)

    def on_rewind(self, *args):
        audio_player.skip(-5.0, announce=True)

    def on_forward(self, *args):
        audio_player.skip(5.0, announce=True)

    def on_seek_slider(self, value: int):
        if self._updating_ui:
            return
        dur = audio_player.duration
        if dur > 0:
            ratio = value / 1000.0
            audio_player.seek(ratio * dur, announce=False)

    def on_volume_slider(self, vol: int):
        if self._updating_ui:
            return
        self.lbl_vol.setText(tr("lbl_player_volume", vol=vol))
        self.slider_vol.setAccessibleDescription(f"{vol}%")
        audio_player.set_volume(vol, announce=False)

    def on_speed_combo(self, sel: int):
        if self._updating_ui:
            return
        if 0 <= sel < len(SPEED_PRESETS):
            audio_player.set_speed(SPEED_PRESETS[sel], announce=True)

    def on_loop_check(self, checked: bool):
        if self._updating_ui:
            return
        audio_player.set_loop(checked, announce=True)

    def _on_transport_event(self, state: str, cur_sec: float, tot_sec: float):
        if not self._alive:
            return

        def _update():
            if not self._alive:
                return
            self._updating_ui = True
            try:
                play_enabled = True if state in ("playing", "paused") else (self._has_local_audio or audio_player.has_audio)
                stop_enabled = state in ("playing", "paused")

                if state != self._last_state:
                    self._last_state = state
                    if state == "playing":
                        text = tr(self.pause_label_key)
                        self.btn_play.setText(text)
                        style_button(self.btn_play, "gold")
                    elif state == "paused":
                        text = tr(self.resume_label_key)
                        self.btn_play.setText(text)
                        style_button(self.btn_play, "success")
                    else:
                        text = tr(self.play_label_key)
                        self.btn_play.setText(text)
                        style_button(self.btn_play, "success")

                if play_enabled != self._last_play_enabled:
                    self._last_play_enabled = play_enabled
                    self.btn_play.setEnabled(play_enabled)
                if stop_enabled != self._last_stop_enabled:
                    self._last_stop_enabled = stop_enabled
                    self.btn_stop.setEnabled(stop_enabled)

                has_timeline = (tot_sec > 0) or self._has_local_audio or audio_player.has_audio
                if has_timeline != self._last_has_timeline:
                    self._last_has_timeline = has_timeline
                    self.btn_rew.setEnabled(has_timeline)
                    self.btn_ff.setEnabled(has_timeline)
                    self.slider_seek.setEnabled(has_timeline)

                if tot_sec > 0:
                    val = int(max(0, min(1000, round((cur_sec / tot_sec) * 1000))))
                    if val != self._last_pos_val:
                        self._last_pos_val = val
                        self.slider_seek.setValue(val)
                    time_text = f"{format_mm_ss(cur_sec)} / {format_mm_ss(tot_sec)}"
                else:
                    if self._last_pos_val != 0:
                        self._last_pos_val = 0
                        self.slider_seek.setValue(0)
                    time_text = "00:00 / 00:00"

                if time_text != self._last_time_text:
                    self._last_time_text = time_text
                    self.lbl_time.setText(time_text)
                    self.slider_seek.setAccessibleDescription(time_text)

                vol = audio_player.volume
                if vol != self._last_vol:
                    self._last_vol = vol
                    self.slider_vol.setValue(vol)
                    self.lbl_vol.setText(tr("lbl_player_volume", vol=vol))
                    self.slider_vol.setAccessibleDescription(f"{vol}%")

                self._sync_speed_selection(audio_player.speed)

                loop_val = audio_player.loop
                if loop_val != self._last_loop:
                    self._last_loop = loop_val
                    self.chk_loop.setChecked(loop_val)
            finally:
                self._updating_ui = False

        call_after(_update)
