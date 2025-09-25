# exporter.py
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import openpyxl
from io import BytesIO
from datetime import datetime
import os

# تسجيل خط عربي (افترض وجود 'arial.ttf' أو استخدم خط نظامي)
try:
    pdfmetrics.registerFont(TTFont('Arabic', 'arial.ttf'))  # ضع الخط في مجلد المشروع
except:
    pass  # استخدم خط افتراضي

def export_to_pdf(data, title, filename=None):
    """تصدير بيانات إلى PDF."""
    if filename is None:
        filename = f'reports/{title}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    os.makedirs('reports', exist_ok=True)
    
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    c.setFont('Arabic', 12) if 'Arabic' in pdfmetrics.getRegisteredFontNames() else c.setFont('Helvetica', 12)
    
    # عنوان
    c.drawString(100, height - 50, title)
    
    # بيانات (افترض data كقائمة tuples: (col1, col2, ...))
    y = height - 100
    for row in data:
        c.drawString(100, y, ' | '.join(str(cell) for cell in row))
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50
    
    c.save()
    return filename

def export_to_excel(data, title, filename=None):
    """تصدير بيانات إلى Excel."""
    if filename is None:
        filename = f'reports/{title}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    os.makedirs('reports', exist_ok=True)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title
    
    # عناوين الأعمدة (افترض أول صف في data هو العناوين)
    if data:
        ws.append(data[0])  # عناوين
        for row in data[1:]:
            ws.append(row)
    
    wb.save(filename)
    return filename

def print_report(data, title):
    """طباعة تقرير (باستخدام QPrintDialog في الواجهة)."""
    # هذه الدالة تُستدعى من الواجهة؛ لا تُطبق هنا، بل في reports_window.py
    pass
# utils/exporter.py - تحسين دعم العربية
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit
import openpyxl
from datetime import datetime
import os

# محاولة تسجيل خط عربي
try:
    # جرب البحث عن خطوط عربية شائعة
    arabic_fonts = ['Arial', 'Tahoma', 'Times New Roman', 'Amiri-Regular']
    for font in arabic_fonts:
        try:
            pdfmetrics.registerFont(TTFont('Arabic', f'{font}.ttf'))
            break
        except:
            continue
except:
    print("تحذير: لم يتم العثور على خط عربي. استخدام الخط الافتراضي.")

def export_to_pdf(data, title, filename=None):
    """تصدير بيانات إلى PDF مع دعم أفضل للعربية."""
    if filename is None:
        filename = f'reports/{title}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    os.makedirs('reports', exist_ok=True)
    
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # محاولة استخدام الخط العربي
    try:
        c.setFont('Arabic', 12)
    except:
        c.setFont('Helvetica', 12)
    
    # عنوان التقرير
    c.drawString(50, height - 50, title)
    c.line(50, height - 55, width - 50, height - 55)
    
    # بيانات الجدول
    y = height - 80
    for row_idx, row in enumerate(data):
        x = 50
        for col_idx, cell in enumerate(row):
            cell_text = str(cell)
            # معالجة النص العربي
            try:
                c.drawString(x, y, cell_text)
            except:
                c.drawString(x, y, cell_text.encode('utf-8').decode('latin-1', 'ignore'))
            x += 100  # تباعد الأعمدة
        
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50
            try:
                c.setFont('Arabic', 12)
            except:
                c.setFont('Helvetica', 12)
    
    c.save()
    return filename

def export_to_excel(data, title, filename=None):
    """تصدير بيانات إلى Excel."""
    if filename is None:
        filename = f'reports/{title}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    os.makedirs('reports', exist_ok=True)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title[:31]  # تقليل الطول إذا كان طويلاً
    
    # إضافة البيانات
    for row in data:
        ws.append(row)
    
    wb.save(filename)
    return filename