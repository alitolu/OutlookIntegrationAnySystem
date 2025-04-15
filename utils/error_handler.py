from typing import Optional, Dict, Any
import traceback
from datetime import datetime

class ErrorHandler:
    def __init__(self):
        self.logger = None
        self.error_counts = {}
        
    def set_logger(self, logger):
        """Logger'ı ayarla"""
        self.logger = logger
        
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> bool:
        """Hata işleme ve loglama"""
        try:
            error_type = type(error).__name__
            error_msg = str(error)
            stack_trace = traceback.format_exc()
            
            # Hata sayısını artır
            self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
            
            # Hatayı logla
            if self.logger:
                self.logger.error(
                    f"Hata: {error_type}\n"
                    f"Mesaj: {error_msg}\n"
                    f"Bağlam: {context}\n"
                    f"Stack Trace:\n{stack_trace}"
                )
            else:
                print(f"Logger ayarlanmamış! Hata: {error_type} - {error_msg}")
            
            # Kritik hata kontrolü
            if self._is_critical_error(error_type, error_msg):
                if self.logger:
                    self.logger.critical(f"Kritik hata tespit edildi: {error_type}")
                return False
                
            return True
            
        except Exception as e:
            print(f"Hata işleme sırasında hata: {str(e)}")
            return False
            
    def _is_critical_error(self, error_type: str, error_msg: str) -> bool:
        """Kritik hata kontrolü"""
        critical_patterns = [
            "PermissionError",
            "DatabaseError",
            "OutOfMemoryError",
            "SystemError"
        ]
        return any(pattern in error_type for pattern in critical_patterns)
