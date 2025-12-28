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
)
from PyQt6.QtCore import Qt, QSize  # Hizalama sabitleri vs.
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
        
        # Kitap Ara ve Ekle
        search_action = QAction("🔍 Ara ve Ekle", self)
        search_action.setShortcut("Ctrl+N")
        search_action.triggered.connect(self.on_search_add_clicked)
        file_menu.addAction(search_action)
        
        # Manuel Ekle
        manual_action = QAction("✏️ Manuel Ekle", self)
        manual_action.setShortcut("Ctrl+Shift+N")
        manual_action.triggered.connect(self.on_manual_add_clicked)
        file_menu.addAction(manual_action)
        
        file_menu.addSeparator()
        
        # İçe Aktar
        import_action = QAction("📥 İçe Aktar (CSV/Excel)...", self)
        import_action.triggered.connect(self.import_books)
        file_menu.addAction(import_action)
        
        # Dışa Aktar alt menüsü
        export_menu = QMenu("📤 Dışa Aktar", self)
        
        export_csv = QAction("CSV olarak...", self)
        export_csv.triggered.connect(lambda: self.export_books("csv"))
        export_menu.addAction(export_csv)
        
        export_json = QAction("JSON olarak...", self)
        export_json.triggered.connect(lambda: self.export_books("json"))
        export_menu.addAction(export_json)
        
        export_xlsx = QAction("Excel olarak...", self)
        export_xlsx.triggered.connect(lambda: self.export_books("xlsx"))
        export_menu.addAction(export_xlsx)
        
        file_menu.addMenu(export_menu)
        
        file_menu.addSeparator()
        
        # Toplu kapak indirme
        fetch_covers_action = QAction("🖼️ Eksik Kapakları İndir...", self)
        fetch_covers_action.triggered.connect(self.fetch_missing_covers)
        file_menu.addAction(fetch_covers_action)
        
        file_menu.addSeparator()
        
        # Çıkış
        exit_action = QAction("Çıkış", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # === Görünüm Menüsü ===
        view_menu = menubar.addMenu("Görünüm")
        
        # İstatistikler
        stats_action = QAction("📊 İstatistikler", self)
        stats_action.setShortcut("Ctrl+I")
        stats_action.triggered.connect(self.show_stats)
        view_menu.addAction(stats_action)
        
        view_menu.addSeparator()
        
        # Kenar çubuğu
        self.sidebar_action = QAction("◀ Kenar Çubuğu", self)
        self.sidebar_action.setShortcut("Ctrl+B")
        self.sidebar_action.setCheckable(True)
        self.sidebar_action.setChecked(True)
        self.sidebar_action.triggered.connect(self.toggle_sidebar)
        view_menu.addAction(self.sidebar_action)
        
        # Sütunları göster/gizle alt menüsü
        columns_menu = QMenu("📋 Sütunlar", self)
        view_menu.addMenu(columns_menu)
        
        self.column_actions = {}
        column_names = ["Kapak", "Başlık", "Yazar", "Sayfa", "Durum", "Puan"]
        for i, name in enumerate(column_names):
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(True)
            if i == 1:  # Başlık her zaman görünür
                action.setEnabled(False)
            action.triggered.connect(lambda checked, col=i: self.toggle_column(col, checked))
            columns_menu.addAction(action)
            self.column_actions[i] = action
        
        columns_menu.addSeparator()
        show_all_action = QAction("Tümünü Göster", self)
        show_all_action.triggered.connect(self.show_all_columns_and_update_menu)
        columns_menu.addAction(show_all_action)
        
        view_menu.addSeparator()
        
        # Tema alt menüsü
        theme_menu = QMenu("🎨 Tema", self)
        view_menu.addMenu(theme_menu)
        
        # Açık tema
        light_action = QAction(THEME_NAMES["light"], self)
        light_action.triggered.connect(lambda: self.apply_theme("light"))
        theme_menu.addAction(light_action)
        
        # Koyu tema
        dark_action = QAction(THEME_NAMES["dark"], self)
        dark_action.triggered.connect(lambda: self.apply_theme("dark"))
        theme_menu.addAction(dark_action)
    
    def show_stats(self):
        """İstatistik penceresini açar."""
        dialog = StatsDialog(self)
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
        
        # Hücre seçimi (inline edit için)
        self.books_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.books_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
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
                "reading": "📖 Okunuyor",
                "read": "📗 Okundu"
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
            
            # Tıklama olayı
            card.mousePressEvent = lambda event, bid=book["id"]: self.on_grid_card_clicked(event, bid)
            
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
    
    def on_grid_card_clicked(self, event, book_id):
        """Grid'de bir kitap kartına tıklandığında."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Sol tık - düzenleme formu aç
            self.open_edit_dialog(book_id)
        elif event.button() == Qt.MouseButton.RightButton:
            # Sağ tık - menü göster
            self.show_grid_context_menu(event.globalPosition().toPoint(), book_id)
    
    def show_grid_context_menu(self, position, book_id):
        """Grid görünümünde sağ tık menüsü."""
        book = db.get_book_by_id(book_id)
        if not book:
            return
        
        menu = QMenu(self)
        
        # Düzenle
        edit_action = menu.addAction("✏️ Düzenle")
        edit_action.triggered.connect(lambda: self.open_edit_dialog(book_id))
        
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
        from services.book_api import search_books, download_cover
        
        # Kapağı olmayan kitapları bul (None veya boş string)
        books = db.get_all_books()
        books_without_cover = [b for b in books if not b["cover_path"] or b["cover_path"].strip() == ""]
        
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