import wx
from gemvox.config import config

# ========================================================================
# GEMVOX v1.1.5 - LUXURY STUDIO DESIGN SYSTEM ("OBSIDIAN & ROYAL GOLD")
# ========================================================================
# Zero-Child Paint Architecture:
# Decorative banners and visual accents are painted directly onto the parent
# window using wx.EVT_PAINT (without creating extra child wx.Panel controls).
# This guarantees 0 unlabeled panels in the Win32 MSAA/UIA accessibility tree,
# while delivering a rich, high-contrast studio look for sighted users.
# ========================================================================


class StudioColors:
    """Luxury Obsidian & Gold / Electric Sapphire color palette."""
    # Surfaces
    BG_DEEP = wx.Colour(13, 16, 23)          # #0D1017 - Deep Obsidian Canvas
    BG_ELEVATED = wx.Colour(21, 26, 36)      # #151A24 - Elevated Card Surface
    BG_HEADER = wx.Colour(17, 22, 33)        # #111621 - Header Banner Surface
    BG_INPUT = wx.Colour(27, 34, 48)         # #1B2230 - Input Field & List Surface
    BG_STATUS = wx.Colour(16, 21, 31)        # #10151F - Status Console Surface

    # Accents
    ACCENT_GOLD = wx.Colour(230, 184, 92)    # #E6B85C - Royal Champagne Gold
    ACCENT_PRIMARY = wx.Colour(59, 130, 246) # #3B82F6 - Electric Sapphire Blue
    ACCENT_SUCCESS = wx.Colour(16, 185, 129) # #10B981 - Emerald Ready/Success
    ACCENT_DANGER = wx.Colour(239, 68, 68)   # #EF4444 - Crimson Stop/Delete
    ACCENT_SECONDARY = wx.Colour(40, 50, 70) # #283246 - Subtle Slate Button

    # Typography
    TEXT_PRIMARY = wx.Colour(243, 246, 252)  # #F3F6FC - Crisp Alabaster White
    TEXT_SECONDARY = wx.Colour(163, 177, 198)# #A3B1C6 - Soft Platinum Silver
    TEXT_MUTED = wx.Colour(115, 130, 156)    # #73829C - Muted Slate
    TEXT_ON_GOLD = wx.Colour(15, 18, 25)     # #0F1219 - Deep Ink on Gold


def get_font(size: int = 10, bold: bool = False, mono: bool = False) -> wx.Font:
    """Return clean, high-legibility studio typography supporting both English and Thai."""
    family = wx.FONTFAMILY_TELETYPE if mono else wx.FONTFAMILY_SWISS
    weight = wx.FONTWEIGHT_BOLD if bold else wx.FONTWEIGHT_NORMAL
    if mono:
        face = "Consolas" if config.language == "en" else "Tahoma"
    else:
        face = "Segoe UI" if config.language == "en" else "Tahoma"
    return wx.Font(size, family, wx.FONTSTYLE_NORMAL, weight, False, face)


def enable_high_dpi():
    """Enable crisp Per-Monitor High-DPI scaling on Windows."""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def create_app_icon() -> wx.Icon:
    """Dynamically render a luxury Obsidian & Gold waveform studio icon."""
    bmp = wx.Bitmap(64, 64)
    dc = wx.MemoryDC(bmp)
    dc.SetBackground(wx.Brush(StudioColors.BG_DEEP))
    dc.Clear()

    gc = wx.GraphicsContext.Create(dc)
    if gc:
        gc.SetPen(wx.Pen(StudioColors.ACCENT_GOLD, 3))
        gc.SetBrush(wx.Brush(StudioColors.BG_ELEVATED))
        gc.DrawRoundedRectangle(4, 4, 56, 56, 14)

        bars = [
            (14, 26, 4, 12, StudioColors.ACCENT_PRIMARY),
            (22, 18, 4, 28, StudioColors.ACCENT_GOLD),
            (30, 12, 4, 40, StudioColors.ACCENT_GOLD),
            (38, 20, 4, 24, StudioColors.ACCENT_GOLD),
            (46, 25, 4, 14, StudioColors.ACCENT_PRIMARY),
        ]
        for x, y, w, h, col in bars:
            gc.SetPen(wx.Pen(col, 1))
            gc.SetBrush(wx.Brush(col))
            gc.DrawRoundedRectangle(x, y, w, h, 2)

    dc.SelectObject(wx.NullBitmap)
    icon = wx.Icon()
    icon.CopyFromBitmap(bmp)
    return icon


