# main.py - الإصدار النهائي
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from database import init_db
from utils.backup import create_backup
from ui.login_window import LoginWindow

# إنشاء المجلدات اللازمة
for folder in ['photos', 'documents', 'reports', 'backups']:
    os.makedirs(folder, exist_ok=True)

class TrainingCenterApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.setup_app()
        
    def setup_app(self):
        """إعداد تطبيق Qt."""
        # دعم RTL للعربية
        self.app.setLayoutDirection(Qt.RightToLeft)
        self.app.setFont(QFont('Tahoma', 10))
        
        # إعداد أيقونة التطبيق (اختياري)
        try:
            self.app.setWindowIcon(QIcon('icon.png'))
        except:
            pass
        
        # تهيئة قاعدة البيانات
        init_db()
        create_backup()
        
    def run(self):
        """تشغيل التطبيق."""
        login_window = LoginWindow()
        if login_window.exec_() == LoginWindow.Accepted:
            from ui.main_window import MainWindow
            main_window = MainWindow(login_window.user_id, login_window.user_role)
            main_window.show()
            sys.exit(self.app.exec_())
        else:
            print("تم إلغاء تسجيل الدخول")
            sys.exit()

if __name__ == '__main__':
    app = TrainingCenterApp()
    app.run()