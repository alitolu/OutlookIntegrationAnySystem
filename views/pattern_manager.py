from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QLineEdit, QPushButton, QCheckBox, 
                           QSpinBox, QLabel, QTableWidget,
                           QTableWidgetItem, QMessageBox)  # Add QMessageBox
from .pattern_edit_dialog import PatternEditDialog  # Add this import

import json

class PatternManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pattern Yönetimi")
        self.setup_ui()
        self.load_patterns()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Pattern Tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Tip", "Prefix", "Örnek Format", 
            "Ayraç İzin", "Min. Güven", "Aktif", "Düzenle"
        ])
        layout.addWidget(self.table)
        
        # Yeni Pattern Ekleme
        add_layout = QHBoxLayout()
        self.add_btn = QPushButton("Yeni Pattern Ekle")
        self.add_btn.clicked.connect(self.add_pattern)
        add_layout.addWidget(self.add_btn)
        layout.addLayout(add_layout)
        
        self.setLayout(layout)
        
    def load_patterns(self):
        """Pattern'ları JSON'dan yükle"""
        try:
            with open("config/awb_patterns.json", "r", encoding='utf-8') as f:
                self.patterns = json.load(f)
                print(f"Loaded patterns: {self.patterns}")  # Debug için
                self.refresh_table()
        except Exception as e:
            print(f"Pattern yükleme hatası: {str(e)}")
            self.patterns = {"patterns": {}}
            
    def save_patterns(self):
        """Pattern'ları JSON dosyasına kaydet"""
        try:
            with open("config/awb_patterns.json", "w", encoding='utf-8') as f:
                json.dump(self.patterns, f, indent=4, ensure_ascii=False)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Kaydetme Hatası",
                f"Pattern'lar kaydedilirken hata oluştu:\n{str(e)}"
            )
            
    def refresh_table(self):
        """Pattern tablosunu json'dan güncelle"""
        self.table.setRowCount(0)
        
        if not self.patterns or "patterns" not in self.patterns:
            print("Pattern verisi bulunamadı!")
            return
            
        for airline, data in self.patterns["patterns"].items():
            try:
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # Debug için pattern verilerini yazdır
                print(f"Loading pattern: {airline}")
                print(f"Data: {data}")
                
                # Tablo kolonlarını doldur
                self.table.setItem(row, 0, QTableWidgetItem(airline))
                self.table.setItem(row, 1, QTableWidgetItem(str(data.get("prefix", ""))))
                self.table.setItem(row, 2, QTableWidgetItem(", ".join(data.get("format_examples", []))))
                self.table.setItem(row, 3, QTableWidgetItem(str(data.get("separator_allowed", False))))
                self.table.setItem(row, 4, QTableWidgetItem(str(data.get("min_confidence", 0.7))))
                self.table.setItem(row, 5, QTableWidgetItem(str(data.get("enabled", True))))
                
                # Düzenle butonu
                edit_btn = QPushButton("Düzenle")
                edit_btn.clicked.connect(lambda checked, a=airline: self.edit_pattern(a))
                self.table.setCellWidget(row, 6, edit_btn)
                
            except Exception as e:
                print(f"Satır {row} yüklenirken hata: {str(e)}")
                continue

    def edit_pattern(self, airline):
        """Pattern düzenleme dialogunu aç"""
        # Mevcut pattern verilerini al
        pattern_data = self.patterns["patterns"].get(airline, {}).copy()
        pattern_data["airline"] = airline  # Airline adını ekle
        
        # Pattern düzenleme dialogunu aç
        dialog = PatternEditDialog(self, pattern_data=pattern_data)
        
        if dialog.exec():
            # Dialog kapandığında yeni verileri kaydet
            new_pattern = dialog.get_pattern()
            new_pattern["enabled"] = self.patterns["patterns"][airline].get("enabled", True)
            
            # Mevcut patterns dizisini koru
            if "patterns" in self.patterns["patterns"][airline]:
                new_pattern["patterns"] = self.patterns["patterns"][airline]["patterns"]
                
            self.patterns["patterns"][airline] = new_pattern
            self.save_patterns()
            self.refresh_table()
            
    def add_pattern(self):
        dialog = PatternEditDialog(self)
        if dialog.exec():
            pattern = dialog.get_pattern()
            self.patterns["patterns"][pattern["airline"]] = pattern
            self.save_patterns()
            self.refresh_table()
