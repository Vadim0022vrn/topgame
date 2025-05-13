import asyncio
import logging
from utils.database import execute_db_query
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message
from datetime import datetime, timedelta
from aiogram.filters.command import CommandObject
from utils.income_utils import calculate_income_with_bonus
from config.level import add_experience
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove

router = Router()

logger = logging.getLogger(__name__)

async def handle_deposit(message: types.Message, amount: int):
    """
    Обрабатывает пополнение банка.
    """
    user_id = message.from_user.id

    if not message.text.split(' ', 1)[1:]:
        await message.answer("Введите сумму для депозита, например: /deposit 1000")
        return

    amount = message.text.split(' ', 1)[1]
    if not amount.isdigit():
        await message.answer("Сумма должна быть числом!")
        return

    amount = int(amount)

    # Проверяем, хватает ли средств на балансе
    query_balance_check = "SELECT balance FROM users WHERE user_id = %s"
    balance_result = await execute_db_query(query_balance_check, (message.from_user.id,))

    # Если результат запроса - это список кортежей
    if not balance_result or balance_result[0][0] < amount:  # Индексируем кортеж
        await message.answer("❌ Недостаточно средств на балансе для перевода!")
        return

    # Тут вызовешь свою функцию перевода денег
    await transfer_to_bank(message.from_user.id, amount)

    await message.answer(f"✅ В банк переведено {amount} 💰")

async def transfer_to_bank(user_id: int, amount: int):
    """Переводит деньги из баланса в банк"""
    query = """
        UPDATE users
        SET bank = bank + %s, balance = balance - %s
        WHERE user_id = %s AND balance >= %s
    """
    await execute_db_query(query, (amount, amount, user_id, amount))


async def handle_withdraw(message: types.Message, amount: int):
    """
    Обрабатывает снятие денег с банка.
    """
    user_id = message.from_user.id

    if not message.text.split(' ', 1)[1:]:
        await message.answer("Введите сумму для снятия, например: /withdraw 1000")
        return

    amount = message.text.split(' ', 1)[1]
    if not amount.isdigit():
        await message.answer("Сумма должна быть числом!")
        return

    amount = int(amount)

    # Проверяем, хватает ли средств на банковском счете
    query_bank_check = "SELECT bank FROM users WHERE user_id = %s"
    bank_result = await execute_db_query(query_bank_check, (message.from_user.id,))

    # Если результат запроса - это список кортежей
    if not bank_result or bank_result[0][0] < amount:  # Индексируем кортеж
        await message.answer("❌ Недостаточно средств на банковском счете для снятия!")
        return

    # Тут вызовешь свою функцию снятия денег
    await withdraw_from_bank(message.from_user.id, amount)

    await message.answer(f"✅ Со счета снято {amount} 💰")

async def withdraw_from_bank(user_id: int, amount: int):
    """Снимает деньги с банковского счета и переводит их на баланс"""
    query = """
        UPDATE users
        SET bank = bank - %s, balance = balance + %s
        WHERE user_id = %s AND bank >= %s
    """
    await execute_db_query(query, (amount, amount, user_id, amount))


INVESTMENT_PLANS = {
    "invest1": (1, 7),   # 1 час - 5%
    "invest2": (12, 15), # 12 часов - 15%
    "invest3": (24, 25), # 24 часа - 25%
    "invest4": (72, 50), # 3 дня - 50%
    "invest5": (168, 100) # 7 дней - 100%
}

