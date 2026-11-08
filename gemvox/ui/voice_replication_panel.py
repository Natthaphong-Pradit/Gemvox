import threading
import wx
from gemvox.config import config
from gemvox.i18n import tr
from gemvox.accessibility import announcer
from gemvox.core.tts_engine import tts_engine
from gemvox.ui.theme import (
    style_panel,
    style_label,
    style_text_ctrl,
    style_button,
    style_radiobox,
    style_staticbox,
)

MANDATORY_CONSENT_TEXT = (
    "I am the owner of this voice and I consent to Google using this voice to create a synthetic voice model."
)


class VoiceReplicationPanel(wx.Panel):
    """Panel for replicating a speaker voice with reference and consent audio."""
    def __init__(self, parent):
        super().__init__(parent)
        self.last_voice_id = None
        style_panel(self, accessible_name=tr("tab_replication"))
        self._init_ui()

    def _init_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        info_box = wx.StaticText(
            self,
            label=tr("vr_info")
        )
        style_label(info_box, "muted")
        main_sizer.Add(info_box, 0, wx.ALL, 14)

        rep_box = wx.StaticBox(self, label=tr("vr_box_cloning"))
        style_staticbox(rep_box)
        rep_box_sizer = wx.StaticBoxSizer(rep_box, wx.VERTICAL)

        grid = wx.FlexGridSizer(rows=5, cols=3, vgap=10, hgap=12)
        grid.AddGrowableCol(1, 1)

        # 1. Voice Name
        lbl_name = wx.StaticText(rep_box, label=tr("lbl_voice_name"))
        style_label(lbl_name)
        self.txt_name = wx.TextCtrl(rep_box, value="My Replicated Voice")
        style_text_ctrl(self.txt_name)
        grid.Add(lbl_name, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.txt_name, 1, wx.EXPAND)
        grid.AddStretchSpacer()

        # 2. Reference audio file
        lbl_ref = wx.StaticText(rep_box, label=tr("lbl_ref_audio"))
        style_label(lbl_ref)
        self.txt_ref_path = wx.TextCtrl(rep_box, value="")
        style_text_ctrl(self.txt_ref_path)
        self.btn_browse_ref = wx.Button(rep_box, label=tr("btn_browse_ref"))
        style_button(self.btn_browse_ref, "secondary")
        grid.Add(lbl_ref, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.txt_ref_path, 1, wx.EXPAND)
        grid.Add(self.btn_browse_ref, 0, wx.ALIGN_CENTER_VERTICAL)

        # 3. Consent statement box
        lbl_consent_statement = wx.StaticText(rep_box, label=tr("lbl_consent_phrase"))
        style_label(lbl_consent_statement)
        self.txt_consent_phrase = wx.TextCtrl(
            rep_box,
            value=MANDATORY_CONSENT_TEXT,
            style=wx.TE_MULTILINE | wx.TE_READONLY
        )
        style_text_ctrl(self.txt_consent_phrase, multiline=True)
        self.btn_copy_consent = wx.Button(rep_box, label=tr("btn_copy_statement"))
        style_button(self.btn_copy_consent, "gold")
        grid.Add(lbl_consent_statement, 0, wx.ALIGN_TOP)
        grid.Add(self.txt_consent_phrase, 1, wx.EXPAND)
        grid.Add(self.btn_copy_consent, 0, wx.ALIGN_CENTER_VERTICAL)

        # 4. Consent audio file
        lbl_con = wx.StaticText(rep_box, label=tr("lbl_con_audio"))
        style_label(lbl_con)
        self.txt_con_path = wx.TextCtrl(rep_box, value="")
        style_text_ctrl(self.txt_con_path)
        self.btn_browse_con = wx.Button(rep_box, label=tr("btn_browse_con"))
        style_button(self.btn_browse_con, "secondary")
        grid.Add(lbl_con, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.txt_con_path, 1, wx.EXPAND)
        grid.Add(self.btn_browse_con, 0, wx.ALIGN_CENTER_VERTICAL)

        # 5. Storage Mode
        lbl_mode = wx.StaticText(rep_box, label=tr("lbl_storage_mode"))
        style_label(lbl_mode)
        self.radio_mode = wx.RadioBox(
            rep_box,
            choices=[tr("mode_stateful"), tr("mode_stateless")],
            majorDimension=1
        )
        style_radiobox(self.radio_mode)
        grid.Add(lbl_mode, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.radio_mode, 1, wx.EXPAND)
        grid.AddStretchSpacer()

        rep_box_sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(rep_box_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        # Actions
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_replicate = wx.Button(self, label=tr("btn_replicate"))
        self.btn_replicate.SetDefault()
        style_button(self.btn_replicate, "primary")

        self.btn_copy_id = wx.Button(self, label=tr("btn_copy_id_y"))
        self.btn_copy_id.Enable(False)
        style_button(self.btn_copy_id, "gold")

        btn_sizer.Add(self.btn_replicate, 0, wx.RIGHT, 10)
        btn_sizer.Add(self.btn_copy_id, 0)
        main_sizer.Add(btn_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Output & Status
        self.lbl_id = wx.StaticText(self, label=tr("lbl_voice_id_none"))
        style_label(self.lbl_id, "mono")
        self.lbl_status = wx.StaticText(self, label=tr("status_ready"))
        style_label(self.lbl_status, "status")
        main_sizer.Add(self.lbl_id, 0, wx.LEFT | wx.RIGHT, 14)
        main_sizer.Add(self.lbl_status, 0, wx.ALL, 14)

        self.SetSizer(main_sizer)

        # Bindings
        self.btn_browse_ref.Bind(wx.EVT_BUTTON, self.on_browse_ref)
        self.btn_browse_con.Bind(wx.EVT_BUTTON, self.on_browse_con)
        self.btn_copy_consent.Bind(wx.EVT_BUTTON, self.on_copy_consent)
        self.btn_replicate.Bind(wx.EVT_BUTTON, self.on_replicate)
        self.btn_copy_id.Bind(wx.EVT_BUTTON, self.on_copy_id)

    def on_browse_ref(self, event):
        with wx.FileDialog(
            self,
            message="Select Reference Audio (WAV, 10-30 seconds)",
            wildcard="WAV files (*.wav)|*.wav",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.txt_ref_path.SetValue(dlg.GetPath())
                announcer.announce(tr("announce_selected_ref_audio", filename=dlg.GetFilename()))

    def on_browse_con(self, event):
        with wx.FileDialog(
            self,
            message="Select Consent Audio (WAV reciting phrase)",
            wildcard="WAV files (*.wav)|*.wav",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.txt_con_path.SetValue(dlg.GetPath())
                announcer.announce(tr("announce_selected_con_audio", filename=dlg.GetFilename()))

    def on_copy_consent(self, event):
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(MANDATORY_CONSENT_TEXT))
            wx.TheClipboard.Close()
            announcer.announce(tr("announce_copied_consent"))

    def on_replicate(self, event):
        name = self.txt_name.GetValue().strip()
        ref_path = self.txt_ref_path.GetValue().strip()
        con_path = self.txt_con_path.GetValue().strip()
        store_stateful = (self.radio_mode.GetSelection() == 0)

        if not name:
            announcer.announce(tr("announce_enter_voice_name"))
            self.txt_name.SetFocus()
            return
        if not ref_path:
            announcer.announce(tr("announce_select_ref_audio"))
            self.btn_browse_ref.SetFocus()
            return
        if not con_path:
            announcer.announce(tr("announce_select_con_audio"))
            self.btn_browse_con.SetFocus()
            return

        self.btn_replicate.Enable(False)
        self.lbl_status.SetLabel(tr("status_replicating"))

        def _worker():
            try:
                voice_id = tts_engine.replicate_voice(
                    display_name=name,
                    reference_audio_path=ref_path,
                    consent_audio_path=con_path,
                    store=store_stateful
                )
                self.last_voice_id = voice_id

                def _ui_update():
                    self.btn_replicate.Enable(True)
                    self.btn_copy_id.Enable(True)
                    self.lbl_id.SetLabel(tr("lbl_voice_id_assigned", voice_id=voice_id))
                    self.lbl_status.SetLabel(tr("status_replicate_success"))

                wx.CallAfter(_ui_update)
            except Exception as e:
                def _error_update():
                    self.btn_replicate.Enable(True)
                    self.lbl_status.SetLabel(tr("status_error", error=e))
                wx.CallAfter(_error_update)

        threading.Thread(target=_worker, daemon=True).start()

    def on_copy_id(self, event):
        if self.last_voice_id:
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(self.last_voice_id))
                wx.TheClipboard.Close()
                announcer.announce(tr("announce_copied_voice_id", voice_id=self.last_voice_id))
