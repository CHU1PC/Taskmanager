from PyQt6.QtCore import QSettings, Qt, QTimer, QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from app.pomodoro_screen.Logic.timer_logic import TimerLogic
from app.pomodoro_screen.ui import (
    create_goal_spin_box,
    create_goal_time_label,
    create_remain_labels,
    create_set_label,
    create_setting_button,
    create_total_time_label,
    create_volume_header,
)


class TimerWidget(QWidget):
    def __init__(self):
        super().__init__()

    def _load_settings(self):
        self.settings = QSettings("CHU1PC", "PomodoroApp")
        self.default_minutes = int(self.settings.value("timer/minutes", 25))
        self.default_rest = int(self.settings.value("timer/rest", 5))
        self.auto_next = self.settings.value("timer/auto_next", False, type=bool)
        self.auto_break = self.settings.value("timer/auto_break", False, type=bool)
        self.sets_completed = int(self.settings.value("history/total_sets", 0))
        self.goal_minutes = int(self.settings.value("goal/minutes", self.default_minutes * 4))

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        right_panel = QWidget()
        right_layout = QGridLayout(right_panel)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.study_announce = QSystemTrayIcon(self)
        self.study_announce.setToolTip("Time Manager APP")
        self.study_announce.setVisible(True)

        self.rest_announce = \
            QSystemTrayIcon(self)
        self.rest_announce.setToolTip("Time Manager APP")
        self.rest_announce.setVisible(True)

        volume_header, self.volume_setting = create_volume_header()
        self.set_label = create_set_label()
        self.settings_btn = create_setting_button()
        self.total_time = create_total_time_label()
        self.goal_spin = create_goal_spin_box(default_minutes=self.default_minutes, goal_minutes=self.goal_minutes)
        goal_time = create_goal_time_label()
        self.remain_time_label, self.remain_count_label = create_remain_labels()


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