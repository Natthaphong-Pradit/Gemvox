from pathlib import Path
import threading
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)
from gemvox.ui.accessible_text import AccessibleTextArea
from gemvox.config import config
from gemvox.i18n import tr
from gemvox.accessibility import announcer
from gemvox.core.tts_engine import tts_engine
from gemvox.ui.theme import (
    apply_accessible,
    call_after,
    clean_mnemonic,
    get_qfont,
    style_button,
    style_label,
)

MANDATORY_CONSENT_TEXT = (
    "I am the owner of this voice and I consent to Google using this voice to create a synthetic voice model."
)


class _StorageModeGroup(QGroupBox):
    """Accessible radio group for Stateful vs Stateless storage mode."""

    def __init__(self, parent=None):
        super().__init__(clean_mnemonic(tr("lbl_storage_mode")), parent)
        self.setAccessibleName(clean_mnemonic(tr("lbl_storage_mode")))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 12, 10, 8)
        layout.setSpacing(6)

        self.group = QButtonGroup(self)
        self.rb_stateful = QRadioButton(tr("mode_stateful"), self)
        self.rb_stateless = QRadioButton(tr("mode_stateless"), self)
        self.rb_stateful.setChecked(True)
        apply_accessible(self.rb_stateful, name=tr("mode_stateful"))
        apply_accessible(self.rb_stateless, name=tr("mode_stateless"))

        self.group.addButton(self.rb_stateful, 0)
        self.group.addButton(self.rb_stateless, 1)
        layout.addWidget(self.rb_stateful)
        layout.addWidget(self.rb_stateless)

    def focus_active_radio(self):
        checked = self.group.checkedButton()
        if checked is not None:
            checked.setFocus()
        else:
            self.rb_stateful.setFocus()

    def selected_index(self) -> int:
        return self.group.checkedId()


