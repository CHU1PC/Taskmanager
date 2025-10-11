from PyQt6.QtCore import QObject, pyqtSignal


class TimerLogic(QObject):
    state_changed = pyqtSignal(str, int, int)
    sets_updated = pyqtSignal(int)
    phase_finished = pyqtSignal(bool)

    def __init__(self, work_minutes: int, rest_minutes: int):
        super().__init__()
        self.work_minutes = work_minutes
        self.rest_minutes = rest_minutes
        self.is_break = False
        self.remaining_tenths = 0
        self.total_tenths = 0
        self.sets_completed = 0
        self.is_running = False

    def start_stop(self):
        """
        self.is_runningがTrueの時タイマーが進む
        """
        self.is_running = not self.is_running
        if self.is_running and self.remaining_tenths == 0:
            self._start_next_phase()

    def reset(self):
        self.is_running = False
        self.is_break = False
        self.sets_completed = 0
        self._reset_display_state()
        self.sets_updated.emit(self.sets_completed)

    def skip(self):
        if self.is_running:
            self.remaining_tenths = 0

    def tick(self):
        """タイマーの刻み処理。100msごとに呼ばれることを想定。"""
        if not self.is_running or self.remaining_tenths <= 0:
            return

        self.remaining_tenths -= 1
        self._emit_state()

        if self.remaining_tenths == 0:
            self.is_running = False
            if not self.is_break:
                self.sets_completed += 1
                self.sets_updated.emit(self.sets_completed)

            self.phase_finished.emit(self.is_break)
            self.is_break = not self.is_break
            self._reset_display_state()

    def _start_next_phase(self):
        duration_min = self.rest_minutes if self.is_break else self.work_minutes
        self.total_tenths = duration_min * 60 * 10
        self.remaining_tenths = self.total_tenths
        self._emit_state()

    def _reset_display_state(self):
        """現在のフェーズに応じた初期状態を通知する"""
        duration_min = self.rest_minutes if self.is_break else self.work_minutes
        self.total_tenths = duration_min * 60 * 10
        self.remaining_tenths = self.total_tenths
        self._emit_state()

    def _emit_state(self):
        phase = "break" if self.is_break else "work"
        self.state_changed.emit(
            phase,
            self.remaining_tenths // 10,
            self.total_tenths // 10
        )
