from bs4 import BeautifulSoup
import email
import re
from typing import List, Dict
import os
import zipfile
import pythoncom
from win32com.client import constants

class MailProcessor:
    def __init__(self):
        self.supported_attachments = ['.txt', '.html', '.xml', '.csv', '.pdf']
        self.pdf_reader = None  # PDF işleme için lazy loading
        
    def process_mail(self, msg) -> Dict:
        """Mail ve eklerini işle"""
        content = {
            'body': self._extract_body(msg),
            'attachments': self._process_attachments(msg),
            'thread': self._extract_thread(msg)
        }
        return content
        
    def _extract_body(self, msg) -> str:
        """HTML ve düz metin içeriğini akıllıca işle"""
        if msg.HTMLBody:
            soup = BeautifulSoup(msg.HTMLBody, 'html.parser')
            # Gereksiz HTML elementlerini temizle
            for tag in soup(['script', 'style', 'meta']):
                tag.decompose()
            return soup.get_text()
        return msg.Body
        
    def _process_attachments(self, msg) -> List[str]:
        """Ekleri işle ve içlerinde AWB ara"""
        results = []
        for attachment in msg.Attachments:
            if self._is_supported_attachment(attachment.FileName):
                content = self._extract_attachment_content(attachment)
                if content:
                    results.append(content)
        return results
        
    def _extract_thread(self, msg) -> List[str]:
        """Mail zincirini akıllıca işle"""
        thread = []
        conversation = msg.GetConversation()
        if conversation:
            for mail in conversation.GetChildren():
                thread.append(self._extract_body(mail))
        return thread

    def _is_supported_attachment(self, filename: str) -> bool:
        """Desteklenen ek formatlarını kontrol et"""
        return any(filename.lower().endswith(ext) for ext in self.supported_attachments)
        
    def _extract_pdf_content(self, pdf_path: str) -> str:
        """PDF içeriğini metin olarak çıkar"""
        if not self.pdf_reader:
            import pdfplumber  # Lazy import
            self.pdf_reader = pdfplumber
            
        text = []
        with self.pdf_reader.open(pdf_path) as pdf:
            for page in pdf.pages:
                text.append(page.extract_text())
        return "\n".join(text)
        
    def _clean_html(self, html: str) -> str:
        """HTML içeriğini temizle ve düzenle"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Gereksiz elementleri kaldır
        for tag in soup(['script', 'style', 'meta', 'link', 'image']):
            tag.decompose()
            
        # Mail zincirleri için özel işleme
        quotes = soup.find_all('blockquote')
        for quote in quotes:
            # Alıntı seviyesini belirt
            quote['style'] = 'margin-left: 1em; color: gray;'
            
        return str(soup)
