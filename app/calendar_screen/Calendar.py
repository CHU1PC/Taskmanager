from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta, time

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCalendarWidget,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QMessageBox, QFrame, QScrollArea, QButtonGroup, QRadioButton, QToolTip,
    QDialog, QDateEdit, QTimeEdit, QDialogButtonBox, QFormLayout, QTextEdit, QComboBox, QMenu
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QSettings, QDate, QTime, QRect, pyqtSignal
from PyQt6.QtGui import QTextCharFormat, QColor, QPainter, QPen, QMouseEvent
from PyQt6.QtWidgets import QSizePolicy

from .WeekTimelineWidget import WeekTimelineWidget


class AddSessionDialog(QDialog):
    """Dialog to manually add or edit a session to the calendar."""

    def __init__(self, parent=None, session_data: Optional[Dict] = None):
        super().__init__(parent)
        self.settings = QSettings("CHU1PC", "TaskManagerApp")
        self.session_data = session_data  # If editing existing session
        self.is_editing = session_data is not None

        if self.is_editing:
            self.setWindowTitle("セッションを編集")
        else:
            self.setWindowTitle("セッションを追加")

        self.setMinimumWidth(450)

        # Dark theme styling
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QDateEdit, QTimeEdit, QComboBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                color: #ffffff;
                selection-background-color: #5c5c5c;
            }
            QPushButton {
                background-color: #4a6fa5;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5a7fb5;
            }
        """)

        self._init_ui()

    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)

        # Title
        if self.is_editing:
            title_text = "セッションを編集"
        else:
            title_text = "セッションを手動で追加"
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        # Form layout
        form_layout = QFormLayout()

        # Task selection
        self.task_combo = QComboBox()
        self._load_tasks()
        form_layout.addRow("タスク:", self.task_combo)

        # Start date
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy/MM/dd")

        # Start time
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm")

        # End date
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy/MM/dd")

        # End time
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm")

        # Set initial values (edit mode or default)
        if self.is_editing and self.session_data:
            # Load existing session data
            task_name = self.session_data.get("task", "")
            session_date_str = self.session_data.get("date", "")
            start_time_str = self.session_data.get("start_time", "00:00")
            end_time_str = self.session_data.get("end_time", "00:00")

            # Check if there's an end_date field (new format) or use date for both (old format)
            end_date_str = self.session_data.get("end_date", session_date_str)

            # Set task
            index = self.task_combo.findText(task_name)
            if index >= 0:
                self.task_combo.setCurrentIndex(index)

            # Set start date
            try:
                start_date = datetime.strptime(session_date_str, "%Y-%m-%d").date()
                self.start_date_edit.setDate(QDate(start_date.year, start_date.month, start_date.day))
            except ValueError:
                self.start_date_edit.setDate(QDate.currentDate())

            # Set end date
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                self.end_date_edit.setDate(QDate(end_date.year, end_date.month, end_date.day))
            except ValueError:
                self.end_date_edit.setDate(QDate.currentDate())

            # Set times
            try:
                start_time = datetime.strptime(start_time_str, "%H:%M").time()
                self.start_time_edit.setTime(QTime(start_time.hour, start_time.minute))
            except ValueError:
                self.start_time_edit.setTime(QTime.currentTime())

            try:
                end_time = datetime.strptime(end_time_str, "%H:%M").time()
                self.end_time_edit.setTime(QTime(end_time.hour, end_time.minute))
            except ValueError:
                self.end_time_edit.setTime(QTime.currentTime().addSecs(3600))
        else:
            # Default values for new session
            self.start_date_edit.setDate(QDate.currentDate())
            self.end_date_edit.setDate(QDate.currentDate())
            self.start_time_edit.setTime(QTime.currentTime())
            self.end_time_edit.setTime(QTime.currentTime().addSecs(3600))  # +1 hour

        form_layout.addRow("開始日:", self.start_date_edit)
        form_layout.addRow("開始時刻:", self.start_time_edit)
        form_layout.addRow("終了日:", self.end_date_edit)
        form_layout.addRow("終了時刻:", self.end_time_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_tasks(self):
        """Load tasks from settings."""
        stored_tasks = self.settings.value("tasks", [])

        for task_entry in stored_tasks:
            task_text = task_entry.get("text", "")
            task_check = task_entry.get("checked", False)
            if task_text and not task_check:
                self.task_combo.addItem(task_text)

        if self.task_combo.count() == 0:
            self.task_combo.addItem("タスクなし")

    def _accept(self):
        """Validate and accept the dialog."""
        # Validate task
        task_name = self.task_combo.currentText()
        if not task_name or task_name == "タスクなし":
            QMessageBox.warning(self, "エラー", "タスクを選択してください。")
            return

        # Validate dates and times
        start_date = self.start_date_edit.date().toPyDate()
        start_time = self.start_time_edit.time()
        end_date = self.end_date_edit.date().toPyDate()
        end_time = self.end_time_edit.time()

        # Combine date and time for comparison
        start_datetime = datetime.combine(start_date, start_time.toPyTime())
        end_datetime = datetime.combine(end_date, end_time.toPyTime())

        if start_datetime >= end_datetime:
            QMessageBox.warning(self, "エラー", "開始日時は終了日時より前である必要があります。")
            return

        # Calculate duration in minutes
        duration = end_datetime - start_datetime
        duration_minutes = int(duration.total_seconds() / 60)

        if duration_minutes <= 0:
            QMessageBox.warning(self, "エラー", "所要時間が0分以下です。")
            return

        self.accept()

    def get_session_data(self) -> Dict:
        """Get the session data from the dialog."""
        task_name = self.task_combo.currentText()
        start_date = self.start_date_edit.date().toPyDate()
        start_time = self.start_time_edit.time()
        end_date = self.end_date_edit.date().toPyDate()
        end_time = self.end_time_edit.time()

        # Calculate duration
        start_datetime = datetime.combine(start_date, start_time.toPyTime())
        end_datetime = datetime.combine(end_date, end_time.toPyTime())
        duration = end_datetime - start_datetime
        duration_minutes = int(duration.total_seconds() / 60)

        return {
            "task": task_name,
            "date": start_date.isoformat(),  # Keep "date" for backward compatibility (start date)
            "end_date": end_date.isoformat(),  # Add end_date field
            "start_time": start_time.toString("HH:mm"),
            "end_time": end_time.toString("HH:mm"),
            "duration_minutes": duration_minutes
        }


class PeriodReportDialog(QDialog):
    """Dialog to specify period and show task summary report."""

    def __init__(self, task_sessions: List[Dict], parent=None):
        super().__init__(parent)
        self.task_sessions = task_sessions
        self.setWindowTitle("期間別タスク集計")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        # Dark theme styling
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QDateEdit, QTimeEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                font-size: 13px;
            }
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 10px;
                font-family: monospace;
                font-size: 13px;
            }
            QPushButton {
                background-color: #4a6fa5;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5a7fb5;
            }
        """)

        self._init_ui()

    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("期間別タスク集計")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        # Form layout for date/time inputs
        form_layout = QFormLayout()

        # Start date and time
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        self.start_date_edit.setDisplayFormat("yyyy/MM/dd")

        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setTime(QTime(0, 0))
        self.start_time_edit.setDisplayFormat("HH:mm")

        start_layout = QHBoxLayout()
        start_layout.addWidget(self.start_date_edit)
        start_layout.addWidget(self.start_time_edit)
        form_layout.addRow("開始日時:", start_layout)

        # End date and time
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setDisplayFormat("yyyy/MM/dd")

        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setTime(QTime(23, 59))
        self.end_time_edit.setDisplayFormat("HH:mm")

        end_layout = QHBoxLayout()
        end_layout.addWidget(self.end_date_edit)
        end_layout.addWidget(self.end_time_edit)
        form_layout.addRow("終了日時:", end_layout)

        layout.addLayout(form_layout)

        # Generate button
        self.generate_btn = QPushButton("集計を実行")
        self.generate_btn.clicked.connect(self._generate_report)
        layout.addWidget(self.generate_btn)

        # Result display
        result_label = QLabel("集計結果:")
        layout.addWidget(result_label)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)

        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _generate_report(self):
        """Generate report for the specified period."""
        # Get start and end datetime
        start_date = self.start_date_edit.date().toPyDate()
        start_time = self.start_time_edit.time().toPyTime()
        start_datetime = datetime.combine(start_date, start_time)

        end_date = self.end_date_edit.date().toPyDate()
        end_time = self.end_time_edit.time().toPyTime()
        end_datetime = datetime.combine(end_date, end_time)

        # Validate dates
        if start_datetime >= end_datetime:
            self.result_text.setPlainText("エラー: 開始日時は終了日時より前である必要があります。")
            return

        # Calculate task totals
        task_totals: Dict[str, int] = {}  # task_name -> total_minutes

        for session in self.task_sessions:
            try:
                # Parse session date and time
                session_date_str = session.get("date", "")
                session_start_str = session.get("start_time", "00:00")
                session_end_str = session.get("end_time", "00:00")

                session_date = datetime.strptime(session_date_str, "%Y-%m-%d").date()
                session_start_time = datetime.strptime(session_start_str, "%H:%M").time()
                session_end_time = datetime.strptime(session_end_str, "%H:%M").time()

                session_start = datetime.combine(session_date, session_start_time)
                session_end = datetime.combine(session_date, session_end_time)

                # Check if session is within the specified period
                if session_start >= start_datetime and session_end <= end_datetime:
                    task_name = session.get("task", "不明")
                    duration = session.get("duration_minutes", 0)

                    if task_name not in task_totals:
                        task_totals[task_name] = 0
                    task_totals[task_name] += duration

            except (ValueError, KeyError):
                continue

        # Format report
        if not task_totals:
            self.result_text.setPlainText("指定された期間にタスクの記録がありません。")
            return

        report_lines = []
        report_lines.append(f"期間: {start_datetime.strftime('%Y/%m/%d %H:%M')} ~ {end_datetime.strftime('%Y/%m/%d %H:%M')}")
        report_lines.append("=" * 60)
        report_lines.append("")

        # Sort by total time (descending)
        sorted_tasks = sorted(task_totals.items(), key=lambda x: x[1], reverse=True)

        total_minutes = 0
        for task_name, minutes in sorted_tasks:
            hours = minutes // 60
            mins = minutes % 60
            total_minutes += minutes

            if hours > 0:
                time_str = f"{hours}時間{mins:02d}分"
            else:
                time_str = f"{mins}分"

            report_lines.append(f"【{task_name}】")
            report_lines.append(f"  合計時間: {time_str} ({minutes}分)")
            report_lines.append("")

        # Add grand total
        report_lines.append("=" * 60)
        total_hours = total_minutes // 60
        total_mins = total_minutes % 60
        report_lines.append(f"総合計: {total_hours}時間{total_mins:02d}分 ({total_minutes}分)")

        self.result_text.setPlainText("\n".join(report_lines))


