from gemvox.config import config

TRANSLATIONS = {
    "en": {
        # Main Window & Menus
        "app_title": "Gemvox {version} - Accessible Gemini 3.8 Flash TTS Studio",
        "banner_title": "GEMVOX  \u2022  AI VOICE & SPEECH STUDIO",
        "banner_subtitle": "Luxury Accessible Production Suite for Google Gemini 3.8 Flash TTS  |  Press F1 for Guided Help",
        "banner_badge": "VERSION {version}  \u2022  OBSIDIAN EDITION",
        "app_opened_announce": "Gemvox {version} opened. Ready to generate speech.",
        "status_ready_main": "Ready. Press Ctrl+Enter to synthesize.",
        "status_engine": "Engine: Gemini 3.8 Flash TTS (24kHz PCM)",
        "status_sr_mode": "Screen Reader Direct Mode",
        "tab_selected_announce": "{name} tab selected",

        # Tab Names
        "tab_single": "Single Speaker TTS",
        "tab_multi": "Multi-Speaker Dialogue",
        "tab_design": "Voice Design Studio",
        "tab_replication": "Voice Replication",
        "tab_library": "Voice Library",
        "tab_settings": "Settings",

        # Menus
        "menu_file": "&File",
        "menu_save_audio": "&Save Audio As...\tCtrl+S",
        "menu_save_audio_help": "Save the current audio file",
        "menu_exit": "E&xit\tAlt+F4",
        "menu_exit_help": "Exit Gemvox",

        "menu_edit": "&Edit",
        "menu_undo": "&Undo\tCtrl+Z",
        "menu_redo": "&Redo\tCtrl+Y",
        "menu_cut": "Cu&t\tCtrl+X",
        "menu_copy": "&Copy\tCtrl+C",
        "menu_paste": "&Paste\tCtrl+V",
        "menu_delete": "&Delete\tDel",
        "menu_select_all": "Select &All\tCtrl+A",
        "menu_clear_field": "C&lear Text Field\tAlt+Shift+L",

        "menu_audio": "&Audio",
        "menu_play_stop": "&Play / Stop Audio\tAlt+P",

        "menu_tabs": "&Tabs",
        "menu_tab1": "1. &Single Speaker TTS\tCtrl+1",
        "menu_tab2": "2. &Multi-Speaker Dialogue\tCtrl+2",
        "menu_tab3": "3. Voice &Design Studio\tCtrl+3",
        "menu_tab4": "4. Voice &Replication\tCtrl+4",
        "menu_tab5": "5. Voice &Library\tCtrl+5",
        "menu_tab6": "6. S&ettings & API Key\tCtrl+6",
        "menu_next_tab": "&Next Tab\tCtrl+Tab",
        "menu_prev_tab": "&Previous Tab\tCtrl+Shift+Tab",

        "menu_tools": "T&ools",
        "menu_insert_tag": "&Insert Vocal Tag...\tAlt+I",
        "menu_browse_style": "&Browse Style Presets...\tAlt+B",
        "menu_create_style": "&Create Custom Style Preset...\tAlt+C",
        "menu_welcome_tour": "&Welcome Tour & Setup Wizard...",

        "menu_help": "&Help",
        "menu_help_guide": "&User Guide & Shortcuts\tF1",
        "menu_about": "&About Gemvox",

        # Single Speaker Panel
        "ss_text_label": "Te&xt to speak (Alt+X):",
        "ss_default_text": "Hello! Welcome to Gemvox, your accessible Gemini 3.8 Flash text-to-speech studio.",
        "btn_insert_tag_i": "&Insert Vocal Tag... (Alt+I)",
        "btn_clear_text": "C&lear Text (Alt+L)",
        "ss_box_params": "Voice & Delivery Parameters",
        "lbl_model": "&Model (Alt+M):",
        "lbl_voice": "&Voice (Alt+V):",
        "btn_audition_u": "A&udition Voice (Alt+U)",
        "lbl_style": "St&yle / Emotion (Alt+Y):",
        "btn_browse_styles": "&Browse Styles... (Alt+B)",
        "btn_create_style": "&Create Custom Style... (Alt+C)",
        "btn_generate_speech": "&Generate Speech (Ctrl+Enter / Alt+G)",
        "btn_play_audio": "&Play Audio (Alt+P)",
        "btn_stop_audio": "Stop Audio (Alt+&P)",
        "btn_save_audio": "&Save Audio As... (Ctrl+S / Alt+S)",
        "status_ready": "Status: Ready.",
        "msg_enter_text": "Please enter text to speak.",
        "msg_text_cleared": "Text cleared.",
        "msg_no_audio_save": "No audio available to save.",

        # Multi-Speaker Panel
        "ms_script_label": "&Dialogue Script (Alt+D) - (Format: Speaker: Text [optional style]):",
        "btn_insert_tag_t": "&Insert Vocal Tag... (Alt+I)",
        "btn_load_podcast": "&Load Podcast Template (Alt+L)",
        "btn_load_interview": "Load I&nterview Template (Alt+N)",
        "btn_update_speakers": "Update Spea&kers (Alt+K)",
        "ms_box_mapping": "Speaker Voice Assignments",
        "lbl_voice_for": "Voice for '{speaker}':",
        "btn_generate_dialogue": "&Generate Dialogue (Ctrl+Enter / Alt+G)",
        "msg_enter_script": "Please enter a dialogue script.",
        "msg_script_cleared": "Dialogue script cleared.",

        # Voice Design Panel
        "vd_info": "Voice Design lets you create a brand-new vocal persona by describing age, timbre,\naccent, and delivery. Gemini returns a persistent Voice ID and sample audio preview.",
        "vd_box_specs": "Vocal Persona Specifications",
        "lbl_voice_name": "Voice &Name (Alt+N):",
        "lbl_gender": "&Gender (Alt+G):",
        "lbl_lang_code": "&Language Code (Alt+L):",
        "lbl_persona_prompt": "Persona &Description Prompt (Alt+D):",
        "btn_sample_astronomer": "Sample: Astronomer",
        "btn_sample_educator": "Sample: Tech Educator",
        "btn_sample_fantasy": "Sample: Fantasy Narrator",
        "btn_create_voice": "&Create Custom Voice (Alt+C)",
        "btn_play_preview": "&Play Sample Preview (Alt+P)",
        "btn_stop_preview": "Stop Sample &Preview (Alt+P)",
        "btn_copy_id_y": "Cop&y Voice ID (Alt+Y)",
        "btn_save_preview_wav": "&Save Preview WAV (Alt+S)",
        "lbl_voice_id_none": "Voice ID: None generated yet.",

        # Voice Replication Panel
        "vr_info": "Voice Replication requires two clean 24kHz mono WAV recordings from the same adult speaker:\n1. Reference audio (10 to 30 seconds of natural speech).\n2. Consent audio clearly reciting the required consent phrase.",
        "vr_box_cloning": "Voice Cloning & Consent Verification",
        "lbl_ref_audio": "&Reference Audio File (Alt+R):",
        "btn_browse_ref": "&Browse Reference... (Alt+B)",
        "lbl_consent_phrase": "Mandatory Consent Phrase:",
        "btn_copy_statement": "&Copy Statement (Alt+C)",
        "lbl_con_audio": "Con&sent Audio File (Alt+S):",
        "btn_browse_con": "Bro&wse Consent... (Alt+W)",
        "lbl_storage_mode": "Storage &Mode (Alt+M):",
        "mode_stateful": "Stateful (Project ID, recommended)",
        "mode_stateless": "Stateless (Client Key)",
        "btn_replicate": "Replicate &Voice (Alt+V)",

        # Voice Library Panel
        "vl_info": "Browse the 30 featured Gemini studio voices or query the Extended Voice Library online:",
        "vl_box_filters": "Catalog Search & Acoustic Filters",
        "lbl_search_query": "&Search Query (Alt+S):",
        "lbl_language": "&Language (Alt+L):",
        "lbl_gender_g": "&Gender (Alt+G):",
        "lbl_domain": "Context &Domain (Alt+D):",
        "btn_search_online": "Search E&xtended Library Online (Alt+X)",
        "btn_show_prebuilt": "Show 30 &Built-in Studio Voices (Alt+B)",
        "lbl_voices_list": "&Voices List (Alt+V):",
        "btn_audition_a": "A&udition Voice (Alt+U)",
        "btn_copy_id_c": "&Copy Voice ID (Alt+C)",

        # Settings Panel
        "set_info": "Configure your Gemini API Key, interface language, studio defaults, and screen reader options:",
        "set_box_cred": "API Credentials, Language & Studio Defaults",
        "lbl_api_key": "Gemini API &Key (Alt+K):",
        "btn_test_conn": "Test &Connection (Alt+C)",
        "btn_get_key": "&Get API Key (Alt+G)",
        "lbl_output_folder": "Output Fol&der (Alt+D):",
        "btn_browse_out": "Bro&wse Output... (Alt+W)",
        "lbl_def_model": "Default &Model (Alt+M):",
        "lbl_def_voice": "Default &Voice (Alt+V):",
        "lbl_ui_language": "Interface &Language (Alt+L):",
        "lang_en": "English (Default)",
        "lang_th": "ไทย (Thai)",
        "set_box_acc": "Accessibility & Audio Feedback",
        "chk_announcements": "Enable Spoken Status Announcements (Active Screen &Reader) (Alt+R)",
        "chk_beeps": "Enable Auditory Sound Cues (&Beeps) (Alt+B)",
        "chk_autoplay": "A&uto-play speech immediately upon generation (Alt+U)",
        "btn_save_settings": "&Save Settings (Alt+S)",
        "msg_settings_saved": "Settings saved successfully.",
        "restart_prompt_title": "Restart Required",
        "restart_prompt_msg": "Your settings have been saved.\n\nGemvox needs to restart for all changes to take full effect.\nWould you like to restart Gemvox now?",

        # Dialogs
        "dlg_tag_title": "Insert Vocal Tag",
        "dlg_tag_banner_title": "INSERT VOCAL TAG",
        "dlg_tag_banner_sub": "Precision inline non-speech cues and breathing pauses",
        "dlg_tag_info": "Select an inline vocal tag to insert at your cursor position:\n(Arrow up and down, then press Enter or click Insert)",
        "btn_insert": "&Insert Tag",
        "btn_cancel": "&Cancel",

        "dlg_custom_style_title": "Create Your Own Custom Style Preset",
        "dlg_custom_style_banner": "CREATE CUSTOM STYLE PRESET",
        "dlg_custom_style_sub": "Save your favorite delivery instructions for instant reuse",
        "dlg_custom_style_info": "Create a reusable custom style preset so you don't have to type instructions repeatedly.\nOnce saved, it will automatically appear in Browse Styles.",
        "lbl_preset_name": "Preset &Name (Alt+N):",
        "lbl_preset_style": "&Style / Delivery Instruction (Alt+S):",
        "btn_save_preset": "&Save Custom Preset",

        "dlg_style_title": "Select Style Preset",
        "dlg_style_banner": "STYLE & EMOTION PRESETS",
        "dlg_style_sub": "Curated & custom vocal delivery styles for Gemini 3.8 Flash TTS",
        "dlg_style_info": "Choose a custom or built-in style preset to guide pace, tone, and emotion:",
        "btn_delete_custom": "&Delete Custom Style (Alt+D)",
        "btn_apply_style": "&Apply Style",

        # Welcome Tour Dialog
        "welcome_title": "Welcome to Gemvox Studio - Quick Setup Tour",
        "welcome_banner_title": "WELCOME TO GEMVOX STUDIO",
        "welcome_banner_sub": "Accessible Gemini 3.8 Flash TTS Production Suite  |  First-Time Guided Tour",
        "welcome_step_indicator": "Step {step} of {total}: {title}",
        "btn_prev_step": "< &Previous (Alt+P)",
        "btn_next_step": "&Next Step (Alt+N) >",
        "btn_go_settings": "&Go to Settings Now (Alt+G)",
        "btn_skip_tour": "&Start Using Gemvox (Esc)",

        # Help Dialog
        "help_title": "Gemvox User Guide & Keyboard Shortcuts (F1)",
        "help_banner_title": "GEMVOX STUDIO  \u2022  SYSTEMATIC USER GUIDE",
        "help_banner_sub": "Select a topic on the left (Up/Down Arrows) and press Tab to read the detailed guide",
        "help_topics_label": "Guide &Topics (Alt+T):",
        "help_content_label": "Detailed &Guide Content (Alt+G):",
        "btn_open_tour": "Open &Welcome Tour (Alt+W)",
        "btn_close": "&Close (Alt+C)",
    },

    "th": {
        # =====================================================================
        # STANDARD ENGLISH MNEMONICS IN THAI MODE:
        # Every '&' mnemonic is placed strictly before the exact same English
        # character as in English mode so Alt+Key shortcuts remain 100%
        # identical regardless of whether the UI is in English or Thai.
        # =====================================================================

        # Main Window & Menus
        "app_title": "Gemvox {version} - สตูดิโอสังเคราะห์เสียงพูด Gemini 3.8 Flash TTS เพื่อการเข้าถึง",
        "banner_title": "GEMVOX  \u2022  สตูดิโอสังเคราะห์เสียงพูด AI ระดับมืออาชีพ",
        "banner_subtitle": "ชุดโปรแกรมสร้างเสียงพูด Google Gemini 3.8 Flash TTS  |  กด F1 เพื่อเปิดคู่มือการใช้งาน",
        "banner_badge": "เวอร์ชัน {version}  \u2022  OBSIDIAN EDITION",
        "app_opened_announce": "เปิดโปรแกรม Gemvox {version} พร้อมสังเคราะห์เสียงพูด",
        "status_ready_main": "พร้อมทำงาน กด Ctrl+Enter เพื่อสังเคราะห์เสียง",
        "status_engine": "เอนจิน: Gemini 3.8 Flash TTS (24kHz PCM)",
        "status_sr_mode": "โหมดเชื่อมต่อ Screen Reader โดยตรง",
        "tab_selected_announce": "เลือกแท็บ {name}",

        # Tab Names
        "tab_single": "สังเคราะห์เสียงพูดเดี่ยว",
        "tab_multi": "บทสนทนาหลายผู้พูด",
        "tab_design": "ออกแบบเสียงใหม่",
        "tab_replication": "โคลนนิ่งเสียงพูด",
        "tab_library": "คลังเสียงและค้นหา",
        "tab_settings": "การตั้งค่า",

        # Menus (English Mnemonics preserved: &F, &S, &x, &E, &U, &R, &t, &C, &P, &D, &A, &l, &T, &1..&6, &N, &o, &I, &B, &W, &H)
        "menu_file": "ไฟล์ (&File)",
        "menu_save_audio": "บันทึกเสียงเป็น (&Save)...\tCtrl+S",
        "menu_save_audio_help": "บันทึกไฟล์เสียงปัจจุบันลงคอมพิวเตอร์",
        "menu_exit": "ออกจากโปรแกรม (E&xit)\tAlt+F4",
        "menu_exit_help": "ปิดโปรแกรม Gemvox",

        "menu_edit": "แก้ไข (&Edit)",
        "menu_undo": "เลิกทำ (&Undo)\tCtrl+Z",
        "menu_redo": "ทำซ้ำ (&Redo)\tCtrl+Y",
        "menu_cut": "ตัด (Cu&t)\tCtrl+X",
        "menu_copy": "คัดลอก (&Copy)\tCtrl+C",
        "menu_paste": "วาง (&Paste)\tCtrl+V",
        "menu_delete": "ลบ (&Delete)\tDel",
        "menu_select_all": "เลือกทั้งหมด (Select &All)\tCtrl+A",
        "menu_clear_field": "ล้างข้อความในช่อง (C&lear)\tAlt+Shift+L",

        "menu_audio": "เสียง (&Audio)",
        "menu_play_stop": "เล่น / หยุดเสียง (&Play)\tAlt+P",

        "menu_tabs": "แท็บ (&Tabs)",
        "menu_tab1": "1. สังเคราะห์เสียงพูดเดี่ยว (&Single)\tCtrl+1",
        "menu_tab2": "2. บทสนทนาหลายผู้พูด (&Multi)\tCtrl+2",
        "menu_tab3": "3. ออกแบบเสียงใหม่ (&Design)\tCtrl+3",
        "menu_tab4": "4. โคลนนิ่งเสียงพูด (&Replication)\tCtrl+4",
        "menu_tab5": "5. คลังเสียงและค้นหา (&Library)\tCtrl+5",
        "menu_tab6": "6. การตั้งค่าและ API Key (S&ettings)\tCtrl+6",
        "menu_next_tab": "แท็บถัดไป (&Next)\tCtrl+Tab",
        "menu_prev_tab": "แท็บก่อนหน้า (&Previous)\tCtrl+Shift+Tab",

        "menu_tools": "เครื่องมือ (T&ools)",
        "menu_insert_tag": "แทรกแท็กเสียงธรรมชาติ (&Insert Vocal Tag)...\tAlt+I",
        "menu_browse_style": "เลือกพรีเซ็ตอารมณ์เสียง (&Browse Styles)...\tAlt+B",
        "menu_create_style": "สร้างพรีเซ็ตอารมณ์เสียงส่วนตัว (&Create Style)...\tAlt+C",
        "menu_welcome_tour": "แนะนำการใช้งานเบื้องต้น (&Welcome Tour)...",

        "menu_help": "ช่วยเหลือ (&Help)",
        "menu_help_guide": "คู่มือการใช้งานและคีย์ลัด (&User Guide)\tF1",
        "menu_about": "เกี่ยวกับ Gemvox (&About)",

        # Single Speaker Panel (English Mnemonics preserved: &X, &I, &L, &M, &V, &U, &Y, &B, &C, &G, &P, &S)
        "ss_text_label": "ข้อความที่ต้องการให้พูด (Alt+&X):",
        "ss_default_text": "สวัสดีครับ! ยินดีต้อนรับสู่ Gemvox สตูดิโอสังเคราะห์เสียงพูด Gemini 3.8 Flash TTS",
        "btn_insert_tag_i": "แทรกแท็กเสียง... (Alt+&I)",
        "btn_clear_text": "ล้างข้อความ (Alt+&L)",
        "ss_box_params": "พารามิเตอร์เสียงและอารมณ์การพูด",
        "lbl_model": "โมเดล (Alt+&M):",
        "lbl_voice": "เสียงพูด (Alt+&V):",
        "btn_audition_u": "ทดลองฟังเสียง (Alt+&U)",
        "lbl_style": "อารมณ์ / สไตล์การพูด (Alt+&Y):",
        "btn_browse_styles": "เลือกสไตล์... (Alt+&B)",
        "btn_create_style": "สร้างสไตล์ส่วนตัว... (Alt+&C)",
        "btn_generate_speech": "สังเคราะห์เสียงพูด (Ctrl+Enter / Alt+&G)",
        "btn_play_audio": "เล่นเสียง (Alt+&P)",
        "btn_stop_audio": "หยุดเสียง (Alt+&P)",
        "btn_save_audio": "บันทึกไฟล์เสียง... (Ctrl+S / Alt+&S)",
        "status_ready": "สถานะ: พร้อมทำงาน",
        "msg_enter_text": "กรุณาพิมพ์ข้อความที่ต้องการให้พูด",
        "msg_text_cleared": "ล้างข้อความเรียบร้อยแล้ว",
        "msg_no_audio_save": "ยังไม่มีไฟล์เสียงสำหรับบันทึก",

        # Multi-Speaker Panel (English Mnemonics preserved: &D, &I, &L, &N, &K, &M, &G, &P, &S)
        "ms_script_label": "สคริปต์บทสนทนา (Alt+&D) - (รูปแบบ: ชื่อผู้พูด: ข้อความ [อารมณ์เสียง]):",
        "btn_insert_tag_t": "แทรกแท็กเสียง... (Alt+&I)",
        "btn_load_podcast": "โหลดเทมเพลตพอดแคสต์ (Alt+&L)",
        "btn_load_interview": "โหลดเทมเพลตสัมภาษณ์ (Alt+&N)",
        "btn_update_speakers": "อัปเดตรายชื่อผู้พูด (Alt+&K)",
        "ms_box_mapping": "การจับคู่เสียงประจำตัวผู้พูด",
        "lbl_voice_for": "เสียงของ '{speaker}':",
        "btn_generate_dialogue": "สังเคราะห์บทสนทนา (Ctrl+Enter / Alt+&G)",
        "msg_enter_script": "กรุณาพิมพ์สคริปต์บทสนทนา",
        "msg_script_cleared": "ล้างสคริปต์บทสนทนาเรียบร้อยแล้ว",

        # Voice Design Panel (English Mnemonics preserved: &N, &G, &L, &D, &C, &P, &Y, &S)
        "vd_info": "Voice Design ช่วยให้คุณออกแบบเสียงพูดใหม่ได้เองจากการเขียนคำบรรยายอายุ โทนเสียง สำเนียง และบุคลิก\nระบบจะสร้างรหัสเสียงถาวร (Voice ID) พร้อมไฟล์เสียงตัวอย่างให้ทันที",
        "vd_box_specs": "รายละเอียดบุคลิกเสียงที่ต้องการออกแบบ",
        "lbl_voice_name": "ชื่อเสียงพูด (Alt+&N):",
        "lbl_gender": "เพศ (Alt+&G):",
        "lbl_lang_code": "รหัสภาษา (Alt+&L):",
        "lbl_persona_prompt": "คำบรรยายบุคลิกเสียง (Alt+&D):",
        "btn_sample_astronomer": "ตัวอย่าง: นักดาราศาสตร์",
        "btn_sample_educator": "ตัวอย่าง: ครูสอนเทคโนโลยี",
        "btn_sample_fantasy": "ตัวอย่าง: นักเล่านิยายแฟนตาซี",
        "btn_create_voice": "สร้างเสียงพูดใหม่ (Alt+&C)",
        "btn_play_preview": "เล่นเสียงตัวอย่าง (Alt+&P)",
        "btn_stop_preview": "หยุดเสียงตัวอย่าง (Alt+&P)",
        "btn_copy_id_y": "คัดลอกรหัสเสียง (Alt+&Y)",
        "btn_save_preview_wav": "บันทึกเสียงตัวอย่าง WAV (Alt+&S)",
        "lbl_voice_id_none": "รหัสเสียง (Voice ID): ยังไม่ได้สร้าง",

        # Voice Replication Panel (English Mnemonics preserved: &N, &R, &B, &C, &S, &W, &M, &V, &Y)
        "vr_info": "การโคลนนิ่งเสียงพูดต้องใช้ไฟล์เสียง WAV 24kHz โมโนที่ชัดเจน 2 ไฟล์จากผู้พูดคนเดียวกัน:\n1. ไฟล์เสียงอ้างอิง (Reference Audio ความยาว 10 ถึง 30 วินาที)\n2. ไฟล์เสียงยืนยันสิทธิ์ (Consent Audio ที่อ่านประโยคยินยอมอย่างชัดเจน)",
        "vr_box_cloning": "ข้อมูลการโคลนนิ่งเสียงและการยืนยันสิทธิ์",
        "lbl_ref_audio": "ไฟล์เสียงอ้างอิง (Alt+&R):",
        "btn_browse_ref": "เลือกไฟล์อ้างอิง (Alt+&B)...",
        "lbl_consent_phrase": "ประโยคยืนยันสิทธิ์มาตรฐาน:",
        "btn_copy_statement": "คัดลอกประโยค (Alt+&C)",
        "lbl_con_audio": "ไฟล์เสียงยืนยันสิทธิ์ (Alt+&S):",
        "btn_browse_con": "เลือกไฟล์ยืนยันสิทธิ์ (Alt+&W)...",
        "lbl_storage_mode": "โหมดการจัดเก็บ (Alt+&M):",
        "mode_stateful": "Stateful (เก็บรหัสไว้ในโปรเจกต์ - แนะนำ)",
        "mode_stateless": "Stateless (เก็บคีย์ฝั่งไคลเอนต์)",
        "btn_replicate": "โคลนนิ่งเสียงพูด (Alt+&V)",

        # Voice Library Panel (English Mnemonics preserved: &S, &L, &G, &D, &X, &B, &V, &U, &C)
        "vl_info": "สำรวจ 30 เสียงสตูดิโอคุณภาพสูงของ Gemini หรือค้นหาเพิ่มเติมจากคลังเสียงออนไลน์:",
        "vl_box_filters": "ตัวกรองและการค้นหาคลังเสียง",
        "lbl_search_query": "คำค้นหา (Alt+&S):",
        "lbl_language": "ภาษา (Alt+&L):",
        "lbl_gender_g": "เพศ (Alt+&G):",
        "lbl_domain": "บริบทการใช้งาน (Alt+&D):",
        "btn_search_online": "ค้นหาคลังเสียงออนไลน์ (Alt+&X)",
        "btn_show_prebuilt": "แสดง 30 เสียงมาตรฐานในตัว (Alt+&B)",
        "lbl_voices_list": "รายชื่อเสียงพูด (Alt+&V):",
        "btn_audition_a": "ทดลองฟังเสียง (Alt+&U)",
        "btn_copy_id_c": "คัดลอกรหัสเสียง (Alt+&C)",

        # Settings Panel (English Mnemonics preserved: &K, &C, &G, &D, &W, &M, &V, &L, &R, &B, &U, &S)
        "set_info": "ตั้งค่ารหัส Gemini API Key ภาษาของโปรแกรม ค่าเริ่มต้นของสตูดิโอ และตัวเลือกการเข้าถึงสำหรับ Screen Reader:",
        "set_box_cred": "ข้อมูล API Key ภาษา และค่าเริ่มต้นของสตูดิโอ",
        "lbl_api_key": "รหัส Gemini API &Key (Alt+K):",
        "btn_test_conn": "ทดสอบการเชื่อมต่อ (Alt+&C)",
        "btn_get_key": "รับรหัส API Key (Alt+&G)",
        "lbl_output_folder": "โฟลเดอร์บันทึกไฟล์เสียง (Alt+&D):",
        "btn_browse_out": "เลือกโฟลเดอร์ (Alt+&W)...",
        "lbl_def_model": "โมเดลเริ่มต้น (Alt+&M):",
        "lbl_def_voice": "เสียงพูดเริ่มต้น (Alt+&V):",
        "lbl_ui_language": "ภาษาของโปรแกรม (Alt+&L):",
        "lang_en": "English (ค่าเริ่มต้น)",
        "lang_th": "ไทย (Thai)",
        "set_box_acc": "การเข้าถึงและเสียงแจ้งเตือนสถานะ",
        "chk_announcements": "เปิดใช้การประกาศสถานะด้วยเสียงผ่าน Active Screen &Reader (Alt+R)",
        "chk_beeps": "เปิดใช้เสียงสัญญาณเตือนเมื่อเริ่ม/เสร็จสิ้นงาน (Alt+&B)",
        "chk_autoplay": "เล่นเสียงพูดอัตโนมัติทันทีที่สังเคราะห์เสร็จ (Alt+&U)",
        "btn_save_settings": "บันทึกการตั้งค่า (Alt+&S)",
        "msg_settings_saved": "บันทึกการตั้งค่าเรียบร้อยแล้ว",
        "restart_prompt_title": "จำเป็นต้องรีสตาร์ทโปรแกรม",
        "restart_prompt_msg": "บันทึกการตั้งค่าของคุณเรียบร้อยแล้ว\n\nโปรแกรมจำเป็นต้องรีสตาร์ทเพื่อให้การตั้งค่าใหม่มีผลอย่างสมบูรณ์\nคุณต้องการรีสตาร์ท Gemvox ตอนนี้เลยหรือไม่?",

        # Dialogs (English Mnemonics preserved: &I, &C, &N, &S, &D, &A)
        "dlg_tag_title": "แทรกแท็กเสียงธรรมชาติ (Insert Vocal Tag)",
        "dlg_tag_banner_title": "แทรกแท็กเสียงธรรมชาติ (VOCAL TAG)",
        "dlg_tag_banner_sub": "เพิ่มจังหวะหยุดหายใจ เสียงถอนหายใจ เสียงหัวเราะ หรือกระซิบลงในตำแหน่งเคอร์เซอร์",
        "dlg_tag_info": "เลือกแท็กเสียงที่ต้องการแทรกตรงตำแหน่งเคอร์เซอร์ของคุณ:\n(กดลูกศรขึ้น/ลง แล้วกด Enter หรือคลิกปุ่มแทรกแท็ก)",
        "btn_insert": "แทรกแท็ก (&Insert)",
        "btn_cancel": "ยกเลิก (&Cancel)",

        "dlg_custom_style_title": "สร้างพรีเซ็ตอารมณ์เสียงส่วนตัว",
        "dlg_custom_style_banner": "สร้างพรีเซ็ตอารมณ์เสียงส่วนตัว",
        "dlg_custom_style_sub": "บันทึกคำสั่งกำหนดอารมณ์และน้ำเสียงที่ใช้บ่อยไว้เรียกใช้ซ้ำได้ทันที",
        "dlg_custom_style_info": "ตั้งชื่อและระบุคำสั่งอารมณ์เสียง เพื่อเก็บไว้ในรายการเลือกสไตล์ (Browse Styles) โดยไม่ต้องพิมพ์ซ้ำ",
        "lbl_preset_name": "ชื่อพรีเซ็ต (Alt+&N):",
        "lbl_preset_style": "คำสั่งอารมณ์ / สไตล์การพูด (Alt+&S):",
        "btn_save_preset": "บันทึกพรีเซ็ตส่วนตัว (&Save)",

        "dlg_style_title": "เลือกพรีเซ็ตอารมณ์เสียง (Style Preset)",
        "dlg_style_banner": "คลังพรีเซ็ตอารมณ์และสไตล์การพูด",
        "dlg_style_sub": "เลือกสไตล์การพูดมาตรฐานหรือสไตล์ส่วนตัวที่คุณสร้างไว้",
        "dlg_style_info": "เลือกสไตล์การพูดเพื่อกำหนดจังหวะ น้ำเสียง และอารมณ์ของโมเดล:",
        "btn_delete_custom": "ลบสไตล์ส่วนตัว (Alt+&D)",
        "btn_apply_style": "ใช้สไตล์นี้ (&Apply)",

        # Welcome Tour Dialog (English Mnemonics preserved: &P, &N, &G, &S)
        "welcome_title": "ยินดีต้อนรับสู่ Gemvox Studio - แนะนำการตั้งค่าเริ่มต้น",
        "welcome_banner_title": "ยินดีต้อนรับสู่ GEMVOX STUDIO",
        "welcome_banner_sub": "สตูดิโอสร้างเสียงพูด Gemini 3.8 Flash TTS  |  ทัวร์แนะนำการใช้งานครั้งแรกอย่างเป็นระบบ",
        "welcome_step_indicator": "ขั้นตอนที่ {step} จาก {total}: {title}",
        "btn_prev_step": "< ย้อนกลับ (Alt+&P)",
        "btn_next_step": "ขั้นตอนถัดไป (Alt+&N) >",
        "btn_go_settings": "ไปที่หน้าการตั้งค่าทันที (Alt+&G)",
        "btn_skip_tour": "เริ่มใช้งาน Gemvox (&Start / Esc)",

        # Help Dialog (English Mnemonics preserved: &T, &G, &W, &C)
        "help_title": "คู่มือการใช้งานและคีย์ลัด Gemvox อย่างเป็นระบบ (F1)",
        "help_banner_title": "GEMVOX STUDIO  \u2022  คู่มือการใช้งานอย่างเป็นระบบ",
        "help_banner_sub": "เลือกหัวข้อทางด้านซ้าย (ลูกศรขึ้น/ลง) แล้วกด Tab เพื่ออ่านคำแนะนำทีละขั้นตอน",
        "help_topics_label": "หมวดหมู่คู่มือ (Alt+&T):",
        "help_content_label": "รายละเอียดคำแนะนำทีละขั้นตอน (Alt+&G):",
        "btn_open_tour": "เปิดทัวร์แนะนำการใช้งาน (Alt+&W)",
        "btn_close": "ปิดหน้าต่าง (Alt+&C)",
    }
}


def tr(key: str, **kwargs) -> str:
    """Translate a UI string key into the currently configured language ('en' or 'th')."""
    lang = config.language
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    text = lang_dict.get(key)
    if text is None:
        text = TRANSLATIONS["en"].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
