"""
Kitaplık Uygulaması - Ana Giriş Noktası
=======================================
Uygulama buradan başlar.
"""

import sys
from PyQt6.QtWidgets import QApplication

# Kendi modüllerimiz
import database as db
from ui.main_window import MainWindow


def main():
    """
    Uygulamayı başlatır.
    """
    # Veritabanını hazırla (yoksa oluşturur)
    db.init_database()
    
    # Qt uygulaması oluştur
    # sys.argv: Komut satırı argümanları (Qt bunları kullanabilir)
    app = QApplication(sys.argv)
    
    # Ana pencereyi oluştur ve göster
    window = MainWindow()
    window.show()
    
    # Uygulama döngüsünü başlat
    # Bu satır uygulamayı "canlı" tutar
    # Kullanıcı pencereyi kapatana kadar çalışır
    sys.exit(app.exec())


# Bu dosya doğrudan çalıştırılırsa main() çağır
# Başka bir dosyadan import edilirse çağırma
if __name__ == "__main__":
    main()