def attach_painted_header(
    window: wx.Window,
    sizer: wx.Sizer,
    title: str,
    subtitle: str,
    badge_text: str = "GEMINI 3.8 STUDIO",
    height: int = 68
):
    """
    Paint a luxury studio header banner directly onto `window` using wx.EVT_PAINT
    and reserve space at the top of `sizer` using a pure sizer spacer (0 child windows).

    Why this matters for Accessibility:
    - Creates ZERO wx.Panel or wx.StaticText child HWND objects.
    - Screen readers (NVDA, JAWS, Narrator) never encounter any 'unlabeled panel'
      or decorative text when tabbing or exploring dialogs.
    - Sighted users still enjoy the full Obsidian & Royal Gold header banner,
      soundwave crest, title, subtitle, and version pill badge.
    """
    sizer.AddSpacer(height)

    def _on_paint(event):
        dc = wx.PaintDC(window)
        w, _ = window.GetClientSize()
        if w <= 0:
            return

        # 1. Header background fill
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush(StudioColors.BG_HEADER))
        dc.DrawRectangle(0, 0, w, height)

        # 2. Top Royal Gold hairline (2px)
        dc.SetBrush(wx.Brush(StudioColors.ACCENT_GOLD))
        dc.DrawRectangle(0, 0, w, 2)

        # 3. Bottom subtle separator line (1px)
        dc.SetBrush(wx.Brush(StudioColors.BG_INPUT))
        dc.DrawRectangle(0, height - 1, w, 1)

        # 4. Mini Gold & Sapphire Acoustic Waveform Emblem on the left
        wave_bars = [
            (16, 26, 3, 14, StudioColors.ACCENT_PRIMARY),
            (22, 18, 3, 30, StudioColors.ACCENT_GOLD),
            (28, 13, 3, 40, StudioColors.ACCENT_GOLD),
            (34, 21, 3, 24, StudioColors.ACCENT_GOLD),
            (40, 27, 3, 12, StudioColors.ACCENT_PRIMARY),
        ]
        for bx, by, bw, bh, bcol in wave_bars:
            dc.SetBrush(wx.Brush(bcol))
            dc.DrawRectangle(bx, by, bw, bh)

        # 5. Title & Subtitle text
        text_left = 54
        dc.SetFont(get_font(13, bold=True))
        dc.SetTextForeground(StudioColors.TEXT_PRIMARY)
        dc.DrawText(title, text_left, 11)

        dc.SetFont(get_font(9, bold=False))
        dc.SetTextForeground(StudioColors.TEXT_SECONDARY)
        dc.DrawText(subtitle, text_left, 38)

        # 6. Right-side Luxury Pill Badge (if window is wide enough)
        if badge_text and w > 480:
            badge_label = f"\u2726 {badge_text}"
            dc.SetFont(get_font(8, bold=True))
            tw, th = dc.GetTextExtent(badge_label)
            pad_x, pad_y = 12, 6
            bw = tw + pad_x * 2
            bh = th + pad_y * 2
            bx = w - bw - 18
            by = (height - bh) // 2

            if bx > text_left + 220:
                dc.SetPen(wx.Pen(StudioColors.ACCENT_GOLD, 1))
                dc.SetBrush(wx.Brush(StudioColors.BG_ELEVATED))
                dc.DrawRoundedRectangle(bx, by, bw, bh, 6)
                dc.SetTextForeground(StudioColors.ACCENT_GOLD)
                dc.DrawText(badge_label, bx + pad_x, by + pad_y)

        event.Skip()

    def _on_size(event):
        window.RefreshRect(wx.Rect(0, 0, window.GetClientSize().width, height))
        event.Skip()

    window.Bind(wx.EVT_PAINT, _on_paint)
    window.Bind(wx.EVT_SIZE, _on_size)


def style_panel(panel: wx.Window, elevated: bool = False, accessible_name: str = None):
    """Apply deep obsidian or elevated studio surface styling to a panel or dialog."""
    bg = StudioColors.BG_ELEVATED if elevated else StudioColors.BG_DEEP
    panel.SetBackgroundColour(bg)
    panel.SetForegroundColour(StudioColors.TEXT_PRIMARY)
    panel.SetFont(get_font(10))
    if accessible_name:
        try:
            panel.SetName(accessible_name)
        except Exception:
            pass


