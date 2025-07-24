import sys
import os

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QStackedWidget,
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QLineEdit, QListWidgetItem, QFormLayout, QSpinBox, QDialog,
    QDialogButtonBox, QCheckBox, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QSettings, QUrl, QSize
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QIcon


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
        layout.addRow("ポモドーロの時間", self.pomo_time)

        self.rest_time = QSpinBox()
        self.rest_time.setRange(1, 99)
        self.rest_time.setValue(rest)
        self.rest_time.setFixedSize(80, 20)
        layout.addRow("休憩時間", self.rest_time)

        self.chk_auto_next = QCheckBox("次のポモドーロを自動で開始")
        self.chk_auto_next.setChecked(auto_next)
        layout.addRow(self.chk_auto_next)

        self.chk_auto_break = QCheckBox("休憩を自動開始")
        self.chk_auto_break.setChecked(auto_break)
        layout.addRow(self.chk_auto_break)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel,
            self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        return (
            self.pomo_time.value(),
            self.rest_time.value(),
            self.chk_auto_next.isChecked(),
            self.chk_auto_break.isChecked()
        )


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
        right_layout = QVBoxLayout(right_panel)
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

        # 設定ボタン
        header = QHBoxLayout()
        self.settings_btn = QPushButton("…")
        self.settings_btn.setFixedSize(30, 30)
        header.addWidget(self.settings_btn)
        header.addStretch()
        right_layout.addLayout(header)

        # セット数表示
        self.sets_label = QLabel("セット数: 0")
        self.sets_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.sets_label.setStyleSheet("font-size: 24px;")
        right_layout.addWidget(self.sets_label)

        # 総勉強時間の表示
        self.total_time = QLabel("総勉強時間: 0時間00分")
        self.total_time.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.total_time.setStyleSheet("font-size: 24px;")
        right_layout.addWidget(self.total_time)

        # 時間表示
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.time_label.setStyleSheet("font-size: 48px;")
        left_layout.addStretch()
        left_layout.addWidget(self.time_label)
        left_layout.addStretch()

        # プログレスバー
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(20)
        left_layout.addWidget(self.progress)

        # ボタン: 開始/停止 と リセット
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("開始")
        btn_layout.addWidget(self.start_btn)
        self.reset_btn = QPushButton("リセット")
        btn_layout.addWidget(self.reset_btn)
        left_layout.addLayout(btn_layout)

        # 境界線を作成
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setLineWidth(1)

        # --- メインレイアウトに全てを追加 ---
        main_layout.addWidget(left_panel, stretch=3)
        main_layout.addWidget(separator)
        main_layout.addWidget(right_panel, stretch=2)

        # 音声再生用
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setSource(QUrl.fromLocalFile(os.path.join(
            os.path.dirname(__file__), "beep1.mp3"
        )))

        audio_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                  "audio")

        self.audio_output.setVolume(0.5)
        self.work_end_sound = QUrl.fromLocalFile(os.path.join(
            audio_path, "beep2.mp3"
        ))
        self.break_end_sound = QUrl.fromLocalFile(os.path.join(
            audio_path, "beep1.mp3"
        ))

        # タイマー
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._update_timer)

        # シグナル
        self.start_btn.clicked.connect(self._on_start_stop)
        self.reset_btn.clicked.connect(self._on_reset)
        self.settings_btn.clicked.connect(self._open_settings)

        self._reset_display()

    def _reset_display(self):
        # 表示とボタンを初期状態に
        minutes = self.default_rest if self.is_break else self.default_minutes
        self.time_label.setText(f"{minutes:02d}:00")
        self.progress.setRange(0, minutes * 60 * 10)
        self.progress.setValue(self.progress.maximum())
        self.start_btn.setText("開始")
        self.sets_label.setText(f"セット数: {self.sets_completed}")
        total_hours = (self.sets_completed * self.default_minutes) // 60
        total_minutes = (self.sets_completed * self.default_minutes) % 60
        self.total_time.setText(f"総勉強時間: {total_hours}時間{total_minutes}分")

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
        else:
            self.player.setSource(self.work_end_sound)

        self.player.play()

        # 作業フェーズ完了時にセット数加算
        if not self.is_break:
            self.sets_completed += 1
            self.settings.setValue("history/total_sets", self.sets_completed)

        # フェーズ切替
        self.is_break = not self.is_break
        self.timer.stop()
        self._reset_display()


class TasksWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("タスクを入力…")
        self.add_btn = QPushButton("追加")
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_line)
        input_layout.addWidget(self.add_btn)
        layout.addLayout(input_layout)

        self.task_list = QListWidget()
        layout.addWidget(self.task_list)

        self.add_btn.clicked.connect(self.add_task)

    def add_task(self):
        text = self.input_line.text().strip()
        if text:
            item = QListWidgetItem(text)
            self.task_list.addItem(item)
            self.input_line.clear()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Time manager App")
        self.resize(800, 500)

        central = QWidget()
        main_layout = QHBoxLayout(central)
        self.setCentralWidget(central)

        self.nav = QListWidget()
        self.nav.setFixedWidth(50)
        self.nav.setIconSize(QSize(24, 24))
        self.nav.setStyleSheet("background-color: #414141")

        img_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "img")
        menu_items = [
            (os.path.join(img_path, "pomodoro.png"), "ポモドーロ"),
            (os.path.join(img_path, "tasks.png"), "タスク"),
            (os.path.join(img_path, "matrix.png"), "時間管理のマトリクス")
        ]

        for icon_path, text in menu_items:
            item = QListWidgetItem("")
            item.setIcon(QIcon(icon_path))

            item.setToolTip(text)

            self.nav.addItem(item)
        main_layout.addWidget(self.nav)

        self.stack = QStackedWidget()
        self.stack.addWidget(PomodoroWidget())
        self.stack.addWidget(TasksWidget())
        main_layout.addWidget(self.stack, stretch=1)

        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav.setCurrentRow(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
