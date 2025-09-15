# Telegram Image Generation Bot - Render Deployment

Bu loyihani Render platformasiga yuklash uchun qo'llanma.

## Kerakli Environment Variables

Render dashboardda quyidagi environment variablelarni sozlang:

### TELEGRAM_BOT_TOKEN (Majburiy)
- Telegram'da @BotFather orqali bot yarating
- Bot tokenini olganingizdan keyin, Render dashboardda "Environment Variables" bo'limiga qo'shing

### GOOGLE_API_KEY (Majburiy)
- Google AI Studio (aistudio.google.com) saytiga kiring
- API key yarating
- Bu keyni Render dashboardda "Environment Variables" bo'limiga qo'shing

### TELEGRAM_CHANNEL_ID (Ixtiyoriy - Kanal posting uchun)
- Telegram kanalingiz ID'sini yoki username'ini kiriting
- Misol: @my_channel yoki -1001234567890
- Bot kanalga admin sifatida qo'shilgan bo'lishi kerak

### ADMIN_USER_IDS (Ixtiyoriy - Admin buyruqlar uchun)
- Admin foydalanuvchilar ID'larini vergul bilan ajrating
- Misol: 123456789,987654321
- Bu ID'lar /channel_post va /set_channel buyruqlarini ishlata oladi

### BOT_USERNAME (Ixtiyoriy - Post'larda ko'rsatish uchun)
- Bot username'ini @ belgisisiz kiriting
- Misol: my_bot_username
- Kanal postlarida bot nomi ko'rsatiladi

## Render'da Deploy Qilish

### Avtomatik Deploy (render.yaml bilan)
1. GitHub/GitLab repositoriyangizni Render'ga ulang
2. render.yaml fayli avtomatik taniladi
3. Environment variables qo'shing:
   - TELEGRAM_BOT_TOKEN
   - GOOGLE_API_KEY
4. Deploy qiling

### Manual Deploy
1. GitHub/GitLab repositoriyangizni Render'ga ulang
2. Service type sifatida "Worker" tanlang
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python main.py`
5. Environment variables qo'shing
6. Deploy qiling

### Muhim Eslatmalar
- Service type "Worker" bo'lishi kerak (web service emas)
- Bot 24/7 ishlab turishi uchun Starter plan yoki undan yuqori kerak
- Environment variables to'g'ri sozlanganligini tekshiring

## Fayllar

- `main.py` - Asosiy bot kodi
- `requirements.txt` - Python paketlar ro'yxati  
- `render.yaml` - Render konfiguratsiya fayli
- `runtime.txt` - Python versiya spetsifikatsiyasi

## Xususiyatlar

Bot quyidagi buyruqlarni qo'llab-quvvatlaydi:
- `/start` - Botni ishga tushirish
- `/imagine [tavsif]` - Rasm yaratish
- `/edit [ko'rsatma]` - Rasmni tahrirlash
- `/text [matn]` - Matn bilan rasm yaratish
- `/recipe [taom]` - Retsept yaratish