import os
import shutil
import subprocess
import sys
import threading
import wave
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QEvent, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from gemvox.ui.accessible_text import AccessibleTextArea
from gemvox.config import config
from gemvox.i18n import tr
from gemvox.core.voice_catalog import INLINE_VOCAL_TAGS, get_all_style_presets
from gemvox.core.audio_player import audio_player
from gemvox.core.updater import (
    REPO_URL,
    UpdateInfo,
    check_for_updates,
    download_and_install_update,
)
from gemvox.accessibility import announcer
from gemvox.ui.help_content import HELP_SECTIONS, WELCOME_TOUR_STEPS
from gemvox.ui.player_bar import AudioTransportBar
from gemvox.ui.theme import (
    StudioHeaderBanner,
    apply_accessible,
    call_after,
    clean_mnemonic,
    get_qfont,
    style_button,
    style_label,
)


def open_output_folder():
    """Open the configured audio output directory in the OS file explorer."""
    out_dir = str(config.output_dir.resolve())
    try:
        config.output_dir.mkdir(parents=True, exist_ok=True)
        if hasattr(os, "startfile"):
            os.startfile(out_dir)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", out_dir])
        else:
            subprocess.Popen(["xdg-open", out_dir])
        announcer.announce(tr("announce_opened_output_dir", path=out_dir))
    except Exception as e:
        announcer.announce(tr("status_error", error=e))


def _open_url_safe(url: str):
    if not QDesktopServices.openUrl(QUrl(url)):
        webbrowser.open(url)


class _BaseStudioDialog(QDialog):
    """Base Universal Design dialog with Alt+<Key> mnemonic hook support."""

    def __init__(self, parent: Optional[QWidget], title: str):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setAccessibleName(clean_mnemonic(title))
        self.setModal(True)

    def _alt_char(self, event: QKeyEvent) -> Optional[str]:
        mods = event.modifiers()
        if (mods & Qt.AltModifier) and not (mods & Qt.ControlModifier) and not (mods & Qt.ShiftModifier):
            key = event.key()
            if Qt.Key_A <= key <= Qt.Key_Z:
                return chr(key)
        return None


