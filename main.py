#!/usr/bin/env python3
"""
AI Post Bot for Render.com Web Service
Generates 20 AI posts daily in Uzbek language (07:00-21:00 UTC) using Google Gemini
Flask Web Service with single endpoint: /
"""

import os
import logging
import schedule
import time
import threading
import requests
import random
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont
import io
import tempfile

from flask import Flask, jsonify
import google.generativeai as genai
from telegram import Bot
from telegram.error import TelegramError

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

# Configure Google Gemini
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    logger.info("Google Gemini configured successfully")
else:
    logger.warning("GOOGLE_API_KEY not found")

# Initialize Flask app
app = Flask(__name__)

# Initialize Telegram bot
bot = None
if TELEGRAM_BOT_TOKEN:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    logger.info("Telegram bot initialized")
else:
    logger.warning("TELEGRAM_BOT_TOKEN not found")

# Daily post counter
daily_post_count = 0
MAX_DAILY_POSTS = 20

# Uzbek content templates for AI posts
POST_TOPICS = [
    "Sun'iy intellekt va kelajak texnologiyalar",
    "Raqamli san'at va AI yaratuvchiligi", 
    "Mashinali o'qitish va neural tarmoqlar",
    "AI ning kundalik hayotdagi roli",
    "Robotlar va avtomatlashtirish",
    "Big Data va ma'lumotlar tahlili",
    "Kibr xavfsizlik va AI himoyasi",
    "Virtual reallik va AI integratsiyasi",
    "AI yordamida biznes rivojlantirish",
    "Tibbiyotda sun'iy intellekt",
    "Ta'limda AI texnologiyalari",
    "Smart shaharlar va IoT",
    "AI va ijodkorlik",
    "Avtonomus transport vositalari",
    "AI etikas va axloqiy masalalar",
    "Chatbot va virtual assistentlar",
    "Computer vision va tasvirni tanish",
    "Natural language processing",
    "AI startaplar va innovatsiyalar",
    "Kelajakdagi AI tendensiyalar"
]

def generate_text_content(topic):
    """Generate Uzbek text content using Gemini 1.5 Flash"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        {topic} mavzusida qiziq va ma'lumotli post yoz. Post o'zbek tilida bo'lishi kerak.
        
        Quyidagi formatda yoz:
        - 2-3 ta qiziq faktlar
        - Amaliy maslahatlar
        - Kelajak istiqbollari
        - Hashtag'lar qo'sh
        
        Post 200-300 so'zdan iborat bo'lsin.
        """
        
        response = model.generate_content(prompt)
        return response.text if response.text else None
        
    except Exception as e:
        logger.error(f"Error generating text content: {e}")
        return None

