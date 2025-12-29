"""
Kitaplık Uygulaması - AI Öneri Servisi (Ollama)
================================================
Yerel Ollama modeli ile kitap önerileri ve analiz.
"""

import json
import requests
from typing import Optional

# Ollama API endpoint
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

# Varsayılan model
DEFAULT_MODEL = "mistral"


def check_ollama_status() -> dict:
    """Ollama'nın çalışıp çalışmadığını kontrol eder."""
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            return {
                "available": True,
                "models": models,
                "recommended": get_best_model(models)
            }
    except requests.exceptions.ConnectionError:
        return {
            "available": False,
            "error": "Ollama çalışmıyor. 'ollama serve' komutu ile başlatın."
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }
    
    return {"available": False, "error": "Bilinmeyen hata"}


def get_best_model(models: list) -> str:
    """Mevcut modellerden en uygununu seçer."""
    # Tercih sırası
    preferred = ["mistral", "llama3.2", "llama3.1", "llama3", "llama2", "gemma2", "gemma", "phi3", "phi"]
    
    for pref in preferred:
        for model in models:
            if pref in model.lower():
                return model
    
    # Hiçbiri yoksa ilk modeli döndür
    return models[0] if models else DEFAULT_MODEL


def generate_response(prompt: str, model: str = None, context: str = None) -> Optional[str]:
    """Ollama'dan yanıt alır."""
    if model is None:
        status = check_ollama_status()
        if not status["available"]:
            return None
        model = status.get("recommended", DEFAULT_MODEL)
    
    full_prompt = prompt
    if context:
        full_prompt = f"{context}\n\n{prompt}"
    
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 1024,
                }
            },
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "").strip()
        else:
            return None
            
    except Exception as e:
        print(f"Ollama hatası: {e}")
        return None


def get_book_recommendation(books: list, preferences: dict = None, model: str = None) -> Optional[str]:
    """Kitaplığa göre öneri yapar."""
    
    # Kitap özetini oluştur
    book_summary = create_book_summary(books)
    
    # Tercihler
    pref_text = ""
    if preferences:
        if preferences.get("favorite_genres"):
            pref_text += f"Favori türleri: {', '.join(preferences['favorite_genres'])}\n"
        if preferences.get("favorite_authors"):
            pref_text += f"Favori yazarları: {', '.join(preferences['favorite_authors'])}\n"
        if preferences.get("mood"):
            pref_text += f"Şu anki ruh hali: {preferences['mood']}\n"
    
    prompt = f"""Sen bir kitap uzmanısın. Kullanıcının kitaplığını ve okuma geçmişini analiz edip kişiselleştirilmiş öneriler yapıyorsun.

Kullanıcının Kitaplığı:
{book_summary}

{pref_text}

Lütfen kullanıcıya 3-5 kitap öner. Önerilerini şu formatta ver:
1. **Kitap Adı** - Yazar
   Neden önerdiğin: [kısa açıklama]

Önerilerin kullanıcının zevkine uygun olmalı. Kitaplığındaki kitaplara benzer ama farklı kitaplar öner.
Türkçe yanıt ver."""

    return generate_response(prompt, model)


def analyze_reading_habits(books: list, model: str = None) -> Optional[str]:
    """Okuma alışkanlıklarını analiz eder."""
    
    book_summary = create_book_summary(books)
    
    prompt = f"""Sen bir kitap uzmanısın. Kullanıcının okuma alışkanlıklarını analiz et.

Kullanıcının Kitaplığı:
{book_summary}

Lütfen şunları analiz et:
1. Favori türler/kategoriler
2. Favori yazarlar
3. Okuma hızı (varsa)
4. Tercih ettiği kitap uzunluğu
5. Dikkat çeken kalıplar

Kısa ve öz bir analiz yap. Türkçe yanıt ver."""

    return generate_response(prompt, model)


def get_similar_books(book_title: str, book_author: str, books: list = None, model: str = None) -> Optional[str]:
    """Benzer kitap önerileri yapar."""
    
    context = ""
    if books:
        owned_titles = [b.get("title", "") for b in books]
        context = f"Kullanıcının kitaplığında şu kitaplar var: {', '.join(owned_titles[:20])}"
    
    prompt = f""""{book_title}" - {book_author} kitabını okuyan birine benzer kitaplar öner.

{context}

5 kitap öner. Kitaplığında zaten olan kitapları önerme.
Her öneri için kısa bir açıklama yaz.

Format:
1. **Kitap Adı** - Yazar: [neden benzer]

Türkçe yanıt ver."""

    return generate_response(prompt, model)


