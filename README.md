# 📚 G'afur G'ulom Bot

Telegram bot — buyuk o'zbek shoiri va yozuvchisi G'afur G'ulom hayoti, ijodi va falsafasi haqida. AI orqali adib bilan suhbatlashish imkoni mavjud.

## ✨ Imkoniyatlar

### 👤 Foydalanuvchi qismi
- 🌐 **3 til**: O'zbek / Rus / Ingliz
- 📢 **Majburiy obuna** kanal(lar)ga
- 💬 **Adib bilan suhbat** — Gemini AI orqali (3+ API key rotatsiya bilan)
- 👤 **Adib haqida** — biografiya
- 📖 **Adib ijodi** — asarlar, hikoyalar, she'rlar (har bir bo'lim sonini ko'rsatadi)
- 🏆 **Stipendiya va ko'rik-tanlovlar**
- ❓ **Savol berish** — admin javob beradi
- 💡 **Kun hikmati** — avtomatik iqtibos jo'natish

### 🛠 Admin qismi
- 📊 Statistika (foydalanuvchilar, kontent)
- 📢 Majburiy obuna kanallarini boshqarish
- 👋 Kirish posti (har bir til uchun, qo'shimcha tugma bilan)
- 📣 Ommaviy post yuborish
- 📝 Ma'lumot qo'shish (biografiya, asar, hikoya, she'r, tanlov)
- ❓ Savollarga javob berish
- 💡 Iqtiboslar va yuborish jadvalini sozlash

## 🛠 Texnologiyalar

- **Python 3.11+**
- **aiogram 3.x** — Telegram Bot Framework
- **Supabase** — PostgreSQL + REST API
- **Google Gemini AI** — AI suhbat
- **APScheduler** — kunlik jadval
- **aiohttp** — webhook server
- **Render.com** — hosting

## 📦 Loyiha tuzilishi

```
gafur_gulom_bot/
├── bot.py                  # Asosiy fayl (webhook server)
├── config.py              # Sozlamalar
├── database.py            # Supabase bilan ishlash
├── requirements.txt
├── render.yaml            # Render deploy
├── runtime.txt
├── .env.example
├── handlers/              # Handler routerlari
├── keyboards/             # Klaviaturalar
├── locales/               # 3 til tarjimalari
├── middlewares/
├── utils/                 # Gemini, scheduler
└── sql/schema.sql         # Supabase jadvallari
```

---

## 🚀 Deploy qilish (Render + Supabase)

### 1-bosqich. Supabase sozlash

1. [supabase.com](https://supabase.com) ga kiring va yangi loyiha yarating
2. Settings → API → quyidagilarni ko'chirib oling:
   - `Project URL` → `SUPABASE_URL`
   - `service_role` kalit (yoki `anon` agar RLS yo'q bo'lsa) → `SUPABASE_KEY`
3. **SQL Editor** ga kiring va `sql/schema.sql` faylidagi kodni yopishtirib **Run** qiling

### 2-bosqich. Telegram bot yaratish

1. [@BotFather](https://t.me/BotFather) ga kiring
2. `/newbot` — bot yarating, tokenni saqlab oling
3. O'z Telegram `user_id` ni biling ([@userinfobot](https://t.me/userinfobot))

### 3-bosqich. Gemini API kalitlari

1. [aistudio.google.com](https://aistudio.google.com/app/apikey) ga kiring
2. **Kamida 3 ta** API key yarating (turli akkauntlardan ham bo'ladi)
3. Vergul bilan ajratib saqlang: `key1,key2,key3`

### 4-bosqich. Render'da deploy

#### Variant A — Blueprint orqali (oson)

1. Loyihani GitHub'ga yuklang
2. Render dashboard → **New +** → **Blueprint**
3. Reponi tanlang — `render.yaml` avtomatik o'qiladi
4. **Environment Variables** qismida quyidagilarni to'ldiring:
   - `BOT_TOKEN` — BotFather tokeni
   - `ADMIN_IDS` — admin id'lar (vergul bilan): `123456789,987654321`
   - `SUPABASE_URL`, `SUPABASE_KEY`
   - `GEMINI_API_KEYS` — `key1,key2,key3`
   - `WEBHOOK_HOST` — Render bergan URL: `https://gafur-gulom-bot.onrender.com` (deploy bo'lgach beriladi)
5. **Apply** bosing — bot ishga tushadi

#### Variant B — Qo'lda

1. Render → **New +** → **Web Service**
2. Repo'ni ulang
3. Sozlamalar:
   - **Build**: `pip install -r requirements.txt`
   - **Start**: `python bot.py`
   - **Health Check Path**: `/health`
4. Environment variables — yuqorida ko'rsatilgani kabi
5. Deploy bo'lgach `WEBHOOK_HOST` ni o'zingizning URL bilan yangilang va qayta deploy qiling

### 5-bosqich. Tekshirish

- Botga `/start` yuboring — til tanlash chiqishi kerak
- Adminlar `/admin` — admin paneli ochiladi
- Ma'lumot qo'shing va sinab ko'ring

---

## ⚠️ Muhim eslatmalar

### Render Free Plan haqida
Bepul planda servis 15 daqiqa faolsiz turganda **uxlab qoladi**. Buni hal qilish uchun:
- [UptimeRobot](https://uptimerobot.com) yoki [cron-job.org](https://cron-job.org) bepul xizmatlari orqali har 5-10 daqiqada `https://your-app.onrender.com/health` URLga ping yuboring
- Yoki Render'da pulli tarifga o'ting

### Webhook xatolari
- Telegram webhook **HTTPS** talab qiladi — Render bu ta'minlaydi
- `WEBHOOK_SECRET` mos kelishi kerak (Render `generateValue: true` bilan o'zi yaratadi)
- Agar bot javob bermasa: `https://your-app.onrender.com/health` ochiq ekanligini tekshiring

### Majburiy obuna kanallari
- Botni har bir kanalga **admin** qilib qo'shing (kamida "View Members" huquqi bilan)
- Kanal id'si: `@username` yoki `-1001234567890` (privat kanal uchun)
- Privat kanal uchun invite link ham qo'shing

### Gemini API
- Kamida 3 ta kalit qo'shing — biri quotani urganda boshqasiga avtomatik o'tadi
- Ko'proq kalit = ko'proq barqaror ishlaydi
- `gemini-2.0-flash` model arzon va tezkor

---

## 🧪 Lokal test (ixtiyoriy)

```bash
# Klonlash
git clone <repo_url>
cd gafur_gulom_bot

# Virtual env
python -m venv venv
source venv/bin/activate    # Linux/Mac
# venv\Scripts\activate     # Windows

# Kutubxonalar
pip install -r requirements.txt

# .env ni to'ldiring
cp .env.example .env
# Va WEBHOOK_HOST'ni ngrok yoki cloudflare tunnel orqali bering

# Ishga tushirish
python bot.py
```

Lokal test uchun [ngrok](https://ngrok.com/) bilan tunnel:
```bash
ngrok http 10000
# Chiqqan https URL'ni .env ichidagi WEBHOOK_HOST'ga yozing
```

---

## 📞 Yordam

- Loyiha tuzilmasi yoki kod haqida savollar bo'lsa — issue oching.
- Bot xatolik bersa — Render dashboard → **Logs** ga qarang.

## 📄 Litsenziya

Ushbu loyiha o'quv va ma'rifiy maqsadlar uchun yaratilgan.
