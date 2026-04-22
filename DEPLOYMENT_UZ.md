# Telegram Botni Render.com ga joylashtirish (Deployment) bo'yicha yo'riqnoma

Ushbu yo'riqnoma orqali siz o'z botingizni Render.com platformasida 24/7 rejimida bepul ishlatishingiz mumkin.

## 1-qadam: GitHub-ga yuklash
1. [GitHub](https://github.com/) hisobingizga kiring.
2. Yangi repository (ombor) oching (masalan: `rizz-bot`).
3. Zip fayl ichidagi barcha fayllarni (`bot.py`, `requirements.txt`, `Procfile`, `database.py`) ushbu repository-ga yuklang.

## 2-qadam: Render.com da hisob ochish
1. [Render.com](https://render.com/) saytiga kiring va GitHub orqali ro'yxatdan o'ting.

## 3-qadam: Yangi Web Service yaratish
1. Render dashboard-da **"New +"** tugmasini bosing va **"Background Worker"**-ni tanlang (chunki bot polling rejimida ishlaydi).
2. GitHub repository-ingizni tanlang.
3. Quyidagi sozlamalarni kiriting:
   - **Name:** `rizz-bot`
   - **Region:** O'zingizga yaqinini tanlang (masalan, Frankfurt).
   - **Branch:** `main` (yoki `master`).
   - **Runtime:** `Python 3`.
   - **Build Command:** `pip install -r requirements.txt`.
   - **Start Command:** `python bot.py`.

## 4-qadam: Environment Variables (Muhit o'zgaruvchilari) ni sozlash
**MUHIM:** "Environment" bo'limiga o'ting va quyidagi o'zgaruvchilarni qo'shing:
- `TELEGRAM_TOKEN`: `8283330138:AAGGsvMo3go_hFm2BR41W6QIcOKaXyNOGt0`
- `GEMINI_API_KEY`: `AIzaSyAFyY4-21IVZtcLvRrzRiN1e_VXIiM_qEQ`
- `ADMIN_USERNAME`: `Qosimov_Shahzod`
- `FREE_TRIAL_LIMIT`: `3`

## 5-qadam: Joylashtirish (Deploy)
1. **"Create Background Worker"** tugmasini bosing.
2. Render botni o'rnatishni boshlaydi. "Logs" bo'limida "Bot ishga tushdi..." degan yozuvni ko'rsangiz, demak hammasi tayyor!

---
**Eslatma:** Render-ning bepul tarifida SQLite bazasi (`bot_users.db`) har safar bot qayta yuklanganda o'chib ketishi mumkin. Agar ma'lumotlar saqlanib qolishini istasangiz, Render-da "Disk" ulab qo'yishingiz yoki tashqi ma'lumotlar bazasidan (masalan, MongoDB yoki PostgreSQL) foydalanishingiz kerak bo'ladi.
