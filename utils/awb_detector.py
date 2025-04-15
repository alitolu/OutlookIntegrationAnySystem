import re
from typing import List, Dict, Tuple
import pandas as pd
import json
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
from utils.pattern_learner import PatternLearner
from utils.grok_client import GrokAIClient
from utils.fuzzy_matcher import FuzzyMatcher

class AWBDetector:
    def __init__(self, main_window=None):
        self.main_window = main_window
        self.pattern_learner = PatternLearner()
        self.load_patterns()
        # Config'den Grok durumunu al
        self.grok_client = None
        if self.main_window and self.main_window.config.get("grok", {}).get("enabled", False):
            self.grok_client = GrokAIClient(
                self.main_window.config.get("grok", {}).get("api_key")
            )
        # Regex pattern'larını compile et
        self._compile_patterns()
        # ThreadPoolExecutor oluştur
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.fuzzy_matcher = FuzzyMatcher()  # Fuzzy matcher instance

    def load_patterns(self):
       
        try:
            with open("config/awb_patterns.json", "r", encoding='utf-8') as f:
                self.patterns = json.load(f)
                #print("Patterns başarıyla yüklendi")
        except UnicodeDecodeError as e:
            print("UTF-8 encoding hatası, json_fixer.py çalıştırılmalı")
            self.patterns = {"patterns": {}}
        except Exception as e:
            print(f"Pattern yükleme hatası: {str(e)}")
            self.patterns = {"patterns": {}}

    def _compile_patterns(self):
        """Regex pattern'larını önceden compile et"""
        self.compiled_patterns = {}
        for airline, data in self.patterns.get("patterns", {}).items():
            if data.get("enabled", True):
                self.compiled_patterns[airline] = [
                    re.compile(pattern, re.IGNORECASE) 
                    for pattern in data.get("patterns", [])
                ]

    @lru_cache(maxsize=1000)
    def _clean_text(self, text: str) -> str:
        """Metni temizle ve normalize et (cache'li)"""
        if not isinstance(text, str):
            return ""
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('–', '-').replace('—', '-')
        return text.strip()

    def find_all_awbs(self, mail_data: dict) -> List[Dict]:
        try:
            if isinstance(mail_data, str):
                mail_data = {
                    "subject": "",
                    "body": mail_data,
                    "attachments": []
                }

          
            results = []
            
            # Paralel arama yap
            futures = []
            texts_to_search = [
                ("subject", mail_data.get("subject", "")),
                ("body", mail_data.get("body", ""))
            ]
            
           
            for location, text in texts_to_search:
                future = self.executor.submit(
                    self._search_text, 
                    text,
                    location
                )
                futures.append(future)

            # Sonuçları topla
            for future in futures:
                results.extend(future.result())

            # Tekrar edenleri kaldır
            unique_results = self._remove_duplicates(results)
            
            # Pattern öğrenme daha sonra eklenecek
            #if unique_results:
                #self.pattern_learner.learn_from_text(
                   # text=mail_data.get("body", ""),
                    #context={"results": unique_results}
                #)
          
            # Grok AI ile analiz
            if not unique_results and self.grok_client:
                grok_results = self.analyze_with_grok(mail_data)
                if grok_results.get("has_potential_awb"):
                    for awb in grok_results["details"]["awb_numbers"]:
                        unique_results.append({
                            "awb": awb,
                            "airline": "UNKNOWN",
                            "match_text": awb,
                            "confidence": grok_results["confidence"],
                            "location": "AI Analiz",
                            "line_number": 0
                        })
            
            return unique_results

        except Exception as e:
            print(f"AWB arama hatası: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []

    def analyze_with_grok(self, mail_data: dict) -> dict:
        """Mail içeriğini x.ai API ile analiz et"""
        try:
            message = f"""
Bu mail içeriğinde AWB numaraları ve diğer referansları analiz et.
Varsa aşağıdaki formatta JSON olarak dön:
{{
    "awb_numbers": ["235-12345678","123-45678901","772238490728"],
    "invoice_numbers": ["INV123","FAT123"],
    "declaration_numbers": ["BYN123","IM123","EX123"],
    "references": ["REF456","REF-123"],
    "context": "ilgili cümle veya paragraf",
    "confidence": 0.95
}}

Mail İçeriği:
Konu: {mail_data.get('subject', '')}
İçerik: {mail_data.get('body', '')}
            """
            
            # Önce analiz yap
            analysis = self.grok_client.analyze_text(message)
            
            # Referansları çıkar
            refs = self.grok_client.extract_references(message)
            
            print(message)
            # Sonuçları birleştir
            combined_results = {
                "analyzed": True,
                "has_potential_awb": bool(refs.get("awb")),
                "confidence": analysis.get("confidence", 0.0),
                "details": {
                    "awb_numbers": refs.get("awb", []),
                    "invoice_numbers": refs.get("invoice", []),
                    "declaration_numbers": refs.get("declaration", []),
                    "references": refs.get("reference", []),
                    "context": analysis.get("context", {}),
                    "entities": analysis.get("entities", [])
                }
            }
            
            # Loglama
            print("\n AI Analiz Sonuçları:")
            print("-" * 50)
            print(f"Mail Konusu: {mail_data.get('subject', '')}")
            print(f"AWB Bulundu: {combined_results['has_potential_awb']}")
            print(f"Güven Skoru: {combined_results['confidence']:.2f}")
            print(f"Bulunan AWB'ler: {', '.join(combined_results['details']['awb_numbers'])}")
            print("-" * 50)
            
            return combined_results
            
        except Exception as e:
            print(f"x.ai analiz hatası: {str(e)}")
            return {"analyzed": False, "error": str(e)}

    def _search_text(self, text: str, location: str = "Mail İçeriği") -> List[Dict]:
        """Metindeki AWB numaralarını tespit eder"""
        try:
            if not text:
                return []
                
            clean_text = self._clean_text(text)
            results = []
            
            for line_number, line in enumerate(clean_text.split('\n'), start=1):
                for airline, patterns in self.compiled_patterns.items():
                    min_confidence = self.patterns["patterns"][airline].get("min_confidence", 0.7)
                    for pattern in patterns:
                        for match in pattern.finditer(line):
                            try:
                                print(match)
                                normalized_awb = self._normalize_awb(match, airline)
                               
                                if self._validate_awb(normalized_awb, airline):
                                    # Önce fuzzy matching yap
                                    matched_text, fuzzy_confidence = self.fuzzy_matcher.find_best_match(
                                        normalized_awb, 
                                        [match.group()],
                                        min_confidence
                                    )

                                    # İlk confidence hesapla
                                    base_confidence = self._calculate_confidence(match.group(), line)
                                    print(f"Geçerli : {normalized_awb} (Base Confidence: {base_confidence})")
                                    
                                    # Eğer fuzzy match yoksa veya düşük güvenilirlikse base confidence kullan
                                    final_confidence = fuzzy_confidence if matched_text else base_confidence
                                    final_match_text = matched_text if matched_text else match.group()

                                    if final_confidence >= min_confidence:
                                        results.append({
                                            "awb": normalized_awb, 
                                            "airline": airline,
                                            "match_text": final_match_text,
                                            "confidence": final_confidence,
                                            "context": self._get_enhanced_context(clean_text, line, match.start(), line_number),
                                            "line_number": line_number,
                                            "location": location
                                        })
                                else:
                                    print(f"❌ Geçersiz AWB: {normalized_awb} (Format Uyuşmuyor)")
                                    
                            except Exception as e:
                                print(f"Eşleşme işleme hatası: {str(e)}")
                                continue
            return results
        except Exception as e:
            print(f"Metin arama hatası: {str(e)}")
            return []

    def _normalize_awb(self, match: re.Match, airline: str) -> str:
        raw_awb = match.group()
        clean_awb = re.sub(r'[\s-]+', '', raw_awb)
       
        if airline == 'DHL':
            if match.lastindex:
                return match.group(1)
            elif len(clean_awb) == 10:
                return clean_awb
        elif airline == 'OZEL':
            return clean_awb
        else:
            if len(clean_awb) >= 11:
                prefix = clean_awb[:3]
                number = clean_awb[3:11]
                return f"{prefix}-{number}"
        return clean_awb

    def _validate_awb(self, awb: str, airline: str) -> bool:
        if not awb:
            return False

        clean_awb = re.sub(r'[-\s/]', '', awb)
        pattern_data = self.patterns["patterns"].get(airline)
        
        if not pattern_data:
            return False
            
        prefix = pattern_data["prefix"]
        length = pattern_data["length"]
      
        if len(clean_awb) != length:
            return False
        
        if prefix:
            if isinstance(prefix, list):
                if not any(clean_awb.startswith(p) for p in prefix):
                    return False
            else:
                if not clean_awb.startswith(prefix):
                    return False
        return True

    def _get_enhanced_context(self, text: str, line: str, pos: int, line_no: int, window: int = 50) -> Dict:
        """Gelişmiş context çıkarma"""
        try:
            # Öncesi ve sonrası için karakter bazlı kesme
            text_before = text[max(0, pos-window):pos]
            text_after = text[pos:min(len(text), pos+window)]
            
            return {
                'before': text_before,
                'current': line,
                'after': text_after,
                'line_number': line_no,
                'position': pos
            }
            
        except Exception as e:
            print(f"Context çıkarma hatası: {str(e)}")
            return {
                'before': '',
                'current': line,
                'after': '',
                'line_number': line_no,
                'position': 0
            }

    def _calculate_confidence(self, text: str, line: str) -> float:
        """AWB tespiti güven skoru hesapla"""
        confidence = 1.0
        
        try:
            # Context bazlı güven artırıcılar
            context_indicators = {
                'awb': 0.3,
                'tracking': 0.2,
                'shipment': 0.2,
                'waybill': 0.2,
                'air cargo': 0.2
            }
            
            for indicator, score in context_indicators.items():
                if re.search(indicator, line, re.IGNORECASE):
                    confidence += score
                    
            # Format bazlı güven artırıcılar
            if re.match(r'^\d{3}-\d{8}$', text):  # Mükemmel format
                confidence += 0.3
                
            return min(confidence, 1.0)  # Max 1.0
            
        except Exception as e:
            print(f"Güven skoru hesaplama hatası: {str(e)}")
            return 0.6  # Varsayılan değer

    def _get_context(self, text: str, pos: int, window: int) -> str:
        """AWB numarasının geçtiği bağlamı al"""
        start = max(0, pos - window)
        end = min(len(text), pos + window)
        return text[start:end].strip()

    def _remove_duplicates(self, results: List[Dict]) -> List[Dict]:
        """Tekrar eden AWB numaralarını temizle"""
        seen = set()
        unique_results = []
        
        for result in results:
            if result["awb"] not in seen:
                seen.add(result["awb"])
                unique_results.append(result)
                
        return unique_results

    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