def style_label(lbl: wx.StaticText, kind: str = "normal"):
    """Style a StaticText control with luxury typography hierarchy."""
    if kind == "section":
        lbl.SetForegroundColour(StudioColors.ACCENT_GOLD)
        lbl.SetFont(get_font(10, bold=True))
    elif kind == "muted":
        lbl.SetForegroundColour(StudioColors.TEXT_SECONDARY)
        lbl.SetFont(get_font(9))
    elif kind == "status":
        lbl.SetForegroundColour(StudioColors.ACCENT_GOLD)
        lbl.SetFont(get_font(10, bold=True))
    elif kind == "mono":
        lbl.SetForegroundColour(StudioColors.ACCENT_PRIMARY)
        lbl.SetFont(get_font(10, bold=True, mono=True))
    else:
        lbl.SetForegroundColour(StudioColors.TEXT_PRIMARY)
        lbl.SetFont(get_font(10, bold=True))


def style_text_ctrl(ctrl: wx.TextCtrl, multiline: bool = False, mono: bool = False):
    """Style a single-line or RichEdit multiline TextCtrl with dark studio contrast."""
    ctrl.SetBackgroundColour(StudioColors.BG_INPUT)
    ctrl.SetForegroundColour(StudioColors.TEXT_PRIMARY)
    font = get_font(11 if multiline else 10, mono=mono)
    ctrl.SetFont(font)

    try:
        attr = wx.TextAttr(StudioColors.TEXT_PRIMARY, StudioColors.BG_INPUT, font)
        ctrl.SetDefaultStyle(attr)
        val = ctrl.GetValue()
        if val:
            ctrl.SetStyle(0, len(val), attr)
    except Exception:
        pass


def style_combo(combo: wx.ComboBox):
    """Style a native ComboBox."""
    combo.SetBackgroundColour(StudioColors.BG_INPUT)
    combo.SetForegroundColour(StudioColors.TEXT_PRIMARY)
    combo.SetFont(get_font(10))


def style_listbox(lb: wx.ListBox):
    """Style a native ListBox with comfortable reading font."""
    lb.SetBackgroundColour(StudioColors.BG_INPUT)
    lb.SetForegroundColour(StudioColors.TEXT_PRIMARY)
    lb.SetFont(get_font(10))


def style_checkbox(chk: wx.CheckBox):
    """Style a native CheckBox."""
    chk.SetBackgroundColour(StudioColors.BG_ELEVATED)
    chk.SetForegroundColour(StudioColors.TEXT_PRIMARY)
    chk.SetFont(get_font(10))


def style_radiobox(rb: wx.RadioBox):
    """Style a native RadioBox."""
    rb.SetBackgroundColour(StudioColors.BG_DEEP)
    rb.SetForegroundColour(StudioColors.ACCENT_GOLD)
    rb.SetFont(get_font(10, bold=True))


def style_staticbox(box: wx.StaticBox):
    """Style a StaticBox group frame in Royal Gold."""
    box.SetBackgroundColour(StudioColors.BG_ELEVATED)
    box.SetForegroundColour(StudioColors.ACCENT_GOLD)
    box.SetFont(get_font(10, bold=True))


def style_button(btn: wx.Button, kind: str = "secondary"):
    """
    Style a native wx.Button with clear visual hierarchy:
    - 'primary': Electric Sapphire Blue (Generate / Save / Apply)
    - 'gold': Royal Champagne Gold (Audition / Special Studio Action)
    - 'success': Emerald Green (Play Audio)
    - 'danger': Crimson Red (Stop / Delete)
    - 'secondary': Elevated Slate (Browse / Tools / Secondary actions)
    """
    btn.SetMinSize((-1, 34))
    if kind == "primary":
        btn.SetBackgroundColour(StudioColors.ACCENT_PRIMARY)
        btn.SetForegroundColour(StudioColors.TEXT_PRIMARY)
        btn.SetFont(get_font(10, bold=True))
    elif kind == "gold":
        btn.SetBackgroundColour(StudioColors.ACCENT_GOLD)
        btn.SetForegroundColour(StudioColors.TEXT_ON_GOLD)
        btn.SetFont(get_font(10, bold=True))
    elif kind == "success":
        btn.SetBackgroundColour(StudioColors.ACCENT_SUCCESS)
        btn.SetForegroundColour(StudioColors.TEXT_PRIMARY)
        btn.SetFont(get_font(10, bold=True))
    elif kind == "danger":
        btn.SetBackgroundColour(StudioColors.ACCENT_DANGER)
        btn.SetForegroundColour(StudioColors.TEXT_PRIMARY)
        btn.SetFont(get_font(10, bold=True))
    else:
        btn.SetBackgroundColour(StudioColors.ACCENT_SECONDARY)
        btn.SetForegroundColour(StudioColors.TEXT_PRIMARY)
        btn.SetFont(get_font(10, bold=False))
