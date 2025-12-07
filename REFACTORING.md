# PyRAG GUI Refactoring

## 🎯 Modüler Yapı

Eski `app_gui.py` (2165 satır) şu modüllere ayrıldı:

### 📁 Yeni Yapı

```
src/gui/
├── __init__.py                    # Module exports  
├── constants.py                   # Constants, colors, config (119 lines)
├── main_window.py                 # Main application window (335 lines)
├── sidebar.py                     # Sidebar component (174 lines)
├── chat.py                        # Chat area component (381 lines)
├── dialogs.py                     # Dialog import hub (14 lines)
├── new_document_dialog.py         # New document dialog (~530 lines)
├── settings_dialog.py             # Settings dialog (~340 lines)
└── database_manager_dialog.py    # Database manager (~410 lines)
```

### 🔧 Her Modülün Sorumluluğu

#### `constants.py`
- Golden ratio (PHI) tanımları
- Renk paleti (COLORS)
- Font boyutları (FONT_SIZES)
- Buton yükseklikleri (BUTTON_HEIGHTS)
- Spacing değerleri (SPACING)
- Desteklenen dosya tipleri
- Default kategoriler ve projeler
- UI mesajları

#### `main_window.py`
- PyRAGApp ana sınıfı
- Sistem başlatma (initialize_system)
- Query işleme (send_message, _process_query)
- Dialog açma (open_new_document_dialog, open_settings_dialog)
- İstatistik gösterme (show_statistics)
- Filter yönetimi

#### `sidebar.py`
- Sidebar sınıfı ve widget'ları
- Logo ve başlık
- API status göstergeleri
- Filter dropdown'ları
- Action butonları (golden ratio düzeninde)
- Versiyon bilgisi

#### `chat.py`
- ChatArea sınıfı
- Chat display (scrollable textbox)
- Message rendering (user, assistant, system, source)
- Input area
- Welcome message
- Chat clear fonksiyonu

#### `dialogs.py`
- Import hub for all dialog windows
- Clean module interface

#### `new_document_dialog.py`
- NewDocumentDialog sınıfı
- Two-row file layout (metadata + progress)
- Real-time status indicators with progress bars
- Background indexing with threading
- Shows page count and chunk count for each document
- No auto-close after completion

#### `settings_dialog.py`
- SettingsDialog sınıfı
- Kategori ve proje yönetimi
- Click-to-select workflow
- Add/delete operations

#### `database_manager_dialog.py`
- DatabaseManagerDialog sınıfı
- Document metadata editing
- CRUD operations on ChromaDB
- Double confirmation for critical operations

### 🚀 Kullanım

#### Yeni Modüler Yapı İle:
```python
from src.gui import main

if __name__ == "__main__":
    main()
```

Veya doğrudan:
```bash
python app_gui_new.py
```

#### Eski Yapı (Hala çalışır):
```bash
python app_gui.py
```

### ✅ Avantajlar

1. **Okunabilirlik**: Her dosya tek bir sorumluluğa sahip
2. **Bakım Kolaylığı**: Değişiklikler izole edilmiş modüllerde
3. **Yeniden Kullanılabilirlik**: Component'ler bağımsız kullanılabilir
4. **Test Edilebilirlik**: Her modül ayrı test edilebilir
5. **Performans**: Lazy loading mümkün
6. **Ekip Çalışması**: Farklı dosyalarda paralel çalışma

### 🔄 Migration Plan

**Faz 1**: ✅ Modüler yapı oluşturuldu
**Faz 2**: Test ve doğrulama
**Faz 3**: app_gui.py'yi app_gui_legacy.py olarak yedekle
**Faz 4**: app_gui_new.py'yi app_gui.py olarak değiştir

### 📝 Notlar

- Tüm Golden Ratio hesaplamaları constants.py'de
- Callback'ler dictionary olarak sidebar'a geçiliyor
- Dialog'lar parent'a message göndermek için parent.chat.append_message() kullanıyor
- Status indicator'lar STATUS_ICONS ve STATUS_COLORS dict'lerinden

### 🐛 Bilinen Sorunlar

- SettingsDialog henüz tam implementasyona sahip değil (basitleştirilmiş versiyon)
- Bazı eski app_gui.py fonksiyonları henüz taşınmadı (nadiren kullanılanlar)

### 📚 Gelecek İyileştirmeler

1. SettingsDialog'u tam olarak implemente et
2. Unit testler ekle
3. Type hints ekle
4. Docstring'leri iyileştir
5. Async/await için refactor (threading yerine)
