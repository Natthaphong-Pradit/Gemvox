import threading
import wx
from gemvox.config import config
from gemvox.i18n import tr
from gemvox.accessibility import announcer
from gemvox.core.tts_engine import tts_engine
from gemvox.core.audio_player import audio_player
from gemvox.ui.theme import (
    style_panel,
    style_label,
    style_text_ctrl,
    style_combo,
    style_button,
    style_staticbox,
)

SAMPLE_DESIGN_PROMPTS = [
    {
        "name": "Warm British Astronomer",
        "gender": "Male",
        "lang": "en-GB",
        "prompt": "A warm, thoughtful astronomer in his late 60s with a gentle British accent, speaking with quiet wonder."
    },
    {
        "name": "Youthful Tech Educator",
        "gender": "Female",
        "lang": "en-US",
        "prompt": "An enthusiastic, friendly computer science teacher in her late 20s, with a clear, encouraging American delivery."
    },
    {
        "name": "Epic Fantasy Narrator",
        "gender": "Male",
        "lang": "en-GB",
        "prompt": "A deep, resonant, theatrical fantasy audiobook narrator with rich baritone texture and dramatic pacing."
    }
]


class VoiceDesignPanel(wx.Panel):
    """Panel for Voice Design: creating persistent vocal personas from text prompts."""
    def __init__(self, parent):
        super().__init__(parent)
        self.last_voice_id = None
        self.last_sample_bytes = None
        style_panel(self, accessible_name=tr("tab_design"))
        self._init_ui()
        audio_player.add_state_listener(self._on_player_state_change)

    def _init_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        info_box = wx.StaticText(
            self,
            label=tr("vd_info")
        )
        style_label(info_box, "muted")
        main_sizer.Add(info_box, 0, wx.ALL, 14)

        # Persona Parameters Card
        design_box = wx.StaticBox(self, label=tr("vd_box_specs"))
        style_staticbox(design_box)
        design_box_sizer = wx.StaticBoxSizer(design_box, wx.VERTICAL)

        # Fields Grid
        grid = wx.FlexGridSizer(rows=4, cols=2, vgap=10, hgap=12)
        grid.AddGrowableCol(1, 1)
        grid.AddGrowableRow(3, 1)

        # Voice Name
        lbl_name = wx.StaticText(design_box, label=tr("lbl_voice_name"))
        style_label(lbl_name)
        self.txt_name = wx.TextCtrl(design_box, value="Warm British Astronomer")
        style_text_ctrl(self.txt_name)
        grid.Add(lbl_name, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.txt_name, 1, wx.EXPAND)

        # Gender
        lbl_gender = wx.StaticText(design_box, label=tr("lbl_gender"))
        style_label(lbl_gender)
        self.combo_gender = wx.ComboBox(design_box, choices=["Male", "Female", "Neutral"], style=wx.CB_READONLY)
        style_combo(self.combo_gender)
        self.combo_gender.SetSelection(0)
        grid.Add(lbl_gender, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.combo_gender, 1, wx.EXPAND)

        # Language code
        lbl_lang = wx.StaticText(design_box, label=tr("lbl_lang_code"))
        style_label(lbl_lang)
        self.txt_lang = wx.TextCtrl(design_box, value="en-GB")
        style_text_ctrl(self.txt_lang)
        grid.Add(lbl_lang, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.txt_lang, 1, wx.EXPAND)

        # Persona prompt
        lbl_prompt = wx.StaticText(design_box, label=tr("lbl_persona_prompt"))
        style_label(lbl_prompt)
        self.txt_prompt = wx.TextCtrl(
            design_box,
            value="A warm, thoughtful astronomer in his late 60s with a gentle British accent, speaking with quiet wonder.",
            style=wx.TE_MULTILINE | wx.TE_RICH2
        )
        style_text_ctrl(self.txt_prompt, multiline=True)
        grid.Add(lbl_prompt, 0, wx.ALIGN_TOP)
        grid.Add(self.txt_prompt, 1, wx.EXPAND)

        design_box_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(design_box_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        # Sample templates bar
        sample_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_sample_astronomer = wx.Button(self, label=tr("btn_sample_astronomer"))
        self.btn_sample_educator = wx.Button(self, label=tr("btn_sample_educator"))
        self.btn_sample_fantasy = wx.Button(self, label=tr("btn_sample_fantasy"))
        style_button(self.btn_sample_astronomer, "secondary")
        style_button(self.btn_sample_educator, "secondary")
        style_button(self.btn_sample_fantasy, "secondary")
        sample_sizer.Add(self.btn_sample_astronomer, 0, wx.RIGHT, 8)
        sample_sizer.Add(self.btn_sample_educator, 0, wx.RIGHT, 8)
        sample_sizer.Add(self.btn_sample_fantasy, 0)
        main_sizer.Add(sample_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        # Action Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_create = wx.Button(self, label=tr("btn_create_voice"))
        self.btn_create.SetDefault()
        style_button(self.btn_create, "primary")

        self.btn_play_preview = wx.Button(self, label=tr("btn_play_preview"))
        self.btn_play_preview.Enable(False)
        style_button(self.btn_play_preview, "success")

        self.btn_copy_id = wx.Button(self, label=tr("btn_copy_id_y"))
        self.btn_copy_id.Enable(False)
        style_button(self.btn_copy_id, "gold")

        self.btn_save_wav = wx.Button(self, label=tr("btn_save_preview_wav"))
        self.btn_save_wav.Enable(False)
        style_button(self.btn_save_wav, "secondary")

        btn_sizer.Add(self.btn_create, 0, wx.RIGHT, 10)
        btn_sizer.Add(self.btn_play_preview, 0, wx.RIGHT, 10)
        btn_sizer.Add(self.btn_copy_id, 0, wx.RIGHT, 10)
        btn_sizer.Add(self.btn_save_wav, 0)
        main_sizer.Add(btn_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Status & ID Output
        self.lbl_id = wx.StaticText(self, label=tr("lbl_voice_id_none"))
        style_label(self.lbl_id, "mono")
        self.lbl_status = wx.StaticText(self, label=tr("status_ready"))
        style_label(self.lbl_status, "status")
        main_sizer.Add(self.lbl_id, 0, wx.LEFT | wx.RIGHT, 14)
        main_sizer.Add(self.lbl_status, 0, wx.ALL, 14)

        self.SetSizer(main_sizer)

        # Bindings
        self.btn_sample_astronomer.Bind(wx.EVT_BUTTON, lambda e: self.load_sample(0))
        self.btn_sample_educator.Bind(wx.EVT_BUTTON, lambda e: self.load_sample(1))
        self.btn_sample_fantasy.Bind(wx.EVT_BUTTON, lambda e: self.load_sample(2))
        self.btn_create.Bind(wx.EVT_BUTTON, self.on_create_voice)
        self.btn_play_preview.Bind(wx.EVT_BUTTON, self.on_play_preview)
        self.btn_copy_id.Bind(wx.EVT_BUTTON, self.on_copy_id)
        self.btn_save_wav.Bind(wx.EVT_BUTTON, self.on_save_wav)

    def load_sample(self, idx: int):
        s = SAMPLE_DESIGN_PROMPTS[idx]
        self.txt_name.SetValue(s["name"])
        self.combo_gender.SetValue(s["gender"])
        self.txt_lang.SetValue(s["lang"])
        self.txt_prompt.SetValue(s["prompt"])
        style_text_ctrl(self.txt_prompt, multiline=True)
        announcer.announce(tr("announce_loaded_sample", name=s["name"]))

    def on_create_voice(self, event):
        name = self.txt_name.GetValue().strip()
        prompt = self.txt_prompt.GetValue().strip()
        gender = self.combo_gender.GetValue().strip()
        lang = self.txt_lang.GetValue().strip()

        if not name:
            announcer.announce(tr("announce_enter_voice_name"))
            self.txt_name.SetFocus()
            return
        if not prompt:
            announcer.announce(tr("announce_enter_persona_prompt"))
            self.txt_prompt.SetFocus()
            return

        self.btn_create.Enable(False)
        self.lbl_status.SetLabel(tr("announce_designing_voice", name=name))

        def _worker():
            try:
                voice_id, sample_bytes, preview_path = tts_engine.design_voice(
                    display_name=name,
                    prompt_description=prompt,
                    gender=gender,
                    language_code=lang
                )
                self.last_voice_id = voice_id
                self.last_sample_bytes = sample_bytes

                def _ui_update():
                    self.btn_create.Enable(True)
                    self.btn_play_preview.Enable(bool(sample_bytes))
                    self.btn_copy_id.Enable(bool(voice_id))
                    self.btn_save_wav.Enable(bool(sample_bytes))
                    self.lbl_id.SetLabel(tr("lbl_voice_id_assigned", voice_id=voice_id))
                    self.lbl_status.SetLabel(tr("status_design_success"))
                    if sample_bytes and config.get("autoplay", True):
                        audio_player.play_wav_bytes(sample_bytes)

                wx.CallAfter(_ui_update)
            except Exception as e:
                def _error_update():
                    self.btn_create.Enable(True)
                    self.lbl_status.SetLabel(tr("status_error", error=e))
                wx.CallAfter(_error_update)

        threading.Thread(target=_worker, daemon=True).start()

    def on_play_preview(self, event=None):
        if audio_player.is_playing:
            audio_player.stop()
        else:
            if self.last_sample_bytes:
                audio_player.play_wav_bytes(self.last_sample_bytes)

    def _on_player_state_change(self, is_playing: bool):
        def _update():
            if is_playing:
                self.btn_play_preview.SetLabel(tr("btn_stop_preview"))
                style_button(self.btn_play_preview, "danger")
            else:
                self.btn_play_preview.SetLabel(tr("btn_play_preview"))
                style_button(self.btn_play_preview, "success")
        wx.CallAfter(_update)

    def on_copy_id(self, event):
        if self.last_voice_id:
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(self.last_voice_id))
                wx.TheClipboard.Close()
                announcer.announce(tr("announce_copied_voice_id", voice_id=self.last_voice_id))

    def on_save_wav(self, event):
        if not self.last_sample_bytes:
            return
        with wx.FileDialog(
            self,
            message=tr("menu_save_audio_help"),
            defaultDir=str(config.output_dir),
            defaultFile=f"preview_{self.txt_name.GetValue().strip().lower().replace(' ', '_')}.wav",
            wildcard="WAV Audio (*.wav)|*.wav",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                dest = dlg.GetPath()
                with open(dest, "wb") as f:
                    f.write(self.last_sample_bytes)
                announcer.announce(tr("announce_saved_preview", path=dest))
