"""
Kitaplık Uygulaması - Veritabanı Modülü
======================================
Bu modül SQLite veritabanı işlemlerini yönetir.
Kitap ekleme, silme, güncelleme, listeleme gibi tüm veri işlemleri burada.
"""

import sqlite3
from datetime import datetime
from pathlib import Path


# Veritabanı dosyasının yolu
# Path(__file__) = bu dosyanın kendisi (database.py)
# .parent = bu dosyanın bulunduğu klasör (kitaplik/)
# Böylece veritabanı her zaman uygulama klasöründe oluşur
DB_PATH = Path(__file__).parent / "kitaplik.db"


def get_connection():
    """
    Veritabanına bağlantı açar.
    
    sqlite3.Row kullanmamızın sebebi:
    Normalde: row[0], row[1] gibi index ile erişirsin
    Row ile: row["title"], row["author"] gibi isimle erişirsin
    Çok daha okunabilir kod yazarız.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """
    Veritabanını ve tabloları oluşturur.
    Uygulama ilk açıldığında çağrılır.
    
    IF NOT EXISTS: Tablo zaten varsa hata vermez, atlar.
    Bu sayede her açılışta güvenle çağırabiliriz.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Kitaplar tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            -- PRIMARY KEY: Her satırı benzersiz kılar
            -- AUTOINCREMENT: Otomatik artan sayı (1, 2, 3...)
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Temel kitap bilgileri
            title TEXT NOT NULL,           -- NOT NULL: Boş olamaz, başlık şart
            author TEXT,                   -- Yazar (anonim olabilir, NULL olabilir)
            isbn TEXT,                     -- ISBN (her kitapta olmayabilir)
            page_count INTEGER,            -- Sayfa sayısı
            publish_year INTEGER,          -- Yayın yılı
            publisher TEXT,                -- Yayınevi
            cover_path TEXT,               -- Kapak görseli dosya yolu
            
            -- API'den gelen ek bilgiler
            subtitle TEXT,                 -- Alt başlık
            description TEXT,              -- Açıklama/özet
            language TEXT,                 -- Dil (tr, en, de...)
            categories TEXT,               -- Kategoriler (virgülle ayrılmış)
            
            -- Çeviri bilgileri (manuel)
            translator TEXT,               -- Çevirmen
            original_title TEXT,           -- Orijinal başlık
            original_language TEXT,        -- Orijinal dil
            
            -- Seri bilgileri
            series_name TEXT,              -- Seri adı
            series_order INTEGER,          -- Seri sırası (1, 2, 3...)
            
            -- Fiziksel bilgiler
            format TEXT DEFAULT 'paperback', -- paperback/hardcover/ebook/audiobook
            location TEXT,                 -- Fiziksel konum (raf, oda...)
            
            -- Okuma takibi
            status TEXT DEFAULT 'unread',  -- 'unread', 'reading', 'read'
            start_date TEXT,               -- Okumaya başlama tarihi (ISO format)
            finish_date TEXT,              -- Bitirme tarihi
            current_page INTEGER,          -- Şu anki sayfa (okunuyor için)
            times_read INTEGER DEFAULT 0,  -- Kaç kez okundu
            rating INTEGER,                -- 1-5 arası puan
            notes TEXT,                    -- Kısa notlar
            review TEXT,                   -- Uzun inceleme/değerlendirme
            
            -- Satın alma bilgileri
            purchase_date TEXT,            -- Satın alma tarihi
            purchase_place TEXT,           -- Nereden alındı
            purchase_price REAL,           -- Fiyat
            currency TEXT DEFAULT 'TRY',   -- Para birimi
            is_gift INTEGER DEFAULT 0,     -- Hediye mi? (0/1)
            gifted_by TEXT,                -- Hediye eden kişi
            
            -- Ödünç durumu
            is_borrowed INTEGER DEFAULT 0, -- Ödünç verildi mi? (0/1)
            borrowed_to TEXT,              -- Kime verildi
            borrowed_date TEXT,            -- Ne zaman verildi
            
            -- Etiketler
            tags TEXT,                     -- Serbest etiketler (virgülle ayrılmış)
            
            -- Sistem bilgileri
            created_at TEXT NOT NULL,      -- Eklenme tarihi
            updated_at TEXT NOT NULL       -- Son güncelleme tarihi
        )
    """)
    
    # ISBN için index oluştur (arama hızlandırır)
    # Aynı ISBN'den birden fazla olabilir (farklı baskılar)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn)
    """)
    
    # Ayarlar tablosu (tema tercihi vs.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    # Raflar tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shelves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            icon TEXT DEFAULT '📚',
            created_at TEXT NOT NULL
        )
    """)
    
    # Kitap-Raf ilişki tablosu (çoka-çok ilişki)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS book_shelves (
            book_id INTEGER NOT NULL,
            shelf_id INTEGER NOT NULL,
            PRIMARY KEY (book_id, shelf_id),
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            FOREIGN KEY (shelf_id) REFERENCES shelves(id) ON DELETE CASCADE
        )
    """)
    
    # Varsayılan rafları ekle (yoksa)
    now = datetime.now().isoformat()
    default_shelves = [
        ("Favoriler", "⭐"),
        ("Okumak İstiyorum", "📋"),
        ("Şu An Okuyorum", "📖"),
        ("Bitirildi", "✅"),
    ]
    for name, icon in default_shelves:
        cursor.execute("""
            INSERT OR IGNORE INTO shelves (name, icon, created_at)
            VALUES (?, ?, ?)
        """, (name, icon, now))
    
    conn.commit()
    conn.close()
    
    # Eski veritabanları için migration
    _migrate_database()
    
    print(f"Veritabanı hazır: {DB_PATH}")


