import os
import asyncio
import json
import random
import hashlib
import hmac

from aiohttp import web
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBAPP_URL = os.environ["WEBAPP_URL"]
PORT = int(os.environ.get("PORT", "8080"))

games = {}


def make_dominoes():
    return [[a, b] for a in range(7) for b in range(a, 7)]


def new_game(chat_id):
    tiles = make_dominoes()
    random.shuffle(tiles)

    return {
        "chat_id": chat_id,
        "players": {},
        "hands": {},
        "board": [],
        "turn": None,
        "started": False,
    }


def valid_move(tile, board):
    if not board:
        return True

    left = board[0][0]
    right = board[-1][1]

    a, b = tile

    return (
        a in (left, right)
        or b in (left, right)
    )


def play_tile(game, user_id, index, side):
    hand = game["hands"].get(str(user_id), [])

    if index < 0 or index >= len(hand):
        return False, "Invalid tile"

    tile = hand[index]

    if not valid_move(tile, game["board"]):
        return False, "ဒီအတုံးကို ချလို့မရပါ"

    a, b = tile

    if not game["board"]:
        game["board"].append([a, b])

    elif side == "left":
        target = game["board"][0][0]

        if b == target:
            tile = [a, b]
        elif a == target:
            tile = [b, a]
        else:
            return False, "ဘယ်ဘက်မှာ ချလို့မရပါ"

        game["board"].insert(0, tile)

    elif side == "right":
        target = game["board"][-1][1]

        if a == target:
            tile = [a, b]
        elif b == target:
            tile = [b, a]
        else:
            return False, "ညာဘက်မှာ ချလို့မရပါ"

        game["board"].append(tile)

    else:
        return False, "Invalid side"

    hand.pop(index)

    player_ids = list(game["players"].keys())

    if not hand:
        game["started"] = False

    else:
        current = player_ids.index(str(user_id))
        next_index = (current + 1) % len(player_ids)
        game["turn"] = player_ids[next_index]

    return True, "OK"


def verify_init_data(init_data):
    try:
        data = dict(
            item.split("=", 1)
            for item in init_data.split("&")
            if "=" in item
        )

        received_hash = data.pop("hash", None)

        if not received_hash:
            return None

        check_string = "\n".join(
            f"{k}={data[k]}"
            for k in sorted(data)
        )

        secret_key = hmac.new(
            b"WebAppData",
            BOT_TOKEN.encode(),
            hashlib.sha256,
        ).digest()

        calculated = hmac.new(
            secret_key,
            check_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(calculated, received_hash):
            return None

        user = json.loads(data.get("user", "{}"))

        return user

    except Exception:
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🀄 PLAY DOMINOES",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]
    ])

    await update.message.reply_text(
        "🀄 DOMINOES\n\n"
        "4 Players\n"
        "UNO လို Web App UI\n\n"
        "ကိုယ့်အလှည့်ရောက်မှ\n"
        "Make your choice ကိုနှိပ်ပြီး\n"
        "ကိုယ့် Domino အတုံးတွေကို ကိုယ်ပဲမြင်ရပါမယ်။",
        reply_markup=keyboard,
    )


async def api_join(request):

    try:
        body = await request.json()

        chat_id = str(body["chat_id"])
        init_data = body.get("initData", "")

        user = verify_init_data(init_data)

        if not user:
            return web.json_response(
                {"error": "Invalid Telegram user"},
                status=403,
            )

        user_id = str(user["id"])
        name = user.get("first_name", "Player")

        if chat_id not in games:
            games[chat_id] = new_game(chat_id)

        game = games[chat_id]

        if user_id not in game["players"]:

            if len(game["players"]) >= 4:
                return web.json_response({
                    "error": "Game is full"
                })

            game["players"][user_id] = name

        if len(game["players"]) == 4 and not game["started"]:

            tiles = make_dominoes()
            random.shuffle(tiles)

            ids = list(game["players"].keys())

            for i, uid in enumerate(ids):
                game["hands"][uid] = tiles[i * 7:(i + 1) * 7]

            game["turn"] = ids[0]
            game["started"] = True

        return await game_state(game, user_id)

    except Exception as e:
        return web.json_response(
            {"error": str(e)},
            status=500,
        )


async def api_state(request):

    chat_id = request.query.get("chat_id")
    init_data = request.query.get("initData", "")

    user = verify_init_data(init_data)

    if not user:
        return web.json_response(
            {"error": "Invalid user"},
            status=403,
        )

    user_id = str(user["id"])

    game = games.get(chat_id)

    if not game:
        return web.json_response({
            "error": "Game not found"
        })

    return await game_state(game, user_id)


async def game_state(game, user_id):

    players = []

    for uid, name in game["players"].items():
        players.append({
            "id": uid,
            "name": name,
            "turn": uid == game["turn"],
        })

    return web.json_response({
        "players": players,
        "board": game["board"],
        "myTurn": game["turn"] == user_id,
        "started": game["started"],

        # ကိုယ့် hand ကို ကိုယ်ပဲရ
        "hand": (
            game["hands"].get(user_id, [])
            if game["turn"] == user_id
            else []
        ),
    })


async def api_play(request):

    try:
        body = await request.json()

        chat_id = str(body["chat_id"])
        init_data = body.get("initData", "")

        user = verify_init_data(init_data)

        if not user:
            return web.json_response(
                {"error": "Invalid user"},
                status=403,
            )

        user_id = str(user["id"])

        game = games.get(chat_id)

        if not game:
            return web.json_response({
                "error": "Game not found"
            })

        if game["turn"] != user_id:
            return web.json_response({
                "error": "Not your turn"
            })

        index = int(body["index"])
        side = body.get("side", "right")

        ok, message = play_tile(
            game,
            user_id,
            index,
            side,
        )

        if not ok:
            return web.json_response({
                "error": message
            })

        return await game_state(game, user_id)

    except Exception as e:
        return web.json_response({
            "error": str(e)
        }, status=500)


async def index(request):
    return web.FileResponse("index.html")


async def health(request):
    return web.Response(text="OK")


async def main():

    telegram_app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    telegram_app.add_handler(
        CommandHandler("start", start)
    )

    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()

    web_app = web.Application()

    web_app.router.add_get("/", index)
    web_app.router.add_get("/index.html", index)
    web_app.router.add_get("/health", health)

    web_app.router.add_post("/api/join", api_join)
    web_app.router.add_get("/api/state", api_state)
    web_app.router.add_post("/api/play", api_play)

    runner = web.AppRunner(web_app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT,
    )

    await site.start()

    print("DOMINOES BOT RUNNING")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
