import sys
import json
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QSystemTrayIcon, QMenu,
                             QScrollArea, QFrame, QHBoxLayout, QComboBox,
                             QGraphicsOpacityEffect, QMessageBox, QDateEdit, QTimeEdit,
                             QDialog, QDialogButtonBox, QCalendarWidget)
from PyQt6.QtCore import (Qt, QTimer, QTime, QDate, QPoint, QPropertyAnimation, 
                          QEasingCurve, QRect, QRectF)
from PyQt6.QtGui import QIcon, QAction, QColor, QFont, QPixmap, QPainter, QBrush, QPainterPath, QPen

# --- 應用程式設定 ---
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(APP_DIR, "pomodoro_schedule.json")
MAX_TASKS_PER_DAY = 20

# --- 多國語言翻譯 ---
TRANSLATIONS = {
    'zh_TW': {
        'window_title': "FocusFlow - 番茄鐘與排程助理",
        'tray_tooltip': "FocusFlow 番茄鐘助理",
        'show': "顯示",
        'quit': "結束",
        'select_start_date': "選擇開始日期:",
        'mode': "模式:",
        'work_rest_format': "工作 {0} 分鐘 / 休息 {1} 分鐘",
        'mode_tooltip': "選擇 工作/休息 分鐘數",
        'start_button_today': "預覽並啟動今日番茄鐘",
        'start_button_other_day': "只能啟動包含今日的排程",
        'add_task_tooltip': "為 {0} 新增任務",
        'task_placeholder': "請輸入任務...",
        'max_tasks_reached': "每日任務數量已達上限 (20)。",
        'no_tasks_today': "請先為今天新增至少一個任務！",
        'preview_title': "排程預覽與確認",
        'preview_header': "<b>番茄鐘真實執行排程:</b><br>",
        'preview_no_tasks': "今日無任務",
        'preview_focus': "專注 - {0}",
        'preview_break': "休息時間",
        'preview_break_next': "休息時間 (下個任務: {0})",
        'preview_gap': "空檔時間",
        'preview_start_button': "啟動",
        'preview_cancel_button': "取消",
        'timer_status_work': "專注工作中...",
        'timer_status_break': "休息時間",
        'timer_status_stopped': "已停止",
        'timer_status_waiting': "等待開始",
        'timer_status_gap': "空檔時間",
        'timer_task_next': "即將開始: {0}",
        'timer_task_next_soon': "下一個排程即將開始...",
        'timer_task_done': "所有排程已結束",
        'notification_title_work': "專注時間",
        'notification_title_break': "休息一下",
        'notification_done': "任務完成",
        'notification_done_msg': "恭喜！已完成今日所有排程。",
        'minimized_msg': "程式已縮小至系統匣，仍在背景執行。",
        'select_date_title': "選擇日期",
        'select_time_title': "選擇時間",
        'save_error': "儲存錯誤",
        'save_error_msg': "無法儲存排程檔案:\n{0}",
        'load_error': "讀取錯誤",
        'load_error_msg': "無法讀取排程檔案，將建立新檔案。\n錯誤: {0}",
    },
    'en': {
        'window_title': "FocusFlow - Pomodoro & Schedule Assistant",
        'tray_tooltip': "FocusFlow Pomodoro Assistant",
        'show': "Show",
        'quit': "Quit",
        'select_start_date': "Select Start Date:",
        'mode': "Mode:",
        'work_rest_format': "Work {0} min / Break {1} min",
        'mode_tooltip': "Select Work/Break minutes",
        'start_button_today': "Preview & Start Today's Pomodoro",
        'start_button_other_day': "Can only start if today is included",
        'add_task_tooltip': "Add task for {0}",
        'task_placeholder': "Enter a task...",
        'max_tasks_reached': "Maximum tasks per day (20) reached.",
        'no_tasks_today': "Please add at least one task for today!",
        'preview_title': "Schedule Preview & Confirmation",
        'preview_header': "<b>Pomodoro Actual Schedule:</b><br>",
        'preview_no_tasks': "No tasks for today",
        'preview_focus': "Focus - {0}",
        'preview_break': "Break Time",
        'preview_break_next': "Break Time (Next: {0})",
        'preview_gap': "Gap Time",
        'preview_start_button': "Start",
        'preview_cancel_button': "Cancel",
        'timer_status_work': "Focusing...",
        'timer_status_break': "On a Break",
        'timer_status_stopped': "Stopped",
        'timer_status_waiting': "Waiting to start",
        'timer_status_gap': "Gap Time",
        'timer_task_next': "Up next: {0}",
        'timer_task_next_soon': "Next session is coming up...",
        'timer_task_done': "All tasks completed",
        'notification_title_work': "Focus Time",
        'notification_title_break': "Take a Break",
        'notification_done': "Tasks Complete",
        'notification_done_msg': "Congratulations! All tasks for today are done.",
        'minimized_msg': "Minimized to tray, still running in background.",
        'select_date_title': "Select Date",
        'select_time_title': "Select Time",
        'save_error': "Save Error",
        'save_error_msg': "Could not save schedule file:\n{0}",
        'load_error': "Load Error",
        'load_error_msg': "Could not load schedule file, a new one will be created.\nError: {0}",
    },
    'ja': {
        'window_title': "FocusFlow - ポモドーロ＆スケジュールアシスタント",
        'tray_tooltip': "FocusFlow ポモドーロアシスタント",
        'show': "表示",
        'quit': "終了",
        'select_start_date': "開始日を選択:",
        'mode': "モード:",
        'work_rest_format': "作業 {0} 分 / 休憩 {1} 分",
        'mode_tooltip': "作業/休憩時間を選択",
        'start_button_today': "今日のポモドーロをプレビュー＆開始",
        'start_button_other_day': "今日が含まれる場合のみ開始可能",
        'add_task_tooltip': "{0} のタスクを追加",
        'task_placeholder': "タスクを入力...",
        'max_tasks_reached': "1日の最大タスク数（20）に達しました。",
        'no_tasks_today': "今日のタスクを少なくとも1つ追加してください！",
        'preview_title': "スケジュールプレビュー＆確認",
        'preview_header': "<b>ポモドーロ実行スケジュール:</b><br>",
        'preview_no_tasks': "今日のタスクはありません",
        'preview_focus': "集中 - {0}",
        'preview_break': "休憩時間",
        'preview_break_next': "休憩時間 (次: {0})",
        'preview_gap': "空き時間",
        'preview_start_button': "開始",
        'preview_cancel_button': "キャンセル",
        'timer_status_work': "集中中...",
        'timer_status_break': "休憩中",
        'timer_status_stopped': "停止",
        'timer_status_waiting': "開始待ち",
        'timer_status_gap': "空き時間",
        'timer_task_next': "次のタスク: {0}",
        'timer_task_next_soon': "次のセッションが間もなく開始...",
        'timer_task_done': "すべてのタスクが完了しました",
        'notification_title_work': "集中時間",
        'notification_title_break': "休憩してください",
        'notification_done': "タスク完了",
        'notification_done_msg': "おめでとうございます！今日のタスクはすべて完了しました。",
        'minimized_msg': "トレイに最小化しました。バックグラウンドで実行中です。",
        'select_date_title': "日付を選択",
        'select_time_title': "時間を選択",
        'save_error': "保存エラー",
        'save_error_msg': "スケジュールファイルを保存できませんでした:\n{0}",
        'load_error': "読み込みエラー",
        'load_error_msg': "スケジュールファイルを読み込めません。新しいファイルを作成します。\nエラー: {0}",
    }
}

