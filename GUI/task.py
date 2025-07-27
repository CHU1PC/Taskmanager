import datetime

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QPushButton,
                             QHBoxLayout, QListWidget, QListWidgetItem, QFrame,
                             QTextEdit, QMenu, QInputDialog, QGridLayout,
                             QGroupBox, QLabel, QDialogButtonBox, QSpinBox,
                             QFormLayout, QDialog, QMessageBox
                             )
from PyQt6.QtGui import QAction, QCursor
from PyQt6.QtCore import Qt, QSettings


class StudyTimeEditDialog(QDialog):
    """勉強時間編集ダイアログ"""
    def __init__(self, parent=None, current_hours=0, current_minutes=0):
        super().__init__(parent)
        self.setWindowTitle("勉強時間を編集")
        self.setFixedSize(300, 150)

        layout = QFormLayout(self)

        # 時間入力
        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(0, 999)
        self.hours_spin.setValue(current_hours)
        self.hours_spin.setSuffix(" 時間")

        # 分入力
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, 59)
        self.minutes_spin.setValue(current_minutes)
        self.minutes_spin.setSuffix(" 分")

        layout.addRow("時間:", self.hours_spin)
        layout.addRow("分:", self.minutes_spin)

        # ボタン
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_total_minutes(self):
        """入力された時間を分数で返す"""
        return self.hours_spin.value() * 60 + self.minutes_spin.value()


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

        # ---------------------------------------------------------------------
        # 左の画面
        # ---------------------------------------------------------------------

        # 本日の総勉強時間
        self.today_sum_time = QLabel("本日の総勉強時間: 0時間00分")
        self.today_sum_time.setStyleSheet("""
            color: #ffffff;
            background-color: #333;
            border-radius: 5px;
            padding: 8px;
            font-size: 14px;
        """)
        self.today_sum_time.\
            setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.today_sum_time.mousePressEvent = self._edit_today_total_time  # type: ignore # noqa

        # 編集ボタンを追加
        self.edit_time_btn = QPushButton("時間を編集")
        self.edit_time_btn.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: #ddd;
                border: 1px solid #666;
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        self.edit_time_btn.clicked.connect(self._edit_today_total_time)

        # リセットボタンを追加
        self.reset_time_btn = QPushButton("時間をリセット")
        self.reset_time_btn.setStyleSheet("""
            QPushButton {
                background-color: #5a2d2d;
                color: #ddd;
                border: 1px solid #7c4a4a;
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #6b3a3a;
            }
        """)
        self.reset_time_btn.clicked.connect(self._reset_today_total_time)

        # ---------------------------------------------------------------------
        # 真ん中の画面
        # ---------------------------------------------------------------------

        # タスク入力欄
        self.input_line = QLineEdit(self)
        self.input_line.setPlaceholderText("タスクを入力…")
        self.input_line.setStyleSheet("color: #ffffff;")

        # 追加ボタン
        self.add_btn = QPushButton("追加")
        self.add_btn.setStyleSheet("color: #ffffff;")
        self.add_btn.clicked.connect(self.on_add_ckicked)

        input_layout = QHBoxLayout()

        # タスク表示欄
        self.task_list = QListWidget(self)
        self.task_list.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(
            self.show_context_menu)
        self.task_list.setStyleSheet("color: #ffffff;")

        # ---------------------------------------------------------------------
        # 右の画面
        # ---------------------------------------------------------------------

        # 詳細エディタ
        self.detail_edit = QTextEdit(self)
        self.detail_edit.setPlaceholderText("タスクを選択すると、ここで詳細を編集できます")
        self.detail_edit.setStyleSheet("color: #ffffff;")

        self.task_list.currentItemChanged.connect(self.on_item_selected)
        self.detail_edit.textChanged.connect(self.on_detail_changed)

        # 勉強時間表示エリア
        study_time_group = QGroupBox("勉強時間統計")
        study_time_group.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                font-weight: bold;
                border: 2px solid #444;
                border-radius: 5px;
                margin: 10px 0;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        study_layout = QGridLayout(study_time_group)

        # 総合計勉強時間
        self.total_study_label = QLabel("総合計: 0時間0分")
        self.total_study_label.setStyleSheet("""
            color: #ffffff;
            background-color: #333;
            border-radius: 5px;
            padding: 8px;
            font-size: 14px;
        """)

        # 今日の勉強時間
        self.today_study_label = QLabel("今日: 0時間0分")
        self.today_study_label.setStyleSheet("""
            color: #ffffff;
            background-color: #333;
            border-radius: 5px;
            padding: 8px;
            font-size: 14px;
        """)

        # 昨日の勉強時間
        self.yesterday_study_label = QLabel("昨日: 0時間0分")
        self.yesterday_study_label.setStyleSheet("""
            color: #ffffff;
            background-color: #333;
            border-radius: 5px;
            padding: 8px;
            font-size: 14px;
        """)

        self._load_tasks()
        self.update_study_time_display()

        # ---------------------------------------------------------------------
        # 画面全体の設定
        # ---------------------------------------------------------------------

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

        # 画面への追加
        input_layout.addWidget(self.add_btn)
        input_layout.addWidget(self.input_line)
        study_layout.addWidget(self.total_study_label, 0, 0, 1, 2)
        study_layout.addWidget(self.today_study_label, 1, 0)
        study_layout.addWidget(self.yesterday_study_label, 1, 1)

        left_layout.addWidget(self.today_sum_time)
        left_layout.addWidget(self.edit_time_btn)
        left_layout.addWidget(self.reset_time_btn)
        left_layout.addStretch()

        mid_layout.addWidget(self.task_list)

        right_layout.addWidget(self.detail_edit)
        right_layout.addWidget(study_time_group)

        # 画面をmainに集める
        mid_layout.addLayout(input_layout)

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
        task_name = item.text()

        # そのタスクの勉強時間記録を削除
        task_study_records = self.settings.value("task_study_time", {})
        if task_name in task_study_records:
            # 削除するタスクの勉強時間を取得
            deleted_task_time = task_study_records[task_name]

            # 全体の勉強時間記録からそのタスクの時間を差し引く
            study_records = self.settings.value("study_time", {})
            for date, minutes in deleted_task_time.items():
                if date in study_records:
                    study_records[date] -= minutes
                    # 0以下になった場合は削除
                    if study_records[date] <= 0:
                        del study_records[date]

            # 更新された全体勉強時間を保存
            self.settings.setValue("study_time", study_records)

            # タスク別勉強時間からも削除
            del task_study_records[task_name]
            self.settings.setValue("task_study_time", task_study_records)

        # リストからアイテムを削除
        row = self.task_list.row(item)
        self.task_list.takeItem(row)

        # 詳細エディタもクリア
        self.detail_edit.clear()

        # タスクデータを保存
        self._save_tasks()

        # 勉強時間表示を更新
        self.update_study_time_display()

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

        self.update_study_time_display()

    def on_detail_changed(self):
        item = self.task_list.currentItem()
        if item:
            item.setData(Qt.ItemDataRole.UserRole,
                         self.detail_edit.toPlainText())
        self._save_tasks()

    def update_study_time_display(self):
        """勉強時間表示を更新"""
        # 勉強時間記録を取得
        study_records = self.settings.value("study_time", {})
        task_study_records = self.settings.value("task_study_time", {})

        # 日付の準備
        today = datetime.date.today().isoformat()
        yesterday = \
            (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

        # 選択中のタスクを取得
        current_item = self.task_list.currentItem()

        if current_item:
            task_name = current_item.text()

            # このタスクの総合計勉強時間（今まで全て）
            task_total_minutes = 0
            if task_name in task_study_records:
                task_total_minutes = \
                    sum(task_study_records[task_name].values())

            task_hours, task_mins = divmod(task_total_minutes, 60)
            self.total_study_label.setText(f"総合計: {task_hours}時間{task_mins}分")

            # このタスクの今日の勉強時間
            today_task_minutes = 0
            if (task_name in task_study_records and
                    today in task_study_records[task_name]):
                today_task_minutes = task_study_records[task_name][today]

            today_hours, today_mins = divmod(today_task_minutes, 60)
            self.today_study_label.setText(f"今日: {today_hours}時間{today_mins}分")

            # このタスクの昨日の勉強時間
            yesterday_task_minutes = 0
            if (task_name in task_study_records and
                    yesterday in task_study_records[task_name]):
                yesterday_task_minutes = \
                    task_study_records[task_name][yesterday]

            yesterday_hours, yesterday_mins = \
                divmod(yesterday_task_minutes, 60)
            self.yesterday_study_label.setText(
                f"昨日: {yesterday_hours}時間{yesterday_mins}分")

        # その日の総合計勉強時間
        today_total_minutes = sum(study_records.values())
        total_hours, total_mins = divmod(today_total_minutes, 60)
        self.today_sum_time.setText(
            f"総合計: {total_hours}時間{total_mins}分")

    def _edit_today_total_time(self, event=None):
        """今日の総勉強時間を編集"""
        # 現在の勉強時間を取得
        study_records = self.settings.value("study_time", {})
        today = datetime.date.today().isoformat()
        current_minutes = study_records.get(today, 0)
        current_hours, current_mins = divmod(current_minutes, 60)

        # 編集ダイアログを表示
        dialog = StudyTimeEditDialog(
            self,
            current_hours=current_hours,
            current_minutes=current_mins
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_total_minutes = dialog.get_total_minutes()

            # 確認メッセージ
            reply = QMessageBox.question(
                self,
                "勉強時間の変更",
                f"今日の総勉強時間を {new_total_minutes // 60}時間{new_total_minutes % 60}分 に変更しますか？\n"  # noqa
                f"現在: {current_hours}時間{current_mins}分",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # 勉強時間を更新
                study_records[today] = new_total_minutes
                self.settings.setValue("study_time", study_records)

                # 画面を更新
                self.update_study_time_display()

                # 成功メッセージ
                QMessageBox.information(
                    self,
                    "変更完了",
                    f"今日の総勉強時間を {new_total_minutes // 60}時間{new_total_minutes % 60}分 に変更しました。"  # noqa
                )

    def _reset_today_total_time(self):
        """今日の総勉強時間をリセット"""
        reply = QMessageBox.question(
            self,
            "勉強時間のリセット",
            "今日の総勉強時間を0にリセットしますか？\n"
            "この操作は取り消せません。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 今日の勉強時間を削除
            study_records = self.settings.value("study_time", {})
            today = datetime.date.today().isoformat()

            if today in study_records:
                del study_records[today]
                self.settings.setValue("study_time", study_records)

            # タスク別の今日の勉強時間もリセット
            task_study_records = self.settings.value("task_study_time", {})
            for task_name in task_study_records:
                if today in task_study_records[task_name]:
                    del task_study_records[task_name][today]
            self.settings.setValue("task_study_time", task_study_records)

            # 画面を更新
            self.update_study_time_display()

            # 完了メッセージ
            QMessageBox.information(
                self,
                "リセット完了",
                "今日の総勉強時間をリセットしました。"
            )
