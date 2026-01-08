# 🧠 Feedback Learning Sistemi Kullanım Kılavuzu

## 📋 Genel Bakış

Feedback Learning sistemi, kullanıcı geri bildirimlerinden öğrenerek Knowledge Graph'ı otomatik olarak geliştirir. Pozitif feedback alan cevaplardan yeni ilişkiler keşfeder ve mevcut ilişkileri güçlendirir.

## 🎯 Temel Özellikler

### 1. **Otomatik İlişki Keşfi**
- Sık birlikte kullanılan dokümanları tespit eder
- Güçlü co-occurrence pattern'leri bulur
- Neo4j'de yeni ilişkiler oluşturur

### 2. **İlişki Güçlendirme**
- Mevcut ilişkileri her pozitif feedback'le güçlendirir
- Zayıf ilişkileri otomatik budalar
- Dinamik ağırlık güncelleme

### 3. **Query Pattern Analizi**
- Başarılı sorguların ortak kelimelerini tespit eder
- Kelime-doküman ilişkilerini öğrenir
- Semantik bağlantılar kurar

## 🚀 Kullanım

### Temel Kullanım - Otomatik Learning

```python
from src.query_engine import QueryEngine

# Query engine başlat
engine = QueryEngine()

# Normal sorgu yap
result = engine.query("kablo seçimi nasıl yapılır?")

# Feedback ekle (otomatik learning tetiklenir)
engine.add_feedback(
    query="kablo seçimi nasıl yapılır?",
    response=result['response'],
    feedback_type='positive',  # veya 'negative'
    sources=result['sources'],
    comment="Çok yararlı bilgi",
    auto_learn=True  # Otomatik öğrenme (varsayılan True)
)
```

### Manuel Learning Tetikleme

```python
# Son 7 günlük feedback'lerden öğren
stats = engine.trigger_learning(time_window_days=7)

print(f"Yeni ilişkiler: {stats['new_relationships']}")
print(f"Güçlendirilen: {stats['strengthened_relationships']}")
print(f"Keşfedilen pattern'ler: {stats['discovered_patterns']}")
```

### Learning İstatistikleri

```python
# Öğrenilen ilişki istatistikleri
learning_stats = engine.get_learning_statistics()

print(f"Toplam öğrenilen ilişkiler: {learning_stats['total_learned']}")
print(f"Ortalama ağırlık: {learning_stats['avg_weight']:.2f}")
```

### Zayıf İlişkileri Temizleme

```python
# 0.3'ten düşük ağırlıklı ilişkileri kaldır
removed = engine.prune_weak_relationships(min_weight=0.3)
print(f"Temizlenen ilişki sayısı: {removed}")
```

## 📊 Nasıl Çalışır?

### 1. Co-occurrence Analizi
```
Kullanıcı beğeniyor:
├─ IS3218 + NEK606 → 4 kez birlikte
├─ IS3218 + EN54-11 → 1 kez birlikte
└─ NEK606 + IS10101 → 1 kez birlikte

Confidence hesaplama:
IS3218 ↔ NEK606 = 4/max(5,5) = 0.80 ✅ (threshold: 0.6)
```

### 2. İlişki Oluşturma
```cypher
MATCH (d1:DOCUMENT {name: 'IS3218'})
MATCH (d2:DOCUMENT {name: 'NEK606'})
MERGE (d1)-[r:COMPLEMENTS]->(d2)
SET r.weight = 0.80, r.learned = true
```

### 3. Pattern Detection
```
Keyword: "kablo"
├─ 10 soruda kullanıldı
├─ Hepsinde IS3218 kaynak olarak döndü
└─ Confidence: 100% → Keyword-Document ilişkisi
```

## ⚙️ Konfigürasyon

### FeedbackLearner Parametreleri

