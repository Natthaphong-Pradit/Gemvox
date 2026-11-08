from pathlib import Path
import wx
from gemvox import VERSION
from gemvox.config import config
from gemvox.i18n import tr
from gemvox.accessibility import announcer
from gemvox.core.audio_player import audio_player
from gemvox.ui.single_speaker_panel import SingleSpeakerPanel
from gemvox.ui.multi_speaker_panel import MultiSpeakerPanel
from gemvox.ui.voice_design_panel import VoiceDesignPanel
from gemvox.ui.voice_replication_panel import VoiceReplicationPanel
from gemvox.ui.voice_library_panel import VoiceLibraryPanel
from gemvox.ui.settings_panel import SettingsPanel
from gemvox.ui.dialogs import (
    HelpDialog,
    InlineTagDialog,
    StylePresetDialog,
    WelcomeTourDialog,
    GenerationHistoryDialog,
    UpdateDialog,
    open_output_folder,
)
from gemvox.ui.theme import (
    StudioColors,
    get_font,
    create_app_icon,
    attach_painted_header,
)


class MainWindow(wx.Frame):
    """
    Main window of Gemvox designed for 100% screen reader accessibility and luxury studio aesthetics.
    Zero-unlabeled-panel architecture:
    - wx.Notebook is placed directly inside MainWindow without an intermediate wrapper wx.Panel.
    - The luxury Obsidian & Royal Gold studio header is painted directly via wx.EVT_PAINT (0 child HWNDs).
    """

    def __init__(self):
        super().__init__(
            None,
            title=tr("app_title", version=VERSION),
            size=(1060, 760),
            style=wx.DEFAULT_FRAME_STYLE
        )
        self.SetMinSize((900, 660))
        self.SetBackgroundColour(StudioColors.BG_DEEP)
        self.SetForegroundColour(StudioColors.TEXT_PRIMARY)
        try:
            self.SetIcon(create_app_icon())
        except Exception:
            pass

        self.tab_names = [
            tr("tab_single"),
            tr("tab_multi"),
            tr("tab_design"),
            tr("tab_replication"),
            tr("tab_library"),
            tr("tab_settings")
        ]

        self._init_menu()
        self._init_ui()
        self._init_accelerators()
        self.Bind(wx.EVT_CHAR_HOOK, self.on_char_hook)
        self.Centre()

        # Initial voice announcement
        announcer.announce(tr("app_opened_announce", version=VERSION))

        # If this is the very first launch (no API key and tour not completed yet),
        # automatically launch the guided Welcome Tour after the main window renders.
        if config.is_first_run:
            wx.CallAfter(self._show_first_run_welcome_tour)

    def _show_first_run_welcome_tour(self):
        dlg = WelcomeTourDialog(self)
        res = dlg.ShowModal()
        dlg.Destroy()
        if res == WelcomeTourDialog.ID_GO_SETTINGS:
            self.switch_tab(5)
            self.focus_tab_primary_control(5)

    def _init_menu(self):
        menu_bar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        m_open_script = file_menu.Append(wx.ID_OPEN, tr("menu_open_script"), tr("menu_open_script_help"))
        m_save_script = file_menu.Append(wx.ID_ANY, tr("menu_save_script"), tr("menu_save_script_help"))
        file_menu.AppendSeparator()
        m_save = file_menu.Append(wx.ID_SAVE, tr("menu_save_audio"), tr("menu_save_audio_help"))
        m_history = file_menu.Append(wx.ID_ANY, tr("menu_history"), tr("menu_history_help"))
        m_open_out = file_menu.Append(wx.ID_ANY, tr("menu_open_output_dir"), tr("menu_open_output_dir_help"))
        file_menu.AppendSeparator()
        m_exit = file_menu.Append(wx.ID_EXIT, tr("menu_exit"), tr("menu_exit_help"))
        menu_bar.Append(file_menu, tr("menu_file"))

        # Edit menu (Standard Windows editing commands)
        edit_menu = wx.Menu()
        m_undo = edit_menu.Append(wx.ID_UNDO, tr("menu_undo"))
        m_redo = edit_menu.Append(wx.ID_REDO, tr("menu_redo"))
        edit_menu.AppendSeparator()
        m_cut = edit_menu.Append(wx.ID_CUT, tr("menu_cut"))
        m_copy = edit_menu.Append(wx.ID_COPY, tr("menu_copy"))
        m_paste = edit_menu.Append(wx.ID_PASTE, tr("menu_paste"))
        m_delete = edit_menu.Append(wx.ID_DELETE, tr("menu_delete"))
        edit_menu.AppendSeparator()
        m_select_all = edit_menu.Append(wx.ID_SELECTALL, tr("menu_select_all"))
        edit_menu.AppendSeparator()
        m_clear_field = edit_menu.Append(wx.ID_ANY, tr("menu_clear_field"))
        menu_bar.Append(edit_menu, tr("menu_edit"))

        # Audio menu
        audio_menu = wx.Menu()
        m_play = audio_menu.Append(wx.ID_ANY, tr("menu_play_stop"))
        m_audio_history = audio_menu.Append(wx.ID_ANY, tr("menu_audio_history"))
        menu_bar.Append(audio_menu, tr("menu_audio"))

        # Tabs menu
        tabs_menu = wx.Menu()
        m_tab1 = tabs_menu.Append(wx.ID_ANY, tr("menu_tab1"))
        m_tab2 = tabs_menu.Append(wx.ID_ANY, tr("menu_tab2"))
        m_tab3 = tabs_menu.Append(wx.ID_ANY, tr("menu_tab3"))
        m_tab4 = tabs_menu.Append(wx.ID_ANY, tr("menu_tab4"))
        m_tab5 = tabs_menu.Append(wx.ID_ANY, tr("menu_tab5"))
        m_tab6 = tabs_menu.Append(wx.ID_ANY, tr("menu_tab6"))
        tabs_menu.AppendSeparator()
        m_next_tab = tabs_menu.Append(wx.ID_ANY, tr("menu_next_tab"))
        m_prev_tab = tabs_menu.Append(wx.ID_ANY, tr("menu_prev_tab"))
        menu_bar.Append(tabs_menu, tr("menu_tabs"))

        # Tools menu
        tools_menu = wx.Menu()
        m_tag = tools_menu.Append(wx.ID_ANY, tr("menu_insert_tag"))
        m_style = tools_menu.Append(wx.ID_ANY, tr("menu_browse_style"))
        m_create_style = tools_menu.Append(wx.ID_ANY, tr("menu_create_style"))
        tools_menu.AppendSeparator()
        m_stats = tools_menu.Append(wx.ID_ANY, tr("menu_text_stats"))
        tools_menu.AppendSeparator()
        m_tour = tools_menu.Append(wx.ID_ANY, tr("menu_welcome_tour"))
        menu_bar.Append(tools_menu, tr("menu_tools"))

        # Help menu
        help_menu = wx.Menu()
        m_help = help_menu.Append(wx.ID_HELP, tr("menu_help_guide"))
        m_update = help_menu.Append(wx.ID_ANY, tr("menu_check_updates"))
        help_menu.AppendSeparator()
        m_about = help_menu.Append(wx.ID_ABOUT, tr("menu_about"))
        menu_bar.Append(help_menu, tr("menu_help"))

        self.SetMenuBar(menu_bar)

        # Bindings
        self.Bind(wx.EVT_MENU, self.on_menu_open_script, m_open_script)
        self.Bind(wx.EVT_MENU, self.on_menu_save_script, m_save_script)
        self.Bind(wx.EVT_MENU, self.on_menu_save, m_save)
        self.Bind(wx.EVT_MENU, self.on_menu_history, m_history)
        self.Bind(wx.EVT_MENU, self.on_menu_open_output, m_open_out)
        self.Bind(wx.EVT_MENU, self.on_menu_exit, m_exit)
        self.Bind(wx.EVT_MENU, self.on_edit_undo, m_undo)
        self.Bind(wx.EVT_MENU, self.on_edit_redo, m_redo)
        self.Bind(wx.EVT_MENU, self.on_edit_cut, m_cut)
        self.Bind(wx.EVT_MENU, self.on_edit_copy, m_copy)
        self.Bind(wx.EVT_MENU, self.on_edit_paste, m_paste)
        self.Bind(wx.EVT_MENU, self.on_edit_delete, m_delete)
        self.Bind(wx.EVT_MENU, self.on_edit_select_all, m_select_all)
        self.Bind(wx.EVT_MENU, self.on_edit_clear, m_clear_field)
        self.Bind(wx.EVT_MENU, self.on_menu_play, m_play)
        self.Bind(wx.EVT_MENU, self.on_menu_history, m_audio_history)
        self.Bind(wx.EVT_MENU, lambda e: self.switch_tab(0), m_tab1)
        self.Bind(wx.EVT_MENU, lambda e: self.switch_tab(1), m_tab2)
        self.Bind(wx.EVT_MENU, lambda e: self.switch_tab(2), m_tab3)
        self.Bind(wx.EVT_MENU, lambda e: self.switch_tab(3), m_tab4)
        self.Bind(wx.EVT_MENU, lambda e: self.switch_tab(4), m_tab5)
        self.Bind(wx.EVT_MENU, lambda e: self.switch_tab(5), m_tab6)
        self.Bind(wx.EVT_MENU, lambda e: self.cycle_tab(forward=True), m_next_tab)
        self.Bind(wx.EVT_MENU, lambda e: self.cycle_tab(forward=False), m_prev_tab)
        self.Bind(wx.EVT_MENU, self.on_menu_tag, m_tag)
        self.Bind(wx.EVT_MENU, self.on_menu_style, m_style)
        self.Bind(wx.EVT_MENU, self.on_menu_create_style, m_create_style)
        self.Bind(wx.EVT_MENU, self.on_menu_text_stats, m_stats)
        self.Bind(wx.EVT_MENU, lambda e: self._show_first_run_welcome_tour(), m_tour)
        self.Bind(wx.EVT_MENU, self.on_menu_help, m_help)
        self.Bind(wx.EVT_MENU, self.on_menu_check_updates, m_update)
        self.Bind(wx.EVT_MENU, self.on_menu_about, m_about)

    def _init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Painted Studio Header Banner (0 child HWNDs — eliminates all unlabeled panels!)
        attach_painted_header(
            self,
            sizer,
            title=tr("banner_title"),
            subtitle=tr("banner_subtitle"),
            badge_text=tr("banner_badge", version=VERSION)
        )

        self.notebook = wx.Notebook(self, name="Studio Workspace Tabs")
        self.notebook.SetBackgroundColour(StudioColors.BG_DEEP)
        self.notebook.SetForegroundColour(StudioColors.TEXT_PRIMARY)
        self.notebook.SetFont(get_font(10, bold=True))

        # 6 Dedicated Accessible Tabs
        self.tab_single = SingleSpeakerPanel(self.notebook)
        self.tab_multi = MultiSpeakerPanel(self.notebook)
        self.tab_design = VoiceDesignPanel(self.notebook)
        self.tab_replication = VoiceReplicationPanel(self.notebook)
        self.tab_library = VoiceLibraryPanel(self.notebook)
        self.tab_settings = SettingsPanel(self.notebook)

        self.notebook.AddPage(self.tab_single, self.tab_names[0])
        self.notebook.AddPage(self.tab_multi, self.tab_names[1])
        self.notebook.AddPage(self.tab_design, self.tab_names[2])
        self.notebook.AddPage(self.tab_replication, self.tab_names[3])
        self.notebook.AddPage(self.tab_library, self.tab_names[4])
        self.notebook.AddPage(self.tab_settings, self.tab_names[5])

        sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 8)
        self.SetSizer(sizer)

        # Status Bar
        status_bar = self.CreateStatusBar(3)
        status_bar.SetBackgroundColour(StudioColors.BG_STATUS)
        status_bar.SetForegroundColour(StudioColors.TEXT_PRIMARY)
        self.SetStatusWidths([-3, -2, -1])
        self.SetStatusText(tr("status_ready_main"), 0)
        self.SetStatusText(tr("status_engine"), 1)
        self.SetStatusText(tr("status_sr_mode"), 2)

        # Tab change event
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_tab_changed)

    def _init_accelerators(self):
        id_gen = wx.NewIdRef()
        self.Bind(wx.EVT_MENU, self.on_global_generate, id=id_gen)
        accel_table = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, wx.WXK_RETURN, id_gen),
        ])
        self.SetAcceleratorTable(accel_table)

    def on_char_hook(self, event):
        """Global key hook that intercepts keystrokes across all child controls and panels."""
        focused = wx.Window.FindFocus()
        if focused and wx.GetTopLevelParent(focused) != self:
            event.Skip()
            return

        key = event.GetKeyCode()
        ctrl = event.ControlDown()
        alt = event.AltDown()
        shift = event.ShiftDown()

        # 0. Tab Control (wx.Notebook) navigation: keep focus locked on Tab Control for Left/Right arrows,
        #    and only enter the tab's inner UI when pressing Tab.
        if focused == self.notebook:
            if not ctrl and not alt and not shift:
                if key in (wx.WXK_LEFT, wx.WXK_UP):
                    self.cycle_tab(forward=False)
                    return
                if key in (wx.WXK_RIGHT, wx.WXK_DOWN):
                    self.cycle_tab(forward=True)
                    return
                if key == wx.WXK_HOME:
                    self.switch_tab(0)
                    return
                if key == wx.WXK_END:
                    self.switch_tab(self.notebook.GetPageCount() - 1)
                    return
            if not ctrl and not alt and key == wx.WXK_TAB:
                current_page = self.notebook.GetCurrentPage()
                if current_page:
                    flags = wx.NavigationKeyEvent.IsBackward if shift else wx.NavigationKeyEvent.IsForward
                    current_page.NavigateIn(flags)
                return

        # 1. Direct tab selection: Ctrl+1..6 or Alt+1..6 (number row or numpad)
        if (ctrl and not alt and not shift) or (alt and not ctrl and not shift):
            if ord('1') <= key <= ord('6'):
                self.switch_tab(key - ord('1'))
                return
            numpad_1 = getattr(wx, 'WXK_NUMPAD1', 325)
            if numpad_1 <= key <= numpad_1 + 5:
                self.switch_tab(key - numpad_1)
                return

        # 2. Next tab: Ctrl+Tab or Ctrl+PageDown
        if ctrl and not alt and not shift:
            if key == wx.WXK_TAB or key == getattr(wx, 'WXK_PAGEDOWN', 367) or key == getattr(wx, 'WXK_NUMPAD_PAGEDOWN', 367):
                self.cycle_tab(forward=True)
                return

        # 3. Previous tab: Ctrl+Shift+Tab or Ctrl+PageUp
        if (ctrl and shift and not alt and key == wx.WXK_TAB) or (ctrl and not alt and not shift and (key == getattr(wx, 'WXK_PAGEUP', 366) or key == getattr(wx, 'WXK_NUMPAD_PAGEUP', 366))):
            self.cycle_tab(forward=False)
            return

        # 4. Global Generate Speech: Ctrl+Enter
        if ctrl and not alt and not shift and (key == wx.WXK_RETURN or key == getattr(wx, 'WXK_NUMPAD_ENTER', 370)):
            self.on_global_generate(None)
            return

        # 5. Global Play / Stop Audio: Alt+P
        if alt and not ctrl and not shift and (key == ord('p') or key == ord('P')):
            self.on_menu_play(None)
            return

        # 5b. Global File & Workflow Shortcuts (Ctrl+O, Ctrl+S, Ctrl+Shift+S, Ctrl+H, Ctrl+Shift+O, Ctrl+I, Alt+Shift+L, F1)
        if not ctrl and not alt and not shift and key == wx.WXK_F1:
            self.on_menu_help(None)
            return
        if ctrl and not alt and not shift:
            if key in (ord('o'), ord('O')):
                self.on_menu_open_script(None)
                return
            if key in (ord('s'), ord('S')):
                self.on_menu_save(None)
                return
            if key in (ord('h'), ord('H')):
                self.on_menu_history(None)
                return
            if key in (ord('i'), ord('I')):
                self.on_menu_text_stats(None)
                return
            if key in (ord('u'), ord('U')):
                self.on_menu_check_updates(None)
                return
        if ctrl and shift and not alt:
            if key in (ord('s'), ord('S')):
                self.on_menu_save_script(None)
                return
            if key in (ord('o'), ord('O')):
                self.on_menu_open_output(None)
                return
        if alt and shift and not ctrl:
            if key in (ord('l'), ord('L')):
                self.on_edit_clear(None)
                return

        # 6. Active Tab Mnemonic Shortcuts (Alt+Key, excluding MenuBar keys F, E, A, T, O, H)
        if alt and not ctrl and not shift and 32 <= key <= 126:
            ch = chr(key).upper()
            if self._handle_active_tab_mnemonic(ch):
                return

        event.Skip()

    def _handle_active_tab_mnemonic(self, ch: str) -> bool:
        """
        Explicitly routes Alt+<Key> mnemonics to the active tab's controls or actions.
        Works reliably even when focus is locked on the wx.Notebook tab header.
        """
        sel = self.notebook.GetSelection()
        if sel == 0 and hasattr(self, 'tab_single'):
            p = self.tab_single
            if ch == 'X':
                p.text_ctrl.SetFocus()
                return True
            if ch == 'I':
                p.on_insert_tag(None)
                return True
            if ch == 'L':
                p.on_clear(None)
                return True
            if ch == 'M':
                p.combo_model.SetFocus()
                return True
            if ch == 'V':
                p.combo_voice.SetFocus()
                return True
            if ch == 'U':
                p.on_audition_voice(None)
                return True
            if ch == 'Y':
                p.txt_style.SetFocus()
                return True
            if ch == 'B':
                p.on_browse_style(None)
                return True
            if ch == 'C':
                p.on_create_custom_style(None)
                return True
            if ch == 'G':
                if p.btn_generate.IsEnabled():
                    p.on_generate(None)
                return True
            if ch == 'S':
                if p.btn_save.IsEnabled():
                    p.on_save(None)
                return True

        elif sel == 1 and hasattr(self, 'tab_multi'):
            p = self.tab_multi
            if ch == 'D':
                p.text_script.SetFocus()
                return True
            if ch == 'I':
                p.on_insert_tag(None)
                return True
            if ch == 'L':
                p.on_load_podcast(None)
                return True
            if ch == 'N':
                p.on_load_interview(None)
                return True
            if ch == 'K':
                p.on_detect_speakers(None)
                return True
            if ch == 'M':
                p.combo_model.SetFocus()
                return True
            if ch == 'G':
                if p.btn_generate.IsEnabled():
                    p.on_generate(None)
                return True
            if ch == 'S':
                if p.btn_save.IsEnabled():
                    p.on_save(None)
                return True

        elif sel == 2 and hasattr(self, 'tab_design'):
            p = self.tab_design
            if ch == 'N':
                p.txt_name.SetFocus()
                return True
            if ch == 'G':
                p.combo_gender.SetFocus()
                return True
            if ch == 'L':
                p.txt_lang.SetFocus()
                return True
            if ch == 'D':
                p.txt_prompt.SetFocus()
                return True
            if ch == 'C':
                if p.btn_create.IsEnabled():
                    p.on_create_voice(None)
                return True
            if ch == 'Y':
                if p.btn_copy_id.IsEnabled():
                    p.on_copy_id(None)
                return True
            if ch == 'S':
                if p.btn_save_wav.IsEnabled():
                    p.on_save_wav(None)
                return True

        elif sel == 3 and hasattr(self, 'tab_replication'):
            p = self.tab_replication
            if ch == 'N':
                p.txt_name.SetFocus()
                return True
            if ch == 'R':
                p.txt_ref_path.SetFocus()
                return True
            if ch == 'B':
                p.on_browse_ref(None)
                return True
            if ch == 'C':
                p.on_copy_consent(None)
                return True
            if ch == 'S':
                p.txt_con_path.SetFocus()
                return True
            if ch == 'W':
                p.on_browse_con(None)
                return True
            if ch == 'M':
                p.radio_mode.SetFocus()
                return True
            if ch == 'V':
                if p.btn_replicate.IsEnabled():
                    p.on_replicate(None)
                return True
            if ch == 'Y':
                if p.btn_copy_id.IsEnabled():
                    p.on_copy_id(None)
                return True

        elif sel == 4 and hasattr(self, 'tab_library'):
            p = self.tab_library
            if ch == 'S':
                p.txt_search.SetFocus()
                return True
            if ch == 'L':
                p.txt_lang.SetFocus()
                return True
            if ch == 'G':
                p.combo_gender.SetFocus()
                return True
            if ch == 'D':
                p.combo_domain.SetFocus()
                return True
            if ch == 'X':
                if p.btn_search_remote.IsEnabled():
                    p.on_search_remote(None)
                return True
            if ch == 'B':
                p.load_prebuilt_voices(announce=True)
                return True
            if ch == 'V':
                p.listbox_voices.SetFocus()
                return True
            if ch == 'U':
                p.on_audition(None)
                return True
            if ch == 'Y':
                if p.btn_use_voice.IsEnabled():
                    p.on_use_voice(None)
                return True
            if ch == 'C':
                p.on_copy_id(None)
                return True
            if ch == 'R':
                if p.btn_delete_custom.IsEnabled():
                    p.on_delete_custom(None)
                return True

        elif sel == 5 and hasattr(self, 'tab_settings'):
            p = self.tab_settings
            if ch == 'K':
                p.txt_key.SetFocus()
                return True
            if ch == 'C':
                if p.btn_test_key.IsEnabled():
                    p.on_test_key(None)
                return True
            if ch == 'G':
                p.on_get_api_key(None)
                return True
            if ch == 'D':
                p.txt_output_dir.SetFocus()
                return True
            if ch == 'W':
                p.on_browse_output(None)
                return True
            if ch == 'M':
                p.combo_def_model.SetFocus()
                return True
            if ch == 'V':
                p.combo_def_voice.SetFocus()
                return True
            if ch == 'L':
                p.combo_language.SetFocus()
                return True
            if ch == 'R':
                p.chk_announcements.SetFocus()
                p._toggle_announcements()
                return True
            if ch == 'B':
                p.chk_beeps.SetFocus()
                p._toggle_beeps()
                return True
            if ch == 'U':
                p.chk_autoplay.SetFocus()
                p._toggle_autoplay()
                return True
            if ch == 'S':
                p.on_save_settings(None)
                return True

        return False

    def cycle_tab(self, forward: bool = True):
        count = self.notebook.GetPageCount()
        if count == 0:
            return
        cur = self.notebook.GetSelection()
        if cur == wx.NOT_FOUND:
            cur = 0
        if forward:
            nxt = (cur + 1) % count
        else:
            nxt = (cur - 1 + count) % count
        self.switch_tab(nxt)

    def switch_tab(self, index: int):
        count = self.notebook.GetPageCount()
        if not (0 <= index < count):
            return
        cur = self.notebook.GetSelection()
        self.notebook.SetFocus()
        if cur == index:
            name = self.tab_names[index] if index < len(self.tab_names) else f"Tab {index + 1}"
            msg = tr("tab_selected_announce", name=name)
            announcer.announce(msg)
            self.SetStatusText(msg, 0)
            wx.CallAfter(self.notebook.SetFocus)
        else:
            self.notebook.SetSelection(index)

    def on_tab_changed(self, event):
        sel = event.GetSelection()
        if sel == wx.NOT_FOUND or sel is None:
            sel = self.notebook.GetSelection()
        self.notebook.SetFocus()
        wx.CallAfter(self.notebook.SetFocus)
        if 0 <= sel < len(self.tab_names):
            name = self.tab_names[sel]
            msg = tr("tab_selected_announce", name=name)
            announcer.announce(msg)
            self.SetStatusText(msg, 0)
        event.Skip()

    def focus_tab_primary_control(self, sel: int):
        def _do_focus():
            target = None
            if sel == 0 and hasattr(self, 'tab_single'):
                target = getattr(self.tab_single, 'text_ctrl', None)
            elif sel == 1 and hasattr(self, 'tab_multi'):
                target = getattr(self.tab_multi, 'text_script', None)
            elif sel == 2 and hasattr(self, 'tab_design'):
                target = getattr(self.tab_design, 'txt_name', None)
            elif sel == 3 and hasattr(self, 'tab_replication'):
                target = getattr(self.tab_replication, 'txt_name', None)
            elif sel == 4 and hasattr(self, 'tab_library'):
                target = getattr(self.tab_library, 'txt_search', None)
            elif sel == 5 and hasattr(self, 'tab_settings'):
                target = getattr(self.tab_settings, 'txt_key', None)
            if target and target.IsShownOnScreen():
                target.SetFocus()
        wx.CallAfter(_do_focus)

    def on_global_generate(self, event):
        sel = self.notebook.GetSelection()
        if sel == 0:
            self.tab_single.on_generate()
        elif sel == 1:
            self.tab_multi.on_generate()
        elif sel == 2:
            self.tab_design.on_create_voice(None)

    def on_edit_undo(self, event):
        focus = wx.Window.FindFocus()
        if isinstance(focus, wx.TextCtrl) and focus.CanUndo():
            focus.Undo()
        else:
            event.Skip()

    def on_edit_redo(self, event):
        focus = wx.Window.FindFocus()
        if isinstance(focus, wx.TextCtrl) and focus.CanRedo():
            focus.Redo()
        else:
            event.Skip()

    def on_edit_cut(self, event):
        focus = wx.Window.FindFocus()
        if isinstance(focus, wx.TextCtrl) and focus.CanCut():
            focus.Cut()
        else:
            event.Skip()

    def on_edit_copy(self, event):
        focus = wx.Window.FindFocus()
        if isinstance(focus, wx.TextCtrl) and focus.CanCopy():
            focus.Copy()
        else:
            event.Skip()

    def on_edit_paste(self, event):
        focus = wx.Window.FindFocus()
        if isinstance(focus, wx.TextCtrl) and focus.CanPaste():
            focus.Paste()
        else:
            event.Skip()

    def on_edit_delete(self, event):
        focus = wx.Window.FindFocus()
        if isinstance(focus, wx.TextCtrl):
            sel_from, sel_to = focus.GetSelection()
            if sel_from != sel_to:
                focus.Remove(sel_from, sel_to)
            else:
                pos = focus.GetInsertionPoint()
                if pos < focus.GetLastPosition():
                    focus.Remove(pos, pos + 1)
        else:
            event.Skip()

    def on_edit_select_all(self, event):
        focus = wx.Window.FindFocus()
        if isinstance(focus, wx.TextCtrl):
            focus.SelectAll()
        else:
            event.Skip()

    def on_edit_clear(self, event):
        sel = self.notebook.GetSelection()
        if sel == 0:
            self.tab_single.on_clear(None)
        elif sel == 1:
            self.tab_multi.text_script.Clear()
            self.tab_multi.text_script.SetFocus()
            announcer.announce(tr("msg_script_cleared"))

    def on_menu_open_script(self, event=None):
        with wx.FileDialog(
            self,
            tr("dlg_open_script_title"),
            wildcard="Text & Script files (*.txt;*.md;*.script)|*.txt;*.md;*.script|All files (*.*)|*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                path = Path(dlg.GetPath())
                try:
                    content = path.read_text(encoding="utf-8")
                    sel = self.notebook.GetSelection()
                    if sel == 1:
                        self.tab_multi.text_script.SetValue(content)
                        self.tab_multi.update_speaker_controls(announce=False)
                        self.tab_multi.text_script.SetFocus()
                    else:
                        if sel != 0:
                            self.switch_tab(0)
                        self.tab_single.text_ctrl.SetValue(content)
                        self.tab_single.text_ctrl.SetFocus()
                    msg = tr("announce_script_loaded", filename=path.name)
                    announcer.announce(msg)
                    self.SetStatusText(msg, 0)
                except Exception as e:
                    err_msg = tr("announce_script_error", error=str(e))
                    announcer.announce(err_msg)
                    self.SetStatusText(err_msg, 0)

    def on_menu_save_script(self, event=None):
        sel = self.notebook.GetSelection()
        if sel == 1:
            content = self.tab_multi.text_script.GetValue()
            default_name = "dialogue_script.txt"
        else:
            content = self.tab_single.text_ctrl.GetValue()
            default_name = "speech_script.txt"
        with wx.FileDialog(
            self,
            tr("dlg_save_script_title"),
            defaultFile=default_name,
            wildcard="Text files (*.txt)|*.txt|All files (*.*)|*.*",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                path = Path(dlg.GetPath())
                try:
                    path.write_text(content, encoding="utf-8")
                    msg = tr("announce_script_saved", path=str(path))
                    announcer.announce(msg)
                    self.SetStatusText(msg, 0)
                except Exception as e:
                    err_msg = tr("announce_script_error", error=str(e))
                    announcer.announce(err_msg)
                    self.SetStatusText(err_msg, 0)

    def on_menu_save(self, event=None):
        sel = self.notebook.GetSelection()
        if sel == 0:
            self.tab_single.on_save()
        elif sel == 1:
            self.tab_multi.on_save()

    def on_menu_history(self, event=None):
        dlg = GenerationHistoryDialog(self)
        dlg.ShowModal()
        dlg.Destroy()

    def on_menu_open_output(self, event=None):
        open_output_folder()

    def on_menu_text_stats(self, event=None):
        sel = self.notebook.GetSelection()
        if sel == 1:
            self.tab_multi.on_announce_stats(None)
        else:
            self.tab_single.on_announce_stats(None)

    def on_menu_play(self, event=None):
        if audio_player.is_playing:
            audio_player.stop()
            return
        sel = self.notebook.GetSelection()
        if sel == 0:
            self.tab_single.on_play_stop()
        elif sel == 1:
            self.tab_multi.on_play_stop()
        elif sel == 2:
            self.tab_design.on_play_preview(None)

    def on_menu_tag(self, event):
        sel = self.notebook.GetSelection()
        if sel == 0:
            self.tab_single.on_insert_tag(None)
        elif sel == 1:
            self.tab_multi.on_insert_tag(None)
        else:
            self.notebook.SetSelection(0)
            self.tab_single.on_insert_tag(None)

    def on_menu_style(self, event):
        self.notebook.SetSelection(0)
        self.tab_single.on_browse_style(None)

    def on_menu_create_style(self, event):
        self.notebook.SetSelection(0)
        self.tab_single.on_create_custom_style(None)

    def on_menu_help(self, event):
        dlg = HelpDialog(self)
        res = dlg.ShowModal()
        dlg.Destroy()
        if res == WelcomeTourDialog.ID_GO_SETTINGS:
            self.switch_tab(5)
            self.focus_tab_primary_control(5)

    def on_menu_check_updates(self, event=None):
        dlg = UpdateDialog(self)
        dlg.ShowModal()
        if dlg:
            dlg.Destroy()

    def on_menu_about(self, event):
        wx.MessageBox(
            f"Gemvox - Accessible Gemini 3.8 Flash TTS Studio\n\n"
            f"Version {VERSION} (Obsidian & Royal Gold Studio Edition)\n"
            "Designed specifically for blind, visually impaired, and sighted creators\n"
            "with both screen reader accessibility and luxury studio aesthetics.\n\n"
            "Supports Gemini 3.8 Flash TTS, Multi-Speaker Dialogue,\n"
            "Voice Design, Voice Replication, Voice Library management,\n"
            "Recent Generations History, and Bilingual (English/Thai) Screen Reader Announcements.\n\n"
            "Includes full standard Windows text editing commands (Undo, Redo,\n"
            "Cut, Copy, Paste, Select All, custom style presets, and precision vocal tag insertion).",
            "About Gemvox",
            wx.OK | wx.ICON_INFORMATION
        )

    def on_menu_exit(self, event):
        self.Close()
