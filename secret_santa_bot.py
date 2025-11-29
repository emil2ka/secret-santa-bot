import telebot
from telebot import types
import random
import json
import os

BOT_TOKEN = os.getenv("7678743643:AAH2ncgI51mpyFrwr_tQEZFWc1Rn6_nsnbo")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1222859648"))             # сюда твой Telegram ID (организатор)

bot = telebot.TeleBot("7678743643:AAH2ncgI51mpyFrwr_tQEZFWc1Rn6_nsnbo")

PARTICIPANTS = [
    "Дильноза",
    "Самира",
    "Алижан",
    "Мансур",
    "Эмиль",
    "Бекасыл",
    "Амирлан",
    "Фатина",
    "Диана",
    "Жанель"
]

PAIRS_FILE = "pairs.json"   # пары "кто кому"
USERS_FILE = "users.json"   # привязка user_id -> имя


# --------------- РАБОТА С ФАЙЛАМИ ---------------

def create_derangement(names):
    """Создает распределение, где никто не дарит сам себе."""
    while True:
        receivers = names[:]
        random.shuffle(receivers)
        if all(giver != receiver for giver, receiver in zip(names, receivers)):
            return dict(zip(names, receivers))


def save_pairs(pairs):
    with open(PAIRS_FILE, "w", encoding="utf-8") as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)


