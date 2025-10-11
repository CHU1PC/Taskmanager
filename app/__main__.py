import os
import sys

# Suppress FFmpeg warnings for MP3 playback
os.environ['QT_LOGGING_RULES'] = 'qt.multimedia.ffmpeg=false'

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from app.pomodoro_screen import PomodoroWidget
from app.task_screen import TasksWidget
from app.urgency_screen import UrgencyWidget
from app.calendar_screen import CalendarWidget
from app.utils import resource_path


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Time manager App")
        self.setStyleSheet("background-color: #282828")
        self.resize(1000, 700)

        central = QWidget(self)
        main_layout = QHBoxLayout(central)
        self.setCentralWidget(central)

        self.nav = QListWidget(self)
        self.nav.setFixedWidth(50)
        self.nav.setIconSize(QSize(24, 24))
        self.nav.setStyleSheet("background-color: #414141")

        menu_items = [
            (resource_path("img/pomodoro.png"), "ポモドーロ"),
            (resource_path("img/tasks.png"), "タスク"),
            (resource_path("img/matrix.png"), "マトリックス"),
            (resource_path("img/calendar.png"), "カレンダー")
        ]

        for icon_path, text in menu_items:
            item = QListWidgetItem("")
            item.setIcon(QIcon(icon_path))

            item.setToolTip(text)

            self.nav.addItem(item)
        main_layout.addWidget(self.nav)

        # ウィジェットを作成して参照を保持
        self.pomodoro_widget = PomodoroWidget()
        self.tasks_widget = TasksWidget()
        self.urgency_widget = UrgencyWidget()
        self.calendar_widget = CalendarWidget()

        self.stack = QStackedWidget()
        self.stack.addWidget(self.pomodoro_widget)
        self.stack.addWidget(self.tasks_widget)
        self.stack.addWidget(self.urgency_widget)
        self.stack.addWidget(self.calendar_widget)

        main_layout.addWidget(self.stack, stretch=1)

        self.nav.currentRowChanged.connect(self.reset_urgency)  # type: ignore
        self.nav.setCurrentRow(0)

    def reset_urgency(self, current_row: int) -> None:
        self.stack.setCurrentIndex(current_row)
        if current_row == 0:
            # Refresh task lists in timer tabs
            self.pomodoro_widget.timer_widget.refresh_tasks()
            self.pomodoro_widget.simple_tracker_widget.refresh_tasks()
        elif current_row == 2:
            self.urgency_widget.refresh_tasks()
        elif current_row == 3:
            # Refresh calendar data when switching to calendar view
            self.calendar_widget._load_data()
            if self.calendar_widget.current_view == "month":
                self.calendar_widget._highlight_dates_with_tasks()
            elif self.calendar_widget.current_view == "week":
                self.calendar_widget._update_week_view()
            elif self.calendar_widget.current_view == "day":
                self.calendar_widget._update_day_view()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