def _migrate_database():
    """Eski veritabanlarına yeni sütunları ekler."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Mevcut sütunları al
    cursor.execute("PRAGMA table_info(books)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    # Eklenecek yeni sütunlar ve varsayılan değerleri
    new_columns = [
        ("subtitle", "TEXT", None),
        ("description", "TEXT", None),
        ("language", "TEXT", None),
        ("categories", "TEXT", None),
        ("translator", "TEXT", None),
        ("original_title", "TEXT", None),
        ("original_language", "TEXT", None),
        ("series_name", "TEXT", None),
        ("series_order", "INTEGER", None),
        ("format", "TEXT", "'paperback'"),
        ("location", "TEXT", None),
        ("current_page", "INTEGER", None),
        ("times_read", "INTEGER", "0"),
        ("review", "TEXT", None),
        ("purchase_date", "TEXT", None),
        ("purchase_place", "TEXT", None),
        ("purchase_price", "REAL", None),
        ("currency", "TEXT", "'TRY'"),
        ("is_gift", "INTEGER", "0"),
        ("gifted_by", "TEXT", None),
        ("is_borrowed", "INTEGER", "0"),
        ("borrowed_to", "TEXT", None),
        ("borrowed_date", "TEXT", None),
        ("tags", "TEXT", None),
    ]
    
    for col_name, col_type, default in new_columns:
        if col_name not in existing_columns:
            try:
                if default:
                    cursor.execute(f"ALTER TABLE books ADD COLUMN {col_name} {col_type} DEFAULT {default}")
                else:
                    cursor.execute(f"ALTER TABLE books ADD COLUMN {col_name} {col_type}")
                print(f"  + Sütun eklendi: {col_name}")
            except Exception as e:
                print(f"  ! Sütun eklenemedi ({col_name}): {e}")
    
    conn.commit()
    conn.close()


def add_book(
    title, 
    author=None, 
    isbn=None, 
    page_count=None, 
    publish_year=None, 
    publisher=None, 
    cover_path=None,
    # API'den gelen ek bilgiler
    subtitle=None,
    description=None,
    language=None,
    categories=None,
    # Çeviri bilgileri
    translator=None,
    original_title=None,
    original_language=None,
    # Seri bilgileri
    series_name=None,
    series_order=None,
    # Fiziksel bilgiler
    format="paperback",
    location=None,
    # Etiketler
    tags=None,
):
    """
    Yeni bir kitap ekler.
    
    Returns:
        Eklenen kitabın id'si
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO books (
            title, author, isbn, page_count, publish_year, publisher, cover_path,
            subtitle, description, language, categories,
            translator, original_title, original_language,
            series_name, series_order, format, location, tags,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title, author, isbn, page_count, publish_year, publisher, cover_path,
        subtitle, description, language, categories,
        translator, original_title, original_language,
        series_name, series_order, format, location, tags,
        now, now
    ))
    
    book_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return book_id


