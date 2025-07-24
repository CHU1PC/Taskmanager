import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QWidget,
                             QVBoxLayout)


class TooltipExample(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ツールチップの例")
        self.setGeometry(300, 300, 300, 200)

        # ボタンを作成
        button = QPushButton("ここにカーソルを当てて", self)

        # ▼▼▼ ここでツールチップを設定 ▼▼▼
        button.setToolTip("これがツールチップとして表示される文字列です。")

        # ウィジェットのレイアウト設定
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(button)
        self.setCentralWidget(central_widget)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TooltipExample()
    window.show()
    sys.exit(app.exec())
