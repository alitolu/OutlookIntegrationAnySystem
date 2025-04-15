class MailAnalyzer:
    def __init__(self):
        self.enabled = False
        print("Mail analiz özellikleri devre dışı")

    def analyze_mail_thread(self, mails):
        """Mail analizini yap"""
        return {
            'thread_summary': 'AI analizi devre dışı',
            'detected_issues': [],
            'status_changes': [],
            'key_events': []
        }
        
    def predict_awbs(self, content):
        """Basit AWB tahmini"""
        return []
        
    def detect_anomalies(self, content):
        """Anomali tespiti - basit versiyon"""
        return []
        
    def summarize_content(self, content):
        """İçerik özeti - basit versiyon"""
        if isinstance(content, dict):
            return content.get('body', '')[:200] + "..."
        return str(content)[:200] + "..."
