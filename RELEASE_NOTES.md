# Gemvox v1.1.8: Fix 400 INVALID_ARGUMENT speechConfig & Enhanced TTS Endpoint Resilience

Accessible Desktop Studio for Google Gemini Speech Synthesis (Single-Speaker, Multi-Speaker Conversational Dialogue, Voice Design, Replication & Library) with First-Class Screen Reader Support (NVDA, JAWS, Narrator).

---

## 🌟 What's New in v1.1.8 (มีอะไรใหม่ในเวอร์ชัน 1.1.8)

### 1. 🛠️ แก้ไขปัญหา 400 INVALID_ARGUMENT (Unknown name "speechConfig" at 'generation_config')
- **สาเหตุของปัญหา**: SDK `google-genai` เมื่อเริ่มทำงานโดยไม่ได้ระบุเวอร์ชัน API จะเชื่อมต่อไปยัง Google AI Studio endpoint `v1` โดยอัตโนมัติ ซึ่ง `v1` รองรับเฉพาะ Text/Vision โมเดลและปฏิเสธฟิลด์ `speechConfig` ใน `generation_config` ส่งผลให้การส่ง Prompt สังเคราะห์เสียงเกิดข้อผิดพลาด 400
- **แก้ไขด้วย v1beta Endpoint**:
  - กำหนด `http_options={"api_version": "v1beta"}` ให้กับ `genai.Client` และตั้งค่า Environment Variable `GOOGLE_GENAI_API_VERSION="v1beta"`
  - สร้างโครงสร้างพารามิเตอร์สังเคราะห์เสียงด้วย `google.genai.types.GenerateContentConfig` และ `types.SpeechConfig` แบบ Strongly-typed ทั้งในโหมดสังเคราะห์เสียงเดี่ยวและบทสนทนาสองผู้พูด
- **แก้ไข Interactions API สำหรับบทสนทนา**:
  - ถอดค่า `mode: "conversational"` ที่เซิร์ฟเวอร์ Google อัปเดตปฏิเสธคำขอออก คงเหลือเฉพาะการระบุรายชื่อผู้พูดและเสียงพากย์ ทำให้การสังเคราะห์บทสนทนาทำงานได้อย่างราบรื่น 100%

---

### 2. 🛡️ ขยายระบบ Fallback อัจฉริยะ (Comprehensive Model & Error Resilience)
- **ดักจับข้อผิดพลาดระดับโมเดลอัตโนมัติ**: ระบบตรวจจับทั้ง `404 Not Found`, `Unknown name speechConfig`, `cannot find field`, `is not supported` และสลับไปยังโมเดลสำรองถัดไปทันทีโดยไม่หยุดทำงาน
- **คงการแจ้งเตือนคีย์ไม่ถูกต้องอย่างแม่นยำ**: หากคีย์ API ผิดพลาด (`API_KEY_INVALID`) หรือโควต้าหมด (`RESOURCE_EXHAUSTED`) ระบบจะไม่สลับโมเดลอย่างไร้ประโยชน์ แต่จะแจ้งให้ผู้ใช้ทราบโดยตรง
- **ลำดับโมเดลสำรอง (Fallback Priority)**:
  1. `gemini-2.5-flash-preview-tts` (ความเสถียรสูงสุด รองรับทุกระดับ API key)
  2. `gemini-3.1-flash-tts-preview` (รองรับการแสดงอารมณ์และ vocal tags ขั้นสูง)
  3. `gemini-2.5-pro-preview-tts` (คุณภาพเสียงพากย์ระดับสตูดิโอความละเอียดสูง)
  4. `gemini-3.8-flash-lite-tts`
  5. `gemini-3.8-flash-tts`
  6. `gemini-2.0-flash` (สำรองพิเศษด้วย Audio Modality)
- **Seamless PCM-to-WAV Wrapping**: ห่อหุ้มข้อมูลเสียง PCM 24kHz 16-bit Mono (audio/L16) เป็นไฟล์ RIFF WAV มาตรฐานโดยอัตโนมัติ

---

