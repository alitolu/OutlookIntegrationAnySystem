import datetime
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QMessageBox, QFileDialog)
from PyQt6.QtGui import QAction, QIcon
import pandas as pd

from utils.ai_analyzer import AIAnalyzer
from utils.mail_analyzer import MailAnalyzer
from utils.mssql_helper import MSSQLHelper
from .pattern_manager import PatternManagerDialog
from .widgets import MailPanel, StatusBar 
from utils.outlook_helper import OutlookHelper
from utils.excel_helper import ExcelHelper
from utils.cache_manager import CacheManager
from controllers.search_controller import SearchController
from utils.config_manager import ConfigManager 
from .data_source_editor import DataSourceEditor  
from utils.data_source_factory import DataSourceFactory

class AWBSearchApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mail Tarama Sistemi")
        self.setGeometry(100, 100, 1200, 800)
        
        # Config yönetimi
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config  # settings.json'dan yüklüyor
        
        # Veri kaynağını oluştur
        self.data_source = DataSourceFactory.create_data_source(self.config)
        
        # Önbellekler için değişkenler
        self.mail_cache = {}
        self.cached_mails = {"mails": [], "last_refresh": None}
        # Status bar'ı diğer panellerden önce oluştur
        self.statusBar = StatusBar(self)
        self.setStatusBar(self.statusBar)
        
        # Yardımcı sınıfları başlat
        self.outlook = OutlookHelper()
        # Excel helper'a dosya yolunu gönder

        excel_file = self.config.get("datasource", {}).get("excel_file", "data/_main.xlsx")
        self.excel = ExcelHelper(excel_file, self.config) 
        self.cache = CacheManager(self.config)
        self.search_controller = SearchController(self)
        
        # Menü barını oluştur
        self.create_menu_bar()
        
        # Başlangıçta temp_ocr klasörünü temizle
        self.clear_temp_ocr()
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget) 
        
        # Sadece mail paneli oluştur
        self.mail_panel = MailPanel(self)
        layout.addWidget(self.mail_panel)

        # Toolbar
        toolbar = self.addToolBar("Araçlar")
        toolbar.setMovable(False)
        
    def apply_filter(self, filter_type):
        self.mail_panel.apply_filter(filter_type)
        
    def load_emails(self):
        self.mail_panel.load_emails()
        
    def show_mail(self, item):
        self.mail_panel.show_mail(item)
        
    def update_results(self, results):
        """Sonuçları mail tablosuna ekle"""
        mappings = self.config.get("datasource", {}).get("column_mappings", {})
        
        for result in results:
            # Mail tablosunda ilgili satırı bul
            for row in range(self.mail_panel.mail_table.rowCount()):
                date_item = self.mail_panel.mail_table.item(row, 0)
                subject_item = self.mail_panel.mail_table.item(row, 1)
                
                if (date_item.text() == result['date'] and 
                    subject_item.text() == result['subject']):
                    # Sonuçları satıra ekle
                    excel_data = self.excel.find_awb(result['awb'])
                    for excel_col, details in mappings.items():
                        if details.get("visible", True):
                            col_index = details.get("index", 0)
                            value = excel_data.get(excel_col, "")
                            self.mail_panel.mail_table.item(row, col_index).setText(value)
                            
                    # Satırı renklendir
                    self.mail_panel.highlight_row(row, bool(excel_data))
                    break

    def closeEvent(self, event):
        """Program kapatılırken temizlik"""
        try:
            # Config kaydet
            self.config_manager.save_config()
            
            # Cache kaydet - config parametresi eklendi
            if self.cached_mails:
                self.cache.save_cache(self.cached_mails, self.config)
                
        except Exception as e:
            print(f"Kapanış hatası: {str(e)}")
            
        super().closeEvent(event)

    def create_menu_bar(self):
        """Menü barını oluştur"""
        menubar = self.menuBar()
        
        # Dosya menüsü
        file_menu = menubar.addMenu("Dosya")
        refresh_action = file_menu.addAction("Mailleri Yenile")
        refresh_action.triggered.connect(self.load_emails)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Çıkış")
        exit_action.triggered.connect(self.close)
        
        # Rapor menüsü
        report_menu = menubar.addMenu("Rapor")
        export_action = report_menu.addAction("Excel'e Aktar")
        export_action.triggered.connect(self.export_results)
        
        # Araçlar menüsü
        tools_menu = menubar.addMenu("Araçlar")
        pattern_manager_action = QAction("Pattern Yönetimi", self)
        pattern_manager_action.triggered.connect(self.show_pattern_manager)
        tools_menu.addAction(pattern_manager_action)

        # Veri Kaynağı menüsü
        data_menu = menubar.addMenu("Veri Kaynağı")
        data_source_action = QAction("Kaynak Düzenle", self)
        data_source_action.triggered.connect(self.show_data_source_editor)
        data_menu.addAction(data_source_action)

        # AI menüsü (sadece ayarlar)
        ai_menu = menubar.addMenu("AI")
        ai_settings_action = ai_menu.addAction("AI Ayarları")
        ai_settings_action.triggered.connect(self.show_ai_settings)

    def export_results(self):
        """Mail tablosundaki sonuçları Excel'e aktar"""
        try:
            data = []
            for row in range(self.mail_panel.mail_table.rowCount()):
                row_data = []
                for col in range(self.mail_panel.mail_table.columnCount() - 1):  # Son sütun hariç (Ara butonu)
                    item = self.mail_panel.mail_table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            df = pd.DataFrame(data, columns=[
                "Tarih", "Konu", "Gönderen", 
                "Eşleşme No", "Excel Poz No", "Excel Statü",
                "Bulunduğu Yer", "Eşleşme Sonuç"
            ])
            
            path, _ = QFileDialog.getSaveFileName(
                self, 
                "Excel Dosyası Kaydet",
                f"Eşleşme_Rapor_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                "Excel Files (*.xlsx)"
            )
            
            if path:
                df.to_excel(path, index=False)
                QMessageBox.information(self, "Başarılı", "Rapor başarıyla kaydedildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Excel aktarma hatası: {str(e)}")

    def show_pattern_manager(self):
        dialog = PatternManagerDialog(self)
        dialog.exec()
        
    def analyze_selected_mail(self):
        """Seçili maili AI ile analiz et"""
        if hasattr(self, 'mail_analyzer'):
            item = self.mail_panel.mail_tree.currentItem()
            if item:
                date = item.text(0)
                subject = item.text(1)
                content = self.mail_panel.get_mail_content(date, subject)
                
                if content:
                    analysis = self.mail_analyzer.analyze_mail_thread([{
                        'date': date,
                        'subject': subject,
                        'body': content
                    }])
                    
                    self.show_analysis_results(analysis)

    def predict_awbs(self):
        """Seçili maildeki olası Eşleşme'leri tahmin et"""
        try:
            # Seçili maili al
            item = self.mail_panel.mail_tree.currentItem()
            if not item:
                QMessageBox.warning(self, "Uyarı", "Lütfen bir mail seçin!")
                return
                
            date = item.text(0)
            subject = item.text(1)
            content = self.mail_panel.get_mail_content(date, subject)
            
            if content:
                # AI ile tahmin yap
                predictions = self.mail_analyzer.predict_awbs(content)
                
                # Sonuçları göster
                result_text = "Bulunan Olası Eşleşme'ler:\n\n"
                for pred in predictions:
                    result_text += f"Eşleşme: {pred['awb']}\n"
                    result_text += f"Güven: {pred['confidence']:.1%}\n"
                    result_text += f"Bağlam: {pred['context']}\n\n"
                
                QMessageBox.information(
                    self,
                    "Eşleşme Tahminleri",
                    result_text if predictions else "Olası Eşleşme bulunamadı!"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Eşleşme tahmini hatası: {str(e)}")

    def detect_anomalies(self):
        """Seçili mailde anormal durumları tespit et"""
        try:
            item = self.mail_panel.mail_tree.currentItem()
            if not item:
                QMessageBox.warning(self, "Uyarı", "Lütfen bir mail seçin!")
                return
                
            date = item.text(0)
            subject = item.text(1)
            content = self.mail_panel.get_mail_content(date, subject)
            
            if content:
                anomalies = self.mail_analyzer.detect_anomalies(content)
                QMessageBox.information(
                    self,
                    "Anomali Tespiti",
                    f"Tespit Edilen Anomaliler:\n\n{chr(10).join(anomalies)}" if anomalies
                    else "Anormal durum tespit edilmedi."
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Anomali tespiti hatası: {str(e)}")

    def show_analysis_results(self, analysis):
        """Mail analiz sonuçlarını göster"""
        try:
            # Sonuç metnini hazırla
            result_text = "Mail Analiz Sonuçları\n\n"
            
            # Özet
            result_text += "ÖZET:\n"
            result_text += f"{analysis.get('thread_summary', 'Özet yok')}\n\n"
            
            # Tespit edilen sorunlar
            if analysis.get('detected_issues'):
                result_text += "SORUNLAR:\n"
                for issue in analysis['detected_issues']:
                    result_text += f"- {issue}\n"
                result_text += "\n"
            
            # Durum değişiklikleri
            if analysis.get('status_changes'):
                result_text += "DURUM DEĞİŞİKLİKLERİ:\n"
                for change in analysis['status_changes']:
                    result_text += f"- {change['date']}: {change.get('from_status', 'Başlangıç')} -> {change['to_status']}\n"
                result_text += "\n"
            
            # Önemli olaylar
            if analysis.get('key_events'):
                result_text += "ÖNEMLİ OLAYLAR:\n"
                for event in analysis['key_events']:
                    result_text += f"- {event['date']}: {event['description']}\n"
            
            # Sonuçları göster
            QMessageBox.information(
                self,
                "Mail Analizi",
                result_text,
                QMessageBox.StandardButton.Ok
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Analiz Hatası",
                f"Analiz sonuçları gösterilirken hata oluştu:\n{str(e)}"
            )

    def show_data_source_editor(self):
        """Veri Kaynağı Editörünü göster"""
        try:
            dialog = DataSourceEditor(self)
            if dialog.exec():
                # Config değişti, Excel ayarlarını yeniden yükle
                excel_file = self.config.get("datasource", {}).get("excel_file", "rapor.xlsx")
                # Config parametresini ekle
                self.excel = ExcelHelper(excel_file, self.config)  # config parametresi eklendi
                self.excel.data = self.excel.load_data()
                
                # Mail tablosunu güncelle
                self.mail_panel.load_filtered_emails()
                
                self.statusBar.showMessage("Veri kaynağı ayarları güncellendi", 3000)
        except Exception as e:
            print(f"Veri kaynağı editörü hata detayı: {str(e)}")  # Hata log'u detaylandırıldı
            QMessageBox.critical(self, "Hata", f"Veri kaynağı editörü hatası: {str(e)}")

    def show_ai_settings(self):
        from views.ai_settings_dialog import AISettingsDialog
        dialog = AISettingsDialog(self.config, self)
        if dialog.exec():
            self.apply_config_changes()

    def apply_config_changes(self):
        """Konfigürasyon değişikliklerini uygula"""
        try:
            # Config'i kaydet
            self.config_manager.save_config()
            
            # Grok AI istemcisini güncelle
            if self.search_controller and self.search_controller.awb_detector:
                self.search_controller.awb_detector.grok_client = None
                if self.config.get("grok", {}).get("enabled", False):
                    from utils.grok_client import GrokAIClient
                    self.search_controller.awb_detector.grok_client = GrokAIClient(
                        self.config.get("grok", {}).get("api_key")
                    )
            
            # Mail panelini güncelle
            if hasattr(self, 'mail_panel'):
                self.mail_panel.apply_config()
                
            # Status bar'ı güncelle
            self.statusBar.showMessage("Ayarlar güncellendi", 3000)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ayarlar güncellenirken hata: {str(e)}")

    def clear_temp_ocr(self):
        """temp_ocr klasörünü temizle"""
        try:
            temp_dir = os.path.join(os.path.dirname(__file__), "..", "temp_ocr")
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        print(f"Dosya silme hatası ({file}): {str(e)}")
        except Exception as e:
            print(f"temp_ocr temizleme hatası: {str(e)}")

