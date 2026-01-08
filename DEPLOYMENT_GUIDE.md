# 🚀 PyRAG Bulut Kurulum Rehberi (Cloud Deployment)

Bu proje "Docker" ve "Next.js" teknolojilerini kullandığı için modern bulut platformlarında dakikalar içinde yayına alınabilir.

GitHub'daki kodlarınızı canlı bir web sitesine dönüştürmek için en kolay (ve genellikle ücretsiz/ucuz) yöntem **Render.com** veya **Railway.app** kullanmaktır.

## Seçenek 1: Render.com (Önerilen - Ücretsiz Başlangıç)

Render, GitHub reponuzu otomatik olarak algılar ve hem Python Beynini (Backend) hem de Web Arayüzünü (Frontend) çalıştırır.

### ADIM 1: Python API (Backend) Kurulumu
1. [render.com](https://render.com) adresine gidin ve GitHub ile giriş yapın.
2. **"New +"** butonuna basın ve **"Web Service"** seçin.
3. Listeden `PyRAG` reponuzu seçin.
4. Ayarları şöyle yapın:
   - **Name:** `pyrag-api`
   - **Runtime:** `Docker` (Otomatik algılar)
   - **Region:** `Frankfurt` (Türkiye'ye en yakın)
   - **Free Tier:** Seçili olsun.
5. **"Create Web Service"** butonuna basın.
6. İşlem bitince size `https://pyrag-api.onrender.com` gibi bir adres verecek. **Bu adresi kopyalayın.**

### ADIM 2: Web Arayüzü (Frontend) Kurulumu
1. Tekrar Dashboard'a dönün, **"New +"** -> **"Static Site"** veya **"Web Service"** seçin.
2. Yine `PyRAG` reponuzu seçin.
3. Ayarları şöyle yapın:
   - **Name:** `pyrag-web`
   - **Root Directory:** `web` (Burası önemli, web klasörünü seçmelisiniz)
   - **Build Command:** `npm run build`
   - **Start Command:** `npm start`
4. **Environment Variables** (Ortam Değişkenleri) kısmına şunu ekleyin:
   - `NEXT_PUBLIC_API_URL`: (Adım 1'de kopyaladığınız adres, örn: `https://pyrag-api.onrender.com`)
5. **"Create"** diyerek bitirin.

🎉 **Tebrikler!** Render size `https://pyrag-web.onrender.com` gibi bir link verecek. Bu linki tüm dünyayla paylaşabilirsiniz.

---

## Seçenek 2: Railway.app (Alternatif)

Railway de GitHub ile mükemmel çalışır.

1. [railway.app](https://railway.app) adresine gidin, GitHub ile giriş yapın.
2. **"New Project"** -> **"Deploy from GitHub repo"** -> `PyRAG` seçin.
3. Railway, `Dockerfile` dosyasını görüp otomatik olarak kurulumu yapacaktır.
4. Size otomatik bir `.railway.app` uzantılı link verecektir.

## Önemli Not (Veritabanı)

Bulutta çalışırken verilerinizin kaybolmaması için kalıcı bir depolamaya ihtiyacınız vardır.
Şu anki kurulum `Qdrant`'ı bellek üzerinde veya geçici diskte çalıştırır. Tam profesyonel kullanım için **Qdrant Cloud** (ücretsiz 1GB veriyor) kullanmanızı ve `src/api.py` içindeki ayarları oraya bağlamanızı öneririz.
