from PyQt6.QtCore import QThread, pyqtSignal

class SearchWorker(QThread):
    progress = pyqtSignal(int)  # İlerleme sinyali
    finished = pyqtSignal(dict)  # Sonuç sinyali
    
    def __init__(self, mail_content, search_func):
        super().__init__()
        self.mail_content = mail_content
        self.search_func = search_func
        
    def run(self):
        try:
            # Mail verilerini hazırla
            text_content = self.mail_content.get('body', '') if isinstance(self.mail_content, dict) else str(self.mail_content)
            mail_data = {
                "subject": self.mail_content.get('subject', ''),
                "body": text_content,
                "attachments": self.mail_content.get('attachments', [])
            }
            
            # İlerleme bildirimi
            self.progress.emit(30)
            
            # AWB arama
            awb_results = self.search_func(mail_data)
            
            # İlerleme bildirimi
            self.progress.emit(70)
            
            # Sonuçları ilet
            self.finished.emit({
                'awb_results': awb_results
            })
            
        except Exception as e:
            print(f"Arama hatası: {str(e)}")
            self.finished.emit({})
