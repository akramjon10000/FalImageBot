#!/usr/bin/env python3
"""
Telegram Image Generation Bot
Uses Fal.ai Stable Diffusion API to generate images from text prompts
"""

import os
import logging
import json
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get API keys from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
FAL_AI_API_KEY = os.getenv('FAL_AI_API_KEY')

# Fal.ai API configuration
FAL_AI_ENDPOINT = 'https://fal.run/fal-ai/stable-diffusion-v2-1'
FAL_AI_HEADERS = {
    'Authorization': f'Key {FAL_AI_API_KEY}',
    'Content-Type': 'application/json'
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /start command - send welcome message in Uzbek
    """
    if not update.message:
        return
        
    welcome_message = (
        "Salom! Rasm yaratish uchun /generate buyrug'idan keyin o'z tavsifingizni yozing. "
        "Masalan: /generate an astronaut riding a horse on Mars"
    )
    await update.message.reply_text(welcome_message)
    
    if update.effective_user:
        logger.info(f"User {update.effective_user.id} started the bot")

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /generate command - generate image from text prompt using Fal.ai
    """
    if not update.message:
        return
        
    status_message = None
    
    try:
        # Extract the text prompt from the command
        if not context.args:
            error_message = "Iltimos, /generate buyrug'idan so'ng rasm uchun tavsif yozing."
            await update.message.reply_text(error_message)
            return
        
        # Join all arguments to form the complete prompt
        text_prompt = ' '.join(context.args)
        
        # Check if prompt is empty after joining
        if not text_prompt.strip():
            error_message = "Iltimos, /generate buyrug'idan so'ng rasm uchun tavsif yozing."
            await update.message.reply_text(error_message)
            return
        
        if update.effective_user:
            logger.info(f"User {update.effective_user.id} requested image generation with prompt: {text_prompt}")
        
        # Send "generating" message to user
        generating_message = "Rasm yaratilmoqda, iltimos kuting..."
        status_message = await update.message.reply_text(generating_message)
        
        # Prepare the API request payload
        payload = {
            "prompt": text_prompt,
            "image_size": "square_hd",
            "num_inference_steps": 50,
            "guidance_scale": 7.5,
            "num_images": 1,
            "enable_safety_checker": True
        }
        
        # Make API request to Fal.ai
        response = requests.post(
            FAL_AI_ENDPOINT,
            headers=FAL_AI_HEADERS,
            json=payload,
            timeout=120  # 2 minutes timeout
        )
        
        # Check if the request was successful
        if response.status_code != 200:
            error_msg = f"Xatolik yuz berdi. API javob kodi: {response.status_code}"
            await status_message.edit_text(error_msg)
            logger.error(f"Fal.ai API error: {response.status_code} - {response.text}")
            return
        
        # Parse the response
        response_data = response.json()
        
        # Extract image URL from response
        if 'images' in response_data and len(response_data['images']) > 0:
            image_url = response_data['images'][0]['url']
            
            # Delete the "generating" message
            await status_message.delete()
            
            # Send the generated image to user
            await update.message.reply_photo(
                photo=image_url,
                caption=f"Yaratilgan rasm: \"{text_prompt}\""
            )
            
            if update.effective_user:
                logger.info(f"Successfully generated and sent image for user {update.effective_user.id}")
            
        else:
            error_msg = "Rasm yaratishda xatolik yuz berdi. Iltimos qayta urinib ko'ring."
            await status_message.edit_text(error_msg)
            logger.error(f"No image URL in Fal.ai response: {response_data}")
            
    except requests.exceptions.Timeout:
        error_msg = "Rasm yaratish juda uzoq davom etdi. Iltimos qayta urinib ko'ring."
        if status_message:
            await status_message.edit_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        logger.error("Fal.ai API request timed out")
        
    except requests.exceptions.RequestException as e:
        error_msg = "Tarmoq xatosi yuz berdi. Iltimos qayta urinib ko'ring."
        if status_message:
            await status_message.edit_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        logger.error(f"Network error during Fal.ai API request: {e}")
        
    except json.JSONDecodeError as e:
        error_msg = "Javobni o'qishda xatolik yuz berdi. Iltimos qayta urinib ko'ring."
        if status_message:
            await status_message.edit_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        logger.error(f"JSON decode error from Fal.ai response: {e}")
        
    except Exception as e:
        error_msg = "Kutilmagan xatolik yuz berdi. Iltimos qayta urinib ko'ring."
        if status_message:
            await status_message.edit_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        logger.error(f"Unexpected error in generate_image: {e}")

def main() -> None:
    """
    Main function to start the Telegram bot
    """
    # Check if required API keys are available
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set in environment variables")
        print("Error: TELEGRAM_BOT_TOKEN environment variable is required")
        return
        
    if not FAL_AI_API_KEY:
        logger.error("FAL_AI_API_KEY is not set in environment variables")
        print("Error: FAL_AI_API_KEY environment variable is required")
        return
    
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("generate", generate_image))
    
    # Log that the bot is starting
    logger.info("Telegram Image Generation Bot is starting...")
    print("Bot is starting... Press Ctrl+C to stop.")
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()