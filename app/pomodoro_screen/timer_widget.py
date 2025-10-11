"""Pomodoro timer widget with complete UI and functionality."""
import datetime

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

from app.pomodoro_screen.shared_state import SharedTimerState
from app.pomodoro_screen.TimerSetting import TimerSettingDialog
from app.pomodoro_screen.VolumeSetting import VolumeSettingDialog
from app.utils import resource_path


class TimerWidget(QWidget):
    """Main widget for Pomodoro timer functionality."""

    def __init__(self, shared_state: SharedTimerState) -> None:
        super().__init__()

        # Shared state
        self.shared_state = shared_state

        # Settings initialization
        self.settings = QSettings("CHU1PC", "PomodoroApp")
        self.task_settings = QSettings("CHU1PC", "TaskManagerApp")

        # Load settings
        self._load_settings()

        # Timer state
        self.is_break: bool = False
        self.remaining_tenths: int = 0
        self.total_tenths: int = 0

        # Initialize UI components
        self._init_ui()
        self._init_audio()
        self._init_timer()

        # Connect to shared state signals
        self.shared_state.task_changed.connect(self._on_shared_task_changed)

        # Load initial task and display
        self._refresh_tasks()
        self._reset_display()

    def _load_settings(self) -> None:
        """Load all settings from QSettings."""
        self.default_minutes: int = int(self.settings.value("timer/minutes", 25))
        self.default_rest: int = int(self.settings.value("timer/rest", 5))
        self.auto_next: bool = self.settings.value("timer/auto_next", False, type=bool)
        self.auto_break: bool = self.settings.value("timer/auto_break", False, type=bool)
        self.sets_completed: int = int(self.settings.value("history/total_sets", 0))
        self.goal_minutes: int = int(
            self.settings.value("goal/minutes", self.default_minutes * 4)
        )

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create panels
        left_panel = self._create_left_panel()
        right_panel = self._create_right_panel()

        # Create separator
        separator = self._create_vertical_separator()

        # Add to main layout
        main_layout.addWidget(left_panel, stretch=3)
        main_layout.addWidget(separator)
        main_layout.addWidget(right_panel, stretch=2)

    def _create_left_panel(self) -> QWidget:
        """Create the left panel with timer display and controls."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Volume button
        volume_header = QHBoxLayout()
        self.volume_setting = QPushButton("🔈")
        self.volume_setting.setFixedSize(30, 30)
        self.volume_setting.setStyleSheet("""
            background-color: #404040;
            color: #ffffff;
        """)
        self.volume_setting.clicked.connect(self._open_volume_settings)  # type: ignore
        volume_header.addStretch()
        volume_header.addWidget(self.volume_setting)

        # Time display
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.time_label.setStyleSheet("color: #ffffff; font-size: 48px;")

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(20)

        # Buttons
        btn_layout = self._create_control_buttons()

        # Add to layout
        layout.addLayout(volume_header)
        layout.addStretch()
        layout.addWidget(self.time_label)
        layout.addStretch()
        layout.addWidget(self.progress)
        layout.addLayout(btn_layout)

        return panel

    def _create_control_buttons(self) -> QHBoxLayout:
        """Create start, reset, and skip buttons."""
        btn_layout = QHBoxLayout()
        button_style = """
            QPushButton {
                font-size: 24px;
                background-color: #222;
                color: #fff;
                border: none;
                border-radius: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #007DFF;
            }
            QPushButton:pressed {
                background-color: #333;
            }
        """

        self.start_btn = QPushButton("開始")
        self.start_btn.setStyleSheet(button_style)
        self.start_btn.clicked.connect(self._on_start_stop)  # type: ignore

        self.reset_btn = QPushButton("リセット")
        self.reset_btn.setStyleSheet(button_style)
        self.reset_btn.clicked.connect(self._on_reset)  # type: ignore

        self.skip_btn = QPushButton("スキップ")
        self.skip_btn.setStyleSheet(button_style)
        self.skip_btn.clicked.connect(self._skip_timer)  # type: ignore

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addWidget(self.skip_btn)

        return btn_layout

    def _create_right_panel(self) -> QWidget:
        """Create the right panel with statistics and task selection."""
        panel = QWidget()
        layout = QGridLayout(panel)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Settings button
        settings_header = QHBoxLayout()
        self.settings_btn = QPushButton("…")
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.setStyleSheet("""
            background-color: #404040;
            color: #ffffff;
        """)
        self.settings_btn.clicked.connect(self._open_settings)  # type: ignore
        settings_header.addWidget(self.settings_btn)
        settings_header.addStretch()

        # Statistics labels
        label_style = """
            QWidget {
                background-color: #222;
                color: #ddd;
                border-radius: 8px;
            }
        """

        self.sets_label = QLabel("")
        self.sets_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.sets_label.setStyleSheet(label_style)
        self.sets_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.total_time = QLabel()
        self.total_time.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.total_time.setStyleSheet(label_style)
        self.total_time.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Goal time
        goal_time = QLabel("目標時間")
        goal_time.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        goal_time.setStyleSheet(label_style)

        self.goal_spin = QSpinBox(self)
        self.goal_spin.setFixedSize(120, 30)
        self.goal_spin.setRange(self.default_minutes, self.default_minutes * 99)
        self.goal_spin.setSingleStep(self.default_minutes)
        self.goal_spin.setValue(self.goal_minutes)
        self.goal_spin.setSuffix(" 分")
        self.goal_spin.valueChanged.connect(self._on_goal_changed)  # type: ignore
        self.goal_spin.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.goal_spin.setStyleSheet(label_style)

        # Remaining time/count
        self.remain_time_label = QLabel()
        self.remain_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.remain_time_label.setStyleSheet(label_style)

        self.remain_count_label = QLabel()
        self.remain_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.remain_count_label.setStyleSheet(label_style)

        # Separator
        separator = self._create_horizontal_separator()

        # Task selection
        task_label = QLabel("現在のタスク")
        task_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        task_label.setStyleSheet(label_style + "padding: 5px;")

        self.task_combo = QComboBox()
        self.task_combo.addItem("タスクなし")
        self.task_combo.setStyleSheet("""
            QComboBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                min-height: 35px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 10px;
            }
            QComboBox:hover {
                background-color: #4c4c4c;
                border: 1px solid #777;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                color: #ffffff;
                selection-background-color: #007DFF;
                border: 1px solid #555;
            }
        """)
        self.task_combo.currentTextChanged.connect(self._on_task_changed)  # type: ignore

        self.current_task_label = QLabel("選択されていません")
        self.current_task_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_task_label.setStyleSheet(label_style + "padding: 8px; font-weight: bold;")

        # Add to layout
        layout.addLayout(settings_header, 0, 0)
        layout.addWidget(self.sets_label, 1, 0)
        layout.addWidget(self.total_time, 1, 1)
        layout.addWidget(goal_time, 2, 0)
        layout.addWidget(self.goal_spin, 2, 1)
        layout.addWidget(self.remain_time_label, 3, 0)
        layout.addWidget(self.remain_count_label, 3, 1)
        layout.addWidget(separator, 4, 0, 1, 2)
        layout.addWidget(task_label, 5, 0, 1, 2)
        layout.addWidget(self.task_combo, 6, 0, 1, 2)
        layout.addWidget(self.current_task_label, 7, 0, 1, 2)

        return panel

    def _create_vertical_separator(self) -> QFrame:
        """Create a vertical separator line."""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setLineWidth(3)
        separator.setStyleSheet("background-color: #464646;")
        return separator

    def _create_horizontal_separator(self) -> QFrame:
        """Create a horizontal separator line."""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setLineWidth(2)
        separator.setStyleSheet("background-color: #464646;")
        return separator

    def _init_audio(self) -> None:
        """Initialize audio players."""
        # System tray notifications
        self.study_announce = QSystemTrayIcon(self)
        self.study_announce.setToolTip("Time Manager APP")
        self.study_announce.setVisible(True)

        self.rest_announce = QSystemTrayIcon(self)
        self.rest_announce.setToolTip("Time Manager APP")
        self.rest_announce.setVisible(True)

        # Sound effects player
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        saved_volume = float(self.settings.value("audio/volume", 0.5))
        self.audio_output.setVolume(saved_volume)
        self.work_end_sound = QUrl.fromLocalFile(resource_path("audio/beep2.mp3"))
        self.break_end_sound = QUrl.fromLocalFile(resource_path("audio/beep1.mp3"))
        self.error_sound = QUrl.fromLocalFile(resource_path("audio/error.mp3"))

        # BGM player
        self.bgm_player = QMediaPlayer()
        self.bgm_audio_output = QAudioOutput()
        self.bgm_player.setAudioOutput(self.bgm_audio_output)
        self.bgm_player.setLoops(QMediaPlayer.Loops.Infinite)

        saved_bgm_volume = float(self.settings.value("audio/bgm_volume", 0.2))
        self.bgm_audio_output.setVolume(saved_bgm_volume)
        self.bgm_player.setSource(QUrl.fromLocalFile(resource_path("audio/clock.mp3")))

    def _init_timer(self) -> None:
        """Initialize the timer."""
        self.timer = QTimer(self)
        self.timer.setInterval(100)  # 100ms interval
        self.timer.timeout.connect(self._update_timer)  # type: ignore

    # Event handlers
    def _on_start_stop(self) -> None:
        """Handle start/stop button click."""
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

    def _on_reset(self) -> None:
        """Handle reset button click."""
        if self.timer.isActive():
            self.timer.stop()
        self.bgm_player.stop()
        self.is_break = False
        self.remaining_tenths = 0
        self.sets_completed = 0
        self.settings.setValue("history/total_sets", 0)
        self._reset_display()

    def _skip_timer(self) -> None:
        """Handle skip button click."""
        self.remaining_tenths = 0
        self.bgm_player.stop()

    def _on_goal_changed(self, value: int) -> None:
        """Handle goal time change."""
        self.goal_minutes = value
        self.settings.setValue("goal/minutes", value)
        self._update_remaining()

    def _on_task_changed(self, task_text: str) -> None:
        """Handle task selection change."""
        if task_text == "タスクなし" or not task_text:
            self.shared_state.selected_task = None
            self.current_task_label.setText("選択されていません")
        else:
            self.shared_state.selected_task = task_text
            display_text = task_text if len(task_text) <= 20 else task_text[:17] + "..."
            self.current_task_label.setText(f"実行中: {display_text}")

        # Save selected task
        self.settings.setValue("current_task", task_text if task_text != "タスクなし" else "")

    def _on_shared_task_changed(self, task: str) -> None:
        """Handle task change from shared state."""
        # Update combo box without triggering signal
        self.task_combo.blockSignals(True)
        idx = self.task_combo.findText(task if task else "タスクなし")
        if idx >= 0:
            self.task_combo.setCurrentIndex(idx)
        self.task_combo.blockSignals(False)

        # Update display
        if task:
            display_text = task if len(task) <= 20 else task[:17] + "..."
            self.current_task_label.setText(f"実行中: {display_text}")
        else:
            self.current_task_label.setText("選択されていません")

    def _open_settings(self) -> None:
        """Open timer settings dialog."""
        parent = self.window()
        dlg = TimerSettingDialog(
            parent,
            self.default_minutes,
            self.default_rest,
            self.auto_next,
            self.auto_break
        )
        dlg.setModal(True)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            m, r, auto_next, auto_break = dlg.values()
            self.default_minutes = m
            self.default_rest = r
            self.auto_next = auto_next
            self.auto_break = auto_break

            # Save to settings
            self.settings.setValue("timer/minutes", m)
            self.settings.setValue("timer/rest", r)
            self.settings.setValue("timer/auto_next", auto_next)
            self.settings.setValue("timer/auto_break", auto_break)

            self._reset_display()
        if parent:
            parent.raise_()

    def _open_volume_settings(self) -> None:
        """Open volume settings dialog."""
        current_sfx_volume_per = int(self.audio_output.volume() * 100)
        current_bgm_volume_per = int(self.bgm_audio_output.volume() * 100)

        dlg = VolumeSettingDialog(
            self,
            initial_bgm_volume=current_bgm_volume_per,
            initial_sfx_volume=current_sfx_volume_per
        )

        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_sfx_volume_per, new_bgm_volume_per = dlg.values()

            new_sfx_volume_float = new_sfx_volume_per / 100.0
            new_bgm_volume_float = new_bgm_volume_per / 100.0

            self.audio_output.setVolume(new_sfx_volume_float)
            self.bgm_audio_output.setVolume(new_bgm_volume_float)

            self.settings.setValue("audio/volume", new_sfx_volume_float)
            self.settings.setValue("audio/bgm_volume", new_bgm_volume_float)

    # Timer logic
    def _start_phase(self) -> None:
        """Start a work or break phase."""
        duration = self.default_rest if self.is_break else self.default_minutes
        self.total_tenths = duration * 60 * 10
        self.remaining_tenths = self.total_tenths
        color = "green" if self.is_break else "white"
        self.time_label.setStyleSheet(f"font-size:48px; color:{color};")
        self.progress.setRange(0, self.total_tenths)
        self.progress.setValue(self.total_tenths)
        self.start_btn.setText("停止")

    def _update_timer(self) -> None:
        """Update timer countdown."""
        if self.remaining_tenths > 0:
            self.remaining_tenths -= 1
            sec = self.remaining_tenths // 10
            m, s = divmod(sec, 60)
            self.time_label.setText(f"{m:02d}:{s:02d}")
            self.progress.setValue(self.remaining_tenths)
            return

        self.bgm_player.stop()

        # Increment set count after work phase
        if not self.is_break:
            self.sets_completed += 1
            self.settings.setValue("history/total_sets", self.sets_completed)

        # Play sound and show notification
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
            if not self.shared_state.selected_task:
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

        # Switch phase
        self.is_break = not self.is_break
        self.timer.stop()
        self._reset_display()

        # Auto-start next phase if enabled
        if self.is_break and self.auto_break:
            self._start_phase()
            self.timer.start()
        elif not self.is_break and self.auto_next:
            self._start_phase()
            self.timer.start()

    def _record_study_time(self, minutes: int) -> bool:
        """Record study time for the current task."""
        today = datetime.date.today().isoformat()

        # If no task is selected, prompt user to select one
        if not self.shared_state.selected_task:
            stored_tasks = self.task_settings.value("tasks", [])

            tasks: list[str] = []
            for task in stored_tasks:
                name = task.get("text", "")
                check = task.get("checked", False)
                if not check and name:
                    tasks.append(name)

            selected, ok = QInputDialog.getItem(  # type: ignore
                self, "タスク選択", "記録するタスクを選んでください:", tasks, 0, False
            )
            if not ok or not selected:
                return False

            idx = self.task_combo.findText(selected)
            if idx >= 0:
                self.task_combo.setCurrentIndex(idx)
            else:
                self.shared_state.selected_task = selected
                self.settings.setValue("current_task", selected)
                disp = selected if len(selected) <= 20 else selected[:17] + "..."
                self.current_task_label.setText(f"実行中: {disp}")

        # Record total study time
        study_records = self.task_settings.value("study_time", {})
        if today not in study_records:
            study_records[today] = 0
        study_records[today] += minutes
        self.task_settings.setValue("study_time", study_records)

        # Record task-specific study time
        task_study_records = self.task_settings.value("task_study_time", {})
        if self.shared_state.selected_task not in task_study_records:
            task_study_records[self.shared_state.selected_task] = {}
        if today not in task_study_records[self.shared_state.selected_task]:
            task_study_records[self.shared_state.selected_task][today] = 0
        task_study_records[self.shared_state.selected_task][today] += minutes

        self.task_settings.setValue("task_study_time", task_study_records)

        return True

    def refresh_tasks(self) -> None:
        """Public method to refresh task list."""
        self._refresh_tasks()

    def _refresh_tasks(self) -> None:
        """Refresh task list from settings."""
        current_text = self.task_combo.currentText()

        self.task_combo.blockSignals(True)
        self.task_combo.clear()
        self.task_combo.addItem("タスクなし")

        stored_tasks = self.task_settings.value("tasks", [])

        for task_entry in stored_tasks:
            task_text = task_entry.get("text", "")
            task_check = task_entry.get("checked", False)
            if task_text and not task_check:
                self.task_combo.addItem(task_text)

        # Restore shared state selection first, then previous selection
        if self.shared_state.selected_task:
            index = self.task_combo.findText(self.shared_state.selected_task)
            if index >= 0:
                self.task_combo.setCurrentIndex(index)
            else:
                self.task_combo.setCurrentIndex(0)
        else:
            index = self.task_combo.findText(current_text)
            if index >= 0:
                self.task_combo.setCurrentIndex(index)
            else:
                self.task_combo.setCurrentIndex(0)

        self.task_combo.blockSignals(False)

    def _reset_display(self) -> None:
        """Reset display to initial state."""
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

        # Restore saved task selection from shared state or settings
        if self.shared_state.selected_task:
            index = self.task_combo.findText(self.shared_state.selected_task)
            if index >= 0:
                self.task_combo.setCurrentIndex(index)
        else:
            saved_task = self.settings.value("current_task", "")
            if saved_task:
                index = self.task_combo.findText(saved_task)
                if index >= 0:
                    self.task_combo.setCurrentIndex(index)

    def _update_remaining(self) -> None:
        """Update remaining time and count display."""
        done = self.sets_completed * self.default_minutes
        remain = max(0, self.goal_minutes - done)

        if self.default_minutes > 0:
            need = (remain + self.default_minutes - 1) // self.default_minutes
        else:
            need = 0

        h, m = divmod(remain, 60)
        self.remain_time_label.setText(f"残り時間:\n{h}時間{m}分")
        self.remain_count_label.setText(f"残りポモドーロ数:\n{need}回")
