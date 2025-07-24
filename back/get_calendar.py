import sys
import os

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QStackedWidget,
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QLineEdit, QListWidgetItem, QFormLayout, QSpinBox, QDialog,
    QDialogButtonBox, QCheckBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, QSettings, QUrl
from PyQt6.QtMultimedia import QSoundEffect


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

        # 設定読み込み
        self.settings = QSettings("CHU1PC", "PomodoroApp")
        self.default_minutes = int(self.settings.value("timer/minutes", 25))
        self.default_rest = int(self.settings.value("timer/rest", 5))

        # セット数管理
        self.sets_completed = 0

        # フェーズ管理
        self.is_break = False
        self.remaining_tenths = 0
        self.total_tenths = 0

        layout = QVBoxLayout(self)

        # 設定ボタン
        header = QHBoxLayout()
        self.settings_btn = QPushButton("…")
        self.settings_btn.setFixedSize(30, 30)
        header.addWidget(self.settings_btn)
        layout.addLayout(header)

        # セット数表示
        self.sets_label = QLabel("セット数: 0")
        self.sets_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.sets_label)

        # 時間表示
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.time_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(self.time_label)

        # プログレスバー
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(20)
        layout.addWidget(self.progress)

        # ボタン: 開始/停止 と リセット
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("開始")
        btn_layout.addWidget(self.start_btn)
        self.reset_btn = QPushButton("リセット")
        btn_layout.addWidget(self.reset_btn)
        layout.addLayout(btn_layout)

        # サウンド設定: QSoundを使用
        sound_file = os.path.join(os.path.dirname(__file__), 'beep.wav')
        if os.path.exists(sound_file):
            self.sound = QSoundEffect()
            self.sound.setSource(QUrl.fromLocalFile(sound_file))
        else:
            self.sound = None
            print(f"警告: サウンドファイルが見つかりません: {sound_file}")

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
        if self.sound:
            self.sound.play()
        else:
            QApplication.beep()
        # 作業フェーズ完了時にセット数加算
        if not self.is_break:
            self.sets_completed += 1
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
        self.nav.setFixedWidth(120)
        for label in ["⌛️ Pomodoro", "📝 Tasks"]:
            item = QListWidgetItem(label)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
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