async def handle_investment(message: types.Message, investment_type: str = None, amount: int = None):
    try:
        # Если параметры не переданы, пытаемся извлечь их из сообщения
        if investment_type is None or amount is None:
            command_parts = message.text.split()
            if len(command_parts) != 2 or not command_parts[1].isdigit():
                await message.answer("Используйте формат: /команда сумма (например, /invest1 1000)")
                return
            
            investment_type = command_parts[0][1:]  # Убираем '/'
            amount = int(command_parts[1])
        
        # Остальная логика handle_investment
        if investment_type not in INVESTMENT_PLANS:
            await message.answer("Неверная команда.")
            return
        
        # Проверяем, есть ли у игрока активная инвестиция
        active_investment_query = """
            SELECT id FROM investments WHERE user_id = %s AND claimed = FALSE
        """
        active_investment = await execute_db_query(active_investment_query, (message.from_user.id,))
        
        if active_investment:
            await message.answer("У вас уже есть активная инвестиция! Сначала заберите её прибыль.")
            return
        
        # Получаем параметры инвестиции
        duration, profit_percent = INVESTMENT_PLANS[investment_type]

        # Рассчитываем базовую прибыль (процент от вложения)
        base_profit = round(amount * (profit_percent / 100))

        # Получаем бонус пользователя (теперь это только процент бонуса)
        bonus_percent = calculate_income_with_bonus(message.from_user.id, base_profit)
        logger.info(f"Бонус города для пользователя {message.from_user.id}: {bonus_percent}")

        # Рассчитываем бонус к прибыли
        bonus_amount = round(base_profit * bonus_percent)

        # Итоговая прибыль = базовая прибыль + бонус
        total_profit = base_profit + bonus_amount

        logger.info(f"Прибыль с бонусом: {total_profit}")

        end_time = datetime.now() + timedelta(hours=duration)

        # Проверяем баланс пользователя
        check_balance = "SELECT bank FROM users WHERE user_id = %s"
        result = await execute_db_query(check_balance, (message.from_user.id,))
        if not result or result[0][0] < amount:  # result[0][0] - баланс из БД
            await message.answer("Недостаточно средств в банке!")
            return
        
        # Вычитаем сумму из банка
        update_balance = "UPDATE users SET bank = bank - %s WHERE user_id = %s"
        await execute_db_query(update_balance, (amount, message.from_user.id))

        # Добавляем запись в инвестиции
        insert_query = """
            INSERT INTO investments (user_id, amount, profit, end_time, claimed)
            VALUES (%s, %s, %s, %s, FALSE)
        """
        await execute_db_query(insert_query, (message.from_user.id, amount, total_profit, end_time))

        await message.answer(f"Вы вложили {amount} 💰 на {duration} ч. Доход: +{total_profit} 💰 (с учетом бонуса). Забрать можно после {end_time.strftime('%Y-%m-%d %H:%M:%S')}.")
    except Exception as e:
        await message.answer("Ошибка при обработке инвестиции.")
        print(f"Ошибка: {e}")

async def handle_claim_investments(message: Message):
    try:
        user_id = message.from_user.id
        
        # Проверяем доступные завершенные инвестиции
        check_query = """
            SELECT id, amount, profit FROM investments
            WHERE user_id = %s AND end_time <= NOW() AND claimed = FALSE
        """
        results = await execute_db_query(check_query, (user_id,))
        
        if not results:
            await message.answer("У вас нет завершенных инвестиций для вывода.")
            return
        
        # Суммируем прибыль (amount + profit)
        total_profit = sum(row[1] + row[2] for row in results)  # row[1] = amount, row[2] = profit
        investment_ids = tuple(row[0] for row in results)  # row[0] = id
        
        # Убираем вызов calculate_income_with_bonus, так как бонус уже применен при создании инвестиции
        total_profit_with_bonus = total_profit  # Бонус уже учтен в profit

        # Опыт (значение можно изменить по желанию)
        exp_earned = round(total_profit_with_bonus * 0.05)  # 5% от прибыли в виде опыта

        # Обновляем статус инвестиций на 'claimed'
        update_query = f"UPDATE investments SET claimed = TRUE WHERE id IN ({','.join(['%s'] * len(investment_ids))})"
        await execute_db_query(update_query, investment_ids)

        # Удаляем собранные инвестиции
        delete_query = f"DELETE FROM investments WHERE id IN ({','.join(['%s'] * len(investment_ids))})"
        await execute_db_query(delete_query, investment_ids)
        
        # Начисляем деньги на банк и опыт в experience
        update_balance = "UPDATE users SET bank = bank + %s, experience = experience + %s WHERE user_id = %s"
        await execute_db_query(update_balance, (total_profit_with_bonus, exp_earned, user_id))
        
        await message.answer(f"Вы успешно забрали {total_profit_with_bonus} 💰 с инвестиций!\n"
                             f"Дополнительно получено {exp_earned} опыта! 🎯")
    except Exception as e:
        await message.answer("Ошибка при выводе инвестиций.")
        print(f"Ошибка: {e}")


