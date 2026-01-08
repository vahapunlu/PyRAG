# 📊 Granular Feedback Sistemi - Kullanım Kılavuzu

## 🎯 Ne İçin?

Normal feedback: "Bu cevap iyi 👍 / kötü 👎"  
**Granular feedback**: "IS3218 mükemmel, NEK606 alakasız, şu cümle çok yararlı!"

## 🔍 Feedback Tipleri

### 1️⃣ **Kaynak Bazlı Feedback**
Her kaynak doküman için ayrı değerlendirme:

```python
from src.granular_feedback import get_granular_feedback_manager

manager = get_granular_feedback_manager()

manager.add_feedback(
    query="Kablo seçimi nasıl yapılır?",
    response="Cevap metni...",
    overall_rating=4,
    source_feedbacks=[
        {
            "document": "IS3218",
            "page": "15",
            "rating": "helpful",      # helpful / not_helpful / irrelevant
            "stars": 5,               # 1-5 yıldız
            "comment": "Çok detaylı"
        },
        {
            "document": "NEK606",
            "page": "8",
            "rating": "not_helpful",
            "stars": 2,
            "comment": "Konuyla alakasız"
        }
    ]
)
```

**Değerlendirme Seçenekleri:**
- ✅ `helpful` - Yararlı, soruya cevap veriyor
- ⚠️ `not_helpful` - Pek yararlı değil, tam değil
- ❌ `irrelevant` - Tamamen alakasız

### 2️⃣ **Text Highlight Feedback**
Kullanıcı yararlı bulduğu metni seçer:

```python
manager.add_feedback(
    query="Yangın alarm kablosu özellikleri?",
    response="Uzun cevap metni...",
    highlights=[
        {
            "text": "EN 54-11 standardına uygun olmalıdır",
            "sentiment": "positive",
            "source": "EN54-11",
            "comment": "Tam aradığım bilgi"
        },
        {
            "text": "Kablo kesiti minimum 1.5mm²",
            "sentiment": "positive",
            "source": "IS3218"
        }
    ]
)
```

### 3️⃣ **Multi-Dimensional Rating**
Cevabı farklı boyutlarda değerlendirme:

```python
manager.add_feedback(
    query="Topraklama nasıl yapılmalı?",
    response="Cevap...",
    overall_rating=4,
    dimensions={
        "relevance": 5,      # Soruyla ne kadar alakalı?
        "clarity": 3,        # Ne kadar açık ve anlaşılır?
        "completeness": 4    # Ne kadar eksiksiz?
    },
    comment="İyi ama biraz daha açık olabilirdi"
)
```

## 📊 Kaynak Kalite Skorları

Sistem her kaynağın kalitesini otomatik hesaplar:

```python
# Tüm kaynak skorlarını al
scores = manager.get_source_quality_scores()

# Örnek çıktı:
{
    "IS3218": {
        "quality_score": 85.5,      # 0-100 arası
        "avg_rating": 4.5,           # 1-5 yıldız ortalaması
        "helpful_count": 10,
        "not_helpful_count": 2,
        "irrelevant_count": 0,
        "total_feedbacks": 12
    },
    "NEK606": {
        "quality_score": 45.0,
        "avg_rating": 2.3,
        ...
    }
}

# En iyi kaynakları al
best_sources = manager.get_best_sources(limit=5)
```

**Kalite Skoru Hesaplama:**
- Helpful = +10 puan
- Not Helpful = -5 puan
- Irrelevant = -10 puan
- Normalize edilir (0-100 arası)

## 🌟 Popüler Highlight'lar

En çok işaretlenen metinleri bulma:

```python
snippets = manager.get_highlighted_snippets(limit=10)

# Örnek:
[
    {
        "text": "Kablo kesiti minimum 1.5mm² olmalıdır",
        "source": "IS3218",
        "frequency": 15  # 15 kullanıcı bu metni işaretledi
    },
    ...
]
```

## 🎨 GUI Entegrasyonu

### HTML/JavaScript Örneği

[examples/granular_feedback_ui.html](examples/granular_feedback_ui.html) dosyasına bakın.

**Özellikler:**
- ⭐ Yıldız rating sistemi
- 👍👎 Her kaynak için butonlar
- ✨ Text selection ile highlight
- 💬 Yorum kutuları
- 📊 Multi-dimensional rating

### API Endpoint Örneği

```python
# FastAPI endpoint
from examples.granular_feedback_api import app

# POST /api/submit_granular_feedback
# GET /api/source_quality_scores
# GET /api/best_sources
# GET /api/highlighted_snippets
```

## 🔄 Otomatik Learning Entegrasyonu

Granular feedback, learning sistemini besler:

```python
manager.add_feedback(
    query="...",
    response="...",
    overall_rating=5,
    source_feedbacks=[...],
    auto_learn=True  # Otomatik learning tetiklenir
)
```

**Ne Öğrenir?**
- Hangi kaynaklar sık birlikte kullanılıyor?
- Hangi kaynaklar daha kaliteli?
- Hangi metinler en yararlı?
- Hangi kombinasyonlar başarılı?

