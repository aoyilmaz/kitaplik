"""
Kitaplık Uygulaması - Kitap API Servisi
=======================================
Birden fazla kaynaktan kitap arama:
- Google Books API
- Open Library
- 1000Kitap (Türkçe)
- Kitapyurdu (Türkçe)
"""

import requests
from pathlib import Path
from typing import Optional
import hashlib
import re
import urllib.parse


# Kapak görselleri klasörü
COVERS_DIR = Path(__file__).parent.parent / "assets" / "covers"

# API timeout (saniye)
TIMEOUT = 10

# User agent for scraping
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}


class BookSearchResult:
    """Arama sonucu için veri sınıfı."""
    
    def __init__(self, 
                 title: str = "",
                 author: str = "",
                 isbn: str = "",
                 publish_year: int = None,
                 publisher: str = "",
                 page_count: int = None,
                 cover_url: str = "",
                 description: str = "",
                 source: str = "",
                 subtitle: str = "",
                 language: str = "",
                 categories: str = ""):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.publish_year = publish_year
        self.publisher = publisher
        self.page_count = page_count
        self.cover_url = cover_url
        self.description = description
        self.source = source
        self.subtitle = subtitle
        self.language = language
        self.categories = categories
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "author": self.author,
            "isbn": self.isbn,
            "publish_year": self.publish_year,
            "publisher": self.publisher,
            "page_count": self.page_count,
            "cover_url": self.cover_url,
            "description": self.description,
            "source": self.source,
            "subtitle": self.subtitle,
            "language": self.language,
            "categories": self.categories,
        }
    
    def __repr__(self):
        return f"<BookSearchResult: {self.title} - {self.author}>"


# ==================== 1000KİTAP (TÜRKÇE) ====================

def search_1000kitap(query: str) -> list[BookSearchResult]:
    """
    1000Kitap.com'da arama yapar (Türkçe kitaplar için en iyi kaynak).
    """
    results = []
    
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://1000kitap.com/ara?q={encoded_query}"
        
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code != 200:
            return results
        
        html = response.text
        
        # Kitap kartlarını bul - farklı pattern'ler dene
        # Pattern 1: Kitap listesi
        pattern1 = r'<a[^>]*href="(/kitap/[^"]+)"[^>]*class="[^"]*"[^>]*>.*?<img[^>]*(?:data-src|src)="([^"]*)"[^>]*>.*?</a>'
        
        # Pattern 2: Başlık ve yazar
        pattern2 = r'<div[^>]*class="[^"]*book-title[^"]*"[^>]*>\s*<a[^>]*>([^<]+)</a>.*?<div[^>]*class="[^"]*book-author[^"]*"[^>]*>\s*<a[^>]*>([^<]+)</a>'
        
        # Tüm img tag'larından kapak URL'lerini çıkar
        img_pattern = r'<img[^>]*(?:data-src|src)="(https://[^"]*(?:covers|images|img)[^"]*\.(?:jpg|jpeg|png|webp))"'
        covers = re.findall(img_pattern, html, re.IGNORECASE)
        
        # Başlık ve yazarları bul
        title_author_pattern = r'<a[^>]*href="/kitap/[^"]*"[^>]*title="([^"]+)"[^>]*>.*?</a>.*?<a[^>]*href="/yazar/[^"]*"[^>]*>([^<]+)</a>'
        matches = re.findall(title_author_pattern, html, re.DOTALL)
        
        for i, match in enumerate(matches[:10]):
            title, author = match
            cover_url = covers[i] if i < len(covers) else ""
            
            book = BookSearchResult(
                title=title.strip(),
                author=author.strip(),
                cover_url=cover_url,
                source="1000kitap"
            )
            results.append(book)
        
        # Alternatif: JSON verisi ara
        if not results:
            json_pattern = r'\{"@type":"Book"[^}]*"name":"([^"]+)"[^}]*"author"[^}]*"name":"([^"]+)"[^}]*"image":"([^"]+)"'
            json_matches = re.findall(json_pattern, html)
            for match in json_matches[:10]:
                title, author, cover = match
                book = BookSearchResult(
                    title=title,
                    author=author,
                    cover_url=cover,
                    source="1000kitap"
                )
                results.append(book)
    
    except Exception as e:
        print(f"1000Kitap arama hatası: {e}")
    
    return results


# ==================== KİTAPYURDU (TÜRKÇE) ====================

