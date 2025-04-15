from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QFileDialog, QTreeWidget,
                           QTreeWidgetItem, QCheckBox, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt
import json
import os
from utils.mssql_helper import MSSQLHelper

class DataSourceEditor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.config = self.main_window.config
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Veri Kaynağı Ayarları")
        self.setMinimumWidth(600)
        layout = QVBoxLayout(self)
        
        # Veri kaynağı tipi seçimi
        self.source_type = QComboBox()
        self.source_type.addItems(["Excel", "MSSQL"])
        self.source_type.currentTextChanged.connect(self.on_source_changed)
        layout.addWidget(QLabel("Veri Kaynağı Tipi:"))
        layout.addWidget(self.source_type)
        
        # Excel dosyası seçimi
        self.excel_layout = QHBoxLayout()
        self.excel_path = QLineEdit(self.config.get("datasource", {}).get("excel_file", ""))
        browse_btn = QPushButton("Gözat...")
        browse_btn.clicked.connect(self.browse_excel)
        self.excel_layout.addWidget(QLabel("Excel Dosyası:"))
        self.excel_layout.addWidget(self.excel_path)
        self.excel_layout.addWidget(browse_btn)
        layout.addLayout(self.excel_layout)
        
        # MSSQL ayarları
        self.mssql_layout = QVBoxLayout()
        self.server_input = QLineEdit()
        self.db_input = QLineEdit()
        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.mssql_layout.addWidget(QLabel("Sunucu:"))
        self.mssql_layout.addWidget(self.server_input)
        self.mssql_layout.addWidget(QLabel("Veritabanı:"))
        self.mssql_layout.addWidget(self.db_input)
        self.mssql_layout.addWidget(QLabel("Kullanıcı Adı:"))
        self.mssql_layout.addWidget(self.user_input)
        self.mssql_layout.addWidget(QLabel("Şifre:"))
        self.mssql_layout.addWidget(self.pass_input)
        
        # MSSQL arama kolonu seçimi için ComboBox ekle
        self.mssql_layout.addWidget(QLabel("Arama Kolonu:"))
        self.search_column_input = QComboBox()
        self.mssql_layout.addWidget(self.search_column_input)
        
        # Tablo adı seçimi
        self.mssql_layout.addWidget(QLabel("Tablo Adı:"))
        self.table_input = QLineEdit()
        self.table_input.setText(self.config.get("datasource", {}).get("mssql", {}).get("table", ""))
        self.mssql_layout.addWidget(self.table_input)
        
        # Kolonları getir butonu
        self.get_columns_btn = QPushButton("Kolonları Getir")
        self.get_columns_btn.clicked.connect(self.get_mssql_columns)
        self.mssql_layout.addWidget(self.get_columns_btn)
        
        self.test_btn = QPushButton("Bağlantıyı Test Et")
        self.test_btn.clicked.connect(self.test_connection)
        self.mssql_layout.addWidget(self.test_btn)
        
        layout.addLayout(self.mssql_layout)
        
        # Kolon ayarları ağacı
        layout.addWidget(QLabel("Kolon Ayarları:"))
        self.column_tree = QTreeWidget()
        self.column_tree.setHeaderLabels(["Kolon Adı", "Görünen Ad", "Görünür", "Aranabilir"])
        self.load_columns()
        layout.addWidget(self.column_tree)
        
        # Mail arama ayarları
        layout.addWidget(QLabel("Mail Arama Ayarları:"))
        self.mail_search_tree = QTreeWidget()
        self.mail_search_tree.setHeaderLabels(["Alan", "Görünen Ad", "Aranabilir"])
        self.load_mail_search_fields()
        layout.addWidget(self.mail_search_tree)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        # Varsayılan veri kaynağı tipini ayarla
        current_type = self.config.get("datasource", {}).get("type", "excel")
        index = self.source_type.findText(current_type.upper())
        if index >= 0:
            self.source_type.setCurrentIndex(index)
            
        # Excel yolu varsa yükle
        excel_file = self.config.get("datasource", {}).get("excel_file", "")
        self.excel_path.setText(excel_file)
        
        # MSSQL ayarlarını yükle
        mssql_config = self.config.get("datasource", {}).get("mssql", {})
        self.server_input.setText(mssql_config.get("server", ""))
        self.db_input.setText(mssql_config.get("database", ""))
        self.user_input.setText(mssql_config.get("username", ""))
        self.pass_input.setText(mssql_config.get("password", ""))
        
        # Başlangıçta doğru paneli göster
        self.on_source_changed(current_type.upper())
        
    def browse_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Excel Dosyası Seç", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.excel_path.setText(file_path)
            
    def load_columns(self):
        column_mappings = self.config.get("datasource", {}).get("column_mappings", {})
        for col_name, details in column_mappings.items():
            item = QTreeWidgetItem(self.column_tree)
            item.setText(0, col_name)
            item.setText(1, details.get("display_name", col_name))
            
            # Görünürlük checkbox
            visible_cb = QCheckBox()
            visible_cb.setChecked(details.get("visible", True))
            self.column_tree.setItemWidget(item, 2, visible_cb)
            
            # Aranabilir checkbox
            searchable_cb = QCheckBox()
            searchable_cb.setChecked(details.get("searchable", False))
            self.column_tree.setItemWidget(item, 3, searchable_cb)
            
    def load_mail_search_fields(self):
        search_fields = self.config.get("datasource", {}).get("mail_search_fields", {})
        for field, details in search_fields.items():
            item = QTreeWidgetItem(self.mail_search_tree)
            item.setText(0, field)
            item.setText(1, details.get("display_name", field))
            
            # Aranabilir checkbox
            searchable_cb = QCheckBox()
            searchable_cb.setChecked(details.get("searchable", True))
            self.mail_search_tree.setItemWidget(item, 2, searchable_cb)
            
    def save_settings(self):
        try:
            if self.source_type.currentText() == "MSSQL":
                # MSSQL ayarlarını kaydet
                self.config["datasource"]["type"] = "mssql"
                self.config["datasource"]["mssql"] = {
                    "server": self.server_input.text(),
                    "database": self.db_input.text(),
                    "username": self.user_input.text(),
                    "password": self.pass_input.text(),
                    "table": self.table_input.text(),
                    "search_column": self.search_column_input.currentText()
                }
            else:
                # Excel ayarlarını kaydet
                self.config["datasource"]["type"] = "excel"
                self.config["datasource"]["excel_file"] = self.excel_path.text()

            # Kolon ayarları
            column_mappings = {}
            root = self.column_tree.invisibleRootItem()
            for i in range(root.childCount()):
                item = root.child(i)
                column_mappings[item.text(0)] = {
                    "display_name": item.text(1),
                    "visible": self.column_tree.itemWidget(item, 2).isChecked(),
                    "searchable": self.column_tree.itemWidget(item, 3).isChecked()
                }
            self.config["datasource"]["column_mappings"] = column_mappings
            
            # Mail arama ayarları
            mail_search_fields = {}
            root = self.mail_search_tree.invisibleRootItem()
            for i in range(root.childCount()):
                item = root.child(i)
                mail_search_fields[item.text(0)] = {
                    "display_name": item.text(1),
                    "searchable": self.mail_search_tree.itemWidget(item, 2).isChecked()
                }
            self.config["datasource"]["mail_search_fields"] = mail_search_fields
            
            # Ana pencereye değişiklikleri uygula
            self.main_window.apply_config_changes()
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ayarlar kaydedilemedi: {str(e)}")
            
    def on_source_changed(self, source_type):
        if source_type == "Excel":
            self.excel_layout.setEnabled(True)
            self.mssql_layout.setEnabled(False)
        elif source_type == "MSSQL":
            self.excel_layout.setEnabled(False)
            self.mssql_layout.setEnabled(True)
            
    def test_connection(self):
        """MSSQL bağlantısını test et"""
        if self.source_type.currentText() == "MSSQL":
            try:
                if not all([
                    self.server_input.text().strip(),
                    self.db_input.text().strip(),
                    self.user_input.text().strip(),
                    self.pass_input.text().strip()
                ]):
                    QMessageBox.warning(self, "Uyarı", "Lütfen tüm bağlantı bilgilerini doldurun!")
                    return
                
                helper = MSSQLHelper({
                    "datasource": {
                        "mssql": {
                            "server": self.server_input.text().strip(),
                            "database": self.db_input.text().strip(),
                            "username": self.user_input.text().strip(),
                            "password": self.pass_input.text().strip(),
                            "table": self.table_input.text().strip() if self.table_input.text().strip() else None,
                            "search_column": self.search_column_input.currentText() if self.search_column_input.currentText() else None
                        }
                    }
                })
                
                if helper.test_connection():
                    QMessageBox.information(self, "Başarılı", "MSSQL bağlantısı başarılı!")
                else:
                    QMessageBox.critical(self, "Hata", "MSSQL bağlantısı başarısız! Lütfen bağlantı bilgilerini kontrol edin.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Bağlantı hatası: {str(e)}")
                
    def get_mssql_columns(self):
        """MSSQL tablosundan kolonları çek"""
        try:
            if not self.table_input.text().strip():
                QMessageBox.warning(self, "Uyarı", "Lütfen bir tablo adı girin!")
                return

            print("MSSQL Helper oluşturuluyor...")
            helper = MSSQLHelper({
                "datasource": {
                    "mssql": {
                        "server": self.server_input.text().strip(),
                        "database": self.db_input.text().strip(),
                        "username": self.user_input.text().strip(),
                        "password": self.pass_input.text().strip(),
                        "table": self.table_input.text().strip()
                    }
                }
            })
            
            print("Kolonlar getiriliyor...")
            columns = helper.get_mssql_columns(self.table_input.text().strip())
            
            if not columns:
                QMessageBox.warning(self, "Uyarı", f"'{self.table_input.text()}' tablosunda kolon bulunamadı!")
                return
                
            print(f"Bulunan kolonlar: {columns}")
            
            # ComboBox'ı doldur
            self.search_column_input.clear()
            self.search_column_input.addItems(columns)
            
            # Mevcut search_column varsa seç
            current_search = self.config.get("datasource", {}).get("mssql", {}).get("search_column", "")
            index = self.search_column_input.findText(current_search)
            if index >= 0:
                self.search_column_input.setCurrentIndex(index)
                
            QMessageBox.information(self, "Başarılı", f"{len(columns)} kolon başarıyla getirildi!")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kolonlar alınırken hata: {str(e)}")
            print(f"Detaylı hata: {str(e)}")