### 3. 🎛️ ปรับโฉมชุดควบคุมเครื่องเล่นเสียงสตูดิโอ (Studio Audio Player Transport Deck)
ติดตั้งแถบควบคุมเครื่องเล่นเสียงระดับมืออาชีพในทุกแท็บหลัก (**สังเคราะห์เสียงเดี่ยว**, **บทสนทนาหลายผู้พูด**, **ออกแบบเสียง**, และ **หน้าต่างประวัติการสังเคราะห์เสียง Ctrl+H**) โดยทำงานแบบ Non-blocking ไม่ทำให้โปรแกรมค้าง:
- **ปุ่มเล่น / พัก / เล่นต่อ (`Alt+P`)**: สลับสถานะ เล่น (Play), พักชั่วคราว (Pause) และเล่นต่อ (Resume) พร้อมเปลี่ยนสีและป้ายกำกับตามสถานะ
- **ปุ่มหยุดเสียง (`Alt+Q`)**: สั่งหยุดเสียงทันทีและรีเซ็ตตำแหน่งเวลาไปยัง `00:00`
- **กรอกลับและกรอไปข้างหน้า 5 วินาที (`F7` / `F8`)**: ข้ามเวลาทีละ 5 วินาทีได้อย่างรวดเร็วและแม่นยำ
- **แถบเลื่อนตำแหน่งเสียง (Interactive Seek Slider)**: เลื่อนหรือระบุตำแหน่งเวลาในคลิปเสียงได้อย่างอิสระ พร้อมหน้าปัดแสดงเวลาแบบ `MM:SS / MM:SS`
- **แถบปรับระดับเสียง (`F9` ลดเสียง / `F10` เพิ่มเสียง)**: ปรับความดังเสียงอิสระตั้งแต่ 0% ถึง 100% พร้อมบันทึกค่าลงการตั้งค่า
- **สลับความเร็วการเล่นเสียง (`Ctrl+Shift+P`)**: เลือกความเร็วได้ 5 ระดับ `0.75x`, `1.0x (ปกติ)`, `1.25x`, `1.5x`, และ `2.0x`
- **โหมดเล่นวนซ้ำอัตโนมัติ (`Ctrl+L`)**: เปิด/ปิดการเล่นวนลูปต่อเนื่องสำหรับตรวจสอบคุณภาพเสียง

---

### 4. 🚀 ปรับปรุงความเสถียรของตัวเริ่มโปรแกรมและตัวทดสอบระบบ (Startup & Diagnostic)
- **แก้ไขระบบ Screen Reader Announcer ข้ามแพลตฟอร์ม**: ปกป้องการโหลด `ctypes.windll` และ `winsound` อย่างปลอดภัย
- **แก้ปัญหาลำดับการสร้าง `wx.App`**: ป้องกันปัญหาหน้าต่างโปรแกรมไม่ปรากฏ หรือปิดตัวลงเงียบ ๆ ภายใต้ `pythonw.exe`
- **ตรวจจับ Python Environment อัตโนมัติใน `Gemvox.bat`**: ค้นหาและสลับไปยัง `venv`, `.venv`, หรือระบบ Python ให้อัตโนมัติ พร้อมติดตั้งแพ็กเกจที่จำเป็นทันที
- **สคริปต์ตรวจสุขภาพระบบ (`Test.bat` / `test_gemvox.py`)**: ตรวจเช็ค Python, wxPython, google-genai, sounddevice และ UI ครบทุกส่วนในคำสั่งเดียว
- **ตัวอัปเดตอัตโนมัติจาก GitHub โดยตรง (`Ctrl+U`)**: ตรวจสอบและอัปเดตเวอร์ชันใหม่พร้อมติดตั้งให้อัตโนมัติ

---

## ⌨️ ตารางคีย์ลัดสำคัญ (Key Shortcuts)
- **`Ctrl+Enter` / `Alt+G`**: สั่งสังเคราะห์เสียงพูด / บทสนทนา / เสียงออกแบบ
- **`Alt+P`**: เล่นเสียง / พักชั่วคราว / เล่นต่อ (Play / Pause / Resume)
- **`Alt+Q`**: หยุดเสียงและรีเซ็ตเวลาเป็น 00:00 (Stop)
- **`F7` / `F8`**: กรอกลับ 5 วินาที (-5s) / กรอไปข้างหน้า 5 วินาที (+5s)
- **`F9` / `F10`**: ลดระดับเสียง (-10%) / เพิ่มระดับเสียง (+10%)
- **`Ctrl+L`**: เปิด/ปิดการเล่นวนซ้ำ (Loop Playback)
- **`Ctrl+Shift+P`**: สลับระดับความเร็วการเล่น (0.75x - 2.0x)
- **`Ctrl+S`**: บันทึกไฟล์เสียงปัจจุบันเป็น WAV
- **`Ctrl+H`**: เปิดหน้าต่างประวัติการสังเคราะห์เสียง
- **`Ctrl+U`**: ตรวจสอบและอัปเดตเวอร์ชันใหม่โดยตรงจาก GitHub
- **`Ctrl+1 .. 6`**: สลับแท็บการทำงานทั้ง 6 หน้า
- **`F1`**: เปิดคู่มือการใช้งานอย่างละเอียด 6 บท

---

## 📦 Download Assets:
- **`Gemvox_Standalone.exe`**: ตัวรันเดี่ยวไฟล์เดียว ไม่ต้องติดตั้ง (Single-file Portable Executable)
- **`Gemvox_v1.1.8_Portable.zip`**: ตัวโปรแกรมฉบับพกพา โฟลเดอร์สมบูรณ์พร้อมไฟล์ DLL ของ Screen Reader (NVDA 32/64-bit) และระบบตั้งค่าแบบพกพา
