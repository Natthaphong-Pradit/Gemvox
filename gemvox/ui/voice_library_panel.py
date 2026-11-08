import threading
import wx
from gemvox.config import config
from gemvox.i18n import tr
from gemvox.accessibility import announcer
from gemvox.core.voice_catalog import PREBUILT_VOICES
from gemvox.core.tts_engine import tts_engine
from gemvox.core.audio_player import audio_player
from gemvox.ui.theme import (
    style_panel,
    style_label,
    style_text_ctrl,
    style_combo,
    style_listbox,
    style_button,
    style_staticbox,
)


class VoiceLibraryPanel(wx.Panel):
    """Panel for browsing the 30 prebuilt studio voices, managing custom voices, and querying the Extended Voice Library."""
    def __init__(self, parent):
        super().__init__(parent)
        self.voices_data = []
        self._showing_remote = False
        style_panel(self, accessible_name=tr("tab_library"))
        self._init_ui()
        self.load_prebuilt_voices(announce=False)
        config.add_voices_listener(self._on_voices_changed)

    def _on_voices_changed(self):
        if not self._showing_remote:
            wx.CallAfter(self.load_prebuilt_voices, False)

    def _init_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        info = wx.StaticText(
            self,
            label=tr("vl_info")
        )
        style_label(info, "muted")
        main_sizer.Add(info, 0, wx.ALL, 14)

        # Filters Card
        filter_box = wx.StaticBox(self, label=tr("vl_box_filters"))
        style_staticbox(filter_box)
        filter_box_sizer = wx.StaticBoxSizer(filter_box, wx.VERTICAL)

        filter_grid = wx.FlexGridSizer(rows=2, cols=4, vgap=10, hgap=12)
        filter_grid.AddGrowableCol(1, 1)
        filter_grid.AddGrowableCol(3, 1)

        # Search query
        lbl_search = wx.StaticText(filter_box, label=tr("lbl_search_query"))
        style_label(lbl_search)
        self.txt_search = wx.TextCtrl(filter_box, value="")
        style_text_ctrl(self.txt_search)
        filter_grid.Add(lbl_search, 0, wx.ALIGN_CENTER_VERTICAL)
        filter_grid.Add(self.txt_search, 1, wx.EXPAND)

        # Language
        lbl_lang = wx.StaticText(filter_box, label=tr("lbl_language"))
        style_label(lbl_lang)
        self.txt_lang = wx.TextCtrl(filter_box, value="en-US")
        style_text_ctrl(self.txt_lang)
        filter_grid.Add(lbl_lang, 0, wx.ALIGN_CENTER_VERTICAL)
        filter_grid.Add(self.txt_lang, 1, wx.EXPAND)

        # Gender
        lbl_gender = wx.StaticText(filter_box, label=tr("lbl_gender_g"))
        style_label(lbl_gender)
        self.combo_gender = wx.ComboBox(filter_box, choices=["All", "female", "male", "neutral"], style=wx.CB_READONLY)
        style_combo(self.combo_gender)
        self.combo_gender.SetSelection(0)
        filter_grid.Add(lbl_gender, 0, wx.ALIGN_CENTER_VERTICAL)
        filter_grid.Add(self.combo_gender, 1, wx.EXPAND)

        # Domain
        lbl_domain = wx.StaticText(filter_box, label=tr("lbl_domain"))
        style_label(lbl_domain)
        self.combo_domain = wx.ComboBox(filter_box, choices=["All", "Audiobook", "Conversational", "News"], style=wx.CB_READONLY)
        style_combo(self.combo_domain)
        self.combo_domain.SetSelection(0)
        filter_grid.Add(lbl_domain, 0, wx.ALIGN_CENTER_VERTICAL)
        filter_grid.Add(self.combo_domain, 1, wx.EXPAND)

        filter_box_sizer.Add(filter_grid, 0, wx.EXPAND | wx.ALL, 10)

        # Search buttons inside filter card
        btn_filter_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_search_remote = wx.Button(filter_box, label=tr("btn_search_online"))
        self.btn_show_prebuilt = wx.Button(filter_box, label=tr("btn_show_prebuilt"))
        style_button(self.btn_search_remote, "primary")
        style_button(self.btn_show_prebuilt, "secondary")
        btn_filter_sizer.Add(self.btn_search_remote, 0, wx.RIGHT, 10)
        btn_filter_sizer.Add(self.btn_show_prebuilt, 0)
        filter_box_sizer.Add(btn_filter_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        main_sizer.Add(filter_box_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        # Voices List
        lbl_list = wx.StaticText(self, label=tr("lbl_voices_list"))
        style_label(lbl_list, "section")
        main_sizer.Add(lbl_list, 0, wx.LEFT | wx.RIGHT, 14)

        self.listbox_voices = wx.ListBox(self, choices=[], style=wx.LB_SINGLE)
        style_listbox(self.listbox_voices)
        main_sizer.Add(self.listbox_voices, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 12)

        # Action Buttons
        act_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_audition = wx.Button(self, label=tr("btn_audition_a"))
        self.btn_use_voice = wx.Button(self, label=tr("btn_use_voice_y"))
        self.btn_copy_id = wx.Button(self, label=tr("btn_copy_id_c"))
        self.btn_delete_custom = wx.Button(self, label=tr("btn_delete_voice_r"))
        self.btn_delete_custom.Enable(False)

        style_button(self.btn_audition, "gold")
        style_button(self.btn_use_voice, "primary")
        style_button(self.btn_copy_id, "secondary")
        style_button(self.btn_delete_custom, "danger")

        act_sizer.Add(self.btn_audition, 0, wx.RIGHT, 8)
        act_sizer.Add(self.btn_use_voice, 0, wx.RIGHT, 8)
        act_sizer.Add(self.btn_copy_id, 0, wx.RIGHT, 8)
        act_sizer.Add(self.btn_delete_custom, 0)
        main_sizer.Add(act_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Status
        self.lbl_status = wx.StaticText(self, label=tr("status_ready"))
        style_label(self.lbl_status, "status")
        main_sizer.Add(self.lbl_status, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        self.SetSizer(main_sizer)

        # Bindings
        self.btn_search_remote.Bind(wx.EVT_BUTTON, self.on_search_remote)
        self.btn_show_prebuilt.Bind(wx.EVT_BUTTON, lambda e: self.load_prebuilt_voices(announce=True))
        self.btn_audition.Bind(wx.EVT_BUTTON, self.on_audition)
        self.btn_use_voice.Bind(wx.EVT_BUTTON, self.on_use_voice)
        self.btn_copy_id.Bind(wx.EVT_BUTTON, self.on_copy_id)
        self.btn_delete_custom.Bind(wx.EVT_BUTTON, self.on_delete_custom)
        self.listbox_voices.Bind(wx.EVT_LISTBOX, self.on_selection_changed)
        self.listbox_voices.Bind(wx.EVT_LISTBOX_DCLICK, self.on_audition)

    def _update_action_buttons(self):
        sel = self.listbox_voices.GetSelection()
        if sel != wx.NOT_FOUND and sel < len(self.voices_data):
            is_custom = bool(self.voices_data[sel].get("is_custom", False))
            self.btn_delete_custom.Enable(is_custom)
            self.btn_use_voice.Enable(True)
        else:
            self.btn_delete_custom.Enable(False)
            self.btn_use_voice.Enable(False)

    def on_selection_changed(self, event):
        self._update_action_buttons()
        event.Skip()

    def load_prebuilt_voices(self, announce: bool = True):
        self._showing_remote = False
        self.voices_data = []
        choices = []

        custom_saved = config.get("custom_voices", [])
        for cv in custom_saved:
            vid = cv.get("id", "")
            dname = cv.get("display_name", vid)
            vtype = cv.get("type", "Custom")
            desc = cv.get("description", "")
            entry = {
                "id": vid,
                "display_name": dname,
                "language_code": "Custom",
                "gender": "Custom",
                "tone": vtype,
                "description": desc,
                "is_custom": True
            }
            self.voices_data.append(entry)
            choices.append(f"[Custom] {dname} ({vid}) | Type: {vtype} - {desc}")

        for v in PREBUILT_VOICES:
            entry = {
                "id": v.id,
                "display_name": v.display_name,
                "language_code": v.language_code,
                "gender": v.gender,
                "tone": v.tone,
                "description": v.description,
                "is_custom": False
            }
            self.voices_data.append(entry)
            choices.append(f"{v.id:<15} | Tone: {v.tone:<16} | ({v.gender}) - {v.description}")

        self.listbox_voices.Set(choices)
        if choices:
            self.listbox_voices.SetSelection(0)
        self._update_action_buttons()

        total = len(choices)
        custom_count = len(custom_saved)
        prebuilt_count = len(PREBUILT_VOICES)
        self.lbl_status.SetLabel(tr("status_showing_voices", total=total, custom=custom_count, prebuilt=prebuilt_count))
        if announce:
            announcer.announce(tr("announce_loaded_voices", total=total, custom=custom_count, prebuilt=prebuilt_count))

    def on_search_remote(self, event):
        query = self.txt_search.GetValue().strip()
        lang = self.txt_lang.GetValue().strip()
        gender = self.combo_gender.GetValue().strip()
        domain = self.combo_domain.GetValue().strip()

        self.btn_search_remote.Enable(False)
        self.lbl_status.SetLabel(tr("announce_querying_library"))

        def _worker():
            try:
                results = tts_engine.search_voice_library(
                    search_query=query,
                    language_code=lang if lang else None,
                    gender=gender if gender != "All" else None,
                    context_domain=domain if domain != "All" else None
                )
                self._showing_remote = True
                self.voices_data = results
                choices = [
                    f"{v['id']} | {v['display_name']} ({v.get('gender','')}, {v.get('language_code','')}): {v.get('description','')}"
                    for v in results
                ]

                def _ui_update():
                    self.btn_search_remote.Enable(True)
                    self.listbox_voices.Set(choices)
                    if choices:
                        self.listbox_voices.SetSelection(0)
                    self._update_action_buttons()
                    self.lbl_status.SetLabel(tr("announce_found_voices", count=len(choices)))

                wx.CallAfter(_ui_update)
            except Exception as e:
                def _error_update():
                    self.btn_search_remote.Enable(True)
                    self.lbl_status.SetLabel(tr("status_error", error=e))
                wx.CallAfter(_error_update)

        threading.Thread(target=_worker, daemon=True).start()

    def get_selected_voice_entry(self) -> dict:
        sel = self.listbox_voices.GetSelection()
        if sel != wx.NOT_FOUND and sel < len(self.voices_data):
            return self.voices_data[sel]
        return {"id": "Kore", "display_name": "Kore", "description": "", "is_custom": False}

    def get_selected_voice_id(self) -> str:
        return self.get_selected_voice_entry().get("id", "Kore")

    def on_audition(self, event):
        voice_id = self.get_selected_voice_id()
        announcer.announce(tr("status_auditioning", voice=voice_id))
        self.lbl_status.SetLabel(tr("status_auditioning", voice=voice_id))

        def _worker():
            try:
                sample_text = f"This is an audition preview for voice {voice_id}."
                wav_bytes, _, _ = tts_engine.synthesize_single_speaker(
                    text=sample_text,
                    voice=voice_id,
                    style="natural and clear"
                )
                audio_player.play_wav_bytes(wav_bytes)
                wx.CallAfter(self.lbl_status.SetLabel, tr("status_audition_done", voice=voice_id))
            except Exception as e:
                wx.CallAfter(self.lbl_status.SetLabel, tr("status_error", error=e))

        threading.Thread(target=_worker, daemon=True).start()

    def on_use_voice(self, event):
        entry = self.get_selected_voice_entry()
        voice_id = entry.get("id", "Kore")
        display_name = entry.get("display_name") or voice_id
        desc = entry.get("description", "")

        top_win = wx.GetTopLevelParent(self)
        if hasattr(top_win, "tab_single"):
            top_win.tab_single.select_voice_by_id(voice_id, display_name=display_name, description=desc)
        msg = tr("announce_voice_selected_for_tts", voice=display_name)
        self.lbl_status.SetLabel(msg)
        announcer.play_sound("success")
        announcer.announce(msg)

    def on_delete_custom(self, event):
        entry = self.get_selected_voice_entry()
        if not entry.get("is_custom"):
            return
        voice_id = entry.get("id", "")
        display_name = entry.get("display_name", voice_id)

        resp = wx.MessageBox(
            tr("confirm_delete_voice_msg", name=display_name, voice_id=voice_id),
            tr("confirm_delete_voice_title"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
            self
        )
        if resp == wx.YES:
            config.remove_custom_voice(voice_id)
            self.load_prebuilt_voices(announce=False)
            self.listbox_voices.SetFocus()
            announcer.announce(tr("announce_deleted_custom_voice", name=display_name))

    def on_copy_id(self, event):
        voice_id = self.get_selected_voice_id()
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(voice_id))
            wx.TheClipboard.Close()
            announcer.announce(tr("announce_copied_voice_id", voice_id=voice_id))