# --- 自訂樣式表 (Stylesheet) ---
STYLESHEET = """
QWidget#MainWindow {
    background-color: rgba(30, 30, 45, 0.9);
    border-radius: 15px;
    border: 1px solid #bd93f9;
}
QLabel, QComboBox {
    color: #E0E0E0;
    font-size: 14px;
    font-family: 'Segoe UI', 'Microsoft JhengHei';
}
QLabel#TitleLabel {
    font-size: 20px;
    font-weight: bold;
    color: #FFFFFF;
    padding: 5px;
}
QLabel#DateHeaderLabel {
    font-size: 16px;
    font-weight: bold;
    color: #ffb86c; /* 橘色日期標題 */
    padding: 5px 0;
    border-bottom: 1px solid #44475a;
    margin-bottom: 5px;
}
QLabel#StatusLabel {
    font-size: 18px;
    font-weight: bold;
    color: #50fa7b; /* 亮綠色 */
}
QLabel#TimerLabel {
    font-size: 48px;
    font-weight: bold;
    color: #FFFFFF;
}
QLineEdit, QComboBox {
    background-color: #282a36;
    border: 1px solid #6272a4;
    border-radius: 5px;
    padding: 5px;
    color: #FFD700; /* 修改為金色 */
}
QPushButton#DateTimeButton {
    background-color: #44475a;
    border: 1px solid #6272a4;
    border-radius: 5px;
    padding: 5px;
    color: #FFD700; /* 修改為金色 */
    text-align: center;
}
QPushButton#DateTimeButton:hover {
    background-color: #5a5d72;
}
QCalendarWidget QToolButton { color: black; }
QPushButton {
    background-color: #6272a4;
    color: #f8f8f2;
    border-radius: 5px;
    padding: 8px 12px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton:hover { background-color: #7082b6; }
QPushButton:pressed { background-color: #505a84; }
QPushButton#AddButton, QPushButton#RemoveButton {
    min-width: 30px;
    max-width: 30px;
    font-size: 18px;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollBar:vertical {
    border: none;
    background: #282a36;
    width: 8px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #6272a4;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
"""

