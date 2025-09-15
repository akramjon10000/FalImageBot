# Telegram Image Generation Bot - Render Deployment

Bu loyihani Render platformasiga yuklash uchun qo'llanma.

## Kerakli Environment Variables

Render dashboardda quyidagi environment variablelarni sozlang:

### TELEGRAM_BOT_TOKEN
- Telegram'da @BotFather orqali bot yarating
- Bot tokenini olganingizdan keyin, Render dashboardda "Environment Variables" bo'limiga qo'shing

### GOOGLE_API_KEY  
- Google AI Studio (aistudio.google.com) saytiga kiring
- API key yarating
- Bu keyni Render dashboardda "Environment Variables" bo'limiga qo'shing

## Render'da Deploy Qilish

1. GitHub/GitLab repositoriyangizni Render'ga ulang
2. Service type sifatida "Background Worker" tanlang
3. Environment variables qo'shing
4. Deploy qiling

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