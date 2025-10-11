"""Week timeline widget similar to Google Calendar week view."""
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime, timedelta

from PyQt6.QtWidgets import QWidget, QToolTip, QMenu
from PyQt6.QtCore import Qt, QDate, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QMouseEvent, QAction


class WeekTimelineWidget(QWidget):
    """Widget to display week view with timeline similar to Google Calendar."""

    # Signals for edit and delete actions
    session_edit_requested = pyqtSignal(dict)
    session_delete_requested = pyqtSignal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.week_start_date: datetime.date = datetime.now().date()
        self.sessions_by_date: Dict[str, List[Dict]] = {}
        self.zoom_level: float = 1.0  # Default zoom level (50px per hour)
        self.session_rects: List[Tuple[QRect, Dict]] = []  # Store rectangles for hover detection
        self._update_height()
        self.setMouseTracking(True)  # Enable mouse tracking for tooltips

    def set_week_start(self, start_date: datetime.date) -> None:
        """Set the start date of the week (should be Monday)."""
        # Ensure it's Monday
        weekday = start_date.weekday()
        self.week_start_date = start_date - timedelta(days=weekday)
        self.update()

    def set_sessions(self, sessions: List[Dict]) -> None:
        """Set sessions grouped by date."""
        # Group sessions by date
        self.sessions_by_date = {}
        for session in sessions:
            start_date_str = session.get("date", "")
            end_date_str = session.get("end_date", start_date_str)

            # If session spans multiple days, split it
            if start_date_str != end_date_str:
                # Add first part (start day to 24:00)
                if start_date_str not in self.sessions_by_date:
                    self.sessions_by_date[start_date_str] = []
                first_part = session.copy()
                first_part["end_time"] = "24:00"
                first_part["is_split_start"] = True
                self.sessions_by_date[start_date_str].append(first_part)

                # Add second part (0:00 to end time on end day)
                if end_date_str not in self.sessions_by_date:
                    self.sessions_by_date[end_date_str] = []
                second_part = session.copy()
                second_part["start_time"] = "00:00"
                second_part["date"] = end_date_str
                second_part["is_split_end"] = True
                self.sessions_by_date[end_date_str].append(second_part)
            else:
                # Normal single-day session
                if start_date_str not in self.sessions_by_date:
                    self.sessions_by_date[start_date_str] = []
                self.sessions_by_date[start_date_str].append(session)
        self.update()

    def set_zoom(self, zoom: float) -> None:
        """Set zoom level (0.5 = 50%, 1.0 = 100%, 2.0 = 200%, etc.)."""
        self.zoom_level = max(0.5, min(zoom, 4.0))  # Limit between 50% and 400%
        self._update_height()
        self.update()

    def _update_height(self) -> None:
        """Update widget height based on zoom level."""
        base_hour_height = 50
        header_height = 60
        hour_height = int(base_hour_height * self.zoom_level)
        total_height = header_height + (24 * hour_height)
        self.setMinimumHeight(total_height)

    def paintEvent(self, event) -> None:
        """Custom paint event to draw week timeline."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Clear previous session rectangles
        self.session_rects.clear()

        width = self.width()
        height = self.height()

        # Colors
        bg_color = QColor("#2b2b2b")
        grid_color = QColor("#3c3c3c")
        text_color = QColor("#ffffff")
        header_bg = QColor("#333333")

        # Draw background
        painter.fillRect(0, 0, width, height, bg_color)

        # Layout dimensions
        header_height = 60
        time_column_width = 60
        day_column_width = (width - time_column_width) // 7
        hour_height = int(50 * self.zoom_level)  # pixels per hour with zoom

        # Draw header with day names and dates
        painter.fillRect(0, 0, width, header_height, header_bg)

        day_names = ["月", "火", "水", "木", "金", "土", "日"]
        painter.setPen(text_color)
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)

        for i in range(7):
            current_date = self.week_start_date + timedelta(days=i)
            x = time_column_width + i * day_column_width

            # Day name
            painter.drawText(
                x, 15, day_column_width, 20,
                Qt.AlignmentFlag.AlignCenter,
                day_names[i]
            )

            # Date
            date_font = QFont()
            date_font.setPointSize(14)
            date_font.setBold(True)
            painter.setFont(date_font)
            painter.drawText(
                x, 35, day_column_width, 25,
                Qt.AlignmentFlag.AlignCenter,
                str(current_date.day)
            )
            painter.setFont(font)

        # Draw vertical grid lines (day separators)
        painter.setPen(QPen(grid_color, 1))
        for i in range(8):
            x = time_column_width + i * day_column_width
            painter.drawLine(x, header_height, x, height)

        # Draw horizontal grid lines (hour separators) and time labels
        painter.setPen(QPen(grid_color, 1))
        for hour in range(25):  # 0-24
            y = header_height + hour * hour_height

            # Draw hour line
            painter.drawLine(time_column_width, y, width, y)

            # Draw time label
            if hour < 24:
                painter.setPen(text_color)
                time_str = f"{hour:02d}:00"
                painter.drawText(5, y + 15, time_column_width - 10, 20, Qt.AlignmentFlag.AlignLeft, time_str)
                painter.setPen(QPen(grid_color, 1))

        # Draw task blocks
        task_colors = [
            QColor("#4a90e2"), QColor("#e24a4a"), QColor("#4ae24a"),
            QColor("#e2d44a"), QColor("#d44ae2"), QColor("#4ae2d4"),
            QColor("#e2884a"), QColor("#884ae2"), QColor("#4ae288")
        ]

        task_color_map = {}
        color_index = 0

        for i in range(7):
            current_date = self.week_start_date + timedelta(days=i)
            date_str = current_date.isoformat()

            if date_str not in self.sessions_by_date:
                continue

            day_sessions = self.sessions_by_date[date_str]
            x_base = time_column_width + i * day_column_width

            for session in day_sessions:
                try:
                    task_name = session.get("task", "不明")
                    start_str = session.get("start_time", "00:00")
                    end_str = session.get("end_time", "00:00")

                    # Handle 24:00 as end of day
                    if end_str == "24:00":
                        end_hour_value = 24.0
                    else:
                        end_time = datetime.strptime(end_str, "%H:%M").time()
                        end_hour_value = end_time.hour + end_time.minute / 60.0

                    start_time = datetime.strptime(start_str, "%H:%M").time()
                    start_hour_value = start_time.hour + start_time.minute / 60.0

                    # Assign color to task
                    if task_name not in task_color_map:
                        task_color_map[task_name] = task_colors[color_index % len(task_colors)]
                        color_index += 1

                    color = task_color_map[task_name]

                    # Calculate position
                    y1 = header_height + int(start_hour_value * hour_height)
                    y2 = header_height + int(end_hour_value * hour_height)
                    block_height = y2 - y1

                    if block_height < 5:  # Minimum height
                        block_height = 5

                    # Draw task block
                    padding = 4
                    block_x = x_base + padding
                    block_width = day_column_width - 2 * padding

                    # Fill block
                    painter.fillRect(block_x, y1, block_width, block_height, color)

                    # Draw border
                    painter.setPen(QPen(QColor("#ffffff"), 1))
                    painter.drawRect(block_x, y1, block_width, block_height)

                    # Store rectangle for hover detection
                    rect = QRect(block_x, y1, block_width, block_height)
                    self.session_rects.append((rect, session))

                    # Draw task name (if space available)
                    if block_height > 20:
                        painter.setPen(QColor("#ffffff"))
                        task_font = QFont()
                        task_font.setPointSize(9)
                        painter.setFont(task_font)

                        # Truncate task name if too long
                        display_name = task_name if len(task_name) <= 12 else task_name[:10] + "..."

                        # Add continuation indicators for split sessions
                        if session.get("is_split_start"):
                            display_name += " →"
                        elif session.get("is_split_end"):
                            display_name = "← " + display_name

                        painter.drawText(
                            block_x + 5, y1 + 5,
                            block_width - 10, 15,
                            Qt.AlignmentFlag.AlignLeft,
                            display_name
                        )

                        # Draw time if more space
                        if block_height > 35:
                            time_text = f"{start_str} ~ {end_str}"
                            time_font = QFont()
                            time_font.setPointSize(8)
                            painter.setFont(time_font)
                            painter.drawText(
                                block_x + 5, y1 + 20,
                                block_width - 10, 12,
                                Qt.AlignmentFlag.AlignLeft,
                                time_text
                            )

                except (ValueError, KeyError):
                    continue

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move event to show tooltips."""
        pos = event.pos()

        # Check if mouse is over any session block
        for rect, session in self.session_rects:
            if rect.contains(pos):
                # Create tooltip text
                task_name = session.get("task", "不明")
                start_time = session.get("start_time", "00:00")
                end_time = session.get("end_time", "00:00")
                duration = session.get("duration_minutes", 0)

                # Calculate hours and minutes
                hours = duration // 60
                minutes = duration % 60

                # Format tooltip
                if hours > 0:
                    duration_text = f"{hours}時間{minutes}分"
                else:
                    duration_text = f"{minutes}分"

                tooltip_text = f"<b>{task_name}</b><br>時間: {start_time} ~ {end_time}<br>所要時間: {duration_text}"

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