class InlineTagDialog(_BaseStudioDialog):
    """Accessible dialog to select and insert inline vocal tags."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent, tr("dlg_tag_title"))
        self.selected_tag: Optional[str] = None
        self._init_ui()

    def _init_ui(self):
        self.resize(600, 480)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(
            StudioHeaderBanner(
                title=tr("dlg_tag_banner_title"),
                subtitle=tr("dlg_tag_banner_sub"),
                badge_text="VOCAL TAG",
            )
        )

        body = QVBoxLayout()
        body.setContentsMargins(14, 12, 14, 14)
        body.setSpacing(10)

        info_label = QLabel(tr("dlg_tag_info"), self)
        info_label.setWordWrap(True)
        style_label(info_label, "muted")
        body.addWidget(info_label)

        self.listbox = QListWidget(self)
        choices = [f"{item['tag']} - {item['label']}: {item['description']}" for item in INLINE_VOCAL_TAGS]
        self.listbox.addItems(choices)
        if choices:
            self.listbox.setCurrentRow(0)
        apply_accessible(
            self.listbox,
            name="Vocal Tags List",
            description=tr("dlg_tag_info"),
        )
        body.addWidget(self.listbox, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        insert_btn = QPushButton(tr("btn_insert"), self)
        insert_btn.setDefault(True)
        style_button(insert_btn, "primary")

        cancel_btn = QPushButton(tr("btn_cancel"), self)
        style_button(cancel_btn, "secondary")

        btn_row.addWidget(insert_btn)
        btn_row.addWidget(cancel_btn)
        body.addLayout(btn_row)

        layout.addLayout(body, 1)

        insert_btn.clicked.connect(self.on_insert)
        cancel_btn.clicked.connect(self.reject)
        self.listbox.itemDoubleClicked.connect(lambda *_: self.on_insert())
        self.listbox.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        ch = self._alt_char(event)
        if ch == "I":
            self.on_insert()
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.listbox.hasFocus():
            self.on_insert()
            return
        super().keyPressEvent(event)

    def on_insert(self, *args):
        sel = self.listbox.currentRow()
        if 0 <= sel < len(INLINE_VOCAL_TAGS):
            self.selected_tag = INLINE_VOCAL_TAGS[sel]["tag"]
            self.accept()
        else:
            self.reject()


class CreateCustomStyleDialog(_BaseStudioDialog):
    """Accessible dialog to create and save a reusable custom style preset."""

    def __init__(self, parent: Optional[QWidget] = None, initial_style: str = ""):
        super().__init__(parent, tr("dlg_custom_style_title"))
        self.initial_style = initial_style
        self.created_name: Optional[str] = None
        self.created_style: Optional[str] = None
        self._init_ui()

    def _init_ui(self):
        self.resize(600, 340)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(
            StudioHeaderBanner(
                title=tr("dlg_custom_style_banner"),
                subtitle=tr("dlg_custom_style_sub"),
                badge_text="CUSTOM PRESET",
            )
        )

        body = QVBoxLayout()
        body.setContentsMargins(14, 12, 14, 14)
        body.setSpacing(12)

        info = QLabel(tr("dlg_custom_style_info"), self)
        info.setWordWrap(True)
        style_label(info, "muted")
        body.addWidget(info)

        form = QFormLayout()
        form.setSpacing(10)

        lbl_name = QLabel(tr("lbl_preset_name"), self)
        self.txt_name = QLineEdit(self)
        apply_accessible(self.txt_name, name=tr("lbl_preset_name"), label=lbl_name)
        form.addRow(lbl_name, self.txt_name)

        lbl_style = QLabel(tr("lbl_preset_style"), self)
        self.txt_style = QLineEdit(self.initial_style, self)
        apply_accessible(self.txt_style, name=tr("lbl_preset_style"), label=lbl_style)
        form.addRow(lbl_style, self.txt_style)

        body.addLayout(form)
        body.addStretch(1)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        save_btn = QPushButton(tr("btn_save_preset"), self)
        save_btn.setDefault(True)
        style_button(save_btn, "primary")

        cancel_btn = QPushButton(tr("btn_cancel"), self)
        style_button(cancel_btn, "secondary")

        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        body.addLayout(btn_row)

        layout.addLayout(body, 1)

        save_btn.clicked.connect(self.on_save)
        cancel_btn.clicked.connect(self.reject)
        self.txt_name.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        ch = self._alt_char(event)
        if ch == "N":
            self.txt_name.setFocus()
            return
        if ch == "S":
            self.txt_style.setFocus()
            return
        if ch == "P":
            self.on_save()
            return
        super().keyPressEvent(event)

    def on_save(self, *args):
        name = self.txt_name.text().strip()
        style = self.txt_style.text().strip()
        if not name:
            announcer.announce(tr("announce_enter_preset_name"))
            self.txt_name.setFocus()
            return
        if not style:
            announcer.announce(tr("announce_enter_preset_style"))
            self.txt_style.setFocus()
            return

        config.add_custom_style(name, style)
        self.created_name = name
        self.created_style = style
        announcer.play_sound("success")
        self.accept()


class StylePresetDialog(_BaseStudioDialog):
    """Accessible dialog to pick from pre-tuned emotion and custom style presets."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent, tr("dlg_style_title"))
        self.selected_style: Optional[str] = None
        self.presets = []
        self._init_ui()

    def _init_ui(self):
        self.resize(660, 510)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(
            StudioHeaderBanner(
                title=tr("dlg_style_banner"),
                subtitle=tr("dlg_style_sub"),
                badge_text="STYLE STUDIO",
            )
        )

        body = QVBoxLayout()
        body.setContentsMargins(14, 12, 14, 14)
        body.setSpacing(10)

        info = QLabel(tr("dlg_style_info"), self)
        info.setWordWrap(True)
        style_label(info, "muted")
        body.addWidget(info)

        self.listbox = QListWidget(self)
        apply_accessible(
            self.listbox,
            name="Style Presets List",
            description=tr("dlg_style_info"),
        )
        body.addWidget(self.listbox, 1)

        action_row = QHBoxLayout()
        self.btn_create_custom = QPushButton(tr("btn_create_style"), self)
        style_button(self.btn_create_custom, "gold")

        self.btn_delete_custom = QPushButton(tr("btn_delete_custom"), self)
        style_button(self.btn_delete_custom, "danger")

        action_row.addWidget(self.btn_create_custom)
        action_row.addWidget(self.btn_delete_custom)
        action_row.addStretch(1)
        body.addLayout(action_row)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        apply_btn = QPushButton(tr("btn_apply_style"), self)
        apply_btn.setDefault(True)
        style_button(apply_btn, "primary")

        cancel_btn = QPushButton(tr("btn_cancel"), self)
        style_button(cancel_btn, "secondary")

        btn_row.addWidget(apply_btn)
        btn_row.addWidget(cancel_btn)
        body.addLayout(btn_row)

        layout.addLayout(body, 1)

        self.refresh_presets()

        apply_btn.clicked.connect(self.on_apply)
        cancel_btn.clicked.connect(self.reject)
        self.listbox.itemDoubleClicked.connect(lambda *_: self.on_apply())
        self.listbox.currentRowChanged.connect(lambda *_: self._update_delete_button())
        self.btn_create_custom.clicked.connect(self.on_create_custom)
        self.btn_delete_custom.clicked.connect(self.on_delete_custom)
        self.listbox.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        ch = self._alt_char(event)
        if ch == "C":
            self.on_create_custom()
            return
        if ch == "D" and self.btn_delete_custom.isEnabled():
            self.on_delete_custom()
            return
        if ch == "A":
            self.on_apply()
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.listbox.hasFocus():
            self.on_apply()
            return
        super().keyPressEvent(event)

    def refresh_presets(self, select_name: Optional[str] = None):
        self.presets = get_all_style_presets()
        self.listbox.clear()
        sel_idx = 0
        for idx, item in enumerate(self.presets):
            prefix = "[Custom] " if item.get("is_custom") else ""
            self.listbox.addItem(f"{prefix}{item['name']} -> \"{item['style']}\"")
            if select_name and item["name"].lower() == select_name.lower():
                sel_idx = idx
        if self.presets:
            self.listbox.setCurrentRow(sel_idx)
        self._update_delete_button()

    def _update_delete_button(self):
        sel = self.listbox.currentRow()
        is_custom = 0 <= sel < len(self.presets) and bool(self.presets[sel].get("is_custom"))
        self.btn_delete_custom.setEnabled(is_custom)

    def on_create_custom(self, *args):
        dlg = CreateCustomStyleDialog(self)
        if dlg.exec() == QDialog.Accepted and dlg.created_name:
            self.refresh_presets(select_name=dlg.created_name)
            self.listbox.setFocus()
            announcer.announce(tr("announce_created_custom_style", name=dlg.created_name))

    def on_delete_custom(self, *args):
        sel = self.listbox.currentRow()
        if 0 <= sel < len(self.presets) and self.presets[sel].get("is_custom"):
            name = self.presets[sel]["name"]
            config.remove_custom_style(name)
            self.refresh_presets()
            self.listbox.setFocus()
            announcer.announce(tr("announce_deleted_custom_style", name=name))

    def on_apply(self, *args):
        sel = self.listbox.currentRow()
        if 0 <= sel < len(self.presets):
            self.selected_style = self.presets[sel]["style"]
            self.accept()
        else:
            self.reject()


