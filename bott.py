# =========================
#        FUSION BOT
#  VK + Google Sheets 24/7
# =========================

import os
import json
import gspread
from vkbottle import Bot, Keyboard, Text
from datetime import datetime

# =========================
# Токен VK (через переменную окружения)
# =========================
TOKEN = os.environ["TOKEN"]
bot = Bot(token=TOKEN)

# =========================
# Google Sheets (через переменную окружения GOOGLE_CREDENTIALS)
# =========================
credentials_json = os.environ["GOOGLE_CREDENTIALS"]
gc = gspread.service_account_from_dict(json.loads(credentials_json))
SHEET_NAME = "AdminsBase"
sheet = gc.open(SHEET_NAME)

admins_sheet = sheet.worksheet("Admins")
punishments_sheet = sheet.worksheet("Punishments")

# =========================
# Функции для загрузки данных
# =========================
def load_admins():
    admins_data = {}
    for row in admins_sheet.get_all_records():
        vk_id = int(row["vk_id"])
        admins_data[vk_id] = {
            "nick": row["nick"].strip(),
            "role": row["role"].strip(),
            "extra_role": row["extra_role"].strip(),
            "level": int(row["level"]),
            "date_start": row["date_start"].strip(),
            "last_promo": row["last_promo"].strip(),
            "answers": int(row["answers"]),
            "vyg": int(row["vyg"]),
            "pred": int(row["pred"]),
            "oral": int(row["oral"]),
            "vk_link": row["vk_link"].strip()
        }
    return admins_data

def load_punishments():
    punishments_data = {}
    for row in punishments_sheet.get_all_records():
        vk_id = int(row["vk_id"])
        if vk_id not in punishments_data:
            punishments_data[vk_id] = []
        punishments_data[vk_id].append({
            "date": str(row["date"]).strip(),
            "type": str(row["type"]).strip(),
            "count": int(row["count"]),
            "reason": str(row["reason"]).strip(),
            "by": str(row["by"]).strip()
        })
    return punishments_data

# =========================
# Повышения по уровням
# =========================
PROMOTIONS = {
    "Младший модератор": {"next": "Модератор", "days": 15, "answers": 5000},
    "Модератор": {"next": "Старший модератор", "days": 20, "answers": 7500},
    "Старший модератор": {"next": "Администратор", "days": 30, "answers": 10000},
    "Администратор": {"next": "Старший администратор", "days": 40, "answers": 20000}
}

# =========================
# Формируем текст информации
# =========================
def main_info(admin):
    date_format = "%Y-%m-%d"
    start_date = datetime.strptime(admin["date_start"], date_format)
    last_promo = datetime.strptime(admin["last_promo"], date_format)
    days_since_promo = (datetime.now() - last_promo).days
    total_days = (datetime.now() - start_date).days

    text = f"🔑 Основная информация 🔑\n"
    text += f"Ваш никнейм: {admin['nick']}\n"
    text += f"Должность: {admin['role']}\n"
    text += f"Доп. должность: {admin['extra_role']}\n"
    text += f"Уровень админ-прав: {admin['level']}\n\n"

    text += f"📅 Важные даты и дни 📅\n"
    text += f"Дата постановки: {admin['date_start']}\n"
    text += f"Последнее повышение: {admin['last_promo']}\n"
    text += f"Дней с момента повышения: {days_since_promo}\n"
    text += f"Всего дней на админ-посту: {total_days}\n\n"

    text += f"⛔️ Активные наказания ⛔️\n"
    text += f"Выговоров: {admin['vyg']}/3\n"
    text += f"Предов: {admin['pred']}/2\n"
    text += f"Устных выговоров: {admin['oral']}/2\n\n"

    text += f"✅ Всего ответов: {admin['answers']}"
    return text

def promotion_info(admin):
    role = admin["role"]
    if role not in PROMOTIONS:
        return "Вы достигли максимального уровня!"
    
    next_role = PROMOTIONS[role]["next"]
    required_days = PROMOTIONS[role]["days"]
    required_answers = PROMOTIONS[role]["answers"]

    date_format = "%Y-%m-%d"
    last_promo = datetime.strptime(admin["last_promo"], date_format)
    days_since_promo = (datetime.now() - last_promo).days
    answers_left = max(0, required_answers - admin["answers"])
    days_left = max(0, required_days - days_since_promo)

    # ✅ Если выполнены все критерии
    if answers_left == 0 and days_left <= 0 and admin["vyg"] == 0 and admin["pred"] == 0 and admin["oral"] == 0:
        return "✅ Вы выполнили все критерии для получения повышения! Руководство сервера было уведомлено!"

    # Иначе — показываем прогресс
    text = f"🔑 Информация о повышениях 🔑\n\n"
    text += f"{role} → {next_role}:\n"
    text += f"Отстоять {required_days} дней с момента повышения.\n"
    text += f"Иметь не менее {required_answers} ответов.\n\n"
    text += f"🔎 Осталось выполнить 🔍\n"
    text += f"Ответов: {answers_left}\n"
    text += f"Дней: {days_left}\n"
    text += f"Выговоров: {admin['vyg']}/3\n"
    text += f"Предов: {admin['pred']}/2\n"
    text += f"Устных: {admin['oral']}/2\n\n"
    return text

def punishment_info(vk_id):
    punishments_data = load_punishments()
    if vk_id not in punishments_data or not punishments_data[vk_id]:
        return "Нет наказаний."
    sorted_punishments = sorted(punishments_data[vk_id], key=lambda x: x["date"], reverse=True)
    text = "Последние 10 действий с наказаниями:\n\n"
    for p in sorted_punishments[:10]:
        text += f"{p['date']} | {p['type']} | Количество: {p['count']}\n"
        text += f"Причина: {p['reason']} by {p['by']}\n\n"
    return text

# =========================
# Обработчик ЛС
# =========================
@bot.on.private_message()
async def handler(message):
    admins_data = load_admins()
    vk_id = message.from_id
    print(f"[DEBUG] Получено сообщение от {vk_id}: {message.text}")

    if vk_id not in admins_data:
        await message.answer("Вы не зарегистрированы как админ, бот не работает для вас.")
        return

    kb = Keyboard(one_time=False)
    kb.add(Text("📌 Основная информация"))
    kb.add(Text("📈 Информация о повышении"))
    kb.row()
    kb.add(Text("⛔ Последние наказания"))

    text = message.text.strip()
    if text == "📌 Основная информация":
        await message.answer(main_info(admins_data[vk_id]), keyboard=kb)
    elif text == "📈 Информация о повышении":
        await message.answer(promotion_info(admins_data[vk_id]), keyboard=kb)
    elif text == "⛔ Последние наказания":
        await message.answer(punishment_info(vk_id), keyboard=kb)
    else:
        await message.answer("Привет! Выберите кнопку:", keyboard=kb)

# =========================
# Запуск бота 24/7
# =========================
bot.run_forever()
