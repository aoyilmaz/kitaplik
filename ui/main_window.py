"""
Kitaplık Uygulaması - Ana Pencere
=================================
Uygulamanın ana arayüzü burada tanımlanır.
"""

from PyQt6.QtWidgets import (
    QMainWindow,       # Ana pencere sınıfı
    QWidget,           # Genel konteyner
    QVBoxLayout,       # Dikey yerleşim
    QHBoxLayout,       # Yatay yerleşim
    QGridLayout,       # Grid yerleşim
    QPushButton,       # Buton
    QTableWidget,      # Tablo
    QTableWidgetItem,  # Tablo hücresi
    QHeaderView,       # Tablo başlık ayarları
    QLabel,            # Yazı etiketi
    QLineEdit,         # Metin girişi
    QMessageBox,       # Uyarı/bilgi diyaloğu
    QMenuBar,          # Menü çubuğu
    QMenu,             # Menü
    QSplitter,         # Bölünebilir panel
    QStackedWidget,    # Sayfa değiştirici
    QScrollArea,       # Kaydırılabilir alan
    QFrame,            # Çerçeve
    QFileDialog,       # Dosya seçici
    QDialog,           # Dialog penceresi
    QGroupBox,         # Grup kutusu
    QCheckBox,         # Onay kutusu
    QComboBox,         # Açılır liste
    QProgressDialog,   # İlerleme dialog'u
    QListWidget,       # Liste widget
    QListWidgetItem,   # Liste öğesi
    QSpinBox,          # Sayı girişi
    QTextEdit,         # Çok satırlı metin
    QFormLayout,       # Form yerleşimi
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal  # Hizalama sabitleri vs.
from PyQt6.QtGui import QFont, QAction, QPixmap  # Font ayarları, menü aksiyonları, görsel

# Kendi modüllerimiz - bir üst klasörden import
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
import database as db
from ui.book_dialog import SearchBookDialog, ManualBookDialog
from ui.themes import get_stylesheet, THEME_NAMES
from ui.shelf_panel import ShelfPanel
from ui.stats_dialog import StatsDialog
from ui.filter_bar import FilterBar


class MainWindow(QMainWindow):
    """
    Ana pencere sınıfı.
    
    QMainWindow'dan miras alıyoruz (inheritance).
    Bu bize menü çubuğu, araç çubuğu, durum çubuğu gibi
    hazır özellikler sağlıyor.
    """
    
    def __init__(self):
        """
        Pencere oluşturulduğunda çalışır.
        super().__init__() ile üst sınıfın __init__'ini çağırıyoruz.
        """
        super().__init__()
        
        # Mevcut tema
        self.current_theme = db.get_setting("theme", "dark")
        
        # Seçili raf (None = tüm kitaplar)
        self.current_shelf_id = None
        
        # Görünüm modu: "list" veya "grid"
        self.view_mode = db.get_setting("view_mode", "list")
        
        # Grid seçim durumu
        self.selected_grid_cards = set()
        self.grid_cards = {}
        
        # Pencere ayarları
        self.setWindowTitle("Kitaplığım")
        self.setMinimumSize(1000, 700)
        
        # Menü çubuğunu oluştur
        self.setup_menu()
        
        # Arayüzü oluştur
        self.setup_ui()
        
        # Temayı uygula
        self.apply_theme(self.current_theme)
        
        # Kitapları yükle
        self.load_books()
        
        # Görünüm butonlarını güncelle
        self.set_view_mode(self.view_mode)
    
    def setup_menu(self):
        """
        Menü çubuğunu oluşturur.
        """
        menubar = self.menuBar()
        
        # === Dosya Menüsü ===
        file_menu = menubar.addMenu("Dosya")
        
        # Kitap Ekle
        search_action = QAction("🔍 Ara ve Ekle...", self)
        search_action.setShortcut("Ctrl+N")
        search_action.triggered.connect(self.on_search_add_clicked)
        file_menu.addAction(search_action)
        
        manual_action = QAction("✏️ Manuel Ekle...", self)
        manual_action.setShortcut("Ctrl+Shift+N")
        manual_action.triggered.connect(self.on_manual_add_clicked)
        file_menu.addAction(manual_action)
        
        file_menu.addSeparator()
        
        # İçe/Dışa Aktar
        import_action = QAction("📥 İçe Aktar...", self)
        import_action.triggered.connect(self.import_books)
        file_menu.addAction(import_action)
        
        export_menu = QMenu("📤 Dışa Aktar", self)
        export_menu.addAction("CSV", lambda: self.export_books("csv"))
        export_menu.addAction("JSON", lambda: self.export_books("json"))
        export_menu.addAction("Excel", lambda: self.export_books("xlsx"))
        file_menu.addMenu(export_menu)
        
        file_menu.addSeparator()
        
        fetch_covers_action = QAction("🖼️ Eksik Kapakları İndir...", self)
        fetch_covers_action.triggered.connect(self.fetch_missing_covers)
        file_menu.addAction(fetch_covers_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Çıkış", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # === Kitaplık Menüsü ===
        library_menu = menubar.addMenu("Kitaplık")
        
        reading_list_action = QAction("📋 Okuma Listesi", self)
        reading_list_action.setShortcut("Ctrl+L")
        reading_list_action.triggered.connect(self.show_reading_list)
        library_menu.addAction(reading_list_action)
        
        series_action = QAction("📚 Seriler", self)
        series_action.triggered.connect(self.show_series_dialog)
        library_menu.addAction(series_action)
        
        quotes_action = QAction("💬 Alıntılar", self)
        quotes_action.triggered.connect(self.show_all_quotes)
        library_menu.addAction(quotes_action)
        
        library_menu.addSeparator()
        
        stats_action = QAction("📊 İstatistikler", self)
        stats_action.setShortcut("Ctrl+I")
        stats_action.triggered.connect(self.show_stats)
        library_menu.addAction(stats_action)
        
        goal_action = QAction("🎯 Okuma Hedefi", self)
        goal_action.triggered.connect(self.show_reading_goal)
        library_menu.addAction(goal_action)
        
        library_menu.addSeparator()
        
        ai_action = QAction("🤖 AI Asistan", self)
        ai_action.setShortcut("Ctrl+Shift+A")
        ai_action.triggered.connect(self.show_ai_assistant)
        library_menu.addAction(ai_action)
        
        # === Görünüm Menüsü ===
        view_menu = menubar.addMenu("Görünüm")
        
        # Kenar çubuğu
        self.sidebar_action = QAction("Kenar Çubuğu", self)
        self.sidebar_action.setShortcut("Ctrl+B")
        self.sidebar_action.setCheckable(True)
        self.sidebar_action.setChecked(True)
        self.sidebar_action.triggered.connect(self.toggle_sidebar)
        view_menu.addAction(self.sidebar_action)
        
        view_menu.addSeparator()
        
        # Görünüm modu
        view_mode_menu = QMenu("Görünüm Modu", self)
        list_action = QAction("📋 Liste", self)
        list_action.triggered.connect(lambda: self.set_view_mode("list"))
        view_mode_menu.addAction(list_action)
        grid_action = QAction("📷 Grid (Kapaklar)", self)
        grid_action.triggered.connect(lambda: self.set_view_mode("grid"))
        view_mode_menu.addAction(grid_action)
        view_menu.addMenu(view_mode_menu)
        
        # Sütunlar
        columns_menu = QMenu("Sütunlar", self)
        self.column_actions = {}
        column_names = ["Kapak", "Başlık", "Yazar", "Sayfa", "Durum", "Puan"]
        for i, name in enumerate(column_names):
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(True)
            if i == 1:
                action.setEnabled(False)
            action.triggered.connect(lambda checked, col=i: self.toggle_column(col, checked))
            columns_menu.addAction(action)
            self.column_actions[i] = action
        columns_menu.addSeparator()
        columns_menu.addAction("Tümünü Göster", self.show_all_columns_and_update_menu)
        view_menu.addMenu(columns_menu)
        
        view_menu.addSeparator()
        
        # Tema
        theme_menu = QMenu("🎨 Tema", self)
        theme_menu.addAction(THEME_NAMES["light"], lambda: self.apply_theme("light"))
        theme_menu.addAction(THEME_NAMES["dark"], lambda: self.apply_theme("dark"))
        view_menu.addMenu(theme_menu)
    
    def show_stats(self):
        """İstatistik penceresini açar."""
        dialog = StatsDialog(self)
        dialog.exec()
    
    def show_reading_goal(self):
        """Okuma hedefi dialog'unu açar."""
        dialog = ReadingGoalDialog(self)
        dialog.exec()
    
    def show_reading_list(self):
        """Okuma listesi dialog'unu açar."""
        dialog = ReadingListDialog(self)
        dialog.exec()
    
    def show_all_quotes(self):
        """Tüm alıntılar dialog'unu açar."""
        dialog = AllQuotesDialog(self)
        dialog.exec()
    
    def show_series_dialog(self):
        """Kitap serileri dialog'unu açar."""
        dialog = SeriesDialog(self)
        if dialog.exec():
            # Seri seçildiyse o serinin kitaplarını göster
            if dialog.selected_series:
                self.show_series_books(dialog.selected_series)
    
    def show_series_books(self, series_name: str):
        """Bir serinin kitaplarını gösterir."""
        books = db.get_books_in_series(series_name)
        if books:
            self.current_shelf_id = None
            self.shelf_panel.shelf_list.setCurrentRow(0)
            self.search_input.clear()
            self.load_books(books)
            self.setWindowTitle(f"Kitaplığım - 📚 {series_name}")
    
    def show_ai_assistant(self):
        """AI Asistan dialog'unu açar."""
        dialog = AIAssistantDialog(self)
        dialog.exec()
    
    def apply_theme(self, theme: str):
        """
        Temayı uygular ve kaydeder.
        """
        self.current_theme = theme
        self.setStyleSheet(get_stylesheet(theme))
        
        # Tercihi kaydet
        db.set_setting("theme", theme)
    
    def setup_ui(self):
        """
        Arayüz bileşenlerini oluşturur ve yerleştirir.
        """
        # Ana widget - QMainWindow'un merkezine koyacağız
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana yerleşim (dikey)
        # Tüm bileşenler üstten alta dizilecek
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)  # Kenar boşlukları
        main_layout.setSpacing(10)  # Bileşenler arası boşluk
        
        # === ÜST KISIM: Başlık, Filtreler ve Arama ===
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        # Sidebar toggle butonu
        self.sidebar_btn = QPushButton("◀")
        self.sidebar_btn.setFixedSize(28, 28)
        self.sidebar_btn.setToolTip("Kenar Çubuğunu Gizle/Göster")
        self.sidebar_btn.clicked.connect(self.toggle_sidebar)
        header_layout.addWidget(self.sidebar_btn)
        
        # Başlık
        title_label = QLabel("📚 Kitaplığım")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        # Filtreler (başlıktan sonra)
        self.filter_bar = FilterBar()
        self.filter_bar.filters_changed.connect(self.on_filters_changed)
        header_layout.addWidget(self.filter_bar)
        
        # Arama kutusu (en sağda)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara...")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self.on_search)
        header_layout.addWidget(self.search_input)
        
        # Görünüm butonları
        self.list_view_btn = QPushButton("☰")
        self.list_view_btn.setFixedSize(32, 32)
        self.list_view_btn.setToolTip("Liste Görünümü")
        self.list_view_btn.clicked.connect(lambda: self.set_view_mode("list"))
        header_layout.addWidget(self.list_view_btn)
        
        self.grid_view_btn = QPushButton("▦")
        self.grid_view_btn.setFixedSize(32, 32)
        self.grid_view_btn.setToolTip("Kapak Görünümü")
        self.grid_view_btn.clicked.connect(lambda: self.set_view_mode("grid"))
        header_layout.addWidget(self.grid_view_btn)
        
        main_layout.addLayout(header_layout)
        
        # === ORTA KISIM: Raf Paneli + Kitap Tablosu ===
        # QSplitter ile yan yana, boyutu ayarlanabilir
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sol: Raf paneli
        self.shelf_panel = ShelfPanel()
        self.shelf_panel.shelf_selected.connect(self.on_shelf_selected)
        self.shelf_panel.all_books_selected.connect(self.on_all_books_selected)
        self.splitter.addWidget(self.shelf_panel)
        
        # Sağ: Görünümler ve butonlar
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        # Stacked widget - liste ve grid görünümleri için
        self.view_stack = QStackedWidget()
        
        # === LİSTE GÖRÜNÜMÜ (Tablo) ===
        self.books_table = QTableWidget()
        self.books_table.setColumnCount(6)
        self.books_table.setHorizontalHeaderLabels([
            "", "Başlık", "Yazar", "Sayfa", "Durum", "Puan"
        ])
        
        # Sütun genişlik ayarları
        header = self.books_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)     # Kapak
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)   # Başlık
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)   # Yazar
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)     # Sayfa
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)     # Durum
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)     # Puan
        self.books_table.setColumnWidth(0, 60)
        self.books_table.setColumnWidth(3, 80)
        self.books_table.setColumnWidth(4, 100)
        self.books_table.setColumnWidth(5, 80)
        
        # Sütunları sürükleyerek sıralama
        header.setSectionsMovable(True)
        header.setDragEnabled(True)
        header.setDragDropMode(QHeaderView.DragDropMode.InternalMove)
        
        # Header sağ tık menüsü (sütun gizleme)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self.show_column_menu)
        
        # Satır seçimi (çoklu seçim için)
        self.books_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.books_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        
        # Inline edit ve sağ tık
        self.books_table.cellChanged.connect(self.on_cell_changed)
        self.books_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.books_table.customContextMenuRequested.connect(self.show_book_context_menu)
        
        self.view_stack.addWidget(self.books_table)
        
        # === GRID GÖRÜNÜMÜ (Kapaklar) ===
        self.grid_scroll = QScrollArea()
        self.grid_scroll.setWidgetResizable(True)
        self.grid_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        
        self.grid_scroll.setWidget(self.grid_container)
        self.view_stack.addWidget(self.grid_scroll)
        
        # Görünüm moduna göre ayarla
        self.view_stack.setCurrentIndex(0 if self.view_mode == "list" else 1)
        
        right_layout.addWidget(self.view_stack)
        
        # Butonlar
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        search_add_btn = QPushButton("🔍 Ara ve Ekle")
        search_add_btn.setMinimumHeight(36)
        search_add_btn.setMinimumWidth(120)
        search_add_btn.clicked.connect(self.on_search_add_clicked)
        button_layout.addWidget(search_add_btn)
        
        manual_add_btn = QPushButton("✏️ Manuel Ekle")
        manual_add_btn.setMinimumHeight(36)
        manual_add_btn.setMinimumWidth(120)
        manual_add_btn.clicked.connect(self.on_manual_add_clicked)
        button_layout.addWidget(manual_add_btn)
        
        delete_button = QPushButton("🗑️ Sil")
        delete_button.setMinimumHeight(36)
        delete_button.setMinimumWidth(80)
        delete_button.clicked.connect(self.on_delete_book_clicked)
        button_layout.addWidget(delete_button)
        
        right_layout.addLayout(button_layout)
        
        self.splitter.addWidget(right_widget)
        
        # Başlangıç boyutları (sol panel dar, sağ geniş)
        self.splitter.setSizes([200, 600])
        
        # Sidebar durumunu yükle
        sidebar_hidden = db.get_setting("sidebar_hidden", "0") == "1"
        if sidebar_hidden:
            self.shelf_panel.hide()
            self.sidebar_btn.setText("▶")
        
        # Sütun ayarlarını yükle
        self.load_column_settings()
        
        main_layout.addWidget(self.splitter)
    
    def load_books(self, books=None):
        """
        Kitapları tabloya yükler.
        
        books parametresi verilmezse mevcut raf ve filtrelere göre kitapları çeker.
        Arama sonuçlarını göstermek için parametre kullanılır.
        """
        if books is None:
            # Önce raf filtresi
            if self.current_shelf_id is None:
                # Filtre çubuğu varsa filtreleri uygula
                if hasattr(self, 'filter_bar') and self.filter_bar.has_active_filters():
                    filters = self.filter_bar.get_filters()
                    books = db.get_filtered_books(
                        status=filters["status"],
                        rating=filters["rating"],
                        year=filters["year"]
                    )
                else:
                    books = db.get_all_books()
            else:
                # Raf seçiliyse, raftan kitapları al
                books = db.get_books_in_shelf(self.current_shelf_id)
        
        # cellChanged sinyalini geçici olarak kapat (yükleme sırasında tetiklenmesin)
        self.books_table.blockSignals(True)
        
        # Tabloyu temizle
        self.books_table.setRowCount(0)
        
        # Thumbnail boyutu
        THUMB_HEIGHT = 50
        
        # Her kitap için bir satır ekle
        for book in books:
            row = self.books_table.rowCount()
            self.books_table.insertRow(row)
            
            # Satır yüksekliğini ayarla
            self.books_table.setRowHeight(row, THUMB_HEIGHT + 10)
            
            # === KAPAK GÖRSELİ (düzenlenemez) ===
            cover_label = QLabel()
            cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if book["cover_path"]:
                pixmap = QPixmap(book["cover_path"])
                if not pixmap.isNull():
                    scaled = pixmap.scaledToHeight(
                        THUMB_HEIGHT, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    cover_label.setPixmap(scaled)
                else:
                    cover_label.setText("📖")
            else:
                cover_label.setText("📖")
            
            self.books_table.setCellWidget(row, 0, cover_label)
            
            # === DÜZENLENEBİLİR SÜTUNLAR ===
            # Başlık
            title_item = QTableWidgetItem(book["title"] or "")
            title_item.setData(Qt.ItemDataRole.UserRole, book["id"])  # ID'yi sakla
            self.books_table.setItem(row, 1, title_item)
            
            # Yazar
            self.books_table.setItem(row, 2, QTableWidgetItem(book["author"] or ""))
            
            # Sayfa sayısı
            self.books_table.setItem(row, 3, QTableWidgetItem(
                str(book["page_count"]) if book["page_count"] else ""
            ))
            
            # Durum (düzenlenebilir - metin olarak)
            status_map = {
                "unread": "📕 Okunmadı",
                "to_read": "📋 Okuyacağım",
                "reading": "📖 Okunuyor",
                "read": "📗 Okundu",
                "wont_read": "🚫 Okumayacağım"
            }
            status_text = status_map.get(book["status"], book["status"])
            status_item = QTableWidgetItem(status_text)
            status_item.setData(Qt.ItemDataRole.UserRole + 1, book["status"])  # Orijinal değeri sakla
            self.books_table.setItem(row, 4, status_item)
            
            # Puan (düzenlenebilir - metin olarak)
            rating = book["rating"]
            rating_text = "⭐" * rating if rating else ""
            rating_item = QTableWidgetItem(rating_text)
            rating_item.setData(Qt.ItemDataRole.UserRole + 1, rating)  # Orijinal değeri sakla
            self.books_table.setItem(row, 5, rating_item)
        
        # Sinyalleri tekrar aç
        self.books_table.blockSignals(False)
        
        # Grid görünümünü güncelle
        self.load_grid_view(books)
    
    def load_grid_view(self, books):
        """Grid görünümünü yükler (kapak görselleri)."""
        # Seçili kartları temizle
        self.selected_grid_cards = set()
        
        # Mevcut widget'ları temizle
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not books:
            empty_label = QLabel("Kitap bulunamadı")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(empty_label, 0, 0)
            return
        
        # Grid boyutları
        COVER_WIDTH = 130
        COVER_HEIGHT = 190
        CARD_WIDTH = COVER_WIDTH + 20
        
        # Dinamik sütun sayısı - mevcut genişliğe göre
        available_width = self.grid_scroll.viewport().width() - 40
        cols = max(2, available_width // (CARD_WIDTH + 20))
        
        # Kartları sakla
        self.grid_cards = {}
        
        # Grid'e kitapları ekle
        for i, book in enumerate(books):
            row = i // cols
            col = i % cols
            
            # Kitap kartı
            card = QFrame()
            card.setObjectName("bookCard")
            card.setFixedSize(CARD_WIDTH, COVER_HEIGHT + 50)
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.setStyleSheet("""
                QFrame#bookCard {
                    background-color: transparent;
                    border-radius: 8px;
                    border: 2px solid transparent;
                }
                QFrame#bookCard:hover {
                    background-color: rgba(255, 255, 255, 0.05);
                }
            """)
            
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(5, 5, 5, 5)
            card_layout.setSpacing(6)
            
            # Kapak görseli
            cover_label = QLabel()
            cover_label.setFixedSize(COVER_WIDTH, COVER_HEIGHT)
            cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cover_label.setStyleSheet("""
                background-color: #2D2D2D;
                border-radius: 4px;
            """)
            
            if book["cover_path"]:
                pixmap = QPixmap(book["cover_path"])
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        COVER_WIDTH, COVER_HEIGHT,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    cover_label.setPixmap(scaled)
                else:
                    cover_label.setText("📖")
                    cover_label.setStyleSheet(cover_label.styleSheet() + "font-size: 48px;")
            else:
                cover_label.setText("📖")
                cover_label.setStyleSheet(cover_label.styleSheet() + "font-size: 48px;")
            
            card_layout.addWidget(cover_label, alignment=Qt.AlignmentFlag.AlignCenter)
            
            # Kitap başlığı
            title_label = QLabel(book["title"] or "")
            title_label.setWordWrap(True)
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label.setMaximumWidth(COVER_WIDTH)
            title_label.setMaximumHeight(36)
            title_label.setStyleSheet("font-size: 11px;")
            card_layout.addWidget(title_label)
            
            # Kitap ID'sini sakla
            card.setProperty("book_id", book["id"])
            self.grid_cards[book["id"]] = card
            
            # Tıklama olayları
            card.mousePressEvent = lambda event, bid=book["id"], c=card: self.on_grid_card_clicked(event, bid, c)
            card.mouseDoubleClickEvent = lambda event, bid=book["id"]: self.on_grid_card_double_clicked(event, bid)
            
            self.grid_layout.addWidget(card, row, col, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Sağa ve aşağıya esnek boşluk
        self.grid_layout.setColumnStretch(cols, 1)
        self.grid_layout.setRowStretch(row + 1, 1)
        
        # Kitap listesini sakla (resize için)
        self._grid_books = books
    
    def resizeEvent(self, event):
        """Pencere boyutu değiştiğinde grid'i yeniden çiz."""
        super().resizeEvent(event)
        
        # Grid görünümündeyse ve kitaplar varsa
        if hasattr(self, '_grid_books') and self._grid_books:
            if self.view_mode == "grid":
                self.load_grid_view(self._grid_books)
    
    def on_grid_card_clicked(self, event, book_id, card):
        """Grid'de bir kitap kartına tek tıklandığında - seçim."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Ctrl tuşu basılı mı?
            ctrl_pressed = event.modifiers() & Qt.KeyboardModifier.ControlModifier
            
            if ctrl_pressed:
                # Çoklu seçim - toggle
                if book_id in self.selected_grid_cards:
                    self.selected_grid_cards.remove(book_id)
                    self.update_card_selection(card, False)
                else:
                    self.selected_grid_cards.add(book_id)
                    self.update_card_selection(card, True)
            else:
                # Tek seçim - diğerlerini temizle
                self.clear_grid_selection()
                self.selected_grid_cards.add(book_id)
                self.update_card_selection(card, True)
                
        elif event.button() == Qt.MouseButton.RightButton:
            # Sağ tık - menü göster
            if book_id not in self.selected_grid_cards:
                # Seçili değilse önce seç
                self.clear_grid_selection()
                self.selected_grid_cards.add(book_id)
                self.update_card_selection(card, True)
            
            self.show_grid_context_menu(event.globalPosition().toPoint(), book_id)
    
    def on_grid_card_double_clicked(self, event, book_id):
        """Grid'de çift tıklama - düzenleme."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_edit_dialog(book_id)
    
    def update_card_selection(self, card, selected: bool):
        """Kart seçim stilini günceller."""
        if selected:
            card.setStyleSheet("""
                QFrame#bookCard {
                    background-color: rgba(0, 120, 212, 0.2);
                    border-radius: 8px;
                    border: 2px solid #0078D4;
                }
            """)
        else:
            card.setStyleSheet("""
                QFrame#bookCard {
                    background-color: transparent;
                    border-radius: 8px;
                    border: 2px solid transparent;
                }
                QFrame#bookCard:hover {
                    background-color: rgba(255, 255, 255, 0.05);
                }
            """)
    
    def clear_grid_selection(self):
        """Tüm grid seçimlerini temizler."""
        for book_id in list(self.selected_grid_cards):
            if book_id in self.grid_cards:
                self.update_card_selection(self.grid_cards[book_id], False)
        self.selected_grid_cards.clear()
    
    def show_grid_context_menu(self, position, book_id):
        """Grid görünümünde sağ tık menüsü."""
        # Çoklu seçim varsa toplu işlem menüsü göster
        if len(self.selected_grid_cards) > 1:
            self.show_grid_multi_select_menu(position)
            return
        
        book = db.get_book_by_id(book_id)
        if not book:
            return
        
        menu = QMenu(self)
        
        # Düzenle
        edit_action = menu.addAction("✏️ Düzenle")
        edit_action.triggered.connect(lambda: self.open_edit_dialog(book_id))
        
        # Kopyala
        copy_action = menu.addAction("📋 Kopyala")
        copy_action.triggered.connect(lambda: self.copy_book(book_id))
        
        # Alıntılar
        quotes_action = menu.addAction("💬 Alıntılar")
        quotes_action.triggered.connect(lambda: self.show_quotes_dialog(book_id))
        
        menu.addSeparator()
        
        # Rafa ekle
        add_to_shelf_menu = QMenu("📚 Rafa Ekle", self)
        shelves = db.get_all_shelves()
        book_shelf_ids = [s["id"] for s in db.get_shelves_for_book(book_id)]
        
        for shelf in shelves:
            action_text = f"{shelf['icon']} {shelf['name']}"
            if shelf["id"] in book_shelf_ids:
                action_text = f"✓ {action_text}"
            
            action = add_to_shelf_menu.addAction(action_text)
            shelf_id = shelf["id"]
            if shelf_id in book_shelf_ids:
                action.triggered.connect(
                    lambda checked, sid=shelf_id, bid=book_id: self.remove_from_shelf(bid, sid)
                )
            else:
                action.triggered.connect(
                    lambda checked, sid=shelf_id, bid=book_id: self.add_to_shelf(bid, sid)
                )
        
        menu.addMenu(add_to_shelf_menu)
        
        menu.addSeparator()
        
        # Sil
        delete_action = menu.addAction("🗑️ Sil")
        delete_action.triggered.connect(lambda: self.delete_book(book_id, book["title"]))
        
        menu.exec(position)
    
    def show_grid_multi_select_menu(self, position):
        """Grid çoklu seçim için sağ tık menüsü."""
        book_ids = list(self.selected_grid_cards)
        
        menu = QMenu(self)
        menu.addAction(f"📚 {len(book_ids)} kitap seçili").setEnabled(False)
        menu.addSeparator()
        
        # Toplu düzenleme
        bulk_edit_action = menu.addAction("✏️ Toplu Düzenle...")
        bulk_edit_action.triggered.connect(lambda: self.show_bulk_edit_dialog(book_ids))
        
        # Rafa ekle alt menüsü
        add_to_shelf_menu = QMenu("📚 Rafa Ekle", self)
        shelves = db.get_all_shelves()
        
        for shelf in shelves:
            action = add_to_shelf_menu.addAction(f"{shelf['icon']} {shelf['name']}")
            shelf_id = shelf["id"]
            action.triggered.connect(
                lambda checked, sid=shelf_id: self.bulk_add_to_shelf(book_ids, sid)
            )
        
        menu.addMenu(add_to_shelf_menu)
        
        menu.addSeparator()
        
        # Toplu silme
        delete_action = menu.addAction("🗑️ Seçilenleri Sil")
        delete_action.triggered.connect(lambda: self.bulk_delete_books(book_ids))
        
        menu.exec(position)
    
    def toggle_sidebar(self):
        """Kenar çubuğunu göster/gizle."""
        if self.shelf_panel.isVisible():
            self.shelf_panel.hide()
            self.sidebar_btn.setText("▶")
            db.set_setting("sidebar_hidden", "1")
            if hasattr(self, 'sidebar_action'):
                self.sidebar_action.setChecked(False)
        else:
            self.shelf_panel.show()
            self.sidebar_btn.setText("◀")
            db.set_setting("sidebar_hidden", "0")
            if hasattr(self, 'sidebar_action'):
                self.sidebar_action.setChecked(True)
    
    def show_column_menu(self, position):
        """Sütun gizleme/gösterme menüsü."""
        menu = QMenu(self)
        
        column_names = ["Kapak", "Başlık", "Yazar", "Sayfa", "Durum", "Puan"]
        
        for i, name in enumerate(column_names):
            action = menu.addAction(name)
            action.setCheckable(True)
            action.setChecked(not self.books_table.isColumnHidden(i))
            
            # Başlık sütunu her zaman görünür olmalı
            if i == 1:
                action.setEnabled(False)
            else:
                action.triggered.connect(lambda checked, col=i: self.toggle_column(col, checked))
        
        menu.addSeparator()
        
        # Tümünü göster
        show_all = menu.addAction("Tümünü Göster")
        show_all.triggered.connect(self.show_all_columns)
        
        menu.exec(self.books_table.horizontalHeader().mapToGlobal(position))
    
    def toggle_column(self, column: int, visible: bool):
        """Sütunu gizle/göster."""
        self.books_table.setColumnHidden(column, not visible)
        
        # Menü action'ını güncelle
        if hasattr(self, 'column_actions') and column in self.column_actions:
            self.column_actions[column].setChecked(visible)
        
        # Ayarı kaydet
        hidden_cols = []
        for i in range(self.books_table.columnCount()):
            if self.books_table.isColumnHidden(i):
                hidden_cols.append(str(i))
        db.set_setting("hidden_columns", ",".join(hidden_cols))
    
    def show_all_columns(self):
        """Tüm sütunları göster."""
        for i in range(self.books_table.columnCount()):
            self.books_table.setColumnHidden(i, False)
        db.set_setting("hidden_columns", "")
    
    def show_all_columns_and_update_menu(self):
        """Tüm sütunları göster ve menüyü güncelle."""
        self.show_all_columns()
        if hasattr(self, 'column_actions'):
            for action in self.column_actions.values():
                action.setChecked(True)
    
    def load_column_settings(self):
        """Sütun ayarlarını yükle."""
        hidden = db.get_setting("hidden_columns", "")
        if hidden:
            for col_str in hidden.split(","):
                try:
                    col = int(col_str)
                    if col != 1:  # Başlık her zaman görünür
                        self.books_table.setColumnHidden(col, True)
                        if hasattr(self, 'column_actions') and col in self.column_actions:
                            self.column_actions[col].setChecked(False)
                except ValueError:
                    pass
    
    def set_view_mode(self, mode: str):
        """Görünüm modunu değiştirir."""
        self.view_mode = mode
        db.set_setting("view_mode", mode)
        
        # Stack widget'ı güncelle
        self.view_stack.setCurrentIndex(0 if mode == "list" else 1)
        
        # Buton stillerini güncelle
        if mode == "list":
            self.list_view_btn.setStyleSheet("background-color: #0078D4;")
            self.grid_view_btn.setStyleSheet("")
        else:
            self.list_view_btn.setStyleSheet("")
            self.grid_view_btn.setStyleSheet("background-color: #0078D4;")
    
    def on_search(self, text):
        """
        Arama kutusuna yazıldığında çalışır.
        """
        if text.strip():
            books = db.search_books(text)
        else:
            books = db.get_all_books()
        
        self.load_books(books)
    
    def on_cell_changed(self, row, column):
        """
        Hücre düzenlendiğinde çağrılır (inline edit).
        """
        # Kapak sütunu düzenlenemez (zaten widget)
        if column == 0:
            return
        
        # Kitap ID'sini al
        title_item = self.books_table.item(row, 1)
        if not title_item:
            return
        
        book_id = title_item.data(Qt.ItemDataRole.UserRole)
        if not book_id:
            return
        
        # Yeni değeri al
        item = self.books_table.item(row, column)
        new_value = item.text().strip()
        
        # Sütuna göre güncelle
        if column == 1:  # Başlık
            if new_value:  # Başlık boş olamaz
                db.update_book(book_id, title=new_value)
            else:
                self.load_books()  # Boşsa geri yükle
                
        elif column == 2:  # Yazar
            db.update_book(book_id, author=new_value or None)
            
        elif column == 3:  # Sayfa
            try:
                page_count = int(new_value) if new_value else None
                db.update_book(book_id, page_count=page_count)
            except ValueError:
                self.load_books()  # Geçersiz sayı, geri yükle
                
        elif column == 4:  # Durum
            # Emoji veya metin olarak girilmiş olabilir
            status_input = new_value.lower()
            if "okunmadı" in status_input or "unread" in status_input or "📕" in new_value:
                db.update_book(book_id, status="unread")
            elif "okunuyor" in status_input or "reading" in status_input or "📖" in new_value:
                db.update_book(book_id, status="reading")
            elif "okundu" in status_input or "read" in status_input or "📗" in new_value:
                db.update_book(book_id, status="read")
            self.load_books()  # Durumu düzgün göstermek için yenile
            
        elif column == 5:  # Puan
            # Yıldız sayısını say veya sayı olarak al
            star_count = new_value.count("⭐")
            if star_count > 0:
                rating = min(star_count, 5)
            else:
                try:
                    rating = int(new_value) if new_value else None
                    if rating and (rating < 1 or rating > 5):
                        rating = None
                except ValueError:
                    rating = None
            db.update_book(book_id, rating=rating)
            self.load_books()  # Puanı yıldız olarak göstermek için yenile

    def on_search_add_clicked(self):
        """
        'Ara ve Ekle' butonuna tıklanınca çalışır.
        Online arama ile kitap ekler.
        """
        dialog = SearchBookDialog(self)
        
        if dialog.exec():
            data = dialog.get_data()
            if not data.get("title"):
                return
            
            # Veritabanına ekle (API'den gelen tüm alanlarla)
            book_id = db.add_book(
                title=data["title"],
                author=data.get("author"),
                isbn=data.get("isbn"),
                page_count=data.get("page_count"),
                publish_year=data.get("publish_year"),
                publisher=data.get("publisher"),
                cover_path=data.get("cover_path"),
                subtitle=data.get("subtitle"),
                description=data.get("description"),
                language=data.get("language"),
                categories=data.get("categories"),
            )
            
            # Tabloyu yenile
            self.load_books()
            self.shelf_panel.refresh()
            self.filter_bar.refresh_years()
    
    def on_manual_add_clicked(self):
        """
        'Manuel Ekle' butonuna tıklanınca çalışır.
        Manuel kitap girişi yapar.
        """
        dialog = ManualBookDialog(self)
        
        if dialog.exec():
            data = dialog.get_data()
            
            # Veritabanına ekle (temel + ek alanlar)
            book_id = db.add_book(
                title=data["title"],
                author=data["author"],
                isbn=data["isbn"],
                page_count=data["page_count"],
                publish_year=data["publish_year"],
                publisher=data["publisher"],
                cover_path=data["cover_path"],
                subtitle=data.get("subtitle"),
                description=data.get("description"),
                language=data.get("language"),
                categories=data.get("categories"),
                translator=data.get("translator"),
                original_title=data.get("original_title"),
                original_language=data.get("original_language"),
                series_name=data.get("series_name"),
                series_order=data.get("series_order"),
                format=data.get("format", "paperback"),
                location=data.get("location"),
                tags=data.get("tags"),
            )
            
            # Okuma takibi ve diğer alanları güncelle
            db.update_book(
                book_id,
                status=data.get("status", "unread"),
                current_page=data.get("current_page"),
                start_date=data.get("start_date"),
                finish_date=data.get("finish_date"),
                times_read=data.get("times_read"),
                rating=data.get("rating"),
                notes=data.get("notes"),
                review=data.get("review"),
                purchase_date=data.get("purchase_date"),
                purchase_place=data.get("purchase_place"),
                purchase_price=data.get("purchase_price"),
                currency=data.get("currency"),
                is_gift=data.get("is_gift"),
                gifted_by=data.get("gifted_by"),
                is_borrowed=data.get("is_borrowed"),
                borrowed_to=data.get("borrowed_to"),
                borrowed_date=data.get("borrowed_date"),
            )
            
            # Tabloyu yenile
            self.load_books()
            self.shelf_panel.refresh()
            self.filter_bar.refresh_years()
    
    def on_delete_book_clicked(self):
        """
        'Sil' butonuna tıklanınca çalışır.
        """
        # Seçili satırı bul
        selected_items = self.books_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Uyarı", "Lütfen silmek için bir kitap seçin.")
            return
        
        row = selected_items[0].row()
        title_cell = self.books_table.item(row, 1)
        book_id = title_cell.data(Qt.ItemDataRole.UserRole)
        book_title = title_cell.text()
        
        self.delete_book(book_id, book_title)
    
    def on_shelf_selected(self, shelf_id: int):
        """Bir raf seçildiğinde."""
        self.current_shelf_id = shelf_id
        self.search_input.clear()
        self.load_books()
    
    def on_all_books_selected(self):
        """'Tüm Kitaplar' seçildiğinde."""
        self.current_shelf_id = None
        self.search_input.clear()
        self.load_books()
    
    def on_filters_changed(self, filters: dict):
        """Filtreler değiştiğinde."""
        # Arama kutusunu temizle (filtre ile arama karışmasın)
        self.search_input.clear()
        # Raf seçimini "Tüm Kitaplar"a al
        self.current_shelf_id = None
        self.shelf_panel.shelf_list.setCurrentRow(0)
        self.load_books()
    
    def show_book_context_menu(self, position):
        """Kitap tablosunda sağ tık menüsünü gösterir."""
        item = self.books_table.itemAt(position)
        if not item:
            return
        
        # Seçili satırları al
        selected_rows = set()
        for item in self.books_table.selectedItems():
            selected_rows.add(item.row())
        
        selected_rows = list(selected_rows)
        
        # Tek kitap mı çoklu seçim mi?
        if len(selected_rows) > 1:
            self.show_multi_select_menu(position, selected_rows)
            return
        
        row = item.row()
        title_cell = self.books_table.item(row, 1)
        if not title_cell:
            return
        
        book_id = title_cell.data(Qt.ItemDataRole.UserRole)
        book_title = title_cell.text()
        
        menu = QMenu(self)
        
        # Düzenle
        edit_action = menu.addAction("✏️ Düzenle")
        edit_action.triggered.connect(lambda: self.open_edit_dialog(book_id))
        
        # Kopyala
        copy_action = menu.addAction("📋 Kopyala")
        copy_action.triggered.connect(lambda: self.copy_book(book_id))
        
        # Alıntılar
        quotes_action = menu.addAction("💬 Alıntılar")
        quotes_action.triggered.connect(lambda: self.show_quotes_dialog(book_id))
        
        menu.addSeparator()
        
        # Rafa ekle alt menüsü
        add_to_shelf_menu = QMenu("📚 Rafa Ekle", self)
        
        # Mevcut rafları listele
        shelves = db.get_all_shelves()
        book_shelf_ids = [s["id"] for s in db.get_shelves_for_book(book_id)]
        
        for shelf in shelves:
            action_text = f"{shelf['icon']} {shelf['name']}"
            
            # Kitap zaten bu raftaysa işaretle
            if shelf["id"] in book_shelf_ids:
                action_text = f"✓ {action_text}"
            
            action = add_to_shelf_menu.addAction(action_text)
            
            # Lambda'da değişken yakalama sorunu için default parametre
            shelf_id = shelf["id"]
            if shelf_id in book_shelf_ids:
                action.triggered.connect(
                    lambda checked, sid=shelf_id, bid=book_id: self.remove_from_shelf(bid, sid)
                )
            else:
                action.triggered.connect(
                    lambda checked, sid=shelf_id, bid=book_id: self.add_to_shelf(bid, sid)
                )
        
        menu.addMenu(add_to_shelf_menu)
        
        # Eğer bir rafta isek, "Bu raftan çıkar" seçeneği
        if self.current_shelf_id is not None:
            menu.addSeparator()
            remove_action = menu.addAction("❌ Bu Raftan Çıkar")
            remove_action.triggered.connect(
                lambda: self.remove_from_shelf(book_id, self.current_shelf_id)
            )
        
        menu.addSeparator()
        
        # Sil
        delete_action = menu.addAction("🗑️ Sil")
        delete_action.triggered.connect(lambda: self.delete_book(book_id, book_title))
        
        menu.exec(self.books_table.mapToGlobal(position))
    
    def show_multi_select_menu(self, position, selected_rows: list):
        """Çoklu seçim için sağ tık menüsü."""
        # Kitap ID'lerini topla
        book_ids = []
        for row in selected_rows:
            title_cell = self.books_table.item(row, 1)
            if title_cell:
                book_id = title_cell.data(Qt.ItemDataRole.UserRole)
                if book_id:
                    book_ids.append(book_id)
        
        if not book_ids:
            return
        
        menu = QMenu(self)
        menu.addAction(f"📚 {len(book_ids)} kitap seçili").setEnabled(False)
        menu.addSeparator()
        
        # Toplu düzenleme
        bulk_edit_action = menu.addAction("✏️ Toplu Düzenle...")
        bulk_edit_action.triggered.connect(lambda: self.show_bulk_edit_dialog(book_ids))
        
        # Rafa ekle alt menüsü
        add_to_shelf_menu = QMenu("📚 Rafa Ekle", self)
        shelves = db.get_all_shelves()
        
        for shelf in shelves:
            action = add_to_shelf_menu.addAction(f"{shelf['icon']} {shelf['name']}")
            shelf_id = shelf["id"]
            action.triggered.connect(
                lambda checked, sid=shelf_id: self.bulk_add_to_shelf(book_ids, sid)
            )
        
        menu.addMenu(add_to_shelf_menu)
        
        menu.addSeparator()
        
        # Toplu silme
        delete_action = menu.addAction("🗑️ Seçilenleri Sil")
        delete_action.triggered.connect(lambda: self.bulk_delete_books(book_ids))
        
        menu.exec(self.books_table.mapToGlobal(position))
    
    def open_edit_dialog(self, book_id: int):
        """Düzenleme formunu açar."""
        book = db.get_book_by_id(book_id)
        if book:
            dialog = ManualBookDialog(self, dict(book))
            
            if dialog.exec():
                data = dialog.get_data()
                
                # Tüm alanları güncelle
                db.update_book(
                    book_id,
                    # Temel
                    title=data["title"],
                    subtitle=data.get("subtitle"),
                    author=data.get("author"),
                    isbn=data.get("isbn"),
                    publisher=data.get("publisher"),
                    publish_year=data.get("publish_year"),
                    page_count=data.get("page_count"),
                    language=data.get("language"),
                    categories=data.get("categories"),
                    format=data.get("format"),
                    cover_path=data.get("cover_path"),
                    # Çeviri & Seri
                    translator=data.get("translator"),
                    original_title=data.get("original_title"),
                    original_language=data.get("original_language"),
                    series_name=data.get("series_name"),
                    series_order=data.get("series_order"),
                    # Okuma takibi
                    status=data.get("status"),
                    current_page=data.get("current_page"),
                    start_date=data.get("start_date"),
                    finish_date=data.get("finish_date"),
                    times_read=data.get("times_read"),
                    rating=data.get("rating"),
                    # Notlar
                    notes=data.get("notes"),
                    review=data.get("review"),
                    description=data.get("description"),
                    # Satın alma
                    purchase_date=data.get("purchase_date"),
                    purchase_place=data.get("purchase_place"),
                    purchase_price=data.get("purchase_price"),
                    currency=data.get("currency"),
                    is_gift=data.get("is_gift"),
                    gifted_by=data.get("gifted_by"),
                    # Konum & Ödünç
                    location=data.get("location"),
                    is_borrowed=data.get("is_borrowed"),
                    borrowed_to=data.get("borrowed_to"),
                    borrowed_date=data.get("borrowed_date"),
                    # Etiketler
                    tags=data.get("tags"),
                )
                
                self.load_books()
    
    def copy_book(self, book_id: int):
        """Kitabı kopyalar."""
        new_id = db.copy_book(book_id)
        if new_id:
            QMessageBox.information(self, "Başarılı", "Kitap kopyalandı!")
            self.load_books()
            self.shelf_panel.refresh()
        else:
            QMessageBox.warning(self, "Hata", "Kitap kopyalanamadı!")
    
    def show_quotes_dialog(self, book_id: int):
        """Alıntılar dialog'unu açar."""
        book = db.get_book_by_id(book_id)
        if book:
            dialog = QuotesDialog(book_id, book["title"], self)
            dialog.exec()
    
    def show_bulk_edit_dialog(self, book_ids: list):
        """Toplu düzenleme dialog'unu açar."""
        dialog = BulkEditDialog(book_ids, self)
        if dialog.exec():
            self.load_books()
            self.shelf_panel.refresh()
    
    def bulk_delete_books(self, book_ids: list):
        """Birden fazla kitabı siler."""
        reply = QMessageBox.question(
            self,
            "Toplu Silme",
            f"{len(book_ids)} kitabı silmek istediğinize emin misiniz?\n\nBu işlem geri alınamaz!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            deleted = db.bulk_delete_books(book_ids)
            QMessageBox.information(self, "Silindi", f"{deleted} kitap silindi.")
            self.load_books()
            self.shelf_panel.refresh()
    
    def bulk_add_to_shelf(self, book_ids: list, shelf_id: int):
        """Birden fazla kitabı rafa ekler."""
        added = db.bulk_add_to_shelf(book_ids, shelf_id)
        if added > 0:
            self.shelf_panel.refresh()
            QMessageBox.information(self, "Eklendi", f"{added} kitap rafa eklendi.")
    
    def delete_book(self, book_id: int, book_title: str):
        """Kitabı siler (onay ile)."""
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            f'"{book_title}" kitabını silmek istediğinize emin misiniz?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_book(book_id)
            self.load_books()
            self.shelf_panel.refresh()
    
    def add_to_shelf(self, book_id: int, shelf_id: int):
        """Kitabı rafa ekler."""
        db.add_book_to_shelf(book_id, shelf_id)
        self.shelf_panel.refresh()
        
    def remove_from_shelf(self, book_id: int, shelf_id: int):
        """Kitabı raftan çıkarır."""
        db.remove_book_from_shelf(book_id, shelf_id)
        self.shelf_panel.refresh()
        
        # Eğer o raftaysak, listeyi güncelle
        if self.current_shelf_id == shelf_id:
            self.load_books()
    
    def export_books(self, format: str):
        """
        Kitapları dışa aktarır.
        
        Args:
            format: "csv", "json" veya "xlsx"
        """
        # Dosya uzantıları ve filtreleri
        filters = {
            "csv": "CSV Dosyası (*.csv)",
            "json": "JSON Dosyası (*.json)",
            "xlsx": "Excel Dosyası (*.xlsx)",
        }
        
    def fetch_missing_covers(self):
        """Kapağı olmayan kitaplar için online arama yaparak kapak indir."""
        from PyQt6.QtWidgets import QProgressDialog
        from PyQt6.QtCore import Qt, QCoreApplication
        from services.book_api import search_books, download_cover, cover_exists
        
        # Kapağı olmayan kitapları bul (dosya gerçekten var mı kontrol et)
        books = db.get_all_books()
        books_without_cover = [b for b in books if not cover_exists(b["cover_path"])]
        
        if not books_without_cover:
            QMessageBox.information(self, "Bilgi", "Tüm kitapların kapağı mevcut!")
            return
        
        reply = QMessageBox.question(
            self,
            "Kapak İndir",
            f"{len(books_without_cover)} kitabın kapağı eksik.\n\n"
            f"Online arama yaparak kapakları indirmek ister misiniz?\n"
            f"(Bu işlem birkaç dakika sürebilir)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # İlerleme dialog'u
        progress = QProgressDialog("Kapaklar indiriliyor...", "İptal", 0, len(books_without_cover), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        downloaded = 0
        failed = 0
        
        for i, book in enumerate(books_without_cover):
            if progress.wasCanceled():
                break
            
            progress.setValue(i)
            progress.setLabelText(f"({i+1}/{len(books_without_cover)}) {book['title'][:40]}...")
            QCoreApplication.processEvents()
            
            # Arama yap
            search_query = book["title"]
            if book["author"]:
                search_query += " " + book["author"]
            
            try:
                results = search_books(search_query, "title")
                if results and results[0].cover_url:
                    cover_path = download_cover(
                        results[0].cover_url, 
                        results[0].isbn or str(book["id"])
                    )
                    if cover_path:
                        db.update_book(book["id"], cover_path=cover_path)
                        downloaded += 1
                    else:
                        failed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"Kapak indirme hatası ({book['title']}): {e}")
                failed += 1
        
        progress.setValue(len(books_without_cover))
        
        QMessageBox.information(
            self,
            "Tamamlandı",
            f"✅ {downloaded} kapak indirildi\n❌ {failed} kitap için kapak bulunamadı"
        )
        
        self.load_books()
    
    def export_books(self, format: str):
        """Kitapları dışa aktar."""
        filters = {
            "csv": "CSV Dosyası (*.csv)",
            "json": "JSON Dosyası (*.json)",
            "xlsx": "Excel Dosyası (*.xlsx)"
        }
        
        # Dosya kaydetme dialogu
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Dışa Aktar",
            f"kitaplik.{format}",
            filters.get(format, "")
        )
        
        if not file_path:
            return
        
        # Tüm kitapları al
        books = db.get_all_books()
        
        # Dışa aktarılacak alanlar
        export_fields = [
            "id", "title", "author", "isbn", "page_count", 
            "publish_year", "publisher", "status", "rating", 
            "notes", "start_date", "finish_date", "created_at"
        ]
        
        try:
            if format == "csv":
                self._export_csv(file_path, books, export_fields)
            elif format == "json":
                self._export_json(file_path, books, export_fields)
            elif format == "xlsx":
                self._export_xlsx(file_path, books, export_fields)
            
            QMessageBox.information(
                self,
                "Başarılı",
                f"{len(books)} kitap dışa aktarıldı:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Hata",
                f"Dışa aktarma hatası:\n{str(e)}"
            )
    
    def _export_csv(self, file_path: str, books, fields):
        """CSV olarak dışa aktar."""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            
            for book in books:
                row = {field: book[field] for field in fields}
                writer.writerow(row)
    
    def _export_json(self, file_path: str, books, fields):
        """JSON olarak dışa aktar."""
        import json
        
        data = []
        for book in books:
            row = {field: book[field] for field in fields}
            data.append(row)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _export_xlsx(self, file_path: str, books, fields):
        """Excel olarak dışa aktar."""
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill
        except ImportError:
            raise Exception("Excel için 'openpyxl' paketi gerekli.\npip install openpyxl")
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Kitaplar"
        
        # Başlık satırı
        header_font = Font(bold=True)
        header_fill = PatternFill(start_color="0078D4", end_color="0078D4", fill_type="solid")
        header_text_color = Font(color="FFFFFF", bold=True)
        
        for col, field in enumerate(fields, 1):
            cell = ws.cell(row=1, column=col, value=field)
            cell.font = header_text_color
            cell.fill = header_fill
        
        # Veri satırları
        for row_idx, book in enumerate(books, 2):
            for col_idx, field in enumerate(fields, 1):
                ws.cell(row=row_idx, column=col_idx, value=book[field])
        
        # Sütun genişliklerini ayarla
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            ws.column_dimensions[column].width = min(max_length + 2, 50)
        
        wb.save(file_path)
    
    def import_books(self):
        """CSV veya Excel dosyasından kitap içe aktar."""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "İçe Aktar",
            "",
            "Tüm Desteklenen (*.csv *.xlsx *.xls);;CSV (*.csv);;Excel (*.xlsx *.xls)"
        )
        
        if not file_path:
            return
        
        try:
            # Dosyayı oku
            if file_path.endswith('.csv'):
                import csv
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    # İlk satırı oku ve ayracı tespit et
                    first_line = f.readline()
                    f.seek(0)
                    
                    # Noktalı virgül mü virgül mü?
                    if ';' in first_line and first_line.count(';') > first_line.count(','):
                        delimiter = ';'
                    else:
                        delimiter = ','
                    
                    reader = csv.DictReader(f, delimiter=delimiter)
                    rows = list(reader)
            else:
                # Excel
                try:
                    import openpyxl
                    wb = openpyxl.load_workbook(file_path)
                    ws = wb.active
                    
                    # İlk satır başlık
                    headers = [cell.value for cell in ws[1]]
                    rows = []
                    for row in ws.iter_rows(min_row=2, values_only=True):
                        row_dict = {headers[i]: row[i] for i in range(len(headers)) if i < len(row)}
                        rows.append(row_dict)
                except ImportError:
                    QMessageBox.critical(self, "Hata", "Excel için openpyxl gerekli!\npip install openpyxl")
                    return
            
            if not rows:
                QMessageBox.warning(self, "Uyarı", "Dosyada veri bulunamadı.")
                return
            
            # İçe aktarma dialog'unu aç
            dialog = ImportDialog(rows, self)
            if dialog.exec():
                imported = dialog.imported_count
                QMessageBox.information(
                    self, 
                    "Başarılı", 
                    f"{imported} kitap başarıyla içe aktarıldı."
                )
                self.load_books()
                self.shelf_panel.refresh()
                self.filter_bar.refresh_years()
        
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İçe aktarma hatası:\n{str(e)}")


class ImportDialog(QDialog):
    """İçe aktarma dialog'u - sütun eşleştirme ve önizleme."""
    
    def __init__(self, rows: list, parent=None):
        super().__init__(parent)
        self.rows = rows
        self.imported_count = 0
        self.column_mappings = {}
        
        self.setWindowTitle("📥 İçe Aktar")
        self.setMinimumSize(800, 600)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Bilgi
        info = QLabel(f"📄 {len(self.rows)} satır bulundu. Sütunları eşleştirin:")
        info.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # Sütun eşleştirme
        mapping_group = QGroupBox("Sütun Eşleştirme")
        mapping_layout = QGridLayout(mapping_group)
        
        file_columns = list(self.rows[0].keys()) if self.rows else []
        
        # Kitaplık alanları
        app_fields = [
            ("", "-- Atla --"),
            ("title", "Başlık *"),
            ("author", "Yazar"),
            ("publisher", "Yayınevi"),
            ("isbn", "ISBN"),
            ("page_count", "Sayfa Sayısı"),
            ("publish_year", "Yayın Yılı"),
            ("status", "Durum (Okundu/Okunuyor/Okunmadı)"),
            ("rating", "Puan (1-5)"),
            ("shelf", "Raf"),
            ("categories", "Kategori"),
            ("notes", "Notlar"),
        ]
        
        self.combo_mappings = {}
        
        for i, file_col in enumerate(file_columns):
            row = i // 3
            col = (i % 3) * 2
            
            label = QLabel(f"{file_col}:")
            label.setStyleSheet("font-weight: bold;")
            mapping_layout.addWidget(label, row, col)
            
            combo = QComboBox()
            for value, display in app_fields:
                combo.addItem(display, value)
            
            # Otomatik eşleştirme dene
            auto_match = self._guess_mapping(file_col)
            if auto_match:
                for j in range(combo.count()):
                    if combo.itemData(j) == auto_match:
                        combo.setCurrentIndex(j)
                        break
            
            mapping_layout.addWidget(combo, row, col + 1)
            self.combo_mappings[file_col] = combo
        
        layout.addWidget(mapping_group)
        
        # Önizleme
        preview_group = QGroupBox("Önizleme (ilk 5 satır)")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(len(file_columns))
        self.preview_table.setHorizontalHeaderLabels(file_columns)
        self.preview_table.setRowCount(min(5, len(self.rows)))
        
        for i, row in enumerate(self.rows[:5]):
            for j, col in enumerate(file_columns):
                item = QTableWidgetItem(str(row.get(col, "") or ""))
                self.preview_table.setItem(i, j, item)
        
        self.preview_table.resizeColumnsToContents()
        preview_layout.addWidget(self.preview_table)
        layout.addWidget(preview_group)
        
        # Online arama seçeneği
        self.search_online = QCheckBox("📡 Online arama ile bilgileri tamamla (yavaş)")
        layout.addWidget(self.search_online)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        import_btn = QPushButton("📥 İçe Aktar")
        import_btn.clicked.connect(self.do_import)
        btn_layout.addWidget(import_btn)
        
        layout.addLayout(btn_layout)
    
    def _guess_mapping(self, col_name: str) -> str:
        """Sütun adına göre otomatik eşleştirme."""
        col_lower = col_name.lower().replace("_", " ").replace("-", " ")
        
        mappings = {
            "başlık": "title", "kitap": "title", "title": "title", "kitap adı": "title",
            "yazar": "author", "author": "author",
            "yayınevi": "publisher", "publisher": "publisher", "yayinevi": "publisher",
            "isbn": "isbn",
            "sayfa": "page_count", "page": "page_count", "sayfa sayısı": "page_count",
            "yıl": "publish_year", "year": "publish_year", "yayın yılı": "publish_year",
            "durum": "status", "status": "status", "okuma durumu": "status", "okuma": "status",
            "puan": "rating", "rating": "rating",
            "raf": "shelf", "shelf": "shelf",
            "kategori": "categories", "tür": "categories", "category": "categories",
            "not": "notes", "notlar": "notes", "notes": "notes",
        }
        
        for key, value in mappings.items():
            if key in col_lower:
                return value
        return ""
    
    def do_import(self):
        """İçe aktarmayı gerçekleştir."""
        from PyQt6.QtWidgets import QProgressDialog
        from PyQt6.QtCore import Qt, QCoreApplication
        
        # Eşleştirmeleri al
        mappings = {}
        for file_col, combo in self.combo_mappings.items():
            app_field = combo.currentData()
            if app_field:
                mappings[file_col] = app_field
        
        # Başlık eşleştirmesi zorunlu
        if "title" not in mappings.values():
            QMessageBox.warning(self, "Uyarı", "Başlık sütunu eşleştirilmeli!")
            return
        
        # Online arama yapılacak mı?
        do_online_search = self.search_online.isChecked()
        
        # API import
        if do_online_search:
            from services.book_api import search_books
        
        # İlerleme dialog'u
        progress = QProgressDialog("İçe aktarılıyor...", "İptal", 0, len(self.rows), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        imported = 0
        shelf_cache = {}  # Raf adı -> id
        
        for i, row in enumerate(self.rows):
            if progress.wasCanceled():
                break
            
            progress.setValue(i)
            QCoreApplication.processEvents()  # UI güncellemesi
            
            # Satırı kitap verisine dönüştür
            book_data = {}
            shelf_name = None
            status_value = "unread"
            
            for file_col, app_field in mappings.items():
                value = row.get(file_col)
                if value is None or str(value).strip() == "":
                    continue
                
                value = str(value).strip()
                
                if app_field == "shelf":
                    shelf_name = value
                elif app_field == "page_count":
                    try:
                        book_data[app_field] = int(float(value))
                    except:
                        pass
                elif app_field == "publish_year":
                    try:
                        book_data[app_field] = int(float(value))
                    except:
                        pass
                elif app_field == "rating":
                    try:
                        book_data[app_field] = min(5, max(1, int(float(value))))
                    except:
                        pass
                elif app_field == "status":
                    # Durum eşleştirmesi
                    value_lower = value.lower()
                    if "okuduklarım" in value_lower or ("okundu" in value_lower and "okunmadı" not in value_lower):
                        status_value = "read"
                    elif "okuyorum" in value_lower or "okuyor" in value_lower:
                        status_value = "reading"
                    else:
                        status_value = "unread"
                else:
                    book_data[app_field] = value
            
            # Başlık yoksa atla
            if not book_data.get("title"):
                continue
            
            progress.setLabelText(f"({i+1}/{len(self.rows)}) {book_data.get('title', '')[:40]}...")
            QCoreApplication.processEvents()
            
            # Online arama
            if do_online_search:
                search_query = book_data.get("title", "")
                if book_data.get("author"):
                    search_query += " " + book_data["author"]
                
                try:
                    results = search_books(search_query, "title")
                    if results:
                        # En iyi eşleşmeyi bul
                        best = results[0]
                        
                        # API'den gelen verileri ekle (mevcut olmayanları)
                        if not book_data.get("isbn") and best.isbn:
                            book_data["isbn"] = best.isbn
                        if not book_data.get("page_count") and best.page_count:
                            book_data["page_count"] = best.page_count
                        if not book_data.get("publish_year") and best.publish_year:
                            book_data["publish_year"] = best.publish_year
                        if not book_data.get("publisher") and best.publisher:
                            book_data["publisher"] = best.publisher
                        if best.cover_url:
                            # Kapağı indir
                            from services.book_api import download_cover
                            cover_path = download_cover(best.cover_url, best.isbn or book_data.get("title", "book"))
                            if cover_path:
                                book_data["cover_path"] = cover_path
                        if best.description:
                            book_data["description"] = best.description[:1000]
                        if best.language:
                            book_data["language"] = best.language
                        if best.categories:
                            book_data["categories"] = best.categories
                except Exception as e:
                    print(f"API hatası: {e}")
            
            # Kitabı ekle
            book_id = db.add_book(**book_data)
            
            # Durumu güncelle
            db.update_book(book_id, status=status_value)
            
            imported += 1
            
            # Raf varsa ekle
            if shelf_name:
                if shelf_name not in shelf_cache:
                    # Rafı bul veya oluştur
                    shelves = db.get_all_shelves()
                    shelf_id = None
                    for shelf in shelves:
                        if shelf["name"].lower() == shelf_name.lower():
                            shelf_id = shelf["id"]
                            break
                    
                    if shelf_id is None:
                        shelf_id = db.add_shelf(shelf_name)
                    
                    shelf_cache[shelf_name] = shelf_id
                
                if shelf_cache.get(shelf_name):
                    db.add_book_to_shelf(book_id, shelf_cache[shelf_name])
        
        progress.setValue(len(self.rows))
        self.imported_count = imported
        self.accept()


# ============================================================
# ALINTILAR DIALOG'U
# ============================================================

class QuotesDialog(QDialog):
    """Kitap alıntıları dialog'u."""
    
    def __init__(self, book_id: int, book_title: str, parent=None):
        super().__init__(parent)
        
        self.book_id = book_id
        self.book_title = book_title
        
        self.setWindowTitle(f"💬 Alıntılar - {book_title}")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        self.setup_ui()
        self.load_quotes()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Yeni alıntı ekleme alanı
        add_group = QGroupBox("Yeni Alıntı Ekle")
        add_layout = QVBoxLayout(add_group)
        
        self.quote_text = QTextEdit()
        self.quote_text.setPlaceholderText("Alıntı metnini buraya yazın...")
        self.quote_text.setMaximumHeight(80)
        add_layout.addWidget(self.quote_text)
        
        details_layout = QHBoxLayout()
        
        self.page_input = QSpinBox()
        self.page_input.setRange(0, 99999)
        self.page_input.setSpecialValueText("Sayfa")
        self.page_input.setFixedWidth(80)
        details_layout.addWidget(QLabel("Sayfa:"))
        details_layout.addWidget(self.page_input)
        
        self.chapter_input = QLineEdit()
        self.chapter_input.setPlaceholderText("Bölüm (opsiyonel)")
        self.chapter_input.setFixedWidth(150)
        details_layout.addWidget(self.chapter_input)
        
        details_layout.addStretch()
        
        add_btn = QPushButton("➕ Ekle")
        add_btn.clicked.connect(self.add_quote)
        details_layout.addWidget(add_btn)
        
        add_layout.addLayout(details_layout)
        layout.addWidget(add_group)
        
        # Alıntı listesi
        self.quotes_list = QListWidget()
        self.quotes_list.setAlternatingRowColors(True)
        self.quotes_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.quotes_list.customContextMenuRequested.connect(self.show_quote_menu)
        layout.addWidget(self.quotes_list, stretch=1)
        
        # Kapat butonu
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def load_quotes(self):
        """Alıntıları yükler."""
        self.quotes_list.clear()
        
        quotes = db.get_quotes_by_book(self.book_id)
        
        for quote in quotes:
            text = quote["text"]
            if len(text) > 100:
                text = text[:100] + "..."
            
            info = []
            if quote["page_number"]:
                info.append(f"s.{quote['page_number']}")
            if quote["chapter"]:
                info.append(quote["chapter"])
            
            display = f'"{text}"'
            if info:
                display += f" ({', '.join(info)})"
            
            if quote["is_favorite"]:
                display = "⭐ " + display
            
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, quote["id"])
            item.setData(Qt.ItemDataRole.UserRole + 1, quote["text"])
            self.quotes_list.addItem(item)
    
    def add_quote(self):
        """Yeni alıntı ekler."""
        text = self.quote_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Uyarı", "Alıntı metni boş olamaz!")
            return
        
        page = self.page_input.value() or None
        chapter = self.chapter_input.text().strip() or None
        
        db.add_quote(self.book_id, text, page, chapter)
        
        # Formu temizle
        self.quote_text.clear()
        self.page_input.setValue(0)
        self.chapter_input.clear()
        
        self.load_quotes()
    
    def show_quote_menu(self, position):
        """Alıntı sağ tık menüsü."""
        item = self.quotes_list.itemAt(position)
        if not item:
            return
        
        quote_id = item.data(Qt.ItemDataRole.UserRole)
        full_text = item.data(Qt.ItemDataRole.UserRole + 1)
        
        menu = QMenu(self)
        
        # Tam metni göster
        view_action = menu.addAction("👁️ Tam Metni Gör")
        view_action.triggered.connect(lambda: QMessageBox.information(self, "Alıntı", full_text))
        
        # Favori
        fav_action = menu.addAction("⭐ Favori Yap/Kaldır")
        fav_action.triggered.connect(lambda: self.toggle_favorite(quote_id))
        
        menu.addSeparator()
        
        # Sil
        delete_action = menu.addAction("🗑️ Sil")
        delete_action.triggered.connect(lambda: self.delete_quote(quote_id))
        
        menu.exec(self.quotes_list.mapToGlobal(position))
    
    def toggle_favorite(self, quote_id: int):
        """Favori durumunu değiştirir."""
        db.toggle_quote_favorite(quote_id)
        self.load_quotes()
    
    def delete_quote(self, quote_id: int):
        """Alıntıyı siler."""
        reply = QMessageBox.question(
            self, "Silme Onayı",
            "Bu alıntıyı silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_quote(quote_id)
            self.load_quotes()


# ============================================================
# TOPLU DÜZENLEME DIALOG'U
# ============================================================

class BulkEditDialog(QDialog):
    """Birden fazla kitabı düzenleme dialog'u."""
    
    def __init__(self, book_ids: list, parent=None):
        super().__init__(parent)
        
        self.book_ids = book_ids
        
        self.setWindowTitle(f"✏️ Toplu Düzenle ({len(book_ids)} kitap)")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        info = QLabel(f"📚 {len(self.book_ids)} kitap seçili.\nSadece değiştirmek istediğiniz alanları doldurun.")
        info.setStyleSheet("color: #888;")
        layout.addWidget(info)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        # Durum
        self.status_combo = QComboBox()
        self.status_combo.addItem("-- Değiştirme --", "")
        self.status_combo.addItem("📕 Okunmadı", "unread")
        self.status_combo.addItem("📋 Okuyacağım", "to_read")
        self.status_combo.addItem("📖 Okunuyor", "reading")
        self.status_combo.addItem("📗 Okundu", "read")
        self.status_combo.addItem("🚫 Okumayacağım", "wont_read")
        form.addRow("Durum:", self.status_combo)
        
        # Puan
        self.rating_combo = QComboBox()
        self.rating_combo.addItem("-- Değiştirme --", 0)
        self.rating_combo.addItem("⭐", 1)
        self.rating_combo.addItem("⭐⭐", 2)
        self.rating_combo.addItem("⭐⭐⭐", 3)
        self.rating_combo.addItem("⭐⭐⭐⭐", 4)
        self.rating_combo.addItem("⭐⭐⭐⭐⭐", 5)
        form.addRow("Puan:", self.rating_combo)
        
        # Dil
        self.language_input = QComboBox()
        self.language_input.setEditable(True)
        self.language_input.addItems(["", "tr", "en", "de", "fr", "es"])
        form.addRow("Dil:", self.language_input)
        
        # Konum
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Fiziksel konum")
        form.addRow("Konum:", self.location_input)
        
        # Etiketler
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Etiketler (virgülle ayır)")
        form.addRow("Etiketler:", self.tags_input)
        
        layout.addLayout(form)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Uygula")
        save_btn.clicked.connect(self.apply_changes)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def apply_changes(self):
        """Değişiklikleri uygular."""
        updates = {}
        
        status = self.status_combo.currentData()
        if status:
            updates["status"] = status
        
        rating = self.rating_combo.currentData()
        if rating:
            updates["rating"] = rating
        
        language = self.language_input.currentText().strip()
        if language:
            updates["language"] = language
        
        location = self.location_input.text().strip()
        if location:
            updates["location"] = location
        
        tags = self.tags_input.text().strip()
        if tags:
            updates["tags"] = tags
        
        if not updates:
            QMessageBox.warning(self, "Uyarı", "Hiçbir alan değiştirilmedi!")
            return
        
        updated = db.bulk_update_books(self.book_ids, **updates)
        QMessageBox.information(self, "Başarılı", f"{updated} kitap güncellendi.")
        self.accept()


# ============================================================
# OKUMA HEDEFİ DIALOG'U
# ============================================================

class ReadingGoalDialog(QDialog):
    """Okuma hedefi belirleme dialog'u."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("🎯 Okuma Hedefi")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        self.setup_ui()
        self.load_goals()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Yeni hedef ekleme
        add_group = QGroupBox("Yeni Hedef Belirle")
        add_layout = QHBoxLayout(add_group)
        
        from datetime import datetime
        current_year = datetime.now().year
        
        self.year_input = QSpinBox()
        self.year_input.setRange(2000, 2100)
        self.year_input.setValue(current_year)
        add_layout.addWidget(QLabel("Yıl:"))
        add_layout.addWidget(self.year_input)
        
        self.target_input = QSpinBox()
        self.target_input.setRange(1, 1000)
        self.target_input.setValue(12)
        add_layout.addWidget(QLabel("Hedef:"))
        add_layout.addWidget(self.target_input)
        add_layout.addWidget(QLabel("kitap"))
        
        add_btn = QPushButton("➕ Ekle")
        add_btn.clicked.connect(self.add_goal)
        add_layout.addWidget(add_btn)
        
        layout.addWidget(add_group)
        
        # Mevcut hedefler
        self.goals_list = QListWidget()
        self.goals_list.setAlternatingRowColors(True)
        layout.addWidget(self.goals_list, stretch=1)
        
        # Kapat
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def load_goals(self):
        """Hedefleri yükler."""
        self.goals_list.clear()
        
        goals = db.get_all_reading_goals()
        
        for goal in goals:
            progress_bar = f"[{'█' * int(goal['progress'] / 10)}{'░' * (10 - int(goal['progress'] / 10))}]"
            
            text = f"{goal['year']}: {goal['completed']}/{goal['target_books']} kitap ({goal['progress']}%) {progress_bar}"
            
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, goal["year"])
            
            # Hedef tamamlandıysa yeşil
            if goal['completed'] >= goal['target_books']:
                item.setForeground(Qt.GlobalColor.green)
            
            self.goals_list.addItem(item)
    
    def add_goal(self):
        """Yeni hedef ekler."""
        year = self.year_input.value()
        target = self.target_input.value()
        
        db.set_reading_goal(year, target)
        self.load_goals()
        QMessageBox.information(self, "Başarılı", f"{year} için {target} kitap hedefi belirlendi!")


# ============================================================
# TÜM ALINTILAR DIALOG'U
# ============================================================

class AllQuotesDialog(QDialog):
    """Tüm kitaplardan alıntıları gösteren dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("💬 Tüm Alıntılar")
        self.setMinimumSize(700, 500)
        self.setModal(True)
        
        self.setup_ui()
        self.load_quotes()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Filtre
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("🔍"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Alıntılarda ara...")
        self.search_input.textChanged.connect(self.filter_quotes)
        filter_layout.addWidget(self.search_input)
        
        self.fav_only = QCheckBox("Sadece Favoriler")
        self.fav_only.toggled.connect(self.load_quotes)
        filter_layout.addWidget(self.fav_only)
        
        layout.addLayout(filter_layout)
        
        # Alıntı listesi
        self.quotes_list = QListWidget()
        self.quotes_list.setAlternatingRowColors(True)
        self.quotes_list.setWordWrap(True)
        self.quotes_list.itemDoubleClicked.connect(self.show_full_quote)
        layout.addWidget(self.quotes_list, stretch=1)
        
        # Kapat
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def load_quotes(self):
        """Alıntıları yükler."""
        self.quotes_list.clear()
        
        quotes = db.get_all_quotes()
        
        for quote in quotes:
            # Favori filtresi
            if self.fav_only.isChecked() and not quote["is_favorite"]:
                continue
            
            text = quote["text"]
            if len(text) > 150:
                text = text[:150] + "..."
            
            display = f'"{text}"\n📖 {quote["book_title"]} - {quote["book_author"] or "Bilinmeyen"}'
            
            if quote["page_number"]:
                display += f" (s.{quote['page_number']})"
            
            if quote["is_favorite"]:
                display = "⭐ " + display
            
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, quote["id"])
            item.setData(Qt.ItemDataRole.UserRole + 1, quote["text"])
            item.setData(Qt.ItemDataRole.UserRole + 2, quote["book_title"])
            self.quotes_list.addItem(item)
    
    def filter_quotes(self, text: str):
        """Alıntıları filtreler."""
        text = text.lower()
        
        for i in range(self.quotes_list.count()):
            item = self.quotes_list.item(i)
            full_text = item.data(Qt.ItemDataRole.UserRole + 1).lower()
            book_title = item.data(Qt.ItemDataRole.UserRole + 2).lower()
            
            visible = text in full_text or text in book_title
            item.setHidden(not visible)
    
    def show_full_quote(self, item):
        """Tam alıntıyı gösterir."""
        full_text = item.data(Qt.ItemDataRole.UserRole + 1)
        book_title = item.data(Qt.ItemDataRole.UserRole + 2)
        
        QMessageBox.information(self, f"📖 {book_title}", full_text)


# ============================================================
# OKUMA LİSTESİ DIALOG'U
# ============================================================

class ReadingListDialog(QDialog):
    """Okuma listesi - sıralı, tahmini süre ile."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("📋 Okuma Listesi")
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        # Okuma hızı ayarları
        self.pages_per_day = 30  # Günlük sayfa
        
        self.setup_ui()
        self.load_reading_list()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        
        # Sol: Okuma listesi
        left_layout = QVBoxLayout()
        
        left_layout.addWidget(QLabel("📋 Okuma Sıram:"))
        
        self.reading_list = QListWidget()
        self.reading_list.setAlternatingRowColors(True)
        self.reading_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.reading_list.currentItemChanged.connect(self.on_book_selected)
        self.reading_list.model().rowsMoved.connect(self.on_list_reordered)
        left_layout.addWidget(self.reading_list, stretch=1)
        
        # Sıralama butonları
        order_layout = QHBoxLayout()
        
        up_btn = QPushButton("⬆️ Yukarı")
        up_btn.clicked.connect(lambda: self.move_book("up"))
        order_layout.addWidget(up_btn)
        
        down_btn = QPushButton("⬇️ Aşağı")
        down_btn.clicked.connect(lambda: self.move_book("down"))
        order_layout.addWidget(down_btn)
        
        remove_btn = QPushButton("❌ Listeden Çıkar")
        remove_btn.clicked.connect(self.remove_from_list)
        order_layout.addWidget(remove_btn)
        
        left_layout.addLayout(order_layout)
        
        layout.addLayout(left_layout, stretch=2)
        
        # Sağ: Detaylar ve ayarlar
        right_layout = QVBoxLayout()
        
        # Okuma hızı ayarları
        speed_group = QGroupBox("⏱️ Okuma Hızı Ayarları")
        speed_layout = QFormLayout(speed_group)
        speed_layout.setSpacing(10)
        
        self.pages_per_day_input = QSpinBox()
        self.pages_per_day_input.setRange(1, 500)
        self.pages_per_day_input.setValue(self.pages_per_day)
        self.pages_per_day_input.valueChanged.connect(self.on_speed_changed)
        speed_layout.addRow("Günlük sayfa:", self.pages_per_day_input)
        
        self.minutes_per_page = QSpinBox()
        self.minutes_per_page.setRange(1, 30)
        self.minutes_per_page.setValue(2)
        self.minutes_per_page.valueChanged.connect(self.on_speed_changed)
        speed_layout.addRow("Sayfa başı dakika:", self.minutes_per_page)
        
        right_layout.addWidget(speed_group)
        
        # Seçili kitap bilgisi
        book_group = QGroupBox("📖 Seçili Kitap")
        book_layout = QVBoxLayout(book_group)
        
        self.book_title_label = QLabel("Kitap seçin")
        self.book_title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.book_title_label.setWordWrap(True)
        book_layout.addWidget(self.book_title_label)
        
        self.book_author_label = QLabel("")
        self.book_author_label.setStyleSheet("color: #888;")
        book_layout.addWidget(self.book_author_label)
        
        self.book_pages_label = QLabel("")
        book_layout.addWidget(self.book_pages_label)
        
        self.book_estimate_label = QLabel("")
        self.book_estimate_label.setStyleSheet("font-size: 13px; color: #4EC9B0;")
        book_layout.addWidget(self.book_estimate_label)
        
        right_layout.addWidget(book_group)
        
        # Toplam istatistik
        stats_group = QGroupBox("📊 Toplam")
        stats_layout = QVBoxLayout(stats_group)
        
        self.total_books_label = QLabel("Kitap: 0")
        stats_layout.addWidget(self.total_books_label)
        
        self.total_pages_label = QLabel("Sayfa: 0")
        stats_layout.addWidget(self.total_pages_label)
        
        self.total_time_label = QLabel("Tahmini süre: -")
        self.total_time_label.setStyleSheet("font-weight: bold; color: #CCA700;")
        stats_layout.addWidget(self.total_time_label)
        
        self.finish_date_label = QLabel("Bitiş tarihi: -")
        self.finish_date_label.setStyleSheet("color: #4EC9B0;")
        stats_layout.addWidget(self.finish_date_label)
        
        right_layout.addWidget(stats_group)
        
        # Kitap ekle
        add_group = QGroupBox("➕ Listeye Ekle")
        add_layout = QVBoxLayout(add_group)
        
        self.candidates_combo = QComboBox()
        self.candidates_combo.setPlaceholderText("Okunmamış kitaplardan seç...")
        add_layout.addWidget(self.candidates_combo)
        
        add_btn = QPushButton("➕ Listeye Ekle")
        add_btn.clicked.connect(self.add_to_list)
        add_layout.addWidget(add_btn)
        
        right_layout.addWidget(add_group)
        
        right_layout.addStretch()
        
        # Kapat
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.accept)
        right_layout.addWidget(close_btn)
        
        layout.addLayout(right_layout, stretch=1)
    
    def load_reading_list(self):
        """Okuma listesini yükler."""
        self.reading_list.clear()
        
        books = db.get_reading_list()
        
        for i, book in enumerate(books, start=1):
            pages = book["page_count"] or 0
            estimate = self.calculate_days(pages)
            
            text = f"{i}. {book['title']}"
            if book["author"]:
                text += f" - {book['author']}"
            text += f"\n   📄 {pages} sayfa • ⏱️ ~{estimate} gün"
            
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, book["id"])
            item.setData(Qt.ItemDataRole.UserRole + 1, dict(book))
            self.reading_list.addItem(item)
        
        # Aday kitapları yükle
        self.load_candidates()
        
        # İstatistikleri güncelle
        self.update_stats()
    
    def load_candidates(self):
        """Listeye eklenebilecek kitapları yükler."""
        self.candidates_combo.clear()
        self.candidates_combo.addItem("Okunmamış kitaplardan seç...", None)
        
        books = db.get_books_to_read_candidates()
        
        for book in books:
            text = book["title"]
            if book["author"]:
                text += f" - {book['author']}"
            self.candidates_combo.addItem(text, book["id"])
    
    def calculate_days(self, pages: int) -> int:
        """Sayfa sayısından gün hesaplar."""
        if pages <= 0 or self.pages_per_day <= 0:
            return 0
        return max(1, round(pages / self.pages_per_day))
    
    def calculate_hours(self, pages: int) -> float:
        """Sayfa sayısından saat hesaplar."""
        minutes = pages * self.minutes_per_page.value()
        return round(minutes / 60, 1)
    
    def on_book_selected(self, current, previous):
        """Kitap seçildiğinde detayları göster."""
        if not current:
            return
        
        book = current.data(Qt.ItemDataRole.UserRole + 1)
        if not book:
            return
        
        self.book_title_label.setText(book.get("title", ""))
        self.book_author_label.setText(book.get("author", "") or "")
        
        pages = book.get("page_count") or 0
        self.book_pages_label.setText(f"📄 {pages} sayfa")
        
        days = self.calculate_days(pages)
        hours = self.calculate_hours(pages)
        self.book_estimate_label.setText(f"⏱️ ~{days} gün ({hours} saat)")
    
    def on_speed_changed(self):
        """Okuma hızı değiştiğinde."""
        self.pages_per_day = self.pages_per_day_input.value()
        self.load_reading_list()
    
    def on_list_reordered(self):
        """Liste sürükle-bırak ile yeniden sıralandığında."""
        book_ids = []
        for i in range(self.reading_list.count()):
            item = self.reading_list.item(i)
            book_ids.append(item.data(Qt.ItemDataRole.UserRole))
        
        db.reorder_reading_list(book_ids)
        self.load_reading_list()
    
    def move_book(self, direction: str):
        """Kitabı yukarı/aşağı taşır."""
        current = self.reading_list.currentItem()
        if not current:
            return
        
        book_id = current.data(Qt.ItemDataRole.UserRole)
        db.move_in_reading_list(book_id, direction)
        self.load_reading_list()
    
    def add_to_list(self):
        """Seçili kitabı listeye ekler."""
        book_id = self.candidates_combo.currentData()
        if not book_id:
            return
        
        db.add_to_reading_list(book_id)
        self.load_reading_list()
    
    def remove_from_list(self):
        """Seçili kitabı listeden çıkarır."""
        current = self.reading_list.currentItem()
        if not current:
            return
        
        book_id = current.data(Qt.ItemDataRole.UserRole)
        db.remove_from_reading_list(book_id)
        self.load_reading_list()
    
    def update_stats(self):
        """Toplam istatistikleri günceller."""
        books = db.get_reading_list()
        
        total_books = len(books)
        total_pages = sum(b["page_count"] or 0 for b in books)
        total_days = self.calculate_days(total_pages)
        total_hours = self.calculate_hours(total_pages)
        
        self.total_books_label.setText(f"📚 {total_books} kitap")
        self.total_pages_label.setText(f"📄 {total_pages} sayfa")
        self.total_time_label.setText(f"⏱️ ~{total_days} gün ({total_hours} saat)")
        
        # Bitiş tarihi
        from datetime import datetime, timedelta
        finish_date = datetime.now() + timedelta(days=total_days)
        self.finish_date_label.setText(f"📅 Tahmini bitiş: {finish_date.strftime('%d %B %Y')}")


# ============================================================
# SERİLER DIALOG'U
# ============================================================

class SeriesDialog(QDialog):
    """Kitap serileri dialog'u."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.selected_series = None
        
        self.setWindowTitle("📚 Kitap Serileri")
        self.setMinimumSize(700, 500)
        self.setModal(True)
        
        self.setup_ui()
        self.load_series()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        
        # Sol: Seri listesi
        left_layout = QVBoxLayout()
        
        left_layout.addWidget(QLabel("📚 Seriler"))
        
        self.series_list = QListWidget()
        self.series_list.setAlternatingRowColors(True)
        self.series_list.currentItemChanged.connect(self.on_series_selected)
        self.series_list.itemDoubleClicked.connect(self.on_series_double_clicked)
        left_layout.addWidget(self.series_list)
        
        layout.addLayout(left_layout, stretch=1)
        
        # Sağ: Seri detayları
        right_layout = QVBoxLayout()
        
        # Seri başlığı
        self.series_title = QLabel("Seri seçin")
        self.series_title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        right_layout.addWidget(self.series_title)
        
        # İstatistikler
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background-color: #2D2D2D; border-radius: 8px; padding: 10px;")
        stats_layout = QGridLayout(stats_frame)
        
        self.stat_total = QLabel("Toplam: -")
        self.stat_read = QLabel("Okunan: -")
        self.stat_reading = QLabel("Okuyor: -")
        self.stat_unread = QLabel("Okunmadı: -")
        self.stat_pages = QLabel("Toplam sayfa: -")
        self.stat_rating = QLabel("Ortalama puan: -")
        
        stats_layout.addWidget(self.stat_total, 0, 0)
        stats_layout.addWidget(self.stat_read, 0, 1)
        stats_layout.addWidget(self.stat_reading, 1, 0)
        stats_layout.addWidget(self.stat_unread, 1, 1)
        stats_layout.addWidget(self.stat_pages, 2, 0)
        stats_layout.addWidget(self.stat_rating, 2, 1)
        
        right_layout.addWidget(stats_frame)
        
        # İlerleme çubuğu
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("font-size: 14px; padding: 10px;")
        right_layout.addWidget(self.progress_label)
        
        # Serideki kitaplar
        right_layout.addWidget(QLabel("📖 Serideki Kitaplar:"))
        
        self.books_list = QListWidget()
        self.books_list.setAlternatingRowColors(True)
        right_layout.addWidget(self.books_list, stretch=1)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        show_btn = QPushButton("📖 Seriyi Göster")
        show_btn.clicked.connect(self.show_series)
        btn_layout.addWidget(show_btn)
        
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)
        
        right_layout.addLayout(btn_layout)
        
        layout.addLayout(right_layout, stretch=2)
    
    def load_series(self):
        """Serileri yükler."""
        self.series_list.clear()
        
        series_list = db.get_all_series()
        
        if not series_list:
            item = QListWidgetItem("Henüz seri yok")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.series_list.addItem(item)
            return
        
        for series in series_list:
            # Durum ikonu
            if series["is_complete"]:
                icon = "✅"  # Tamamı okundu
            elif series["read_count"] > 0:
                icon = "📖"  # Bir kısmı okundu
            else:
                icon = "📚"  # Hiç okunmadı
            
            text = f"{icon} {series['name']} ({series['book_count']} kitap)"
            
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, series["name"])
            self.series_list.addItem(item)
    
    def on_series_selected(self, current, previous):
        """Seri seçildiğinde detayları göster."""
        if not current:
            return
        
        series_name = current.data(Qt.ItemDataRole.UserRole)
        if not series_name:
            return
        
        # İstatistikleri al
        stats = db.get_series_stats(series_name)
        if not stats:
            return
        
        # Başlık
        self.series_title.setText(f"📚 {series_name}")
        
        # İstatistikler
        self.stat_total.setText(f"📚 Toplam: {stats['total']} kitap")
        self.stat_read.setText(f"✅ Okunan: {stats['read_count']}")
        self.stat_reading.setText(f"📖 Okuyor: {stats['reading_count']}")
        self.stat_unread.setText(f"📕 Okunmadı: {stats['unread_count']}")
        self.stat_pages.setText(f"📄 Sayfa: {stats['total_pages'] or 0}")
        
        if stats['avg_rating']:
            self.stat_rating.setText(f"⭐ Puan: {stats['avg_rating']}")
        else:
            self.stat_rating.setText("⭐ Puan: -")
        
        # İlerleme
        progress = stats['progress']
        bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
        
        if stats['is_complete']:
            self.progress_label.setText(f"🎉 Seri tamamlandı! [{bar}] {progress}%")
            self.progress_label.setStyleSheet("color: #4EC9B0; font-size: 14px; padding: 10px;")
        else:
            self.progress_label.setText(f"İlerleme: [{bar}] {progress}%")
            self.progress_label.setStyleSheet("color: #CCA700; font-size: 14px; padding: 10px;")
        
        # Kitapları listele
        self.books_list.clear()
        books = db.get_books_in_series(series_name)
        
        for book in books:
            # Durum ikonu
            status_icons = {"read": "✅", "reading": "📖", "unread": "📕"}
            icon = status_icons.get(book["status"], "📕")
            
            # Sıra numarası
            order = f"#{book['series_order']}" if book["series_order"] else ""
            
            # Puan
            rating = "⭐" * (book["rating"] or 0) if book["rating"] else ""
            
            text = f"{icon} {order} {book['title']} {rating}"
            
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, book["id"])
            self.books_list.addItem(item)
    
    def on_series_double_clicked(self, item):
        """Seriye çift tıklandığında göster."""
        self.show_series()
    
    def show_series(self):
        """Seçili seriyi ana listede göster."""
        current = self.series_list.currentItem()
        if current:
            self.selected_series = current.data(Qt.ItemDataRole.UserRole)
            if self.selected_series:
                self.accept()


# ============================================================
# AI ASISTAN DIALOG'U
# ============================================================

class AIWorkerThread(QThread):
    """AI yanıtını arka planda alır."""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            if result:
                self.finished.emit(result)
            else:
                self.error.emit("Yanıt alınamadı. Ollama çalışıyor mu?")
        except Exception as e:
            self.error.emit(str(e))


class AIAssistantDialog(QDialog):
    """AI Asistan dialog'u - Ollama ile kitap önerileri."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("🤖 AI Kitap Asistanı")
        self.setMinimumSize(700, 600)
        self.setModal(True)
        
        self.worker = None
        self.model = None
        
        self.setup_ui()
        self.check_ollama()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Durum çubuğu
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet("background-color: #2D2D2D; border-radius: 8px; padding: 10px;")
        status_layout = QHBoxLayout(self.status_frame)
        
        self.status_icon = QLabel("⏳")
        self.status_icon.setStyleSheet("font-size: 24px;")
        status_layout.addWidget(self.status_icon)
        
        self.status_label = QLabel("Ollama kontrol ediliyor...")
        self.status_label.setStyleSheet("font-size: 14px;")
        status_layout.addWidget(self.status_label, stretch=1)
        
        self.model_combo = QComboBox()
        self.model_combo.setFixedWidth(150)
        self.model_combo.setEnabled(False)
        status_layout.addWidget(self.model_combo)
        
        layout.addWidget(self.status_frame)
        
        # Hızlı eylemler
        actions_label = QLabel("🚀 Hızlı Eylemler:")
        actions_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(actions_label)
        
        actions_layout = QHBoxLayout()
        
        self.recommend_btn = QPushButton("📚 Kitap Öner")
        self.recommend_btn.clicked.connect(self.get_recommendations)
        self.recommend_btn.setEnabled(False)
        actions_layout.addWidget(self.recommend_btn)
        
        self.analyze_btn = QPushButton("📊 Okuma Analizi")
        self.analyze_btn.clicked.connect(self.analyze_habits)
        self.analyze_btn.setEnabled(False)
        actions_layout.addWidget(self.analyze_btn)
        
        self.plan_btn = QPushButton("📅 Okuma Planı")
        self.plan_btn.clicked.connect(self.get_reading_plan)
        self.plan_btn.setEnabled(False)
        actions_layout.addWidget(self.plan_btn)
        
        layout.addLayout(actions_layout)
        
        # Soru sor
        question_layout = QHBoxLayout()
        
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Bir soru sor... (örn: 'Dostoyevski gibi başka yazarlar öner')")
        self.question_input.returnPressed.connect(self.ask_question)
        self.question_input.setEnabled(False)
        question_layout.addWidget(self.question_input)
        
        self.ask_btn = QPushButton("Sor")
        self.ask_btn.clicked.connect(self.ask_question)
        self.ask_btn.setEnabled(False)
        question_layout.addWidget(self.ask_btn)
        
        layout.addLayout(question_layout)
        
        # Yanıt alanı
        layout.addWidget(QLabel("💬 Yanıt:"))
        
        self.response_text = QTextEdit()
        self.response_text.setReadOnly(True)
        self.response_text.setPlaceholderText("AI yanıtı burada görünecek...")
        self.response_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                border: 1px solid #3C3C3C;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(self.response_text, stretch=1)
        
        # Alt bilgi
        info_label = QLabel("💡 İpucu: Ollama kurulu değilse 'brew install ollama && ollama pull mistral' ile kurabilirsiniz.")
        info_label.setStyleSheet("color: #888; font-size: 11px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Kapat butonu
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def check_ollama(self):
        """Ollama durumunu kontrol eder."""
        try:
            from services.ai_service import check_ollama_status
            
            status = check_ollama_status()
            
            if status["available"]:
                self.status_icon.setText("✅")
                self.status_label.setText(f"Ollama hazır!")
                self.model = status["recommended"]
                
                # Modelleri ekle
                self.model_combo.clear()
                for model in status["models"]:
                    self.model_combo.addItem(model)
                
                # Önerilen modeli seç
                index = self.model_combo.findText(self.model)
                if index >= 0:
                    self.model_combo.setCurrentIndex(index)
                
                self.model_combo.setEnabled(True)
                self.model_combo.currentTextChanged.connect(self.on_model_changed)
                
                # Butonları aktif et
                self.recommend_btn.setEnabled(True)
                self.analyze_btn.setEnabled(True)
                self.plan_btn.setEnabled(True)
                self.question_input.setEnabled(True)
                self.ask_btn.setEnabled(True)
            else:
                self.status_icon.setText("❌")
                self.status_label.setText(status.get("error", "Ollama bulunamadı"))
                
        except ImportError:
            self.status_icon.setText("❌")
            self.status_label.setText("AI servisi yüklenemedi")
        except Exception as e:
            self.status_icon.setText("❌")
            self.status_label.setText(f"Hata: {str(e)}")
    
    def on_model_changed(self, model_name):
        """Model değiştiğinde."""
        self.model = model_name
    
    def set_loading(self, loading: bool):
        """Yükleniyor durumunu ayarlar."""
        self.recommend_btn.setEnabled(not loading)
        self.analyze_btn.setEnabled(not loading)
        self.plan_btn.setEnabled(not loading)
        self.ask_btn.setEnabled(not loading)
        self.question_input.setEnabled(not loading)
        
        if loading:
            self.response_text.setPlainText("⏳ Düşünüyorum...")
            self.status_icon.setText("⏳")
        else:
            self.status_icon.setText("✅")
    
    def on_response(self, response: str):
        """AI yanıtı geldiğinde."""
        self.set_loading(False)
        self.response_text.setPlainText(response)
    
    def on_error(self, error: str):
        """Hata olduğunda."""
        self.set_loading(False)
        self.response_text.setPlainText(f"❌ Hata: {error}")
    
    def get_recommendations(self):
        """Kitap önerisi al."""
        from services.ai_service import get_book_recommendation
        
        books = db.get_all_books()
        if not books:
            self.response_text.setPlainText("Kitaplığınız boş. Önce kitap ekleyin!")
            return
        
        self.set_loading(True)
        
        self.worker = AIWorkerThread(
            get_book_recommendation,
            [dict(b) for b in books],
            model=self.model
        )
        self.worker.finished.connect(self.on_response)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def analyze_habits(self):
        """Okuma alışkanlıklarını analiz et."""
        from services.ai_service import analyze_reading_habits
        
        books = db.get_all_books()
        if not books:
            self.response_text.setPlainText("Kitaplığınız boş. Önce kitap ekleyin!")
            return
        
        self.set_loading(True)
        
        self.worker = AIWorkerThread(
            analyze_reading_habits,
            [dict(b) for b in books],
            model=self.model
        )
        self.worker.finished.connect(self.on_response)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def get_reading_plan(self):
        """Okuma planı oluştur."""
        from services.ai_service import get_reading_plan
        
        books = db.get_all_books()
        if not books:
            self.response_text.setPlainText("Kitaplığınız boş. Önce kitap ekleyin!")
            return
        
        # Hedefi al
        from datetime import datetime
        goal_data = db.get_reading_goal(datetime.now().year)
        goal = goal_data["target_books"] if goal_data else None
        
        self.set_loading(True)
        
        self.worker = AIWorkerThread(
            get_reading_plan,
            [dict(b) for b in books],
            goal=goal,
            model=self.model
        )
        self.worker.finished.connect(self.on_response)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def ask_question(self):
        """Serbest soru sor."""
        from services.ai_service import generate_response, create_book_summary
        
        question = self.question_input.text().strip()
        if not question:
            return
        
        books = db.get_all_books()
        context = create_book_summary([dict(b) for b in books]) if books else "Kitaplık boş."
        
        prompt = f"""Sen bir kitap uzmanısın. Kullanıcının kitaplığı hakkında bilgin var.

{context}

Kullanıcının sorusu: {question}

Türkçe ve yardımcı bir şekilde yanıtla."""
        
        self.set_loading(True)
        self.question_input.clear()
        
        self.worker = AIWorkerThread(
            generate_response,
            prompt,
            model=self.model
        )
        self.worker.finished.connect(self.on_response)
        self.worker.error.connect(self.on_error)
        self.worker.start()