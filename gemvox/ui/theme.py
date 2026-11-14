import re
from typing import Callable, Optional
from PySide6.QtCore import Qt, QObject, QRectF, Signal, QCoreApplication
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QWidget,
)
from gemvox.config import config

# ========================================================================
# GEMVOX v1.2.0 - UNIVERSAL DESIGN STUDIO SYSTEM ("OBSIDIAN & ROYAL GOLD")
# ========================================================================
# Engineered for both:
# 1. Screen Reader & Keyboard-First Users (UIA/MSAA metadata, QLabel buddies,
#    tabChangesFocus, wx-compatible keyboard & tab-bar navigation).
# 2. Sighted & Low-Vision Creators (High-contrast Obsidian & Royal Gold 2.0
#    surfaces, crisp 2px focus rings, card hierarchy, and custom vector paint).
# ========================================================================


class StudioColors:
    """Luxury Obsidian & Gold / Electric Sapphire color palette."""
    # Hex values for QSS
    HEX_BG_DEEP = "#0D1017"
    HEX_BG_ELEVATED = "#151A24"
    HEX_BG_HEADER = "#111621"
    HEX_BG_INPUT = "#1B2230"
    HEX_BG_INPUT_HOVER = "#212A3B"
    HEX_BG_STATUS = "#10151F"
    HEX_BORDER = "#263044"
    HEX_BORDER_SUBTLE = "#1E2636"

    HEX_ACCENT_GOLD = "#E6B85C"
    HEX_ACCENT_GOLD_HOVER = "#F2CA74"
    HEX_ACCENT_PRIMARY = "#3B82F6"
    HEX_ACCENT_PRIMARY_HOVER = "#60A5FA"
    HEX_ACCENT_SUCCESS = "#10B981"
    HEX_ACCENT_SUCCESS_HOVER = "#34D399"
    HEX_ACCENT_DANGER = "#EF4444"
    HEX_ACCENT_DANGER_HOVER = "#F87171"
    HEX_ACCENT_SECONDARY = "#283246"
    HEX_ACCENT_SECONDARY_HOVER = "#334059"

    HEX_TEXT_PRIMARY = "#F3F6FC"
    HEX_TEXT_SECONDARY = "#A3B1C6"
    HEX_TEXT_MUTED = "#73829C"
    HEX_TEXT_ON_GOLD = "#0F1219"

    # QColor instances for QPainter
    BG_DEEP = QColor(13, 16, 23)
    BG_ELEVATED = QColor(21, 26, 36)
    BG_HEADER = QColor(17, 22, 33)
    BG_INPUT = QColor(27, 34, 48)
    BG_STATUS = QColor(16, 21, 31)

    ACCENT_GOLD = QColor(230, 184, 92)
    ACCENT_PRIMARY = QColor(59, 130, 246)
    ACCENT_SUCCESS = QColor(16, 185, 129)
    ACCENT_DANGER = QColor(239, 68, 68)
    ACCENT_SECONDARY = QColor(40, 50, 70)

    TEXT_PRIMARY = QColor(243, 246, 252)
    TEXT_SECONDARY = QColor(163, 177, 198)
    TEXT_MUTED = QColor(115, 130, 156)
    TEXT_ON_GOLD = QColor(15, 18, 25)


_AMPERSAND_RE = re.compile(r"&(?!&)")


def clean_mnemonic(text: str) -> str:
    """Strip single '&' mnemonic markers while preserving '&&' as '&' for clean screen reader labels."""
    if not text:
        return ""
    return _AMPERSAND_RE.sub("", text).replace("&&", "&")


def get_qfont(size: int = 10, bold: bool = False, mono: bool = False) -> QFont:
    """Return clean, high-legibility studio typography supporting both English and Thai."""
    if mono:
        face = "Consolas" if config.language == "en" else "Tahoma"
    else:
        face = "Segoe UI" if config.language == "en" else "Tahoma"
    font = QFont(face, size)
    font.setBold(bold)
    return font


def repolish(widget: QWidget):
    """Force QSS re-evaluation after dynamic property updates."""
    style = widget.style()
    if style:
        style.unpolish(widget)
        style.polish(widget)
    widget.update()


def apply_accessible(
    widget: QWidget,
    name: Optional[str] = None,
    description: Optional[str] = None,
    label: Optional[QLabel] = None,
):
    """Apply clean UIA/MSAA accessibility metadata and optional QLabel buddy binding."""
    if name is not None:
        widget.setAccessibleName(clean_mnemonic(name))
    elif label is not None and not widget.accessibleName():
        widget.setAccessibleName(clean_mnemonic(label.text()))
    if description is not None:
        widget.setAccessibleDescription(description)
    if label is not None:
        label.setBuddy(widget)


