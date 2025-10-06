from PyQt6.QtCore import QSettings, Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)


def create_setting_button() -> QPushButton:
    header = QHBoxLayout()
    settings_btn = QPushButton("…")
    settings_btn.setFixedSize(30, 30)
    settings_btn.setStyleSheet("""
            background-color: #404040;
            color: #ffffff;
        """)
    header.addWidget(settings_btn)
    header.addStretch()

    return settings_btn


def create_goal_spin_box(default_minutes: int, goal_minutes: int) -> QSpinBox:
    goal_spin = QSpinBox()
    goal_spin.setFixedSize(120, 30)
    # 目標時間はポモドーロの時間単位で設定できるようにしたいためrangeを設定する
    goal_spin.setRange(default_minutes, default_minutes * 99)
    # setSingleStepで矢印が押されたときにどれだけ値が増減するかを決める
    goal_spin.setSingleStep(default_minutes)
    goal_spin.setValue(goal_minutes)
    goal_spin.setSuffix(" 分")
    goal_spin.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
    goal_spin.setStyleSheet("""
        QWidget {
            background-color: #222;
            color: #ddd;
        }
    """)

    return goal_spin


def create_goal_time_label() -> QLabel:
    goal_time = QLabel("目標時間")
    goal_time.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
    goal_time.setStyleSheet("""
        QWidget {
            background-color: #222;
            color: #ddd;
            border-radius: 8px;
        }
    """)

    return goal_time


def create_total_time_label() -> QLabel:
    total_time = QLabel()
    total_time.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
    total_time.setStyleSheet("""
            QWidget {
                background-color: #222;
                color: #ddd;
                border-radius: 8px;
            }
        """)
    total_time.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    return total_time


def create_volume_header() -> tuple[QHBoxLayout, QPushButton]:
    volume_header = QHBoxLayout()
    volume_setting = QPushButton("🔈")
    volume_setting.setFixedSize(30, 30)
    volume_setting.setStyleSheet("""
            background-color: #404040;
            color: #ffffff;
        """)
    volume_header.addStretch()
    volume_header.addWidget(volume_setting)

    return volume_header, volume_setting


def create_set_label() -> QLabel:
    sets_label = QLabel("")
    sets_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    sets_label.setStyleSheet("""
        QWidget {
            background-color: #222;
            color: #ddd;
            border-radius: 8px;
        }
    """)
    sets_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    return sets_label


def create_remain_labels() -> tuple[QLabel, QLabel]:
    remain_time_label = QLabel()
    remain_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    remain_time_label.setStyleSheet("""
        QWidget {
            background-color: #222;
            color: #ddd;
            border-radius: 8px;
        }
    """)
    remain_count_label = QLabel()
    remain_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    return remain_time_label, remain_count_label
