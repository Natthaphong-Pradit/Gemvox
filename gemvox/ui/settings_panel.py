import os
import subprocess
import sys
import threading
import webbrowser
import wx
from gemvox.config import config
from gemvox.i18n import tr
from gemvox.accessibility import announcer
from gemvox.core.client import client_manager
from gemvox.core.voice_catalog import SUPPORTED_MODELS, PREBUILT_VOICES
from gemvox.ui.theme import (
    style_panel,
    style_label,
    style_text_ctrl,
    style_combo,
    style_checkbox,
    style_button,
    style_staticbox,
)

AI_STUDIO_API_KEY_URL = "https://aistudio.google.com/apikey"


def restart_application(top_window: wx.Window = None):
    """Cleanly relaunch Gemvox so newly saved settings and language changes take immediate effect."""
    try:
        if getattr(sys, "frozen", False):
            cmd = [sys.executable] + sys.argv[1:]
        else:
            cmd = [sys.executable] + sys.argv
        subprocess.Popen(cmd, cwd=os.getcwd())
    except Exception as e:
        print(f"Error restarting application: {e}")
    finally:
        if top_window:
            top_window.Destroy()
        wx.GetApp().ExitMainLoop()


class SettingsPanel(wx.Panel):
    """Accessible settings panel for API key, interface language, accessibility, and defaults."""
    def __init__(self, parent):
        super().__init__(parent)
        style_panel(self, accessible_name=tr("tab_settings"))
        self._init_ui()

    def _init_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        info = wx.StaticText(
            self,
            label=tr("set_info")
        )
        style_label(info, "muted")
        main_sizer.Add(info, 0, wx.ALL, 14)

        # Credentials, Language & Studio Defaults Card
        cred_box = wx.StaticBox(self, label=tr("set_box_cred"))
        style_staticbox(cred_box)
        cred_box_sizer = wx.StaticBoxSizer(cred_box, wx.VERTICAL)

        grid = wx.FlexGridSizer(rows=5, cols=3, vgap=12, hgap=12)
        grid.AddGrowableCol(1, 1)

        # 1. API Key
        lbl_key = wx.StaticText(cred_box, label=tr("lbl_api_key"))
        style_label(lbl_key)
        self.txt_key = wx.TextCtrl(cred_box, value=config.api_key, style=wx.TE_PASSWORD)
        style_text_ctrl(self.txt_key)
        key_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_test_key = wx.Button(cred_box, label=tr("btn_test_conn"))
        self.btn_get_key = wx.Button(cred_box, label=tr("btn_get_key"))
        style_button(self.btn_test_key, "secondary")
        style_button(self.btn_get_key, "gold")
        key_btn_sizer.Add(self.btn_test_key, 0, wx.RIGHT, 6)
        key_btn_sizer.Add(self.btn_get_key, 0)
        grid.Add(lbl_key, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.txt_key, 1, wx.EXPAND)
        grid.Add(key_btn_sizer, 0, wx.ALIGN_CENTER_VERTICAL)

        # 2. Output folder
        lbl_out = wx.StaticText(cred_box, label=tr("lbl_output_folder"))
        style_label(lbl_out)
        self.txt_output_dir = wx.TextCtrl(cred_box, value=str(config.output_dir))
        style_text_ctrl(self.txt_output_dir)
        self.btn_browse_out = wx.Button(cred_box, label=tr("btn_browse_out"))
        style_button(self.btn_browse_out, "secondary")
        grid.Add(lbl_out, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.txt_output_dir, 1, wx.EXPAND)
        grid.Add(self.btn_browse_out, 0, wx.ALIGN_CENTER_VERTICAL)

        # 3. Default Model
        lbl_def_model = wx.StaticText(cred_box, label=tr("lbl_def_model"))
        style_label(lbl_def_model)
        model_names = [m["name"] for m in SUPPORTED_MODELS]
        self.combo_def_model = wx.ComboBox(cred_box, choices=model_names, style=wx.CB_READONLY)
        style_combo(self.combo_def_model)
        def_m = config.get("default_model", "gemini-3.8-flash-tts")
        sel_m = 0
        for i, m in enumerate(SUPPORTED_MODELS):
            if m["id"] == def_m:
                sel_m = i
                break
        self.combo_def_model.SetSelection(sel_m)
        grid.Add(lbl_def_model, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.combo_def_model, 1, wx.EXPAND)
        grid.AddStretchSpacer()

        # 4. Default Voice
        lbl_def_voice = wx.StaticText(cred_box, label=tr("lbl_def_voice"))
        style_label(lbl_def_voice)
        voice_ids = [v.id for v in PREBUILT_VOICES]
        self.combo_def_voice = wx.ComboBox(cred_box, choices=voice_ids, style=wx.CB_READONLY)
        style_combo(self.combo_def_voice)
        def_v = config.get("default_voice", "Kore")
        sel_v = 0
        for i, vid in enumerate(voice_ids):
            if vid.lower() == def_v.lower():
                sel_v = i
                break
        self.combo_def_voice.SetSelection(sel_v)
        grid.Add(lbl_def_voice, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.combo_def_voice, 1, wx.EXPAND)
        grid.AddStretchSpacer()

        # 5. Interface Language (English Default / Thai)
        lbl_lang = wx.StaticText(cred_box, label=tr("lbl_ui_language"))
        style_label(lbl_lang)
        self.lang_codes = ["en", "th"]
        lang_choices = [tr("lang_en"), tr("lang_th")]
        self.combo_language = wx.ComboBox(cred_box, choices=lang_choices, style=wx.CB_READONLY)
        style_combo(self.combo_language)
        cur_lang = config.language
        self.combo_language.SetSelection(1 if cur_lang == "th" else 0)
        grid.Add(lbl_lang, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.combo_language, 1, wx.EXPAND)
        grid.AddStretchSpacer()

        cred_box_sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 12)
        main_sizer.Add(cred_box_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 14)

        # Accessibility Checkboxes
        acc_box = wx.StaticBox(self, label=tr("set_box_acc"))
        style_staticbox(acc_box)
        acc_sizer = wx.StaticBoxSizer(acc_box, wx.VERTICAL)

        self.chk_announcements = wx.CheckBox(
            acc_box,
            label=tr("chk_announcements")
        )
        style_checkbox(self.chk_announcements)
        self.chk_announcements.SetValue(config.get("speech_announcements", True))

        self.chk_beeps = wx.CheckBox(
            acc_box,
            label=tr("chk_beeps")
        )
        style_checkbox(self.chk_beeps)
        self.chk_beeps.SetValue(config.get("sound_cues", True))

        self.chk_autoplay = wx.CheckBox(
            acc_box,
            label=tr("chk_autoplay")
        )
        style_checkbox(self.chk_autoplay)
        self.chk_autoplay.SetValue(config.get("autoplay", True))

        acc_sizer.Add(self.chk_announcements, 0, wx.ALL, 8)
        acc_sizer.Add(self.chk_beeps, 0, wx.ALL, 8)
        acc_sizer.Add(self.chk_autoplay, 0, wx.ALL, 8)
        main_sizer.Add(acc_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 14)

        # Save Button
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_save = wx.Button(self, label=tr("btn_save_settings"))
        self.btn_save.SetDefault()
        style_button(self.btn_save, "primary")
        btn_sizer.Add(self.btn_save, 0, wx.RIGHT, 10)
        main_sizer.Add(btn_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        # Status
        self.lbl_status = wx.StaticText(self, label=tr("status_ready"))
        style_label(self.lbl_status, "status")
        main_sizer.Add(self.lbl_status, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 14)

        self.SetSizer(main_sizer)

        # Bindings
        self.btn_test_key.Bind(wx.EVT_BUTTON, self.on_test_key)
        self.btn_get_key.Bind(wx.EVT_BUTTON, self.on_get_api_key)
        self.btn_browse_out.Bind(wx.EVT_BUTTON, self.on_browse_output)
        self.btn_save.Bind(wx.EVT_BUTTON, self.on_save_settings)

    def on_get_api_key(self, event):
        """Open Google AI Studio Get API Key page directly in the default browser."""
        announcer.announce("Opening Google AI Studio Get API Key page in your default browser.")
        self.lbl_status.SetLabel(f"Opening Google AI Studio: {AI_STUDIO_API_KEY_URL}")
        if not wx.LaunchDefaultBrowser(AI_STUDIO_API_KEY_URL):
            webbrowser.open(AI_STUDIO_API_KEY_URL)

    def on_test_key(self, event):
        key = self.txt_key.GetValue().strip()
        if not key:
            announcer.announce("API key is empty. Please enter your Gemini API key.")
            self.txt_key.SetFocus()
            return

        self.btn_test_key.Enable(False)
        self.lbl_status.SetLabel("Testing Gemini API connection...")

        def _worker():
            success, msg = client_manager.validate_key(key)
            def _ui_update():
                self.btn_test_key.Enable(True)
                self.lbl_status.SetLabel(f"Connection result: {msg}")
                if success:
                    announcer.play_sound("success")
                    announcer.announce("Gemini API connection test successful!")
                else:
                    announcer.play_sound("error")
                    announcer.announce(f"Connection test failed: {msg}")
            wx.CallAfter(_ui_update)

        threading.Thread(target=_worker, daemon=True).start()

    def on_browse_output(self, event):
        with wx.DirDialog(self, "Select Output Directory", defaultPath=self.txt_output_dir.GetValue()) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.txt_output_dir.SetValue(dlg.GetPath())
                announcer.announce(f"Selected output directory: {dlg.GetPath()}")

    def on_save_settings(self, event):
        config.set("api_key", self.txt_key.GetValue().strip(), auto_save=False)
        config.set("output_dir", self.txt_output_dir.GetValue().strip(), auto_save=False)

        sel_m = self.combo_def_model.GetSelection()
        if sel_m != wx.NOT_FOUND:
            config.set("default_model", SUPPORTED_MODELS[sel_m]["id"], auto_save=False)

        sel_v = self.combo_def_voice.GetSelection()
        if sel_v != wx.NOT_FOUND:
            config.set("default_voice", PREBUILT_VOICES[sel_v].id, auto_save=False)

        sel_lang = self.combo_language.GetSelection()
        if sel_lang != wx.NOT_FOUND and sel_lang < len(self.lang_codes):
            config.set("language", self.lang_codes[sel_lang], auto_save=False)

        config.set("speech_announcements", self.chk_announcements.GetValue(), auto_save=False)
        config.set("sound_cues", self.chk_beeps.GetValue(), auto_save=False)
        config.set("autoplay", self.chk_autoplay.GetValue(), auto_save=False)
        config.set("first_run_completed", True, auto_save=False)

        config.save()
        announcer.play_sound("success")
        announcer.announce(tr("msg_settings_saved"))
        self.lbl_status.SetLabel(tr("msg_settings_saved"))

        # Always prompt the user to restart so all changes (including language and defaults) take effect
        resp = wx.MessageBox(
            tr("restart_prompt_msg"),
            tr("restart_prompt_title"),
            wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION,
            self
        )
        if resp == wx.YES:
            top_win = wx.GetTopLevelParent(self)
            restart_application(top_win)

    def _toggle_announcements(self, event=None):
        val = not self.chk_announcements.GetValue()
        self.chk_announcements.SetValue(val)
        announcer.announce(f"Spoken announcements {'enabled' if val else 'disabled'}.")

    def _toggle_beeps(self, event=None):
        val = not self.chk_beeps.GetValue()
        self.chk_beeps.SetValue(val)
        announcer.announce(f"Sound cues {'enabled' if val else 'disabled'}.")

    def _toggle_autoplay(self, event=None):
        val = not self.chk_autoplay.GetValue()
        self.chk_autoplay.SetValue(val)
        announcer.announce(f"Autoplay {'enabled' if val else 'disabled'}.")
