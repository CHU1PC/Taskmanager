from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QPushButton, QLineEdit)


class TaskEditDialog(QDialog):
    def __init__(self, task_name, current_priority, parent=None):
        super().__init__(parent)
        self.setWindowTitle("タスクを編集")
        self.setModal(True)
        self.resize(400, 200)

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
        self.name_edit = QLineEdit(task_name)
        layout.addWidget(self.name_edit)

        # 緊急度選択
        layout.addWidget(QLabel("緊急度:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItem("📋 通常", "normal")
        self.priority_combo.addItem("🔥 緊急×重要", "urgent_important")
        self.priority_combo.addItem("⚡ 緊急×非重要", "urgent_not_important")
        self.priority_combo.addItem("💡 非緊急×重要", "not_urgent_important")
        self.priority_combo.addItem("📝 非緊急×非重要", "not_urgent_not_important")

        # 現在の緊急度を選択状態にする
        for i in range(self.priority_combo.count()):
            if self.priority_combo.itemData(i) == current_priority:
                self.priority_combo.setCurrentIndex(i)
                break

        layout.addWidget(self.priority_combo)

        # ボタン
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("キャンセル")

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # エンターキーでOK
        self.name_edit.returnPressed.connect(self.accept)

    def get_values(self):
        """編集された値を取得"""
        return {
            'name': self.name_edit.text().strip(),
            'priority_data': self.priority_combo.currentData(),
            'priority_text': self.priority_combo.currentText()
        }
