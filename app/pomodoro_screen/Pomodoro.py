import datetime

from PyQt6.QtWidgets import (QDialog, QSpinBox, QVBoxLayout, QHBoxLayout,
                             QLabel, QWidget, QGridLayout, QPushButton,
                             QSizePolicy, QProgressBar, QFrame,
                             QSystemTrayIcon, QComboBox, QInputDialog
                             )
from PyQt6.QtCore import Qt, QSettings, QTimer, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput


from app.utils import resource_path
from app.pomodoro_screen.VolumeSetting import VolumeSettingDialog
from app.pomodoro_screen.TimerSetting import TimerSettingDialog


class TimerWidget(QWidget):
    def __init__(self):
        super().__init__()

        # ウィジェットを水平方向に並べる
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 左と右に分ける
        left_panel = QWidget()
        right_panel = QWidget()

        # 左のlayoutは垂直方向にWidgetを並べて
        # 右のlayoutは行列の座標で配置を指定できるlayout
        left_layout = QVBoxLayout(left_panel)
        right_layout = QGridLayout(right_panel)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # 上寄せ

        # ---------------------------------------------------------------------
        # 設定読み込み
        # ---------------------------------------------------------------------

        # タスク設定と同じものを使用する
        self.task_settings = QSettings("CHU1PC", "TaskManagerApp")

        # QsettingsでCHU1PC/PomodoroAppに保存する
        self.settings = QSettings("CHU1PC", "PomodoroApp")

        # 1ポモドーロの時間を読み込む
        self.default_minutes = int(self.settings.value("timer/minutes", 25))

        # 休憩時間を読み込む
        self.default_rest = int(self.settings.value("timer/rest", 5))

        # ポモドーロの自動開始の有無を読み込む
        self.auto_next = \
            self.settings.value("timer/auto_next", False, type=bool)

        # 休憩時間の自動開始の有無を読み込む
        self.auto_break = \
            self.settings.value("timer/auto_break", False, type=bool)

        # 行ってセット数(ポモドーロの数)を読み込む
        self.sets_completed = int(self.settings.value("history/total_sets", 0))

        # 目標時間を読み込む
        self.goal_minutes = int(self.settings.value("goal/minutes",
                                                    self.default_minutes * 4))

        # ---------------------------------------------------------------------
        # フェーズ管理
        # ---------------------------------------------------------------------
        self.is_break = False  # Falseの時は勉強時間
        self.remaining_tenths = 0
        self.total_tenths = 0

        # ---------------------------------------------------------------------
        # 通知用
        # ---------------------------------------------------------------------
        self.study_announce = QSystemTrayIcon(self)
        self.study_announce.setToolTip("Time Manager APP")
        self.study_announce.setVisible(True)

        self.rest_announce = \
            QSystemTrayIcon(self)
        self.rest_announce.setToolTip("Time Manager APP")
        self.rest_announce.setVisible(True)

        # ---------------------------------------------------------------------
        # タイマー設定ボタン
        # ---------------------------------------------------------------------

        # 水平方向にWidgetを並べる
        header = QHBoxLayout()
        self.settings_btn = QPushButton("…")
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.setStyleSheet("""
                background-color: #404040;
                color: #ffffff;
            """)
        header.addWidget(self.settings_btn)
        header.addStretch()

        # ---------------------------------------------------------------------
        # 音量設定ボタン
        # ---------------------------------------------------------------------
        volume_header = QHBoxLayout()
        self.volume_setting = QPushButton("🔈")
        self.volume_setting.setFixedSize(30, 30)
        self.volume_setting.setStyleSheet("""
                background-color: #404040;
                color: #ffffff;
            """)
        volume_header.addStretch()
        volume_header.addWidget(self.volume_setting)

        # ---------------------------------------------------------------------
        # 右側の画面の文字列の表示
        # ---------------------------------------------------------------------

        # セット数の表示
        self.sets_label = QLabel("")
        self.sets_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.sets_label.setStyleSheet("""
            QWidget {
                background-color: #222;
                color: #ddd;
                border-radius: 8px;
            }
        """)
        self.sets_label.setSizePolicy(QSizePolicy.Policy.Expanding,
                                      QSizePolicy.Policy.Fixed)

        # 総勉強時間の表示
        self.total_time = QLabel()
        self.total_time.setAlignment(Qt.AlignmentFlag.AlignHCenter |
                                     Qt.AlignmentFlag.AlignVCenter)
        self.total_time.setStyleSheet("""
            QWidget {
                background-color: #222;
                color: #ddd;
                border-radius: 8px;
            }
        """)
        self.total_time.setSizePolicy(QSizePolicy.Policy.Expanding,
                                      QSizePolicy.Policy.Fixed)

        # 目標勉強時間
        self.goal_spin = QSpinBox(self)
        self.goal_spin.setFixedSize(120, 30)
        # 目標時間はポモドーロの時間単位で設定できるようにしたいためrangeを設定する
        self.goal_spin.setRange(self.default_minutes,
                                self.default_minutes * 99)
        # setSingleStepで矢印が押されたときにどれだけ値が増減するかを決める
        self.goal_spin.setSingleStep(self.default_minutes)
        self.goal_spin.setValue(self.goal_minutes)
        self.goal_spin.setSuffix(" 分")
        self.goal_spin.valueChanged.connect(self._on_goal_changed)
        self.goal_spin.setAlignment(Qt.AlignmentFlag.AlignHCenter |
                                    Qt.AlignmentFlag.AlignVCenter)
        self.goal_spin.setStyleSheet("""
            QWidget {
                background-color: #222;
                color: #ddd;
            }
        """)
        goal_time = QLabel("目標時間")
        goal_time.setAlignment(Qt.AlignmentFlag.AlignHCenter |
                               Qt.AlignmentFlag.AlignVCenter)
        goal_time.setStyleSheet("""
            QWidget {
                background-color: #222;
                color: #ddd;
                border-radius: 8px;
            }
        """)

        # 残り時間
        self.remain_time_label = QLabel()
        self.remain_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.remain_time_label.setStyleSheet("""
            QWidget {
                background-color: #222;
                color: #ddd;
                border-radius: 8px;
            }
        """)

        # 残りポモドーロ数
        self.remain_count_label = QLabel()
        self.remain_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_separator = QFrame()
        right_separator.setFrameShape(QFrame.Shape.HLine)
        right_separator.setFrameShadow(QFrame.Shadow.Sunken)
        right_separator.setLineWidth(2)
        right_separator.setStyleSheet("background-color: #464646;")

        task_label = QLabel("現在のタスク")
        task_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        task_label.setStyleSheet("""
            QWidget {
                background-color: #222;
                color: #ddd;
                border-radius: 8px;
                padding: 5px;
            }
        """)

        self.task_combo = QComboBox()
        self.task_combo.setStyleSheet("""
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

        self.task_combo.addItem("タスクなし")
        self.task_combo.setStyleSheet("color: #ffffff;")
        self.task_combo.currentTextChanged.connect(self._on_task_changed)

        # タスク更新ボタン
        self.refresh_task_btn = QPushButton("更新")
        self.refresh_task_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                background-color: #222;      /* ボタン背景色 */
                color: #fff;                 /* 文字色 */
                border: none;                /* デフォルトの枠線を消す */
                border-radius: 16px;         /* 角の丸み(px) */
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #007DFF;
            }
            QPushButton:pressed {
                background-color: #333;
            }
        """)
        self.refresh_task_btn.clicked.connect(self._refresh_tasks)

        # 現在のタスク表示
        self.current_task_label = QLabel("選択されていません")
        self.current_task_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_task_label.setStyleSheet("""
            QWidget {
                background-color: #222;
                color: #ddd;
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
            }
        """)

        # タスク選択行
        task_select_layout = QHBoxLayout()
        task_select_layout.addWidget(self.task_combo, stretch=3)
        task_select_layout.addWidget(self.refresh_task_btn, stretch=1)

        task_select_widget = QWidget()
        task_select_widget.setLayout(task_select_layout)

        self.selected_task = None

        # 画面への追加
        right_layout.addWidget(self.sets_label, 1, 0)
        right_layout.addWidget(self.total_time, 1, 1)
        right_layout.addWidget(goal_time, 2, 0)
        right_layout.addWidget(self.goal_spin, 2, 1)
        right_layout.addWidget(self.remain_time_label, 3, 0)
        right_layout.addWidget(self.remain_count_label, 3, 1)

        right_layout.addWidget(right_separator, 4, 0, 1, 2)

        right_layout.addWidget(task_label, 5, 0, 1, 2)
        right_layout.addWidget(task_select_widget, 6, 0, 1, 2)
        right_layout.addWidget(self.current_task_label, 7, 0, 1, 2)
        right_layout.addLayout(header, 0, 0)

        self._refresh_tasks()
        # _update_remainingで目標時間から残りの時間数とポモドーロ数を計算して表示させる
        self._update_remaining()

        # ---------------------------------------------------------------------
        # 左側の画面の文字列の表示
        # ---------------------------------------------------------------------

        # 時間表示
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignHCenter |
                                     Qt.AlignmentFlag.AlignVCenter)
        self.time_label.setStyleSheet("""
                color: #ffffff;
                font-size: 48px;
            """)

        # プログレスバー
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(20)

        # ボタン: 開始/停止 と リセットとスキップ
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("開始")
        self.start_btn.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                background-color: #222;      /* ボタン背景色 */
                color: #fff;                 /* 文字色 */
                border: none;                /* デフォルトの枠線を消す */
                border-radius: 12px;         /* 角の丸み(px) */
                padding: 8px 16px;           /* 上下左右の余白 */
            }
            QPushButton:hover {
                background-color: #007DFF;
            }
            QPushButton:pressed {
                background-color: #333;
            }
        """)
        btn_layout.addWidget(self.start_btn)

        self.reset_btn = QPushButton("リセット")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                background-color: #222;      /* ボタン背景色 */
                color: #fff;                 /* 文字色 */
                border: none;                /* デフォルトの枠線を消す */
                border-radius: 12px;         /* 角の丸み(px) */
                padding: 8px 16px;           /* 上下左右の余白 */
            }
            QPushButton:hover {
                background-color: #007DFF;
            }
            QPushButton:pressed {
                background-color: #333;
            }
        """)
        btn_layout.addWidget(self.reset_btn)

        self.skip_btn = QPushButton("スキップ")
        self.skip_btn.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                background-color: #222;      /* ボタン背景色 */
                color: #fff;                 /* 文字色 */
                border: none;                /* デフォルトの枠線を消す */
                border-radius: 12px;         /* 角の丸み(px) */
                padding: 8px 16px;           /* 上下左右の余白 */
            }
            QPushButton:hover {
                background-color: #007DFF;
            }
            QPushButton:pressed {
                background-color: #333;
            }
        """)
        btn_layout.addWidget(self.skip_btn)

        # タイマー
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._update_timer)

        # シグナル
        self.start_btn.clicked.connect(self._on_start_stop)
        self.reset_btn.clicked.connect(self._on_reset)
        self.skip_btn.clicked.connect(self._skip_timer)

        self.settings_btn.clicked.connect(self._open_settings)
        self.volume_setting.clicked.connect(self._open_volume_settings)

        # 終了音声
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        saved_volume = float(self.settings.value("audio/volume", 0.5))
        self.audio_output.setVolume(saved_volume)
        self.work_end_sound = \
            QUrl.fromLocalFile(resource_path("audio/beep2.mp3"))
        self.break_end_sound = \
            QUrl.fromLocalFile(resource_path("audio/beep1.mp3"))
        self.error_sound = \
            QUrl.fromLocalFile(resource_path("audio/error.mp3"))

        # 勉強中音声
        self.bgm_player = QMediaPlayer()
        self.bgm_audio_output = QAudioOutput()
        self.bgm_player.setAudioOutput(self.bgm_audio_output)
        self.bgm_player.setLoops(QMediaPlayer.Loops.Infinite)

        saved_bgm_volume = float(self.settings.value("audio/bgm_volume", 0.2))
        self.bgm_audio_output.setVolume(saved_bgm_volume)
        self.bgm_player.setSource(
            QUrl.fromLocalFile(resource_path("audio/clock.mp3")))

        left_layout.addLayout(volume_header)
        left_layout.addStretch()
        left_layout.addWidget(self.time_label)
        left_layout.addStretch()
        left_layout.addWidget(self.progress)
        left_layout.addLayout(btn_layout)

        # ---------------------------------------------------------------------
        # 画面全体の設定
        # ---------------------------------------------------------------------
        # 境界線を作成
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setLineWidth(3)
        separator.setStyleSheet("background-color: #464646;")

        # --- メインレイアウトに全てを追加 ---
        main_layout.addWidget(left_panel, stretch=3)
        main_layout.addWidget(separator)
        main_layout.addWidget(right_panel, stretch=2)

        self._reset_display()

    def _skip_timer(self):
        """スキップボタンが押された際にtimerの時間を強制的に0にする
        """
        self.remaining_tenths = 0
        self.bgm_player.stop()

    def _open_volume_settings(self):
        """音量設定Widgetが開かれた時の処理
        """

        # 今現在のsfxとbgmの音量を取ってくる(0~1 → 0~100)
        current_sfx_volume_per = int(self.audio_output.volume() * 100)
        current_bgm_volume_per = int(self.bgm_audio_output.volume() * 100)

        dlg = VolumeSettingDialog(self,
                                  initial_bgm_volume=current_bgm_volume_per,
                                  initial_sfx_volume=current_sfx_volume_per)

        # dlg.exec()とはユーザがOKかCancelボタンを返したかどうかを返してAccepted(OK)が押されたら変更する
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # ダイアログから新しい音量を取得
            new_sfx_volume_per, new_bgm_volume_per = dlg.values()

            new_sfx_volume_float = new_sfx_volume_per / 100.0  # %に変更する
            new_bgm_volume_float = new_bgm_volume_per / 100.0  # %に変更する

            self.audio_output.setVolume(new_sfx_volume_float)
            self.bgm_audio_output.setVolume(new_bgm_volume_float)

            # settingsに書き込む
            self.settings.setValue("audio/volume", new_sfx_volume_float)
            self.settings.setValue("audio/bgm_volume", new_bgm_volume_float)

    def _open_settings(self):
        """ポモドーロの設定Widgetが開かれた時の処理
        """
        parent = self.window()
        dlg = TimerSettingDialog(parent,
                                 self.default_minutes,
                                 self.default_rest,
                                 self.auto_next,
                                 self.auto_break)
        dlg.setModal(True)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            m, r, auto_next, auto_break = dlg.values()
            self.default_minutes = m
            self.default_rest = r
            self.auto_next = auto_next
            self.auto_break = auto_break

            # QSettingsにも書き込む
            self.settings.setValue("timer/minutes", m)
            self.settings.setValue("timer/rest", r)
            self.settings.setValue("timer/auto_next", auto_next)
            self.settings.setValue("timer/auto_break", auto_break)

            # リセットして画面再描画
            # self.is_break = False
            # self.remaining_tenths = 0
            # self.sets_completed = 0
            self._reset_display()
        if parent:
            parent.raise_()

    def _on_goal_changed(self, v):
        self.goal_minutes = v
        self.settings.setValue("goal/minutes", v)
        self._update_remaining()

    def _update_remaining(self):
        done = self.sets_completed * self.default_minutes
        remain = max(0, self.goal_minutes - done)

        if self.default_minutes > 0:
            need = (remain + self.default_minutes - 1) // self.default_minutes
        else:
            need = 0

        # 表示更新
        h, m = divmod(remain, 60)
        self.remain_time_label.setText(f"残り時間:\n{h}時間{m}分")
        self.remain_time_label.setStyleSheet("""
            QWidget {
                background-color: #222;
                color: #ddd;
                border-radius: 8px;
            }
        """)
        self.remain_count_label.setText(f"残りポモドーロ数:\n{need}回")
        self.remain_count_label.setStyleSheet("""
            QWidget {
                background-color: #222;
                color: #ddd;
                border-radius: 8px;
            }
        """)

    def _on_start_stop(self):
        # タイマーの開始／停止
        if not self.timer.isActive():
            if self.remaining_tenths == 0:
                self._start_phase()
            self.timer.start()
            self.start_btn.setText("停止")

            if not self.is_break:
                self.bgm_player.play()

        else:
            self.timer.stop()
            self.start_btn.setText("再開")

            self.bgm_player.pause()

    def _on_reset(self):
        # リセット: タイマー停止、表示とセット数リセット
        if self.timer.isActive():
            self.timer.stop()
        self.bgm_player.stop()
        self.is_break = False
        self.remaining_tenths = 0
        self.sets_completed = 0
        self.settings.setValue("history/total_sets", 0)
        self._reset_display()

    def _start_phase(self):
        # 作業 or 休憩フェーズ開始
        duration = self.default_rest if self.is_break else self.default_minutes
        self.total_tenths = duration * 60 * 10
        self.remaining_tenths = self.total_tenths
        color = "green" if self.is_break else "white"
        self.time_label.setStyleSheet(f"font-size:48px; color:{color};")
        self.progress.setRange(0, self.total_tenths)
        self.progress.setValue(self.total_tenths)
        self.start_btn.setText("停止")

    def _update_timer(self):
        # カウントダウン処理
        if self.remaining_tenths > 0:
            self.remaining_tenths -= 1
            sec = self.remaining_tenths // 10
            m, s = divmod(sec, 60)
            self.time_label.setText(f"{m:02d}:{s:02d}")
            self.progress.setValue(self.remaining_tenths)
            return

        self.bgm_player.stop()

        # 作業フェーズ完了時にセット数加算
        if not self.is_break:
            self.sets_completed += 1
            self.settings.setValue("history/total_sets", self.sets_completed)

        # フェーズ終了時に音を鳴らす
        if self.is_break:
            self.player.setSource(self.break_end_sound)
            self.study_announce.showMessage(
                "休憩終了",
                "休憩時間が終了しました! がんばりましょう!!!!",
                QSystemTrayIcon.MessageIcon.Information,
                10000
            )
            self.player.play()
        else:
            if not self.selected_task:
                self.player.setSource(self.error_sound)
                self.study_announce.showMessage(
                    "タスクが選択されていません!!!!",
                    "タスクが選択されていないため、今選択してください",
                    QSystemTrayIcon.MessageIcon.Warning,
                    10000
                )
            else:
                self.player.setSource(self.work_end_sound)
                self.study_announce.showMessage(
                    "ポモドーロ完了",
                    "作業時間が終了しました! お疲れ様です",
                    QSystemTrayIcon.MessageIcon.Information,
                    10000
                )
            self.player.play()
            self._record_study_time(self.default_minutes)

        # フェーズ切替
        self.is_break = not self.is_break
        self.timer.stop()
        self._reset_display()

        if self.is_break and self.auto_break:
            self._start_phase()
            self.timer.start()
        elif not self.is_break and self.auto_next:
            self._start_phase()
            self.timer.start()

    def _record_study_time(self, minutes):
        today = datetime.date.today().isoformat()

        if not self.selected_task:
            stored_tasks = self.task_settings.value("tasks", [])

            tasks = []
            for task in stored_tasks:
                name = task.get("text", "")
                check = task.get("checked", False)
                if not check and name:
                    tasks.append(name)
            selected, ok = QInputDialog.getItem(
                self, "タスク選択", "記録するタスクを選んでください:", tasks, 0, False
            )
            if not ok or not selected:
                return False

            idx = self.task_combo.findText(selected)
            if idx >= 0:
                # シグナルで _on_task_changed が呼ばれ self.selected_task が更新される
                self.task_combo.setCurrentIndex(idx)
            else:
                # 念のため直接セット
                self.selected_task = selected
                self.settings.setValue("current_task", selected)
                disp = selected if len(selected) <= 20 else selected[:17] + "..."
                self.current_task_label.setText(f"実行中: {disp}")

        study_records = self.task_settings.value("study_time", {})

        # 今日の記録を更新
        if today not in study_records:
            study_records[today] = 0
        study_records[today] += minutes
        self.task_settings.setValue("study_time", study_records)

        task_study_records = \
            self.task_settings.value("task_study_time", {})
        if self.selected_task not in task_study_records:
            task_study_records[self.selected_task] = {}
        if today not in task_study_records[self.selected_task]:
            task_study_records[self.selected_task][today] = 0
        task_study_records[self.selected_task][today] += minutes

        # タスク別勉強時間を保存
        self.task_settings.setValue("task_study_time", task_study_records)

        return True

    def _refresh_tasks(self):
        """タスクリストを更新"""
        # 現在の選択を保存
        current_text = self.task_combo.currentText()

        # コンボボックスをクリア
        self.task_combo.clear()
        self.task_combo.addItem("タスクなし")

        # task.pyと同じ設定でタスクを読み込み
        task_settings = QSettings("CHU1PC", "TaskManagerApp")
        stored_tasks = task_settings.value("tasks", [])

        # 未完了のタスクのみを追加
        for task_entry in stored_tasks:
            task_text = task_entry.get("text", "")
            task_check = task_entry.get("checked", False)
            if task_text and not task_check:
                self.task_combo.addItem(task_text)

        # 前の選択を復元（可能なら）
        index = self.task_combo.findText(current_text)
        if index >= 0:
            self.task_combo.setCurrentIndex(index)
        else:
            self.task_combo.setCurrentIndex(0)  # "タスクなし"を選択

    def _on_task_changed(self, task_text):
        """タスク選択が変更された時の処理"""
        if task_text == "タスクなし" or not task_text:
            self.selected_task = None
            self.current_task_label.setText("選択されていません")
        else:
            self.selected_task = task_text
            # テキストが長い場合は省略表示
            display_text = task_text if len(task_text) <= 20 \
                else task_text[:17] + "..."
            self.current_task_label.setText(f"実行中: {display_text}")

        # 設定に選択中のタスクを保存
        self.settings.setValue("current_task", task_text if
                               task_text != "タスクなし" else "")

    def _reset_display(self):
        """なにかしらの変更が行われたせいにその変更を画面に適応させる
        """
        minutes = self.default_rest if self.is_break else self.default_minutes
        self.time_label.setText(f"{minutes:02d}:00")
        self.progress.setRange(0, minutes * 60 * 10)
        self.progress.setValue(self.progress.maximum())
        self.start_btn.setText("開始")
        self.sets_label.setText(f"セット数: \n{self.sets_completed}")
        total_hours = (self.sets_completed * self.default_minutes) // 60
        total_minutes = (self.sets_completed * self.default_minutes) % 60
        self.total_time.setText(f"総勉強時間: \n{total_hours}時間{total_minutes}分")
        self._update_remaining()

        # 保存されている選択中のタスクを復元
        saved_task = self.settings.value("current_task", "")
        if saved_task:
            index = self.task_combo.findText(saved_task)
            if index >= 0:
                self.task_combo.setCurrentIndex(index)
