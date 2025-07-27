from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QPushButton,
                             QHBoxLayout, QListWidget, QListWidgetItem, QFrame,
                             QTextEdit, QMenu, QInputDialog
                             )
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QSettings


class TasksWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("CHU1PC", "TaskManagerApp")

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
        self.task_list.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(
            self.show_context_menu)
        self.task_list.setStyleSheet("color: #ffffff;")
        mid_layout.addWidget(self.task_list)

        # 詳細エディタ
        self.detail_edit = QTextEdit(self)
        self.detail_edit.setPlaceholderText("タスクを選択すると、ここで詳細を編集できます")
        right_layout.addWidget(self.detail_edit)

        self.task_list.currentItemChanged.connect(self.on_item_selected)
        self.detail_edit.textChanged.connect(self.on_detail_changed)

        self._load_tasks()

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

    def _save_tasks(self):
        tasks = []
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item is not None:
                tasks.append({
                    "text": item.text(),
                    "detail": item.data(Qt.ItemDataRole.UserRole),
                    "checked": item.checkState() == Qt.CheckState.Checked
                })
        # 辞書のリストなら QSettings が QVariantList/QVariantMap に変換してくれる
        self.settings.setValue("tasks", tasks)

    def _load_tasks(self):
        stored = self.settings.value("tasks", [])
        for entry in stored:
            item = QListWidgetItem(entry.get("text", ""))
            # ダブルクリックで名前編集＆チェックＯＫにする
            item.setFlags(item.flags()
                          | Qt.ItemFlag.ItemIsEditable
                          | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if entry.get("checked") else
                Qt.CheckState.Unchecked
            )
            item.setData(Qt.ItemDataRole.UserRole, entry.get("detail", ""))
            self.task_list.addItem(item)

    def on_add_ckicked(self):
        task_text = self.input_line.text()
        if not task_text:
            return

        # チェックボックスの状態を取得

        item = QListWidgetItem(task_text)

        item.setCheckState(Qt.CheckState.Unchecked)

        item.setData(Qt.ItemDataRole.UserRole, "")

        # リストにアイテムを追加
        self.task_list.addItem(item)

        # 入力欄をリセット
        self.input_line.clear()
        self.input_line.setFocus()

        self._save_tasks()

    def show_context_menu(self, pos):
        item = self.task_list.itemAt(pos)
        if not item:
            return

        menu = QMenu()
        edit_act = QAction("編集", self)
        delete_act = QAction("削除", self)
        menu.addAction(edit_act)
        menu.addAction(delete_act)

        # アクションにコールバックを紐付け
        edit_act.triggered.connect(lambda: self.edit_task(item))
        delete_act.triggered.connect(lambda: self.delete_task(item))

        # グローバル座標に変換してメニュー表示
        viewport = self.task_list.viewport()
        if viewport is not None:
            global_pos = viewport.mapToGlobal(pos)
            menu.exec(global_pos)

    def edit_task(self, item: QListWidgetItem):
        """アイテム名を編集"""
        # 例えばポップアップで新しいテキストを聞く
        new_text, ok = QInputDialog.getText(
            self, "タスクを編集", "タスク名：", text=item.text()
        )
        if ok and new_text.strip():
            item.setText(new_text)
            # UserRole に詳細を入れているならキーが変わったら必要に応じて更新

        self._save_tasks()

    def delete_task(self, item: QListWidgetItem):
        """アイテムを削除"""
        row = self.task_list.row(item)
        self.task_list.takeItem(row)
        # 詳細エディタもクリア
        self.detail_edit.clear()
        self._save_tasks()

    # 既存のメソッド…
    def on_item_selected(self, current, previous):
        if current is None:
            self.detail_edit.clear()
            return

        # 通常の処理
        detail = current.data(Qt.ItemDataRole.UserRole) or ""
        self.detail_edit.blockSignals(True)
        self.detail_edit.setPlainText(detail)
        self.detail_edit.blockSignals(False)

    def on_detail_changed(self):
        item = self.task_list.currentItem()
        if item:
            item.setData(Qt.ItemDataRole.UserRole,
                         self.detail_edit.toPlainText())
        self._save_tasks()