def style_button(btn: QPushButton, variant: str = "primary", accessible_name: Optional[str] = None):
    """Apply Universal Design button variant and clean accessible name."""
    btn.setProperty("variant", variant)
    btn.setFocusPolicy(Qt.StrongFocus)
    btn.setCursor(Qt.PointingHandCursor)
    name = accessible_name if accessible_name is not None else clean_mnemonic(btn.text())
    if name:
        btn.setAccessibleName(name)
    repolish(btn)


def style_label(lbl: QLabel, kind: str = "normal"):
    """Style a QLabel with studio typography hierarchy."""
    lbl.setProperty("kind", kind)
    repolish(lbl)


class _UiDispatcher(QObject):
    """Thread-safe dispatcher to invoke callables on the Qt main GUI thread (simulates wx.CallAfter)."""
    _invoke = Signal(object)

    def __init__(self):
        super().__init__()
        self._invoke.connect(self._execute, Qt.QueuedConnection)

    def _execute(self, fn: Callable[[], None]):
        try:
            fn()
        except RuntimeError:
            # Widget may already have been deleted during shutdown
            pass

    def post(self, fn: Callable, *args, **kwargs):
        app = QCoreApplication.instance()
        if app is None:
            return
        if self.thread() != app.thread():
            self.moveToThread(app.thread())
        self._invoke.emit(lambda: fn(*args, **kwargs))


_dispatcher: Optional[_UiDispatcher] = None


def call_after(fn: Callable, *args, **kwargs):
    """Invoke `fn(*args, **kwargs)` asynchronously on the Qt main thread (wx.CallAfter equivalent)."""
    global _dispatcher
    app = QCoreApplication.instance()
    if app is None:
        return
    if _dispatcher is None:
        _dispatcher = _UiDispatcher()
    _dispatcher.post(fn, *args, **kwargs)


