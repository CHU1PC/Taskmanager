"""Shared state manager for Pomodoro and Stopwatch widgets."""
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal


class SharedTimerState(QObject):
    """Manages shared state between Pomodoro timer and Stopwatch."""

    # Signals for state changes
    task_changed = pyqtSignal(str)  # Emits task name
    time_updated = pyqtSignal(int)  # Emits elapsed time in tenths of seconds

    def __init__(self) -> None:
        super().__init__()
        self._selected_task: Optional[str] = None
        self._elapsed_tenths: int = 0

    @property
    def selected_task(self) -> Optional[str]:
        """Get currently selected task."""
        return self._selected_task

    @selected_task.setter
    def selected_task(self, task: Optional[str]) -> None:
        """Set selected task and emit signal."""
        if self._selected_task != task:
            self._selected_task = task
            self.task_changed.emit(task or "")

    @property
    def elapsed_tenths(self) -> int:
        """Get elapsed time in tenths of seconds."""
        return self._elapsed_tenths

    @elapsed_tenths.setter
    def elapsed_tenths(self, tenths: int) -> None:
        """Set elapsed time and emit signal."""
        self._elapsed_tenths = tenths
        self.time_updated.emit(tenths)

    def reset(self) -> None:
        """Reset all state."""
        self._elapsed_tenths = 0
        self.time_updated.emit(0)
