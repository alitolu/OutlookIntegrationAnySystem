from tkinter import messagebox
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QPushButton, 
                           QTextBrowser, QDialogButtonBox, QTabWidget, QWidget, QLabel, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont
import openai
import re
import os
import tempfile

class AIAnalysisDialog(QDialog):
    def __init__(self, analysis_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yapay Zeka Analizi")
        self.setGeometry(200, 200, 600, 400)
        
        layout = QVBoxLayout(self)
        
        self.browser = QTextBrowser()
        self.browser.setHtml(f"""
            <h3>Mail Analizi</h3>
            <p>{analysis_text}</p>
        """)
        layout.addWidget(self.browser)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

class MailPreviewDialog(QDialog):
    def __init__(self, mail_content, parent=None):
        super().__init__(parent)
        self.mail_content = mail_content
        self.outlook_msg = mail_content.get('outlook_msg')  # Outlook mesaj nesnesi
        self.temp_files = []  # Geçici dosyaları takip et
        
        self.setWindowTitle("Mail Detayı")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)
        
        layout = QVBoxLayout(self)
        
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.temp_dir = os.path.join(self.base_dir, "temp_ocr")
        self.cleanup()
        self.attachment_paths = {} 
        
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
            
        # Ekleri temp_ocr'a kaydet
        if self.outlook_msg and self.outlook_msg.Attachments.Count > 0:
            for i in range(self.outlook_msg.Attachments.Count):
                attachment = self.outlook_msg.Attachments.Item(i+1)
                filename = attachment.FileName
                base_name, ext = os.path.splitext(filename)
                
                # Benzersiz dosya adı oluştur
                temp_path = os.path.join(self.temp_dir, filename)
                counter = 1
                while os.path.exists(temp_path):
                    new_name = f"{base_name}_{counter}{ext}"
                    temp_path = os.path.join(self.temp_dir, new_name)
                    counter += 1
                
                # Dosyayı kaydet ve yolunu sakla
                attachment.SaveAsFile(temp_path)
                self.attachment_paths[i] = temp_path
                self.temp_files.append(temp_path)
                
        # HTML içeriğini göster
        self.browser = QTextBrowser()
        self.browser.setHtml(self.format_mail_content())
        self.browser.anchorClicked.connect(self.handle_attachment_click)
        self.browser.setOpenLinks(False)
        
        layout.addWidget(self.browser)
        
    def format_mail_content(self):
        """Mail içeriğini HTML formatında düzenle"""
        attachments_html = ""
        if self.outlook_msg and self.outlook_msg.Attachments.Count > 0:
            attachments_html = "<p><b>Ekler:</b></p><ul>"
            for i in range(self.outlook_msg.Attachments.Count):
                attachment = self.outlook_msg.Attachments.Item(i+1)
                temp_path = self.attachment_paths.get(i, "")
                attachments_html += f'<li><a href="file:///{temp_path}">{attachment.FileName}</a></li>'
            attachments_html += "</ul>"
            
        return f"""
        <h3>{self.outlook_msg.Subject}</h3>
        <p><b>Tarih:</b> {self.outlook_msg.ReceivedTime.strftime("%Y-%m-%d %H:%M")}</p>
        <p><b>Kimden:</b> {self.outlook_msg.SenderName}</p>
        <p><b>Kime:</b> {self.outlook_msg.To}</p>
        {attachments_html}
        <hr>
        {self.outlook_msg.HTMLBody if self.outlook_msg.HTMLBody else self.outlook_msg.Body}
        """

    def handle_attachment_click(self, url):
        """Ek tıklandığında çalışır"""
        if url.scheme() == "file":
            try:
                file_path = url.path().strip('/')
                if os.path.exists(file_path):
                    os.startfile(file_path)
                else:
                    print(f"Dosya bulunamadı: {file_path}")
            except Exception as e:
                print(f"Dosya açma hatası: {str(e)}")

    def keyPressEvent(self, event):
        """ESC tuşuna basılınca dialog'u kapat"""
        if event.key() == Qt.Key.Key_Escape:
            self.cleanup_and_close()
        super().keyPressEvent(event)
            
    def cleanup(self):
        try:
            for temp_file in self.temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception as e:
                    print(f"Dosya silme hatası: {str(e)}")
            self.temp_files.clear()
        except Exception as e:
            print(f"Temizlik hatası: {str(e)}")
      
    def cleanup_and_close(self):
        """Temizlik yap ve kapat"""
        try:
            for temp_file in self.temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception as e:
                    print(f"Dosya silme hatası: {str(e)}")
            self.temp_files.clear()
        except Exception as e:
            print(f"Temizlik hatası: {str(e)}")
        finally:
            self.close()
            
    def closeEvent(self, event):
        """Dialog kapanırken temizlik garantisi"""
        self.cleanup_and_close()
        super().closeEvent(event)

class AWBSelectionDialog(QDialog):
    def __init__(self, matches, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Eşleşme Seçimi")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Açıklama
        layout.addWidget(QLabel("Birden fazla eşleşme bulundu. Lütfen kullanmak istediğiniz eşleşmeyi seçin:"))
        
        # Eşleşme listesi
        self.list_widget = QListWidget()
        for match in matches:
            item = QListWidgetItem(f"""
                Eşleşme No: {match['awb']}
                Metin: {match.get('match_text', '')}
                Konum: {match.get('location', 'Mail İçeriği')}
                Güven: {match.get('confidence', 0):.1%}
            """)
            item.setData(Qt.ItemDataRole.UserRole, match)  # Tüm veriyi sakla
            self.list_widget.addItem(item)
            
        layout.addWidget(self.list_widget)
        
        # Butonlar
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_selected_match(self):
        """Seçilen eşleşmeyi döndür"""
        current = self.list_widget.currentItem()
        if current:
            return current.data(Qt.ItemDataRole.UserRole)
        return None