def get_all_books():
    """
    Tüm kitapları getirir.
    Eklenme sırasına göre (eski → yeni) sıralar.
    
    Returns:
        Kitap listesi (her biri dict benzeri Row objesi)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM books ORDER BY id ASC
    """)
    
    books = cursor.fetchall()
    conn.close()
    
    return books


def get_filtered_books(status=None, rating=None, year=None):
    """
    Filtrelenmiş kitapları getirir.
    
    Args:
        status: 'unread', 'reading', 'read' veya None (tümü)
        rating: 1-5 arası puan veya None (tümü)
        year: Yayın yılı veya None (tümü)
    
    Returns:
        Filtrelenmiş kitap listesi
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM books WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    if rating:
        query += " AND rating = ?"
        params.append(rating)
    
    if year:
        query += " AND publish_year = ?"
        params.append(year)
    
    query += " ORDER BY id ASC"
    
    cursor.execute(query, params)
    books = cursor.fetchall()
    conn.close()
    
    return books


def get_distinct_years():
    """
    Kitaplardaki benzersiz yayın yıllarını getirir.
    
    Returns:
        Yıl listesi (azalan sırada)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT publish_year FROM books 
        WHERE publish_year IS NOT NULL 
        ORDER BY publish_year DESC
    """)
    
    years = [row["publish_year"] for row in cursor.fetchall()]
    conn.close()
    
    return years


def get_book_by_id(book_id):
    """
    ID'ye göre tek bir kitap getirir.
    
    Returns:
        Kitap varsa Row objesi, yoksa None
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    
    conn.close()
    return book


def update_book(book_id, **kwargs):
    """
    Bir kitabı günceller.
    
    Kullanım:
        update_book(1, title="Yeni Başlık", rating=5)
        update_book(1, status="read", finish_date="2024-01-15")
    
    **kwargs: İstediğin kadar alan=değer çifti gönderebilirsin
    """
    if not kwargs:
        return  # Güncellenecek bir şey yok
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Güncelleme zamanını ekle
    kwargs["updated_at"] = datetime.now().isoformat()
    
    # Dinamik SQL oluştur
    # {"title": "X", "rating": 5} -> "title = ?, rating = ?, updated_at = ?"
    set_clause = ", ".join(f"{key} = ?" for key in kwargs.keys())
    values = list(kwargs.values()) + [book_id]
    
    cursor.execute(f"""
        UPDATE books SET {set_clause} WHERE id = ?
    """, values)
    
    conn.commit()
    conn.close()


def delete_book(book_id):
    """
    Bir kitabı siler.
    
    Dikkat: Bu işlem geri alınamaz!
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
    
    conn.commit()
    conn.close()


def search_books(query):
    """
    Kitap arar (başlık veya yazar içinde).
    
    LIKE '%sorgu%': İçinde 'sorgu' geçen her şeyi bulur
    Büyük/küçük harf duyarsız (SQLite varsayılanı)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    search_term = f"%{query}%"
    
    cursor.execute("""
        SELECT * FROM books 
        WHERE title LIKE ? OR author LIKE ?
        ORDER BY created_at DESC
    """, (search_term, search_term))
    
    books = cursor.fetchall()
    conn.close()
    
    return books


# ==================== AYARLAR ====================

