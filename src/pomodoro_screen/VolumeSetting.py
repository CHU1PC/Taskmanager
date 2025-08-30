from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QVBoxLayout, QLabel,
                             QSlider
                             )
from PyQt6.QtCore import Qt


class VolumeSettingDialog(QDialog):
    def __init__(self, parent=None,
                 initial_bgm_volume=20, initial_sfx_volume=50):
        super().__init__(parent)

        # ウィジェットを縦に並べる
        layout = QVBoxLayout(self)

        # ---------------------------------------------------------------------
        # 効果音用
        # ---------------------------------------------------------------------
        self.sfx_volume_label = QLabel(f"効果音の音量: {initial_sfx_volume}%")
        self.sfx_volume_label.setStyleSheet("""
                background-color: #404040;
                color: #ffffff;
            """)
        self.sfx_volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.sfx_volume_label)

        # 効果音用音量調整スライダー
        self.sfx_slider = QSlider(Qt.Orientation.Horizontal)
        self.sfx_slider.setRange(0, 100)
        self.sfx_slider.setValue(initial_sfx_volume)
        layout.addWidget(self.sfx_slider)

        # ---------------------------------------------------------------------
        # BGM用
        # ---------------------------------------------------------------------
        self.bgm_volume_label = QLabel(f"BGMの音量: {initial_bgm_volume}%")
        self.bgm_volume_label.setStyleSheet("""
                background-color: #404040;
                color: #ffffff;
            """)
        self.bgm_volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.bgm_volume_label)

        # BGM音量調整スライダー
        self.bgm_slider = QSlider(Qt.Orientation.Horizontal)
        self.bgm_slider.setRange(0, 100)
        self.bgm_slider.setValue(initial_bgm_volume)
        layout.addWidget(self.bgm_slider)

        # ---------------------------------------------------------------------
        # スライダーの値が変更されたらラベルを更新
        # ---------------------------------------------------------------------
        self.sfx_slider.valueChanged.connect(
            lambda value: self.sfx_volume_label.setText(f"効果音の音量: {value}%")
        )
        self.bgm_slider.valueChanged.connect(
            lambda value: self.bgm_volume_label.setText(f"BGMの音量: {value}%")
        )

        # ---------------------------------------------------------------------
        # OK/Cancelボタン
        # ---------------------------------------------------------------------
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.setStyleSheet("color: #ffffff;")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        """効果音の音量とBGMの音量を返す

        Returns:
            self.sfx_slider.value() (int): 効果音の音量
            self.bgm_slider.value() (int): BGMの音量
        """
        return (self.sfx_slider.value(), self.bgm_slider.value())