def generate_image_with_gemini(topic):
    """Generate image using Gemini 2.5 Flash Image"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        
        # Create English prompt for better image generation
        image_prompt = f"High-quality digital art about {topic}, futuristic technology, AI concepts, modern design, vibrant colors"
        
        response = model.generate_content(image_prompt)
        
        # Extract image data
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        if hasattr(part.inline_data, 'data'):
                            import base64
                            raw_data = part.inline_data.data
                            if isinstance(raw_data, str):
                                return base64.b64decode(raw_data)
                            else:
                                return raw_data
        return None
        
    except Exception as e:
        logger.error(f"Error generating image with Gemini: {e}")
        return None

def create_text_image(text, topic):
    """Create PNG image from text using PIL (fallback)"""
    try:
        # Create image
        width, height = 800, 600
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # Try to use a font
        try:
            font_size = 24
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Add topic as title
        title_y = 50
        draw.text((50, title_y), topic, fill='black', font=font)
        
        # Add text content
        text_y = 120
        max_width = width - 100
        
        # Split text into lines that fit
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Draw lines
        for i, line in enumerate(lines[:15]):  # Limit to 15 lines
            y_position = text_y + (i * 30)
            if y_position < height - 30:
                draw.text((50, y_position), line, fill='black', font=font)
        
        # Save to bytes
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
        
    except Exception as e:
        logger.error(f"Error creating text image: {e}")
        return None

def send_post_to_channel():
    """Send AI-generated post to Telegram channel"""
    global daily_post_count
    
    if daily_post_count >= MAX_DAILY_POSTS:
        logger.info(f"Daily limit reached ({MAX_DAILY_POSTS} posts)")
        return
    
    if not bot or not TELEGRAM_CHANNEL_ID:
        logger.error("Bot or channel ID not configured")
        return
    
    try:
        # Select random topic
        topic = random.choice(POST_TOPICS)
        logger.info(f"Generating post for topic: {topic}")
        
        # Generate text content
        text_content = generate_text_content(topic)
        if not text_content:
            text_content = f"🤖 {topic}\n\nSun'iy intellekt sohasidagi eng so'nggi yangiliklarni kuzatib boring!\n\n#AI #SuniyIntellekt #Texnologiya"
        
        # Try to generate image with Gemini
        image_data = generate_image_with_gemini(topic)
        
        # If Gemini fails, create text image with PIL
        if not image_data:
            logger.info("Gemini image generation failed, using PIL fallback")
            image_data = create_text_image(text_content[:200], topic)
        
        if not image_data:
            logger.error("Failed to create any image")
            return
        
        # Save image to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            temp_file.write(image_data)
            temp_file_path = temp_file.name
        
        # Send to channel
        try:
            with open(temp_file_path, 'rb') as image_file:
                bot.send_photo(
                    chat_id=TELEGRAM_CHANNEL_ID,
                    photo=image_file,
                    caption=text_content,
                    parse_mode='HTML'
                )
            
            daily_post_count += 1
            logger.info(f"Post {daily_post_count}/{MAX_DAILY_POSTS} sent successfully to channel")
            
        except TelegramError as e:
            logger.error(f"Failed to send post to channel: {e}")
        
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass
                
    except Exception as e:
        logger.error(f"Error in send_post_to_channel: {e}")

def reset_daily_counter():
    """Reset daily post counter at midnight"""
    global daily_post_count
    daily_post_count = 0
    logger.info("Daily post counter reset")

def setup_schedule():
    """Setup posting schedule - every 42 minutes between 07:00-21:00 UTC"""
    # Reset counter daily at midnight
    schedule.every().day.at("00:00").do(reset_daily_counter)
    
    # Schedule posts every 42 minutes during working hours (07:00-21:00 UTC)
    # This gives us approximately 20 posts per day
    start_hour = 7
    end_hour = 21
    interval_minutes = 42
    
    current_hour = start_hour
    current_minute = 0
    
    while current_hour < end_hour:
        time_str = f"{current_hour:02d}:{current_minute:02d}"
        schedule.every().day.at(time_str).do(send_post_to_channel)
        logger.info(f"Scheduled post at {time_str} UTC")
        
        # Add interval
        current_minute += interval_minutes
        if current_minute >= 60:
            current_hour += current_minute // 60
            current_minute = current_minute % 60
    
    logger.info(f"Scheduled {len(schedule.jobs)-1} daily posts between {start_hour:02d}:00-{end_hour:02d}:00 UTC")

def run_scheduler():
    """Run the scheduler in background thread"""
    while True:
        schedule.run_pending()
        time.sleep(60)

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "alive"})

@app.route('/test', methods=['GET'])
def test_post():
    """Test endpoint to manually trigger a post"""
    try:
        send_post_to_channel()
        return jsonify({"status": "test post sent", "posts_today": daily_post_count})
    except Exception as e:
        logger.error(f"Test post failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def main():
    """Main function"""
    print("🤖 AI Post Bot Render.com Web Service da ishga tushdi. 07:00-21:00 UTC oralig'ida 20 ta post jo'natiladi.")
    
    # Setup schedule
    setup_schedule()
    
    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Scheduler thread started")
    
    # Start Flask app
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()