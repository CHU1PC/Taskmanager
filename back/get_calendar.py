import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QStackedWidget,
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QLineEdit, QListWidgetItem, QFormLayout, QSpinBox, QDialog,
    QDialogButtonBox, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, QSettings


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

        # --- ここでスピンボックスをフォームに追加 ---
        self.pomo_time = QSpinBox()
        self.pomo_time.setRange(0, 99)
        self.pomo_time.setValue(minutes)
        self.pomo_time.setFixedSize(80, 20)
        layout.addRow("ポモドーロの時間", self.pomo_time)

        self.rest_time = QSpinBox()
        self.rest_time.setRange(0, 99)
        self.rest_time.setValue(rest)
        self.rest_time.setFixedSize(80, 20)
        layout.addRow("休憩時間", self.rest_time)

        self.chk_auto_next = QCheckBox("次のポモドーロを自動で開始")
        self.chk_auto_next.setChecked(auto_next)
        layout.addRow(self.chk_auto_next)

        self.chk_auto_break = QCheckBox("休憩を自動開始")
        self.chk_auto_break.setChecked(auto_break)
        layout.addRow(self.chk_auto_break)

        # OK / Cancelボタン
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel,
            self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        # 分, 休憩, 自動Pomo, 自動休憩 を返す
        return (
            self.pomo_time.value(),
            self.rest_time.value(),
            self.chk_auto_next.isChecked(),
            self.chk_auto_break.isChecked()
        )


class PomodoroWidget(QWidget):
    def __init__(self):
        super().__init__()

        # --- QSettingsのキー定義 ---
        self.settings = QSettings("CHU1PC", "PomodoroApp")

        # --- 保存済み値を読み込む(未設定の場合は25:00) ---
        self.default_minutes = int(self.settings.value("timer/minutes", 25))
        self.default_rest = int(self.settings.value("timer/rest", 5))
        self.auto_next = \
            self.settings.value("timer/auto_next", False, type=bool)
        self.auto_break = \
            self.settings.value("timer/auto_break", False, type=bool)

        self.is_break = False

        layout = QVBoxLayout(self)

        # ヘッダー: ...ボタン
        header = QHBoxLayout()
        self.settings_btn = QPushButton("…")
        self.settings_btn.setFixedSize(30, 30)
        header.addWidget(self.settings_btn)
        layout.addLayout(header)

        # タイマー表示
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.time_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(self.time_label)

        # 開始/停止ボタン
        self.start_btn = QPushButton("開始")
        layout.addWidget(self.start_btn)

        # QTimer: 100msごと
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._update_timer)
        self.remaining_tenths = 0

        # シグナル接続
        self.start_btn.clicked.connect(self._on_start_stop)
        self.settings_btn.clicked.connect(self._open_settings)

        # 初期表示
        self._reset_display()

    def _reset_display(self):
        m = self.default_minutes
        self.time_label.setText(f"{m:02d}:00")

    def _open_settings(self):
        dlg = TimerSettingDialog(self, self.default_minutes,
                                 self.default_rest)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            m, r = dlg.values()
            # 新しい設定をメンバ変数にも、永続化先にも書き込む
            self.default_minutes = m
            self.default_rest = r
            self.settings.setValue("timer/minutes", m)
            self.settings.setValue("timer/rest", r)
            self._reset_display()

    def _on_start_stop(self):
        if not self.timer.isActive():
            # 最初は作業フェーズを開始
            self.is_break = False
            self._start_phase()
            self.timer.start()
            self.start_btn.setText("停止")
        else:
            # 停止したらリセット表示に戻す
            self.timer.stop()
            self._reset_display()

    def _start_phase(self):
        # フェーズに応じて remaining_tenths を設定
        minutes = self.default_rest if self.is_break else self.default_minutes
        self.remaining_tenths = minutes * 60 * 10
        # ラベル色でフェーズを識別（任意）
        color = "green" if self.is_break else "black"
        self.time_label.setStyleSheet(f"font-size:48px; color:{color};")
        self.time_label.setText(f"{minutes:02d}:00")

    def _update_timer(self):
        if self.remaining_tenths <= 0:
            self.is_break = not self.is_break
            self._start_phase()
            # ボタンは停止にして次のフェーズに移る
            self.start_btn.setText("停止")
            return
        self.remaining_tenths -= 1
        total_sec = self.remaining_tenths // 10
        m, s = divmod(total_sec, 60)
        self.time_label.setText(f"{m:02d}:{s:02d}")


class TasksWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # 入力欄＋追加ボタン
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("タスクを入力…")
        self.add_btn = QPushButton("追加")
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_line)
        input_layout.addWidget(self.add_btn)
        layout.addLayout(input_layout)

        # タスクリスト
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

        # サイドバー
        self.nav = QListWidget()
        self.nav.setFixedWidth(120)
        for label in ["⌛️ Pomodoro", "📝 Tasks"]:
            item = QListWidgetItem(label)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.nav.addItem(item)
        main_layout.addWidget(self.nav)

        # スタック
        self.stack = QStackedWidget()
        self.stack.addWidget(PomodoroWidget())
        self.stack.addWidget(TasksWidget())
        main_layout.addWidget(self.stack, stretch=1)

        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav.setCurrentRow(0)


if __name__ == "__main__":
    # まずアプリケーション情報を設定
    app = QApplication(sys.argv)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())
