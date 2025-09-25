# scanner.py
import pyinsane2

def scan_document():
    """مسح وثيقة (يحفظ كصورة أو PDF)."""
    try:
        scanner = pyinsane2.Scanner()  # اكتشاف scanner
        image = scanner.scan()  # مسح
        file_path = f'documents/scanned_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        os.makedirs('documents', exist_ok=True)
        image.save(file_path)
        return file_path
    except Exception as e:
        print(f"خطأ في المسح: {e}")
        return None
