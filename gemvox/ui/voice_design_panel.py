import threading
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from gemvox.ui.accessible_text import AccessibleTextArea
from gemvox.config import config
from gemvox.i18n import tr
from gemvox.accessibility import announcer
from gemvox.core.tts_engine import tts_engine
from gemvox.core.audio_player import audio_player
from gemvox.ui.player_bar import AudioTransportBar
from gemvox.ui.theme import (
    apply_accessible,
    call_after,
    clean_mnemonic,
    get_qfont,
    style_button,
    style_label,
)

SAMPLE_DESIGN_PROMPTS = [
    {
        "name": "Warm British Astronomer",
        "gender": "Male",
        "lang": "en-GB",
        "prompt": "A warm, thoughtful astronomer in his late 60s with a gentle British accent, speaking with quiet wonder.",
    },
    {
        "name": "Youthful Tech Educator",
        "gender": "Female",
        "lang": "en-US",
        "prompt": "An enthusiastic, friendly computer science teacher in her late 20s, with a clear, encouraging American delivery.",
    },
    {
        "name": "Epic Fantasy Narrator",
        "gender": "Male",
        "lang": "en-GB",
        "prompt": "A deep, resonant, theatrical fantasy audiobook narrator with rich baritone texture and dramatic pacing.",
    },
]


