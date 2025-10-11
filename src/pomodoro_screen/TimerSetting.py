from PyQt6.QtWidgets import (QDialog, QFormLayout, QSpinBox, QCheckBox,
                             QDialogButtonBox, QLabel)
from PyQt6.QtCore import Qt


class TimerSettingDialog(QDialog):
    def __init__(self, parent=None, minutes=25, rest=5,
                 auto_next=False, auto_break=False):
        super().__init__(parent)
        self.setWindowTitle("タイマーの設定")
        self.resize(320, 260)

        # ラベルと入力フォームのペアでWidgetを配置するクラス
        layout = QFormLayout(self)

        # 入力フォームは中央寄せ
        layout.setFormAlignment(Qt.AlignmentFlag.AlignCenter)
        # 水平方向に20だけ間隔をあけて, 垂直方向に15だけ開ける
        layout.setHorizontalSpacing(20)
        layout.setVerticalSpacing(15)

        # ---------------------------------------------------------------------
        # ポモドーロの時間の設定を行う
        # ---------------------------------------------------------------------

        # 整数値の入力や、上下の矢印ボタンで値を増減することもできる
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

        # ---------------------------------------------------------------------
        # 休憩時間の設定を行う
        # ---------------------------------------------------------------------
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

        # ---------------------------------------------------------------------
        # ポモドーロと休憩時間の自動開始の有無
        # ---------------------------------------------------------------------

        self.chk_auto_next = QCheckBox("次のポモドーロを自動で開始")
        self.chk_auto_next.setChecked(auto_next)
        self.chk_auto_next.setStyleSheet("color: #ffffff;")
        layout.addRow(self.chk_auto_next)

        self.chk_auto_break = QCheckBox("休憩を自動開始")
        self.chk_auto_break.setChecked(auto_break)
        self.chk_auto_break.setStyleSheet("color: #ffffff;")
        layout.addRow(self.chk_auto_break)

        # ---------------------------------------------------------------------
        # OK, Cancelボタンの設定
        # ---------------------------------------------------------------------
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
        """Timerで設定した値を返す

        Returns:
            self.pomo_time.value() (int): ポモドーロの時間を返す
            self.rest_time.value() (int): 休憩時間を返す
            self.chk_auto_next.isChecked() (bool): ポモドーロを自動開始の有無
            self.chk_auto_break.isChecked() (bool): 休憩の自動開始の有無
        """
        return (
            self.pomo_time.value(),
            self.rest_time.value(),
            self.chk_auto_next.isChecked(),
            self.chk_auto_break.isChecked()
        )
