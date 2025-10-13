import datetime

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QPushButton,
                             QHBoxLayout, QListWidget, QListWidgetItem, QFrame,
                             QTextEdit, QMenu, QGridLayout, QGroupBox, QLabel,
                             QMessageBox, QComboBox, QDialog, QStyledItemDelegate
                             )
from PyQt6.QtGui import QAction, QPainter, QPen, QColor
from PyQt6.QtCore import Qt, QSettings, QRect

from .TaskEdit import TaskEditDialog
from .Taskdelete import TaskDeleteDialog
from .TaskAdd import TaskAddDialog


class TaskItemDelegate(QStyledItemDelegate):
    """カスタムデリゲートで階層構造をインデントで表示"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.task_widget = None

    def set_task_widget(self, widget):
        """TasksWidgetへの参照を設定"""
        self.task_widget = widget

    def paint(self, painter, option, index):
        """アイテムを描画"""
        if not self.task_widget:
            super().paint(painter, option, index)
            return

        # タスクの階層レベルを取得
        row = index.row()
        level = self.task_widget._get_task_level(row)

        # 階層レベルに応じて描画領域を調整
        if level > 0:
            # インデントを追加（1レベルあたり20ピクセル）
            indent_width = level * 20
            adjusted_option = option
            adjusted_option.rect = QRect(
                option.rect.left() + indent_width,
                option.rect.top(),
                option.rect.width() - indent_width,
                option.rect.height()
            )
            super().paint(painter, adjusted_option, index)
        else:
            super().paint(painter, option, index)

    def sizeHint(self, option, index):
        """アイテムのサイズヒント"""
        size = super().sizeHint(option, index)
        # 標準的な高さ
        size.setHeight(max(size.height(), 28))
        return size

    def editorEvent(self, event, model, option, index):
        """エディターイベント（チェックボックスのクリック判定など）"""
        if not self.task_widget:
            return super().editorEvent(event, model, option, index)

        # タスクの階層レベルを取得
        row = index.row()
        level = self.task_widget._get_task_level(row)

        # 階層レベルに応じてクリック判定領域を調整
        if level > 0:
            indent_width = level * 20
            adjusted_option = option
            adjusted_option.rect = QRect(
                option.rect.left() + indent_width,
                option.rect.top(),
                option.rect.width() - indent_width,
                option.rect.height()
            )
            return super().editorEvent(event, model, adjusted_option, index)
        else:
            return super().editorEvent(event, model, option, index)


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
        self.all_sum_time = QLabel("全タスクの総勉強時間: 0時間00分")
        self.all_sum_time.setStyleSheet("""
            color: #ffffff;
            background-color: #333;
            border-radius: 5px;
            padding: 8px;
            font-size: 14px;
        """)

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

        # 追加ボタン（大きく目立つように）
        self.add_btn = QPushButton("➕ 新しいタスクを追加")
        self.add_btn.setStyleSheet("""
            QPushButton {
                color: #ffffff;
                background-color: #4a90e2;
                border: none;
                border-radius: 8px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5aa0f2;
            }
            QPushButton:pressed {
                background-color: #3a7fc2;
            }
        """)
        self.add_btn.clicked.connect(self.on_add_clicked)

        # タスク表示欄
        self.task_list = QListWidget(self)
        self.task_list.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(
            self.show_context_menu)
        self.task_list.setStyleSheet("color: #ffffff;")
        self.task_list.itemChanged.connect(self._on_item_changed)
        self.task_list.currentItemChanged.connect(self.on_item_selected)

        # カスタムデリゲートを設定
        self.item_delegate = TaskItemDelegate(self.task_list)
        self.item_delegate.set_task_widget(self)
        self.task_list.setItemDelegate(self.item_delegate)

        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            item.setData(Qt.ItemDataRole.UserRole + 2, item.checkState())
            item.setData(Qt.ItemDataRole.UserRole + 3, item.text())

        # タスク表示並び替え変更用ボタン
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
        self.task_sort.setStyleSheet("color: #ffffff;")
        self.task_sort.addItem("特になし")
        self.task_sort.addItem("グループ")
        self.task_sort.addItem("緊急度順")
        self.task_sort.addItem("アイゼンハワーマトリックス")
        self.task_sort.currentTextChanged.connect(self.sort_tasks)

        # 保存された並び順設定を読み込み
        saved_sort_type = self.settings.value("sort_type", "特になし")
        sort_index = self.task_sort.findText(saved_sort_type)
        if sort_index >= 0:
            self.task_sort.setCurrentIndex(sort_index)

        # ---------------------------------------------------------------------
        # 右の画面
        # ---------------------------------------------------------------------

        # 詳細エディタ
        self.detail_edit = QTextEdit(self)
        self.detail_edit.setPlaceholderText("タスクを選択すると、ここで詳細を編集できます")
        self.detail_edit.setStyleSheet("color: #ffffff;")

        self.detail_edit.textChanged.connect(self.on_detail_changed)

        # 緊急度重要度用
        self.urgency = QLabel("緊急度, 重要度:\n📖普通")
        self.urgency.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.urgency.setStyleSheet("""
            color: #ffffff;
            background-color: #333;
            border-radius: 5px;
            padding: 8px;
            font-size: 14px;
            font-weight: bold;
        """)

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
        study_layout.addWidget(self.total_study_label, 0, 0, 1, 2)
        study_layout.addWidget(self.today_study_label, 1, 0)
        study_layout.addWidget(self.yesterday_study_label, 1, 1)

        left_layout.addWidget(self.all_sum_time)
        left_layout.addWidget(self.reset_time_btn)
        left_layout.addStretch()

        mid_layout.addWidget(self.add_btn)
        mid_layout.addWidget(self.task_sort)
        mid_layout.addWidget(self.task_list)

        right_layout.addWidget(self.urgency)
        right_layout.addWidget(self.detail_edit)
        right_layout.addWidget(study_time_group)

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
                # 元のタスク名を保存（階層表示用のインデントなどを除く）
                original_name = item.data(Qt.ItemDataRole.UserRole + 5) or item.text()
                tasks.append({
                    "text": original_name,
                    "detail": item.data(Qt.ItemDataRole.UserRole),
                    "checked": item.checkState() == Qt.CheckState.Checked,
                    "urgency": item.data(Qt.ItemDataRole.UserRole + 1),
                    "parent_task_id": item.data(Qt.ItemDataRole.UserRole + 4)
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
            urgency = entry.get("urgency", "normal")
            item.setData(Qt.ItemDataRole.UserRole + 1, urgency)
            parent_task_id = entry.get("parent_task_id")
            item.setData(Qt.ItemDataRole.UserRole + 4, parent_task_id)
            # 元のタスク名を保存（階層表示用）
            item.setData(Qt.ItemDataRole.UserRole + 5, entry.get("text", ""))
            self.task_list.addItem(item)

        # タスク読み込み後に保存された並び順を適用
        self.sort_tasks()
        # 循環参照をチェックして修正
        self._fix_circular_references()
        # 階層表示を更新
        self._update_hierarchy_display()

    def on_add_clicked(self):
        # ダイアログを開く
        dialog = TaskAddDialog(self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        values = dialog.get_values()
        task_text = values["name"]

        if not task_text:
            QMessageBox.warning(self, "エラー", "タスク名を入力してください")
            return

        # 選択された緊急度を取得
        priority_data = values["priority_data"]
        parent_task_id = values["parent_task_id"]

        item = QListWidgetItem(task_text)
        item.setCheckState(Qt.CheckState.Unchecked)

        # 詳細欄は空で初期化（緊急度情報は含めない）
        item.setData(Qt.ItemDataRole.UserRole, "")

        # カスタムデータとして緊急度も保存
        item.setData(Qt.ItemDataRole.UserRole + 1, priority_data)

        # 親タスクIDを設定
        item.setData(Qt.ItemDataRole.UserRole + 4, parent_task_id)

        # 元のタスク名を保存
        item.setData(Qt.ItemDataRole.UserRole + 5, task_text)

        # リストにアイテムを追加
        self.task_list.addItem(item)
        self.sort_tasks()

        # 追加したアイテムを選択して緊急度表示を更新
        self.task_list.setCurrentItem(item)

        self._save_tasks()
        self._update_hierarchy_display()

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
        current_parent_id = item.data(Qt.ItemDataRole.UserRole + 4)
        current_task_index = self.task_list.row(item)

        dialog = TaskEditDialog(item.text(), current_priority, current_parent_id, current_task_index, self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        values = dialog.get_values()
        if not values["name"]:
            QMessageBox.warning(self, "エラー", "タスク名を入力してください")
            return

        old_name = item.text()
        new_name = values["name"]

        # --- ここで task_study_time を旧名→新名へマイグレーション ---
        if new_name != old_name:
            task_study_records = self.settings.value("task_study_time", {})
            if (isinstance(task_study_records, dict) and
               old_name in task_study_records):
                # 既存の新名データがあればマージ
                merged = task_study_records.get(new_name, {})
                for date, minutes in task_study_records[old_name].items():
                    merged[date] = merged.get(date, 0) + minutes
                task_study_records[new_name] = merged
                del task_study_records[old_name]
                self.settings.setValue("task_study_time", task_study_records)

        # 表示と属性の更新
        item.setText(new_name)
        item.setData(Qt.ItemDataRole.UserRole + 1, values["priority_data"])
        item.setData(Qt.ItemDataRole.UserRole + 4, values["parent_task_id"])
        item.setData(Qt.ItemDataRole.UserRole + 5, new_name)

        if self.task_list.currentItem() == item:
            priority_display = \
                self._get_priority_display_text(values["priority_data"])
            self.urgency.setText(f"緊急度, 重要度:\n{priority_display}")

        self.sort_tasks()
        self._save_tasks()
        self._update_hierarchy_display()
        self.update_study_time_display()

    def delete_task(self, item: QListWidgetItem):
        """アイテムを削除"""
        original_name = item.data(Qt.ItemDataRole.UserRole + 5) or item.text()
        task_index = self.task_list.row(item)

        # 子タスクがあるかチェック
        has_children = False
        for i in range(self.task_list.count()):
            other_item = self.task_list.item(i)
            if other_item and other_item.data(Qt.ItemDataRole.UserRole + 4) == task_index:
                has_children = True
                break

        # 削除確認ダイアログ
        warning_text = "勉強時間の記録も一緒に削除されます。この操作は取り消せません。"
        if has_children:
            warning_text += "\n\n注意: このタスクには子タスクがあります。削除すると、子タスクは親タスクなしになります。"

        dialog = TaskDeleteDialog(
            title="タスクの削除",
            text=f"タスク「{original_name}」を本当に削除しますか？",
            informative_text=warning_text,
            parent=self
        )

        # ダイアログを実行し、結果（どのボタンが押されたか）を取得します
        # "はい"が押されたら Accepted、"キャンセル"なら Rejected が返ります
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 子タスクの親IDをリセット
            for i in range(self.task_list.count()):
                other_item = self.task_list.item(i)
                if other_item and other_item.data(Qt.ItemDataRole.UserRole + 4) == task_index:
                    other_item.setData(Qt.ItemDataRole.UserRole + 4, None)

            # 他のタスクのparent_idを更新（削除されたタスクより後ろのインデックスを-1する）
            for i in range(self.task_list.count()):
                other_item = self.task_list.item(i)
                if other_item:
                    parent_id = other_item.data(Qt.ItemDataRole.UserRole + 4)
                    if parent_id is not None and parent_id > task_index:
                        other_item.setData(Qt.ItemDataRole.UserRole + 4, parent_id - 1)

            # 勉強時間の記録を削除
            task_study_records = self.settings.value("task_study_time", {})
            if original_name in task_study_records:
                deleted_task_time = task_study_records[original_name]
                study_records = self.settings.value("study_time", {})
                for date, minutes in deleted_task_time.items():
                    if date in study_records:
                        study_records[date] -= minutes
                        if study_records[date] <= 0:
                            del study_records[date]
                self.settings.setValue("study_time", study_records)
                del task_study_records[original_name]
                self.settings.setValue("task_study_time", task_study_records)

            # タスクを削除
            self.task_list.takeItem(task_index)

            self.detail_edit.clear()
            self._save_tasks()
            self._update_hierarchy_display()
            self.update_study_time_display()

    def on_item_selected(self, current, previous):
        if current is None:
            self.detail_edit.clear()
            self.urgency.setText("緊急度, 重要度:\n📖普通")
            return

        # 通常の処理
        detail = current.data(Qt.ItemDataRole.UserRole) or ""
        self.detail_edit.blockSignals(True)
        self.detail_edit.setPlainText(detail)
        self.detail_edit.blockSignals(False)

        # 緊急度表示を更新
        priority_data = current.data(Qt.ItemDataRole.UserRole + 1) or "normal"
        priority_display = self._get_priority_display_text(priority_data)
        self.urgency.setText(f"緊急度, 重要度:\n{priority_display}")

        self.update_study_time_display()

    def _get_priority_display_text(self, priority_data):
        """緊急度データから表示用テキストを取得"""
        priority_map = {
            "normal": "📋 通常",
            "urgent_important": "🔥 緊急×重要",
            "urgent_not_important": "⚡ 緊急×非重要",
            "not_urgent_important": "💡 非緊急×重要",
            "not_urgent_not_important": "📝 非緊急×非重要"
        }
        return priority_map.get(priority_data, "📖 普通")

    def on_detail_changed(self):
        """
        詳細テキスト編集時は itemChanged をブロックして、
        save() のみ実行する
        """
        item = self.task_list.currentItem()
        if not item:
            return

        # 1) itemChanged シグナルをブロック
        self.task_list.blockSignals(True)

        # 2) ユーザーデータとして詳細を保存
        item.setData(Qt.ItemDataRole.UserRole,
                     self.detail_edit.toPlainText())

        # 3) block 解除
        self.task_list.blockSignals(False)

        # 4) 保存のみ
        self._save_tasks()

    def _on_item_changed(self, item: QListWidgetItem):
        """チェック変更なら sort&save、テキスト変更なら save のみ"""
        # 1) 以前の状態を取得
        old_check = item.data(Qt.ItemDataRole.UserRole + 2)
        old_text = item.data(Qt.ItemDataRole.UserRole + 3)

        # 2) 今の状態を取得
        new_check = item.checkState()
        new_text = item.text()

        # 3) 変化のタイプで振り分け
        if new_check != old_check:
            # チェックが変わったとき
            # 親タスクがチェックされた場合、子タスクも全てチェックする
            if new_check == Qt.CheckState.Checked:
                # itemChanged シグナルを一時的にブロック（無限ループ防止）
                self.task_list.itemChanged.disconnect(self._on_item_changed)

                # 現在のタスクのインデックスを取得
                current_idx = None
                for i in range(self.task_list.count()):
                    if self.task_list.item(i) == item:
                        current_idx = i
                        break

                if current_idx is not None:
                    # 全ての子タスクを取得してチェック
                    child_indices = self._get_child_task_indices(current_idx)

                    for child_idx in child_indices:
                        child_item = self.task_list.item(child_idx)
                        if child_item:
                            child_item.setCheckState(Qt.CheckState.Checked)
                            # 子タスクの保存状態も更新
                            child_item.setData(Qt.ItemDataRole.UserRole + 2, Qt.CheckState.Checked)

                # シグナルを再接続
                self.task_list.itemChanged.connect(self._on_item_changed)

            # まず保存してから（親子関係のインデックスを正しく保存）
            self._save_tasks()
            # その後ソート（保存されたデータから親子関係を再構築）
            self.sort_tasks()
        elif new_text != old_text:
            # テキストが変わったとき（直接編集された場合）
            original_name = new_text.strip()
            item.setData(Qt.ItemDataRole.UserRole + 5, original_name)
            self._save_tasks()
            self._update_hierarchy_display()
        else:
            # detail用の setData 等、関係ない変更
            return

        # 4) 新しい状態を保存して次回に備える
        item.setData(Qt.ItemDataRole.UserRole + 2, new_check)
        item.setData(Qt.ItemDataRole.UserRole + 3, new_text)

    def _fix_circular_references(self):
        """循環参照と無効な親参照を検出して修正"""
        fixed = False
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item:
                parent_id = item.data(Qt.ItemDataRole.UserRole + 4)

                # 無効な親IDをチェック（範囲外または自分自身）
                if parent_id is not None:
                    if parent_id < 0 or parent_id >= self.task_list.count() or parent_id == i:
                        item.setData(Qt.ItemDataRole.UserRole + 4, None)
                        fixed = True
                        continue

                # 循環参照をチェック
                if self._has_circular_reference(i):
                    # 循環参照を発見した場合、親参照をリセット
                    item.setData(Qt.ItemDataRole.UserRole + 4, None)
                    fixed = True

        if fixed:
            # 問題が見つかった場合は保存
            self._save_tasks()

    def _has_circular_reference(self, task_index):
        """タスクが循環参照を持っているかチェック"""
        visited = set()
        current_idx = task_index

        while current_idx is not None:
            if current_idx in visited:
                # 循環参照を検出
                return True
            visited.add(current_idx)

            item = self.task_list.item(current_idx)
            if not item:
                break

            parent_id = item.data(Qt.ItemDataRole.UserRole + 4)
            if parent_id is None or parent_id < 0 or parent_id >= self.task_list.count():
                break

            current_idx = parent_id

        return False

    def _update_hierarchy_display(self):
        """タスクの階層構造を視覚的に表示（カスタムデリゲートで描画するため、テキストは変更しない）"""
        # 元のタスク名を表示名として設定
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item:
                # 元のタスク名を取得
                original_name = item.data(Qt.ItemDataRole.UserRole + 5) or item.text()

                # 表示を更新（編集時の混乱を避けるため、blockSignalsを使用）
                self.task_list.blockSignals(True)
                item.setText(original_name)
                self.task_list.blockSignals(False)

        # リストを再描画してカスタムデリゲートを適用
        self.task_list.viewport().update()

    def _get_task_level(self, task_index):
        """タスクの階層レベルを取得（0がトップレベル）"""
        level = 0
        current_idx = task_index
        visited = set()

        while current_idx is not None:
            if current_idx in visited:
                # 循環参照を検出
                break
            visited.add(current_idx)

            item = self.task_list.item(current_idx)
            if not item:
                break

            parent_id = item.data(Qt.ItemDataRole.UserRole + 4)
            if parent_id is None:
                break

            level += 1
            current_idx = parent_id

        return level

    def _get_child_task_indices(self, parent_idx, visited=None):
        """指定した親タスクの全ての子タスクのインデックスを再帰的に取得"""
        if visited is None:
            visited = set()

        child_indices = []

        # 循環参照を防ぐために訪問済みチェック
        if parent_idx in visited:
            return child_indices
        visited.add(parent_idx)

        # 子タスクを再帰的に探す
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item:
                item_parent_id = item.data(Qt.ItemDataRole.UserRole + 4)
                if item_parent_id == parent_idx and i not in visited:
                    child_indices.append(i)
                    # 孫タスクも取得
                    child_indices.extend(self._get_child_task_indices(i, visited))

        return child_indices

    def _get_child_task_names(self, parent_task_name, visited=None):
        """指定した親タスクの全ての子タスク名を再帰的に取得"""
        if visited is None:
            visited = set()

        child_names = []
        parent_idx = None

        # 親タスクのインデックスを見つける
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item:
                original_name = item.data(Qt.ItemDataRole.UserRole + 5) or item.text()
                if original_name == parent_task_name:
                    parent_idx = i
                    break

        if parent_idx is None:
            return child_names

        # 循環参照を防ぐために訪問済みチェック
        if parent_idx in visited:
            return child_names
        visited.add(parent_idx)

        # 子タスクを再帰的に探す
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item:
                item_parent_id = item.data(Qt.ItemDataRole.UserRole + 4)
                if item_parent_id == parent_idx and i not in visited:
                    child_name = item.data(Qt.ItemDataRole.UserRole + 5) or item.text()
                    child_names.append(child_name)
                    # 孫タスクも取得
                    child_names.extend(self._get_child_task_names(child_name, visited))

        return child_names

    def update_study_time_display(self):
        """勉強時間表示を更新"""
        # 勉強時間記録を取得
        task_study_records = self.settings.value("task_study_time", {})

        # 日付の準備
        today = datetime.date.today().isoformat()
        yesterday = \
            (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

        # 選択中のタスクを取得
        current_item = self.task_list.currentItem()

        if current_item:
            # 元のタスク名を取得（インデントなどを除く）
            task_name = current_item.data(Qt.ItemDataRole.UserRole + 5) or current_item.text()

            # このタスクと全ての子タスクのリストを作成
            task_names = [task_name] + self._get_child_task_names(task_name)

            # このタスクの総合計勉強時間（今まで全て、子タスクを含む）
            task_total_minutes = 0
            for name in task_names:
                if name in task_study_records:
                    task_total_minutes += sum(task_study_records[name].values())

            task_hours, task_mins = divmod(task_total_minutes, 60)
            self.total_study_label.setText(f"総合計: {task_hours}時間{task_mins}分")

            # このタスクの今日の勉強時間（子タスクを含む）
            today_task_minutes = 0
            for name in task_names:
                if (name in task_study_records and
                        today in task_study_records[name]):
                    today_task_minutes += task_study_records[name][today]

            today_hours, today_mins = divmod(today_task_minutes, 60)
            self.today_study_label.setText(f"今日: {today_hours}時間{today_mins}分")

            # このタスクの昨日の勉強時間（子タスクを含む）
            yesterday_task_minutes = 0
            for name in task_names:
                if (name in task_study_records and
                        yesterday in task_study_records[name]):
                    yesterday_task_minutes += task_study_records[name][yesterday]

            yesterday_hours, yesterday_mins = \
                divmod(yesterday_task_minutes, 60)
            self.yesterday_study_label.setText(
                f"昨日: {yesterday_hours}時間{yesterday_mins}分")

        # 全タスクの総合計勉強時間
        names_in_list = set()
        for i in range(self.task_list.count()):
            it = self.task_list.item(i)
            if it:
                original_name = it.data(Qt.ItemDataRole.UserRole + 5) or it.text()
                names_in_list.add(original_name)

        all_total_minutes = 0
        for name, per_task in task_study_records.items():
            if name in names_in_list:
                for time in per_task.values():
                    all_total_minutes += time
        total_hours, total_mins = divmod(all_total_minutes, 60)
        self.all_sum_time.setText(f"全タスクの総合計: {total_hours}時間{total_mins}分")

    def _reset_today_total_time(self):
        """総勉強時間をリセット"""
        msg_box = QMessageBox(self)

        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle("勉強時間のリセット")
        msg_box.setText("総勉強時間を再計算しますか？")
        msg_box.setInformativeText("この操作は取り消せません。")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes |
                                   QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        # スタイルを直接設定
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #282828;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
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
                "総勉強時間をリセットしました。"
            )

    def _get_hierarchical_sort_key(self, item, sort_type):
        """階層を考慮したソートキーを生成"""
        check_state = 0 if item.checkState() == Qt.CheckState.Unchecked else 1

        if sort_type == "緊急度順":
            priority_data = item.data(Qt.ItemDataRole.UserRole + 1) or "normal"
            priority_order = {
                "urgent_important": 0,
                "urgent_not_important": 1,
                "not_urgent_important": 2,
                "normal": 3,
                "not_urgent_not_important": 4
            }
            priority = priority_order.get(priority_data, 3)
            return (check_state, priority, item.text())

        elif sort_type == "アイゼンハワーマトリックス":
            priority_data = item.data(Qt.ItemDataRole.UserRole + 1) or "normal"
            eisenhower_order = {
                "urgent_important": 0,
                "urgent_not_important": 1,
                "not_urgent_important": 2,
                "normal": 3,
                "not_urgent_not_important": 4
            }
            priority = eisenhower_order.get(priority_data, 3)
            return (check_state, priority, item.text())

        elif sort_type == "グループ":
            detail = item.data(Qt.ItemDataRole.UserRole) or ""
            group_name = ""
            if detail.strip().startswith('[') and ']' in detail:
                end_bracket = detail.find(']')
                group_name = detail[1:end_bracket].strip()
            return (check_state, group_name, item.text())

        else:  # "特になし"
            return (check_state, item.text())

    def _sort_hierarchically(self, items, sort_type):
        """親子関係を維持しながらタスクをソート"""
        # インデックスとアイテムのマッピングを作成
        index_to_item = {i: item for i, item in enumerate(items)}

        # 親子関係のマップを作成
        children_map = {}  # parent_idx -> [child_indices]
        for idx, item in enumerate(items):
            parent_id = item.data(Qt.ItemDataRole.UserRole + 4)
            if parent_id is not None and parent_id in index_to_item:
                if parent_id not in children_map:
                    children_map[parent_id] = []
                children_map[parent_id].append(idx)

        # トップレベルのタスク（親がないタスク）を取得
        top_level = []
        for idx, item in enumerate(items):
            parent_id = item.data(Qt.ItemDataRole.UserRole + 4)
            if parent_id is None or parent_id not in index_to_item:
                top_level.append(idx)

        # トップレベルのタスクをソート
        top_level.sort(key=lambda idx: self._get_hierarchical_sort_key(
            index_to_item[idx], sort_type))

        # 各親の子タスクもソート
        for parent_idx in children_map:
            children_map[parent_idx].sort(
                key=lambda idx: self._get_hierarchical_sort_key(
                    index_to_item[idx], sort_type))

        # 階層的にタスクを並べる
        result = []
        visited = set()

        def add_task_and_children(task_idx):
            if task_idx in visited:
                return
            visited.add(task_idx)
            result.append(index_to_item[task_idx])

            # 子タスクを追加
            if task_idx in children_map:
                for child_idx in children_map[task_idx]:
                    add_task_and_children(child_idx)

        # トップレベルから順に追加
        for task_idx in top_level:
            add_task_and_children(task_idx)

        return result

    def sort_tasks(self):
        """選択されたソート方式に基づいてタスクを並び替える（親子関係を維持）"""
        # 現在のソート方式を取得
        sort_type = self.task_sort.currentText()

        # 0. ソート前に親子関係を名前ベースで保存
        parent_name_map = {}  # task_name -> parent_task_name
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item:
                task_name = item.data(Qt.ItemDataRole.UserRole + 5) or item.text()
                parent_id = item.data(Qt.ItemDataRole.UserRole + 4)
                if parent_id is not None and 0 <= parent_id < self.task_list.count():
                    parent_item = self.task_list.item(parent_id)
                    if parent_item:
                        parent_name = parent_item.data(Qt.ItemDataRole.UserRole + 5) or parent_item.text()
                        parent_name_map[task_name] = parent_name

        # 1. いったん全ての項目をリストから取り出す
        items = []
        while self.task_list.count() > 0:
            item = self.task_list.takeItem(0)
            if item is not None:
                items.append(item)

        # 2. 階層を維持しながらソート
        sorted_items = self._sort_hierarchically(items, sort_type)

        # 3. 並び替えたリストをQListWidgetに戻す
        for item in sorted_items:
            self.task_list.addItem(item)

        # 4. ソート後に親子関係のインデックスを再構築
        name_to_index = {}  # task_name -> current_index
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item:
                task_name = item.data(Qt.ItemDataRole.UserRole + 5) or item.text()
                name_to_index[task_name] = i

        # 親子関係を復元
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item:
                task_name = item.data(Qt.ItemDataRole.UserRole + 5) or item.text()
                if task_name in parent_name_map:
                    parent_name = parent_name_map[task_name]
                    if parent_name in name_to_index:
                        new_parent_id = name_to_index[parent_name]
                        item.setData(Qt.ItemDataRole.UserRole + 4, new_parent_id)
                    else:
                        # 親が見つからない場合はクリア
                        item.setData(Qt.ItemDataRole.UserRole + 4, None)
                else:
                    # 元々親がない場合
                    item.setData(Qt.ItemDataRole.UserRole + 4, None)

        # 並び順設定を保存
        self.settings.setValue("sort_type", sort_type)

        # 階層表示を更新
        self._update_hierarchy_display()
