"""
Universal Design Multiline Text Area backed by native Win32 RICHEDIT50W.

Why native RICHEDIT50W inside QWidget.createWindowContainer(QWindow.fromWinId):
- Qt6's native C++ QPlainTextEdit / QTextEdit Windows UIA provider has a known
  defect where empty lines (blank lines between paragraphs) repeat the previous
  line's text in screen readers like NVDA instead of announcing "blank".
- Subclassing QAccessibleWidget + QAccessibleTextInterface in PySide6 6.12
  (Shiboken6) causes access violations on clear() and omits textAtOffset().
- Hosting Windows' native RICHEDIT50W (msftedit.dll) inside a QFrame via
  QWindow.fromWinId + QWidget.createWindowContainer gives screen readers
  100% native Windows UIA/MSAA text navigation ("blank" on empty lines,
  character/word/line reading, read-only caret navigation) while preserving
  Gemvox's Obsidian & Royal Gold styling, Tab/Shift+Tab focus traversal,
  context menus, and MainWindow/Dialog keyboard shortcuts.
"""

import ctypes
from ctypes import wintypes
from typing import Optional
import weakref

import win32con
import win32gui
from PySide6.QtCore import QEvent, QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QFont, QKeyEvent, QWindow
from PySide6.QtWidgets import QApplication, QFrame, QVBoxLayout, QWidget

from gemvox.ui.theme import clean_mnemonic, get_qfont

_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32
_ole32 = ctypes.windll.ole32

_msftedit_loaded = False
_com_initialized = False


def _ensure_win32_init():
    global _msftedit_loaded, _com_initialized
    if not _msftedit_loaded:
        _kernel32.LoadLibraryW("msftedit.dll")
        _msftedit_loaded = True
    if not _com_initialized:
        _ole32.CoInitialize(None)
        _com_initialized = True


# Win32 / RichEdit constants
_EM_SETSEL = 0x00B1
_EM_SCROLLCARET = 0x00B7
_EM_CANUNDO = 0x00C6
_EM_UNDO = 0x00C7
_EM_SETREADONLY = 0x00CF
_EM_REPLACESEL = 0x00C2
_EM_CANPASTE = 0x0432
_EM_EXGETSEL = 0x0434
_EM_EXSETSEL = 0x0437
_EM_SETBKGNDCOLOR = 0x0443
_EM_SETCHARFORMAT = 0x0444
_EM_REDO = 0x0454
_EM_CANREDO = 0x0455
_EM_SETTEXTMODE = 0x0459

_SCF_ALL = 0x0004
_TM_PLAINTEXT = 1
_CFM_COLOR = 0x40000000
_CFM_FACE = 0x20000000
_CFM_SIZE = 0x80000000
_OBJID_CLIENT = 0xFFFFFFFC

# Obsidian & Royal Gold colors (Win32 COLORREF is 0x00BBGGRR)
_BG_COLORREF = 0x00261A16    # #161A26
_TEXT_COLORREF = 0x00F9F3F1  # #F1F3F9


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_uint32),
        ("Data2", ctypes.c_uint16),
        ("Data3", ctypes.c_uint16),
        ("Data4", ctypes.c_ubyte * 8),
    ]


_CLSID_AccPropServices = _GUID(
    0xB5F8350B, 0x0548, 0x48B1, (ctypes.c_ubyte * 8)(0xA6, 0xEE, 0x88, 0xBD, 0x00, 0xB4, 0xA5, 0xE7)
)
_IID_IAccPropServices = _GUID(
    0x6E26E776, 0x04F0, 0x495D, (ctypes.c_ubyte * 8)(0x80, 0xE4, 0x33, 0x30, 0x35, 0x2E, 0x31, 0x69)
)
_PROPID_ACC_NAME = _GUID(
    0x608D3DF8, 0x8128, 0x4AA7, (ctypes.c_ubyte * 8)(0xA4, 0x28, 0xF5, 0x5E, 0x49, 0x26, 0x72, 0x91)
)
_PROPID_ACC_DESCRIPTION = _GUID(
    0x4D48DFE4, 0xBD3F, 0x491F, (ctypes.c_ubyte * 8)(0xA6, 0x48, 0x49, 0x2D, 0x6F, 0x20, 0xC5, 0x88)
)


class _CHARRANGE(ctypes.Structure):
    _fields_ = [("cpMin", wintypes.LONG), ("cpMax", wintypes.LONG)]


