import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel,
    QVBoxLayout, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class StatBox(QWidget):
    def __init__(self, title: str, value: str, parent=None):
        super().__init__(parent)
        # レイアウト
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        # タイトルラベル
        title_label = QLabel(title, self)
        title_label.setFont(QFont(None, 10))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 値ラベル
        value_label = QLabel(value, self)
        value_label.setFont(QFont(None, 24, QFont.Weight.Bold))
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        # スタイルシートで背景色・角丸・文字色などを指定
        self.setStyleSheet("""
            QWidget {
                background-color: #222;
                color: #ddd;
                border-radius: 8px;
            }
        """)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stats Dashboard")

        grid = QGridLayout(self)
        grid.setSpacing(10)

        pomo = QLabel("今日のポモ: 0")

        # 4 つのボックスを配置
        grid.addWidget(pomo)
        grid.addWidget(StatBox("今日の集中期間", "0 m"), 0, 1)
        grid.addWidget(StatBox("合計ポモ", "11"), 1, 0)
        grid.addWidget(StatBox("総集中期間", "4h 35m"), 1, 1)

        self.setLayout(grid)
        self.resize(400, 300)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
