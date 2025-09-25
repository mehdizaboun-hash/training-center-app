# database.py
import sqlite3
import os
from datetime import datetime

DB_PATH = 'training_center.db'

def init_db():
    """إنشاء قاعدة البيانات وجداولها إذا لم تكن موجودة."""
    if os.path.exists(DB_PATH):
        return  # لا تعيد الإنشاء إذا وُجدت
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # جدول المستخدمين (للأمان)
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL  -- 'admin', 'manager', 'user'
        )
    ''')
    
    # إضافة مستخدم افتراضي (admin: password)
    from utils.security import hash_password
    cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                   ('admin', hash_password('password'), 'admin'))
    
    # جدول المتربصين
    cursor.execute('''
        CREATE TABLE trainees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            specialty TEXT,  -- التخصص
            photo_path TEXT,  -- مسار الصورة
            batch_id INTEGER,  -- رقم الفوج
            join_date DATE,
            FOREIGN KEY (batch_id) REFERENCES batches(id)
        )
    ''')
    
    # جدول الأفواج (للترقية)
    cursor.execute('''
        CREATE TABLE batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,  -- اسم الفوج
            period TEXT  -- السداسي الحالي
        )
    ''')
    
    # جدول الغيابات
    cursor.execute('''
        CREATE TABLE absences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trainee_id INTEGER NOT NULL,
            date DATE NOT NULL,
            session_type TEXT,  -- 'full_day' أو 'session'
            reason TEXT,  -- سبب الغياب
            justification_path TEXT,  -- مسار الشهادة
            FOREIGN KEY (trainee_id) REFERENCES trainees(id)
        )
    ''')
    
    # جدول الوثائق
    cursor.execute('''
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trainee_id INTEGER NOT NULL,
            doc_type TEXT NOT NULL,  -- 'id', 'certificate', etc.
            file_path TEXT NOT NULL,
            upload_date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (trainee_id) REFERENCES trainees(id)
        )
    ''')
    
    # جدول جداول الحصص
    cursor.execute('''
        CREATE TABLE schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT NOT NULL,  -- 'الاثنين', etc.
            time_slot TEXT,  -- '08:00-10:00'
            subject TEXT,
            batch_id INTEGER,
            FOREIGN KEY (batch_id) REFERENCES batches(id)
        )
    ''')
    
    # جدول الترقيات
    cursor.execute('''
        CREATE TABLE promotions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER NOT NULL,
            from_period TEXT,
            to_period TEXT,
            minutes_path TEXT,  -- مسار محضر الترقية PDF
            date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (batch_id) REFERENCES batches(id)
        )
    ''')
    
    # جدول الإجراءات التأديبية
    cursor.execute('''
        CREATE TABLE disciplinary_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trainee_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,  -- 'warning', 'reprimand', 'council'
            date DATE DEFAULT CURRENT_DATE,
            description TEXT,
            pdf_path TEXT,  -- مسار المحضر PDF
            FOREIGN KEY (trainee_id) REFERENCES trainees(id)
        )
    ''')
    
    # جدول سجل النشاطات
    cursor.execute('''
        CREATE TABLE activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # جدول المراكز (للتوسع المستقبلي)
    cursor.execute('''
        CREATE TABLE centers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT
        )
    ''')
    # إضافة مركز افتراضي
    cursor.execute("INSERT INTO centers (name, location) VALUES (?, ?)", ('مركز التكوين الرئيسي', 'الجزائر'))
    
    conn.commit()
    conn.close()
    print("تم إنشاء قاعدة البيانات بنجاح.")

def get_connection():
    """الحصول على اتصال بالقاعدة."""
    return sqlite3.connect(DB_PATH)
