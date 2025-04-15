import json
import zlib
import os
import shutil
from datetime import datetime, timedelta

class CacheManager:
    def __init__(self,  config=None):
        
        self.config = config  # Config parametresi eklendi
   
        self.cache_file = self.config.get("cache", {}).get("path")
        self.max_size_mb = 100
        self.cache_dir = "cache"
        self.cleanup_threshold = 0.9  # 90% doluluk temizlik başlatır
        
        # Cache dizinini oluştur
        os.makedirs(self.cache_dir, exist_ok=True)

    def load_cache(self):
        """Cache'den veri yükle"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    
                    # Sıkıştırılmış içerikleri aç
                    for mail in cache_data.get("mails", []):
                        if isinstance(mail.get("body"), str) and mail["body"].startswith("compressed:"):
                            compressed = bytes.fromhex(mail["body"][11:])  # "compressed:" prefixi çıkar
                            mail["body"] = zlib.decompress(compressed).decode('utf-8')
                    
                    return cache_data
            return {"mails": [], "last_refresh": None}
        except Exception as e:
            print(f"Cache okuma hatası: {str(e)}")
            return {"mails": [], "last_refresh": None}
            
    def save_cache(self, data, config):
        """Cache'e veri kaydet"""
        try:
            # Cache boyut kontrolü
            self.check_cache_size()
            
            # Mail sayısı sınırlaması
            max_mails = config.get("cache", {}).get("max_mails", 1000)
            if len(data["mails"]) > max_mails:
                data["mails"] = data["mails"][:max_mails]
            
            # İçerikleri sıkıştır
            for mail in data["mails"]:
                if isinstance(mail.get("body"), str):
                    compressed = zlib.compress(mail["body"].encode())
                    mail["body"] = f"compressed:{compressed.hex()}"
            
            data["last_refresh"] = datetime.now().isoformat()
            
            # Geçici dosyaya yaz
            temp_file = f"{self.cache_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            # Asıl dosyayı güvenli şekilde değiştir    
            shutil.move(temp_file, self.cache_file)
            
            return True
        except Exception as e:
            print(f"Cache kaydetme hatası: {str(e)}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False
            
    def check_cache_size(self):
        """Cache boyutunu kontrol et ve gerekirse temizle"""
        try:
            total_size = 0
            for root, dirs, files in os.walk(self.cache_dir):
                total_size += sum(os.path.getsize(os.path.join(root, name)) 
                                for name in files)
                                
            # MB'a çevir
            total_size_mb = total_size / (1024 * 1024)
            
            # Eşik değeri aşıldıysa temizlik yap
            if total_size_mb > (self.max_size_mb * self.cleanup_threshold):
                self.cleanup_cache()
                
        except Exception as e:
            print(f"Cache boyut kontrolü hatası: {str(e)}")
            
    def cleanup_cache(self):
        """Eski cache dosyalarını temizle"""
        try:
            # 7 günden eski dosyaları sil
            cutoff = datetime.now() - timedelta(days=7)
            
            for file in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, file)
                if os.path.isfile(file_path):
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if mtime < cutoff:
                        os.remove(file_path)
                        
        except Exception as e:
            print(f"Cache temizleme hatası: {str(e)}")