class GenerationHistoryDialog(_BaseStudioDialog):
    """Accessible dialog for browsing, replaying, exporting, and managing generated WAV files."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent, tr("dlg_history_title"))
        self.files_data: list[Path] = []
        self._init_ui()
        self.refresh_history(announce=False)

    def _init_ui(self):
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(
            StudioHeaderBanner(
                title=tr("dlg_history_banner"),
                subtitle=tr("dlg_history_sub"),
                badge_text="AUDIO HISTORY",
            )
        )

        body = QVBoxLayout()
        body.setContentsMargins(14, 12, 14, 14)
        body.setSpacing(10)

        info = QLabel(tr("dlg_history_info"), self)
        info.setWordWrap(True)
        style_label(info, "muted")
        body.addWidget(info)

        lbl_list = QLabel(tr("lbl_history_list"), self)
        style_label(lbl_list, "section")
        body.addWidget(lbl_list)

        self.listbox = QListWidget(self)
        apply_accessible(self.listbox, name=tr("lbl_history_list"), label=lbl_list)
        body.addWidget(self.listbox, 1)

        self.player_bar = AudioTransportBar(
            self,
            get_audio_bytes_cb=self._read_selected_wav_bytes,
        )
        self.btn_play = self.player_bar.btn_play
        self.btn_stop = self.player_bar.btn_stop
        body.addWidget(self.player_bar)

        act_row = QHBoxLayout()
        self.btn_save_as = QPushButton(tr("btn_hist_save_as"), self)
        self.btn_delete = QPushButton(tr("btn_hist_delete"), self)
        self.btn_open_folder = QPushButton(tr("btn_hist_open_folder"), self)
        self.btn_refresh = QPushButton(tr("btn_hist_refresh"), self)
        close_btn = QPushButton(tr("btn_close"), self)

        style_button(self.btn_save_as, "gold")
        style_button(self.btn_delete, "danger")
        style_button(self.btn_open_folder, "secondary")
        style_button(self.btn_refresh, "secondary")
        style_button(close_btn, "primary")

        act_row.addWidget(self.btn_save_as)
        act_row.addWidget(self.btn_delete)
        act_row.addWidget(self.btn_open_folder)
        act_row.addWidget(self.btn_refresh)
        act_row.addStretch(1)
        act_row.addWidget(close_btn)
        body.addLayout(act_row)

        layout.addLayout(body, 1)

        self.btn_save_as.clicked.connect(self.on_save_as)
        self.btn_delete.clicked.connect(self.on_delete)
        self.btn_open_folder.clicked.connect(lambda *_: open_output_folder())
        self.btn_refresh.clicked.connect(lambda *_: self.refresh_history(announce=True))
        close_btn.clicked.connect(self.reject)
        self.listbox.currentRowChanged.connect(self.on_select_item)
        self.listbox.itemDoubleClicked.connect(lambda *_: self.on_play_selected())

        self.listbox.setFocus()

    def _read_selected_wav_bytes(self) -> Optional[bytes]:
        target = self._get_selected_file()
        if target and target.is_file():
            try:
                return target.read_bytes()
            except Exception:
                return None
        return None

    def on_select_item(self, *args):
        if not audio_player.is_active:
            data = self._read_selected_wav_bytes()
            if data:
                self.player_bar.set_audio_ready(True, data)

    def on_play_selected(self, *args):
        data = self._read_selected_wav_bytes()
        if data:
            audio_player.play_wav_bytes(data, announce_on_start=True)

    def _get_wav_duration_from_file(self, path: Path) -> float:
        try:
            with wave.open(str(path), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0:
                    return round(frames / float(rate), 2)
        except Exception:
            pass
        return 0.0

    def refresh_history(self, announce: bool = False):
        self.files_data = []
        self.listbox.clear()
        out_dir = config.output_dir
        wav_files = []
        try:
            if out_dir.is_dir():
                wav_files = sorted(
                    out_dir.glob("*.wav"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
        except Exception:
            wav_files = []

        choices = []
        for p in wav_files:
            try:
                st = p.stat()
                size_kb = max(1, round(st.st_size / 1024))
                mtime_str = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                dur = self._get_wav_duration_from_file(p)
                self.files_data.append(p)
                choices.append(f"{p.name}  |  {dur}s  |  {size_kb} KB  |  {mtime_str}")
            except Exception:
                pass

        if choices:
            self.listbox.addItems(choices)
            self.listbox.setCurrentRow(0)
            self.player_bar.set_audio_ready(True, self._read_selected_wav_bytes())
            self.btn_save_as.setEnabled(True)
            self.btn_delete.setEnabled(True)
        else:
            self.listbox.addItem(tr("msg_history_empty"))
            self.listbox.setCurrentRow(0)
            self.player_bar.set_audio_ready(False)
            self.btn_save_as.setEnabled(False)
            self.btn_delete.setEnabled(False)

        if announce:
            announcer.announce(tr("announce_history_count", count=len(self.files_data)))

    def _get_selected_file(self) -> Optional[Path]:
        sel = self.listbox.currentRow()
        if 0 <= sel < len(self.files_data):
            return self.files_data[sel]
        return None

    def on_play_stop(self, *args):
        self.player_bar.on_play_pause()

    def on_save_as(self, *args):
        target = self._get_selected_file()
        if not target or not target.is_file():
            return
        dest, _ = QFileDialog.getSaveFileName(
            self,
            tr("menu_save_audio_help"),
            str(config.output_dir / target.name),
            "WAV Audio (*.wav)",
        )
        if dest:
            try:
                shutil.copy2(target, dest)
                announcer.announce(tr("announce_audio_saved", path=dest))
            except Exception as e:
                announcer.announce(tr("status_error", error=e))

    def on_delete(self, *args):
        target = self._get_selected_file()
        if not target or not target.is_file():
            return
        resp = QMessageBox.warning(
            self,
            tr("confirm_delete_audio_title"),
            tr("confirm_delete_audio_msg", filename=target.name),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            try:
                if audio_player.is_active:
                    audio_player.stop()
                target.unlink()
                announcer.announce(tr("announce_history_deleted", filename=target.name))
                self.refresh_history(announce=False)
                self.listbox.setFocus()
            except Exception as e:
                announcer.announce(tr("status_error", error=e))

    def keyPressEvent(self, event: QKeyEvent):
        mods = event.modifiers()
        key = event.key()
        if mods == Qt.NoModifier:
            if key in (Qt.Key_Return, Qt.Key_Enter) and self.listbox.hasFocus():
                self.on_play_selected()
                return
            if key == Qt.Key_Delete and self.listbox.hasFocus():
                self.on_delete()
                return
            if key == Qt.Key_F7:
                audio_player.skip(-5.0, announce=True)
                return
            if key == Qt.Key_F8:
                audio_player.skip(5.0, announce=True)
                return
            if key == Qt.Key_F9:
                audio_player.change_volume(-10, announce=True)
                return
            if key == Qt.Key_F10:
                audio_player.change_volume(10, announce=True)
                return
        if mods == Qt.ControlModifier and key == Qt.Key_L:
            audio_player.toggle_loop(announce=True)
            return
        ch = self._alt_char(event)
        if ch == "P" and self.btn_play.isEnabled():
            self.on_play_stop()
            return
        if ch == "Q":
            audio_player.stop(announce=True)
            return
        if ch == "S" and self.btn_save_as.isEnabled():
            self.on_save_as()
            return
        if ch == "D" and self.btn_delete.isEnabled():
            self.on_delete()
            return
        if ch == "L":
            open_output_folder()
            return
        if ch == "R":
            self.refresh_history(announce=True)
            return
        if ch == "G":
            self.listbox.setFocus()
            return
        if ch == "C":
            self.reject()
            return
        super().keyPressEvent(event)


class UpdateDialog(_BaseStudioDialog):
    """Accessible Direct GitHub Auto-Updater Dialog (Ctrl+U)."""

    def __init__(self, parent: Optional[QWidget] = None, initial_info: Optional[UpdateInfo] = None):
        super().__init__(parent, tr("dlg_update_title"))
        self.update_info: Optional[UpdateInfo] = None
        self._is_busy = False
        self._last_announced_milestone = -1
        self._alive = True
        self.destroyed.connect(self._on_destroyed)
        self._init_ui()
        if initial_info is not None:
            call_after(self._on_check_completed, initial_info)
        else:
            call_after(self.start_check)

    def _on_destroyed(self, *args):
        self._alive = False

    def _init_ui(self):
        self.resize(760, 520)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(
            StudioHeaderBanner(
                title=tr("dlg_update_banner"),
                subtitle=tr("dlg_update_sub"),
                badge_text="GITHUB UPDATER",
            )
        )

        body = QVBoxLayout()
        body.setContentsMargins(14, 12, 14, 14)
        body.setSpacing(10)

        self.lbl_status = QLabel(tr("upd_checking"), self)
        style_label(self.lbl_status, "status")
        body.addWidget(self.lbl_status)

        self.gauge = QProgressBar(self)
        self.gauge.setRange(0, 100)
        self.gauge.setValue(0)
        apply_accessible(self.gauge, name="Update Download Progress")
        body.addWidget(self.gauge)

        lbl_notes = QLabel(tr("lbl_upd_notes"), self)
        style_label(lbl_notes, "section")
        body.addWidget(lbl_notes)

        self.txt_notes = AccessibleTextArea(tr("upd_checking"), self, read_only=True)
        self.txt_notes.setTabChangesFocus(True)
        self.txt_notes.setFont(get_qfont(10, mono=True))
        apply_accessible(self.txt_notes, name=tr("lbl_upd_notes"), label=lbl_notes)
        body.addWidget(self.txt_notes, 1)

        btn_row = QHBoxLayout()
        self.btn_install = QPushButton(tr("btn_upd_install"), self)
        self.btn_install.setEnabled(False)
        self.btn_check = QPushButton(tr("btn_upd_check"), self)
        self.btn_open_repo = QPushButton(tr("btn_upd_open_repo"), self)
        self.btn_close = QPushButton(tr("btn_close"), self)

        style_button(self.btn_install, "gold")
        style_button(self.btn_check, "secondary")
        style_button(self.btn_open_repo, "secondary")
        style_button(self.btn_close, "primary")

        btn_row.addWidget(self.btn_install)
        btn_row.addWidget(self.btn_check)
        btn_row.addWidget(self.btn_open_repo)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_close)
        body.addLayout(btn_row)

        layout.addLayout(body, 1)

        self.btn_install.clicked.connect(self.on_install)
        self.btn_check.clicked.connect(lambda *_: self.start_check())
        self.btn_open_repo.clicked.connect(self.on_open_repo)
        self.btn_close.clicked.connect(self.reject)

    def _mode_display_name(self, mode: str) -> str:
        if mode == "standalone_exe":
            return tr("upd_mode_standalone")
        if mode == "portable_dir":
            return tr("upd_mode_portable")
        return tr("upd_mode_source")

    def start_check(self):
        if self._is_busy or not self._alive:
            return
        self._is_busy = True
        self.btn_install.setEnabled(False)
        self.btn_check.setEnabled(False)
        self.gauge.setRange(0, 0)  # Indeterminate pulse
        self.lbl_status.setText(tr("upd_checking"))
        self.txt_notes.setPlainText(
            f"Repository : {REPO_URL}\n"
            f"Status     : {tr('upd_checking')}\n"
        )
        announcer.announce(tr("upd_checking"))

        def _worker():
            info = check_for_updates()
            call_after(self._on_check_completed, info)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_check_completed(self, info: UpdateInfo):
        if not self._alive:
            return
        self._is_busy = False
        self.update_info = info
        self.gauge.setRange(0, 100)
        self.gauge.setValue(0)
        self.btn_check.setEnabled(True)

        if info.error:
            status_msg = tr("upd_error_status", error=info.error)
            self.lbl_status.setText(status_msg)
            self.txt_notes.setPlainText(
                f"Repository : {REPO_URL}\n"
                f"Error      : {info.error}\n"
            )
            announcer.play_sound("error")
            announcer.announce(tr("upd_error_announce", error=info.error))
            return

        mode_label = self._mode_display_name(info.install_mode)
        if info.is_newer:
            status_msg = tr(
                "upd_available_status",
                latest=info.latest_version,
                current=info.current_version,
                mode=mode_label,
            )
            self.btn_install.setText(tr("btn_upd_install"))
            style_button(self.btn_install, "gold")
            self.btn_install.setEnabled(True)
            self.btn_install.setDefault(True)
            announcer.play_sound("complete")
            announcer.announce(tr("upd_available_announce", latest=info.latest_version))
        else:
            status_msg = tr(
                "upd_up_to_date_status",
                current=info.current_version,
                mode=mode_label,
            )
            self.btn_install.setText(tr("btn_upd_reinstall"))
            style_button(self.btn_install, "gold")
            self.btn_install.setEnabled(bool(info.download_url))
            announcer.play_sound("success")
            announcer.announce(tr("upd_up_to_date_announce", current=info.current_version))

        self.lbl_status.setText(status_msg)
        details = (
            f"====================================================================\n"
            f"GEMVOX DIRECT GITHUB AUTO-UPDATER\n"
            f"====================================================================\n"
            f"GitHub Repository : {REPO_URL}\n"
            f"Current Version   : v{info.current_version}\n"
            f"Latest Version    : v{info.latest_version}\n"
            f"Installation Mode : {mode_label}\n"
            f"Update Package    : {info.asset_name}\n"
            f"Published At      : {info.published_at or 'Latest'}\n"
            f"====================================================================\n\n"
            f"RELEASE NOTES & DETAILS:\n"
            f"{info.release_notes}\n"
        )
        self.txt_notes.setPlainText(details)
        self.txt_notes.scroll_to_top()
        if info.is_newer:
            self.btn_install.setFocus()
        else:
            self.txt_notes.setFocus()

    def on_install(self, *args):
        if self._is_busy or not self.update_info or not self.update_info.download_url:
            return
        self._is_busy = True
        self._last_announced_milestone = -1
        self.btn_install.setEnabled(False)
        self.btn_check.setEnabled(False)
        self.btn_close.setEnabled(False)
        self.gauge.setRange(0, 100)
        self.gauge.setValue(0)
        announcer.play_sound("start")
        announcer.announce(tr("upd_downloading_announce"))

        def _progress(percent: int, stage: str):
            def _ui():
                if not self._alive:
                    return
                pct = max(0, min(100, int(percent)))
                self.gauge.setValue(pct)
                self.lbl_status.setText(tr("upd_downloading_status", stage=stage, percent=pct))
                milestone = (pct // 25) * 25
                if milestone in (25, 50, 75, 100) and milestone > self._last_announced_milestone:
                    self._last_announced_milestone = milestone
                    announcer.announce(f"{pct}%", interrupt=False)

            call_after(_ui)

        def _worker():
            ok, msg = download_and_install_update(self.update_info, progress_callback=_progress)
            call_after(self._on_install_completed, ok, msg)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_install_completed(self, ok: bool, msg: str):
        if not self._alive:
            return
        self._is_busy = False
        if not ok:
            self.btn_install.setEnabled(True)
            self.btn_check.setEnabled(True)
            self.btn_close.setEnabled(True)
            err_text = tr("upd_error_status", error=msg)
            self.lbl_status.setText(err_text)
            announcer.play_sound("error")
            announcer.announce(tr("upd_error_announce", error=msg))
            return

        self.gauge.setValue(100)
        self.lbl_status.setText(msg)
        announcer.play_sound("success")
        announcer.announce(tr("upd_installing_announce"))
        self.accept()
        app = QApplication.instance()
        if app:
            app.quit()

    def on_open_repo(self, *args):
        target_url = REPO_URL
        if self.update_info and self.update_info.html_url:
            target_url = self.update_info.html_url
        _open_url_safe(target_url)

    def keyPressEvent(self, event: QKeyEvent):
        ch = self._alt_char(event)
        if ch == "N":
            self.txt_notes.setFocus()
            return
        if ch == "I" and self.btn_install.isEnabled():
            self.on_install()
            return
        if ch == "G" and self.btn_check.isEnabled():
            self.start_check()
            return
        if ch == "R":
            self.on_open_repo()
            return
        if ch == "C" and self.btn_close.isEnabled():
            self.reject()
            return
        super().keyPressEvent(event)


class WelcomeTourDialog(_BaseStudioDialog):
    """First-run Welcome Screen & Guided Setup Tour."""

    ID_GO_SETTINGS = 100

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent, tr("welcome_title"))
        self.steps = WELCOME_TOUR_STEPS.get(config.language, WELCOME_TOUR_STEPS["en"])
        self.current_step = 0
        self._init_ui()

    def _init_ui(self):
        self.resize(760, 540)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(
            StudioHeaderBanner(
                title=tr("welcome_banner_title"),
                subtitle=tr("welcome_banner_sub"),
                badge_text="SETUP TOUR",
            )
        )

        body = QVBoxLayout()
        body.setContentsMargins(14, 12, 14, 14)
        body.setSpacing(10)

        self.lbl_step = QLabel("", self)
        style_label(self.lbl_step, "section")
        body.addWidget(self.lbl_step)

        self.txt_body = AccessibleTextArea("", self, read_only=True)
        self.txt_body.setTabChangesFocus(True)
        self.txt_body.setFont(get_qfont(10.5))
        apply_accessible(self.txt_body, name="Welcome Tour Content", label=self.lbl_step)
        body.addWidget(self.txt_body, 1)

        btn_row = QHBoxLayout()
        self.btn_prev = QPushButton(tr("btn_prev_step"), self)
        self.btn_next = QPushButton(tr("btn_next_step"), self)
        self.btn_go_settings = QPushButton(tr("btn_go_settings"), self)
        self.btn_go_settings.setDefault(True)
        self.btn_close = QPushButton(tr("btn_skip_tour"), self)

        style_button(self.btn_prev, "secondary")
        style_button(self.btn_next, "secondary")
        style_button(self.btn_go_settings, "gold")
        style_button(self.btn_close, "primary")

        btn_row.addWidget(self.btn_prev)
        btn_row.addWidget(self.btn_next)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_go_settings)
        btn_row.addWidget(self.btn_close)
        body.addLayout(btn_row)

        layout.addLayout(body, 1)

        self.btn_prev.clicked.connect(self.on_prev)
        self.btn_next.clicked.connect(self.on_next)
        self.btn_go_settings.clicked.connect(self.on_go_settings)
        self.btn_close.clicked.connect(self.on_close)

        self._update_step_view(announce_step=False)
        self.txt_body.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        ch = self._alt_char(event)
        if ch == "P" and self.btn_prev.isEnabled():
            self.on_prev()
            return
        if ch == "N" and self.btn_next.isEnabled():
            self.on_next()
            return
        if ch == "G":
            self.on_go_settings()
            return
        if ch == "S":
            self.on_close()
            return
        super().keyPressEvent(event)

    def _update_step_view(self, announce_step: bool = True):
        step_data = self.steps[self.current_step]
        total = len(self.steps)
        header_text = tr(
            "welcome_step_indicator",
            step=self.current_step + 1,
            total=total,
            title=step_data["title"],
        )
        self.lbl_step.setText(header_text)
        self.txt_body.setPlainText(step_data["body"])
        self.txt_body.scroll_to_top()

        self.btn_prev.setEnabled(self.current_step > 0)
        self.btn_next.setEnabled(self.current_step < total - 1)

        if announce_step:
            announcer.announce(f"{header_text}. {step_data['body']}")

    def on_prev(self, *args):
        if self.current_step > 0:
            self.current_step -= 1
            self._update_step_view(announce_step=True)
            self.txt_body.setFocus()

    def on_next(self, *args):
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self._update_step_view(announce_step=True)
            self.txt_body.setFocus()

    def on_go_settings(self, *args):
        config.set("first_run_completed", True)
        self.done(self.ID_GO_SETTINGS)

    def on_close(self, *args):
        config.set("first_run_completed", True)
        self.reject()


class HelpDialog(_BaseStudioDialog):
    """Systematic Step-by-Step User Guide & Visual Help Mode (F1)."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent, tr("help_title"))
        self.sections = HELP_SECTIONS.get(config.language, HELP_SECTIONS["en"])
        self._init_ui()

    def _init_ui(self):
        self.resize(880, 640)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(
            StudioHeaderBanner(
                title=tr("help_banner_title"),
                subtitle=tr("help_banner_sub"),
                badge_text="F1 USER GUIDE",
            )
        )

        body = QVBoxLayout()
        body.setContentsMargins(14, 12, 14, 14)
        body.setSpacing(12)

        split_row = QHBoxLayout()
        split_row.setSpacing(12)

        # Left column: Topics List
        left_col = QVBoxLayout()
        left_col.setSpacing(6)
        lbl_topics = QLabel(tr("help_topics_label"), self)
        style_label(lbl_topics, "section")
        left_col.addWidget(lbl_topics)

        self.list_topics = QListWidget(self)
        self.list_topics.setFixedWidth(280)
        topic_titles = [s["title"] for s in self.sections]
        self.list_topics.addItems(topic_titles)
        apply_accessible(self.list_topics, name=tr("help_topics_label"), label=lbl_topics)
        left_col.addWidget(self.list_topics, 1)
        split_row.addLayout(left_col)

        # Right column: Content Viewer
        right_col = QVBoxLayout()
        right_col.setSpacing(6)
        lbl_content = QLabel(tr("help_content_label"), self)
        style_label(lbl_content, "section")
        right_col.addWidget(lbl_content)

        self.txt_content = AccessibleTextArea("", self, read_only=True)
        self.txt_content.setTabChangesFocus(True)
        self.txt_content.setFont(get_qfont(10, mono=True))
        apply_accessible(self.txt_content, name=tr("help_content_label"), label=lbl_content)
        right_col.addWidget(self.txt_content, 1)
        split_row.addLayout(right_col, 1)

        body.addLayout(split_row, 1)

        btn_row = QHBoxLayout()
        btn_tour = QPushButton(tr("btn_open_tour"), self)
        style_button(btn_tour, "gold")

        close_btn = QPushButton(tr("btn_close"), self)
        close_btn.setDefault(True)
        style_button(close_btn, "primary")

        btn_row.addWidget(btn_tour)
        btn_row.addStretch(1)
        btn_row.addWidget(close_btn)
        body.addLayout(btn_row)

        layout.addLayout(body, 1)

        self.list_topics.currentRowChanged.connect(self.on_topic_selected)
        btn_tour.clicked.connect(self.on_open_tour)
        close_btn.clicked.connect(self.reject)

        if topic_titles:
            self.list_topics.setCurrentRow(0)
            self._load_section(0, announce=False)

        self.list_topics.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        ch = self._alt_char(event)
        if ch == "T":
            self.list_topics.setFocus()
            return
        if ch == "G":
            self.txt_content.setFocus()
            return
        if ch == "W":
            self.on_open_tour()
            return
        if ch == "C":
            self.reject()
            return
        super().keyPressEvent(event)

    def _load_section(self, idx: int, announce: bool = False):
        if 0 <= idx < len(self.sections):
            sec = self.sections[idx]
            self.txt_content.setPlainText(sec["content"])
            self.txt_content.scroll_to_top()
            if announce:
                announcer.announce(sec["title"])

    def on_topic_selected(self, row: int):
        if row >= 0:
            self._load_section(row, announce=True)

    def on_open_tour(self, *args):
        dlg = WelcomeTourDialog(self)
        res = dlg.exec()
        if res == WelcomeTourDialog.ID_GO_SETTINGS:
            self.done(WelcomeTourDialog.ID_GO_SETTINGS)
