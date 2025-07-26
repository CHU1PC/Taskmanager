from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QPushButton,
                             QHBoxLayout, QListWidget, QListWidgetItem, QFrame,
                             )
from PyQt6.QtCore import Qt


class TasksWidget(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QHBoxLayout(self)

        left_panel = QWidget(self)
        mid_panel = QWidget(self)
        right_panel = QWidget(self)

        left_layout = QVBoxLayout(left_panel)
        mid_layout = QVBoxLayout(mid_panel)
        right_layout = QVBoxLayout(right_panel)

        # タスク入力欄
        self.input_line = QLineEdit(self)
        self.input_line.setPlaceholderText("タスクを入力…")

        # 追加ボタン
        self.add_btn = QPushButton("追加")
        self.add_btn.setStyleSheet("color: #ffffff;")
        self.add_btn.clicked.connect(self.on_add_ckicked)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.add_btn)
        input_layout.addWidget(self.input_line)

        mid_layout.addLayout(input_layout)

        # タスク表示欄
        self.task_list = QListWidget(self)
        self.task_list.setStyleSheet("color: #ffffff;")
        mid_layout.addWidget(self.task_list)

        # 画面を分ける線を書く
        separator0 = QFrame(self)
        separator0.setFrameShape(QFrame.Shape.VLine)
        separator0.setFrameShadow(QFrame.Shadow.Sunken)
        separator0.setLineWidth(3)
        separator0.setStyleSheet("background-color: #464646;")

        separator1 = QFrame(self)
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        separator1.setLineWidth(3)
        separator1.setStyleSheet("background-color: #464646;")

        # 画面をmainに集める
        main_layout.addWidget(left_panel, stretch=2)
        main_layout.addWidget(separator0)
        main_layout.addWidget(mid_panel, stretch=3)
        main_layout.addWidget(separator1)
        main_layout.addWidget(right_panel, stretch=2)

    def on_add_ckicked(self):
        task_text = self.input_line.text()
        if not task_text:
            return

        # チェックボックスの状態を取得

        item = QListWidgetItem(task_text)

        item.setCheckState(Qt.CheckState.Unchecked)

        # リストにアイテムを追加
        self.task_list.addItem(item)

        # 入力欄をリセット
        self.input_line.clear()
        self.input_line.setFocus()
