# 🚀 DeepSeek API Kurulum Rehberi

## ⭐ Neden DeepSeek?

- ✅ **GPT-4 kalitesinde** performans
- ✅ **90% daha ucuz** (GPT-4'ten)
- ✅ **Ücretsiz $5 kredit** ile başlayın
- ✅ **Matematik ve tablo'da mükemmel**

### Maliyet Karşılaştırması

| İşlem | GPT-4o | DeepSeek V3 | Tasarruf |
|-------|--------|-------------|----------|
| 100 sayfa PDF indeksleme | $2.00 | $0.20 | **90%** |
| 100 sorgu yanıtı | $3.00 | $0.40 | **87%** |
| **Aylık Toplam (orta kullanım)** | **$60-150** | **$3-8** | **95%** 🎉 |

---

## 📝 Kurulum Adımları

### 1️⃣ DeepSeek API Key Alın

1. **Kayıt Olun**: https://platform.deepseek.com/
2. **Email ile giriş yapın** (Google/GitHub da olur)
3. **API Keys** sayfasına gidin
4. **Create API Key** butonuna tıklayın
5. Key'i kopyalayın (örnek: `sk-xxxxxxxxxxxxxxxx`)

> 💡 İlk kayıtta **$5 ücretsiz kredit** verilir!

### 2️⃣ `.env` Dosyasını Düzenleyin

Proje klasöründeki `.env` dosyasını açın ve DeepSeek key'inizi ekleyin:

```env
# DeepSeek API Key
DEEPSEEK_API_KEY=sk-your-key-here

# OpenAI API Key (sadece embedding için gerekli)
OPENAI_API_KEY=sk-your-openai-key-here

# Model ayarları (zaten yapılandırılmış)
LLM_MODEL=deepseek-chat
EMBEDDING_MODEL=text-embedding-3-small
```

### 3️⃣ Test Edin

**GUI ile:**
```powershell
python main.py gui
```

**CLI ile:**
```powershell
python main.py query "Test sorusu nedir?"
```

İlk çalıştırmada şu mesajı görmelisiniz:
```
📡 Using DeepSeek API (90% cheaper!)...
✅ LlamaIndex configured
```

---

## 🔄 OpenAI'a Geri Dönmek İsterseniz

`.env` dosyasında sadece model ismini değiştirin:

```env
LLM_MODEL=gpt-4o-mini
# veya
LLM_MODEL=gpt-4o
```

---

## 💰 Kullanım ve Ücretlendirme

### DeepSeek Fiyatlandırma (Aralık 2025)

- **Input**: $0.27 / 1M token
- **Output**: $1.10 / 1M token

### Örnek Hesaplamalar

**100 sayfalık PDF indeksleme:**
- ~50,000 token → **$0.014** (1.5 cent!)

**100 soru-cevap:**
- Her sorgu ~1,500 token → **$0.40**

**Aylık bütçe (5 kullanıcı, 500 sorgu):**
- İlk indeksleme: $0.50
- Aylık sorgular: $2-5
- **Toplam: $3-8/ay** 🎉

### Kredinizi Kontrol Edin

https://platform.deepseek.com/usage

---

## 🛠️ Sorun Giderme

### Hata: "Invalid API key"

```
❌ Çözüm:
1. API key'i doğru kopyaladığınızdan emin olun
2. .env dosyasında boşluk olmamalı
3. Key'in başında "sk-" olmalı
```

### Hata: "Insufficient credits"

```
❌ Çözüm:
1. https://platform.deepseek.com/usage adresinden kredinizi kontrol edin
2. Kredi bitmiş ise kredi kartı ekleyin (minimum $5)
3. Veya OpenAI'a geçin (LLM_MODEL=gpt-4o-mini)
```

### DeepSeek yerine OpenAI kullanılıyor

```
❌ Çözüm:
1. .env dosyasında LLM_MODEL=deepseek-chat olduğundan emin olun
2. DEEPSEEK_API_KEY dolu olmalı
3. Programı yeniden başlatın
```

---

## 📊 Performans Karşılaştırması

| Özellik | GPT-4o | DeepSeek V3 |
|---------|--------|-------------|
| **Kalite** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Hız** | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Fiyat** | 💰💰💰💰💰 | 💰 |
| **Matematik** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Tablo Anlama** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Türkçe** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 🎯 Sonuç

DeepSeek V3 ile:
- ✅ **95% daha az maliyet**
- ✅ **Aynı kalite**
- ✅ **Daha hızlı yanıtlar**
- ✅ **Sınırsız kullanım** (krediniz bitene kadar)

**Başlamak için:** `.env` dosyasına key'inizi ekleyin ve GUI'yi başlatın! 🚀

---

## 📞 Yardım

Sorun yaşarsanız:
1. `logs/` klasöründeki log dosyalarını kontrol edin
2. `python main.py stats` komutuyla sistem durumunu görün
3. DeepSeek dökümantasyonu: https://platform.deepseek.com/docs
