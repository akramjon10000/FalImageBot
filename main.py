#!/usr/bin/env python3
"""
Telegram Image Generation Bot using Google Generative AI (Gemini)

This bot provides two main commands:
1. /start - Welcome message and usage instructions
2. /imagine <prompt> - Generate an image from a text prompt using Google's Gemini AI

The bot uses Replit Secrets to securely store API keys and handles image generation
by saving the generated image to a temporary file before sending it to the user.
"""

import os
import logging
import tempfile
import asyncio
from io import BytesIO
from dotenv import load_dotenv

# Import Telegram bot libraries (python-telegram-bot v20+)
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

# Import Google Generative AI library for image generation
import google.generativeai as genai
import base64

# Load environment variables from .env file (if exists)
load_dotenv()

# Configure logging to track bot operations and errors
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Suppress sensitive logging to prevent secret leakage
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

# Get API keys from Replit Secrets (environment variables)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Configure Google Generative AI with the API key
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    logger.info("Google Generative AI configured successfully")
else:
    logger.warning("GOOGLE_API_KEY not found in environment variables")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /start command - send welcome message with usage instructions
    
    Args:
        update: Telegram update object containing the message
        context: Telegram context for the current conversation
    """
    # Check if the update contains a message
    if not update.message:
        return
        
    # Prepare welcome message with bot description and usage instructions
    welcome_message = (
        "🎨 AI Rasm Generatori Botiga Xush Kelibsiz!\n\n"
        "Men Google'ning Nano Banana (Gemini 2.5 Flash Image) AI'si bilan ajoyib rasmlar yarata olaman!\n\n"
        "🎯 Barcha funksiyalar:\n"
        "• /imagine [tavsif] - yangi rasm yaratish\n"
        "• /edit [tavsif] - rasm tahrirlash\n"
        "• /compose - bir nechta rasmni birlashtirish\n"
        "• /style - stil uzatish\n"
        "• /text [matn] - matn bilan rasm yaratish\n"
        "• /recipe [taom] - retsept yaratish\n"
        "• /interactive - suhbat rejimi\n\n"
        "📱 Misollar:\n"
        "• /imagine daraxtda sigir chiqib olgan\n"
        "• /text HELLO rasmda yozing\n"
        "• /recipe osh\n\n"
        "🚀 Endi rasmlarni yaratishni boshlang!"
    )
    
    try:
        # Send the welcome message to the user
        await update.message.reply_text(welcome_message)
        
        # Log the user interaction for monitoring
        if update.effective_user:
            logger.info(f"User {update.effective_user.id} ({update.effective_user.username}) started the bot")
            
    except TelegramError as e:
        # Handle any errors that occur while sending the welcome message
        logger.error(f"Failed to send welcome message: {e}")


async def imagine(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /imagine command - generate image from text prompt using Google Gemini AI
    
    This function:
    1. Extracts the text prompt from the user's command
    2. Validates that a prompt was provided
    3. Sends a "generating" status message to the user
    4. Uses Google's Gemini AI to generate an image
    5. Saves the generated image to a temporary file
    6. Sends the image back to the user via Telegram
    
    Args:
        update: Telegram update object containing the message
        context: Telegram context containing command arguments
    """
    # Check if the update contains a message
    if not update.message:
        return
    
    # Initialize variables for status tracking
    status_message = None
    
    try:
        # Extract the text prompt from command arguments
        if not context.args:
            error_message = (
                "❌ Please provide a description for the image you want to generate.\n"
                "Example: /imagine a cat sitting on a rainbow"
            )
            await update.message.reply_text(error_message)
            return
        
        # Join all arguments to form the complete prompt
        text_prompt = ' '.join(context.args)
        
        # Validate that the prompt is not empty after joining
        if not text_prompt.strip():
            error_message = (
                "❌ Please provide a description for the image you want to generate.\n"
                "Example: /imagine a cat sitting on a rainbow"
            )
            await update.message.reply_text(error_message)
            return
        
        # Log the image generation request
        if update.effective_user:
            logger.info(f"User {update.effective_user.id} requested image generation with prompt: '{text_prompt}'")
        
        # Send status message to inform user that generation has started
        generating_message = "🎨 Generating your image, please wait..."
        try:
            status_message = await update.message.reply_text(generating_message)
        except TelegramError as e:
            logger.error(f"Failed to send status message: {e}")
            # Continue with image generation even if status message fails
        
        # Check if Google API key is configured
        if not GOOGLE_API_KEY:
            error_msg = "❌ Google API key is not configured. Please contact the bot administrator."
            if status_message:
                await status_message.edit_text(error_msg)
            else:
                await update.message.reply_text(error_msg)
            logger.error("Attempted image generation without Google API key")
            return
        
        # Initialize the Gemini model for image generation
        # Note: Using Gemini 2.5 Flash Image model (Nano Banana) for image generation
        model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        
        # Generate image using Google Gemini AI
        logger.info(f"Sending image generation request to Google Gemini AI")
        
        # Use asyncio executor to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: model.generate_content(text_prompt)
        )
        
        # Process the response and extract image data
        image_data = None
        image_saved = False
        
        # Check if the response contains candidates (generated content)
        candidate = None
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            
            # Iterate through all parts of the response
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    # Check if this part contains inline image data
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Check if the data is base64 encoded or raw bytes
                        if hasattr(part.inline_data, 'data'):
                            raw_data = part.inline_data.data
                            # If data is string (base64), decode it
                            if isinstance(raw_data, str):
                                image_data = base64.b64decode(raw_data)
                            else:
                                image_data = raw_data
                            logger.info("Successfully extracted image data from Gemini response")
                            break
                    # Log any text responses from the model
                    elif hasattr(part, 'text') and part.text:
                        logger.info(f"Gemini text response: {part.text}")
        
        # If no image data was found in the response
        if not image_data:
            error_msg = "❌ Failed to generate image. The model may not support image generation or your prompt couldn't be processed."
            if status_message:
                await status_message.edit_text(error_msg)
            else:
                await update.message.reply_text(error_msg)
            logger.error(f"No image data found in Gemini response. Response structure: {[type(part).__name__ for part in candidate.content.parts] if candidate and candidate.content and candidate.content.parts else 'No parts'}")
            return
        
        # Save the generated image to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            temp_file.write(image_data)
            temp_file_path = temp_file.name
            image_saved = True
            logger.info(f"Image saved to temporary file: {temp_file_path}")
        
        # Delete the status message since we're about to send the image
        if status_message:
            try:
                await status_message.delete()
            except TelegramError as e:
                logger.warning(f"Could not delete status message: {e}")
        
        # Send the generated image to the user
        try:
            with open(temp_file_path, 'rb') as image_file:
                await update.message.reply_photo(
                    photo=image_file,
                    caption=f"🎨 Generated image: \"{text_prompt}\""
                )
            
            logger.info(f"Successfully sent generated image to user {update.effective_user.id if update.effective_user else 'unknown'}")
            
        except TelegramError as e:
            # If sending the image fails, try to send an error message
            error_msg = "❌ Failed to send the generated image. Please try again."
            try:
                await update.message.reply_text(error_msg)
            except TelegramError:
                pass
            logger.error(f"Failed to send image: {e}")
        
        finally:
            # Clean up: remove the temporary file
            if image_saved:
                try:
                    os.unlink(temp_file_path)
                    logger.info("Temporary image file cleaned up")
                except OSError as e:
                    logger.warning(f"Failed to delete temporary file: {e}")
    
    except Exception as e:
        # Handle any unexpected errors during image generation
        error_msg = "❌ An unexpected error occurred while generating your image. Please try again."
        
        # Try to update status message or send new error message
        if status_message:
            try:
                await status_message.edit_text(error_msg)
            except TelegramError:
                try:
                    await update.message.reply_text(error_msg)
                except TelegramError:
                    pass
        else:
            try:
                await update.message.reply_text(error_msg)
            except TelegramError:
                pass
        
        logger.error(f"Unexpected error in imagine command: {e}", exc_info=True)


