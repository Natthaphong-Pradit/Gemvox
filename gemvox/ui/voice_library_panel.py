import threading
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from gemvox.config import config
from gemvox.i18n import tr
from gemvox.accessibility import announcer
from gemvox.core.voice_catalog import PREBUILT_VOICES
from gemvox.core.tts_engine import tts_engine
from gemvox.core.audio_player import audio_player
from gemvox.ui.theme import (
    apply_accessible,
    call_after,
    clean_mnemonic,
    style_button,
    style_label,
)


class VoiceLibraryPanel(QWidget):
    """Panel for browsing the 30 prebuilt studio voices, managing custom voices, and querying the Extended Voice Library."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.voices_data: list[dict] = []
        self._showing_remote = False
        self.setAccessibleName(clean_mnemonic(tr("tab_library")))
        self._init_ui()
        self.load_prebuilt_voices(announce=False)
        config.add_voices_listener(self._on_voices_changed)

    def _on_voices_changed(self):
        if not self._showing_remote:
            call_after(self.load_prebuilt_voices, False)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        info = QLabel(tr("vl_info"), self)
        info.setWordWrap(True)
        style_label(info, "muted")
        main_layout.addWidget(info)

        # Filters Card
        filter_box = QGroupBox(clean_mnemonic(tr("vl_box_filters")), self)
        filter_box.setAccessibleName(clean_mnemonic(tr("vl_box_filters")))
        filter_layout = QVBoxLayout(filter_box)
        filter_layout.setContentsMargins(12, 14, 12, 12)
        filter_layout.setSpacing(10)

        filter_grid = QGridLayout()
        filter_grid.setHorizontalSpacing(12)
        filter_grid.setVerticalSpacing(10)
        filter_grid.setColumnStretch(1, 1)
        filter_grid.setColumnStretch(3, 1)

        # Search query
        lbl_search = QLabel(tr("lbl_search_query"), filter_box)
        self.txt_search = QLineEdit("", filter_box)
        apply_accessible(self.txt_search, name=tr("lbl_search_query"), label=lbl_search)
        filter_grid.addWidget(lbl_search, 0, 0)
        filter_grid.addWidget(self.txt_search, 0, 1)

        # Language
        lbl_lang = QLabel(tr("lbl_language"), filter_box)
        self.txt_lang = QLineEdit("en-US", filter_box)
        apply_accessible(self.txt_lang, name=tr("lbl_language"), label=lbl_lang)
        filter_grid.addWidget(lbl_lang, 0, 2)
        filter_grid.addWidget(self.txt_lang, 0, 3)

        # Gender
        lbl_gender = QLabel(tr("lbl_gender_g"), filter_box)
        self.combo_gender = QComboBox(filter_box)
        self.combo_gender.addItems(["All", "female", "male", "neutral"])
        self.combo_gender.setCurrentIndex(0)
        apply_accessible(self.combo_gender, name=tr("lbl_gender_g"), label=lbl_gender)
        filter_grid.addWidget(lbl_gender, 1, 0)
        filter_grid.addWidget(self.combo_gender, 1, 1)

        # Domain
        lbl_domain = QLabel(tr("lbl_domain"), filter_box)
        self.combo_domain = QComboBox(filter_box)
        self.combo_domain.addItems(["All", "Audiobook", "Conversational", "News"])
        self.combo_domain.setCurrentIndex(0)
        apply_accessible(self.combo_domain, name=tr("lbl_domain"), label=lbl_domain)
        filter_grid.addWidget(lbl_domain, 1, 2)
        filter_grid.addWidget(self.combo_domain, 1, 3)

        filter_layout.addLayout(filter_grid)

        btn_filter_row = QHBoxLayout()
        btn_filter_row.setSpacing(10)
        self.btn_search_remote = QPushButton(tr("btn_search_online"), filter_box)
        self.btn_show_prebuilt = QPushButton(tr("btn_show_prebuilt"), filter_box)
        style_button(self.btn_search_remote, "primary")
        style_button(self.btn_show_prebuilt, "secondary")
        btn_filter_row.addWidget(self.btn_search_remote)
        btn_filter_row.addWidget(self.btn_show_prebuilt)
        btn_filter_row.addStretch(1)
        filter_layout.addLayout(btn_filter_row)

        main_layout.addWidget(filter_box)

        # Voices List
        lbl_list = QLabel(tr("lbl_voices_list"), self)
        style_label(lbl_list, "section")
        main_layout.addWidget(lbl_list)

        self.listbox_voices = QListWidget(self)
        apply_accessible(self.listbox_voices, name=tr("lbl_voices_list"), label=lbl_list)
        main_layout.addWidget(self.listbox_voices, 1)

        # Action Buttons
        act_row = QHBoxLayout()
        act_row.setSpacing(8)
        self.btn_audition = QPushButton(tr("btn_audition_a"), self)
        self.btn_use_voice = QPushButton(tr("btn_use_voice_y"), self)
        self.btn_copy_id = QPushButton(tr("btn_copy_id_c"), self)
        self.btn_delete_custom = QPushButton(tr("btn_delete_voice_r"), self)
        self.btn_delete_custom.setEnabled(False)

        style_button(self.btn_audition, "gold")
        style_button(self.btn_use_voice, "primary")
        style_button(self.btn_copy_id, "secondary")
        style_button(self.btn_delete_custom, "danger")

        act_row.addWidget(self.btn_audition)
        act_row.addWidget(self.btn_use_voice)
        act_row.addWidget(self.btn_copy_id)
        act_row.addWidget(self.btn_delete_custom)
        act_row.addStretch(1)
        main_layout.addLayout(act_row)

        # Status
        self.lbl_status = QLabel(tr("status_ready"), self)
        style_label(self.lbl_status, "status")
        apply_accessible(self.lbl_status, name="Status")
        main_layout.addWidget(self.lbl_status)

        # Connections
        self.btn_search_remote.clicked.connect(self.on_search_remote)
        self.btn_show_prebuilt.clicked.connect(lambda *_: self.load_prebuilt_voices(announce=True))
        self.btn_audition.clicked.connect(self.on_audition)
        self.btn_use_voice.clicked.connect(self.on_use_voice)
        self.btn_copy_id.clicked.connect(self.on_copy_id)
        self.btn_delete_custom.clicked.connect(self.on_delete_custom)
        self.listbox_voices.currentRowChanged.connect(lambda *_: self._update_action_buttons())
        self.listbox_voices.itemDoubleClicked.connect(lambda *_: self.on_audition())

    def _update_action_buttons(self):
        sel = self.listbox_voices.currentRow()
        if 0 <= sel < len(self.voices_data):
            is_custom = bool(self.voices_data[sel].get("is_custom", False))
            self.btn_delete_custom.setEnabled(is_custom)
            self.btn_use_voice.setEnabled(True)
        else:
            self.btn_delete_custom.setEnabled(False)
            self.btn_use_voice.setEnabled(False)

    def load_prebuilt_voices(self, announce: bool = True):
        self._showing_remote = False
        self.voices_data = []
        self.listbox_voices.clear()
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
                "is_custom": True,
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
                "is_custom": False,
            }
            self.voices_data.append(entry)
            choices.append(f"{v.id:<15} | Tone: {v.tone:<16} | ({v.gender}) - {v.description}")

        self.listbox_voices.addItems(choices)
        if choices:
            self.listbox_voices.setCurrentRow(0)
        self._update_action_buttons()

        total = len(choices)
        custom_count = len(custom_saved)
        prebuilt_count = len(PREBUILT_VOICES)
        self.lbl_status.setText(tr("status_showing_voices", total=total, custom=custom_count, prebuilt=prebuilt_count))
        if announce:
            announcer.announce(tr("announce_loaded_voices", total=total, custom=custom_count, prebuilt=prebuilt_count))

    def on_search_remote(self, *args):
        query = self.txt_search.text().strip()
        lang = self.txt_lang.text().strip()
        gender = self.combo_gender.currentText().strip()
        domain = self.combo_domain.currentText().strip()

        self.btn_search_remote.setEnabled(False)
        self.lbl_status.setText(tr("announce_querying_library"))

        def _worker():
            try:
                results = tts_engine.search_voice_library(
                    search_query=query,
                    language_code=lang if lang else None,
                    gender=gender if gender != "All" else None,
                    context_domain=domain if domain != "All" else None,
                )
                self._showing_remote = True
                self.voices_data = results
                choices = [
                    f"{v['id']} | {v['display_name']} ({v.get('gender','')}, {v.get('language_code','')}): {v.get('description','')}"
                    for v in results
                ]

                def _ui_update():
                    self.btn_search_remote.setEnabled(True)
                    self.listbox_voices.clear()
                    self.listbox_voices.addItems(choices)
                    if choices:
                        self.listbox_voices.setCurrentRow(0)
                    self._update_action_buttons()
                    self.lbl_status.setText(tr("announce_found_voices", count=len(choices)))

                call_after(_ui_update)
            except Exception as e:
                def _error_update():
                    self.btn_search_remote.setEnabled(True)
                    self.lbl_status.setText(tr("status_error", error=e))

                call_after(_error_update)

        threading.Thread(target=_worker, daemon=True).start()

    def get_selected_voice_entry(self) -> dict:
        sel = self.listbox_voices.currentRow()
        if 0 <= sel < len(self.voices_data):
            return self.voices_data[sel]
        return {"id": "Kore", "display_name": "Kore", "description": "", "is_custom": False}

    def get_selected_voice_id(self) -> str:
        return self.get_selected_voice_entry().get("id", "Kore")

    def on_audition(self, *args):
        voice_id = self.get_selected_voice_id()
        announcer.announce(tr("status_auditioning", voice=voice_id))
        self.lbl_status.setText(tr("status_auditioning", voice=voice_id))

        def _worker():
            try:
                sample_text = f"This is an audition preview for voice {voice_id}."
                wav_bytes, _, _ = tts_engine.synthesize_single_speaker(
                    text=sample_text,
                    voice=voice_id,
                    style="natural and clear",
                )
                audio_player.play_wav_bytes(wav_bytes)
                call_after(self.lbl_status.setText, tr("status_audition_done", voice=voice_id))
            except Exception as e:
                call_after(self.lbl_status.setText, tr("status_error", error=e))

        threading.Thread(target=_worker, daemon=True).start()

    def on_use_voice(self, *args):
        entry = self.get_selected_voice_entry()
        voice_id = entry.get("id", "Kore")
        display_name = entry.get("display_name") or voice_id
        desc = entry.get("description", "")

        top_win = self.window()
        if hasattr(top_win, "tab_single"):
            top_win.tab_single.select_voice_by_id(voice_id, display_name=display_name, description=desc)
        msg = tr("announce_voice_selected_for_tts", voice=display_name)
        self.lbl_status.setText(msg)
        announcer.play_sound("success")
        announcer.announce(msg)

    def on_delete_custom(self, *args):
        entry = self.get_selected_voice_entry()
        if not entry.get("is_custom"):
            return
        voice_id = entry.get("id", "")
        display_name = entry.get("display_name", voice_id)

        resp = QMessageBox.warning(
            self,
            tr("confirm_delete_voice_title"),
            tr("confirm_delete_voice_msg", name=display_name, voice_id=voice_id),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            config.remove_custom_voice(voice_id)
            self.load_prebuilt_voices(announce=False)
            self.listbox_voices.setFocus()
            announcer.announce(tr("announce_deleted_custom_voice", name=display_name))

    def on_copy_id(self, *args):
        voice_id = self.get_selected_voice_id()
        cb = QApplication.clipboard()
        if cb is not None:
            cb.setText(voice_id)
            announcer.announce(tr("announce_copied_voice_id", voice_id=voice_id))
