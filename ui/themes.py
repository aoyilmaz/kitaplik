"""
Kitaplık Uygulaması - Tema Stilleri
===================================
VS Code benzeri modern tema.
"""

# Renk paleti - VS Code tarzı
COLORS = {
    "light": {
        "bg": "#FFFFFF",
        "bg_secondary": "#F3F3F3",
        "bg_tertiary": "#E8E8E8",
        "text": "#1E1E1E",
        "text_secondary": "#6E6E6E",
        "border": "#D4D4D4",
        "accent": "#0078D4",
        "accent_hover": "#106EBE",
        "accent_light": "#E5F1FB",
        "success": "#16825D",
        "warning": "#DDB100",
        "danger": "#D32F2F",
        "selection": "#ADD6FF",
    },
    "dark": {
        "bg": "#1E1E1E",
        "bg_secondary": "#252526",
        "bg_tertiary": "#2D2D2D",
        "text": "#CCCCCC",
        "text_secondary": "#858585",
        "border": "#3C3C3C",
        "accent": "#0078D4",
        "accent_hover": "#1C97EA",
        "accent_light": "#094771",
        "success": "#4EC9B0",
        "warning": "#CCA700",
        "danger": "#F14C4C",
        "selection": "#264F78",
    }
}


def get_stylesheet(theme: str = "dark") -> str:
    """
    VS Code benzeri tema stylesheet'i döndürür.
    """
    c = COLORS.get(theme, COLORS["dark"])
    
    return f"""
    /* ===== GENEL ===== */
    * {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        font-size: 13px;
    }}
    
    QMainWindow, QDialog {{
        background-color: {c["bg"]};
        color: {c["text"]};
    }}
    
    QWidget {{
        background-color: {c["bg"]};
        color: {c["text"]};
    }}
    
    /* ===== BAŞLIKLAR ===== */
    QLabel {{
        color: {c["text"]};
        background-color: transparent;
        padding: 2px;
    }}
    
    /* ===== BUTONLAR ===== */
    QPushButton {{
        background-color: {c["accent"]};
        color: white;
        border: none;
        padding: 6px 14px;
        border-radius: 2px;
        font-weight: 500;
        min-height: 24px;
    }}
    
    QPushButton:hover {{
        background-color: {c["accent_hover"]};
    }}
    
    QPushButton:pressed {{
        background-color: {c["accent"]};
        opacity: 0.8;
    }}
    
    QPushButton:disabled {{
        background-color: {c["bg_tertiary"]};
        color: {c["text_secondary"]};
    }}
    
    /* Secondary button */
    QPushButton[flat="true"], QPushButton#secondaryButton {{
        background-color: transparent;
        color: {c["text"]};
        border: 1px solid {c["border"]};
    }}
    
    QPushButton[flat="true"]:hover, QPushButton#secondaryButton:hover {{
        background-color: {c["bg_tertiary"]};
    }}
    
    /* ===== METİN GİRİŞLERİ ===== */
    QLineEdit, QTextEdit, QSpinBox {{
        background-color: {c["bg_tertiary"]};
        color: {c["text"]};
        border: 1px solid {c["border"]};
        padding: 6px 8px;
        border-radius: 2px;
        selection-background-color: {c["selection"]};
    }}
    
    QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {{
        border: 1px solid {c["accent"]};
        outline: none;
    }}
    
    QLineEdit::placeholder {{
        color: {c["text_secondary"]};
    }}
    
    /* ===== AÇILIR LİSTE ===== */
    QComboBox {{
        background-color: {c["bg_tertiary"]};
        color: {c["text"]};
        border: 1px solid {c["border"]};
        padding: 5px 10px;
        border-radius: 2px;
        min-height: 24px;
    }}
    
    QComboBox:hover {{
        border: 1px solid {c["accent"]};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {c["text_secondary"]};
        margin-right: 8px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {c["bg_secondary"]};
        color: {c["text"]};
        border: 1px solid {c["border"]};
        selection-background-color: {c["accent"]};
        selection-color: white;
        padding: 4px;
    }}
    
    /* ===== TABLO ===== */
    QTableWidget {{
        background-color: {c["bg"]};
        color: {c["text"]};
        border: 1px solid {c["border"]};
        gridline-color: {c["border"]};
        border-radius: 4px;
        outline: none;
    }}
    
    QTableWidget::item {{
        padding: 8px;
        border: none;
    }}
    
    QTableWidget::item:selected {{
        background-color: {c["selection"]};
        color: {c["text"]};
    }}
    
    QTableWidget::item:hover {{
        background-color: {c["bg_tertiary"]};
    }}
    
    QHeaderView::section {{
        background-color: {c["bg_secondary"]};
        color: {c["text_secondary"]};
        padding: 8px 12px;
        border: none;
        border-bottom: 1px solid {c["border"]};
        font-weight: 600;
        text-transform: uppercase;
        font-size: 11px;
    }}
    
    /* ===== LİSTE ===== */
    QListWidget {{
        background-color: {c["bg"]};
        color: {c["text"]};
        border: 1px solid {c["border"]};
        border-radius: 4px;
        outline: none;
        padding: 4px;
    }}
    
    QListWidget::item {{
        padding: 8px 12px;
        border-radius: 4px;
        margin: 2px 4px;
    }}
    
    QListWidget::item:selected {{
        background-color: {c["accent"]};
        color: white;
    }}
    
    QListWidget::item:hover:!selected {{
        background-color: {c["bg_tertiary"]};
    }}
    
    /* ===== GRUP KUTUSU ===== */
    QGroupBox {{
        color: {c["text"]};
        border: 1px solid {c["border"]};
        border-radius: 4px;
        margin-top: 16px;
        padding-top: 16px;
        font-weight: 600;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 8px;
        color: {c["text_secondary"]};
    }}
    
    /* ===== KAYDIRMA ÇUBUĞU ===== */
    QScrollBar:vertical {{
        background-color: {c["bg"]};
        width: 14px;
        margin: 0;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {c["bg_tertiary"]};
        border-radius: 7px;
        min-height: 30px;
        margin: 2px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {c["text_secondary"]};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    
    QScrollBar:horizontal {{
        background-color: {c["bg"]};
        height: 14px;
        margin: 0;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {c["bg_tertiary"]};
        border-radius: 7px;
        min-width: 30px;
        margin: 2px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {c["text_secondary"]};
    }}
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}
    
    /* ===== MESAJ KUTUSU ===== */
    QMessageBox {{
        background-color: {c["bg_secondary"]};
    }}
    
    QMessageBox QLabel {{
        color: {c["text"]};
    }}
    
    /* ===== SPLITTER ===== */
    QSplitter::handle {{
        background-color: {c["border"]};
    }}
    
    QSplitter::handle:horizontal {{
        width: 1px;
    }}
    
    QSplitter::handle:vertical {{
        height: 1px;
    }}
    
    /* ===== MENÜ ===== */
    QMenuBar {{
        background-color: {c["bg_secondary"]};
        color: {c["text"]};
        border-bottom: 1px solid {c["border"]};
        padding: 2px;
    }}
    
    QMenuBar::item {{
        padding: 6px 10px;
        border-radius: 4px;
    }}
    
    QMenuBar::item:selected {{
        background-color: {c["bg_tertiary"]};
    }}
    
    QMenu {{
        background-color: {c["bg_secondary"]};
        color: {c["text"]};
        border: 1px solid {c["border"]};
        padding: 4px;
    }}
    
    QMenu::item {{
        padding: 6px 24px;
        border-radius: 4px;
    }}
    
    QMenu::item:selected {{
        background-color: {c["accent"]};
        color: white;
    }}
    
    QMenu::separator {{
        height: 1px;
        background-color: {c["border"]};
        margin: 4px 8px;
    }}
    
    /* ===== PROGRESS BAR ===== */
    QProgressBar {{
        background-color: {c["bg_tertiary"]};
        border: none;
        border-radius: 4px;
        text-align: center;
        color: {c["text"]};
    }}
    
    QProgressBar::chunk {{
        background-color: {c["accent"]};
        border-radius: 4px;
    }}
    
    /* ===== FRAME ===== */
    QFrame[frameShape="4"] {{
        color: {c["border"]};
    }}
    
    QFrame#card {{
        background-color: {c["bg_secondary"]};
        border: 1px solid {c["border"]};
        border-radius: 6px;
    }}
    
    /* ===== TOOLTIP ===== */
    QToolTip {{
        background-color: {c["bg_secondary"]};
        color: {c["text"]};
        border: 1px solid {c["border"]};
        padding: 6px;
        border-radius: 4px;
    }}
    """


# Tema isimleri (UI'da gösterilecek)
THEME_NAMES = {
    "light": "☀️ Açık Tema",
    "dark": "🌙 Koyu Tema",
}