def create_app_icon() -> QIcon:
    """Dynamically render a luxury Obsidian & Gold waveform studio icon."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(StudioColors.BG_DEEP)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)

    painter.setPen(QPen(StudioColors.ACCENT_GOLD, 3))
    painter.setBrush(StudioColors.BG_ELEVATED)
    painter.drawRoundedRect(QRectF(4, 4, 56, 56), 14, 14)

    bars = [
        (14, 26, 4, 12, StudioColors.ACCENT_PRIMARY),
        (22, 18, 4, 28, StudioColors.ACCENT_GOLD),
        (30, 12, 4, 40, StudioColors.ACCENT_GOLD),
        (38, 20, 4, 24, StudioColors.ACCENT_GOLD),
        (46, 25, 4, 14, StudioColors.ACCENT_PRIMARY),
    ]
    painter.setPen(Qt.NoPen)
    for x, y, w, h, col in bars:
        painter.setBrush(col)
        painter.drawRoundedRect(QRectF(x, y, w, h), 2, 2)

    painter.end()
    return QIcon(pixmap)


class StudioHeaderBanner(QWidget):
    """
    Custom-painted luxury Obsidian & Royal Gold studio header banner.
    FocusPolicy is NoFocus so keyboard & screen reader users skip straight
    to interactive controls without encountering decorative elements.
    """

    def __init__(
        self,
        title: str,
        subtitle: str,
        badge_text: str = "GEMINI 3.8 STUDIO",
        height: int = 68,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._title = title
        self._subtitle = subtitle
        self._badge_text = badge_text
        self._height = height
        self.setFixedHeight(height)
        self.setFocusPolicy(Qt.NoFocus)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def paintEvent(self, event):
        w = self.width()
        h = self.height()
        if w <= 0 or h <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # 1. Subtle gradient background
        grad = QLinearGradient(0, 0, w, 0)
        grad.setColorAt(0.0, StudioColors.BG_HEADER)
        grad.setColorAt(0.65, QColor(20, 26, 39))
        grad.setColorAt(1.0, StudioColors.BG_HEADER)
        painter.fillRect(0, 0, w, h, grad)

        # 2. Top Royal Gold hairline (2px)
        painter.fillRect(0, 0, w, 2, StudioColors.ACCENT_GOLD)

        # 3. Bottom subtle separator line (1px)
        painter.fillRect(0, h - 1, w, 1, StudioColors.BG_INPUT)

        # 4. Mini Gold & Sapphire Acoustic Waveform Emblem
        wave_bars = [
            (16, 26, 3, 14, StudioColors.ACCENT_PRIMARY),
            (22, 18, 3, 30, StudioColors.ACCENT_GOLD),
            (28, 13, 3, 40, StudioColors.ACCENT_GOLD),
            (34, 21, 3, 24, StudioColors.ACCENT_GOLD),
            (40, 27, 3, 12, StudioColors.ACCENT_PRIMARY),
        ]
        painter.setPen(Qt.NoPen)
        for bx, by, bw, bh, bcol in wave_bars:
            painter.setBrush(bcol)
            painter.drawRoundedRect(QRectF(bx, by, bw, bh), 1.5, 1.5)

        # 5. Title & Subtitle text
        text_left = 54
        painter.setFont(get_qfont(13, bold=True))
        painter.setPen(StudioColors.TEXT_PRIMARY)
        painter.drawText(QRectF(text_left, 8, w - text_left - 200, 28), Qt.AlignVCenter | Qt.AlignLeft, self._title)

        painter.setFont(get_qfont(9, bold=False))
        painter.setPen(StudioColors.TEXT_SECONDARY)
        painter.drawText(QRectF(text_left, 35, w - text_left - 200, 24), Qt.AlignVCenter | Qt.AlignLeft, self._subtitle)

        # 6. Right-side Luxury Pill Badge
        if self._badge_text and w > 480:
            badge_label = f"\u2726 {self._badge_text}"
            badge_font = get_qfont(8, bold=True)
            painter.setFont(badge_font)
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(badge_label)
            th = fm.height()
            pad_x, pad_y = 14, 6
            bw = tw + pad_x * 2
            bh = th + pad_y * 2
            bx = w - bw - 18
            by = (h - bh) // 2

            if bx > text_left + 220:
                painter.setPen(QPen(StudioColors.ACCENT_GOLD, 1.2))
                painter.setBrush(StudioColors.BG_ELEVATED)
                painter.drawRoundedRect(QRectF(bx, by, bw, bh), 8, 8)
                painter.setPen(StudioColors.ACCENT_GOLD)
                painter.drawText(QRectF(bx, by, bw, bh), Qt.AlignCenter, badge_label)

        painter.end()


def build_studio_stylesheet() -> str:
    """Return the complete Universal Design QSS stylesheet for Gemvox v1.2.0."""
    c = StudioColors
    return f"""
    QMainWindow, QDialog {{
        background-color: {c.HEX_BG_DEEP};
        color: {c.HEX_TEXT_PRIMARY};
    }}

    QWidget {{
        color: {c.HEX_TEXT_PRIMARY};
    }}

    /* Menu Bar & Menus */
    QMenuBar {{
        background-color: {c.HEX_BG_HEADER};
        color: {c.HEX_TEXT_PRIMARY};
        border-bottom: 1px solid {c.HEX_BORDER_SUBTLE};
        padding: 3px 6px;
    }}
    QMenuBar::item {{
        background: transparent;
        padding: 5px 10px;
        border-radius: 5px;
    }}
    QMenuBar::item:selected, QMenuBar::item:pressed {{
        background-color: {c.HEX_BG_INPUT};
        color: {c.HEX_ACCENT_GOLD};
    }}
    QMenu {{
        background-color: {c.HEX_BG_ELEVATED};
        color: {c.HEX_TEXT_PRIMARY};
        border: 1px solid {c.HEX_BORDER};
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 24px 6px 14px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {c.HEX_ACCENT_PRIMARY};
        color: #FFFFFF;
    }}
    QMenu::separator {{
        height: 1px;
        background: {c.HEX_BORDER};
        margin: 4px 8px;
    }}

    /* Studio Workspace Tabs */
    QTabWidget::pane {{
        border: 1px solid {c.HEX_BORDER_SUBTLE};
        border-radius: 10px;
        background-color: {c.HEX_BG_DEEP};
        top: -1px;
    }}
    QTabBar::tab {{
        background-color: {c.HEX_BG_ELEVATED};
        color: {c.HEX_TEXT_SECONDARY};
        border: 1px solid {c.HEX_BORDER_SUBTLE};
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        padding: 8px 14px;
        margin-right: 4px;
        font-weight: 600;
    }}
    QTabBar::tab:hover {{
        background-color: {c.HEX_BG_INPUT};
        color: {c.HEX_TEXT_PRIMARY};
    }}
    QTabBar::tab:selected {{
        background-color: {c.HEX_BG_INPUT};
        color: {c.HEX_ACCENT_GOLD};
        border-color: {c.HEX_ACCENT_GOLD};
        border-bottom: 2px solid {c.HEX_ACCENT_GOLD};
    }}
    QTabBar:focus {{
        outline: 2px solid {c.HEX_ACCENT_GOLD};
    }}

    /* GroupBox / Studio Cards */
    QGroupBox {{
        background-color: {c.HEX_BG_ELEVATED};
        border: 1px solid {c.HEX_BORDER};
        border-radius: 10px;
        margin-top: 14px;
        padding: 14px 12px 12px 12px;
        font-weight: 700;
        color: {c.HEX_ACCENT_GOLD};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 14px;
        padding: 0 8px;
        background-color: {c.HEX_BG_ELEVATED};
        color: {c.HEX_ACCENT_GOLD};
        border-radius: 4px;
    }}

    /* Labels */
    QLabel {{
        background: transparent;
        color: {c.HEX_TEXT_PRIMARY};
        font-weight: 600;
    }}
    QLabel[kind="section"] {{
        color: {c.HEX_ACCENT_GOLD};
        font-weight: 700;
        font-size: 10.5pt;
    }}
    QLabel[kind="muted"] {{
        color: {c.HEX_TEXT_SECONDARY};
        font-weight: 400;
        font-size: 9.5pt;
    }}
    QLabel[kind="status"] {{
        color: {c.HEX_ACCENT_GOLD};
        font-weight: 700;
        font-size: 10pt;
        padding: 4px 8px;
        background-color: {c.HEX_BG_STATUS};
        border: 1px solid {c.HEX_BORDER_SUBTLE};
        border-radius: 6px;
    }}
    QLabel[kind="mono"] {{
        color: {c.HEX_ACCENT_PRIMARY_HOVER};
        font-family: "Consolas", "Tahoma", monospace;
        font-weight: 700;
        font-size: 10pt;
    }}

    /* Inputs & Editors */
    QLineEdit, QPlainTextEdit, QTextEdit {{
        background-color: {c.HEX_BG_INPUT};
        color: {c.HEX_TEXT_PRIMARY};
        border: 1px solid {c.HEX_BORDER};
        border-radius: 7px;
        padding: 7px 10px;
        selection-background-color: {c.HEX_ACCENT_PRIMARY};
        selection-color: #FFFFFF;
    }}
    QLineEdit:hover, QPlainTextEdit:hover, QTextEdit:hover {{
        background-color: {c.HEX_BG_INPUT_HOVER};
    }}
    QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {{
        border: 2px solid {c.HEX_ACCENT_GOLD};
        background-color: {c.HEX_BG_INPUT};
    }}

    /* ComboBox */
    QComboBox {{
        background-color: {c.HEX_BG_INPUT};
        color: {c.HEX_TEXT_PRIMARY};
        border: 1px solid {c.HEX_BORDER};
        border-radius: 7px;
        padding: 6px 10px;
        min-height: 22px;
    }}
    QComboBox:hover {{
        background-color: {c.HEX_BG_INPUT_HOVER};
    }}
    QComboBox:focus {{
        border: 2px solid {c.HEX_ACCENT_GOLD};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c.HEX_BG_ELEVATED};
        color: {c.HEX_TEXT_PRIMARY};
        border: 1px solid {c.HEX_ACCENT_GOLD};
        selection-background-color: {c.HEX_ACCENT_PRIMARY};
        selection-color: #FFFFFF;
        padding: 4px;
    }}

    /* ListWidget */
    QListWidget {{
        background-color: {c.HEX_BG_INPUT};
        color: {c.HEX_TEXT_PRIMARY};
        border: 1px solid {c.HEX_BORDER};
        border-radius: 8px;
        padding: 4px;
        outline: none;
    }}
    QListWidget:focus {{
        border: 2px solid {c.HEX_ACCENT_GOLD};
    }}
    QListWidget::item {{
        padding: 7px 10px;
        border-radius: 5px;
        margin: 1px 0;
    }}
    QListWidget::item:selected {{
        background-color: {c.HEX_ACCENT_PRIMARY};
        color: #FFFFFF;
        font-weight: 600;
    }}
    QListWidget::item:hover:!selected {{
        background-color: {c.HEX_BG_INPUT_HOVER};
    }}

    /* Buttons */
    QPushButton {{
        background-color: {c.HEX_ACCENT_SECONDARY};
        color: {c.HEX_TEXT_PRIMARY};
        border: 1px solid {c.HEX_BORDER};
        border-radius: 7px;
        padding: 7px 14px;
        font-weight: 700;
        min-height: 20px;
    }}
    QPushButton:hover {{
        background-color: {c.HEX_ACCENT_SECONDARY_HOVER};
    }}
    QPushButton:focus {{
        border: 2px solid {c.HEX_ACCENT_GOLD};
    }}
    QPushButton:disabled {{
        background-color: #161B26;
        color: {c.HEX_TEXT_MUTED};
        border-color: #1E2534;
    }}

    QPushButton[variant="primary"] {{
        background-color: {c.HEX_ACCENT_PRIMARY};
        color: #FFFFFF;
        border-color: {c.HEX_ACCENT_PRIMARY};
    }}
    QPushButton[variant="primary"]:hover {{
        background-color: {c.HEX_ACCENT_PRIMARY_HOVER};
    }}
    QPushButton[variant="primary"]:focus {{
        border: 2px solid {c.HEX_ACCENT_GOLD};
    }}

    QPushButton[variant="gold"] {{
        background-color: {c.HEX_ACCENT_GOLD};
        color: {c.HEX_TEXT_ON_GOLD};
        border-color: {c.HEX_ACCENT_GOLD};
    }}
    QPushButton[variant="gold"]:hover {{
        background-color: {c.HEX_ACCENT_GOLD_HOVER};
    }}
    QPushButton[variant="gold"]:focus {{
        border: 2px solid #FFFFFF;
    }}

    QPushButton[variant="success"] {{
        background-color: {c.HEX_ACCENT_SUCCESS};
        color: {c.HEX_TEXT_ON_GOLD};
        border-color: {c.HEX_ACCENT_SUCCESS};
    }}
    QPushButton[variant="success"]:hover {{
        background-color: {c.HEX_ACCENT_SUCCESS_HOVER};
    }}
    QPushButton[variant="success"]:focus {{
        border: 2px solid {c.HEX_ACCENT_GOLD};
    }}

    QPushButton[variant="danger"] {{
        background-color: {c.HEX_ACCENT_DANGER};
        color: #FFFFFF;
        border-color: {c.HEX_ACCENT_DANGER};
    }}
    QPushButton[variant="danger"]:hover {{
        background-color: {c.HEX_ACCENT_DANGER_HOVER};
    }}
    QPushButton[variant="danger"]:focus {{
        border: 2px solid {c.HEX_ACCENT_GOLD};
    }}

    /* CheckBox & RadioButton */
    QCheckBox, QRadioButton {{
        spacing: 8px;
        color: {c.HEX_TEXT_PRIMARY};
        padding: 3px 4px;
        border-radius: 5px;
    }}
    QCheckBox:focus, QRadioButton:focus {{
        border: 1px solid {c.HEX_ACCENT_GOLD};
        background-color: {c.HEX_BG_INPUT};
    }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 17px;
        height: 17px;
        border: 1px solid {c.HEX_BORDER};
        background-color: {c.HEX_BG_INPUT};
    }}
    QCheckBox::indicator {{
        border-radius: 4px;
    }}
    QRadioButton::indicator {{
        border-radius: 9px;
    }}
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background-color: {c.HEX_ACCENT_GOLD};
        border-color: {c.HEX_ACCENT_GOLD};
    }}

    /* Sliders */
    QSlider::groove:horizontal {{
        height: 6px;
        background: {c.HEX_BG_INPUT};
        border-radius: 3px;
    }}
    QSlider::sub-page:horizontal {{
        background: {c.HEX_ACCENT_GOLD};
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: {c.HEX_TEXT_PRIMARY};
        border: 2px solid {c.HEX_ACCENT_GOLD};
        width: 14px;
        height: 14px;
        margin: -5px 0;
        border-radius: 8px;
    }}
    QSlider:focus {{
        border: 1px solid {c.HEX_ACCENT_GOLD};
        border-radius: 4px;
    }}

    /* Progress Bar */
    QProgressBar {{
        background-color: {c.HEX_BG_INPUT};
        border: 1px solid {c.HEX_BORDER};
        border-radius: 6px;
        text-align: center;
        color: {c.HEX_TEXT_PRIMARY};
        height: 18px;
        font-weight: 700;
    }}
    QProgressBar::chunk {{
        background-color: {c.HEX_ACCENT_GOLD};
        border-radius: 5px;
    }}

    /* Status Bar */
    QStatusBar {{
        background-color: {c.HEX_BG_STATUS};
        color: {c.HEX_TEXT_PRIMARY};
        border-top: 1px solid {c.HEX_BORDER_SUBTLE};
    }}
    QStatusBar::item {{
        border: none;
    }}

    /* ScrollArea & ScrollBars */
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: {c.HEX_BG_DEEP};
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {c.HEX_BORDER};
        min-height: 24px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {c.HEX_TEXT_MUTED};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    """