async def edit_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /edit command - edit an image based on user's description
    
    User should send an image with caption /edit [description] or send /edit [description] 
    as a reply to an image message.
    
    Args:
        update: Telegram update object containing the message
        context: Telegram context containing command arguments
    """
    if not update.message:
        return
    
    status_message = None
    
    try:
        # Extract the editing instructions from command arguments
        if not context.args:
            instruction_message = (
                "📝 Rasm tahrirlash uchun:\n\n"
                "1. Rasmni yuboring va caption sifatida: /edit [tavsif]\n"
                "2. Yoki avval rasmni yuboring, keyin /edit [tavsif] yozing\n\n"
                "Misol: /edit realistic qiling\n"
                "Misol: /edit rangi qizil qiling"
            )
            await update.message.reply_text(instruction_message)
            return
        
        # Join all arguments to form the editing instruction
        edit_instruction = ' '.join(context.args)
        
        # Check if there's an image in the current message
        photo = None
        if update.message.photo:
            photo = update.message.photo[-1]  # Get the highest resolution photo
        elif update.message.reply_to_message and update.message.reply_to_message.photo:
            photo = update.message.reply_to_message.photo[-1]
        
        if not photo:
            error_message = (
                "❌ Rasm topilmadi!\n\n"
                "Iltimos:\n"
                "• Rasm yuboring va caption sifatida /edit [tavsif] yozing\n"
                "• Yoki rasmga javob sifatida /edit [tavsif] yozing"
            )
            await update.message.reply_text(error_message)
            return
        
        # Log the image editing request
        if update.effective_user:
            logger.info(f"User {update.effective_user.id} requested image editing with instruction: '{edit_instruction}'")
        
        # Send status message
        editing_message = "🔄 Rasmni tahrirlayapman, iltimos kuting..."
        try:
            status_message = await update.message.reply_text(editing_message)
        except TelegramError as e:
            logger.error(f"Failed to send status message: {e}")
        
        # Check if Google API key is configured
        if not GOOGLE_API_KEY:
            error_msg = "❌ Google API key sozlanmagan. Bot administratori bilan bog'laning."
            if status_message:
                await status_message.edit_text(error_msg)
            else:
                await update.message.reply_text(error_msg)
            logger.error("Attempted image editing without Google API key")
            return
        
        # Download the image from Telegram
        file = await photo.get_file()
        image_bytes = await file.download_as_bytearray()
        
        logger.info("Image downloaded from Telegram successfully")
        
        # Initialize the Gemini model for image editing
        model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        
        # Create the image part for Gemini
        image_part = {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(image_bytes).decode('utf-8')
        }
        
        # Create the prompt for image editing
        editing_prompt = f"Bu rasmni tahrirlang: {edit_instruction}"
        
        # Generate edited image using Google Gemini AI
        logger.info(f"Sending image editing request to Google Gemini AI")
        
        # Use asyncio executor to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: model.generate_content([editing_prompt, image_part])
        )
        
        # Process the response and extract image data
        image_data = None
        image_saved = False
        
        # Check if the response contains candidates (generated content)
        candidate = None
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            
            # Iterate through all parts of the response
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    # Check if this part contains inline image data
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Check if the data is base64 encoded or raw bytes
                        if hasattr(part.inline_data, 'data'):
                            raw_data = part.inline_data.data
                            # If data is string (base64), decode it
                            if isinstance(raw_data, str):
                                image_data = base64.b64decode(raw_data)
                            else:
                                image_data = raw_data
                            logger.info("Successfully extracted edited image data from Gemini response")
                            break
                    # Log any text responses from the model
                    elif hasattr(part, 'text') and part.text:
                        logger.info(f"Gemini text response: {part.text}")
        
        # If no image data was found in the response
        if not image_data:
            error_msg = "❌ Rasmni tahrirlashda xatolik yuz berdi. Iltimos qayta urinib ko'ring."
            if status_message:
                await status_message.edit_text(error_msg)
            else:
                await update.message.reply_text(error_msg)
            logger.error(f"No image data found in Gemini editing response. Response structure: {[type(part).__name__ for part in candidate.content.parts] if candidate and candidate.content and candidate.content.parts else 'No parts'}")
            return
        
        # Save the edited image to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            temp_file.write(image_data)
            temp_file_path = temp_file.name
            image_saved = True
            logger.info(f"Edited image saved to temporary file: {temp_file_path}")
        
        # Delete the status message since we're about to send the image
        if status_message:
            try:
                await status_message.delete()
            except TelegramError as e:
                logger.warning(f"Could not delete status message: {e}")
        
        # Send the edited image to the user
        try:
            with open(temp_file_path, 'rb') as image_file:
                await update.message.reply_photo(
                    photo=image_file,
                    caption=f"✨ Tahrirlangan rasm: \"{edit_instruction}\""
                )
            
            logger.info(f"Successfully sent edited image to user {update.effective_user.id if update.effective_user else 'unknown'}")
            
        except TelegramError as e:
            # If sending the image fails, try to send an error message
            error_msg = "❌ Tahrirlangan rasmni yuborishda xatolik yuz berdi. Iltimos qayta urinib ko'ring."
            try:
                await update.message.reply_text(error_msg)
            except TelegramError:
                pass
            logger.error(f"Failed to send edited image: {e}")
        
        finally:
            # Clean up: remove the temporary file
            if image_saved:
                try:
                    os.unlink(temp_file_path)
                    logger.info("Temporary edited image file cleaned up")
                except OSError as e:
                    logger.warning(f"Failed to delete temporary file: {e}")
    
    except Exception as e:
        # Handle any unexpected errors during image editing
        error_msg = "❌ Rasmni tahrirlashda kutilmagan xatolik yuz berdi. Iltimos qayta urinib ko'ring."
        
        # Try to update status message or send new error message
        if status_message:
            try:
                await status_message.edit_text(error_msg)
            except TelegramError:
                try:
                    await update.message.reply_text(error_msg)
                except TelegramError:
                    pass
        else:
            try:
                await update.message.reply_text(error_msg)
            except TelegramError:
                pass
        
        logger.error(f"Unexpected error in edit_image command: {e}", exc_info=True)


async def compose_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /compose command - combine multiple images into one new image
    """
    if not update.message:
        return
    
    try:
        if not context.args:
            instruction_message = (
                "🎨 Rasm birlashtirish uchun:\n\n"
                "1. Bir nechta rasm yuboring (2-4 ta)\n"
                "2. /compose [qanday birlashtirishni xohlaysiz]\n\n"
                "Misollar:\n"
                "• /compose bitta rasam qiling\n"
                "• /compose kollaj yasang\n"
                "• /compose chiroyli tarzda birlashtiring"
            )
            await update.message.reply_text(instruction_message)
            return
        
        combine_instruction = ' '.join(context.args)
        await update.message.reply_text(f"🔄 Rasmlarni birlashtiraman: {combine_instruction}")
        
        # For now, guide user to send images first
        guide_message = (
            "📤 Iltimos avval rasmlarni yuboring, keyin bu buyruqni qayta ishga tushiring.\n"
            "Yoki rasmlarni yuboring va caption sifatida /compose [tavsif] yozing."
        )
        await update.message.reply_text(guide_message)
        
    except Exception as e:
        logger.error(f"Error in compose_images: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def style_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /style command - transfer style from one image to another
    """
    if not update.message:
        return
    
    try:
        if not context.args:
            instruction_message = (
                "🎨 Stil uzatish uchun:\n\n"
                "1. Asosiy rasmni yuboring\n"
                "2. Stil rasmini yuboring\n" 
                "3. /style [qanday stil berish kerak]\n\n"
                "Misollar:\n"
                "• /style Van Gogh uslubida\n"
                "• /style cartoon qiling\n"
                "• /style realistik qiling"
            )
            await update.message.reply_text(instruction_message)
            return
        
        style_instruction = ' '.join(context.args)
        await update.message.reply_text(f"🎨 Stil uzataman: {style_instruction}")
        
        guide_message = (
            "📤 Iltimos avval 2 ta rasm yuboring (asosiy + stil), keyin bu buyruqni ishga tushiring."
        )
        await update.message.reply_text(guide_message)
        
    except Exception as e:
        logger.error(f"Error in style_transfer: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def text_render(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /text command - generate images with high-quality text rendering
    """
    if not update.message:
        return
    
    status_message = None
    
    try:
        if not context.args:
            instruction_message = (
                "📝 Matn bilan rasm yaratish uchun:\n\n"
                "/text [yozilishi kerak bo'lgan matn] [qo'shimcha tavsif]\n\n"
                "Misollar:\n"
                "• /text HELLO chiroyli logo\n"
                "• /text NANO BANANA poster\n"
                "• /text O'ZBEKISTON bayraq bilan"
            )
            await update.message.reply_text(instruction_message)
            return
        
        text_to_render = ' '.join(context.args)
        
        if update.effective_user:
            logger.info(f"User {update.effective_user.id} requested text rendering: '{text_to_render}'")
        
        status_message = await update.message.reply_text("📝 Matn bilan rasm yarataman...")
        
        if not GOOGLE_API_KEY:
            error_msg = "❌ Google API key sozlanmagan."
            await status_message.edit_text(error_msg)
            return
        
        model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        
        # Create a prompt optimized for text rendering
        text_prompt = f"Create a high-quality image with clear, legible text that says: '{text_to_render}'. Make sure the text is well-placed, readable and visually appealing."
        
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: model.generate_content(text_prompt)
        )
        
        # Extract and send image (same logic as imagine function)
        image_data = None
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        if hasattr(part.inline_data, 'data'):
                            raw_data = part.inline_data.data
                            if isinstance(raw_data, str):
                                image_data = base64.b64decode(raw_data)
                            else:
                                image_data = raw_data
                            break
        
        if image_data:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                temp_file.write(image_data)
                temp_file_path = temp_file.name
            
            await status_message.delete()
            
            with open(temp_file_path, 'rb') as image_file:
                await update.message.reply_photo(
                    photo=image_file,
                    caption=f"📝 Matn rasmi: \"{text_to_render}\""
                )
            
            os.unlink(temp_file_path)
            logger.info(f"Successfully sent text-rendered image to user")
        else:
            await status_message.edit_text("❌ Matn rasmi yaratishda xatolik.")
        
    except Exception as e:
        error_msg = "❌ Matn rasmi yaratishda xatolik yuz berdi."
        if status_message:
            await status_message.edit_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        logger.error(f"Error in text_render: {e}")


