import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
BOT_USERNAME = os.environ["BOT_USERNAME"]


async def domino(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    # Main Mini App direct link
    app_url = (
        f"https://t.me/{BOT_USERNAME}"
        f"?startapp=domino"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🀄 PLAY DOMINOES",
                url=app_url,
            )
        ]
    ])

    await update.message.reply_text(
        "🀄 DOMINOES\n\n"
        "👥 4 Players\n"
        "🎮 Group Multiplayer\n\n"
        "အောက်က PLAY DOMINOES ကိုနှိပ်ပြီး "
        "Game ထဲဝင်ပါ။\n\n"
        "ကိုယ့်အလှည့်ရောက်မှ "
        "Make your choice ပေါ်ပါမယ်။",
        reply_markup=keyboard,
    )


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    await update.message.reply_text(
        "🀄 DOMINOES\n\n"
        "Group ထဲမှာ /domino လို့ပို့ပြီး "
        "Game စနိုင်ပါတယ်။"
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    await update.message.reply_text(
        "🀄 DOMINOES HELP\n\n"
        "/domino - Game စရန်\n"
        "/start - Bot စရန်"
    )


def main():

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("domino", domino)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    print("DOMINOES BOT RUNNING")

    app.run_polling()


if __name__ == "__main__":
    main()
