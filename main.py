import sys
import json
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, 
                             QSystemTrayIcon, QMenu, QScrollArea, QFrame, QHBoxLayout, 
                             QComboBox, QMessageBox, QDialog, QDialogButtonBox, QSpinBox)
from PyQt6.QtCore import (Qt, QTimer, QDate, QPoint, QRectF, QTime)
from PyQt6.QtGui import QIcon, QAction, QColor, QFont, QPixmap, QPainter, QBrush, QPainterPath, QPen

# --- 假設這些檔案存在於同一個資料夾 ---
# translations.py 和 ui_components.py 的內容需要您保留原樣
try:
    from translations import TRANSLATIONS
    from ui_components import (NotificationWidget, DatePickerButton, DayScheduleWidget)
except ImportError:
    # 如果檔案不存在，提供一個基本的備用方案
    TRANSLATIONS = {'zh_TW': {'window_title': 'FocusFlow'}}
    class NotificationWidget(QWidget): pass
    class DatePickerButton(QPushButton): pass
    class DayScheduleWidget(QWidget): pass
    print("警告：缺少 translations.py 或 ui_components.py 檔案。")
# ------------------------------------

# --- 應用程式設定 ---
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(APP_DIR, "pomodoro_schedule.json")

# --- 自訂樣式表 (Stylesheet) ---
STYLESHEET = """
QWidget#MainWindow {
    background-color: rgba(30, 30, 45, 0.9);
    border-radius: 15px;
    border: 1px solid #bd93f9;
}
QLabel, QComboBox, QSpinBox {
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
    color: #ffb86c;
    padding: 5px 0;
    border-bottom: 1px solid #44475a;
    margin-bottom: 5px;
}
QLabel#StatusLabel {
    font-size: 18px;
    font-weight: bold;
    color: #50fa7b;
}
QLabel#TimerLabel {
    font-size: 48px;
    font-weight: bold;
    color: #FFFFFF;
}
QLineEdit, QComboBox, QSpinBox {
    background-color: #282a36;
    border: 1px solid #6272a4;
    border-radius: 5px;
    padding: 5px;
    color: #FFD700; /* 金色 */
}
QPushButton#DateTimeButton {
    background-color: #44475a;
    border: 1px solid #6272a4;
    border-radius: 5px;
    padding: 5px;
    color: #FFD700; /* 金色 */
    text-align: center;
}
QPushButton#DateTimeButton:hover { background-color: #5a5d72; }
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
QScrollArea { border: none; background-color: transparent; }
QScrollBar:vertical {
    border: none; background: #282a36; width: 8px; margin: 0px;
}
QScrollBar::handle:vertical {
    background: #6272a4; min-height: 20px; border-radius: 4px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
"""

