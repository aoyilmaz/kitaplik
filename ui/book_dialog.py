"""
Kitaplık Uygulaması - Kitap Dialog'ları
=======================================
1. SearchBookDialog - Online arama ile kitap ekleme
2. ManualBookDialog - Manuel kitap ekleme/düzenleme (tüm alanlar)
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGridLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QTextEdit,
    QLabel,
    QMessageBox,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
    QWidget,
    QDateEdit,
    QCheckBox,
    QScrollArea,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QDate, QByteArray
from PyQt6.QtGui import QPixmap

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from services.book_api import search_books, download_cover


# ============================================================
# ARAMA THREAD'İ
# ============================================================

class SearchThread(QThread):
    """Arka planda arama yapan thread."""
    
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, query: str, search_type: str):
        super().__init__()
        self.query = query
        self.search_type = search_type
    
    def run(self):
        try:
            results = search_books(self.query, self.search_type)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


# ============================================================
# ARAMA İLE KİTAP EKLEME DIALOG'U
# ============================================================

class SearchBookDialog(QDialog):
    """Online arama ile kitap ekleme."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.search_thread = None
        self.search_results = []
        self.selected_book = None
        self.cover_path = None
        
        self.setWindowTitle("🔍 Kitap Ara ve Ekle")
        self.setMinimumSize(700, 600)
        self.setModal(True)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # === ARAMA ===
        search_group = QGroupBox("Arama")
        search_layout = QVBoxLayout(search_group)
        
        search_row = QHBoxLayout()
        
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItem("📖 Başlık", "title")
        self.search_type_combo.addItem("✍️ Yazar", "author")
        self.search_type_combo.addItem("🔢 ISBN", "isbn")
        self.search_type_combo.setFixedWidth(120)
        search_row.addWidget(self.search_type_combo)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Aramak istediğiniz terimi girin...")
        self.search_input.returnPressed.connect(self.on_search)
        search_row.addWidget(self.search_input)
        
        self.search_btn = QPushButton("🔍 Ara")
        self.search_btn.clicked.connect(self.on_search)
        self.search_btn.setFixedWidth(100)
        search_row.addWidget(self.search_btn)
        
        search_layout.addLayout(search_row)
        
        self.status_label = QLabel("Kitap adı, yazar veya ISBN ile arama yapın.")
        self.status_label.setStyleSheet("color: #858585;")
        search_layout.addWidget(self.status_label)
        
        layout.addWidget(search_group)
        
        # === SONUÇLAR ===
        results_group = QGroupBox("Sonuçlar")
        results_layout = QVBoxLayout(results_group)
        
        self.results_list = QListWidget()
        self.results_list.setMinimumHeight(300)
        self.results_list.itemClicked.connect(self.on_result_clicked)
        self.results_list.itemDoubleClicked.connect(self.on_result_double_clicked)
        self.results_list.setStyleSheet("""
            QListWidget::item { padding: 10px; border-bottom: 1px solid #3C3C3C; }
            QListWidget::item:selected { background-color: #0078D4; }
            QListWidget::item:hover:!selected { background-color: #2D2D2D; }
        """)
        results_layout.addWidget(self.results_list)
        
        self.selected_label = QLabel("")
        self.selected_label.setStyleSheet("color: #4EC9B0; font-weight: bold;")
        results_layout.addWidget(self.selected_label)
        
        layout.addWidget(results_group)
        
        # === BUTONLAR ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.add_btn = QPushButton("➕ Ekle")
        self.add_btn.setEnabled(False)
        self.add_btn.clicked.connect(self.on_add)
        button_layout.addWidget(self.add_btn)
        
        layout.addLayout(button_layout)
    
    def on_search(self):
        query = self.search_input.text().strip()
        if not query:
            return
        
        search_type = self.search_type_combo.currentData()
        
        self.search_btn.setEnabled(False)
        self.search_btn.setText("...")
        self.status_label.setText("Aranıyor...")
        self.results_list.clear()
        self.selected_book = None
        self.add_btn.setEnabled(False)
        self.selected_label.setText("")
        
        self.search_thread = SearchThread(query, search_type)
        self.search_thread.finished.connect(self.on_search_finished)
        self.search_thread.error.connect(self.on_search_error)
        self.search_thread.start()
    
    def on_search_finished(self, results):
        self.search_btn.setEnabled(True)
        self.search_btn.setText("🔍 Ara")
        self.search_results = results
        
        if not results:
            self.status_label.setText("Sonuç bulunamadı.")
            return
        
        sorted_results = sorted(results, key=lambda b: (not bool(b.cover_url), b.title))
        self.status_label.setText(f"{len(sorted_results)} sonuç bulundu.")
        
        for book in sorted_results:
            cover_icon = "🖼️" if book.cover_url else "📄"
            year_str = f" ({book.publish_year})" if book.publish_year else ""
            author_str = f" • {book.author}" if book.author else ""
            source = "Google" if book.source == "google" else "OpenLib"
            
            text = f"{cover_icon}  {book.title}{year_str}{author_str}  [{source}]"
            
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, book)
            
            tooltip = f"📖 {book.title}"
            if book.subtitle:
                tooltip += f"\n   {book.subtitle}"
            if book.author:
                tooltip += f"\n✍️ {book.author}"
            if book.publisher:
                tooltip += f"\n🏢 {book.publisher}"
            if book.page_count:
                tooltip += f"\n📄 {book.page_count} sayfa"
            if book.categories:
                tooltip += f"\n📁 {book.categories}"
            if book.language:
                tooltip += f"\n🌐 {book.language.upper()}"
            item.setToolTip(tooltip)
            
            self.results_list.addItem(item)
    
    def on_search_error(self, error_msg):
        self.search_btn.setEnabled(True)
        self.search_btn.setText("🔍 Ara")
        self.status_label.setText(f"Hata: {error_msg}")
    
    def on_result_clicked(self, item):
        book = item.data(Qt.ItemDataRole.UserRole)
        if book:
            self.selected_book = book
            self.add_btn.setEnabled(True)
            self.selected_label.setText(f"✓ Seçilen: {book.title}")
    
    def on_result_double_clicked(self, item):
        self.on_result_clicked(item)
        self.on_add()
    
    def on_add(self):
        if not self.selected_book:
            return
        
        if self.selected_book.cover_url:
            identifier = self.selected_book.isbn or self.selected_book.title[:20].replace(" ", "_")
            self.cover_path = download_cover(self.selected_book.cover_url, identifier)
        
        self.accept()
    
    def get_data(self) -> dict:
        if not self.selected_book:
            return {}
        
        return {
            "title": self.selected_book.title,
            "author": self.selected_book.author or None,
            "isbn": self.selected_book.isbn or None,
            "page_count": self.selected_book.page_count,
            "publish_year": self.selected_book.publish_year,
            "publisher": self.selected_book.publisher or None,
            "cover_path": self.cover_path,
            "subtitle": self.selected_book.subtitle or None,
            "description": self.selected_book.description or None,
            "language": self.selected_book.language or None,
            "categories": self.selected_book.categories or None,
        }