def search_kitapyurdu(query: str) -> list[BookSearchResult]:
    """
    Kitapyurdu.com'da arama yapar.
    """
    results = []
    
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.kitapyurdu.com/index.php?route=product/search&filter_name={encoded_query}"
        
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code != 200:
            return results
        
        html = response.text
        
        # Ürün bloklarını bul
        # Her ürün product-cr class'ı içinde
        product_pattern = r'<div[^>]*class="[^"]*product-cr[^"]*"[^>]*>(.*?)<div[^>]*class="[^"]*product-cr[^"]*"'
        products = re.split(r'<div[^>]*class="[^"]*product-cr[^"]*"[^>]*>', html)
        
        for block in products[1:11]:  # İlk 10 ürün
            # Başlık
            title_match = re.search(r'<a[^>]*class="[^"]*pr-img-link[^"]*"[^>]*title="([^"]+)"', block)
            if not title_match:
                title_match = re.search(r'<div[^>]*class="[^"]*name[^"]*"[^>]*>.*?<a[^>]*>([^<]+)</a>', block, re.DOTALL)
            title = title_match.group(1).strip() if title_match else ""
            
            # Yazar
            author_match = re.search(r'<div[^>]*class="[^"]*author[^"]*"[^>]*>\s*<a[^>]*>([^<]+)</a>', block, re.DOTALL)
            author = author_match.group(1).strip() if author_match else ""
            
            # Kapak - data-src veya src
            img_match = re.search(r'<img[^>]*(?:data-src|src)="([^"]+)"[^>]*class="[^"]*lazy', block)
            if not img_match:
                img_match = re.search(r'<img[^>]*src="(https://[^"]+\.(?:jpg|jpeg|png|webp))"', block, re.IGNORECASE)
            cover_url = img_match.group(1) if img_match else ""
            
            # Yayınevi
            publisher_match = re.search(r'<div[^>]*class="[^"]*publisher[^"]*"[^>]*>.*?<span>([^<]+)</span>', block, re.DOTALL)
            publisher = publisher_match.group(1).strip() if publisher_match else ""
            
            if title:
                book = BookSearchResult(
                    title=title,
                    author=author,
                    publisher=publisher,
                    cover_url=cover_url,
                    source="kitapyurdu"
                )
                results.append(book)
    
    except Exception as e:
        print(f"Kitapyurdu arama hatası: {e}")
    
    return results


# ==================== BKM KİTAP (TÜRKÇE) ====================

def search_bkmkitap(query: str) -> list[BookSearchResult]:
    """
    BKM Kitap'ta arama yapar.
    """
    results = []
    
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.bkmkitap.com/arama?q={encoded_query}"
        
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code != 200:
            return results
        
        html = response.text
        
        # Ürün kartlarını bul
        # productItem class'ı ile işaretli
        blocks = re.split(r'<div[^>]*class="[^"]*productItem[^"]*"', html)
        
        for block in blocks[1:11]:
            # Başlık
            title_match = re.search(r'<a[^>]*class="[^"]*productName[^"]*"[^>]*title="([^"]+)"', block)
            if not title_match:
                title_match = re.search(r'<div[^>]*class="[^"]*productName[^"]*"[^>]*>.*?<a[^>]*>([^<]+)</a>', block, re.DOTALL)
            title = title_match.group(1).strip() if title_match else ""
            
            # Yazar
            author_match = re.search(r'<a[^>]*class="[^"]*productAuthor[^"]*"[^>]*>([^<]+)</a>', block)
            author = author_match.group(1).strip() if author_match else ""
            
            # Kapak
            img_match = re.search(r'<img[^>]*data-src="([^"]+)"', block)
            if not img_match:
                img_match = re.search(r'<img[^>]*src="(https://[^"]+\.(?:jpg|jpeg|png))"', block, re.IGNORECASE)
            cover_url = img_match.group(1) if img_match else ""
            
            if title:
                book = BookSearchResult(
                    title=title,
                    author=author,
                    cover_url=cover_url,
                    source="bkmkitap"
                )
                results.append(book)
    
    except Exception as e:
        print(f"BKM Kitap arama hatası: {e}")
    
    return results


# ==================== OPEN LIBRARY ====================

