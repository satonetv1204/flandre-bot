import discord
from discord.ext import tasks
from discord import app_commands
from datetime import datetime, timedelta
import pytz
import random
import os
import json

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
tree = app_commands.CommandTree(client)

JST = pytz.timezone("Asia/Tokyo")

# 予約保存
SCHEDULE_FILE = "schedules.json"

if not os.path.exists(SCHEDULE_FILE):
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

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


# =====================
# 予約コマンド
# =====================

@tree.command(name="予約", description="メッセージを予約送信する")
@app_commands.describe(
    日後="何日後か",
    時間="送信時間 (例: 22:00)",
    メッセージ="送信するメッセージ"
)
async def reserve(
    interaction: discord.Interaction,
    日後: int,
    時間: str,
    メッセージ: str
):

    try:
        hour, minute = map(int, 時間.split(":"))

        send_time = datetime.now(JST) + timedelta(days=日後)
        send_time = send_time.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0
        )

        schedule_data = {
            "channel_id": interaction.channel.id,
            "message": メッセージ,
            "time": send_time.strftime("%Y-%m-%d %H:%M")
        }

        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            schedules = json.load(f)

        schedules.append(schedule_data)

        with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
            json.dump(schedules, f, ensure_ascii=False, indent=4)

        await interaction.response.send_message(
            f"予約したよ〜！\n"
            f"日時: {send_time.strftime('%Y/%m/%d %H:%M')}\n"
            f"メッセージ: {メッセージ}",
            ephemeral=True
        )

    except Exception as e:
        await interaction.response.send_message(
            f"エラーだよ〜！\n{e}",
            ephemeral=True
        )


# =====================
# 自動通知
# =====================

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

    # =====================
    # 予約チェック
    # =====================

    with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
        schedules = json.load(f)

    remaining = []

    for schedule in schedules:

        schedule_time = JST.localize(
            datetime.strptime(schedule["time"], "%Y-%m-%d %H:%M")
        )

        if (
            schedule_time.year == now.year and
            schedule_time.month == now.month and
            schedule_time.day == now.day and
            schedule_time.hour == now.hour and
            schedule_time.minute == now.minute
        ):

            channel = client.get_channel(schedule["channel_id"])

            if channel:
                await channel.send(schedule["message"])

        else:
            remaining.append(schedule)

    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(remaining, f, ensure_ascii=False, indent=4)


# =====================
# 起動
# =====================

@client.event
async def on_ready():
    print(f"ログインしました: {client.user}")

    await tree.sync()

    taikousen_bot.start()

    print("スラッシュコマンド同期完了")


keep_alive()
client.run(TOKEN)
