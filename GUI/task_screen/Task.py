import datetime

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QPushButton,
                             QHBoxLayout, QListWidget, QListWidgetItem, QFrame,
                             QTextEdit, QMenu, QGridLayout, QGroupBox, QLabel,
                             QMessageBox, QComboBox, QDialog
                             )
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QSettings

from .TaskEdit import TaskEditDialog


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

        # 全タスクの総勉強時間
        self.today_sum_time = QLabel("全タスクの総合計:\n0時間00分")
        self.today_sum_time.setStyleSheet("""
            color: #ffffff;
            background-color: #333;
            border-radius: 5px;
            padding: 8px;
            font-size: 14px;
        """)
        self.today_sum_time.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # リセットボタンを追加
        self.reset_time_btn = QPushButton("時間をリセット")
        self.reset_time_btn.setStyleSheet("""
            QPushButton {
                background-color: #870000;
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
        self.reset_time_btn.clicked.connect(self._reset_total_time)

        # ---------------------------------------------------------------------
        # 真ん中の画面
        # ---------------------------------------------------------------------

        # タスク入力欄
        self.input_line = QLineEdit(self)
        self.input_line.setPlaceholderText("タスクを入力…")
        self.input_line.setStyleSheet("""
            color: #ffffff;
            background-color: #333;
            border-radius: 5px;
            padding: 8px;
            font-size: 14px;
        """)
        self.input_line.returnPressed.connect(self.on_add_ckicked)

        # 緊急度選択ComboBox
        self.priority_combo = QComboBox(self)
        self.priority_combo.setStyleSheet("""
            QComboBox {
                background-color: #333;
                color: #ddd;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                color: #ddd;
            }
            QComboBox QAbstractItemView {
                background-color: #333;
                color: #ddd;
                selection-background-color: #555;
            }
        """)

        # 緊急度×重要度の4つの分類を追加
        self.priority_combo.addItem("📋 通常", "normal")
        self.priority_combo.addItem("🔥 緊急×重要", "urgent_important")
        self.priority_combo.addItem("⚡ 緊急×非重要", "urgent_not_important")
        self.priority_combo.addItem("💡 非緊急×重要", "not_urgent_important")
        self.priority_combo.addItem("📝 非緊急×非重要", "not_urgent_not_important")

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
        self.task_list.setStyleSheet("""
                                     color: #ffffff;
                                     font-size: 14px;
                                     """)
        self.task_list.itemChanged.connect(self.sort_tasks)

        # タスク表示の並び替え変更用ボタン
        self.task_sort = QComboBox()
        self.task_sort.setStyleSheet("""
            QComBox {
                background-color: #333;
                color: #ddd:
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
            }
            QComBox::drop-down {
                border: none;
            }
            QComBox:down-arrow {
                color: #ddd;
            }
        """)
        self.task_sort.addItem("特になし")
        self.task_sort.addItem("グループ")
        self.task_sort.addItem("緊急度順")
        self.task_sort.addItem("アイゼンハワーマトリックス")
        self.task_sort.currentTextChanged.connect(self.on_sort_changed)

        # ---------------------------------------------------------------------
        # 右の画面
        # ---------------------------------------------------------------------

        # 詳細エディタ
        self.detail_edit = QTextEdit(self)
        self.detail_edit.setPlaceholderText("タスクを選択すると、ここで詳細を編集できます")
        self.detail_edit.setStyleSheet("color: #ffffff;")

        self.task_list.currentItemChanged.connect(self.on_item_selected)
        self.detail_edit.textChanged.connect(self.on_detail_changed)

        # 緊急度の表示
        urgency = QLabel("緊急度 重要度: \n普通")

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
        left_layout.addStretch()
        left_layout.addWidget(self.reset_time_btn)
        left_layout.addStretch()

        mid_layout.addLayout(input_layout)
        mid_layout.addWidget(self.priority_combo)
        mid_layout.addWidget(self.task_sort)
        mid_layout.addWidget(self.task_list)

        right_layout.addWidget(self.detail_edit)
        right_layout.addWidget(study_time_group)

        # 画面をmainに集める

        main_layout.addWidget(left_panel, stretch=2)
        main_layout.addWidget(separator0)
        main_layout.addWidget(mid_panel, stretch=4)
        main_layout.addWidget(separator1)
        main_layout.addWidget(right_panel, stretch=3)

    def _save_tasks(self):
        tasks = []
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item is not None:
                tasks.append({
                    "text": item.text(),
                    "detail": item.data(Qt.ItemDataRole.UserRole),
                    "checked": item.checkState() == Qt.CheckState.Checked,
                    "priority": item.data(Qt.ItemDataRole.UserRole + 1)
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
            # 緊急度データも復元
            priority_data = entry.get("priority", "normal")
            item.setData(Qt.ItemDataRole.UserRole + 1, priority_data)
            self.task_list.addItem(item)

    def on_add_ckicked(self):
        task_text = self.input_line.text()
        if not task_text:
            return

        # 選択された緊急度を取得
        priority_data = self.priority_combo.currentData()

        item = QListWidgetItem(task_text)
        item.setCheckState(Qt.CheckState.Unchecked)

        # 詳細欄は空で初期化（緊急度情報は含めない）
        item.setData(Qt.ItemDataRole.UserRole, "")

        # カスタムデータとして緊急度も保存
        item.setData(Qt.ItemDataRole.UserRole + 1, priority_data)

        # リストにアイテムを追加
        self.task_list.addItem(item)
        self.sort_tasks()

        # 入力欄をリセット
        self.input_line.clear()
        self.input_line.setFocus()

        # 緊急度選択も通常に戻す
        self.priority_combo.setCurrentIndex(0)

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
        """タスク名と緊急度を編集"""
        current_priority = item.data(Qt.ItemDataRole.UserRole + 1) or "normal"

        dialog = TaskEditDialog(item.text(), current_priority, self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        values = dialog.get_values()

        if not values["name"]:
            QMessageBox.warning(self, "エラー", "タスク名を入力してください")
            return

        item.setText(values["name"])
        item.setData(Qt.ItemDataRole.UserRole + 1, values["priority_data"])

        # 詳細欄の緊急度情報は削除せず、現在の内容をそのまま保持
        # （ユーザーが編集した内容を保護）

        self.sort_tasks()
        self._save_tasks()

    def delete_task(self, item: QListWidgetItem):
        """アイテムを削除"""
        task_name = item.text()

        # 削除確認ダイアログを表示
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("タスクの削除")
        msg_box.setText(f"タスク「{task_name}」を削除しますか？")
        msg_box.setInformativeText("勉強時間の記録も一緒に削除されます。\nこの操作は取り消せません。")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        # ダークテーマスタイル
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #3c3c3c;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
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
            QPushButton:contains("Yes") {
                background-color: #d63384;
            }
            QPushButton:contains("Yes"):hover {
                background-color: #e91e63;
            }
        """)

        reply = msg_box.exec()

        if reply != QMessageBox.StandardButton.Yes:
            return  # キャンセルされた場合は削除しない

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

        # 全てのタスクの総合計勉強時間
        today_total_minutes = sum(study_records.values())
        total_hours, total_mins = divmod(today_total_minutes, 60)
        self.today_sum_time.setText(
            f"全タスクの総合計:\n{total_hours}時間{total_mins}分")

    def _reset_total_time(self):
        """全タスクの総勉強時間をリセット"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("勉強時間のリセット")
        msg_box.setText("全タスクの総勉強時間を0にリセットしますか？\nこの操作は取り消せません。")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #3c3c3c;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
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
            QPushButton:contains("Yes") {
                background-color: #a44;
            }
            QPushButton:contains("Yes"):hover {
                background-color: #b55;
            }
        """)

        reply = msg_box.exec()

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
                "全タスクの総勉強時間をリセットしました。",
            )

    def on_sort_changed(self):
        """ソート方式が変更された時の処理"""
        self.sort_tasks()

    def sort_tasks(self):
        """選択されたソート方式に基づいてタスクを並び替える"""
        # 現在のソート方式を取得
        sort_type = self.task_sort.currentText()

        # 1. いったん全ての項目をリストから取り出して、Pythonのリストに入れる
        items = []
        while self.task_list.count() > 0:
            item = self.task_list.takeItem(0)
            if item is not None:
                items.append(item)

        if sort_type == "特になし":
            # チェック状態のみでソート（デフォルト動作）
            items.sort(key=lambda item: (
                0 if item.checkState() == Qt.CheckState.Unchecked else 1
            ))

        elif sort_type == "グループ":
            # 詳細欄にグループ情報がある場合はそれでソート
            # 詳細の先頭に [グループ名] の形式で書いてあることを想定
            def get_group_key(item):
                detail = item.data(Qt.ItemDataRole.UserRole) or ""
                # チェック状態を最優先、次にグループ名でソート
                check_state = (
                    0 if item.checkState() == Qt.CheckState.Unchecked else 1
                )
                group_name = ""

                # 詳細の先頭から [グループ名] を抽出
                if detail.strip().startswith('[') and ']' in detail:
                    end_bracket = detail.find(']')
                    group_name = detail[1:end_bracket].strip()

                return (check_state, group_name, item.text())

            items.sort(key=get_group_key)

        elif sort_type == "緊急度順":
            # 新しい緊急度システムに基づいてソート
            def get_priority_key(item):
                # チェック状態を最優先
                check_state = (
                    0 if item.checkState() == Qt.CheckState.Unchecked else 1
                )

                # 保存された緊急度データを取得
                priority_data = (item.data(Qt.ItemDataRole.UserRole + 1) or
                                 "normal")

                # 緊急度の優先順位を設定（数値が小さいほど優先度が高い）
                priority_order = {
                    "urgent_important": 0,      # 🔥 緊急×重要
                    "urgent_not_important": 1,  # ⚡ 緊急×非重要
                    "not_urgent_important": 2,  # 💡 非緊急×重要
                    "normal": 3,                # 📋 通常
                    "not_urgent_not_important": 4  # 📝 非緊急×非重要
                }

                priority = priority_order.get(priority_data, 3)

                return (check_state, priority, item.text())

            items.sort(key=get_priority_key)

        elif sort_type == "アイゼンハワーマトリックス":
            # アイゼンハワーマトリックスに基づいて明確にソート
            def get_eisenhower_key(item):
                # チェック状態を最優先
                check_state = (
                    0 if item.checkState() == Qt.CheckState.Unchecked else 1
                )

                # 保存された緊急度データを取得
                priority_data = (item.data(Qt.ItemDataRole.UserRole + 1) or
                                 "normal")

                # アイゼンハワーマトリックスの順序
                # 1. Do First (緊急×重要)
                # 2. Schedule (非緊急×重要)
                # 3. Delegate (緊急×非重要)
                # 4. Eliminate (非緊急×非重要)
                eisenhower_order = {
                    "urgent_important": 0,        # Do First
                    "not_urgent_important": 1,    # Schedule
                    "urgent_not_important": 2,    # Delegate
                    "normal": 3,                  # 通常
                    "not_urgent_not_important": 4  # Eliminate
                }

                priority = eisenhower_order.get(priority_data, 3)

                return (check_state, priority, item.text())

            items.sort(key=get_eisenhower_key)

        # 3. 並び替えたリストをQListWidgetに戻す
        for item in items:
            self.task_list.addItem(item)
