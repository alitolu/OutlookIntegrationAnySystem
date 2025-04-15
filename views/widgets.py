from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, 
                           QTreeWidgetItem, QPushButton, QLabel, QTableWidget,
                           QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, 
                           QMessageBox, QStatusBar, QProgressDialog, QDateTimeEdit, 
                           QGroupBox, QCheckBox, QRadioButton, QButtonGroup, QMenu,
                           QApplication, QSplitter) 
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QIcon 
from views.dialogs import MailPreviewDialog, AWBSelectionDialog  # AWBSelectionDialog eklendi
from utils.search_worker import SearchWorker
from utils.data_source_factory import DataSourceFactory
from utils.attachment_processor import AttachmentProcessor

class SearchButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)

class SearchThread(QThread):
    finished = pyqtSignal(object)
    
    def __init__(self, mail_content, search_function):
        super().__init__()
        self.mail_content = mail_content
        self.search_function = search_function
        
    def run(self):
        try:
            result = self.search_function(self.mail_content)
            self.finished.emit({"awb_results": result})
        except Exception as e:
            print(f"Arama thread hatası: {str(e)}")
            self.finished.emit({"awb_results": []})

class MailPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.current_folder = None  
        self.data_source = DataSourceFactory.create_data_source(self.main_window.config)
        self.init_ui()
        self.setup_table_events()  
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Outlook Klasör ve Mail bölümü için yatay düzen
        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sol taraf - Outlook Klasör Ağacı
        folder_widget = QWidget()
        folder_layout = QVBoxLayout(folder_widget)
        folder_widget.setMaximumWidth(200)  # Maksimum genişlik
        folder_widget.setMinimumWidth(150)  # Minimum genişlik
        
        folder_label = QLabel("Outlook Klasörleri")
        folder_layout.addWidget(folder_label)
        
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabels(["Klasörler"])
        self.folder_tree.itemClicked.connect(self.on_folder_selected)
        folder_layout.addWidget(self.folder_tree)
        
        # Klasörleri yükle butonu
        refresh_folders_btn = QPushButton("Klasörleri Yenile")
        refresh_folders_btn.clicked.connect(self.load_outlook_folders)
        folder_layout.addWidget(refresh_folders_btn)
        
        h_splitter.addWidget(folder_widget)
        
        # Sağ taraf - Mevcut mail tablosu ve diğer elemanlar
        mail_widget = QWidget()
        mail_layout = QVBoxLayout(mail_widget)
        
        # Arama paneli ekle
        search_panel = QHBoxLayout()
        
        # Sadece arama kutusu
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Mail içeriğinde ara...")
        self.search_input.textChanged.connect(self.filter_mails)
        search_panel.addWidget(self.search_input)
        
        # AI Analiz butonu kaldırıldı
        
        mail_layout.addLayout(search_panel)

        # Mail tablosu kolonları - dinamik yapı
        self.mail_table = QTableWidget()
        
        # Başlangıç kolonları
        base_columns = ["Tarih", "Konu", "Gönderen"]
        visible_columns = base_columns.copy()
        
        # Config'den Excel kolonlarını al
        column_mappings = self.main_window.config.get("datasource", {}).get("column_mappings", {})
        for col_name, details in column_mappings.items():
            if details.get("visible", True):
                visible_columns.append(details["display_name"])
                
        # İşlem kolonu en sona ekle
        visible_columns.append("İşlem")
        
        # Tabloyu oluştur
        self.mail_table.setColumnCount(len(visible_columns))
        self.mail_table.setHorizontalHeaderLabels(visible_columns)
        
        # Kolon genişliklerini ayarla
        header = self.mail_table.horizontalHeader()
        
        # Tüm kolonlar için Interactive mod
        for col in range(self.mail_table.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        
        # Başlangıç genişlikleri
        self.mail_table.setColumnWidth(0, 120)  # Tarih
        self.mail_table.setColumnWidth(1, 300)  # Konu
        self.mail_table.setColumnWidth(2, 150)  # Gönderen
        
        # Minimum genişlikler
        header.setMinimumSectionSize(80)  # En düşük genişlik
        
        # Tablo genel ayarları
        self.mail_table.setMinimumWidth(800)  # Minimum tablo genişliği
        self.mail_table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        mail_layout.addWidget(self.mail_table)
        
        # Filtreler
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Outlook Mailleri"))
        
        # Filtre butonları
        filter_layout = QHBoxLayout()
        for text, filter_type in [("Tümü", "all"), ("Günlük", "daily"), ("Haftalık", "weekly"), ("Aylık", "monthly")]:
            btn = QPushButton(text)
            btn.clicked.connect(lambda c, t=filter_type: self.main_window.apply_filter(t))
            filter_layout.addWidget(btn)
        
        refresh_btn = QPushButton("Yenile")
        refresh_btn.clicked.connect(self.main_window.load_emails)
        filter_layout.addWidget(refresh_btn)
        
        mail_layout.addLayout(header_layout)
        mail_layout.addLayout(filter_layout)
        
        h_splitter.addWidget(mail_widget)
        
        # Splitter oranlarını ayarla - sol panel daha dar
        h_splitter.setStretchFactor(0, 1)  # Klasör ağacı - daha dar
        h_splitter.setStretchFactor(1, 3)  # Mail tablosu - daha geniş
        
        # Başlangıç genişliklerini ayarla
        total_width = self.width()
        h_splitter.setSizes([int(total_width * 0.2), int(total_width * 0.8)])
        
        # Ana düzene splitter'ı ekle
        layout.addWidget(h_splitter)
        
    def apply_filter(self, filter_type):
        """Mail filtresini uygula"""
        progress = QProgressDialog("Filtre uygulanıyor...", "İptal", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        try:
            self.main_window.selected_filter = filter_type
            self.load_filtered_emails()
            progress.setValue(100)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Filtre hatası: {str(e)}")
        finally:
            progress.close()
        
    def load_emails(self):
        try:

            self.mail_table.setRowCount(0)
            folder = self.current_folder 
            
            if not folder:
                QMessageBox.warning(self, "Hata", "Klasörü bulunamadı!")
                return

            # Progress dialog oluştur
            progress = QProgressDialog("Mailler yükleniyor...", "İptal", 0, 100, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()

            # Config'i geçerek mailleri al
            mails = self.main_window.outlook.get_mails(folder, self.main_window.config)
            total_mails = len(mails)
            
            for i, mail in enumerate(mails):
                progress.setValue(int((i / total_mails) * 100))
                if progress.wasCanceled():
                    break
                    
                progress.setLabelText(f"Mailler yükleniyor... ({i+1}/{total_mails})")

            # Cache'e kaydet
            if mails:
                self.main_window.cache.save_cache(
                    {"mails": [m.to_dict() for m in mails]}, 
                    self.main_window.config
                )
                self.load_filtered_emails()
                
            progress.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Mail yükleme hatası: {str(e)}")
            
    def show_mail(self, item):
        """Seçili maili göster"""
        date = item.text(0)
        subject = item.text(1)
        
        # Cache'den veya Outlook'tan mail içeriğini al
        mail_content = self.get_mail_content(date, subject)
        if mail_content:
            dialog = MailPreviewDialog(mail_content, self)
            dialog.exec()
            
    def get_mail_content(self, date, subject):
        """Mail içeriğini getir"""
        cache_key = f"{date}_{subject}"
      
        if cache_key in self.main_window.mail_cache:
            return self.main_window.mail_cache[cache_key]
            
        try:
            if self.current_folder:
                messages = self.current_folder.Items
                messages.Sort("[ReceivedTime]", True)
                
                for msg in messages:
                    if (msg.ReceivedTime.strftime("%Y-%m-%d %H:%M") == date and 
                        msg.Subject == subject):

                        content = self.format_mail_content(msg)
                        
                        attachments = []
                        if msg.Attachments.Count > 0:
                            for attachment in msg.Attachments:
                                attachments.append(attachment.FileName)
                        
                        formatted_content = {
                            "subject": subject,
                            "body": content,
                            "attachments": attachments,
                            "outlook_msg": msg  # Orijinal Outlook mesajı buradan geliyor
                        }
                      
                        self.main_window.mail_cache[cache_key] = formatted_content
                        return formatted_content
                        
        except Exception as e:
            print(f"Mail içeriği alma hatası: {str(e)}")
            
        return None

    def format_mail_content(self, msg):
        """Mail içeriğini HTML formatında düzenle"""
        attachments_html = ""
        if msg.Attachments.Count > 0:
            attachments_html = "<p><b>Ekler:</b></p><ul>"
            for i in range(msg.Attachments.Count):
                attachment = msg.Attachments.Item(i+1)
                # Eki tıklanabilir link yap
                attachments_html += f'<li><a href="attachment://{i}">{attachment.FileName}</a></li>'
            attachments_html += "</ul>"
            
        return f"""
        <h3>{msg.Subject}</h3>
        <p><b>Tarih:</b> {msg.ReceivedTime.strftime("%Y-%m-%d %H:%M")}</p>
        <p><b>Kimden:</b> {msg.SenderName}</p>
        <p><b>Kime:</b> {msg.To}</p>
        {attachments_html}
        <hr>
        {msg.HTMLBody if msg.HTMLBody else msg.Body}
        """

    def load_filtered_emails(self):
        """Filtrelenmiş mailleri göster"""
        progress = QProgressDialog("Mailler filtreleniyor...", "İptal", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        try:
            self.mail_table.setRowCount(0)
            cached_mails = self.main_window.cache.load_cache()
            date_range = self.get_date_range()
            
            mail_count = 0
            awb_count = 0
            total_mails = len(cached_mails["mails"])
            
            for i, mail in enumerate(cached_mails["mails"]):
                # Progress güncelle
                progress.setValue(int((i / total_mails) * 100))
                if progress.wasCanceled():
                    break
                    
                # Timezone kontrolü
                msg_date = datetime.fromisoformat(mail["date"]).replace(tzinfo=None)
                if date_range and msg_date < date_range:
                    continue
                    
                row = self.mail_table.rowCount()
                self.mail_table.insertRow(row)
                
                # Mail bilgilerini ekle
                self.mail_table.setItem(row, 0, QTableWidgetItem(msg_date.strftime("%Y-%m-%d %H:%M")))
                self.mail_table.setItem(row, 1, QTableWidgetItem(mail["subject"]))
                self.mail_table.setItem(row, 2, QTableWidgetItem(mail["sender"]))
                
                # Excel kolonları için boş hücreler
                for col in range(3, self.mail_table.columnCount()-1):  # Son kolon hariç
                    self.mail_table.setItem(row, col, QTableWidgetItem(""))
                
                # En son kolona İşlem butonu ekle
                search_btn = QPushButton("Eşleştir")
                search_btn.clicked.connect(lambda checked, r=row: self.search_awb_for_row(r))
                self.mail_table.setCellWidget(row, self.mail_table.columnCount()-1, search_btn)
                
                mail_count += 1
                if self.mail_table.item(row, 3).text():
                    awb_count += 1

                # İşlem detayını göster
                progress.setLabelText(f"Mailler filtreleniyor... ({i+1}/{total_mails})")
                
            # StatusBar güncelle
            if hasattr(self.main_window, 'statusBar'):
                self.main_window.statusBar.update_counts(
                    mail_count=mail_count,
                    awb_count=awb_count,
                    last_update=datetime.now().strftime("%Y-%m-%d %H:%M")
                )

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Filtreleme hatası: {str(e)}")
        finally:
            progress.setValue(100)
            progress.close()

    def get_date_range(self):
        """Seçili filtreye göre tarih aralığı hesapla"""
        now = datetime.now().replace(tzinfo=None)  # Timezone bilgisini kaldır
        filter_type = self.main_window.selected_filter
        
        if filter_type == "daily":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif filter_type == "weekly":
            return (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        elif filter_type == "monthly":
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return None

    def search_awb_for_row(self, row):
        """Seçili satırdaki mail için Eşleşme ara"""
        try:
            # Mail bilgilerini al
            date = self.mail_table.item(row, 0).text()
            subject = self.mail_table.item(row, 1).text()
            
            # Progress dialog
            self.progress = QProgressDialog("Eşleşme aranıyor...", None, 0, 0, self)
            self.progress.setWindowTitle("Arama")
            self.progress.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress.setMinimumDuration(0)  # Hemen göster
            self.progress.setCancelButton(None)  # İptal butonu kaldır
            
            # Mail içeriğini al
            mail_content = self.get_mail_content(date, subject)
            
            if not mail_content:
                self.progress.close()
                return
                
            # Arama thread'ini başlat
            self.search_thread = SearchThread(
                mail_content,
                self.main_window.search_controller.awb_detector.find_all_awbs
            )
            
            # Thread bitince sonuçları işle
            self.search_thread.finished.connect(
                lambda results: self.handle_search_results(row, results)  # results zaten dict formatında
            )
            
            # Progress dialog'u thread bitince kapat
            self.search_thread.finished.connect(self.progress.close)
            
            # Thread'i başlat
            self.search_thread.start()
            
            # Progress dialog'u göster
            self.progress.exec()
            
        except Exception as e:
            print(f"Arama hatası: {str(e)}")
            if hasattr(self, 'progress'):
                self.progress.close()

    def handle_search_results(self, row, results):
        try:
            if hasattr(self, 'progress'):
                self.progress.close()

            awb_results = results.get('awb_results', [])
            if not awb_results:
                self.highlight_row(row, False)
                return
                
            # Birden fazla sonuç varsa seçim dialogunu göster
            if len(awb_results) > 1:
                dialog = AWBSelectionDialog(awb_results, self)
                if dialog.exec():
                    result = dialog.get_selected_match()
                else:
                    return  # Kullanıcı iptal etti
            else:
                result = awb_results[0]  # Tek sonuç varsa direkt al
                
            # Bundan sonrası aynı...
            
            # Excel'de ara
            result_data = self.data_source.find_awb(result["awb"])
            
            # Excel verilerini tabloya ekle
            column_mappings = self.main_window.config.get("datasource", {}).get("column_mappings", {})
            if result_data and column_mappings:
                start_col = 3  # İlk 3 kolon sabit (Tarih, Konu, Gönderen)
                for col_name, details in column_mappings.items():
                    if details.get("visible", True) and start_col < self.mail_table.columnCount()-1:
                        value = result_data.get(col_name, "")
                        item = self.mail_table.item(row, start_col)
                        if item:
                            item.setText(str(value))
                        start_col += 1

            # Eşleşme bilgilerini ekle
            location_col = self.mail_table.columnCount() - 2
            match_col = self.mail_table.columnCount() - 1
            
            # Eşleşen metni kaydet
            self.mail_table.setItem(row, match_col, 
                                  QTableWidgetItem(result.get("match_text", "")))
            
            # Satırı renklendir - Excel'de bulunduysa yeşil, bulunamadıysa turuncu
            self.highlight_row(row, bool(result_data))

        except Exception as e:
            print(f"Sonuç işleme hatası: {str(e)}")
            if hasattr(self, 'progress'):
                self.progress.close()

    def highlight_row(self, row, found: bool):
        """Satır rengini sonuca göre değiştir"""
        # Renk paleti
        colors = {
            'success': {'bg': QColor("#4CAF50"), 'text': QColor("#FFFFFF")},    # Koyu yeşil
            'warning': {'bg': QColor("#FF9800"), 'text': QColor("#FFFFFF")},    # Koyu turuncu
            'error': {'bg': QColor("#F44336"), 'text': QColor("#FFFFFF")},      # Koyu kırmızı
            'default': {'bg': QColor("#FFFFFF"), 'text': QColor("#000000")}     # Beyaz arkaplan, siyah yazı
        }
        
        # Satır durumunu belirle
        if found:
            # Excel kontrolü
            excel_poz = self.mail_table.item(row, 4).text()
            excel_status = self.mail_table.item(row, 5).text()
            if excel_poz or excel_status:  # Excel'de bulundu
                color = colors['success']
            else:  # Excel'de bulunamadı
                color = colors['warning']
        else:  # AWB bulunamadı
            color = colors['error']

        # Satırı renklendir
        for col in range(self.mail_table.columnCount()):
            item = self.mail_table.item(row, col)
            if item:
                item.setBackground(color['bg'])
                item.setForeground(color['text'])  # Yazı rengini beyaz yap

        # Arama butonunu güncelle
        search_btn = self.mail_table.cellWidget(row, 8)
        if search_btn:
            if found:
                search_btn.setText("Yenile")
                search_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        padding: 5px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
            else:
                search_btn.setText("Eşleştir")  # AWB Ara -> Eşleştir
                search_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336;
                        color: white;
                        border: none;
                        padding: 5px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #da190b;
                    }
                """)

    def setup_table_events(self):
        """Tablo event'larını ayarla"""
        # Çift tıklama
        self.mail_table.doubleClicked.connect(self.show_mail_detail)
       
        # Sağ tıklama menüsü
        self.mail_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.mail_table.customContextMenuRequested.connect(self.show_context_menu)

    def show_mail_detail(self, index):
        """Seçili maili göster"""
        row = index.row()
        date = self.mail_table.item(row, 0).text()
        subject = self.mail_table.item(row, 1).text()
        mail_content = self.get_mail_content(date, subject)  # Mail içeriğini al
        if mail_content:
            dialog = MailPreviewDialog(mail_content, self)  # Dialog'u aç
            dialog.exec()

    def show_context_menu(self, position):
        """Sağ tıklama menüsünü göster"""
        menu = QMenu(self)
        row = self.mail_table.indexAt(position).row()
        if row >= 0:
            # Temel menü seçenekleri
            view_action = menu.addAction("Mail Detayını Göster")
            search_action = menu.addAction("Eşleşme Ara")
            
            # AI menüsü
             #ai_menu = menu.addMenu("AI İşlemleri")
             #analyze = ai_menu.addAction("İçerik Analizi")
             #predict = ai_menu.addAction("Eşleşme Tahmin")
             #detect = ai_menu.addAction("Anomali Tespiti")
             #summarize = ai_menu.addAction("Özet Çıkar")
            
            # Yeni menü seçenekleri
            menu.addSeparator()
            search_declaration = menu.addAction("Ekleri de Eşleştir")
            create_declaration = menu.addAction("Eklerden Otomatik Beyanname Oluştur")
            send_to_rep = menu.addAction("İlgili Müşteri Temsilcisine Gönder")
            
            menu.addSeparator()
            copy_awb = menu.addAction("Eşleşme No Kopyala")
            copy_subject = menu.addAction("Konu Kopyala")
            
            # Seçilen aksiyonu işle
            action = menu.exec(self.mail_table.viewport().mapToGlobal(position))
            
            if action == view_action:
                date = self.mail_table.item(row, 0).text()
                subject = self.mail_table.item(row, 1).text()
                mail_content = self.get_mail_content(date, subject)
                if mail_content:
                    dialog = MailPreviewDialog(mail_content, self)
                    dialog.exec()
            elif action == search_action:
                self.search_awb_for_row(row)
            elif action == copy_awb:
                awb = self.mail_table.item(row, 3).text()
                if awb:
                    QApplication.clipboard().setText(awb)
                    self.main_window.statusBar.showMessage("Eşleşme kopyalandı", 2000)
            elif action == copy_subject:
                subject = self.mail_table.item(row, 1).text()
                QApplication.clipboard().setText(subject)
                self.main_window.statusBar.showMessage("Konu kopyalandı", 2000)
            elif action == create_declaration:
                # TODO: Beyanname oluşturma işlemi eklenecek
                QMessageBox.information(self, "Bilgi", "Bu özellik henüz aktif değil")
            elif action == send_to_rep:
                # TODO: Müşteri temsilcisine gönderme işlemi eklenecek
                QMessageBox.information(self, "Bilgi", "Bu özellik henüz aktif değil")
            elif action == search_declaration:
                self.search_attachments(row)  # Yeni metodu çağır

    def filter_mails(self, text):
        """Mail tablosunda arama yap"""
        search_text = text.lower()
        search_fields = self.main_window.config.get("datasource", {}).get("mail_search_fields", {})
        
        for row in range(self.mail_table.rowCount()):
            should_show = False
            
            if search_fields.get("subject", {}).get("searchable"):
                subject = self.mail_table.item(row, 1).text().lower()
                if search_text in subject:
                    should_show = True
                    
            
            self.mail_table.setRowHidden(row, not should_show)
        
    def get_selected_mail_content(self, row):
        """Seçili mailin içeriğini al"""
        date = self.mail_table.item(row, 0).text()
        subject = self.mail_table.item(row, 1).text()
        return self.get_mail_content(date, subject)

    def show_predictions_dialog(self, predictions):
        """Eşleşme tahminlerini gösteren dialog"""
        message = "Bulunan Eşleşme Tahminleri:\n\n"
        for pred in predictions:
            message += f"Eşleşme: {pred['awb']}\n"
            message += f"Güven Skoru: {pred.get('confidence', 0):.2%}\n"
            message += f"Eşleşen Metin: {pred.get('match_text', '')}\n"
            message += f"Konum: {pred.get('location', 'Mail İçeriği')}\n"
            message += "-" * 40 + "\n"
        QMessageBox.information(
            self,
            "AWB Tahminleri",
            message if predictions else "AWB bulunamadı"
        )

    def apply_config(self):
        """Konfigürasyon değişikliklerini uygula"""
        # Tablo kolonlarını güncelle
        visible_columns = ["Tarih", "Konu", "Gönderen"] 
        columns = self.main_window.config.get("datasource", {}).get("column_mappings", {})
       
        for col_name, details in columns.items():
            if details.get("visible", True):
                visible_columns.append(details["display_name"])
                
        visible_columns.append("İşlem") 
        
       
        self.mail_table.setColumnCount(len(visible_columns))
        self.mail_table.setHorizontalHeaderLabels(visible_columns)
        
        header = self.mail_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        
        self.load_filtered_emails()

    def apply_column_settings(self):
        """Kolon ayarlarını uygula"""
        try:
           
            base_columns = ["Tarih", "Konu", "Gönderen"]
            visible_columns = base_columns.copy()
            
           
            mappings = self.main_window.config.get("datasource", {}).get("column_mappings", {})
            for col_name, details in mappings.items():
                if details.get("visible", True):
                    visible_columns.append(details["display_name"])
         
            visible_columns.append("İşlem")
           
            self.mail_table.setColumnCount(len(visible_columns))
            self.mail_table.setHorizontalHeaderLabels(visible_columns)
            
            header = self.mail_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            self.reorganize_table_data(base_columns, visible_columns)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kolon ayarları uygulanırken hata: {str(e)}")

    def reorganize_table_data(self, base_columns, new_columns):
        """Tablo verilerini yeni kolon yapısına göre düzenle"""
        try:
            temp_data = []
            for row in range(self.mail_table.rowCount()):
                row_data = {}
                for col in range(self.mail_table.columnCount()):
                    header = self.mail_table.horizontalHeaderItem(col).text()
                    item = self.mail_table.item(row, col)
                    if item:
                        row_data[header] = item.text()
                temp_data.append(row_data)
            
            # Tabloyu temizle
            self.mail_table.setRowCount(0)
            
            for row_data in temp_data:
                row = self.mail_table.rowCount()
                self.mail_table.insertRow(row)
                
                for col, header in enumerate(new_columns):
                    if header in base_columns:
                        text = row_data.get(header, "")
                        self.mail_table.setItem(row, col, QTableWidgetItem(text))
                    elif header != "İşlem":
                        text = row_data.get(header, "")
                        self.mail_table.setItem(row, col, QTableWidgetItem(text))
                if "İşlem" in new_columns:
                    search_btn = QPushButton("Eşleştir")
                    search_btn.clicked.connect(lambda checked, r=row: self.search_awb_for_row(r))
                    self.mail_table.setCellWidget(row, new_columns.index("İşlem"), search_btn)
                    
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Tablo yeniden düzenlenirken hata: {str(e)}")

    def load_outlook_folders(self):
        """Outlook klasörlerini yükle"""
        try:
            self.folder_tree.clear()

            
            root_folders = self.main_window.outlook.get_root_folder()
            if not root_folders:
                print("Outlook klasörleri alınamadı!")
                return
            
            inbox_item = QTreeWidgetItem(self.folder_tree)
            inbox_item.setText(0, "Gelen Kutusu")
            inbox_item.setData(0, Qt.ItemDataRole.UserRole, root_folders["inbox"].EntryID)
            
            self._load_subfolder(root_folders["inbox"], inbox_item)
            
            sent_item = QTreeWidgetItem(self.folder_tree)
            sent_item.setText(0, "Gönderilmiş Öğeler")
            sent_item.setData(0, Qt.ItemDataRole.UserRole, root_folders["sent"].EntryID)
            
            self.folder_tree.expandAll()
            
        except Exception as e:
            print(f"Klasör yükleme hatası: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Klasörler yüklenirken hata: {str(e)}")

    def _load_subfolder(self, outlook_folder, parent_item):
        """Alt klasörleri recursive olarak yükle"""
        try:
           
            for folder in outlook_folder.Folders:
                try:
                    
                    folder_item = QTreeWidgetItem(parent_item)
                    folder_item.setText(0, folder.Name)
                    folder_item.setData(0, Qt.ItemDataRole.UserRole, folder.EntryID)
                    
                    if folder.Folders.Count > 0:
                        self._load_subfolder(folder, folder_item)
                        
                except Exception as folder_error:
                    print(f"Alt klasör yükleme hatası ({folder.Name}): {str(folder_error)}")
                    continue
                    
        except Exception as e:
            print(f"Alt klasör yükleme genel hatası: {str(e)}")
            
    def on_folder_selected(self, item):
        """Klasör seçildiğinde mailleri yükle"""
        try:
            folder_id = item.data(0, Qt.ItemDataRole.UserRole)
            folder = self.main_window.outlook.get_folder_by_id(folder_id)
            
            if folder:
                self.current_folder = folder  
                self.load_emails()
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Mailler yüklenirken hata: {str(e)}")

    def search_attachments(self, row):
        """Mail eklerini tarayıp eşleştir"""
        try:
            # Mail bilgilerini al
            date = self.mail_table.item(row, 0).text()
            subject = self.mail_table.item(row, 1).text()
            mail_content = self.get_mail_content(date, subject)  # İki parametre ile çağır
            
            if not mail_content:
                return

            # Outlook mesaj nesnesinden ekleri al
            outlook_msg = mail_content.get('outlook_msg')

            # OCR kontrolü
            ocr_enabled = self.main_window.config.get("ocr", {}).get("enabled", False)
            if not ocr_enabled:
                QMessageBox.warning(self, "Uyarı", "OCR özelliği kapalı. Ayarlardan etkinleştirin.")
                return

            # Progress dialog
            progress = QProgressDialog("Ekler analiz ediliyor...", None, 0, outlook_msg.Attachments.Count, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()

            # AttachmentProcessor kullan
            processor = AttachmentProcessor(self.main_window.config)
            all_results = []

            for i in range(outlook_msg.Attachments.Count):
                attachment = outlook_msg.Attachments.Item(i+1)
                progress.setValue(i)
                
                # Eki işle
                result = processor.process_attachment(attachment)
                if result and result.get('content'):
                    # Mail içeriği formatını oluştur
                    attachment_content = {
                        "subject": f"Ek: {result['filename']}",
                        "body": result['content'],
                        "attachments": [],
                        "outlook_msg": outlook_msg
                    }
                    
                    # Ekin içeriğinde AWB ara
                    self.search_thread = SearchThread(
                        attachment_content,
                        self.main_window.search_controller.awb_detector.find_all_awbs
                    )
                    
                    # Thread bitince sonuçları işle
                    self.search_thread.finished.connect(
                        lambda results: self.handle_search_results(row, results)
                    )
                    
                    # Progress dialog'u thread bitince kapat
                    self.search_thread.finished.connect(progress.close)
                    
                    # Thread'i başlat
                    self.search_thread.start()
                    
                    # Progress dialog'u göster
                    progress.exec()

            progress.close()

        except Exception as e:
            print(f"Ek analiz hatası: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Ekler analiz edilirken hata: {str(e)}")
    
class ResultsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
   
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Başlık ve arama alanı
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Sonuçlar"))
        
        # Arama ve filtre araçları
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ara...")
        self.search_input.textChanged.connect(self.filter_results)
        search_layout.addWidget(self.search_input)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)  
        self.results_table.setHorizontalHeaderLabels([
            "Poz No", "Statü", "Aranan",
            "Kaynak", "Mail Konusu", "Tarih",
            "Bulunduğu Yer", "Maildeki Metin"  
        ])
        
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  
        
        layout.addLayout(header_layout)
        layout.addLayout(search_layout)
        layout.addWidget(self.results_table)

    # Sadece gerekli metodları bırak
    def filter_results(self):
        try:
            search_text = self.search_input.text().lower()
            airline_filter = self.airline_filter.currentText()
            
            for row in range(self.results_table.rowCount()):
                should_show = True
                awb = self.results_table.item(row, 2).text().lower()
                
                if search_text and search_text not in awb:
                    should_show = False
                    
                self.results_table.setRowHidden(row, not should_show)
                
        except Exception as e:
            print(f"Filtreleme hatası: {str(e)}")

    def search_with_progress(self):
        self.main_window.search_controller.search_awb()

    def export_to_excel(self):
        """Sonuçları Excel dosyasına aktar"""
        try:
            import pandas as pd
            from PyQt6.QtWidgets import QFileDialog

            path, _ = QFileDialog.getSaveFileName(self, "Excel Dosyası Kaydet", "", "Excel Files (*.xlsx)")
            if not path:
                return

            data = []
            for row in range(self.results_table.rowCount()):
                row_data = []
                for column in range(self.results_table.columnCount()):
                    item = self.results_table.item(row, column)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            df = pd.DataFrame(data, columns=[
                "Poz No", "Statü", "Aranan",
                "Kaynak", "Mail Konusu", "Tarih",
                "Bulunduğu Yer", "Eşleşen Metin"  # Yeni kolon
            ])
            df.to_excel(path, index=False)
            QMessageBox.information(self, "Başarılı", "Sonuçlar başarıyla kaydedildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Excel'e aktarma hatası: {str(e)}")

class StatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.init_labels()
        
    def init_labels(self):
        self.mail_count_label = QLabel("Toplam Mail: 0")
        self.awb_count_label = QLabel("Eşleşme Sayısı: 0")
        self.last_update_label = QLabel("Son Güncelleme: -")
        
        self.addWidget(self.mail_count_label)
        self.addWidget(QLabel("|"))
        self.addWidget(self.awb_count_label)
        self.addWidget(QLabel("|"))
        self.addWidget(self.last_update_label)
        
    def update_counts(self, mail_count, awb_count, last_update):
        self.mail_count_label.setText(f"Toplam Mail: {mail_count}")
        self.awb_count_label.setText(f"Eşleşme Sayısı: {awb_count}")
        self.last_update_label.setText(f"Son Güncelleme: {last_update}")




