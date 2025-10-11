"""Simple time tracking widget with start/stop buttons."""
import datetime
from typing import Optional

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.pomodoro_screen.shared_state import SharedTimerState


class SimpleTrackerWidget(QWidget):
    """Simple widget with start/stop buttons for time tracking."""

    def __init__(self, shared_state: SharedTimerState) -> None:
        super().__init__()

        # Shared state
        self.shared_state = shared_state

        # Settings initialization
        self.task_settings = QSettings("CHU1PC", "TaskManagerApp")

        # Tracking state
        self.session_start_time: Optional[datetime.datetime] = None
        self.session_start_date: Optional[str] = None  # Store the date when tracking started
        self.is_tracking: bool = False

        # Initialize UI
        self._init_ui()

        # Connect to shared state signals
        self.shared_state.task_changed.connect(self._on_shared_task_changed)

        # Load initial task
        self._refresh_tasks()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Title
        title = QLabel("簡単計測")
        title.setStyleSheet("""
            color: #ffffff;
            font-size: 24px;
            font-weight: bold;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Task selection
        task_label = QLabel("タスク:")
        task_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        main_layout.addWidget(task_label)

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
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                color: #ffffff;
                selection-background-color: #5c5c5c;
            }
        """)
        self.task_combo.currentTextChanged.connect(self._on_task_changed)
        main_layout.addWidget(self.task_combo)

        # Current task display
        self.current_task_label = QLabel("タスクが選択されていません")
        self.current_task_label.setStyleSheet("""
            color: #ffffff;
            background-color: #333;
            border-radius: 5px;
            padding: 10px;
            font-size: 14px;
        """)
        self.current_task_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.current_task_label)

        # Status label
        self.status_label = QLabel("計測していません")
        self.status_label.setStyleSheet("""
            color: #888;
            font-size: 16px;
            padding: 20px;
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        main_layout.addStretch()

        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)

        # Start button
        self.start_btn = QPushButton("計測開始")
        self.start_btn.setFixedSize(200, 80)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5aa0f2;
            }
            QPushButton:disabled {
                background-color: #3c3c3c;
                color: #666;
            }
        """)
        self.start_btn.clicked.connect(self._on_start_clicked)
        buttons_layout.addWidget(self.start_btn)

        # Stop button
        self.stop_btn = QPushButton("計測停止")
        self.stop_btn.setFixedSize(200, 80)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e24a4a;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f25a5a;
            }
            QPushButton:disabled {
                background-color: #3c3c3c;
                color: #666;
            }
        """)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        self.stop_btn.setEnabled(False)
        buttons_layout.addWidget(self.stop_btn)

        main_layout.addLayout(buttons_layout)
        main_layout.addStretch()

    def _on_start_clicked(self) -> None:
        """Handle start button click."""
        if not self.shared_state.selected_task:
            # Prompt user to select a task first
            self._prompt_task_selection()
            if not self.shared_state.selected_task:
                return

        self.is_tracking = True
        self.session_start_time = datetime.datetime.now()
        self.session_start_date = datetime.date.today().isoformat()  # Record the date when tracking starts

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        start_time_str = self.session_start_time.strftime("%H:%M:%S")
        self.status_label.setText(f"計測中... 開始時刻: {start_time_str}")
        self.status_label.setStyleSheet("""
            color: #4ae24a;
            font-size: 16px;
            padding: 20px;
        """)

    def _on_stop_clicked(self) -> None:
        """Handle stop button click."""
        if not self.is_tracking or self.session_start_time is None:
            return

        end_time = datetime.datetime.now()
        duration = end_time - self.session_start_time

        # Calculate duration in minutes
        duration_minutes = int(duration.total_seconds() / 60)

        if duration_minutes < 1:
            duration_minutes = 1  # At least 1 minute

        # Save session
        self._save_session(self.session_start_time, end_time, duration_minutes)

        # Reset state
        self.is_tracking = False
        self.session_start_time = None
        self.session_start_date = None

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        self.status_label.setText(f"保存完了: {duration_minutes}分")
        self.status_label.setStyleSheet("""
            color: #888;
            font-size: 16px;
            padding: 20px;
        """)

    def _save_session(self, start_time: datetime.datetime, end_time: datetime.datetime, duration_minutes: int) -> None:
        """Save session data with merging logic."""
        # Use the date when tracking started, not the current date
        today = self.session_start_date if self.session_start_date else datetime.date.today().isoformat()

        # Load existing sessions
        task_sessions = self.task_settings.value("task_sessions", [])

        # Create new session data
        new_session = {
            "task": self.shared_state.selected_task,
            "date": today,
            "start_time": start_time.strftime("%H:%M"),
            "end_time": end_time.strftime("%H:%M"),
            "duration_minutes": duration_minutes
        }

        # Check for recent sessions to merge (within 5 minutes)
        merged = False
        for i, session in enumerate(task_sessions):
            if (session.get("task") == self.shared_state.selected_task and
                session.get("date") == today):

                try:
                    # Parse session end time
                    session_end_str = session.get("end_time", "00:00")
                    session_end = datetime.datetime.strptime(f"{today} {session_end_str}", "%Y-%m-%d %H:%M")

                    # Calculate gap between sessions
                    gap = start_time - session_end
                    gap_minutes = gap.total_seconds() / 60

                    # If gap is 5 minutes or less, merge sessions
                    if 0 <= gap_minutes <= 5:
                        # Update the existing session's end time and duration
                        task_sessions[i]["end_time"] = end_time.strftime("%H:%M")
                        task_sessions[i]["duration_minutes"] += duration_minutes
                        merged = True
                        break
                except (ValueError, KeyError):
                    continue

        # If not merged, add as new session
        if not merged:
            task_sessions.append(new_session)

        # Save sessions
        self.task_settings.setValue("task_sessions", task_sessions)

        # Update total study time
        study_records = self.task_settings.value("study_time", {})
        if today not in study_records:
            study_records[today] = 0
        study_records[today] += duration_minutes
        self.task_settings.setValue("study_time", study_records)

        # Update task-specific study time
        task_study_records = self.task_settings.value("task_study_time", {})
        if self.shared_state.selected_task not in task_study_records:
            task_study_records[self.shared_state.selected_task] = {}
        if today not in task_study_records[self.shared_state.selected_task]:
            task_study_records[self.shared_state.selected_task][today] = 0
        task_study_records[self.shared_state.selected_task][today] += duration_minutes
        self.task_settings.setValue("task_study_time", task_study_records)

    def _prompt_task_selection(self) -> None:
        """Prompt user to select a task."""
        stored_tasks = self.task_settings.value("tasks", [])

        tasks: list[str] = []
        for task in stored_tasks:
            name = task.get("text", "")
            check = task.get("checked", False)
            if not check and name:
                tasks.append(name)

        if not tasks:
            return

        selected, ok = QInputDialog.getItem(
            self, "タスク選択", "記録するタスクを選んでください:", tasks, 0, False
        )

        if ok and selected:
            idx = self.task_combo.findText(selected)
            if idx >= 0:
                self.task_combo.setCurrentIndex(idx)

    def _on_task_changed(self, task_text: str) -> None:
        """Handle task selection change."""
        if task_text == "タスクなし" or not task_text:
            self.shared_state.selected_task = None
            self.current_task_label.setText("タスクが選択されていません")
        else:
            self.shared_state.selected_task = task_text
            display_text = task_text if len(task_text) <= 30 else task_text[:27] + "..."
            self.current_task_label.setText(f"選択中: {display_text}")

    def _on_shared_task_changed(self, task: str) -> None:
        """Handle task change from shared state."""
        self.task_combo.blockSignals(True)
        idx = self.task_combo.findText(task if task else "タスクなし")
        if idx >= 0:
            self.task_combo.setCurrentIndex(idx)
        self.task_combo.blockSignals(False)

        if task:
            display_text = task if len(task) <= 30 else task[:27] + "..."
            self.current_task_label.setText(f"選択中: {display_text}")
        else:
            self.current_task_label.setText("タスクが選択されていません")

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

        # Restore selection
        idx = self.task_combo.findText(current_text)
        if idx >= 0:
            self.task_combo.setCurrentIndex(idx)
        else:
            self.task_combo.setCurrentIndex(0)

        self.task_combo.blockSignals(False)

        # Manually update shared state
        selected_text = self.task_combo.currentText()
        if selected_text and selected_text != "タスクなし":
            self.shared_state.selected_task = selected_text
            display_text = selected_text if len(selected_text) <= 30 else selected_text[:27] + "..."
            self.current_task_label.setText(f"選択中: {display_text}")
        else:
            self.shared_state.selected_task = None
            self.current_task_label.setText("タスクが選択されていません")
