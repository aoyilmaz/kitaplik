"""
Kitaplık Uygulaması - Filtre Çubuğu
===================================
Durum, puan ve yıla göre filtreleme.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
)
from PyQt6.QtCore import pyqtSignal

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
import database as db


class FilterBar(QWidget):
    """
    Filtre çubuğu widget'ı.
    
    Signals:
        filters_changed(dict): Filtreler değiştiğinde
            {"status": str|None, "rating": int|None, "year": int|None}
    """
    
    filters_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Arayüzü oluşturur."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(8)
        
        # Filtre etiketi
        filter_label = QLabel("🔍")
        layout.addWidget(filter_label)
        
        # === DURUM FİLTRESİ ===
        self.status_combo = QComboBox()
        self.status_combo.addItem("Durum: Tümü", None)
        self.status_combo.addItem("📕 Okunmadı", "unread")
        self.status_combo.addItem("📖 Okunuyor", "reading")
        self.status_combo.addItem("📗 Okundu", "read")
        self.status_combo.setFixedWidth(130)
        self.status_combo.currentIndexChanged.connect(self.on_filter_changed)
        layout.addWidget(self.status_combo)
        
        # === PUAN FİLTRESİ ===
        self.rating_combo = QComboBox()
        self.rating_combo.addItem("Puan: Tümü", None)
        self.rating_combo.addItem("⭐ 1+", 1)
        self.rating_combo.addItem("⭐⭐ 2+", 2)
        self.rating_combo.addItem("⭐⭐⭐ 3+", 3)
        self.rating_combo.addItem("⭐⭐⭐⭐ 4+", 4)
        self.rating_combo.addItem("⭐⭐⭐⭐⭐ 5", 5)
        self.rating_combo.setFixedWidth(120)
        self.rating_combo.currentIndexChanged.connect(self.on_filter_changed)
        layout.addWidget(self.rating_combo)
        
        # === YIL FİLTRESİ ===
        self.year_combo = QComboBox()
        self.year_combo.addItem("Yıl: Tümü", None)
        self.year_combo.setFixedWidth(100)
        self.year_combo.currentIndexChanged.connect(self.on_filter_changed)
        layout.addWidget(self.year_combo)
        
        # === TEMİZLE BUTONU ===
        clear_btn = QPushButton("✕")
        clear_btn.setToolTip("Filtreleri Temizle")
        clear_btn.setFixedWidth(30)
        clear_btn.clicked.connect(self.clear_filters)
        layout.addWidget(clear_btn)
        
        # Yılları yükle
        self.refresh_years()
    
    def refresh_years(self):
        """Yıl listesini günceller."""
        current_year = self.year_combo.currentData()
        
        self.year_combo.blockSignals(True)  # Değişiklik sinyali gönderme
        self.year_combo.clear()
        self.year_combo.addItem("Yıl: Tümü", None)
        
        years = db.get_distinct_years()
        for year in years:
            self.year_combo.addItem(str(year), year)
        
        # Önceki seçimi koru
        if current_year:
            index = self.year_combo.findData(current_year)
            if index >= 0:
                self.year_combo.setCurrentIndex(index)
        
        self.year_combo.blockSignals(False)
    
    def on_filter_changed(self):
        """Filtre değiştiğinde sinyal gönderir."""
        filters = self.get_filters()
        self.filters_changed.emit(filters)
    
    def get_filters(self) -> dict:
        """Mevcut filtre değerlerini döndürür."""
        return {
            "status": self.status_combo.currentData(),
            "rating": self.rating_combo.currentData(),
            "year": self.year_combo.currentData(),
        }
    
    def clear_filters(self):
        """Tüm filtreleri temizler."""
        self.status_combo.setCurrentIndex(0)
        self.rating_combo.setCurrentIndex(0)
        self.year_combo.setCurrentIndex(0)
        # on_filter_changed otomatik tetiklenecek
    
    def has_active_filters(self) -> bool:
        """Aktif filtre var mı?"""
        filters = self.get_filters()
        return any(v is not None for v in filters.values())