def get_setting(key: str, default: str = None) -> str | None:
    """
    Bir ayar değerini getirir.
    
    Args:
        key: Ayar anahtarı (örn: "theme")
        default: Ayar yoksa döndürülecek değer
    
    Returns:
        Ayar değeri veya default
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return row["value"]
    return default


def set_setting(key: str, value: str):
    """
    Bir ayar değerini kaydeder.
    Varsa günceller, yoksa ekler.
    
    Args:
        key: Ayar anahtarı
        value: Ayar değeri
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # INSERT OR REPLACE: Varsa güncelle, yoksa ekle
    cursor.execute("""
        INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
    """, (key, value))
    
    conn.commit()
    conn.close()


# ==================== RAFLAR ====================

def get_all_shelves():
    """Tüm rafları getirir."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM shelves ORDER BY created_at")
    shelves = cursor.fetchall()
    
    conn.close()
    return shelves


def add_shelf(name: str, icon: str = "📚"):
    """
    Yeni raf ekler.
    
    Returns:
        Eklenen rafın id'si veya None (isim zaten varsa)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO shelves (name, icon, created_at)
            VALUES (?, ?, ?)
        """, (name, icon, now))
        
        shelf_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return shelf_id
    except sqlite3.IntegrityError:
        # İsim zaten var
        conn.close()
        return None


def delete_shelf(shelf_id: int):
    """Bir rafı siler (içindeki kitaplar raftan çıkar, silinmez)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM shelves WHERE id = ?", (shelf_id,))
    
    conn.commit()
    conn.close()


def update_shelf(shelf_id: int, name: str = None, icon: str = None):
    """Raf bilgilerini günceller."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if name:
        cursor.execute("UPDATE shelves SET name = ? WHERE id = ?", (name, shelf_id))
    if icon:
        cursor.execute("UPDATE shelves SET icon = ? WHERE id = ?", (icon, shelf_id))
    
    conn.commit()
    conn.close()


def add_book_to_shelf(book_id: int, shelf_id: int):
    """Kitabı rafa ekler."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO book_shelves (book_id, shelf_id)
            VALUES (?, ?)
        """, (book_id, shelf_id))
        conn.commit()
    except sqlite3.IntegrityError:
        # Zaten ekli
        pass
    
    conn.close()


def remove_book_from_shelf(book_id: int, shelf_id: int):
    """Kitabı raftan çıkarır."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM book_shelves
        WHERE book_id = ? AND shelf_id = ?
    """, (book_id, shelf_id))
    
    conn.commit()
    conn.close()


def get_books_in_shelf(shelf_id: int):
    """Bir raftaki kitapları getirir."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT b.* FROM books b
        INNER JOIN book_shelves bs ON b.id = bs.book_id
        WHERE bs.shelf_id = ?
        ORDER BY b.created_at DESC
    """, (shelf_id,))
    
    books = cursor.fetchall()
    conn.close()
    return books


def get_shelves_for_book(book_id: int):
    """Bir kitabın bulunduğu rafları getirir."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.* FROM shelves s
        INNER JOIN book_shelves bs ON s.id = bs.shelf_id
        WHERE bs.book_id = ?
        ORDER BY s.name
    """, (book_id,))
    
    shelves = cursor.fetchall()
    conn.close()
    return shelves


def get_shelf_book_count(shelf_id: int) -> int:
    """Bir raftaki kitap sayısını döndürür."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) as count FROM book_shelves WHERE shelf_id = ?
    """, (shelf_id,))
    
    result = cursor.fetchone()
    conn.close()
    return result["count"]


# ==================== İSTATİSTİKLER ====================

def get_statistics() -> dict:
    """
    Kütüphane istatistiklerini döndürür.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Toplam kitap
    cursor.execute("SELECT COUNT(*) as count FROM books")
    stats["total_books"] = cursor.fetchone()["count"]
    
    # Duruma göre kitap sayıları
    cursor.execute("SELECT COUNT(*) as count FROM books WHERE status = 'read'")
    stats["read_books"] = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM books WHERE status = 'reading'")
    stats["reading_books"] = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM books WHERE status = 'unread'")
    stats["unread_books"] = cursor.fetchone()["count"]
    
    # Toplam sayfa (tüm kitaplar)
    cursor.execute("SELECT COALESCE(SUM(page_count), 0) as total FROM books")
    stats["total_pages"] = cursor.fetchone()["total"]
    
    # Okunan sayfa (sadece okunan kitaplar)
    cursor.execute("""
        SELECT COALESCE(SUM(page_count), 0) as total 
        FROM books 
        WHERE status = 'read'
    """)
    stats["read_pages"] = cursor.fetchone()["total"]
    
    # Ortalama puan (sadece puanlananlar)
    cursor.execute("""
        SELECT AVG(rating) as avg, COUNT(*) as count 
        FROM books 
        WHERE rating IS NOT NULL AND rating > 0
    """)
    rating_result = cursor.fetchone()
    stats["average_rating"] = round(rating_result["avg"], 1) if rating_result["avg"] else 0
    stats["rated_books"] = rating_result["count"]
    
    # Toplam raf
    cursor.execute("SELECT COUNT(*) as count FROM shelves")
    stats["total_shelves"] = cursor.fetchone()["count"]
    
    conn.close()
    return stats