class VoiceReplicationPanel(QWidget):
    """Panel for replicating a speaker voice with reference and consent audio."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_voice_id = None
        self.setAccessibleName(clean_mnemonic(tr("tab_replication")))
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        info_box = QLabel(tr("vr_info"), self)
        info_box.setWordWrap(True)
        style_label(info_box, "muted")
        main_layout.addWidget(info_box)

        rep_box = QGroupBox(clean_mnemonic(tr("vr_box_cloning")), self)
        rep_box.setAccessibleName(clean_mnemonic(tr("vr_box_cloning")))
        grid = QGridLayout(rep_box)
        grid.setContentsMargins(12, 14, 12, 12)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)

        # 1. Voice Name
        lbl_name = QLabel(tr("lbl_voice_name"), rep_box)
        self.txt_name = QLineEdit("My Replicated Voice", rep_box)
        apply_accessible(self.txt_name, name=tr("lbl_voice_name"), label=lbl_name)
        grid.addWidget(lbl_name, 0, 0)
        grid.addWidget(self.txt_name, 0, 1)

        # 2. Reference audio file
        lbl_ref = QLabel(tr("lbl_ref_audio"), rep_box)
        self.txt_ref_path = QLineEdit("", rep_box)
        apply_accessible(self.txt_ref_path, name=tr("lbl_ref_audio"), label=lbl_ref)
        self.btn_browse_ref = QPushButton(tr("btn_browse_ref"), rep_box)
        style_button(self.btn_browse_ref, "secondary")
        grid.addWidget(lbl_ref, 1, 0)
        grid.addWidget(self.txt_ref_path, 1, 1)
        grid.addWidget(self.btn_browse_ref, 1, 2)

        # 3. Consent statement box
        lbl_consent_statement = QLabel(tr("lbl_consent_phrase"), rep_box)
        self.txt_consent_phrase = AccessibleTextArea(MANDATORY_CONSENT_TEXT, rep_box, read_only=True)
        self.txt_consent_phrase.setTabChangesFocus(True)
        self.txt_consent_phrase.setFixedHeight(64)
        self.txt_consent_phrase.setFont(get_qfont(10))
        apply_accessible(self.txt_consent_phrase, name=tr("lbl_consent_phrase"), label=lbl_consent_statement)
        self.btn_copy_consent = QPushButton(tr("btn_copy_statement"), rep_box)
        style_button(self.btn_copy_consent, "gold")
        grid.addWidget(lbl_consent_statement, 2, 0, Qt.AlignTop)
        grid.addWidget(self.txt_consent_phrase, 2, 1)
        grid.addWidget(self.btn_copy_consent, 2, 2, Qt.AlignVCenter)

        # 4. Consent audio file
        lbl_con = QLabel(tr("lbl_con_audio"), rep_box)
        self.txt_con_path = QLineEdit("", rep_box)
        apply_accessible(self.txt_con_path, name=tr("lbl_con_audio"), label=lbl_con)
        self.btn_browse_con = QPushButton(tr("btn_browse_con"), rep_box)
        style_button(self.btn_browse_con, "secondary")
        grid.addWidget(lbl_con, 3, 0)
        grid.addWidget(self.txt_con_path, 3, 1)
        grid.addWidget(self.btn_browse_con, 3, 2)

        # 5. Storage Mode
        lbl_mode = QLabel(tr("lbl_storage_mode"), rep_box)
        self.radio_mode = _StorageModeGroup(rep_box)
        lbl_mode.setBuddy(self.radio_mode.rb_stateful)
        grid.addWidget(lbl_mode, 4, 0, Qt.AlignTop)
        grid.addWidget(self.radio_mode, 4, 1)

        main_layout.addWidget(rep_box)

        # Actions
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.btn_replicate = QPushButton(tr("btn_replicate"), self)
        self.btn_replicate.setDefault(True)
        style_button(self.btn_replicate, "primary")

        self.btn_copy_id = QPushButton(tr("btn_copy_id_y"), self)
        self.btn_copy_id.setEnabled(False)
        style_button(self.btn_copy_id, "gold")

        btn_row.addWidget(self.btn_replicate)
        btn_row.addWidget(self.btn_copy_id)
        btn_row.addStretch(1)
        main_layout.addLayout(btn_row)

        # Output & Status
        self.lbl_id = QLabel(tr("lbl_voice_id_none"), self)
        style_label(self.lbl_id, "mono")
        apply_accessible(self.lbl_id, name="Assigned Voice ID")

        self.lbl_status = QLabel(tr("status_ready"), self)
        style_label(self.lbl_status, "status")
        apply_accessible(self.lbl_status, name="Status")

        main_layout.addWidget(self.lbl_id)
        main_layout.addWidget(self.lbl_status)
        main_layout.addStretch(1)

        # Connections
        self.btn_browse_ref.clicked.connect(self.on_browse_ref)
        self.btn_browse_con.clicked.connect(self.on_browse_con)
        self.btn_copy_consent.clicked.connect(self.on_copy_consent)
        self.btn_replicate.clicked.connect(self.on_replicate)
        self.btn_copy_id.clicked.connect(self.on_copy_id)

    def on_browse_ref(self, *args):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Reference Audio (WAV, 10-30 seconds)",
            str(config.output_dir),
            "WAV files (*.wav)",
        )
        if path:
            self.txt_ref_path.setText(path)
            announcer.announce(tr("announce_selected_ref_audio", filename=Path(path).name))

    def on_browse_con(self, *args):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Consent Audio (WAV reciting phrase)",
            str(config.output_dir),
            "WAV files (*.wav)",
        )
        if path:
            self.txt_con_path.setText(path)
            announcer.announce(tr("announce_selected_con_audio", filename=Path(path).name))

    def on_copy_consent(self, *args):
        cb = QApplication.clipboard()
        if cb is not None:
            cb.setText(MANDATORY_CONSENT_TEXT)
            announcer.announce(tr("announce_copied_consent"))

    def on_replicate(self, *args):
        name = self.txt_name.text().strip()
        ref_path = self.txt_ref_path.text().strip()
        con_path = self.txt_con_path.text().strip()
        store_stateful = (self.radio_mode.selected_index() == 0)

        if not name:
            announcer.announce(tr("announce_enter_voice_name"))
            self.txt_name.setFocus()
            return
        if not ref_path:
            announcer.announce(tr("announce_select_ref_audio"))
            self.btn_browse_ref.setFocus()
            return
        if not con_path:
            announcer.announce(tr("announce_select_con_audio"))
            self.btn_browse_con.setFocus()
            return

        self.btn_replicate.setEnabled(False)
        self.lbl_status.setText(tr("status_replicating"))

        def _worker():
            try:
                voice_id = tts_engine.replicate_voice(
                    display_name=name,
                    reference_audio_path=ref_path,
                    consent_audio_path=con_path,
                    store=store_stateful,
                )
                self.last_voice_id = voice_id

                def _ui_update():
                    self.btn_replicate.setEnabled(True)
                    self.btn_copy_id.setEnabled(True)
                    self.lbl_id.setText(tr("lbl_voice_id_assigned", voice_id=voice_id))
                    self.lbl_status.setText(tr("status_replicate_success"))

                call_after(_ui_update)
            except Exception as e:
                def _error_update():
                    self.btn_replicate.setEnabled(True)
                    self.lbl_status.setText(tr("status_error", error=e))

                call_after(_error_update)

        threading.Thread(target=_worker, daemon=True).start()

    def on_copy_id(self, *args):
        if self.last_voice_id:
            cb = QApplication.clipboard()
            if cb is not None:
                cb.setText(self.last_voice_id)
                announcer.announce(tr("announce_copied_voice_id", voice_id=self.last_voice_id))
