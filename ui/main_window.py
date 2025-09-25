# main_window.py
from database import get_connection
from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QMenuBar, QAction, QMessageBox, 
                             QFileDialog, QApplication)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from .trainees_window import TraineesWindow
from .attendance_window import AttendanceWindow
from .documents_window import DocumentsWindow
from .schedule_window import ScheduleWindow
from .promotion_window import PromotionWindow
from .disciplinary_window import DisciplinaryWindow
from .reports_window import ReportsWindow
from utils.security import has_permission, log_activity
from utils.backup import create_backup
from database import init_db

class MainWindow(QMainWindow):
    def __init__(self, user_id, user_role):
        super().__init__()
        self.user_id = user_id
        self.user_role = user_role
        init_db()  # تأكيد إنشاء DB
        self.setWindowTitle('نظام إدارة التكوين المهني - مرحباً بك')
        self.setGeometry(100, 100, 1200, 800)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setFont(QFont('Tahoma', 10))  # خط عربي
        
        # شريط القوائم
        self.create_menu_bar()
        
        # Tabs الرئيسية
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # إضافة Tabs (فقط إذا كانت الصلاحيات تسمح)
        if has_permission(user_role, 'user'):
            self.add_tabs()
        
        # نسخ احتياطي تلقائي كل 24 ساعة (مثال بسيط؛ استخدم scheduler للدقة)
        self.backup_timer = QTimer()
        self.backup_timer.timeout.connect(create_backup)
        self.backup_timer.start(86400000)  # 24 ساعة بالملي ثانية
        create_backup()  # نسخة أولى
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # قائمة الملف
        file_menu = menubar.addMenu('الملف')
        backup_action = QAction('نسخ احتياطي', self)
        backup_action.triggered.connect(create_backup)
        file_menu.addAction(backup_action)
        
        exit_action = QAction('خروج', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # قائمة المساعدة
        help_menu = menubar.addMenu('مساعدة')
        about_action = QAction('حول البرنامج', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def add_tabs(self):
        # تبويب المتربصين
        self.trainees_tab = TraineesWindow(self.user_role)
        self.tabs.addTab(self.trainees_tab, 'إدارة المتربصين')
        
        # تبويب الحضور
        self.attendance_tab = AttendanceWindow(self.user_role)
        self.tabs.addTab(self.attendance_tab, 'الحضور والغياب')
        
        # تبويب الوثائق
        self.documents_tab = DocumentsWindow(self.user_role)
        self.tabs.addTab(self.documents_tab, 'أرشفة الوثائق')
        
        # تبويب الجداول
        self.schedule_tab = ScheduleWindow(self.user_role)
        self.tabs.addTab(self.schedule_tab, 'جداول الحصص')
        
        # تبويب الترقية
        self.promotion_tab = PromotionWindow(self.user_role)
        self.tabs.addTab(self.promotion_tab, 'ترقية الأفواج')
        
        # تبويب الإجراءات التأديبية
        self.disciplinary_tab = DisciplinaryWindow(self.user_role)
        self.tabs.addTab(self.disciplinary_tab, 'الإجراءات التأديبية')
        
        # تبويب التقارير
        self.reports_tab = ReportsWindow(self.user_role)
        self.tabs.addTab(self.reports_tab, 'التقارير والإحصائيات')
    
    def show_about(self):
        QMessageBox.information(self, 'حول', 'نظام إدارة التكوين المهني v1.0\nمطور: BLACKBOX.AI\nللاستفسارات: contact@example.com')
    
    def closeEvent(self, event):
        log_activity(self.user_id, 'خروج من النظام')
        event.accept()