class VoiceDesignPanel(QWidget):
    """Panel for Voice Design: creating persistent vocal personas from text prompts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_voice_id = None
        self.last_sample_bytes = None
        self.setAccessibleName(clean_mnemonic(tr("tab_design")))
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        info_box = QLabel(tr("vd_info"), self)
        info_box.setWordWrap(True)
        style_label(info_box, "muted")
        main_layout.addWidget(info_box)

        # Persona Parameters Card
        design_box = QGroupBox(clean_mnemonic(tr("vd_box_specs")), self)
        design_box.setAccessibleName(clean_mnemonic(tr("vd_box_specs")))
        grid = QGridLayout(design_box)
        grid.setContentsMargins(12, 14, 12, 12)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(3, 1)

        # Voice Name
        lbl_name = QLabel(tr("lbl_voice_name"), design_box)
        self.txt_name = QLineEdit("Warm British Astronomer", design_box)
        apply_accessible(self.txt_name, name=tr("lbl_voice_name"), label=lbl_name)
        grid.addWidget(lbl_name, 0, 0)
        grid.addWidget(self.txt_name, 0, 1)

        # Gender
        lbl_gender = QLabel(tr("lbl_gender"), design_box)
        self.combo_gender = QComboBox(design_box)
        self.combo_gender.addItems(["Male", "Female", "Neutral"])
        self.combo_gender.setCurrentIndex(0)
        apply_accessible(self.combo_gender, name=tr("lbl_gender"), label=lbl_gender)
        grid.addWidget(lbl_gender, 1, 0)
        grid.addWidget(self.combo_gender, 1, 1)

        # Language code
        lbl_lang = QLabel(tr("lbl_lang_code"), design_box)
        self.txt_lang = QLineEdit("en-GB", design_box)
        apply_accessible(self.txt_lang, name=tr("lbl_lang_code"), label=lbl_lang)
        grid.addWidget(lbl_lang, 2, 0)
        grid.addWidget(self.txt_lang, 2, 1)

        # Persona prompt
        lbl_prompt = QLabel(tr("lbl_persona_prompt"), design_box)
        self.txt_prompt = AccessibleTextArea(
            "A warm, thoughtful astronomer in his late 60s with a gentle British accent, speaking with quiet wonder.",
            design_box,
        )
        self.txt_prompt.setTabChangesFocus(True)
        self.txt_prompt.setFont(get_qfont(10.5))
        apply_accessible(self.txt_prompt, name=tr("lbl_persona_prompt"), label=lbl_prompt)
        grid.addWidget(lbl_prompt, 3, 0)
        grid.addWidget(self.txt_prompt, 3, 1)

        main_layout.addWidget(design_box, 1)

        # Sample templates bar
        sample_row = QHBoxLayout()
        sample_row.setSpacing(8)
        self.btn_sample_astronomer = QPushButton(tr("btn_sample_astronomer"), self)
        self.btn_sample_educator = QPushButton(tr("btn_sample_educator"), self)
        self.btn_sample_fantasy = QPushButton(tr("btn_sample_fantasy"), self)
        style_button(self.btn_sample_astronomer, "secondary")
        style_button(self.btn_sample_educator, "secondary")
        style_button(self.btn_sample_fantasy, "secondary")
        sample_row.addWidget(self.btn_sample_astronomer)
        sample_row.addWidget(self.btn_sample_educator)
        sample_row.addWidget(self.btn_sample_fantasy)
        sample_row.addStretch(1)
        main_layout.addLayout(sample_row)

        # Action Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.btn_create = QPushButton(tr("btn_create_voice"), self)
        self.btn_create.setDefault(True)
        style_button(self.btn_create, "primary")

        self.btn_copy_id = QPushButton(tr("btn_copy_id_y"), self)
        self.btn_copy_id.setEnabled(False)
        style_button(self.btn_copy_id, "gold")

        self.btn_save_wav = QPushButton(tr("btn_save_preview_wav"), self)
        self.btn_save_wav.setEnabled(False)
        style_button(self.btn_save_wav, "secondary")

        btn_row.addWidget(self.btn_create)
        btn_row.addWidget(self.btn_copy_id)
        btn_row.addWidget(self.btn_save_wav)
        btn_row.addStretch(1)
        main_layout.addLayout(btn_row)

        # Studio Audio Player & Transport Deck
        self.player_bar = AudioTransportBar(
            self,
            get_audio_bytes_cb=lambda: self.last_sample_bytes,
            play_label_key="btn_play_preview",
            pause_label_key="btn_pause_preview",
            resume_label_key="btn_resume_preview",
        )
        self.btn_play_preview = self.player_bar.btn_play
        self.btn_stop = self.player_bar.btn_stop
        main_layout.addWidget(self.player_bar)

        # Status & ID Output
        self.lbl_id = QLabel(tr("lbl_voice_id_none"), self)
        style_label(self.lbl_id, "mono")
        apply_accessible(self.lbl_id, name="Assigned Voice ID")

        self.lbl_status = QLabel(tr("status_ready"), self)
        style_label(self.lbl_status, "status")
        apply_accessible(self.lbl_status, name="Status")

        main_layout.addWidget(self.lbl_id)
        main_layout.addWidget(self.lbl_status)

        # Connections
        self.btn_sample_astronomer.clicked.connect(lambda *_: self.load_sample(0))
        self.btn_sample_educator.clicked.connect(lambda *_: self.load_sample(1))
        self.btn_sample_fantasy.clicked.connect(lambda *_: self.load_sample(2))
        self.btn_create.clicked.connect(self.on_create_voice)
        self.btn_copy_id.clicked.connect(self.on_copy_id)
        self.btn_save_wav.clicked.connect(self.on_save_wav)

    def load_sample(self, idx: int):
        s = SAMPLE_DESIGN_PROMPTS[idx]
        self.txt_name.setText(s["name"])
        g_idx = self.combo_gender.findText(s["gender"])
        if g_idx >= 0:
            self.combo_gender.setCurrentIndex(g_idx)
        self.txt_lang.setText(s["lang"])
        self.txt_prompt.setPlainText(s["prompt"])
        announcer.announce(tr("announce_loaded_sample", name=s["name"]))

    def on_create_voice(self, *args):
        name = self.txt_name.text().strip()
        prompt = self.txt_prompt.toPlainText().strip()
        gender = self.combo_gender.currentText().strip()
        lang = self.txt_lang.text().strip()

        if not name:
            announcer.announce(tr("announce_enter_voice_name"))
            self.txt_name.setFocus()
            return
        if not prompt:
            announcer.announce(tr("announce_enter_persona_prompt"))
            self.txt_prompt.setFocus()
            return

        self.btn_create.setEnabled(False)
        self.lbl_status.setText(tr("announce_designing_voice", name=name))

        def _worker():
            try:
                voice_id, sample_bytes, _ = tts_engine.design_voice(
                    display_name=name,
                    prompt_description=prompt,
                    gender=gender,
                    language_code=lang,
                )
                self.last_voice_id = voice_id
                self.last_sample_bytes = sample_bytes

                def _ui_update():
                    self.btn_create.setEnabled(True)
                    self.player_bar.set_audio_ready(bool(sample_bytes), sample_bytes)
                    self.btn_copy_id.setEnabled(bool(voice_id))
                    self.btn_save_wav.setEnabled(bool(sample_bytes))
                    self.lbl_id.setText(tr("lbl_voice_id_assigned", voice_id=voice_id))
                    self.lbl_status.setText(tr("status_design_success"))
                    if sample_bytes and config.get("autoplay", True):
                        audio_player.play_wav_bytes(sample_bytes)

                call_after(_ui_update)
            except Exception as e:
                def _error_update():
                    self.btn_create.setEnabled(True)
                    self.lbl_status.setText(tr("status_error", error=e))

                call_after(_error_update)

        threading.Thread(target=_worker, daemon=True).start()

    def on_play_preview(self, *args):
        self.player_bar.on_play_pause()

    def on_copy_id(self, *args):
        if self.last_voice_id:
            cb = QApplication.clipboard()
            if cb is not None:
                cb.setText(self.last_voice_id)
                announcer.announce(tr("announce_copied_voice_id", voice_id=self.last_voice_id))

    def on_save_wav(self, *args):
        if not self.last_sample_bytes:
            return
        default_name = f"preview_{self.txt_name.text().strip().lower().replace(' ', '_')}.wav"
        dest, _ = QFileDialog.getSaveFileName(
            self,
            tr("menu_save_audio_help"),
            str(config.output_dir / default_name),
            "WAV Audio (*.wav)",
        )
        if dest:
            with open(dest, "wb") as f:
                f.write(self.last_sample_bytes)
            announcer.announce(tr("announce_preview_saved", path=dest))
            self.lbl_status.setText(tr("status_saved_path", path=dest))
