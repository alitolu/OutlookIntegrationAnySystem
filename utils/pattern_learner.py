import json
import re
from typing import Dict, List
from collections import defaultdict

class PatternLearner:
    def __init__(self, pattern_file="config/awb_patterns.json"):
        self.pattern_file = pattern_file
        self.load_patterns()
        self.learned_patterns = defaultdict(int)
        
    def load_patterns(self):
        """Pattern'ları yükle"""
        try:
            with open(self.pattern_file, 'r', encoding='utf-8') as f:
                self.patterns = json.load(f)
        except Exception as e:
            print(f"Pattern yükleme hatası: {str(e)}")
            self.patterns = {"patterns": {}}

    def learn_from_text(self, text: str, context: Dict = None):
        """Metinden yeni pattern'lar öğren"""
        try:
            known_patterns = []
            
            # Mail içeriğinde AWB bul
            for airline, data in self.patterns["patterns"].items():
                for pattern in data.get("patterns", []):
                    matches = list(re.finditer(pattern, text, re.IGNORECASE))
                    for match in matches:
                        # Match objesinin start ve end pozisyonlarını kullan
                        start_pos = match.start()
                        end_pos = match.end()
                        
                        # Öncesi ve sonrası için context al
                        pre_text = text[max(0, start_pos-50):start_pos]
                        post_text = text[end_pos:min(len(text), end_pos+50)]
                        
                        known_patterns.append({
                            "pattern": pattern,
                            "match": match.group(),
                            "airline": airline,
                            "pre_text": pre_text,
                            "post_text": post_text
                        })
            
            # Her pattern için analiz yap
            for known in known_patterns:
                self._analyze_context(
                    known["pre_text"], 
                    known["post_text"], 
                    known
                )
                
            # Öğrenilen pattern'ları kaydet
            if len(self.learned_patterns) > 0:
                self.save_learned_patterns()
                
        except Exception as e:
            print(f"Pattern öğrenme hatası: {str(e)}")
            
    def _analyze_context(self, pre_text: str, post_text: str, known: Dict):
        """Pattern kontekstini analiz et"""
        # Önceki metinde tekrar eden yapıları bul
        pre_patterns = re.findall(r'\b\w+\b', pre_text)
        pre_special = re.findall(r'[^\w\s]', pre_text)
        
        # Sonraki metinde tekrar eden yapıları bul
        post_patterns = re.findall(r'\b\w+\b', post_text)
        post_special = re.findall(r'[^\w\s]', post_text)
        
        # Pattern oluştur ve skorla
        pattern = self._create_pattern(known["match"], pre_patterns[-3:], post_patterns[:3])
        self.learned_patterns[pattern] += 1

    def _create_pattern(self, match: str, pre: List[str], post: List[str]) -> str:
        """Yeni pattern oluştur"""
        
        # HTML ve CSS etiketlerini filtrele
        def filter_html_css(words):
            html_css = {'span', 'div', 'p', 'b', 'h3', 'color', 'serif', 'black', 'none', 
                       'mso', 'ligatures', 'Subject'}
            return [w for w in words if w.lower() not in html_css]
        
        pre = filter_html_css(pre)
        post = filter_html_css(post)
        
        pattern = ""
        # AWB formatı için özel kontrol
        if re.match(r'^\d{3}-?\d{8}$', match):
            prefix = match[:3]
            pattern = f"{prefix}[-\\s]*(\\d{{4}}[\\s-]?\\d{{4}})"
        else:
            # Genel pattern
            if pre:
                pattern += f"(?:{'|'.join(pre)})\\s*"
            digits = len(re.findall(r'\d', match))
            pattern += f"\\d{{{digits}}}"
            if post:
                pattern += f"\\s*(?:{'|'.join(post)})"
            
        return pattern

    def save_learned_patterns(self):
        """Öğrenilen pattern'ları kaydet"""
        try:
            min_occurrences = 3
            
            # Sadece belirli formattaki pattern'ları kabul et
            valid_patterns = {}
            for pattern, count in self.learned_patterns.items():
                if (count >= min_occurrences and 
                    not re.search(r'(?:span|div|p|b|h3|color|serif|black|none|mso|ligatures|Subject)', pattern)):
                    valid_patterns[pattern] = count
            
            # Her airline için pattern'ları güncelle
            for airline in self.patterns["patterns"]:
                base_patterns = self.patterns["patterns"][airline]["patterns"][:2]  # İlk 2 pattern'ı koru
                self.patterns["patterns"][airline]["patterns"] = base_patterns
            
            # Kaydet
            with open(self.pattern_file, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            print(f"Pattern kaydetme hatası: {str(e)}")
