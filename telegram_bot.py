#!/usr/bin/env python3
import logging
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
    url = "https://instagram-scraper-stable-api.p.rapidapi.com/get_ig_user_posts.php"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "instagram-scraper-stable-api.p.rapidapi.com",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "username_or_url": f"https://www.instagram.com/{username}/",
        "pagination_token": "",
        "amount": "12"
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=headers, data=data)

    if response.status_code != 200:
        raise Exception(f"API error: {response.status_code} - {response.text}")

    result = response.json()
    raise Exception(f"RAW RESPONSE: {str(result)[:500]}")

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
                is_video = post.get("media_type") == 2
                if is_video:
                    media_url = post.get("video_versions", [{}])[0].get("url")
                else:
                    media_url = post.get("image_versions2", {}).get("candidates", [{}])[0].get("url")

                if not media_url:
                    continue

                async with httpx.AsyncClient(timeout=60) as client:
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
        await status_msg.edit_text(f"❌ {str(e)}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username))
    logger.info("Instagram bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
