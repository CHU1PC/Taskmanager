import sys
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QLabel, QPushButton

class LayoutExample(QWidget):
    def __init__(self):
        super().__init__()
        # 水平レイアウトを作成
        layout = QHBoxLayout(self)

        label_left = QLabel("左寄せのラベル")
        label_right = QLabel("右寄せのラベル")

        layout.addWidget(label_left)
        layout.addStretch()  # 中央に伸縮するスペースを追加
        layout.addWidget(label_right)

# --- 実行用コード ---
app = QApplication(sys.argv)
window = LayoutExample()
window.show()
sys.exit(app.exec())