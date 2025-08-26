import os
from dotenv import load_dotenv
import sys
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from playwright.async_api import async_playwright

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))


# === Attendance Marking Function ===
async def mark_attendance():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-notifications", "--disable-geolocation"]
            )
            context = await browser.new_context(
                permissions=["geolocation"]
            )
            await context.set_geolocation(
                {"latitude": 12.970179455028731, "longitude": 77.63868360859301}
            )
            page = await context.new_page()

            await page.goto("https://srv2.transerve.co.in:8092/Login?fg=false")

            # Fill login fields
            await page.fill("#txtdomain", "ACFPL")
            await page.fill("#txtEmail", "00179")
            await page.fill("#txtPassword", "ATDPT9442M")

            # Click login button
            await page.click("#btnLogin")

            # Wait for sign in button and click
            await page.wait_for_selector("#btnsignin", timeout=5000)
            await page.click("#btnsignin")

            await page.wait_for_timeout(3000)  # allow page load

            print("✅ Attendance marked successfully!")
            await browser.close()

        return True, "Attendance marked successfully ✅"

    except Exception as e:
        print(f"❌ Attendance marking failed: {e}")
        return False, f"❌ Attendance marking failed: {str(e)}"


# === Reminder Message ===
async def remind(context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("✅ Do it now", callback_data="do_it_now")],
        [InlineKeyboardButton("⏭ Skip for today", callback_data="skip_today")],
        [InlineKeyboardButton("⏰ Remind me later (After 1 Hour)", callback_data="remind_later")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text="⏰ Attendance Reminder:\nChoose an option:",
        reply_markup=reply_markup
    )

# === Handle Button Actions ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "do_it_now":
        success, message = await mark_attendance()
        if success:
            await query.edit_message_text(f"✅ {message}")
            await shutdown_after()
        else:
            await query.edit_message_text(f"⚠️ {message}")
            await context.bot.send_message(chat_id=CHAT_ID, text=f"⚠️ {message}")
            await shutdown_after()

    elif query.data == "skip_today":
        await query.edit_message_text("⏭ Skipped attendance for today.")
        await shutdown_after()

    elif query.data == "remind_later":
        await query.edit_message_text("⏰ Will remind you again in 1 hour.")
        context.job_queue.run_once(remind, when=3600)

async def shutdown_after(delay=0):
    if delay:
        await asyncio.sleep(delay)
    print("✅ Done. Shutting down container.")
    sys.exit(0)


# === Main ===
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CallbackQueryHandler(button_handler))

    # When triggered by GitHub Actions cron, send the reminder immediately
    app.job_queue.run_once(remind, when=0)

    # Start polling so it can listen for your reply on Telegram
    print("🤖 Bot running... Waiting for your instruction...")
    app.run_polling()

if __name__ == "__main__":
    main()





