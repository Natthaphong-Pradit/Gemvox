import threading
import wx
from gemvox.config import config
from gemvox.i18n import tr
from gemvox.accessibility import announcer
from gemvox.core.voice_catalog import (
    SUPPORTED_MODELS,
    get_all_voices
)
from gemvox.core.tts_engine import tts_engine
from gemvox.core.audio_player import audio_player
from gemvox.ui.dialogs import InlineTagDialog
from gemvox.ui.player_bar import AudioTransportBar
from gemvox.ui.theme import (
    style_panel,
    style_label,
    style_text_ctrl,
    style_combo,
    style_button,
    style_staticbox,
)

DEFAULT_PODCAST_SCRIPT = (
    "Joe: Welcome back everyone to the Tech Horizons podcast! [cheerful and friendly]\n"
    "Jane: So excited to be here today Joe. What exciting updates are we exploring? [calm and relaxed]\n"
    "Joe: Today we are testing the brand new Gemini 3.8 Flash TTS model with Gemvox! [warm and enthusiastic]\n"
    "Jane: That sounds incredible. <short pause> Let's hear how natural the conversation sounds. [upbeat]"
)

DEFAULT_INTERVIEW_SCRIPT = (
    "Host: Good evening and welcome to our special broadcast. [professional news anchor]\n"
    "Expert: Thank you for inviting me. It is a pleasure to join you. [calm and thoughtful]\n"
    "Host: Could you explain the importance of accessible software for visually impaired developers? [attentive and curious]\n"
    "Expert: Absolutely. Screen reader accessibility turns complex barriers into seamless opportunities. [warm and confident]"
)