def search_openlibrary(query: str, search_type: str = "title") -> list[BookSearchResult]:
    """Open Library'de arama yapar."""
    results = []
    
    try:
        if search_type == "isbn":
            book = _fetch_openlibrary_by_isbn(query)
            if book:
                results.append(book)
        else:
            field = "title" if search_type == "title" else "author"
            encoded_query = urllib.parse.quote(query)
            url = f"https://openlibrary.org/search.json?{field}={encoded_query}&limit=10"
            
            response = requests.get(url, timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                
                for doc in data.get("docs", [])[:10]:
                    book = BookSearchResult(
                        title=doc.get("title", ""),
                        author=", ".join(doc.get("author_name", [])[:2]),
                        isbn=doc.get("isbn", [""])[0] if doc.get("isbn") else "",
                        publish_year=doc.get("first_publish_year"),
                        publisher=doc.get("publisher", [""])[0] if doc.get("publisher") else "",
                        page_count=doc.get("number_of_pages_median"),
                        cover_url=f"https://covers.openlibrary.org/b/id/{doc.get('cover_i')}-L.jpg" if doc.get("cover_i") else "",
                        source="openlibrary"
                    )
                    results.append(book)
    
    except Exception as e:
        print(f"Open Library arama hatası: {e}")
    
    return results


def _fetch_openlibrary_by_isbn(isbn: str) -> Optional[BookSearchResult]:
    """ISBN ile Open Library'den kitap bilgisi çeker."""
    isbn = isbn.replace("-", "").replace(" ", "").strip()
    
    try:
        url = f"https://openlibrary.org/isbn/{isbn}.json"
        response = requests.get(url, timeout=TIMEOUT)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        author = None
        authors = data.get("authors", [])
        if authors:
            author_key = authors[0].get("key")
            if author_key:
                author = _fetch_openlibrary_author(author_key)
        
        publish_year = None
        publish_date = data.get("publish_date", "")
        if publish_date:
            year_str = "".join(filter(str.isdigit, publish_date[-4:]))
            if year_str and len(year_str) == 4:
                publish_year = int(year_str)
        
        cover_url = ""
        covers = data.get("covers", [])
        if covers:
            cover_url = f"https://covers.openlibrary.org/b/id/{covers[0]}-L.jpg"
        
        return BookSearchResult(
            title=data.get("title", ""),
            author=author or "",
            isbn=isbn,
            publish_year=publish_year,
            publisher=data.get("publishers", [""])[0] if data.get("publishers") else "",
            page_count=data.get("number_of_pages"),
            cover_url=cover_url,
            source="openlibrary"
        )
    
    except Exception as e:
        print(f"Open Library ISBN hatası: {e}")
        return None


def _fetch_openlibrary_author(author_key: str) -> Optional[str]:
    """Yazar adını çeker."""
    try:
        url = f"https://openlibrary.org{author_key}.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json().get("name")
    except:
        pass
    return None


# ==================== GOOGLE BOOKS ====================

def search_google_books(query: str, search_type: str = "title") -> list[BookSearchResult]:
    """Google Books API'de arama yapar."""
    results = []
    
    try:
        if search_type == "isbn":
            q = f"isbn:{query}"
        elif search_type == "author":
            q = f"inauthor:{query}"
        else:
            q = f"intitle:{query}"
        
        encoded_q = urllib.parse.quote(q)
        url = f"https://www.googleapis.com/books/v1/volumes?q={encoded_q}&maxResults=10&langRestrict=tr"
        
        response = requests.get(url, timeout=TIMEOUT)
        if response.status_code != 200:
            return results
        
        data = response.json()
        
        for item in data.get("items", [])[:10]:
            vol = item.get("volumeInfo", {})
            
            isbn = ""
            for identifier in vol.get("industryIdentifiers", []):
                if identifier.get("type") in ["ISBN_13", "ISBN_10"]:
                    isbn = identifier.get("identifier", "")
                    break
            
            cover_url = ""
            if vol.get("imageLinks"):
                cover_url = vol["imageLinks"].get("large") or \
                           vol["imageLinks"].get("medium") or \
                           vol["imageLinks"].get("thumbnail", "")
                cover_url = cover_url.replace("http://", "https://")
                cover_url = re.sub(r'&zoom=\d', '', cover_url)
                cover_url = cover_url.replace("&edge=curl", "")
            
            publish_year = None
            published_date = vol.get("publishedDate", "")
            if published_date:
                year_str = published_date[:4]
                if year_str.isdigit():
                    publish_year = int(year_str)
            
            book = BookSearchResult(
                title=vol.get("title", ""),
                author=", ".join(vol.get("authors", [])[:2]),
                isbn=isbn,
                publish_year=publish_year,
                publisher=vol.get("publisher", ""),
                page_count=vol.get("pageCount"),
                cover_url=cover_url,
                description=vol.get("description", "")[:1000] if vol.get("description") else "",
                source="google",
                subtitle=vol.get("subtitle", ""),
                language=vol.get("language", ""),
                categories=", ".join(vol.get("categories", [])[:3]),
            )
            results.append(book)
    
    except Exception as e:
        print(f"Google Books arama hatası: {e}")
    
    return results


# ==================== BİRLEŞİK ARAMA ====================

def search_books(query: str, search_type: str = "title") -> list[BookSearchResult]:
    """
    Tüm kaynaklarda arama yapar ve sonuçları birleştirir.
    Türkçe kaynaklar öncelikli.
    """
    all_results = []
    seen_titles = set()
    
    def normalize_title(title: str) -> str:
        """Başlığı normalize et (karşılaştırma için)."""
        return re.sub(r'[^\w\s]', '', title.lower().strip())
    
    def add_results(results: list):
        for book in results:
            if not book.title:
                continue
            key = normalize_title(book.title)
            if key in seen_titles:
                for i, existing in enumerate(all_results):
                    if normalize_title(existing.title) == key:
                        if not existing.cover_url and book.cover_url:
                            all_results[i] = book
                        break
            else:
                seen_titles.add(key)
                all_results.append(book)
    
    # 1. Google Books (genelde iyi sonuç veriyor)
    google_results = search_google_books(query, search_type)
    add_results(google_results)
    
    # 2. Türkçe kaynaklar (sadece başlık araması)
    if search_type == "title":
        # Kitapyurdu
        kitapyurdu_results = search_kitapyurdu(query)
        add_results(kitapyurdu_results)
        
        # BKM Kitap
        bkm_results = search_bkmkitap(query)
        add_results(bkm_results)
        
        # 1000Kitap
        kitap1000_results = search_1000kitap(query)
        add_results(kitap1000_results)
    
    # 3. Open Library
    ol_results = search_openlibrary(query, search_type)
    add_results(ol_results)
    
    # Kapağı olanlar önce
    all_results.sort(key=lambda x: (0 if x.cover_url else 1))
    
    return all_results[:15]


def fetch_book_by_isbn(isbn: str) -> Optional[dict]:
    """ISBN ile kitap bilgisi çeker."""
    isbn = isbn.replace("-", "").replace(" ", "").strip()
    
    results = search_google_books(isbn, "isbn")
    if results:
        return results[0].to_dict()
    
    book = _fetch_openlibrary_by_isbn(isbn)
    if book:
        return book.to_dict()
    
    return None


# ==================== KAPAK İNDİRME ====================

def download_cover(cover_url: str, identifier: str = None) -> Optional[str]:
    """Kapak görselini indirir ve kaydeder."""
    if not cover_url:
        return None
    
    try:
        response = requests.get(cover_url, headers=HEADERS, timeout=TIMEOUT)
        
        if response.status_code != 200:
            return None
        
        # Geçerli görsel mi kontrol et (en az 1KB)
        if len(response.content) < 1000:
            return None
        
        # Dosya adı
        if not identifier:
            identifier = hashlib.md5(cover_url.encode()).hexdigest()[:12]
        
        # Güvenli dosya adı
        identifier = re.sub(r'[^\w\-]', '_', str(identifier))[:50]
        
        # Klasör yoksa oluştur
        COVERS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Dosyayı kaydet
        file_path = COVERS_DIR / f"{identifier}.jpg"
        file_path.write_bytes(response.content)
        
        return str(file_path)
        
    except Exception as e:
        print(f"Kapak indirme hatası: {e}")
        return None


def cover_exists(cover_path: str) -> bool:
    """Kapak dosyasının gerçekten var olup olmadığını kontrol eder."""
    if not cover_path:
        return False
    
    if cover_path.startswith("http://") or cover_path.startswith("https://"):
        return False
    
    return Path(cover_path).exists()


# ==================== TEST ====================

if __name__ == "__main__":
    print("=" * 50)
    print("Kitap Arama Testi (Türkçe Kaynaklar)")
    print("=" * 50)
    
    test_books = [
        "Suç ve Ceza",
        "Tutunamayanlar",
        "Kürk Mantolu Madonna",
        "İnce Memed",
    ]
    
    for book_name in test_books:
        print(f"\n📚 Aranan: '{book_name}'")
        results = search_books(book_name, "title")
        
        if results:
            for i, book in enumerate(results[:3], 1):
                cover_status = "✅" if book.cover_url else "❌"
                print(f"   {i}. {book.title} - {book.author} [{book.source}] {cover_status}")
        else:
            print("   Sonuç bulunamadı")
