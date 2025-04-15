import datetime
from PyQt6.QtWidgets import QProgressDialog, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer

class DetailedProgressDialog(QProgressDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setMinimumDuration(0)
        self.setAutoClose(True)
        self.setAutoReset(False)
        
        # Detay widgetı
        details_widget = QWidget(self)
        details_layout = QVBoxLayout(details_widget)
        
        # İlerleme detayları
        self.current_operation = QLabel()
        self.sub_operation = QLabel()
        self.stats_label = QLabel()
        self.eta_label = QLabel()
        
        details_layout.addWidget(self.current_operation)
        details_layout.addWidget(self.sub_operation)
        details_layout.addWidget(self.stats_label)
        details_layout.addWidget(self.eta_label)
        
        # Ana layout'a ekle
        self.setLabel(details_widget)
        
        # İstatistikler
        self.start_time = None
        self.processed_items = 0
        self.total_items = 0
        
        # ETA güncelleme zamanlayıcısı
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_eta)
        
    def start(self, total_items):
        """İlerleme çubuğunu başlat"""
        self.total_items = total_items
        self.processed_items = 0
        self.start_time = datetime.now()
        self.setMaximum(total_items)
        self.setValue(0)
        self.timer.start(1000)  # Her saniye güncelle
        
    def update_progress(self, current_op, sub_op=None, increment=1):
        """İlerlemeyi güncelle"""
        self.processed_items += increment
        self.setValue(self.processed_items)
        
        self.current_operation.setText(f"İşlem: {current_op}")
        if sub_op:
            self.sub_operation.setText(f"Alt İşlem: {sub_op}")
            
        self.stats_label.setText(
            f"İşlenen: {self.processed_items}/{self.total_items} "
            f"({(self.processed_items/self.total_items*100):.1f}%)"
        )
        
    def update_eta(self):
        """Tahmini kalan süreyi güncelle"""
        if self.start_time and self.processed_items > 0:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            items_per_second = self.processed_items / elapsed
            remaining_items = self.total_items - self.processed_items
            eta_seconds = remaining_items / items_per_second
            
            self.eta_label.setText(
                f"Tahmini Kalan Süre: {eta_seconds:.0f} saniye"
            )