class TimelineWidget(QWidget):
    """Widget to display tasks in a timeline view (hourly)."""

    # Signals for edit and delete actions
    session_edit_requested = pyqtSignal(dict)
    session_delete_requested = pyqtSignal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.sessions: List[Dict] = []
        self.zoom_level: float = 1.0  # Default zoom level
        self.session_rects: List[Tuple[QRect, Dict]] = []  # Store rectangles for hover detection
        self._update_height()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)  # Enable mouse tracking for tooltips

    def set_sessions(self, sessions: List[Dict]) -> None:
        """Set the sessions to display."""
        self.sessions = sessions
        self.update()

    def set_zoom(self, zoom: float) -> None:
        """Set zoom level (0.5 = 50%, 1.0 = 100%, 2.0 = 200%, etc.)."""
        self.zoom_level = max(0.5, min(zoom, 4.0))  # Limit between 50% and 400%
        self._update_height()
        self.update()

    def _update_height(self) -> None:
        """Update widget height based on zoom level."""
        base_height = 25  # Base height per hour
        hour_height = int(base_height * self.zoom_level)
        total_height = 24 * hour_height
        self.setMinimumHeight(total_height)

    def paintEvent(self, event) -> None:
        """Custom paint event to draw timeline."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Clear previous session rectangles
        self.session_rects.clear()

        # Colors
        bg_color = QColor("#2b2b2b")
        line_color = QColor("#555555")
        text_color = QColor("#ffffff")

        # Draw background
        painter.fillRect(self.rect(), bg_color)

        # Calculate dimensions
        width = self.width()
        height = self.height()
        base_hour_height = 25
        hour_height = int(base_hour_height * self.zoom_level)
        time_label_width = 60

        # Draw hour lines and labels
        painter.setPen(QPen(line_color, 1))
        for hour in range(25):  # 0-24
            y = hour * hour_height
            painter.drawLine(time_label_width, y, width, y)

            # Draw hour label
            painter.setPen(text_color)
            time_str = f"{hour:02d}:00"
            painter.drawText(5, y + 15, time_str)
            painter.setPen(line_color)

        # Draw sessions
        if not self.sessions:
            painter.setPen(text_color)
            painter.drawText(width // 2 - 100, height // 2, "この日のタスク記録はありません")
            return

        # Task colors (cycle through these)
        task_colors = [
            QColor("#4a90e2"), QColor("#e24a4a"), QColor("#4ae24a"),
            QColor("#e2d44a"), QColor("#d44ae2"), QColor("#4ae2d4"),
            QColor("#e2884a"), QColor("#884ae2"), QColor("#4ae288")
        ]

        task_color_map = {}
        color_index = 0

        for session in self.sessions:
            task_name = session["task"]
            start_time = session["start"]
            end_time = session["end"]

            # Assign color to task
            if task_name not in task_color_map:
                task_color_map[task_name] = task_colors[color_index % len(task_colors)]
                color_index += 1

            color = task_color_map[task_name]

            # Calculate position
            start_hour = start_time.hour + start_time.minute / 60.0
            end_hour = end_time.hour + end_time.minute / 60.0

            y1 = int(start_hour * hour_height)
            y2 = int(end_hour * hour_height)

            # Draw session block
            session_rect_x = time_label_width + 10
            session_rect_width = width - time_label_width - 20

            painter.fillRect(session_rect_x, y1, session_rect_width, y2 - y1, color)

            # Draw border
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawRect(session_rect_x, y1, session_rect_width, y2 - y1)

            # Store rectangle for hover detection
            rect = QRect(session_rect_x, y1, session_rect_width, y2 - y1)
            self.session_rects.append((rect, session))

            # Draw text
            painter.setPen(text_color)
            text = f"{task_name}:   {start_time.strftime('%H:%M')} ~ {end_time.strftime('%H:%M')}"
            painter.drawText(session_rect_x + 5, y1 + 20, text)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move event to show tooltips."""
        pos = event.pos()

        # Check if mouse is over any session block
        for rect, session in self.session_rects:
            if rect.contains(pos):
                # Create tooltip text
                task_name = session.get("task", "不明")
                start_time = session.get("start")
                end_time = session.get("end")
                duration = session.get("duration_minutes", 0)

                # Calculate hours and minutes
                hours = duration // 60
                minutes = duration % 60

                # Format tooltip
                if hours > 0:
                    duration_text = f"{hours}時間{minutes}分"
                else:
                    duration_text = f"{minutes}分"

                # Format time strings
                if isinstance(start_time, time):
                    start_str = start_time.strftime('%H:%M')
                    end_str = end_time.strftime('%H:%M')
                else:
                    start_str = str(start_time)
                    end_str = str(end_time)

                tooltip_text = f"<b>{task_name}</b><br>時間: {start_str} ~ {end_str}<br>所要時間: {duration_text}"

                # Show tooltip
                QToolTip.setFont(self.font())
                QToolTip.showText(event.globalPosition().toPoint(), tooltip_text, self)
                return

        # Hide tooltip if not over any session
        QToolTip.hideText()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press event to show context menu."""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()

            # Check if mouse is over any session block
            for rect, session in self.session_rects:
                if rect.contains(pos):
                    # Show context menu
                    self._show_context_menu(event.globalPosition().toPoint(), session)
                    return

        super().mousePressEvent(event)

    def _show_context_menu(self, global_pos, session: Dict) -> None:
        """Show context menu for a session."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
            }
            QMenu::item {
                padding: 8px 30px;
            }
            QMenu::item:selected {
                background-color: #4a6fa5;
            }
        """)

        edit_action = QAction("✏️ 編集", self)
        delete_action = QAction("🗑️ 削除", self)

        edit_action.triggered.connect(lambda: self.session_edit_requested.emit(session))
        delete_action.triggered.connect(lambda: self.session_delete_requested.emit(session))

        menu.addAction(edit_action)
        menu.addAction(delete_action)

        menu.exec(global_pos)


class CalendarWidget(QWidget):
    """Enhanced calendar widget with month/week/day views."""

    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings("CHU1PC", "TaskManagerApp")
        self.current_view = "week"  # month, week, day - default to week
        self.selected_date = QDate.currentDate()

        self._load_data()
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the UI components."""
        main_layout = QVBoxLayout(self)

        # Top bar: View switcher
        top_bar = QHBoxLayout()

        view_label = QLabel("表示:")
        view_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        top_bar.addWidget(view_label)

        self.month_btn = QRadioButton("月")
        self.week_btn = QRadioButton("週")
        self.day_btn = QRadioButton("日")

        for btn in [self.month_btn, self.week_btn, self.day_btn]:
            btn.setStyleSheet("""
                QRadioButton {
                    color: #ffffff;
                    font-size: 18px;
                    padding: 10px 15px;
                    min-width: 60px;
                }
                QRadioButton::indicator {
                    width: 20px;
                    height: 20px;
                }
            """)

        self.week_btn.setChecked(True)  # Default to week view
        self.month_btn.toggled.connect(lambda checked: self._switch_view("month") if checked else None)
        self.week_btn.toggled.connect(lambda checked: self._switch_view("week") if checked else None)
        self.day_btn.toggled.connect(lambda checked: self._switch_view("day") if checked else None)

        top_bar.addWidget(self.month_btn)
        top_bar.addWidget(self.week_btn)
        top_bar.addWidget(self.day_btn)
        top_bar.addStretch()

        # Add session button
        self.add_session_btn = QPushButton("➕ セッション追加")
        self.add_session_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a9e5a;
                color: #ffffff;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5aae6a;
            }
        """)
        self.add_session_btn.clicked.connect(self._add_session)
        top_bar.addWidget(self.add_session_btn)

        # Period report button
        self.report_btn = QPushButton("📊 期間集計")
        self.report_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a6fa5;
                color: #ffffff;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a7fb5;
            }
        """)
        self.report_btn.clicked.connect(self._show_period_report)
        top_bar.addWidget(self.report_btn)

        main_layout.addLayout(top_bar)

        # Content area (will switch between different views)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        main_layout.addWidget(self.content_widget)

        # Initialize views
        self._init_month_view()
        self._init_week_view()
        self._init_day_view()

        # Show week view by default
        self._switch_view("week")

    def _init_month_view(self) -> None:
        """Initialize month view with calendar."""
        self.month_view = QWidget()
        month_layout = QHBoxLayout(self.month_view)

        # Left: Calendar
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        self.calendar = QCalendarWidget()
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QCalendarWidget QToolButton {
                color: #ffffff;
                background-color: #3c3c3c;
                border: none;
                padding: 5px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #4c4c4c;
            }
            QCalendarWidget QMenu {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QCalendarWidget QSpinBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555;
            }
            QCalendarWidget QAbstractItemView {
                background-color: #2b2b2b;
                color: #ffffff;
                selection-background-color: #5c5c5c;
            }
        """)
        self.calendar.clicked.connect(self._on_calendar_date_selected)

        left_layout.addWidget(self.calendar)

        # Right: Task summary for selected date
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.month_date_label = QLabel("日付を選択してください")
        self.month_date_label.setStyleSheet("""
            color: #ffffff;
            background-color: #333;
            border-radius: 5px;
            padding: 10px;
            font-size: 16px;
            font-weight: bold;
        """)
        right_layout.addWidget(self.month_date_label)

        self.month_total_time_label = QLabel("総学習時間: 0分")
        self.month_total_time_label.setStyleSheet("""
            color: #ffffff;
            background-color: #333;
            border-radius: 5px;
            padding: 8px;
            font-size: 14px;
        """)
        right_layout.addWidget(self.month_total_time_label)

        task_list_label = QLabel("タスク別学習時間:")
        task_list_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        right_layout.addWidget(task_list_label)

        self.month_task_list = QListWidget()
        self.month_task_list.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3c3c3c;
            }
            QListWidget::item:selected {
                background-color: #4c4c4c;
            }
            QListWidget::item:hover {
                background-color: #3c3c3c;
            }
        """)
        right_layout.addWidget(self.month_task_list)

        # Button to switch to day view
        self.view_day_btn = QPushButton("この日を詳しく見る")
        self.view_day_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a6fa5;
                color: #fff;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5a7fb5;
            }
        """)
        self.view_day_btn.clicked.connect(lambda: self._switch_view("day"))
        right_layout.addWidget(self.view_day_btn)

        month_layout.addWidget(left_panel, 1)
        month_layout.addWidget(right_panel, 1)

    def _init_week_view(self) -> None:
        """Initialize week view with Google Calendar style timeline."""
        self.week_view = QWidget()
        week_layout = QVBoxLayout(self.week_view)

        # Navigation and zoom controls
        nav_layout = QHBoxLayout()

        self.prev_week_btn = QPushButton("← 前の週")
        self.prev_week_btn.clicked.connect(self._prev_week)

        self.week_label = QLabel()
        self.week_label.setStyleSheet("""
            color: #ffffff;
            font-size: 16px;
            font-weight: bold;
        """)
        self.week_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_week_btn = QPushButton("次の週 →")
        self.next_week_btn.clicked.connect(self._next_week)

        # Zoom controls
        self.week_zoom_out_btn = QPushButton("-")
        self.week_zoom_out_btn.setFixedSize(30, 30)
        self.week_zoom_out_btn.clicked.connect(lambda: self._zoom_week(0.8))

        self.week_zoom_label = QLabel("100%")
        self.week_zoom_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        self.week_zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.week_zoom_label.setFixedWidth(50)

        self.week_zoom_in_btn = QPushButton("+")
        self.week_zoom_in_btn.setFixedSize(30, 30)
        self.week_zoom_in_btn.clicked.connect(lambda: self._zoom_week(1.25))

        for btn in [self.prev_week_btn, self.next_week_btn, self.week_zoom_out_btn, self.week_zoom_in_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3c3c3c;
                    color: #fff;
                    border-radius: 4px;
                    padding: 8px;
                }
                QPushButton:hover {
                    background-color: #4c4c4c;
                }
            """)

        nav_layout.addWidget(self.prev_week_btn)
        nav_layout.addWidget(self.week_label, 1)
        nav_layout.addWidget(self.next_week_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(QLabel("ズーム:", styleSheet="color: #ffffff;"))
        nav_layout.addWidget(self.week_zoom_out_btn)
        nav_layout.addWidget(self.week_zoom_label)
        nav_layout.addWidget(self.week_zoom_in_btn)

        week_layout.addLayout(nav_layout)

        # Week timeline with scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #555;
                background-color: #2b2b2b;
            }
        """)

        self.week_timeline = WeekTimelineWidget()
        self.week_timeline.session_edit_requested.connect(self._edit_session)
        self.week_timeline.session_delete_requested.connect(self._delete_session)
        scroll.setWidget(self.week_timeline)

        week_layout.addWidget(scroll)

    def _init_day_view(self) -> None:
        """Initialize day view with timeline."""
        self.day_view = QWidget()
        day_layout = QVBoxLayout(self.day_view)

        # Navigation and zoom controls
        nav_layout = QHBoxLayout()

        self.prev_day_btn = QPushButton("← 前の日")
        self.prev_day_btn.clicked.connect(self._prev_day)

        self.day_label = QLabel()
        self.day_label.setStyleSheet("""
            color: #ffffff;
            font-size: 18px;
            font-weight: bold;
        """)
        self.day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_day_btn = QPushButton("次の日 →")
        self.next_day_btn.clicked.connect(self._next_day)

        # Zoom controls
        self.day_zoom_out_btn = QPushButton("-")
        self.day_zoom_out_btn.setFixedSize(30, 30)
        self.day_zoom_out_btn.clicked.connect(lambda: self._zoom_day(0.8))

        self.day_zoom_label = QLabel("100%")
        self.day_zoom_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        self.day_zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.day_zoom_label.setFixedWidth(50)

        self.day_zoom_in_btn = QPushButton("+")
        self.day_zoom_in_btn.setFixedSize(30, 30)
        self.day_zoom_in_btn.clicked.connect(lambda: self._zoom_day(1.25))

        for btn in [self.prev_day_btn, self.next_day_btn, self.day_zoom_out_btn, self.day_zoom_in_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3c3c3c;
                    color: #fff;
                    border-radius: 4px;
                    padding: 8px;
                }
                QPushButton:hover {
                    background-color: #4c4c4c;
                }
            """)

        nav_layout.addWidget(self.prev_day_btn)
        nav_layout.addWidget(self.day_label, 1)
        nav_layout.addWidget(self.next_day_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(QLabel("ズーム:", styleSheet="color: #ffffff;"))
        nav_layout.addWidget(self.day_zoom_out_btn)
        nav_layout.addWidget(self.day_zoom_label)
        nav_layout.addWidget(self.day_zoom_in_btn)

        day_layout.addLayout(nav_layout)

        # Timeline scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #555;
                background-color: #2b2b2b;
            }
        """)

        self.timeline = TimelineWidget()
        self.timeline.session_edit_requested.connect(self._edit_session)
        self.timeline.session_delete_requested.connect(self._delete_session)
        scroll.setWidget(self.timeline)

        day_layout.addWidget(scroll)

    def _switch_view(self, view: str) -> None:
        """Switch between month/week/day views."""
        self.current_view = view

        # Clear content layout
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        # Add appropriate view
        if view == "month":
            self.content_layout.addWidget(self.month_view)
            self._highlight_dates_with_tasks()
        elif view == "week":
            self.content_layout.addWidget(self.week_view)
            self._update_week_view()
        elif view == "day":
            self.content_layout.addWidget(self.day_view)
            self._update_day_view()

    def _load_data(self) -> None:
        """Load task study time data from settings."""
        self.task_study_time: Dict[str, Dict[str, int]] = self.settings.value(
            "task_study_time", {}
        )
        self.study_time: Dict[str, int] = self.settings.value("study_time", {})

        # Load session data (with timestamps)
        self.task_sessions: List[Dict] = self.settings.value("task_sessions", [])

    def _highlight_dates_with_tasks(self) -> None:
        """Highlight dates that have task records."""
        format_with_tasks = QTextCharFormat()
        format_with_tasks.setBackground(QColor("#4a6fa5"))

        dates_with_tasks = set()
        for task_name, date_dict in self.task_study_time.items():
            for date_str in date_dict.keys():
                dates_with_tasks.add(date_str)

        for date_str in dates_with_tasks:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                qdate = QDate(dt.year, dt.month, dt.day)
                self.calendar.setDateTextFormat(qdate, format_with_tasks)
            except ValueError:
                continue

    def _on_calendar_date_selected(self, qdate: QDate) -> None:
        """Handle date selection in calendar."""
        self.selected_date = qdate
        selected_date = qdate.toString("yyyy-MM-dd")

        self.month_date_label.setText(f"選択された日付: {selected_date}")

        total_minutes = self.study_time.get(selected_date, 0)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        self.month_total_time_label.setText(f"総学習時間: {hours}時間{minutes:02d}分")

        self.month_task_list.clear()

        for task_name, date_dict in self.task_study_time.items():
            if selected_date in date_dict:
                task_minutes = date_dict[selected_date]
                task_hours = task_minutes // 60
                task_mins = task_minutes % 60

                item_text = f"{task_name}: {task_hours}時間{task_mins:02d}分"
                item = QListWidgetItem(item_text)
                self.month_task_list.addItem(item)

        if self.month_task_list.count() == 0:
            item = QListWidgetItem("この日の記録はありません")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.month_task_list.addItem(item)

    def _update_week_view(self) -> None:
        """Update week view with Google Calendar style timeline."""
        # Get week start (Monday)
        selected_py_date = self.selected_date.toPyDate()
        week_start = selected_py_date - timedelta(days=selected_py_date.weekday())
        week_end = week_start + timedelta(days=6)

        self.week_label.setText(
            f"{week_start.strftime('%Y年%m月%d日')} - {week_end.strftime('%Y年%m月%d日')}"
        )

        # Set week start date for timeline widget
        self.week_timeline.set_week_start(week_start)

        # Pass all sessions to the timeline widget
        self.week_timeline.set_sessions(self.task_sessions)

    def _update_day_view(self) -> None:
        """Update day view with timeline."""
        selected_py_date = self.selected_date.toPyDate()
        date_str = selected_py_date.isoformat()

        self.day_label.setText(
            f"{selected_py_date.strftime('%Y年%m月%d日 (%A)')}"
        )

        # Get sessions for this day (including sessions that span into or from this day)
        day_sessions = []
        for s in self.task_sessions:
            start_date_str = s.get("date", "")
            end_date_str = s.get("end_date", start_date_str)

            # Include if this day is the start date or end date
            if start_date_str == date_str or end_date_str == date_str:
                day_sessions.append(s)

        # Convert string times to datetime objects
        converted_sessions = []
        for session in day_sessions:
            try:
                start_date_str = session.get("date", "")
                end_date_str = session.get("end_date", start_date_str)
                start_str = session.get("start_time", "00:00")
                end_str = session.get("end_time", "00:00")

                # If session spans multiple days, split it
                if start_date_str != end_date_str:
                    if start_date_str == date_str:
                        # This is the start day - show from start time to 24:00
                        start_time = datetime.strptime(start_str, "%H:%M").time()
                        # Use 23:59:59 to represent end of day
                        end_time = datetime.strptime("23:59", "%H:%M").time()

                        converted_sessions.append({
                            "task": session.get("task", "不明") + " →",
                            "start": start_time,
                            "end": end_time,
                            "duration_minutes": session.get("duration_minutes", 0),
                            "is_split_start": True
                        })
                    elif end_date_str == date_str:
                        # This is the end day - show from 00:00 to end time
                        start_time = datetime.strptime("00:00", "%H:%M").time()
                        end_time = datetime.strptime(end_str, "%H:%M").time()

                        converted_sessions.append({
                            "task": "← " + session.get("task", "不明"),
                            "start": start_time,
                            "end": end_time,
                            "duration_minutes": session.get("duration_minutes", 0),
                            "is_split_end": True
                        })
                else:
                    # Normal single-day session
                    start_time = datetime.strptime(start_str, "%H:%M").time()
                    end_time = datetime.strptime(end_str, "%H:%M").time()

                    converted_sessions.append({
                        "task": session.get("task", "不明"),
                        "start": start_time,
                        "end": end_time,
                        "duration_minutes": session.get("duration_minutes", 0)
                    })
            except (ValueError, KeyError):
                continue

        self.timeline.set_sessions(converted_sessions)

    def _prev_week(self) -> None:
        """Navigate to previous week."""
        self.selected_date = self.selected_date.addDays(-7)
        self._update_week_view()

    def _next_week(self) -> None:
        """Navigate to next week."""
        self.selected_date = self.selected_date.addDays(7)
        self._update_week_view()

    def _prev_day(self) -> None:
        """Navigate to previous day."""
        self.selected_date = self.selected_date.addDays(-1)
        self._update_day_view()

    def _next_day(self) -> None:
        """Navigate to next day."""
        self.selected_date = self.selected_date.addDays(1)
        self._update_day_view()

    def _zoom_week(self, factor: float) -> None:
        """Zoom in or out on week view."""
        current_zoom = self.week_timeline.zoom_level
        new_zoom = current_zoom * factor
        self.week_timeline.set_zoom(new_zoom)
        self.week_zoom_label.setText(f"{int(new_zoom * 100)}%")

    def _zoom_day(self, factor: float) -> None:
        """Zoom in or out on day view."""
        current_zoom = self.timeline.zoom_level
        new_zoom = current_zoom * factor
        self.timeline.set_zoom(new_zoom)
        self.day_zoom_label.setText(f"{int(new_zoom * 100)}%")

    def _show_period_report(self) -> None:
        """Show period report dialog."""
        dialog = PeriodReportDialog(self.task_sessions, self)
        dialog.exec()

    def _add_session(self) -> None:
        """Show add session dialog and save the session."""
        dialog = AddSessionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get session data
            session_data = dialog.get_session_data()

            # Save session to settings
            task_sessions = self.settings.value("task_sessions", [])
            task_sessions.append(session_data)
            self.settings.setValue("task_sessions", task_sessions)

            # Update task-specific study time
            task_name = session_data["task"]
            start_date_str = session_data["date"]
            end_date_str = session_data.get("end_date", start_date_str)
            duration = session_data["duration_minutes"]

            # If the session spans multiple days, distribute the time across those days
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            study_records = self.settings.value("study_time", {})
            task_study_records = self.settings.value("task_study_time", {})

            if start_date == end_date:
                # Single day session - record all time on that day
                if start_date_str not in study_records:
                    study_records[start_date_str] = 0
                study_records[start_date_str] += duration

                if task_name not in task_study_records:
                    task_study_records[task_name] = {}
                if start_date_str not in task_study_records[task_name]:
                    task_study_records[task_name][start_date_str] = 0
                task_study_records[task_name][start_date_str] += duration
            else:
                # Multi-day session - record time on the start date for now
                # (You could also split the time proportionally across days if needed)
                if start_date_str not in study_records:
                    study_records[start_date_str] = 0
                study_records[start_date_str] += duration

                if task_name not in task_study_records:
                    task_study_records[task_name] = {}
                if start_date_str not in task_study_records[task_name]:
                    task_study_records[task_name][start_date_str] = 0
                task_study_records[task_name][start_date_str] += duration

            self.settings.setValue("study_time", study_records)
            self.settings.setValue("task_study_time", task_study_records)

            # Reload data and refresh view
            self._load_data()
            if self.current_view == "month":
                self._highlight_dates_with_tasks()
            elif self.current_view == "week":
                self._update_week_view()
            elif self.current_view == "day":
                self._update_day_view()

            # Show success message
            QMessageBox.information(self, "成功", "セッションを追加しました。")

    def _edit_session(self, session: Dict) -> None:
        """Edit an existing session."""
        dialog = AddSessionDialog(self, session_data=session)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get new session data
            new_session_data = dialog.get_session_data()

            # Find and update the session
            task_sessions = self.settings.value("task_sessions", [])

            # Find the original session by matching all fields
            for i, s in enumerate(task_sessions):
                if (s.get("task") == session.get("task") and
                    s.get("date") == session.get("date") and
                    s.get("start_time") == session.get("start_time") and
                    s.get("end_time") == session.get("end_time")):

                    # Calculate old duration to subtract
                    old_duration = s.get("duration_minutes", 0)
                    old_task = s.get("task")
                    old_date = s.get("date")

                    # Update session
                    task_sessions[i] = new_session_data

                    # Update study time records
                    new_task = new_session_data["task"]
                    new_date = new_session_data["date"]
                    new_duration = new_session_data["duration_minutes"]

                    # Remove old duration from old task/date
                    study_records = self.settings.value("study_time", {})
                    if old_date in study_records:
                        study_records[old_date] -= old_duration
                        if study_records[old_date] <= 0:
                            del study_records[old_date]

                    task_study_records = self.settings.value("task_study_time", {})
                    if old_task in task_study_records and old_date in task_study_records[old_task]:
                        task_study_records[old_task][old_date] -= old_duration
                        if task_study_records[old_task][old_date] <= 0:
                            del task_study_records[old_task][old_date]

                    # Add new duration to new task/date
                    if new_date not in study_records:
                        study_records[new_date] = 0
                    study_records[new_date] += new_duration

                    if new_task not in task_study_records:
                        task_study_records[new_task] = {}
                    if new_date not in task_study_records[new_task]:
                        task_study_records[new_task][new_date] = 0
                    task_study_records[new_task][new_date] += new_duration

                    # Save updated records
                    self.settings.setValue("task_sessions", task_sessions)
                    self.settings.setValue("study_time", study_records)
                    self.settings.setValue("task_study_time", task_study_records)

                    break

            # Reload data and refresh view
            self._load_data()
            if self.current_view == "week":
                self._update_week_view()
            elif self.current_view == "day":
                self._update_day_view()
            elif self.current_view == "month":
                self._highlight_dates_with_tasks()

            QMessageBox.information(self, "成功", "セッションを更新しました。")

    def _delete_session(self, session: Dict) -> None:
        """Delete a session."""
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "削除の確認",
            f"このセッションを削除しますか？\n\nタスク: {session.get('task')}\n時間: {session.get('start_time')} ~ {session.get('end_time')}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Find and remove the session
        task_sessions = self.settings.value("task_sessions", [])

        for i, s in enumerate(task_sessions):
            if (s.get("task") == session.get("task") and
                s.get("date") == session.get("date") and
                s.get("start_time") == session.get("start_time") and
                s.get("end_time") == session.get("end_time")):

                # Get session info
                task_name = s.get("task")
                date_str = s.get("date")
                duration = s.get("duration_minutes", 0)

                # Remove session
                task_sessions.pop(i)

                # Update study time records
                study_records = self.settings.value("study_time", {})
                if date_str in study_records:
                    study_records[date_str] -= duration
                    if study_records[date_str] <= 0:
                        del study_records[date_str]

                task_study_records = self.settings.value("task_study_time", {})
                if task_name in task_study_records and date_str in task_study_records[task_name]:
                    task_study_records[task_name][date_str] -= duration
                    if task_study_records[task_name][date_str] <= 0:
                        del task_study_records[task_name][date_str]

                # Save updated records
                self.settings.setValue("task_sessions", task_sessions)
                self.settings.setValue("study_time", study_records)
                self.settings.setValue("task_study_time", task_study_records)

                break

        # Reload data and refresh view
        self._load_data()
        if self.current_view == "week":
            self._update_week_view()
        elif self.current_view == "day":
            self._update_day_view()
        elif self.current_view == "month":
            self._highlight_dates_with_tasks()

        QMessageBox.information(self, "成功", "セッションを削除しました。")
