"""
Accessible Synthesis Progress Tracker for Gemvox.

Estimates synthesis duration from character count:
    estimated_seconds = 1.5 + (char_count / 50.0)
Drives a smooth visual QProgressBar (0% -> 90% over estimated time,
slowing between 90% and 95% if the API takes longer, then jumping to 100%
when audio is ready) while keeping screen reader announcements strictly
milestone-based (Start, 50%, Complete) plus on-demand status via Ctrl+I.
"""

import math
import time
from PySide6.QtCore import QObject, QTimer, Signal
from gemvox.accessibility import announcer
from gemvox.i18n import tr


def estimate_synthesis_seconds(char_count: int) -> float:
    """Return estimated synthesis time in seconds for a given character count."""
    return 1.5 + (max(0, int(char_count)) / 50.0)


class SynthesisProgressTracker(QObject):
    """Tracks synthesis progress with smooth Qt timer updates and milestone announcements."""

    progress_changed = Signal(int)
    active_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._on_tick)

        self.is_running = False
        self.estimated_seconds = 1.5
        self.elapsed_seconds = 0.0
        self.percent = 0
        self._start_time = 0.0
        self._announced_50 = False

    def start(self, char_count: int):
        """Begin tracking synthesis progress for text of length char_count."""
        self.estimated_seconds = estimate_synthesis_seconds(char_count)
        self.elapsed_seconds = 0.0
        self.percent = 0
        self._announced_50 = False
        self._start_time = time.monotonic()
        self.is_running = True

        self.active_changed.emit(True)
        self.progress_changed.emit(0)

        est_rounded = max(1, round(self.estimated_seconds))
        announcer.announce(tr("announce_synth_start_est", seconds=est_rounded))
        self._timer.start()

    def _on_tick(self):
        if not self.is_running:
            self._timer.stop()
            return

        elapsed = max(0.0, time.monotonic() - self._start_time)
        self.elapsed_seconds = elapsed
        ratio = elapsed / max(0.1, self.estimated_seconds)

        if ratio <= 1.0:
            pct = int(ratio * 90.0)
        else:
            # Smoothly asymptotically approach 95% if API takes longer than estimated
            extra = ratio - 1.0
            pct = 90 + min(5, int(5.0 * (1.0 - math.exp(-extra * 0.5))))

        pct = max(self.percent, min(95, pct))
        if pct != self.percent:
            self.percent = pct
            self.progress_changed.emit(self.percent)

        if self.percent >= 50 and not self._announced_50:
            self._announced_50 = True
            announcer.announce(tr("announce_synth_halfway"))

    def finish(self, success: bool = True):
        """Complete or abort progress tracking."""
        self._timer.stop()
        was_running = self.is_running
        self.is_running = False

        if success:
            self.percent = 100
            self.progress_changed.emit(100)
            if was_running:
                announcer.announce(tr("announce_synth_complete"))
        else:
            self.percent = 0
            self.progress_changed.emit(0)

        self.active_changed.emit(False)

    def announce_status(self):
        """Announce current synthesis status on demand (Ctrl+I)."""
        if self.is_running:
            remaining = max(0, round(self.estimated_seconds - self.elapsed_seconds))
            announcer.announce(
                tr(
                    "announce_synth_status_running",
                    percent=self.percent,
                    remaining=remaining,
                )
            )
        else:
            announcer.announce(tr("announce_synth_status_idle"))