def get_monthly_reading_stats(year: int = None) -> list:
    """
    Aylık okuma istatistiklerini döndürür.
    
    Returns:
        [{"month": 1, "year": 2024, "count": 5, "pages": 1200}, ...]
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if year:
        cursor.execute("""
            SELECT 
                CAST(strftime('%m', finish_date) AS INTEGER) as month,
                CAST(strftime('%Y', finish_date) AS INTEGER) as year,
                COUNT(*) as count,
                COALESCE(SUM(page_count), 0) as pages
            FROM books 
            WHERE status = 'read' 
                AND finish_date IS NOT NULL
                AND strftime('%Y', finish_date) = ?
            GROUP BY year, month
            ORDER BY year, month
        """, (str(year),))
    else:
        cursor.execute("""
            SELECT 
                CAST(strftime('%m', finish_date) AS INTEGER) as month,
                CAST(strftime('%Y', finish_date) AS INTEGER) as year,
                COUNT(*) as count,
                COALESCE(SUM(page_count), 0) as pages
            FROM books 
            WHERE status = 'read' AND finish_date IS NOT NULL
            GROUP BY year, month
            ORDER BY year DESC, month DESC
            LIMIT 12
        """)
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_yearly_reading_stats() -> list:
    """
    Yıllık okuma istatistiklerini döndürür.
    
    Returns:
        [{"year": 2024, "count": 24, "pages": 8500}, ...]
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            CAST(strftime('%Y', finish_date) AS INTEGER) as year,
            COUNT(*) as count,
            COALESCE(SUM(page_count), 0) as pages
        FROM books 
        WHERE status = 'read' AND finish_date IS NOT NULL
        GROUP BY year
        ORDER BY year DESC
    """)
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_author_stats(limit: int = 10) -> list:
    """
    En çok okunan yazarları döndürür.
    
    Returns:
        [{"author": "Dostoyevski", "count": 5, "pages": 2500, "avg_rating": 4.5}, ...]
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            author,
            COUNT(*) as count,
            COALESCE(SUM(page_count), 0) as pages,
            ROUND(AVG(CASE WHEN rating > 0 THEN rating END), 1) as avg_rating
        FROM books 
        WHERE author IS NOT NULL AND author != ''
        GROUP BY author
        ORDER BY count DESC, pages DESC
        LIMIT ?
    """, (limit,))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_category_stats() -> list:
    """
    Kategori dağılımını döndürür.
    
    Returns:
        [{"category": "Roman", "count": 15}, ...]
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Kategoriler virgülle ayrılmış olabilir, her birini say
    cursor.execute("""
        SELECT categories FROM books 
        WHERE categories IS NOT NULL AND categories != ''
    """)
    
    category_counts = {}
    for row in cursor.fetchall():
        cats = row["categories"].split(",")
        for cat in cats:
            cat = cat.strip()
            if cat:
                category_counts[cat] = category_counts.get(cat, 0) + 1
    
    conn.close()
    
    # Sırala ve döndür
    results = [{"category": k, "count": v} for k, v in category_counts.items()]
    results.sort(key=lambda x: x["count"], reverse=True)
    return results[:15]  # En fazla 15


