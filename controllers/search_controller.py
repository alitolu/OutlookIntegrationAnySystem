import json
import re
import threading
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtWidgets import QTableWidgetItem, QProgressDialog
from PyQt6.QtCore import Qt, QThread, pyqtSignal  
import concurrent
from datetime import datetime
from utils.awb_detector import AWBDetector
from utils.pattern_learner import PatternLearner

class SearchWorker(QThread):
    progress = pyqtSignal(int)
    result = pyqtSignal(dict)
    finished = pyqtSignal()

    def __init__(self, search_function, mails):
        super().__init__()
        self.search_function = search_function
        self.mails = mails

    def run(self):
        with ThreadPoolExecutor() as executor:
            futures = []
            batch_size = 10
            total_batches = len(self.mails) // batch_size + 1

            for i in range(0, len(self.mails), batch_size):
                batch = self.mails[i:i + batch_size]
                future = executor.submit(self.search_function, batch)
                futures.append(future)

            completed = 0
            for future in as_completed(futures):
                completed += 1
                self.progress.emit(int((completed / total_batches) * 100))
                results = future.result()
                self.result.emit(results)

        self.finished.emit()

class SearchController:
    def __init__(self, main_window):
        self.main_window = main_window
        self.search_thread = None
        self.awb_detector = AWBDetector(main_window)  # main_window'u geç
        self.pattern_learner = PatternLearner()  # Pattern learner ekle
        self.load_patterns()
        self.search_worker = None
        self.data_source_type = self.main_window.config.get("datasource", {}).get("type", "excel")

    def load_patterns(self):
        """AWB pattern'larını json'dan yükle"""
        try:
            with open("config/awb_patterns.json", "r") as f:
                self.patterns = json.load(f)["patterns"]
        except Exception as e:
            print(f"Pattern yükleme hatası: {str(e)}")
            self.patterns = {}

    def search_completed(self):
        """Arama tamamlandığında"""
        self.main_window.statusBar.showMessage("Arama tamamlandı", 3000)
        self.main_window.progress_dialog.close()

    def _search_worker(self):
        with ThreadPoolExecutor() as executor:
            mails = self.main_window.cache.load_cache()["mails"]
            batch_size = self.main_window.config["search"]["batch_size"]
            
            # Mailleri batch'lere böl
            batches = [mails[i:i + batch_size] 
                      for i in range(0, len(mails), batch_size)]
            
            # Her batch için paralel arama
            futures = [executor.submit(self._search_batch, batch) 
                      for batch in batches]
            
            # Sonuçları topla
            results = []
            for future in concurrent.futures.as_completed(futures):
                results.extend(future.result())
                
            # UI güncellemesi
            self.main_window.update_results(results)
    
    def _search_batch(self, mails):
        """Bir batch içindeki maillerde AWB ara"""
        results = []
        seen_awbs = set()
        
        for mail in mails:
            text_to_search = f"{mail['body']} {mail['subject']}"
            detected_awbs = self.awb_detector.find_all_awbs(text_to_search)
            
            for awb_info in detected_awbs:
                # Pattern'dan min_confidence değerini al
                airline = awb_info['airline']
                pattern_data = self.awb_detector.patterns["patterns"].get(airline, {})
                min_confidence = pattern_data.get("min_confidence", 0.7)
                
                if awb_info['confidence'] >= min_confidence:
                    normalized_awb, airline = self.awb_normalizer.normalize_awb(
                        awb_info['awb'], 
                        pattern_data
                    )
                    is_valid = self.awb_validator.validate_and_normalize(normalized_awb)
                    
                    if is_valid and normalized_awb not in seen_awbs:
                        seen_awbs.add(normalized_awb)
                        results.append({
                            "awb": normalized_awb,
                            "airline": airline,
                            "confidence": awb_info['confidence'],
                            "context": awb_info['context'],
                            "matched_text": awb_info['match_text'],
                            "line_number": awb_info['line_number'],
                            "date": mail["date"],
                            "subject": mail["subject"]
                        })
                        
        return sorted(results, key=lambda x: x['confidence'], reverse=True)
        
    def update_ui(self, results):
        """UI'da sonuçları göster"""
        table = self.main_window.results_panel.results_table
        table.setRowCount(0)
        
        for row, result in enumerate(results):
            table.insertRow(row)
            excel_data = self.main_window.excel.find_awb(result["awb"])
            
            items = [
                excel_data.get("poz_no", ""),        # Poz No
                excel_data.get("status", ""),        # Statü
                result["awb"],                       # Aranan AWB
                excel_data.get("awb_text", ""),      # Excel'deki AWB
                result["subject"],                   # Mail Konusu
                result["date"]                       # Tarih
            ]
            
            for col, text in enumerate(items):
                table.setItem(row, col, QTableWidgetItem(str(text)))


