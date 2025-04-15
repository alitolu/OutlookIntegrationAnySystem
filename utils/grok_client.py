import requests
from typing import Dict, Optional, List  # List eklendi
import urllib3
import ssl
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

class TLSAdapter(HTTPAdapter):
    """Legacy sunucular için özel TLS adaptörü"""
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

class GrokAIClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://api.x.ai/v1"  # x.ai API endpoint'i
        self.headers = {
            "Authorization": f"Bearer {api_key}" if api_key else None,
            "Content-Type": "application/json"
        }
        
        # SSL uyarılarını kapat
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Custom TLS ayarları ile session oluştur
        self.session = requests.Session()
        adapter = TLSAdapter()
        self.session.mount("https://", adapter)
        self.session.verify = False
        self.session.trust_env = False

    def analyze_text(self, content: str) -> Dict:
        """Metin analizi yap"""
        try:
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "messages": [
                        {
                            "role": "system",
                            "content": "Mail içeriğinden AWB numaralarını, fatura numaralarını ve diğer referans bilgilerini çıkar."
                        },
                        {
                            "role": "user",
                            "content": content
                        }
                    ],
                    "model": "grok-2-latest",
                    "stream": False,
                    "temperature": 0
                },
                verify=False
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                'confidence': 0.9 if result.get('choices') else 0.0,
                'entities': self._parse_entities(result),
                'context': {'text_length': len(content)}
            }
            
        except Exception as e:
            print(f"X.ai analiz hatası: {str(e)}")
            return {}

    def extract_references(self, text: str) -> Dict:
        """Referans numaralarını çıkar"""
        try:
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "messages": [
                        {
                            "role": "system",
                            "content": "Mail içeriğinden referans bilgilerini JSON formatında çıkar: {awb: [], invoice: [], declaration: [], reference: []}"
                        },
                        {
                            "role": "user",
                            "content": text
                        }
                    ],
                    "model": "grok-2-latest",
                    "stream": False,
                    "temperature": 0
                },
                verify=False
            )
            response.raise_for_status()
            result = response.json()
            
            return self._parse_references(result)
            
        except Exception as e:
            print(f"X.ai referans hatası: {str(e)}")
            return {"awb": [], "invoice": [], "declaration": [], "reference": []}

    def _parse_entities(self, result: Dict) -> List:
        """AI yanıtından entity'leri çıkar"""
        entities = []
        if result.get('choices'):
            content = result['choices'][0]['message']['content']
            # JSON formatına çevir ve parse et
            try:
                import json
                data = json.loads(content)
                if isinstance(data, dict):
                    entities = data.get('entities', [])
            except:
                pass
        return entities

    def _parse_references(self, result: Dict) -> Dict:
        """AI yanıtından referansları çıkar"""
        refs = {
            "awb": [],
            "invoice": [],
            "declaration": [],
            "reference": []
        }
        
        if result.get('choices'):
            content = result['choices'][0]['message']['content']
            try:
                import json
                data = json.loads(content)
                if isinstance(data, dict):
                    refs.update(data)
            except:
                pass
                
        return refs

    def __del__(self):
        """Session'ı kapat"""
        if hasattr(self, 'session'):
            self.session.close()