# --- 自訂時間輸入對話框 ---
class CustomTimeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle(self.parent_window.get_text('custom_mode_title'))
        
        self.layout = QVBoxLayout(self)
        
        work_layout = QHBoxLayout()
        self.work_label = QLabel(self.parent_window.get_text('work_minutes_label'))
        self.work_spinbox = QSpinBox()
        self.work_spinbox.setRange(1, 99)
        self.work_spinbox.setValue(25)
        work_layout.addWidget(self.work_label)
        work_layout.addWidget(self.work_spinbox)
        self.layout.addLayout(work_layout)

        break_layout = QHBoxLayout()
        self.break_label = QLabel(self.parent_window.get_text('break_minutes_label'))
        self.break_spinbox = QSpinBox()
        self.break_spinbox.setRange(1, 99)
        self.break_spinbox.setValue(5)
        break_layout.addWidget(self.break_label)
        break_layout.addWidget(self.break_spinbox)
        self.layout.addLayout(break_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(self.parent_window.get_text('ok'))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.parent_window.get_text('cancel'))
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_times(self):
        return (self.work_spinbox.value(), self.break_spinbox.value())

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
        self.current_lang = 'zh_TW'
        self.custom_mode_data = None
        self.last_mode_index = 0

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
        return TRANSLATIONS.get(self.current_lang, {}).get(key, key)

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
        
        top_panel = QFrame()
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(0,0,0,0)

        self.date_label = QLabel()
        self.date_picker = DatePickerButton(self)
        
        self.mode_label = QLabel()
        self.pomodoro_mode_combo = QComboBox()
        self.pomodoro_mode_combo.currentIndexChanged.connect(self.pomodoro_mode_changed)
        
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
        self.setWindowTitle(self.get_text('window_title'))
        self.date_label.setText(self.get_text('select_start_date'))
        self.mode_label.setText(self.get_text('mode'))
        
        self.pomodoro_mode_combo.blockSignals(True)
        self.pomodoro_mode_combo.clear()
        self.pomodoro_mode_combo.addItem(self.get_text('work_rest_format').format(20, 5), (20, 5))
        self.pomodoro_mode_combo.addItem(self.get_text('work_rest_format').format(25, 10), (25, 10))
        self.pomodoro_mode_combo.addItem(self.get_text('work_rest_format').format(30, 15), (30, 15))
        if self.custom_mode_data:
            self.pomodoro_mode_combo.addItem(self.get_text('work_rest_format').format(self.custom_mode_data[0], self.custom_mode_data[1]), self.custom_mode_data)
        self.pomodoro_mode_combo.addItem(self.get_text('custom_mode'), "custom")
        self.pomodoro_mode_combo.setToolTip(self.get_text('mode_tooltip'))
        self.pomodoro_mode_combo.setCurrentIndex(self.last_mode_index)
        self.pomodoro_mode_combo.blockSignals(False)

        for day_widget in self.day_widgets.values(): day_widget.retranslate_ui()
        self.update_start_button_text()
        self.stop_button.setText(self.get_text('preview_cancel_button'))
        self.tray_icon.setToolTip(self.get_text('tray_tooltip'))
        self.show_action.setText(self.get_text('show'))
        self.quit_action.setText(self.get_text('quit'))

    def pomodoro_mode_changed(self, index):
        if self.pomodoro_mode_combo.itemData(index) == "custom":
            dialog = CustomTimeDialog(self)
            if dialog.exec():
                self.custom_mode_data = dialog.get_times()
                self.last_mode_index = self.pomodoro_mode_combo.count() - 1 
                self.retranslate_ui() 
                self.pomodoro_mode_combo.setCurrentIndex(self.last_mode_index)
            else:
                self.pomodoro_mode_combo.setCurrentIndex(self.last_mode_index)
        else:
            self.last_mode_index = index

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
        for date_str, widget in self.day_widgets.items():
            day_data = widget.get_day_data()
            if day_data and day_data.get('tasks'): self.schedule_data[date_str] = day_data
            elif date_str in self.schedule_data: del self.schedule_data[date_str]
        full_data = {'language': self.current_lang, 'schedule': self.schedule_data}
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, ensure_ascii=False, indent=4)
        except IOError as e:
            QMessageBox.warning(self, self.get_text('save_error'), self.get_text('save_error_msg').format(e))

    def load_data(self):
        try:
            if not os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump({'language': 'zh_TW', 'schedule': {}}, f)
                self.schedule_data = {}; self.current_lang = 'zh_TW'
            else:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
                    full_data = json.loads(content) if content else {}
                    self.schedule_data = full_data.get('schedule', {})
                    self.current_lang = full_data.get('language', 'zh_TW')
                    index = self.lang_combo.findData(self.current_lang)
                    if index != -1: self.lang_combo.setCurrentIndex(index)
        except (json.JSONDecodeError, IOError) as e:
            QMessageBox.critical(self, self.get_text('load_error'), self.get_text('load_error_msg').format(e))
            self.schedule_data = {}; self.current_lang = 'zh_TW'

    def generate_pomodoro_schedule(self):
        """
        生成番茄鐘排程的核心函數。
        1. 獲取並按時間排序當天的任務。
        2. 找到第一個尚未開始的任務作為起點。
        3. 如果所有任務都已過去，詢問使用者是否從頭開始。
        4. 重新排序任務列表，將即將執行的任務放在最前面，形成一個環形隊列。
        5. 基於這個新的隊列，生成一個連續不斷的工作-休息時間鏈。
        """
        today_str = QDate.currentDate().toString("yyyy-MM-dd")
        if today_str not in self.schedule_data or not self.schedule_data[today_str].get("tasks"):
            return None, self.get_text('preview_no_tasks')
        
        tasks = self.schedule_data[today_str]["tasks"]
        if not tasks:
            return None, self.get_text('preview_no_tasks')

        # 步驟 1: 按時間對任務進行排序，確保處理順序正確
        tasks.sort(key=lambda x: QTime.fromString(x.get('time', '00:00'), "HH:mm"))

        mode_data = self.pomodoro_mode_combo.currentData()
        if not isinstance(mode_data, tuple) or len(mode_data) != 2:
            QMessageBox.warning(self, "模式錯誤", "請選擇一個有效的番茄鐘模式。")
            return None, "模式錯誤"
        
        work_min, break_min = mode_data
        now_dt = datetime.now()
        
        # 步驟 2: 找到第一個尚未開始的任務的索引
        start_task_index = -1
        for i, task_info in enumerate(tasks):
            task_start_dt = datetime.combine(now_dt.date(), QTime.fromString(task_info['time'], "HH:mm").toPyTime())
            if task_start_dt >= now_dt:
                start_task_index = i
                break
        
        # 步驟 3: 如果所有任務的設定時間都已過去
        if start_task_index == -1:
            reply = QMessageBox.question(self, self.get_text('all_tasks_past_title'), self.get_text('all_tasks_past_msg'),
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                start_task_index = 0  # 從今天的第一個任務開始
            else:
                return None, self.get_text('all_tasks_past_info')

        # 步驟 4: 建立一個新的、環形排列的任務列表，確保所有任務都會被執行
        tasks_to_run = tasks[start_task_index:] + tasks[:start_task_index]

        # 步驟 5: 設定整個連續排程的起始時間
        first_task_original_time = QTime.fromString(tasks_to_run[0]['time'], "HH:mm").toPyTime()
        current_dt = datetime.combine(now_dt.date(), first_task_original_time)
        # 如果任務的預定時間已過（或即將到來），則從現在開始；否則，從預定時間開始
        current_dt = max(now_dt, current_dt) 

        schedule_list = []
        schedule_text_lines = [self.get_text('preview_header')]

        # 步驟 6: 遍歷重新排序後的任務列表，生成連續的時間鏈
        for i, task_info in enumerate(tasks_to_run):
            task_name = task_info['name']
            
            # 每個任務的工作時間都從上一個活動（休息）結束的時間點開始
            # 對於第一個任務，current_dt 已經在上面設定好了
            work_start_dt = current_dt
            work_end_dt = work_start_dt + timedelta(minutes=work_min)
            schedule_list.append({"type": "work", "name": task_name, "start": work_start_dt, "end": work_end_dt})
            schedule_text_lines.append(f"<font color='#D4AC0D'>{work_start_dt.strftime('%H:%M')} - {work_end_dt.strftime('%H:%M')}: {self.get_text('preview_focus').format(task_name)}</font>")

            break_start_dt = work_end_dt
            break_end_dt = break_start_dt + timedelta(minutes=break_min)
            
            # 決定休息時間的提示文字
            if i + 1 < len(tasks_to_run):
                next_task_name = tasks_to_run[i+1]['name']
                break_name = self.get_text('preview_break_next').format(next_task_name)
            else:
                break_name = self.get_text('preview_break_final')

            schedule_list.append({"type": "break", "name": break_name, "start": break_start_dt, "end": break_end_dt})
            schedule_text_lines.append(f"<font color='#E74C3C'>{break_start_dt.strftime('%H:%M')} - {break_end_dt.strftime('%H:%M')}: {self.get_text('preview_break')}</font>")
            
            # 更新時間點，為下一個任務做準備
            current_dt = break_end_dt
            
        return schedule_list, "<br>".join(schedule_text_lines)

    def validate_schedule(self, schedule):
        if not schedule: return False
        for i in range(len(schedule) - 1):
            # 允許時間相等，因為一個結束後下一個立刻開始
            if schedule[i]['end'] > schedule[i+1]['start']:
                print(f"驗證錯誤: 事件 {i} 結束於 {schedule[i]['end']} 但下個事件 {i+1} 開始於 {schedule[i+1]['start']}")
                return False
        return True

    def preview_and_start_pomodoro(self):
        self.autosave_data()
        generated_schedule, schedule_text = self.generate_pomodoro_schedule()

        if not generated_schedule:
            QMessageBox.warning(self, "提示", schedule_text)
            return
        
        if not self.validate_schedule(generated_schedule):
            QMessageBox.critical(self, self.get_text('validation_error_title'), self.get_text('validation_error_msg'))
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
                    is_work = task['type'] == 'work'
                    title = self.get_text('notification_title_work') if is_work else self.get_text('notification_title_break')
                    message = task['name'].split('(')[0].strip()
                    self.show_notification(title, message, notification_type=task['type'])

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
                    self.show_notification(self.get_text('notification_done'), self.get_text('notification_done_msg'), notification_type='done')
                    self.stop_pomodoro()
            elif self.pomodoro_schedule and now < self.pomodoro_schedule[0]["start"]:
                first_task = self.pomodoro_schedule[0]
                self.status_label.setText(self.get_text('timer_status_waiting'))
                self.task_label.setText(self.get_text('timer_task_next').format(first_task['name']))
                self.timer_label.setText(first_task['start'].strftime("%H:%M"))
            else:
                # 這種情況理論上不應該發生在連續排程中，但作為備用
                self.status_label.setText(self.get_text('timer_status_gap'))
                self.task_label.setText(self.get_text('timer_task_done'))
                self.timer_label.setText("--:--")

    def show_notification(self, title, message, notification_type='info'):
        try:
            self.notification = NotificationWidget(title, message, notification_type, self)
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
    # 確保 ui_components 和 translations 檔案存在
    if 'DayScheduleWidget' not in globals():
        QMessageBox.critical(None, "錯誤", "缺少必要的 ui_components.py 檔案，程式無法執行。")
        sys.exit(1)
    window = PomodoroApp()
    window.show()
    sys.exit(app.exec())