class MultiSpeakerPanel(wx.Panel):
    """Panel for multi-speaker conversational dialogue generation."""
    def __init__(self, parent):
        super().__init__(parent)
        self.last_audio_bytes = None
        self.last_saved_path = None
        self.speaker_combos = {}
        self._voices_cache = []
        style_panel(self, accessible_name=tr("tab_multi"))
        self._init_ui()
        config.add_voices_listener(self._on_voices_changed)

    def _on_voices_changed(self):
        wx.CallAfter(self.update_speaker_controls)

    def _init_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 1. Script Header and Help
        script_header = wx.StaticText(
            self,
            label=tr("ms_script_label")
        )
        style_label(script_header, "section")
        main_sizer.Add(script_header, 0, wx.LEFT | wx.TOP | wx.RIGHT, 14)

        self.text_script = wx.TextCtrl(
            self,
            value=DEFAULT_PODCAST_SCRIPT,
            style=wx.TE_MULTILINE | wx.TE_RICH2
        )
        style_text_ctrl(self.text_script, multiline=True)
        self.text_script.Bind(wx.EVT_CONTEXT_MENU, self.on_text_context_menu)
        main_sizer.Add(self.text_script, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 12)

        # Template and Insertion buttons
        tmpl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_insert_tag = wx.Button(self, label=tr("btn_insert_tag_t"))
        self.btn_load_podcast = wx.Button(self, label=tr("btn_load_podcast"))
        self.btn_load_interview = wx.Button(self, label=tr("btn_load_interview"))
        self.btn_detect_speakers = wx.Button(self, label=tr("btn_update_speakers"))
        self.btn_stats = wx.Button(self, label=tr("btn_stats"))

        style_button(self.btn_insert_tag, "secondary")
        style_button(self.btn_load_podcast, "secondary")
        style_button(self.btn_load_interview, "secondary")
        style_button(self.btn_detect_speakers, "gold")
        style_button(self.btn_stats, "secondary")

        tmpl_sizer.Add(self.btn_insert_tag, 0, wx.RIGHT, 6)
        tmpl_sizer.Add(self.btn_load_podcast, 0, wx.RIGHT, 6)
        tmpl_sizer.Add(self.btn_load_interview, 0, wx.RIGHT, 6)
        tmpl_sizer.Add(self.btn_detect_speakers, 0, wx.RIGHT, 6)
        tmpl_sizer.Add(self.btn_stats, 0)
        main_sizer.Add(tmpl_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        # 2. Speaker Voice Mapping Section
        self.mapping_box = wx.StaticBox(self, label=tr("ms_box_mapping"))
        style_staticbox(self.mapping_box)
        self.box_sizer = wx.StaticBoxSizer(self.mapping_box, wx.VERTICAL)

        self.speakers_grid = wx.FlexGridSizer(cols=2, vgap=8, hgap=12)
        self.speakers_grid.AddGrowableCol(1, 1)
        self.box_sizer.Add(self.speakers_grid, 0, wx.EXPAND | wx.ALL, 8)
        main_sizer.Add(self.box_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        # 3. Model & Action Row
        ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)

        lbl_model = wx.StaticText(self, label=tr("lbl_model"))
        style_label(lbl_model)
        model_choices = [m["name"] for m in SUPPORTED_MODELS]
        self.combo_model = wx.ComboBox(self, choices=model_choices, style=wx.CB_READONLY)
        style_combo(self.combo_model)
        def_m = config.get("default_model", "gemini-2.5-flash-preview-tts")
        sel_m = 0
        for i, m in enumerate(SUPPORTED_MODELS):
            if m["id"] == def_m:
                sel_m = i
                break
        self.combo_model.SetSelection(sel_m)

        self.btn_generate = wx.Button(self, label=tr("btn_generate_dialogue"))
        self.btn_generate.SetDefault()
        style_button(self.btn_generate, "primary")

        self.btn_save = wx.Button(self, label=tr("btn_save_audio"))
        self.btn_save.Enable(False)
        style_button(self.btn_save, "secondary")

        ctrl_sizer.Add(lbl_model, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        ctrl_sizer.Add(self.combo_model, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)
        ctrl_sizer.Add(self.btn_generate, 0, wx.RIGHT, 10)
        ctrl_sizer.Add(self.btn_save, 0)
        main_sizer.Add(ctrl_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # 4. Studio Audio Player & Transport Deck
        self.player_bar = AudioTransportBar(
            self,
            get_audio_bytes_cb=lambda: self.last_audio_bytes
        )
        self.btn_play = self.player_bar.btn_play
        self.btn_stop = self.player_bar.btn_stop
        main_sizer.Add(self.player_bar.sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # 5. Status
        self.lbl_status = wx.StaticText(self, label=tr("status_ready"))
        style_label(self.lbl_status, "status")
        main_sizer.Add(self.lbl_status, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        self.SetSizer(main_sizer)

        # Bindings
        self.btn_insert_tag.Bind(wx.EVT_BUTTON, self.on_insert_tag)
        self.btn_load_podcast.Bind(wx.EVT_BUTTON, self.on_load_podcast)
        self.btn_load_interview.Bind(wx.EVT_BUTTON, self.on_load_interview)
        self.btn_detect_speakers.Bind(wx.EVT_BUTTON, self.on_detect_speakers)
        self.btn_stats.Bind(wx.EVT_BUTTON, self.on_announce_stats)
        self.btn_generate.Bind(wx.EVT_BUTTON, self.on_generate)
        self.btn_save.Bind(wx.EVT_BUTTON, self.on_save)

        # Initial detection
        self.update_speaker_controls()

    def on_announce_stats(self, event=None):
        stats = tts_engine.calculate_text_stats(self.text_script.GetValue())
        self.lbl_status.SetLabel(tr("status_text_stats", **stats))
        announcer.announce(tr("announce_text_stats", **stats))

    def on_load_podcast(self, event):
        self.text_script.SetValue(DEFAULT_PODCAST_SCRIPT)
        style_text_ctrl(self.text_script, multiline=True)
        self.update_speaker_controls()
        announcer.announce(tr("announce_loaded_podcast"))

    def on_load_interview(self, event):
        self.text_script.SetValue(DEFAULT_INTERVIEW_SCRIPT)
        style_text_ctrl(self.text_script, multiline=True)
        self.update_speaker_controls()
        announcer.announce(tr("announce_loaded_interview"))

    def on_detect_speakers(self, event):
        count = self.update_speaker_controls()
        announcer.announce(tr("announce_detected_speakers", count=count))

    def _get_combo_voice_id(self, combo: wx.ComboBox) -> str:
        sel = combo.GetSelection()
        if sel != wx.NOT_FOUND and sel < len(self._voices_cache):
            return self._voices_cache[sel].id
        return "Kore"

    def update_speaker_controls(self) -> int:
        """Parses script, discovers speakers, and creates accessible voice dropdowns while preserving selections."""
        previous_selections = {}
        for spk, combo in self.speaker_combos.items():
            try:
                previous_selections[spk] = self._get_combo_voice_id(combo)
            except Exception:
                pass

        script = self.text_script.GetValue()
        _, speakers = tts_engine.parse_dialogue_script(script)
        if not speakers:
            speakers = ["Joe", "Jane"]

        voices = get_all_voices()
        self._voices_cache = voices
        voice_choices = [
            f"{v.display_name} ({v.id})" if v.is_custom else f"{v.id} - {v.tone} ({v.gender})"
            for v in voices
        ]

        # Clear existing
        self.speakers_grid.Clear(True)
        self.speaker_combos.clear()

        default_pairings = ["Puck", "Kore", "Zephyr", "Charon", "Fenrir", "Leda"]

        for idx, spk in enumerate(speakers):
            lbl = wx.StaticText(self.mapping_box, label=tr("lbl_voice_for", speaker=spk))
            style_label(lbl)
            combo = wx.ComboBox(self.mapping_box, choices=voice_choices, style=wx.CB_READONLY)
            style_combo(combo)

            def_voice = previous_selections.get(spk) or default_pairings[idx % len(default_pairings)]
            sel_idx = 0
            for vi, v in enumerate(voices):
                if v.id.lower() == def_voice.lower():
                    sel_idx = vi
                    break
            if voice_choices:
                combo.SetSelection(sel_idx)

            self.speakers_grid.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL)
            self.speakers_grid.Add(combo, 1, wx.EXPAND)
            self.speaker_combos[spk] = combo

        self.box_sizer.Layout()
        self.Layout()
        return len(speakers)

    def on_generate(self, event=None):
        script = self.text_script.GetValue().strip()
        if not script:
            announcer.announce(tr("msg_enter_script"))
            self.text_script.SetFocus()
            return

        turns, speakers = tts_engine.parse_dialogue_script(script)
        if not turns:
            announcer.announce(tr("announce_no_valid_turns"))
            return

        speaker_voice_map = {}
        for spk in speakers:
            combo = self.speaker_combos.get(spk)
            if combo:
                speaker_voice_map[spk] = self._get_combo_voice_id(combo)
            else:
                speaker_voice_map[spk] = "Kore"

        sel_m = self.combo_model.GetSelection()
        model_id = SUPPORTED_MODELS[sel_m]["id"] if sel_m != wx.NOT_FOUND else "gemini-3.8-flash-tts"

        self.btn_generate.Enable(False)
        self.lbl_status.SetLabel(tr("status_generating_multi", count=len(speakers)))

        def _worker():
            try:
                wav_bytes, out_path, duration = tts_engine.synthesize_multi_speaker(
                    turns=turns,
                    speaker_voice_map=speaker_voice_map,
                    model=model_id
                )
                self.last_audio_bytes = wav_bytes
                self.last_saved_path = out_path

                def _ui_update():
                    self.btn_generate.Enable(True)
                    self.btn_save.Enable(True)
                    self.player_bar.set_audio_ready(True, wav_bytes)
                    self.lbl_status.SetLabel(tr("status_multi_ready", duration=duration, path=out_path))
                    if config.get("autoplay", True):
                        audio_player.play_wav_bytes(wav_bytes)

                wx.CallAfter(_ui_update)
            except Exception as e:
                def _error_update():
                    self.btn_generate.Enable(True)
                    self.lbl_status.SetLabel(tr("status_error", error=e))
                wx.CallAfter(_error_update)

        threading.Thread(target=_worker, daemon=True).start()

    def on_play_stop(self, event=None):
        self.player_bar.on_play_pause()

    def on_save(self, event=None):
        if not self.last_audio_bytes:
            announcer.announce(tr("msg_no_audio_save"))
            return

        with wx.FileDialog(
            self,
            message=tr("menu_save_audio_help"),
            defaultDir=str(config.output_dir),
            defaultFile="gemvox_dialogue.wav",
            wildcard="WAV Audio (*.wav)|*.wav",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                dest = dlg.GetPath()
                with open(dest, "wb") as f:
                    f.write(self.last_audio_bytes)
                announcer.announce(tr("announce_audio_saved", path=dest))
                self.lbl_status.SetLabel(tr("status_saved_path", path=dest))

    def on_text_context_menu(self, event):
        """Standard accessible Windows context menu for dialogue script editing."""
        menu = wx.Menu()
        m_undo = menu.Append(wx.ID_UNDO, tr("menu_undo"))
        m_redo = menu.Append(wx.ID_REDO, tr("menu_redo"))
        menu.AppendSeparator()
        m_cut = menu.Append(wx.ID_CUT, tr("menu_cut"))
        m_copy = menu.Append(wx.ID_COPY, tr("menu_copy"))
        m_paste = menu.Append(wx.ID_PASTE, tr("menu_paste"))
        m_del = menu.Append(wx.ID_DELETE, tr("menu_delete"))
        menu.AppendSeparator()
        m_all = menu.Append(wx.ID_SELECTALL, tr("menu_select_all"))
        menu.AppendSeparator()
        m_tag = menu.Append(wx.ID_ANY, tr("btn_insert_tag_t"))

        m_undo.Enable(self.text_script.CanUndo())
        m_redo.Enable(self.text_script.CanRedo())
        m_cut.Enable(self.text_script.CanCut())
        m_copy.Enable(self.text_script.CanCopy())
        m_paste.Enable(self.text_script.CanPaste())

        self.Bind(wx.EVT_MENU, lambda e: self.text_script.Undo(), m_undo)
        self.Bind(wx.EVT_MENU, lambda e: self.text_script.Redo(), m_redo)
        self.Bind(wx.EVT_MENU, lambda e: self.text_script.Cut(), m_cut)
        self.Bind(wx.EVT_MENU, lambda e: self.text_script.Copy(), m_copy)
        self.Bind(wx.EVT_MENU, lambda e: self.text_script.Paste(), m_paste)
        self.Bind(wx.EVT_MENU, lambda e: self._delete_selection_or_char(), m_del)
        self.Bind(wx.EVT_MENU, lambda e: self.text_script.SelectAll(), m_all)
        self.Bind(wx.EVT_MENU, self.on_insert_tag, m_tag)

        self.PopupMenu(menu)
        menu.Destroy()

    def _delete_selection_or_char(self):
        sel_from, sel_to = self.text_script.GetSelection()
        if sel_from != sel_to:
            self.text_script.Remove(sel_from, sel_to)
        else:
            pos = self.text_script.GetInsertionPoint()
            if pos < self.text_script.GetLastPosition():
                self.text_script.Remove(pos, pos + 1)

    def on_insert_tag(self, event=None):
        sel_from, sel_to = self.text_script.GetSelection()
        pos = self.text_script.GetInsertionPoint()
        val = self.text_script.GetValue()

        dlg = InlineTagDialog(self)
        if dlg.ShowModal() == wx.ID_OK and dlg.selected_tag:
            tag = dlg.selected_tag
            self.text_script.SetFocus()

            if sel_from != sel_to:
                self.text_script.SetSelection(sel_from, sel_to)
                prefix = " " if (sel_from > 0 and not val[sel_from - 1].isspace()) else ""
                suffix = " " if (sel_to < len(val) and not val[sel_to].isspace() and val[sel_to] not in ".,!?;:") else ""
            else:
                self.text_script.SetInsertionPoint(pos)
                prefix = " " if (pos > 0 and not val[pos - 1].isspace()) else ""
                suffix = " " if (pos < len(val) and not val[pos].isspace() and val[pos] not in ".,!?;:") else ""

            tag_text = f"{prefix}{tag}{suffix}"
            self.text_script.WriteText(tag_text)
            style_text_ctrl(self.text_script, multiline=True)
            announcer.announce(tr("announce_inserted_tag", tag=tag))
        else:
            self.text_script.SetFocus()
        dlg.Destroy()
