"""
Kitaplık Uygulaması - Gelişmiş İstatistik Dialog
================================================
- Okuma grafikleri (aylık/yıllık trend)
- Yazar istatistikleri
- Kategori dağılımı (pasta grafik)
- Okuma hızı
- Hedef takibi
- Yıllık özet raporu
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QPushButton,
    QProgressBar,
    QTabWidget,
    QWidget,
    QSpinBox,
    QComboBox,
    QScrollArea,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush

import sys
from pathlib import Path
from datetime import datetime
sys.path.append(str(Path(__file__).parent.parent))
import database as db


# ============================================================
# YARDIMCI WIDGET'LAR
# ============================================================

class StatCard(QFrame):
    """Tek bir istatistik kartı."""
    
    def __init__(self, icon: str, value: str, label: str, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumWidth(120)
        self.setMaximumWidth(160)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(3)
        layout.setContentsMargins(10, 10, 10, 10)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)
        
        label_label = QLabel(label)
        label_label.setStyleSheet("color: #858585; font-size: 11px;")
        label_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label_label)


class BarChart(QWidget):
    """Basit çubuk grafik widget'ı."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []  # [(label, value), ...]
        self.max_value = 0
        self.bar_color = QColor("#0078D4")
        self.setMinimumHeight(200)
    
    def set_data(self, data: list):
        """Veriyi ayarla: [(label, value), ...]"""
        self.data = data
        self.max_value = max((v for _, v in data), default=1)
        self.update()
    
    def paintEvent(self, event):
        if not self.data:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height() - 30  # Alt etiket için boşluk
        bar_width = max(20, min(50, (width - 40) // len(self.data) - 10))
        spacing = (width - len(self.data) * bar_width) // (len(self.data) + 1)
        
        x = spacing
        for label, value in self.data:
            # Çubuk yüksekliği
            bar_height = int((value / self.max_value) * (height - 20)) if self.max_value > 0 else 0
            y = height - bar_height
            
            # Çubuk çiz
            painter.setBrush(QBrush(self.bar_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x, y, bar_width, bar_height, 3, 3)
            
            # Değer
            if value > 0:
                painter.setPen(QPen(QColor("#FFFFFF")))
                painter.drawText(x, y - 5, bar_width, 20, Qt.AlignmentFlag.AlignCenter, str(value))
            
            # Etiket
            painter.setPen(QPen(QColor("#858585")))
            painter.drawText(x - 5, height + 5, bar_width + 10, 20, Qt.AlignmentFlag.AlignCenter, str(label))
            
            x += bar_width + spacing


class PieChart(QWidget):
    """Basit pasta grafik widget'ı."""
    
    COLORS = [
        "#0078D4", "#00B294", "#FFB900", "#E81123", "#8764B8",
        "#00BCF2", "#107C10", "#FF8C00", "#5C2D91", "#038387"
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []  # [(label, value), ...]
        self.setMinimumSize(200, 200)
    
    def set_data(self, data: list):
        """Veriyi ayarla: [(label, value), ...]"""
        self.data = data[:10]  # En fazla 10
        self.update()
    
    def paintEvent(self, event):
        if not self.data:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Pasta boyutu
        size = min(self.width(), self.height()) - 20
        x = (self.width() - size) // 2
        y = 10
        rect = QRectF(x, y, size, size)
        
        total = sum(v for _, v in self.data)
        if total == 0:
            return
        
        start_angle = 90 * 16  # 12 o'clock pozisyonundan başla
        
        for i, (label, value) in enumerate(self.data):
            span_angle = int((value / total) * 360 * 16)
            
            color = QColor(self.COLORS[i % len(self.COLORS)])
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("#1E1E1E"), 2))
            
            painter.drawPie(rect, start_angle, span_angle)
            start_angle += span_angle


class HorizontalBarItem(QFrame):
    """Yatay çubuk öğesi (yazar/kategori listesi için)."""
    
    def __init__(self, label: str, value: int, max_value: int, extra: str = "", parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 3, 5, 3)
        layout.setSpacing(10)
        
        # Etiket
        label_lbl = QLabel(label)
        label_lbl.setMinimumWidth(150)
        label_lbl.setMaximumWidth(200)
        layout.addWidget(label_lbl)
        
        # Çubuk
        bar = QProgressBar()
        bar.setMinimum(0)
        bar.setMaximum(max_value)
        bar.setValue(value)
        bar.setTextVisible(False)
        bar.setMaximumHeight(16)
        bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #2D2D2D;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #0078D4;
                border-radius: 3px;
            }
        """)
        layout.addWidget(bar, stretch=1)
        
        # Değer
        value_lbl = QLabel(f"{value}")
        value_lbl.setStyleSheet("font-weight: bold; min-width: 30px;")
        value_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(value_lbl)
        
        # Ekstra (ör: puan)
        if extra:
            extra_lbl = QLabel(extra)
            extra_lbl.setStyleSheet("color: #858585;")
            layout.addWidget(extra_lbl)


# ============================================================
# ANA İSTATİSTİK DIALOG
# ============================================================

class StatsDialog(QDialog):
    """Gelişmiş istatistik penceresi."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Kütüphane İstatistikleri")
        self.setMinimumSize(750, 600)
        self.current_year = datetime.now().year
        self.setup_ui()
        self.load_all_stats()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # === TAB 1: GENEL BAKIŞ ===
        self.tabs.addTab(self.create_overview_tab(), "📊 Genel Bakış")
        
        # === TAB 2: OKUMA GRAFİKLERİ ===
        self.tabs.addTab(self.create_charts_tab(), "📈 Grafikler")
        
        # === TAB 3: YAZARLAR ===
        self.tabs.addTab(self.create_authors_tab(), "✍️ Yazarlar")
        
        # === TAB 4: KATEGORİLER ===
        self.tabs.addTab(self.create_categories_tab(), "📁 Kategoriler")
        
        # === TAB 5: OKUMA HIZI ===
        self.tabs.addTab(self.create_speed_tab(), "⚡ Okuma Hızı")
        
        # === TAB 6: HEDEF ===
        self.tabs.addTab(self.create_goal_tab(), "🎯 Hedef")
        
        # === TAB 7: YILLIK ÖZET ===
        self.tabs.addTab(self.create_summary_tab(), "📅 Yıllık Özet")
        
        layout.addWidget(self.tabs)
        
        # Kapat butonu
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def create_overview_tab(self) -> QWidget:
        """Genel bakış tab'ı."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Kartlar
        cards_layout = QGridLayout()
        cards_layout.setSpacing(10)
        
        self.total_card = StatCard("📚", "0", "Toplam")
        cards_layout.addWidget(self.total_card, 0, 0)
        
        self.read_card = StatCard("✅", "0", "Okunan")
        cards_layout.addWidget(self.read_card, 0, 1)
        
        self.reading_card = StatCard("📖", "0", "Okunuyor")
        cards_layout.addWidget(self.reading_card, 0, 2)
        
        self.unread_card = StatCard("📕", "0", "Okunmadı")
        cards_layout.addWidget(self.unread_card, 0, 3)
        
        self.pages_card = StatCard("📄", "0", "Sayfa")
        cards_layout.addWidget(self.pages_card, 1, 0)
        
        self.rating_card = StatCard("⭐", "-", "Ort. Puan")
        cards_layout.addWidget(self.rating_card, 1, 1)
        
        self.authors_card = StatCard("✍️", "0", "Yazar")
        cards_layout.addWidget(self.authors_card, 1, 2)
        
        self.shelves_card = StatCard("🗂️", "0", "Raf")
        cards_layout.addWidget(self.shelves_card, 1, 3)
        
        layout.addLayout(cards_layout)
        
        # İlerleme çubuğu
        progress_frame = QFrame()
        progress_frame.setFrameShape(QFrame.Shape.StyledPanel)
        progress_layout = QVBoxLayout(progress_frame)
        
        progress_label = QLabel("📈 Okuma İlerlemesi")
        progress_label.setStyleSheet("font-weight: bold;")
        progress_layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimumHeight(25)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_detail = QLabel("")
        self.progress_detail.setStyleSheet("color: #858585;")
        progress_layout.addWidget(self.progress_detail)
        
        layout.addWidget(progress_frame)
        layout.addStretch()
        
        return widget
    
    def create_charts_tab(self) -> QWidget:
        """Grafik tab'ı."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Yıl seçici
        year_row = QHBoxLayout()
        year_row.addWidget(QLabel("Yıl:"))
        self.chart_year_combo = QComboBox()
        current_year = datetime.now().year
        for y in range(current_year, current_year - 5, -1):
            self.chart_year_combo.addItem(str(y), y)
        self.chart_year_combo.currentIndexChanged.connect(self.load_charts)
        year_row.addWidget(self.chart_year_combo)
        year_row.addStretch()
        layout.addLayout(year_row)
        
        # Aylık grafik
        layout.addWidget(QLabel("📅 Aylık Okuma Trendi"))
        self.monthly_chart = BarChart()
        layout.addWidget(self.monthly_chart)
        
        # Yıllık grafik
        layout.addWidget(QLabel("📊 Yıllık Karşılaştırma"))
        self.yearly_chart = BarChart()
        self.yearly_chart.bar_color = QColor("#00B294")
        layout.addWidget(self.yearly_chart)
        
        return widget
    
    def create_authors_tab(self) -> QWidget:
        """Yazar istatistikleri tab'ı."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("✍️ En Çok Okunan Yazarlar"))
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.authors_container = QWidget()
        self.authors_layout = QVBoxLayout(self.authors_container)
        self.authors_layout.setSpacing(5)
        self.authors_layout.addStretch()
        
        scroll.setWidget(self.authors_container)
        layout.addWidget(scroll)
        
        return widget
    
    def create_categories_tab(self) -> QWidget:
        """Kategori dağılımı tab'ı."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Sol: Pasta grafik
        left = QVBoxLayout()
        left.addWidget(QLabel("📁 Kategori Dağılımı"))
        self.category_chart = PieChart()
        self.category_chart.setMinimumSize(250, 250)
        left.addWidget(self.category_chart)
        left.addStretch()
        layout.addLayout(left)
        
        # Sağ: Liste
        right = QVBoxLayout()
        right.addWidget(QLabel("Kategoriler"))
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.categories_container = QWidget()
        self.categories_layout = QVBoxLayout(self.categories_container)
        self.categories_layout.setSpacing(3)
        self.categories_layout.addStretch()
        
        scroll.setWidget(self.categories_container)
        right.addWidget(scroll)
        layout.addLayout(right)
        
        return widget
    
    def create_speed_tab(self) -> QWidget:
        """Okuma hızı tab'ı."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("⚡ Okuma Hızı İstatistikleri"))
        
        # Kartlar
        cards = QHBoxLayout()
        
        self.speed_avg_days = StatCard("📅", "-", "Ort. Gün/Kitap")
        cards.addWidget(self.speed_avg_days)
        
        self.speed_avg_pages = StatCard("📄", "-", "Ort. Sayfa/Gün")
        cards.addWidget(self.speed_avg_pages)
        
        self.speed_total_days = StatCard("⏱️", "-", "Toplam Gün")
        cards.addWidget(self.speed_total_days)
        
        cards.addStretch()
        layout.addLayout(cards)
        
        # En hızlı / en yavaş
        self.fastest_label = QLabel("")
        self.fastest_label.setStyleSheet("padding: 10px; background-color: #1E3A1E; border-radius: 5px;")
        layout.addWidget(self.fastest_label)
        
        self.slowest_label = QLabel("")
        self.slowest_label.setStyleSheet("padding: 10px; background-color: #3A1E1E; border-radius: 5px;")
        layout.addWidget(self.slowest_label)
        
        layout.addStretch()
        return widget
    
    def create_goal_tab(self) -> QWidget:
        """Hedef takibi tab'ı."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("🎯 Yıllık Okuma Hedefi"))
        
        # Hedef ayarlama
        goal_row = QHBoxLayout()
        goal_row.addWidget(QLabel(f"{self.current_year} Hedefi:"))
        
        self.goal_spinbox = QSpinBox()
        self.goal_spinbox.setRange(0, 500)
        self.goal_spinbox.setSuffix(" kitap")
        goal_row.addWidget(self.goal_spinbox)
        
        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self.save_goal)
        goal_row.addWidget(save_btn)
        
        goal_row.addStretch()
        layout.addLayout(goal_row)
        
        # İlerleme
        self.goal_progress = QProgressBar()
        self.goal_progress.setMinimum(0)
        self.goal_progress.setMaximum(100)
        self.goal_progress.setMinimumHeight(40)
        self.goal_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3C3C3C;
                border-radius: 10px;
                text-align: center;
                font-size: 14px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #0078D4;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.goal_progress)
        
        self.goal_status = QLabel("")
        self.goal_status.setStyleSheet("font-size: 14px; padding: 10px;")
        self.goal_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.goal_status)
        
        self.goal_detail = QLabel("")
        self.goal_detail.setStyleSheet("color: #858585;")
        self.goal_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.goal_detail)
        
        layout.addStretch()
        return widget
    
    def create_summary_tab(self) -> QWidget:
        """Yıllık özet tab'ı."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Yıl seçici
        year_row = QHBoxLayout()
        year_row.addWidget(QLabel("📅 Yıl:"))
        self.summary_year_combo = QComboBox()
        current_year = datetime.now().year
        for y in range(current_year, current_year - 10, -1):
            self.summary_year_combo.addItem(str(y), y)
        self.summary_year_combo.currentIndexChanged.connect(self.load_summary)
        year_row.addWidget(self.summary_year_combo)
        year_row.addStretch()
        layout.addLayout(year_row)
        
        # Özet içerik
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.summary_container = QWidget()
        self.summary_layout = QVBoxLayout(self.summary_container)
        
        scroll.setWidget(self.summary_container)
        layout.addWidget(scroll)
        
        return widget
    
    # ============================================================
    # VERİ YÜKLEME
    # ============================================================
    
    def load_all_stats(self):
        """Tüm istatistikleri yükler."""
        self.load_overview()
        self.load_charts()
        self.load_authors()
        self.load_categories()
        self.load_speed()
        self.load_goal()
        self.load_summary()
    
    def load_overview(self):
        """Genel bakış verilerini yükler."""
        stats = db.get_statistics()
        
        self.total_card.value_label.setText(str(stats["total_books"]))
        self.read_card.value_label.setText(str(stats["read_books"]))
        self.reading_card.value_label.setText(str(stats["reading_books"]))
        self.unread_card.value_label.setText(str(stats["unread_books"]))
        
        pages = stats["total_pages"]
        self.pages_card.value_label.setText(f"{pages:,}".replace(",", "."))
        
        if stats["average_rating"] > 0:
            self.rating_card.value_label.setText(f"{stats['average_rating']}")
        
        # Yazar sayısı
        authors = db.get_author_stats(100)
        self.authors_card.value_label.setText(str(len(authors)))
        
        self.shelves_card.value_label.setText(str(stats["total_shelves"]))
        
        # İlerleme
        total = stats["total_books"]
        read = stats["read_books"]
        if total > 0:
            percentage = int((read / total) * 100)
            self.progress_bar.setValue(percentage)
            self.progress_bar.setFormat(f"%p% ({read}/{total} kitap okundu)")
            self.progress_detail.setText(f"Toplam {stats['read_pages']:,} sayfa okundu".replace(",", "."))
        else:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Henüz kitap yok")
    
    def load_charts(self):
        """Grafikleri yükler."""
        year = self.chart_year_combo.currentData()
        
        # Aylık
        monthly = db.get_monthly_reading_stats(year)
        month_names = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", 
                       "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
        
        monthly_data = {m["month"]: m["count"] for m in monthly}
        chart_data = [(month_names[i], monthly_data.get(i+1, 0)) for i in range(12)]
        self.monthly_chart.set_data(chart_data)
        
        # Yıllık
        yearly = db.get_yearly_reading_stats()
        yearly_data = [(str(y["year"]), y["count"]) for y in yearly[:5]]
        yearly_data.reverse()
        self.yearly_chart.set_data(yearly_data)
    
    def load_authors(self):
        """Yazar istatistiklerini yükler."""
        # Mevcut öğeleri temizle
        while self.authors_layout.count() > 1:
            item = self.authors_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        authors = db.get_author_stats(15)
        if not authors:
            self.authors_layout.insertWidget(0, QLabel("Henüz yazar verisi yok"))
            return
        
        max_count = authors[0]["count"] if authors else 1
        
        for author in authors:
            rating_str = f"⭐ {author['avg_rating']}" if author['avg_rating'] else ""
            item = HorizontalBarItem(
                author["author"] or "Bilinmiyor",
                author["count"],
                max_count,
                rating_str
            )
            self.authors_layout.insertWidget(self.authors_layout.count() - 1, item)
    
    def load_categories(self):
        """Kategori verilerini yükler."""
        # Mevcut öğeleri temizle
        while self.categories_layout.count() > 1:
            item = self.categories_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        categories = db.get_category_stats()
        if not categories:
            self.categories_layout.insertWidget(0, QLabel("Henüz kategori verisi yok"))
            return
        
        # Pasta grafik
        chart_data = [(c["category"], c["count"]) for c in categories[:10]]
        self.category_chart.set_data(chart_data)
        
        # Liste
        max_count = categories[0]["count"] if categories else 1
        colors = PieChart.COLORS
        
        for i, cat in enumerate(categories):
            row = QHBoxLayout()
            
            # Renk kutusu
            color_box = QLabel("■")
            color_box.setStyleSheet(f"color: {colors[i % len(colors)]}; font-size: 16px;")
            row.addWidget(color_box)
            
            # İsim
            name = QLabel(cat["category"])
            row.addWidget(name, stretch=1)
            
            # Sayı
            count = QLabel(str(cat["count"]))
            count.setStyleSheet("font-weight: bold;")
            row.addWidget(count)
            
            container = QWidget()
            container.setLayout(row)
            self.categories_layout.insertWidget(self.categories_layout.count() - 1, container)
    
    def load_speed(self):
        """Okuma hızı verilerini yükler."""
        speed = db.get_reading_speed_stats()
        
        self.speed_avg_days.value_label.setText(
            f"{speed['avg_days_per_book']}" if speed['avg_days_per_book'] else "-"
        )
        self.speed_avg_pages.value_label.setText(
            f"{speed['avg_pages_per_day']}" if speed['avg_pages_per_day'] else "-"
        )
        self.speed_total_days.value_label.setText(
            str(speed['total_reading_days']) if speed['total_reading_days'] else "-"
        )
        
        if speed['fastest_book']:
            fb = speed['fastest_book']
            self.fastest_label.setText(
                f"🏆 En Hızlı: {fb['title']} - {fb['author'] or 'Bilinmiyor'}\n"
                f"   {fb['days']} günde {fb['pages'] or '?'} sayfa"
            )
        else:
            self.fastest_label.setText("En hızlı kitap verisi yok")
        
        if speed['slowest_book']:
            sb = speed['slowest_book']
            self.slowest_label.setText(
                f"🐢 En Yavaş: {sb['title']} - {sb['author'] or 'Bilinmiyor'}\n"
                f"   {sb['days']} günde {sb['pages'] or '?'} sayfa"
            )
        else:
            self.slowest_label.setText("En yavaş kitap verisi yok")
    
    def load_goal(self):
        """Hedef verilerini yükler."""
        goal_data = db.get_reading_goal(self.current_year)
        
        self.goal_spinbox.setValue(goal_data["goal"])
        self.goal_progress.setValue(goal_data["percentage"])
        
        if goal_data["goal"] > 0:
            self.goal_progress.setFormat(
                f"{goal_data['read']} / {goal_data['goal']} kitap ({goal_data['percentage']}%)"
            )
            
            if goal_data["on_track"]:
                self.goal_status.setText("✅ Hedefte gidiyorsun!")
                self.goal_status.setStyleSheet("color: #00B294; font-size: 14px; padding: 10px;")
            else:
                self.goal_status.setText("⚠️ Biraz geride kaldın")
                self.goal_status.setStyleSheet("color: #FFB900; font-size: 14px; padding: 10px;")
            
            self.goal_detail.setText(f"{goal_data['remaining']} kitap daha okumalısın")
        else:
            self.goal_progress.setFormat("Hedef belirlenmedi")
            self.goal_status.setText("Yukarıdan hedef belirle")
            self.goal_status.setStyleSheet("color: #858585; font-size: 14px; padding: 10px;")
            self.goal_detail.setText("")
    
    def save_goal(self):
        """Hedefi kaydeder."""
        goal = self.goal_spinbox.value()
        db.set_reading_goal(self.current_year, goal)
        self.load_goal()
    
    def load_summary(self):
        """Yıllık özeti yükler."""
        # Mevcut içeriği temizle
        while self.summary_layout.count():
            item = self.summary_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        year = self.summary_year_combo.currentData()
        summary = db.get_year_summary(year)
        
        if summary["total_books"] == 0:
            self.summary_layout.addWidget(QLabel(f"{year} yılında okunan kitap yok"))
            return
        
        # Başlık
        title = QLabel(f"📚 {year} Yılı Okuma Özeti")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        self.summary_layout.addWidget(title)
        
        # Temel istatistikler
        stats_text = f"""
        📖 Toplam {summary['total_books']} kitap okundu
        📄 Toplam {summary['total_pages']:,} sayfa
        📊 Ortalama {summary['avg_pages_per_book']} sayfa/kitap
        ⭐ Ortalama puan: {summary['avg_rating'] or 'N/A'}
        """.replace(",", ".")
        
        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet("padding: 10px; background-color: #252526; border-radius: 5px;")
        self.summary_layout.addWidget(stats_label)
        
        # En çok okunan yazarlar
        if summary["top_authors"]:
            authors_title = QLabel("✍️ En Çok Okunan Yazarlar")
            authors_title.setStyleSheet("font-weight: bold; margin-top: 10px;")
            self.summary_layout.addWidget(authors_title)
            
            for a in summary["top_authors"]:
                lbl = QLabel(f"  • {a['author']}: {a['count']} kitap")
                self.summary_layout.addWidget(lbl)
        
        # En beğenilen kitaplar
        if summary["top_rated_books"]:
            rated_title = QLabel("⭐ En Yüksek Puanlı Kitaplar")
            rated_title.setStyleSheet("font-weight: bold; margin-top: 10px;")
            self.summary_layout.addWidget(rated_title)
            
            for b in summary["top_rated_books"]:
                stars = "⭐" * (b['rating'] or 0)
                lbl = QLabel(f"  • {b['title']} {stars}")
                self.summary_layout.addWidget(lbl)
        
        # Aylık dağılım
        monthly_title = QLabel("📅 Aylık Dağılım")
        monthly_title.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.summary_layout.addWidget(monthly_title)
        
        month_names = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", 
                       "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
        monthly_text = "  "
        for m in summary["monthly_breakdown"]:
            if m["count"] > 0:
                monthly_text += f"{month_names[m['month']-1]}:{m['count']}  "
        
        monthly_label = QLabel(monthly_text if monthly_text.strip() else "  Veri yok")
        self.summary_layout.addWidget(monthly_label)
        
        self.summary_layout.addStretch()