"""Pomodoro screen with tabbed interface for timer and stopwatch."""
from PyQt6.QtWidgets import QTabWidget, QWidget, QVBoxLayout

from app.pomodoro_screen.shared_state import SharedTimerState
from app.pomodoro_screen.timer_widget import TimerWidget
from app.pomodoro_screen.stopwatch_widget import StopwatchWidget


class PomodoroWidget(QWidget):
    """Main Pomodoro widget with tabs for timer and stopwatch modes."""

    def __init__(self) -> None:
        super().__init__()

        # Create shared state
        self.shared_state = SharedTimerState()

        # Create main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #282828;
            }
            QTabBar::tab {
                background-color: #282828;
                color: #888;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #3c3c3c;
                color: #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #4c4c4c;
                color: #ffffff;
            }
        """)

        # Create and add timer widget
        self.timer_widget = TimerWidget(self.shared_state)
        self.tabs.addTab(self.timer_widget, "🍅 ポモドーロ")

        # Create and add stopwatch widget
        self.stopwatch_widget = StopwatchWidget(self.shared_state)
        self.tabs.addTab(self.stopwatch_widget, "⏱️ ストップウォッチ")

        # Connect tab change signal to refresh tasks
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Add tabs to layout
        layout.addWidget(self.tabs)

    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change event to refresh task lists."""
        if index == 0:  # Pomodoro tab
            self.timer_widget.refresh_tasks()
        elif index == 1:  # Stopwatch tab
            self.stopwatch_widget.refresh_tasks()