# ============================================================
# MANUEL KİTAP EKLEME/DÜZENLEME DIALOG'U (TÜM ALANLAR)
# ============================================================

class ManualBookDialog(QDialog):
    """Manuel kitap ekleme veya düzenleme - tüm alanlarla."""
    
    def __init__(self, parent=None, book=None):
        super().__init__(parent)
        
        self.book = book
        self.cover_path = book.get("cover_path") if book else None
        
        title = "📖 Kitap Düzenle" if book else "✏️ Manuel Kitap Ekle"
        self.setWindowTitle(title)
        self.setMinimumSize(700, 650)
        self.setModal(True)
        
        self.setup_ui()
        
        if book:
            self.populate_form(book)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Ana içerik - Tab widget
        self.tabs = QTabWidget()
        
        # === TAB 1: TEMEL BİLGİLER ===
        tab1 = QWidget()
        tab1_layout = QHBoxLayout(tab1)
        
        # Sol: Form
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Kitap başlığı (zorunlu)")
        form_layout.addRow("Başlık *:", self.title_input)
        
        self.subtitle_input = QLineEdit()
        self.subtitle_input.setPlaceholderText("Alt başlık")
        form_layout.addRow("Alt Başlık:", self.subtitle_input)
        
        self.author_input = QLineEdit()
        self.author_input.setPlaceholderText("Yazar adı")
        form_layout.addRow("Yazar:", self.author_input)
        
        self.isbn_input = QLineEdit()
        self.isbn_input.setPlaceholderText("ISBN numarası")
        form_layout.addRow("ISBN:", self.isbn_input)
        
        self.publisher_input = QLineEdit()
        self.publisher_input.setPlaceholderText("Yayınevi")
        form_layout.addRow("Yayınevi:", self.publisher_input)
        
        self.year_input = QSpinBox()
        self.year_input.setRange(0, 2100)
        self.year_input.setSpecialValueText("-")
        form_layout.addRow("Yayın Yılı:", self.year_input)
        
        self.page_count_input = QSpinBox()
        self.page_count_input.setRange(0, 99999)
        self.page_count_input.setSpecialValueText("-")
        form_layout.addRow("Sayfa Sayısı:", self.page_count_input)
        
        self.language_input = QComboBox()
        self.language_input.setEditable(True)
        self.language_input.addItems(["", "tr", "en", "de", "fr", "es", "it", "ru", "ar", "ja", "zh"])
        form_layout.addRow("Dil:", self.language_input)
        
        self.categories_input = QLineEdit()
        self.categories_input.setPlaceholderText("Roman, Bilim Kurgu, Tarih...")
        form_layout.addRow("Kategoriler:", self.categories_input)
        
        self.format_input = QComboBox()
        self.format_input.addItems(["📕 Karton Kapak", "📗 Ciltli", "📱 E-Kitap", "🎧 Sesli Kitap"])
        form_layout.addRow("Format:", self.format_input)
        
        tab1_layout.addLayout(form_layout, stretch=2)
        
        # Sağ: Kapak
        cover_layout = QVBoxLayout()
        
        self.cover_label = QLabel()
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setFixedSize(140, 200)
        self.cover_label.setText("📖")
        self.cover_label.setStyleSheet("background-color: #2D2D2D; border-radius: 8px; font-size: 48px;")
        cover_layout.addWidget(self.cover_label)
        
        # Kapak butonları
        cover_btn_layout = QVBoxLayout()
        cover_btn_layout.setSpacing(5)
        
        self.search_cover_btn = QPushButton("🔍 Kapak Ara")
        self.search_cover_btn.clicked.connect(self.search_cover)
        cover_btn_layout.addWidget(self.search_cover_btn)
        
        self.select_cover_btn = QPushButton("📁 Dosyadan Seç")
        self.select_cover_btn.clicked.connect(self.select_cover_file)
        cover_btn_layout.addWidget(self.select_cover_btn)
        
        self.remove_cover_btn = QPushButton("🗑️ Kapağı Kaldır")
        self.remove_cover_btn.clicked.connect(self.remove_cover)
        cover_btn_layout.addWidget(self.remove_cover_btn)
        
        cover_layout.addLayout(cover_btn_layout)
        cover_layout.addStretch()
        tab1_layout.addLayout(cover_layout)
        
        self.tabs.addTab(tab1, "📚 Temel Bilgiler")
        
        # === TAB 2: ÇEVİRİ & SERİ ===
        tab2 = QWidget()
        tab2_layout = QFormLayout(tab2)
        tab2_layout.setSpacing(10)
        
        self.translator_input = QLineEdit()
        self.translator_input.setPlaceholderText("Çevirmen adı")
        tab2_layout.addRow("Çevirmen:", self.translator_input)
        
        self.original_title_input = QLineEdit()
        self.original_title_input.setPlaceholderText("Orijinal başlık")
        tab2_layout.addRow("Orijinal Başlık:", self.original_title_input)
        
        self.original_language_input = QComboBox()
        self.original_language_input.setEditable(True)
        self.original_language_input.addItems(["", "en", "de", "fr", "es", "ru", "ja", "zh"])
        tab2_layout.addRow("Orijinal Dil:", self.original_language_input)
        
        tab2_layout.addRow(QLabel(""))  # Boşluk
        
        self.series_name_input = QLineEdit()
        self.series_name_input.setPlaceholderText("Seri adı (örn: Harry Potter)")
        tab2_layout.addRow("Seri Adı:", self.series_name_input)
        
        self.series_order_input = QSpinBox()
        self.series_order_input.setRange(0, 999)
        self.series_order_input.setSpecialValueText("-")
        tab2_layout.addRow("Seri Sırası:", self.series_order_input)
        
        self.tabs.addTab(tab2, "🔄 Çeviri & Seri")
        
        # === TAB 3: OKUMA TAKİBİ ===
        tab3 = QWidget()
        tab3_layout = QFormLayout(tab3)
        tab3_layout.setSpacing(10)
        
        self.status_input = QComboBox()
        self.status_input.addItems(["📕 Okunmadı", "📖 Okunuyor", "📗 Okundu"])
        self.status_input.currentIndexChanged.connect(self.on_status_changed)
        tab3_layout.addRow("Durum:", self.status_input)
        
        self.current_page_input = QSpinBox()
        self.current_page_input.setRange(0, 99999)
        self.current_page_input.setSpecialValueText("-")
        tab3_layout.addRow("Mevcut Sayfa:", self.current_page_input)
        
        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setSpecialValueText("Seçilmedi")
        self.start_date_input.setDate(QDate(2000, 1, 1))
        tab3_layout.addRow("Başlama Tarihi:", self.start_date_input)
        
        self.finish_date_input = QDateEdit()
        self.finish_date_input.setCalendarPopup(True)
        self.finish_date_input.setSpecialValueText("Seçilmedi")
        self.finish_date_input.setDate(QDate(2000, 1, 1))
        tab3_layout.addRow("Bitirme Tarihi:", self.finish_date_input)
        
        self.times_read_input = QSpinBox()
        self.times_read_input.setRange(0, 99)
        self.times_read_input.setSpecialValueText("-")
        tab3_layout.addRow("Okuma Sayısı:", self.times_read_input)
        
        self.rating_input = QComboBox()
        self.rating_input.addItems(["-", "⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"])
        tab3_layout.addRow("Puan:", self.rating_input)
        
        self.tabs.addTab(tab3, "📊 Okuma Takibi")
        
        # === TAB 4: NOTLAR ===
        tab4 = QWidget()
        tab4_layout = QVBoxLayout(tab4)
        
        tab4_layout.addWidget(QLabel("Kısa Notlar:"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Kısa notlarınız...")
        self.notes_input.setMaximumHeight(80)
        tab4_layout.addWidget(self.notes_input)
        
        tab4_layout.addWidget(QLabel("İnceleme / Değerlendirme:"))
        self.review_input = QTextEdit()
        self.review_input.setPlaceholderText("Detaylı incelemeniz...")
        tab4_layout.addWidget(self.review_input)
        
        tab4_layout.addWidget(QLabel("Açıklama / Özet:"))
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Kitap açıklaması...")
        self.description_input.setMaximumHeight(80)
        tab4_layout.addWidget(self.description_input)
        
        self.tabs.addTab(tab4, "📝 Notlar")
        
        # === TAB 5: SATIN ALMA & KONUM ===
        tab5 = QWidget()
        tab5_layout = QFormLayout(tab5)
        tab5_layout.setSpacing(10)
        
        self.purchase_date_input = QDateEdit()
        self.purchase_date_input.setCalendarPopup(True)
        self.purchase_date_input.setSpecialValueText("Seçilmedi")
        self.purchase_date_input.setDate(QDate(2000, 1, 1))
        tab5_layout.addRow("Satın Alma Tarihi:", self.purchase_date_input)
        
        self.purchase_place_input = QLineEdit()
        self.purchase_place_input.setPlaceholderText("D&R, Amazon, Sahaf...")
        tab5_layout.addRow("Satın Alma Yeri:", self.purchase_place_input)
        
        price_layout = QHBoxLayout()
        self.purchase_price_input = QDoubleSpinBox()
        self.purchase_price_input.setRange(0, 99999)
        self.purchase_price_input.setDecimals(2)
        self.purchase_price_input.setSpecialValueText("-")
        price_layout.addWidget(self.purchase_price_input)
        self.currency_input = QComboBox()
        self.currency_input.addItems(["TRY", "USD", "EUR", "GBP"])
        self.currency_input.setFixedWidth(70)
        price_layout.addWidget(self.currency_input)
        tab5_layout.addRow("Fiyat:", price_layout)
        
        self.is_gift_check = QCheckBox("Bu kitap hediye")
        tab5_layout.addRow("", self.is_gift_check)
        
        self.gifted_by_input = QLineEdit()
        self.gifted_by_input.setPlaceholderText("Hediye eden kişi")
        tab5_layout.addRow("Hediye Eden:", self.gifted_by_input)
        
        tab5_layout.addRow(QLabel(""))  # Boşluk
        
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Salon rafı, Yatak odası...")
        tab5_layout.addRow("Konum:", self.location_input)
        
        self.is_borrowed_check = QCheckBox("Ödünç verildi")
        tab5_layout.addRow("", self.is_borrowed_check)
        
        self.borrowed_to_input = QLineEdit()
        self.borrowed_to_input.setPlaceholderText("Kime verildi")
        tab5_layout.addRow("Ödünç Alan:", self.borrowed_to_input)
        
        self.borrowed_date_input = QDateEdit()
        self.borrowed_date_input.setCalendarPopup(True)
        self.borrowed_date_input.setSpecialValueText("Seçilmedi")
        self.borrowed_date_input.setDate(QDate(2000, 1, 1))
        tab5_layout.addRow("Ödünç Tarihi:", self.borrowed_date_input)
        
        self.tabs.addTab(tab5, "💰 Satın Alma")
        
        # === TAB 6: ETİKETLER ===
        tab6 = QWidget()
        tab6_layout = QVBoxLayout(tab6)
        
        tab6_layout.addWidget(QLabel("Etiketler (virgülle ayırın):"))
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("favori, imzalı, nadir, hediye...")
        tab6_layout.addWidget(self.tags_input)
        
        tab6_layout.addStretch()
        
        self.tabs.addTab(tab6, "🏷️ Etiketler")
        
        layout.addWidget(self.tabs)
        
        # === BUTONLAR ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.on_save)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def on_status_changed(self, index):
        """Durum değişince ilgili alanları aktif/pasif yap."""
        # Okunuyor ise mevcut sayfa aktif
        self.current_page_input.setEnabled(index == 1)
    
    def show_cover(self, path: str):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(140, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.cover_label.setPixmap(scaled)
            self.cover_label.setStyleSheet("border-radius: 8px;")
    
    def populate_form(self, book):
        """Formu mevcut verilerle doldur."""
        # Temel bilgiler
        self.title_input.setText(book.get("title", "") or "")
        self.subtitle_input.setText(book.get("subtitle", "") or "")
        self.author_input.setText(book.get("author", "") or "")
        self.isbn_input.setText(book.get("isbn", "") or "")
        self.publisher_input.setText(book.get("publisher", "") or "")
        if book.get("publish_year"):
            self.year_input.setValue(book["publish_year"])
        if book.get("page_count"):
            self.page_count_input.setValue(book["page_count"])
        self.language_input.setCurrentText(book.get("language", "") or "")
        self.categories_input.setText(book.get("categories", "") or "")
        
        # Format
        format_map = {"paperback": 0, "hardcover": 1, "ebook": 2, "audiobook": 3}
        self.format_input.setCurrentIndex(format_map.get(book.get("format", "paperback"), 0))
        
        # Çeviri & Seri
        self.translator_input.setText(book.get("translator", "") or "")
        self.original_title_input.setText(book.get("original_title", "") or "")
        self.original_language_input.setCurrentText(book.get("original_language", "") or "")
        self.series_name_input.setText(book.get("series_name", "") or "")
        if book.get("series_order"):
            self.series_order_input.setValue(book["series_order"])
        
        # Okuma takibi
        status_map = {"unread": 0, "reading": 1, "read": 2}
        self.status_input.setCurrentIndex(status_map.get(book.get("status"), 0))
        if book.get("current_page"):
            self.current_page_input.setValue(book["current_page"])
        if book.get("start_date"):
            self.start_date_input.setDate(QDate.fromString(book["start_date"], "yyyy-MM-dd"))
        if book.get("finish_date"):
            self.finish_date_input.setDate(QDate.fromString(book["finish_date"], "yyyy-MM-dd"))
        if book.get("times_read"):
            self.times_read_input.setValue(book["times_read"])
        self.rating_input.setCurrentIndex(book.get("rating") or 0)
        
        # Notlar
        self.notes_input.setPlainText(book.get("notes", "") or "")
        self.review_input.setPlainText(book.get("review", "") or "")
        self.description_input.setPlainText(book.get("description", "") or "")
        
        # Satın alma
        if book.get("purchase_date"):
            self.purchase_date_input.setDate(QDate.fromString(book["purchase_date"], "yyyy-MM-dd"))
        self.purchase_place_input.setText(book.get("purchase_place", "") or "")
        if book.get("purchase_price"):
            self.purchase_price_input.setValue(book["purchase_price"])
        self.currency_input.setCurrentText(book.get("currency", "TRY") or "TRY")
        self.is_gift_check.setChecked(book.get("is_gift", 0) == 1)
        self.gifted_by_input.setText(book.get("gifted_by", "") or "")
        
        # Konum & Ödünç
        self.location_input.setText(book.get("location", "") or "")
        self.is_borrowed_check.setChecked(book.get("is_borrowed", 0) == 1)
        self.borrowed_to_input.setText(book.get("borrowed_to", "") or "")
        if book.get("borrowed_date"):
            self.borrowed_date_input.setDate(QDate.fromString(book["borrowed_date"], "yyyy-MM-dd"))
        
        # Etiketler
        self.tags_input.setText(book.get("tags", "") or "")
        
        # Kapak
        if book.get("cover_path"):
            self.cover_path = book["cover_path"]
            self.show_cover(book["cover_path"])
    
    def search_cover(self):
        """Kapak ara dialog'unu aç."""
        title = self.title_input.text().strip()
        author = self.author_input.text().strip()
        
        if not title:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce kitap başlığını girin!")
            return
        
        dialog = CoverSearchDialog(title, author, self)
        if dialog.exec():
            if dialog.selected_cover_path:
                self.cover_path = dialog.selected_cover_path
                self.show_cover(self.cover_path)
    
    def select_cover_file(self):
        """Dosyadan kapak seç."""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Kapak Görseli Seç",
            "",
            "Görseller (*.jpg *.jpeg *.png *.webp);;Tüm Dosyalar (*)"
        )
        
        if file_path:
            # Kapağı assets/covers klasörüne kopyala
            import shutil
            from pathlib import Path
            
            covers_dir = Path(__file__).parent.parent / "assets" / "covers"
            covers_dir.mkdir(parents=True, exist_ok=True)
            
            # Benzersiz dosya adı
            import hashlib
            file_hash = hashlib.md5(file_path.encode()).hexdigest()[:12]
            ext = Path(file_path).suffix or ".jpg"
            dest_path = covers_dir / f"{file_hash}{ext}"
            
            shutil.copy2(file_path, dest_path)
            
            self.cover_path = str(dest_path)
            self.show_cover(self.cover_path)
    
    def remove_cover(self):
        """Kapağı kaldır."""
        self.cover_path = None
        self.cover_label.setPixmap(QPixmap())
        self.cover_label.setText("📖")
        self.cover_label.setStyleSheet("background-color: #2D2D2D; border-radius: 8px; font-size: 48px;")
    
    def on_save(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Uyarı", "Başlık zorunludur!")
            self.title_input.setFocus()
            return
        self.accept()
    
    def _get_date_value(self, date_edit):
        """Tarih alanından değer al, 2000-01-01 ise None döndür."""
        date = date_edit.date()
        if date.year() == 2000 and date.month() == 1 and date.day() == 1:
            return None
        return date.toString("yyyy-MM-dd")
    
    def get_data(self) -> dict:
        format_map = {0: "paperback", 1: "hardcover", 2: "ebook", 3: "audiobook"}
        status_map = {0: "unread", 1: "reading", 2: "read"}
        
        return {
            # Temel
            "title": self.title_input.text().strip(),
            "subtitle": self.subtitle_input.text().strip() or None,
            "author": self.author_input.text().strip() or None,
            "isbn": self.isbn_input.text().strip() or None,
            "publisher": self.publisher_input.text().strip() or None,
            "publish_year": self.year_input.value() or None,
            "page_count": self.page_count_input.value() or None,
            "language": self.language_input.currentText().strip() or None,
            "categories": self.categories_input.text().strip() or None,
            "format": format_map.get(self.format_input.currentIndex(), "paperback"),
            "cover_path": self.cover_path,
            
            # Çeviri & Seri
            "translator": self.translator_input.text().strip() or None,
            "original_title": self.original_title_input.text().strip() or None,
            "original_language": self.original_language_input.currentText().strip() or None,
            "series_name": self.series_name_input.text().strip() or None,
            "series_order": self.series_order_input.value() or None,
            
            # Okuma takibi
            "status": status_map.get(self.status_input.currentIndex(), "unread"),
            "current_page": self.current_page_input.value() or None,
            "start_date": self._get_date_value(self.start_date_input),
            "finish_date": self._get_date_value(self.finish_date_input),
            "times_read": self.times_read_input.value() or None,
            "rating": self.rating_input.currentIndex() or None,
            
            # Notlar
            "notes": self.notes_input.toPlainText().strip() or None,
            "review": self.review_input.toPlainText().strip() or None,
            "description": self.description_input.toPlainText().strip() or None,
            
            # Satın alma
            "purchase_date": self._get_date_value(self.purchase_date_input),
            "purchase_place": self.purchase_place_input.text().strip() or None,
            "purchase_price": self.purchase_price_input.value() or None,
            "currency": self.currency_input.currentText(),
            "is_gift": 1 if self.is_gift_check.isChecked() else 0,
            "gifted_by": self.gifted_by_input.text().strip() or None,
            
            # Konum & Ödünç
            "location": self.location_input.text().strip() or None,
            "is_borrowed": 1 if self.is_borrowed_check.isChecked() else 0,
            "borrowed_to": self.borrowed_to_input.text().strip() or None,
            "borrowed_date": self._get_date_value(self.borrowed_date_input),
            
            # Etiketler
            "tags": self.tags_input.text().strip() or None,
        }


# ============================================================
# KAPAK ARAMA DIALOG'U
# ============================================================

class CoverSearchDialog(QDialog):
    """Kitap kapağı arama dialog'u."""
    
    def __init__(self, title: str, author: str = "", parent=None):
        super().__init__(parent)
        
        self.title = title
        self.author = author
        self.search_results = []
        self.selected_cover_path = None
        self.search_thread = None
        
        self.setWindowTitle("🖼️ Kapak Ara")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        self.setup_ui()
        
        # Otomatik arama başlat
        self.do_search()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Arama satırı
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setText(f"{self.title} {self.author}".strip())
        self.search_input.returnPressed.connect(self.do_search)
        search_layout.addWidget(self.search_input)
        
        self.search_btn = QPushButton("🔍 Ara")
        self.search_btn.clicked.connect(self.do_search)
        search_layout.addWidget(self.search_btn)
        
        layout.addLayout(search_layout)
        
        # Durum
        self.status_label = QLabel("Aranıyor...")
        layout.addWidget(self.status_label)
        
        # Sonuç grid'i - scroll area içinde
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.results_widget = QWidget()
        self.results_layout = QGridLayout(self.results_widget)
        self.results_layout.setSpacing(10)
        
        scroll.setWidget(self.results_widget)
        layout.addWidget(scroll, stretch=1)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def do_search(self):
        """Arama yap."""
        query = self.search_input.text().strip()
        if not query:
            return
        
        self.status_label.setText("🔍 Aranıyor...")
        self.search_btn.setEnabled(False)
        self.clear_results()
        
        # Thread ile arama
        self.search_thread = SearchThread(query, "title")
        self.search_thread.finished.connect(self.on_search_done)
        self.search_thread.error.connect(self.on_search_error)
        self.search_thread.start()
    
    def on_search_done(self, results):
        """Arama tamamlandı."""
        self.search_btn.setEnabled(True)
        self.search_results = results
        
        # Sadece kapağı olanları filtrele
        results_with_cover = [r for r in results if r.cover_url]
        
        if not results_with_cover:
            self.status_label.setText("❌ Kapak bulunamadı")
            return
        
        self.status_label.setText(f"✅ {len(results_with_cover)} kapak bulundu - birini seçin")
        
        # Grid'e ekle
        row, col = 0, 0
        max_cols = 4
        
        for result in results_with_cover[:12]:  # Max 12 sonuç
            cover_widget = CoverPreviewWidget(result, self)
            cover_widget.clicked.connect(self.on_cover_selected)
            self.results_layout.addWidget(cover_widget, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def on_search_error(self, error):
        """Arama hatası."""
        self.search_btn.setEnabled(True)
        self.status_label.setText(f"❌ Hata: {error}")
    
    def clear_results(self):
        """Sonuçları temizle."""
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def on_cover_selected(self, cover_url: str, book_info: dict):
        """Kapak seçildi."""
        self.status_label.setText("⏳ Kapak indiriliyor...")
        
        # Kapağı indir
        from services.book_api import download_cover
        import hashlib
        
        identifier = book_info.get("isbn") or hashlib.md5(cover_url.encode()).hexdigest()[:12]
        cover_path = download_cover(cover_url, identifier)
        
        if cover_path:
            self.selected_cover_path = cover_path
            self.accept()
        else:
            self.status_label.setText("❌ Kapak indirilemedi!")


class CoverPreviewWidget(QWidget):
    """Kapak önizleme widget'ı."""
    
    clicked = pyqtSignal(str, dict)  # cover_url, book_info
    
    def __init__(self, book_result, parent=None):
        super().__init__(parent)
        
        self.book_result = book_result
        self.cover_url = book_result.cover_url
        
        self.setFixedSize(120, 180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            CoverPreviewWidget {
                background-color: #2D2D2D;
                border-radius: 5px;
                border: 2px solid transparent;
            }
            CoverPreviewWidget:hover {
                border: 2px solid #007ACC;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Kapak görseli
        self.cover_label = QLabel()
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setFixedSize(100, 130)
        self.cover_label.setText("⏳")
        self.cover_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(self.cover_label)
        
        # Kaynak
        source_label = QLabel(book_result.source)
        source_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        source_label.setStyleSheet("font-size: 10px; color: #888;")
        layout.addWidget(source_label)
        
        # Kapağı arka planda yükle
        self.loader_thread = CoverLoaderThread(self.cover_url)
        self.loader_thread.finished.connect(self.on_cover_loaded)
        self.loader_thread.start()
    
    def on_cover_loaded(self, data: bytes):
        """Kapak yüklendi."""
        if data:
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(data))
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    100, 130, 
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.cover_label.setPixmap(scaled)
                self.cover_label.setStyleSheet("")
            else:
                self.cover_label.setText("❌")
        else:
            self.cover_label.setText("❌")
    
    def mousePressEvent(self, event):
        """Tıklama olayı."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.cover_url, {
                "title": self.book_result.title,
                "author": self.book_result.author,
                "isbn": self.book_result.isbn,
            })


class CoverLoaderThread(QThread):
    """Arka planda kapak yükleyen thread."""
    
    finished = pyqtSignal(bytes)
    
    def __init__(self, url: str):
        super().__init__()
        self.url = url
    
    def run(self):
        try:
            import requests
            response = requests.get(self.url, timeout=10)
            if response.status_code == 200:
                self.finished.emit(response.content)
            else:
                self.finished.emit(b"")
        except Exception as e:
            print(f"Kapak yükleme hatası: {e}")
            self.finished.emit(b"")


# Geriye uyumluluk
BookDialog = ManualBookDialog