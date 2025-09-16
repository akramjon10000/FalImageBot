# Overview

This is a Telegram Image Generation Bot that integrates with Google's Gemini AI to generate images from text prompts. The bot receives text commands from Telegram users, processes them through Google's Generative AI service, and returns the generated images back to the users. The application is built as a Python-based asynchronous bot using the python-telegram-bot library with webhook support for web service deployment.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Framework
The application uses the python-telegram-bot library (version 22.4) to handle Telegram Bot API interactions. The bot is configured with command handlers that respond to user messages and process text prompts for image generation.

## Asynchronous Design
The system is built using Python's asyncio framework with aiohttp for handling HTTP requests. This allows the bot to handle multiple user requests concurrently without blocking operations, which is essential for managing the potentially long response times from AI image generation services.

## Image Generation Integration
The bot integrates with Google's Gemini 2.5 Flash Image Preview model:
- Direct API calls to Google Generative AI service
- Real-time image generation from text prompts
- Base64 image data processing and temporary file handling
- Built-in error handling for API rate limits and failures

## Configuration Management
Environment variables are used for sensitive configuration data:
- Telegram Bot Token for API authentication
- Google API Key for image generation service access
- Webhook URL and PORT configuration for web service deployment
- Auto-detection of deployment environment (Render vs local)

## Error Handling and Logging
The application implements comprehensive logging using Python's built-in logging module with INFO level logging for tracking bot operations, API calls, and error conditions. The system includes proper exception handling for both Telegram API errors and external service failures.

## Request Processing Flow
1. User sends a text command to the Telegram bot
2. Telegram sends webhook request to bot's HTTP server
3. Bot processes the message and extracts the prompt
4. Request is sent to Google Gemini AI for image generation
5. Generated image is processed and sent back to the user
6. All errors and operations are logged for monitoring

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
- **aiohttp**: Asynchronous HTTP server for webhook handling
- **logging**: Built-in Python logging framework
- **tempfile**: Temporary file handling for image processing
- **base64**: Image data encoding/decoding
- **os**: Environment variable access

# Recent Changes

## September 16, 2025 - Web Service Deployment Configuration
- **Deployment Strategy**: Converted bot from Background Worker to Web Service for Render free tier
- **Webhook Implementation**: Replaced polling with webhook for better resource efficiency
- **HTTP Server**: Added aiohttp server with health check endpoints (/, /health)
- **Port Configuration**: Configured to use PORT environment variable (default 5000)
- **render.yaml Update**: Changed from worker to web service type with free plan
- **Replit Workflow**: Removed local workflow to prevent webhook/polling conflicts
- **Status**: Bot runs exclusively on Render as web service, not on Replit

## Current Deployment Status
🚀 **ACTIVE DEPLOYMENT**: Render Web Service (Free Tier)
- **Service Type**: Web Service (not Background Worker)
- **Port**: 5000 (required by Render)
- **Health Checks**: GET / and GET /health endpoints
- **Webhook**: POST /webhook for Telegram updates

⚠️ **REPLIT STATUS**: Development environment only
- **No Active Workflow**: Bot does not run on Replit to avoid conflicts
- **Reason**: Telegram doesn't allow both polling and webhook simultaneously
- **Usage**: Code development and testing only

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