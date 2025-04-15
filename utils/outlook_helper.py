import win32com.client
from models.mail_model import MailModel
from datetime import datetime, timedelta

class OutlookHelper:
    @staticmethod
    def get_outlook_connection():
        outlook = win32com.client.Dispatch("Outlook.Application")
        namespace = outlook.GetNamespace("MAPI")
        return namespace.GetDefaultFolder(6)

  

    @staticmethod
    def get_mails(folder, config):
        """Config'e göre sınırlı sayıda mail getir"""
        messages = folder.Items
        messages.Sort("[ReceivedTime]", True)  # En yeni mailleri üste al
        
        max_mails = int(config["cache"]["max_mails"])  # int dönüşümü ekle
        max_days = int(config["outlook"]["max_days"])
        cutoff_date = datetime.now().replace(tzinfo=None) - timedelta(days=max_days)
        
        mails = []
        mail_count = 0
        
        for msg in messages:
            if mail_count >= max_mails:  # Mail sayısı limitini kontrol et
                break
                
            # Outlook tarihini timezone bilgisi olmayan datetime'a çevir
            msg_date = msg.ReceivedTime.replace(tzinfo=None)
            
            if msg_date < cutoff_date:  # Tarih kontrolü
                break
                
            try:
                mail = OutlookHelper.format_mail(msg)
                mails.append(mail)
                mail_count += 1
            except Exception as e:
                print(f"Mail okuma hatası: {str(e)}")
                continue
                
        return mails[:max_mails]  # Son kontrol için slice

    @staticmethod
    def format_mail(msg):
        """Tek bir maili MailModel'e dönüştür"""
        return MailModel(
            date=msg.ReceivedTime.replace(tzinfo=None),  
            subject=msg.Subject,
            body=msg.Body,
            sender=msg.SenderName,
            to=msg.To,
            has_attachments=msg.Attachments.Count > 0
        )

    def get_mail_content(self, msg):
        """Mail ve eklerinin içeriğini al"""
        content = []
        
        # 1. HTML içerik veya düz metin içeriği al
        if msg.HTMLBody:
            content.append(msg.HTMLBody)  # Önce HTML formatını dene
        elif msg.Body:
            content.append(msg.Body)      # HTML yoksa düz metin al
            
        # 2. Ekleri listele
        if msg.Attachments.Count > 0:
            attachments_text = "\n\nEkler:\n"
            for attachment in msg.Attachments:
                attachments_text += f"- {attachment.FileName}\n"
            content.append(attachments_text)
                    
        return "\n".join(content)

    def get_root_folder(self):
        """Outlook'un ana klasörlerini al"""
        try:
            outlook = win32com.client.Dispatch("Outlook.Application")
            namespace = outlook.GetNamespace("MAPI")
            
            # Özel klasörleri al
            inbox = namespace.GetDefaultFolder(6)  # 6 = Gelen Kutusu
            sent = namespace.GetDefaultFolder(5)   # 5 = Gönderilmiş Öğeler
            
            print("Ana klasörler alınıyor:")
            print(f"Gelen Kutusu: {inbox.Name}")
            print(f"Gönderilmiş Öğeler: {sent.Name}")
            
            return {
                "inbox": inbox,
                "sent": sent
            }
            
        except Exception as e:
            print(f"Outlook klasörleri alınırken hata: {str(e)}")
            return None
            
    def get_folder_by_id(self, folder_id):
        """Entry ID ile klasör getir"""
        try:
            outlook = win32com.client.Dispatch("Outlook.Application")
            namespace = outlook.GetNamespace("MAPI")
            folder = namespace.GetFolderFromID(folder_id)
            #print(f"Seçilen klasör: {folder.Name}")
            return folder
        except Exception as e:
            print(f"Klasör getirme hatası: {str(e)}")
            return None
