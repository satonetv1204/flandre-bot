import discord
from discord.ext import tasks
from datetime import datetime
import pytz
import random
import os

from flask import Flask
from threading import Thread

# =====================
# Keep Alive
# =====================

app = Flask('')


@app.route('/')
def home():
    return "Flandre Bot is alive!"


def run():
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()


# =====================
# Discord Bot
# =====================

TOKEN = os.getenv("TOKEN")

# 送信先チャンネル
CHANNEL_ID = 1048447164398972979

# 21:55 のメンション対象
REMINDER_ROLE_IDS = [
    1021009629968347147,
    1235963423209160786
]

# 22:00 のメンション対象
BATTLE_ROLE_ID = 1501746343738216610

intents = discord.Intents.default()
client = discord.Client(intents=intents)

JST = pytz.timezone("Asia/Tokyo")

# 21:55 メッセージ
reminder_messages = [
    "あと5分で対抗戦だよ〜！",
    "ねぇねぇ、準備できてる〜？",
    "逃げちゃダメだよ？",
    "21時55分だぁ！集合〜！",
]

# 22:00 メッセージ
battle_messages = [
    "22時だよ〜♪ 壊れるまで遊ぼうね？",
    "対抗戦の時間だよ～！きゃははっ！",
    "対抗戦開始だよ！ねぇねぇ、今日は誰が壊れちゃうのかな？",
    "22時！フランちゃん参上〜！",
    "対抗戦の時間だよ！まだ元気だよね？遊べるよね？",
    "対抗戦開始！逃げてもむだだよ〜？",
    "きゃははっ！戦闘開始だぁ！",
    "今日はいっぱい暴れられるといいなぁ♪",
    "壊しちゃってもいいよね？"
]


@tasks.loop(minutes=1)
async def taikousen_bot():
    now = datetime.now(JST)

    # 土曜=5 日曜=6
    if now.weekday() in [5, 6]:

        channel = client.get_channel(CHANNEL_ID)

        # 21:55 リマインド
        if now.hour == 21 and now.minute == 55:

            mentions = " ".join(
                [f"<@&{role_id}>" for role_id in REMINDER_ROLE_IDS]
            )

            await channel.send(
                f"{mentions}\n"
                f"{random.choice(reminder_messages)}"
            )

        # 22:00 対抗戦開始
        if now.hour == 22 and now.minute == 0:

            await channel.send(
                f"<@&{BATTLE_ROLE_ID}>\n"
                f"{random.choice(battle_messages)}"
            )


@client.event
async def on_ready():
    print(f"ログインしました: {client.user}")
    taikousen_bot.start()


keep_alive()
client.run(TOKEN)
