from vkbottle import Bot, Keyboard, Text
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
import json

# ===== VK TOKEN =====
TOKEN = os.environ["VK_TOKEN"]
bot = Bot(token=TOKEN)

# ===== GOOGLE CREDS =====
creds_dict = json.loads(os.environ["GOOGLE_CREDS"])
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
gc = gspread.authorize(creds)

# ===== GOOGLE SHEET =====
SHEET_NAME = "AdminsBase"
sheet = gc.open(SHEET_NAME)
admins_sheet = sheet.worksheet("Admins")
punishments_sheet = sheet.worksheet("Punishments")

# ===== LOAD DATA =====
def load_admins():
    data = {}
    for row in admins_sheet.get_all_records():
        vk_id = int(row["vk_id"])
        data[vk_id] = {
            "nick": row["nick"],
            "role": row["role"],
            "extra_role": row["extra_role"],
            "level": int(row["level"]),
            "date_start": row["date_start"],
            "last_promo": row["last_promo"],
            "answers": int(row["answers"]),
            "vyg": int(row["vyg"]),
            "pred": int(row["pred"]),
            "oral": int(row["oral"]),
        }
    return data

def load_punishments():
    data = {}
    for row in punishments_sheet.get_all_records():
        vk_id = int(row["vk_id"])
        data.setdefault(vk_id, []).append(row)
    return data

PROMOTIONS = {
    "Младший модератор": {"next": "Модератор", "days": 15, "answers": 5000},
    "Модератор": {"next": "Старший модератор", "days": 20, "answers": 7500},
    "Старший модератор": {"next": "Администратор", "days": 30, "answers": 10000},
    "Администратор": {"next": "Старший администратор", "days": 40, "answers": 20000},
}

def promotion_info(admin):
    role = admin["role"]
    if role not in PROMOTIONS:
        return "Вы достигли максимального уровня!"

    rule = PROMOTIONS[role]
    days = (datetime.now() - datetime.strptime(admin["last_promo"], "%Y-%m-%d")).days

    if (
        admin["answers"] >= rule["answers"]
        and days >= rule["days"]
        and admin["vyg"] == 0
        and admin["pred"] == 0
        and admin["oral"] == 0
    ):
        return "✅ Вы выполнили все критерии для получения повышения! Руководство сервера было уведомлено!"

    return (
        f"До повышения: {rule['next']}\n"
        f"Ответов: {rule['answers'] - admin['answers']}\n"
        f"Дней: {rule['days'] - days}"
    )

@bot.on.private_message()
async def handler(message):
    admins = load_admins()
    vk_id = message.from_id

    if vk_id not in admins:
        await message.answer("Вы не зарегистрированы.")
        return

    kb = Keyboard()
    kb.add(Text("📈 Повышение"))

    if message.text == "📈 Повышение":
        await message.answer(promotion_info(admins[vk_id]), keyboard=kb)
    else:
        await message.answer("Выберите:", keyboard=kb)

bot.run_forever()