# --- 特效提示視窗 ---
class NotificationWidget(QWidget):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.bg_frame = QFrame(self)
        self.bg_frame.setStyleSheet("QFrame { background-color: rgba(20, 20, 30, 0.9); border-radius: 15px; border: 1px solid #bd93f9; }")
        frame_layout = QVBoxLayout(self.bg_frame)
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: #bd93f9; font-size: 20px; font-weight: bold;")
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet("color: white; font-size: 16px;")
        self.message_label.setWordWrap(True)
        frame_layout.addWidget(self.title_label)
        frame_layout.addWidget(self.message_label)
        self.layout.addWidget(self.bg_frame)
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(500)
        QTimer.singleShot(5000, self.hide_animation)

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

# --- 主視窗 ---
class PomodoroApp(QWidget):
    def __init__(self):
        super().__init__()
        self.schedule_data = {}
        self.pomodoro_schedule = []
        self.day_widgets = {}
        self.current_task_index = -1
        self.is_running = False
        self.old_pos = None
        self.data_dirty = False
        self.current_lang = 'zh_TW' # 預設語言

        self.init_ui()
        self.load_data()
        self.populate_week_view(QDate.currentDate())
        self.retranslate_ui()

        self.main_timer = QTimer(self)
        self.main_timer.timeout.connect(self.update_timer)
        self.main_timer.start(1000)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.autosave_data)
        self.autosave_timer.start(3000)

    def get_text(self, key):
        return TRANSLATIONS[self.current_lang].get(key, key)

    def init_ui(self):
        self.setObjectName("MainWindow")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(STYLESHEET)
        self.resize(450, 700)
        self.app_icon = self.get_app_icon()
        self.setWindowIcon(self.app_icon)
        self.setup_tray_icon()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setup_title_bar()
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(15, 0, 15, 15)
        self.setup_view = QWidget()
        self.timer_view = QWidget()
        self.setup_ui(self.setup_view)
        self.timer_ui(self.timer_view)
        self.content_layout.addWidget(self.setup_view)
        self.content_layout.addWidget(self.timer_view)
        self.main_layout.addWidget(self.title_bar)
        self.main_layout.addWidget(self.content_widget)
        self.timer_view.hide()

    def get_app_icon(self):
        icon_path = 'icon.png'
        if os.path.exists(os.path.join(APP_DIR, icon_path)): return QIcon(os.path.join(APP_DIR, icon_path))
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor("#d9534f")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(5, 15, 54, 44)
        painter.setBrush(QBrush(QColor("#5cb85c")))
        path = QPainterPath()
        path.moveTo(32, 0); path.quadTo(20, 10, 32, 20); path.quadTo(44, 10, 32, 0)
        painter.drawPath(path)
        painter.end()
        return QIcon(pixmap)

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.app_icon)
        self.tray_menu = QMenu()
        self.show_action = QAction()
        self.quit_action = QAction()
        self.show_action.triggered.connect(self.showNormal)
        self.quit_action.triggered.connect(self.quit_app)
        self.tray_menu.addAction(self.show_action); self.tray_menu.addAction(self.quit_action)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def setup_title_bar(self):
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(40)
        self.title_bar.setStyleSheet("background-color: transparent;")
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(15, 0, 15, 0)
        self.title_label = QLabel("FocusFlow"); self.title_label.setObjectName("TitleLabel")
        self.minimize_button = QPushButton("—"); self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.clicked.connect(self.show_minimized)
        self.close_button = QPushButton("✕"); self.close_button.setFixedSize(30, 30)
        self.close_button.clicked.connect(self.quit_app)
        title_bar_layout.addWidget(self.title_label); title_bar_layout.addStretch()
        title_bar_layout.addWidget(self.minimize_button); title_bar_layout.addWidget(self.close_button)

    def setup_ui(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(0, 10, 0, 0); layout.setSpacing(10)
        
        # --- 頂部控制面板 ---
        top_panel = QFrame()
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(0,0,0,0)

        self.date_label = QLabel()
        self.date_picker = DatePickerButton(self)
        
        self.mode_label = QLabel()
        self.pomodoro_mode_combo = QComboBox()
        
        self.lang_label = QLabel("語言:")
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("繁體中文", "zh_TW")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("日本語", "ja")
        self.lang_combo.currentIndexChanged.connect(self.language_changed)

        top_layout.addWidget(self.date_label)
        top_layout.addWidget(self.date_picker)
        top_layout.addStretch()
        top_layout.addWidget(self.mode_label)
        top_layout.addWidget(self.pomodoro_mode_combo)
        top_layout.addStretch()
        top_layout.addWidget(self.lang_label)
        top_layout.addWidget(self.lang_combo)
        layout.addWidget(top_panel)

        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
        self.week_view_widget = QWidget()
        self.week_view_layout = QVBoxLayout(self.week_view_widget)
        self.week_view_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(self.week_view_widget)
        layout.addWidget(scroll_area)
        
        self.start_button = QPushButton()
        self.start_button.clicked.connect(self.preview_and_start_pomodoro)
        layout.addWidget(self.start_button)

    def timer_ui(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(10, 20, 10, 20); layout.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.setSpacing(20)
        self.status_label = QLabel(); self.status_label.setObjectName("StatusLabel"); self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.task_label = QLabel(); self.task_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.task_label.setWordWrap(True); self.task_label.setFont(QFont('Segoe UI', 18))
        self.timer_label = QLabel("00:00"); self.timer_label.setObjectName("TimerLabel"); self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stop_button = QPushButton(); self.stop_button.clicked.connect(self.stop_pomodoro)
        layout.addStretch(); layout.addWidget(self.status_label); layout.addWidget(self.task_label); layout.addWidget(self.timer_label); layout.addStretch(); layout.addWidget(self.stop_button)

    def language_changed(self):
        self.current_lang = self.lang_combo.currentData()
        self.data_dirty = True
        self.retranslate_ui()

    def retranslate_ui(self):
        # 主視窗
        self.setWindowTitle(self.get_text('window_title'))
        self.date_label.setText(self.get_text('select_start_date'))
        self.mode_label.setText(self.get_text('mode'))
        
        # 番茄鐘模式下拉選單
        self.pomodoro_mode_combo.clear()
        self.pomodoro_mode_combo.addItem(self.get_text('work_rest_format').format(20, 5), (20, 5))
        self.pomodoro_mode_combo.addItem(self.get_text('work_rest_format').format(25, 10), (25, 10))
        self.pomodoro_mode_combo.addItem(self.get_text('work_rest_format').format(30, 15), (30, 15))
        self.pomodoro_mode_combo.setToolTip(self.get_text('mode_tooltip'))
        
        # 更新七日視圖中的文字
        for day_widget in self.day_widgets.values():
            day_widget.retranslate_ui()
            for task_widget in day_widget.task_widgets:
                task_widget.task_input.setPlaceholderText(self.get_text('task_placeholder'))

        # 啟動按鈕
        self.update_start_button_text()
        
        # 計時器介面
        self.stop_button.setText(self.get_text('preview_cancel_button'))
        
        # 系統匣
        self.tray_icon.setToolTip(self.get_text('tray_tooltip'))
        self.show_action.setText(self.get_text('show'))
        self.quit_action.setText(self.get_text('quit'))

    def update_start_button_text(self):
        start_date = self.date_picker.date
        is_today_in_view = QDate.currentDate() >= start_date and QDate.currentDate() < start_date.addDays(7)
        self.start_button.setEnabled(is_today_in_view)
        self.start_button.setText(self.get_text('start_button_today') if is_today_in_view else self.get_text('start_button_other_day'))

    def date_selection_changed(self, date):
        self.populate_week_view(date)

    def populate_week_view(self, start_date):
        for i in reversed(range(self.week_view_layout.count())): 
            widget = self.week_view_layout.itemAt(i).widget()
            if widget: widget.setParent(None)
        self.day_widgets.clear()
        for i in range(7):
            date = start_date.addDays(i)
            date_str = date.toString("yyyy-MM-dd")
            day_widget = DayScheduleWidget(date, self)
            if date_str in self.schedule_data: day_widget.load_day_data(self.schedule_data[date_str])
            self.week_view_layout.addWidget(day_widget)
            self.day_widgets[date_str] = day_widget
        self.update_start_button_text()

    def schedule_changed(self):
        self.data_dirty = True

    def autosave_data(self):
        if self.data_dirty:
            self.save_data_to_file()
            self.data_dirty = False

    def save_data_to_file(self):
        # 先收集UI上的資料
        for date_str, widget in self.day_widgets.items():
            day_data = widget.get_day_data()
            if day_data: self.schedule_data[date_str] = day_data
            elif date_str in self.schedule_data: del self.schedule_data[date_str]
        
        # 將語言設定加入儲存
        full_data = {
            'language': self.current_lang,
            'schedule': self.schedule_data
        }
        
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, ensure_ascii=False, indent=4)
        except IOError as e:
            QMessageBox.warning(self, self.get_text('save_error'), self.get_text('save_error_msg').format(e))

    def load_data(self):
        try:
            if not os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump({'language': 'zh_TW', 'schedule': {}}, f)
                self.schedule_data = {}
                self.current_lang = 'zh_TW'
            else:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
                    full_data = json.loads(content) if content else {}
                    self.schedule_data = full_data.get('schedule', {})
                    self.current_lang = full_data.get('language', 'zh_TW')
                    
                    # 更新語言下拉選單的顯示
                    index = self.lang_combo.findData(self.current_lang)
                    if index != -1:
                        self.lang_combo.setCurrentIndex(index)

        except (json.JSONDecodeError, IOError) as e:
            QMessageBox.critical(self, self.get_text('load_error'), self.get_text('load_error_msg').format(e))
            self.schedule_data = {}
            self.current_lang = 'zh_TW'

    def generate_pomodoro_schedule(self):
        today_str = QDate.currentDate().toString("yyyy-MM-dd")
        if today_str not in self.schedule_data or not self.schedule_data[today_str].get("tasks"):
            return None, self.get_text('preview_no_tasks')
        
        tasks = self.schedule_data[today_str]["tasks"]
        work_min, break_min = self.pomodoro_mode_combo.currentData()
        now_dt = datetime.now()
        
        schedule_list = []
        schedule_text_lines = [self.get_text('preview_header')]

        first_task_time = QTime.fromString(tasks[0]['time'], "HH:mm").toPyTime()
        current_dt = datetime.combine(now_dt.date(), first_task_time)
        current_dt = max(now_dt, current_dt)

        for i, task_info in enumerate(tasks):
            task_name = task_info['name']
            
            # 如果這不是第一個任務，檢查與上一個休息結束時間的空檔
            if schedule_list:
                prev_end_dt = schedule_list[-1]['end']
                task_start_dt = datetime.combine(now_dt.date(), QTime.fromString(task_info['time'], "HH:mm").toPyTime())
                current_dt = max(prev_end_dt, task_start_dt)

            work_start_dt = current_dt
            work_end_dt = work_start_dt + timedelta(minutes=work_min)
            schedule_list.append({"type": "work", "name": task_name, "start": work_start_dt, "end": work_end_dt})
            schedule_text_lines.append(f"<font color='#D4AC0D'>{work_start_dt.strftime('%H:%M')} - {work_end_dt.strftime('%H:%M')}: {self.get_text('preview_focus').format(task_name)}</font>")

            break_start_dt = work_end_dt
            break_end_dt = break_start_dt + timedelta(minutes=break_min)
            
            next_task_msg = ""
            if i + 1 < len(tasks):
                next_task_name = tasks[i+1]['name']
                next_task_msg = self.get_text('preview_break_next').format(next_task_name)
            else:
                next_task_msg = self.get_text('preview_break')

            schedule_list.append({"type": "break", "name": next_task_msg, "start": break_start_dt, "end": break_end_dt})
            schedule_text_lines.append(f"<font color='#E74C3C'>{break_start_dt.strftime('%H:%M')} - {break_end_dt.strftime('%H:%M')}: {self.get_text('preview_break')}</font>")
            
            current_dt = break_end_dt

        return schedule_list, "<br>".join(schedule_text_lines)

    def preview_and_start_pomodoro(self):
        self.autosave_data()
        generated_schedule, schedule_text = self.generate_pomodoro_schedule()

        if not generated_schedule:
            QMessageBox.warning(self, "提示", self.get_text('no_tasks_today'))
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(self.get_text('preview_title'))
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        label = QLabel(schedule_text); label.setWordWrap(True); label.setTextFormat(Qt.TextFormat.RichText)
        scroll = QScrollArea(); scroll.setWidget(label); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(scroll)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(self.get_text('preview_start_button'))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.get_text('preview_cancel_button'))
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec():
            self.pomodoro_schedule = generated_schedule
            self.is_running = True
            self.current_task_index = -1
            self.setup_view.hide()
            self.timer_view.show()
            self.update_timer()

    def stop_pomodoro(self):
        self.is_running = False; self.pomodoro_schedule = []; self.current_task_index = -1
        self.timer_view.hide(); self.setup_view.show()
        self.status_label.setText(self.get_text('timer_status_stopped')); self.task_label.setText("..."); self.timer_label.setText("00:00")

    def update_timer(self):
        if not self.is_running: return
        now = datetime.now()
        found_task = False
        for i, task in enumerate(self.pomodoro_schedule):
            if task["start"] <= now < task["end"]:
                if self.current_task_index != i:
                    self.current_task_index = i
                    title = self.get_text('notification_title_work') if task['type'] == 'work' else self.get_text('notification_title_break')
                    self.show_notification(title, task['name'].split('(')[0].strip())

                remaining_delta = task["end"] - now
                remaining_secs = int(remaining_delta.total_seconds())
                minutes, seconds = divmod(max(0, remaining_secs), 60)
                self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")
                self.task_label.setText(task['name'])
                is_work = task['type'] == 'work'
                self.status_label.setText(self.get_text('timer_status_work') if is_work else self.get_text('timer_status_break'))
                self.status_label.setStyleSheet("color: #50fa7b;" if is_work else "color: #8be9fd;")
                found_task = True
                break
        
        if not found_task:
            if self.pomodoro_schedule and now >= self.pomodoro_schedule[-1]["end"]:
                if self.is_running:
                    self.show_notification(self.get_text('notification_done'), self.get_text('notification_done_msg'))
                    self.stop_pomodoro()
            elif self.pomodoro_schedule and now < self.pomodoro_schedule[0]["start"]:
                first_task = self.pomodoro_schedule[0]
                self.status_label.setText(self.get_text('timer_status_waiting'))
                self.task_label.setText(self.get_text('timer_task_next').format(first_task['name']))
                self.timer_label.setText(first_task['start'].strftime("%H:%M"))
            else:
                self.status_label.setText(self.get_text('timer_status_gap'))
                self.task_label.setText(self.get_text('timer_task_done'))
                self.timer_label.setText("--:--")

    def show_notification(self, title, message):
        try:
            self.notification = NotificationWidget(title, message)
            self.notification.show_animation()
        except Exception as e:
            print(f"顯示通知時發生錯誤: {e}")

    def show_minimized(self):
        self.hide()
        self.tray_icon.showMessage("FocusFlow", self.get_text('minimized_msg'), self.app_icon, 2000)

    def showNormal(self):
        super().showNormal()
        self.setWindowState(Qt.WindowState.WindowNoState)
        self.activateWindow()

    def quit_app(self):
        self.autosave_data()
        self.tray_icon.hide()
        QApplication.instance().quit()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isHidden(): self.showNormal()
            else: self.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.title_bar.geometry().contains(event.pos()):
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 15, 15)
        bg_color = QColor(40, 42, 54, 230) if self.is_running else QColor(30, 30, 45, 217)
        painter.fillPath(path, QBrush(bg_color))
        pen = QPen(QColor(189, 147, 249, 150), 1)
        painter.setPen(pen)
        painter.drawPath(path)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = PomodoroApp()
    window.show()
    sys.exit(app.exec())
