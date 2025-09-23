# config.py

# Renkler
BG_COLOR_DARK = "#f0f0f0"
BG_COLOR_MEDIUM = "#e0e0e0" # Butonlar ve liste öğeleri için
BG_COLOR_LIST = "#f8f8f8"
FG_COLOR = "#2c3e50"      
FIELD_BG = "#ffffff"

# Fontlar
FONT_DEFAULT = ("Arial", 10)
FONT_HEADING = ("Arial", 12, "bold")
FONT_LABEL = ("Arial", 10, "bold")

# Ping ve animasyon ayarları
PING_INTERVAL_SECONDS = 300 # Varsayılan ping süresi 5 dakika (300 saniye)
ANIMATION_DELAY_MS = 100

# Yeni: Ping süresi seçenekleri
PING_OPTIONS = {
    "5 Saniye": 5,
    "30 Saniye": 30,
    "1 Dakika": 60,
    "5 Dakika": 300,
    "30 Dakika": 1800
}
