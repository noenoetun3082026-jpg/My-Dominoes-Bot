import os
import json
import random
import asyncio

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InlineQueryResultCachedSticker,
    InputTextMessageContent
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    InlineQueryHandler,
    MessageHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    filters,
    ContextTypes
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GROUPS_FILE = "groups.json"

game_session = {
    "active": False,
    "players": {},
    "player_order": [],
    "hands": {},
    "board": [],
    "stockpile": [],
    "current_turn": 0,
    "chat_id": None,
    "sticker_mapping": {}
}

def load_groups():
    if not os.path.exists(GROUPS_FILE):
        return {}

    try:
        with open(GROUPS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_groups():
    with open(GROUPS_FILE, "w", encoding="utf-8") as f:
        json.dump(
            GROUPS,
            f,
            ensure_ascii=False,
            indent=2
        )

GROUPS = load_groups()

def create_dominoes():
    dominoes = []

    for i in range(7):
        for j in range(i, 7):
            dominoes.append((i, j))

    return dominoes
    async def is_bot_admin(context, chat_id):
    try:
        me = await context.bot.get_me()
        member = await context.bot.get_chat_member(
            chat_id,
            me.id
        )
        return member.status == "administrator"
    except:
        return False


async def remember_group(chat, context):
    if chat.type not in ["group", "supergroup"]:
        return False

    if not await is_bot_admin(context, chat.id):
        return False

    GROUPS[str(chat.id)] = {
        "id": chat.id,
        "title": chat.title or "Unknown",
        "username": chat.username or ""
    }

    save_groups()

    print(
        "GROUP SAVED:",
        chat.title,
        chat.id
    )

    return True


async def bot_status_changed(update, context):
    if not update.my_chat_member:
        return

    chat = update.my_chat_member.chat

    if chat.type not in ["group", "supergroup"]:
        return

    status = update.my_chat_member.new_chat_member.status

    if status == "administrator":

        saved = await remember_group(
            chat,
            context
        )

        if saved:
            try:
                await context.bot.send_message(
                    chat.id,
                    "ဒီ GP ကို မှတ်ထားပါပြီ။"
                )
            except:
                pass

    elif status in ["left", "kicked"]:

        gid = str(chat.id)

        if gid in GROUPS:
            del GROUPS[gid]
            save_groups()


async def start(update, context):
    await remember_group(
        update.effective_chat,
        context
    )

    await update.message.reply_text(
        "မင်္ဂလာပါ!\n"
        "Dominoes Bot မှ ကြိုဆိုပါတယ်။\n\n"
        "/newgame - ဂိမ်းစရန်\n"
        "/groups - GP များကြည့်ရန်\n"
        "/broadcast စာ - GP အားလုံးကို ပို့ရန်"
    )


async def new_game(update, context):

    await remember_group(
        update.effective_chat,
        context
    )

    if game_session["active"]:
        await update.message.reply_text(
            "ဂိမ်းတစ်ခု ရှိနေပါပြီ။"
        )
        return

    game_session["active"] = True
    game_session["players"] = {}
    game_session["player_order"] = []
    game_session["hands"] = {}
    game_session["board"] = []
    game_session["stockpile"] = []
    game_session["current_turn"] = 0
    game_session["chat_id"] = (
        update.effective_chat.id
    )

    await update.message.reply_text(
        "Dominoes ဂိမ်းစပါပြီ!\n"
        "/join နဲ့ ဝင်ပါ။\n"
        "/startgame နဲ့ စပါ။"
)
    async def join_game(update, context):
    if not game_session["active"]:
        await update.message.reply_text(
            "ဂိမ်းမရှိသေးပါ။"
        )
        return

    user = update.effective_user

    if user.id in game_session["players"]:
        await update.message.reply_text(
            "ဝင်ထားပြီးသားပါ။"
        )
        return

    game_session["players"][user.id] = (
        user.first_name
    )

    game_session["player_order"].append(
        user.id
    )

    await update.message.reply_text(
        f"{user.first_name} ဝင်လာပါပြီ။"
    )


async def start_game(update, context):
    if not game_session["active"]:
        await update.message.reply_text(
            "ဂိမ်းမစရသေးပါ။"
        )
        return

    if not game_session["player_order"]:
        await update.message.reply_text(
            "ကစားသမားမရှိသေးပါ။"
        )
        return

    tiles = create_dominoes()
    random.shuffle(tiles)

    game_session["board"] = []
    game_session["current_turn"] = 0
    game_session["hands"] = {}

    players = game_session["player_order"]

    if len(players) * 7 > len(tiles):
        await update.message.reply_text(
            "ကစားသမားများလွန်းပါတယ်။"
        )
        return

    for uid in players:
        game_session["hands"][uid] = [
            tiles.pop()
            for _ in range(7)
        ]

    game_session["stockpile"] = tiles

    await update.message.reply_text(
        "Dominoes ဂိမ်း စပါပြီ!"
    )

    await send_turn_message(context)


async def send_turn_message(context):
    if not game_session["player_order"]:
        return

    index = game_session["current_turn"]
    uid = game_session["player_order"][index]
    name = game_session["players"][uid]

    keyboard = [
        [
            InlineKeyboardButton(
                "Make your choice!",
                switch_inline_query_current_chat=""
            )
        ],
        [
            InlineKeyboardButton(
                "Draw",
                callback_data="draw_tile"
            ),
            InlineKeyboardButton(
                "Pass",
                callback_data="pass_turn"
            )
        ]
    ]

    await context.bot.send_message(
        game_session["chat_id"],
        f"Next player: {name}",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


async def load_sticker_set(context):
    try:
        stickers = (
            await context.bot
            .get_sticker_set("DominoSO")
        ).stickers

        dominoes = create_dominoes()

        game_session["sticker_mapping"] = {}

        for i, domino in enumerate(dominoes):
            if i < len(stickers):
                game_session[
                    "sticker_mapping"
                ][domino] = stickers[i].file_id

    except Exception as e:
        print("STICKER ERROR:", e)
        async def inline_query(update, context):
    query = update.inline_query
    uid = query.from_user.id

    if not game_session["active"]:
        await query.answer([], cache_time=0)
        return

    if uid not in game_session["hands"]:
        await query.answer([], cache_time=0)
        return

    turn = game_session["current_turn"]

    if game_session["player_order"][turn] != uid:
        await query.answer([], cache_time=0)
        return

    results = []
    hand = game_session["hands"][uid]

    for i, tile in enumerate(hand):
        text = f"PLAY_{uid}_{i}"

        if tile in game_session["sticker_mapping"]:
            results.append(
                InlineQueryResultCachedSticker(
                    id=str(i),
                    sticker_file_id=game_session[
                        "sticker_mapping"
                    ][tile],
                    input_message_content=(
                        InputTextMessageContent(text)
                    )
                )
            )
        else:
            results.append(
                InlineQueryResultArticle(
                    id=str(i),
                    title=f"[{tile[0]}|{tile[1]}]",
                    input_message_content=(
                        InputTextMessageContent(text)
                    )
                )
            )

    await query.answer(
        results,
        cache_time=0
    )


async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()

    if not game_session["active"]:
        return

    uid = query.from_user.id
    turn = game_session["current_turn"]

    if game_session["player_order"][turn] != uid:
        return

    if query.data == "draw_tile":

        if game_session["stockpile"]:
            tile = game_session["stockpile"].pop()

            game_session["hands"][uid].append(tile)

            await context.bot.send_message(
                game_session["chat_id"],
                "Drawing 1 card"
            )

            await send_turn_message(context)

        else:
            await context.bot.send_message(
                game_session["chat_id"],
                "ဆွဲစရာအတုံး မကျန်တော့ပါ။"
            )

    elif query.data == "pass_turn":

        game_session["current_turn"] = (
            turn + 1
        ) % len(game_session["player_order"])

        await send_turn_message(context)


async def play_domino(update, context):
    if not game_session["active"]:
        return

    if not update.message:
        return

    text = update.message.text or ""

    if not text.startswith("PLAY_"):
        return

    try:
        parts = text.split("_")
        uid = int(parts[1])
        index = int(parts[2])
    except:
        return

    turn = game_session["current_turn"]

    if game_session["player_order"][turn] != uid:
        return

    hand = game_session["hands"][uid]

    if index >= len(hand):
        return

    tile = hand[index]
    board = game_session["board"]

    if not board:
        board.append(tile)
        hand.pop(index)

    else:
        left = board[0][0]
        right = board[-1][1]

        if tile[0] == left:
            board.insert(0, (tile[1], tile[0]))
            hand.pop(index)

        elif tile[1] == left:
            board.insert(0, tile)
            hand.pop(index)

        elif tile[0] == right:
            board.append(tile)
            hand.pop(index)

        elif tile[1] == right:
            board.append((tile[1], tile[0]))
            hand.pop(index)

        else:
            await update.message.reply_text(
                "ဒီအတုံးကို ချလို့မရပါ။"
            )
            return

    if tile in game_session["sticker_mapping"]:
        await context.bot.send_sticker(
            game_session["chat_id"],
            game_session["sticker_mapping"][tile]
        )

    if not hand:
        name = game_session["players"][uid]

        await update.message.reply_text(
            f"{name} အနိုင်ရပါပြီ!"
        )

        game_session["active"] = False
        return

    game_session["current_turn"] = (
        turn + 1
    ) % len(game_session["player_order"])

    await send_turn_message(context)


async def groups(update, context):
    if not GROUPS:
        await update.message.reply_text(
            "မှတ်ထားတဲ့ GP မရှိသေးပါ။"
        )
        return

    text = "မှတ်ထားတဲ့ GP များ\n\n"

    for i, group in enumerate(
        GROUPS.values(),
        1
    ):
        text += (
            f"{i}. {group['title']}\n"
            f"ID: {group['id']}\n\n"
        )

    await update.message.reply_text(text)


async def broadcast(update, context):
    if not context.args:
        await update.message.reply_text(
            "/broadcast စာ"
        )
        return

    msg = " ".join(context.args)

    ok = 0
    fail = 0

    for group in list(GROUPS.values()):
        try:
            await context.bot.send_message(
                group["id"],
                msg
            )
            ok += 1
            await asyncio.sleep(0.5)
        except:
            fail += 1

    await update.message.reply_text(
        f"ပို့ပြီးပါပြီ။\n"
        f"အောင်မြင်: {ok}\n"
        f"မအောင်မြင်: {fail}"
    )


def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN မရှိပါ။")
        return

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("newgame", new_game)
    )

    app.add_handler(
        CommandHandler("join", join_game)
    )

    app.add_handler(
        CommandHandler("startgame", start_game)
    )

    app.add_handler(
        CommandHandler("groups", groups)
    )

    app.add_handler(
        CommandHandler("broadcast", broadcast)
    )

    app.add_handler(
        ChatMemberHandler(
            bot_status_changed,
            ChatMemberHandler.MY_CHAT_MEMBER
        )
    )

    app.add_handler(
        InlineQueryHandler(inline_query)
    )

    app.add_handler(
        CallbackQueryHandler(handle_callback)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            play_domino
        )
    )

    print("Dominoes Bot Running...")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
