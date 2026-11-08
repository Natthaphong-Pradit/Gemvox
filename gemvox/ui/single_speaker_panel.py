import threading
import wx
from gemvox.config import config
from gemvox.i18n import tr
from gemvox.accessibility import announcer
from gemvox.core.voice_catalog import (
    SUPPORTED_MODELS,
    get_all_voices,
    find_voice
)
from gemvox.core.tts_engine import tts_engine
from gemvox.core.audio_player import audio_player
from gemvox.ui.dialogs import InlineTagDialog, StylePresetDialog, CreateCustomStyleDialog
from gemvox.ui.player_bar import AudioTransportBar
from gemvox.ui.theme import (
    style_panel,
    style_label,
    style_text_ctrl,
    style_combo,
    style_button,
    style_staticbox,
)


class SingleSpeakerPanel(wx.Panel):
    """Panel for single-speaker TTS generation with full style, vocal tag control, and luxury studio layout."""
    def __init__(self, parent):
        super().__init__(parent)
        self.last_audio_bytes = None
        self.last_saved_path = None
        style_panel(self, accessible_name=tr("tab_single"))
        self._init_ui()
        config.add_voices_listener(self._on_voices_changed)

    def _on_voices_changed(self):
        wx.CallAfter(self.refresh_voices)

    def _init_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 1. Text Input Section
        text_label = wx.StaticText(self, label=tr("ss_text_label"))
        style_label(text_label, "section")
        main_sizer.Add(text_label, 0, wx.LEFT | wx.TOP | wx.RIGHT, 14)

        self.text_ctrl = wx.TextCtrl(
            self,
            value=tr("ss_default_text"),
            style=wx.TE_MULTILINE | wx.TE_RICH2
        )
        style_text_ctrl(self.text_ctrl, multiline=True)
        self.text_ctrl.Bind(wx.EVT_CONTEXT_MENU, self.on_text_context_menu)
        main_sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 12)

        # Vocal Tag Insertion & Text Tools bar
        tag_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_insert_tag = wx.Button(self, label=tr("btn_insert_tag_i"))
        self.btn_clear = wx.Button(self, label=tr("btn_clear_text"))
        self.btn_stats = wx.Button(self, label=tr("btn_stats"))
        style_button(self.btn_insert_tag, "secondary")
        style_button(self.btn_clear, "secondary")
        style_button(self.btn_stats, "secondary")
        tag_sizer.Add(self.btn_insert_tag, 0, wx.RIGHT, 8)
        tag_sizer.Add(self.btn_clear, 0, wx.RIGHT, 8)
        tag_sizer.Add(self.btn_stats, 0)
        main_sizer.Add(tag_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        # 2. Options Card: Model, Voice, Style
        opt_box = wx.StaticBox(self, label=tr("ss_box_params"))
        style_staticbox(opt_box)
        opt_box_sizer = wx.StaticBoxSizer(opt_box, wx.VERTICAL)

        grid_sizer = wx.FlexGridSizer(rows=3, cols=3, vgap=10, hgap=12)
        grid_sizer.AddGrowableCol(1, 1)

        # Model row
        lbl_model = wx.StaticText(opt_box, label=tr("lbl_model"))
        style_label(lbl_model)
        model_choices = [m["name"] for m in SUPPORTED_MODELS]
        self.combo_model = wx.ComboBox(opt_box, choices=model_choices, style=wx.CB_READONLY)
        style_combo(self.combo_model)
        def_m = config.get("default_model", "gemini-3.8-flash-tts")
        sel_m = 0
        for i, m in enumerate(SUPPORTED_MODELS):
            if m["id"] == def_m:
                sel_m = i
                break
        self.combo_model.SetSelection(sel_m)
        grid_sizer.Add(lbl_model, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.combo_model, 1, wx.EXPAND)
        grid_sizer.AddStretchSpacer()

        # Voice row
        lbl_voice = wx.StaticText(opt_box, label=tr("lbl_voice"))
        style_label(lbl_voice)
        self.combo_voice = wx.ComboBox(opt_box, choices=[], style=wx.CB_READONLY)
        style_combo(self.combo_voice)
        self.refresh_voices()

        self.btn_audition = wx.Button(opt_box, label=tr("btn_audition_u"))
        style_button(self.btn_audition, "gold")
        grid_sizer.Add(lbl_voice, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.combo_voice, 1, wx.EXPAND)
        grid_sizer.Add(self.btn_audition, 0, wx.ALIGN_CENTER_VERTICAL)

        # Style row
        lbl_style = wx.StaticText(opt_box, label=tr("lbl_style"))
        style_label(lbl_style)
        self.txt_style = wx.TextCtrl(opt_box, value=config.get("default_style", "cheerful and friendly"))
        style_text_ctrl(self.txt_style)
        style_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_browse_style = wx.Button(opt_box, label=tr("btn_browse_styles"))
        self.btn_create_style = wx.Button(opt_box, label=tr("btn_create_style"))
        style_button(self.btn_browse_style, "secondary")
        style_button(self.btn_create_style, "secondary")
        style_btn_sizer.Add(self.btn_browse_style, 0, wx.RIGHT, 6)
        style_btn_sizer.Add(self.btn_create_style, 0)
        grid_sizer.Add(lbl_style, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.txt_style, 1, wx.EXPAND)
        grid_sizer.Add(style_btn_sizer, 0, wx.ALIGN_CENTER_VERTICAL)

        opt_box_sizer.Add(grid_sizer, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(opt_box_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        # 3. Generation & Export Bar
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_generate = wx.Button(self, label=tr("btn_generate_speech"))
        self.btn_generate.SetDefault()
        style_button(self.btn_generate, "primary")

        self.btn_save = wx.Button(self, label=tr("btn_save_audio"))
        self.btn_save.Enable(False)
        style_button(self.btn_save, "secondary")

        btn_sizer.Add(self.btn_generate, 0, wx.RIGHT, 10)
        btn_sizer.Add(self.btn_save, 0)
        main_sizer.Add(btn_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # 4. Studio Audio Player & Transport Deck
        self.player_bar = AudioTransportBar(
            self,
            get_audio_bytes_cb=lambda: self.last_audio_bytes
        )
        self.btn_play = self.player_bar.btn_play
        self.btn_stop = self.player_bar.btn_stop
        main_sizer.Add(self.player_bar.sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # 5. Accessible Status Readout Console
        self.lbl_status = wx.StaticText(self, label=tr("status_ready"))
        style_label(self.lbl_status, "status")
        main_sizer.Add(self.lbl_status, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        self.SetSizer(main_sizer)

        # Bindings
        self.btn_insert_tag.Bind(wx.EVT_BUTTON, self.on_insert_tag)
        self.btn_clear.Bind(wx.EVT_BUTTON, self.on_clear)
        self.btn_stats.Bind(wx.EVT_BUTTON, self.on_announce_stats)
        self.btn_browse_style.Bind(wx.EVT_BUTTON, self.on_browse_style)
        self.btn_create_style.Bind(wx.EVT_BUTTON, self.on_create_custom_style)
        self.btn_audition.Bind(wx.EVT_BUTTON, self.on_audition_voice)
        self.btn_generate.Bind(wx.EVT_BUTTON, self.on_generate)
        self.btn_save.Bind(wx.EVT_BUTTON, self.on_save)

    def refresh_voices(self, select_voice_id: str = None):
        """Populate the voice combo box with all prebuilt and custom voices."""
        if select_voice_id is None and hasattr(self, " _voices_cache") and self.combo_voice.GetCount() > 0:
            select_voice_id = self.get_selected_voice_id()
        elif select_voice_id is None and self.combo_voice.GetCount() > 0:
            select_voice_id = self.get_selected_voice_id()

        voices = get_all_voices()
        self._voices_cache = voices
        choices = []
        for v in voices:
            if v.is_custom:
                choices.append(f"{v.display_name} ({v.id}) - {v.tone}")
            else:
                choices.append(f"{v.id} - {v.tone} ({v.gender})")
        self.combo_voice.Set(choices)

        target_voice = select_voice_id or config.get("default_voice", "Kore")
        sel_idx = 0
        for i, v in enumerate(voices):
            if v.id.lower() == target_voice.lower():
                sel_idx = i
                break
        if choices:
            self.combo_voice.SetSelection(sel_idx)

    def select_voice_by_id(self, voice_id: str, display_name: str = None, description: str = ""):
        """Select a voice by ID in the combo box, adding it to custom voices if it is from the online library."""
        found = find_voice(voice_id)
        if not found:
            config.add_custom_voice(
                voice_id=voice_id,
                display_name=display_name or voice_id,
                voice_type="Extended Library",
                description=description
            )
        self.refresh_voices(select_voice_id=voice_id)

    def get_selected_voice_id(self) -> str:
        voices = getattr(self, "_voices_cache", None) or get_all_voices()
        sel = self.combo_voice.GetSelection()
        if sel != wx.NOT_FOUND and sel < len(voices):
            return voices[sel].id
        return "Kore"

    def get_selected_model_id(self) -> str:
        sel = self.combo_model.GetSelection()
        if sel != wx.NOT_FOUND and sel < len(SUPPORTED_MODELS):
            return SUPPORTED_MODELS[sel]["id"]
        return "gemini-3.8-flash-tts"

    def on_announce_stats(self, event=None):
        stats = tts_engine.calculate_text_stats(self.text_ctrl.GetValue())
        self.lbl_status.SetLabel(tr("status_text_stats", **stats))
        announcer.announce(tr("announce_text_stats", **stats))

    def on_text_context_menu(self, event):
        """Standard accessible Windows context menu for text editing."""
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
        m_tag = menu.Append(wx.ID_ANY, tr("btn_insert_tag_i"))

        m_undo.Enable(self.text_ctrl.CanUndo())
        m_redo.Enable(self.text_ctrl.CanRedo())
        m_cut.Enable(self.text_ctrl.CanCut())
        m_copy.Enable(self.text_ctrl.CanCopy())
        m_paste.Enable(self.text_ctrl.CanPaste())

        self.Bind(wx.EVT_MENU, lambda e: self.text_ctrl.Undo(), m_undo)
        self.Bind(wx.EVT_MENU, lambda e: self.text_ctrl.Redo(), m_redo)
        self.Bind(wx.EVT_MENU, lambda e: self.text_ctrl.Cut(), m_cut)
        self.Bind(wx.EVT_MENU, lambda e: self.text_ctrl.Copy(), m_copy)
        self.Bind(wx.EVT_MENU, lambda e: self.text_ctrl.Paste(), m_paste)
        self.Bind(wx.EVT_MENU, lambda e: self._delete_selection_or_char(), m_del)
        self.Bind(wx.EVT_MENU, lambda e: self.text_ctrl.SelectAll(), m_all)
        self.Bind(wx.EVT_MENU, self.on_insert_tag, m_tag)

        self.PopupMenu(menu)
        menu.Destroy()

    def _delete_selection_or_char(self):
        sel_from, sel_to = self.text_ctrl.GetSelection()
        if sel_from != sel_to:
            self.text_ctrl.Remove(sel_from, sel_to)
        else:
            pos = self.text_ctrl.GetInsertionPoint()
            if pos < self.text_ctrl.GetLastPosition():
                self.text_ctrl.Remove(pos, pos + 1)

    def on_insert_tag(self, event=None):
        sel_from, sel_to = self.text_ctrl.GetSelection()
        pos = self.text_ctrl.GetInsertionPoint()
        val = self.text_ctrl.GetValue()

        dlg = InlineTagDialog(self)
        if dlg.ShowModal() == wx.ID_OK and dlg.selected_tag:
            tag = dlg.selected_tag
            self.text_ctrl.SetFocus()

            if sel_from != sel_to:
                self.text_ctrl.SetSelection(sel_from, sel_to)
                prefix = " " if (sel_from > 0 and not val[sel_from - 1].isspace()) else ""
                suffix = " " if (sel_to < len(val) and not val[sel_to].isspace() and val[sel_to] not in ".,!?;:") else ""
            else:
                self.text_ctrl.SetInsertionPoint(pos)
                prefix = " " if (pos > 0 and not val[pos - 1].isspace()) else ""
                suffix = " " if (pos < len(val) and not val[pos].isspace() and val[pos] not in ".,!?;:") else ""

            tag_text = f"{prefix}{tag}{suffix}"
            self.text_ctrl.WriteText(tag_text)
            style_text_ctrl(self.text_ctrl, multiline=True)
            announcer.announce(tr("announce_inserted_tag", tag=tag))
        else:
            self.text_ctrl.SetFocus()
        dlg.Destroy()

    def on_clear(self, event):
        self.text_ctrl.Clear()
        style_text_ctrl(self.text_ctrl, multiline=True)
        self.text_ctrl.SetFocus()
        announcer.announce(tr("msg_text_cleared"))

    def on_browse_style(self, event):
        dlg = StylePresetDialog(self)
        if dlg.ShowModal() == wx.ID_OK and dlg.selected_style:
            self.txt_style.SetValue(dlg.selected_style)
            self.txt_style.SetFocus()
            announcer.announce(tr("announce_applied_style", style=dlg.selected_style))
        dlg.Destroy()

    def on_create_custom_style(self, event=None):
        current_style = self.txt_style.GetValue().strip()
        dlg = CreateCustomStyleDialog(self, initial_style=current_style)
        if dlg.ShowModal() == wx.ID_OK and dlg.created_style:
            self.txt_style.SetValue(dlg.created_style)
            self.txt_style.SetFocus()
            self.lbl_status.SetLabel(tr("status_saved_custom_style", name=dlg.created_name, style=dlg.created_style))
            announcer.announce(tr("announce_saved_custom_style", name=dlg.created_name))
        dlg.Destroy()

    def on_audition_voice(self, event):
        voice_id = self.get_selected_voice_id()
        model_id = self.get_selected_model_id()
        audition_phrase = f"Hello, I am {voice_id}. This is a preview of my voice."

        self.lbl_status.SetLabel(tr("status_auditioning", voice=voice_id))

        def _worker():
            try:
                wav_bytes, _, _ = tts_engine.synthesize_single_speaker(
                    text=audition_phrase,
                    voice=voice_id,
                    style="natural and clear",
                    model=model_id
                )
                audio_player.play_wav_bytes(wav_bytes)
                wx.CallAfter(self.lbl_status.SetLabel, tr("status_audition_done", voice=voice_id))
            except Exception as e:
                wx.CallAfter(self.lbl_status.SetLabel, tr("status_error", error=e))

        threading.Thread(target=_worker, daemon=True).start()

    def on_generate(self, event=None):
        text = self.text_ctrl.GetValue().strip()
        if not text:
            announcer.announce(tr("msg_enter_text"))
            self.text_ctrl.SetFocus()
            return

        voice_id = self.get_selected_voice_id()
        model_id = self.get_selected_model_id()
        style = self.txt_style.GetValue().strip()

        self.btn_generate.Enable(False)
        self.lbl_status.SetLabel(tr("status_generating_single", voice=voice_id))

        def _worker():
            try:
                wav_bytes, out_path, duration = tts_engine.synthesize_single_speaker(
                    text=text,
                    voice=voice_id,
                    style=style,
                    model=model_id
                )
                self.last_audio_bytes = wav_bytes
                self.last_saved_path = out_path

                def _ui_update():
                    self.btn_generate.Enable(True)
                    self.btn_save.Enable(True)
                    self.player_bar.set_audio_ready(True, wav_bytes)
                    self.lbl_status.SetLabel(tr("status_single_ready", duration=duration, path=out_path))
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

        default_name = f"gemvox_speech_{self.get_selected_voice_id().lower()}.wav"
        with wx.FileDialog(
            self,
            message=tr("menu_save_audio_help"),
            defaultDir=str(config.output_dir),
            defaultFile=default_name,
            wildcard="WAV Audio (*.wav)|*.wav",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                dest = dlg.GetPath()
                with open(dest, "wb") as f:
                    f.write(self.last_audio_bytes)
                announcer.announce(tr("announce_audio_saved", path=dest))
                self.lbl_status.SetLabel(tr("status_saved_path", path=dest))