## 📈 Kullanım Senaryoları

### Senaryo 1: Kaynak Filtreleme

```python
# Düşük kaliteli kaynakları filtrele
scores = manager.get_source_quality_scores()
good_sources = [
    doc for doc, data in scores.items() 
    if data['quality_score'] > 70
]

# Sadece iyi kaynaklardan ara
result = engine.query(
    "Kablo seçimi?",
    allowed_sources=good_sources
)
```

### Senaryo 2: Cevap Geliştirme

```python
# En çok beğenilen snippetleri kullan
popular_snippets = manager.get_highlighted_snippets()

# Template cevaplar oluştur
# Örn: "X konusunda en popüler bilgi: {snippet}"
```

### Senaryo 3: Kalite Raporu

```python
# Haftalık rapor
stats = manager.get_statistics()
best = manager.get_best_sources(limit=10)

report = f"""
📊 Haftalık Kaynak Kalite Raporu
================================
Toplam Feedback: {stats['total_feedbacks']}
Ortalama Rating: {stats['avg_overall_rating']:.1f}/5

🏆 En İyi Kaynaklar:
"""

for source in best:
    report += f"\n{source['document']}: {source['quality_score']:.1f}/100"
```

## 🎯 Best Practices

### 1. UI Tasarımı

```html
✅ DOĞRU:
- Her kaynak için ayrı rating alanı
- Açık ve net butonlar (Yararlı / Alakasız)
- Text selection ile highlight desteği
- Yorum kutuları isteğe bağlı

❌ YANLIŞ:
- Karmaşık formlar
- Çok fazla zorunlu alan
- Anlaşılmaz seçenekler
```

### 2. Feedback Toplama

```python
# Minimum düşük tut
# En az overall rating + kaynak ratingleri yeterli
manager.add_feedback(
    query=query,
    response=response,
    overall_rating=4,  # ZORUNLU
    source_feedbacks=[  # ÖNERİLEN
        {"document": "IS3218", "rating": "helpful", "stars": 5}
    ]
    # highlights ve dimensions OPSIYONEL
)
```

### 3. Kalite Eşikleri

```python
# Kaynak filtreleme eşikleri
EXCELLENT = 80   # %80+ → Kesinlikle kullan
GOOD = 60        # %60-80 → Kullan
MEDIOCRE = 40    # %40-60 → Dikkatli kullan
POOR = 40        # %40- → Filtreye düşünülebilir

scores = manager.get_source_quality_scores()
for doc, data in scores.items():
    score = data['quality_score']
    if score >= EXCELLENT:
        print(f"✅ {doc}: Mükemmel kaynak")
    elif score >= GOOD:
        print(f"👍 {doc}: İyi kaynak")
    elif score >= MEDIOCRE:
        print(f"⚠️ {doc}: Orta kaynak")
    else:
        print(f"❌ {doc}: Zayıf kaynak")
```

## 🔧 Veritabanı Yapısı

### feedback tablosu
```sql
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    query TEXT,
    response TEXT,
    overall_rating INTEGER,     -- 1-5 yıldız
    relevance_rating INTEGER,   -- Dimension
    clarity_rating INTEGER,     -- Dimension
    completeness_rating INTEGER,-- Dimension
    comment TEXT
)
```

### source_feedback tablosu
```sql
CREATE TABLE source_feedback (
    id INTEGER PRIMARY KEY,
    feedback_id INTEGER,
    document_name TEXT,
    page_number TEXT,
    rating TEXT,  -- helpful/not_helpful/irrelevant
    stars INTEGER,
    comment TEXT,
    timestamp TEXT
)
```

### text_highlights tablosu
```sql
CREATE TABLE text_highlights (
    id INTEGER PRIMARY KEY,
    feedback_id INTEGER,
    highlighted_text TEXT,
    sentiment TEXT,  -- positive/negative
    source_document TEXT,
    comment TEXT
)
```

### source_quality_scores tablosu (aggregated)
```sql
CREATE TABLE source_quality_scores (
    document_name TEXT PRIMARY KEY,
    avg_rating REAL,
    quality_score REAL,  -- 0-100
    helpful_count INTEGER,
    not_helpful_count INTEGER,
    irrelevant_count INTEGER,
    total_feedbacks INTEGER
)
```

## 📱 Mobil / Compact UI Önerileri

```python
# Basitleştirilmiş mobil versiyonu
{
    "overall": 4,  # Yıldız
    "sources": [
        {"doc": "IS3218", "thumb": "up"},    # Sadece 👍/👎
        {"doc": "NEK606", "thumb": "down"}
    ]
}
```

## 🎓 Sonuç

Granular feedback ile:
- ✅ Her kaynağın kalitesini öğrenirsiniz
- ✅ Hangi metinlerin yararlı olduğunu bilirsiniz
- ✅ Sistem daha hassas öğrenir
- ✅ Kullanıcılar daha detaylı geri bildirim verir
- ✅ Cevap kalitesi sürekli artar

**İyi kullanımlar! 🚀**