async def handle_bank(message: types.Message):
    try:
        user_id = message.from_user.id

        # Получаем информацию о балансе, кэшбеке и инвестициях из таблицы users
        user_query = '''
            SELECT bank, cashback, solix FROM users WHERE user_id = %s
        '''
        user_result = await execute_db_query(user_query, (user_id,))

        if not user_result:
            await message.answer("⚠️ Ваш профиль не найден. Зарегистрируйтесь через /start.")
            return

        bank_balance, cashback, solix = user_result[0]

        # Получаем информацию о текущих инвестициях из таблицы investments
        investments_query = '''
            SELECT SUM(amount), SUM(profit) FROM investments WHERE user_id = %s AND claimed = FALSE
        '''
        investments_result = await execute_db_query(investments_query, (user_id,))

        if investments_result and investments_result[0][0] is not None:
            total_invested, total_profit = investments_result[0]
        else:
            total_invested, total_profit = 0, 0

        # Формируем сообщение с информацией о банковском счете, инвестициях и кэшбеке
        bank_info = (
            f"🏦 <b>Ваш банковский счет:</b>\n"
            f"💰 Баланс: <b>{bank_balance}</b>\n"
            f"💳 Кэшбек: <b>{cashback}</b>\n"
            f"💎 Solix: <b>{solix}</b> (Криптовалюта)\n"
            f"📈 Инвестиции: <b>{total_invested}</b> (ожидаемая прибыль: <b>{total_profit}</b>)\n"
        )

        # Отправляем сообщение с клавиатурой банка
        await message.answer(bank_info, parse_mode="HTML", reply_markup=get_bank_keyboard())

    except Exception as e:
        logging.error(f"Ошибка при получении информации о банковском счете: {str(e)}")
        await message.answer("⚠️ Ошибка при получении информации о банковском счете.")

