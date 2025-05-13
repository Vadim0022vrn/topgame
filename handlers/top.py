from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from utils.database import execute_db_query
import logging

logger = logging.getLogger(__name__)

async def handle_top(message: types.Message):
    """
    Обработчик команды /top. Выводит ТОП-10 самых богатых игроков.
    """
    try:
        # Получаем ТОП-10 игроков
        query = '''
            SELECT user_id, username, balance, bank
            FROM users
            ORDER BY (balance + bank) DESC
            LIMIT 10
        '''
        top_players = await execute_db_query(query)

        # Получаем данные текущего игрока
        user_id = message.from_user.id
        query = '''
            SELECT user_id, username, balance, bank
            FROM users
            WHERE user_id = %s
        '''
        current_player = await execute_db_query(query, (user_id,))

        if not current_player:
            await message.answer("⚠️ Ваш профиль не найден. Зарегистрируйтесь через /start.")
            return

        current_player = current_player[0]

        # Формируем сообщение с ТОП-10
        message_text = "🏆 ТОП-10 самых богатых игроков:\n\n"
        for i, (user_id, username, balance, bank) in enumerate(top_players, start=1):
            message_text += f"{i}. {username} (ID: {user_id})\n"
            message_text += f"   💵 Баланс: {balance}\n"
            message_text += f"   🏦 Банк: {bank}\n"
            message_text += f"   💰 Итого: {balance + bank}\n\n"

        # Добавляем место текущего игрока
        query = '''
            SELECT COUNT(*) + 1
            FROM users
            WHERE (balance + bank) > (%s + %s)
        '''
        current_player_rank = await execute_db_query(query, (current_player[2], current_player[3]))
        current_player_rank = current_player_rank[0][0] if current_player_rank else 1

        message_text += f"Ваше место в рейтинге: {current_player_rank}\n"
        message_text += f"💵 Ваш баланс: {current_player[2]}\n"
        message_text += f"🏦 Ваш банк: {current_player[3]}\n"
        message_text += f"💰 Итого: {current_player[2] + current_player[3]}"

        # Отправляем сообщение
        await message.answer(message_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при получении ТОПа: {e}")
        await message.answer("⚠️ Произошла ошибка при получении рейтинга.")


async def handle_toplevel(message: types.Message):
    """
    Обработчик команды /toplevel. Выводит ТОП-10 игроков по уровню.
    """
    try:
        # Получаем ТОП-10 игроков по уровню
        query = '''
            SELECT user_id, username, level
            FROM users
            ORDER BY level DESC
            LIMIT 10
        '''
        top_players = await execute_db_query(query)

        # Получаем данные текущего игрока
        user_id = message.from_user.id
        query = '''
            SELECT user_id, username, level
            FROM users
            WHERE user_id = %s
        '''
        current_player = await execute_db_query(query, (user_id,))

        if not current_player:
            await message.answer("⚠️ Ваш профиль не найден. Зарегистрируйтесь через /start.")
            return

        current_player = current_player[0]

        # Формируем сообщение с ТОП-10
        message_text = "🏆 ТОП-10 игроков по уровню:\n\n"
        for i, (user_id, username, level) in enumerate(top_players, start=1):
            message_text += f"{i}. {username} (ID: {user_id})\n"
            message_text += f"   🎯 Уровень: {level}\n\n"

        # Добавляем место текущего игрока
        query = '''
            SELECT COUNT(*) + 1
            FROM users
            WHERE level > %s
        '''
        current_player_rank = await execute_db_query(query, (current_player[2],))
        current_player_rank = current_player_rank[0][0] if current_player_rank else 1

        message_text += f"Ваше место в рейтинге: {current_player_rank}\n"
        message_text += f"🎯 Ваш уровень: {current_player[2]}"

        # Отправляем сообщение
        await message.answer(message_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при получении ТОПа по уровню: {e}")
        await message.answer("⚠️ Произошла ошибка при получении рейтинга.")


async def handle_toprefs(message: types.Message):
    """
    Обработчик команды /toprefs. Выводит ТОП-10 игроков по количеству рефералов.
    """
    try:
        # Получаем ТОП-10 игроков по количеству рефералов
        query = '''
            SELECT user_id, username, reffer
            FROM users
            ORDER BY reffer DESC
            LIMIT 10
        '''
        top_players = await execute_db_query(query)

        # Получаем данные текущего игрока
        user_id = message.from_user.id
        query = '''
            SELECT user_id, username, reffer
            FROM users
            WHERE user_id = %s
        '''
        current_player = await execute_db_query(query, (user_id,))

        if not current_player:
            await message.answer("⚠️ Ваш профиль не найден. Зарегистрируйтесь через /start.")
            return

        current_player = current_player[0]

        # Формируем сообщение с ТОП-10
        message_text = "🏆 ТОП-10 игроков по количеству рефералов:\n\n"
        for i, (user_id, username, reffer) in enumerate(top_players, start=1):
            message_text += f"{i}. {username} (ID: {user_id})\n"
            message_text += f"   👥 Рефералов: {reffer}\n\n"

        # Добавляем место текущего игрока
        query = '''
            SELECT COUNT(*) + 1
            FROM users
            WHERE reffer > %s
        '''
        current_player_rank = await execute_db_query(query, (current_player[2],))
        current_player_rank = current_player_rank[0][0] if current_player_rank else 1

        message_text += f"Ваше место в рейтинге: {current_player_rank}\n"
        message_text += f"👥 Ваше количество рефералов: {current_player[2]}"

        # Отправляем сообщение
        await message.answer(message_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при получении ТОПа по рефералам: {e}")
        await message.answer("⚠️ Произошла ошибка при получении рейтинга.")


async def handle_top_command(message: types.Message):
    """
    Обработчик команды /top. Выводит информацию о команде и предоставляет кнопки для навигации.
    """
    try:
        # Создаем клавиатуру с кнопками
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🏆 ТОП богачей"), KeyboardButton(text="🎯 ТОП уровней")],
                [KeyboardButton(text="👥 ТОП рефералов"), KeyboardButton(text="👤 Профиль")],
                [KeyboardButton(text="‼ Помощь")]
            ],
            resize_keyboard=True  # Кнопки будут автоматически подстраиваться под размер экрана
        )

        # Отправляем сообщение с информацией и клавиатурой
        await message.answer(
            "🏆 Добро пожаловать в раздел ТОПов!\n\n"
            "Здесь вы можете посмотреть рейтинги игроков по различным критериям:\n"
            "- 🏆 ТОП богачей: Рейтинг игроков по балансу.\n"
            "- 🎯 ТОП уровней: Рейтинг игроков по уровню.\n"
            "- 👥 ТОП рефералов: Рейтинг игроков по количеству приглашенных друзей.\n\n"
            "Выберите один из вариантов ниже:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /top: {e}")
        await message.answer("⚠️ Произошла ошибка при обработке команды.")
