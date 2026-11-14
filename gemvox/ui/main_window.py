from pathlib import Path
import threading
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from gemvox import VERSION
from gemvox.config import config
from gemvox.i18n import tr
from gemvox.accessibility import announcer
from gemvox.core.audio_player import audio_player
from gemvox.core.updater import check_for_updates
from gemvox.ui.single_speaker_panel import SingleSpeakerPanel
from gemvox.ui.multi_speaker_panel import MultiSpeakerPanel
from gemvox.ui.voice_design_panel import VoiceDesignPanel
from gemvox.ui.voice_replication_panel import VoiceReplicationPanel
from gemvox.ui.voice_library_panel import VoiceLibraryPanel
from gemvox.ui.settings_panel import SettingsPanel
from gemvox.ui.accessible_text import AccessibleTextArea
from gemvox.ui.dialogs import (
    HelpDialog,
    WelcomeTourDialog,
    GenerationHistoryDialog,
    UpdateDialog,
    open_output_folder,
)
from gemvox.ui.theme import (
    StudioHeaderBanner,
    apply_accessible,
    call_after,
    clean_mnemonic,
    create_app_icon,
    style_label,
)


class MainWindow(QMainWindow):
    """
    Main window of Gemvox v1.2.0 (Universal Design PySide6 Edition).
    Combines full screen reader accessibility (UIA/MSAA metadata, direct screen reader
    announcer, wx-compatible tab-bar & Alt+Mnemonic keyboard navigation) with a
    modern Obsidian & Royal Gold studio interface for sighted creators.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app_title", version=VERSION))
        self.setAccessibleName(tr("app_title", version=VERSION))
        self.resize(1080, 780)
        self.setMinimumSize(920, 680)
        try:
            self.setWindowIcon(create_app_icon())
        except Exception:
            pass

        self.tab_names = [
            tr("tab_single"),
            tr("tab_multi"),
            tr("tab_design"),
            tr("tab_replication"),
            tr("tab_library"),
            tr("tab_settings"),
        ]
        self._alive = True
        self._startup_update_checked = False

        self._init_menu()
        self._init_ui()

        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)

        # Initial voice announcement & focus on tab bar
        self.tabs.tabBar().setFocus()
        announcer.announce(tr("app_opened_announce", version=VERSION))

        if config.is_first_run:
            call_after(self._show_first_run_welcome_tour)
        elif config.get("auto_check_updates", True):
            call_after(self._start_startup_update_check)

    def closeEvent(self, event):
        self._alive = False
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        super().closeEvent(event)

    def _show_first_run_welcome_tour(self):
        if not self._alive:
            return
        dlg = WelcomeTourDialog(self)
        res = dlg.exec()
        if res == WelcomeTourDialog.ID_GO_SETTINGS:
            self.switch_tab(5)
            self.focus_tab_primary_control(5)
        if config.get("auto_check_updates", True) and not self._startup_update_checked:
            self._start_startup_update_check()

    def _start_startup_update_check(self):
        """Silently check GitHub for updates on startup; show UpdateDialog only if a newer version exists."""
        if self._startup_update_checked:
            return
        self._startup_update_checked = True

        def _worker():
            try:
                info = check_for_updates()
            except Exception:
                return
            if self._alive:
                call_after(self._on_startup_update_check_done, info)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_startup_update_check_done(self, info):
        if not self._alive:
            return
        if not info or info.error or not info.is_newer:
            return
        dlg = UpdateDialog(self, initial_info=info)
        dlg.exec()

    def _init_menu(self):
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu(tr("menu_file"))
        m_open_script = file_menu.addAction(tr("menu_open_script"))
        m_save_script = file_menu.addAction(tr("menu_save_script"))
        file_menu.addSeparator()
        m_save = file_menu.addAction(tr("menu_save_audio"))
        m_history = file_menu.addAction(tr("menu_history"))
        m_open_out = file_menu.addAction(tr("menu_open_output_dir"))
        file_menu.addSeparator()
        m_exit = file_menu.addAction(tr("menu_exit"))

        # Edit menu
        edit_menu = menu_bar.addMenu(tr("menu_edit"))
        m_undo = edit_menu.addAction(tr("menu_undo"))
        m_redo = edit_menu.addAction(tr("menu_redo"))
        edit_menu.addSeparator()
        m_cut = edit_menu.addAction(tr("menu_cut"))
        m_copy = edit_menu.addAction(tr("menu_copy"))
        m_paste = edit_menu.addAction(tr("menu_paste"))
        m_delete = edit_menu.addAction(tr("menu_delete"))
        edit_menu.addSeparator()
        m_select_all = edit_menu.addAction(tr("menu_select_all"))
        edit_menu.addSeparator()
        m_clear_field = edit_menu.addAction(tr("menu_clear_field"))

        # Audio menu
        audio_menu = menu_bar.addMenu(tr("menu_audio"))
        m_play = audio_menu.addAction(tr("menu_play_stop"))
        m_stop = audio_menu.addAction(tr("menu_stop_audio"))
        audio_menu.addSeparator()
        m_rew = audio_menu.addAction(tr("menu_rewind_5s"))
        m_ff = audio_menu.addAction(tr("menu_forward_5s"))
        audio_menu.addSeparator()
        m_vol_down = audio_menu.addAction(tr("menu_vol_down"))
        m_vol_up = audio_menu.addAction(tr("menu_vol_up"))
        m_speed = audio_menu.addAction(tr("menu_cycle_speed"))
        m_loop = audio_menu.addAction(tr("menu_toggle_loop"))
        audio_menu.addSeparator()
        m_audio_history = audio_menu.addAction(tr("menu_audio_history"))

        # Tabs menu
        tabs_menu = menu_bar.addMenu(tr("menu_tabs"))
        m_tab1 = tabs_menu.addAction(tr("menu_tab1"))
        m_tab2 = tabs_menu.addAction(tr("menu_tab2"))
        m_tab3 = tabs_menu.addAction(tr("menu_tab3"))
        m_tab4 = tabs_menu.addAction(tr("menu_tab4"))
        m_tab5 = tabs_menu.addAction(tr("menu_tab5"))
        m_tab6 = tabs_menu.addAction(tr("menu_tab6"))
        tabs_menu.addSeparator()
        m_next_tab = tabs_menu.addAction(tr("menu_next_tab"))
        m_prev_tab = tabs_menu.addAction(tr("menu_prev_tab"))

        # Tools menu
        tools_menu = menu_bar.addMenu(tr("menu_tools"))
        m_tag = tools_menu.addAction(tr("menu_insert_tag"))
        m_style = tools_menu.addAction(tr("menu_browse_style"))
        m_create_style = tools_menu.addAction(tr("menu_create_style"))
        tools_menu.addSeparator()
        m_stats = tools_menu.addAction(tr("menu_text_stats"))
        tools_menu.addSeparator()
        m_tour = tools_menu.addAction(tr("menu_welcome_tour"))

        # Help menu
        help_menu = menu_bar.addMenu(tr("menu_help"))
        m_help = help_menu.addAction(tr("menu_help_guide"))
        m_update = help_menu.addAction(tr("menu_check_updates"))
        help_menu.addSeparator()
        m_about = help_menu.addAction(tr("menu_about"))

        # Connections
        m_open_script.triggered.connect(self.on_menu_open_script)
        m_save_script.triggered.connect(self.on_menu_save_script)
        m_save.triggered.connect(self.on_menu_save)
        m_history.triggered.connect(self.on_menu_history)
        m_open_out.triggered.connect(self.on_menu_open_output)
        m_exit.triggered.connect(self.close)

        m_undo.triggered.connect(self.on_edit_undo)
        m_redo.triggered.connect(self.on_edit_redo)
        m_cut.triggered.connect(self.on_edit_cut)
        m_copy.triggered.connect(self.on_edit_copy)
        m_paste.triggered.connect(self.on_edit_paste)
        m_delete.triggered.connect(self.on_edit_delete)
        m_select_all.triggered.connect(self.on_edit_select_all)
        m_clear_field.triggered.connect(self.on_edit_clear)

        m_play.triggered.connect(self.on_menu_play)
        m_stop.triggered.connect(lambda *_: audio_player.stop(announce=True))
        m_rew.triggered.connect(lambda *_: audio_player.skip(-5.0, announce=True))
        m_ff.triggered.connect(lambda *_: audio_player.skip(5.0, announce=True))
        m_vol_down.triggered.connect(lambda *_: audio_player.change_volume(-10, announce=True))
        m_vol_up.triggered.connect(lambda *_: audio_player.change_volume(10, announce=True))
        m_speed.triggered.connect(lambda *_: audio_player.cycle_speed(announce=True))
        m_loop.triggered.connect(lambda *_: audio_player.toggle_loop(announce=True))
        m_audio_history.triggered.connect(self.on_menu_history)

        m_tab1.triggered.connect(lambda *_: self.switch_tab(0))
        m_tab2.triggered.connect(lambda *_: self.switch_tab(1))
        m_tab3.triggered.connect(lambda *_: self.switch_tab(2))
        m_tab4.triggered.connect(lambda *_: self.switch_tab(3))
        m_tab5.triggered.connect(lambda *_: self.switch_tab(4))
        m_tab6.triggered.connect(lambda *_: self.switch_tab(5))
        m_next_tab.triggered.connect(lambda *_: self.cycle_tab(forward=True))
        m_prev_tab.triggered.connect(lambda *_: self.cycle_tab(forward=False))

        m_tag.triggered.connect(self.on_menu_tag)
        m_style.triggered.connect(self.on_menu_style)
        m_create_style.triggered.connect(self.on_menu_create_style)
        m_stats.triggered.connect(self.on_menu_text_stats)
        m_tour.triggered.connect(self._show_first_run_welcome_tour)

        m_help.triggered.connect(self.on_menu_help)
        m_update.triggered.connect(self.on_menu_check_updates)
        m_about.triggered.connect(self.on_menu_about)

    def _init_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Custom-painted Studio Header Banner (non-focusable)
        root_layout.addWidget(
            StudioHeaderBanner(
                title=tr("banner_title"),
                subtitle=tr("banner_subtitle"),
                badge_text=tr("banner_badge", version=VERSION),
            )
        )

        # Workspace Container
        ws_layout = QVBoxLayout()
        ws_layout.setContentsMargins(10, 10, 10, 8)
        ws_layout.setSpacing(0)

        self.tabs = QTabWidget(central)
        self.tabs.setDocumentMode(False)
        self.tabs.tabBar().setFocusPolicy(Qt.StrongFocus)
        apply_accessible(self.tabs, name="Studio Workspace Tabs")
        apply_accessible(self.tabs.tabBar(), name="Studio Workspace Tabs")

        # 6 Dedicated Accessible Tabs
        self.tab_single = SingleSpeakerPanel(self.tabs)
        self.tab_multi = MultiSpeakerPanel(self.tabs)
        self.tab_design = VoiceDesignPanel(self.tabs)
        self.tab_replication = VoiceReplicationPanel(self.tabs)
        self.tab_library = VoiceLibraryPanel(self.tabs)
        self.tab_settings = SettingsPanel(self.tabs)

        self.tabs.addTab(self.tab_single, clean_mnemonic(self.tab_names[0]))
        self.tabs.addTab(self.tab_multi, clean_mnemonic(self.tab_names[1]))
        self.tabs.addTab(self.tab_design, clean_mnemonic(self.tab_names[2]))
        self.tabs.addTab(self.tab_replication, clean_mnemonic(self.tab_names[3]))
        self.tabs.addTab(self.tab_library, clean_mnemonic(self.tab_names[4]))
        self.tabs.addTab(self.tab_settings, clean_mnemonic(self.tab_names[5]))

        ws_layout.addWidget(self.tabs, 1)
        root_layout.addLayout(ws_layout, 1)

        # 3-Segment Accessible Status Bar
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)
        self.lbl_status_main = QLabel(tr("status_ready_main"), status_bar)
        self.lbl_status_engine = QLabel(tr("status_engine"), status_bar)
        self.lbl_status_sr = QLabel(tr("status_sr_mode"), status_bar)
        style_label(self.lbl_status_main, "muted")
        style_label(self.lbl_status_engine, "muted")
        style_label(self.lbl_status_sr, "muted")

        status_bar.addWidget(self.lbl_status_main, 3)
        status_bar.addWidget(self.lbl_status_engine, 2)
        status_bar.addPermanentWidget(self.lbl_status_sr, 1)

        self.tabs.currentChanged.connect(self.on_tab_changed)

    def _set_status_text(self, text: str):
        self.lbl_status_main.setText(text)

    # ====================================================================
    # GLOBAL KEYBOARD & ACCESSIBILITY HOOK (Simulates wx.EVT_CHAR_HOOK)
    # ====================================================================
    def eventFilter(self, watched, event):
        if not self._alive:
            return False
        etype = event.type()
        if etype not in (QEvent.KeyPress, QEvent.ShortcutOverride):
            return False
        if not self.isActiveWindow():
            return False
        if not isinstance(event, QKeyEvent):
            return False

        if etype == QEvent.ShortcutOverride:
            if self._is_handled_shortcut(event):
                event.accept()
                return True
            return False

        if self._handle_key_press(event):
            return True
        return False

    def _is_handled_shortcut(self, event: QKeyEvent) -> bool:
        """Return True if this key combination should be intercepted by MainWindow."""
        mods = event.modifiers()
        key = event.key()
        ctrl = bool(mods & Qt.ControlModifier)
        alt = bool(mods & Qt.AltModifier)
        shift = bool(mods & Qt.ShiftModifier)

        focused = QApplication.focusWidget()
        if focused == self.tabs.tabBar():
            if not ctrl and not alt and key in (
                Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down,
                Qt.Key_Home, Qt.Key_End, Qt.Key_Tab, Qt.Key_Backtab,
            ):
                return True

        if (ctrl and not alt and not shift) or (alt and not ctrl and not shift):
            if Qt.Key_1 <= key <= Qt.Key_6:
                return True

        if ctrl and not alt and key in (Qt.Key_Tab, Qt.Key_Backtab, Qt.Key_PageDown, Qt.Key_PageUp):
            return True

        if ctrl and not alt and not shift and key in (Qt.Key_Return, Qt.Key_Enter):
            return True

        if alt and not ctrl and not shift and key in (Qt.Key_P, Qt.Key_Q):
            return True

        if not ctrl and not alt and not shift and key in (Qt.Key_F1, Qt.Key_F7, Qt.Key_F8, Qt.Key_F9, Qt.Key_F10):
            return True

        if ctrl and not alt and not shift and key in (Qt.Key_O, Qt.Key_S, Qt.Key_H, Qt.Key_I, Qt.Key_U, Qt.Key_L):
            return True

        if ctrl and shift and not alt and key in (Qt.Key_S, Qt.Key_O, Qt.Key_P):
            return True

        if alt and shift and not ctrl and key == Qt.Key_L:
            return True

        if alt and not ctrl and not shift and Qt.Key_A <= key <= Qt.Key_Z:
            ch = chr(key)
            if ch not in ("F", "E", "A", "T", "O", "H"):
                return self._can_handle_active_tab_mnemonic(ch)

        return False

    def _handle_key_press(self, event: QKeyEvent) -> bool:
        mods = event.modifiers()
        key = event.key()
        ctrl = bool(mods & Qt.ControlModifier)
        alt = bool(mods & Qt.AltModifier)
        shift = bool(mods & Qt.ShiftModifier)

        focused = QApplication.focusWidget()

        # 0. Tab Bar Navigation: keep focus locked on Tab Bar for Left/Right/Up/Down/Home/End,
        #    and enter the tab's inner workspace only on Tab.
        if focused == self.tabs.tabBar():
            if not ctrl and not alt and not shift:
                if key in (Qt.Key_Left, Qt.Key_Up):
                    self.cycle_tab(forward=False)
                    return True
                if key in (Qt.Key_Right, Qt.Key_Down):
                    self.cycle_tab(forward=True)
                    return True
                if key == Qt.Key_Home:
                    self.switch_tab(0)
                    return True
                if key == Qt.Key_End:
                    self.switch_tab(self.tabs.count() - 1)
                    return True
            if not ctrl and not alt and key in (Qt.Key_Tab, Qt.Key_Backtab):
                if shift or key == Qt.Key_Backtab:
                    self.focusPreviousChild()
                else:
                    self.focus_tab_primary_control(self.tabs.currentIndex(), immediate=True)
                return True

        # 1. Direct tab selection: Ctrl+1..6 or Alt+1..6
        if (ctrl and not alt and not shift) or (alt and not ctrl and not shift):
            if Qt.Key_1 <= key <= Qt.Key_6:
                self.switch_tab(key - Qt.Key_1)
                return True

        # 2. Next tab: Ctrl+Tab or Ctrl+PageDown
        if ctrl and not alt and not shift:
            if key in (Qt.Key_Tab, Qt.Key_PageDown):
                self.cycle_tab(forward=True)
                return True

        # 3. Previous tab: Ctrl+Shift+Tab or Ctrl+PageUp
        if (ctrl and shift and not alt and key in (Qt.Key_Tab, Qt.Key_Backtab)) or (
            ctrl and not alt and not shift and key == Qt.Key_PageUp
        ):
            self.cycle_tab(forward=False)
            return True

        # 4. Global Generate Speech: Ctrl+Enter
        if ctrl and not alt and not shift and key in (Qt.Key_Return, Qt.Key_Enter):
            self.on_global_generate()
            return True

        # 5. Global Audio Transport: Alt+P, Alt+Q, F7..F10
        if alt and not ctrl and not shift:
            if key == Qt.Key_P:
                self.on_menu_play()
                return True
            if key == Qt.Key_Q:
                audio_player.stop(announce=True)
                return True

        if not ctrl and not alt and not shift:
            if key == Qt.Key_F1:
                self.on_menu_help()
                return True
            if key == Qt.Key_F7:
                audio_player.skip(-5.0, announce=True)
                return True
            if key == Qt.Key_F8:
                audio_player.skip(5.0, announce=True)
                return True
            if key == Qt.Key_F9:
                audio_player.change_volume(-10, announce=True)
                return True
            if key == Qt.Key_F10:
                audio_player.change_volume(10, announce=True)
                return True

        if ctrl and not alt and not shift:
            if key == Qt.Key_O:
                self.on_menu_open_script()
                return True
            if key == Qt.Key_S:
                self.on_menu_save()
                return True
            if key == Qt.Key_H:
                self.on_menu_history()
                return True
            if key == Qt.Key_I:
                self.on_menu_text_stats()
                return True
            if key == Qt.Key_U:
                self.on_menu_check_updates()
                return True
            if key == Qt.Key_L:
                audio_player.toggle_loop(announce=True)
                return True

        if ctrl and shift and not alt:
            if key == Qt.Key_S:
                self.on_menu_save_script()
                return True
            if key == Qt.Key_O:
                self.on_menu_open_output()
                return True
            if key == Qt.Key_P:
                audio_player.cycle_speed(announce=True)
                return True

        if alt and shift and not ctrl:
            if key == Qt.Key_L:
                self.on_edit_clear()
                return True

        # 6. Active Tab Mnemonic Shortcuts (Alt+Key)
        if alt and not ctrl and not shift and Qt.Key_A <= key <= Qt.Key_Z:
            ch = chr(key)
            if ch not in ("F", "E", "A", "T", "O", "H"):
                if self._handle_active_tab_mnemonic(ch):
                    return True

        return False

    def _can_handle_active_tab_mnemonic(self, ch: str) -> bool:
        sel = self.tabs.currentIndex()
        mapping = {
            0: set("XILMVUYBCGS"),
            1: set("DILNKMGS"),
            2: set("NGLDCYS"),
            3: set("NRBCSWMVY"),
            4: set("SLGDXBVUYCR"),
            5: set("KCGDWMVLRBUS"),
        }
        return ch in mapping.get(sel, set())

    def _handle_active_tab_mnemonic(self, ch: str) -> bool:
        """Explicitly route Alt+<Key> mnemonics to the active tab's controls or actions."""
        sel = self.tabs.currentIndex()
        if sel == 0:
            p = self.tab_single
            if ch == "X":
                p.text_ctrl.setFocus()
                return True
            if ch == "I":
                p.on_insert_tag()
                return True
            if ch == "L":
                p.on_clear()
                return True
            if ch == "M":
                p.combo_model.setFocus()
                return True
            if ch == "V":
                p.combo_voice.setFocus()
                return True
            if ch == "U":
                p.on_audition_voice()
                return True
            if ch == "Y":
                p.txt_style.setFocus()
                return True
            if ch == "B":
                p.on_browse_style()
                return True
            if ch == "C":
                p.on_create_custom_style()
                return True
            if ch == "G":
                if p.btn_generate.isEnabled():
                    p.on_generate()
                return True
            if ch == "S":
                if p.btn_save.isEnabled():
                    p.on_save()
                return True

        elif sel == 1:
            p = self.tab_multi
            if ch == "D":
                p.text_script.setFocus()
                return True
            if ch == "I":
                p.on_insert_tag()
                return True
            if ch == "L":
                p.on_load_podcast()
                return True
            if ch == "N":
                p.on_load_interview()
                return True
            if ch == "K":
                p.on_detect_speakers()
                return True
            if ch == "M":
                p.combo_model.setFocus()
                return True
            if ch == "G":
                if p.btn_generate.isEnabled():
                    p.on_generate()
                return True
            if ch == "S":
                if p.btn_save.isEnabled():
                    p.on_save()
                return True

        elif sel == 2:
            p = self.tab_design
            if ch == "N":
                p.txt_name.setFocus()
                return True
            if ch == "G":
                p.combo_gender.setFocus()
                return True
            if ch == "L":
                p.txt_lang.setFocus()
                return True
            if ch == "D":
                p.txt_prompt.setFocus()
                return True
            if ch == "C":
                if p.btn_create.isEnabled():
                    p.on_create_voice()
                return True
            if ch == "Y":
                if p.btn_copy_id.isEnabled():
                    p.on_copy_id()
                return True
            if ch == "S":
                if p.btn_save_wav.isEnabled():
                    p.on_save_wav()
                return True

        elif sel == 3:
            p = self.tab_replication
            if ch == "N":
                p.txt_name.setFocus()
                return True
            if ch == "R":
                p.txt_ref_path.setFocus()
                return True
            if ch == "B":
                p.on_browse_ref()
                return True
            if ch == "C":
                p.on_copy_consent()
                return True
            if ch == "S":
                p.txt_con_path.setFocus()
                return True
            if ch == "W":
                p.on_browse_con()
                return True
            if ch == "M":
                p.radio_mode.focus_active_radio()
                return True
            if ch == "V":
                if p.btn_replicate.isEnabled():
                    p.on_replicate()
                return True
            if ch == "Y":
                if p.btn_copy_id.isEnabled():
                    p.on_copy_id()
                return True

        elif sel == 4:
            p = self.tab_library
            if ch == "S":
                p.txt_search.setFocus()
                return True
            if ch == "L":
                p.txt_lang.setFocus()
                return True
            if ch == "G":
                p.combo_gender.setFocus()
                return True
            if ch == "D":
                p.combo_domain.setFocus()
                return True
            if ch == "X":
                if p.btn_search_remote.isEnabled():
                    p.on_search_remote()
                return True
            if ch == "B":
                p.load_prebuilt_voices(announce=True)
                return True
            if ch == "V":
                p.listbox_voices.setFocus()
                return True
            if ch == "U":
                p.on_audition()
                return True
            if ch == "Y":
                if p.btn_use_voice.isEnabled():
                    p.on_use_voice()
                return True
            if ch == "C":
                p.on_copy_id()
                return True
            if ch == "R":
                if p.btn_delete_custom.isEnabled():
                    p.on_delete_custom()
                return True

        elif sel == 5:
            p = self.tab_settings
            if ch == "K":
                p.txt_key.setFocus()
                return True
            if ch == "C":
                if p.btn_test_key.isEnabled():
                    p.on_test_key()
                return True
            if ch == "G":
                p.on_get_api_key()
                return True
            if ch == "D":
                p.txt_output_dir.setFocus()
                return True
            if ch == "W":
                p.on_browse_output()
                return True
            if ch == "M":
                p.combo_def_model.setFocus()
                return True
            if ch == "V":
                p.combo_def_voice.setFocus()
                return True
            if ch == "L":
                p.combo_language.setFocus()
                return True
            if ch == "R":
                p.chk_announcements.setFocus()
                p._toggle_announcements()
                return True
            if ch == "B":
                p.chk_beeps.setFocus()
                p._toggle_beeps()
                return True
            if ch == "U":
                p.chk_autoplay.setFocus()
                p._toggle_autoplay()
                return True
            if ch == "S":
                p.on_save_settings()
                return True

        return False

    # ====================================================================
    # TAB SWITCHING & FOCUS MANAGEMENT
    # ====================================================================
    def cycle_tab(self, forward: bool = True):
        count = self.tabs.count()
        if count == 0:
            return
        cur = max(0, self.tabs.currentIndex())
        nxt = (cur + 1) % count if forward else (cur - 1 + count) % count
        self.switch_tab(nxt)

    def switch_tab(self, index: int):
        count = self.tabs.count()
        if not (0 <= index < count):
            return
        cur = self.tabs.currentIndex()
        self.tabs.tabBar().setFocus()
        if cur == index:
            name = self.tab_names[index] if index < len(self.tab_names) else f"Tab {index + 1}"
            msg = tr("tab_selected_announce", name=name)
            announcer.announce(msg)
            self._set_status_text(msg)
            call_after(self.tabs.tabBar().setFocus)
        else:
            self.tabs.setCurrentIndex(index)

    def on_tab_changed(self, sel: int):
        self.tabs.tabBar().setFocus()
        call_after(self.tabs.tabBar().setFocus)
        if 0 <= sel < len(self.tab_names):
            name = self.tab_names[sel]
            msg = tr("tab_selected_announce", name=name)
            announcer.announce(msg)
            self._set_status_text(msg)

    def focus_tab_primary_control(self, sel: int, immediate: bool = False):
        def _do_focus():
            target = None
            if sel == 0:
                target = self.tab_single.text_ctrl
            elif sel == 1:
                target = self.tab_multi.text_script
            elif sel == 2:
                target = self.tab_design.txt_name
            elif sel == 3:
                target = self.tab_replication.txt_name
            elif sel == 4:
                target = self.tab_library.txt_search
            elif sel == 5:
                target = self.tab_settings.txt_key
            if target is not None and target.isVisible():
                target.setFocus()

        if immediate:
            _do_focus()
        else:
            call_after(_do_focus)

    # ====================================================================
    # MENU & GLOBAL ACTIONS
    # ====================================================================
    def on_global_generate(self, *args):
        sel = self.tabs.currentIndex()
        if sel == 0:
            self.tab_single.on_generate()
        elif sel == 1:
            self.tab_multi.on_generate()
        elif sel == 2:
            self.tab_design.on_create_voice()

    def _focused_text_editor(self):
        focus = QApplication.focusWidget()
        if isinstance(focus, (QLineEdit, QPlainTextEdit, QTextEdit, AccessibleTextArea)):
            return focus
        return AccessibleTextArea.active_editor()

    def on_edit_undo(self, *args):
        w = self._focused_text_editor()
        if w is not None:
            w.undo()

    def on_edit_redo(self, *args):
        w = self._focused_text_editor()
        if w is not None:
            w.redo()

    def on_edit_cut(self, *args):
        w = self._focused_text_editor()
        if w is not None:
            w.cut()

    def on_edit_copy(self, *args):
        w = self._focused_text_editor()
        if w is not None:
            w.copy()

    def on_edit_paste(self, *args):
        w = self._focused_text_editor()
        if w is not None:
            w.paste()

    def on_edit_delete(self, *args):
        w = self._focused_text_editor()
        if isinstance(w, AccessibleTextArea):
            w.delete_selection_or_char()
        elif isinstance(w, QLineEdit):
            w.del_()
        elif isinstance(w, (QPlainTextEdit, QTextEdit)):
            cursor = w.textCursor()
            if cursor.hasSelection():
                cursor.removeSelectedText()
            else:
                cursor.deleteChar()

    def on_edit_select_all(self, *args):
        w = self._focused_text_editor()
        if w is not None:
            w.selectAll()

    def on_edit_clear(self, *args):
        sel = self.tabs.currentIndex()
        if sel == 0:
            self.tab_single.on_clear()
        elif sel == 1:
            self.tab_multi.text_script.clear()
            self.tab_multi.text_script.setFocus()
            announcer.announce(tr("msg_script_cleared"))

    def on_menu_open_script(self, *args):
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            tr("dlg_open_script_title"),
            str(config.output_dir),
            "Text & Script files (*.txt *.md *.script);;All files (*.*)",
        )
        if path_str:
            path = Path(path_str)
            try:
                content = path.read_text(encoding="utf-8")
                sel = self.tabs.currentIndex()
                if sel == 1:
                    self.tab_multi.text_script.setPlainText(content)
                    self.tab_multi.update_speaker_controls()
                    self.tab_multi.text_script.setFocus()
                else:
                    if sel != 0:
                        self.switch_tab(0)
                    self.tab_single.text_ctrl.setPlainText(content)
                    self.tab_single.text_ctrl.setFocus()
                msg = tr("announce_script_loaded", filename=path.name)
                announcer.announce(msg)
                self._set_status_text(msg)
            except Exception as e:
                err_msg = tr("announce_script_error", error=str(e))
                announcer.announce(err_msg)
                self._set_status_text(err_msg)

    def on_menu_save_script(self, *args):
        sel = self.tabs.currentIndex()
        if sel == 1:
            content = self.tab_multi.text_script.toPlainText()
            default_name = "dialogue_script.txt"
        else:
            content = self.tab_single.text_ctrl.toPlainText()
            default_name = "speech_script.txt"
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            tr("dlg_save_script_title"),
            str(config.output_dir / default_name),
            "Text files (*.txt);;All files (*.*)",
        )
        if path_str:
            path = Path(path_str)
            try:
                path.write_text(content, encoding="utf-8")
                msg = tr("announce_script_saved", path=str(path))
                announcer.announce(msg)
                self._set_status_text(msg)
            except Exception as e:
                err_msg = tr("announce_script_error", error=str(e))
                announcer.announce(err_msg)
                self._set_status_text(err_msg)

    def on_menu_save(self, *args):
        sel = self.tabs.currentIndex()
        if sel == 0:
            self.tab_single.on_save()
        elif sel == 1:
            self.tab_multi.on_save()

    def on_menu_history(self, *args):
        dlg = GenerationHistoryDialog(self)
        dlg.exec()

    def on_menu_open_output(self, *args):
        open_output_folder()

    def on_menu_text_stats(self, *args):
        sel = self.tabs.currentIndex()
        if sel == 1:
            self.tab_multi.on_announce_stats()
        else:
            self.tab_single.on_announce_stats()

    def on_menu_play(self, *args):
        sel = self.tabs.currentIndex()
        if sel == 0:
            self.tab_single.on_play_stop()
        elif sel == 1:
            self.tab_multi.on_play_stop()
        elif sel == 2:
            self.tab_design.on_play_preview()
        else:
            audio_player.toggle_play_pause(announce=True)

    def on_menu_tag(self, *args):
        sel = self.tabs.currentIndex()
        if sel == 0:
            self.tab_single.on_insert_tag()
        elif sel == 1:
            self.tab_multi.on_insert_tag()
        else:
            self.tabs.setCurrentIndex(0)
            self.tab_single.on_insert_tag()

    def on_menu_style(self, *args):
        self.tabs.setCurrentIndex(0)
        self.tab_single.on_browse_style()

    def on_menu_create_style(self, *args):
        self.tabs.setCurrentIndex(0)
        self.tab_single.on_create_custom_style()

    def on_menu_help(self, *args):
        dlg = HelpDialog(self)
        res = dlg.exec()
        if res == WelcomeTourDialog.ID_GO_SETTINGS:
            self.switch_tab(5)
            self.focus_tab_primary_control(5)

    def on_menu_check_updates(self, *args):
        dlg = UpdateDialog(self)
        dlg.exec()

    def on_menu_about(self, *args):
        QMessageBox.information(
            self,
            "About Gemvox",
            f"Gemvox - Accessible Gemini 3.8 Flash TTS Studio\n\n"
            f"Version {VERSION} (Universal Design PySide6 Edition)\n"
            "Designed for blind, visually impaired, and sighted creators\n"
            "with full screen reader accessibility, wx-compatible keyboard navigation,\n"
            "and Obsidian & Royal Gold studio aesthetics.\n\n"
            "Supports Gemini 3.8 Flash TTS, Multi-Speaker Dialogue,\n"
            "Voice Design, Voice Replication, Voice Library management,\n"
            "Recent Generations History, and Bilingual (English/Thai) Screen Reader Announcements.",
        )
