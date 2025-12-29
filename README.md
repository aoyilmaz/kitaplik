# 📚 Kitaplığım

Kişisel kitap koleksiyonunuzu yönetmek için modern ve kullanıcı dostu bir masaüstü uygulaması.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Özellikler

### 📖 Kitap Yönetimi
- **Online Arama**: Google Books, Open Library, Kitapyurdu, İdefix, BKM Kitap ve daha fazlasından kitap bilgilerini otomatik çek
- **Manuel Ekleme**: 40+ alan ile detaylı kitap kaydı (çeviri bilgileri, satın alma, konum vb.)
- **Kapak Görselleri**: Çoklu kaynaktan kapak arama veya dosyadan ekleme
- **Toplu İşlemler**: Çoklu seçim ile toplu düzenleme, silme ve rafa ekleme
- **Kitap Kopyalama**: Mevcut kitabı şablon olarak kullanarak hızlı ekleme
- **Alıntılar**: Her kitaptan sevilen cümleleri sayfa numarası ile kaydet

### 📚 Kitap Serileri
- Serileri otomatik grupla
- Seri içi okuma durumu takibi
- Seri tamamlama yüzdesi
- Serideki diğer kitapları görüntüleme

### 📋 Okuma Listesi
- **5 Farklı Durum**: Okunmadı, Okuyacağım, Okunuyor, Okundu, Okumayacağım
- **Sıralı Liste**: Sürükle-bırak ile okuma sırası belirleme
- **Tahmini Süre**: Günlük sayfa hızına göre bitiş tarihi hesaplama
- **İstatistikler**: Toplam sayfa, tahmini gün ve saat

### 🎯 Okuma Takibi
- Sayfa takibi (şu an hangi sayfadasın)
- Okuma tarihleri (başlama ve bitirme)
- Yıllık okuma hedefi belirleme ve takip
- Okuma sayısı

### 🗂️ Organizasyon
- **Raflar**: Özel raflar oluşturun (Favoriler, Okunacaklar, vb.)
- **Filtreleme**: Durum, yıl, puan ve metin ile hızlı filtreleme
- **Sıralama**: Tüm sütunlara göre sıralama
- **Anlık Arama**: Başlık, yazar, ISBN ile arama

### 📊 İstatistikler (7 Sekmeli)
1. **Genel Bakış**: Toplam kitap, sayfa, okuma durumu dağılımı
2. **Yazarlar**: En çok okunan yazarlar grafiği
3. **Yayınevleri**: Yayınevi dağılımı
4. **Yıllar**: Yayın yılı analizi
5. **Okuma Hızı**: Aylık okuma grafiği, en hızlı/yavaş okunan kitaplar
6. **Puanlar**: Puan dağılımı, en yüksek puanlı kitaplar
7. **Hedef**: Yıllık okuma hedefi takibi

### 🤖 AI Asistan (Ollama)
- **Kişiselleştirilmiş Öneriler**: Kitaplığına göre kitap önerileri
- **Okuma Analizi**: Okuma alışkanlıklarını analiz
- **Okuma Planı**: Okunmamış kitaplar için plan oluşturma
- **Serbest Soru**: Kitaplar hakkında her şeyi sor
- Tamamen yerel, internet gerektirmez

### 🎨 Arayüz
- VS Code tarzı modern koyu/açık tema
- Grid (kapak) ve liste görünümü
- Özelleştirilebilir sütunlar
- Açılıp kapanabilen kenar çubuğu
- Satır içi düzenleme (çift tık)

### 📤 İçe/Dışa Aktarma
- **İçe Aktar**: CSV ve Excel dosyalarından toplu kitap yükleme
- **Dışa Aktar**: CSV, JSON ve Excel formatlarında dışa aktarma
- Akıllı sütun eşleştirme

## 🚀 Kurulum

### Gereksinimler
- Python 3.10 veya üzeri
- pip (Python paket yöneticisi)

### Adımlar

```bash
# 1. Repoyu klonlayın
git clone https://github.com/okan-aydogan/kitaplik.git
cd kitaplik

# 2. Sanal ortam oluşturun (önerilen)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 4. Uygulamayı çalıştırın
python main.py
```

### AI Asistan için (Opsiyonel)

```bash
# Ollama'yı kurun (macOS)
brew install ollama

# Model indirin
ollama pull mistral

# Ollama'yı başlatın (arka planda çalışır)
ollama serve
```

## 📦 Bağımlılıklar

| Paket | Açıklama |
|-------|----------|
| PyQt6 | Modern GUI framework |
| requests | HTTP istekleri (API aramaları, Ollama) |
| openpyxl | Excel dosyası desteği |

## ⌨️ Klavye Kısayolları

| Kısayol | İşlev |
|---------|-------|
| `Ctrl+N` | Online arama ile kitap ekle |
| `Ctrl+Shift+N` | Manuel kitap ekle |
| `Ctrl+L` | Okuma listesi |
| `Ctrl+I` | İstatistikler |
| `Ctrl+B` | Kenar çubuğunu aç/kapat |
| `Ctrl+Shift+A` | AI Asistan |
| `Ctrl+Q` | Çıkış |
| `Delete` | Seçili kitabı sil |
| `Ctrl+Click` | Çoklu seçim |

## 📁 Proje Yapısı

```
kitaplik/
├── main.py              # Uygulama giriş noktası
├── database.py          # SQLite veritabanı işlemleri
├── requirements.txt     # Python bağımlılıkları
├── assets/
│   └── covers/          # İndirilen kapak görselleri
├── services/
│   ├── book_api.py      # Kitap arama API'leri
│   └── ai_service.py    # Ollama AI entegrasyonu
└── ui/
    ├── main_window.py   # Ana pencere ve dialoglar
    ├── book_dialog.py   # Kitap ekleme/düzenleme
    ├── shelf_panel.py   # Raf paneli
    ├── filter_bar.py    # Filtre çubuğu
    ├── stats_dialog.py  # İstatistik dialogu
    └── themes.py        # Tema stilleri
```

## 🗄️ Veritabanı

SQLite veritabanı kullanılır. İlk çalıştırmada `kitaplik.db` otomatik oluşturulur.

**Tablolar:**
- `books` - Kitap bilgileri (40+ alan)
- `shelves` - Raflar
- `book_shelves` - Kitap-raf ilişkileri
- `quotes` - Kitap alıntıları
- `reading_goals` - Yıllık okuma hedefleri
- `settings` - Uygulama ayarları

## 🚧 Gelecek Özellikler

- [ ] Goodreads entegrasyonu
- [ ] Yedekleme/Geri yükleme
- [ ] Çoklu dil desteği
- [ ] Kullanıcı profilleri
- [ ] Bulut senkronizasyonu

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 🙏 Teşekkürler

- [Google Books API](https://developers.google.com/books)
- [Open Library](https://openlibrary.org/)
- [Ollama](https://ollama.ai/)
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)

---
