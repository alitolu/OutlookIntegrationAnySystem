import logging
from datetime import datetime
import os

class Logger:
    def __init__(self, log_file="app.log"):
        self.log_file = log_file
        self.setup_logger()
        
    def setup_logger(self):
        logger = logging.getLogger('AWBSearchApp')
        logger.setLevel(logging.INFO)
        
        # Dosya handler
        fh = logging.FileHandler(self.log_file, encoding='utf-8')
        fh.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
        )
        fh.setFormatter(formatter)
        
        logger.addHandler(fh)
        self.logger = logger
        
    def rotate_logs(self, max_size_mb=10):
        """Log dosyasını boyuta göre döndür"""
        try:
            if os.path.exists(self.log_file):
                size_mb = os.path.getsize(self.log_file) / (1024 * 1024)
                if size_mb > max_size_mb:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    backup = f"{self.log_file}.{timestamp}"
                    os.rename(self.log_file, backup)
        except Exception as e:
            print(f"Log döndürme hatası: {str(e)}")
