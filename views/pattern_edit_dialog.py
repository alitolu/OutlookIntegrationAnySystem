import re
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                           QCheckBox, QDoubleSpinBox, QPushButton, QSpinBox,
                           QTextEdit, QLabel, QHBoxLayout)  # Added QHBoxLayout import

class PatternEditDialog(QDialog):
    def __init__(self, parent=None, pattern_data=None):
        super().__init__(parent)
        self.pattern_data = pattern_data or {}
        self.setWindowTitle("Pattern Düzenle")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QFormLayout()
        
        self.airline = QLineEdit()
        layout.addRow("Tip:", self.airline)
        
        # Prefix ( kodu)
        self.prefix = QLineEdit()
        layout.addRow("Prefix (Kodu):", self.prefix)
        
        # Karakter uzunlukları
        self.length = QSpinBox()
        self.length.setRange(8, 100)
        layout.addRow("Toplam Uzunluk:", self.length)
        
        self.prefix_length = QSpinBox()
        self.prefix_length.setRange(0, 10)
        layout.addRow("Prefix Uzunluğu:", self.prefix_length)
        
        # Format örnekleri
        self.format_example = QTextEdit()
        self.format_example.setPlaceholderText("Her satıra bir örnek yazın")
        layout.addRow("Format Örnekleri:", self.format_example)
        
        # Ayraç izni
        self.allow_separator = QCheckBox()
        layout.addRow("Ayraçlara İzin Ver:", self.allow_separator)
        
        # Minimum güven skoru
        self.min_confidence = QDoubleSpinBox()
        self.min_confidence.setRange(0.1, 1.0)
        self.min_confidence.setSingleStep(0.1)
        self.min_confidence.setValue(0.7)
        layout.addRow("Minimum Güven:", self.min_confidence)
        
        # Test alanı
        self.test_input = QLineEdit()
        layout.addRow("Test :", self.test_input)
        
        self.test_btn = QPushButton("Test Et")
        self.test_btn.clicked.connect(self.test_pattern)
        layout.addRow("", self.test_btn)
        
        self.test_result = QLabel()
        layout.addRow("Test Sonucu:", self.test_result)
        
        # Kaydet/İptal
        buttons = QHBoxLayout()
        save_btn = QPushButton("Kaydet")
        cancel_btn = QPushButton("İptal")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow("", buttons)
        
        self.setLayout(layout)
        
        # Mevcut verileri doldur
        if self.pattern_data:
            self.load_pattern_data()
            
    def load_pattern_data(self):
        """Pattern verilerini form alanlarına doldur"""
        if not self.pattern_data:
            return
            
        #  adı - düzenlenemez
        self.airline.setText(self.pattern_data.get("airline", ""))
        self.airline.setEnabled(False)  # Varolan pattern için havayolu değiştirilemez
        
        # Temel bilgiler
        self.prefix.setText(self.pattern_data.get("prefix", ""))
        self.length.setValue(self.pattern_data.get("length", 11))
        self.prefix_length.setValue(self.pattern_data.get("prefix_length", 3))
        
        # Format örnekleri
        examples = self.pattern_data.get("format_examples", [])
        self.format_example.setText("\n".join(examples))
        
        # Ayarlar
        self.allow_separator.setChecked(self.pattern_data.get("separator_allowed", True))
        self.min_confidence.setValue(float(self.pattern_data.get("min_confidence", 0.7)))

    def test_pattern(self):
        """Test AWB'yi kontrol et"""
        test_awb = self.test_input.text()
        pattern = self.get_pattern()
        
        # AWB formatını test et
        is_valid = True
        clean_awb = re.sub(r'[\s-]', '', test_awb)
        
        if len(clean_awb) != pattern["length"]:
            is_valid = False
        elif pattern["prefix"] and not clean_awb.startswith(pattern["prefix"]):
            is_valid = False
            
        self.test_result.setText("Geçerli ✓" if is_valid else "Geçersiz ✗")
        self.test_result.setStyleSheet(
            "color: green" if is_valid else "color: red"
        )
        
    def get_pattern(self):
        """Form verilerini pattern dict'e dönüştür"""
        pattern = {
            "airline": self.airline.text(),
            "prefix": self.prefix.text(),
            "length": self.length.value(),
            "prefix_length": self.prefix_length.value(),
            "format_examples": [x.strip() for x in self.format_example.toPlainText().splitlines() if x.strip()],
            "separator_allowed": self.allow_separator.isChecked(),
            "min_confidence": self.min_confidence.value(),
            "enabled": True
        }
        
        # Eğer mevcut pattern düzenleniyorsa patterns dizisini koru
        if self.pattern_data and "patterns" in self.pattern_data:
            pattern["patterns"] = self.pattern_data["patterns"]
            
        return pattern

    def _generate_pattern(self):
        """Format örneklerine göre regex pattern oluştur"""
        prefix = self.prefix.text()
        remaining_length = self.length.value() - len(prefix)
        separator = "[-\\s]*" if self.allow_separator.isChecked() else ""
        
        if prefix:
            # Prefix'li pattern (örn: 235[-\s]*\d{8})
            return f"{prefix}{separator}\\d{{{remaining_length}}}"
        else:
            # Prefix'siz pattern (örn: \d{10})
            return f"(?<!\\d)\\d{{{self.length.value()}}}(?!\\d)"
