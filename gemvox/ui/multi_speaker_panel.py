import threading
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
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
)
from gemvox.core.tts_engine import tts_engine
from gemvox.core.audio_player import audio_player
from gemvox.ui.dialogs import InlineTagDialog
from gemvox.ui.player_bar import AudioTransportBar
from gemvox.ui.theme import (
    apply_accessible,
    call_after,
    clean_mnemonic,
    get_qfont,
    style_button,
    style_label,
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


class MultiSpeakerPanel(QWidget):
    """Panel for multi-speaker conversational dialogue generation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_audio_bytes = None
        self.last_saved_path = None
        self.speaker_combos: dict[str, QComboBox] = {}
        self._voices_cache = []
        self.setAccessibleName(clean_mnemonic(tr("tab_multi")))
        self._init_ui()
        config.add_voices_listener(self._on_voices_changed)

    def _on_voices_changed(self):
        call_after(self.update_speaker_controls)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        # 1. Script Header and Editor
        script_header = QLabel(tr("ms_script_label"), self)
        style_label(script_header, "section")
        main_layout.addWidget(script_header)

        self.text_script = AccessibleTextArea(DEFAULT_PODCAST_SCRIPT, self)
        self.text_script.setTabChangesFocus(True)
        self.text_script.setFont(get_qfont(11))
        self.text_script.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text_script.customContextMenuRequested.connect(self.on_text_context_menu)
        apply_accessible(
            self.text_script,
            name=tr("ms_script_label"),
            description="Multi-speaker dialogue script editor",
            label=script_header,
        )
        main_layout.addWidget(self.text_script, 1)

        # Template and Insertion buttons
        tmpl_row = QHBoxLayout()
        tmpl_row.setSpacing(6)
        self.btn_insert_tag = QPushButton(tr("btn_insert_tag_t"), self)
        self.btn_load_podcast = QPushButton(tr("btn_load_podcast"), self)
        self.btn_load_interview = QPushButton(tr("btn_load_interview"), self)
        self.btn_detect_speakers = QPushButton(tr("btn_update_speakers"), self)
        self.btn_stats = QPushButton(tr("btn_stats"), self)

        style_button(self.btn_insert_tag, "secondary")
        style_button(self.btn_load_podcast, "secondary")
        style_button(self.btn_load_interview, "secondary")
        style_button(self.btn_detect_speakers, "gold")
        style_button(self.btn_stats, "secondary")

        tmpl_row.addWidget(self.btn_insert_tag)
        tmpl_row.addWidget(self.btn_load_podcast)
        tmpl_row.addWidget(self.btn_load_interview)
        tmpl_row.addWidget(self.btn_detect_speakers)
        tmpl_row.addWidget(self.btn_stats)
        tmpl_row.addStretch(1)
        main_layout.addLayout(tmpl_row)

        # 2. Speaker Voice Mapping Section
        self.mapping_box = QGroupBox(clean_mnemonic(tr("ms_box_mapping")), self)
        self.mapping_box.setAccessibleName(clean_mnemonic(tr("ms_box_mapping")))
        self.speakers_grid = QGridLayout(self.mapping_box)
        self.speakers_grid.setContentsMargins(12, 14, 12, 12)
        self.speakers_grid.setHorizontalSpacing(12)
        self.speakers_grid.setVerticalSpacing(8)
        self.speakers_grid.setColumnStretch(1, 1)
        main_layout.addWidget(self.mapping_box)

        # 3. Model & Action Row
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(10)

        lbl_model = QLabel(tr("lbl_model"), self)
        self.combo_model = QComboBox(self)
        self.combo_model.addItems([m["name"] for m in SUPPORTED_MODELS])
        def_m = config.get("default_model", "gemini-2.5-flash-preview-tts")
        sel_m = 0
        for i, m in enumerate(SUPPORTED_MODELS):
            if m["id"] == def_m:
                sel_m = i
                break
        self.combo_model.setCurrentIndex(sel_m)
        apply_accessible(self.combo_model, name=tr("lbl_model"), label=lbl_model)

        self.btn_generate = QPushButton(tr("btn_generate_dialogue"), self)
        self.btn_generate.setDefault(True)
        style_button(self.btn_generate, "primary")

        self.btn_save = QPushButton(tr("btn_save_audio"), self)
        self.btn_save.setEnabled(False)
        style_button(self.btn_save, "secondary")

        ctrl_row.addWidget(lbl_model)
        ctrl_row.addWidget(self.combo_model)
        ctrl_row.addSpacing(6)
        ctrl_row.addWidget(self.btn_generate)
        ctrl_row.addWidget(self.btn_save)
        ctrl_row.addStretch(1)
        main_layout.addLayout(ctrl_row)

        # 4. Studio Audio Player & Transport Deck
        self.player_bar = AudioTransportBar(
            self,
            get_audio_bytes_cb=lambda: self.last_audio_bytes,
        )
        self.btn_play = self.player_bar.btn_play
        self.btn_stop = self.player_bar.btn_stop
        main_layout.addWidget(self.player_bar)

        # 5. Status
        self.lbl_status = QLabel(tr("status_ready"), self)
        style_label(self.lbl_status, "status")
        apply_accessible(self.lbl_status, name="Status")
        main_layout.addWidget(self.lbl_status)

        # Connections
        self.btn_insert_tag.clicked.connect(self.on_insert_tag)
        self.btn_load_podcast.clicked.connect(self.on_load_podcast)
        self.btn_load_interview.clicked.connect(self.on_load_interview)
        self.btn_detect_speakers.clicked.connect(self.on_detect_speakers)
        self.btn_stats.clicked.connect(self.on_announce_stats)
        self.btn_generate.clicked.connect(self.on_generate)
        self.btn_save.clicked.connect(self.on_save)

        # Initial detection
        self.update_speaker_controls()

    def on_announce_stats(self, *args):
        stats = tts_engine.calculate_text_stats(self.text_script.toPlainText())
        self.lbl_status.setText(tr("status_text_stats", **stats))
        announcer.announce(tr("announce_text_stats", **stats))

    def on_load_podcast(self, *args):
        self.text_script.setPlainText(DEFAULT_PODCAST_SCRIPT)
        self.update_speaker_controls()
        announcer.announce(tr("announce_loaded_podcast"))

    def on_load_interview(self, *args):
        self.text_script.setPlainText(DEFAULT_INTERVIEW_SCRIPT)
        self.update_speaker_controls()
        announcer.announce(tr("announce_loaded_interview"))

    def on_detect_speakers(self, *args):
        count = self.update_speaker_controls()
        announcer.announce(tr("announce_detected_speakers", count=count))

    def _get_combo_voice_id(self, combo: QComboBox) -> str:
        sel = combo.currentIndex()
        if 0 <= sel < len(self._voices_cache):
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

        script = self.text_script.toPlainText()
        _, speakers = tts_engine.parse_dialogue_script(script)
        if not speakers:
            speakers = ["Joe", "Jane"]

        voices = get_all_voices()
        self._voices_cache = voices
        voice_choices = [
            f"{v.display_name} ({v.id})" if v.is_custom else f"{v.id} - {v.tone} ({v.gender})"
            for v in voices
        ]

        # Clear existing grid items cleanly
        while self.speakers_grid.count():
            item = self.speakers_grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self.speaker_combos.clear()

        default_pairings = ["Puck", "Kore", "Zephyr", "Charon", "Fenrir", "Leda"]

        for idx, spk in enumerate(speakers):
            lbl = QLabel(tr("lbl_voice_for", speaker=spk), self.mapping_box)
            combo = QComboBox(self.mapping_box)
            combo.addItems(voice_choices)

            def_voice = previous_selections.get(spk) or default_pairings[idx % len(default_pairings)]
            sel_idx = 0
            for vi, v in enumerate(voices):
                if v.id.lower() == def_voice.lower():
                    sel_idx = vi
                    break
            if voice_choices:
                combo.setCurrentIndex(sel_idx)

            apply_accessible(combo, name=tr("lbl_voice_for", speaker=spk), label=lbl)
            self.speakers_grid.addWidget(lbl, idx, 0)
            self.speakers_grid.addWidget(combo, idx, 1)
            self.speaker_combos[spk] = combo

        return len(speakers)

    def on_generate(self, *args):
        script = self.text_script.toPlainText().strip()
        if not script:
            announcer.announce(tr("msg_enter_script"))
            self.text_script.setFocus()
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

        sel_m = self.combo_model.currentIndex()
        model_id = SUPPORTED_MODELS[sel_m]["id"] if 0 <= sel_m < len(SUPPORTED_MODELS) else "gemini-3.8-flash-tts"

        self.btn_generate.setEnabled(False)
        self.lbl_status.setText(tr("status_generating_multi", count=len(speakers)))

        def _worker():
            try:
                wav_bytes, out_path, duration = tts_engine.synthesize_multi_speaker(
                    turns=turns,
                    speaker_voice_map=speaker_voice_map,
                    model=model_id,
                )
                self.last_audio_bytes = wav_bytes
                self.last_saved_path = out_path

                def _ui_update():
                    self.btn_generate.setEnabled(True)
                    self.btn_save.setEnabled(True)
                    self.player_bar.set_audio_ready(True, wav_bytes)
                    self.lbl_status.setText(tr("status_multi_ready", duration=duration, path=out_path))
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

        dest, _ = QFileDialog.getSaveFileName(
            self,
            tr("menu_save_audio_help"),
            str(config.output_dir / "gemvox_dialogue.wav"),
            "WAV Audio (*.wav)",
        )
        if dest:
            with open(dest, "wb") as f:
                f.write(self.last_audio_bytes)
            announcer.announce(tr("announce_audio_saved", path=dest))
            self.lbl_status.setText(tr("status_saved_path", path=dest))

    def on_text_context_menu(self, pos):
        """Standard accessible Windows context menu for dialogue script editing."""
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
        act_tag = menu.addAction(clean_mnemonic(tr("btn_insert_tag_t")))

        act_undo.setEnabled(self.text_script.canUndo())
        act_redo.setEnabled(self.text_script.canRedo())
        act_cut.setEnabled(self.text_script.hasSelection())
        act_copy.setEnabled(self.text_script.hasSelection())
        act_paste.setEnabled(self.text_script.canPaste())

        act_undo.triggered.connect(self.text_script.undo)
        act_redo.triggered.connect(self.text_script.redo)
        act_cut.triggered.connect(self.text_script.cut)
        act_copy.triggered.connect(self.text_script.copy)
        act_paste.triggered.connect(self.text_script.paste)
        act_del.triggered.connect(self.text_script.delete_selection_or_char)
        act_all.triggered.connect(self.text_script.selectAll)
        act_tag.triggered.connect(self.on_insert_tag)

        menu.exec(self.text_script.mapToGlobal(pos))

    def on_insert_tag(self, *args):
        dlg = InlineTagDialog(self)
        if dlg.exec() and dlg.selected_tag:
            tag = dlg.selected_tag
            self.text_script.setFocus()
            self.text_script.insert_text_at_selection(tag)
            announcer.announce(tr("announce_inserted_tag", tag=tag))
        else:
            self.text_script.setFocus()
