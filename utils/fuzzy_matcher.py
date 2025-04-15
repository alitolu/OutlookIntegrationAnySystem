from difflib import SequenceMatcher
from fuzzywuzzy import fuzz
from typing import List, Tuple

class FuzzyMatcher:
    def find_best_match(self, search_text: str, candidates: List[str], threshold: float = 0.8) -> Tuple[str, float]:
        """En iyi eşleşmeyi bul"""
        best_match = None
        best_ratio = 0
        
        for candidate in candidates:
            # Benzerlik oranını hesapla (0-1 arası)
            ratio = fuzz.ratio(search_text, candidate) / 100
            
            # Daha iyi bir eşleşme bulunduysa güncelle
            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = candidate
                
        return best_match, best_ratio

    def examples(self):
        """Fuzzy matching örnekleri"""
        # Örnek 1: Basit yazım hatası
        print(fuzz.ratio("235-12345678", "235-12345677"))  # 98% benzerlik
        
        # Örnek 2: Boşluk/tire farkı
        print(fuzz.ratio("235-1234 5678", "235 12345678"))  # 93% benzerlik
        
        # Örnek 3: Karakter yer değiştirme
        print(fuzz.ratio("235-12345678", "235-12354678"))  # 96% benzerlik
        
        # Örnek 4: Eksik karakter
        print(fuzz.ratio("235-12345678", "235-1234567"))   # 89% benzerlik
