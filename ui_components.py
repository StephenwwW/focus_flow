from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QFrame, QHBoxLayout, QMessageBox, 
                             QDialog, QDialogButtonBox, QCalendarWidget, QTimeEdit,
                             QGraphicsOpacityEffect, QApplication)
from PyQt6.QtCore import Qt, QTimer, QTime, QDate, QPropertyAnimation, QEasingCurve, QRectF
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QBrush, QPen, QPainterPath

MAX_TASKS_PER_DAY = 20

# --- 特效提示視窗 ---
class NotificationWidget(QWidget):
    def __init__(self, title, message, notification_type='info', parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.bg_frame = QFrame(self)
        self.bg_frame.setStyleSheet("QFrame { background-color: rgba(20, 20, 30, 0.95); border-radius: 15px; border: 1px solid #bd93f9; }")
        
        frame_layout = QHBoxLayout(self.bg_frame)
        frame_layout.setSpacing(15)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(48, 48)
        frame_layout.addWidget(self.icon_label)
        self.create_icon(notification_type)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.title_label.setStyleSheet("color: #bd93f9; font-size: 18px; font-weight: bold;")
        
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.message_label.setStyleSheet("color: white; font-size: 14px;")
        self.message_label.setWordWrap(True)
        
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.message_label)
        text_layout.addStretch()
        
        frame_layout.addLayout(text_layout)
        self.layout.addWidget(self.bg_frame)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(500)
        
        QTimer.singleShot(30000, self.hide_animation)

    def create_icon(self, icon_type):
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if icon_type == 'work':
            painter.setPen(QPen(QColor("#50fa7b"), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            path = QPainterPath()
            path.moveTo(10, 38); path.quadTo(24, 42, 38, 38); path.lineTo(38, 10)
            path.quadTo(24, 14, 10, 10); path.lineTo(10, 38)
            painter.drawPath(path)
            painter.drawLine(24, 12, 24, 39)
        elif icon_type == 'break':
            painter.setPen(QPen(QColor("#8be9fd"), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(8, 12, 28, 24)
            painter.drawArc(36, 18, 8, 12, -90 * 16, 180 * 16)
            painter.drawLine(14, 8, 16, 12); painter.drawLine(22, 8, 24, 12); painter.drawLine(30, 8, 32, 12)
        elif icon_type == 'done':
            painter.setPen(QPen(QColor("#50fa7b"), 4, cap=Qt.PenCapStyle.RoundCap, join=Qt.PenJoinStyle.RoundJoin))
            painter.drawLine(10, 24, 22, 36); painter.drawLine(22, 36, 38, 12)
        else:
            painter.setPen(QPen(QColor("#f1fa8c"), 3))
            painter.drawEllipse(8, 8, 32, 32)
            painter.setFont(QFont("Arial", 18, QFont.Weight.Bold))
            painter.drawText(QRectF(8, 8, 32, 32), Qt.AlignmentFlag.AlignCenter, "i")

        painter.end()
        self.icon_label.setPixmap(pixmap)

    def show_animation(self):
        self.opacity_effect.setOpacity(0)
        self.show()
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        self.move(screen_geometry.right() - self.width() - 20, screen_geometry.bottom() - self.height() - 20)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.start()

    def hide_animation(self):
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.finished.connect(self.close)
        self.animation.start()

# --- 自訂日期/時間選擇按鈕 ---
class DatePickerButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setObjectName("DateTimeButton")
        self.date = QDate.currentDate()
        self.setText(self.date.toString("yyyy-MM-dd"))
        self.clicked.connect(self.pick_date)

    def pick_date(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(self.parent_window.get_text('select_date_title'))
        layout = QVBoxLayout(dialog)
        calendar = QCalendarWidget(dialog)
        calendar.setSelectedDate(self.date)
        calendar.setMinimumDate(QDate.currentDate())
        calendar.setMaximumDate(QDate(2035, 12, 31))
        layout.addWidget(calendar)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec():
            new_date = calendar.selectedDate()
            if self.date != new_date:
                self.setDate(new_date)
                self.parent_window.date_selection_changed(self.date)

    def setDate(self, date):
        self.date = date
        self.setText(self.date.toString("yyyy-MM-dd"))

class TimePickerButton(QPushButton):
    def __init__(self, initial_time_str="09:00", parent=None):
        super().__init__(parent)
        self.task_row_widget = parent
        self.parent_window = self.task_row_widget.parent_day_widget.parent_window
        self.setObjectName("DateTimeButton")
        self.time = QTime.fromString(initial_time_str, "HH:mm")
        self.setText(self.time.toString("HH:mm"))
        self.clicked.connect(self.pick_time)

    def pick_time(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(self.parent_window.get_text('select_time_title'))
        layout = QVBoxLayout(dialog)
        time_edit = QTimeEdit(dialog)
        time_edit.setDisplayFormat("HH:mm")
        time_edit.setTime(self.time)
        layout.addWidget(time_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec():
            new_time = time_edit.time()

            # --- 新增：時間驗證邏輯 ---
            is_today = self.task_row_widget.parent_day_widget.date == QDate.currentDate()
            is_first_task = self.task_row_widget == self.task_row_widget.parent_day_widget.task_widgets[0]

            if is_today and is_first_task and new_time <= QTime.currentTime():
                # 建立一個自訂樣式的 QMessageBox
                msg_box = QMessageBox(self.parent_window)
                msg_box.setWindowTitle(self.parent_window.get_text('invalid_time_title'))
                msg_box.setText(self.parent_window.get_text('invalid_time_msg'))
                msg_box.setIcon(QMessageBox.Icon.Warning)
                # --- 核心修改：設定淺色背景與黑色文字 ---
                msg_box.setStyleSheet("""
                    QMessageBox {
                        background-color: #f0f0f0; /* 淺灰色背景 */
                    }
                    QLabel {
                        color: black; /* 黑色文字 */
                        font-size: 14px;
                    }
                    QPushButton {
                        background-color: #c0c0c0;
                        color: black;
                        border-radius: 5px;
                        padding: 8px 12px;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #d0d0d0;
                    }
                """)
                
                msg_box.exec()
                return # 不更新時間，直接返回


            if self.time != new_time:
                self.setTime(new_time)
                self.parent_window.schedule_changed()

    def setTime(self, time):
        self.time = time
        self.setText(self.time.toString("HH:mm"))
        
# --- 單一任務列 Widget ---
class TaskRowWidget(QWidget):
    def __init__(self, task_text="", task_time_str="09:00", parent=None):
        super().__init__(parent)
        self.parent_day_widget = parent
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.task_input = QLineEdit(task_text)
        self.task_input.setPlaceholderText(self.parent_day_widget.parent_window.get_text('task_placeholder'))
        self.task_input.textChanged.connect(self.parent_day_widget.parent_window.schedule_changed)
        self.time_picker = TimePickerButton(task_time_str, self)
        self.remove_button = QPushButton("✕")
        self.remove_button.setObjectName("RemoveButton")
        self.remove_button.clicked.connect(self.remove_self)
        layout.addWidget(self.task_input)
        layout.addWidget(self.time_picker)
        layout.addWidget(self.remove_button)

    def remove_self(self):
        self.parent_day_widget.remove_task_widget(self)

    def get_data(self):
        return {"name": self.task_input.text(), "time": self.time_picker.time.toString("HH:mm")}

# --- 單日排程 Widget ---
class DayScheduleWidget(QFrame):
    def __init__(self, date, parent_window):
        super().__init__()
        self.date = date
        self.parent_window = parent_window
        self.task_widgets = []
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(8)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        header_layout = QHBoxLayout()
        self.date_label = QLabel(self.date.toString("yyyy-MM-dd (ddd)"))
        self.date_label.setObjectName("DateHeaderLabel")
        header_layout.addWidget(self.date_label)
        header_layout.addStretch()
        self.add_button = QPushButton("+")
        self.add_button.setObjectName("AddButton")
        header_layout.addWidget(self.add_button)
        self.main_layout.addLayout(header_layout)
        self.tasks_layout = QVBoxLayout()
        self.tasks_layout.setSpacing(5)
        self.main_layout.addLayout(self.tasks_layout)
        self.main_layout.addStretch()
        
        self.add_button.clicked.connect(self.add_task_row)
        self.retranslate_ui()

    def retranslate_ui(self):
        self.add_button.setToolTip(self.parent_window.get_text('add_task_tooltip').format(self.date.toString('MM/dd')))
        for widget in self.task_widgets:
            widget.task_input.setPlaceholderText(self.parent_window.get_text('task_placeholder'))

    def add_task_row(self, task_data=None):
        if len(self.task_widgets) >= MAX_TASKS_PER_DAY:
            QMessageBox.information(self.parent_window, "提示", self.parent_window.get_text('max_tasks_reached'))
            return
        task_text = task_data['name'] if task_data else ""
        if self.task_widgets:
            last_time = self.task_widgets[-1].time_picker.time
            new_time = last_time.addSecs(30 * 60)
            task_time = new_time.toString("HH:mm")
        else:
            task_time = task_data['time'] if task_data else "09:00"
        task_widget = TaskRowWidget(task_text, task_time, self)
        self.tasks_layout.addWidget(task_widget)
        self.task_widgets.append(task_widget)
        self.parent_window.schedule_changed()

    def remove_task_widget(self, task_widget):
        if task_widget in self.task_widgets:
            self.task_widgets.remove(task_widget)
            self.tasks_layout.removeWidget(task_widget)
            task_widget.deleteLater()
            self.parent_window.schedule_changed()

    def get_day_data(self):
        tasks = [w.get_data() for w in self.task_widgets if w.get_data()['name'].strip()]
        if not tasks: return None
        tasks.sort(key=lambda x: QTime.fromString(x['time'], "HH:mm"))
        return {"tasks": tasks}

    def load_day_data(self, day_data):
        for task in day_data.get("tasks", []):
            self.add_task_row(task)
