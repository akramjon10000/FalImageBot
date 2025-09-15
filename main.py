#!/usr/bin/env python3
"""
Telegram Image Generation Bot
Uses Fal.ai Stable Diffusion API to generate images from text prompts
"""

import os
import logging
import json
import asyncio
import aiohttp
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError
from typing import Optional

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

# Fal.ai API configuration - Updated to correct endpoint
FAL_AI_ENDPOINT = 'https://queue.fal.run/fal-ai/stable-diffusion-v15'
FAL_AI_HEADERS = {
    'Authorization': f'Key {FAL_AI_API_KEY}',
    'Content-Type': 'application/json'
}

async def poll_for_result(session: aiohttp.ClientSession, request_id: str, max_polls: int = 30) -> Optional[dict]:
    """
    Poll Fal.ai queue API for completion of queued request
    """
    status_endpoint = f'https://queue.fal.run/fal-ai/stable-diffusion-v15/requests/{request_id}/status'
    result_endpoint = f'https://queue.fal.run/fal-ai/stable-diffusion-v15/requests/{request_id}'
    
    for poll_count in range(max_polls):
        try:
            # Check status
            async with session.get(status_endpoint, headers=FAL_AI_HEADERS) as response:
                if response.status == 200:
                    status_data = await response.json()
                    status = status_data.get('status', '')
                    
                    if status == 'COMPLETED':
                        # Get the result
                        async with session.get(result_endpoint, headers=FAL_AI_HEADERS) as result_response:
                            if result_response.status == 200:
                                return await result_response.json()
                            else:
                                logger.error(f"Failed to get result: {result_response.status}")
                                return None
                    
                    elif status in ['FAILED', 'CANCELLED']:
                        logger.error(f"Request failed with status: {status}")
                        return None
                    
                    # Still in progress, wait and poll again
                    await asyncio.sleep(2)  # Wait 2 seconds between polls
                else:
                    logger.error(f"Status check failed: {response.status}")
                    await asyncio.sleep(2)
                    
        except Exception as e:
            logger.error(f"Error polling for result: {e}")
            await asyncio.sleep(2)
    
    # Max polls reached
    logger.error(f"Polling timeout after {max_polls} attempts")
    return None

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
    
    try:
        await update.message.reply_text(welcome_message)
        if update.effective_user:
            logger.info(f"User {update.effective_user.id} started the bot")
    except TelegramError as e:
        logger.error(f"Failed to send welcome message: {e}")

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
            try:
                await update.message.reply_text(error_message)
            except TelegramError as e:
                logger.error(f"Failed to send error message: {e}")
            return
        
        # Join all arguments to form the complete prompt
        text_prompt = ' '.join(context.args)
        
        # Check if prompt is empty after joining
        if not text_prompt.strip():
            error_message = "Iltimos, /generate buyrug'idan so'ng rasm uchun tavsif yozing."
            try:
                await update.message.reply_text(error_message)
            except TelegramError as e:
                logger.error(f"Failed to send error message: {e}")
            return
        
        if update.effective_user:
            logger.info(f"User {update.effective_user.id} requested image generation with prompt: {text_prompt}")
        
        # Send "generating" message to user
        generating_message = "Rasm yaratilmoqda, iltimos kuting..."
        try:
            status_message = await update.message.reply_text(generating_message)
        except TelegramError as e:
            logger.error(f"Failed to send status message: {e}")
            # Still continue with image generation
        
        # Prepare the API request payload
        payload = {
            "prompt": text_prompt,
            "image_size": "square_hd",
            "num_inference_steps": 25,  # Reduced from 50 for faster generation
            "guidance_scale": 7.5,
            "num_images": 1,
            "enable_safety_checker": True
        }
        
        # Use async HTTP request instead of blocking requests
        async with aiohttp.ClientSession() as session:
            async with session.post(
                FAL_AI_ENDPOINT,
                headers=FAL_AI_HEADERS,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                
                # Handle queue-based processing
                if response.status == 202:
                    # Request was queued, need to poll for result
                    response_data = await response.json()
                    request_id = response_data.get('request_id')
                    
                    if not request_id:
                        error_msg = "Fal.ai API xatosi: Request ID topilmadi"
                        if status_message:
                            try:
                                await status_message.edit_text(error_msg)
                            except TelegramError:
                                pass
                        logger.error("No request_id in 202 response")
                        return
                    
                    # Poll for completion
                    result = await poll_for_result(session, request_id)
                    if not result:
                        error_msg = "Rasm yaratish juda uzoq davom etdi. Iltimos qayta urinib ko'ring."
                        if status_message:
                            try:
                                await status_message.edit_text(error_msg)
                            except TelegramError:
                                pass
                        return
                    
                    response_data = result
                
                elif response.status == 200:
                    # Direct response (sync mode)
                    response_data = await response.json()
                
                else:
                    # Error response
                    error_text = await response.text()
                    error_msg = f"Xatolik yuz berdi. API javob kodi: {response.status}"
                    if status_message:
                        try:
                            await status_message.edit_text(error_msg)
                        except TelegramError:
                            pass
                    logger.error(f"Fal.ai API error: {response.status} - {error_text}")
                    return
        
        # Extract image URL from response
        if 'images' in response_data and len(response_data['images']) > 0:
            image_url = response_data['images'][0]['url']
            
            # Delete the "generating" message
            if status_message:
                try:
                    await status_message.delete()
                except TelegramError as e:
                    logger.warning(f"Could not delete status message: {e}")
            
            # Send the generated image to user
            try:
                await update.message.reply_photo(
                    photo=image_url,
                    caption=f"Yaratilgan rasm: \"{text_prompt}\""
                )
                
                if update.effective_user:
                    logger.info(f"Successfully generated and sent image for user {update.effective_user.id}")
            except TelegramError as e:
                error_msg = "Rasm yuborishda xatolik yuz berdi. Iltimos qayta urinib ko'ring."
                try:
                    await update.message.reply_text(error_msg)
                except TelegramError:
                    pass
                logger.error(f"Failed to send image: {e}")
        else:
            error_msg = "Rasm yaratishda xatolik yuz berdi. Iltimos qayta urinib ko'ring."
            if status_message:
                try:
                    await status_message.edit_text(error_msg)
                except TelegramError:
                    try:
                        await update.message.reply_text(error_msg)
                    except TelegramError:
                        pass
            logger.error(f"No image URL in Fal.ai response: {response_data}")
            
    except asyncio.TimeoutError:
        error_msg = "Rasm yaratish juda uzoq davom etdi. Iltimos qayta urinib ko'ring."
        if status_message:
            try:
                await status_message.edit_text(error_msg)
            except TelegramError:
                try:
                    await update.message.reply_text(error_msg)
                except TelegramError:
                    pass
        logger.error("Fal.ai API request timed out")
        
    except aiohttp.ClientError as e:
        error_msg = "Tarmoq xatosi yuz berdi. Iltimos qayta urinib ko'ring."
        if status_message:
            try:
                await status_message.edit_text(error_msg)
            except TelegramError:
                try:
                    await update.message.reply_text(error_msg)
                except TelegramError:
                    pass
        logger.error(f"Network error during Fal.ai API request: {e}")
        
    except json.JSONDecodeError as e:
        error_msg = "Javobni o'qishda xatolik yuz berdi. Iltimos qayta urinib ko'ring."
        if status_message:
            try:
                await status_message.edit_text(error_msg)
            except TelegramError:
                try:
                    await update.message.reply_text(error_msg)
                except TelegramError:
                    pass
        logger.error(f"JSON decode error from Fal.ai response: {e}")
        
    except Exception as e:
        error_msg = "Kutilmagan xatolik yuz berdi. Iltimos qayta urinib ko'ring."
        if status_message:
            try:
                await status_message.edit_text(error_msg)
            except TelegramError:
                try:
                    await update.message.reply_text(error_msg)
                except TelegramError:
                    pass
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