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
from telegram.ext import Application, CommandHandler, ContextTypes
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
        "🎨 Welcome to the AI Image Generator Bot!\n\n"
        "I can create amazing images from your text descriptions using Google's Gemini AI.\n\n"
        "📝 How to use:\n"
        "• Send /imagine followed by your image description\n"
        "• Example: /imagine a beautiful sunset over mountains\n\n"
        "🚀 Start creating your images now!"
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
        # Note: Using Gemini 1.5 Flash model with image generation capability
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generate image using Google Gemini AI
        logger.info(f"Sending image generation request to Google Gemini AI")
        
        # Use asyncio executor to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: model.generate_content(
                f"Create an image of: {text_prompt}",
                generation_config=genai.GenerationConfig(
                    response_mime_type="image/png"
                )
            )
        )
        
        # Process the response and extract image data
        image_data = None
        image_saved = False
        
        # Check if the response contains candidates (generated content)
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
            logger.error(f"No image data found in Gemini response. Response structure: {[type(part).__name__ for part in candidate.content.parts] if candidate.content and candidate.content.parts else 'No parts'}")
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