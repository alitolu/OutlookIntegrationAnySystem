from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                          QLabel, QProgressBar, QTextEdit, QPushButton,
                          QTreeWidget, QTreeWidgetItem)
from PyQt6.QtCore import Qt, QTimer

class AIAnalysisDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Analiz Sonuçları")
        self.setMinimumSize(800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Progress bar
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        # Tab widget
        tabs = QTabWidget()
        
        # AWB Analiz tab'ı
        awb_tab = QWidget()
        awb_layout = QVBoxLayout(awb_tab)
        self.awb_tree = QTreeWidget()
        self.awb_tree.setHeaderLabels(["Tip", "Numara", "Güven", "Konteks"])
        awb_layout.addWidget(self.awb_tree)
        tabs.addTab(awb_tab, "AWB Analizi")
        
        # Belge Analiz tab'ı
        doc_tab = QWidget()
        doc_layout = QVBoxLayout(doc_tab)
        self.doc_tree = QTreeWidget()
        self.doc_tree.setHeaderLabels(["Alan", "Değer", "Güven"])
        doc_layout.addWidget(self.doc_tree)
        tabs.addTab(doc_tab, "Belge Analizi")
        
        layout.addWidget(tabs)
        
        # Status bar
        self.status_label = QLabel()
        layout.addWidget(self.status_label)

    def update_results(self, results):
        """Analiz sonuçlarını göster"""
        self.awb_tree.clear()
        self.doc_tree.clear()
        
        # AWB sonuçları
        for awb in results.get("awb_numbers", []):
            item = QTreeWidgetItem(self.awb_tree)
            item.setText(0, "AWB")
            item.setText(1, awb["number"])
            item.setText(2, f"{awb['confidence']:.2%}")
            item.setText(3, awb.get("context", ""))

        # Belge analiz sonuçları
        for field, value in results.get("document_analysis", {}).items():
            item = QTreeWidgetItem(self.doc_tree)
            item.setText(0, field)
            item.setText(1, str(value.get("value", "")))
            item.setText(2, f"{value.get('confidence', 0):.2%}")

    def show_error(self, message):
        """Hata mesajını göster"""
        self.status_label.setText(f"Hata: {message}")
        self.status_label.setStyleSheet("color: red")
        QTimer.singleShot(3000, lambda: self.status_label.clear())

    def show_success(self, message):
        """Başarı mesajını göster"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: green")
        QTimer.singleShot(3000, lambda: self.status_label.clear())