```python
from src.feedback_learner import FeedbackLearner

learner = FeedbackLearner(
    min_confidence=0.6,   # Minimum güven skoru (0-1)
    min_support=3,        # Minimum co-occurrence sayısı
    learning_rate=0.1,    # İlişki güçlendirme oranı
    decay_days=30         # Eski feedback'lerin azalan etkisi
)
```

### Varsayılan Değerler
- **min_confidence**: 0.6 (60% güven)
- **min_support**: 3 (en az 3 kez birlikte görülmeli)
- **learning_rate**: 0.1 (her feedback ile %10 artış)
- **decay_days**: 30 (30 günden eski feedback'ler daha az etkili)

## 🔍 İlişki Türleri

### COMPLEMENTS
Birbirini tamamlayan dokümanlar
```
(IS3218)-[:COMPLEMENTS]->(NEK606)
```
**Örnek**: Kablo seçimi konusunda her ikisi de sık kullanılıyor

### RELATED_TO
Benzer konuları içeren dokümanlar
```
(EN54-11)-[:RELATED_TO]->(IS3218)
```
**Örnek**: Her ikisi de yangın güvenliği hakkında

## 📈 Örnek Senaryolar

### Senaryo 1: Kablo Seçimi Uzmanlığı

```python
# 1. Kullanıcı kablo seçimi soruları soruyor
result1 = engine.query("kablo kesiti nasıl hesaplanır?")
result2 = engine.query("yangın alarm kablosu hangi standardı kullanır?")
result3 = engine.query("kablo tipi nasıl belirlenir?")

# 2. Hepsinden memnun, pozitif feedback veriyor
for result in [result1, result2, result3]:
    engine.add_feedback(
        query=result['query'],
        response=result['response'],
        feedback_type='positive',
        sources=result['sources']
    )

# 3. Sistem öğreniyor:
# ✅ IS3218 ↔ NEK606 güçlü ilişki tespit edildi
# ✅ "kablo" kelimesi → IS3218 dokümanı pattern'i
# ✅ Neo4j'de COMPLEMENTS ilişkisi oluşturuldu
```

### Senaryo 2: İlişki Güçlendirme

```python
# İlk learning
stats1 = engine.trigger_learning()
# → IS3218-NEK606: weight = 0.75

# Daha fazla pozitif feedback
# ... (kullanıcılar benzer sorular soruyor) ...

# İkinci learning
stats2 = engine.trigger_learning()
# → IS3218-NEK606: weight = 0.83 (güçlendi!)
```

### Senaryo 3: Zayıf İlişki Budama

```python
# Periyodik temizlik (örn: haftada 1)
import schedule

def weekly_cleanup():
    # 0.3'ten düşük ilişkileri temizle
    removed = engine.prune_weak_relationships(min_weight=0.3)
    print(f"🗑️ {removed} zayıf ilişki temizlendi")

schedule.every().monday.at("02:00").do(weekly_cleanup)
```

## 🎨 GUI Entegrasyonu

GUI'de feedback butonu eklenebilir:

```python
# app_gui.py içinde
def on_feedback_button_click(feedback_type):
    """Kullanıcı 👍 veya 👎 tıkladığında"""
    engine.add_feedback(
        query=current_query,
        response=current_response,
        feedback_type=feedback_type,  # 'positive' veya 'negative'
        sources=current_sources,
        auto_learn=True  # Otomatik öğrenme
    )
    
    # Bildirim göster
    show_notification("✅ Geri bildirim kaydedildi ve sistemden öğrenildi!")
```

## 📊 İstatistik ve Raporlama

```python
# Feedback istatistikleri
feedback_stats = engine.get_feedback_stats()
print(f"Toplam pozitif: {feedback_stats['positive_count']}")
print(f"Toplam negatif: {feedback_stats['negative_count']}")

# Learning istatistikleri
learning_stats = engine.get_learning_statistics()
print(f"Öğrenilen ilişkiler: {learning_stats['total_learned']}")
print(f"Ortalama güven: {learning_stats['avg_weight']:.2%}")

# Son feedback'ler
recent = engine.get_recent_feedback(limit=10)
for fb in recent:
    print(f"{fb['timestamp']}: {fb['feedback_type']} - {fb['query'][:50]}...")
```

## 🔄 Periyodik Learning Schedule

```python
import schedule
import time
from src.query_engine import QueryEngine

engine = QueryEngine()

def daily_learning():
    """Her gün saat 02:00'de çalış"""
    print("🧠 Günlük learning başlatılıyor...")
    stats = engine.trigger_learning(time_window_days=7)
    print(f"✅ Tamamlandı: {stats['new_relationships']} yeni ilişki")

def weekly_cleanup():
    """Her Pazartesi 03:00'te temizlik"""
    print("🗑️ Haftalık temizlik başlatılıyor...")
    removed = engine.prune_weak_relationships(min_weight=0.3)
    print(f"✅ {removed} zayıf ilişki temizlendi")

# Schedule tanımla
schedule.every().day.at("02:00").do(daily_learning)
schedule.every().monday.at("03:00").do(weekly_cleanup)

# Çalıştır
while True:
    schedule.run_pending()
    time.sleep(3600)  # Her saat kontrol et
```

## 🎯 Best Practices

### 1. Threshold'ları Ayarlama
```python
# Sıkı (az ama kaliteli ilişkiler)
learner = FeedbackLearner(min_confidence=0.8, min_support=5)

# Gevşek (daha çok ilişki, deneysel)
learner = FeedbackLearner(min_confidence=0.5, min_support=2)
```

### 2. Time Window Kullanımı
```python
# Sadece son 7 günden öğren (taze feedback)
stats = engine.trigger_learning(time_window_days=7)

# Tüm geçmişten öğren (kapsamlı analiz)
stats = engine.trigger_learning(time_window_days=None)
```

### 3. Periyodik Temizlik
```python
# Ayda bir agresif temizlik
monthly_cleanup = engine.prune_weak_relationships(min_weight=0.5)

# Haftalık hafif temizlik
weekly_cleanup = engine.prune_weak_relationships(min_weight=0.3)
```

## 🐛 Troubleshooting

### Problem: İlişki oluşturulmuyor
```python
# Çözüm 1: Threshold'ları azalt
learner.min_confidence = 0.5
learner.min_support = 2

# Çözüm 2: Daha fazla feedback topla
feedback_count = engine.get_feedback_stats()['positive_count']
print(f"Pozitif feedback: {feedback_count}")
# En az 10-15 pozitif feedback olmalı
```

### Problem: Neo4j bağlantı hatası
```python
# .env.neo4j dosyasını kontrol et
# NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
```

### Problem: Çok fazla zayıf ilişki
```python
# Threshold'ları artır
learner.min_confidence = 0.7
learner.min_support = 5

# Veya mevcut zayıfları temizle
engine.prune_weak_relationships(min_weight=0.5)
```

## 📚 API Referansı

### QueryEngine Methods

| Method | Açıklama | Parametreler |
|--------|----------|--------------|
| `add_feedback()` | Feedback ekle | query, response, feedback_type, sources, auto_learn |
| `trigger_learning()` | Manuel learning | time_window_days |
| `get_learning_statistics()` | İstatistikler | - |
| `prune_weak_relationships()` | Temizlik | min_weight |

### FeedbackLearner Methods

| Method | Açıklama | Return |
|--------|----------|--------|
| `learn_from_feedback()` | Ana learning | stats dict |
| `get_learning_statistics()` | İstatistikler | stats dict |
| `prune_weak_relationships()` | Budama | removed count |

## 🎓 Sonuç

Feedback Learning sistemi:
- ✅ Kullanıcı feedback'lerinden otomatik öğrenir
- ✅ Knowledge Graph'ı dinamik olarak geliştirir
- ✅ Sistem zamanla daha akıllı hale gelir
- ✅ Manuel müdahale gerektirmez
- ✅ Sürekli kendini optimize eder

**İyi kullanımlar! 🚀**
