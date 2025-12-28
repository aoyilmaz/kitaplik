"""
Kitaplık Uygulaması - Raf Paneli
================================
Sol tarafta gösterilen raf listesi ve yönetimi.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QInputDialog,
    QMessageBox,
    QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
import database as db


class ShelfPanel(QWidget):
    """
    Raf paneli widget'ı.
    
    Signals:
        shelf_selected(int): Bir raf seçildiğinde (shelf_id)
        all_books_selected(): "Tüm Kitaplar" seçildiğinde
    """
    
    # Sinyaller - bu sınıftan dışarıya bilgi göndermek için
    shelf_selected = pyqtSignal(int)    # Parametre: shelf_id
    all_books_selected = pyqtSignal()   # Parametresiz
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_shelves()
    
    def setup_ui(self):
        """Arayüzü oluşturur."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 10, 0)
        
        # === BAŞLIK ===
        title = QLabel("📚 Raflar")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # === RAF LİSTESİ ===
        self.shelf_list = QListWidget()
        self.shelf_list.setMinimumWidth(180)
        
        # Tıklama olayı
        self.shelf_list.itemClicked.connect(self.on_shelf_clicked)
        
        # Sağ tık menüsü
        self.shelf_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.shelf_list.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.shelf_list)
        
        # === YENİ RAF BUTONU ===
        add_btn = QPushButton("➕ Yeni Raf")
        add_btn.clicked.connect(self.on_add_shelf)
        layout.addWidget(add_btn)
    
    def load_shelves(self):
        """Rafları yükler."""
        self.shelf_list.clear()
        
        # "Tüm Kitaplar" öğesi (özel, id = -1)
        all_item = QListWidgetItem("📖 Tüm Kitaplar")
        all_item.setData(Qt.ItemDataRole.UserRole, -1)
        self.shelf_list.addItem(all_item)
        
        # Ayırıcı çizgi efekti için boş öğe
        separator = QListWidgetItem("─" * 15)
        separator.setFlags(Qt.ItemFlag.NoItemFlags)  # Seçilemez
        self.shelf_list.addItem(separator)
        
        # Rafları ekle
        shelves = db.get_all_shelves()
        for shelf in shelves:
            count = db.get_shelf_book_count(shelf["id"])
            text = f"{shelf['icon']} {shelf['name']} ({count})"
            
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, shelf["id"])
            self.shelf_list.addItem(item)
        
        # İlk öğeyi seç (Tüm Kitaplar)
        self.shelf_list.setCurrentRow(0)
    
    def on_shelf_clicked(self, item):
        """Bir raf tıklandığında."""
        shelf_id = item.data(Qt.ItemDataRole.UserRole)
        
        if shelf_id is None:
            # Ayırıcıya tıklandı, yoksay
            return
        
        if shelf_id == -1:
            # "Tüm Kitaplar"
            self.all_books_selected.emit()
        else:
            self.shelf_selected.emit(shelf_id)
    
    def on_add_shelf(self):
        """Yeni raf ekler."""
        # İsim sor
        name, ok = QInputDialog.getText(
            self,
            "Yeni Raf",
            "Raf adı:"
        )
        
        if not ok or not name.strip():
            return
        
        # Emoji seç (basit liste)
        emojis = ["📚", "⭐", "❤️", "📖", "📋", "✅", "🎯", "💡", "🔥", "🌟"]
        icon, ok = QInputDialog.getItem(
            self,
            "İkon Seç",
            "Raf ikonu:",
            emojis,
            0,
            False
        )
        
        if not ok:
            icon = "📚"
        
        # Ekle
        shelf_id = db.add_shelf(name.strip(), icon)
        
        if shelf_id:
            self.load_shelves()
        else:
            QMessageBox.warning(
                self,
                "Hata",
                f'"{name}" adında bir raf zaten var!'
            )
    
    def show_context_menu(self, position):
        """Sağ tık menüsünü gösterir."""
        item = self.shelf_list.itemAt(position)
        if not item:
            return
        
        shelf_id = item.data(Qt.ItemDataRole.UserRole)
        
        # "Tüm Kitaplar" ve ayırıcı için menü gösterme
        if shelf_id is None or shelf_id == -1:
            return
        
        menu = QMenu(self)
        
        # Yeniden adlandır
        rename_action = menu.addAction("✏️ Yeniden Adlandır")
        rename_action.triggered.connect(lambda: self.rename_shelf(shelf_id))
        
        # Sil
        delete_action = menu.addAction("🗑️ Sil")
        delete_action.triggered.connect(lambda: self.delete_shelf(shelf_id))
        
        menu.exec(self.shelf_list.mapToGlobal(position))
    
    def rename_shelf(self, shelf_id):
        """Rafı yeniden adlandırır."""
        name, ok = QInputDialog.getText(
            self,
            "Yeniden Adlandır",
            "Yeni ad:"
        )
        
        if ok and name.strip():
            db.update_shelf(shelf_id, name=name.strip())
            self.load_shelves()
    
    def delete_shelf(self, shelf_id):
        """Rafı siler."""
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu rafı silmek istediğinize emin misiniz?\n\n"
            "(Kitaplar silinmez, sadece raftan çıkarılır)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_shelf(shelf_id)
            self.load_shelves()
            # Tüm kitaplara dön
            self.all_books_selected.emit()
    
    def refresh(self):
        """Listeyi yeniler (dışarıdan çağrılabilir)."""
        current_row = self.shelf_list.currentRow()
        self.load_shelves()
        # Seçimi koru
        if current_row < self.shelf_list.count():
            self.shelf_list.setCurrentRow(current_row)