def get_reading_plan(books: list, goal: int = None, model: str = None) -> Optional[str]:
    """Okuma planı oluşturur."""
    
    # Okunmamış kitapları bul
    unread = [b for b in books if b.get("status") == "unread"]
    reading = [b for b in books if b.get("status") == "reading"]
    
    unread_list = "\n".join([f"- {b.get('title', '')} ({b.get('page_count', '?')} sayfa)" for b in unread[:15]])
    reading_list = "\n".join([f"- {b.get('title', '')} (sayfa {b.get('current_page', 0)}/{b.get('page_count', '?')})" for b in reading])
    
    goal_text = f"Yıllık hedef: {goal} kitap" if goal else ""
    
    prompt = f"""Kullanıcı için bir okuma planı oluştur.

Şu an okuduğu kitaplar:
{reading_list or "Yok"}

Okunmamış kitaplar:
{unread_list or "Yok"}

{goal_text}

Lütfen önümüzdeki 1-2 ay için bir okuma planı öner.
Kitapları hangi sırayla okuması gerektiğini ve nedenini açıkla.
Türkçe yanıt ver."""

    return generate_response(prompt, model)


def ask_about_book(book: dict, question: str, model: str = None) -> Optional[str]:
    """Belirli bir kitap hakkında soru yanıtlar."""
    
    book_info = f"""
Kitap: {book.get('title', '')}
Yazar: {book.get('author', '')}
Kategori: {book.get('categories', '')}
Sayfa: {book.get('page_count', '')}
Yayın Yılı: {book.get('publish_year', '')}
Açıklama: {book.get('description', '')[:500] if book.get('description') else 'Yok'}
"""
    
    prompt = f"""Şu kitap hakkında bir soru var:

{book_info}

Soru: {question}

Kısa ve bilgilendirici bir yanıt ver. Türkçe yanıt ver."""

    return generate_response(prompt, model)


def get_series_reading_order(series_name: str, books: list = None, model: str = None) -> Optional[str]:
    """Seri okuma sırasını önerir."""
    
    owned = ""
    if books:
        series_books = [b for b in books if b.get("series_name", "").lower() == series_name.lower()]
        if series_books:
            owned = "Kullanıcının sahip olduğu kitaplar:\n"
            for b in series_books:
                status = {"read": "✅ Okundu", "reading": "📖 Okunuyor", "unread": "📕 Okunmadı"}.get(b.get("status"), "")
                owned += f"- #{b.get('series_order', '?')} {b.get('title', '')} {status}\n"
    
    prompt = f""""{series_name}" serisi hakkında bilgi ver.

{owned}

1. Bu serinin doğru okuma sırası nedir?
2. Seri kaç kitaptan oluşuyor?
3. Seri hakkında kısa bilgi ver.

Türkçe yanıt ver."""

    return generate_response(prompt, model)


def create_book_summary(books: list) -> str:
    """Kitap listesinden özet oluşturur."""
    
    if not books:
        return "Kitaplık boş."
    
    # İstatistikler
    total = len(books)
    read = len([b for b in books if b.get("status") == "read"])
    reading = len([b for b in books if b.get("status") == "reading"])
    
    # Yazarlar
    authors = {}
    for b in books:
        author = b.get("author", "Bilinmiyor")
        if author:
            authors[author] = authors.get(author, 0) + 1
    top_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Kategoriler
    categories = {}
    for b in books:
        cats = b.get("categories", "")
        if cats:
            for cat in cats.split(","):
                cat = cat.strip()
                if cat:
                    categories[cat] = categories.get(cat, 0) + 1
    top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # En yüksek puanlı kitaplar
    rated_books = [b for b in books if b.get("rating") and b.get("rating") >= 4]
    rated_books.sort(key=lambda x: x.get("rating", 0), reverse=True)
    
    # Son okunanlar
    recent_read = [b for b in books if b.get("status") == "read" and b.get("finish_date")]
    recent_read.sort(key=lambda x: x.get("finish_date", ""), reverse=True)
    
    summary = f"""
Toplam: {total} kitap ({read} okundu, {reading} okunuyor)

En Çok Okunan Yazarlar:
{chr(10).join([f"- {a}: {c} kitap" for a, c in top_authors]) if top_authors else "Veri yok"}

Kategoriler:
{chr(10).join([f"- {c}: {n} kitap" for c, n in top_categories]) if top_categories else "Veri yok"}

En Beğenilen Kitaplar (4-5 yıldız):
{chr(10).join([f"- {b.get('title', '')} ({b.get('author', '')}) - {'⭐' * b.get('rating', 0)}" for b in rated_books[:5]]) if rated_books else "Henüz puanlanan kitap yok"}

Son Okunanlar:
{chr(10).join([f"- {b.get('title', '')} ({b.get('author', '')})" for b in recent_read[:5]]) if recent_read else "Veri yok"}
"""
    
    return summary.strip()


# Test
if __name__ == "__main__":
    print("Ollama durumu kontrol ediliyor...")
    status = check_ollama_status()
    print(f"Durum: {status}")
    
    if status["available"]:
        print(f"\nÖnerilen model: {status['recommended']}")
        print(f"Mevcut modeller: {', '.join(status['models'])}")
        
        # Test prompt
        response = generate_response("Merhaba, nasılsın?", status["recommended"])
        print(f"\nTest yanıtı: {response}")
