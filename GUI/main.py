import os
import sys

from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QListWidget,
                             QListWidgetItem, QStackedWidget, QApplication)
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon

from pomodoro_screen import PomodoroWidget
from task_screen import TasksWidget


def resource_path(rel_path: str) -> str:
    """
    PyInstaller のビルド方式に合わせて
    リソースが展開されるベースパスを返す。
    """
    # onefile のときは _MEIPASS、一方 onedir や普通の実行時はスクリプトのある場所
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    return os.path.join(base_path, rel_path)


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
            (resource_path("img/tasks.png"), "タスク")
        ]

        for icon_path, text in menu_items:
            item = QListWidgetItem("")
            item.setIcon(QIcon(icon_path))

            item.setToolTip(text)

            self.nav.addItem(item)
        main_layout.addWidget(self.nav)

        self.stack = QStackedWidget()
        self.stack.addWidget(PomodoroWidget())
        self.stack.addWidget(TasksWidget())
        main_layout.addWidget(self.stack, stretch=1)

        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav.setCurrentRow(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
