from typing import Callable, Optional
import wx
from gemvox.i18n import tr
from gemvox.core.audio_player import audio_player, SPEED_PRESETS, format_mm_ss
from gemvox.ui.theme import (
    StudioColors,
    get_font,
    style_label,
    style_combo,
    style_checkbox,
    style_button,
    style_staticbox,
)


class AudioTransportBar:
    """
    Studio Audio Player & Transport Controller.
    Zero-Unlabeled-Panel Architecture:
    Creates a native wx.StaticBox directly on `parent` without any wrapper wx.Panel,
    providing Play/Pause (Alt+P), Stop (Alt+Q), Rewind -5s (F7), Fast-Forward +5s (F8),
    interactive Seek Slider, MM:SS / MM:SS time display, Volume Slider (F9/F10),
    Playback Speed selector (0.75x - 2.0x), and Loop toggle (Ctrl+L).
    """

    def __init__(
        self,
        parent: wx.Window,
        get_audio_bytes_cb: Optional[Callable[[], Optional[bytes]]] = None,
        on_play_custom_cb: Optional[Callable[[], None]] = None,
        play_label_key: str = "btn_play_audio",
        pause_label_key: str = "btn_pause_audio",
        resume_label_key: str = "btn_resume_audio",
    ):
        self.parent = parent
        self.get_audio_bytes_cb = get_audio_bytes_cb
        self.on_play_custom_cb = on_play_custom_cb
        self.play_label_key = play_label_key
        self.pause_label_key = pause_label_key
        self.resume_label_key = resume_label_key
        self._has_local_audio = False
        self._updating_ui = False

        self.box = wx.StaticBox(parent, label=tr("player_box_title"))
        style_staticbox(self.box)
        self.sizer = wx.StaticBoxSizer(self.box, wx.VERTICAL)

        # Row 1: Transport Buttons + Seek Slider + Time Readout
        row1 = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_play = wx.Button(self.box, label=tr(self.play_label_key))
        self.btn_play.Enable(False)
        style_button(self.btn_play, "success")

        self.btn_stop = wx.Button(self.box, label=tr("btn_stop_audio_q"))
        self.btn_stop.Enable(False)
        style_button(self.btn_stop, "danger")

        self.btn_rew = wx.Button(self.box, label=tr("btn_rewind_5s"))
        self.btn_rew.Enable(False)
        style_button(self.btn_rew, "secondary")

        self.btn_ff = wx.Button(self.box, label=tr("btn_forward_5s"))
        self.btn_ff.Enable(False)
        style_button(self.btn_ff, "secondary")

        lbl_pos = wx.StaticText(self.box, label=tr("lbl_player_pos"))
        style_label(lbl_pos, "muted")

        self.slider_seek = wx.Slider(
            self.box,
            value=0,
            minValue=0,
            maxValue=1000,
            style=wx.SL_HORIZONTAL,
            name=tr("lbl_player_pos")
        )
        self.slider_seek.SetBackgroundColour(StudioColors.BG_ELEVATED)
        self.slider_seek.SetForegroundColour(StudioColors.ACCENT_GOLD)
        self.slider_seek.Enable(False)

        self.lbl_time = wx.StaticText(self.box, label="00:00 / 00:00")
        style_label(self.lbl_time, "mono")

        row1.Add(self.btn_play, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        row1.Add(self.btn_stop, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        row1.Add(self.btn_rew, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        row1.Add(self.btn_ff, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        row1.Add(lbl_pos, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        row1.Add(self.slider_seek, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        row1.Add(self.lbl_time, 0, wx.ALIGN_CENTER_VERTICAL)

        # Row 2: Volume Slider + Playback Speed + Loop Checkbox
        row2 = wx.BoxSizer(wx.HORIZONTAL)

        self.lbl_vol = wx.StaticText(self.box, label=tr("lbl_player_volume", vol=audio_player.volume))
        style_label(self.lbl_vol, "muted")

        self.slider_vol = wx.Slider(
            self.box,
            value=audio_player.volume,
            minValue=0,
            maxValue=100,
            size=(130, -1),
            style=wx.SL_HORIZONTAL,
            name=tr("lbl_player_volume_name")
        )
        self.slider_vol.SetBackgroundColour(StudioColors.BG_ELEVATED)
        self.slider_vol.SetForegroundColour(StudioColors.ACCENT_PRIMARY)

        lbl_speed = wx.StaticText(self.box, label=tr("lbl_player_speed"))
        style_label(lbl_speed, "muted")

        speed_choices = [f"{s:g}x" for s in SPEED_PRESETS]
        self.combo_speed = wx.ComboBox(
            self.box,
            choices=speed_choices,
            style=wx.CB_READONLY,
            name=tr("lbl_player_speed")
        )
        style_combo(self.combo_speed)
        self._sync_speed_selection(audio_player.speed)

        self.chk_loop = wx.CheckBox(self.box, label=tr("chk_player_loop"))
        style_checkbox(self.chk_loop)
        self.chk_loop.SetFont(get_font(9))
        self.chk_loop.SetValue(audio_player.loop)

        row2.Add(self.lbl_vol, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        row2.Add(self.slider_vol, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)
        row2.Add(lbl_speed, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        row2.Add(self.combo_speed, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)
        row2.Add(self.chk_loop, 0, wx.ALIGN_CENTER_VERTICAL)

        self.sizer.Add(row1, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 6)
        self.sizer.Add(row2, 0, wx.EXPAND | wx.ALL, 6)

        # Bindings
        self.btn_play.Bind(wx.EVT_BUTTON, self.on_play_pause)
        self.btn_stop.Bind(wx.EVT_BUTTON, self.on_stop)
        self.btn_rew.Bind(wx.EVT_BUTTON, self.on_rewind)
        self.btn_ff.Bind(wx.EVT_BUTTON, self.on_forward)
        self.slider_seek.Bind(wx.EVT_SLIDER, self.on_seek_slider)
        self.slider_vol.Bind(wx.EVT_SLIDER, self.on_volume_slider)
        self.combo_speed.Bind(wx.EVT_COMBOBOX, self.on_speed_combo)
        self.chk_loop.Bind(wx.EVT_CHECKBOX, self.on_loop_check)

        audio_player.add_transport_listener(self._on_transport_event)
        self.box.Bind(wx.EVT_WINDOW_DESTROY, self._on_destroy)

    def _on_destroy(self, event):
        if event.GetEventObject() == self.box:
            audio_player.remove_transport_listener(self._on_transport_event)
        event.Skip()

    def _sync_speed_selection(self, speed_val: float):
        try:
            idx = SPEED_PRESETS.index(speed_val)
        except ValueError:
            idx = 1
        if self.combo_speed.GetSelection() != idx:
            self.combo_speed.SetSelection(idx)

    def set_audio_ready(self, ready: bool = True, wav_bytes: Optional[bytes] = None):
        """Enable Play/Transport controls once audio has been generated or selected."""
        self._has_local_audio = bool(ready)
        if wav_bytes and not audio_player.is_active:
            audio_player.load_wav_bytes(wav_bytes)
        self.btn_play.Enable(self._has_local_audio or audio_player.is_active)
        has_timeline = self._has_local_audio or audio_player.has_audio
        self.btn_rew.Enable(has_timeline)
        self.btn_ff.Enable(has_timeline)
        self.slider_seek.Enable(has_timeline)

    def on_play_pause(self, event=None):
        if self.on_play_custom_cb is not None and not audio_player.is_active:
            self.on_play_custom_cb()
            return
        wav_bytes = self.get_audio_bytes_cb() if self.get_audio_bytes_cb else None
        audio_player.toggle_play_pause(fallback_wav_bytes=wav_bytes, announce=True)

    def on_stop(self, event=None):
        audio_player.stop(announce=True)

    def on_rewind(self, event=None):
        audio_player.skip(-5.0, announce=True)

    def on_forward(self, event=None):
        audio_player.skip(5.0, announce=True)

    def on_seek_slider(self, event):
        if self._updating_ui:
            return
        dur = audio_player.duration
        if dur > 0:
            ratio = self.slider_seek.GetValue() / 1000.0
            audio_player.seek(ratio * dur, announce=False)

    def on_volume_slider(self, event):
        if self._updating_ui:
            return
        vol = self.slider_vol.GetValue()
        self.lbl_vol.SetLabel(tr("lbl_player_volume", vol=vol))
        audio_player.set_volume(vol, announce=False)

    def on_speed_combo(self, event):
        if self._updating_ui:
            return
        sel = self.combo_speed.GetSelection()
        if sel != wx.NOT_FOUND and sel < len(SPEED_PRESETS):
            audio_player.set_speed(SPEED_PRESETS[sel], announce=True)

    def on_loop_check(self, event):
        if self._updating_ui:
            return
        audio_player.set_loop(self.chk_loop.GetValue(), announce=True)

    def _on_transport_event(self, state: str, cur_sec: float, tot_sec: float):
        def _update():
            if not self.box:
                return
            self._updating_ui = True
            try:
                if state == "playing":
                    self.btn_play.SetLabel(tr(self.pause_label_key))
                    style_button(self.btn_play, "gold")
                    self.btn_play.Enable(True)
                    self.btn_stop.Enable(True)
                elif state == "paused":
                    self.btn_play.SetLabel(tr(self.resume_label_key))
                    style_button(self.btn_play, "success")
                    self.btn_play.Enable(True)
                    self.btn_stop.Enable(True)
                else:
                    self.btn_play.SetLabel(tr(self.play_label_key))
                    style_button(self.btn_play, "success")
                    self.btn_play.Enable(self._has_local_audio or audio_player.has_audio)
                    self.btn_stop.Enable(False)

                has_timeline = (tot_sec > 0) or self._has_local_audio
                self.btn_rew.Enable(has_timeline)
                self.btn_ff.Enable(has_timeline)
                self.slider_seek.Enable(has_timeline)

                if tot_sec > 0:
                    pos_val = int(round((cur_sec / tot_sec) * 1000))
                    pos_val = max(0, min(1000, pos_val))
                else:
                    pos_val = 0

                if wx.Window.FindFocus() != self.slider_seek:
                    self.slider_seek.SetValue(pos_val)

                self.lbl_time.SetLabel(f"{format_mm_ss(cur_sec)} / {format_mm_ss(tot_sec)}")

                vol = audio_player.volume
                if self.slider_vol.GetValue() != vol:
                    self.slider_vol.SetValue(vol)
                self.lbl_vol.SetLabel(tr("lbl_player_volume", vol=vol))

                self._sync_speed_selection(audio_player.speed)
                if self.chk_loop.GetValue() != audio_player.loop:
                    self.chk_loop.SetValue(audio_player.loop)
            finally:
                self._updating_ui = False

        wx.CallAfter(_update)
