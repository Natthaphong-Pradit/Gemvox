import threading
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from gemvox.ui.accessible_text import AccessibleTextArea
from gemvox.config import config
from gemvox.i18n import tr
from gemvox.accessibility import announcer
from gemvox.core.voice_catalog import (
    SUPPORTED_MODELS,
    get_all_voices,
    find_voice,
)
from gemvox.core.tts_engine import tts_engine
from gemvox.core.audio_player import audio_player
from gemvox.ui.dialogs import InlineTagDialog, StylePresetDialog, CreateCustomStyleDialog
from gemvox.ui.player_bar import AudioTransportBar
from gemvox.ui.theme import (
    apply_accessible,
    call_after,
    clean_mnemonic,
    get_qfont,
    style_button,
    style_label,
)


class SingleSpeakerPanel(QWidget):
    """Panel for single-speaker TTS generation with full style, vocal tag control, and Universal Design layout."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_audio_bytes = None
        self.last_saved_path = None
        self._voices_cache = []
        self.setAccessibleName(clean_mnemonic(tr("tab_single")))
        self._init_ui()
        config.add_voices_listener(self._on_voices_changed)

    def _on_voices_changed(self):
        call_after(self.refresh_voices)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        # 1. Text Input Section
        text_label = QLabel(tr("ss_text_label"), self)
        style_label(text_label, "section")
        main_layout.addWidget(text_label)

        self.text_ctrl = AccessibleTextArea(tr("ss_default_text"), self)
        self.text_ctrl.setTabChangesFocus(True)
        self.text_ctrl.setFont(get_qfont(11))
        self.text_ctrl.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text_ctrl.customContextMenuRequested.connect(self.on_text_context_menu)
        apply_accessible(
            self.text_ctrl,
            name=tr("ss_text_label"),
            description="Enter text to synthesize into speech",
            label=text_label,
        )
        main_layout.addWidget(self.text_ctrl, 1)

        # Vocal Tag Insertion & Text Tools bar
        tag_row = QHBoxLayout()
        tag_row.setSpacing(8)
        self.btn_insert_tag = QPushButton(tr("btn_insert_tag_i"), self)
        self.btn_clear = QPushButton(tr("btn_clear_text"), self)
        self.btn_stats = QPushButton(tr("btn_stats"), self)
        style_button(self.btn_insert_tag, "secondary")
        style_button(self.btn_clear, "secondary")
        style_button(self.btn_stats, "secondary")
        tag_row.addWidget(self.btn_insert_tag)
        tag_row.addWidget(self.btn_clear)
        tag_row.addWidget(self.btn_stats)
        tag_row.addStretch(1)
        main_layout.addLayout(tag_row)

        # 2. Options Card: Model, Voice, Style
        opt_box = QGroupBox(clean_mnemonic(tr("ss_box_params")), self)
        opt_box.setAccessibleName(clean_mnemonic(tr("ss_box_params")))
        grid = QGridLayout(opt_box)
        grid.setContentsMargins(12, 14, 12, 12)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)

        # Model row
        lbl_model = QLabel(tr("lbl_model"), opt_box)
        self.combo_model = QComboBox(opt_box)
        self.combo_model.addItems([m["name"] for m in SUPPORTED_MODELS])
        def_m = config.get("default_model", "gemini-3.8-flash-tts")
        sel_m = 0
        for i, m in enumerate(SUPPORTED_MODELS):
            if m["id"] == def_m:
                sel_m = i
                break
        self.combo_model.setCurrentIndex(sel_m)
        apply_accessible(self.combo_model, name=tr("lbl_model"), label=lbl_model)
        grid.addWidget(lbl_model, 0, 0)
        grid.addWidget(self.combo_model, 0, 1)

        # Voice row
        lbl_voice = QLabel(tr("lbl_voice"), opt_box)
        self.combo_voice = QComboBox(opt_box)
        apply_accessible(self.combo_voice, name=tr("lbl_voice"), label=lbl_voice)
        self.refresh_voices()

        self.btn_audition = QPushButton(tr("btn_audition_u"), opt_box)
        style_button(self.btn_audition, "gold")
        grid.addWidget(lbl_voice, 1, 0)
        grid.addWidget(self.combo_voice, 1, 1)
        grid.addWidget(self.btn_audition, 1, 2)

        # Style row
        lbl_style = QLabel(tr("lbl_style"), opt_box)
        self.txt_style = QLineEdit(config.get("default_style", "cheerful and friendly"), opt_box)
        apply_accessible(self.txt_style, name=tr("lbl_style"), label=lbl_style)

        style_btn_row = QHBoxLayout()
        style_btn_row.setSpacing(6)
        self.btn_browse_style = QPushButton(tr("btn_browse_styles"), opt_box)
        self.btn_create_style = QPushButton(tr("btn_create_style"), opt_box)
        style_button(self.btn_browse_style, "secondary")
        style_button(self.btn_create_style, "secondary")
        style_btn_row.addWidget(self.btn_browse_style)
        style_btn_row.addWidget(self.btn_create_style)

        grid.addWidget(lbl_style, 2, 0)
        grid.addWidget(self.txt_style, 2, 1)
        grid.addLayout(style_btn_row, 2, 2)

        main_layout.addWidget(opt_box)

        # 3. Generation & Export Bar
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.btn_generate = QPushButton(tr("btn_generate_speech"), self)
        self.btn_generate.setDefault(True)
        style_button(self.btn_generate, "primary")

        self.btn_save = QPushButton(tr("btn_save_audio"), self)
        self.btn_save.setEnabled(False)
        style_button(self.btn_save, "secondary")

        btn_row.addWidget(self.btn_generate)
        btn_row.addWidget(self.btn_save)
        btn_row.addStretch(1)
        main_layout.addLayout(btn_row)

        # 4. Studio Audio Player & Transport Deck
        self.player_bar = AudioTransportBar(
            self,
            get_audio_bytes_cb=lambda: self.last_audio_bytes,
        )
        self.btn_play = self.player_bar.btn_play
        self.btn_stop = self.player_bar.btn_stop
        main_layout.addWidget(self.player_bar)

        # 5. Accessible Status Readout Console
        self.lbl_status = QLabel(tr("status_ready"), self)
        style_label(self.lbl_status, "status")
        apply_accessible(self.lbl_status, name="Status")
        main_layout.addWidget(self.lbl_status)

        # Connections
        self.btn_insert_tag.clicked.connect(self.on_insert_tag)
        self.btn_clear.clicked.connect(self.on_clear)
        self.btn_stats.clicked.connect(self.on_announce_stats)
        self.btn_browse_style.clicked.connect(self.on_browse_style)
        self.btn_create_style.clicked.connect(self.on_create_custom_style)
        self.btn_audition.clicked.connect(self.on_audition_voice)
        self.btn_generate.clicked.connect(self.on_generate)
        self.btn_save.clicked.connect(self.on_save)

    def refresh_voices(self, select_voice_id: str = None):
        """Populate the voice combo box with all prebuilt and custom voices."""
        if select_voice_id is None and self.combo_voice.count() > 0:
            select_voice_id = self.get_selected_voice_id()

        voices = get_all_voices()
        self._voices_cache = voices
        choices = []
        for v in voices:
            if v.is_custom:
                choices.append(f"{v.display_name} ({v.id}) - {v.tone}")
            else:
                choices.append(f"{v.id} - {v.tone} ({v.gender})")
        self.combo_voice.clear()
        self.combo_voice.addItems(choices)

        target_voice = select_voice_id or config.get("default_voice", "Kore")
        sel_idx = 0
        for i, v in enumerate(voices):
            if v.id.lower() == target_voice.lower():
                sel_idx = i
                break
        if choices:
            self.combo_voice.setCurrentIndex(sel_idx)

    def select_voice_by_id(self, voice_id: str, display_name: str = None, description: str = ""):
        """Select a voice by ID in the combo box, adding it to custom voices if it is from the online library."""
        found = find_voice(voice_id)
        if not found:
            config.add_custom_voice(
                voice_id=voice_id,
                display_name=display_name or voice_id,
                voice_type="Extended Library",
                description=description,
            )
        self.refresh_voices(select_voice_id=voice_id)

    def get_selected_voice_id(self) -> str:
        voices = self._voices_cache or get_all_voices()
        sel = self.combo_voice.currentIndex()
        if 0 <= sel < len(voices):
            return voices[sel].id
        return "Kore"

    def get_selected_model_id(self) -> str:
        sel = self.combo_model.currentIndex()
        if 0 <= sel < len(SUPPORTED_MODELS):
            return SUPPORTED_MODELS[sel]["id"]
        return "gemini-3.8-flash-tts"

    def on_announce_stats(self, *args):
        stats = tts_engine.calculate_text_stats(self.text_ctrl.toPlainText())
        self.lbl_status.setText(tr("status_text_stats", **stats))
        announcer.announce(tr("announce_text_stats", **stats))

    def on_text_context_menu(self, pos):
        """Standard accessible Windows context menu for text editing."""
        menu = QMenu(self)

        act_undo = menu.addAction(clean_mnemonic(tr("menu_undo")))
        act_redo = menu.addAction(clean_mnemonic(tr("menu_redo")))
        menu.addSeparator()
        act_cut = menu.addAction(clean_mnemonic(tr("menu_cut")))
        act_copy = menu.addAction(clean_mnemonic(tr("menu_copy")))
        act_paste = menu.addAction(clean_mnemonic(tr("menu_paste")))
        act_del = menu.addAction(clean_mnemonic(tr("menu_delete")))
        menu.addSeparator()
        act_all = menu.addAction(clean_mnemonic(tr("menu_select_all")))
        menu.addSeparator()
        act_tag = menu.addAction(clean_mnemonic(tr("btn_insert_tag_i")))

        act_undo.setEnabled(self.text_ctrl.canUndo())
        act_redo.setEnabled(self.text_ctrl.canRedo())
        act_cut.setEnabled(self.text_ctrl.hasSelection())
        act_copy.setEnabled(self.text_ctrl.hasSelection())
        act_paste.setEnabled(self.text_ctrl.canPaste())

        act_undo.triggered.connect(self.text_ctrl.undo)
        act_redo.triggered.connect(self.text_ctrl.redo)
        act_cut.triggered.connect(self.text_ctrl.cut)
        act_copy.triggered.connect(self.text_ctrl.copy)
        act_paste.triggered.connect(self.text_ctrl.paste)
        act_del.triggered.connect(self.text_ctrl.delete_selection_or_char)
        act_all.triggered.connect(self.text_ctrl.selectAll)
        act_tag.triggered.connect(self.on_insert_tag)

        menu.exec(self.text_ctrl.mapToGlobal(pos))

    def on_insert_tag(self, *args):
        dlg = InlineTagDialog(self)
        if dlg.exec() and dlg.selected_tag:
            tag = dlg.selected_tag
            self.text_ctrl.setFocus()
            self.text_ctrl.insert_text_at_selection(tag)
            announcer.announce(tr("announce_inserted_tag", tag=tag))
        else:
            self.text_ctrl.setFocus()

    def on_clear(self, *args):
        self.text_ctrl.clear()
        self.text_ctrl.setFocus()
        announcer.announce(tr("msg_text_cleared"))

    def on_browse_style(self, *args):
        dlg = StylePresetDialog(self)
        if dlg.exec() and dlg.selected_style:
            self.txt_style.setText(dlg.selected_style)
            self.txt_style.setFocus()
            announcer.announce(tr("announce_applied_style", style=dlg.selected_style))

    def on_create_custom_style(self, *args):
        current_style = self.txt_style.text().strip()
        dlg = CreateCustomStyleDialog(self, initial_style=current_style)
        if dlg.exec() and dlg.created_style:
            self.txt_style.setText(dlg.created_style)
            self.txt_style.setFocus()
            self.lbl_status.setText(tr("status_saved_custom_style", name=dlg.created_name, style=dlg.created_style))
            announcer.announce(tr("announce_saved_custom_style", name=dlg.created_name))

    def on_audition_voice(self, *args):
        voice_id = self.get_selected_voice_id()
        model_id = self.get_selected_model_id()
        audition_phrase = f"Hello, I am {voice_id}. This is a preview of my voice."

        self.lbl_status.setText(tr("status_auditioning", voice=voice_id))

        def _worker():
            try:
                wav_bytes, _, _ = tts_engine.synthesize_single_speaker(
                    text=audition_phrase,
                    voice=voice_id,
                    style="natural and clear",
                    model=model_id,
                )
                audio_player.play_wav_bytes(wav_bytes)
                call_after(self.lbl_status.setText, tr("status_audition_done", voice=voice_id))
            except Exception as e:
                call_after(self.lbl_status.setText, tr("status_error", error=e))

        threading.Thread(target=_worker, daemon=True).start()

    def on_generate(self, *args):
        text = self.text_ctrl.toPlainText().strip()
        if not text:
            announcer.announce(tr("msg_enter_text"))
            self.text_ctrl.setFocus()
            return

        voice_id = self.get_selected_voice_id()
        model_id = self.get_selected_model_id()
        style = self.txt_style.text().strip()

        self.btn_generate.setEnabled(False)
        self.lbl_status.setText(tr("status_generating_single", voice=voice_id))

        def _worker():
            try:
                wav_bytes, out_path, duration = tts_engine.synthesize_single_speaker(
                    text=text,
                    voice=voice_id,
                    style=style,
                    model=model_id,
                )
                self.last_audio_bytes = wav_bytes
                self.last_saved_path = out_path

                def _ui_update():
                    self.btn_generate.setEnabled(True)
                    self.btn_save.setEnabled(True)
                    self.player_bar.set_audio_ready(True, wav_bytes)
                    self.lbl_status.setText(tr("status_single_ready", duration=duration, path=out_path))
                    if config.get("autoplay", True):
                        audio_player.play_wav_bytes(wav_bytes)

                call_after(_ui_update)
            except Exception as e:
                def _error_update():
                    self.btn_generate.setEnabled(True)
                    self.lbl_status.setText(tr("status_error", error=e))

                call_after(_error_update)

        threading.Thread(target=_worker, daemon=True).start()

    def on_play_stop(self, *args):
        self.player_bar.on_play_pause()

    def on_save(self, *args):
        if not self.last_audio_bytes:
            announcer.announce(tr("msg_no_audio_save"))
            return

        default_name = f"gemvox_speech_{self.get_selected_voice_id().lower()}.wav"
        dest, _ = QFileDialog.getSaveFileName(
            self,
            tr("menu_save_audio_help"),
            str(config.output_dir / default_name),
            "WAV Audio (*.wav)",
        )
        if dest:
            with open(dest, "wb") as f:
                f.write(self.last_audio_bytes)
            announcer.announce(tr("announce_audio_saved", path=dest))
            self.lbl_status.setText(tr("status_saved_path", path=dest))