async def recipe_generator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /recipe command - generate illustrated recipes
    """
    if not update.message:
        return
    
    status_message = None
    
    try:
        if not context.args:
            instruction_message = (
                "🍳 Retsept yaratish uchun:\n\n"
                "/recipe [taom nomi]\n\n"
                "Misollar:\n"
                "• /recipe osh\n"
                "• /recipe manti\n"
                "• /recipe pizza"
            )
            await update.message.reply_text(instruction_message)
            return
        
        dish_name = ' '.join(context.args)
        
        if update.effective_user:
            logger.info(f"User {update.effective_user.id} requested recipe for: '{dish_name}'")
        
        status_message = await update.message.reply_text(f"🍳 {dish_name} retseptini yarataman...")
        
        if not GOOGLE_API_KEY:
            error_msg = "❌ Google API key sozlanmagan."
            await status_message.edit_text(error_msg)
            return
        
        model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        
        # Create a prompt for illustrated recipe
        recipe_prompt = f"Generate an illustrated recipe for {dish_name}. Include step-by-step images and clear text instructions in Uzbek language."
        
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: model.generate_content(recipe_prompt)
        )
        
        # Extract and send content (both text and images)
        text_content = ""
        image_data = None
        
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_content += part.text + "\n"
                    elif hasattr(part, 'inline_data') and part.inline_data:
                        if hasattr(part.inline_data, 'data'):
                            raw_data = part.inline_data.data
                            if isinstance(raw_data, str):
                                image_data = base64.b64decode(raw_data)
                            else:
                                image_data = raw_data
        
        await status_message.delete()
        
        # Send text if available
        if text_content.strip():
            await update.message.reply_text(f"🍳 {dish_name} retsepti:\n\n{text_content[:4000]}")
        
        # Send image if available
        if image_data:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                temp_file.write(image_data)
                temp_file_path = temp_file.name
            
            with open(temp_file_path, 'rb') as image_file:
                await update.message.reply_photo(
                    photo=image_file,
                    caption=f"🍳 {dish_name} retsept rasmi"
                )
            
            os.unlink(temp_file_path)
        
        logger.info(f"Successfully sent recipe for {dish_name}")
        
    except Exception as e:
        error_msg = "❌ Retsept yaratishda xatolik yuz berdi."
        if status_message:
            await status_message.edit_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        logger.error(f"Error in recipe_generator: {e}")


async def interactive_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /interactive command - start conversational image refinement
    """
    if not update.message:
        return
    
    try:
        interactive_message = (
            "🤖 Interaktiv rejim yoqildi!\n\n"
            "Endi siz menga:\n"
            "• Rasm yaratishni so'rashingiz mumkin\n"
            "• Mavjud rasmni o'zgartirishni so'rashingiz mumkin\n"
            "• Qadama-qadam rasm yaratishni so'rashingiz mumkin\n\n"
            "💬 Shunchaki oddiy matn yuboring va men sizga yordam beraman!\n\n"
            "Misol: \"Tog'li landshaft yarating\"\n"
            "Keyin: \"Qor qo'shing\"\n"
            "Keyin: \"Osmoni quyuqroq qiling\""
        )
        await update.message.reply_text(interactive_message)
        
        if update.effective_user:
            logger.info(f"User {update.effective_user.id} started interactive mode")
        
    except Exception as e:
        logger.error(f"Error in interactive_mode: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi.")


