#!/usr/bin/env python3
import logging
import os
import asyncio
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_BOT_TOKEN = "8721581325:AAFzOhC1izk6Px2-s_pgVWF2sIdi_8N-7TI"
RAPIDAPI_KEY = "150c7ebc5bmsh4eed288776c75a2p1dafa9jsnac52f1938a6a"
ADMIN_USER_ID = 8262267515

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_user_posts(username: str) -> list:
    url = "https://instagram-scraper-stable-api.p.rapidapi.com/ig_get_user_posts.php"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "instagram-scraper-stable-api.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    payload = {"username_or_url": f"https://www.instagram.com/{username}/"}

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"API error: {response.status_code}")

    data = response.json()
    if "error" in data:
        raise Exception(data["error"])

    return data.get("data", {}).get("user", {}).get("edge_owner_to_timeline_media", {}).get("edges", [])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 Instagram Post Puller\n\n"
        "Send me an Instagram username and I'll fetch all their posts!\n\n"
        "Example: cristiano"
    )

async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("⛔ Unauthorised.")
        return

    username = update.message.text.strip().replace("@", "")
    status_msg = await update.message.reply_text(f"🔍 Fetching posts from @{username}... please wait.")

    try:
        posts = await get_user_posts(username)

        if not posts:
            await status_msg.edit_text(f"❌ No posts found for @{username} or account is private.")
            return

        await status_msg.edit_text(f"📦 Found {len(posts)} posts! Sending now...")

        count = 0
        for post in posts:
            try:
                node = post.get("node", {})
                is_video = node.get("is_video", False)
                media_url = node.get("video_url") if is_video else node.get("display_url")

                if not media_url:
                    continue

                async with httpx.AsyncClient(timeout=30) as client:
                    media_response = await client.get(media_url)
                    media_bytes = media_response.content

                if is_video:
                    await update.message.reply_video(video=media_bytes)
                else:
                    await update.message.reply_photo(photo=media_bytes)

                count += 1
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error on post {count}: {e}")
                continue

        await update.message.reply_text(f"✅ Done! Sent {count} posts from @{username}")

    except Exception as e:
        logger.error(f"Error: {e}")
        await status_msg.edit_text(f"❌ Error: {str(e)}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username))
    logger.info("Instagram bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
