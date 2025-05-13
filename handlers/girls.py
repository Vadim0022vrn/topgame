from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.database import execute_db_query
from config.girls import GIRLS
from handlers.profile import handle_assets
import logging
import random

logger = logging.getLogger(__name__)

# Состояния для подтверждения расставания
class BreakUpStates(StatesGroup):
    confirm_break_up = State()

def format_bonuses(bonuses):
    """
    Форматирует бонусы в читаемый вид.
    Пример: {'income': 0.05, 'experience': 0.03} -> "Доход +5%, Опыт +3%"
    """
    if not bonuses:
        return "Нет бонусов"
    
    formatted_bonuses = []
    for bonus_type, value in bonuses.items():
        if bonus_type == "income":
            formatted_bonuses.append(f"Доход +{int(value * 100)}%")
        elif bonus_type == "experience":
            formatted_bonuses.append(f"Опыт +{int(value * 100)}%")
    
    return ", ".join(formatted_bonuses)

async def handle_my_girl(message: types.Message):
    """
    Показывает информацию о текущей девушке игрока.
    """
    try:
        user_id = message.from_user.id

        # Получаем текущую девушку игрока
        girl_data = await execute_db_query(
            "SELECT girlfriend FROM users WHERE user_id = %s",
            (user_id,)
        )
        if not girl_data or not girl_data[0][0]:
            await message.answer("😢 У вас пока нет девушки.")
            return

        girl_id = girl_data[0][0]
        girl_info = GIRLS[girl_id]

        # Форматируем бонусы
        bonuses_text = format_bonuses(girl_info['bonus'])

        # Создаем клавиатуру с кнопками
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="💔 Бросить девушку")],
                [KeyboardButton(text="🏠 Имущество"), KeyboardButton(text="👤 Профиль")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            f"👩 Ваша девушка: {girl_info['name']}\n"
            f"💵 Ежемесячные траты на девушку: {girl_info['monthly_cost']}💵\n"
            f"🎁 Бонусы: {bonuses_text}\n\n"
            f"⚠️ Если вы решите расстаться, {girl_info['name']} может обратиться в суд и отсудить у вас часть ваших средств (от 7% до 15% от текущего баланса).",
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Ошибка при получении информации о девушке: {e}")
        await message.answer("⚠️ Произошла ошибка при получении информации о девушке.")

async def handle_break_up(message: types.Message, state: FSMContext):
    """
    Обработчик для кнопки "Бросить девушку". Запрашивает подтверждение.
    """
    try:
        user_id = message.from_user.id

        # Получаем текущую девушку игрока
        girl_data = await execute_db_query(
            "SELECT girlfriend FROM users WHERE user_id = %s",
            (user_id,)
        )
        if not girl_data or not girl_data[0][0]:
            await message.answer("😢 У вас пока нет девушки.")
            return

        girl_id = girl_data[0][0]
        girl_info = GIRLS[girl_id]

        # Запрашиваем подтверждение
        await message.answer(
            f"⚠️ Вы уверены, что хотите расстаться с {girl_info['name']}?\n"
            f"Она может обратиться в суд и отсудить у вас часть ваших средств (от 7% до 15% от текущего баланса).\n\n"
            f"Напишите 'да', чтобы подтвердить, или 'нет', чтобы отменить.",
            reply_markup=ReplyKeyboardRemove()  # Убираем клавиатуру для подтверждения
        )
        await state.set_state(BreakUpStates.confirm_break_up)

    except Exception as e:
        logger.error(f"Ошибка при запросе подтверждения расставания: {e}")
        await message.answer("⚠️ Произошла ошибка при запросе подтверждения.")

async def handle_confirm_break_up(message: types.Message, state: FSMContext):
    """
    Обработчик подтверждения расставания.
    """
    try:
        user_id = message.from_user.id
        user_response = message.text.lower()

        if user_response == "да":
            # Получаем текущий баланс игрока
            balance_data = await execute_db_query(
                "SELECT balance FROM users WHERE user_id = %s",
                (user_id,)
            )
            if not balance_data:
                await message.answer("⚠️ Произошла ошибка при получении данных о балансе.")
                await state.clear()
                return

            balance = balance_data[0][0]

            # Рассчитываем случайный процент от 7% до 15%
            breakup_percent = random.randint(7, 15) / 100
            breakup_cost = int(balance * breakup_percent)

            # Удаляем девушку у игрока
            await execute_db_query(
                "UPDATE users SET girlfriend = NULL WHERE user_id = %s",
                (user_id,)
            )

            # Списание средств
            await execute_db_query(
                "UPDATE users SET balance = balance - %s WHERE user_id = %s",
                (breakup_cost, user_id)
            )

            # Перенаправляем в раздел "Имущество"
            await message.answer(
                f"💔 Вы расстались с девушкой. Она обратилась в суд и отсудила у вас {breakup_cost}💵 ({breakup_percent * 100}% от вашего баланса).\n\n"
                f"💰 Ваш текущий баланс: {balance - breakup_cost}💵."
            )
            await handle_assets(message)  # Перенаправление в раздел "Имущество"
        elif user_response == "нет":
            await message.answer("✅ Расставание отменено.")
        else:
            await message.answer("⚠️ Пожалуйста, напишите 'да' или 'нет'.")

        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка при удалении девушки: {e}")
        await message.answer("⚠️ Произошла ошибка при удалении девушки.")
        await state.clear()