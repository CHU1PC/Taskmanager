"""Stopwatch widget for continuous time tracking with auto-save."""
import datetime

from PyQt6.QtCore import QSettings, Qt, QTimer, QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.pomodoro_screen.shared_state import SharedTimerState
from app.utils import resource_path


class StopwatchWidget(QWidget):
    """Stopwatch widget for tracking time continuously with auto-save."""

    def __init__(self, shared_state: SharedTimerState) -> None:
        super().__init__()

        # Shared state
        self.shared_state = shared_state

        # Settings initialization
        self.settings = QSettings("CHU1PC", "PomodoroApp")
        self.task_settings = QSettings("CHU1PC", "TaskManagerApp")

        # Stopwatch state
        self.is_running: bool = False
        self.last_save_tenths: int = 0

        # Auto-save interval (120 seconds = 1200 tenths)
        self.auto_save_interval: int = 1200

        # Initialize UI, audio, and timer
        self._init_ui()
        self._init_audio()
        self._init_timer()

        # Connect to shared state signals
        self.shared_state.task_changed.connect(self._on_shared_task_changed)
        self.shared_state.time_updated.connect(self._on_shared_time_updated)

        # Load initial task
        self._refresh_tasks()

        # Initial display update
        self._update_display()

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
        """Create the left panel with stopwatch display and controls."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Title
        title = QLabel("ストップウォッチ")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: bold;")

        # Time display
        self.time_label = QLabel("00:00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.time_label.setStyleSheet("color: #ffffff; font-size: 64px; font-family: monospace;")

        # Buttons
        btn_layout = self._create_control_buttons()

        # Auto-save indicator
        self.save_indicator = QLabel("最終保存: 未保存")
        self.save_indicator.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.save_indicator.setStyleSheet("""
            color: #aaa;
            font-size: 12px;
            padding: 5px;
        """)

        # Add to layout
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.time_label)
        layout.addWidget(self.save_indicator)
        layout.addStretch()
        layout.addLayout(btn_layout)

        return panel

    def _create_control_buttons(self) -> QHBoxLayout:
        """Create start, stop, and reset buttons."""
        btn_layout = QHBoxLayout()
        button_style = """
            QPushButton {
                font-size: 20px;
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

        self.start_stop_btn = QPushButton("開始")
        self.start_stop_btn.setStyleSheet(button_style)
        self.start_stop_btn.clicked.connect(self._on_start_stop)

        self.reset_btn = QPushButton("リセット")
        self.reset_btn.setStyleSheet(button_style)
        self.reset_btn.clicked.connect(self._on_reset)

        self.save_btn = QPushButton("手動保存")
        self.save_btn.setStyleSheet(button_style)
        self.save_btn.clicked.connect(self._manual_save)

        btn_layout.addWidget(self.start_stop_btn)
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addWidget(self.save_btn)

        return btn_layout

    def _create_right_panel(self) -> QWidget:
        """Create the right panel with task selection and statistics."""
        panel = QWidget()
        layout = QGridLayout(panel)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        label_style = """
            QWidget {
                background-color: #222;
                color: #ddd;
                border-radius: 8px;
                padding: 8px;
            }
        """

        # Session time
        self.session_label = QLabel("今セッション: 0分")
        self.session_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.session_label.setStyleSheet(label_style)

        # Separator
        separator = self._create_horizontal_separator()

        # Task selection
        task_label = QLabel("現在のタスク")
        task_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        task_label.setStyleSheet(label_style)

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
        self.task_combo.currentTextChanged.connect(self._on_task_changed)

        self.current_task_label = QLabel("選択されていません")
        self.current_task_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_task_label.setStyleSheet(label_style + "font-weight: bold;")

        # Add to layout
        layout.addWidget(self.session_label, 0, 0, 1, 2)
        layout.addWidget(separator, 1, 0, 1, 2)
        layout.addWidget(task_label, 2, 0, 1, 2)
        layout.addWidget(self.task_combo, 3, 0, 1, 2)
        layout.addWidget(self.current_task_label, 4, 0, 1, 2)

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
        # Sound effects player
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        # Use same volume settings as Pomodoro
        saved_volume = float(self.settings.value("audio/volume", 0.5))
        self.audio_output.setVolume(saved_volume)

        # Load sound files
        self.save_sound = QUrl.fromLocalFile(resource_path("audio/beep1.mp3"))

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
        self.timer.timeout.connect(self._update_timer)

    # Shared state handlers
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

    def _on_shared_time_updated(self, tenths: int) -> None:
        """Handle time update from shared state."""
        self._update_display()

    # Event handlers
    def _on_start_stop(self) -> None:
        """Handle start/stop button click."""
        if not self.is_running:
            if not self.shared_state.selected_task:
                # Prompt user to select a task first
                self._prompt_task_selection()
                if not self.shared_state.selected_task:
                    return

            self.is_running = True
            self.timer.start()
            self.start_stop_btn.setText("停止")
            # Start BGM
            self.bgm_player.play()
        else:
            self.is_running = False
            self.timer.stop()
            self.start_stop_btn.setText("再開")
            # Pause BGM
            self.bgm_player.pause()
            # Save on stop
            self._save_time()

    def _on_reset(self) -> None:
        """Handle reset button click."""
        if self.timer.isActive():
            self.timer.stop()

        # Stop BGM
        self.bgm_player.stop()

        # Save before reset
        if self.shared_state.elapsed_tenths > 0:
            self._save_time()

        self.is_running = False
        self.shared_state.elapsed_tenths = 0
        self.last_save_tenths = 0
        self.start_stop_btn.setText("開始")
        self._update_display()
        self.save_indicator.setText("最終保存: リセット済み")

    def _manual_save(self) -> None:
        """Handle manual save button click."""
        if self.shared_state.elapsed_tenths > 0:
            self._save_time()

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
        self.settings.setValue("stopwatch_task", task_text if task_text != "タスクなし" else "")

    def _update_timer(self) -> None:
        """Update timer (called every 100ms)."""
        self.shared_state.elapsed_tenths += 1
        self._update_display()

        # Auto-save every 2 minutes
        if self.shared_state.elapsed_tenths - self.last_save_tenths >= self.auto_save_interval:
            self._save_time()

    def _update_display(self) -> None:
        """Update time display."""
        total_seconds = self.shared_state.elapsed_tenths // 10
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        # Update session time
        session_minutes = total_seconds // 60
        self.session_label.setText(f"今セッション: {session_minutes}分")

    def _save_time(self) -> None:
        """Save accumulated time to settings."""
        if not self.shared_state.selected_task or self.shared_state.elapsed_tenths <= self.last_save_tenths:
            return

        # Calculate time to save (in minutes, rounded down)
        tenths_to_save = self.shared_state.elapsed_tenths - self.last_save_tenths
        minutes_to_save = tenths_to_save // 600  # Round down to nearest minute

        if minutes_to_save <= 0:
            return

        today = datetime.date.today().isoformat()

        # Record total study time
        study_records = self.task_settings.value("study_time", {})
        if today not in study_records:
            study_records[today] = 0
        study_records[today] += minutes_to_save
        self.task_settings.setValue("study_time", study_records)

        # Record task-specific study time
        task_study_records = self.task_settings.value("task_study_time", {})
        if self.shared_state.selected_task not in task_study_records:
            task_study_records[self.shared_state.selected_task] = {}
        if today not in task_study_records[self.shared_state.selected_task]:
            task_study_records[self.shared_state.selected_task][today] = 0
        task_study_records[self.shared_state.selected_task][today] += minutes_to_save

        self.task_settings.setValue("task_study_time", task_study_records)

        # Update last save point
        self.last_save_tenths = self.shared_state.elapsed_tenths

        # Update indicator
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.save_indicator.setText(f"最終保存: {now} ({minutes_to_save}分)")

        # Play save sound
        self.player.setSource(self.save_sound)
        self.player.play()

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

        # Determine which task to select
        task_to_select = None
        if self.shared_state.selected_task:
            task_to_select = self.shared_state.selected_task
        elif current_text and current_text != "タスクなし":
            task_to_select = current_text
        else:
            saved_task = self.settings.value("stopwatch_task", "")
            if saved_task:
                task_to_select = saved_task

        # Set the selection
        if task_to_select:
            index = self.task_combo.findText(task_to_select)
            if index >= 0:
                self.task_combo.setCurrentIndex(index)
            else:
                self.task_combo.setCurrentIndex(0)
        else:
            self.task_combo.setCurrentIndex(0)

        self.task_combo.blockSignals(False)

        # Manually update shared state and UI based on current selection
        selected_text = self.task_combo.currentText()
        if selected_text and selected_text != "タスクなし":
            self.shared_state.selected_task = selected_text
            display_text = selected_text if len(selected_text) <= 20 else selected_text[:17] + "..."
            self.current_task_label.setText(f"実行中: {display_text}")
        else:
            self.shared_state.selected_task = None
            self.current_task_label.setText("選択されていません")

    def _prompt_task_selection(self) -> None:
        """Prompt user to select a task before starting."""
        stored_tasks = self.task_settings.value("tasks", [])

        tasks = []
        for task in stored_tasks:
            name = task.get("text", "")
            check = task.get("checked", False)
            if not check and name:
                tasks.append(name)

        if not tasks:
            return

        selected, ok = QInputDialog.getItem(
            self, "タスク選択", "ストップウォッチで記録するタスクを選んでください:", tasks, 0, False
        )
        if ok and selected:
            idx = self.task_combo.findText(selected)
            if idx >= 0:
                self.task_combo.setCurrentIndex(idx)
