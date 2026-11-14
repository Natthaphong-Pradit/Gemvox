import os
import subprocess
import sys
import threading
import webbrowser
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from gemvox.config import config
from gemvox.i18n import tr
from gemvox.accessibility import announcer
try:
    from gemvox.core.client import client_manager
except ImportError:
    from gemvox.core import client_manager
from gemvox.core.voice_catalog import SUPPORTED_MODELS, get_all_voices
from gemvox.ui.dialogs import UpdateDialog
from gemvox.ui.theme import (
    apply_accessible,
    call_after,
    clean_mnemonic,
    style_button,
    style_label,
)

AI_STUDIO_API_KEY_URL = "https://aistudio.google.com/apikey"


def restart_application(top_window: QWidget = None):
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
        if top_window is not None:
            top_window.close()
        app = QApplication.instance()
        if app is not None:
            app.quit()


class SettingsPanel(QWidget):
    """Accessible settings panel for API key, interface language, accessibility, and defaults."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._voices_cache = []
        self.setAccessibleName(clean_mnemonic(tr("tab_settings")))
        self._init_ui()
        config.add_voices_listener(self._on_voices_changed)

    def _on_voices_changed(self):
        call_after(self.refresh_default_voices)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        info = QLabel(tr("set_info"), self)
        info.setWordWrap(True)
        style_label(info, "muted")
        main_layout.addWidget(info)

        # Credentials, Language & Studio Defaults Card
        cred_box = QGroupBox(clean_mnemonic(tr("set_box_cred")), self)
        cred_box.setAccessibleName(clean_mnemonic(tr("set_box_cred")))
        grid = QGridLayout(cred_box)
        grid.setContentsMargins(12, 14, 12, 12)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)

        # 1. API Key
        lbl_key = QLabel(tr("lbl_api_key"), cred_box)
        self.txt_key = QLineEdit(config.api_key, cred_box)
        self.txt_key.setEchoMode(QLineEdit.Password)
        apply_accessible(self.txt_key, name=tr("lbl_api_key"), label=lbl_key)

        key_btn_row = QHBoxLayout()
        key_btn_row.setSpacing(6)
        self.btn_test_key = QPushButton(tr("btn_test_conn"), cred_box)
        self.btn_get_key = QPushButton(tr("btn_get_key"), cred_box)
        style_button(self.btn_test_key, "secondary")
        style_button(self.btn_get_key, "gold")
        key_btn_row.addWidget(self.btn_test_key)
        key_btn_row.addWidget(self.btn_get_key)

        grid.addWidget(lbl_key, 0, 0)
        grid.addWidget(self.txt_key, 0, 1)
        grid.addLayout(key_btn_row, 0, 2)

        # 2. Output folder
        lbl_out = QLabel(tr("lbl_output_folder"), cred_box)
        self.txt_output_dir = QLineEdit(str(config.output_dir), cred_box)
        apply_accessible(self.txt_output_dir, name=tr("lbl_output_folder"), label=lbl_out)
        self.btn_browse_out = QPushButton(tr("btn_browse_out"), cred_box)
        style_button(self.btn_browse_out, "secondary")
        grid.addWidget(lbl_out, 1, 0)
        grid.addWidget(self.txt_output_dir, 1, 1)
        grid.addWidget(self.btn_browse_out, 1, 2)

        # 3. Default Model
        lbl_def_model = QLabel(tr("lbl_def_model"), cred_box)
        self.combo_def_model = QComboBox(cred_box)
        self.combo_def_model.addItems([m["name"] for m in SUPPORTED_MODELS])
        def_m = config.get("default_model", "gemini-3.8-flash-tts")
        sel_m = 0
        for i, m in enumerate(SUPPORTED_MODELS):
            if m["id"] == def_m:
                sel_m = i
                break
        self.combo_def_model.setCurrentIndex(sel_m)
        apply_accessible(self.combo_def_model, name=tr("lbl_def_model"), label=lbl_def_model)
        grid.addWidget(lbl_def_model, 2, 0)
        grid.addWidget(self.combo_def_model, 2, 1)

        # 4. Default Voice
        lbl_def_voice = QLabel(tr("lbl_def_voice"), cred_box)
        self.combo_def_voice = QComboBox(cred_box)
        apply_accessible(self.combo_def_voice, name=tr("lbl_def_voice"), label=lbl_def_voice)
        self.refresh_default_voices()
        grid.addWidget(lbl_def_voice, 3, 0)
        grid.addWidget(self.combo_def_voice, 3, 1)

        # 5. Interface Language
        lbl_lang = QLabel(tr("lbl_ui_language"), cred_box)
        self.lang_codes = ["en", "th"]
        self.combo_language = QComboBox(cred_box)
        self.combo_language.addItems([tr("lang_en"), tr("lang_th")])
        self.combo_language.setCurrentIndex(1 if config.language == "th" else 0)
        apply_accessible(self.combo_language, name=tr("lbl_ui_language"), label=lbl_lang)
        grid.addWidget(lbl_lang, 4, 0)
        grid.addWidget(self.combo_language, 4, 1)

        main_layout.addWidget(cred_box)

        # Accessibility Checkboxes Card
        acc_box = QGroupBox(clean_mnemonic(tr("set_box_acc")), self)
        acc_box.setAccessibleName(clean_mnemonic(tr("set_box_acc")))
        acc_layout = QVBoxLayout(acc_box)
        acc_layout.setContentsMargins(12, 14, 12, 12)
        acc_layout.setSpacing(8)

        self.chk_announcements = QCheckBox(tr("chk_announcements"), acc_box)
        self.chk_announcements.setChecked(config.get("speech_announcements", True))
        apply_accessible(self.chk_announcements, name=tr("chk_announcements"))

        self.chk_beeps = QCheckBox(tr("chk_beeps"), acc_box)
        self.chk_beeps.setChecked(config.get("sound_cues", True))
        apply_accessible(self.chk_beeps, name=tr("chk_beeps"))

        self.chk_autoplay = QCheckBox(tr("chk_autoplay"), acc_box)
        self.chk_autoplay.setChecked(config.get("autoplay", True))
        apply_accessible(self.chk_autoplay, name=tr("chk_autoplay"))

        acc_layout.addWidget(self.chk_announcements)
        acc_layout.addWidget(self.chk_beeps)
        acc_layout.addWidget(self.chk_autoplay)
        main_layout.addWidget(acc_box)

        # Save & Update Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.btn_save = QPushButton(tr("btn_save_settings"), self)
        self.btn_save.setDefault(True)
        self.btn_check_updates = QPushButton(tr("btn_check_updates"), self)
        style_button(self.btn_save, "primary")
        style_button(self.btn_check_updates, "gold")
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_check_updates)
        btn_row.addStretch(1)
        main_layout.addLayout(btn_row)

        # Status
        self.lbl_status = QLabel(tr("status_ready"), self)
        style_label(self.lbl_status, "status")
        apply_accessible(self.lbl_status, name="Status")
        main_layout.addWidget(self.lbl_status)
        main_layout.addStretch(1)

        # Connections
        self.btn_test_key.clicked.connect(self.on_test_key)
        self.btn_get_key.clicked.connect(self.on_get_api_key)
        self.btn_browse_out.clicked.connect(self.on_browse_output)
        self.btn_save.clicked.connect(self.on_save_settings)
        self.btn_check_updates.clicked.connect(self.on_check_updates)

    def refresh_default_voices(self):
        current_id = None
        sel = self.combo_def_voice.currentIndex()
        if 0 <= sel < len(self._voices_cache):
            current_id = self._voices_cache[sel].id

        voices = get_all_voices()
        self._voices_cache = voices
        choices = [
            f"{v.display_name} ({v.id})" if v.is_custom else v.id
            for v in voices
        ]
        self.combo_def_voice.clear()
        self.combo_def_voice.addItems(choices)

        def_v = current_id or config.get("default_voice", "Kore")
        sel_v = 0
        for i, v in enumerate(voices):
            if v.id.lower() == def_v.lower():
                sel_v = i
                break
        if choices:
            self.combo_def_voice.setCurrentIndex(sel_v)

    def on_get_api_key(self, *args):
        """Open Google AI Studio Get API Key page directly in the default browser."""
        announcer.announce(tr("announce_opening_ai_studio"))
        self.lbl_status.setText(tr("status_opening_ai_studio", url=AI_STUDIO_API_KEY_URL))
        if not QDesktopServices.openUrl(QUrl(AI_STUDIO_API_KEY_URL)):
            webbrowser.open(AI_STUDIO_API_KEY_URL)

    def on_test_key(self, *args):
        key = self.txt_key.text().strip()
        if not key:
            announcer.announce(tr("announce_empty_api_key"))
            self.txt_key.setFocus()
            return

        self.btn_test_key.setEnabled(False)
        self.lbl_status.setText(tr("status_testing_conn"))

        def _worker():
            success, msg = client_manager.validate_key(key)

            def _ui_update():
                self.btn_test_key.setEnabled(True)
                self.lbl_status.setText(tr("status_conn_result", msg=msg))
                if success:
                    announcer.play_sound("success")
                    announcer.announce(tr("announce_conn_success"))
                else:
                    announcer.play_sound("error")
                    announcer.announce(tr("announce_conn_failed", msg=msg))

            call_after(_ui_update)

        threading.Thread(target=_worker, daemon=True).start()

    def on_browse_output(self, *args):
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.txt_output_dir.text(),
        )
        if path:
            self.txt_output_dir.setText(path)
            announcer.announce(tr("announce_selected_output_dir", path=path))

    def on_save_settings(self, *args):
        config.set("api_key", self.txt_key.text().strip(), auto_save=False)
        config.set("output_dir", self.txt_output_dir.text().strip(), auto_save=False)

        sel_m = self.combo_def_model.currentIndex()
        if 0 <= sel_m < len(SUPPORTED_MODELS):
            config.set("default_model", SUPPORTED_MODELS[sel_m]["id"], auto_save=False)

        sel_v = self.combo_def_voice.currentIndex()
        if 0 <= sel_v < len(self._voices_cache):
            config.set("default_voice", self._voices_cache[sel_v].id, auto_save=False)

        sel_lang = self.combo_language.currentIndex()
        if 0 <= sel_lang < len(self.lang_codes):
            config.set("language", self.lang_codes[sel_lang], auto_save=False)

        config.set("speech_announcements", self.chk_announcements.isChecked(), auto_save=False)
        config.set("sound_cues", self.chk_beeps.isChecked(), auto_save=False)
        config.set("autoplay", self.chk_autoplay.isChecked(), auto_save=False)
        config.set("first_run_completed", True, auto_save=False)

        config.save()
        announcer.play_sound("success")
        announcer.announce(tr("msg_settings_saved"))
        self.lbl_status.setText(tr("msg_settings_saved"))

        resp = QMessageBox.question(
            self,
            tr("restart_prompt_title"),
            tr("restart_prompt_msg"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if resp == QMessageBox.Yes:
            restart_application(self.window())

    def _toggle_announcements(self, *args):
        val = not self.chk_announcements.isChecked()
        self.chk_announcements.setChecked(val)
        announcer.announce(tr("announce_toggle_announcements_on" if val else "announce_toggle_announcements_off"))

    def _toggle_beeps(self, *args):
        val = not self.chk_beeps.isChecked()
        self.chk_beeps.setChecked(val)
        announcer.announce(tr("announce_toggle_beeps_on" if val else "announce_toggle_beeps_off"))

    def _toggle_autoplay(self, *args):
        val = not self.chk_autoplay.isChecked()
        self.chk_autoplay.setChecked(val)
        announcer.announce(tr("announce_toggle_autoplay_on" if val else "announce_toggle_autoplay_off"))

    def on_check_updates(self, *args):
        dlg = UpdateDialog(self)
        dlg.exec()
