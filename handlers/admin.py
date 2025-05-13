import asyncio
import logging
import html
import chardet
import mysql.connector
from aiogram import types
from config.config import API_TOKEN, MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, RANKS
from utils.database import execute_db_query

logger = logging.getLogger(__name__)

# 🔐 Проверка прав доступа (только для ранга 30)
async def is_creator(user_id: int) -> bool:
    def sync_check():
        # Подключение к базе данных
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = connection.cursor()
        cursor.execute('SELECT rank FROM users WHERE user_id = %s', (user_id,))
        result = cursor.fetchone()
        connection.close()
        return result and result[0] == 30
    return await asyncio.to_thread(sync_check)

# 🔝 /setrank <id> <rank>
async def handle_setrank(message: types.Message):
    if not await is_creator(message.from_user.id):
        await message.answer("⛔ У вас нет прав на выполнение этой команды.")
        return

    args = message.text.split()[1:]
    if len(args) != 2 or not all(arg.isdigit() for arg in args):
        await message.answer("❌ Используйте: /setrank <id> <rank>")
        return

    user_id, rank = map(int, args)

    if rank < 1 or rank > 30:
        await message.answer("❌ Ранг должен быть от 1 до 30.")
        return

    def sync_set_rank():
        # Подключение к базе данных
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = connection.cursor()
        cursor.execute('UPDATE users SET rank = %s WHERE id = %s', (rank, user_id))
        connection.commit()
        connection.close()

    await asyncio.to_thread(sync_set_rank)
    await message.answer(f"✅ Пользователю с ID {user_id} установлен ранг {RANKS.get(rank, 'Неизвестно')} ({rank}).")

# 💰 /setbalance <id> <amount>
async def handle_setbalance(message: types.Message):
    if not await is_creator(message.from_user.id):
        await message.answer("⛔ У вас нет прав на выполнение этой команды.")
        return

    args = message.text.split()[1:]
    if len(args) != 2 or not all(arg.isdigit() for arg in args):
        await message.answer("❌ Используйте: /setbalance <id> <amount>")
        return

    user_id, amount = map(int, args)

    def sync_set_balance():
        # Подключение к базе данных
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = connection.cursor()
        cursor.execute('UPDATE users SET balance = %s WHERE id = %s', (amount, user_id))
        connection.commit()
        connection.close()

    await asyncio.to_thread(sync_set_balance)
    await message.answer(f"✅ Баланс пользователя с ID {user_id} изменён на {amount}💵.")

# 🎯 /setlevel <id> <level>
async def handle_setlevel(message: types.Message):
    if not await is_creator(message.from_user.id):
        await message.answer("⛔ У вас нет прав на выполнение этой команды.")
        return

    args = message.text.split()[1:]
    if len(args) != 2 or not all(arg.isdigit() for arg in args):
        await message.answer("❌ Используйте: /setlevel <id> <level>")
        return

    user_id, level = map(int, args)

    def sync_set_level():
        # Подключение к базе данных
        # Подключение к базе данных
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = connection.cursor()
        cursor.execute('UPDATE users SET level = %s WHERE id = %s', (level, user_id))
        connection.commit()
        connection.close()

    await asyncio.to_thread(sync_set_level)
    await message.answer(f"✅ Уровень пользователя с ID {user_id} установлен на {level}.")

