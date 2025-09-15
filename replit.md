# Overview

This is a Telegram Image Generation Bot that integrates with Fal.ai's Stable Diffusion API to generate images from text prompts. The bot receives text commands from Telegram users, processes them through Fal.ai's AI image generation service, and returns the generated images back to the users. The application is built as a Python-based asynchronous bot using the python-telegram-bot library.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Framework
The application uses the python-telegram-bot library (version 22.4) to handle Telegram Bot API interactions. The bot is configured with command handlers that respond to user messages and process text prompts for image generation.

## Asynchronous Design
The system is built using Python's asyncio framework with aiohttp for handling HTTP requests. This allows the bot to handle multiple user requests concurrently without blocking operations, which is essential for managing the potentially long response times from AI image generation services.

## Image Generation Integration
The bot integrates with Fal.ai's Stable Diffusion v1.5 API through a queue-based system:
- Requests are submitted to the Fal.ai queue endpoint
- The system polls for completion status using a dedicated polling mechanism
- Results are retrieved once generation is complete
- The polling system includes configurable retry limits to prevent infinite loops

## Configuration Management
Environment variables are used for sensitive configuration data:
- Telegram Bot Token for API authentication
- Fal.ai API Key for image generation service access
- Environment variables are loaded using python-dotenv for development convenience

## Error Handling and Logging
The application implements comprehensive logging using Python's built-in logging module with INFO level logging for tracking bot operations, API calls, and error conditions. The system includes proper exception handling for both Telegram API errors and external service failures.

## Request Processing Flow
1. User sends a text command to the Telegram bot
2. Bot receives the message and extracts the prompt
3. Request is submitted to Fal.ai's queue system
4. Bot polls the status endpoint until completion
5. Generated image is retrieved and sent back to the user
6. Errors are logged and appropriate responses are sent to users

# External Dependencies

## Telegram Bot API
- **Service**: Telegram Bot API
- **Purpose**: Core bot functionality and message handling
- **Library**: python-telegram-bot (v22.4)
- **Authentication**: Bot token via environment variable (TELEGRAM_BOT_TOKEN)
- **Setup**: Configured and working in Replit environment

## Google Generative AI (Gemini)
- **Service**: Google Gemini AI (Gemini 2.5 Flash Image Preview)
- **Purpose**: AI-powered image generation and editing from text prompts
- **Library**: google-generativeai (v0.8.5)
- **Authentication**: API key via environment variable (GOOGLE_API_KEY)
- **Setup**: Configured and working in Replit environment

## Python Runtime Dependencies
- **asyncio**: Built-in Python asynchronous programming support
- **logging**: Built-in Python logging framework
- **tempfile**: Temporary file handling for image processing
- **base64**: Image data encoding/decoding
- **os**: Environment variable access

# Recent Changes

## September 15, 2025 - Replit Environment Setup Complete
- **Project Import**: Successfully imported GitHub project to Replit environment
- **Dependencies**: Installed all required Python packages (google-generativeai, python-telegram-bot)
- **Environment Configuration**: Set up API keys (TELEGRAM_BOT_TOKEN, GOOGLE_API_KEY) via Replit Secrets
- **Workflow Setup**: Configured Bot workflow to run main.py continuously
- **Deployment**: Configured for VM deployment to maintain persistent bot operation
- **Conflict Handling**: Added improved error handling for Telegram bot conflicts
- **Status**: Setup complete but bot has conflict with another instance running elsewhere

## Critical Issue: Bot Token Conflict
⚠️ **IMPORTANT**: The bot cannot run properly because another instance is using the same bot token (likely on Render based on render.yaml file).

**To fix this conflict, choose ONE of these options:**
1. **Rotate Bot Token**: 
   - Go to Telegram @BotFather
   - Send `/revoke` then `/token` to get a new token
   - Update only this Replit's TELEGRAM_BOT_TOKEN secret with the new token
   
2. **Stop Other Deployments**:
   - Check Render dashboard and stop/suspend the telegram-image-bot service
   - Remove TELEGRAM_BOT_TOKEN from other environments
   
**Until resolved**: The bot will show conflict errors and cannot serve users reliably.

## Previous - Channel Posting System Complete
- **Channel Posting Feature**: Added automated daily posting system with AI-generated images and educational content
- **Content Database**: Created 10 comprehensive Nano Banana (Google Gemini AI) tips and tricks with practical examples
- **Scheduling System**: Implemented JobQueue-based posting at 9:00 AM, 2:00 PM, and 6:00 PM Tashkent time (UTC+5)
- **Admin Commands**: Added /channel_post and /set_channel commands for manual control (admin-only)
- **Render Deployment**: Complete deployment configuration with render.yaml, requirements.txt, and documentation
- **Environment Variables**: Added TELEGRAM_CHANNEL_ID, ADMIN_USER_IDS, BOT_USERNAME for channel functionality
- **Format Improvements**: HTML formatting for better message display, proper timezone handling
- **Security**: Admin commands protected with user ID validation, channel validation before posting

## Previous Changes  
- Successfully imported GitHub project to Replit environment
- Fixed dependency installation issues with python-telegram-bot
- Configured API keys (TELEGRAM_BOT_TOKEN and GOOGLE_API_KEY) via Replit Secrets
- Verified bot functionality - successfully starts and connects to both Telegram and Google AI APIs
- Bot workflow is running and ready to receive user commands