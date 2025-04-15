from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QCheckBox, QSpinBox, QPushButton,
                           QGroupBox, QFormLayout)

class AISettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("AI Ayarları")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # API Ayarları
        api_group = QGroupBox("API Ayarları")
        api_layout = QFormLayout()
        
        self.enabled = QCheckBox("AI Özelliklerini Aktif Et")
        self.enabled.setChecked(self.config.get("grok", {}).get("enabled", False))
        
        self.api_key = QLineEdit(self.config.get("grok", {}).get("api_key", ""))
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        
        api_layout.addRow(self.enabled)
        api_layout.addRow("API Key:", self.api_key)
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # Analiz Ayarları  
        analysis_group = QGroupBox("Analiz Ayarları")
        analysis_layout = QFormLayout()
        
        self.confidence = QSpinBox()
        self.confidence.setRange(1, 100)
        self.confidence.setValue(int(self.config.get("grok", {}).get("confidence_threshold", 0.7) * 100))
        
        self.context_window = QSpinBox()
        self.context_window.setRange(50, 500)
        self.context_window.setValue(self.config.get("grok", {}).get("context_window", 100))
        
        analysis_layout.addRow("Minimum Güven (%):", self.confidence)
        analysis_layout.addRow("Konteks Penceresi:", self.context_window)
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)
        
        # Cache Ayarları
        cache_group = QGroupBox("Cache Ayarları")
        cache_layout = QFormLayout()
        
        self.cache_enabled = QCheckBox("AI Sonuçlarını Cache'le")
        self.cache_enabled.setChecked(self.config.get("grok", {}).get("cache_results", True))
        
        self.cache_ttl = QSpinBox()
        self.cache_ttl.setRange(1, 24)
        self.cache_ttl.setValue(self.config.get("grok", {}).get("cache_ttl", 3600) // 3600)
        
        cache_layout.addRow(self.cache_enabled)
        cache_layout.addRow("Cache Süresi (saat):", self.cache_ttl)
        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def save_settings(self):
        """Ayarları kaydet"""
        self.config["grok"] = {
            "enabled": self.enabled.isChecked(),
            "api_key": self.api_key.text(),
            "confidence_threshold": self.confidence.value() / 100,
            "context_window": self.context_window.value(),
            "cache_results": self.cache_enabled.isChecked(),
            "cache_ttl": self.cache_ttl.value() * 3600
        }
        self.accept()
