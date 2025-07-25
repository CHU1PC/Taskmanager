from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QPushButton,
                             QHBoxLayout, QListWidget, QListWidgetItem)


class TasksWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("タスクを入力…")
        self.add_btn = QPushButton("追加")
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_line)
        input_layout.addWidget(self.add_btn)
        layout.addLayout(input_layout)

        self.task_list = QListWidget()
        layout.addWidget(self.task_list)

        self.add_btn.clicked.connect(self.add_task)

    def add_task(self):
        text = self.input_line.text().strip()
        if text:
            item = QListWidgetItem(text)
            self.task_list.addItem(item)
            self.input_line.clear()