# 🗑 /resetuser <id>
async def handle_resetuser(message: types.Message):
    if not await is_creator(message.from_user.id):
        await message.answer("⛔ У вас нет прав на выполнение этой команды.")
        return

    args = message.text.split()[1:]
    if len(args) != 1 or not args[0].isdigit():
        await message.answer("❌ Используйте: /resetuser <id>")
        return

    user_id = int(args[0])

    def sync_reset_user():
        # Подключение к базе данных
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE users SET 
                balance = 0, level = 1, experience = 0, rank = 1, daily_streak = 0, last_daily = NULL
            WHERE id = %s
        ''', (user_id,))
        connection.commit()
        connection.close()

    await asyncio.to_thread(sync_reset_user)
    await message.answer(f"♻️ Профиль пользователя с ID {user_id} сброшен.")

# 🔍 /userinfo <id>
async def handle_userinfo(message: types.Message):
    if not await is_creator(message.from_user.id):
        await message.answer("⛔ У вас нет прав на выполнение этой команды.")
        return

    args = message.text.split()[1:]
    if len(args) != 1 or not args[0].isdigit():
        await message.answer("❌ Используйте: /userinfo <id>")
        return

    user_id = int(args[0])

    def sync_get_user_info():
        # Подключение к базе данных
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = connection.cursor()
        cursor.execute('SELECT id, username, rank, level, balance, registration_date FROM users WHERE id = %s', (user_id,))
        result = cursor.fetchone()
        connection.close()
        return result

    user_info = await asyncio.to_thread(sync_get_user_info)
    if user_info:
        id_, username, rank, level, balance, reg_date = user_info
        await message.answer(
            f"📝 <b>Информация о пользователе</b>\n"
            f"🆔 ID: <b>{id_}</b>\n"
            f"👤 Имя: <b>{username}</b>\n"
            f"🏅 Ранг: <b>{RANKS.get(rank, 'Неизвестно')}</b>\n"
            f"🎯 Уровень: <b>{level}</b>\n"
            f"💰 Баланс: <b>{balance}💵</b>\n"
            f"📅 Дата регистрации: <b>{reg_date}</b>",
            parse_mode="HTML"
        )
    else:
        await message.answer("⚠️ Пользователь не найден.")

# 🚫 /ban <id>
async def handle_ban(message: types.Message):
    if not await is_creator(message.from_user.id):
        await message.answer("⛔ У вас нет прав на выполнение этой команды.")
        return

    args = message.text.split()[1:]
    if len(args) != 1 or not args[0].isdigit():
        await message.answer("❌ Используйте: /ban <id>")
        return

    user_id = int(args[0])

    def sync_ban_user():
        # Подключение к базе данных
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = connection.cursor()
        cursor.execute('UPDATE users SET rank = 0 WHERE id = %s', (user_id,))
        connection.commit()
        connection.close()

    await asyncio.to_thread(sync_ban_user)
    await message.answer(f"🚫 Пользователь с ID {user_id} заблокирован.")

# ✅ /unban <id>
async def handle_unban(message: types.Message):
    if not await is_creator(message.from_user.id):
        await message.answer("⛔ У вас нет прав на выполнение этой команды.")
        return

    args = message.text.split()[1:]
    if len(args) != 1 or not args[0].isdigit():
        await message.answer("❌ Используйте: /unban <id>")
        return

    user_id = int(args[0])

    def sync_unban_user():
        # Подключение к базе данных
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = connection.cursor()
        cursor.execute('UPDATE users SET rank = 1 WHERE id = %s', (user_id,))
        connection.commit()
        connection.close()

    await asyncio.to_thread(sync_unban_user)
    await message.answer(f"✅ Пользователь с ID {user_id} разблокирован.")

# 💵 /givebalance <id> <amount>
async def handle_givebalance(message: types.Message):
    if not await is_creator(message.from_user.id):
        await message.answer("⛔ У вас нет прав на выполнение этой команды.")
        return

    args = message.text.split()[1:]
    if len(args) != 2 or not all(arg.isdigit() for arg in args):
        await message.answer("❌ Используйте: /givebalance <id> <amount>")
        return

    user_id, amount = map(int, args)

    def sync_give_balance():
        # Подключение к базе данных
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = connection.cursor()
        cursor.execute('UPDATE users SET balance = balance + %s WHERE id = %s', (amount, user_id))
        connection.commit()
        connection.close()

    await asyncio.to_thread(sync_give_balance)
    await message.answer(f"💵 Пользователю с ID {user_id} начислено {amount}💵.")

# 💸 /giveall <amount>
async def handle_giveall(message: types.Message):
    if not await is_creator(message.from_user.id):
        await message.answer("⛔ У вас нет прав на выполнение этой команды.")
        return

    args = message.text.split()[1:]
    if len(args) != 1 or not args[0].isdigit():
        await message.answer("❌ Используйте: /giveall <amount>")
        return

    amount = int(args[0])

    def sync_give_all():
        # Подключение к базе данных
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = connection.cursor()
        cursor.execute('UPDATE users SET balance = balance + %s', (amount,))
        connection.commit()
        connection.close()

    await asyncio.to_thread(sync_give_all)
    await message.answer(f"💸 Всем пользователям начислено {amount}💵.")

    # 📊 /stats — Общая статистика бота
async def handle_stats(message: types.Message):
    if not await is_creator(message.from_user.id):
        await message.answer("⛔ У вас нет прав на выполнение этой команды.")
        return

    def sync_get_stats():
        # Подключение к базе данных
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*), AVG(level), SUM(balance) FROM users")
        total_users, avg_level, total_balance = cursor.fetchone()
        connection.close()
        return total_users, avg_level or 0, total_balance or 0

    total_users, avg_level, total_balance = await asyncio.to_thread(sync_get_stats)
    await message.answer(
        f"📊 <b>Статистика бота</b>\n"
        f"👥 Пользователей: <b>{total_users}</b>\n"
        f"🎯 Средний уровень: <b>{avg_level:.2f}</b>\n"
        f"💵 Общий баланс: <b>{total_balance}💵</b>",
        parse_mode="HTML"
    )

# 🏆 /topusers <n> — Топ пользователей по уровню
async def handle_topusers(message: types.Message):
    if not await is_creator(message.from_user.id):
        await message.answer("⛔ У вас нет прав на выполнение этой команды.")
        return

    args = message.text.split()[1:]
    if len(args) != 1 or not args[0].isdigit():
        await message.answer("❌ Используйте: /topusers <количество>")
        return

    limit = int(args[0])

    def sync_get_topusers():
        # Подключение к базе данных
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = connection.cursor()
        cursor.execute(
            "SELECT username, level, balance FROM users ORDER BY level DESC, balance DESC LIMIT %s",
            (limit,)
        )
        results = cursor.fetchall()
        connection.close()
        return results

    top_users = await asyncio.to_thread(sync_get_topusers)
    if top_users:
        text = "🏆 <b>Топ пользователей:</b>\n" + "\n".join(
            [f"{idx+1}. 👤 <b>{username}</b> — 🎯 {level} lvl — 💵 {balance}💵" for idx, (username, level, balance) in enumerate(top_users)]
        )
    else:
        text = "⚠️ Нет данных для отображения."

    await message.answer(text, parse_mode="HTML")

# 🪙 /addcurrency <id> <currency> <amount> — Добавить валюту пользователю
async def handle_addcurrency(message: types.Message):
    if not await is_creator(message.from_user.id):
        await message.answer("⛔ У вас нет прав на выполнение этой команды.")
        return

    args = message.text.split()[1:]
    if len(args) != 3 or not args[0].isdigit() or not args[2].isdigit():
        await message.answer("❌ Используйте: /addcurrency <id> <currency> <amount>")
        return

    user_id, currency, amount = int(args[0]), args[1].lower(), int(args[2])
    allowed_currencies = ["balance", "solix", "aurix", "valorium", "novacoin"]

    if currency not in allowed_currencies:
        await message.answer(f"⚠️ Неверная валюта. Доступные: {', '.join(allowed_currencies)}")
        return

    def sync_add_currency():
        # Подключение к базе данных
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = connection.cursor()
        cursor.execute(f"UPDATE users SET {currency} = {currency} + %s WHERE id = %s", (amount, user_id))
        connection.commit()
        connection.close()

    await asyncio.to_thread(sync_add_currency)
    await message.answer(f"🪙 Пользователю с ID {user_id} добавлено {amount} {currency}.")

    # 🛡 /mod <id> — Сделать модератором (26 уровень)
async def handle_mod(message: types.Message):
    if not await is_creator(message.from_user.id):
        await message.answer("⛔ У вас нет прав на выполнение этой команды.")
        return

    args = message.text.split()[1:]
    if len(args) != 1 or not args[0].isdigit():
        await message.answer("❌ Используйте: /mod <id>")
        return

    user_id = int(args[0])

    def sync_set_mod():
        # Подключение к базе данных
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = connection.cursor()
        cursor.execute('UPDATE users SET rank = 26 WHERE id = %s', (user_id,))
        connection.commit()
        connection.close()

    await asyncio.to_thread(sync_set_mod)
    await message.answer(f"🛡 Пользователь с ID {user_id} теперь модератор (ранг 26).")

# 🚫 /banlist — Список забаненных пользователей
async def handle_banlist(message: types.Message):
    if not await is_creator(message.from_user.id):
        await message.answer("⛔ У вас нет прав на выполнение этой команды.")
        return

    def sync_get_banlist():
        # Подключение к базе данных
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = connection.cursor()
        cursor.execute('SELECT id, username FROM users WHERE rank = 0')
        banned_users = cursor.fetchall()
        connection.close()
        return banned_users

    banned_users = await asyncio.to_thread(sync_get_banlist)
    count = len(banned_users)
    if count > 0:
        users_list = "\\n".join([f"🆔 {id_} — 👤 {username}" for id_, username in banned_users])
        await message.answer(f"🚫 <b>Забаненные пользователи ({count}):</b>\\n{users_list}", parse_mode="HTML")
    else:
        await message.answer("✅ Нет забаненных пользователей.")

# 📜 /showlogs — Показать последние строки из логов с автоопределением кодировки
async def handle_showlogs(message: types.Message):
    logger.info("⚡ Запуск команды /showlogs")
    try:
        if not await is_creator(message.from_user.id):
            await message.answer("⛔ У вас нет прав на выполнение этой команды.")
            return

        # 🔄 Автоопределение кодировки файла логов
        with open("log.log", "rb") as raw_file:
            raw_data = raw_file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding'] or 'utf-8'
            logger.info(f"🔤 Определена кодировка файла логов: {encoding}")
            
        decoded_data = raw_data.decode(encoding, errors='replace')
        lines = decoded_data.splitlines()[-20:]  # Последние 20 строк

        if lines:
            escaped_lines = html.escape("\\n".join(lines))
            chunk_size = 4000
            for i in range(0, len(escaped_lines), chunk_size):
                await message.answer(f"📜 <b>Логи:</b>\\n<pre>{escaped_lines[i:i+chunk_size]}</pre>", parse_mode="HTML")
        else:
            await message.answer("⚠️ Лог пуст.")

    except Exception as e:
        logger.error(f"❌ Ошибка при чтении логов: {str(e)}")
        await message.answer(f"⚠️ Ошибка при чтении логов: {str(e)}")

# 📢 /broadcast <message>
async def handle_broadcast(message: types.Message):
    """Команда для рассылки сообщения всем пользователям."""
    if not await is_creator(message.from_user.id):
        await message.answer("⛔ У вас нет прав на выполнение этой команды.")
        return

    # Получаем текст сообщения от администратора, начиная с 9-го символа (после команды)
    broadcast_text = message.text[10:].strip()  # Отрезаем команду /broadcast и пробел

    if not broadcast_text:
        await message.answer("❌ Пожалуйста, укажите текст сообщения для рассылки.")
        return

    try:
        # Получаем список всех пользователей
        # Подключение к базе данных
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = connection.cursor()
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        connection.close()

        # Рассылаем сообщение всем пользователям
        for user in users:
            user_id = user[0]
            try:
                await message.bot.send_message(user_id, broadcast_text)
            except Exception as e:
                # Логируем ошибки при отправке сообщения
                print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

        await message.answer(f"✅ Сообщение было успешно отправлено всем пользователям.")

    except Exception as e:
        await message.answer(f"⚠️ Произошла ошибка при рассылке сообщений: {e}")

async def handle_ticket_list(message: types.Message):
    try:
        if not await is_creator(message.from_user.id):
            await message.answer("⛔ У вас нет прав на выполнение этой команды.")
            return

        # Получаем список открытых тикетов
        tickets = await execute_db_query(
            "SELECT id, user_id, message FROM tickets WHERE status = 'open'"
        )

        if not tickets:
            await message.answer("📭 Нет открытых тикетов.")
            return

        # Формируем список тикетов
        tickets_list = "📬 Открытые тикеты:\n\n"
        for ticket in tickets:
            ticket_id, user_id, user_message = ticket
            tickets_list += f"🆔 ID: {ticket_id}\n👤 Пользователь: {user_id}\n📝 Вопрос: {user_message}\n\n"

        await message.answer(tickets_list)

    except Exception as e:
        logger.error(f"Ошибка при получении списка тикетов: {e}")
        await message.answer("⚠️ Произошла ошибка при получении списка тикетов.")

async def handle_reply_ticket(message: types.Message):
    try:
        if not await is_creator(message.from_user.id):
            await message.answer("⛔ У вас нет прав на выполнение этой команды.")
            return

        args = message.text.split(maxsplit=2)  # Разделяем команду на части
        if len(args) < 3:
            await message.answer("❌ Используйте: /replyticket <ticket_id> <ответ>")
            return

        ticket_id = args[1]
        admin_reply = args[2]
        admin_id = message.from_user.id

        # Обновляем тикет в базе данных
        await execute_db_query(
            "UPDATE tickets SET status = 'closed', admin_id = %s, admin_reply = %s WHERE id = %s",
            (admin_id, admin_reply, ticket_id)
        )

        # Получаем ID пользователя, создавшего тикет
        user_id_result = await execute_db_query(
            "SELECT user_id FROM tickets WHERE id = %s",
            (ticket_id,)
        )

        if user_id_result:
            user_id = user_id_result[0][0]

            # Отправляем ответ пользователю
            await message.bot.send_message(  # Используем message.bot вместо bot
                user_id,
                f"📩 Ответ на ваш вопрос (тикет #{ticket_id}):\n\n{admin_reply}"
            )

        await message.answer(f"✅ Ответ на тикет #{ticket_id} отправлен пользователю.")

    except Exception as e:
        logger.error(f"Ошибка при ответе на тикет: {e}")
        await message.answer("⚠️ Произошла ошибка при ответе на тикет.")

async def handle_close_ticket(message: types.Message):
    try:
        if not await is_creator(message.from_user.id):
            await message.answer("⛔ У вас нет прав на выполнение этой команды.")
            return

        args = message.text.split()
        if len(args) != 2 or not args[1].isdigit():
            await message.answer("❌ Используйте: /closeticket <ticket_id>")
            return

        ticket_id = args[1]

        # Закрываем тикет
        await execute_db_query(
            "UPDATE tickets SET status = 'closed' WHERE id = %s",
            (ticket_id,)
        )

        await message.answer(f"✅ Тикет #{ticket_id} закрыт.")

    except Exception as e:
        logger.error(f"Ошибка при закрытии тикета: {e}")
        await message.answer("⚠️ Произошла ошибка при закрытии тикета.")

