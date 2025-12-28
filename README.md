# 📚 Kitaplığım

Kişisel kitap koleksiyonunuzu yönetmek için modern ve kullanıcı dostu bir masaüstü uygulaması.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

<p align="center">
  <img src="docs/screenshot.png" alt="Kitaplığım Ekran Görüntüsü" width="800">
</p>

## ✨ Özellikler

### 📖 Kitap Yönetimi
- **Online Arama**: Google Books, Open Library, Kitapyurdu ve daha fazlasından kitap bilgilerini otomatik çek
- **Manuel Ekleme**: 40+ alan ile detaylı kitap kaydı
- **Kapak Görselleri**: Online arama veya dosyadan kapak ekleme
- **Toplu İçe Aktarma**: CSV ve Excel dosyalarından kitap listesi yükle

### 🗂️ Organizasyon
- **Raflar**: Kitaplarınızı özel raflarda düzenleyin (Favoriler, Okunacaklar, vb.)
- **Filtreleme**: Durum, yıl ve metin ile hızlı filtreleme
- **Sıralama**: Başlık, yazar, yıl, puan ve ekleme tarihine göre sırala
- **Arama**: Anlık arama ile kitaplarınızı bulun

### 📊 İstatistikler
- Okuma durumu dağılımı
- Yıllara göre yayın analizi
- En çok okunan yazarlar
- Yayınevi dağılımı
- Sayfa ve puan istatistikleri
- Aylık okuma grafiği

### 🎨 Arayüz
- VS Code tarzı modern koyu tema
- Grid ve liste görünümü
- Özelleştirilebilir sütunlar
- Açılıp kapanabilen kenar çubuğu

### 📤 Dışa Aktarma
- CSV, JSON ve Excel formatlarında dışa aktarma

## 🚀 Kurulum

### Gereksinimler
- Python 3.10 veya üzeri
- pip (Python paket yöneticisi)

### Adımlar

1. **Repoyu klonlayın**
```bash
git clone https://github.com/KULLANICI_ADIN/kitaplik.git
cd kitaplik
```

2. **Sanal ortam oluşturun (önerilen)**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. **Bağımlılıkları yükleyin**
```bash
pip install -r requirements.txt
```

4. **Uygulamayı çalıştırın**
```bash
python main.py
```

## 📦 Bağımlılıklar

| Paket | Açıklama |
|-------|----------|
| PyQt6 | Modern GUI framework |
| requests | HTTP istekleri (API aramaları) |
| openpyxl | Excel dosyası desteği |

## 🎯 Kullanım

### Kitap Ekleme

**Online Arama ile:**
1. `Ctrl+N` veya Kitap Ekle → Online Arama
2. Kitap adı, yazar veya ISBN ile arayın
3. Sonuçlardan birini seçin
4. Kaydet

**Manuel:**
1. `Ctrl+M` veya Kitap Ekle → Manuel Ekle
2. Bilgileri doldurun
3. Kapak eklemek için "🔍 Kapak Ara" butonunu kullanın
4. Kaydet

### CSV/Excel'den İçe Aktarma

1. Dosya → 📥 İçe Aktar
2. CSV veya Excel dosyanızı seçin
3. Sütunları eşleştirin (otomatik algılanır)
4. İçe Aktar

**Desteklenen sütunlar:**
- Kitap_Adı / Başlık → Kitap başlığı
- Yazar → Yazar adı
- Yayınevi → Yayınevi
- Sayfa_Sayısı → Sayfa sayısı
- Yayın_Yılı → Yayın yılı
- Okuma Durumu → Okundu/Okunuyor/Okunmadı
- Raf → Raf adı (otomatik oluşturulur)

### Klavye Kısayolları

| Kısayol | İşlev |
|---------|-------|
| `Ctrl+N` | Online arama ile kitap ekle |
| `Ctrl+M` | Manuel kitap ekle |
| `Ctrl+F` | Arama kutusuna odaklan |
| `Ctrl+I` | İstatistikleri göster |
| `Ctrl+B` | Kenar çubuğunu aç/kapat |
| `Ctrl+Q` | Uygulamadan çık |
| `Delete` | Seçili kitabı sil |

## 📁 Proje Yapısı

```
kitaplik/
├── main.py              # Uygulama giriş noktası
├── database.py          # SQLite veritabanı işlemleri
├── requirements.txt     # Python bağımlılıkları
├── assets/
│   └── covers/          # İndirilen kapak görselleri
├── services/
│   └── book_api.py      # Kitap arama API'leri
└── ui/
    ├── main_window.py   # Ana pencere
    ├── book_dialog.py   # Kitap ekleme/düzenleme dialogları
    ├── shelf_panel.py   # Raf paneli
    ├── filter_bar.py    # Filtre çubuğu
    ├── stats_dialog.py  # İstatistik dialogu
    └── themes.py        # Tema stilleri
```

## 🗄️ Veritabanı

Uygulama SQLite veritabanı kullanır. İlk çalıştırmada `kitaplik.db` dosyası otomatik oluşturulur.

**Tablolar:**
- `books` - Kitap bilgileri (40+ alan)
- `shelves` - Raflar
- `book_shelves` - Kitap-raf ilişkileri

## 🤝 Katkıda Bulunma

1. Bu repoyu fork edin
2. Feature branch oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -m 'Yeni özellik eklendi'`)
4. Branch'inizi push edin (`git push origin feature/yeni-ozellik`)
5. Pull Request açın

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 🙏 Teşekkürler

- [Google Books API](https://developers.google.com/books) - Kitap verileri
- [Open Library](https://openlibrary.org/) - Açık kitap veritabanı
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework

---

<p align="center">
  Claude ile ❤️ ile yapıldı
</p>
