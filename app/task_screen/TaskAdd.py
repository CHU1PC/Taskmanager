from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QPushButton, QLineEdit)
from PyQt6.QtCore import QSettings


class TaskAddDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("タスクを追加")
        self.setModal(True)
        self.resize(400, 350)
        self.settings = QSettings("CHU1PC", "TaskManagerApp")

        # ダークテーマに合わせたスタイル
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #333;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
            }
            QComboBox {
                background-color: #333;
                color: #ddd;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                background-color: #555;
                color: #fff;
                border-radius: 4px;
                padding: 8px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)

        layout = QVBoxLayout(self)

        # タスク名入力
        layout.addWidget(QLabel("タスク名:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("新しいタスクの名前を入力...")
        layout.addWidget(self.name_edit)

        # 緊急度選択
        layout.addWidget(QLabel("緊急度:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItem("📋 通常", "normal")
        self.priority_combo.addItem("🔥 緊急×重要", "urgent_important")
        self.priority_combo.addItem("⚡ 緊急×非重要", "urgent_not_important")
        self.priority_combo.addItem("💡 非緊急×重要", "not_urgent_important")
        self.priority_combo.addItem("📝 非緊急×非重要", "not_urgent_not_important")
        layout.addWidget(self.priority_combo)

        # 親タスク選択
        layout.addWidget(QLabel("親タスク:"))
        self.parent_combo = QComboBox()
        self.parent_combo.addItem("なし（トップレベル）", None)

        # 利用可能なタスクを取得
        stored_tasks = self.settings.value("tasks", [])
        for idx, task_entry in enumerate(stored_tasks):
            task_text = task_entry.get("text", "")
            if task_text:
                self.parent_combo.addItem(task_text, idx)

        layout.addWidget(self.parent_combo)

        # ボタン
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("追加")
        self.cancel_button = QPushButton("キャンセル")

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # エンターキーでOK
        self.name_edit.returnPressed.connect(self.accept)

        # フォーカスをタスク名入力に設定
        self.name_edit.setFocus()

    def get_values(self):
        """入力された値を取得"""
        return {
            'name': self.name_edit.text().strip(),
            'priority_data': self.priority_combo.currentData(),
            'priority_text': self.priority_combo.currentText(),
            'parent_task_id': self.parent_combo.currentData()
        }