def get_bank_keyboard():
    """
    Создает клавиатуру для меню банка.
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профиль")],  # Кнопка "Профиль"
            [KeyboardButton(text="💳 Собрать кэшбек")],  # Кнопка "Собрать кэшбек"
            [KeyboardButton(text="📈 Инвестиции")],  # Кнопка "Собрать кэшбек"
        ],
        resize_keyboard=True  # Кнопки будут автоматически подстраиваться под размер экрана
    )
    return keyboard



async def handle_collect_cashback(message: types.Message):
    try:
        user_id = message.from_user.id

        # Получаем текущий кэшбек пользователя
        cashback_query = '''
            SELECT cashback FROM users WHERE user_id = %s
        '''
        cashback_result = await execute_db_query(cashback_query, (user_id,))

        if not cashback_result:
            await message.answer("⚠️ Ваш профиль не найден. Зарегистрируйтесь через /start.")
            return

        cashback = cashback_result[0][0]

        if cashback <= 0:
            await message.answer("ℹ️ У вас нет накопленного кэшбека для сбора.")
            return

        # Обновляем баланс пользователя и обнуляем кэшбек
        update_query = '''
            UPDATE users 
            SET balance = balance + %s, cashback = 0 
            WHERE user_id = %s
        '''
        await execute_db_query(update_query, (cashback, user_id))

        # Добавляем опыт: 1 опыт за каждые 5$ снятых
        experience_to_add = cashback // 5  # Целочисленное деление на 5
        if experience_to_add > 0:
            new_level, total_experience, level_increased = await add_experience(user_id, experience_to_add)
            if level_increased:
                await message.answer(f"🎉 Поздравляем! Вы достигли уровня {new_level}!")

        # Отправляем сообщение об успешном сборе кэшбека
        await message.answer(f"✅ Вы успешно собрали кэшбек в размере {cashback} 💰 и получили {experience_to_add} опыта!")

    except Exception as e:
        logging.error(f"Ошибка при сборе кэшбека: {str(e)}")
        await message.answer("⚠️ Ошибка при сборе кэшбека.")



async def handle_invests(message: types.Message):
    """
    Обработчик команды /invests. Показывает информацию о доступных инвестициях и кнопки для выбора.
    """
    try:
        # Сообщение с описанием инвестиций
        invest_info = (
            "📈 <b>Доступные инвестиции:</b>\n\n"
            "1. <b>Инвестиция 1</b>: 1 час, 5% прибыли.\n"
            "2. <b>Инвестиция 2</b>: 12 часов, 15% прибыли.\n"
            "3. <b>Инвестиция 3</b>: 24 часа, 25% прибыли.\n"
            "4. <b>Инвестиция 4</b>: 3 дня, 50% прибыли.\n"
            "5. <b>Инвестиция 5</b>: 7 дней, 100% прибыли.\n\n"
            "Выберите инвестицию:"
        )

        # Создаем клавиатуру с кнопками для выбора инвестиций
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Инвестиция 1"), KeyboardButton(text="Инвестиция 2")],
                [KeyboardButton(text="Инвестиция 3"), KeyboardButton(text="Инвестиция 4")],
                [KeyboardButton(text="Инвестиция 5")],
                [KeyboardButton(text="👤 Профиль")],
            ],
            resize_keyboard=True  # Кнопки будут автоматически подстраиваться под размер экрана
        )

        # Отправляем сообщение с описанием и кнопками
        await message.answer(invest_info, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Ошибка при показе информации об инвестициях: {str(e)}")
        await message.answer("⚠️ Ошибка при показе информации об инвестициях.")

# Состояния FSM для инвестиций
class InvestmentState(StatesGroup):
    waiting_for_amount = State()  # Состояние ожидания ввода суммы
    investment_type = State()     # Состояние для сохранения типа инвестиции

# Обработчик для кнопок выбора инвестиции
async def handle_investment_choice(message: types.Message, state: FSMContext):
    try:
        # Сохраняем тип инвестиции в состояние FSM
        investment_type = message.text
        await state.update_data(investment_type=investment_type)

        # Переводим пользователя в состояние ожидания ввода суммы
        await state.set_state(InvestmentState.waiting_for_amount)

        # Запрашиваем сумму у пользователя
        await message.answer(f"Вы выбрали {investment_type}. Введите сумму для инвестиции:", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        logging.error(f"Ошибка при выборе инвестиции: {str(e)}")
        await message.answer("⚠️ Ошибка при выборе инвестиции.")

# Обработчик для ввода суммы
async def handle_investment_amount(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        amount = int(message.text)

        # Получаем сохраненный тип инвестиции из состояния FSM
        data = await state.get_data()
        investment_type = data.get("investment_type")

        # Определяем команду для handle_investment на основе выбранного типа инвестиции
        investment_commands = {
            "Инвестиция 1": "invest1",
            "Инвестиция 2": "invest2",
            "Инвестиция 3": "invest3",
            "Инвестиция 4": "invest4",
            "Инвестиция 5": "invest5",
        }

        # Получаем команду для выбранной инвестиции
        command = investment_commands.get(investment_type)
        if not command:
            await message.answer("⚠️ Неизвестный тип инвестиции.")
            return

        # Вызываем handle_investment с нужными параметрами
        await handle_investment(message, investment_type=command, amount=amount)

        # Сбрасываем состояние FSM
        await state.clear()

        # Возвращаем клавиатуру с кнопками
        await message.answer("Выберите следующее действие:", reply_markup=get_bank_keyboard())

    except Exception as e:
        logging.error(f"Ошибка при обработке суммы инвестиции: {str(e)}")
        await message.answer("⚠️ Ошибка при обработке суммы инвестиции.")

# Обработчик для некорректного ввода
async def handle_invalid_amount(message: types.Message):
    await message.answer("⚠️ Сумма должна быть числом. Попробуйте еще раз.")