class _CHARFORMAT2W(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwMask", wintypes.DWORD),
        ("dwEffects", wintypes.DWORD),
        ("yHeight", wintypes.LONG),
        ("yOffset", wintypes.LONG),
        ("crTextColor", wintypes.COLORREF),
        ("bCharSet", ctypes.c_byte),
        ("bPitchAndFamily", ctypes.c_byte),
        ("szFaceName", wintypes.WCHAR * 32),
        ("wWeight", wintypes.WORD),
        ("sSpacing", ctypes.c_short),
        ("crBackColor", wintypes.COLORREF),
        ("lcid", wintypes.LCID),
        ("dwReserved", wintypes.DWORD),
        ("sStyle", ctypes.c_short),
        ("wKerning", wintypes.WORD),
        ("bUnderlineType", ctypes.c_byte),
        ("bAnimation", ctypes.c_byte),
        ("bRevAuthor", ctypes.c_byte),
        ("bUnderlineColor", ctypes.c_byte),
    ]


def _set_hwnd_acc_prop(hwnd: int, prop_id: _GUID, value: str):
    if not hwnd:
        return
    _ensure_win32_init()
    ptr = ctypes.c_void_p()
    hr = _ole32.CoCreateInstance(
        ctypes.byref(_CLSID_AccPropServices),
        None,
        1,
        ctypes.byref(_IID_IAccPropServices),
        ctypes.byref(ptr),
    )
    if hr != 0 or not ptr.value:
        return
    try:
        vtable = ctypes.cast(ptr, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        set_prop_str = ctypes.WINFUNCTYPE(
            ctypes.c_long,
            ctypes.c_void_p,
            wintypes.HWND,
            wintypes.DWORD,
            wintypes.DWORD,
            _GUID,
            wintypes.LPCWSTR,
        )(vtable[7])
        set_prop_str(ptr, hwnd, _OBJID_CLIENT, 0, prop_id, value)
    finally:
        release = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtable[2])
        release(ptr)


_VK_TO_QT = {
    win32con.VK_TAB: Qt.Key_Tab,
    win32con.VK_RETURN: Qt.Key_Return,
    win32con.VK_ESCAPE: Qt.Key_Escape,
    win32con.VK_PRIOR: Qt.Key_PageUp,
    win32con.VK_NEXT: Qt.Key_PageDown,
    win32con.VK_F1: Qt.Key_F1,
    win32con.VK_F7: Qt.Key_F7,
    win32con.VK_F8: Qt.Key_F8,
    win32con.VK_F9: Qt.Key_F9,
    win32con.VK_F10: Qt.Key_F10,
}

# Ctrl+<key> combinations that should stay inside RICHEDIT50W for text editing
_NATIVE_CTRL_VKS = {
    ord("A"), ord("C"), ord("V"), ord("X"), ord("Z"), ord("Y"),
    win32con.VK_LEFT, win32con.VK_RIGHT, win32con.VK_UP, win32con.VK_DOWN,
    win32con.VK_HOME, win32con.VK_END, win32con.VK_BACK, win32con.VK_DELETE,
    win32con.VK_INSERT,
}


def _vk_to_qt_key(vk: int) -> Optional[int]:
    if vk in _VK_TO_QT:
        return _VK_TO_QT[vk]
    if ord("0") <= vk <= ord("9"):
        return Qt.Key(vk)
    if ord("A") <= vk <= ord("Z"):
        return Qt.Key(vk)
    return None


def _current_qt_modifiers() -> Qt.KeyboardModifiers:
    mods = Qt.NoModifier
    if _user32.GetKeyState(win32con.VK_CONTROL) & 0x8000:
        mods |= Qt.ControlModifier
    if _user32.GetKeyState(win32con.VK_SHIFT) & 0x8000:
        mods |= Qt.ShiftModifier
    if _user32.GetKeyState(win32con.VK_MENU) & 0x8000:
        mods |= Qt.AltModifier
    return mods


