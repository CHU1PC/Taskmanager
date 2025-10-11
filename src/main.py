import sys

from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QListWidget,
                             QListWidgetItem, QStackedWidget, QApplication)
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon

from pomodoro_screen import PomodoroWidget
from task_screen import TasksWidget
from urgency_screen import UrgencyWidget

from utils import resource_path


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
            (resource_path("img/matrix.png"), "マトリックス")
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

        self.stack = QStackedWidget()
        self.stack.addWidget(self.pomodoro_widget)
        self.stack.addWidget(self.tasks_widget)
        self.stack.addWidget(self.urgency_widget)

        main_layout.addWidget(self.stack, stretch=1)

        self.nav.currentRowChanged.connect(self.reset_urgency)
        self.nav.setCurrentRow(0)

    def reset_urgency(self, current_row):
        self.stack.setCurrentIndex(current_row)
        if current_row == 2:
            self.urgency_widget.refresh_tasks()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
