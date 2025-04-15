Eposta içeriğinde Referans Arama Uygulaması

E-posta ve dokümanlarda Referans Numaralarını tespit ederek kullanmış olduğunuz ERP veya benzeri uygulamarınızda son durumlarını tespit eder.

Proje Genel Bakış
Bu uygulama, e-postalardaki (öncelikle Outlook) takip numaralarının otomatik tespitini yapıp, yapay zeka destekli analiz yetenekleri sunar. Lojistik profesyonelleri ve kargo koordinatörleri için iletişim kaynaklarını tarayarak ilgili takip bilgilerini verimli bir şekilde bulmalarını sağlar.

Mimari
Uygulama MVC (Model-View-Controller) mimarisi kullanır:

Görünümler (Views): Ana pencere ve yardımcı iletişim kutuları dahil kullanıcı arayüzü bileşenleri
Kontrolörler ve Modeller: Temel iş mantığı ve veri yapıları
Yardımcı Araçlar: Tespit, analiz ve entegrasyon için özelleştirilmiş bileşenler

Temel Özellikler

✉️ Outlook entegrasyonu ile e-posta tarama

🔍 Yapılandırılabilir desen tespiti

🧠 Yapay zeka destekli içerik analizi

📊 Excel içe/dışa aktarma özellikleri

📎 Ek dosya işleme

💾 Arama sonuçlarını önbellekleme


Bileşenler

Kullanıcı Arayüzü Katmanı

main_window.py: Ana uygulama arayüzü

data_source_editor.py: E-posta kaynaklarını yapılandırma

pattern_manager.py: Tespit desenlerini yönetme

widgets.py: Yeniden kullanılabilir arayüz bileşenleri

progress.py: Detaylı ilerleme raporlama

Çekirdek

search_controller.py: Arama işlemlerini koordine eder

mail_model.py: E-posta veri gösterimi

Yardımcı Araçlar

_detector.py: Desen tanıma

cache_manager.py: Arama sonuçları önbelleği

config_manager.py: Uygulama ayarları

excel_helper.py: Excel dosya işlemleri

mail_analyzer.py: E-posta içerik analizi

outlook_helper.py: Microsoft Outlook entegrasyonu

ai_analyzer.py: Yapay zeka destekli içerik analizi

attachment_processor.py: E-posta eklerini işleme

Yapılandırma

Uygulama yapılandırma için JSON dosyaları kullanır:

settings.json: Uygulama ayarları

_patterns.json: Yapılandırılabilir tespit desenleri


Kullanım
Gereksinimler
Python 3.8 veya üzeri
Microsoft Outlook (e-posta entegrasyonu için)
Gerekli Python paketleri requirements.txt dosyasında listelenmiştir
Özellik Kullanım Örnekleri
E-posta Tarama
Ana ekrandan bir referans numarası girin ve "Ara" düğmesine tıklayın. Uygulama, Outlook'tan son 15 günlük e-postaları tarayacak ve ilgili referansları bulacaktır.

Desen Yönetimi
"Ayarlar > Desen Yöneticisi" bölümünden özel referans numarası desenlerinizi ekleyebilir veya düzenleyebilirsiniz.

Excel İşlemleri
"Dosya > Verileri Dışa Aktar" seçeneği ile arama sonuçlarını Excel'e aktarabilirsiniz.

Sorun Giderme
Outlook Bağlantı Hatası: Outlook'un açık olduğundan ve doğru profille oturum açtığınızdan emin olun.
OCR Hatası: Tesseract OCR'nin doğru kurulduğunu kontrol edin.
Önbellek Sorunları: "cache/" klasörünü temizleyerek yeniden başlatın.

![image](https://github.com/user-attachments/assets/1d2ca3d5-067e-4599-bca8-aaf3e2e09bb2)

