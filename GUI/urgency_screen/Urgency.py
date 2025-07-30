from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QWidget, QGridLayout,
                             QListWidget
                             )
from PyQt6.QtCore import Qt, QSettings


class UrgencyWidget(QWidget):
    def __init__(self):
        super().__init__()
        task_settings = QSettings("CHU1PC", "TaskManagerApp")
        self.stored_tasks = task_settings.value("tasks", [])

        # タスクリストウィジェットを属性として保持
        self.top_left_list = None
        self.top_right_list = None
        self.buttom_left_list = None
        self.buttom_right_list = None

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QGridLayout(self)

        # 左上の画面
        self.top_left = QVBoxLayout()
        urgen_high_impo_high = QLabel("🔥 緊急×重要")
        urgen_high_impo_high.setAlignment(Qt.AlignmentFlag.AlignTop)
        urgen_high_impo_high.setStyleSheet("""
            QLabel {
                background-color: #222;
                color: #BC0000;
                border-radius: 20px;
                font-size: 20px
            }
        """)
        self.top_left.addWidget(urgen_high_impo_high)

        # 右上の画面
        self.top_right = QVBoxLayout()
        urgen_high_impo_low = QLabel("⚡️ 緊急×非重要")
        urgen_high_impo_low.setAlignment(Qt.AlignmentFlag.AlignTop)
        urgen_high_impo_low.setStyleSheet("""
            QLabel {
                background-color: #222;
                color: #FFD800;
                border-radius: 20px;
                font-size: 20px
            }
        """)
        self.top_right.addWidget(urgen_high_impo_low)

        # 左下の画面
        self.buttom_left = QVBoxLayout()
        urgen_low_impo_high = QLabel("💡 非緊急×重要")
        urgen_low_impo_high.setAlignment(Qt.AlignmentFlag.AlignTop)
        urgen_low_impo_high.setStyleSheet("""
            QLabel {
                background-color: #222;
                color: #005CFF;
                border-radius: 20px;
                font-size: 20px
            }
        """)
        self.buttom_left.addWidget(urgen_low_impo_high)

        # 右下の画面
        self.buttom_right = QVBoxLayout()
        urgen_low_impo_low = QLabel("📝 非緊急×非重要")
        urgen_low_impo_low.setAlignment(Qt.AlignmentFlag.AlignTop)
        urgen_low_impo_low.setStyleSheet("""
            QLabel {
                background-color: #222;
                color: #00EB5D;
                border-radius: 20px;
                font-size: 20px
            }
        """)
        self.buttom_right.addWidget(urgen_low_impo_low)

        # タスクリストを作成（一度だけ）
        self._create_task_lists()
        self._update_tasks()

        main_layout.addLayout(self.top_left, 0, 0)
        main_layout.addLayout(self.top_right, 0, 1)
        main_layout.addLayout(self.buttom_left, 1, 0)
        main_layout.addLayout(self.buttom_right, 1, 1)

    def _create_task_lists(self):
        """タスクリストウィジェットを作成（一度だけ実行）"""
        if not self.top_left_list:
            self.top_left_list = QListWidget()
            self.top_left.addWidget(self.top_left_list)

        if not self.top_right_list:
            self.top_right_list = QListWidget()
            self.top_right.addWidget(self.top_right_list)

        if not self.buttom_left_list:
            self.buttom_left_list = QListWidget()
            self.buttom_left.addWidget(self.buttom_left_list)

        if not self.buttom_right_list:
            self.buttom_right_list = QListWidget()
            self.buttom_right.addWidget(self.buttom_right_list)

    def _update_tasks(self):
        """タスクの内容のみを更新"""
        # 既存の内容をクリア
        self.top_left_list.clear()
        self.top_right_list.clear()
        self.buttom_left_list.clear()
        self.buttom_right_list.clear()

        # 最新のタスクデータを取得
        task_settings = QSettings("CHU1PC", "TaskManagerApp")
        self.stored_tasks = task_settings.value("tasks", [])

        # タスクを分類して追加
        for task_entry in self.stored_tasks:
            task_text = task_entry.get("text", "")
            task_label = task_entry.get("urgency", "")
            if task_entry.get("checked", False):
                continue

            if task_label == "urgent_important":
                self.top_left_list.addItem(task_text)
            elif task_label == "urgent_not_important":
                self.top_right_list.addItem(task_text)
            elif task_label == "not_urgent_important":
                self.buttom_left_list.addItem(task_text)
            else:
                self.buttom_right_list.addItem(task_text)

    def refresh_tasks(self):
        """外部から呼び出してタスクを更新"""
        self._update_tasks()
