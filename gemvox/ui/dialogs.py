import wx
from gemvox.config import config
from gemvox.i18n import tr
from gemvox.core.voice_catalog import INLINE_VOCAL_TAGS, STYLE_PRESETS, get_all_style_presets
from gemvox.accessibility import announcer
from gemvox.ui.theme import (
    style_panel,
    style_label,
    style_text_ctrl,
    style_listbox,
    style_button,
    attach_painted_header,
)


class InlineTagDialog(wx.Dialog):
    """Accessible dialog to select and insert inline vocal tags (zero unlabeled child panels)."""
    def __init__(self, parent):
        super().__init__(parent, title=tr("dlg_tag_title"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.selected_tag = None
        style_panel(self, accessible_name=tr("dlg_tag_title"))
        self._init_ui()
        self.CentreOnParent()

    def _init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        attach_painted_header(
            self,
            sizer,
            title=tr("dlg_tag_banner_title"),
            subtitle=tr("dlg_tag_banner_sub"),
            badge_text="VOCAL TAG"
        )

        info_label = wx.StaticText(
            self,
            label=tr("dlg_tag_info")
        )
        style_label(info_label, "muted")
        sizer.Add(info_label, 0, wx.ALL, 12)

        # Accessible listbox
        choices = [f"{item['tag']} - {item['label']}: {item['description']}" for item in INLINE_VOCAL_TAGS]
        self.listbox = wx.ListBox(self, choices=choices, style=wx.LB_SINGLE)
        style_listbox(self.listbox)
        if choices:
            self.listbox.SetSelection(0)
        sizer.Add(self.listbox, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        # Buttons
        btn_sizer = wx.StdDialogButtonSizer()
        insert_btn = wx.Button(self, wx.ID_OK, label=tr("btn_insert"))
        insert_btn.SetDefault()
        style_button(insert_btn, "primary")
        cancel_btn = wx.Button(self, wx.ID_CANCEL, label=tr("btn_cancel"))
        style_button(cancel_btn, "secondary")
        btn_sizer.AddButton(insert_btn)
        btn_sizer.AddButton(cancel_btn)
        btn_sizer.Realize()
        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 12)

        self.SetSizer(sizer)
        self.SetSize((580, 460))

        insert_btn.Bind(wx.EVT_BUTTON, self.on_insert)
        self.listbox.Bind(wx.EVT_LISTBOX_DCLICK, self.on_insert)

    def on_insert(self, event):
        sel = self.listbox.GetSelection()
        if sel != wx.NOT_FOUND:
            self.selected_tag = INLINE_VOCAL_TAGS[sel]["tag"]
            self.EndModal(wx.ID_OK)
        else:
            self.EndModal(wx.ID_CANCEL)


class CreateCustomStyleDialog(wx.Dialog):
    """Accessible dialog to create and save a reusable custom style preset (zero unlabeled child panels)."""
    def __init__(self, parent, initial_style: str = ""):
        super().__init__(
            parent,
            title=tr("dlg_custom_style_title"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        self.initial_style = initial_style
        self.created_name = None
        self.created_style = None
        style_panel(self, accessible_name=tr("dlg_custom_style_title"))
        self._init_ui()
        self.CentreOnParent()

    def _init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        attach_painted_header(
            self,
            sizer,
            title=tr("dlg_custom_style_banner"),
            subtitle=tr("dlg_custom_style_sub"),
            badge_text="CUSTOM PRESET"
        )

        info = wx.StaticText(
            self,
            label=tr("dlg_custom_style_info")
        )
        style_label(info, "muted")
        sizer.Add(info, 0, wx.ALL, 12)

        grid = wx.FlexGridSizer(rows=2, cols=2, vgap=12, hgap=12)
        grid.AddGrowableCol(1, 1)

        lbl_name = wx.StaticText(self, label=tr("lbl_preset_name"))
        style_label(lbl_name)
        self.txt_name = wx.TextCtrl(self, value="")
        style_text_ctrl(self.txt_name)
        grid.Add(lbl_name, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.txt_name, 1, wx.EXPAND)

        lbl_style = wx.StaticText(self, label=tr("lbl_preset_style"))
        style_label(lbl_style)
        self.txt_style = wx.TextCtrl(self, value=self.initial_style)
        style_text_ctrl(self.txt_style)
        grid.Add(lbl_style, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.txt_style, 1, wx.EXPAND)

        sizer.Add(grid, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        btn_sizer = wx.StdDialogButtonSizer()
        save_btn = wx.Button(self, wx.ID_OK, label=tr("btn_save_preset"))
        save_btn.SetDefault()
        style_button(save_btn, "primary")
        cancel_btn = wx.Button(self, wx.ID_CANCEL, label=tr("btn_cancel"))
        style_button(cancel_btn, "secondary")
        btn_sizer.AddButton(save_btn)
        btn_sizer.AddButton(cancel_btn)
        btn_sizer.Realize()
        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 12)

        self.SetSizer(sizer)
        self.SetSize((590, 330))

        save_btn.Bind(wx.EVT_BUTTON, self.on_save)

    def on_save(self, event):
        name = self.txt_name.GetValue().strip()
        style = self.txt_style.GetValue().strip()
        if not name:
            announcer.announce("Please enter a preset name.")
            self.txt_name.SetFocus()
            return
        if not style:
            announcer.announce("Please enter a style or delivery instruction.")
            self.txt_style.SetFocus()
            return

        config.add_custom_style(name, style)
        self.created_name = name
        self.created_style = style
        announcer.play_sound("success")
        self.EndModal(wx.ID_OK)


class StylePresetDialog(wx.Dialog):
    """Accessible dialog to pick from pre-tuned emotion and custom style presets (zero unlabeled child panels)."""
    def __init__(self, parent):
        super().__init__(parent, title=tr("dlg_style_title"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.selected_style = None
        self.presets = []
        style_panel(self, accessible_name=tr("dlg_style_title"))
        self._init_ui()
        self.CentreOnParent()

    def _init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        attach_painted_header(
            self,
            sizer,
            title=tr("dlg_style_banner"),
            subtitle=tr("dlg_style_sub"),
            badge_text="STYLE STUDIO"
        )

        info = wx.StaticText(
            self,
            label=tr("dlg_style_info")
        )
        style_label(info, "muted")
        sizer.Add(info, 0, wx.ALL, 12)

        self.listbox = wx.ListBox(self, choices=[], style=wx.LB_SINGLE)
        style_listbox(self.listbox)
        sizer.Add(self.listbox, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        action_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_create_custom = wx.Button(self, label=tr("btn_create_style"))
        self.btn_delete_custom = wx.Button(self, label=tr("btn_delete_custom"))
        style_button(self.btn_create_custom, "gold")
        style_button(self.btn_delete_custom, "danger")
        action_sizer.Add(self.btn_create_custom, 0, wx.RIGHT, 8)
        action_sizer.Add(self.btn_delete_custom, 0)
        sizer.Add(action_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        btn_sizer = wx.StdDialogButtonSizer()
        apply_btn = wx.Button(self, wx.ID_OK, label=tr("btn_apply_style"))
        apply_btn.SetDefault()
        style_button(apply_btn, "primary")
        cancel_btn = wx.Button(self, wx.ID_CANCEL, label=tr("btn_cancel"))
        style_button(cancel_btn, "secondary")
        btn_sizer.AddButton(apply_btn)
        btn_sizer.AddButton(cancel_btn)
        btn_sizer.Realize()
        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 12)

        self.SetSizer(sizer)
        self.SetSize((640, 490))

        self.refresh_presets()

        apply_btn.Bind(wx.EVT_BUTTON, self.on_apply)
        self.listbox.Bind(wx.EVT_LISTBOX_DCLICK, self.on_apply)
        self.listbox.Bind(wx.EVT_LISTBOX, self.on_selection_changed)
        self.btn_create_custom.Bind(wx.EVT_BUTTON, self.on_create_custom)
        self.btn_delete_custom.Bind(wx.EVT_BUTTON, self.on_delete_custom)

    def refresh_presets(self, select_name: str = None):
        self.presets = get_all_style_presets()
        choices = []
        sel_idx = 0
        for idx, item in enumerate(self.presets):
            prefix = "[Custom] " if item.get("is_custom") else ""
            choices.append(f"{prefix}{item['name']} -> \"{item['style']}\"")
            if select_name and item["name"].lower() == select_name.lower():
                sel_idx = idx
        self.listbox.Set(choices)
        if choices:
            self.listbox.SetSelection(sel_idx)
        self._update_delete_button()

    def _update_delete_button(self):
        sel = self.listbox.GetSelection()
        is_custom = (sel != wx.NOT_FOUND and sel < len(self.presets) and bool(self.presets[sel].get("is_custom")))
        self.btn_delete_custom.Enable(is_custom)

    def on_selection_changed(self, event):
        self._update_delete_button()
        event.Skip()

    def on_create_custom(self, event):
        dlg = CreateCustomStyleDialog(self)
        if dlg.ShowModal() == wx.ID_OK and dlg.created_name:
            self.refresh_presets(select_name=dlg.created_name)
            self.listbox.SetFocus()
            announcer.announce(f"Created custom style preset '{dlg.created_name}'.")
        dlg.Destroy()

    def on_delete_custom(self, event):
        sel = self.listbox.GetSelection()
        if sel != wx.NOT_FOUND and sel < len(self.presets) and self.presets[sel].get("is_custom"):
            name = self.presets[sel]["name"]
            config.remove_custom_style(name)
            self.refresh_presets()
            self.listbox.SetFocus()
            announcer.announce(f"Deleted custom style preset '{name}'.")

    def on_apply(self, event):
        sel = self.listbox.GetSelection()
        if sel != wx.NOT_FOUND and sel < len(self.presets):
            self.selected_style = self.presets[sel]["style"]
            self.EndModal(wx.ID_OK)
        else:
            self.EndModal(wx.ID_CANCEL)


# ========================================================================
# WELCOME SCREEN & FIRST-RUN GUIDED SETUP TOUR
# ========================================================================
WELCOME_TOUR_STEPS = {
    "en": [
        {
            "title": "Welcome to Gemvox Studio",
            "body": (
                "Welcome to Gemvox — your accessible desktop studio for Google Gemini 3.8 Flash Text-to-Speech.\n\n"
                "Gemvox is engineered from the ground up for both blind/visually impaired creators (NVDA, JAWS, Narrator) "
                "and sighted audio producers.\n\n"
                "KEY HIGHLIGHTS:\n"
                "  1. Direct Active Screen Reader Output: Zero SAPI 5 voice collisions.\n"
                "  2. 100% Keyboard-Driven: Fast Alt+Mnemonics and Ctrl+1..6 tab switching.\n"
                "  3. Complete Gemini 3.8 Flash TTS Suite: Single Speaker, Multi-Speaker Dialogue, "
                "Voice Design, Voice Replication, and 30+ Studio Voices.\n\n"
                "Press 'Next Step (Alt+N)' to learn how to set up your API Key in 1 minute, or press "
                "'Go to Settings Now (Alt+G)' to configure your studio immediately."
            )
        },
        {
            "title": "Step 1: Configure Your Gemini API Key & Language",
            "body": (
                "Before generating speech, Gemvox requires a Google Gemini API Key:\n\n"
                "HOW TO SET UP YOUR API KEY:\n"
                "  1. Click 'Go to Settings Now (Alt+G)' below (or press Ctrl+6 anytime).\n"
                "  2. In the Settings tab, press 'Get API Key (Alt+G)' to open Google AI Studio in your web browser.\n"
                "  3. Copy your API key and paste it into the 'Gemini API Key (Alt+K)' box.\n"
                "  4. Optional: Press 'Test Connection (Alt+C)' to verify your key.\n"
                "  5. Choose your preferred Interface Language: English (Default) or Thai (ภาษาไทย).\n"
                "  6. Press 'Save Settings (Alt+S)'. Gemvox will offer to restart so your new settings take full effect.\n\n"
                "Note: Your settings are stored persistently, so future updates will never erase your configuration."
            )
        },
        {
            "title": "Step 2: Navigating Tabs & Generating Your First Audio",
            "body": (
                "Once your API key is saved, creating studio-quality speech is effortless:\n\n"
                "HOW TO GENERATE SPEECH:\n"
                "  1. Press Ctrl+1 for Single Speaker TTS or Ctrl+2 for Multi-Speaker Dialogue (or press Alt+T to open the Tabs menu).\n"
                "  2. When switching tabs with Left/Right arrows or Ctrl+1..6, focus stays locked on the Tab header "
                "until you press Tab (or a direct shortcut like Alt+X) to enter the workspace.\n"
                "  3. In Single Speaker TTS, press Alt+X to focus the text box and type your script, optionally press Alt+I "
                "to insert vocal tags (<sigh>, <laugh>, <short pause>), or press Alt+B to pick a delivery style.\n"
                "  4. Press Ctrl+Enter (or Alt+G) to synthesize speech!\n"
                "  5. Press Alt+P to Play/Stop audio, and Ctrl+S to save as a 24kHz WAV file.\n"
                "  6. Press F1 at any time to open the systematic step-by-step User Guide."
            )
        }
    ],
    "th": [
        {
            "title": "ยินดีต้อนรับสู่ Gemvox Studio",
            "body": (
                "ยินดีต้อนรับสู่ Gemvox — สตูดิโอสังเคราะห์เสียงพูด AI ขับเคลื่อนด้วย Google Gemini 3.8 Flash TTS\n\n"
                "โปรแกรมนี้ได้รับการออกแบบให้เข้าถึงได้อย่างสมบูรณ์แบบสำหรับผู้ใช้ Screen Reader (NVDA, JAWS, Narrator) "
                "ควบคู่กับดีไซน์ระดับสตูดิโอที่สวยงามและใช้งานง่ายสำหรับผู้ใช้ทุกคน\n\n"
                "จุดเด่นสำคัญ:\n"
                "  1. ส่งเสียงพูดผ่าน Active Screen Reader โดยตรง: ไม่มีเสียง SAPI 5 มาพูดแทรกหรือตีกัน\n"
                "  2. ควบคุมด้วยคีย์บอร์ดได้ 100%: มีปุ่มลัด Alt+ตัวอักษรครบทุกปุ่มโดยไม่ชนกับเมนูบาร์ และสลับแท็บด้วย Ctrl+1 ถึง 6\n"
                "  3. ครบทุกฟีเจอร์ของ Gemini 3.8 Flash TTS: พูดเดี่ยว, บทสนทนาหลายผู้พูด, ออกแบบเสียงใหม่, "
                "โคลนนิ่งเสียงพูด และคลังเสียงสตูดิโอกว่า 30 เสียง\n\n"
                "กดปุ่ม 'ขั้นตอนถัดไป (Alt+N)' เพื่อดูวิธีตั้งค่าเริ่มต้น หรือกดปุ่ม 'ไปที่หน้าการตั้งค่าทันที (Alt+G)' เพื่อเริ่มตั้งค่าได้เลยครับ"
            )
        },
        {
            "title": "ขั้นตอนที่ 1: การตั้งค่า Gemini API Key และภาษาของโปรแกรม",
            "body": (
                "ก่อนเริ่มสังเคราะห์เสียงพูด กรุณาตั้งค่ารหัสเชื่อมต่อ Gemini API Key ตามขั้นตอนดังนี้:\n\n"
                "วิธีตั้งค่าอย่างเป็นระบบ:\n"
                "  1. กดปุ่ม 'ไปที่หน้าการตั้งค่าทันที (Alt+G)' ด้านล่างนี้ (หรือกด Ctrl+6 ได้ตลอดเวลา)\n"
                "  2. ในหน้าการตั้งค่า กดปุ่ม 'รับรหัส API Key (Alt+G)' เพื่อเปิดหน้าเว็บ Google AI Studio บนเบราว์เซอร์\n"
                "  3. คัดลอก API Key มาวางในช่อง 'รหัส Gemini API Key (Alt+K)'\n"
                "  4. กดปุ่ม 'ทดสอบการเชื่อมต่อ (Alt+C)' เพื่อตรวจสอบความพร้อมใช้งาน\n"
                "  5. เลือกภาษาของโปรแกรม (Interface Language) ระหว่าง English (ค่าเริ่มต้น) หรือ ไทย (Thai)\n"
                "  6. กดปุ่ม 'บันทึกการตั้งค่า (Alt+S)' โปรแกรมจะถามเพื่อรีสตาร์ทให้การตั้งค่ามีผลสมบูรณ์\n\n"
                "หมายเหตุ: ระบบจัดเก็บการตั้งค่าแบบถาวร เมื่ออัปเดตโปรแกรมในอนาคต คุณไม่จำเป็นต้องตั้งค่าใหม่"
            )
        },
        {
            "title": "ขั้นตอนที่ 2: การสำรวจแท็บและเริ่มสังเคราะห์เสียงพูดครั้งแรก",
            "body": (
                "เมื่อตั้งค่า API Key เรียบร้อยแล้ว คุณสามารถสร้างเสียงพูดคุณภาพสูงได้ง่ายๆ ดังนี้:\n\n"
                "ขั้นตอนการใช้งานหลัก:\n"
                "  1. กด Ctrl+1 สำหรับสังเคราะห์เสียงพูดเดี่ยว หรือ Ctrl+2 สำหรับบทสนทนาหลายผู้พูด (หรือกด Alt+T เพื่อเปิดเมนูแท็บ)\n"
                "  2. เมื่อเลื่อนดูแท็บด้วยลูกศรซ้าย/ขวา โฟกัสจะล็อกอยู่บนหัวแท็บก่อนเสมอ เมื่อต้องการเข้าใช้งานจึงค่อยกดปุ่ม Tab (หรือกดคีย์ลัดอย่าง Alt+X เพื่อกระโดดเข้าช่องข้อความทันที)\n"
                "  3. ในหน้าเสียงพูดเดี่ยว กด Alt+X เพื่อเข้าช่องพิมพ์ข้อความ กด Alt+I เพื่อแทรกแท็กเสียงธรรมชาติ (<sigh>, <laugh>, <short pause>) "
                "หรือกด Alt+B เพื่อเลือกพรีเซ็ตอารมณ์เสียง\n"
                "  4. กด Ctrl+Enter (หรือ Alt+G) เพื่อสั่งสังเคราะห์เสียงทันที!\n"
                "  5. กด Alt+P เพื่อเล่นหรือหยุดเสียง และกด Ctrl+S เพื่อบันทึกเป็นไฟล์ WAV\n"
                "  6. กดปุ่ม F1 ได้ตลอดเวลาเพื่อเปิดคู่มือการใช้งานอย่างเป็นระบบ"
            )
        }
    ]
}


class WelcomeTourDialog(wx.Dialog):
    """
    First-run Welcome Screen & Guided Setup Tour.
    Features step-by-step instructions and a direct 'Go to Settings Now (Alt+G)' action.
    Uses painted header so there are zero unlabeled panels.
    """
    ID_GO_SETTINGS = wx.ID_YES

    def __init__(self, parent):
        super().__init__(
            parent,
            title=tr("welcome_title"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        self.steps = WELCOME_TOUR_STEPS.get(config.language, WELCOME_TOUR_STEPS["en"])
        self.current_step = 0
        style_panel(self, accessible_name=tr("welcome_title"))
        self._init_ui()
        self.CentreOnParent()

    def _init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        attach_painted_header(
            self,
            sizer,
            title=tr("welcome_banner_title"),
            subtitle=tr("welcome_banner_sub"),
            badge_text="SETUP TOUR"
        )

        # Step indicator label
        self.lbl_step = wx.StaticText(self, label="")
        style_label(self.lbl_step, "section")
        sizer.Add(self.lbl_step, 0, wx.LEFT | wx.RIGHT | wx.TOP, 14)

        # Read-only RichEdit tour viewer (100% accessible with arrow keys)
        self.txt_body = wx.TextCtrl(
            self,
            value="",
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2
        )
        style_text_ctrl(self.txt_body, multiline=True)
        sizer.Add(self.txt_body, 1, wx.EXPAND | wx.ALL, 14)

        # Navigation & Action Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_prev = wx.Button(self, label=tr("btn_prev_step"))
        self.btn_next = wx.Button(self, label=tr("btn_next_step"))
        self.btn_go_settings = wx.Button(self, self.ID_GO_SETTINGS, label=tr("btn_go_settings"))
        self.btn_go_settings.SetDefault()
        self.btn_close = wx.Button(self, wx.ID_CANCEL, label=tr("btn_skip_tour"))

        style_button(self.btn_prev, "secondary")
        style_button(self.btn_next, "secondary")
        style_button(self.btn_go_settings, "gold")
        style_button(self.btn_close, "primary")

        btn_sizer.Add(self.btn_prev, 0, wx.RIGHT, 8)
        btn_sizer.Add(self.btn_next, 0, wx.RIGHT, 16)
        btn_sizer.AddStretchSpacer(1)
        btn_sizer.Add(self.btn_go_settings, 0, wx.RIGHT, 8)
        btn_sizer.Add(self.btn_close, 0)

        sizer.Add(btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 14)

        self.SetSizer(sizer)
        self.SetSize((740, 520))

        self.btn_prev.Bind(wx.EVT_BUTTON, self.on_prev)
        self.btn_next.Bind(wx.EVT_BUTTON, self.on_next)
        self.btn_go_settings.Bind(wx.EVT_BUTTON, self.on_go_settings)
        self.btn_close.Bind(wx.EVT_BUTTON, self.on_close)

        self._update_step_view(announce_step=False)
        wx.CallAfter(self.txt_body.SetFocus)

    def _update_step_view(self, announce_step: bool = True):
        step_data = self.steps[self.current_step]
        total = len(self.steps)
        header_text = tr(
            "welcome_step_indicator",
            step=self.current_step + 1,
            total=total,
            title=step_data["title"]
        )
        self.lbl_step.SetLabel(header_text)
        self.txt_body.SetValue(step_data["body"])
        style_text_ctrl(self.txt_body, multiline=True)
        self.txt_body.SetInsertionPoint(0)

        self.btn_prev.Enable(self.current_step > 0)
        self.btn_next.Enable(self.current_step < total - 1)

        if announce_step:
            announcer.announce(f"{header_text}. {step_data['body']}")

    def on_prev(self, event):
        if self.current_step > 0:
            self.current_step -= 1
            self._update_step_view(announce_step=True)
            self.txt_body.SetFocus()

    def on_next(self, event):
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self._update_step_view(announce_step=True)
            self.txt_body.SetFocus()

    def on_go_settings(self, event):
        config.set("first_run_completed", True)
        self.EndModal(self.ID_GO_SETTINGS)

    def on_close(self, event):
        config.set("first_run_completed", True)
        self.EndModal(wx.ID_CANCEL)


# ========================================================================
# SYSTEMATIC VISUAL & ACCESSIBLE HELP MODE (F1)
# ========================================================================
HELP_SECTIONS = {
    "en": [
        {
            "title": "1. Quick Start & First-Time Setup",
            "content": (
                "====================================================================\n"
                "1. QUICK START & FIRST-TIME SETUP (STEP-BY-STEP)\n"
                "====================================================================\n\n"
                "Welcome to Gemvox Studio! Follow these 4 steps to start synthesizing speech:\n\n"
                "STEP 1: OBTAIN & SAVE YOUR GEMINI API KEY\n"
                "  1. Press Ctrl+6 to open the 'Settings' tab.\n"
                "  2. Press Alt+G ('Get API Key') to open Google AI Studio in your web browser.\n"
                "  3. Create or copy your API key, then paste it into 'Gemini API Key (Alt+K)'.\n"
                "  4. Press Alt+C ('Test Connection') to verify that your key is active.\n"
                "  5. Press Alt+S ('Save Settings'). Gemvox will prompt to restart so all changes take effect.\n\n"
                "STEP 2: CHOOSE YOUR LANGUAGE & DEFAULTS\n"
                "  * In Settings (Ctrl+6), use 'Interface Language (Alt+L)' to switch between English (Default) "
                "and Thai (ภาษาไทย).\n"
                "  * Choose your preferred Default Model (Flash vs. Flash-Lite) and Default Voice.\n"
                "  * Your configuration is automatically preserved across future app updates.\n\n"
                "STEP 3: GENERATE YOUR FIRST SPEECH\n"
                "  1. Press Ctrl+1 to go to the 'Single Speaker TTS' tab.\n"
                "  2. Press Alt+X to focus the text box and type your message.\n"
                "  3. Press Ctrl+Enter (or Alt+G) to generate speech.\n\n"
                "STEP 4: PLAY & EXPORT WAV AUDIO\n"
                "  * Audio plays automatically upon generation (if Auto-play is enabled).\n"
                "  * Press Alt+P at any time to Play or Stop audio immediately.\n"
                "  * Press Ctrl+S to save the 24kHz WAV audio file to any location."
            )
        },
        {
            "title": "2. Tab Navigation & Screen Reader Architecture",
            "content": (
                "====================================================================\n"
                "2. TAB NAVIGATION & SCREEN READER ARCHITECTURE\n"
                "====================================================================\n\n"
                "Gemvox is designed with zero unlabeled panels and 100% native Win32 accessibility:\n\n"
                "DIRECT ACTIVE SCREEN READER OUTPUT:\n"
                "  * All progress and status announcements are routed directly to your active screen reader "
                "(NVDA via bundled nvdaControllerClient32/64.dll, JAWS via COM API, ZDSR, PC Talker, etc.).\n"
                "  * Windows SAPI 5 fallback is completely removed so voices never clash or overlap.\n\n"
                "HOW TAB CONTROL FOCUS LOCK WORKS:\n"
                "  1. Jump to any of the 6 tabs using Ctrl+1 through Ctrl+6 (or Alt+1 through Alt+6), "
                "or open the Tabs menu with Alt+T.\n"
                "  2. You can also cycle tabs using Ctrl+Tab (Next) and Ctrl+Shift+Tab (Previous).\n"
                "  3. When a tab is selected, focus stays cleanly locked on the Tab Control header.\n"
                "  4. Use Left/Right Arrow keys to browse tabs, then press TAB (or any direct control shortcut "
                "such as Alt+X) when you are ready to enter the controls inside that tab."
            )
        },
        {
            "title": "3. Single Speaker TTS, Styles & Vocal Tags (Ctrl+1)",
            "content": (
                "====================================================================\n"
                "3. SINGLE SPEAKER TTS, STYLES & VOCAL TAGS (CTRL+1)\n"
                "====================================================================\n\n"
                "STEP-BY-STEP WORKFLOW:\n"
                "  1. Focus Text Input (Alt+X): Type or paste the transcript you want spoken verbatim.\n"
                "  2. Insert Inline Vocal Tags (Alt+I): Opens the Vocal Tag Picker dialog.\n"
                "     * Use Up/Down Arrows to choose tags like <short pause>, <long pause>, <sigh>, "
                "<laugh>, <whisper>, <gasp>, or <yawn>.\n"
                "     * Press Enter to insert the tag at your exact cursor position.\n"
                "  3. Select Model (Alt+M) & Voice (Alt+V):\n"
                "     * Choose between Gemini 3.8 Flash TTS (studio fidelity) or Flash-Lite (ultra-fast).\n"
                "     * Press Alt+U ('Audition Voice') to hear a preview of the selected voice.\n"
                "  4. Set Style / Emotion (Alt+Y):\n"
                "     * Type any natural instruction (e.g., 'cheerful and friendly', 'whispered urgently').\n"
                "     * Press Alt+B ('Browse Styles') to pick from curated or custom presets.\n"
                "     * Press Alt+C ('Create Custom Style') to save your own style preset for instant reuse.\n"
                "  5. Generate (Ctrl+Enter / Alt+G): Synthesizes and saves the WAV file automatically."
            )
        },
        {
            "title": "4. Multi-Speaker Conversational Dialogue (Ctrl+2)",
            "content": (
                "====================================================================\n"
                "4. MULTI-SPEAKER CONVERSATIONAL DIALOGUE (CTRL+2)\n"
                "====================================================================\n\n"
                "Create natural multi-person podcasts, interviews, and audiobooks in a single track:\n\n"
                "STEP 1: WRITE OR LOAD A DIALOGUE SCRIPT (Alt+D)\n"
                "  * Format each line as:\n"
                "      SpeakerName: Text to speak [optional style instruction]\n"
                "  * Example:\n"
                "      Joe: Welcome back to our show! [cheerful and warm]\n"
                "      Jane: Thanks Joe! <short pause> Excited to be here. [calm and relaxed]\n"
                "  * Press Alt+I to insert an inline vocal tag at your cursor position.\n"
                "  * Or press Alt+L to load the Podcast Template, or Alt+N for the Interview Template.\n\n"
                "STEP 2: ASSIGN VOICES TO EACH SPEAKER (Alt+K)\n"
                "  * Press Alt+K ('Update Speakers') after editing speaker names in your script.\n"
                "  * Gemvox automatically creates a Voice dropdown for each detected speaker.\n\n"
                "STEP 3: GENERATE DIALOGUE (Ctrl+Enter / Alt+G)\n"
                "  * Press Ctrl+Enter to synthesize the entire conversation into one seamless WAV file."
            )
        },
        {
            "title": "5. Voice Design, Replication & Library (Ctrl+3, 4, 5)",
            "content": (
                "====================================================================\n"
                "5. VOICE DESIGN, VOICE REPLICATION & VOICE LIBRARY\n"
                "====================================================================\n\n"
                "A. VOICE DESIGN STUDIO (Ctrl+3) - CREATE VOICES FROM TEXT PROMPTS:\n"
                "  1. Enter a Voice Name (Alt+N), Gender (Alt+G), and Language Code (Alt+L).\n"
                "  2. In Persona Description Prompt (Alt+D), describe the voice's age, timbre, and accent\n"
                "     (e.g., 'A warm British astronomer in his 60s speaking with quiet wonder').\n"
                "  3. Press Alt+C ('Create Custom Voice'). Gemini generates a persistent Voice ID and sample audio.\n"
                "  4. The new voice is automatically added to your voice selectors across the app.\n\n"
                "B. VOICE REPLICATION (Ctrl+4) - CLONE A VOICE WITH CONSENT:\n"
                "  1. Enter a Voice Name (Alt+N) and select a 10-30s clean 24kHz mono Reference WAV (Alt+R / Alt+B).\n"
                "  2. Press Alt+C ('Copy Statement') to copy the mandatory consent phrase.\n"
                "  3. Select the Consent WAV recording (Alt+S / Alt+W) reciting that exact phrase.\n"
                "  4. Choose Stateful or Stateless mode (Alt+M) and press Alt+V ('Replicate Voice').\n\n"
                "C. VOICE LIBRARY & EXTENDED SEARCH (Ctrl+5):\n"
                "  * Browse all 30 built-in Studio Voices (Alt+B) or search the Extended Library online (Alt+X).\n"
                "  * Press Alt+U (or double-click any voice in the list) to Audition it immediately."
            )
        },
        {
            "title": "6. Complete Keyboard Shortcuts Reference",
            "content": (
                "====================================================================\n"
                "6. COMPLETE KEYBOARD SHORTCUTS REFERENCE (ZERO COLLISIONS)\n"
                "====================================================================\n\n"
                "TOP MENU BAR SHORTCUTS:\n"
                "  * Alt+F : File Menu           |  Alt+E : Edit Menu\n"
                "  * Alt+A : Audio Menu          |  Alt+T : Tabs Menu\n"
                "  * Alt+O : Tools Menu          |  Alt+H : Help Menu\n\n"
                "GLOBAL SHORTCUTS (WORK ANYWHERE):\n"
                "  * Ctrl+Enter          : Generate Speech / Dialogue / Voice Design\n"
                "  * Alt+P               : Play / Stop current audio immediately\n"
                "  * Ctrl+S              : Save current audio as WAV file\n"
                "  * Ctrl+1 .. Ctrl+6    : Switch directly to Tab 1 through Tab 6 (also Alt+1..6)\n"
                "  * Ctrl+Tab            : Switch to Next Tab (also Ctrl+PageDown)\n"
                "  * Ctrl+Shift+Tab      : Switch to Previous Tab (also Ctrl+PageUp)\n"
                "  * F1                  : Open this Systematic User Guide\n"
                "  * Alt+Shift+L         : Clear text field in active tab\n\n"
                "STANDARD WINDOWS TEXT EDITING SHORTCUTS:\n"
                "  * Ctrl+Z / Ctrl+Y     : Undo / Redo text edit\n"
                "  * Ctrl+X / Ctrl+C     : Cut / Copy selected text\n"
                "  * Ctrl+V / Ctrl+A     : Paste / Select All text\n"
                "  * Shift+F10 / AppsKey : Open accessible right-click context menu\n\n"
                "SINGLE-SPEAKER TAB (CTRL+1):\n"
                "  * Alt+X : Focus Text Input      |  Alt+I : Insert Vocal Tag at Cursor\n"
                "  * Alt+L : Clear Text            |  Alt+M : Select Model\n"
                "  * Alt+V : Select Voice          |  Alt+U : Audition Voice\n"
                "  * Alt+Y : Focus Style / Emotion |  Alt+B : Browse Style Presets\n"
                "  * Alt+C : Create Custom Style   |  Alt+G : Generate Speech\n\n"
                "MULTI-SPEAKER TAB (CTRL+2):\n"
                "  * Alt+D : Focus Dialogue Script |  Alt+I : Insert Vocal Tag at Cursor\n"
                "  * Alt+L : Load Podcast Template |  Alt+N : Load Interview Template\n"
                "  * Alt+K : Update Speakers       |  Alt+G : Generate Dialogue\n\n"
                "SETTINGS TAB (CTRL+6):\n"
                "  * Alt+K : Focus API Key         |  Alt+C : Test API Connection\n"
                "  * Alt+G : Get API Key Online    |  Alt+D : Output Folder\n"
                "  * Alt+L : Interface Language    |  Alt+S : Save Settings"
            )
        }
    ],
    "th": [
        {
            "title": "1. เริ่มต้นใช้งานอย่างรวดเร็วและการตั้งค่าครั้งแรก",
            "content": (
                "====================================================================\n"
                "1. เริ่มต้นใช้งานอย่างรวดเร็วและการตั้งค่าครั้งแรก (ทีละขั้นตอน)\n"
                "====================================================================\n\n"
                "ยินดีต้อนรับสู่ Gemvox Studio! ทำตาม 4 ขั้นตอนง่ายๆ เพื่อเริ่มสังเคราะห์เสียงพูด:\n\n"
                "ขั้นตอนที่ 1: การรับและตั้งค่ารหัส GEMINI API KEY\n"
                "  1. กด Ctrl+6 เพื่อเปิดแท็บ 'การตั้งค่า (Settings)'\n"
                "  2. กดปุ่ม Alt+G ('รับรหัส API Key') เพื่อเปิดเว็บ Google AI Studio บนเบราว์เซอร์ของคุณ\n"
                "  3. คัดลอก API Key มาวางลงในช่อง 'รหัส Gemini API Key (Alt+K)'\n"
                "  4. กดปุ่ม Alt+C ('ทดสอบการเชื่อมต่อ') เพื่อตรวจสอบว่าคีย์ใช้งานได้ปกติ\n"
                "  5. กดปุ่ม Alt+S ('บันทึกการตั้งค่า') โปรแกรมจะถามเพื่อรีสตาร์ทให้การตั้งค่ามีผลสมบูรณ์\n\n"
                "ขั้นตอนที่ 2: การเลือกภาษาและค่าเริ่มต้นของโปรแกรม\n"
                "  * ในหน้าการตั้งค่า (Ctrl+6) กด Alt+L เพื่อเลือกภาษาของโปรแกรมระหว่าง English (ค่าเริ่มต้น) หรือ ไทย (Thai)\n"
                "  * เลือกโมเดลเริ่มต้นและเสียงพูดเริ่มต้นที่คุณชื่นชอบ\n"
                "  * ข้อมูลการตั้งค่าทั้งหมดจะถูกเก็บไว้อย่างเป็นระบบ เมื่ออัปเดตเวอร์ชันใหม่ไม่ต้องตั้งค่าซ้ำ\n\n"
                "ขั้นตอนที่ 3: การสังเคราะห์เสียงพูดครั้งแรก\n"
                "  1. กด Ctrl+1 เพื่อไปที่แท็บ 'สังเคราะห์เสียงพูดเดี่ยว'\n"
                "  2. กด Alt+X เพื่อเข้าสู่ช่องพิมพ์ข้อความ แล้วพิมพ์ประโยคที่ต้องการ\n"
                "  3. กด Ctrl+Enter (หรือ Alt+G) เพื่อสั่งสังเคราะห์เสียงทันที!\n\n"
                "ขั้นตอนที่ 4: การเล่นและบันทึกไฟล์เสียง WAV\n"
                "  * กด Alt+P ได้ตลอดเวลาเพื่อ เล่น (Play) หรือ หยุด (Stop) เสียงทันที\n"
                "  * กด Ctrl+S เพื่อบันทึกไฟล์เสียง WAV (24kHz) เก็บไว้ในโฟลเดอร์ที่ต้องการ"
            )
        },
        {
            "title": "2. การสลับแท็บและการทำงานร่วมกับ Screen Reader",
            "content": (
                "====================================================================\n"
                "2. การสลับแท็บและการทำงานร่วมกับ SCREEN READER\n"
                "====================================================================\n\n"
                "Gemvox ออกแบบให้ปราศจาก Unlabeled Panel 100% เพื่อความรวดเร็วในการใช้งาน:\n\n"
                "การส่งเสียงพูดตรงเข้า ACTIVE SCREEN READER:\n"
                "  * ทุกข้อความแจ้งเตือนสถานะจะถูกส่งตรงไปยัง Screen Reader ที่เปิดใช้งานอยู่โดยตรง "
                "(เช่น NVDA ผ่าน nvdaControllerClient32/64.dll ที่แนบมากับโปรแกรม, JAWS ผ่าน COM API, ZDSR ฯลฯ)\n"
                "  * ตัดการทำงานของ SAPI 5 ออกทั้งหมด ทำให้ไม่มีเสียงพูดซ้อนทับหรือตีกัน\n\n"
                "ระบบล็อกโฟกัสบนหัวแท็บ (TAB CONTROL FOCUS LOCK):\n"
                "  1. กด Ctrl+1 ถึง Ctrl+6 (หรือ Alt+1 ถึง Alt+6) เพื่อสลับไปยังแท็บที่ 1 ถึง 6 ได้ทันที (หรือกด Alt+T เพื่อเปิดเมนูแท็บ)\n"
                "  2. หรือกด Ctrl+Tab (แท็บถัดไป) และ Ctrl+Shift+Tab (แท็บก่อนหน้า)\n"
                "  3. เมื่อสลับแท็บ โฟกัสจะถูกล็อกไว้ที่หัวแท็บ (Tab Control) ก่อนเสมอ ไม่กระโดดเข้าข้างในเอง\n"
                "  4. คุณสามารถกดลูกศรซ้าย/ขวาเพื่อสำรวจชื่อแท็บ และเมื่อต้องการเข้าใช้งานจึงค่อยกดปุ่ม Tab (หรือกดคีย์ลัดของคอนโทรล เช่น Alt+X ได้ทันที)"
            )
        },
        {
            "title": "3. สังเคราะห์เสียงเดี่ยว อารมณ์เสียง และแท็กเสียง (Ctrl+1)",
            "content": (
                "====================================================================\n"
                "3. สังเคราะห์เสียงเดี่ยว อารมณ์เสียง และแท็กเสียง (CTRL+1)\n"
                "====================================================================\n\n"
                "ลำดับขั้นตอนการใช้งานอย่างละเอียด:\n"
                "  1. ช่องพิมพ์ข้อความ (Alt+X): พิมพ์หรือวางบทพูดที่ต้องการให้อ่านตามตัวอักษร\n"
                "  2. แทรกแท็กเสียงธรรมชาติ (Alt+I): เปิดหน้าต่างเลือก Vocal Tag\n"
                "     * กดลูกศรขึ้น/ลง เพื่อเลือกแท็ก เช่น <short pause> (หยุดสั้นๆ), <long pause> (หยุดยาว),\n"
                "       <sigh> (ถอนหายใจ), <laugh> (หัวเราะ), <whisper> (กระซิบ), หรือ <yawn> (หาว)\n"
                "     * กด Enter เพื่อแทรกแท็กลงตรงตำแหน่งเคอร์เซอร์เดิมอย่างแม่นยำ 100%\n"
                "  3. เลือกโมเดล (Alt+M) และเสียงพูด (Alt+V):\n"
                "     * เลือกโมเดล Flash (คุณภาพระดับสตูดิโอ) หรือ Flash-Lite (ประมวลผลไวพิเศษ)\n"
                "     * กดปุ่ม Alt+U ('ทดลองฟังเสียง') เพื่อฟังตัวอย่างเสียงที่เลือกอยู่\n"
                "  4. กำหนดอารมณ์ / สไตล์การพูด (Alt+Y):\n"
                "     * พิมพ์คำสั่งอารมณ์ได้อิสระ หรือกด Alt+B ('เลือกสไตล์') เพื่อเลือกจากรายการพรีเซ็ต\n"
                "     * กด Alt+C ('สร้างสไตล์ส่วนตัว') เพื่อบันทึกสไตล์ที่ใช้บ่อยเก็บไว้ใช้ซ้ำโดยไม่ต้องพิมพ์ใหม่\n"
                "  5. สังเคราะห์เสียง (Ctrl+Enter / Alt+G): ประมวลผลและเล่นเสียงอัตโนมัติ"
            )
        },
        {
            "title": "4. การสร้างบทสนทนาหลายผู้พูด (Ctrl+2)",
            "content": (
                "====================================================================\n"
                "4. การสร้างบทสนทนาหลายผู้พูด (MULTI-SPEAKER DIALOGUE - CTRL+2)\n"
                "====================================================================\n\n"
                "สร้างพอดแคสต์ รายการสัมภาษณ์ หรือละครเสียงที่มีผู้พูดโต้ตอบกันหลายคนในไฟล์เดียว:\n\n"
                "ขั้นตอนที่ 1: เขียนหรือโหลดสคริปต์บทสนทนา (Alt+D)\n"
                "  * พิมพ์แต่ละบรรทัดในรูปแบบ:\n"
                "      ชื่อผู้พูด: ข้อความที่ต้องการให้พูด [อารมณ์เสียงเพิ่มเติม]\n"
                "  * ตัวอย่าง:\n"
                "      Joe: ยินดีต้อนรับทุกท่านเข้าสู่พอดแคสต์ของเราครับ! [cheerful and warm]\n"
                "      Jane: ขอบคุณค่ะคุณโจ <short pause> วันนี้เรามีเรื่องน่าตื่นเต้นมาคุยกันค่ะ [calm]\n"
                "  * กด Alt+I เพื่อแทรกแท็กเสียงธรรมชาติลงในตำแหน่งเคอร์เซอร์\n"
                "  * หรือกด Alt+L เพื่อโหลดเทมเพลตพอดแคสต์ และ Alt+N เพื่อโหลดเทมเพลตสัมภาษณ์\n\n"
                "ขั้นตอนที่ 2: จับคู่เสียงให้ผู้พูดแต่ละคน (Alt+K)\n"
                "  * เมื่อพิมพ์สคริปต์เสร็จ กดปุ่ม Alt+K ('อัปเดตรายชื่อผู้พูด')\n"
                "  * โปรแกรมจะสร้างช่องเลือกเสียง (Dropdown) แยกตามรายชื่อตัวละครในสคริปต์ให้อัตโนมัติ\n\n"
                "ขั้นตอนที่ 3: สังเคราะห์บทสนทนา (Ctrl+Enter / Alt+G)\n"
                "  * กด Ctrl+Enter เพื่อรวมเสียงสนทนาของทุกตัวละครออกมาเป็นไฟล์ WAV ไฟล์เดียวอย่างเป็นธรรมชาติ"
            )
        },
        {
            "title": "5. ออกแบบเสียงใหม่ โคลนเสียง และคลังเสียง (Ctrl+3, 4, 5)",
            "content": (
                "====================================================================\n"
                "5. ออกแบบเสียงใหม่ • โคลนนิ่งเสียงพูด • คลังเสียงสตูดิโอ\n"
                "====================================================================\n\n"
                "ก. ออกแบบเสียงใหม่จากคำบรรยาย (Voice Design Studio - Ctrl+3):\n"
                "  1. ตั้งชื่อเสียงพูด (Alt+N) เลือกเพศ (Alt+G) และรหัสภาษา (Alt+L)\n"
                "  2. พิมพ์คำบรรยายบุคลิกเสียงในช่อง Prompt (Alt+D) เช่น อายุ โทนเสียง สำเนียงการพูด\n"
                "  3. กดปุ่ม Alt+C ('สร้างเสียงพูดใหม่') ระบบจะสร้างรหัส Voice ID ถาวรพร้อมเสียงตัวอย่าง\n"
                "  4. เสียงที่สร้างเสร็จจะถูกบันทึกเข้าสู่รายการเลือกเสียงในทุกแท็บโดยอัตโนมัติ\n\n"
                "ข. โคลนนิ่งเสียงพูด (Voice Replication - Ctrl+4):\n"
                "  1. ตั้งชื่อเสียง (Alt+N) และเลือกไฟล์เสียงอ้างอิง WAV 24kHz ความยาว 10-30 วินาที (Alt+R / Alt+B)\n"
                "  2. กดปุ่ม Alt+C ('คัดลอกประโยค') เพื่อดูประโยคยืนยันสิทธิ์มาตรฐาน\n"
                "  3. เลือกไฟล์เสียง WAV ที่เจ้าของเสียงอ่านประโยคยืนยันสิทธิ์นั้น (Alt+S / Alt+W)\n"
                "  4. เลือกโหมดการจัดเก็บ (Alt+M) แล้วกดปุ่ม Alt+V ('โคลนนิ่งเสียงพูด')\n\n"
                "ค. คลังเสียงและการค้นหาออนไลน์ (Voice Library - Ctrl+5):\n"
                "  * แสดงรายชื่อ 30 เสียงสตูดิโอมาตรฐาน (Alt+B) หรือค้นหาจากคลังออนไลน์ (Alt+X)\n"
                "  * กดปุ่ม Alt+U (หรือกดดับเบิลคลิก) เพื่อทดลองฟังเสียงตัวอย่างได้ทันที"
            )
        },
        {
            "title": "6. ตารางสรุปคีย์ลัดทั้งหมด (Keyboard Shortcuts)",
            "content": (
                "====================================================================\n"
                "6. ตารางสรุปคีย์ลัดทั้งหมด (ไร้การชนกับเมนูบาร์ 100%)\n"
                "====================================================================\n\n"
                "คีย์ลัดเมนูบาร์ด้านบน (TOP MENU BAR):\n"
                "  * Alt+F : เมนูไฟล์ (File)        |  Alt+E : เมนูแก้ไข (Edit)\n"
                "  * Alt+A : เมนูเสียง (Audio)      |  Alt+T : เมนูแท็บ (Tabs)\n"
                "  * Alt+O : เมนูเครื่องมือ (Tools)  |  Alt+H : เมนูช่วยเหลือ (Help)\n\n"
                "คีย์ลัดระดับ GLOBAL (กดใช้งานได้จากทุกหน้า):\n"
                "  * Ctrl+Enter          : สั่งสังเคราะห์เสียงพูด / บทสนทนา / ออกแบบเสียง\n"
                "  * Alt+P               : เล่นเสียง / หยุดเสียงทันที (Non-blocking)\n"
                "  * Ctrl+S              : บันทึกไฟล์เสียงปัจจุบันเป็นไฟล์ WAV\n"
                "  * Ctrl+1 ถึง Ctrl+6    : สลับไปยังแท็บที่ 1 ถึง 6 โดยตรง (หรือกด Alt+1 ถึง 6)\n"
                "  * Ctrl+Tab            : เลื่อนไปแท็บถัดไป (หรือ Ctrl+PageDown)\n"
                "  * Ctrl+Shift+Tab      : เลื่อนไปแท็บก่อนหน้า (หรือ Ctrl+PageUp)\n"
                "  * F1                  : เปิดหน้าต่างคู่มือการใช้งานอย่างเป็นระบบนี้\n"
                "  * Alt+Shift+L         : ล้างข้อความในช่องพิมพ์ของแท็บปัจจุบัน\n\n"
                "คีย์ลัดจัดการข้อความมาตรฐาน WINDOWS:\n"
                "  * Ctrl+Z / Ctrl+Y     : เลิกทำ (Undo) / ทำซ้ำ (Redo)\n"
                "  * Ctrl+X / Ctrl+C     : ตัด (Cut) / คัดลอก (Copy)\n"
                "  * Ctrl+V / Ctrl+A     : วาง (Paste) / เลือกทั้งหมด (Select All)\n"
                "  * Shift+F10 / AppsKey : เปิดเมนูบริบท (Context Menu)\n\n"
                "คีย์ลัดในแท็บสังเคราะห์เสียงเดี่ยว (CTRL+1):\n"
                "  * Alt+X : ช่องพิมพ์ข้อความ      |  Alt+I : แทรกแท็กเสียงตรงเคอร์เซอร์\n"
                "  * Alt+L : ล้างข้อความ          |  Alt+M : เลือกโมเดล\n"
                "  * Alt+V : เลือกเสียงพูด         |  Alt+U : ทดลองฟังเสียง\n"
                "  * Alt+Y : ช่องกำหนดอารมณ์/สไตล์ |  Alt+B : เลือกพรีเซ็ตสไตล์\n"
                "  * Alt+C : สร้างสไตล์ส่วนตัว     |  Alt+G : สังเคราะห์เสียงพูด\n\n"
                "คีย์ลัดในแท็บบทสนทนาหลายผู้พูด (CTRL+2):\n"
                "  * Alt+D : ช่องสคริปต์บทสนทนา   |  Alt+I : แทรกแท็กเสียงตรงเคอร์เซอร์\n"
                "  * Alt+L : โหลดเทมเพลตพอดแคสต์  |  Alt+N : โหลดเทมเพลตสัมภาษณ์\n"
                "  * Alt+K : อัปเดตรายชื่อผู้พูด     |  Alt+G : สังเคราะห์บทสนทนา\n\n"
                "คีย์ลัดในแท็บการตั้งค่า (CTRL+6):\n"
                "  * Alt+K : ช่องใส่ API Key      |  Alt+C : ทดสอบการเชื่อมต่อ\n"
                "  * Alt+G : รับรหัส API Key      |  Alt+D : โฟลเดอร์บันทึกเสียง\n"
                "  * Alt+L : เลือกภาษาโปรแกรม     |  Alt+S : บันทึกการตั้งค่า"
            )
        }
    ]
}


class HelpDialog(wx.Dialog):
    """
    Systematic Step-by-Step User Guide & Visual Help Mode (F1).
    Features a clean Master-Detail split layout:
    - Left: Topic ListBox (Alt+T) for instant chapter jumping.
    - Right: RichEdit2 Step-by-Step Guide Viewer (Alt+G) for detailed reading.
    - Painted top header banner with 0 unlabeled panels.
    """
    def __init__(self, parent):
        super().__init__(
            parent,
            title=tr("help_title"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        self.sections = HELP_SECTIONS.get(config.language, HELP_SECTIONS["en"])
        style_panel(self, accessible_name=tr("help_title"))
        self._init_ui()
        self.CentreOnParent()

    def _init_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        attach_painted_header(
            self,
            main_sizer,
            title=tr("help_banner_title"),
            subtitle=tr("help_banner_sub"),
            badge_text="F1 USER GUIDE"
        )

        # Master-Detail Split Area
        split_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Left column: Topics ListBox
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        lbl_topics = wx.StaticText(self, label=tr("help_topics_label"))
        style_label(lbl_topics, "section")
        left_sizer.Add(lbl_topics, 0, wx.BOTTOM, 6)

        topic_titles = [s["title"] for s in self.sections]
        self.list_topics = wx.ListBox(self, choices=topic_titles, style=wx.LB_SINGLE, size=(270, -1))
        style_listbox(self.list_topics)
        left_sizer.Add(self.list_topics, 1, wx.EXPAND)
        split_sizer.Add(left_sizer, 0, wx.EXPAND | wx.RIGHT, 12)

        # Right column: Detailed Guide Content
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        lbl_content = wx.StaticText(self, label=tr("help_content_label"))
        style_label(lbl_content, "section")
        right_sizer.Add(lbl_content, 0, wx.BOTTOM, 6)

        self.txt_content = wx.TextCtrl(
            self,
            value="",
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2
        )
        style_text_ctrl(self.txt_content, multiline=True, mono=True)
        right_sizer.Add(self.txt_content, 1, wx.EXPAND)
        split_sizer.Add(right_sizer, 1, wx.EXPAND)

        main_sizer.Add(split_sizer, 1, wx.EXPAND | wx.ALL, 14)

        # Bottom action bar
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_tour = wx.Button(self, label=tr("btn_open_tour"))
        style_button(btn_tour, "gold")
        close_btn = wx.Button(self, wx.ID_CANCEL, label=tr("btn_close"))
        close_btn.SetDefault()
        style_button(close_btn, "primary")

        btn_sizer.Add(btn_tour, 0, wx.RIGHT, 10)
        btn_sizer.AddStretchSpacer(1)
        btn_sizer.Add(close_btn, 0)
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 14)

        self.SetSizer(main_sizer)
        self.SetSize((860, 620))

        self.list_topics.Bind(wx.EVT_LISTBOX, self.on_topic_selected)
        btn_tour.Bind(wx.EVT_BUTTON, self.on_open_tour)

        if topic_titles:
            self.list_topics.SetSelection(0)
            self._load_section(0, announce=False)

        wx.CallAfter(self.list_topics.SetFocus)

    def _load_section(self, idx: int, announce: bool = False):
        if 0 <= idx < len(self.sections):
            sec = self.sections[idx]
            self.txt_content.SetValue(sec["content"])
            style_text_ctrl(self.txt_content, multiline=True, mono=True)
            self.txt_content.SetInsertionPoint(0)
            if announce:
                announcer.announce(sec["title"])

    def on_topic_selected(self, event):
        sel = self.list_topics.GetSelection()
        if sel != wx.NOT_FOUND:
            self._load_section(sel, announce=True)
        event.Skip()

    def on_open_tour(self, event):
        dlg = WelcomeTourDialog(self)
        res = dlg.ShowModal()
        dlg.Destroy()
        if res == WelcomeTourDialog.ID_GO_SETTINGS:
            self.EndModal(WelcomeTourDialog.ID_GO_SETTINGS)