def load_pairs():
    if not os.path.exists(PAIRS_FILE):
        return None
    with open(PAIRS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# --------------- КРАСИВЫЕ КНОПКИ ---------------

def make_name_keyboard():
    """Инлайн-клавиатура с именами участников."""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for name in PARTICIPANTS:
        buttons.append(types.InlineKeyboardButton(
            text=name,
            callback_data=f"reg:{name}"
        ))
    keyboard.add(*buttons)
    return keyboard


def make_whoami_keyboard():
    """Кнопка 'Узнать, кому я дарю'."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(
        text="🎁 Узнать, кому я дарю",
        callback_data="whoami"
    ))
    return keyboard


# --------------- КОМАНДЫ АДМИНА ---------------

@bot.message_handler(commands=["make_pairs"])
def make_pairs(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "У тебя нет прав использовать эту команду 🙈")
        return

    pairs = create_derangement(PARTICIPANTS)
    save_pairs(pairs)
    bot.reply_to(message, "✅ Пары тайного Санты созданы и сохранены!")


@bot.message_handler(commands=["reset_pairs"])
def reset_pairs(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "У тебя нет прав использовать эту команду 🙈")
        return

    if os.path.exists(PAIRS_FILE):
        os.remove(PAIRS_FILE)
    bot.reply_to(message, "♻️ Пары удалены. Можно снова вызвать /make_pairs.")


@bot.message_handler(commands=["reset_users"])
def reset_users(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "У тебя нет прав использовать эту команду 🙈")
        return

    if os.path.exists(USERS_FILE):
        os.remove(USERS_FILE)
    bot.reply_to(message, "♻️ Все регистрации пользователей сброшены.")


@bot.message_handler(commands=["list_users"])
def list_users(message):
    """Чисто для админа: кто какое имя занял."""
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "У тебя нет прав использовать эту команду 🙈")
        return

    users = load_users()
    if not users:
        bot.reply_to(message, "Пока никто не зарегистрировался.")
        return

    lines = []
    for uid, name in users.items():
        lines.append(f"{name} — `{uid}`")
    text = "👥 Зарегистрированные участники:\n\n" + "\n".join(lines)
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


# --------------- /START И ОСНОВНОЙ UX ---------------

@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = str(message.from_user.id)
    users = load_users()

    if user_id in users:
        name = users[user_id]
        text = (
            "🎄 *Тайный Санта 2025* 🎄\n\n"
            f"Ты уже зарегистрирован как *{name}*.\n\n"
            "Нажми кнопку ниже, чтобы узнать, кому ты даришь подарок 👇"
        )
        bot.send_message(
            message.chat.id, text,
            parse_mode="Markdown",
            reply_markup=make_whoami_keyboard()
        )
    else:
        text = (
            "🎄 *Тайный Санта 2025* 🎄\n\n"
            "Привет! Я помогу вам сыграть в Тайного Санту в компании из 10 человек.\n\n"
            "🔹 Шаг 1: Выбери *своё имя* из списка ниже.\n"
            "🔹 Шаг 2: После регистрации нажми кнопку, чтобы узнать, кому ты даришь подарок 🎁\n\n"
            "Список участников:"
        )
        bot.send_message(
            message.chat.id, text,
            parse_mode="Markdown",
            reply_markup=make_name_keyboard()
        )


# --------------- CALLBACK-ОБРАБОТЧИКИ (КНОПКИ) ---------------

@bot.callback_query_handler(func=lambda call: call.data.startswith("reg:"))
def callback_register_name(call):
    user_id = str(call.from_user.id)
    requested_name = call.data[4:]  # убираем "reg:"

    users = load_users()

    # Если пользователь уже зарегистрирован
    if user_id in users:
        current_name = users[user_id]
        bot.answer_callback_query(
            call.id,
            text=f"Ты уже зарегистрирован как {current_name}."
        )
        try:
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None
            )
        except Exception:
            pass
        bot.send_message(
            call.message.chat.id,
            f"Ты уже зарегистрирован как *{current_name}*.\n"
            "Нажми кнопку ниже, чтобы узнать, кому ты даришь подарок 🎁",
            parse_mode="Markdown",
            reply_markup=make_whoami_keyboard()
        )
        return

    # Если выбранное имя уже занято другим
    if requested_name in users.values():
        bot.answer_callback_query(
            call.id,
            text="Это имя уже занято другим участником 👀"
        )
        bot.send_message(
            call.message.chat.id,
            "Это имя уже выбрал кто-то другой.\n"
            "Если это ошибка — свяжись с организатором.",
        )
        return

    # Регистрируем
    users[user_id] = requested_name
    save_users(users)

    bot.answer_callback_query(
        call.id,
        text=f"Ты зарегистрирован как {requested_name} ✅"
    )

    # Убираем старую клаву с именами (если получится)
    try:
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
    except Exception:
        pass

    bot.send_message(
        call.message.chat.id,
        f"Отлично, *{requested_name}*! 🎉\n\n"
        "Теперь нажми кнопку ниже, чтобы узнать, кому ты даришь подарок 👇",
        parse_mode="Markdown",
        reply_markup=make_whoami_keyboard()
    )


@bot.callback_query_handler(func=lambda call: call.data == "whoami")
def callback_whoami(call):
    user_id = str(call.from_user.id)
    users = load_users()
    pairs = load_pairs()

    if not pairs:
        bot.answer_callback_query(
            call.id,
            text="Пары ещё не созданы 🙈"
        )
        bot.send_message(
            call.message.chat.id,
            "Пары ещё не созданы. Попроси организатора вызвать команду /make_pairs 🎄"
        )
        return

    if user_id not in users:
        bot.answer_callback_query(
            call.id,
            text="Сначала выбери своё имя!"
        )
        bot.send_message(
            call.message.chat.id,
            "Сначала нужно зарегистрироваться — нажми /start и выбери своё имя 😊"
        )
        return

    name = users[user_id]
    recipient = pairs.get(name)

    if not recipient:
        bot.answer_callback_query(
            call.id,
            text="Ошибка при поиске пары 😥"
        )
        bot.send_message(
            call.message.chat.id,
            "Возникла ошибка при поиске пары. Свяжись с организатором."
        )
        return

    bot.answer_callback_query(call.id, text="Секрет доставлен 🤫")

    bot.send_message(
        call.message.chat.id,
        f"🤫 *Тайный Санта*\n\n"
        f"{name}, ты даришь подарок: *{recipient}*.\n\n"
        "Никому не рассказывай, это секрет! 🎁",
        parse_mode="Markdown"
    )


# --------------- ФОЛЛБЭК ДЛЯ ТЕКСТА (НА ВСЯКИЙ) ---------------

@bot.message_handler(func=lambda m: True, content_types=["text"])
def fallback_message(message):
    # Просто мягко направляем людей на /start и кнопки
    bot.send_message(
        message.chat.id,
        "Для участия в Тайном Санте нажми /start и выбери своё имя с помощью кнопок 🎄"
    )


# --------------- ЗАПУСК БОТА ---------------

print("Бот запущен. Ожидаю сообщения...")
bot.infinity_polling()