class AccessibleTextArea(QFrame):
    """
    Universal Design Multiline Text Area using native Win32 RICHEDIT50W.
    Exposes the same public API as QPlainTextEdit for Gemvox panels and dialogs.
    """

    textChanged = Signal()
    _active_ref: Optional[weakref.ref] = None

    @classmethod
    def active_editor(cls) -> Optional["AccessibleTextArea"]:
        if cls._active_ref is not None:
            return cls._active_ref()
        return None

    def __init__(self, text: str = "", parent: Optional[QWidget] = None, read_only: bool = False):
        super().__init__(parent)
        _ensure_win32_init()

        self._read_only = False
        self._tab_changes_focus = True
        self._suppress_tab_char = False
        self._suppress_sys_char = False
        self._font = get_qfont(11)
        self._old_wndproc = None
        self._hwnd = 0

        self.setObjectName("AccessibleTextFrame")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setStyleSheet(
            "QFrame#AccessibleTextFrame {"
            "  background-color: #161A26;"
            "  border: 1px solid #2A3142;"
            "  border-radius: 6px;"
            "}"
            "QFrame#AccessibleTextFrame[focused='true'] {"
            "  border: 2px solid #E6B85C;"
            "}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        style = (
            win32con.WS_POPUP
            | win32con.ES_MULTILINE
            | win32con.ES_AUTOVSCROLL
            | win32con.ES_WANTRETURN
            | win32con.WS_VSCROLL
            | win32con.WS_TABSTOP
        )
        win_text = (text or "").replace("\r\n", "\n").replace("\n", "\r\n")
        self._hwnd = _user32.CreateWindowExW(
            0, "RICHEDIT50W", win_text, style, 0, 0, 300, 120, 0, 0, 0, 0
        )

        if self._hwnd:
            # Force plain-text mode so pasted HTML doesn't bring white backgrounds/fonts
            _user32.SendMessageW(self._hwnd, _EM_SETTEXTMODE, _TM_PLAINTEXT, 0)
            _user32.SendMessageW(self._hwnd, _EM_SETBKGNDCOLOR, 0, _BG_COLORREF)
            self._apply_char_format()
            self._install_wndproc()

            self._qwin = QWindow.fromWinId(self._hwnd)
            self._container = QWidget.createWindowContainer(self._qwin, self)
            self._container.setFocusPolicy(Qt.NoFocus)
            layout.addWidget(self._container)
        else:
            self._qwin = None
            self._container = None

        self.setReadOnly(read_only)

    def _apply_char_format(self):
        if not self._hwnd:
            return
        cf = _CHARFORMAT2W()
        cf.cbSize = ctypes.sizeof(_CHARFORMAT2W)
        cf.dwMask = _CFM_FACE | _CFM_SIZE | _CFM_COLOR
        cf.dwEffects = 0
        pt = self._font.pointSize()
        if pt <= 0:
            pt = 11
        cf.yHeight = pt * 20
        cf.crTextColor = _TEXT_COLORREF
        cf.szFaceName = self._font.family()[:31]
        _user32.SendMessageW(self._hwnd, _EM_SETCHARFORMAT, _SCF_ALL, ctypes.byref(cf))

    def _install_wndproc(self):
        self_ref = weakref.ref(self)

        def _wndproc(hwnd, msg, wp, lp):
            obj = self_ref()
            if obj is None:
                return win32gui.DefWindowProc(hwnd, msg, wp, lp)
            return obj._handle_win32_msg(hwnd, msg, wp, lp)

        self._wndproc_cb = _wndproc
        self._old_wndproc = win32gui.SetWindowLong(self._hwnd, win32con.GWL_WNDPROC, self._wndproc_cb)

    def _forward_qt_key(self, qt_key: int, mods: Qt.KeyboardModifiers) -> bool:
        target = self.window()
        if target is None:
            return False
        ev = QKeyEvent(QEvent.KeyPress, qt_key, mods)
        QApplication.sendEvent(target, ev)
        return ev.isAccepted()

    def _return_win32_focus_to_window(self):
        if self._hwnd and _user32.GetFocus() == self._hwnd:
            top = self.window()
            if top is not None and top.winId():
                _user32.SetFocus(int(top.winId()))

    def _move_qt_focus(self, forward: bool):
        self._return_win32_focus_to_window()
        if forward:
            self.focusNextChild()
        else:
            self.focusPreviousChild()

    def _give_win32_focus(self):
        try:
            if not self._hwnd or not self.isVisible():
                return
            if QApplication.focusWidget() is not self:
                return
        except RuntimeError:
            return
        if _user32.GetFocus() != self._hwnd:
            _user32.SetFocus(self._hwnd)
        else:
            _user32.NotifyWinEvent(0x8005, self._hwnd, _OBJID_CLIENT, 0)  # EVENT_OBJECT_FOCUS

    def _handle_win32_msg(self, hwnd, msg, wp, lp):
        if msg == win32con.WM_SETFOCUS:
            AccessibleTextArea._active_ref = weakref.ref(self)
            try:
                self.setProperty("focused", True)
                self.style().polish(self)
            except RuntimeError:
                pass
        elif msg == win32con.WM_KILLFOCUS:
            if AccessibleTextArea.active_editor() is self:
                AccessibleTextArea._active_ref = None
            try:
                self.setProperty("focused", False)
                self.style().polish(self)
            except RuntimeError:
                pass
        elif msg == win32con.WM_CONTEXTMENU:
            if self.contextMenuPolicy() == Qt.CustomContextMenu:
                x = ctypes.c_short(lp & 0xFFFF).value
                y = ctypes.c_short((lp >> 16) & 0xFFFF).value
                if x == -1 and y == -1:
                    local_pos = QPoint(16, 16)
                else:
                    local_pos = self.mapFromGlobal(QPoint(x, y))
                QTimer.singleShot(0, lambda p=local_pos: self.customContextMenuRequested.emit(p))
                return 0
        elif msg == win32con.WM_KEYDOWN or msg == win32con.WM_SYSKEYDOWN:
            mods = _current_qt_modifiers()
            ctrl = bool(mods & Qt.ControlModifier)
            shift = bool(mods & Qt.ShiftModifier)
            alt = bool(mods & Qt.AltModifier)

            if wp == win32con.VK_TAB and self._tab_changes_focus:
                self._suppress_tab_char = True
                if ctrl:
                    QTimer.singleShot(0, lambda m=mods: (self._return_win32_focus_to_window(), self._forward_qt_key(Qt.Key_Tab, m)))
                else:
                    QTimer.singleShot(0, lambda fwd=not shift: self._move_qt_focus(fwd))
                return 0

            if ctrl and wp in (win32con.VK_PRIOR, win32con.VK_NEXT, win32con.VK_RETURN):
                qt_k = _vk_to_qt_key(wp)
                if qt_k is not None:
                    QTimer.singleShot(0, lambda k=qt_k, m=mods: self._forward_qt_key(k, m))
                    return 0

            if alt and not ctrl:
                qt_k = _vk_to_qt_key(wp)
                if qt_k is not None:
                    self._suppress_sys_char = True
                    QTimer.singleShot(0, lambda k=qt_k, m=mods: self._forward_qt_key(k, m))
                    return 0

            if ctrl and wp not in _NATIVE_CTRL_VKS:
                qt_k = _vk_to_qt_key(wp)
                if qt_k is not None:
                    QTimer.singleShot(0, lambda k=qt_k, m=mods: self._forward_qt_key(k, m))
                    return 0

            if not ctrl and not alt and wp in (
                win32con.VK_F1, win32con.VK_F7, win32con.VK_F8, win32con.VK_F9, win32con.VK_F10
            ):
                qt_k = _vk_to_qt_key(wp)
                if qt_k is not None:
                    QTimer.singleShot(0, lambda k=qt_k, m=mods: self._forward_qt_key(k, m))
                    return 0

            if wp == win32con.VK_ESCAPE and not ctrl and not alt:
                QTimer.singleShot(0, lambda m=mods: self._forward_qt_key(Qt.Key_Escape, m))
                return 0

        elif msg == win32con.WM_CHAR:
            if self._suppress_tab_char and wp == 9:
                self._suppress_tab_char = False
                return 0
        elif msg == win32con.WM_SYSCHAR:
            if self._suppress_sys_char:
                self._suppress_sys_char = False
                return 0
        elif msg == win32con.WM_NCDESTROY:
            if AccessibleTextArea.active_editor() is self:
                AccessibleTextArea._active_ref = None
            old = self._old_wndproc
            self._old_wndproc = None
            self._hwnd = 0
            if old:
                return win32gui.CallWindowProc(old, hwnd, msg, wp, lp)

        if self._old_wndproc:
            return win32gui.CallWindowProc(self._old_wndproc, hwnd, msg, wp, lp)
        return win32gui.DefWindowProc(hwnd, msg, wp, lp)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self._hwnd:
            QTimer.singleShot(0, self._give_win32_focus)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        # Only return Win32 focus to the top-level window when focus moved to
        # another Qt widget (not when SetFocus(self._hwnd) caused WM_KILLFOCUS
        # on the parent QWindow, which sets focusWidget() to None).
        if QApplication.focusWidget() is not None:
            self._return_win32_focus_to_window()

    def setFocus(self, reason=Qt.OtherFocusReason):
        super().setFocus(reason)
        if self._hwnd:
            QTimer.singleShot(0, self._give_win32_focus)

    def setTabChangesFocus(self, enabled: bool):
        self._tab_changes_focus = bool(enabled)

    def tabChangesFocus(self) -> bool:
        return self._tab_changes_focus

    def setFont(self, font: QFont):
        super().setFont(font)
        self._font = QFont(font)
        self._apply_char_format()

    def setReadOnly(self, ro: bool):
        self._read_only = bool(ro)
        if self._hwnd:
            _user32.SendMessageW(self._hwnd, _EM_SETREADONLY, 1 if ro else 0, 0)

    def isReadOnly(self) -> bool:
        return self._read_only

    def setAccessibleName(self, name: str):
        cleaned = clean_mnemonic(name)
        super().setAccessibleName(cleaned)
        _set_hwnd_acc_prop(self._hwnd, _PROPID_ACC_NAME, cleaned)

    def setAccessibleDescription(self, desc: str):
        super().setAccessibleDescription(desc)
        _set_hwnd_acc_prop(self._hwnd, _PROPID_ACC_DESCRIPTION, desc)

    def toPlainText(self) -> str:
        if not self._hwnd:
            return ""
        length = _user32.GetWindowTextLengthW(self._hwnd)
        if length <= 0:
            return ""
        buf = ctypes.create_unicode_buffer(length + 2)
        _user32.GetWindowTextW(self._hwnd, buf, length + 2)
        return buf.value.replace("\r\n", "\n").replace("\r", "\n")

    def setPlainText(self, text: str):
        if not self._hwnd:
            return
        win_text = (text or "").replace("\r\n", "\n").replace("\n", "\r\n")
        _user32.SetWindowTextW(self._hwnd, win_text)
        self._apply_char_format()
        self.textChanged.emit()

    def clear(self):
        if self._hwnd:
            _user32.SetWindowTextW(self._hwnd, "")
            self.textChanged.emit()

    def scroll_to_top(self):
        if not self._hwnd:
            return
        _user32.SendMessageW(self._hwnd, _EM_SETSEL, 0, 0)
        _user32.SendMessageW(self._hwnd, _EM_SCROLLCARET, 0, 0)
        _user32.SendMessageW(self._hwnd, win32con.WM_VSCROLL, win32con.SB_TOP, 0)

    def canUndo(self) -> bool:
        return bool(self._hwnd and _user32.SendMessageW(self._hwnd, _EM_CANUNDO, 0, 0))

    def canRedo(self) -> bool:
        return bool(self._hwnd and _user32.SendMessageW(self._hwnd, _EM_CANREDO, 0, 0))

    def canPaste(self) -> bool:
        return bool(self._hwnd and _user32.SendMessageW(self._hwnd, _EM_CANPASTE, 0, 0))

    def hasSelection(self) -> bool:
        if not self._hwnd:
            return False
        cr = _CHARRANGE()
        _user32.SendMessageW(self._hwnd, _EM_EXGETSEL, 0, ctypes.byref(cr))
        return cr.cpMin != cr.cpMax

    def undo(self):
        if self._hwnd:
            _user32.SendMessageW(self._hwnd, _EM_UNDO, 0, 0)

    def redo(self):
        if self._hwnd:
            _user32.SendMessageW(self._hwnd, _EM_REDO, 0, 0)

    def cut(self):
        if self._hwnd:
            _user32.SendMessageW(self._hwnd, win32con.WM_CUT, 0, 0)

    def copy(self):
        if self._hwnd:
            _user32.SendMessageW(self._hwnd, win32con.WM_COPY, 0, 0)

    def paste(self):
        if self._hwnd:
            _user32.SendMessageW(self._hwnd, win32con.WM_PASTE, 0, 0)

    def selectAll(self):
        if self._hwnd:
            _user32.SendMessageW(self._hwnd, _EM_SETSEL, 0, -1)

    def delete_selection_or_char(self):
        if not self._hwnd or self._read_only:
            return
        if self.hasSelection():
            _user32.SendMessageW(self._hwnd, win32con.WM_CLEAR, 0, 0)
        else:
            _user32.SendMessageW(self._hwnd, win32con.WM_KEYDOWN, win32con.VK_DELETE, 0)
            _user32.SendMessageW(self._hwnd, win32con.WM_KEYUP, win32con.VK_DELETE, 0)

    def insert_text_at_selection(self, tag: str):
        if not self._hwnd or self._read_only:
            return
        win_tag = (tag or "").replace("\r\n", "\n").replace("\n", "\r\n")
        _user32.SendMessageW(self._hwnd, _EM_REPLACESEL, 1, ctypes.c_wchar_p(win_tag))
        _user32.SetFocus(self._hwnd)
