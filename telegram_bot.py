#!/usr/bin/env python3
import logging
import os
import asyncio
import instaloader
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_BOT_TOKEN = "8721581325:AAFzOhC1izk6Px2-s_pgVWF2sIdi_8N-7TI"
ADMIN_USER_ID = 8633029909

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

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
    await update.message.reply_text(f"🔍 Fetching posts from @{username}... please wait.")

    download_path = Path(f"downloads/{username}")
    download_path.mkdir(parents=True, exist_ok=True)

    try:
        L = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            post_metadata_txt_pattern=""
        )

        profile = instaloader.Profile.from_username(L.context, username)
        posts = list(profile.get_posts())

        if not posts:
            await update.message.reply_text(f"❌ No posts found for @{username}")
            return

        await update.message.reply_text(f"📦 Found {len(posts)} posts! Sending now...")

        count = 0
        for post in posts:
            try:
                L.download_post(post, target=download_path)

                for file in sorted(download_path.iterdir()):
                    if file.suffix in [".jpg", ".jpeg", ".png"]:
                        with open(file, "rb") as f:
                            await update.message.reply_photo(photo=f)
                        file.unlink()
                    elif file.suffix in [".mp4", ".mov"]:
                        with open(file, "rb") as f:
                            await update.message.reply_video(video=f)
                        file.unlink()

                count += 1
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Error on post {count}: {e}")
                continue

        await update.message.reply_text(f"✅ Done! Sent {count} posts from @{username}")

    except instaloader.exceptions.ProfileNotExistsException:
        await update.message.reply_text(f"❌ Account @{username} not found or is private.")
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username))
    logger.info("Instagram bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()

