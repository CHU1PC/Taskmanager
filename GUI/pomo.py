import os
import sys

from PyQt6.QtWidgets import (QDialog, QFormLayout, QSpinBox, QCheckBox,
                             QDialogButtonBox, QVBoxLayout, QHBoxLayout,
                             QLabel, QSlider, QWidget, QGridLayout,
                             QPushButton, QSizePolicy, QProgressBar, QFrame,
                             QSystemTrayIcon
                             )
from PyQt6.QtCore import Qt, QSettings, QTimer, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QIcon


def resource_path(rel_path: str) -> str:
    """
    PyInstaller のビルド方式に合わせて
    リソースが展開されるベースパスを返す。
    """
    # onefile のときは _MEIPASS、一方 onedir や普通の実行時はスクリプトのある場所
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    return os.path.join(base_path, rel_path)


class TimerSettingDialog(QDialog):
    def __init__(self, parent=None, minutes=25, rest=5,
                 auto_next=False, auto_break=False):
        super().__init__(parent)
        self.setWindowTitle("タイマーの設定")
        self.resize(320, 260)

        layout = QFormLayout(self)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        layout.setFormAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setHorizontalSpacing(20)
        layout.setVerticalSpacing(15)

        self.pomo_time = QSpinBox()
        self.pomo_time.setRange(1, 99)
        self.pomo_time.setValue(minutes)
        self.pomo_time.setFixedSize(80, 20)
        self.pomo_time.setStyleSheet("""
                background-color: #404040;
                color: #ffffff;
            """)
        pomodoro_time = QLabel("ポモドーロの時間")
        pomodoro_time.setStyleSheet("color: #ffffff;")
        layout.addRow(pomodoro_time, self.pomo_time)

        self.rest_time = QSpinBox()
        self.rest_time.setRange(1, 99)
        self.rest_time.setValue(rest)
        self.rest_time.setFixedSize(80, 20)
        self.rest_time.setStyleSheet("""
                background-color: #404040;
                color: #ffffff;
            """)
        rest_time = QLabel("休憩時間")
        rest_time.setStyleSheet("color: #ffffff;")
        layout.addRow(rest_time, self.rest_time)

        self.chk_auto_next = QCheckBox("次のポモドーロを自動で開始")
        self.chk_auto_next.setChecked(auto_next)
        self.chk_auto_next.setStyleSheet("color: #ffffff;")
        layout.addRow(self.chk_auto_next)

        self.chk_auto_break = QCheckBox("休憩を自動開始")
        self.chk_auto_break.setChecked(auto_break)
        self.chk_auto_break.setStyleSheet("color: #ffffff;")
        layout.addRow(self.chk_auto_break)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel,
            self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.setStyleSheet("color: #ffffff;")
        layout.addWidget(buttons)

    def values(self):
        return (
            self.pomo_time.value(),
            self.rest_time.value(),
            self.chk_auto_next.isChecked(),
            self.chk_auto_break.isChecked()
        )


class VolumeSettingDialog(QDialog):
    def __init__(self, parent=None, initial_volume=50):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        # 現在の音量を表示する
        self.volume_label = QLabel(f"音量: {initial_volume}%")
        self.volume_label.setStyleSheet("""
                background-color: #404040;
                color: #ffffff;
            """)
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.volume_label)

        # 音量調整スライダー
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(initial_volume)
        layout.addWidget(self.slider)

        # スライダーの値が変更されたらラベルを更新
        self.slider.valueChanged.connect(self.update_label)

        # OK/Cancelボタン
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def update_label(self, value):
        self.volume_label.setText(f"音量: {value}%")

    def volume(self):
        return self.slider.value()