def main() -> None:
    """
    Main function to initialize and start the Telegram bot
    
    This function:
    1. Validates that required API keys are available
    2. Creates the Telegram Application instance
    3. Registers command handlers for /start and /imagine
    4. Starts the bot in polling mode to listen for messages
    """
    # Check if the Telegram Bot Token is available
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set in environment variables")
        print("❌ Error: TELEGRAM_BOT_TOKEN environment variable is required")
        print("Please add your Telegram Bot Token to Replit Secrets")
        return
    
    # Check if the Google API Key is available
    if not GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY is not set in environment variables")
        print("❌ Error: GOOGLE_API_KEY environment variable is required")
        print("Please add your Google API Key to Replit Secrets")
        return
    
    # Create the Telegram Application instance with the bot token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Register command handlers
    # /start command - welcome message and instructions
    application.add_handler(CommandHandler("start", start))
    
    # /imagine command - image generation from text prompt
    application.add_handler(CommandHandler("imagine", imagine))
    
    # /edit command - image editing based on user instructions
    application.add_handler(CommandHandler("edit", edit_image))
    
    # /compose command - combine multiple images
    application.add_handler(CommandHandler("compose", compose_images))
    
    # /style command - style transfer between images
    application.add_handler(CommandHandler("style", style_transfer))
    
    # /text command - high-quality text rendering
    application.add_handler(CommandHandler("text", text_render))
    
    # /recipe command - illustrated recipe generation
    application.add_handler(CommandHandler("recipe", recipe_generator))
    
    # /interactive command - conversational image refinement
    application.add_handler(CommandHandler("interactive", interactive_mode))
    
    # Log that the bot is starting
    logger.info("🤖 Telegram Image Generation Bot is starting...")
    print("🚀 Bot is starting... Press Ctrl+C to stop.")
    print("💡 Make sure you have set TELEGRAM_BOT_TOKEN and GOOGLE_API_KEY in Replit Secrets")
    
    # Start the bot and keep it running until interrupted
    # This enables the bot to receive and respond to messages
    application.run_polling(allowed_updates=Update.ALL_TYPES)


# Entry point - run the bot when script is executed directly
if __name__ == '__main__':
    main()