def get_reading_speed_stats() -> dict:
    """
    Okuma hızı istatistiklerini döndürür.
    
    Returns:
        {
            "avg_days_per_book": float,
            "avg_pages_per_day": float,
            "fastest_book": {...},
            "slowest_book": {...},
        }
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {
        "avg_days_per_book": 0,
        "avg_pages_per_day": 0,
        "fastest_book": None,
        "slowest_book": None,
        "total_reading_days": 0,
    }
    
    # Başlama ve bitiş tarihi olan kitapları al
    cursor.execute("""
        SELECT 
            id, title, author, page_count,
            start_date, finish_date,
            julianday(finish_date) - julianday(start_date) as days
        FROM books 
        WHERE status = 'read' 
            AND start_date IS NOT NULL 
            AND finish_date IS NOT NULL
            AND start_date != ''
            AND finish_date != ''
            AND julianday(finish_date) >= julianday(start_date)
        ORDER BY days ASC
    """)
    
    books = cursor.fetchall()
    conn.close()
    
    if not books:
        return stats
    
    total_days = 0
    total_pages = 0
    
    for book in books:
        days = book["days"] or 1  # En az 1 gün
        total_days += days
        total_pages += book["page_count"] or 0
    
    stats["total_reading_days"] = int(total_days)
    stats["avg_days_per_book"] = round(total_days / len(books), 1)
    
    if total_days > 0:
        stats["avg_pages_per_day"] = round(total_pages / total_days, 1)
    
    # En hızlı (en az gün)
    fastest = books[0]
    stats["fastest_book"] = {
        "title": fastest["title"],
        "author": fastest["author"],
        "days": int(fastest["days"] or 1),
        "pages": fastest["page_count"],
    }
    
    # En yavaş (en çok gün)
    slowest = books[-1]
    stats["slowest_book"] = {
        "title": slowest["title"],
        "author": slowest["author"],
        "days": int(slowest["days"] or 1),
        "pages": slowest["page_count"],
    }
    
    return stats


def get_reading_goal(year: int = None) -> dict:
    """
    Okuma hedefi durumunu döndürür.
    
    Returns:
        {
            "year": 2024,
            "goal": 24,
            "read": 18,
            "percentage": 75,
            "remaining": 6,
            "on_track": True,
        }
    """
    from datetime import datetime
    
    if year is None:
        year = datetime.now().year
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Hedefi al
    goal = int(get_setting(f"reading_goal_{year}", "0") or 0)
    
    # Bu yıl okunan kitap sayısı
    cursor.execute("""
        SELECT COUNT(*) as count FROM books 
        WHERE status = 'read' 
            AND finish_date IS NOT NULL
            AND strftime('%Y', finish_date) = ?
    """, (str(year),))
    
    read = cursor.fetchone()["count"]
    conn.close()
    
    # Hesaplamalar
    percentage = int((read / goal * 100)) if goal > 0 else 0
    remaining = max(0, goal - read)
    
    # Yılın kaçıncı gününde olduğumuzu hesapla
    now = datetime.now()
    if now.year == year:
        day_of_year = now.timetuple().tm_yday
        days_in_year = 366 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 365
        expected_percentage = (day_of_year / days_in_year) * 100
        on_track = percentage >= expected_percentage
    else:
        on_track = percentage >= 100
    
    return {
        "year": year,
        "goal": goal,
        "read": read,
        "percentage": min(percentage, 100),
        "remaining": remaining,
        "on_track": on_track,
    }


def set_reading_goal(year: int, goal: int):
    """Yıllık okuma hedefini ayarlar."""
    set_setting(f"reading_goal_{year}", str(goal))


def get_year_summary(year: int) -> dict:
    """
    Yıllık özet raporu döndürür.
    
    Returns:
        {
            "year": 2024,
            "total_books": 24,
            "total_pages": 8500,
            "avg_rating": 4.2,
            "avg_pages_per_book": 354,
            "top_authors": [...],
            "top_rated_books": [...],
            "monthly_breakdown": [...],
            "categories": [...],
            "formats": {...},
        }
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    summary = {"year": year}
    
    # Temel istatistikler
    cursor.execute("""
        SELECT 
            COUNT(*) as total_books,
            COALESCE(SUM(page_count), 0) as total_pages,
            ROUND(AVG(CASE WHEN rating > 0 THEN rating END), 1) as avg_rating,
            ROUND(AVG(page_count), 0) as avg_pages_per_book
        FROM books 
        WHERE status = 'read' 
            AND finish_date IS NOT NULL
            AND strftime('%Y', finish_date) = ?
    """, (str(year),))
    
    row = cursor.fetchone()
    summary["total_books"] = row["total_books"]
    summary["total_pages"] = row["total_pages"]
    summary["avg_rating"] = row["avg_rating"] or 0
    summary["avg_pages_per_book"] = int(row["avg_pages_per_book"] or 0)
    
    # En çok okunan yazarlar (bu yıl)
    cursor.execute("""
        SELECT author, COUNT(*) as count
        FROM books 
        WHERE status = 'read' 
            AND finish_date IS NOT NULL
            AND strftime('%Y', finish_date) = ?
            AND author IS NOT NULL AND author != ''
        GROUP BY author
        ORDER BY count DESC
        LIMIT 5
    """, (str(year),))
    summary["top_authors"] = [dict(row) for row in cursor.fetchall()]
    
    # En yüksek puanlı kitaplar
    cursor.execute("""
        SELECT title, author, rating
        FROM books 
        WHERE status = 'read' 
            AND finish_date IS NOT NULL
            AND strftime('%Y', finish_date) = ?
            AND rating IS NOT NULL AND rating > 0
        ORDER BY rating DESC, title
        LIMIT 5
    """, (str(year),))
    summary["top_rated_books"] = [dict(row) for row in cursor.fetchall()]
    
    # Aylık dağılım
    cursor.execute("""
        SELECT 
            CAST(strftime('%m', finish_date) AS INTEGER) as month,
            COUNT(*) as count
        FROM books 
        WHERE status = 'read' 
            AND finish_date IS NOT NULL
            AND strftime('%Y', finish_date) = ?
        GROUP BY month
        ORDER BY month
    """, (str(year),))
    
    monthly = {i: 0 for i in range(1, 13)}
    for row in cursor.fetchall():
        monthly[row["month"]] = row["count"]
    summary["monthly_breakdown"] = [{"month": m, "count": c} for m, c in monthly.items()]
    
    # Format dağılımı
    cursor.execute("""
        SELECT format, COUNT(*) as count
        FROM books 
        WHERE status = 'read' 
            AND finish_date IS NOT NULL
            AND strftime('%Y', finish_date) = ?
        GROUP BY format
    """, (str(year),))
    summary["formats"] = {row["format"] or "paperback": row["count"] for row in cursor.fetchall()}
    
    conn.close()
    return summary


# Bu dosya doğrudan çalıştırılırsa test et
if __name__ == "__main__":
    # Veritabanını oluştur
    init_database()
    
    # Test: Bir kitap ekle
    book_id = add_book(
        title="Suç ve Ceza",
        author="Fyodor Dostoyevski",
        page_count=687,
        publish_year=1866
    )
    print(f"Kitap eklendi, ID: {book_id}")
    
    # Test: Tüm kitapları listele
    books = get_all_books()
    print(f"\nToplam {len(books)} kitap var:")
    for book in books:
        print(f"  - {book['title']} ({book['author']})")