class PomodoroWidget(QWidget):
    def __init__(self):
        super().__init__()

        # --- 1.メインの水平レイアウトを作成 ---
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- 2.左と右に分ける ---
        left_panel = QWidget()
        right_panel = QWidget()

        left_layout = QVBoxLayout(left_panel)
        right_layout = QGridLayout(right_panel)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # 上寄せ

        # 設定読み込み
        self.settings = QSettings("CHU1PC", "PomodoroApp")
        self.default_minutes = int(self.settings.value("timer/minutes", 25))
        self.default_rest = int(self.settings.value("timer/rest", 5))

        # セット数管理
        self.sets_completed = int(self.settings.value("history/total_sets", 0))

        # フェーズ管理
        self.is_break = False
        self.remaining_tenths = 0
        self.total_tenths = 0

        # 通知用
        self.study_announce = \
            QSystemTrayIcon(QIcon(resource_path("img/start_study")), self)
        self.study_announce.setToolTip("Time Manager APP")
        self.study_announce.setVisible(True)

        self.rest_announce = \
            QSystemTrayIcon(QIcon(resource_path("img/start_rest")), self)
        self.rest_announce.setToolTip("Time Manager APP")
        self.rest_announce.setVisible(True)

        # タイマー設定ボタン
        header = QHBoxLayout()
        self.settings_btn = QPushButton("…")
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.setStyleSheet("""
                background-color: #404040;
                color: #ffffff;
            """)
        header.addWidget(self.settings_btn)
        header.addStretch()
        right_layout.addLayout(header, 0, 0)

        # 音量設定ボタン
        volume_header = QHBoxLayout()
        self.volume_setting = QPushButton("🔈")
        self.volume_setting.setFixedSize(30, 30)
        self.volume_setting.setStyleSheet("""
                background-color: #404040;
                color: #ffffff;
            """)
        volume_header.addStretch()
        volume_header.addWidget(self.volume_setting)
        left_layout.addLayout(volume_header)

        # セット数表示
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
        right_layout.addWidget(self.sets_label, 1, 0)

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
        right_layout.addWidget(self.total_time, 1, 1)

        # 目標勉強時間
        self.goal_minutes = int(self.settings.value("goal/minutes",
                                                    self.default_minutes * 4))

        self.goal_spin = QSpinBox(self)
        self.goal_spin.setFixedSize(120, 30)
        self.goal_spin.setRange(self.default_minutes,
                                self.default_minutes * 99)
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
        right_layout.addWidget(goal_time, 2, 0)
        right_layout.addWidget(self.goal_spin, 2, 1)

        # 残り時間／残りポモドーロ数ラベル
        self.remain_time_label = QLabel()
        self.remain_count_label = QLabel()
        self.remain_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.remain_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_layout.addWidget(self.remain_time_label, 3, 0)
        right_layout.addWidget(self.remain_count_label, 3, 1)

        # 最後に…
        self._update_remaining()

        # 時間表示
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignHCenter |
                                     Qt.AlignmentFlag.AlignVCenter)
        self.time_label.setStyleSheet("""
                background-color: #404040;
                color: #ffffff;
                font-size: 48px;
            """)
        left_layout.addStretch()
        left_layout.addWidget(self.time_label)
        left_layout.addStretch()

        # プログレスバー
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(20)
        left_layout.addWidget(self.progress)

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
        left_layout.addLayout(btn_layout)

        #
        # 境界線を作成
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setLineWidth(1)

        # --- メインレイアウトに全てを追加 ---
        main_layout.addWidget(left_panel, stretch=3)
        main_layout.addWidget(separator)
        main_layout.addWidget(right_panel, stretch=2)

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

        # 音声再生用
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        saved_volume = float(self.settings.value("audio/volume", 0.5))
        self.audio_output.setVolume(saved_volume)
        self.work_end_sound = \
            QUrl.fromLocalFile(resource_path("audio/beep2.mp3"))
        self.break_end_sound = \
            QUrl.fromLocalFile(resource_path("audio/beep1.mp3"))

        self._reset_display()

    def _skip_timer(self):
        # 任意でタイマーの時間を0にする
        self.remaining_tenths = 0

    def _reset_display(self):
        # 表示とボタンを初期状態に
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

    def _open_volume_settings(self):
        current_volume_percent = int(self.audio_output.volume() * 100)

        dlg = VolumeSettingDialog(self, initial_volume=current_volume_percent)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            # ダイアログから新しい音量を取得
            new_volume_precent = dlg.volume()
            new_volume_float = new_volume_precent / 100.0

            self.audio_output.setVolume(new_volume_float)
            self.settings.setValue("audio/volume", new_volume_float)

    def _open_settings(self):
        parent = self.window()
        dlg = TimerSettingDialog(parent,
                                 self.default_minutes,
                                 self.default_rest,
                                 False, False)
        dlg.setModal(True)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            m, r, _, _ = dlg.values()
            self.default_minutes = m
            self.default_rest = r
            self.settings.setValue("timer/minutes", m)
            self.settings.setValue("timer/rest", r)
            self.is_break = False
            self.remaining_tenths = 0
            self.sets_completed = 0
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
        else:
            self.timer.stop()
            self.start_btn.setText("再開")

    def _on_reset(self):
        # リセット: タイマー停止、表示とセット数リセット
        if self.timer.isActive():
            self.timer.stop()
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

        # フェーズ終了時に音を鳴らす
        if self.is_break:
            self.player.setSource(self.break_end_sound)
            self.study_announce.showMessage(
                "ポモドーロ完了",
                "作業時間が終了しました! お疲れ様です",
                QSystemTrayIcon.MessageIcon.Information,
                5000
            )
        else:
            self.player.setSource(self.work_end_sound)
            self.study_announce.showMessage(
                "休憩終了",
                "休憩時間が終了しました! がんばりましょう!!!!",
                QSystemTrayIcon.MessageIcon.Information,
                5000
            )

        self.player.play()

        # 作業フェーズ完了時にセット数加算
        if not self.is_break:
            self.sets_completed += 1
            self.settings.setValue("history/total_sets", self.sets_completed)

        # フェーズ切替
        self.is_break = not self.is_break
        self.timer.stop()
        self._reset_display()
